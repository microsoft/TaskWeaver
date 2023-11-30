import os
import shutil
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

    def get_dir(*dir: str):
        return os.path.join(project, *dir)

    dir_list = [
        "codeinterpreter_examples",
        "planner_examples",
        "plugins",
        "config",
        "workspace",
    ]
    for dir in dir_list:
        dir_path = get_dir(dir)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    init_temp_dir = get_dir("init")
    import zipfile
    from pathlib import Path

    tpl_dir = os.path.join(init_temp_dir, "template")
    ext_zip_file = Path(__file__).parent / "taskweaver-ext.zip"
    if os.path.exists(ext_zip_file):
        with zipfile.ZipFile(ext_zip_file, "r") as zip_ref:
            # Extract all files to the current directory
            zip_ref.extractall(tpl_dir)

        tpl_planner_example_dir = os.path.join(tpl_dir, "taskweaver-ext", "planner_examples")
        tpl_ci_example_dir = os.path.join(tpl_dir, "taskweaver-ext", "codeinterpreter_examples")
        tpl_plugin_dir = os.path.join(tpl_dir, "taskweaver-ext", "plugins")
        tpl_config_dir = os.path.join(tpl_dir, "taskweaver-ext")
        planner_example_dir = get_dir("planner_examples")
        ci_example_dir = get_dir("codeinterpreter_examples")
        plugin_dir = get_dir("plugins")
        copy_files(tpl_planner_example_dir, planner_example_dir)
        copy_files(tpl_ci_example_dir, ci_example_dir)
        copy_files(tpl_plugin_dir, plugin_dir)
        copy_file(tpl_config_dir, "taskweaver_config.json", get_dir(""))

    try:
        shutil.rmtree(init_temp_dir)
    except Exception:
        click.secho("Failed to remove temporary directory", fg="yellow")
    click.secho(
        f"TaskWeaver project has been initialized successfully at {click.format_filename(project)}.",
        fg="green",
    )


def copy_files(src_dir: str, dst_dir: str):
    # Get a list of all files in the source directory
    files = os.listdir(src_dir)

    # Loop through the files and copy each one to the destination directory
    for file in files:
        if os.path.isfile(os.path.join(src_dir, file)):
            copy_file(src_dir, file, dst_dir)


def copy_file(src_dir: str, filename: str, dst_dir: str):
    shutil.copy(
        os.path.join(src_dir, filename),
        os.path.join(dst_dir, filename),
    )
