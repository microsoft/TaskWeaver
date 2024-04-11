import enum
import json
import logging
import os
import platform
import sys
import time
from ast import literal_eval
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

from jupyter_client import BlockingKernelClient
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
from jupyter_client.manager import KernelManager
from jupyter_client.multikernelmanager import MultiKernelManager

from taskweaver.ces.common import EnvPlugin, ExecutionArtifact, ExecutionResult, get_id

logger = logging.getLogger(__name__)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.WARNING)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

ExecType = Literal["user", "control"]
ResultMimeType = Union[
    Literal["text/plain", "text/html", "text/markdown", "text/latex"],
    str,
]


@dataclass
class DisplayData:
    data: Dict[ResultMimeType, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    transient: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvExecution:
    exec_id: str
    code: str
    exec_type: ExecType = "user"

    # streaming output
    stdout: List[str] = field(default_factory=list)
    stderr: List[str] = field(default_factory=list)
    displays: List[DisplayData] = field(default_factory=list)

    # final output
    result: Dict[ResultMimeType, str] = field(default_factory=dict)
    error: str = ""


@dataclass
class EnvSession:
    session_id: str
    kernel_status: Literal[
        "pending",
        "ready",
        "running",
        "stopped",
        "error",
    ] = "pending"
    kernel_id: str = ""
    execution_count: int = 0
    execution_dict: Dict[str, EnvExecution] = field(default_factory=dict)
    session_dir: str = ""
    session_var: Dict[str, str] = field(default_factory=dict)
    plugins: Dict[str, EnvPlugin] = field(default_factory=dict)


class KernelSpecProvider(KernelSpecManager):
    def get_kernel_spec(self, kernel_name: str) -> KernelSpec:
        if kernel_name == "taskweaver":
            return KernelSpec(
                argv=[
                    "python",
                    "-m",
                    "taskweaver.ces.kernel.launcher",
                    "-f",
                    "{connection_file}",
                ],
                display_name="TaskWeaver",
                language="python",
                metadata={"debugger": True},
            )
        return super().get_kernel_spec(kernel_name)


class TaskWeaverMultiKernelManager(MultiKernelManager):
    def pre_start_kernel(
        self,
        kernel_name: str | None,
        kwargs: Any,
    ) -> tuple[KernelManager, str, str]:
        env: Optional[Dict[str, str]] = kwargs.get("env")

        km, kernel_name, kernel_id = super().pre_start_kernel(kernel_name, kwargs)
        if env is not None:
            if "CONNECTION_FILE" in env:
                km.connection_file = env["CONNECTION_FILE"]
        return km, kernel_name, kernel_id


class EnvMode(enum.Enum):
    Local = "local"
    Container = "container"


class Environment:
    def __init__(
        self,
        env_id: Optional[str] = None,
        env_dir: Optional[str] = None,
        env_mode: Optional[EnvMode] = EnvMode.Local,
        port_start_inside_container: Optional[int] = 12345,
    ) -> None:
        self.session_dict: Dict[str, EnvSession] = {}
        self.id = get_id(prefix="env") if env_id is None else env_id
        self.env_dir = env_dir if env_dir is not None else os.getcwd()
        self.mode = env_mode

        if self.mode == EnvMode.Local:
            self.multi_kernel_manager = TaskWeaverMultiKernelManager(
                default_kernel_name="taskweaver",
                kernel_spec_manager=KernelSpecProvider(),
            )

        elif self.mode == EnvMode.Container:
            try:
                import docker
                import docker.errors
            except ImportError:
                raise ImportError(
                    "docker package is required for container-based kernel. "
                    "Please install it by running `pip install docker`.",
                )

            try:
                self.docker_client = docker.from_env()
            except docker.errors.DockerException as e:
                raise docker.errors.DockerException(f"Failed to connect to Docker daemon: {e}. ")

            self.image_name = "taskweavercontainers/taskweaver-executor:test"
            try:
                local_image = self.docker_client.images.get(self.image_name)
                registry_image = self.docker_client.images.get_registry_data(self.image_name)
                if local_image.id != registry_image.id:
                    logger.info(f"Local image {local_image.id} does not match registry image {registry_image.id}.")
                    raise docker.errors.ImageNotFound("Local image is outdated.")
            except docker.errors.ImageNotFound:
                logger.info("Pulling image from docker.io.")
                try:
                    self.docker_client.images.pull(self.image_name)
                except docker.errors.DockerException as e:
                    raise docker.errors.DockerException(f"Failed to pull image: {e}. ")

            self.session_container_dict: Dict[str, str] = {}
            self.port_start_inside_container = port_start_inside_container
        else:
            raise ValueError(f"Unsupported environment mode {env_mode}")

        logger.info(f"Environment {self.id} is created.")

    def _get_connection_file(self, session_id: str, kernel_id: str) -> str:
        return os.path.join(
            self._get_session(session_id).session_dir,
            "ces",
            f"conn-{session_id}-{kernel_id}.json",
        )

    def start_session(
        self,
        session_id: str,
        session_dir: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> None:
        session = self._get_session(session_id, session_dir=session_dir)
        ces_session_dir = os.path.join(session.session_dir, "ces")
        new_kernel_id = get_id(prefix="knl")
        os.makedirs(ces_session_dir, exist_ok=True)
        cwd = cwd if cwd is not None else os.path.join(session.session_dir, "cwd")
        os.makedirs(cwd, exist_ok=True)

        if self.mode == EnvMode.Local:
            # set python home from current python environment
            python_home = os.path.sep.join(sys.executable.split(os.path.sep)[:-2])
            python_path = os.pathsep.join(
                [
                    os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..")),
                    os.path.join(python_home, "Lib", "site-packages"),
                ]
                + sys.path,
            )

            # inherit current environment variables
            # TODO: filter out sensitive environment information
            kernel_env = os.environ.copy()
            kernel_env.update(
                {
                    "TASKWEAVER_ENV_ID": self.id,
                    "TASKWEAVER_SESSION_ID": session.session_id,
                    "TASKWEAVER_SESSION_DIR": session.session_dir,
                    "TASKWEAVER_LOGGING_FILE_PATH": os.path.join(
                        ces_session_dir,
                        "kernel_logging.log",
                    ),
                    "CONNECTION_FILE": self._get_connection_file(session_id, new_kernel_id),
                    "PATH": os.environ["PATH"],
                    "PYTHONPATH": python_path,
                    "PYTHONHOME": python_home,
                },
            )
            session.kernel_id = self.multi_kernel_manager.start_kernel(
                kernel_id=new_kernel_id,
                cwd=cwd,
                env=kernel_env,
            )

            self._cmd_session_init(session)
            session.kernel_status = "ready"
        elif self.mode == EnvMode.Container:
            connection_file = self._get_connection_file(session_id, new_kernel_id)
            new_port_start = self.port_start_inside_container
            kernel_env = {
                "TASKWEAVER_KERNEL_MODE": "container",
                "TASKWEAVER_SESSION_ID": session_id,
                "TASKWEAVER_KERNEL_ID": new_kernel_id,
                "TASKWEAVER_CES_DIR": "/app/ces/",
                "TASKWEAVER_CWD": "/app/cwd/",
                "TASKWEAVER_PORT_START": str(new_port_start),
                "TASKWEAVER_LOGGING_FILE_PATH": "/app/ces/kernel_logging.log",
            }

            if platform.system() != "Windows":
                # change the permission of the ces and cwd directories
                kernel_env["TASKWEAVER_UID"] = str(os.getuid())
                kernel_env["TASKWEAVER_GID"] = str(os.getgid())

            # ports will be assigned automatically at the host
            container = self.docker_client.containers.run(
                image=self.image_name,
                detach=True,
                environment=kernel_env,
                volumes={
                    os.path.abspath(ces_session_dir): {"bind": "/app/ces/", "mode": "rw"},
                    os.path.abspath(cwd): {"bind": "/app/cwd", "mode": "rw"},
                },
                ports={
                    f"{new_port_start}/tcp": None,
                    f"{new_port_start + 1}/tcp": None,
                    f"{new_port_start + 2}/tcp": None,
                    f"{new_port_start + 3}/tcp": None,
                    f"{new_port_start + 4}/tcp": None,
                },
            )

            tick = 0
            while tick < 10:
                container.reload()
                if container.status == "running" and os.path.isfile(connection_file):
                    logger.info("Container is running and connection file is ready.")
                    break
                time.sleep(1)  # wait for 1 second before checking again
                tick += 1
            if tick == 10:
                raise Exception("Container is not ready after 10 seconds")

            # save the ports to ces session dir
            port_bindings = container.attrs["NetworkSettings"]["Ports"]
            shell_port = int(port_bindings[f"{new_port_start}/tcp"][0]["HostPort"])
            iopub_port = int(port_bindings[f"{new_port_start + 1}/tcp"][0]["HostPort"])
            stdin_port = int(port_bindings[f"{new_port_start + 2}/tcp"][0]["HostPort"])
            hb_port = int(port_bindings[f"{new_port_start + 3}/tcp"][0]["HostPort"])
            control_port = int(port_bindings[f"{new_port_start + 4}/tcp"][0]["HostPort"])
            with open(os.path.join(ces_session_dir, "ports.json"), "w") as f:
                f.write(
                    json.dumps(
                        {
                            "shell_port": shell_port,
                            "iopub_port": iopub_port,
                            "stdin_port": stdin_port,
                            "hb_port": hb_port,
                            "control_port": control_port,
                        },
                    ),
                )

            self.session_container_dict[session_id] = container.id
            session.kernel_id = new_kernel_id
            self._cmd_session_init(session)
            session.kernel_status = "ready"
        else:
            raise ValueError(f"Unsupported environment mode {self.mode}")

    def execute_code(
        self,
        session_id: str,
        code: str,
        exec_id: Optional[str] = None,
    ) -> ExecutionResult:
        exec_id = get_id(prefix="exec") if exec_id is None else exec_id
        session = self._get_session(session_id)
        if session.kernel_status == "pending":
            self.start_session(session_id)

        session.execution_count += 1
        execution_index = session.execution_count
        self._execute_control_code_on_kernel(
            session.session_id,
            f"%_taskweaver_exec_pre_check {execution_index} {exec_id}",
        )
        exec_result = self._execute_code_on_kernel(
            session.session_id,
            exec_id=exec_id,
            code=code,
        )
        exec_extra_result = self._execute_control_code_on_kernel(
            session.session_id,
            f"%_taskweaver_exec_post_check {execution_index} {exec_id}",
        )
        session.execution_dict[exec_id] = exec_result

        # TODO: handle session id, round id, post id, etc.
        return self._parse_exec_result(exec_result, exec_extra_result["data"])

    def load_plugin(
        self,
        session_id: str,
        plugin_name: str,
        plugin_impl: str,
        plugin_config: Optional[Dict[str, str]] = None,
    ) -> None:
        session = self._get_session(session_id)
        if plugin_name in session.plugins.keys():
            prev_plugin = session.plugins[plugin_name]
            if prev_plugin.loaded:
                self._cmd_plugin_unload(session, prev_plugin)
            del session.plugins[plugin_name]

        plugin = EnvPlugin(
            name=plugin_name,
            impl=plugin_impl,
            config=plugin_config,
            loaded=False,
        )
        self._cmd_plugin_load(session, plugin)
        plugin.loaded = True
        session.plugins[plugin_name] = plugin

    def test_plugin(
        self,
        session_id: str,
        plugin_name: str,
    ) -> None:
        session = self._get_session(session_id)
        plugin = session.plugins[plugin_name]
        self._cmd_plugin_test(session, plugin)

    def unload_plugin(
        self,
        session_id: str,
        plugin_name: str,
    ) -> None:
        session = self._get_session(session_id)
        if plugin_name in session.plugins.keys():
            plugin = session.plugins[plugin_name]
            if plugin.loaded:
                self._cmd_plugin_unload(session, plugin)
            del session.plugins[plugin_name]

    def update_session_var(
        self,
        session_id: str,
        session_var: Dict[str, str],
    ) -> None:
        session = self._get_session(session_id)
        session.session_var.update(session_var)
        self._update_session_var(session)

    def stop_session(self, session_id: str) -> None:
        session = self._get_session(session_id)
        if session is None:
            # session not exist
            return
        if session.kernel_status == "stopped":
            return
        if session.kernel_status == "pending":
            session.kernel_status = "stopped"
            return
        try:
            if session.kernel_id != "":
                if self.mode == EnvMode.Local:
                    kernel = self.multi_kernel_manager.get_kernel(session.kernel_id)
                    is_alive = kernel.is_alive()
                    if is_alive:
                        kernel.shutdown_kernel(now=True)
                    kernel.cleanup_resources()
                elif self.mode == EnvMode.Container:
                    container_id = self.session_container_dict[session_id]
                    logger.info(f"Stopping container {container_id} for session {session_id}")
                    container = self.docker_client.containers.get(container_id)
                    container.stop()
                    container.remove()
                    del self.session_container_dict[session_id]
                else:
                    raise ValueError(f"Unsupported environment mode {self.mode}")

        except Exception as e:
            logger.error(e)
        session.kernel_status = "stopped"

    def download_file(self, session_id: str, file_path: str) -> str:
        session = self._get_session(session_id)
        full_path = self._execute_code_on_kernel(
            session.session_id,
            get_id(prefix="exec"),
            f"%%_taskweaver_convert_path\n{file_path}",
            silent=True,
        )
        return full_path.result["text/plain"]

    def _get_session(
        self,
        session_id: str,
        session_dir: Optional[str] = None,
    ) -> EnvSession:
        if session_id not in self.session_dict and session_dir is not None:
            new_session = EnvSession(session_id)
            new_session.session_dir = (
                session_dir if session_dir is not None else self._get_default_session_dir(session_id)
            )
            os.makedirs(new_session.session_dir, exist_ok=True)
            self.session_dict[session_id] = new_session

        return self.session_dict.get(session_id, None)

    def _get_default_session_dir(self, session_id: str) -> str:
        os.makedirs(os.path.join(self.env_dir, "sessions"), exist_ok=True)
        return os.path.join(self.env_dir, "sessions", session_id)

    def _execute_control_code_on_kernel(
        self,
        session_id: str,
        code: str,
        silent: bool = False,
        store_history: bool = False,
    ) -> Dict[Literal["is_success", "message", "data"], Union[bool, str, Any]]:
        exec_result = self._execute_code_on_kernel(
            session_id,
            get_id(prefix="exec"),
            code=code,
            silent=silent,
            store_history=store_history,
            exec_type="control",
        )
        if exec_result.error != "":
            raise Exception(exec_result.error)
        if "text/plain" not in exec_result.result:
            raise Exception("No text returned.")
        result = literal_eval(exec_result.result["text/plain"])
        if not result["is_success"]:
            raise Exception(result["message"])
        return result

    def _get_session_ports(self, session_id: str) -> Dict[str, int]:
        session = self._get_session(session_id)
        with open(os.path.join(session.session_dir, "ces", "ports.json"), "r") as f:
            return json.load(f)

    def _get_client(
        self,
        session_id: str,
    ) -> BlockingKernelClient:
        session = self._get_session(session_id)
        connection_file = self._get_connection_file(session_id, session.kernel_id)
        client = BlockingKernelClient(connection_file=connection_file)
        client.load_connection_file()
        # overwrite the ip and ports if outside container
        if self.mode == EnvMode.Container:
            client.ip = "127.0.0.1"  # TODO: get the host ip
            ports = self._get_session_ports(session_id)
            client.shell_port = ports["shell_port"]
            client.stdin_port = ports["stdin_port"]
            client.hb_port = ports["hb_port"]
            client.control_port = ports["control_port"]
            client.iopub_port = ports["iopub_port"]
        return client

    def _execute_code_on_kernel(
        self,
        session_id: str,
        exec_id: str,
        code: str,
        silent: bool = False,
        store_history: bool = True,
        exec_type: ExecType = "user",
    ) -> EnvExecution:
        exec_result = EnvExecution(exec_id=exec_id, code=code, exec_type=exec_type)
        kc = self._get_client(session_id)
        kc.wait_for_ready(timeout=30)
        kc.start_channels()
        result_msg_id = kc.execute(
            code=code,
            silent=silent,
            store_history=store_history,
            allow_stdin=False,
            stop_on_error=True,
        )
        try:
            # TODO: interrupt kernel if it takes too long
            while True:
                message = kc.get_iopub_msg(timeout=180)

                logger.debug(json.dumps(message, indent=2, default=str))

                assert message["parent_header"]["msg_id"] == result_msg_id
                msg_type = message["msg_type"]
                if msg_type == "status":
                    if message["content"]["execution_state"] == "idle":
                        break
                elif msg_type == "stream":
                    stream_name = message["content"]["name"]
                    stream_text = message["content"]["text"]

                    if stream_name == "stdout":
                        exec_result.stdout.append(stream_text)
                    elif stream_name == "stderr":
                        exec_result.stderr.append(stream_text)
                    else:
                        assert False, f"Unsupported stream name: {stream_name}"

                elif msg_type == "execute_result":
                    execute_result = message["content"]["data"]
                    exec_result.result = execute_result
                elif msg_type == "error":
                    error_name = message["content"]["ename"]
                    error_value = message["content"]["evalue"]
                    error_traceback_lines = message["content"]["traceback"]
                    if error_traceback_lines is None:
                        error_traceback_lines = [f"{error_name}: {error_value}"]
                    error_traceback = "\n".join(error_traceback_lines)
                    exec_result.error = error_traceback
                elif msg_type == "execute_input":
                    pass
                elif msg_type == "display_data":
                    data: Dict[ResultMimeType, Any] = message["content"]["data"]
                    metadata: Dict[str, Any] = message["content"]["metadata"]
                    transient: Dict[str, Any] = message["content"]["transient"]
                    exec_result.displays.append(
                        DisplayData(data=data, metadata=metadata, transient=transient),
                    )
                elif msg_type == "update_display_data":
                    data: Dict[ResultMimeType, Any] = message["content"]["data"]
                    metadata: Dict[str, Any] = message["content"]["metadata"]
                    transient: Dict[str, Any] = message["content"]["transient"]
                    exec_result.displays.append(
                        DisplayData(data=data, metadata=metadata, transient=transient),
                    )
                else:
                    pass
        finally:
            kc.stop_channels()
        return exec_result

    def _update_session_var(self, session: EnvSession) -> None:
        self._execute_control_code_on_kernel(
            session.session_id,
            f"%%_taskweaver_update_session_var\n{json.dumps(session.session_var)}",
        )

    def _cmd_session_init(self, session: EnvSession) -> None:
        self._execute_control_code_on_kernel(
            session.session_id,
            f"%_taskweaver_session_init {session.session_id}",
        )

    def _cmd_plugin_load(self, session: EnvSession, plugin: EnvPlugin) -> None:
        self._execute_control_code_on_kernel(
            session.session_id,
            f"%%_taskweaver_plugin_register {plugin.name}\n{plugin.impl}",
        )
        self._execute_control_code_on_kernel(
            session.session_id,
            f"%%_taskweaver_plugin_load {plugin.name}\n{json.dumps(plugin.config or {})}",
        )

    def _cmd_plugin_test(self, session: EnvSession, plugin: EnvPlugin) -> None:
        self._execute_control_code_on_kernel(
            session.session_id,
            f"%_taskweaver_plugin_test {plugin.name}",
        )

    def _cmd_plugin_unload(self, session: EnvSession, plugin: EnvPlugin) -> None:
        self._execute_control_code_on_kernel(
            session.session_id,
            f"%_taskweaver_plugin_unload {plugin.name}",
        )

    def _parse_exec_result(
        self,
        exec_result: EnvExecution,
        extra_result: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        result = ExecutionResult(
            execution_id=exec_result.exec_id,
            code=exec_result.code,
            is_success=exec_result.error == "",
            error=exec_result.error,
            output="",
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
            log=[],
            artifact=[],
        )

        for mime_type in exec_result.result.keys():
            if mime_type.startswith("text/"):
                text_result = exec_result.result[mime_type]
                try:
                    parsed_result = literal_eval(text_result)
                    result.output = parsed_result
                except Exception:
                    result.output = text_result
        display_artifact_count = 0
        for display in exec_result.displays:
            display_artifact_count += 1
            artifact = ExecutionArtifact()
            artifact.name = f"{exec_result.exec_id}-display-{display_artifact_count}"
            has_svg = False
            has_pic = False
            for mime_type in display.data.keys():
                if mime_type.startswith("image/"):
                    if mime_type == "image/svg+xml":
                        if has_pic and has_svg:
                            continue
                        has_svg = True
                        has_pic = True
                        artifact.type = "svg"
                        artifact.file_content_encoding = "str"
                    else:
                        if has_pic:
                            continue
                        has_pic = True
                        artifact.type = "image"
                        artifact.file_content_encoding = "base64"
                    artifact.mime_type = mime_type
                    artifact.file_content = display.data[mime_type]
                if mime_type.startswith("text/"):
                    artifact.preview = display.data[mime_type]

            if has_pic:
                result.artifact.append(artifact)

        if isinstance(extra_result, dict):
            for key, value in extra_result.items():
                if key == "log":
                    result.log = value
                elif key == "artifact":
                    for artifact_dict in value:
                        artifact_item = ExecutionArtifact(
                            name=artifact_dict["name"],
                            type=artifact_dict["type"],
                            original_name=artifact_dict["original_name"],
                            file_name=artifact_dict["file"],
                            preview=artifact_dict["preview"],
                        )
                        result.artifact.append(artifact_item)
                else:
                    pass

        return result
