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
        self.kernel_mode = self._get_str(
            "kernel_mode",
            "container",
        )
        if self.kernel_mode == "local":
            print(
                "TaskWeaver is running in the `local` mode. This implies that "
                "the code execution service will run on the same machine as the TaskWeaver server. "
                "For better security, it is recommended to run the code execution service in the `container` mode. "
                "More information can be found in the documentation "
                "(https://microsoft.github.io/TaskWeaver/docs/advanced/code_execution).",
            )


class ExecutionServiceModule(Module):
    def __init__(self) -> None:
        self.manager: Optional[Manager] = None

    @provider
    def provide_executor_manager(self, config: ExecutionServiceConfig) -> Manager:
        if self.manager is None:
            self.manager = code_execution_service_factory(
                env_dir=config.env_dir,
                kernel_mode=config.kernel_mode,
            )
        return self.manager
