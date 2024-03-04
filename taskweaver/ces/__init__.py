from typing import Literal

from taskweaver.ces.common import Manager
from taskweaver.ces.environment import Environment, EnvMode
from taskweaver.ces.manager.sub_proc import SubProcessManager


def code_execution_service_factory(
    env_dir: str,
    kernel_mode: Literal["local", "container"] = "local",
) -> Manager:
    return SubProcessManager(
        env_dir=env_dir,
        kernel_mode=kernel_mode,
    )
