from __future__ import annotations

import dataclasses
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from taskweaver.plugin.context import ArtifactType


@dataclass
class EnvPlugin:
    name: str
    impl: str  # file content for the implementation
    config: Optional[Dict[str, str]]
    loaded: bool


def get_id(length: int = 6, prefix: Optional[str] = None) -> str:
    """Get a random id with the given length and prefix."""
    id = secrets.token_hex(length)
    if prefix is not None:
        return f"{prefix}-{id}"
    return id


@dataclass
class ExecutionArtifact:
    name: str = ""
    type: ArtifactType = "file"
    mime_type: str = ""
    original_name: str = ""
    file_name: str = ""
    file_content: str = ""
    file_content_encoding: Literal["str", "base64"] = "str"
    preview: str = ""

    @staticmethod
    def from_dict(d: Dict[str, str]) -> ExecutionArtifact:
        return ExecutionArtifact(
            name=d["name"],
            # TODO: check artifacts type
            type=d["type"],  # type: ignore
            mime_type=d["mime_type"],
            original_name=d["original_name"],
            file_name=d["file_name"],
            file_content=d["file_content"],
            preview=d["preview"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class ExecutionResult:
    execution_id: str
    code: str

    is_success: bool = False
    error: Optional[str] = None

    output: Union[str, List[Tuple[str, str]]] = ""
    stdout: List[str] = dataclasses.field(default_factory=list)
    stderr: List[str] = dataclasses.field(default_factory=list)

    log: List[Tuple[str, str, str]] = dataclasses.field(default_factory=list)
    artifact: List[ExecutionArtifact] = dataclasses.field(default_factory=list)


class Client(ABC):
    """
    Client is the interface for the execution client.
    """

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def load_plugin(
        self,
        plugin_name: str,
        plugin_code: str,
        plugin_config: Dict[str, str],
    ) -> None:
        ...

    @abstractmethod
    def test_plugin(self, plugin_name: str) -> None:
        ...

    @abstractmethod
    def update_session_var(self, session_var_dict: Dict[str, str]) -> None:
        ...

    @abstractmethod
    def execute_code(self, exec_id: str, code: str) -> ExecutionResult:
        ...


class Manager(ABC):
    """
    Manager is the interface for the execution manager.
    """

    @abstractmethod
    def initialize(self) -> None:
        ...

    @abstractmethod
    def clean_up(self) -> None:
        ...

    @abstractmethod
    def get_session_client(
        self,
        session_id: str,
        env_id: Optional[str] = None,
        session_dir: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Client:
        ...
