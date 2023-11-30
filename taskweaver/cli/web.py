import click

from taskweaver.cli.util import require_workspace


@click.command()
@require_workspace()
@click.option(
    "--host",
    "-h",
    default="localhost",
    help="Host to run TaskWeaver web server",
    type=str,
    show_default=True,
)
@click.option("--port", "-p", default=8080, help="Port to run TaskWeaver web server", type=int, show_default=True)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    help="Run TaskWeaver web server in debug mode",
    show_default=True,
)
@click.option(
    "--open/--no-open",
    "-o/-n",
    is_flag=True,
    default=True,
    help="Open TaskWeaver web server in browser",
    show_default=True,
)
def web(host: str, port: int, debug: bool, open: bool):
    """Start TaskWeaver web server"""

    from taskweaver.chat.web import start_web_service

    if not debug:
        # debug mode will restart app iteratively, skip the plugin listing
        # display_enabled_examples_plugins()
        pass

    def post_app_start():
        if open:
            click.secho("launching web browser...", fg="green")
            open_url = f"http://{'localhost' if host == '0.0.0.0' else host}:{port}"
            click.launch(open_url)

    start_web_service(
        host,
        port,
        is_debug=debug,
        post_app_start=post_app_start if open else None,
    )
