from os import path

from injector import inject

from taskweaver.config.module_config import ModuleConfig


class WorkspaceConfig(ModuleConfig):
    def _configure(self):
        self._set_name("workspace")

        self.mode = self._get_str("mode", "local")
        self.workspace_path = self._get_path(
            "workspace_path",
            path.join(
                self.src.app_base_path,
                "workspace",
            ),
        )


class Workspace(object):
    @inject
    def __init__(self, config: WorkspaceConfig) -> None:
        self.config = config

    def get_session_dir(self, session_id: str) -> str:
        return path.join(self.config.workspace_path, "sessions", session_id)
