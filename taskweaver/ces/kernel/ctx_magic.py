import json
import os
from typing import Any, Dict

from IPython.core.interactiveshell import InteractiveShell
from IPython.core.magic import Magics, cell_magic, line_cell_magic, line_magic, magics_class, needs_local_scope

from taskweaver.ces.runtime.executor import Executor


def fmt_response(is_success: bool, message: str, data: Any = None):
    return {
        "is_success": is_success,
        "message": message,
        "data": data,
    }


@magics_class
class TaskWeaverContextMagic(Magics):
    def __init__(self, shell: InteractiveShell, executor: Executor, **kwargs: Any):
        super(TaskWeaverContextMagic, self).__init__(shell, **kwargs)
        self.executor = executor

    @needs_local_scope
    @line_magic
    def _taskweaver_session_init(self, line: str, local_ns: Dict[str, Any]):
        self.executor.load_lib(local_ns)
        return fmt_response(True, "TaskWeaver context initialized.")

    @cell_magic
    def _taskweaver_update_session_var(self, line: str, cell: str):
        json_dict_str = cell
        session_var_dict = json.loads(json_dict_str)
        self.executor.update_session_var(session_var_dict)
        return fmt_response(True, "Session var updated.", self.executor.session_var)

    @line_magic
    def _taskweaver_check_session_var(self, line: str, cell: str):
        return fmt_response(True, "Session var checked.", self.executor.session_var)

    @cell_magic
    def _taskweaver_convert_path(self, line: str, cell: str):
        raw_path_str = cell
        import os

        full_path = os.path.abspath(raw_path_str)
        return fmt_response(True, "Path converted.", full_path)

    @line_magic
    def _taskweaver_exec_pre_check(self, line: str):
        exec_idx, exec_id = line.split(" ")
        exec_idx = int(exec_idx)
        return fmt_response(True, "", self.executor.pre_execution(exec_idx, exec_id))

    @needs_local_scope
    @line_magic
    def _taskweaver_exec_post_check(self, line: str, local_ns: Dict[str, Any]):
        if "_" in local_ns:
            self.executor.ctx.set_output(local_ns["_"])
        return fmt_response(True, "", self.executor.get_post_execution_state())


@magics_class
class TaskWeaverPluginMagic(Magics):
    def __init__(self, shell: InteractiveShell, executor: Executor, **kwargs: Any):
        super(TaskWeaverPluginMagic, self).__init__(shell, **kwargs)
        self.executor = executor

    @line_cell_magic
    def _taskweaver_plugin_register(self, line: str, cell: str):
        plugin_name = line
        plugin_code = cell
        try:
            self.executor.register_plugin(plugin_name, plugin_code)
            return fmt_response(True, f"Plugin {plugin_name} registered.")
        except Exception as e:
            return fmt_response(
                False,
                f"Plugin {plugin_name} failed to register: " + str(e),
            )

    @line_magic
    def _taskweaver_plugin_test(self, line: str):
        plugin_name = line
        is_success, messages = self.executor.test_plugin(plugin_name)
        if is_success:
            return fmt_response(
                True,
                f"Plugin {plugin_name} passed tests: " + "\n".join(messages),
            )

        return fmt_response(
            False,
            f"Plugin {plugin_name} failed to test: " + "\n".join(messages),
        )

    @needs_local_scope
    @line_cell_magic
    def _taskweaver_plugin_load(self, line: str, cell: str, local_ns: Dict[str, Any]):
        plugin_name = line
        plugin_config: Any = json.loads(cell)
        try:
            self.executor.config_plugin(plugin_name, plugin_config)
            local_ns[plugin_name] = self.executor.get_plugin_instance(plugin_name)
            return fmt_response(True, f"Plugin {plugin_name} loaded.")
        except Exception as e:
            return fmt_response(
                False,
                f"Plugin {plugin_name} failed to load: " + str(e),
            )

    @needs_local_scope
    @line_magic
    def _taskweaver_plugin_unload(self, line: str, local_ns: Dict[str, Any]):
        plugin_name = line
        if plugin_name not in local_ns:
            return fmt_response(
                True,
                f"Plugin {plugin_name} not loaded, skipping unloading.",
            )
        del local_ns[plugin_name]
        return fmt_response(True, f"Plugin {plugin_name} unloaded.")


def load_ipython_extension(ipython: InteractiveShell):
    env_id = os.environ.get("TASKWEAVER_ENV_ID", "local")
    session_id = os.environ.get("TASKWEAVER_SESSION_ID", "session_temp")
    session_dir = os.environ.get(
        "TASKWEAVER_SESSION_DIR",
        os.path.realpath(os.getcwd()),
    )

    executor = Executor(
        env_id=env_id,
        session_id=session_id,
        session_dir=session_dir,
    )

    ctx_magic = TaskWeaverContextMagic(ipython, executor)
    plugin_magic = TaskWeaverPluginMagic(ipython, executor)

    ipython.register_magics(ctx_magic)
    ipython.register_magics(plugin_magic)
    ipython.InteractiveTB.set_mode(mode="Plain")
