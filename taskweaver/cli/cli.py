import click

from ..app import TaskWeaverApp
from .chat import chat
from .init import init
from .util import CliContext, get_ascii_banner
from .web import web


@click.group(
    name="taskweaver",
    help=f"\b\n{get_ascii_banner()}\nTaskWeaver",
    invoke_without_command=True,
    commands=[init, chat, web],
)
@click.pass_context
@click.version_option(package_name="taskweaver")
@click.option(
    "--project",
    "-p",
    help="Path to the project directory",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    required=False,
    default=None,
)
def taskweaver(ctx: click.Context, project: str):
    workspace_base, is_valid, is_empty = TaskWeaverApp.discover_app_dir(project)

    # subcommand_target = ctx.invoked_subcommand if ctx.invoked_subcommand is not None else "chat"

    ctx.obj = CliContext(
        workspace=workspace_base,
        workspace_param=project,
        is_workspace_valid=is_valid,
        is_workspace_empty=is_empty,
    )
    if not ctx.invoked_subcommand:
        ctx.invoke(chat)
        return
