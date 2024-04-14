import glob
import os
import re
import sys

import yaml
from packaging import version

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def load_task_case(eval_case_dir: str):
    assert os.path.isdir(eval_case_dir), f"Invalid eval case dir: {eval_case_dir}"
    eval_case_file = glob.glob(os.path.join(eval_case_dir, "*.yaml"))
    if len(eval_case_file) != 1:
        raise ValueError(
            f"Invalid eval case dir: {eval_case_dir} because only one eval case YAML file is expected.",
        )
    eval_case_file = eval_case_file[0]
    with open(eval_case_file, "r") as f:
        eval_meta_data = yaml.safe_load(f)

    return eval_meta_data


def check_package_version(package_specification):
    match = re.match(r"([a-zA-Z0-9-_]+)(?:(>=|>)([\d.]+))?", package_specification)
    if not match:
        raise ValueError(f"Invalid package specification: {package_specification}")

    package_name, operator, required_version = match.groups()

    try:
        installed_version = importlib_metadata.version(package_name)
        if not operator:
            print(f"{package_name} version {installed_version} is installed.")
        elif operator == ">=" and version.parse(installed_version) >= version.parse(required_version):
            print(
                f"{package_name} version {installed_version} is installed, "
                f"satisfying the minimum required version {required_version}.",
            )
        elif operator == ">" and version.parse(installed_version) > version.parse(required_version):
            print(
                f"{package_name} version {installed_version} is installed, "
                f"greater than the required version {required_version}.",
            )
        else:
            raise Exception(
                f"Error: {package_name} installed version {installed_version} "
                f"does not satisfy the condition {operator} {required_version}.",
            )
    except importlib_metadata.PackageNotFoundError:
        raise Exception(f"Error: {package_name} is not installed.") from None


if __name__ == "__main__":
    package_specification = "numpy=1.24.3"
    try:
        check_package_version(package_specification)
    except Exception as e:
        print(e)
