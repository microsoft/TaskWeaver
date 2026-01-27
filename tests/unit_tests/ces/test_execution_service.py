"""Unit tests for ExecutionServiceProvider and ExecutionServiceClient."""

from unittest.mock import MagicMock, patch

import pytest

from taskweaver.ces.common import Client, ExecutionResult
from taskweaver.ces.manager.execution_service import ExecutionServiceClient, ExecutionServiceProvider


class TestExecutionServiceClient:
    """Tests for ExecutionServiceClient."""

    def test_init(self) -> None:
        """Test client initialization."""
        client = ExecutionServiceClient(
            session_id="test-session",
            server_url="http://localhost:8000",
            api_key="secret",
            timeout=120.0,
            cwd="/custom/path",
        )
        assert client.session_id == "test-session"
        assert client.server_url == "http://localhost:8000"
        assert client.api_key == "secret"
        assert client.timeout == 120.0
        assert client.cwd == "/custom/path"
        assert client._client is None

    def test_implements_client_abc(self) -> None:
        """Test that ExecutionServiceClient implements Client ABC."""
        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        assert isinstance(client, Client)

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_start(self, mock_client_class: MagicMock) -> None:
        """Test starting the client."""
        mock_exec_client = MagicMock()
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test-session",
            server_url="http://localhost:8000",
            api_key="secret",
            timeout=120.0,
            cwd="/custom/path",
        )
        client.start()

        mock_client_class.assert_called_once_with(
            session_id="test-session",
            server_url="http://localhost:8000",
            api_key="secret",
            timeout=120.0,
            cwd="/custom/path",
        )
        mock_exec_client.start.assert_called_once()
        assert client._client is mock_exec_client

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_start_idempotent(self, mock_client_class: MagicMock) -> None:
        """Test that start is idempotent."""
        mock_exec_client = MagicMock()
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        client.start()  # Second call should be no-op

        assert mock_client_class.call_count == 1

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_stop(self, mock_client_class: MagicMock) -> None:
        """Test stopping the client."""
        mock_exec_client = MagicMock()
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        client.stop()

        mock_exec_client.stop.assert_called_once()
        mock_exec_client.close.assert_called_once()
        assert client._client is None

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_stop_not_started(self, mock_client_class: MagicMock) -> None:
        """Test stop when not started is no-op."""
        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.stop()  # Should not raise

        mock_client_class.assert_not_called()

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_stop_cleans_up_on_error(self, mock_client_class: MagicMock) -> None:
        """Test that stop cleans up even if stop() raises."""
        mock_exec_client = MagicMock()
        mock_exec_client.stop.side_effect = Exception("Stop failed")
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        client.stop()

        # Client should still be cleaned up
        assert client._client is None
        mock_exec_client.close.assert_called_once()

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_load_plugin(self, mock_client_class: MagicMock) -> None:
        """Test loading a plugin."""
        mock_exec_client = MagicMock()
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        client.load_plugin("test_plugin", "def test(): pass", {"key": "value"})

        mock_exec_client.load_plugin.assert_called_once_with(
            "test_plugin",
            "def test(): pass",
            {"key": "value"},
        )

    def test_load_plugin_not_started(self) -> None:
        """Test that load_plugin raises when not started."""
        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )

        with pytest.raises(RuntimeError, match="Client not started"):
            client.load_plugin("test", "code", {})

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_test_plugin(self, mock_client_class: MagicMock) -> None:
        """Test the test_plugin method."""
        mock_exec_client = MagicMock()
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        client.test_plugin("test_plugin")

        mock_exec_client.test_plugin.assert_called_once_with("test_plugin")

    def test_test_plugin_not_started(self) -> None:
        """Test that test_plugin raises when not started."""
        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )

        with pytest.raises(RuntimeError, match="Client not started"):
            client.test_plugin("test")

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_update_session_var(self, mock_client_class: MagicMock) -> None:
        """Test updating session variables."""
        mock_exec_client = MagicMock()
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        client.update_session_var({"var1": "value1"})

        mock_exec_client.update_session_var.assert_called_once_with({"var1": "value1"})

    def test_update_session_var_not_started(self) -> None:
        """Test that update_session_var raises when not started."""
        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )

        with pytest.raises(RuntimeError, match="Client not started"):
            client.update_session_var({"var": "val"})

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_execute_code(self, mock_client_class: MagicMock) -> None:
        """Test executing code."""
        mock_exec_client = MagicMock()
        mock_result = ExecutionResult(
            execution_id="exec-001",
            code="print('hello')",
            is_success=True,
        )
        mock_exec_client.execute_code.return_value = mock_result
        mock_client_class.return_value = mock_exec_client

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        result = client.execute_code("exec-001", "print('hello')")

        assert result == mock_result
        mock_exec_client.execute_code.assert_called_once_with(
            "exec-001",
            "print('hello')",
            on_output=None,
        )

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    def test_execute_code_with_callback(self, mock_client_class: MagicMock) -> None:
        """Test executing code with output callback."""
        mock_exec_client = MagicMock()
        mock_result = ExecutionResult(
            execution_id="exec-001",
            code="print('hello')",
            is_success=True,
        )
        mock_exec_client.execute_code.return_value = mock_result
        mock_client_class.return_value = mock_exec_client

        def on_output(stream: str, text: str) -> None:
            pass

        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        client.start()
        client.execute_code("exec-001", "print('hello')", on_output=on_output)

        mock_exec_client.execute_code.assert_called_once_with(
            "exec-001",
            "print('hello')",
            on_output=on_output,
        )

    def test_execute_code_not_started(self) -> None:
        """Test that execute_code raises when not started."""
        client = ExecutionServiceClient(
            session_id="test",
            server_url="http://localhost:8000",
        )

        with pytest.raises(RuntimeError, match="Client not started"):
            client.execute_code("exec-001", "code")


