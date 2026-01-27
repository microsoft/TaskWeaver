"""Server launcher for auto-starting the execution server.

This module provides utilities to automatically start the execution server
as a subprocess or Docker container when needed.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ServerLauncherError(Exception):
    """Exception raised when server launch fails."""


class ServerLauncher:
    """Manages the lifecycle of the execution server.

    This class can start the server as a subprocess or Docker container,
    wait for it to become ready, and shut it down when no longer needed.
    """

    DEFAULT_IMAGE = "taskweavercontainers/taskweaver-executor:latest"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        api_key: Optional[str] = None,
        work_dir: Optional[str] = None,
        container: bool = False,
        container_image: Optional[str] = None,
        startup_timeout: float = 60.0,
        kill_existing: bool = True,
    ) -> None:
        """Initialize the server launcher.

        Args:
            host: Host to bind the server to.
            port: Port to bind the server to.
            api_key: Optional API key for authentication.
            work_dir: Working directory for session data.
            container: Whether to run the server in a Docker container.
            container_image: Docker image to use (only if container=True).
            startup_timeout: Maximum time to wait for server startup.
            kill_existing: Whether to kill existing server on the port before starting.
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.work_dir = work_dir or os.getcwd()
        self.container = container
        self.container_image = container_image or self.DEFAULT_IMAGE
        self.startup_timeout = startup_timeout
        self.kill_existing = kill_existing

        self._process: Optional[subprocess.Popen[bytes]] = None
        self._container_id: Optional[str] = None
        self._started = False

    @property
    def server_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"

    def is_server_running(self) -> bool:
        """Check if the server is already running and healthy.

        Returns:
            True if server is running and responding to health checks.
        """
        try:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = httpx.get(
                f"{self.server_url}/api/v1/health",
                headers=headers,
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def _get_pid_on_port(self) -> Optional[int]:
        """Get the PID of the process listening on the configured port.

        Returns:
            PID if found, None otherwise.
        """
        import platform

        try:
            if platform.system() == "Windows":
                # Use netstat on Windows
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                for line in result.stdout.split("\n"):
                    if f":{self.port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            return int(parts[-1])
            else:
                # Use lsof on Unix-like systems
                result = subprocess.run(
                    ["lsof", "-ti", f":{self.port}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout.strip():
                    return int(result.stdout.strip().split("\n")[0])
        except Exception as e:
            logger.debug(f"Failed to get PID on port {self.port}: {e}")
        return None

    def kill_existing_server(self) -> bool:
        """Kill any existing server process on the configured port.

        Returns:
            True if a server was killed, False if no server was found.
        """
        pid = self._get_pid_on_port()
        if pid is None:
            return False

        logger.info(f"Killing existing server process (PID: {pid}) on port {self.port}")
        try:
            import platform

            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
            else:
                os.kill(pid, signal.SIGTERM)
                # Give it a moment to terminate gracefully
                time.sleep(1)
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Already terminated

            # Wait for port to be released
            for _ in range(10):
                if not self.is_server_running() and self._get_pid_on_port() is None:
                    logger.info(f"Successfully killed server on port {self.port}")
                    return True
                time.sleep(0.5)

            logger.warning(f"Server process may still be running on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to kill server process: {e}")
            return False

    def start(self) -> None:
        """Start the execution server.

        If kill_existing is True and an existing server is found, it will be killed first.
        Otherwise, if a server is already running, this is a no-op.

        Raises:
            ServerLauncherError: If the server fails to start.
        """
        if self._started:
            return

        if self.is_server_running():
            if self.kill_existing:
                logger.info(f"Found existing server at {self.server_url}, killing it...")
                self.kill_existing_server()
                # Wait a bit for port to be released
                time.sleep(1)
            else:
                logger.info(f"Code Execution Server already running at {self.server_url}")
                self._started = True
                return

        if self.container:
            self._start_container()
        else:
            self._start_subprocess()

        self._wait_for_ready()
        self._started = True

    def _start_subprocess(self) -> None:
        """Start the server as a subprocess."""
        logger.info(f"Starting server subprocess on {self.host}:{self.port}")

        cmd = [
            sys.executable,
            "-m",
            "taskweaver.ces.server",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--work-dir",
            self.work_dir,
        ]

        if self.api_key:
            cmd.extend(["--api-key", self.api_key])

        # Environment for the subprocess
        env = os.environ.copy()
        env["TASKWEAVER_SERVER_HOST"] = self.host
        env["TASKWEAVER_SERVER_PORT"] = str(self.port)
        env["TASKWEAVER_SERVER_WORK_DIR"] = self.work_dir
        if self.api_key:
            env["TASKWEAVER_SERVER_API_KEY"] = self.api_key

        try:
            self._process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # Start in new process group to allow clean shutdown
                start_new_session=True,
            )
            logger.info(f"Server subprocess started with PID {self._process.pid}")
        except Exception as e:
            raise ServerLauncherError(f"Failed to start server subprocess: {e}")

    def _start_container(self) -> None:
        """Start the server in a Docker container."""
        logger.info(f"Starting server container {self.container_image}")

        try:
            import docker
            import docker.errors
        except ImportError:
            raise ServerLauncherError(
                "docker package is required for container mode. " "Please install it with: pip install docker",
            )

        try:
            client = docker.from_env()
        except docker.errors.DockerException as e:
            raise ServerLauncherError(f"Failed to connect to Docker: {e}")

        # Ensure image exists
        try:
            client.images.get(self.container_image)
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling image {self.container_image}...")
            try:
                client.images.pull(self.container_image)
            except docker.errors.DockerException as e:
                raise ServerLauncherError(f"Failed to pull image: {e}")

        # Environment variables for container
        container_env = {
            "TASKWEAVER_SERVER_HOST": "0.0.0.0",
            "TASKWEAVER_SERVER_PORT": "8000",
            "TASKWEAVER_SERVER_WORK_DIR": "/app/workspace",
        }
        if self.api_key:
            container_env["TASKWEAVER_SERVER_API_KEY"] = self.api_key

        # Volume mapping
        volumes = {
            os.path.abspath(self.work_dir): {"bind": "/app/workspace", "mode": "rw"},
        }

        try:
            container = client.containers.run(
                image=self.container_image,
                detach=True,
                environment=container_env,
                volumes=volumes,
                ports={"8000/tcp": self.port},
                remove=True,  # Auto-remove on stop
            )
            self._container_id = container.id
            logger.info(f"Server container started with ID {self._container_id[:12]}")
        except docker.errors.DockerException as e:
            raise ServerLauncherError(f"Failed to start container: {e}")

    def _wait_for_ready(self) -> None:
        """Wait for the server to become ready.

        Raises:
            ServerLauncherError: If server doesn't become ready in time.
        """
        logger.info(f"Starting Code Execution Server at {self.server_url}")
        start_time = time.time()

        while time.time() - start_time < self.startup_timeout:
            if self.is_server_running():
                elapsed = time.time() - start_time
                logger.info(f"Code Execution Server ready ({elapsed:.1f}s)")
                return

            # Check if process/container is still alive
            if self._process is not None:
                poll_result = self._process.poll()
                if poll_result is not None:
                    # Process has exited
                    stdout, stderr = self._process.communicate()
                    raise ServerLauncherError(
                        f"Server process exited with code {poll_result}. "
                        f"Stderr: {stderr.decode('utf-8', errors='replace')}",
                    )

            if self._container_id is not None:
                try:
                    import docker

                    client = docker.from_env()
                    container = client.containers.get(self._container_id)
                    if container.status not in ("running", "created"):
                        logs = container.logs().decode("utf-8", errors="replace")
                        raise ServerLauncherError(
                            f"Container exited with status {container.status}. " f"Logs: {logs}",
                        )
                except Exception as e:
                    if "docker" not in str(type(e).__module__):
                        raise

            time.sleep(0.5)

        raise ServerLauncherError(
            f"Server did not become ready within {self.startup_timeout} seconds",
        )

    def stop(self) -> None:
        """Stop the execution server."""
        if not self._started:
            return

        if self._process is not None:
            self._stop_subprocess()

        if self._container_id is not None:
            self._stop_container()

        self._started = False

    def _stop_subprocess(self) -> None:
        """Stop the server subprocess."""
        if self._process is None:
            return

        logger.info(f"Stopping server subprocess (PID {self._process.pid})")

        try:
            # Try graceful shutdown first
            if os.name == "nt":
                # Windows
                self._process.terminate()
            else:
                # Unix - send SIGTERM to process group
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

            # Wait for graceful shutdown
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill
                logger.warning("Server didn't stop gracefully, forcing kill")
                if os.name == "nt":
                    self._process.kill()
                else:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                self._process.wait(timeout=5)

        except Exception as e:
            logger.error(f"Error stopping server subprocess: {e}")
        finally:
            self._process = None

    def _stop_container(self) -> None:
        """Stop the server container."""
        if self._container_id is None:
            return

        logger.info(f"Stopping server container {self._container_id[:12]}")

        try:
            import docker

            client = docker.from_env()
            container = client.containers.get(self._container_id)
            container.stop(timeout=10)
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
        finally:
            self._container_id = None

    def __enter__(self) -> "ServerLauncher":
        """Context manager entry - start the server."""
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit - stop the server."""
        self.stop()
