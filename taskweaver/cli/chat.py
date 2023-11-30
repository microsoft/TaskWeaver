import click

from taskweaver.cli.util import CliContext, get_ascii_banner, require_workspace


@click.command()
@require_workspace()
@click.pass_context
def chat(ctx: click.Context):
    """
    Chat with TaskWeaver in command line
    """

    ctx_obj: CliContext = ctx.obj

    from taskweaver.chat.console import chat_taskweaver

    click.echo(get_ascii_banner())
    chat_taskweaver(ctx_obj.workspace)
