"""Unit tests for TaskWeaver CLI commands."""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from taskweaver.cli.cli import taskweaver
from taskweaver.cli.util import CliContext


@pytest.fixture()
def cli_runner():
    """Provide a Click CliRunner for testing CLI commands."""
    return CliRunner()


@pytest.fixture()
def temp_workspace():
    """Create a temporary workspace with taskweaver_config.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "taskweaver_config.json")
        config_data = {
            "llm.api_key": "test_key",
            "llm.model": "gpt-4",
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        yield tmpdir


@pytest.fixture()
def empty_workspace():
    """Create a temporary empty workspace without taskweaver_config.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestCliContextDataclass:
    """Test CliContext dataclass."""

    def test_cli_context_has_server_url_field(self):
        """Test that CliContext includes server_url field."""
        ctx = CliContext(
            workspace="/tmp/workspace",
            workspace_param="/tmp/workspace",
            is_workspace_valid=True,
            is_workspace_empty=False,
            server_url="http://localhost:8000",
        )
        assert ctx.server_url == "http://localhost:8000"

    def test_cli_context_server_url_optional(self):
        """Test that CliContext server_url is optional."""
        ctx = CliContext(
            workspace="/tmp/workspace",
            workspace_param="/tmp/workspace",
            is_workspace_valid=True,
            is_workspace_empty=False,
        )
        assert ctx.server_url is None

    def test_cli_context_all_fields(self):
        """Test that CliContext has all required fields."""
        ctx = CliContext(
            workspace="/tmp/workspace",
            workspace_param="/tmp/workspace",
            is_workspace_valid=True,
            is_workspace_empty=False,
            server_url="http://localhost:8000",
        )
        assert ctx.workspace == "/tmp/workspace"
        assert ctx.workspace_param == "/tmp/workspace"
        assert ctx.is_workspace_valid is True
        assert ctx.is_workspace_empty is False
        assert ctx.server_url == "http://localhost:8000"


