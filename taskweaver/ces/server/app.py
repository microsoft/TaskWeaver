"""FastAPI application setup for the execution server."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taskweaver.ces.server.routes import router
from taskweaver.ces.server.session_manager import ServerSessionManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle (startup and shutdown)."""
    # Startup
    logger.info("Starting TaskWeaver Execution Server")

    # Initialize session manager from app state config
    work_dir = getattr(app.state, "work_dir", None) or os.getcwd()
    env_id = getattr(app.state, "env_id", None) or "server"

    session_manager = ServerSessionManager(
        env_id=env_id,
        work_dir=work_dir,
    )
    app.state.session_manager = session_manager

    logger.info(f"Session manager initialized with work_dir={work_dir}")

    yield

    # Shutdown
    logger.info("Shutting down TaskWeaver Execution Server")
    session_manager.cleanup_all()


def create_app(
    api_key: Optional[str] = None,
    work_dir: Optional[str] = None,
    env_id: Optional[str] = None,
    cors_origins: Optional[list[str]] = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        api_key: Optional API key for authentication. If not provided,
                 authentication is disabled for localhost.
        work_dir: Working directory for session data.
        env_id: Environment identifier.
        cors_origins: List of allowed CORS origins. Defaults to allowing all.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="TaskWeaver Execution Server",
        description="HTTP API for remote code execution with Jupyter kernels",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Store configuration in app state for lifespan to use
    app.state.api_key = api_key or os.getenv("TASKWEAVER_SERVER_API_KEY")
    app.state.work_dir = work_dir or os.getenv("TASKWEAVER_SERVER_WORK_DIR")
    app.state.env_id = env_id or os.getenv("TASKWEAVER_ENV_ID")

    # Configure CORS
    if cors_origins is None:
        cors_origins = ["*"]  # Allow all origins by default for local dev

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router)

    return app


# Default app instance for uvicorn
app = create_app()
