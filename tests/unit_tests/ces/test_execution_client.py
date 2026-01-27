"""Unit tests for ExecutionClient."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from taskweaver.ces.client.execution_client import ExecutionClient, ExecutionClientError
from taskweaver.ces.common import ExecutionResult


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Dict[str, Any] | None = None,
        text: str = "",
        content: bytes = b"",
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text or (json.dumps(json_data) if json_data else "")
        self.content = content

    def json(self) -> Dict[str, Any]:
        if self._json_data is None:
            raise ValueError("No JSON data")
        return self._json_data


class TestExecutionClientInit:
    """Tests for ExecutionClient initialization."""

    def test_basic_init(self) -> None:
        """Test basic client initialization."""
        client = ExecutionClient(
            session_id="test-session",
            server_url="http://localhost:8000",
        )
        assert client.session_id == "test-session"
        assert client.server_url == "http://localhost:8000"
        assert client.api_key is None
        assert client.timeout == 300.0
        assert client.cwd is None
        assert client._started is False

    def test_init_with_trailing_slash(self) -> None:
        """Test that trailing slash is stripped from server_url."""
        client = ExecutionClient(
            session_id="test",
            server_url="http://localhost:8000/",
        )
        assert client.server_url == "http://localhost:8000"

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        client = ExecutionClient(
            session_id="test",
            server_url="http://localhost:8000",
            api_key="secret-key",
        )
        assert client.api_key == "secret-key"
        assert client._headers["X-API-Key"] == "secret-key"

    def test_init_with_custom_timeout(self) -> None:
        """Test initialization with custom timeout."""
        client = ExecutionClient(
            session_id="test",
            server_url="http://localhost:8000",
            timeout=60.0,
        )
        assert client.timeout == 60.0

    def test_init_with_cwd(self) -> None:
        """Test initialization with cwd."""
        client = ExecutionClient(
            session_id="test",
            server_url="http://localhost:8000",
            cwd="/custom/path",
        )
        assert client.cwd == "/custom/path"

    def test_api_base_property(self) -> None:
        """Test api_base property."""
        client = ExecutionClient(
            session_id="test",
            server_url="http://localhost:8000",
        )
        assert client.api_base == "http://localhost:8000/api/v1"


class TestExecutionClientResponseHandling:
    """Tests for response handling."""

    def test_handle_response_success(self) -> None:
        """Test handling successful response."""
        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        response = MockResponse(
            status_code=200,
            json_data={"result": "success"},
        )
        result = client._handle_response(response)  # type: ignore
        assert result == {"result": "success"}

    def test_handle_response_error_with_json(self) -> None:
        """Test handling error response with JSON detail."""
        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        response = MockResponse(
            status_code=404,
            json_data={"detail": "Session not found"},
        )
        with pytest.raises(ExecutionClientError) as exc_info:
            client._handle_response(response)  # type: ignore
        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value)

    def test_handle_response_error_without_json(self) -> None:
        """Test handling error response without JSON."""
        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        response = MockResponse(
            status_code=500,
            text="Internal Server Error",
        )
        response._json_data = None  # Force non-JSON response

        with pytest.raises(ExecutionClientError) as exc_info:
            client._handle_response(response)  # type: ignore
        assert exc_info.value.status_code == 500


class TestExecutionClientHealthCheck:
    """Tests for health_check method."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_health_check_success(self, mock_client_class: MagicMock) -> None:
        """Test successful health check."""
        mock_client = MagicMock()
        mock_client.get.return_value = MockResponse(
            status_code=200,
            json_data={"status": "healthy", "version": "1.0.0", "active_sessions": 3},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        result = client.health_check()

        assert result["status"] == "healthy"
        mock_client.get.assert_called_once_with("/api/v1/health")

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_health_check_connection_error(self, mock_client_class: MagicMock) -> None:
        """Test health check with connection error."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")

        with pytest.raises(ExecutionClientError) as exc_info:
            client.health_check()
        assert "Cannot connect" in str(exc_info.value)

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_health_check_timeout(self, mock_client_class: MagicMock) -> None:
        """Test health check with timeout."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")

        with pytest.raises(ExecutionClientError) as exc_info:
            client.health_check()
        assert "timeout" in str(exc_info.value).lower()


