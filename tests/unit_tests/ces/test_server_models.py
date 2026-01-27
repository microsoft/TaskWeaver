"""Unit tests for the execution server Pydantic models."""

from datetime import datetime
from unittest.mock import MagicMock

from taskweaver.ces.server.models import (
    ArtifactModel,
    CreateSessionRequest,
    CreateSessionResponse,
    ErrorResponse,
    ExecuteCodeRequest,
    ExecuteCodeResponse,
    ExecuteStreamResponse,
    HealthResponse,
    LoadPluginRequest,
    LoadPluginResponse,
    OutputEvent,
    ResultEvent,
    SessionInfoResponse,
    StopSessionResponse,
    UpdateVariablesRequest,
    UpdateVariablesResponse,
    artifact_from_execution,
    execution_result_to_response,
)


class TestRequestModels:
    """Tests for request models."""

    def test_create_session_request_basic(self) -> None:
        """Test CreateSessionRequest with required fields only."""
        req = CreateSessionRequest(session_id="test-session-123")
        assert req.session_id == "test-session-123"
        assert req.cwd is None

    def test_create_session_request_with_cwd(self) -> None:
        """Test CreateSessionRequest with cwd specified."""
        req = CreateSessionRequest(session_id="test-session", cwd="/tmp/work")
        assert req.session_id == "test-session"
        assert req.cwd == "/tmp/work"

    def test_load_plugin_request(self) -> None:
        """Test LoadPluginRequest model."""
        req = LoadPluginRequest(
            name="test_plugin",
            code="def test(): pass",
            config={"key": "value"},
        )
        assert req.name == "test_plugin"
        assert req.code == "def test(): pass"
        assert req.config == {"key": "value"}

    def test_load_plugin_request_empty_config(self) -> None:
        """Test LoadPluginRequest with default empty config."""
        req = LoadPluginRequest(name="plugin", code="pass")
        assert req.config == {}

    def test_execute_code_request_basic(self) -> None:
        """Test ExecuteCodeRequest with required fields."""
        req = ExecuteCodeRequest(
            exec_id="exec-001",
            code="print('hello')",
        )
        assert req.exec_id == "exec-001"
        assert req.code == "print('hello')"
        assert req.stream is False

    def test_execute_code_request_streaming(self) -> None:
        """Test ExecuteCodeRequest with streaming enabled."""
        req = ExecuteCodeRequest(
            exec_id="exec-002",
            code="print('hello')",
            stream=True,
        )
        assert req.stream is True

    def test_update_variables_request(self) -> None:
        """Test UpdateVariablesRequest model."""
        req = UpdateVariablesRequest(
            variables={"var1": "value1", "var2": "value2"},
        )
        assert req.variables == {"var1": "value1", "var2": "value2"}


