from typing import Optional

from injector import inject
from opentelemetry.trace import StatusCode

from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.code_interpreter.code_generator import CodeGeneratorCLIOnly
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.module.tracing import Tracing, get_current_span, get_tracer, tracing_decorator
from taskweaver.role import Role


class CodeInterpreterConfig(ModuleConfig):
    def _configure(self):
        self._set_name("code_interpreter_cli_only")
        self.use_local_uri = self._get_bool("use_local_uri", False)
        self.max_retry_count = self._get_int("max_retry_count", 3)


class CodeInterpreterCLIOnly(Role):
    @inject
    def __init__(
        self,
        generator: CodeGeneratorCLIOnly,
        executor: CodeExecutor,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        config: CodeInterpreterConfig,
    ):
        self.generator = generator
        self.executor = executor
        self.logger = logger
        self.config = config
        self.event_emitter = event_emitter
        self.retry_count = 0
        self.return_index = 0

        self.logger.info("CodeInterpreter initialized successfully.")

    @tracing_decorator
    def reply(
        self,
        memory: Memory,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: bool = False,
    ) -> Post:
        current_span = get_current_span()

        post_proxy = self.event_emitter.create_post_proxy("CodeInterpreter")
        self.generator.reply(
            memory,
            post_proxy=post_proxy,
            prompt_log_path=prompt_log_path,
            use_back_up_engine=use_back_up_engine,
        )

        code = post_proxy.post.get_attachment(type=AttachmentType.python)[0]
        if len(code) == 0:
            post_proxy.update_message(post_proxy.post.get_attachment(type=AttachmentType.thought)[0], is_end=True)
            current_span.set_status(StatusCode.OK, "No code is generated.")
            return post_proxy.end()

        code_to_exec = "! " + code
        with get_tracer().start_as_current_span("CodeInterpreterCLIOnly.execute_code") as span:
            span.set_attribute("code_to_exec", code_to_exec)

            exec_result = self.executor.execute_code(
                exec_id=post_proxy.post.id,
                code=code_to_exec,
            )

        CLI_res = exec_result.stderr if len(exec_result.stderr) != 0 else exec_result.stdout
        post_proxy.update_message(
            "\n".join(CLI_res),
            is_end=True,
        )

        if exec_result.is_success:
            current_span.set_status(StatusCode.OK, "Code is executed.")
        else:
            current_span.set_status(StatusCode.ERROR, "Code execution failed.")
        current_span.set_attribute("code_output", CLI_res)

        return post_proxy.end()
