import os
from typing import Literal, Optional

from injector import inject

from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.code_interpreter.code_generator import CodeGenerator, format_code_revision_message
from taskweaver.code_interpreter.code_generator.code_generator import format_output_revision_message
from taskweaver.code_interpreter.code_verification import code_snippet_verification, format_code_correction_message
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import PostEventProxy, SessionEventEmitter
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
            [
                "pandas",
                "matplotlib",
                "numpy",
                "sklearn",
                "scipy",
                "seaborn",
                "datetime",
                "typing",
            ],
        )


def update_verification(
    response: PostEventProxy,
    status: Literal["NONE", "INCORRECT", "CORRECT"] = "NONE",
    error: str = "No verification is done.",
):
    response.update_attachment(status, AttachmentType.verification)
    response.update_attachment(
        error,
        AttachmentType.code_error,
    )


def update_execution(
    response: PostEventProxy,
    status: Literal["NONE", "SUCCESS", "FAILURE"] = "NONE",
    result: str = "No code is executed.",
):
    response.update_attachment(status, AttachmentType.execution_status)
    response.update_attachment(result, AttachmentType.execution_result)


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
        post_proxy = self.event_emitter.create_post_proxy("CodeInterpreter")
        post_proxy.update_status("generating code")
        self.generator.reply(
            memory,
            post_proxy,
            prompt_log_path,
            use_back_up_engine,
        )

        if post_proxy.post.message is not None and post_proxy.post.message != "":  # type: ignore
            update_verification(
                post_proxy,
                "NONE",
                "No code verification is performed.",
            )
            update_execution(post_proxy, "NONE", "No code is executed.")
            return post_proxy.end()

        code = next(
            (a for a in post_proxy.post.attachment_list if a.type == AttachmentType.python),
            None,
        )

        if code is None:
            # no code is generated is usually due to the failure of parsing the llm output
            update_verification(
                post_proxy,
                "NONE",
                "No code verification is performed.",
            )
            update_execution(
                post_proxy,
                "NONE",
                "No code is executed due to code generation failure.",
            )
            post_proxy.update_message("Failed to generate code.")
            if self.retry_count < self.config.max_retry_count:
                error_message = format_output_revision_message()
                post_proxy.update_attachment(
                    error_message,
                    AttachmentType.revise_message,
                )
                post_proxy.update_send_to("CodeInterpreter")
                self.retry_count += 1
            else:
                self.retry_count = 0

            return post_proxy.end()

        post_proxy.update_status("verifying code")
        self.logger.info(f"Code to be verified: {code.content}")
        code_verify_errors = code_snippet_verification(
            code.content,
            [plugin.name for plugin in self.generator.get_plugin_pool()],
            self.config.code_verification_on,
            plugin_only=False,
            allowed_modules=self.config.allowed_modules,
        )

        if code_verify_errors is None:
            update_verification(
                post_proxy,
                "NONE",
                "No code verification is performed.",
            )
        elif len(code_verify_errors) > 0:
            self.logger.info(
                f"Code verification finished with {len(code_verify_errors)} errors.",
            )
            code_error = "\n".join(code_verify_errors)
            update_verification(post_proxy, "INCORRECT", code_error)
            post_proxy.update_message(code_error)
            if self.retry_count < self.config.max_retry_count:
                post_proxy.update_attachment(
                    format_code_correction_message(),
                    AttachmentType.revise_message,
                )
                post_proxy.update_send_to("CodeInterpreter")
                self.retry_count += 1
            else:
                self.retry_count = 0

            # add execution status and result
            update_execution(
                post_proxy,
                "NONE",
                "No code is executed due to code verification failure.",
            )
            return post_proxy.end()
        elif len(code_verify_errors) == 0:
            update_verification(post_proxy, "CORRECT", "No error is found.")

        post_proxy.update_status("executing code")
        self.logger.info(f"Code to be executed: {code.content}")

        exec_result = self.executor.execute_code(
            exec_id=post_proxy.post.id,
            code=code.content,
        )

        code_output = self.executor.format_code_output(
            exec_result,
            with_code=False,
            use_local_uri=self.config.use_local_uri,
        )

        update_execution(
            post_proxy,
            status="SUCCESS" if exec_result.is_success else "FAILURE",
            result=code_output,
        )

        # add artifact paths
        post_proxy.update_attachment(
            [
                (
                    a.file_name
                    if os.path.isabs(a.file_name) or not self.config.use_local_uri
                    else os.path.join(self.executor.execution_cwd, a.file_name)
                )
                for a in exec_result.artifact
            ],  # type: ignore
            AttachmentType.artifact_paths,
        )

        post_proxy.update_message(
            self.executor.format_code_output(
                exec_result,
                with_code=True,  # the message to be sent to the user should contain the code
                use_local_uri=self.config.use_local_uri,
            ),
        )

        if exec_result.is_success or self.retry_count >= self.config.max_retry_count:
            self.retry_count = 0
        else:
            post_proxy.update_send_to("CodeInterpreter")
            post_proxy.update_attachment(
                format_code_revision_message(),
                AttachmentType.revise_message,
            )
            self.retry_count += 1
        return post_proxy.end()
