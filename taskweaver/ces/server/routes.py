"""FastAPI route handlers for the execution server."""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from taskweaver.ces.server.models import (
    ArtifactModel,
    CreateSessionRequest,
    CreateSessionResponse,
    ExecuteCodeRequest,
    ExecuteCodeResponse,
    ExecuteStreamResponse,
    HealthResponse,
    LoadPluginRequest,
    LoadPluginResponse,
    SessionInfoResponse,
    StopSessionResponse,
    UpdateVariablesRequest,
    UpdateVariablesResponse,
    UploadFileRequest,
    UploadFileResponse,
    execution_result_to_response,
)
from taskweaver.ces.server.session_manager import ServerSessionManager

logger = logging.getLogger(__name__)

# API Router with versioned prefix
router = APIRouter(prefix="/api/v1")

# Server version
SERVER_VERSION = "0.1.0"


def get_session_manager(request: Request) -> ServerSessionManager:
    """Dependency to get the session manager from app state."""
    return request.app.state.session_manager


def get_api_key(request: Request) -> Optional[str]:
    """Dependency to get the configured API key from app state."""
    return getattr(request.app.state, "api_key", None)


def verify_api_key(
    request: Request,
    api_key: Optional[str] = Depends(get_api_key),
) -> None:
    """Verify the API key if one is configured.

    API key is optional for localhost connections.
    """
    if not api_key:
        # No API key configured, allow all requests
        return

    # Check if request is from localhost (API key optional)
    client_host = request.client.host if request.client else None
    if client_host in ("127.0.0.1", "localhost", "::1"):
        # Still check API key if provided
        provided_key = request.headers.get("X-API-Key")
        if provided_key and provided_key != api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return

    # Non-localhost requests require API key
    provided_key = request.headers.get("X-API-Key")
    if not provided_key:
        raise HTTPException(status_code=401, detail="API key required")
    if provided_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# =============================================================================
# Health Check
# =============================================================================


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> HealthResponse:
    """Health check endpoint (no authentication required)."""
    return HealthResponse(
        status="healthy",
        version=SERVER_VERSION,
        active_sessions=session_manager.active_session_count,
    )


# =============================================================================
# Session Management
# =============================================================================


