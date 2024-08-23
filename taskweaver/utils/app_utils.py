from os import listdir, path
from typing import Optional, Tuple


def discover_app_dir(
    app_dir: Optional[str] = None,
) -> Tuple[str, bool, bool]:
    """
    Discover the app directory from the given path or the current working directory.
    """

    def validate_app_config(workspace: str) -> bool:
        config_path = path.join(workspace, "taskweaver_config.json")
        if not path.exists(config_path):
            return False
        # TODO: read, parse and validate config
        return True

    def is_dir_valid(dir: str) -> bool:
        return path.exists(dir) and path.isdir(dir) and validate_app_config(dir)

    def is_empty(dir: str) -> bool:
        return not path.exists(dir) or (path.isdir(dir) and len(listdir(dir)) == 0)

    if app_dir is not None:
        app_dir = path.abspath(app_dir)
        return app_dir, is_dir_valid(app_dir), is_empty(app_dir)
    else:
        cwd = path.abspath(".")
        cur_dir = cwd
        while True:
            if is_dir_valid(cur_dir):
                return cur_dir, True, False

            next_path = path.abspath(path.join(cur_dir, ".."))
            if next_path == cur_dir:
                return cwd, False, is_empty(cwd)
            cur_dir = next_path
