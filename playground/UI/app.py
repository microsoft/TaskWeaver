import chainlit as cl
import sys
import os

from typing import Dict
from taskweaver.memory.round import Round

from taskweaver.session.session import Session

repo_path = os.path.join(os.path.dirname(__file__), "../../")
sys.path.append(repo_path)
from taskweaver.app.app import TaskWeaverApp

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
            if atta.type in ["python", "execution_result"]:
                continue
            elif atta.type == "artifact_paths":
                artifact_paths = [item.replace("file://", "") for item in atta.content]
            else:
                elements.append(
                    cl.Text(name=atta.type, content=atta.content, display="inline")
                )
        elements.append(
            cl.Text(
                name=f"{post.send_from} -> {post.send_to}",
                content=post.message,
                display="inline",
            )
        )
        await cl.Message(
            content="---", elements=elements, parent_id=id, author=post.send_from
        ).send()

    if post.send_to == "User":
        elements = None
        if len(artifact_paths) > 0:
            elements = []
            for path in artifact_paths:
                image = cl.Image(name=path, display="inline", path=path, size="large")
                elements.append(image)
        await cl.Message(content=f"{post.message}", elements=elements).send()
