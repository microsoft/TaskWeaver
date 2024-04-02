from os import listdir, path
from typing import Any, Dict, Optional, Tuple

from injector import Injector

from taskweaver.app.session_manager import SessionManager, SessionManagerModule
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.plugin import PluginModule
from taskweaver.module.execution_service import ExecutionServiceModule
from taskweaver.role.role import RoleModule

# if TYPE_CHECKING:
from taskweaver.session.session import Session


class TaskWeaverApp(object):
    def __init__(
        self,
        app_dir: Optional[str] = None,
        use_local_uri: Optional[bool] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the TaskWeaver app.
        :param app_dir: The project directory.
        :param use_local_uri: Whether to use local URI for artifacts.
        :param config: The configuration.
        :param kwargs: The additional arguments.
        """

        app_dir, is_valid, _ = TaskWeaverApp.discover_app_dir(app_dir)
        app_config_file = path.join(app_dir, "taskweaver_config.json") if is_valid else None
        config = {
            **(config or {}),
            **(kwargs or {}),
        }
        if use_local_uri is not None:
            config["use_local_uri"] = use_local_uri

        config_src = AppConfigSource(
            config_file_path=app_config_file,
            config=config,
            app_base_path=app_dir,
        )
        self.app_injector = Injector(
            [SessionManagerModule, PluginModule, LoggingModule, ExecutionServiceModule, RoleModule],
        )
        self.app_injector.binder.bind(AppConfigSource, to=config_src)
        self.session_manager: SessionManager = self.app_injector.get(SessionManager)
        self._init_app_modules()

    def get_session(
        self,
        session_id: Optional[str] = None,
        prev_round_id: Optional[str] = None,
    ) -> Session:
        """
        Get the session. Return a new session if the session ID is not provided.
        :param session_id: The session ID.
        :param prev_round_id: The previous round ID.
        :return: The session.
        """
        return self.session_manager.get_session(session_id, prev_round_id)

    def stop(self) -> None:
        """
        Stop the TaskWeaver app. This function must be called before the app exits.
        """
        self.session_manager.stop_all_sessions()

    @staticmethod
    def discover_app_dir(
        app_dir: Optional[str] = None,
    ) -> Tuple[str, bool, bool]:
        """
        Discover the app directory from the given path or the current working directory.
        """

        def validate_app_config(workspace: str) -> bool:
            config_path = path.join(workspace, "taskweaver_config.json")
            if not path.exists(config_path):
                return False
            # TODO: read, parse and validate config
            return True

        def is_dir_valid(dir: str) -> bool:
            return path.exists(dir) and path.isdir(dir) and validate_app_config(dir)

        def is_empty(dir: str) -> bool:
            return not path.exists(dir) or (path.isdir(dir) and len(listdir(dir)) == 0)

        if app_dir is not None:
            app_dir = path.abspath(app_dir)
            return app_dir, is_dir_valid(app_dir), is_empty(app_dir)
        else:
            cwd = path.abspath(".")
            cur_dir = cwd
            while True:
                if is_dir_valid(cur_dir):
                    return cur_dir, True, False

                next_path = path.abspath(path.join(cur_dir, ".."))
                if next_path == cur_dir:
                    return cwd, False, is_empty(cwd)
                cur_dir = next_path

    def _init_app_modules(self) -> None:
        from taskweaver.llm import LLMApi

        self.app_injector.get(LLMApi)
