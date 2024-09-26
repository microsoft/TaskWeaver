from typing import Literal

RoleName = str
RoundState = Literal["finished", "failed", "created"]
SharedMemoryEntryType = Literal["plan", "experience_sub_path", "example_sub_path"]
SharedMemoryEntryScope = Literal["round", "conversation"]
