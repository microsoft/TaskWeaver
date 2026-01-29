"""Server subcommand for starting the Code Execution Server."""

import os

import click

from taskweaver.cli.util import CliContext, require_workspace


@click.command()
@require_workspace()
@click.pass_context
@click.option(
    "--host",
    type=str,
    default=None,
    help="Host to bind to (default: localhost)",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Port to bind to (default: 8000)",
)
@click.option(
    "--api-key",
    type=str,
    default=None,
    help="API key for authentication (optional for localhost)",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    help="Log level (default: info)",
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Enable auto-reload for development",
)
def server(
    ctx: click.Context,
    host: str,
    port: int,
    api_key: str,
    log_level: str,
    reload: bool,
):
    """Start the Code Execution Server.

    The server handles code execution requests from TaskWeaver sessions.
    Start this server first, then run 'taskweaver chat' in another terminal.

    \b
    Example:
        taskweaver -p ./project server --port 8000
        taskweaver -p ./project chat --server-url http://localhost:8000
    """
    ctx_obj: CliContext = ctx.obj
    workspace = ctx_obj.workspace
    assert workspace is not None

    from taskweaver.config.config_mgt import AppConfigSource

    app_config_file = os.path.join(workspace, "taskweaver_config.json")
    config_src = AppConfigSource(
        config_file_path=app_config_file if os.path.exists(app_config_file) else None,
        config={},
        app_base_path=workspace,
    )

    def get_config(key: str, default):
        return config_src.json_file_store.get(key, default)

    effective_host = host or get_config("execution_service.server.host", "localhost")
    effective_port = port or get_config("execution_service.server.port", 8000)
    effective_api_key = api_key or get_config("execution_service.server.api_key", None)
    work_dir = get_config(
        "execution_service.env_dir",
        os.path.join(workspace, "env"),
    )

    os.makedirs(work_dir, exist_ok=True)

    os.environ["TASKWEAVER_SERVER_HOST"] = effective_host
    os.environ["TASKWEAVER_SERVER_PORT"] = str(effective_port)
    os.environ["TASKWEAVER_SERVER_WORK_DIR"] = work_dir
    if effective_api_key:
        os.environ["TASKWEAVER_SERVER_API_KEY"] = effective_api_key

    click.echo()
    click.echo("=" * 60)
    click.echo("  TaskWeaver Code Execution Server")
    click.echo("=" * 60)
    click.echo(f"  Project:   {ctx_obj.workspace}")
    click.echo(f"  Host:      {effective_host}")
    click.echo(f"  Port:      {effective_port}")
    click.echo(f"  URL:       http://{effective_host}:{effective_port}")
    click.echo(f"  Health:    http://{effective_host}:{effective_port}/api/v1/health")
    click.echo(f"  Work Dir:  {work_dir}")
    click.echo(f"  API Key:   {'configured' if effective_api_key else 'not required (localhost)'}")
    click.echo("=" * 60)
    click.echo()
    click.echo("To connect a chat session, run in another terminal:")
    click.echo(f"  taskweaver -p {ctx_obj.workspace} chat --server-url http://{effective_host}:{effective_port}")
    click.echo()

    try:
        import uvicorn
    except ImportError:
        click.secho(
            "Error: uvicorn is required to run the server. " "Please install it with: pip install uvicorn",
            fg="red",
        )
        raise SystemExit(1)

    try:
        import fastapi  # noqa: F401
    except ImportError:
        click.secho(
            "Error: fastapi is required to run the server. " "Please install it with: pip install fastapi",
            fg="red",
        )
        raise SystemExit(1)

    uvicorn.run(
        "taskweaver.ces.server.app:app",
        host=effective_host,
        port=effective_port,
        reload=reload,
        log_level=log_level,
    )