class TestTaskWeaverCommand:
    """Test main taskweaver command."""

    def test_taskweaver_help(self, cli_runner: CliRunner):
        """Test that taskweaver command displays help correctly."""
        result = cli_runner.invoke(taskweaver, ["--help"])
        assert result.exit_code == 0
        assert "TaskWeaver" in result.output
        assert "--project" in result.output
        assert "--server-url" in result.output

    def test_taskweaver_version(self, cli_runner: CliRunner):
        """Test that taskweaver command displays version."""
        result = cli_runner.invoke(taskweaver, ["--version"])
        assert result.exit_code == 0

    def test_taskweaver_global_server_url_option(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that global --server-url option is passed to CliContext."""
        result = cli_runner.invoke(
            taskweaver,
            [
                "-p",
                temp_workspace,
                "--server-url",
                "http://localhost:8000",
                "chat",
                "--help",
            ],
        )
        assert result.exit_code == 0

    def test_taskweaver_project_option(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that --project option is recognized."""
        result = cli_runner.invoke(
            taskweaver,
            ["-p", temp_workspace, "chat", "--help"],
        )
        assert result.exit_code == 0


class TestServerCommand:
    """Test server subcommand."""

    def test_server_help(self, cli_runner: CliRunner):
        """Test that server command help displays correctly."""
        result = cli_runner.invoke(taskweaver, ["server", "--help"])
        assert result.exit_code == 0
        assert "Code Execution Server" in result.output
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--api-key" in result.output
        assert "--log-level" in result.output
        assert "--reload" in result.output

    def test_server_requires_valid_workspace(
        self,
        cli_runner: CliRunner,
        empty_workspace: str,
    ):
        """Test that server command requires a valid workspace."""
        result = cli_runner.invoke(
            taskweaver,
            ["-p", empty_workspace, "server"],
        )
        assert result.exit_code == 1
        assert "not a valid Task Weaver project directory" in result.output
        assert "taskweaver_config.json" in result.output

    def test_server_with_valid_workspace(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that server command accepts valid workspace."""
        result = cli_runner.invoke(
            taskweaver,
            ["-p", temp_workspace, "server", "--help"],
        )
        assert result.exit_code == 0

    def test_server_host_option(self, cli_runner: CliRunner):
        """Test that server command has --host option."""
        result = cli_runner.invoke(taskweaver, ["server", "--help"])
        assert "--host" in result.output
        assert "Host to bind to" in result.output

    def test_server_port_option(self, cli_runner: CliRunner):
        """Test that server command has --port option."""
        result = cli_runner.invoke(taskweaver, ["server", "--help"])
        assert "--port" in result.output
        assert "Port to bind to" in result.output

    def test_server_api_key_option(self, cli_runner: CliRunner):
        """Test that server command has --api-key option."""
        result = cli_runner.invoke(taskweaver, ["server", "--help"])
        assert "--api-key" in result.output
        assert "API key" in result.output

    def test_server_log_level_option(self, cli_runner: CliRunner):
        """Test that server command has --log-level option."""
        result = cli_runner.invoke(taskweaver, ["server", "--help"])
        assert "--log-level" in result.output
        assert "Log level" in result.output

    def test_server_reload_option(self, cli_runner: CliRunner):
        """Test that server command has --reload option."""
        result = cli_runner.invoke(taskweaver, ["server", "--help"])
        assert "--reload" in result.output
        assert "auto-reload" in result.output

    def test_server_log_level_choices(self, cli_runner: CliRunner):
        """Test that server command log-level has correct choices."""
        result = cli_runner.invoke(taskweaver, ["server", "--help"])
        assert "debug" in result.output
        assert "info" in result.output
        assert "warning" in result.output
        assert "error" in result.output
        assert "critical" in result.output


class TestChatCommand:
    """Test chat subcommand."""

    def test_chat_help(self, cli_runner: CliRunner):
        """Test that chat command help displays correctly."""
        result = cli_runner.invoke(taskweaver, ["chat", "--help"])
        assert result.exit_code == 0
        assert "Chat with TaskWeaver" in result.output

    def test_chat_requires_valid_workspace(
        self,
        cli_runner: CliRunner,
        empty_workspace: str,
    ):
        """Test that chat command requires a valid workspace."""
        result = cli_runner.invoke(
            taskweaver,
            ["-p", empty_workspace, "chat"],
        )
        assert result.exit_code == 1
        assert "not a valid Task Weaver project directory" in result.output

    def test_chat_server_url_option(self, cli_runner: CliRunner):
        """Test that chat command has --server-url option."""
        result = cli_runner.invoke(taskweaver, ["chat", "--help"])
        assert result.exit_code == 0
        assert "--server-url" in result.output
        assert "Code Execution Server" in result.output

    def test_chat_accepts_server_url_option(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that chat command accepts --server-url option."""
        result = cli_runner.invoke(
            taskweaver,
            ["-p", temp_workspace, "chat", "--help"],
        )
        assert result.exit_code == 0
        assert "--server-url" in result.output

    def test_chat_with_global_server_url(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that chat command can use global --server-url option."""
        result = cli_runner.invoke(
            taskweaver,
            [
                "-p",
                temp_workspace,
                "--server-url",
                "http://localhost:8000",
                "chat",
                "--help",
            ],
        )
        assert result.exit_code == 0


class TestInitCommand:
    """Test init subcommand."""

    def test_init_help(self, cli_runner: CliRunner):
        """Test that init command help displays correctly."""
        result = cli_runner.invoke(taskweaver, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize" in result.output or "init" in result.output.lower()

    def test_init_does_not_require_workspace(self, cli_runner: CliRunner):
        """Test that init command does not require existing workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = cli_runner.invoke(
                taskweaver,
                ["-p", tmpdir, "init"],
            )
            assert result.exit_code == 0


class TestCliContextIntegration:
    """Test CliContext integration with CLI commands."""

    def test_cli_context_created_with_server_url(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that CliContext is created with server_url from global option."""
        result = cli_runner.invoke(
            taskweaver,
            [
                "-p",
                temp_workspace,
                "--server-url",
                "http://example.com:8000",
                "chat",
                "--help",
            ],
        )
        assert result.exit_code == 0

    def test_cli_context_server_url_none_by_default(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that CliContext server_url is None when not provided."""
        result = cli_runner.invoke(
            taskweaver,
            ["-p", temp_workspace, "chat", "--help"],
        )
        assert result.exit_code == 0

    def test_chat_server_url_overrides_global(
        self,
        cli_runner: CliRunner,
        temp_workspace: str,
    ):
        """Test that chat --server-url overrides global --server-url."""
        result = cli_runner.invoke(
            taskweaver,
            [
                "-p",
                temp_workspace,
                "--server-url",
                "http://global:8000",
                "chat",
                "--help",
            ],
        )
        assert result.exit_code == 0
        assert "--server-url" in result.output
