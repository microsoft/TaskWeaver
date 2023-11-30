import os
from typing import List, Optional

from injector import inject

from taskweaver.code_interpreter.code_generator.code_verification import CodeVerificationConfig
from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm import LLMApi
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Attachment, Conversation, Memory, Post, Round
from taskweaver.memory.plugin import PluginRegistry
from taskweaver.misc.example import load_examples
from taskweaver.role import PostTranslator, Role
from taskweaver.utils import read_yaml
from taskweaver.utils.llm_api import ChatMessageType, format_chat_message


class CodeGeneratorConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("code_generator")
        self.role_name = self._get_str("role_name", "ProgramApe")
        self.executor_name = self._get_str("executor_name", "CodeExecutor")
        self.load_plugin = self._get_bool("load_plugin", True)
        self.load_example = self._get_bool("load_example", True)
        self.prompt_file_path = self._get_path(
            "prompt_file_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "code_generator_json_prompt.yaml",
            ),
        )
        self.example_base_path = self._get_path(
            "example_base_path",
            os.path.join(
                self.src.app_base_path,
                "codeinterpreter_examples",
            ),
        )


class CodeGenerator(Role):
    @inject
    def __init__(
        self,
        config: CodeGeneratorConfig,
        plugin_registry: PluginRegistry,
        logger: TelemetryLogger,
        llm_api: LLMApi,
        code_verification_config: CodeVerificationConfig,
    ):
        self.config = config
        self.plugin_registry = plugin_registry
        self.logger = logger
        self.llm_api = llm_api
        self.code_verification_config = code_verification_config

        self.role_name = self.config.role_name
        self.executor_name = self.config.executor_name

        self.post_translator = PostTranslator(logger)
        self.prompt_data = read_yaml(self.config.prompt_file_path)

        self.instruction_template = self.prompt_data["content"]
        self.query_requirements = self.prompt_data["requirements"].format(
            PLUGIN_ONLY_PROMPT=self.compose_plugin_only_requirements(),
            ROLE_NAME=self.role_name,
        )
        self.plugin_spec = self.load_plugins()
        self.examples = self.load_examples()

        self.instruction = self.instruction_template.format(
            ROLE_NAME=self.role_name,
            EXECUTOR_NAME=self.executor_name,
            PLUGIN=self.plugin_spec,
        )

    def compose_plugin_only_requirements(self):
        requirements = []
        if not self.code_verification_config.code_verification_on:
            return ""
        if self.code_verification_config.plugin_only:
            requirements.append(
                f"- {self.role_name} should only use the following plugins and"
                + " Python built-in functions to complete the task: "
                + ", ".join([f"{plugin.name}" for plugin in self.plugin_registry.get_list()]),
            )
            requirements.append(f"- {self.role_name} cannot define new functions or plugins.")
        allowed_modules = self.code_verification_config.allowed_modules
        if len(allowed_modules) > 0:
            requirements.append(
                f"- {self.role_name} can only import the following Python modules: "
                + ", ".join([f"{module}" for module in allowed_modules]),
            )
        if len(allowed_modules) == 0 and self.code_verification_config.plugin_only:
            requirements.append(f"- {self.role_name} cannot import any Python modules.")
        return "\n".join(requirements)

    def compose_prompt(self, rounds: List[Round]) -> List[ChatMessageType]:
        chat_history = [format_chat_message(role="system", message=self.instruction)]
        for i, example in enumerate(self.examples):
            chat_history.extend(self.compose_conversation(example.rounds, i + 1))
        chat_history.extend(
            self.compose_conversation(
                rounds,
                len(self.examples) + 1,
                add_requirements=True,
            ),
        )
        return chat_history

    def compose_conversation(
        self,
        rounds: List[Round],
        index: int,
        add_requirements: bool = False,
    ) -> List[ChatMessageType]:
        def format_attachment(attachment: Attachment):
            if attachment.type == "thought":
                return attachment.content.format(ROLE_NAME=self.role_name)
            else:
                return attachment.content

        chat_history = []
        is_first_post = True
        for round_index, conversation_round in enumerate(rounds):
            for post_index, post in enumerate(conversation_round.post_list):
                # compose user query
                user_message = ""
                assistant_message = ""

                if is_first_post:
                    user_message = f"==============================\n" f"## Conversation-{index}\n"
                    is_first_post = False

                if post.send_from == "Planner" and post.send_to == "CodeInterpreter":
                    user_query = conversation_round.user_query
                    plan = next(iter(post.get_attachment(type="plan")), None)
                    enrichment = ""
                    if plan is not None:
                        enrichment = (
                            f"To complete this request:{user_query}\n\n"
                            f"I have drawn up a plan: \n{plan}\n\n"
                            f"Please proceed with this step of this plan:"
                        )

                    user_message += f"-----------------------------\n" f"- User: {enrichment}{post.message}"
                elif post.send_from == "CodeInterpreter" and post.send_to == "CodeInterpreter":
                    # for code correction
                    user_message += (
                        f"-----------------------------\n" f"- User: {post.get_attachment('revise_message')[0]}"
                    )

                    assistant_message = self.post_translator.post_to_raw_text(
                        post=post,
                        content_formatter=format_attachment,
                        if_format_message=False,
                        if_format_send_to=False,
                        ignore_types=["revise_message"],
                    )
                elif post.send_from == "CodeInterpreter" and post.send_to == "Planner":
                    assistant_message = self.post_translator.post_to_raw_text(
                        post=post,
                        content_formatter=format_attachment,
                        if_format_message=False,
                        if_format_send_to=False,
                        ignore_types=["revise_message"],
                    )
                else:
                    raise ValueError(f"Invalid post: {post}")

                if len(assistant_message) > 0:
                    chat_history.append(
                        format_chat_message(
                            role="assistant",
                            message=assistant_message,
                        ),
                    )
                if len(user_message) > 0:
                    # add requirements to the last user message
                    if add_requirements and post_index == len(conversation_round.post_list) - 1:
                        user_message += f"\n{self.query_requirements}"
                    chat_history.append(
                        format_chat_message(role="user", message=user_message),
                    )

        return chat_history

    def reply(
        self,
        memory: Memory,
        event_handler: callable,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: Optional[bool] = False,
    ) -> Post:
        rounds = memory.get_role_rounds(
            role="CodeInterpreter",
            include_failure_rounds=False,
        )
        prompt = self.compose_prompt(rounds)

        def early_stop(type, value):
            if type in ["text", "python", "sample"]:
                return True
            else:
                return False

        response = self.post_translator.raw_text_to_post(
            llm_output=self.llm_api.chat_completion(prompt, use_backup_engine=use_back_up_engine)["content"],
            send_from="CodeInterpreter",
            event_handler=event_handler,
            early_stop=early_stop,
        )
        response.send_to = "Planner"
        for attachment in response.attachment_list:
            if attachment.type in ["sample", "text"]:
                response.message = attachment.content

        if prompt_log_path is not None:
            self.logger.dump_log_file(prompt, prompt_log_path)

        return response

    def load_plugins(self) -> str:
        if self.config.load_plugin:
            return "\n".join(
                [plugin.format_prompt() for plugin in self.plugin_registry.get_list()],
            )
        return ""

    def load_examples(self) -> List[Conversation]:
        if self.config.load_example:
            return load_examples(folder=self.config.example_base_path, has_plugins=True)
        return []


def format_code_revision_message() -> str:
    return (
        "The execution of the previous generated code has failed. "
        "If you think you can fix the problem by rewriting the code, "
        "please generate code and run it again.\n"
        "Otherwise, please explain the problem to me."
    )
