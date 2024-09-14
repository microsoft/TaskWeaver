from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from taskweaver.utils import create_id


@dataclass
class SharedMemoryEntry:
    type: Literal["plan", "experience_sub_path"]
    content: str
    scope: Literal["round", "conversation"]
    id: str

    @staticmethod
    def create(
        type: Literal["plan", "experience_sub_path"],
        content: str,
        scope: Literal["round", "conversation"],
        id: str = None,
    ) -> SharedMemoryEntry:
        if id is None:
            id = "sme-" + create_id()
        return SharedMemoryEntry(
            type=type,
            content=content,
            scope=scope,
            id=id,
        )

    def __repr__(self):
        return f"SharedMemoryEntry: {self.type} effective in {self.scope}\n{self.content}"

    def __str__(self):
        return self.__repr__()

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "content": self.content,
            "scope": self.scope,
            "id": self.id,
        }
