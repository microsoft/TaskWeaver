import inspect
import os.path
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional, Tuple, Union

from injector import Module, inject, provider

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.misc.component_registry import ComponentRegistry
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.module.tracing import Tracing
from taskweaver.utils import import_module, read_yaml


@dataclass
class RoleEntry:
    name: str
    alias: str
    module: type
    intro: str

    @staticmethod
    def from_yaml_file(file_path: str):
        data = read_yaml(file_path)
        name = os.path.basename(file_path).split(".")[0]  # set role name as YAML file name without extension
        module_path, class_name = data["module"].rsplit(".", 1)
        module = import_module(module_path)
        cls = getattr(module, class_name)
        return RoleEntry(
            name=name,
            alias=data["alias"],
            module=cls,
            intro=data["intro"],
        )


class RoleConfig(ModuleConfig):
    @inject
    def __init__(self, src: AppConfigSource) -> None:
        self.src: AppConfigSource = src
        self._set_role_name()
        self._configure()

    def _set_role_name(self):
        child_class = self.__class__
        file_name = inspect.getfile(child_class)
        role_name = os.path.basename(file_name).split(".")[0]
        self._set_name(role_name)


class Role:
    @inject
    def __init__(
        self,
        config: ModuleConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        role_entry: Optional[RoleEntry] = None,
    ):
        """
        The base class for all roles.
        """
        self.config = config
        self.logger = logger
        self.tracing = tracing
        self.event_emitter = event_emitter

        self.role_entry = role_entry

        self.name = self.config.name

        if role_entry is not None:
            parent_dir_name = os.path.basename(os.path.dirname(inspect.getfile(self.__class__)))
            assert self.name == parent_dir_name == role_entry.name, (
                f"Role name {self.name}, role entry name {role_entry.name}, "
                f"and parent dir name {parent_dir_name} should be the same"
            )

        self.alias: str = self.role_entry.alias if self.role_entry else ""
        self.intro: str = self.role_entry.intro if self.role_entry else ""

    def get_intro(self) -> str:
        return self.intro

    def get_alias(self) -> str:
        return self.alias

    def set_alias(self, alias: str) -> None:
        self.alias = alias

    def reply(self, memory: Memory, **kwargs: ...) -> Post:
        raise NotImplementedError()

    def close(self) -> None:
        self.logger.info(f"{self.alias} closed successfully")


class RoleModuleConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("role")
        module_base_path = self.src.module_base_path
        self.ext_role_base_path = self._get_path(
            "base_path",
            os.path.join(
                module_base_path,
                "ext_role",
            ),
        )
        self.code_interpreter_base_path = self._get_path(
            "code_interpreter_base_path",
            os.path.join(
                module_base_path,
                "code_interpreter",
            ),
        )


class RoleRegistry(ComponentRegistry[RoleEntry]):
    def __init__(
        self,
        file_glob: Union[str, List[str]],
        ttl: Optional[timedelta] = None,
    ) -> None:
        super().__init__(file_glob, ttl)

    def _load_component(self, path: str) -> Tuple[str, RoleEntry]:
        entry: Optional[RoleEntry] = RoleEntry.from_yaml_file(file_path=path)
        assert entry, f"failed to loading role from {path}"
        return entry.name, entry

    def get_role_name_list(self):
        return [entry.name for entry in self.get_list()]


class RoleModule(Module):
    @provider
    def provide_role_registries(
        self,
        config: RoleModuleConfig,
    ) -> RoleRegistry:
        import os

        glob_strings: List[str] = []
        for sub_dir in os.listdir(config.ext_role_base_path):
            sub_dir_path = os.path.join(config.ext_role_base_path, sub_dir)
            if os.path.isdir(sub_dir_path):
                glob_strings.append(os.path.join(sub_dir_path, "*.role.yaml"))

        for sub_dir in os.listdir(config.code_interpreter_base_path):
            sub_dir_path = os.path.join(config.code_interpreter_base_path, sub_dir)
            if os.path.isdir(sub_dir_path):
                glob_strings.append(os.path.join(sub_dir_path, "*.role.yaml"))
        return RoleRegistry(
            glob_strings,
            ttl=timedelta(minutes=5),
        )
