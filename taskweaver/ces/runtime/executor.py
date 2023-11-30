import os
import tempfile
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from taskweaver.ces.common import EnvPlugin
from taskweaver.ces.runtime.context import ExecutorPluginContext, LogErrorLevel
from taskweaver.plugin.base import Plugin
from taskweaver.plugin.context import PluginContext


@dataclass
class PluginTestEntry:
    name: str
    description: str
    test: Callable[[Plugin], None]


@dataclass
class RuntimePlugin(EnvPlugin):
    initializer: Optional[type[Plugin]] = None
    test_cases: List[PluginTestEntry] = field(default_factory=list)

    @property
    def module_name(self) -> str:
        return f"taskweaver_ext.plugin.{self.name}"

    def load_impl(self):
        if self.loaded:
            return

        def register_plugin(impl: Type[Plugin]):
            if self.initializer is not None:
                raise Exception(
                    f"duplicated plugin impl registration for plugin {self.name}",
                )
            self.initializer = impl

        def register_plugin_test(
            test_name: str,
            test_desc: str,
            test_impl: Callable[[Plugin], None],
        ):
            self.test_cases.append(
                PluginTestEntry(
                    test_name,
                    test_desc,
                    test_impl,
                ),
            )

        try:
            # the following code is to load the plugin module and register the plugin
            import importlib
            import os
            import sys

            from taskweaver.plugin import register

            module_name = self.module_name
            with tempfile.TemporaryDirectory() as temp_dir:
                module_path = os.path.join(temp_dir, f"{self.name}.py")
                with open(module_path, "w") as f:
                    f.write(self.impl)

                spec = importlib.util.spec_from_file_location(  # type: ignore
                    module_name,
                    module_path,
                )
                module = importlib.util.module_from_spec(spec)  # type: ignore
                sys.modules[module_name] = module  # type: ignore

                register.register_plugin_inner = register_plugin
                register.register_plugin_test_inner = register_plugin_test
                spec.loader.exec_module(module)  # type: ignore
                register.register_plugin_inner = None
                register.register_plugin_test_inner = None

                if self.initializer is None:
                    raise Exception("no registration found")
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"failed to load plugin {self.name} {str(e)}")

        self.loaded = True

    def unload_impl(self):
        if not self.loaded:
            return

        # attempt to unload the module, though it is not guaranteed to work
        # there might be some memory leak or other issues there are still some references to
        # certain code inside of the original module
        try:
            self.initializer = None
            import sys

            del sys.modules[self.module_name]
        except Exception:
            pass
        self.loaded = False

    def get_instance(self, context: PluginContext) -> Plugin:
        if self.initializer is None:
            raise Exception(f"plugin {self.name} is not loaded")

        try:
            return self.initializer(self.name, context, self.config or {})
        except Exception as e:
            raise Exception(
                f"failed to create instance for plugin {self.name} {str(e)}",
            )

    def test_impl(self):
        error_list: List[str] = []

        from taskweaver.plugin.context import temp_context

        for test in self.test_cases:
            try:
                with temp_context() as ctx:
                    print("=====================================================")
                    print("Test Name:", test.name)
                    print("Test Description:", test.description)
                    print("Running Test...")
                    inst = self.get_instance(ctx)
                    test.test(inst)
                    print()
            except Exception as e:
                traceback.print_exc()
                error_list.append(
                    f"failed to test plugin {self.name} on {test.name} ({test.description}) \n {str(e)}",
                )

        return len(error_list) == 0, error_list


class Executor:
    def __init__(self, env_id: str, session_id: str, session_dir: str) -> None:
        self.env_id: str = env_id
        self.session_id: str = session_id
        self.session_dir: str = session_dir

        # Session var management
        self.session_var: Dict[str, str] = {}

        # Plugin management state
        self.plugin_registry: Dict[str, RuntimePlugin] = {}

        # Execution counter and id
        self.cur_execution_count: int = 0
        self.cur_execution_id: str = ""

        self._init_session_dir()
        self.ctx: ExecutorPluginContext = ExecutorPluginContext(self)

    def _init_session_dir(self):
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

    def pre_execution(self, exec_idx: int, exec_id: str):
        self.cur_execution_count = exec_idx
        self.cur_execution_id = exec_id

        self.ctx.artifact_list = []
        self.ctx.log_messages = []
        self.ctx.output = []

    def load_lib(self, local_ns: Dict[str, Any]):
        try:
            local_ns["pd"] = __import__("pandas")
        except ImportError:
            self.log(
                "warning",
                "recommended package pandas not found, certain functions may not work properly",
            )

        try:
            local_ns["np"] = __import__("numpy")
        except ImportError:
            self.log(
                "warning",
                "recommended package numpy not found, certain functions may not work properly",
            )

        try:
            local_ns["plt"] = __import__("matplotlib.pyplot")
        except ImportError:
            self.log(
                "warning",
                "recommended package matplotlib not found, certain functions may not work properly",
            )

    def register_plugin(self, plugin_name: str, plugin_impl: str):
        plugin = RuntimePlugin(
            plugin_name,
            plugin_impl,
            None,
            False,
        )
        plugin.load_impl()
        self.plugin_registry[plugin_name] = plugin

    def config_plugin(self, plugin_name: str, plugin_config: Dict[str, str]):
        plugin = self.plugin_registry[plugin_name]
        plugin.config = plugin_config

    def get_plugin_instance(self, plugin_name: str) -> Plugin:
        plugin = self.plugin_registry[plugin_name]
        return plugin.get_instance(self.ctx)

    def test_plugin(self, plugin_name: str) -> tuple[bool, list[str]]:
        plugin = self.plugin_registry[plugin_name]
        return plugin.test_impl()

    def get_post_execution_state(self):
        return {
            "artifact": self.ctx.artifact_list,
            "log": self.ctx.log_messages,
            "output": self.ctx.get_normalized_output(),
        }

    def log(self, level: LogErrorLevel, message: str):
        self.ctx.log(level, "Engine", message)

    def update_session_var(self, variables: Dict[str, str]):
        self.session_var = {str(k): str(v) for k, v in variables.items()}
