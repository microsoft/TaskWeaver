from typing import Optional

from injector import inject

from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.code_interpreter.code_generator import CodeGeneratorCLIOnly
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.module.tracing import Tracing, tracing_decorator
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
        self.tracing = tracing
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
    ) -> Post:
        post_proxy = self.event_emitter.create_post_proxy("CodeInterpreter")
        self.generator.reply(
            memory,
            post_proxy=post_proxy,
            prompt_log_path=prompt_log_path,
        )

        code = post_proxy.post.get_attachment(type=AttachmentType.python)[0]
        if len(code) == 0:
            post_proxy.update_message(post_proxy.post.get_attachment(type=AttachmentType.thought)[0], is_end=True)
            return post_proxy.end()

        code_to_exec = "! " + code

        self.tracing.set_span_attribute("code", code_to_exec)

        exec_result = self.executor.execute_code(
            exec_id=post_proxy.post.id,
            code=code_to_exec,
        )

        CLI_res = exec_result.stderr if len(exec_result.stderr) != 0 else exec_result.stdout
        post_proxy.update_message(
            "\n".join(CLI_res),
            is_end=True,
        )

        if not exec_result.is_success:
            self.tracing.set_span_status("ERROR", "Code execution failed.")
        self.tracing.set_span_attribute("code_output", CLI_res)

        reply_post = post_proxy.end()

        self.tracing.set_span_attribute("out.from", reply_post.send_from)
        self.tracing.set_span_attribute("out.to", reply_post.send_to)
        self.tracing.set_span_attribute("out.message", reply_post.message)
        self.tracing.set_span_attribute("out.attachments", str(reply_post.attachment_list))

        return reply_post
