import json
import os
from typing import List, Optional, cast

from injector import inject

from taskweaver.llm import LLMApi, format_chat_message
from taskweaver.llm.util import ChatMessageType, PromptTypeWithTools
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post, Round
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import PostEventProxy, SessionEventEmitter
from taskweaver.module.tracing import Tracing, tracing_decorator
from taskweaver.role import Role
from taskweaver.role.role import RoleConfig
from taskweaver.utils import read_yaml


class CodeGeneratorCLIOnlyConfig(RoleConfig):
    def _configure(self) -> None:
        self._set_name("code_generator")
        self.role_name = self._get_str("role_name", "ProgramApe")

        self.prompt_file_path = self._get_path(
            "prompt_file_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "code_generator_prompt_cli_only.yaml",
            ),
        )
        self.prompt_compression = self._get_bool("prompt_compression", False)
        assert self.prompt_compression is False, "Compression is not supported for CLI only mode."

        self.compression_prompt_path = self._get_path(
            "compression_prompt_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "compression_prompt.yaml",
            ),
        )


class CodeGeneratorCLIOnly(Role):
    @inject
    def __init__(
        self,
        config: CodeGeneratorCLIOnlyConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        llm_api: LLMApi,
    ):
        super().__init__(config, logger, tracing, event_emitter)
        self.config = config
        self.llm_api = llm_api

        self.role_name: str = self.config.role_name

        self.prompt_data = read_yaml(self.config.prompt_file_path)
        self.instruction_template = self.prompt_data["content"]

        import platform

        self.os_name = platform.system()
        self.cli_name = os.environ.get("SHELL") or os.environ.get("COMSPEC")

    @tracing_decorator
    def reply(
        self,
        memory: Memory,
        post_proxy: Optional[PostEventProxy] = None,
        prompt_log_path: Optional[str] = None,
        **kwargs: ...,
    ) -> Post:
        assert post_proxy is not None, "Post proxy is not provided."

        # extract all rounds from memory
        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )

        prompt = self._compose_prompt(
            system_instructions=self.instruction_template.format(
                ROLE_NAME=self.alias,
                OS_NAME=self.os_name,
            ),
            rounds=rounds,
        )
        post_proxy.update_send_to("Planner")

        if prompt_log_path is not None:
            self.logger.dump_prompt_file(
                cast(PromptTypeWithTools, {"prompt": prompt}),
                prompt_log_path,
            )

        prompt_size = self.tracing.count_tokens(json.dumps(prompt))
        self.tracing.set_span_attribute("prompt_size", prompt_size)
        self.tracing.add_prompt_size(
            size=prompt_size,
            labels={
                "direction": "input",
            },
        )

        self.tracing.set_span_attribute("prompt", json.dumps(prompt, indent=2))
        llm_response = self.llm_api.chat_completion(
            messages=prompt,
            response_format=None,
            stream=False,
        )

        try:
            response_content = llm_response["content"]
            if response_content.startswith("```json"):
                response_content = response_content[7:-3]
            llm_response = json.loads(response_content)
            output_size = self.tracing.count_tokens(llm_response)
            self.tracing.set_span_attribute("output_size", output_size)
            self.tracing.add_prompt_size(
                size=output_size,
                labels={
                    "direction": "output",
                },
            )
        except json.JSONDecodeError:
            self.tracing.set_span_status(
                "ERROR",
                f"Failed to decode LLM response {llm_response}.",
            )
            raise ValueError(f"Unexpected response from LLM: {llm_response}")

        assert "description" in llm_response, "Description is not found in LLM response."
        assert "code" in llm_response, "Code is not found in LLM response."

        if (
            self.os_name == "Windows"
            and len(llm_response["code"]) != 0
            and not llm_response["code"].startswith("powershell -Command")
        ):
            llm_response["code"] = f"powershell -Command {llm_response['code']}"

        post_proxy.update_attachment(
            llm_response["description"],
            AttachmentType.thought,
        )
        post_proxy.update_attachment("python", AttachmentType.reply_type)
        post_proxy.update_attachment(llm_response["code"], AttachmentType.reply_content)

        self.tracing.set_span_attribute("code", llm_response["code"])

        return post_proxy.end()

    def _compose_prompt(
        self,
        system_instructions: str,
        rounds: List[Round],
    ) -> List[ChatMessageType]:
        prompt = [format_chat_message(role="system", message=system_instructions)]

        for _round in rounds:
            for post in _round.post_list:
                if post.send_to == self.alias:
                    prompt.append(
                        format_chat_message(role="user", message=post.message),
                    )
                elif post.send_from == self.alias:
                    prompt.append(
                        format_chat_message(role="assistant", message=post.message),
                    )

        return prompt
