import os
from typing import Optional

from injector import Module, provider

from taskweaver.ces import code_execution_service_factory
from taskweaver.ces.common import Manager
from taskweaver.config.module_config import ModuleConfig


class ExecutionServiceConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("execution_service")
        self.env_dir = self._get_path(
            "env_dir",
            os.path.join(self.src.app_base_path, "env"),
        )

        # Server configuration
        self.server_url = self._get_str(
            "server.url",
            "http://localhost:8000",
        )
        self.server_api_key = self._get_str(
            "server.api_key",
            default=None,
            required=False,
        )
        self.server_auto_start = self._get_bool(
            "server.auto_start",
            True,
        )
        self.server_container = self._get_bool(
            "server.container",
            False,
        )
        self.server_container_image = self._get_str(
            "server.container_image",
            default=None,
            required=False,
        )
        self.server_timeout = self._get_float(
            "server.timeout",
            300.0,
        )
        self.server_startup_timeout = self._get_float(
            "server.startup_timeout",
            60.0,
        )
        self.server_kill_existing = self._get_bool(
            "server.kill_existing",
            True,
        )


class ExecutionServiceModule(Module):
    def __init__(self) -> None:
        self.manager: Optional[Manager] = None

    @provider
    def provide_executor_manager(self, config: ExecutionServiceConfig) -> Manager:
        if self.manager is None:
            self.manager = code_execution_service_factory(
                env_dir=config.env_dir,
                server_url=config.server_url,
                server_api_key=config.server_api_key,
                server_auto_start=config.server_auto_start,
                server_container=config.server_container,
                server_container_image=config.server_container_image,
                server_timeout=config.server_timeout,
                server_startup_timeout=config.server_startup_timeout,
                server_kill_existing=config.server_kill_existing,
            )
        return self.manager
