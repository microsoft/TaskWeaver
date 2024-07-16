from typing import Optional

from injector import inject

from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.code_interpreter.code_interpreter_cli_only import CodeGeneratorCLIOnly
from taskweaver.code_interpreter.interpreter import Interpreter
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.module.tracing import Tracing, tracing_decorator
from taskweaver.role import Role
from taskweaver.role.role import RoleConfig, RoleEntry


class CodeInterpreterConfig(RoleConfig):
    def _configure(self):
        self.use_local_uri = self._get_bool("use_local_uri", False)
        self.max_retry_count = self._get_int("max_retry_count", 3)


class CodeInterpreterCLIOnly(Role, Interpreter):
    @inject
    def __init__(
        self,
        generator: CodeGeneratorCLIOnly,
        executor: CodeExecutor,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        config: CodeInterpreterConfig,
        role_entry: RoleEntry,
    ):
        super().__init__(config, logger, tracing, event_emitter, role_entry)

        self.generator = generator
        self.generator.set_alias(self.alias)
        self.executor = executor
        self.retry_count = 0
        self.return_index = 0

        self.logger.info(f"{self.alias} initialized successfully.")

    def update_session_variables(self, session_variables: dict) -> None:
        assert False, "Not implemented"

    @tracing_decorator
    def reply(
        self,
        memory: Memory,
        prompt_log_path: Optional[str] = None,
    ) -> Post:
        post_proxy = self.event_emitter.create_post_proxy(self.alias)
        self.generator.reply(
            memory,
            post_proxy=post_proxy,
            prompt_log_path=prompt_log_path,
        )

        code = post_proxy.post.get_attachment(type=AttachmentType.reply_content)[0]
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

    def close(self) -> None:
        self.generator.close()
        self.executor.stop()
        super().close()
