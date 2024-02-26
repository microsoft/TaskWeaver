from typing import Literal

from taskweaver.ces.common import Manager
from taskweaver.ces.environment import Environment, EnvMode
from taskweaver.ces.manager.sub_proc import SubProcessManager


def code_execution_service_factory(
    env_dir: str,
    kernel_mode: Literal["SubProcess", "Container"] = "SubProcess",
    port_start: int = 49500,
    port_end: int = 49999,
) -> Manager:
    return SubProcessManager(
        env_dir=env_dir,
        kernel_mode=kernel_mode,
        port_start=port_start,
        port_end=port_end,
    )
