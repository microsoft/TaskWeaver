import os
import re
import sys
from typing import Any, Dict, List, Tuple

import requests

try:
    import chainlit as cl

    print("If UI is not started, please go to the folder playground/UI and run `chainlit run app.py` to start the UI")
except Exception:
    raise Exception(
        "Package chainlit is required for using UI. Please install it manually by running: "
        "`pip install chainlit` and then run `chainlit run app.py`",
    )

repo_path = os.path.join(os.path.dirname(__file__), "../../")
sys.path.append(repo_path)
from taskweaver.app.app import TaskWeaverApp
from taskweaver.memory.attachment import AttachmentType
from taskweaver.memory.round import Round
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


@cl.on_chat_start
async def start():
    user_session_id = cl.user_session.get("id")
    app_session_dict[user_session_id] = app.get_session()


@cl.on_message
async def main(message: cl.Message):
    user_session_id = cl.user_session.get("id")
    session = app_session_dict[user_session_id]
    session_cwd_path = session.execution_cwd

    def send_message_sync(msg: str, files: Any) -> Round:
        return session.send_message(msg, files=files)

    # display loader before sending message
    id = await cl.Message(content="").send()

    response_round = await cl.make_async(send_message_sync)(
        message.content,
        [
            {
                "name": element.name if element.name else "file",
                "content": element.content,
            }
            for element in message.elements
            if element.type == "file" and element.content is not None
        ],
    )

    artifact_paths = []
    for post in response_round.post_list:
        if post.send_from == "User":
            continue
        elements = []
        for atta in post.attachment_list:
            if atta.type in [
                AttachmentType.python,
                AttachmentType.execution_result,
            ]:
                continue
            elif atta.type == AttachmentType.artifact_paths:
                artifact_paths = atta.content
            else:
                elements.append(
                    cl.Text(
                        name=atta.type.value,
                        content=atta.content.encode(),
                        display="inline",
                    ),
                )
        elements.append(
            cl.Text(
                name=f"{post.send_from} -> {post.send_to}",
                content=post.message,
                display="inline",
            ),
        )
        await cl.Message(
            content="---",
            elements=elements,
            parent_id=id,
            author=post.send_from,
        ).send()

    if post.send_to == "User":
        files = []
        if len(artifact_paths) > 0:
            for file_path in artifact_paths:
                # if path is image or csv (the top 5 rows), display it
                file_name = os.path.basename(file_path)
                files.append((file_name, file_path))

        # Extract the file path from the message and display it
        message = post.message
        pattern = r"(!?)\[(.*?)\]\((.*?)\)"
        matches = re.findall(pattern, message)
        for match in matches:
            img_prefix, file_name, file_path = match
            if "://" in file_path:
                if not is_link_clickable(file_path):
                    message = message.replace(f"{img_prefix}[{file_name}]({file_path})", file_name)
                continue
            files.append((file_name, file_path))
            message = message.replace(f"{img_prefix}[{file_name}]({file_path})", file_name)

        elements = file_display(files, session_cwd_path)
        await cl.Message(content=f"{message}", elements=elements if len(elements) > 0 else None).send()
