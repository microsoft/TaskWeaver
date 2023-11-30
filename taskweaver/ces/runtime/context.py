import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from taskweaver.plugin.context import ArtifactType, LogErrorLevel, PluginContext

if TYPE_CHECKING:
    from taskweaver.ces.runtime.executor import Executor


class ExecutorPluginContext(PluginContext):
    def __init__(self, executor: Any) -> None:
        self.executor: Executor = executor

        self.artifact_list: List[Dict[str, str]] = []
        self.log_messages: List[Tuple[LogErrorLevel, str, str]] = []
        self.output: List[Tuple[str, str]] = []

    @property
    def execution_id(self) -> str:
        return self.executor.cur_execution_id

    @property
    def session_id(self) -> str:
        return self.executor.session_id

    @property
    def env_id(self) -> str:
        return self.executor.env_id

    @property
    def execution_idx(self) -> int:
        return self.executor.cur_execution_count

    def add_artifact(
        self,
        name: str,
        file_name: str,
        type: ArtifactType,
        val: Any,
        desc: Optional[str] = None,
    ) -> str:
        desc_preview = desc if desc is not None else self._get_preview_by_type(type, val)

        id, path = self.create_artifact_path(name, file_name, type, desc=desc_preview)
        if type == "chart":
            with open(path, "w") as f:
                f.write(val)
        elif type == "df":
            val.to_csv(path, index=False)
        elif type == "file" or type == "txt" or type == "svg" or type == "html":
            with open(path, "w") as f:
                f.write(val)
        else:
            raise Exception("unsupported data type")

        return id

    def _get_preview_by_type(self, type: str, val: Any) -> str:
        if type == "chart":
            preview = "chart"
        elif type == "df":
            preview = f"DataFrame in shape {val.shape} with columns {list(val.columns)}"
        elif type == "file" or type == "txt":
            preview = str(val)[:100]
        elif type == "html":
            preview = "Web Page"
        else:
            preview = str(val)
        return preview

    def create_artifact_path(
        self,
        name: str,
        file_name: str,
        type: ArtifactType,
        desc: str,
    ) -> Tuple[str, str]:
        id = f"obj_{self.execution_idx}_{type}_{len(self.artifact_list):04x}"

        file_path = f"{id}_{file_name}"
        full_file_path = self._get_obj_path(file_path)

        self.artifact_list.append(
            {
                "name": name,
                "type": type,
                "original_name": file_name,
                "file": file_path,
                "preview": desc,
            },
        )
        return id, full_file_path

    def set_output(self, output: List[Tuple[str, str]]):
        if isinstance(output, list):
            self.output.extend(output)
        else:
            self.output.append((str(output), ""))

    def get_normalized_output(self):
        def to_str(v: Any) -> str:
            # TODO: configure/tune value length limit
            # TODO: handle known/common data types explicitly
            return str(v)[:5000]

        def normalize_tuple(i: int, v: Any) -> Tuple[str, str]:
            default_name = f"execution_result_{i + 1}"
            if isinstance(v, tuple) or isinstance(v, list):
                list_value: Any = v
                name = to_str(list_value[0]) if len(list_value) > 0 else default_name
                if len(list_value) <= 2:
                    val = to_str(list_value[1]) if len(list_value) > 1 else to_str(None)
                else:
                    val = to_str(list_value[1:])
                return (name, val)

            return (default_name, to_str(v))

        return [normalize_tuple(i, o) for i, o in enumerate(self.output)]

    def log(self, level: LogErrorLevel, tag: str, message: str):
        self.log_messages.append((level, tag, message))

    def _get_obj_path(self, name: str) -> str:
        return os.path.join(self.executor.session_dir, "cwd", name)

    def call_llm_api(self, messages: List[Dict[str, str]], **args: Any) -> Any:
        # TODO: use llm_api from handle side
        return None

    def get_env(self, plugin_name: str, variable_name: str):
        # To avoid duplicate env variable, use plugin_name and vari_name to compose the final environment variable
        name = f"PLUGIN_{plugin_name}_{variable_name}"
        if name in os.environ:
            return os.environ[name]
        raise Exception(
            "Environment variable " + name + " is required to be specified in environment",
        )

    def get_session_var(
        self,
        variable_name: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        if variable_name in self.executor.session_var:
            return self.executor.session_var[variable_name]
        return default
