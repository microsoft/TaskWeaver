from __future__ import annotations

import os
from typing import Dict, Optional

from taskweaver.ces.common import Client, ExecutionResult, KernelModeType, Manager


class SubProcessClient(Client):
    def __init__(
        self,
        mgr: SubProcessManager,
        session_id: str,
        env_id: str,
        session_dir: str,
        cwd: str,
    ) -> None:
        self.mgr = mgr
        self.started = False
        self.env_id = env_id
        self.session_id = session_id
        self.cwd = cwd
        self.session_dir = session_dir

    def start(self) -> None:
        self.mgr.env.start_session(self.session_id, session_dir=self.session_dir, cwd=self.cwd)

    def stop(self) -> None:
        self.mgr.env.stop_session(self.session_id)

    def load_plugin(
        self,
        plugin_name: str,
        plugin_code: str,
        plugin_config: Dict[str, str],
    ) -> None:
        self.mgr.env.load_plugin(
            self.session_id,
            plugin_name,
            plugin_code,
            plugin_config,
        )

    def test_plugin(self, plugin_name: str) -> None:
        self.mgr.env.test_plugin(self.session_id, plugin_name)

    def update_session_var(self, session_var_dict: Dict[str, str]) -> None:
        self.mgr.env.update_session_var(self.session_id, session_var_dict)

    def execute_code(self, exec_id: str, code: str) -> ExecutionResult:
        return self.mgr.env.execute_code(self.session_id, code=code, exec_id=exec_id)


class SubProcessManager(Manager):
    def __init__(
        self,
        env_id: Optional[str] = None,
        env_dir: Optional[str] = None,
        kernel_mode: KernelModeType = "local",
        custom_image: Optional[str] = None,
    ) -> None:
        from taskweaver.ces.environment import Environment, EnvMode

        env_id = env_id or os.getenv("TASKWEAVER_ENV_ID", "local")
        env_dir = env_dir or os.getenv(
            "TASKWEAVER_ENV_DIR",
            os.path.realpath(os.getcwd()),
        )
        self.kernel_mode: KernelModeType = kernel_mode
        if self.kernel_mode == "local":
            env_mode = EnvMode.Local
        elif self.kernel_mode == "container":
            env_mode = EnvMode.Container
        else:
            raise ValueError(f"Invalid kernel mode: {self.kernel_mode}, expected 'local' or 'container'.")
        self.env = Environment(
            env_id,
            env_dir,
            env_mode=env_mode,
            custom_image=custom_image,
        )

    def initialize(self) -> None:
        # no need to initialize the manager itself
        pass

    def clean_up(self) -> None:
        # no need to clean up the manager itself
        pass

    def get_session_client(
        self,
        session_id: str,
        env_id: Optional[str] = None,
        session_dir: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Client:
        cwd = cwd or os.getcwd()
        session_dir = session_dir or os.path.join(self.env.env_dir, session_id)
        return SubProcessClient(
            self,
            session_id=session_id,
            env_id=self.env.id,
            session_dir=session_dir,
            cwd=cwd,
        )

    def get_kernel_mode(self) -> KernelModeType:
        return self.kernel_mode
