from taskweaver.ces.common import Manager
from taskweaver.ces.manager.sub_proc import SubProcessManager


def code_execution_service_factory(env_dir: str) -> Manager:
    return SubProcessManager(env_dir=env_dir)
