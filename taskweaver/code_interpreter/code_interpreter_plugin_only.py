import json
from typing import Optional

from injector import inject

from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.code_interpreter.code_generator import CodeGeneratorPluginOnly
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.role import Role


class CodeInterpreterConfig(ModuleConfig):
    def _configure(self):
        self._set_name("code_interpreter_plugin_only")
        self.use_local_uri = self._get_bool("use_local_uri", False)
        self.max_retry_count = self._get_int("max_retry_count", 3)


class CodeInterpreterPluginOnly(Role):
    @inject
    def __init__(
        self,
        generator: CodeGeneratorPluginOnly,
        executor: CodeExecutor,
        logger: TelemetryLogger,
        event_emitter: SessionEventEmitter,
        config: CodeInterpreterConfig,
    ):
        self.generator = generator
        self.executor = executor
        self.logger = logger
        self.config = config
        self.retry_count = 0
        self.return_index = 0

        self.logger.info("CodeInterpreter initialized successfully.")

    def reply(
        self,
        memory: Memory,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: Optional[bool] = False,
    ) -> Post:
        response: Post = self.generator.reply(
            memory,
        )

        if response.message is not None:
            return response

        functions = json.loads(response.get_attachment(type=AttachmentType.function)[0])
        if len(functions) > 0:
            code = []
            for i, f in enumerate(functions):
                function_name = f["name"]
                function_args = json.loads(f["arguments"])
                function_call = (
                    f"r{self.return_index + i}={function_name}("
                    + ", ".join(
                        [
                            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}"
                            for key, value in function_args.items()
                        ],
                    )
                    + ")"
                )
                code.append(function_call)
            code.append(f'{", ".join([f"r{self.return_index + i}" for i in range(len(functions))])}')
            self.return_index += len(functions)

            self.event_emitter.emit_compat("code", "\n".join(code))
            exec_result = self.executor.execute_code(
                exec_id=response.id,
                code="\n".join(code),
            )

            response.message = self.executor.format_code_output(
                exec_result,
                with_code=True,
                use_local_uri=self.config.use_local_uri,
            )
            event_handler("CodeInterpreter-> Planner", response.message)
        else:
            response.message = "No code is generated because no function is selected."
            event_handler("CodeInterpreter-> Planner", response.message)

        return response