class TestExecutionServiceProvider:
    """Tests for ExecutionServiceProvider."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        provider = ExecutionServiceProvider()

        assert provider.server_url == "http://localhost:8000"
        assert provider.api_key is None
        assert provider.auto_start is True
        assert provider.container is False
        assert provider.timeout == 300.0
        assert provider._initialized is False
        assert provider._launcher is None

    def test_init_custom(self) -> None:
        """Test custom initialization."""
        provider = ExecutionServiceProvider(
            server_url="http://custom:9000",
            api_key="secret",
            auto_start=False,
            container=True,
            container_image="custom/image",
            work_dir="/custom/path",
            timeout=120.0,
            startup_timeout=30.0,
        )

        assert provider.server_url == "http://custom:9000"
        assert provider.api_key == "secret"
        assert provider.auto_start is False
        assert provider.container is True
        assert provider.container_image == "custom/image"
        assert provider.work_dir == "/custom/path"
        assert provider.timeout == 120.0
        assert provider.startup_timeout == 30.0

    def test_url_parsing(self) -> None:
        """Test that host and port are parsed from URL."""
        provider = ExecutionServiceProvider(server_url="http://myhost:9000")

        assert provider._host == "myhost"
        assert provider._port == 9000

    def test_url_parsing_default_port(self) -> None:
        """Test default port when not in URL."""
        provider = ExecutionServiceProvider(server_url="http://myhost")

        assert provider._host == "myhost"
        assert provider._port == 8000

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_initialize_with_auto_start(self, mock_launcher_class: MagicMock) -> None:
        """Test initialization with auto_start enabled."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider(
            server_url="http://localhost:8000",
            auto_start=True,
            api_key="secret",
            work_dir="/work",
            container=True,
            container_image="custom/image",
            startup_timeout=30.0,
        )
        provider.initialize()

        mock_launcher_class.assert_called_once_with(
            host="localhost",
            port=8000,
            api_key="secret",
            work_dir="/work",
            container=True,
            container_image="custom/image",
            startup_timeout=30.0,
        )
        mock_launcher.start.assert_called_once()
        assert provider._initialized is True

    def test_initialize_without_auto_start(self) -> None:
        """Test initialization without auto_start."""
        provider = ExecutionServiceProvider(auto_start=False)
        provider.initialize()

        assert provider._initialized is True
        assert provider._launcher is None

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_initialize_idempotent(self, mock_launcher_class: MagicMock) -> None:
        """Test that initialize is idempotent."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider(auto_start=True)
        provider.initialize()
        provider.initialize()  # Second call should be no-op

        assert mock_launcher_class.call_count == 1

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_clean_up(self, mock_launcher_class: MagicMock) -> None:
        """Test clean_up method."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider(auto_start=True)
        provider.initialize()
        provider.clean_up()

        mock_launcher.stop.assert_called_once()
        assert provider._initialized is False
        assert provider._launcher is None

    def test_clean_up_without_launcher(self) -> None:
        """Test clean_up when no launcher exists."""
        provider = ExecutionServiceProvider(auto_start=False)
        provider.initialize()
        provider.clean_up()  # Should not raise

        assert provider._initialized is False

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_get_session_client(self, mock_launcher_class: MagicMock) -> None:
        """Test getting a session client."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider(
            server_url="http://localhost:8000",
            api_key="secret",
            timeout=120.0,
        )
        provider.initialize()

        client = provider.get_session_client(
            session_id="test-session",
            cwd="/custom/path",
        )

        assert isinstance(client, ExecutionServiceClient)
        assert client.session_id == "test-session"
        assert client.server_url == "http://localhost:8000"
        assert client.api_key == "secret"
        assert client.timeout == 120.0
        assert client.cwd == "/custom/path"

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_get_session_client_uses_session_dir_as_cwd(
        self,
        mock_launcher_class: MagicMock,
    ) -> None:
        """Test that session_dir is used as cwd when cwd not specified."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider()
        provider.initialize()

        client = provider.get_session_client(
            session_id="test",
            session_dir="/session/dir",
        )

        assert client.cwd == "/session/dir"

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_get_session_client_cwd_overrides_session_dir(
        self,
        mock_launcher_class: MagicMock,
    ) -> None:
        """Test that cwd takes precedence over session_dir."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider()
        provider.initialize()

        client = provider.get_session_client(
            session_id="test",
            session_dir="/session/dir",
            cwd="/explicit/cwd",
        )

        assert client.cwd == "/explicit/cwd"

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_get_session_client_auto_initializes(
        self,
        mock_launcher_class: MagicMock,
    ) -> None:
        """Test that get_session_client auto-initializes if needed."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider(auto_start=True)
        # Don't call initialize()

        client = provider.get_session_client("test-session")

        # Should have auto-initialized
        assert provider._initialized is True
        assert client is not None

    def test_get_kernel_mode(self) -> None:
        """Test get_kernel_mode returns 'local'."""
        provider = ExecutionServiceProvider()

        # Server mode always reports as 'local' since kernel is local to server
        assert provider.get_kernel_mode() == "local"