class TestResponseModels:
    """Tests for response models."""

    def test_health_response(self) -> None:
        """Test HealthResponse model."""
        resp = HealthResponse(
            version="1.0.0",
            active_sessions=5,
        )
        assert resp.status == "healthy"
        assert resp.version == "1.0.0"
        assert resp.active_sessions == 5

    def test_create_session_response(self) -> None:
        """Test CreateSessionResponse model."""
        resp = CreateSessionResponse(
            session_id="test-session",
            cwd="/tmp/work",
        )
        assert resp.session_id == "test-session"
        assert resp.status == "created"
        assert resp.cwd == "/tmp/work"

    def test_stop_session_response(self) -> None:
        """Test StopSessionResponse model."""
        resp = StopSessionResponse(session_id="test-session")
        assert resp.session_id == "test-session"
        assert resp.status == "stopped"

    def test_session_info_response(self) -> None:
        """Test SessionInfoResponse model."""
        now = datetime.utcnow()
        resp = SessionInfoResponse(
            session_id="test-session",
            status="running",
            created_at=now,
            last_activity=now,
            loaded_plugins=["plugin1", "plugin2"],
            execution_count=10,
            cwd="/tmp/work",
        )
        assert resp.session_id == "test-session"
        assert resp.status == "running"
        assert resp.created_at == now
        assert resp.loaded_plugins == ["plugin1", "plugin2"]
        assert resp.execution_count == 10

    def test_load_plugin_response(self) -> None:
        """Test LoadPluginResponse model."""
        resp = LoadPluginResponse(name="test_plugin")
        assert resp.name == "test_plugin"
        assert resp.status == "loaded"

    def test_execute_code_response_success(self) -> None:
        """Test ExecuteCodeResponse for successful execution."""
        resp = ExecuteCodeResponse(
            execution_id="exec-001",
            is_success=True,
            output="Hello World",
            stdout=["Hello World\n"],
        )
        assert resp.execution_id == "exec-001"
        assert resp.is_success is True
        assert resp.error is None
        assert resp.output == "Hello World"
        assert resp.stdout == ["Hello World\n"]

    def test_execute_code_response_failure(self) -> None:
        """Test ExecuteCodeResponse for failed execution."""
        resp = ExecuteCodeResponse(
            execution_id="exec-002",
            is_success=False,
            error="SyntaxError: invalid syntax",
        )
        assert resp.is_success is False
        assert resp.error == "SyntaxError: invalid syntax"

    def test_execute_code_response_with_artifacts(self) -> None:
        """Test ExecuteCodeResponse with artifacts."""
        artifact = ArtifactModel(
            name="chart",
            type="image",
            mime_type="image/png",
            file_name="chart.png",
            preview="[chart image]",
        )
        resp = ExecuteCodeResponse(
            execution_id="exec-003",
            is_success=True,
            artifact=[artifact],
        )
        assert len(resp.artifact) == 1
        assert resp.artifact[0].name == "chart"
        assert resp.artifact[0].type == "image"

    def test_execute_stream_response(self) -> None:
        """Test ExecuteStreamResponse model."""
        resp = ExecuteStreamResponse(
            execution_id="exec-001",
            stream_url="/api/v1/sessions/test/stream/exec-001",
        )
        assert resp.execution_id == "exec-001"
        assert resp.stream_url == "/api/v1/sessions/test/stream/exec-001"

    def test_update_variables_response(self) -> None:
        """Test UpdateVariablesResponse model."""
        resp = UpdateVariablesResponse(
            variables={"var1": "new_value"},
        )
        assert resp.status == "updated"
        assert resp.variables == {"var1": "new_value"}

    def test_error_response(self) -> None:
        """Test ErrorResponse model."""
        resp = ErrorResponse(detail="Session not found")
        assert resp.detail == "Session not found"


class TestArtifactModel:
    """Tests for ArtifactModel."""

    def test_artifact_model_basic(self) -> None:
        """Test ArtifactModel with basic fields."""
        artifact = ArtifactModel(
            name="output",
            type="file",
        )
        assert artifact.name == "output"
        assert artifact.type == "file"
        assert artifact.mime_type == ""
        assert artifact.file_content is None
        assert artifact.download_url is None

    def test_artifact_model_with_content(self) -> None:
        """Test ArtifactModel with inline content."""
        artifact = ArtifactModel(
            name="result",
            type="text",
            file_content="Some text content",
            file_content_encoding="str",
        )
        assert artifact.file_content == "Some text content"
        assert artifact.file_content_encoding == "str"

    def test_artifact_model_with_download_url(self) -> None:
        """Test ArtifactModel with download URL."""
        artifact = ArtifactModel(
            name="large_file",
            type="file",
            file_name="data.csv",
            download_url="/api/v1/sessions/test/artifacts/data.csv",
        )
        assert artifact.download_url == "/api/v1/sessions/test/artifacts/data.csv"


