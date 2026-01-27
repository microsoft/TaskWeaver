"""HTTP client for the TaskWeaver Execution Server.

This module implements the Client ABC using HTTP requests to communicate
with the remote execution server.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx

from taskweaver.ces.common import Client, ExecutionArtifact, ExecutionResult

logger = logging.getLogger(__name__)


class ExecutionClientError(Exception):
    """Exception raised when the execution client encounters an error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ExecutionClient(Client):
    """HTTP client for the TaskWeaver Execution Server.

    This client implements the Client ABC and communicates with the
    execution server via HTTP API calls.
    """

    def __init__(
        self,
        session_id: str,
        server_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 300.0,
        cwd: Optional[str] = None,
    ) -> None:
        """Initialize the execution client.

        Args:
            session_id: Unique session identifier.
            server_url: URL of the execution server.
            api_key: Optional API key for authentication.
            timeout: Request timeout in seconds.
            cwd: Optional working directory for code execution.
        """
        self.session_id = session_id
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.cwd = cwd
        self._started = False

        # Build headers
        self._headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
        if api_key:
            self._headers["X-API-Key"] = api_key

        # HTTP client with connection pooling
        self._client = httpx.Client(
            base_url=self.server_url,
            headers=self._headers,
            timeout=httpx.Timeout(timeout, connect=30.0),
        )

    @property
    def api_base(self) -> str:
        """Get the API base URL."""
        return f"{self.server_url}/api/v1"

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate errors.

        Args:
            response: HTTP response object.

        Returns:
            Parsed JSON response.

        Raises:
            ExecutionClientError: If the request failed.
        """
        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get("detail", response.text)
            except Exception:
                detail = response.text

            raise ExecutionClientError(
                f"Server error ({response.status_code}): {detail}",
                status_code=response.status_code,
            )

        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check if the server is healthy.

        Returns:
            Health check response with status, version, and active sessions.

        Raises:
            ExecutionClientError: If the server is not healthy.
        """
        try:
            response = self._client.get("/api/v1/health")
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ExecutionClientError(f"Cannot connect to server: {e}")
        except httpx.TimeoutException as e:
            raise ExecutionClientError(f"Connection timeout: {e}")

    def start(self) -> None:
        """Start the execution session by creating it on the server.

        Raises:
            ExecutionClientError: If session creation fails.
        """
        if self._started:
            return

        try:
            response = self._client.post(
                "/api/v1/sessions",
                json={
                    "session_id": self.session_id,
                    "cwd": self.cwd,
                },
            )
            result = self._handle_response(response)
            self.cwd = result.get("cwd", self.cwd)
            self._started = True
            logger.info(f"Started session {self.session_id} on {self.server_url}")
        except ExecutionClientError as e:
            if e.status_code == 409:
                # Session already exists, consider it started
                self._started = True
                logger.info(f"Session {self.session_id} already exists, reusing")
            else:
                raise

    def stop(self) -> None:
        """Stop the execution session.

        Raises:
            ExecutionClientError: If session stop fails.
        """
        if not self._started:
            return

        try:
            response = self._client.delete(f"/api/v1/sessions/{self.session_id}")
            self._handle_response(response)
            self._started = False
            logger.info(f"Stopped session {self.session_id}")
        except ExecutionClientError as e:
            if e.status_code == 404:
                self._started = False
            else:
                raise
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.debug(f"Server unavailable while stopping session {self.session_id} (expected during shutdown)")
            self._started = False

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session.

        Returns:
            Session information including status, plugins, execution count.

        Raises:
            ExecutionClientError: If the request fails.
        """
        response = self._client.get(f"/api/v1/sessions/{self.session_id}")
        return self._handle_response(response)

    def load_plugin(
        self,
        plugin_name: str,
        plugin_code: str,
        plugin_config: Dict[str, str],
    ) -> None:
        """Load a plugin into the session.

        Args:
            plugin_name: Name of the plugin.
            plugin_code: Plugin source code.
            plugin_config: Plugin configuration dictionary.

        Raises:
            ExecutionClientError: If plugin loading fails.
        """
        response = self._client.post(
            f"/api/v1/sessions/{self.session_id}/plugins",
            json={
                "name": plugin_name,
                "code": plugin_code,
                "config": plugin_config,
            },
        )
        self._handle_response(response)
        logger.info(f"Loaded plugin {plugin_name} in session {self.session_id}")

    def test_plugin(self, plugin_name: str) -> None:
        """Test a loaded plugin.

        Note: This is currently a no-op as the server doesn't have a test endpoint.
        Plugin testing happens during load.

        Args:
            plugin_name: Name of the plugin to test.
        """
        # Plugin testing is implicit during load
        # Could add a dedicated test endpoint in the future
        logger.debug(f"Plugin test for {plugin_name} (implicit during load)")

    def update_session_var(self, session_var_dict: Dict[str, str]) -> None:
        """Update session variables.

        Args:
            session_var_dict: Dictionary of session variables to update.

        Raises:
            ExecutionClientError: If the update fails.
        """
        response = self._client.post(
            f"/api/v1/sessions/{self.session_id}/variables",
            json={"variables": session_var_dict},
        )
        self._handle_response(response)

    def execute_code(
        self,
        exec_id: str,
        code: str,
        on_output: Optional[Callable[[str, str], None]] = None,
    ) -> ExecutionResult:
        """Execute code in the session.

        Args:
            exec_id: Unique execution identifier.
            code: Python code to execute.
            on_output: Optional callback for streaming output.
                       Signature: on_output(stream_name: str, text: str)

        Returns:
            ExecutionResult with the execution outcome.

        Raises:
            ExecutionClientError: If execution fails.
        """
        if on_output is not None:
            # Use streaming execution
            return self._execute_code_streaming(exec_id, code, on_output)
        else:
            # Use synchronous execution
            return self._execute_code_sync(exec_id, code)

    def _execute_code_sync(self, exec_id: str, code: str) -> ExecutionResult:
        """Execute code synchronously.

        Args:
            exec_id: Unique execution identifier.
            code: Python code to execute.

        Returns:
            ExecutionResult with the execution outcome.
        """
        response = self._client.post(
            f"/api/v1/sessions/{self.session_id}/execute",
            json={
                "exec_id": exec_id,
                "code": code,
                "stream": False,
            },
        )
        result = self._handle_response(response)
        return self._parse_execution_result(result, code)

    def _execute_code_streaming(
        self,
        exec_id: str,
        code: str,
        on_output: Callable[[str, str], None],
    ) -> ExecutionResult:
        """Execute code with streaming output.

        Args:
            exec_id: Unique execution identifier.
            code: Python code to execute.
            on_output: Callback for streaming output.

        Returns:
            ExecutionResult with the execution outcome.
        """
        # First, initiate streaming execution
        response = self._client.post(
            f"/api/v1/sessions/{self.session_id}/execute",
            json={
                "exec_id": exec_id,
                "code": code,
                "stream": True,
            },
        )
        init_result = self._handle_response(response)
        stream_url = init_result.get("stream_url", "")

        # Extract path from stream URL
        if stream_url.startswith("http"):
            # Full URL provided
            stream_path = stream_url.replace(self.server_url, "")
        else:
            stream_path = stream_url

        # Connect to SSE stream
        final_result: Optional[Dict[str, Any]] = None

        with self._client.stream("GET", stream_path) as sse_response:
            for line in sse_response.iter_lines():
                if not line:
                    continue

                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    if not data_str:
                        continue

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if event_type == "output":
                        # Stream output to callback
                        stream_type = data.get("type", "stdout")
                        text = data.get("text", "")
                        on_output(stream_type, text)
                    elif event_type == "result":
                        final_result = data
                    elif event_type == "done":
                        break

        if final_result is None:
            raise ExecutionClientError("No result received from streaming execution")

        return self._parse_execution_result(final_result, code)

    def _parse_execution_result(
        self,
        result: Dict[str, Any],
        code: str,
    ) -> ExecutionResult:
        """Parse the execution result from the server response.

        Args:
            result: Server response dictionary.
            code: The executed code.

        Returns:
            ExecutionResult object.
        """
        artifacts: List[ExecutionArtifact] = []
        for art_data in result.get("artifact", []):
            artifact = ExecutionArtifact(
                name=art_data.get("name", ""),
                type=art_data.get("type", "file"),
                mime_type=art_data.get("mime_type", ""),
                original_name=art_data.get("original_name", ""),
                file_name=art_data.get("file_name", ""),
                file_content=art_data.get("file_content", ""),
                file_content_encoding=art_data.get("file_content_encoding", "str"),
                preview=art_data.get("preview", ""),
                download_url=art_data.get("download_url", ""),
            )
            artifacts.append(artifact)

        # Parse log entries
        log: List[Tuple[str, str, str]] = []
        for log_entry in result.get("log", []):
            if isinstance(log_entry, (list, tuple)) and len(log_entry) >= 3:
                log.append((str(log_entry[0]), str(log_entry[1]), str(log_entry[2])))

        # Parse variables
        variables: List[Tuple[str, str]] = []
        for var_entry in result.get("variables", []):
            if isinstance(var_entry, (list, tuple)) and len(var_entry) >= 2:
                variables.append((str(var_entry[0]), str(var_entry[1])))

        return ExecutionResult(
            execution_id=result.get("execution_id", ""),
            code=code,
            is_success=result.get("is_success", False),
            error=result.get("error"),
            output=result.get("output", ""),
            stdout=result.get("stdout", []),
            stderr=result.get("stderr", []),
            log=log,
            artifact=artifacts,
            variables=variables,
        )

    def download_artifact(self, filename: str) -> bytes:
        """Download an artifact file from the server.

        Args:
            filename: Name of the artifact file.

        Returns:
            Raw file content as bytes.

        Raises:
            ExecutionClientError: If download fails.
        """
        response = self._client.get(
            f"/api/v1/sessions/{self.session_id}/artifacts/{filename}",
        )
        if response.status_code >= 400:
            raise ExecutionClientError(
                f"Failed to download artifact: {response.text}",
                status_code=response.status_code,
            )
        return response.content

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._client.close()

    def __enter__(self) -> "ExecutionClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
