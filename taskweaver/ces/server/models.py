"""Pydantic request/response models for the execution server API."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

# =============================================================================
# Request Models
# =============================================================================


class CreateSessionRequest(BaseModel):
    """Request to create a new execution session."""

    session_id: str = Field(..., description="Unique session identifier")
    cwd: Optional[str] = Field(None, description="Working directory for code execution")


class LoadPluginRequest(BaseModel):
    """Request to load a plugin into a session."""

    name: str = Field(..., description="Plugin name")
    code: str = Field(..., description="Plugin source code")
    config: Dict[str, Any] = Field(default_factory=dict, description="Plugin configuration")


class ExecuteCodeRequest(BaseModel):
    """Request to execute code in a session."""

    exec_id: str = Field(..., description="Unique execution identifier")
    code: str = Field(..., description="Python code to execute")
    stream: bool = Field(False, description="Enable streaming output via SSE")


class UpdateVariablesRequest(BaseModel):
    """Request to update session variables."""

    variables: Dict[str, str] = Field(..., description="Session variables to update")


# =============================================================================
# Response Models
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy"] = "healthy"
    version: str = Field(..., description="Server version")
    active_sessions: int = Field(..., description="Number of active sessions")


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session_id: str = Field(..., description="Session identifier")
    status: Literal["created"] = "created"
    cwd: str = Field(..., description="Actual working directory")


class StopSessionResponse(BaseModel):
    """Response after stopping a session."""

    session_id: str = Field(..., description="Session identifier")
    status: Literal["stopped"] = "stopped"


class SessionInfoResponse(BaseModel):
    """Detailed session information."""

    session_id: str = Field(..., description="Session identifier")
    status: Literal["running", "stopped"] = Field(..., description="Session status")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    loaded_plugins: List[str] = Field(default_factory=list, description="Loaded plugin names")
    execution_count: int = Field(0, description="Number of executions")
    cwd: str = Field(..., description="Working directory")


class LoadPluginResponse(BaseModel):
    """Response after loading a plugin."""

    name: str = Field(..., description="Plugin name")
    status: Literal["loaded"] = "loaded"


class ArtifactModel(BaseModel):
    """Model representing an execution artifact (image, chart, etc.)."""

    name: str = Field(..., description="Artifact name")
    type: str = Field(..., description="Artifact type (image, file, chart, svg, etc.)")
    mime_type: str = Field("", description="MIME type of the artifact")
    original_name: str = Field("", description="Original file name")
    file_name: str = Field("", description="Saved file name")
    file_content: Optional[str] = Field(None, description="Base64 or string content for small files")
    file_content_encoding: Optional[str] = Field(None, description="Encoding: 'str' or 'base64'")
    preview: str = Field("", description="Text preview of the artifact")
    download_url: Optional[str] = Field(None, description="URL to download large files")


class ExecuteCodeResponse(BaseModel):
    """Response from synchronous code execution."""

    execution_id: str = Field(..., description="Execution identifier")
    is_success: bool = Field(..., description="Whether execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    output: Any = Field(None, description="Execution output/result")
    stdout: List[str] = Field(default_factory=list, description="Standard output lines")
    stderr: List[str] = Field(default_factory=list, description="Standard error lines")
    log: List[Tuple[str, str, str]] = Field(default_factory=list, description="Log entries")
    artifact: List[ArtifactModel] = Field(default_factory=list, description="Generated artifacts")
    variables: List[Tuple[str, str]] = Field(default_factory=list, description="Session variables")


class ExecuteStreamResponse(BaseModel):
    """Response when streaming is enabled (returns stream URL)."""

    execution_id: str = Field(..., description="Execution identifier")
    stream_url: str = Field(..., description="SSE stream URL")


class UpdateVariablesResponse(BaseModel):
    """Response after updating session variables."""

    status: Literal["updated"] = "updated"
    variables: Dict[str, str] = Field(..., description="Updated variables")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")


# =============================================================================
# SSE Event Models (for streaming)
# =============================================================================


class OutputEvent(BaseModel):
    """SSE event for stdout/stderr output during execution."""

    type: Literal["stdout", "stderr"] = Field(..., description="Output stream type")
    text: str = Field(..., description="Output text")


class ResultEvent(BaseModel):
    """SSE event for final execution result."""

    execution_id: str = Field(..., description="Execution identifier")
    is_success: bool = Field(..., description="Whether execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    output: Any = Field(None, description="Execution output/result")
    stdout: List[str] = Field(default_factory=list, description="Standard output lines")
    stderr: List[str] = Field(default_factory=list, description="Standard error lines")
    log: List[Tuple[str, str, str]] = Field(default_factory=list, description="Log entries")
    artifact: List[ArtifactModel] = Field(default_factory=list, description="Generated artifacts")
    variables: List[Tuple[str, str]] = Field(default_factory=list, description="Session variables")


# =============================================================================
# Utility Functions
# =============================================================================


def artifact_from_execution(artifact: Any) -> ArtifactModel:
    """Convert an ExecutionArtifact to ArtifactModel."""
    return ArtifactModel(
        name=artifact.name,
        type=artifact.type,
        mime_type=artifact.mime_type,
        original_name=artifact.original_name,
        file_name=artifact.file_name,
        file_content=artifact.file_content if artifact.file_content else None,
        file_content_encoding=artifact.file_content_encoding if artifact.file_content else None,
        preview=artifact.preview,
    )


def execution_result_to_response(
    result: Any,
    session_id: str,
    base_url: str = "",
) -> ExecuteCodeResponse:
    """Convert an ExecutionResult to ExecuteCodeResponse.

    Args:
        result: ExecutionResult from Environment.execute_code()
        session_id: Session identifier for constructing download URLs
        base_url: Base URL for constructing artifact download URLs

    Returns:
        ExecuteCodeResponse model
    """
    artifacts = []
    for art in result.artifact:
        artifact_model = artifact_from_execution(art)
        # Always set download URL for artifacts with file_name
        # The session manager saves inline artifacts to disk, so all artifacts should have file_name
        if art.file_name:
            artifact_model.download_url = f"{base_url}/api/v1/sessions/{session_id}/artifacts/{art.file_name}"
        artifacts.append(artifact_model)

    return ExecuteCodeResponse(
        execution_id=result.execution_id,
        is_success=result.is_success,
        error=result.error,
        output=result.output,
        stdout=result.stdout,
        stderr=result.stderr,
        log=result.log,
        artifact=artifacts,
        variables=result.variables,
    )
