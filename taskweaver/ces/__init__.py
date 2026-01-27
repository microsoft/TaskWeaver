"""Code Execution Service package.

This module provides factory functions for creating execution service managers.
All execution goes through an HTTP server (local auto-start or remote).
"""

from typing import Optional

from taskweaver.ces.common import Manager
from taskweaver.ces.manager.defer import DeferredManager
from taskweaver.ces.manager.execution_service import ExecutionServiceProvider


def code_execution_service_factory(
    env_dir: str,
    server_url: str = "http://localhost:8000",
    server_api_key: Optional[str] = None,
    server_auto_start: bool = True,
    server_container: bool = False,
    server_container_image: Optional[str] = None,
    server_timeout: float = 300.0,
    server_startup_timeout: float = 60.0,
    server_kill_existing: bool = True,
) -> Manager:
    """Factory function to create the execution service manager.

    All execution uses the HTTP server architecture. By default, a local server
    is auto-started. For remote execution, set server_url and auto_start=False.

    Args:
        env_dir: Environment/working directory for session data.
        server_url: URL of the execution server.
        server_api_key: API key for server authentication.
        server_auto_start: Whether to auto-start the server if not running.
        server_container: Whether to run the server in a Docker container.
        server_container_image: Docker image for the server container.
        server_timeout: Request timeout for server communication.
        server_startup_timeout: Maximum time to wait for server startup.
        server_kill_existing: Whether to kill existing server on the port before starting.

    Returns:
        Manager instance configured for server-based execution.
    """

    def server_manager_factory() -> ExecutionServiceProvider:
        return ExecutionServiceProvider(
            server_url=server_url,
            api_key=server_api_key,
            auto_start=server_auto_start,
            container=server_container,
            container_image=server_container_image,
            work_dir=env_dir,
            timeout=server_timeout,
            startup_timeout=server_startup_timeout,
            kill_existing=server_kill_existing,
        )

    return DeferredManager(
        kernel_mode="local",
        manager_factory=server_manager_factory,
    )


__all__ = [
    "Manager",
    "DeferredManager",
    "ExecutionServiceProvider",
    "code_execution_service_factory",
]
