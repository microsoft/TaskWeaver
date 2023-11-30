from __future__ import annotations

import os
from typing import Dict, Optional

from taskweaver.ces.common import Client, ExecutionResult, Manager
from taskweaver.ces.environment import Environment


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
    ) -> None:
        env_id = env_id or os.getenv("TASKWEAVER_ENV_ID", "local")
        env_dir = env_dir or os.getenv(
            "TASKWEAVER_ENV_DIR",
            os.path.realpath(os.getcwd()),
        )
        self.env = Environment(env_id, env_dir)

    def initialize(self) -> None:
        pass

    def clean_up(self) -> None:
        self.env.clean_up()

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
