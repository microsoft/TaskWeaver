import os
from typing import Any

import click

from taskweaver.cli.util import CliContext


def validate_empty_workspace(ctx: click.Context, param: Any, value: Any) -> str:
    ctx_obj: CliContext = ctx.obj
    value = (
        value if value is not None else ctx_obj.workspace_param if ctx_obj.workspace_param is not None else os.getcwd()
    )
    value_str = str(value)
    is_cur_empty: bool = not os.path.exists(value) or (os.path.isdir(value) and len(os.listdir(value_str)) == 0)
    if ctx_obj.is_workspace_valid:
        if value == ctx_obj.workspace:
            click.echo(
                "The current directory has already been initialized. No need to do it again.",
            )
        else:
            click.echo(
                "The current directory is under a configured workspace.",
            )
        ctx.exit(1)
    if not is_cur_empty:
        click.echo(
            f"The directory {click.format_filename(value)} is not empty. "
            "Please change the working directory to an empty directory for initializing a new workspace. "
            "Refer to --help for more information.",
        )
        ctx.exit(1)
    return value


@click.command(short_help="Initialize TaskWeaver project")
@click.pass_context
@click.option(
    "--project",
    "-p",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    required=False,
    default=None,
    is_eager=True,
    callback=validate_empty_workspace,
)
def init(
    ctx: click.Context,
    project: str,
):
    """Initialize TaskWeaver environment"""
    click.echo(
        f"Initializing TaskWeaver in directory {project}...",
    )
    if not os.path.exists(project):
        os.mkdir(project)

    import zipfile
    from pathlib import Path

    tpl_dir = os.path.join(project, "temp")
    if not os.path.exists(tpl_dir):
        os.mkdir(tpl_dir)

    ext_zip_file = Path(__file__).parent / "taskweaver-project.zip"
    if os.path.exists(ext_zip_file):
        with zipfile.ZipFile(ext_zip_file, "r") as zip_ref:
            # Extract all files to the current directory
            zip_ref.extractall(tpl_dir)
        copy_files(os.path.join(tpl_dir, "project"), project)
    try:
        import shutil

        shutil.rmtree(tpl_dir)
    except Exception:
        click.secho("Failed to remove temporary directory", fg="yellow")
    click.secho(
        f"TaskWeaver project has been initialized successfully at {click.format_filename(project)}.",
        fg="green",
    )


def copy_files(src_dir: str, dst_dir: str):
    # Check if the destination folder exists. If not, create it.
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    import shutil

    # Copy the content of source_folder to destination_folder
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
