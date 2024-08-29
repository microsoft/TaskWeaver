import os
from pathlib import Path
from typing import List, Literal, Optional

from injector import inject

from taskweaver.ces.common import ExecutionResult, Manager
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.memory.plugin import PluginRegistry
from taskweaver.module.tracing import Tracing, get_tracer, tracing_decorator
from taskweaver.plugin.context import ArtifactType
from taskweaver.session import SessionMetadata

TRUNCATE_CHAR_LENGTH = 1500


def get_artifact_uri(execution_id: str, file: str, use_local_uri: bool) -> str:
    return (
        Path(os.path.join("workspace", execution_id, file)).as_uri() if use_local_uri else f"http://artifact-ref/{file}"
    )


def get_default_artifact_name(artifact_type: ArtifactType, mine_type: str) -> str:
    if artifact_type == "file":
        return "artifact"
    if artifact_type == "image":
        if mine_type == "image/png":
            return "image.png"
        if mine_type == "image/jpeg":
            return "image.jpg"
        if mine_type == "image/gif":
            return "image.gif"
        if mine_type == "image/svg+xml":
            return "image.svg"
    if artifact_type == "chart":
        return "chart.json"
    if artifact_type == "svg":
        return "svg.svg"
    return "file"


class CodeExecutor:
    @inject
    def __init__(
        self,
        session_metadata: SessionMetadata,
        config: AppConfigSource,
        exec_mgr: Manager,
        plugin_registry: PluginRegistry,
        tracing: Tracing,
    ) -> None:
        self.session_id = session_metadata.session_id
        self.workspace = session_metadata.workspace
        self.execution_cwd = session_metadata.execution_cwd
        self.exec_mgr = exec_mgr
        self.exec_client = self.exec_mgr.get_session_client(
            self.session_id,
            session_dir=self.workspace,
            cwd=self.execution_cwd,
        )
        self.client_started: bool = False
        self.plugin_registry = plugin_registry
        self.plugin_loaded: bool = False
        self.config = config
        self.tracing = tracing
        self.session_variables = {}

    @tracing_decorator
    def execute_code(self, exec_id: str, code: str) -> ExecutionResult:
        with get_tracer().start_as_current_span("start"):
            self.start()

        if not self.plugin_loaded:
            with get_tracer().start_as_current_span("load_plugin"):
                self.load_plugin()
                self.plugin_loaded = True

        # update session variables
        self.exec_client.update_session_var(self.session_variables)

        with get_tracer().start_as_current_span("run_code"):
            self.tracing.set_span_attribute("code", code)
            result = self.exec_client.execute_code(exec_id, code)

        if result.is_success:
            for artifact in result.artifact:
                if artifact.file_name == "":
                    original_name = (
                        artifact.original_name
                        if artifact.original_name != ""
                        else get_default_artifact_name(
                            artifact.type,
                            artifact.mime_type,
                        )
                    )
                    file_name = f"{artifact.name}_{original_name}"
                    self._save_file(
                        file_name,
                        artifact.file_content,
                        artifact.file_content_encoding,
                    )
                    artifact.file_name = file_name

        if not result.is_success:
            self.tracing.set_span_status("ERROR", "Code execution failed.")
        self.tracing.set_span_attribute(
            "result",
            self.format_code_output(result, with_code=False, code_mask=None),
        )

        return result

    def update_session_var(self, session_var_dict: dict) -> None:
        self.session_variables.update(session_var_dict)

    def _save_file(
        self,
        file_name: str,
        content: str,
        content_encoding: Literal["base64", "str"] = "str",
    ) -> None:
        file_path = os.path.join(self.execution_cwd, file_name)
        if content_encoding == "base64":
            with open(file_path, "wb") as f:
                import base64

                f.write(base64.b64decode(content))
        else:
            with open(file_path, "w") as f:
                f.write(content)

    def load_plugin(self):
        for p in self.plugin_registry.get_list():
            try:
                src_file = f"{self.config.app_base_path}/plugins/{p.impl}.py"
                with open(src_file, "r") as f:
                    plugin_code = f.read()
                self.exec_client.load_plugin(
                    p.name,
                    plugin_code,
                    p.config,
                )
            except Exception as e:
                print(f"Plugin {p.name} failed to load: {str(e)}")

    def start(self):
        if not self.client_started:
            self.exec_client.start()
            self.client_started = True

    def stop(self):
        self.exec_client.stop()

    def format_code_output(
        self,
        result: ExecutionResult,
        indent: int = 0,
        with_code: bool = True,
        code_mask: Optional[str] = None,
        use_local_uri: bool = False,
    ) -> str:
        lines: List[str] = []

        # code execution result
        if with_code:
            if code_mask is not None and len(code_mask) > 0:
                display_code = result.code.replace(code_mask, "")
            else:
                display_code = result.code
            lines.append(
                f"The following python code has been executed:\n" "```python\n" f"{display_code}\n" "```\n\n",
            )

        lines.append(
            f"The execution of the generated python code above has"
            f" {'succeeded' if result.is_success else 'failed'}\n",
        )

        # code output
        if result.output != "":
            output = result.output
            if isinstance(output, list) and len(output) > 0:
                lines.append(
                    "The values of variables of the above Python code after execution are:\n",
                )
                for o in output:
                    lines.append(f"{str(o)}")
                lines.append("")
            else:
                lines.append(
                    "The result of above Python code after execution is:\n" + str(output),
                )
        elif result.is_success:
            if len(result.stdout) > 0:
                lines.append(
                    "The stdout is:",
                )
                lines.append("\n".join(result.stdout)[:TRUNCATE_CHAR_LENGTH])
            else:
                lines.append(
                    "The execution is successful but no output is generated.",
                )

        # console output when execution failed
        if not result.is_success:
            lines.append(
                "During execution, the following messages were logged:",
            )
            if len(result.log) > 0:
                lines.extend([f"- [(l{1})]{ln[0]}: {ln[2]}" for ln in result.log])
            if result.error is not None:
                lines.append(result.error[:TRUNCATE_CHAR_LENGTH])
            if len(result.stdout) > 0:
                lines.append("\n".join(result.stdout)[:TRUNCATE_CHAR_LENGTH])
            if len(result.stderr) > 0:
                lines.append("\n".join(result.stderr)[:TRUNCATE_CHAR_LENGTH])
            lines.append("")

        # artifacts
        if len(result.artifact) > 0:
            lines.append("The following artifacts were generated:")
            lines.extend(
                [
                    f"- type: {a.type} ; uri: "
                    + (
                        get_artifact_uri(
                            execution_id=result.execution_id,
                            file=(
                                a.file_name
                                if os.path.isabs(a.file_name) or not use_local_uri
                                else os.path.join(self.execution_cwd, a.file_name)
                            ),
                            use_local_uri=use_local_uri,
                        )
                    )
                    + f" ; description: {a.preview}"
                    for a in result.artifact
                ],
            )
            lines.append("")

        return "\n".join([" " * indent + ln for ln in lines])
