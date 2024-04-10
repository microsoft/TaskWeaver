from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Generic, List, Optional, Tuple, TypeVar, Union

from taskweaver.utils import glob_files

component_type = TypeVar("component_type")


class ComponentDisabledException(Exception):
    pass


class ComponentRegistry(ABC, Generic[component_type]):
    def __init__(self, file_glob: Union[str, List[str]], ttl: Optional[timedelta] = None) -> None:
        super().__init__()
        self._registry: Optional[Dict[str, component_type]] = None
        self._registry_update: datetime = datetime.fromtimestamp(0)
        self._file_glob: Union[str, List[str]] = file_glob
        self._ttl: Optional[timedelta] = ttl

    @abstractmethod
    def _load_component(self, path: str) -> Tuple[str, component_type]:
        raise NotImplementedError

    def is_available(self, freshness: Optional[timedelta] = None) -> bool:
        if self._registry is None:
            return False
        staleness = datetime.now() - self._registry_update
        if self._ttl is not None and staleness > self._ttl:
            return False
        if freshness is not None and staleness > freshness:
            return False
        return True

    def get_registry(
        self,
        force_reload: bool = False,
        freshness: Optional[timedelta] = None,
        show_error: bool = False,
    ) -> Dict[str, component_type]:
        if not force_reload and self.is_available(freshness):
            assert self._registry is not None
            return self._registry

        registry: Dict[str, component_type] = {}
        for path in glob_files(self._file_glob):
            try:
                name, component = self._load_component(path)
            except ComponentDisabledException:
                continue
            except Exception as e:
                if show_error:
                    print(f"failed to loading component from {path}, skipping: {e}")
                continue
            if component is None:
                if show_error:
                    print(f"failed to loading component from {path}, skipping")
                continue
            registry[name] = component

        self._registry_update = datetime.now()
        self._registry = registry
        return registry

    @property
    def registry(self) -> Dict[str, component_type]:
        return self.get_registry()

    def get_list(self, force_reload: bool = False, freshness: Optional[timedelta] = None) -> List[component_type]:
        registry = self.get_registry(force_reload, freshness, show_error=True)
        keys = sorted(registry.keys())
        return [registry[k] for k in keys]

    @property
    def list(self) -> List[component_type]:
        return self.get_list()

    def get(self, name: str) -> Optional[component_type]:
        return self.registry.get(name, None)

    def __getitem__(self, name: str) -> Optional[component_type]:
        return self.get(name)

    @property
    def file_glob(self) -> str:
        return self._file_glob

    @file_glob.setter
    def file_glob(self, file_glob: str) -> None:
        if self._file_glob == file_glob:
            return
        self._file_glob = file_glob
        self._registry = None
