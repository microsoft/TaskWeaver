"""Unit tests for ServerLauncher."""

import os
import signal
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from taskweaver.ces.client.server_launcher import ServerLauncher, ServerLauncherError


class TestServerLauncherInit:
    """Tests for ServerLauncher initialization."""

    def test_default_init(self) -> None:
        """Test default initialization values."""
        launcher = ServerLauncher()
        assert launcher.host == "localhost"
        assert launcher.port == 8000
        assert launcher.api_key is None
        assert launcher.container is False
        assert launcher.startup_timeout == 60.0
        assert launcher._started is False
        assert launcher._process is None
        assert launcher._container_id is None

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom values."""
        launcher = ServerLauncher(
            host="0.0.0.0",
            port=9000,
            api_key="secret",
            work_dir="/custom/path",
            container=True,
            container_image="custom/image:latest",
            startup_timeout=120.0,
        )
        assert launcher.host == "0.0.0.0"
        assert launcher.port == 9000
        assert launcher.api_key == "secret"
        assert launcher.work_dir == "/custom/path"
        assert launcher.container is True
        assert launcher.container_image == "custom/image:latest"
        assert launcher.startup_timeout == 120.0

    def test_server_url_property(self) -> None:
        """Test server_url property."""
        launcher = ServerLauncher(host="localhost", port=8000)
        assert launcher.server_url == "http://localhost:8000"

        launcher = ServerLauncher(host="0.0.0.0", port=9000)
        assert launcher.server_url == "http://0.0.0.0:9000"

    def test_default_work_dir(self) -> None:
        """Test that work_dir defaults to cwd."""
        launcher = ServerLauncher()
        assert launcher.work_dir == os.getcwd()

    def test_default_container_image(self) -> None:
        """Test default container image."""
        launcher = ServerLauncher(container=True)
        assert launcher.container_image == ServerLauncher.DEFAULT_IMAGE


class TestServerLauncherIsRunning:
    """Tests for is_server_running method."""

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_server_running(self, mock_get: MagicMock) -> None:
        """Test detecting running server."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        launcher = ServerLauncher()
        assert launcher.is_server_running() is True

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "/api/v1/health" in call_args[0][0]

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_server_running_with_api_key(self, mock_get: MagicMock) -> None:
        """Test health check includes API key header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        launcher = ServerLauncher(api_key="secret")
        launcher.is_server_running()

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["X-API-Key"] == "secret"

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_server_not_running_connection_error(self, mock_get: MagicMock) -> None:
        """Test detecting server not running (connection error)."""
        mock_get.side_effect = Exception("Connection refused")

        launcher = ServerLauncher()
        assert launcher.is_server_running() is False

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_server_not_running_bad_status(self, mock_get: MagicMock) -> None:
        """Test detecting server not running (bad status code)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        launcher = ServerLauncher()
        assert launcher.is_server_running() is False