class TestExecutionServiceProviderManager:
    """Tests for Manager ABC compliance."""

    def test_implements_manager_abc(self) -> None:
        """Test that ExecutionServiceProvider implements Manager ABC."""
        from taskweaver.ces.common import Manager

        provider = ExecutionServiceProvider()
        assert isinstance(provider, Manager)

    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_full_lifecycle(self, mock_launcher_class: MagicMock) -> None:
        """Test full provider lifecycle."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        provider = ExecutionServiceProvider(auto_start=True)

        # Initialize
        provider.initialize()
        assert provider._initialized is True

        # Get session client
        client = provider.get_session_client("test-session")
        assert isinstance(client, Client)

        # Clean up
        provider.clean_up()
        assert provider._initialized is False

    @patch("taskweaver.ces.manager.execution_service.ExecutionClient")
    @patch("taskweaver.ces.manager.execution_service.ServerLauncher")
    def test_client_session_lifecycle(
        self,
        mock_launcher_class: MagicMock,
        mock_exec_client_class: MagicMock,
    ) -> None:
        """Test complete client session lifecycle through provider."""
        mock_launcher = MagicMock()
        mock_launcher_class.return_value = mock_launcher

        mock_exec_client = MagicMock()
        mock_result = ExecutionResult(
            execution_id="exec-001",
            code="x = 42",
            is_success=True,
            output="42",
        )
        mock_exec_client.execute_code.return_value = mock_result
        mock_exec_client_class.return_value = mock_exec_client

        # Create provider and get client
        provider = ExecutionServiceProvider(auto_start=True)
        provider.initialize()

        client = provider.get_session_client("test-session", cwd="/work")

        # Use client
        client.start()
        result = client.execute_code("exec-001", "x = 42")
        assert result.is_success is True
        assert result.output == "42"

        client.stop()

        # Clean up provider
        provider.clean_up()

        # Verify lifecycle calls
        mock_launcher.start.assert_called_once()
        mock_launcher.stop.assert_called_once()
        mock_exec_client.start.assert_called_once()
        mock_exec_client.stop.assert_called_once()
