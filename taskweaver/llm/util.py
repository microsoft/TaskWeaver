from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

ChatMessageRoleType = Literal["system", "user", "assistant", "function"]
ChatContentType = Dict[Literal["type", "text", "image_url"], str | Dict[Literal["url"], str]]
ChatMessageType = Dict[Literal["role", "name", "content"], str | List[ChatContentType]]

PromptTypeSimple = List[ChatMessageType]


class PromptFunctionType(TypedDict):
    name: str
    description: str
    parameters: Dict[str, Any]


class PromptToolType(TypedDict):
    type: Literal["function"]
    function: PromptFunctionType


class PromptTypeWithTools(TypedDict):
    prompt: PromptTypeSimple
    tools: Optional[List[PromptToolType]]


def format_chat_message_content(
    content_type: Literal["text", "image_url"],
    content_value: str,
) -> ChatContentType:
    if content_type == "image_url":
        return {
            "type": content_type,
            content_type: {
                "url": content_value,
            },
        }
    else:
        return {
            "type": content_type,
            content_type: content_value,
        }


def format_chat_message(
    role: ChatMessageRoleType,
    message: str | List[ChatContentType],
    name: Optional[str] = None,
) -> ChatMessageType:
    msg: ChatMessageType = {
        "role": role,
        "content": message,
    }
    if name is not None:
        msg["name"] = name
    return msg


def serialize_prompt(
    prompt: Union[PromptTypeSimple, PromptTypeWithTools],
    pretty: bool = False,
) -> str:
    import json

    if not pretty:
        return json.dumps(prompt, indent=2)

    def serialize_chat_message(message: ChatMessageType) -> str:
        return "\n".join(
            [
                f"<|im_start|>{message['role']}" + (f" name={message['name']}" if "name" in message else ""),
                message["content"],
                "<|im_end|>",
            ],
        )

    def format_prompt_simple(prompt: PromptTypeSimple) -> str:
        return "\n".join([serialize_chat_message(message) for message in prompt])

    def serialize_tool(tool: PromptToolType) -> str:
        return json.dumps(tool, indent=2)

    if isinstance(prompt, list):
        return format_prompt_simple(prompt)
    else:
        return "\n".join(
            [
                "<----------------- Prompt ----------------->",
                *format_prompt_simple(prompt["prompt"]),
                "<----------------- Tools ----------------->",
                *[serialize_tool(tool) for tool in prompt["tools"] or []],
            ],
        )
