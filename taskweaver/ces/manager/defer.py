from __future__ import annotations

from typing import Callable, Dict, Optional

from taskweaver.ces.common import Client, ExecutionResult, KernelModeType, Manager


class DeferredClient(Client):
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        self.client_factory = client_factory
        self.proxy_client: Optional[Client] = None

    def start(self) -> None:
        # defer the start to the proxy client
        pass

    def stop(self) -> None:
        if self.proxy_client is not None:
            self.proxy_client.stop()

    def load_plugin(self, plugin_name: str, plugin_code: str, plugin_config: Dict[str, str]) -> None:
        self._get_proxy_client().load_plugin(plugin_name, plugin_code, plugin_config)

    def test_plugin(self, plugin_name: str) -> None:
        self._get_proxy_client().test_plugin(plugin_name)

    def update_session_var(self, session_var_dict: Dict[str, str]) -> None:
        self._get_proxy_client().update_session_var(session_var_dict)

    def execute_code(self, exec_id: str, code: str) -> ExecutionResult:
        return self._get_proxy_client().execute_code(exec_id, code)

    def _get_proxy_client(self) -> Client:
        if self.proxy_client is None:
            self.proxy_client = self.client_factory()
            self.proxy_client.start()
        return self.proxy_client


class DeferredManager(Manager):
    def __init__(self, kernel_mode: KernelModeType, manager_factory: Callable[[], Manager]) -> None:
        super().__init__()
        self.kernel_mode: KernelModeType = kernel_mode
        self.manager_factory = manager_factory
        self.proxy_manager: Optional[Manager] = None

    def initialize(self) -> None:
        # defer the initialization to the proxy manager
        pass

    def clean_up(self) -> None:
        if self.proxy_manager is not None:
            self.proxy_manager.clean_up()

    def get_session_client(
        self,
        session_id: str,
        env_id: Optional[str] = None,
        session_dir: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> DeferredClient:
        def client_factory() -> Client:
            return self._get_proxy_manager().get_session_client(session_id, env_id, session_dir, cwd)

        return DeferredClient(client_factory)

    def get_kernel_mode(self) -> KernelModeType:
        return self.kernel_mode

    def _get_proxy_manager(self) -> Manager:
        if self.proxy_manager is None:
            self.proxy_manager = self.manager_factory()
            self.proxy_manager.initialize()
        return self.proxy_manager
