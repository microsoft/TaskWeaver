import inspect
import os.path

from injector import inject

from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.utils import read_yaml


class Role:
    @inject
    def __init__(
        self,
        config: ModuleConfig,
        logger: TelemetryLogger,
        event_emitter: SessionEventEmitter,
    ):
        self.config = config
        self.logger = logger
        self.event_emitter = event_emitter

        self.name = self.config.name

        role_meta_data_file = os.path.splitext(self.get_child_file_path())[0] + ".yaml"

        if os.path.exists(role_meta_data_file):
            self.meta_data = read_yaml(role_meta_data_file)
        else:
            self.meta_data = None

        self.intro = self.meta_data["intro"] if self.meta_data is not None else None
        self.alias = self.meta_data["alias"] if self.meta_data is not None else None

    def get_child_file_path(self):
        child_class = self.__class__
        child_module = inspect.getmodule(child_class)
        child_file_path = os.path.abspath(child_module.__file__)

        return child_file_path

    def get_intro(self) -> str:
        return self.intro

    def get_alias(self) -> str:
        return self.alias

    def reply(self, memory: Memory, **kwargs) -> Post:
        pass
