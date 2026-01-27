"""TaskWeaver Code Execution Server.

This package provides an HTTP API for remote code execution,
wrapping the existing Environment class behind a FastAPI server.
"""

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
)
from taskweaver.ces.server.session_manager import ServerSession, ServerSessionManager

__all__ = [
    # Models
    "ArtifactModel",
    "CreateSessionRequest",
    "CreateSessionResponse",
    "ErrorResponse",
    "ExecuteCodeRequest",
    "ExecuteCodeResponse",
    "ExecuteStreamResponse",
    "HealthResponse",
    "LoadPluginRequest",
    "LoadPluginResponse",
    "OutputEvent",
    "ResultEvent",
    "SessionInfoResponse",
    "StopSessionResponse",
    "UpdateVariablesRequest",
    "UpdateVariablesResponse",
    # Session Manager
    "ServerSession",
    "ServerSessionManager",
]
