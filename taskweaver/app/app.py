from os import path
from typing import Any, Dict, Optional, Tuple

from injector import Injector

from taskweaver.app.session_manager import SessionManager, SessionManagerModule
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.plugin import PluginModule
from taskweaver.module.execution_service import ExecutionServiceModule
from taskweaver.role.role import RoleModule
from taskweaver.session.session import Session


def _cleanup_existing_servers(port: int = 8000) -> Optional[int]:
    """Check for and kill any existing server processes on the specified port.

    This is called at TaskWeaver startup to ensure a clean state.

    Args:
        port: The port to check for existing servers.

    Returns:
        The PID of the killed server, or None if no server was found.
    """
    import os
    import platform
    import signal
    import subprocess
    import time

    def get_pid_on_port(port: int) -> Optional[int]:
        """Get the PID of the process listening on the port."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                for line in result.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            return int(parts[-1])
            else:
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout.strip():
                    return int(result.stdout.strip().split("\n")[0])
        except Exception:
            pass
        return None

    pid = get_pid_on_port(port)
    if pid is None:
        return None

    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
        else:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        # Wait for port to be released
        for _ in range(10):
            if get_pid_on_port(port) is None:
                return pid
            time.sleep(0.5)

        return pid
    except Exception:
        return None


class TaskWeaverApp(object):
    def __init__(
        self,
        app_dir: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the TaskWeaver app.
        :param app_dir: The project directory.
        :param config: The configuration.
        :param kwargs: The additional arguments.
        """

        app_dir, is_valid, _ = TaskWeaverApp.discover_app_dir(app_dir)
        app_config_file = path.join(app_dir, "taskweaver_config.json") if is_valid else None
        config = {
            **(config or {}),
            **(kwargs or {}),
        }

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
        from taskweaver.utils.app_utils import discover_app_dir

        return discover_app_dir(app_dir)

    def _init_app_modules(self) -> None:
        from taskweaver.llm import LLMApi

        self.app_injector.get(LLMApi)
