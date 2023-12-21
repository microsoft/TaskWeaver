from typing import Dict, Literal, Optional

ChatMessageRoleType = Literal["system", "user", "assistant", "function"]
ChatMessageType = Dict[Literal["role", "name", "content"], str]


def format_chat_message(
    role: ChatMessageRoleType,
    message: str,
    name: Optional[str] = None,
) -> ChatMessageType:
    msg: ChatMessageType = {
        "role": role,
        "content": message,
    }
    if name is not None:
        msg["name"] = name
    return msg
