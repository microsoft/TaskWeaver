from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple, TypeVar

from taskweaver.ces.common import Client, ExecutionResult, KernelModeType, Manager

TaskResult = TypeVar("TaskResult")


def deferred_var(
    name: str,
    init: Callable[[], TaskResult],
    threaded: bool,
) -> Callable[[], TaskResult]:
    result: Optional[Tuple[TaskResult]] = None
    if not threaded:
        result = (init(),)

        def sync_result() -> TaskResult:
            assert result is not None
            return result[0]

        return sync_result

    import threading

    lock = threading.Lock()
    loaded_event = threading.Event()
    thread: Optional[threading.Thread] = None

    def task() -> None:
        nonlocal result
        result = (init(),)
        loaded_event.set()

    def async_result() -> TaskResult:
        nonlocal result, thread
        loaded_event.wait()
        with lock:
            if thread is not None:
                thread.join()
                thread = None

        assert result is not None
        return result[0]

    with lock:
        threading.Thread(target=task, daemon=True).start()

    return async_result


class DeferredClient(Client):
    def __init__(
        self,
        client_factory: Callable[[], Client],
        async_warm_up: bool = False,
    ) -> None:
        self.client_factory = client_factory
        self.async_warm_up = async_warm_up
        self.deferred_var: Optional[Callable[[], Client]] = None

    def start(self) -> None:
        # defer the start to the proxy client
        if self.async_warm_up:
            self._init_deferred_var()

    def stop(self) -> None:
        if self.deferred_var is not None:
            self.deferred_var().stop()

    def load_plugin(
        self,
        plugin_name: str,
        plugin_code: str,
        plugin_config: Dict[str, str],
    ) -> None:
        self._get_proxy_client().load_plugin(plugin_name, plugin_code, plugin_config)

    def test_plugin(self, plugin_name: str) -> None:
        self._get_proxy_client().test_plugin(plugin_name)

    def update_session_var(self, session_var_dict: Dict[str, str]) -> None:
        self._get_proxy_client().update_session_var(session_var_dict)

    def execute_code(self, exec_id: str, code: str) -> ExecutionResult:
        return self._get_proxy_client().execute_code(exec_id, code)

    def _get_proxy_client(self) -> Client:
        return self._init_deferred_var()()

    def _init_deferred_var(self) -> Callable[[], Client]:
        if self.deferred_var is None:

            def task() -> Client:
                client = self.client_factory()
                client.start()
                return client

            self.deferred_var = deferred_var("DeferredClient", task, self.async_warm_up)
        return self.deferred_var


class DeferredManager(Manager):
    def __init__(
        self,
        kernel_mode: KernelModeType,
        manager_factory: Callable[[], Manager],
        async_warm_up: bool = True,
    ) -> None:
        super().__init__()
        self.kernel_mode: KernelModeType = kernel_mode
        self.manager_factory = manager_factory
        self.async_warm_up = async_warm_up
        self.deferred_var: Optional[Callable[[], Manager]] = None

    def initialize(self) -> None:
        # defer the initialization to the proxy manager
        if self.async_warm_up:
            self._init_deferred_var()

    def clean_up(self) -> None:
        if self.deferred_var is not None:
            self.deferred_var().clean_up()

    def get_session_client(
        self,
        session_id: str,
        env_id: Optional[str] = None,
        session_dir: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> DeferredClient:
        def client_factory() -> Client:
            return self._get_proxy_manager().get_session_client(
                session_id,
                env_id,
                session_dir,
                cwd,
            )

        return DeferredClient(client_factory, self.async_warm_up)

    def get_kernel_mode(self) -> KernelModeType:
        return self.kernel_mode

    def _get_proxy_manager(self) -> Manager:
        return self._init_deferred_var()()

    def _init_deferred_var(self) -> Callable[[], Manager]:
        if self.deferred_var is None:
            self.deferred_var = deferred_var(
                "DeferredManager",
                self.manager_factory,
                self.async_warm_up,
            )
        return self.deferred_var
