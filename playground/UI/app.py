import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import requests

from taskweaver.memory.type_vars import RoleName
from taskweaver.module.event_emitter import PostEventType, RoundEventType, SessionEventHandlerBase

try:
    import chainlit as cl

    print(
        "If UI is not started, please go to the folder playground/UI and run `chainlit run app.py` to start the UI",
    )
except Exception:
    raise Exception(
        "Package chainlit is required for using UI. Please install it manually by running: "
        "`pip install chainlit` and then run `chainlit run app.py`",
    )

repo_path = os.path.join(os.path.dirname(__file__), "../../")
sys.path.append(repo_path)
from taskweaver.app.app import TaskWeaverApp
from taskweaver.memory.attachment import AttachmentType
from taskweaver.session.session import Session

project_path = os.path.join(repo_path, "project")
app = TaskWeaverApp(app_dir=project_path, use_local_uri=True)
app_session_dict: Dict[str, Session] = {}


def file_display(files: List[Tuple[str, str]], session_cwd_path: str):
    elements: List[cl.Element] = []
    for file_name, file_path in files:
        # if image, no need to display as another file
        if file_path.endswith((".png", ".jpg", ".jpeg", ".gif")):
            image = cl.Image(
                name=file_path,
                display="inline",
                path=file_path,
                size="large",
            )
            elements.append(image)
        else:
            if file_path.endswith(".csv"):
                import pandas as pd

                data = (
                    pd.read_csv(file_path)
                    if os.path.isabs(file_path)
                    else pd.read_csv(os.path.join(session_cwd_path, file_path))
                )
                row_count = len(data)
                table = cl.Text(
                    name=file_path,
                    content=f"There are {row_count} in the data. The top {min(row_count, 5)} rows are:\n"
                    + data.head(n=5).to_markdown(),
                    display="inline",
                )
                elements.append(table)
            else:
                print(f"Unsupported file type: {file_name} for inline display.")
            # download files from plugin context
            file = cl.File(
                name=file_name,
                display="inline",
                path=file_path if os.path.isabs(file_path) else os.path.join(session_cwd_path, file_path),
            )
            elements.append(file)
    return elements


def is_link_clickable(url: str):
    if url:
        try:
            response = requests.get(url)
            # If the response status code is 200, the link is clickable
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    else:
        return False


