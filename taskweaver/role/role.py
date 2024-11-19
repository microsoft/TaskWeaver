import inspect
import os.path
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Literal, Optional, Set, Tuple, Union

from injector import Module, inject, provider

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Conversation, Memory, Post
from taskweaver.memory.experience import Experience, ExperienceGenerator
from taskweaver.misc.component_registry import ComponentRegistry
from taskweaver.misc.example import load_examples
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
        super().__init__(src)
        self.src: AppConfigSource = src
        self._set_role_name()

        self.use_experience = self._get_bool(
            "use_experience",
            False,
        )
        self.experience_dir = self._get_path(
            "experience_dir",
            os.path.join(
                self.src.app_base_path,
                "experience",
            ),
        )
        self.dynamic_experience_sub_path = self._get_bool(
            "dynamic_experience_sub_path",
            False,
        )

        self.use_example = self._get_bool(
            "use_example",
            True,
        )
        self.example_base_path = self._get_path(
            "example_base_path",
            os.path.join(
                self.src.app_base_path,
                "examples",
                f"{self.name}_examples",
            ),
        )
        self.dynamic_example_sub_path = self._get_bool(
            "dynamic_example_sub_path",
            False,
        )

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
        config: RoleConfig,
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

        self.experiences: List[Experience] = []
        self.experience_generator: Optional[ExperienceGenerator] = None
        self.experience_loaded_from: Optional[str] = None

        self.examples: List[Conversation] = []
        self.example_loaded_from: Optional[str] = None

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

    def format_experience(
        self,
        template: str,
    ) -> str:
        return (
            self.experience_generator.format_experience_in_prompt(template, self.experiences)
            if self.config.use_experience
            else ""
        )

    def prepare_loading(
        self,
        use_flag: bool,
        dynamic_sub_path: bool,
        base_path: str,
        memory: Optional[Memory],
        loaded_from_attr: str,
        item_type: Literal["experience", "example"],
    ) -> Optional[str]:
        """Prepare for loading by checking configurations and memory, and return load_from path if applicable."""
        if not use_flag:
            setattr(self, f"{item_type}s", [])
            return None

        if not os.path.exists(base_path):
            raise FileNotFoundError(
                f"The default {item_type} base path {base_path} does not exist."
                f"The original {item_type} base paths have been changed to `{item_type}s` folder."
                f"Please migrate the {item_type}s to the new base path.",
            )

        sub_path = ""
        if dynamic_sub_path:
            assert memory is not None, f"Memory should be provided when dynamic_{item_type}_sub_path is True"
            sub_paths = memory.get_shared_memory_entries(entry_type=f"{item_type}_sub_path")
            if sub_paths:
                self.tracing.set_span_attribute(f"{item_type}_sub_path", str(sub_paths))
                # todo: handle multiple sub paths
                sub_path = sub_paths[0].content
            else:
                self.logger.info(f"No {item_type} sub path found in memory.")
                setattr(self, f"{item_type}s", [])
                return None

        load_from = os.path.join(base_path, sub_path)
        if getattr(self, loaded_from_attr) is not None and getattr(self, loaded_from_attr) == load_from:
            self.logger.info(f"{item_type.capitalize()} already loaded from {load_from}.")
            return None

        setattr(self, loaded_from_attr, load_from)
        return sub_path

    def role_load_experience(
        self,
        query: str,
        memory: Optional[Memory] = None,
    ) -> None:
        sub_path = self.prepare_loading(
            self.config.use_experience,
            self.config.dynamic_experience_sub_path,
            self.config.experience_dir,
            memory,
            "experience_loaded_from",
            "experience",
        )
        if sub_path is None:
            return

        if self.experience_generator is None:
            raise ValueError(
                "Experience generator is not initialized. Each role instance should have its own generator.",
            )

        self.experience_generator.set_experience_dir(self.config.experience_dir)
        self.experience_generator.set_sub_path(sub_path)
        self.experience_generator.refresh()
        self.experience_generator.load_experience()
        self.logger.info(
            "Experience loaded successfully for {}, there are {} experiences with filter [{}]".format(
                self.alias,
                len(self.experience_generator.experience_list),
                sub_path,
            ),
        )

        experiences = self.experience_generator.retrieve_experience(query)
        self.logger.info(f"Retrieved {len(experiences)} experiences for query [{query}]")
        self.experiences = [exp for exp, _ in experiences]

    def role_load_example(
        self,
        role_set: Set[str],
        memory: Optional[Memory] = None,
    ) -> None:
        sub_path = self.prepare_loading(
            self.config.use_example,
            self.config.dynamic_example_sub_path,
            self.config.example_base_path,
            memory,
            "example_loaded_from",
            "example",
        )
        if sub_path is None:
            return

        self.examples = load_examples(
            folder=self.config.example_base_path,
            sub_path=sub_path,
            role_set=role_set,
        )
        self.logger.info(
            "Example loaded successfully for {}, there are {} examples with filter [{}]".format(
                self.alias,
                len(self.examples),
                sub_path,
            ),
        )


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
