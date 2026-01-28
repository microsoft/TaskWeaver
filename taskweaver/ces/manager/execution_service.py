"""ExecutionServiceProvider - Manager implementation for server-based execution.

This module provides the ExecutionServiceProvider class which implements the
Manager ABC and uses the HTTP client to communicate with the execution server.
"""

from __future__ import annotations

import logging
import os
from typing import Callable, Dict, Optional

from taskweaver.ces.client.execution_client import ExecutionClient
from taskweaver.ces.client.server_launcher import ServerLauncher
from taskweaver.ces.common import Client, ExecutionResult, KernelModeType, Manager

logger = logging.getLogger(__name__)


class ExecutionServiceClient(Client):
    """Client wrapper that manages HTTP client lifecycle.

    This class wraps ExecutionClient and handles session creation/cleanup
    to implement the Client ABC interface.
    """

    def __init__(
        self,
        session_id: str,
        server_url: str,
        api_key: Optional[str] = None,
        timeout: float = 300.0,
        cwd: Optional[str] = None,
    ) -> None:
        """Initialize the execution service client.

        Args:
            session_id: Unique session identifier.
            server_url: URL of the execution server.
            api_key: Optional API key for authentication.
            timeout: Request timeout in seconds.
            cwd: Optional working directory for code execution.
        """
        self.session_id = session_id
        self.server_url = server_url
        self.api_key = api_key
        self.timeout = timeout
        self.cwd = cwd
        self._client: Optional[ExecutionClient] = None

    def start(self) -> None:
        """Start the session by creating it on the server."""
        if self._client is not None:
            return

        self._client = ExecutionClient(
            session_id=self.session_id,
            server_url=self.server_url,
            api_key=self.api_key,
            timeout=self.timeout,
            cwd=self.cwd,
        )
        self._client.start()

    def stop(self) -> None:
        """Stop the session."""
        if self._client is None:
            return

        try:
            self._client.stop()
        finally:
            self._client.close()
            self._client = None

    def load_plugin(
        self,
        plugin_name: str,
        plugin_code: str,
        plugin_config: Dict[str, str],
    ) -> None:
        """Load a plugin into the session."""
        if self._client is None:
            raise RuntimeError("Client not started")
        self._client.load_plugin(plugin_name, plugin_code, plugin_config)

    def test_plugin(self, plugin_name: str) -> None:
        """Test a loaded plugin."""
        if self._client is None:
            raise RuntimeError("Client not started")
        self._client.test_plugin(plugin_name)

    def update_session_var(self, session_var_dict: Dict[str, str]) -> None:
        """Update session variables."""
        if self._client is None:
            raise RuntimeError("Client not started")
        self._client.update_session_var(session_var_dict)

    def execute_code(
        self,
        exec_id: str,
        code: str,
        on_output: Optional[Callable[[str, str], None]] = None,
    ) -> ExecutionResult:
        """Execute code in the session."""
        if self._client is None:
            raise RuntimeError("Client not started")
        return self._client.execute_code(exec_id, code, on_output=on_output)

    def upload_file(
        self,
        filename: str,
        content: bytes,
    ) -> str:
        """Upload a file to the session's working directory."""
        if self._client is None:
            raise RuntimeError("Client not started")
        return self._client.upload_file(filename, content)


class ExecutionServiceProvider(Manager):
    """Manager implementation that uses the HTTP execution server.

    This class implements the Manager ABC and manages the server lifecycle
    (auto-start if needed) and creates ExecutionServiceClient instances
    for each session.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        auto_start: bool = True,
        container: bool = False,
        container_image: Optional[str] = None,
        work_dir: Optional[str] = None,
        timeout: float = 300.0,
        startup_timeout: float = 60.0,
        kill_existing: bool = True,
    ) -> None:
        """Initialize the execution service provider.

        Args:
            server_url: URL of the execution server.
            api_key: Optional API key for authentication.
            auto_start: Whether to auto-start the server if not running.
            container: Whether to run the server in a Docker container.
            container_image: Docker image to use (only if container=True).
            work_dir: Working directory for session data.
            timeout: Request timeout in seconds.
            startup_timeout: Maximum time to wait for server startup.
            kill_existing: Whether to kill existing server on the port before starting.
        """
        self.server_url = server_url
        self.api_key = api_key
        self.auto_start = auto_start
        self.container = container
        self.container_image = container_image
        self.work_dir = work_dir or os.getcwd()
        self.timeout = timeout
        self.startup_timeout = startup_timeout
        self.kill_existing = kill_existing

        self._launcher: Optional[ServerLauncher] = None
        self._initialized = False

        # Parse host and port from URL for launcher
        from urllib.parse import urlparse

        parsed = urlparse(server_url)
        self._host = parsed.hostname or "localhost"
        self._port = parsed.port or 8000

    def initialize(self) -> None:
        """Initialize the manager and start server if needed."""
        if self._initialized:
            return

        if self.auto_start:
            self._launcher = ServerLauncher(
                host=self._host,
                port=self._port,
                api_key=self.api_key,
                work_dir=self.work_dir,
                container=self.container,
                container_image=self.container_image,
                startup_timeout=self.startup_timeout,
                kill_existing=self.kill_existing,
            )
            self._launcher.start()

        self._initialized = True
        logger.info(f"ExecutionServiceProvider initialized with server at {self.server_url}")

    def clean_up(self) -> None:
        """Clean up resources and stop server if we started it."""
        if self._launcher is not None:
            self._launcher.stop()
            self._launcher = None

        self._initialized = False
        logger.info("ExecutionServiceProvider cleaned up")

    def get_session_client(
        self,
        session_id: str,
        env_id: Optional[str] = None,
        session_dir: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Client:
        """Get a client for the specified session.

        Args:
            session_id: Unique session identifier.
            env_id: Environment ID (ignored for server mode).
            session_dir: Session directory (used as cwd if cwd not specified).
            cwd: Working directory for code execution.

        Returns:
            ExecutionServiceClient for the session.
        """
        # Ensure initialized
        if not self._initialized:
            self.initialize()

        # Use session_dir as cwd if cwd not specified
        effective_cwd = cwd or session_dir

        return ExecutionServiceClient(
            session_id=session_id,
            server_url=self.server_url,
            api_key=self.api_key,
            timeout=self.timeout,
            cwd=effective_cwd,
        )

    def get_kernel_mode(self) -> KernelModeType:
        """Get the kernel mode.

        For server mode, this returns 'local' since the server handles
        the actual kernel mode internally.
        """
        # Server mode abstracts the kernel mode - report as 'local'
        # since the kernel runs local to the server
        return "local"
