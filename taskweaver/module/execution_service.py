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


class ExecutionServiceModule(Module):
    def __init__(self) -> None:
        self.manager: Optional[Manager] = None

    @provider
    def provide_executor_manager(self, config: ExecutionServiceConfig) -> Manager:
        if self.manager is None:
            self.manager = code_execution_service_factory(
                config.env_dir,
            )
        return self.manager
