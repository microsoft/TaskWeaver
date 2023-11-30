import os


def get_package_version():
    import datetime
    import json

    version_file = os.path.join(os.path.dirname(__file__), "..", "version.json")
    with open(version_file, "r") as f:
        version_spec = json.load(f)
    base_version = version_spec["prod"]
    main_suffix = version_spec["main"]
    dev_suffix = version_spec["dev"]

    version = base_version
    branch_name = os.environ.get("BUILD_SOURCEBRANCHNAME", None)
    build_number = os.environ.get("BUILD_BUILDNUMBER", None)

    if branch_name == "production":
        return version

    version += main_suffix if main_suffix is not None else ""
    if branch_name == "main":
        return version

    version += dev_suffix if dev_suffix is not None else ""
    if build_number is not None:
        version += f"+{build_number}"
    else:
        version += f"+local.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    return version


if __name__ == "__main__":
    print(get_package_version())
