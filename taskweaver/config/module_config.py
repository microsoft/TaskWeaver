from typing import Any, List, Optional

from injector import inject, singleton

from taskweaver.config.config_mgt import AppConfigSource


@singleton
class ModuleConfig(object):
    @inject
    def __init__(self, src: AppConfigSource) -> None:
        self.src: AppConfigSource = src
        self.name: str = ""
        self._configure()

    def _set_name(self, name: str) -> None:
        self.name = name

    def _config_key(self, key: str) -> str:
        return f"{self.name}.{key}" if self.name != "" else key

    def _configure(self) -> None:
        pass

    def _get_str(self, key: str, default: Optional[str], required: bool = True) -> str:
        return self.src.get_str(self._config_key(key), default, required)

    def _get_enum(self, key: str, options: List[str], default: Optional[str], required: bool = True) -> str:
        return self.src.get_enum(self._config_key(key), options, default)

    def _get_bool(self, key: str, default: Optional[bool]) -> bool:
        return self.src.get_bool(self._config_key(key), default)

    def _get_list(self, key: str, default: Optional[List[Any]]) -> List[Any]:
        return self.src.get_list(self._config_key(key), default)

    def _get_dict(self, key: str, default: Optional[dict]) -> dict:
        return self.src.get_dict(self._config_key(key), default)

    def _get_int(self, key: str, default: Optional[int]) -> int:
        return self.src.get_int(self._config_key(key), default)

    def _get_float(self, key: str, default: Optional[float]) -> float:
        return self.src.get_float(self._config_key(key), default)

    def _get_path(self, key: str, default: Optional[str]) -> str:
        return self.src.get_path(self._config_key(key), default)
