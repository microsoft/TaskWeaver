from __future__ import annotations

import json
from typing import Any, Dict, List, Union


def create_id(length: int = 4) -> str:
    import secrets
    from datetime import datetime

    date_str = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    ran_str = secrets.token_hex(length)
    return f"{date_str}-{ran_str}"


def read_yaml(path: str) -> Dict[str, Any]:
    import yaml

    try:
        with open(path, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise ValueError(f"Yaml loading failed due to: {e}")


def write_yaml(path: str, content: Dict[str, Any]):
    import yaml

    try:
        with open(path, "w") as file:
            yaml.safe_dump(content, file, sort_keys=False)
    except Exception as e:
        raise ValueError(f"Yaml writing failed due to: {e}")


def validate_yaml(content: Any, schema: str) -> bool:
    import json
    import os

    import jsonschema

    # plugin_dir = PLUGIN.BASE_PATH
    # plugin_schema_path = os.path.join(plugin_dir, plugin_name + ".yaml")
    # content = read_yaml(plugin_schema_path)
    assert schema in ["example_schema", "plugin_schema"]
    if schema == "example_schema":
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "../plugin/taskweaver.conversation-v1.schema.json",
        )
    else:
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "../plugin/taskweaver.plugin-v1.schema.json",
        )

    with open(schema_path) as file:
        schema_object: Any = json.load(file)
    try:
        jsonschema.validate(content, schema=schema_object)
        return True
    except jsonschema.ValidationError as e:
        raise ValueError(f"Yaml validation failed due to: {e}")


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o: Any):
        import dataclasses

        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, cls=EnhancedJSONEncoder)


def json_dump(obj: Any, fp: Any):
    json.dump(obj, fp, cls=EnhancedJSONEncoder)


def generate_md5_hash(content: str) -> str:
    from hashlib import md5

    return md5(content.encode()).hexdigest()


def glob_files(path: Union[str, List[str]]) -> list[str]:
    import glob

    if isinstance(path, str):
        return glob.glob(path)
    else:
        return [item for sublist in [glob.glob(p) for p in path] for item in sublist]


def import_module(module_name: str):
    import importlib

    return importlib.import_module(module_name)
