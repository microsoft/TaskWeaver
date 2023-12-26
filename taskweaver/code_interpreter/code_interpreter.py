import os
from typing import Literal, Optional

from injector import inject

from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.code_interpreter.code_generator import CodeGenerator, format_code_revision_message
from taskweaver.code_interpreter.code_generator.code_generator import format_output_revision_message
from taskweaver.code_interpreter.code_verification import code_snippet_verification, format_code_correction_message
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Attachment, Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.role import Role


class CodeInterpreterConfig(ModuleConfig):
    def _configure(self):
        self._set_name("code_interpreter")
        self.use_local_uri = self._get_bool("use_local_uri", False)
        self.max_retry_count = self._get_int("max_retry_count", 3)

        # for verification
        self.code_verification_on = self._get_bool("code_verification_on", False)
        self.allowed_modules = self._get_list(
            "allowed_modules",
            ["pandas", "matplotlib", "numpy", "sklearn", "scipy", "seaborn", "datetime", "typing"],
        )


def update_verification(
    response: Post,
    status: Literal["NONE", "INCORRECT", "CORRECT"] = "NONE",
    error: str = "No verification is done.",
):
    response.add_attachment(Attachment.create(AttachmentType.verification, status))
    response.add_attachment(
        Attachment.create(AttachmentType.code_error, error),
    )


def update_execution(
    response: Post,
    status: Literal["NONE", "SUCCESS", "FAILURE"] = "NONE",
    result: str = "No code is executed.",
):
    response.add_attachment(Attachment.create(AttachmentType.execution_status, status))
    response.add_attachment(
        Attachment.create(AttachmentType.execution_result, result),
    )


class CodeInterpreter(Role):
    @inject
    def __init__(
        self,
        generator: CodeGenerator,
        executor: CodeExecutor,
        logger: TelemetryLogger,
        event_emitter: SessionEventEmitter,
        config: CodeInterpreterConfig,
    ):
        self.config = config

        self.generator = generator
        self.generator.configure_verification(
            code_verification_on=self.config.code_verification_on,
            allowed_modules=self.config.allowed_modules,
        )

        self.executor = executor
        self.logger = logger
        self.event_emitter = event_emitter
        self.retry_count = 0

        self.logger.info("CodeInterpreter initialized successfully.")

    def reply(
        self,
        memory: Memory,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: bool = False,
    ) -> Post:
        response: Post = self.generator.reply(
            memory,
            prompt_log_path,
            use_back_up_engine,
        )
        if response.message is not None:
            update_verification(response, "NONE", "No code verification is performed.")
            update_execution(response, "NONE", "No code is executed.")
            self.event_emitter.emit_compat("CodeInterpreter->Planner", response.message)
            return response

        code = next((a for a in response.attachment_list if a.type == AttachmentType.python), None)

        if code is None:
            # no code is generated is usually due to the failure of parsing the llm output
            update_verification(response, "NONE", "No code verification is performed.")
            update_execution(response, "NONE", "No code is executed due to code generation failure.")
            response.message = "Failed to generate code."
            if self.retry_count < self.config.max_retry_count:
                error_message = format_output_revision_message()
                response.add_attachment(
                    Attachment.create(
                        AttachmentType.revise_message,
                        error_message,
                    ),
                )
                response.send_to = "CodeInterpreter"
                self.event_emitter.emit_compat(
                    "CodeInterpreter->CodeInterpreter",
                    error_message,
                )
                self.retry_count += 1
            else:
                self.retry_count = 0
                self.event_emitter.emit_compat("CodeInterpreter->Planner", response.message)

            return response

        self.logger.info(f"Code to be verified: {code.content}")
        code_verify_errors = code_snippet_verification(
            code.content,
            [plugin.name for plugin in self.generator.get_plugin_pool()],
            self.config.code_verification_on,
            plugin_only=False,
            allowed_modules=self.config.allowed_modules,
        )

        if code_verify_errors is None:
            self.event_emitter.emit_compat("verification", "NONE")
            update_verification(response, "NONE", "No code verification is performed.")
        elif len(code_verify_errors) > 0:
            self.logger.info(
                f"Code verification finished with {len(code_verify_errors)} errors.",
            )
            code_error = "\n".join(code_verify_errors)
            self.event_emitter.emit_compat("verification", f"INCORRECT: {code_error}")
            update_verification(response, "INCORRECT", code_error)
            response.message = code_error
            if self.retry_count < self.config.max_retry_count:
                response.add_attachment(
                    Attachment.create(
                        AttachmentType.revise_message,
                        format_code_correction_message(),
                    ),
                )
                response.send_to = "CodeInterpreter"
                self.event_emitter.emit_compat(
                    "CodeInterpreter->CodeInterpreter",
                    format_code_correction_message(),
                )
                self.retry_count += 1
            else:
                self.retry_count = 0
                self.event_emitter.emit_compat("CodeInterpreter->Planner", response.message)

            # add execution status and result
            update_execution(response, "NONE", "No code is executed due to code verification failure.")
            return response
        elif len(code_verify_errors) == 0:
            self.event_emitter.emit_compat("verification", "CORRECT")
            update_verification(response, "CORRECT", "No error is found.")

        self.logger.info(f"Code to be executed: {code.content}")

        exec_result = self.executor.execute_code(
            exec_id=response.id,
            code=code.content,
        )
        self.event_emitter.emit_compat("status", "SUCCESS" if exec_result.is_success else "FAILURE")
        code_output = self.executor.format_code_output(
            exec_result,
            with_code=False,
            use_local_uri=self.config.use_local_uri,
        )

        self.event_emitter.emit_compat("result", code_output)
        update_execution(
            response,
            status="SUCCESS" if exec_result.is_success else "FAILURE",
            result=code_output,
        )

        # add artifact paths
        response.add_attachment(
            Attachment.create(
                AttachmentType.artifact_paths,
                [
                    (
                        a.file_name
                        if os.path.isabs(a.file_name) or not self.config.use_local_uri
                        else os.path.join(self.executor.execution_cwd, a.file_name)
                    )
                    for a in exec_result.artifact
                ],
            ),
        )

        response.message = self.executor.format_code_output(
            exec_result,
            with_code=True,  # the message to be sent to the user should contain the code
            use_local_uri=self.config.use_local_uri,
        )

        if exec_result.is_success or self.retry_count >= self.config.max_retry_count:
            self.retry_count = 0
            self.event_emitter.emit_compat("CodeInterpreter->Planner", response.message)
        else:
            response.add_attachment(
                Attachment.create(
                    AttachmentType.revise_message,
                    format_code_revision_message(),
                ),
            )
            response.send_to = "CodeInterpreter"
            self.event_emitter.emit_compat(
                "CodeInterpreter->CodeInterpreter",
                format_code_revision_message(),
            )
            self.retry_count += 1
        return response
