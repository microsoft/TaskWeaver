from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Optional, TypedDict, TypeVar

from taskweaver.utils import create_id

T = TypeVar("T")


@dataclass
class Attachment(Generic[T]):
    if TYPE_CHECKING:
        AttachmentDict = TypedDict("AttachmentDict", {"type": str, "content": T, "id": Optional[str]})

    """Attachment is the unified interface for responses attached to the text mssage.

    Args:
        type: the type of the attachment, which can be "thought", "code", "markdown", or "execution_result".
        content: the content of the response element.
        id: the unique id of the response element.
    """

    id: str
    type: str
    content: T

    @staticmethod
    def create(type: str, content: T, id: Optional[str] = None) -> Attachment[T]:
        id = id if id is not None else "atta-" + create_id()
        return Attachment(
            type=type,
            content=content,
            id=id,
        )

    def __repr__(self) -> str:
        return f"{self.type.upper()}: {self.content}"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> AttachmentDict:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
        }

    @staticmethod
    def from_dict(content: AttachmentDict) -> Attachment[T]:
        return Attachment.create(
            type=content["type"],
            content=content["content"],
            id=content["id"] if "id" in content else None,
        )