class TestExecutionClientSession:
    """Tests for session start/stop."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_start_session(self, mock_client_class: MagicMock) -> None:
        """Test starting a session."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={"session_id": "test", "status": "created", "cwd": "/tmp/work"},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.start()

        assert client._started is True
        assert client.cwd == "/tmp/work"
        mock_client.post.assert_called_once_with(
            "/api/v1/sessions",
            json={"session_id": "test", "cwd": None},
        )

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_start_session_already_started(self, mock_client_class: MagicMock) -> None:
        """Test that start is idempotent."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={"session_id": "test", "status": "created", "cwd": "/tmp/work"},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.start()
        client.start()  # Second call should be no-op

        assert mock_client.post.call_count == 1

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_start_session_already_exists(self, mock_client_class: MagicMock) -> None:
        """Test starting session when it already exists on server."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=409,
            json_data={"detail": "Session already exists"},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.start()  # Should not raise, just mark as started

        assert client._started is True

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_stop_session(self, mock_client_class: MagicMock) -> None:
        """Test stopping a session."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={"session_id": "test", "status": "created", "cwd": "/tmp"},
        )
        mock_client.delete.return_value = MockResponse(
            status_code=200,
            json_data={"session_id": "test", "status": "stopped"},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.start()
        client.stop()

        assert client._started is False
        mock_client.delete.assert_called_once_with("/api/v1/sessions/test")

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_stop_session_not_started(self, mock_client_class: MagicMock) -> None:
        """Test that stop is no-op when not started."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.stop()

        mock_client.delete.assert_not_called()

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_stop_session_already_gone(self, mock_client_class: MagicMock) -> None:
        """Test stopping session when it's already gone on server."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={"session_id": "test", "status": "created", "cwd": "/tmp"},
        )
        mock_client.delete.return_value = MockResponse(
            status_code=404,
            json_data={"detail": "Session not found"},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.start()
        client.stop()  # Should not raise

        assert client._started is False


class TestExecutionClientPlugin:
    """Tests for plugin operations."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_load_plugin(self, mock_client_class: MagicMock) -> None:
        """Test loading a plugin."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={"name": "test_plugin", "status": "loaded"},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.load_plugin(
            plugin_name="test_plugin",
            plugin_code="def test(): pass",
            plugin_config={"key": "value"},
        )

        mock_client.post.assert_called_once_with(
            "/api/v1/sessions/test/plugins",
            json={
                "name": "test_plugin",
                "code": "def test(): pass",
                "config": {"key": "value"},
            },
        )

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_test_plugin(self, mock_client_class: MagicMock) -> None:
        """Test the test_plugin method (currently a no-op)."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.test_plugin("test_plugin")  # Should not raise


class TestExecutionClientVariables:
    """Tests for session variable operations."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_update_session_var(self, mock_client_class: MagicMock) -> None:
        """Test updating session variables."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={"status": "updated", "variables": {"var1": "value1"}},
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.update_session_var({"var1": "value1"})

        mock_client.post.assert_called_once_with(
            "/api/v1/sessions/test/variables",
            json={"variables": {"var1": "value1"}},
        )