@router.post(
    "/sessions",
    response_model=CreateSessionResponse,
    status_code=201,
    dependencies=[Depends(verify_api_key)],
)
async def create_session(
    request: CreateSessionRequest,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> CreateSessionResponse:
    """Create a new execution session."""
    if session_manager.session_exists(request.session_id):
        raise HTTPException(
            status_code=409,
            detail=f"Session {request.session_id} already exists",
        )

    try:
        session = session_manager.create_session(
            session_id=request.session_id,
            cwd=request.cwd,
        )
        return CreateSessionResponse(
            session_id=session.session_id,
            status="created",
            cwd=session.cwd,
        )
    except Exception as e:
        logger.error(f"Failed to create session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/sessions/{session_id}",
    response_model=StopSessionResponse,
    dependencies=[Depends(verify_api_key)],
)
async def stop_session(
    session_id: str,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> StopSessionResponse:
    """Stop and remove an execution session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        session_manager.stop_session(session_id)
        return StopSessionResponse(session_id=session_id, status="stopped")
    except Exception as e:
        logger.error(f"Failed to stop session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sessions/{session_id}",
    response_model=SessionInfoResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_session_info(
    session_id: str,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> SessionInfoResponse:
    """Get information about a session."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return SessionInfoResponse(
        session_id=session.session_id,
        status="running",
        created_at=session.created_at,
        last_activity=session.last_activity,
        loaded_plugins=session.loaded_plugins,
        execution_count=session.execution_count,
        cwd=session.cwd,
    )


# =============================================================================
# Plugin Management
# =============================================================================


@router.post(
    "/sessions/{session_id}/plugins",
    response_model=LoadPluginResponse,
    dependencies=[Depends(verify_api_key)],
)
async def load_plugin(
    session_id: str,
    request: LoadPluginRequest,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> LoadPluginResponse:
    """Load a plugin into a session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        session_manager.load_plugin(
            session_id=session_id,
            plugin_name=request.name,
            plugin_code=request.code,
            plugin_config=request.config,
        )
        return LoadPluginResponse(name=request.name, status="loaded")
    except Exception as e:
        logger.error(f"Failed to load plugin {request.name} in session {session_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to load plugin: {e}")


# =============================================================================
# Code Execution
# =============================================================================


# Store for pending streaming executions
_pending_streams: Dict[str, asyncio.Queue[Dict[str, Any]]] = {}


@router.post(
    "/sessions/{session_id}/execute",
    response_model=None,  # Can return ExecuteCodeResponse or ExecuteStreamResponse
    dependencies=[Depends(verify_api_key)],
)
async def execute_code(
    session_id: str,
    request: ExecuteCodeRequest,
    http_request: Request,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> ExecuteCodeResponse | ExecuteStreamResponse:
    """Execute code in a session.

    If stream=false (default), returns the full result synchronously.
    If stream=true, returns a stream URL for SSE-based streaming.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    base_url = str(http_request.base_url).rstrip("/")

    if request.stream:
        # Streaming mode: set up queue and return stream URL
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        stream_key = f"{session_id}:{request.exec_id}"
        _pending_streams[stream_key] = queue

        # Start execution in background
        asyncio.create_task(
            _execute_streaming(
                session_manager,
                session_id,
                request.exec_id,
                request.code,
                queue,
                stream_key,
                base_url,
            ),
        )
        stream_url = f"{base_url}/api/v1/sessions/{session_id}/execute/{request.exec_id}/stream"
        return ExecuteStreamResponse(
            execution_id=request.exec_id,
            stream_url=stream_url,
        )

    # Synchronous execution
    try:
        result = await session_manager.execute_code_async(
            session_id=session_id,
            exec_id=request.exec_id,
            code=request.code,
        )
        base_url = str(http_request.base_url).rstrip("/")
        return execution_result_to_response(result, session_id, base_url)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        logger.error(f"Execution failed in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_streaming(
    session_manager: ServerSessionManager,
    session_id: str,
    exec_id: str,
    code: str,
    queue: asyncio.Queue[Dict[str, Any]],
    stream_key: str,
    base_url: str,
) -> None:
    """Execute code and stream output to the queue."""
    loop = asyncio.get_event_loop()

    def on_output(stream_name: str, text: str) -> None:
        """Callback for streaming output."""
        asyncio.run_coroutine_threadsafe(
            queue.put({"event": "output", "data": {"type": stream_name, "text": text}}),
            loop,
        )

    try:
        result = await session_manager.execute_code_async(
            session_id=session_id,
            exec_id=exec_id,
            code=code,
            on_output=on_output,
        )

        # Convert artifacts for the response
        artifacts = []
        for art in result.artifact:
            artifact_model = ArtifactModel(
                name=art.name,
                type=art.type,
                mime_type=art.mime_type,
                original_name=art.original_name,
                file_name=art.file_name,
                file_content=art.file_content if art.file_content else None,
                file_content_encoding=art.file_content_encoding if art.file_content else None,
                preview=art.preview,
            )
            # Set download URL for artifacts with file_name
            if art.file_name:
                artifact_model.download_url = f"{base_url}/api/v1/sessions/{session_id}/artifacts/{art.file_name}"
            artifacts.append(artifact_model.model_dump())

        # Send result event
        await queue.put(
            {
                "event": "result",
                "data": {
                    "execution_id": result.execution_id,
                    "is_success": result.is_success,
                    "error": result.error,
                    "output": result.output,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "log": result.log,
                    "artifact": artifacts,
                    "variables": result.variables,
                },
            },
        )
    except Exception as e:
        logger.error(f"Streaming execution failed: {e}")
        await queue.put(
            {
                "event": "result",
                "data": {
                    "execution_id": exec_id,
                    "is_success": False,
                    "error": str(e),
                    "output": None,
                    "stdout": [],
                    "stderr": [],
                    "log": [],
                    "artifact": [],
                    "variables": [],
                },
            },
        )
    finally:
        # Signal end of stream
        await queue.put({"event": "done", "data": {}})
        # Clean up after a delay to allow client to receive final events
        await asyncio.sleep(5)
        _pending_streams.pop(stream_key, None)


@router.get(
    "/sessions/{session_id}/execute/{exec_id}/stream",
    dependencies=[Depends(verify_api_key)],
)
async def stream_execution(
    session_id: str,
    exec_id: str,
) -> StreamingResponse:
    """Stream execution output via Server-Sent Events (SSE)."""
    stream_key = f"{session_id}:{exec_id}"
    queue = _pending_streams.get(stream_key)

    if queue is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active stream for execution {exec_id}",
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from the queue."""
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=300)
                event_type = item["event"]
                data = json.dumps(item["data"])
                yield f"event: {event_type}\ndata: {data}\n\n"

                if event_type == "done":
                    break
            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# Session Variables
# =============================================================================


@router.post(
    "/sessions/{session_id}/variables",
    response_model=UpdateVariablesResponse,
    dependencies=[Depends(verify_api_key)],
)
async def update_variables(
    session_id: str,
    request: UpdateVariablesRequest,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> UpdateVariablesResponse:
    """Update session variables."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        session_manager.update_session_variables(session_id, request.variables)
        return UpdateVariablesResponse(status="updated", variables=request.variables)
    except Exception as e:
        logger.error(f"Failed to update variables in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/sessions/{session_id}/files",
    response_model=UploadFileResponse,
    dependencies=[Depends(verify_api_key)],
)
async def upload_file(
    session_id: str,
    request: UploadFileRequest,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> UploadFileResponse:
    """Upload a file to a session's working directory."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        import base64

        if request.encoding == "base64":
            content = base64.b64decode(request.content)
        else:
            content = request.content.encode("utf-8")

        file_path = session_manager.upload_file(session_id, request.filename, content)
        return UploadFileResponse(
            filename=request.filename,
            status="uploaded",
            path=file_path,
        )
    except Exception as e:
        logger.error(f"Failed to upload file {request.filename} to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Artifacts
# =============================================================================


@router.get(
    "/sessions/{session_id}/artifacts/{filename:path}",
    dependencies=[Depends(verify_api_key)],
)
async def download_artifact(
    session_id: str,
    filename: str,
    session_manager: ServerSessionManager = Depends(get_session_manager),
) -> FileResponse:
    """Download an artifact file from a session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    artifact_path = session_manager.get_artifact_path(session_id, filename)
    if artifact_path is None:
        raise HTTPException(status_code=404, detail=f"Artifact {filename} not found")

    # Determine mime type
    mime_type, _ = mimetypes.guess_type(artifact_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    return FileResponse(
        path=artifact_path,
        filename=os.path.basename(filename),
        media_type=mime_type,
    )
