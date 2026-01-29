import click

from taskweaver.cli.util import CliContext, get_ascii_banner, require_workspace


@click.command()
@require_workspace()
@click.pass_context
@click.option(
    "--server-url",
    help="URL of the Code Execution Server (overrides --server-url from parent command)",
    type=str,
    required=False,
    default=None,
)
def chat(ctx: click.Context, server_url: str):
    """Chat with TaskWeaver in command line."""
    ctx_obj: CliContext = ctx.obj

    from taskweaver.chat.console import chat_taskweaver

    effective_server_url = server_url or ctx_obj.server_url

    click.echo(get_ascii_banner())
    chat_taskweaver(ctx_obj.workspace, server_url=effective_server_url)
