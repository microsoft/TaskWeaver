from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from taskweaver.utils import create_id

from .type_vars import SharedMemoryEntryScope, SharedMemoryEntryType


@dataclass
class SharedMemoryEntry:
    type: SharedMemoryEntryType
    content: str
    scope: SharedMemoryEntryScope
    id: str

    @staticmethod
    def create(
        type: SharedMemoryEntryType,
        content: str,
        scope: SharedMemoryEntryScope,
        id: Optional[str] = None,
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

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.type,
            "content": self.content,
            "scope": self.scope,
            "id": self.id,
        }
