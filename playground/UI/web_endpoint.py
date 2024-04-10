import atexit
import os
import sys
from typing import Dict, Optional

import chainlit as cl
from chainlit.context import init_http_context
from chainlit.server import app
from pydantic import BaseModel

# change current directory to the directory of this file for loading resources
os.chdir(os.path.dirname(__file__))
repo_path = os.path.join(os.path.dirname(__file__), "../../")
sys.path.append(repo_path)
from taskweaver.app.app import TaskWeaverApp
from taskweaver.session.session import Session

project_path = os.path.join(repo_path, "project")
tw_app = TaskWeaverApp(app_dir=project_path, use_local_uri=True)
atexit.register(tw_app.stop)
app_session_dict: Dict[str, Session] = {}


class Request(BaseModel):
    query: str
    prev_session_id: Optional[str] = None


@app.get("/query")
async def query(request: Request):
    init_http_context()

    print("Received query: ", request.query, " session_id: ", request.prev_session_id)
    msg = cl.Message(content=request.query)
    response = await api_call(message=msg, user_session_id=request.prev_session_id)
    return response


@cl.on_message
async def api_call(message: cl.Message, user_session_id: str):
    if user_session_id is None or user_session_id not in app_session_dict:
        user_session_id = cl.user_session.get("id")
        print("Starting new session: ", user_session_id)
        session: Session = tw_app.get_session()
        app_session_dict[user_session_id] = session
    else:
        session: Session = app_session_dict[user_session_id]
        print("Continue the existing session: ", user_session_id)

    response_round = await cl.make_async(session.send_message)(
        message.content,
        files=[
            {
                "name": element.name if element.name else "file",
                "path": element.path,
            }
            for element in message.elements
            if element.type == "file" or element.type == "image"
        ],
    )
    response = response_round.to_dict()
    response["prev_session_id"] = user_session_id
    return response


@cl.on_chat_end
async def end():
    user_session_id = cl.user_session.get("id")
    app_session = app_session_dict[user_session_id]
    print(f"Stopping session {app_session.session_id}")
    app_session.stop()
    app_session_dict.pop(user_session_id)


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)


# Test the endpoint
# curl --location --request GET 'http://localhost:8000/query' \
# --header 'Content-Type: application/json' \
# --data '{
#     "query": "how are you?"
# }'

# To continue the previous session
# {
#     "query": "how are you?",
#     "prev_session_id": "session id "
# }
