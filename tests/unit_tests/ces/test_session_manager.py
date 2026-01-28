"""Unit tests for ServerSessionManager."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from taskweaver.ces.common import ExecutionResult
from taskweaver.ces.server.session_manager import ServerSession, ServerSessionManager


class TestServerSession:
    """Tests for the ServerSession dataclass."""

    def test_server_session_creation(self) -> None:
        """Test ServerSession creation with defaults."""
        mock_env = MagicMock()
        session = ServerSession(
            session_id="test-session",
            environment=mock_env,
        )
        assert session.session_id == "test-session"
        assert session.environment == mock_env
        assert session.loaded_plugins == []
        assert session.execution_count == 0
        assert session.cwd == ""
        assert session.session_dir == ""

    def test_server_session_with_custom_values(self) -> None:
        """Test ServerSession with custom values."""
        mock_env = MagicMock()
        now = datetime.utcnow()
        session = ServerSession(
            session_id="test-session",
            environment=mock_env,
            created_at=now,
            last_activity=now,
            loaded_plugins=["plugin1"],
            execution_count=5,
            cwd="/tmp/work",
            session_dir="/tmp/sessions/test",
        )
        assert session.loaded_plugins == ["plugin1"]
        assert session.execution_count == 5
        assert session.cwd == "/tmp/work"

    def test_update_activity(self) -> None:
        """Test that update_activity updates the timestamp."""
        mock_env = MagicMock()
        session = ServerSession(
            session_id="test-session",
            environment=mock_env,
        )
        old_activity = session.last_activity

        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)
        session.update_activity()

        assert session.last_activity >= old_activity


class TestServerSessionManager:
    """Tests for ServerSessionManager."""

    @pytest.fixture()
    def manager(self, tmp_path: str) -> ServerSessionManager:
        """Create a ServerSessionManager with a temp work dir."""
        return ServerSessionManager(
            env_id="test-env",
            work_dir=str(tmp_path),
        )

    def test_manager_initialization(self, tmp_path: str) -> None:
        """Test manager initialization."""
        manager = ServerSessionManager(
            env_id="test-env",
            work_dir=str(tmp_path),
        )
        assert manager.env_id == "test-env"
        assert manager.work_dir == str(tmp_path)
        assert manager.active_session_count == 0

    def test_manager_default_env_id(self, tmp_path: str) -> None:
        """Test manager uses default env_id from environment."""
        with patch.dict(os.environ, {"TASKWEAVER_ENV_ID": "custom-env"}, clear=False):
            manager = ServerSessionManager(work_dir=str(tmp_path))
            assert manager.env_id == "custom-env"

    def test_active_session_count(self, manager: ServerSessionManager) -> None:
        """Test active_session_count property."""
        assert manager.active_session_count == 0

    def test_session_exists_false(self, manager: ServerSessionManager) -> None:
        """Test session_exists returns False for non-existent session."""
        assert manager.session_exists("non-existent") is False

    def test_get_session_none(self, manager: ServerSessionManager) -> None:
        """Test get_session returns None for non-existent session."""
        assert manager.get_session("non-existent") is None

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_create_session(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test creating a new session."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        session = manager.create_session("test-session")

        assert session.session_id == "test-session"
        assert manager.session_exists("test-session")
        assert manager.active_session_count == 1

        # Verify Environment was created and started
        mock_env_class.assert_called_once()
        mock_env.start_session.assert_called_once()

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_create_session_with_cwd(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
        tmp_path: str,
    ) -> None:
        """Test creating a session with custom cwd."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        custom_cwd = os.path.join(str(tmp_path), "custom", "path")
        session = manager.create_session("test-session", cwd=custom_cwd)

        assert session.cwd == custom_cwd

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_create_duplicate_session_raises(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that creating a duplicate session raises ValueError."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")

        with pytest.raises(ValueError, match="already exists"):
            manager.create_session("test-session")

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_stop_session(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test stopping a session."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        assert manager.session_exists("test-session")

        manager.stop_session("test-session")

        assert not manager.session_exists("test-session")
        assert manager.active_session_count == 0
        mock_env.stop_session.assert_called_once_with("test-session")

    def test_stop_nonexistent_session_raises(
        self,
        manager: ServerSessionManager,
    ) -> None:
        """Test that stopping a non-existent session raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.stop_session("non-existent")

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_stop_session_with_env_error(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that session is still removed even if env.stop_session fails."""
        mock_env = MagicMock()
        mock_env.stop_session.side_effect = Exception("Cleanup error")
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        manager.stop_session("test-session")

        # Session should be removed despite the error
        assert not manager.session_exists("test-session")

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_load_plugin(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test loading a plugin into a session."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        manager.load_plugin(
            session_id="test-session",
            plugin_name="test_plugin",
            plugin_code="def test(): pass",
            plugin_config={"key": "value"},
        )

        mock_env.load_plugin.assert_called_once_with(
            session_id="test-session",
            plugin_name="test_plugin",
            plugin_impl="def test(): pass",
            plugin_config={"key": "value"},
        )

        session = manager.get_session("test-session")
        assert session is not None
        assert "test_plugin" in session.loaded_plugins

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_load_plugin_nonexistent_session(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that loading plugin for non-existent session raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.load_plugin(
                session_id="non-existent",
                plugin_name="test_plugin",
                plugin_code="def test(): pass",
            )

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_load_plugin_duplicate(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that loading the same plugin twice doesn't duplicate in list."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        manager.load_plugin("test-session", "plugin1", "code")
        manager.load_plugin("test-session", "plugin1", "code")

        session = manager.get_session("test-session")
        assert session is not None
        assert session.loaded_plugins.count("plugin1") == 1

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_execute_code(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test executing code in a session."""
        mock_env = MagicMock()
        mock_result = ExecutionResult(
            execution_id="exec-001",
            code="print('hello')",
            is_success=True,
            output="",
        )
        mock_env.execute_code.return_value = mock_result
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        result = manager.execute_code(
            session_id="test-session",
            exec_id="exec-001",
            code="print('hello')",
        )

        assert result.is_success is True
        mock_env.execute_code.assert_called_once_with(
            session_id="test-session",
            code="print('hello')",
            exec_id="exec-001",
            on_output=None,
        )

        session = manager.get_session("test-session")
        assert session is not None
        assert session.execution_count == 1

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_execute_code_with_callback(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test executing code with output callback."""
        mock_env = MagicMock()
        mock_result = ExecutionResult(
            execution_id="exec-001",
            code="print('hello')",
            is_success=True,
        )
        mock_env.execute_code.return_value = mock_result
        mock_env_class.return_value = mock_env

        def on_output(stream: str, text: str) -> None:
            pass

        manager.create_session("test-session")
        manager.execute_code(
            session_id="test-session",
            exec_id="exec-001",
            code="print('hello')",
            on_output=on_output,
        )

        # Verify callback was passed
        call_kwargs = mock_env.execute_code.call_args[1]
        assert call_kwargs["on_output"] == on_output

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_execute_code_nonexistent_session(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that executing code for non-existent session raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.execute_code(
                session_id="non-existent",
                exec_id="exec-001",
                code="print('hello')",
            )

    @patch("taskweaver.ces.server.session_manager.Environment")
    @pytest.mark.asyncio
    async def test_execute_code_async(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test async code execution."""
        mock_env = MagicMock()
        mock_result = ExecutionResult(
            execution_id="exec-001",
            code="x = 42",
            is_success=True,
            output="42",
        )
        mock_env.execute_code.return_value = mock_result
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        result = await manager.execute_code_async(
            session_id="test-session",
            exec_id="exec-001",
            code="x = 42",
        )

        assert result.is_success is True
        assert result.output == "42"

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_update_session_variables(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test updating session variables."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        manager.update_session_variables(
            session_id="test-session",
            variables={"var1": "value1"},
        )

        mock_env.update_session_var.assert_called_once_with(
            "test-session",
            {"var1": "value1"},
        )

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_update_session_variables_nonexistent(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that updating vars for non-existent session raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.update_session_variables("non-existent", {"var": "val"})

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_get_artifact_path_exists(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
        tmp_path: str,
    ) -> None:
        """Test getting artifact path when file exists."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        session = manager.create_session("test-session")

        # Create a test artifact file
        artifact_path = os.path.join(session.cwd, "test_artifact.png")
        with open(artifact_path, "w") as f:
            f.write("test")

        result = manager.get_artifact_path("test-session", "test_artifact.png")
        assert result == artifact_path

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_get_artifact_path_not_exists(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test getting artifact path when file doesn't exist."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")
        result = manager.get_artifact_path("test-session", "nonexistent.png")
        assert result is None

    def test_get_artifact_path_nonexistent_session(
        self,
        manager: ServerSessionManager,
    ) -> None:
        """Test getting artifact path for non-existent session."""
        result = manager.get_artifact_path("non-existent", "file.png")
        assert result is None

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_cleanup_all(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test cleaning up all sessions."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("session-1")
        manager.create_session("session-2")
        manager.create_session("session-3")
        assert manager.active_session_count == 3

        manager.cleanup_all()

        assert manager.active_session_count == 0
        assert mock_env.stop_session.call_count == 3

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_cleanup_all_with_errors(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test cleanup_all continues despite individual session errors."""
        mock_env = MagicMock()
        mock_env.stop_session.side_effect = [Exception("Error 1"), None, Exception("Error 2")]
        mock_env_class.return_value = mock_env

        manager.create_session("session-1")
        manager.create_session("session-2")
        manager.create_session("session-3")

        # Should not raise, just log errors
        manager.cleanup_all()
        assert manager.active_session_count == 0


class TestServerSessionManagerUploadFile:
    """Tests for file upload functionality."""

    @pytest.fixture()
    def manager(self, tmp_path: str) -> ServerSessionManager:
        """Create a ServerSessionManager with a temp work dir."""
        return ServerSessionManager(
            env_id="test-env",
            work_dir=str(tmp_path),
        )

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_upload_file_success(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test successful file upload."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        session = manager.create_session("test-session")

        # Upload a file
        content = b"col1,col2\n1,2\n3,4"
        result = manager.upload_file("test-session", "data.csv", content)

        # Verify file was written to session's cwd
        assert result == os.path.join(session.cwd, "data.csv")
        assert os.path.isfile(result)

        # Verify content
        with open(result, "rb") as f:
            assert f.read() == content

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_upload_file_binary_content(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test uploading binary file content."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")

        # Binary content with non-UTF8 bytes
        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        result = manager.upload_file("test-session", "image.png", binary_content)

        # Verify file was written correctly
        with open(result, "rb") as f:
            assert f.read() == binary_content

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_upload_file_nonexistent_session(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that uploading to non-existent session raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            manager.upload_file("nonexistent", "file.csv", b"content")

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_upload_file_path_traversal_prevention(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that path traversal attacks are prevented."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        session = manager.create_session("test-session")

        # Attempt path traversal
        content = b"malicious content"
        result = manager.upload_file("test-session", "../../../etc/passwd", content)

        # Should sanitize to just "passwd" and write to session's cwd
        assert result == os.path.join(session.cwd, "passwd")
        assert os.path.isfile(result)

        # Verify file is in session's cwd, not in /etc
        assert session.cwd in result

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_upload_file_with_subdirectory_in_name(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that subdirectory paths in filename are sanitized."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        session = manager.create_session("test-session")

        # Filename with subdirectory
        content = b"data"
        result = manager.upload_file("test-session", "subdir/file.csv", content)

        # Should strip the subdirectory
        assert result == os.path.join(session.cwd, "file.csv")

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_upload_file_updates_activity(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that upload updates session activity timestamp."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        session = manager.create_session("test-session")
        old_activity = session.last_activity

        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)

        manager.upload_file("test-session", "file.csv", b"content")

        assert session.last_activity >= old_activity

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_upload_file_overwrite_existing(
        self,
        mock_env_class: MagicMock,
        manager: ServerSessionManager,
    ) -> None:
        """Test that uploading overwrites existing file."""
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager.create_session("test-session")

        # Upload initial file
        manager.upload_file("test-session", "file.txt", b"original content")

        # Upload again with same name
        result = manager.upload_file("test-session", "file.txt", b"new content")

        # Verify content was overwritten
        with open(result, "rb") as f:
            assert f.read() == b"new content"


class TestServerSessionManagerThreadSafety:
    """Tests for thread safety of ServerSessionManager."""

    @patch("taskweaver.ces.server.session_manager.Environment")
    def test_concurrent_session_creation(
        self,
        mock_env_class: MagicMock,
        tmp_path: str,
    ) -> None:
        """Test that concurrent session creation is thread-safe."""
        import threading

        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        manager = ServerSessionManager(work_dir=str(tmp_path))
        created_sessions: list[str] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        def create_session(session_id: str) -> None:
            try:
                manager.create_session(session_id)
                with lock:
                    created_sessions.append(session_id)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=create_session, args=(f"session-{i}",)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All sessions should be created successfully
        assert len(created_sessions) == 10
        assert len(errors) == 0
        assert manager.active_session_count == 10
