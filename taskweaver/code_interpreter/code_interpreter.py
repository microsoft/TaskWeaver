from typing import Optional

from injector import inject

from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.code_interpreter.code_generator import (
    CodeGenerator,
    code_snippet_verification,
    format_code_correction_message,
    format_code_revision_message,
)
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Attachment, Memory, Post
from taskweaver.role import Role


class CodeInterpreterConfig(ModuleConfig):
    def _configure(self):
        self._set_name("code_interpreter")
        self.use_local_uri = self._get_bool("use_local_uri", False)
        self.max_retry_count = self._get_int("max_retry_count", 3)


class CodeInterpreter(Role):
    @inject
    def __init__(
        self,
        generator: CodeGenerator,
        executor: CodeExecutor,
        logger: TelemetryLogger,
        config: CodeInterpreterConfig,
    ):
        self.generator = generator
        self.executor = executor
        self.logger = logger
        self.config = config
        self.retry_count = 0

    def reply(
        self,
        memory: Memory,
        event_handler: callable,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: Optional[bool] = False,
    ) -> Post:
        response: Post = self.generator.reply(
            memory,
            event_handler,
            prompt_log_path,
            use_back_up_engine,
        )
        if response.message is not None:
            response.add_attachment(Attachment.create("verification", "NONE"))
            response.add_attachment(
                Attachment.create("code_error", "No code is generated."),
            )
            response.add_attachment(Attachment.create("execution_status", "NONE"))
            response.add_attachment(
                Attachment.create("execution_result", "No code is executed."),
            )
            event_handler("CodeInterpreter->Planner", response.message)
            return response

        code = next((a for a in response.attachment_list if a.type == "python"), None)

        code_verify_errors = code_snippet_verification(
            code.content,
            [plugin.name for plugin in self.generator.plugin_registry.get_list()],
            self.generator.code_verification_config,
        )

        if code_verify_errors is None:
            event_handler("verification", "NONE")
            response.add_attachment(Attachment.create("verification", "NONE"))
            response.add_attachment(
                Attachment.create("code_error", "No code verification is performed."),
            )
        elif len(code_verify_errors) > 0:
            self.logger.info(
                f"Code verification finished with {len(code_verify_errors)} errors.",
            )
            code_error = "\n".join(code_verify_errors)
            event_handler("verification", f"INCORRECT: {code_error}")
            response.add_attachment(Attachment.create("verification", "INCORRECT"))
            response.add_attachment(Attachment.create("code_error", code_error))
            response.message = code_error
            if self.retry_count < self.config.max_retry_count:
                response.add_attachment(
                    Attachment.create(
                        "revise_message",
                        format_code_correction_message(),
                    ),
                )
                response.send_to = "CodeInterpreter"
                event_handler(
                    "CodeInterpreter->CodeInterpreter",
                    format_code_correction_message(),
                )
                self.retry_count += 1
            else:
                self.retry_count = 0
                event_handler("CodeInterpreter->Planner", response.message)

            # add execution status and result
            response.add_attachment(Attachment.create("execution_status", "NONE"))
            response.add_attachment(
                Attachment.create(
                    "execution_result",
                    "No code is executed due to code verification failure.",
                ),
            )
            return response
        elif len(code_verify_errors) == 0:
            event_handler("verification", "CORRECT")
            response.add_attachment(Attachment.create("verification", "CORRECT"))
            response.add_attachment(
                Attachment.create("code_error", "No error is found."),
            )

        self.logger.info(f"Code to be executed: {code.content}")

        exec_result = self.executor.execute_code(
            exec_id=response.id,
            code=code.content,
        )
        response.add_attachment(
            Attachment.create(
                "execution_status",
                "SUCCESS" if exec_result.is_success else "FAILURE",
            ),
        )
        event_handler("status", "SUCCESS" if exec_result.is_success else "FAILURE")

        response.add_attachment(
            Attachment.create(
                "execution_result",
                self.executor.format_code_output(
                    exec_result,
                    with_code=False,
                    use_local_uri=self.config.use_local_uri,
                ),
            ),
        )
        event_handler(
            "result",
            self.executor.format_code_output(
                exec_result,
                with_code=False,
                use_local_uri=self.config.use_local_uri,
            ),
        )

        response.message = self.executor.format_code_output(
            exec_result,
            use_local_uri=self.config.use_local_uri,
        )
        if exec_result.is_success or self.retry_count >= self.config.max_retry_count:
            self.retry_count = 0
            event_handler("CodeInterpreter->Planner", response.message)
        else:
            response.add_attachment(
                Attachment.create(
                    "revise_message",
                    format_code_revision_message(),
                ),
            )
            response.send_to = "CodeInterpreter"
            event_handler(
                "CodeInterpreter->CodeInterpreter",
                format_code_revision_message(),
            )
            self.retry_count += 1
        return response
