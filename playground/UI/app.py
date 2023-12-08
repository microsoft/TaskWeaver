import chainlit as cl
import sys
import os
repo_path = os.path.join(os.path.dirname(__file__), "../../")
sys.path.append(repo_path)
from taskweaver.app.app import TaskWeaverApp
project_path=os.path.join(repo_path, "project")
app = TaskWeaverApp(app_dir=project_path, use_local_uri=True)
session = app.get_session()

@cl.on_message
async def main(message: cl.Message):
    # Your custom logic goes here...
    response_round = session.send_message(
        message.content,
        event_handler=lambda x, y:  f"{x}:\n{y}"
    )
    print("TaskWeaver response finished")
    id = await cl.Message(content="").send()
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
                elements.append(cl.Text(name=atta.type, content=atta.content, display="inline"))
        elements.append(cl.Text(name=f"{post.send_from} -> {post.send_to}", content=post.message, display="inline"))
        await cl.Message(content=f"{post.send_from}:", elements=elements, parent_id = id).send()
    print("Respond to user")
    if post.send_to == "User":
        elements = None
        if len(artifact_paths) > 0:
            elements = []
            for path in artifact_paths:
                image = cl.Image(name=path, display="inline", path=path, size ="large")
                elements.append(image)
        await cl.Message(content=f"{post.message}", elements=elements).send()