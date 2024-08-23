from typing import Literal

from taskweaver.ces.common import Manager
from taskweaver.ces.manager.defer import DeferredManager
from taskweaver.ces.manager.sub_proc import SubProcessManager


def code_execution_service_factory(
    env_dir: str,
    kernel_mode: Literal["local", "container"] = "local",
) -> Manager:
    def sub_proc_manager_factory() -> SubProcessManager:
        return SubProcessManager(
            env_dir=env_dir,
            kernel_mode=kernel_mode,
        )

    return DeferredManager(
        kernel_mode=kernel_mode,
        manager_factory=sub_proc_manager_factory,
    )
