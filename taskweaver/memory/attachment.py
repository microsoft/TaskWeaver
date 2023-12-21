from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, TypedDict

from taskweaver.utils import create_id


class AttachmentType(Enum):
    # Planner Type
    init_plan = "init_plan"
    plan = "plan"
    current_plan_step = "current_plan_step"

    # CodeInterpreter - generate code
    thought = "thought"
    python = "python"

    # CodeInterpreter - sample code
    sample = "sample"

    # CodeInterpreter - verification
    verification = "verification"

    # CodeInterpreter - text message
    text = "text"

    # CodeInterpreter - execute code
    code_error = "code_error"
    execution_status = "execution_status"
    execution_result = "execution_result"
    artifact_paths = "artifact_paths"  # TODO: remove and store artifacts to extra info

    # CodeInterpreter - revise code
    revise_message = "revise_message"

    # function calling
    function = "function"

    # Misc
    invalid_response = "invalid_response"


@dataclass
class Attachment:
    if TYPE_CHECKING:
        AttachmentDict = TypedDict(
            "AttachmentDict",
            {"type": str, "content": str, "id": Optional[str], "extra": Optional[Any]},
        )

    """Attachment is the unified interface for responses attached to the text massage.

    Args:
        type: the type of the attachment, which can be "thought", "code", "markdown", or "execution_result".
        content: the content of the response element.
        id: the unique id of the response element.
    """

    id: str
    type: AttachmentType
    content: str
    extra: Optional[Any] = None

    @staticmethod
    def create(
        type: AttachmentType,
        content: str,
        id: Optional[str] = None,
    ) -> Attachment:
        import builtins

        if builtins.type(type) is str:
            type = AttachmentType(type)
        assert type in AttachmentType, f"Invalid attachment type: {type}"
        id = id if id is not None else "atta-" + create_id()
        return Attachment(
            type=type,
            content=content,
            id=id,
        )

    def __repr__(self) -> str:
        return f"{self.type.value.upper()}: {self.content}"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> AttachmentDict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "extra": self.extra,
        }

    @staticmethod
    def from_dict(content: AttachmentDict) -> Attachment:
        type = AttachmentType(content["type"])
        return Attachment.create(
            type=type,
            content=content["content"],
            id=content["id"] if "id" in content else None,
        )
