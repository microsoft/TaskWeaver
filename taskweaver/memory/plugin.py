import os
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from injector import Module, provider

from taskweaver.config.module_config import ModuleConfig
from taskweaver.misc.component_registry import ComponentRegistry
from taskweaver.utils import read_yaml, validate_yaml


@dataclass
class PluginParameter:
    """PluginParameter is the data structure for plugin parameters (including arguments and return values.)"""

    name: str = ""
    type: str = "None"
    required: bool = False
    description: Optional[str] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return PluginParameter(
            name=d["name"],
            description=d["description"],
            required=d["required"] if "required" in d else False,
            type=d["type"] if "type" in d else "Any",
        )

    def format_prompt(self, indent: int = 0) -> str:
        lines: List[str] = []

        def line(cnt: str):
            lines.append(" " * indent + cnt)

        line(f"- name: {self.name}")
        line(f"  type: {self.type}")
        line(f"  required: {self.required}")
        line(f"  description: {self.description}")

        return "\n".join(lines)


@dataclass
class PluginSpec:
    """PluginSpec is the data structure for plugin specification defined in the yaml files."""

    name: str = ""
    description: str = ""
    args: List[PluginParameter] = field(default_factory=list)
    returns: List[PluginParameter] = field(default_factory=list)
    embedding: List[float] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return PluginSpec(
            name=d["name"],
            description=d["description"],
            args=[PluginParameter.from_dict(p) for p in d["parameters"]],
            returns=[PluginParameter.from_dict(p) for p in d["returns"]],
            embedding=[],
        )

    def format_prompt(self) -> str:
        def normalize_type(t: str) -> str:
            if t.lower() == "string":
                return "str"
            if t.lower() == "integer":
                return "int"
            return t

        def normalize_description(d: str) -> str:
            d = d.strip().replace("\n", "\n# ")
            return d

        def normalize_value(v: PluginParameter) -> PluginParameter:
            return PluginParameter(
                name=v.name,
                type=normalize_type(v.type),
                required=v.required,
                description=normalize_description(v.description or ""),
            )

        def format_arg_val(val: PluginParameter) -> str:
            val = normalize_value(val)
            type_val = f"Optional[{val.type}]" if val.type != "Any" and not val.required else "Any"
            if val.description is not None:
                return f"\n# {val.description}\n{val.name}: {type_val}"
            return f"{val.name}: {type_val}"

        param_list = ",".join([format_arg_val(p) for p in self.args])

        return_type = ""
        if len(self.returns) > 1:

            def format_return_val(val: PluginParameter) -> str:
                val = normalize_value(val)
                if val.description is not None:
                    return f"\n# {val.name}: {val.description}\n{val.type}"
                return val.type

            return_type = f"Tuple[{','.join([format_return_val(r) for r in self.returns])}]"
        elif len(self.returns) == 1:
            rv = normalize_value(self.returns[0])
            if rv.description is not None:
                return_type = f"\\\n# {rv.name}: {rv.description}\n{rv.type}"
            return_type = rv.type
        else:
            return_type = "None"
        return f"# {self.description}\ndef {self.name}({param_list}) -> {return_type}:...\n"


@dataclass
class PluginEntry:
    name: str
    impl: str
    spec: PluginSpec
    config: Dict[str, Any]
    required: bool
    enabled: bool = True

    @staticmethod
    def from_yaml_file(path: str) -> Optional["PluginEntry"]:
        content = read_yaml(path)
        return PluginEntry.from_yaml_content(content)

    @staticmethod
    def from_yaml_content(content: Dict) -> Optional["PluginEntry"]:
        do_validate = False
        valid_state = False
        if do_validate:
            valid_state = validate_yaml(content, schema="plugin_schema")
        if not do_validate or valid_state:
            spec: PluginSpec = PluginSpec.from_dict(content)
            return PluginEntry(
                name=spec.name,
                impl=content.get("code", spec.name),
                spec=spec,
                config=content.get("configurations", {}),
                required=content.get("required", False),
                enabled=content.get("enabled", True),
            )
        return None

    def format_prompt(self) -> str:
        return self.spec.format_prompt()

    def to_dict(self):
        return {
            "name": self.name,
            "impl": self.impl,
            "spec": self.spec,
            "config": self.config,
            "required": self.required,
            "enabled": self.enabled,
        }


class PluginRegistry(ComponentRegistry[PluginEntry]):
    def __init__(
        self,
        file_glob: str,
        ttl: Optional[timedelta] = None,
    ) -> None:
        super().__init__(file_glob, ttl)

    def _load_component(self, path: str) -> Tuple[str, PluginEntry]:
        entry: Optional[PluginEntry] = PluginEntry.from_yaml_file(path)
        if entry is None:
            raise Exception(f"failed to loading plugin from {path}")
        if not entry.enabled:
            raise Exception(f"plugin {entry.name} is disabled")
        return entry.name, entry


class PluginModuleConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("plugin")
        app_dir = self.src.app_base_path
        self.base_path = self._get_path(
            "base_path",
            os.path.join(
                app_dir,
                "plugins",
            ),
        )


class PluginModule(Module):
    @provider
    def provide_plugin_registry(
        self,
        config: PluginModuleConfig,
    ) -> PluginRegistry:
        import os

        file_glob = os.path.join(config.base_path, "*.yaml")
        return PluginRegistry(
            file_glob=file_glob,
            ttl=timedelta(minutes=10),
        )