class TestSSEEventModels:
    """Tests for SSE event models."""

    def test_output_event_stdout(self) -> None:
        """Test OutputEvent for stdout."""
        event = OutputEvent(type="stdout", text="Hello\n")
        assert event.type == "stdout"
        assert event.text == "Hello\n"

    def test_output_event_stderr(self) -> None:
        """Test OutputEvent for stderr."""
        event = OutputEvent(type="stderr", text="Warning: something\n")
        assert event.type == "stderr"
        assert event.text == "Warning: something\n"

    def test_result_event(self) -> None:
        """Test ResultEvent model."""
        event = ResultEvent(
            execution_id="exec-001",
            is_success=True,
            output="result",
            stdout=["line1\n", "line2\n"],
        )
        assert event.execution_id == "exec-001"
        assert event.is_success is True
        assert event.output == "result"
        assert len(event.stdout) == 2


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_artifact_from_execution(self) -> None:
        """Test artifact_from_execution conversion."""
        # Create a mock ExecutionArtifact
        mock_artifact = MagicMock()
        mock_artifact.name = "test_artifact"
        mock_artifact.type = "image"
        mock_artifact.mime_type = "image/png"
        mock_artifact.original_name = "chart.png"
        mock_artifact.file_name = "chart_001.png"
        mock_artifact.file_content = None
        mock_artifact.file_content_encoding = "str"
        mock_artifact.preview = "[image preview]"

        result = artifact_from_execution(mock_artifact)

        assert isinstance(result, ArtifactModel)
        assert result.name == "test_artifact"
        assert result.type == "image"
        assert result.mime_type == "image/png"
        assert result.file_content is None

    def test_artifact_from_execution_with_content(self) -> None:
        """Test artifact_from_execution with inline content."""
        mock_artifact = MagicMock()
        mock_artifact.name = "small_file"
        mock_artifact.type = "text"
        mock_artifact.mime_type = "text/plain"
        mock_artifact.original_name = "output.txt"
        mock_artifact.file_name = "output.txt"
        mock_artifact.file_content = "Hello World"
        mock_artifact.file_content_encoding = "str"
        mock_artifact.preview = "Hello World"

        result = artifact_from_execution(mock_artifact)

        assert result.file_content == "Hello World"
        assert result.file_content_encoding == "str"

    def test_execution_result_to_response_success(self) -> None:
        """Test execution_result_to_response for successful result."""
        # Create mock result
        mock_result = MagicMock()
        mock_result.execution_id = "exec-001"
        mock_result.is_success = True
        mock_result.error = None
        mock_result.output = "42"
        mock_result.stdout = ["output line\n"]
        mock_result.stderr = []
        mock_result.log = [("INFO", "logger", "message")]
        mock_result.artifact = []
        mock_result.variables = [("x", "42")]

        response = execution_result_to_response(mock_result, "session-001")

        assert isinstance(response, ExecuteCodeResponse)
        assert response.execution_id == "exec-001"
        assert response.is_success is True
        assert response.output == "42"
        assert response.stdout == ["output line\n"]
        assert response.log == [("INFO", "logger", "message")]
        assert response.variables == [("x", "42")]

    def test_execution_result_to_response_with_artifacts(self) -> None:
        """Test execution_result_to_response with artifacts."""
        # Create mock artifact
        mock_artifact = MagicMock()
        mock_artifact.name = "chart"
        mock_artifact.type = "image"
        mock_artifact.mime_type = "image/png"
        mock_artifact.original_name = "chart.png"
        mock_artifact.file_name = "chart_001.png"
        mock_artifact.file_content = None  # Large file, no inline content
        mock_artifact.file_content_encoding = "str"
        mock_artifact.preview = "[chart]"

        mock_result = MagicMock()
        mock_result.execution_id = "exec-002"
        mock_result.is_success = True
        mock_result.error = None
        mock_result.output = ""
        mock_result.stdout = []
        mock_result.stderr = []
        mock_result.log = []
        mock_result.artifact = [mock_artifact]
        mock_result.variables = []

        response = execution_result_to_response(
            mock_result,
            "session-001",
            base_url="http://localhost:8000",
        )

        assert len(response.artifact) == 1
        assert response.artifact[0].name == "chart"
        # Large artifact should have download URL
        assert response.artifact[0].download_url == (
            "http://localhost:8000/api/v1/sessions/session-001/artifacts/chart_001.png"
        )

    def test_execution_result_to_response_failure(self) -> None:
        """Test execution_result_to_response for failed result."""
        mock_result = MagicMock()
        mock_result.execution_id = "exec-003"
        mock_result.is_success = False
        mock_result.error = "NameError: name 'undefined' is not defined"
        mock_result.output = ""
        mock_result.stdout = []
        mock_result.stderr = ["Traceback...\n", "NameError...\n"]
        mock_result.log = []
        mock_result.artifact = []
        mock_result.variables = []

        response = execution_result_to_response(mock_result, "session-001")

        assert response.is_success is False
        assert "NameError" in response.error
        assert len(response.stderr) == 2


class TestModelSerialization:
    """Tests for model serialization (JSON export)."""

    def test_request_model_json_export(self) -> None:
        """Test that request models can be exported to JSON."""
        req = ExecuteCodeRequest(
            exec_id="exec-001",
            code="x = 42",
            stream=True,
        )
        json_data = req.model_dump()
        assert json_data["exec_id"] == "exec-001"
        assert json_data["code"] == "x = 42"
        assert json_data["stream"] is True

    def test_response_model_json_export(self) -> None:
        """Test that response models can be exported to JSON."""
        resp = ExecuteCodeResponse(
            execution_id="exec-001",
            is_success=True,
            output="result",
            artifact=[
                ArtifactModel(name="test", type="file"),
            ],
        )
        json_data = resp.model_dump()
        assert json_data["execution_id"] == "exec-001"
        assert json_data["is_success"] is True
        assert len(json_data["artifact"]) == 1

    def test_health_response_json_export(self) -> None:
        """Test HealthResponse JSON serialization."""
        resp = HealthResponse(version="1.0.0", active_sessions=3)
        json_data = resp.model_dump()
        assert json_data["status"] == "healthy"
        assert json_data["version"] == "1.0.0"
        assert json_data["active_sessions"] == 3
