"""Server-side session management for the execution server.

This module provides ServerSessionManager which wraps the existing Environment
class and manages multiple execution sessions.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from taskweaver.ces.common import ExecutionResult
from taskweaver.ces.environment import Environment, EnvMode

logger = logging.getLogger(__name__)


@dataclass
class ServerSession:
    """Represents a server-side execution session."""

    session_id: str
    environment: Environment
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    loaded_plugins: List[str] = field(default_factory=list)
    execution_count: int = 0
    cwd: str = ""
    session_dir: str = ""

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()


class ServerSessionManager:
    """Manages multiple execution sessions on the server side.

    This class wraps the Environment class and provides session lifecycle
    management for the HTTP API.
    """

    def __init__(
        self,
        env_id: Optional[str] = None,
        work_dir: Optional[str] = None,
    ) -> None:
        """Initialize the session manager.

        Args:
            env_id: Optional environment identifier.
            work_dir: Working directory for session data. Defaults to current directory.
        """
        self.env_id = env_id or os.getenv("TASKWEAVER_ENV_ID", "server")
        self.work_dir = work_dir or os.getenv("TASKWEAVER_SERVER_WORK_DIR", os.getcwd())
        self._sessions: Dict[str, ServerSession] = {}
        self._lock = threading.RLock()

        # Ensure work directory exists
        os.makedirs(self.work_dir, exist_ok=True)
        logger.info(f"ServerSessionManager initialized with work_dir={self.work_dir}")

    @property
    def active_session_count(self) -> int:
        """Return the number of active sessions."""
        with self._lock:
            return len(self._sessions)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        with self._lock:
            return session_id in self._sessions

    def get_session(self, session_id: str) -> Optional[ServerSession]:
        """Get a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def create_session(
        self,
        session_id: str,
        cwd: Optional[str] = None,
    ) -> ServerSession:
        """Create a new execution session.

        Args:
            session_id: Unique session identifier.
            cwd: Optional working directory for code execution.

        Returns:
            The created ServerSession.

        Raises:
            ValueError: If session already exists.
        """
        with self._lock:
            if session_id in self._sessions:
                raise ValueError(f"Session {session_id} already exists")

            # Create session directory structure
            session_dir = os.path.join(self.work_dir, "sessions", session_id)
            os.makedirs(session_dir, exist_ok=True)

            # Determine cwd
            if cwd is None:
                cwd = os.path.join(session_dir, "cwd")
            os.makedirs(cwd, exist_ok=True)

            # Create Environment for this session (EnvMode.Local only on server)
            environment = Environment(
                env_id=self.env_id,
                env_dir=self.work_dir,
                env_mode=EnvMode.Local,
            )

            # Start the kernel session
            environment.start_session(
                session_id=session_id,
                session_dir=session_dir,
                cwd=cwd,
            )

            session = ServerSession(
                session_id=session_id,
                environment=environment,
                cwd=cwd,
                session_dir=session_dir,
            )
            self._sessions[session_id] = session

            logger.info(f"Created session {session_id} with cwd={cwd}")
            return session

    def stop_session(self, session_id: str) -> None:
        """Stop and remove a session.

        Args:
            session_id: Session identifier.

        Raises:
            KeyError: If session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")

            session = self._sessions[session_id]
            try:
                session.environment.stop_session(session_id)
            except Exception as e:
                logger.error(f"Error stopping session {session_id}: {e}")
            finally:
                del self._sessions[session_id]
                logger.info(f"Stopped session {session_id}")

    def load_plugin(
        self,
        session_id: str,
        plugin_name: str,
        plugin_code: str,
        plugin_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Load a plugin into a session.

        Args:
            session_id: Session identifier.
            plugin_name: Name of the plugin.
            plugin_code: Plugin source code.
            plugin_config: Optional plugin configuration.

        Raises:
            KeyError: If session does not exist.
        """
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")

        session.environment.load_plugin(
            session_id=session_id,
            plugin_name=plugin_name,
            plugin_impl=plugin_code,
            plugin_config=plugin_config,
        )

        if plugin_name not in session.loaded_plugins:
            session.loaded_plugins.append(plugin_name)

        session.update_activity()
        logger.info(f"Loaded plugin {plugin_name} in session {session_id}")

    def execute_code(
        self,
        session_id: str,
        exec_id: str,
        code: str,
        on_output: Optional[Callable[[str, str], None]] = None,
    ) -> ExecutionResult:
        """Execute code in a session.

        Args:
            session_id: Session identifier.
            exec_id: Execution identifier.
            code: Python code to execute.
            on_output: Optional callback for streaming output.

        Returns:
            ExecutionResult from the code execution.

        Raises:
            KeyError: If session does not exist.
        """
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")

        result = session.environment.execute_code(
            session_id=session_id,
            code=code,
            exec_id=exec_id,
            on_output=on_output,
        )

        # Save inline artifacts to disk so they can be downloaded via HTTP
        self._save_inline_artifacts(session, result)

        session.execution_count += 1
        session.update_activity()

        return result

    async def execute_code_async(
        self,
        session_id: str,
        exec_id: str,
        code: str,
        on_output: Optional[Callable[[str, str], None]] = None,
    ) -> ExecutionResult:
        """Execute code asynchronously in a session.

        This runs the synchronous execute_code in a thread pool to avoid
        blocking the async event loop.

        Args:
            session_id: Session identifier.
            exec_id: Execution identifier.
            code: Python code to execute.
            on_output: Optional callback for streaming output.

        Returns:
            ExecutionResult from the code execution.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute_code(session_id, exec_id, code, on_output),
        )

    def _save_inline_artifacts(
        self,
        session: ServerSession,
        result: ExecutionResult,
    ) -> None:
        """Save inline artifacts (base64 content) to disk for HTTP download.

        This ensures all artifacts can be accessed via the download endpoint,
        regardless of whether they were generated inline (e.g., plt.show())
        or saved to disk (e.g., plt.savefig()).

        Args:
            session: The server session.
            result: Execution result containing artifacts.
        """
        for artifact in result.artifact:
            # Skip if no inline content or already has a file_name
            if not artifact.file_content:
                continue
            if artifact.file_name:
                continue

            # Determine file extension from mime type
            ext = ".bin"
            if artifact.mime_type:
                mime_to_ext = {
                    "image/png": ".png",
                    "image/jpeg": ".jpg",
                    "image/gif": ".gif",
                    "image/svg+xml": ".svg",
                    "text/html": ".html",
                    "application/json": ".json",
                }
                ext = mime_to_ext.get(artifact.mime_type, ".bin")

            # Generate filename from artifact name
            file_name = f"{artifact.name}_image{ext}"
            file_path = os.path.join(session.cwd, file_name)

            try:
                # Decode and save the content
                if artifact.file_content_encoding == "base64":
                    content = base64.b64decode(artifact.file_content)
                    with open(file_path, "wb") as f:
                        f.write(content)
                else:
                    # String content (e.g., SVG)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(artifact.file_content)

                # Update artifact with the file_name so download URL can be constructed
                artifact.file_name = file_name
                artifact.original_name = file_name
                logger.debug(f"Saved inline artifact to {file_path}")

            except Exception as e:
                logger.warning(f"Failed to save inline artifact {artifact.name}: {e}")

    def update_session_variables(
        self,
        session_id: str,
        variables: Dict[str, str],
    ) -> None:
        """Update session variables.

        Args:
            session_id: Session identifier.
            variables: Variables to update.

        Raises:
            KeyError: If session does not exist.
        """
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")

        session.environment.update_session_var(session_id, variables)
        session.update_activity()

    def get_artifact_path(self, session_id: str, filename: str) -> Optional[str]:
        """Get the full path to an artifact file.

        Args:
            session_id: Session identifier.
            filename: Artifact filename.

        Returns:
            Full path to the artifact, or None if not found.
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        # Artifacts are typically in the cwd directory
        artifact_path = os.path.join(session.cwd, filename)
        if os.path.isfile(artifact_path):
            return artifact_path

        # Also check session_dir/cwd
        artifact_path = os.path.join(session.session_dir, "cwd", filename)
        if os.path.isfile(artifact_path):
            return artifact_path

        return None

    def cleanup_all(self) -> None:
        """Stop all sessions and clean up resources."""
        with self._lock:
            session_ids = list(self._sessions.keys())

        for session_id in session_ids:
            try:
                self.stop_session(session_id)
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {e}")

        logger.info("Cleaned up all sessions")
