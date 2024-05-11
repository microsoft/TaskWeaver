import copy
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, NamedTuple, Optional

AppConfigSourceType = Literal["override", "env", "json", "app", "default"]
AppConfigValueType = Literal["str", "int", "float", "bool", "list", "enum", "path", "dict"]


class AppConfigSourceValue(NamedTuple):
    source: AppConfigSourceType
    value: Any


@dataclass
class AppConfigItem:
    name: str
    value: Any
    type: AppConfigValueType
    sources: List[AppConfigSourceValue]


class AppConfigSource:
    _bool_str_map: Dict[str, bool] = {
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "1": True,
        "0": False,
    }
    _null_str_set = set(["null", "none", "nil"])

    _path_app_base_ref: str = "${AppBaseDir}"
    _path_module_base_ref: str = "${ModuleBaseDir}"

    def __init__(
        self,
        config_file_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        app_base_path: Optional[str] = None,
    ):
        self.module_base_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), ".."),
        )
        self.app_base_path = os.path.realpath(".") if app_base_path is None else os.path.realpath(app_base_path)

        self.config: Dict[str, AppConfigItem] = {}
        self.config_file_path = config_file_path
        self.in_memory_store = config
        self.override_store: Dict[str, Any] = {}
        if config_file_path is not None:
            self.json_file_store = self._load_config_from_json(config_file_path)
        else:
            self.json_file_store = {}

    def _load_config_from_json(self, config_file_path: str) -> Dict[str, Any]:
        self.config_file_path = config_file_path
        assert os.path.exists(
            self.config_file_path,
        ), f"Config file {config_file_path} does not exist"
        try:
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                self.json_file_store = json.load(f)
                return self.json_file_store
        except Exception as e:
            print("Failed to load config file", config_file_path)
            raise e

    def _get_config_value(
        self,
        var_name: str,
        var_type: AppConfigValueType,
        default_value: Optional[Any] = None,
        required: bool = True,
    ) -> Optional[Any]:
        self.set_config_value(var_name, var_type, default_value, "default")

        if var_name in self.override_store:
            val = self.override_store.get(var_name, None)
            if val is not None:
                return val

        if self.in_memory_store is not None:
            val = self.in_memory_store.get(var_name, None)
            if val is not None:
                return val
        # env var has the format of upper case with dot replaced by underscore
        # e.g., llm.api_base -> LLM_API_BASE
        val = os.environ.get(var_name.upper().replace(".", "_"), None)
        if val is not None:
            if val.lower() in AppConfigSource._null_str_set:
                return None
            else:
                return val

        if var_name in self.json_file_store.keys():
            return self.json_file_store.get(var_name, default_value)

        if default_value is not None:
            return default_value

        if not required:
            return None

        raise ValueError(f"Config value {var_name} is not found")

    def set_config_value(
        self,
        var_name: str,
        var_type: AppConfigValueType,
        value: Optional[Any],
        source: AppConfigSourceType = "app",
    ):
        if not (var_name in self.config.keys()):
            self.config[var_name] = AppConfigItem(
                name=var_name,
                value=value,
                type=var_type,
                sources=[AppConfigSourceValue(source=source, value=value)],
            )
        else:
            new_sources = [s for s in self.config[var_name].sources if s.source != source]
            new_sources.append(AppConfigSourceValue(source=source, value=value))
            new_sources.sort(key=lambda s: s.source)
            self.config[var_name].sources = new_sources
            self.config[var_name].value = value
        if source == "override":
            self.override_store[var_name] = value

    def get_bool(
        self,
        var_name: str,
        default_value: Optional[bool] = None,
        required: bool = True,
    ) -> bool:
        val = self._get_config_value(var_name, "bool", default_value, required)

        if isinstance(val, bool):
            return val
        elif str(val).lower() in AppConfigSource._bool_str_map.keys():
            return AppConfigSource._bool_str_map[str(val).lower()]
        elif val is None and default_value is None and required:
            raise ValueError(f"Config value {var_name} is not found")
        else:
            raise ValueError(
                f"Invalid boolean config value {val}, "
                f"only support transforming {AppConfigSource._bool_str_map.keys()}",
            )

    def get_str(
        self,
        var_name: str,
        default_value: Optional[str] = None,
        required: bool = True,
    ) -> str:
        val = self._get_config_value(var_name, "str", default_value, required)

        if val is None and default_value is None and required is False:
            return None  # type: ignore

        return str(val)

    def get_enum(
        self,
        key: str,
        options: List[str],
        default: Optional[str] = None,
        required: bool = True,
    ) -> str:
        val = self._get_config_value(key, "enum", default, required)
        if val not in options and val is not None:
            raise ValueError(f"Invalid enum config value {val}, options are {options}")

        if val is None and default is None and required:
            raise ValueError("Config value {key} is not found")

        return val

    def get_list(self, key: str, default: Optional[List[Any]] = None) -> List[Any]:
        val = self._get_config_value(key, "list", default)
        if isinstance(val, list):
            return val
        elif isinstance(val, str):
            return re.split(r"\s*,\s*", val)
        elif val is None:
            return []
        else:
            raise ValueError(f"Invalid list config value {val}")

    def get_float(
        self,
        var_name: str,
        default_value: Optional[float] = None,
    ) -> float:
        val = self._get_config_value(var_name, "int", default_value)
        if isinstance(val, float):
            return val
        if isinstance(val, int):
            return float(val)
        else:
            try:
                any_val: Any = val
                float_number = float(any_val)
                return float_number
            except ValueError:
                raise ValueError(
                    f"Invalid digit config value {val}, " f"only support transforming to int or float",
                )

    def get_int(
        self,
        var_name: str,
        default_value: Optional[int] = None,
    ) -> int:
        val = self._get_config_value(var_name, "int", default_value)
        if isinstance(val, int):
            return val
        if isinstance(val, float):
            return int(val)
        else:
            try:
                any_val: Any = val
                int_number = int(any_val)
                return int_number
            except ValueError:
                raise ValueError(
                    f"Invalid digit config value {val}, " f"only support transforming to int or float",
                )

    def get_path(
        self,
        var_name: str,
        default_value: Optional[str] = None,
    ) -> str:
        if default_value is not None:
            default_value = self.normalize_path_val_config(default_value)

        val = self._get_config_value(var_name, "path", default_value)
        if val is None and default_value is None:
            raise ValueError(f"Invalid path config value {val}")
        return self.decode_path_val_config(str(val))

    def normalize_path_val_config(self, path_val: str) -> str:
        if path_val.startswith(self.app_base_path):
            path_val = path_val.replace(self.app_base_path, self._path_app_base_ref, 1)
        if path_val.startswith(self.module_base_path):
            path_val = path_val.replace(
                self.module_base_path,
                self._path_module_base_ref,
                1,
            )
        # if path is under user's home, normalize to relative to user
        user_home = os.path.expanduser("~")
        if path_val.startswith(user_home):
            path_val = path_val.replace(user_home, "~", 1)

        # normalize path separator
        path_val = path_val.replace(os.path.sep, "/")

        return path_val

    def decode_path_val_config(self, path_config: str) -> str:
        # normalize path separator
        path_config = path_config.replace("/", os.path.sep)

        if path_config.startswith(self._path_app_base_ref):
            path_config = path_config.replace(
                self._path_app_base_ref,
                self.app_base_path,
                1,
            )
        if path_config.startswith(self._path_module_base_ref):
            path_config = path_config.replace(
                self._path_module_base_ref,
                self.module_base_path,
                1,
            )

        if path_config.startswith("~"):
            path_config = os.path.expanduser(path_config)
        return path_config

    def get_dict(self, key: str, default: Optional[dict] = None) -> dict:
        val = self._get_config_value(key, "dict", default)
        if isinstance(val, dict):
            return val
        else:
            raise ValueError(f"Invalid dict config value {val}")

    def clone(self):
        return copy.deepcopy(self)
