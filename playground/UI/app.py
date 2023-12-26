import os
import sys
from typing import Dict

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


@cl.on_chat_start
async def start():
    user_session_id = cl.user_session.get("id")
    app_session_dict[user_session_id] = app.get_session()


@cl.on_message
async def main(message: cl.Message):
    user_session_id = cl.user_session.get("id")
    session = app_session_dict[user_session_id]

    def send_message_sync(msg: str) -> Round:
        return session.send_message(msg)

    # display loader before sending message
    id = await cl.Message(content="").send()

    response_round = await cl.make_async(send_message_sync)(message.content)

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
        elements = None
        if len(artifact_paths) > 0:
            elements = []
            for path in artifact_paths:
                # if path is image, display it
                if path.endswith((".png", ".jpg", ".jpeg", ".gif")):
                    image = cl.Image(
                        name=path,
                        display="inline",
                        path=path,
                        size="large",
                    )
                    elements.append(image)
                elif path.endswith(".csv"):
                    import pandas as pd

                    data = pd.read_csv(path)
                    row_count = len(data)
                    table = cl.Text(
                        name=path,
                        content=f"There are {row_count} in the data. The top {min(row_count, 5)} rows are:\n"
                        + data.head(n=5).to_markdown(),
                        display="inline",
                    )
                    elements.append(table)
        await cl.Message(content=f"{post.message}", elements=elements).send()