class ChainLitMessageUpdater(SessionEventHandlerBase):
    def __init__(self, root_step: cl.Step):
        self.root_step = root_step
        self.reset_cur_step()

    def reset_cur_step(self):
        self.cur_step: Optional[cl.Step] = None
        self.cur_attachment_list: List[Tuple[str, AttachmentType, str, bool]] = []
        self.cur_post_status: str = "Updating"
        self.cur_send_to: RoleName = "Unknown"
        self.cur_message: str = ""
        self.cur_message_is_end: bool = False
        self.cur_message_sent: bool = False

    def handle_round(
        self,
        type: RoundEventType,
        msg: str,
        extra: Any,
        round_id: str,
        **kwargs: Any,
    ):
        if type == RoundEventType.round_error:
            self.root_step.is_error = True
            self.root_step.output = msg
            cl.run_sync(self.root_step.update())

    def handle_post(
        self,
        type: PostEventType,
        msg: str,
        extra: Any,
        post_id: str,
        round_id: str,
        **kwargs: Any,
    ):
        if type == PostEventType.post_start:
            self.reset_cur_step()
            self.cur_step = cl.Step(name=extra["role"], show_input=True, root=False)
            cl.run_sync(self.cur_step.__aenter__())
        elif type == PostEventType.post_end:
            assert self.cur_step is not None
            content = self.format_post_body(True)
            cl.run_sync(self.cur_step.stream_token(content, True))
            cl.run_sync(self.cur_step.__aexit__(None, None, None))  # type: ignore
            self.reset_cur_step()
        elif type == PostEventType.post_error:
            pass
        elif type == PostEventType.post_attachment_update:
            assert self.cur_step is not None, "cur_step should not be None"
            id: str = extra["id"]
            a_type: AttachmentType = extra["type"]
            is_end: bool = extra["is_end"]
            # a_extra: Any = extra["extra"]
            if len(self.cur_attachment_list) == 0 or id != self.cur_attachment_list[-1][0]:
                self.cur_attachment_list.append((id, a_type, msg, is_end))

            else:
                prev_msg = self.cur_attachment_list[-1][2]
                self.cur_attachment_list[-1] = (id, a_type, prev_msg + msg, is_end)

        elif type == PostEventType.post_send_to_update:
            self.cur_send_to = extra["role"]
        elif type == PostEventType.post_message_update:
            self.cur_message += msg
            if extra["is_end"]:
                self.cur_message_is_end = True
        elif type == PostEventType.post_status_update:
            self.cur_post_status = msg

        if self.cur_step is not None:
            content = self.format_post_body(False)
            cl.run_sync(self.cur_step.stream_token(content, True))
            if self.cur_message_is_end and not self.cur_message_sent:
                self.cur_message_sent = True
                self.cur_step.elements = [
                    *(self.cur_step.elements or []),
                    cl.Text(
                        content=self.cur_message,
                        display="inline",
                    ),
                ]
                cl.run_sync(self.cur_step.update())

    def format_post_body(self, is_end: bool) -> str:
        content_chunks: List[str] = []

        for attachment in self.cur_attachment_list:
            a_type = attachment[1]

            # skip artifact paths always
            if a_type in [AttachmentType.artifact_paths]:
                continue

            # skip Python in final result
            if is_end and a_type in [AttachmentType.python]:
                continue

            content_chunks.append(self.format_attachment(attachment))

        if self.cur_message != "":
            if self.cur_send_to == "Unknown":
                content_chunks.append("**Message**:")
            else:
                content_chunks.append(f"**Message To {self.cur_send_to}**:")

            if not self.cur_message_sent:
                content_chunks.append(self.cur_message)

        if not is_end:
            status_chunk = f"**Status**: {self.cur_post_status}"
            content_chunks.append(status_chunk)

        return "\n\n".join(content_chunks)

    def format_attachment(
        self,
        attachment: Tuple[str, AttachmentType, str, bool],
    ) -> str:
        id, a_type, msg, is_end = attachment
        newline = "\n" if "\n" in msg else " "
        attach_type = " ".join([item.capitalize() for item in a_type.value.split("_")])
        return f"**{attach_type}**:{newline}{msg}"


@cl.on_chat_start
async def start():
    user_session_id = cl.user_session.get("id")
    app_session_dict[user_session_id] = app.get_session()


@cl.on_message
async def main(message: cl.Message):
    user_session_id = cl.user_session.get("id")  # type: ignore
    session: Session = app_session_dict[user_session_id]  # type: ignore
    session_cwd_path = session.execution_cwd

    # display loader before sending message

    async with cl.Step(name="", show_input=True, root=True) as root_step:
        response_round = await cl.make_async(session.send_message)(
            message.content,
            files=[
                {
                    "name": element.name if element.name else "file",
                    "path": element.path,
                }
                for element in message.elements
                if element.type == "file"
            ],
            event_handler=ChainLitMessageUpdater(root_step),
        )

    artifact_paths = [
        p
        for p in response_round.post_list
        for a in p.attachment_list
        if a.type == AttachmentType.artifact_paths
        for p in a.content
    ]

    for post in [p for p in response_round.post_list if p.send_to == "User"]:
        files: List[Tuple[str, str]] = []
        if len(artifact_paths) > 0:
            for file_path in artifact_paths:
                # if path is image or csv (the top 5 rows), display it
                file_name = os.path.basename(file_path)
                files.append((file_name, file_path))

        # Extract the file path from the message and display it
        user_msg_content = post.message
        pattern = r"(!?)\[(.*?)\]\((.*?)\)"
        matches = re.findall(pattern, user_msg_content)
        for match in matches:
            img_prefix, file_name, file_path = match
            if "://" in file_path:
                if not is_link_clickable(file_path):
                    user_msg_content = user_msg_content.replace(
                        f"{img_prefix}[{file_name}]({file_path})",
                        file_name,
                    )
                continue
            files.append((file_name, file_path))
            user_msg_content = user_msg_content.replace(
                f"{img_prefix}[{file_name}]({file_path})",
                file_name,
            )

        elements = file_display(files, session_cwd_path)
        await cl.Message(
            author="TaskWeaver",
            content=f"{user_msg_content}",
            elements=elements if len(elements) > 0 else None,
        ).send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    # change current directory to the directory of this file for loading resources
    os.path.curdir = os.path.dirname(__file__)
    run_chainlit(__file__)
