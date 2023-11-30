import contextlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Tuple

LogErrorLevel = Literal["info", "warning", "error"]
ArtifactType = Literal["chart", "image", "df", "file", "txt", "svg", "html"]


class PluginContext(ABC):
    """
    interface for API to interact with execution environment of plugin

    The runtime will provide an implementation of this interface to the plugin.
    Plugin could use the API provded withotu need to implement this interface.
    """

    @property
    @abstractmethod
    def env_id(self) -> str:
        """get the environment id of the plugin"""
        ...

    @property
    @abstractmethod
    def session_id(self) -> str:
        """get the session id of the plugin"""
        ...

    @property
    @abstractmethod
    def execution_id(self) -> str:
        """get the execution id of the plugin"""
        ...

    @abstractmethod
    def add_artifact(
        self,
        name: str,
        file_name: str,
        type: ArtifactType,
        val: Any,
        desc: Optional[str] = None,
    ) -> str:
        """
        add an artifact to the execution context

        :param name: the name of the artifact
        :param file_name: the name of the file
        :param type: the type of the artifact
        :param val: the value of the artifact
        :param desc: the description of the artifact

        :return: the id of the artifact
        """
        ...

    @abstractmethod
    def create_artifact_path(
        self,
        name: str,
        file_name: str,
        type: ArtifactType,
        desc: str,
    ) -> Tuple[str, str]:
        """
        create a path for an artifact and the plugin can use this path to save the artifact.
        This methods is provided for the plugin to save the artifact by itself rather than saving by the runtime,
        for general cases when the file content could be passed directly, the plugin should use add_artifact instead.

        :param name: the name of the artifact
        :param file_name: the name of the file
        :param type: the type of the artifact
        :param desc: the description of the artifact

        :return: the id and the path of the artifact
        """
        ...

    @abstractmethod
    def get_session_var(
        self,
        variable_name: str,
        default: Optional[str],
    ) -> Optional[str]:
        """
        get a session variable from the context

        :param variable_name: the name of the variable
        :param default: the default value of the variable

        :return: the value of the variable
        """
        ...

    @abstractmethod
    def log(self, level: LogErrorLevel, tag: str, message: str) -> None:
        """log a message from the plugin"""

    @abstractmethod
    def get_env(self, plugin_name: str, variable_name: str) -> str:
        """get an environment variable from the context"""


class TestPluginContxt(PluginContext):
    """
    This plugin context is used for testing purpose.
    """

    def __init__(self, temp_dir: str) -> None:
        self._session_id = "test"
        self._env_id = "test"
        self._execution_id = "test"
        self._logs: List[Tuple[LogErrorLevel, str, str]] = []
        self._env: Dict[str, str] = {}
        self._session_var: Dict[str, str] = {}
        self._temp_dir = temp_dir
        self._artifacts: List[Dict[str, str]] = []

    @property
    def env_id(self) -> str:
        return "test"

    @property
    def session_id(self) -> str:
        return "test"

    @property
    def execution_id(self) -> str:
        return "test"

    def add_artifact(
        self,
        name: str,
        file_name: str,
        type: ArtifactType,
        val: Any,
        desc: Optional[str] = None,
    ) -> str:
        id = f"test_artifact_id_{len(self._artifacts)}"
        self._artifacts.append(
            {
                "id": id,
                "name": name,
                "file_name": file_name,
                "type": type,
                "desc": desc or "",
            },
        )
        return id

    def create_artifact_path(
        self,
        name: str,
        file_name: str,
        type: ArtifactType,
        desc: str,
    ) -> Tuple[str, str]:
        id = f"test_artifact_id_{len(self._artifacts)}"
        self._artifacts.append(
            {
                "id": id,
                "name": name,
                "file_name": file_name,
                "type": type,
                "desc": desc or "",
            },
        )
        return id, self._temp_dir + "/" + file_name

    def log(self, level: LogErrorLevel, tag: str, message: str) -> None:
        return self._logs.append((level, tag, message))

    def get_env(self, plugin_name: str, variable_name: str) -> str:
        return self._env[plugin_name + "_" + variable_name]

    def get_session_var(
        self,
        variable_name: str,
        default: Optional[str],
    ) -> Optional[str]:
        return self._session_var.get(variable_name, default)


@contextlib.contextmanager
def temp_context(workspace_dir: Optional[str] = None):
    import os
    import shutil
    import tempfile
    import uuid

    if workspace_dir is None:
        workspace_dir = tempfile.mkdtemp()
    else:
        workspace_dir = os.path.join(workspace_dir, str(uuid.uuid4()))
        os.makedirs(workspace_dir)

    try:
        yield TestPluginContxt(workspace_dir)
    finally:
        shutil.rmtree(workspace_dir)
