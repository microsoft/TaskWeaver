from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

from taskweaver.memory.type_vars import RoleName
from taskweaver.utils import create_id


@dataclass
class SharedMemoryEntry:
    type: Literal["plan", "experience_sub_path"]
    by: str
    content: str
    scope: Literal["round", "conversation"]
    # The id of the round or conversation
    scope_id: str
    aggregation_keys: Tuple[Literal["by", "type", "scope", "scope_id", "id"], ...]
    id: str

    @staticmethod
    def create(
        type: Literal["plan", "experience_sub_path"],
        by: RoleName,
        content: str,
        scope: Literal["round", "conversation"],
        scope_id: str,
        aggregation_keys: Optional[Tuple[Literal["by", "type", "scope", "scope_id", "id"], ...]] = None,
        id: str = None,
    ) -> SharedMemoryEntry:
        if aggregation_keys is None:
            aggregation_keys = ("by", "type", "scope", "scope_id")
        if id is None:
            id = "sme-" + create_id()
        return SharedMemoryEntry(
            type=type,
            by=by,
            content=content,
            scope=scope,
            scope_id=scope_id,
            aggregation_keys=aggregation_keys,
            id=id,
        )

    def get_aggregation_key(self) -> str:
        key = ""
        for _field in self.aggregation_keys:
            if not hasattr(self, _field):
                raise ValueError(f"SharedMemoryEntry does not have the field {_field}")
            key += f"{getattr(self, _field)}_"
        return key.strip("_")

    def __repr__(self):
        return f"SharedMemoryEntry: {self.type} by {self.by} in {self.scope} {self.scope_id}\n{self.content}"

    def __str__(self):
        return self.__repr__()

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "by": self.by,
            "content": self.content,
            "scope": self.scope,
            "scope_id": self.scope_id,
            "unique_key_fields": self.aggregation_keys,
            "id": self.id,
        }