class TestExecutionClientExecute:
    """Tests for code execution."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_execute_code_sync_success(self, mock_client_class: MagicMock) -> None:
        """Test synchronous code execution."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={
                "execution_id": "exec-001",
                "is_success": True,
                "output": "Hello World",
                "stdout": ["Hello World\n"],
                "stderr": [],
                "log": [],
                "artifact": [],
                "variables": [],
            },
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        result = client.execute_code("exec-001", "print('Hello World')")

        assert isinstance(result, ExecutionResult)
        assert result.execution_id == "exec-001"
        assert result.is_success is True
        assert result.output == "Hello World"
        assert result.code == "print('Hello World')"

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_execute_code_sync_failure(self, mock_client_class: MagicMock) -> None:
        """Test synchronous code execution with error."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={
                "execution_id": "exec-001",
                "is_success": False,
                "error": "NameError: name 'undefined' is not defined",
                "output": "",
                "stdout": [],
                "stderr": ["Traceback...\n"],
                "log": [],
                "artifact": [],
                "variables": [],
            },
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        result = client.execute_code("exec-001", "undefined")

        assert result.is_success is False
        assert "NameError" in result.error  # type: ignore

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_execute_code_with_artifacts(self, mock_client_class: MagicMock) -> None:
        """Test code execution that produces artifacts."""
        mock_client = MagicMock()
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={
                "execution_id": "exec-001",
                "is_success": True,
                "output": "",
                "stdout": [],
                "stderr": [],
                "log": [("INFO", "logger", "Generated chart")],
                "artifact": [
                    {
                        "name": "chart",
                        "type": "image",
                        "mime_type": "image/png",
                        "original_name": "chart.png",
                        "file_name": "chart_001.png",
                        "file_content": "",
                        "file_content_encoding": "str",
                        "preview": "[chart]",
                    },
                ],
                "variables": [("x", "42")],
            },
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        result = client.execute_code("exec-001", "plot()")

        assert len(result.artifact) == 1
        assert result.artifact[0].name == "chart"
        assert result.artifact[0].type == "image"
        assert len(result.log) == 1
        assert len(result.variables) == 1
        assert result.variables[0] == ("x", "42")


class TestExecutionClientStreaming:
    """Tests for streaming code execution."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_execute_code_streaming(self, mock_client_class: MagicMock) -> None:
        """Test streaming code execution."""
        mock_client = MagicMock()

        # Mock the initial POST to get stream URL
        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={
                "execution_id": "exec-001",
                "stream_url": "/api/v1/sessions/test/stream/exec-001",
            },
        )

        # Mock the SSE stream
        sse_lines = [
            "event:output",
            'data:{"type":"stdout","text":"Hello\\n"}',
            "",
            "event:output",
            'data:{"type":"stdout","text":"World\\n"}',
            "",
            "event:result",
            (
                'data:{"execution_id":"exec-001","is_success":true,"output":"","'
                'stdout":["Hello\\n","World\\n"],"stderr":[],"log":[],"artifact":[],"variables":[]}'
            ),
            "",
            "event:done",
            "data:{}",
        ]

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=None)
        mock_stream.iter_lines.return_value = iter(sse_lines)
        mock_client.stream.return_value = mock_stream
        mock_client_class.return_value = mock_client

        output_calls: List[tuple[str, str]] = []

        def on_output(stream: str, text: str) -> None:
            output_calls.append((stream, text))

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        result = client.execute_code("exec-001", "print('Hello')\nprint('World')", on_output=on_output)

        assert result.is_success is True
        assert len(output_calls) == 2
        assert output_calls[0] == ("stdout", "Hello\n")
        assert output_calls[1] == ("stdout", "World\n")

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_execute_code_streaming_no_result(self, mock_client_class: MagicMock) -> None:
        """Test streaming execution when no result is received."""
        mock_client = MagicMock()

        mock_client.post.return_value = MockResponse(
            status_code=200,
            json_data={
                "execution_id": "exec-001",
                "stream_url": "/api/v1/sessions/test/stream/exec-001",
            },
        )

        # Mock stream that ends without result
        sse_lines = [
            "event:output",
            'data:{"type":"stdout","text":"partial output"}',
            "",
            "event:done",
            "data:{}",
        ]

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=None)
        mock_stream.iter_lines.return_value = iter(sse_lines)
        mock_client.stream.return_value = mock_stream
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")

        with pytest.raises(ExecutionClientError, match="No result received"):
            client.execute_code("exec-001", "code", on_output=lambda s, t: None)


class TestExecutionClientArtifacts:
    """Tests for artifact download."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_download_artifact(self, mock_client_class: MagicMock) -> None:
        """Test downloading an artifact."""
        mock_client = MagicMock()
        mock_client.get.return_value = MockResponse(
            status_code=200,
            content=b"fake image data",
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        content = client.download_artifact("chart.png")

        assert content == b"fake image data"
        mock_client.get.assert_called_once_with("/api/v1/sessions/test/artifacts/chart.png")

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_download_artifact_not_found(self, mock_client_class: MagicMock) -> None:
        """Test downloading non-existent artifact."""
        mock_client = MagicMock()
        mock_client.get.return_value = MockResponse(
            status_code=404,
            text="Not found",
        )
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")

        with pytest.raises(ExecutionClientError) as exc_info:
            client.download_artifact("nonexistent.png")
        assert exc_info.value.status_code == 404


class TestExecutionClientContextManager:
    """Tests for context manager protocol."""

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_context_manager(self, mock_client_class: MagicMock) -> None:
        """Test using client as context manager."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        with ExecutionClient(session_id="test", server_url="http://localhost:8000") as client:
            assert isinstance(client, ExecutionClient)

        mock_client.close.assert_called_once()

    @patch("taskweaver.ces.client.execution_client.httpx.Client")
    def test_close(self, mock_client_class: MagicMock) -> None:
        """Test explicit close."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ExecutionClient(session_id="test", server_url="http://localhost:8000")
        client.close()

        mock_client.close.assert_called_once()


class TestExecutionClientError:
    """Tests for ExecutionClientError exception."""

    def test_error_with_message(self) -> None:
        """Test error with message only."""
        error = ExecutionClientError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.status_code is None

    def test_error_with_status_code(self) -> None:
        """Test error with message and status code."""
        error = ExecutionClientError("Not found", status_code=404)
        assert str(error) == "Not found"
        assert error.status_code == 404
