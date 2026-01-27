"""CLI entry point for the TaskWeaver Execution Server.

Usage:
    python -m taskweaver.ces.server [OPTIONS]

Options:
    --host TEXT      Host to bind to [default: localhost]
    --port INTEGER   Port to bind to [default: 8000]
    --api-key TEXT   API key for authentication (optional)
    --work-dir PATH  Working directory for session data [default: current dir]
    --reload         Enable auto-reload for development
    --log-level TEXT Log level [default: info]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys


def configure_logging(level: str) -> None:
    """Configure logging for the server."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    """Main entry point for the server CLI."""
    parser = argparse.ArgumentParser(
        description="TaskWeaver Code Execution Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("TASKWEAVER_SERVER_HOST", "localhost"),
        help="Host to bind to",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("TASKWEAVER_SERVER_PORT", "8000")),
        help="Port to bind to",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("TASKWEAVER_SERVER_API_KEY"),
        help="API key for authentication (optional for localhost)",
    )

    parser.add_argument(
        "--work-dir",
        type=str,
        default=os.getenv("TASKWEAVER_SERVER_WORK_DIR", os.getcwd()),
        help="Working directory for session data",
    )

    parser.add_argument(
        "--env-id",
        type=str,
        default=os.getenv("TASKWEAVER_ENV_ID", "server"),
        help="Environment identifier",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("TASKWEAVER_LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level",
    )

    args = parser.parse_args()

    # Configure logging
    configure_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Set environment variables for the app to pick up
    os.environ["TASKWEAVER_SERVER_HOST"] = args.host
    os.environ["TASKWEAVER_SERVER_PORT"] = str(args.port)
    os.environ["TASKWEAVER_SERVER_WORK_DIR"] = args.work_dir
    os.environ["TASKWEAVER_ENV_ID"] = args.env_id

    if args.api_key:
        os.environ["TASKWEAVER_SERVER_API_KEY"] = args.api_key

    print()
    print("=" * 60)
    print("  TaskWeaver Code Execution Server")
    print("=" * 60)
    print(f"  Host:      {args.host}")
    print(f"  Port:      {args.port}")
    print(f"  URL:       http://{args.host}:{args.port}")
    print(f"  Health:    http://{args.host}:{args.port}/api/v1/health")
    print(f"  Work Dir:  {args.work_dir}")
    print(f"  API Key:   {'configured' if args.api_key else 'not required (localhost)'}")
    print("=" * 60)
    print()

    logger.info("Starting TaskWeaver Execution Server")

    try:
        import uvicorn
    except ImportError:
        logger.error(
            "uvicorn is required to run the server. " "Please install it with: pip install uvicorn",
        )
        sys.exit(1)

    # Run the server
    uvicorn.run(
        "taskweaver.ces.server.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