class TestServerLauncherStartSubprocess:
    """Tests for subprocess-based server start."""

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_start_when_already_running(self, mock_get: MagicMock) -> None:
        """Test start is no-op when server already running and kill_existing=False."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        launcher = ServerLauncher(kill_existing=False)
        launcher.start()

        assert launcher._started is True
        assert launcher._process is None  # No subprocess created

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_start_subprocess(self, mock_popen: MagicMock, mock_get: MagicMock) -> None:
        """Test starting server as subprocess."""
        # First call: not running, subsequent calls: running
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]

        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process still running
        mock_popen.return_value = mock_process

        launcher = ServerLauncher(
            host="127.0.0.1",
            port=8080,
            work_dir="/tmp/work",
        )
        launcher.start()

        assert launcher._started is True
        assert launcher._process is mock_process

        # Verify Popen was called with correct arguments
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert "-m" in cmd
        assert "taskweaver.ces.server" in cmd
        assert "--host" in cmd
        assert "127.0.0.1" in cmd
        assert "--port" in cmd
        assert "8080" in cmd
        assert "--work-dir" in cmd
        assert "/tmp/work" in cmd

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_start_subprocess_with_api_key(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test subprocess includes API key argument."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        launcher = ServerLauncher(api_key="secret-key")
        launcher.start()

        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert "--api-key" in cmd
        assert "secret-key" in cmd

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_start_subprocess_failure(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test handling subprocess start failure."""
        mock_get.side_effect = Exception("Not running")
        mock_popen.side_effect = OSError("Cannot execute")

        launcher = ServerLauncher()

        with pytest.raises(ServerLauncherError, match="Failed to start"):
            launcher.start()

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_start_already_started(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test start is idempotent when already started."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        launcher = ServerLauncher()
        launcher.start()
        launcher.start()  # Second call should be no-op

        assert mock_popen.call_count == 1


class TestServerLauncherStartContainer:
    """Tests for container-based server start."""

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_start_container_missing_docker(self, mock_get: MagicMock) -> None:
        """Test error when docker package not installed."""
        mock_get.side_effect = Exception("Not running")

        with patch.dict("sys.modules", {"docker": None}):
            launcher = ServerLauncher(container=True)

            with pytest.raises(ServerLauncherError, match="docker package is required"):
                launcher.start()

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_start_container_docker_not_running(self, mock_get: MagicMock) -> None:
        """Test error when Docker daemon not running."""
        mock_get.side_effect = Exception("Not running")

        # Mock docker module
        mock_docker = MagicMock()
        mock_docker.errors.DockerException = Exception
        mock_docker.from_env.side_effect = Exception("Cannot connect to Docker")

        with patch.dict("sys.modules", {"docker": mock_docker, "docker.errors": mock_docker.errors}):
            launcher = ServerLauncher(container=True)

            with pytest.raises(ServerLauncherError, match="Failed to connect to Docker"):
                launcher.start()

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_start_container_image_not_found(self, mock_get: MagicMock) -> None:
        """Test pulling image when not found locally."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]

        # Mock docker module
        mock_docker = MagicMock()
        mock_docker.errors.DockerException = Exception
        mock_docker.errors.ImageNotFound = Exception

        mock_client = MagicMock()
        mock_client.images.get.side_effect = Exception("Image not found")
        mock_client.images.pull.return_value = MagicMock()

        mock_container = MagicMock()
        mock_container.id = "abc123def456"  # pragma: allowlist secret
        mock_container.status = "running"
        mock_client.containers.run.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        mock_docker.from_env.return_value = mock_client

        with patch.dict("sys.modules", {"docker": mock_docker, "docker.errors": mock_docker.errors}):
            launcher = ServerLauncher(container=True)
            launcher.start()

            mock_client.images.pull.assert_called_once()

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_start_container_success(self, mock_get: MagicMock) -> None:
        """Test successful container start."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]

        mock_docker = MagicMock()
        mock_docker.errors.DockerException = Exception
        mock_docker.errors.ImageNotFound = type("ImageNotFound", (Exception,), {})

        mock_client = MagicMock()
        mock_client.images.get.return_value = MagicMock()  # Image exists

        mock_container = MagicMock()
        mock_container.id = "abc123def456"  # pragma: allowlist secret
        mock_container.status = "running"
        mock_client.containers.run.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        mock_docker.from_env.return_value = mock_client

        with patch.dict("sys.modules", {"docker": mock_docker, "docker.errors": mock_docker.errors}):
            launcher = ServerLauncher(
                container=True,
                port=9000,
                api_key="secret",
                work_dir="/tmp/work",
            )
            launcher.start()

            assert launcher._started is True
            assert launcher._container_id == "abc123def456"  # pragma: allowlist secret

            # Verify container run arguments
            call_kwargs = mock_client.containers.run.call_args[1]
            assert call_kwargs["detach"] is True
            assert call_kwargs["remove"] is True
            assert call_kwargs["ports"] == {"8000/tcp": 9000}
            assert call_kwargs["environment"]["TASKWEAVER_SERVER_API_KEY"] == "secret"


class TestServerLauncherWaitForReady:
    """Tests for _wait_for_ready method."""

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_wait_for_ready_success(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test waiting for server to become ready."""
        # Server becomes ready after first check
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        launcher = ServerLauncher()
        launcher.start()

        assert launcher._started is True

    @patch("taskweaver.ces.client.server_launcher.time.sleep")
    @patch("taskweaver.ces.client.server_launcher.time.time")
    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_wait_for_ready_timeout(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
        mock_time: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """Test timeout waiting for server."""
        mock_get.side_effect = Exception("Not running")

        # Simulate time passing beyond timeout
        mock_time.side_effect = [0, 0, 10, 20, 30, 40, 50, 60, 70]  # Exceeds 60s timeout

        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        launcher = ServerLauncher(startup_timeout=60.0)

        with pytest.raises(ServerLauncherError, match="did not become ready"):
            launcher.start()

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_wait_for_ready_process_exited(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test handling when process exits during startup."""
        mock_get.side_effect = Exception("Not running")

        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.communicate.return_value = (b"", b"Error: startup failed")
        mock_popen.return_value = mock_process

        launcher = ServerLauncher()

        with pytest.raises(ServerLauncherError, match="process exited"):
            launcher.start()


class TestServerLauncherStop:
    """Tests for server stop."""

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    @patch("os.name", "posix")
    @patch("os.killpg")
    @patch("os.getpgid")
    def test_stop_subprocess(
        self,
        mock_getpgid: MagicMock,
        mock_killpg: MagicMock,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test stopping subprocess."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        mock_getpgid.return_value = 12345

        launcher = ServerLauncher()
        launcher.start()
        launcher.stop()

        assert launcher._started is False
        assert launcher._process is None
        # On Unix, should send SIGTERM to process group
        mock_killpg.assert_called()

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    @patch("os.name", "posix")
    @patch("os.killpg")
    @patch("os.getpgid")
    def test_stop_subprocess_unix(
        self,
        mock_getpgid: MagicMock,
        mock_killpg: MagicMock,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test stopping subprocess on Unix (sends to process group)."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        mock_getpgid.return_value = 12345

        launcher = ServerLauncher()
        launcher.start()
        launcher.stop()

        # On Unix, should send signal to process group
        mock_killpg.assert_called()

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    @patch("os.name", "posix")
    @patch("os.killpg")
    @patch("os.getpgid")
    def test_stop_subprocess_force_kill(
        self,
        mock_getpgid: MagicMock,
        mock_killpg: MagicMock,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test force killing subprocess that doesn't stop gracefully."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.wait.side_effect = [
            subprocess.TimeoutExpired(cmd="test", timeout=10),
            0,  # Second wait succeeds after force kill
        ]
        mock_popen.return_value = mock_process
        mock_getpgid.return_value = 12345

        launcher = ServerLauncher()
        launcher.start()
        launcher.stop()

        assert mock_killpg.call_count == 2
        calls = mock_killpg.call_args_list
        assert calls[0][0][1] == signal.SIGTERM
        assert calls[1][0][1] == signal.SIGKILL

    def test_stop_not_started(self) -> None:
        """Test stop is no-op when not started."""
        launcher = ServerLauncher()
        launcher.stop()  # Should not raise

        assert launcher._started is False

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    def test_stop_container(self, mock_get: MagicMock) -> None:
        """Test stopping container."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]

        mock_docker = MagicMock()
        mock_docker.errors.DockerException = Exception
        mock_docker.errors.ImageNotFound = type("ImageNotFound", (Exception,), {})

        mock_client = MagicMock()
        mock_client.images.get.return_value = MagicMock()

        mock_container = MagicMock()
        mock_container.id = "abc123def456"  # pragma: allowlist secret
        mock_container.status = "running"
        mock_client.containers.run.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        mock_docker.from_env.return_value = mock_client

        with patch.dict("sys.modules", {"docker": mock_docker, "docker.errors": mock_docker.errors}):
            launcher = ServerLauncher(container=True)
            launcher.start()
            launcher.stop()

            assert launcher._started is False
            assert launcher._container_id is None
            mock_container.stop.assert_called_once_with(timeout=10)


class TestServerLauncherContextManager:
    """Tests for context manager protocol."""

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_context_manager(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test using launcher as context manager."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        with ServerLauncher() as launcher:
            assert launcher._started is True

        assert launcher._started is False

    @patch("taskweaver.ces.client.server_launcher.httpx.get")
    @patch("subprocess.Popen")
    def test_context_manager_with_exception(
        self,
        mock_popen: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test context manager cleans up on exception."""
        mock_get.side_effect = [
            Exception("Not running"),
            MagicMock(status_code=200),
        ]
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        with pytest.raises(ValueError):
            with ServerLauncher() as launcher:
                assert launcher._started is True
                raise ValueError("Test error")

        assert launcher._started is False


class TestServerLauncherError:
    """Tests for ServerLauncherError exception."""

    def test_error_message(self) -> None:
        """Test error with message."""
        error = ServerLauncherError("Something went wrong")
        assert str(error) == "Something went wrong"
