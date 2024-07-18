import datetime
import json
import os
from typing import List, Optional

from injector import inject

from taskweaver.code_interpreter.plugin_selection import PluginSelector, SelectedPluginPool
from taskweaver.llm import LLMApi
from taskweaver.llm.util import ChatMessageType, format_chat_message
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Attachment, Conversation, Memory, Post, Round, RoundCompressor
from taskweaver.memory.attachment import AttachmentType
from taskweaver.memory.experience import Experience, ExperienceGenerator
from taskweaver.memory.plugin import PluginEntry, PluginRegistry
from taskweaver.misc.example import load_examples
from taskweaver.module.event_emitter import PostEventProxy, SessionEventEmitter
from taskweaver.module.tracing import Tracing, tracing_decorator
from taskweaver.role import PostTranslator, Role
from taskweaver.role.role import RoleConfig
from taskweaver.utils import read_yaml


class CodeGeneratorConfig(RoleConfig):
    def _configure(self) -> None:
        self._set_name("code_generator")
        self.role_name = self._get_str("role_name", "ProgramApe")
        self.load_plugin = self._get_bool("load_plugin", True)
        self.load_example = self._get_bool("load_example", True)
        self.prompt_file_path = self._get_path(
            "prompt_file_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "code_generator_prompt.yaml",
            ),
        )
        self.example_base_path = self._get_path(
            "example_base_path",
            os.path.join(
                self.src.app_base_path,
                "codeinterpreter_examples",
            ),
        )
        self.prompt_compression = self._get_bool("prompt_compression", False)
        self.compression_prompt_path = self._get_path(
            "compression_prompt_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "compression_prompt.yaml",
            ),
        )
        self.enable_auto_plugin_selection = self._get_bool(
            "enable_auto_plugin_selection",
            False,
        )
        self.auto_plugin_selection_topk = self._get_int("auto_plugin_selection_topk", 3)

        self.use_experience = self._get_bool("use_experience", False)

        self.llm_alias = self._get_str("llm_alias", default="", required=False)


class CodeGenerator(Role):
    @inject
    def __init__(
        self,
        config: CodeGeneratorConfig,
        plugin_registry: PluginRegistry,
        logger: TelemetryLogger,
        event_emitter: SessionEventEmitter,
        tracing: Tracing,
        llm_api: LLMApi,
        round_compressor: RoundCompressor,
        post_translator: PostTranslator,
        experience_generator: ExperienceGenerator,
    ):
        super().__init__(config, logger, tracing, event_emitter)
        self.llm_api = llm_api

        self.role_name = self.config.role_name

        self.post_translator = post_translator
        self.prompt_data = read_yaml(self.config.prompt_file_path)

        self.instruction_template = self.prompt_data["content"]

        self.conversation_head_template = self.prompt_data["conversation_head"]
        self.user_message_head_template = self.prompt_data["user_message_head"]
        self.plugin_pool = plugin_registry.get_list()
        self.query_requirements_template = self.prompt_data["requirements"]
        self.response_json_schema = json.loads(self.prompt_data["response_json_schema"])

        self.examples = None
        self.code_verification_on: bool = False
        self.allowed_modules: List[str] = []

        self.round_compressor: RoundCompressor = round_compressor
        self.compression_template = read_yaml(self.config.compression_prompt_path)["content"]

        if self.config.enable_auto_plugin_selection:
            self.plugin_selector = PluginSelector(plugin_registry, self.llm_api)
            self.plugin_selector.load_plugin_embeddings()
            logger.info("Plugin embeddings loaded")
            self.selected_plugin_pool = SelectedPluginPool()

        if self.config.use_experience:
            self.experience_generator = experience_generator
            self.experience_generator.refresh()
            self.experience_generator.load_experience()
            self.logger.info(
                "Experience loaded successfully, "
                "there are {} experiences".format(len(self.experience_generator.experience_list)),
            )

        self.logger.info("CodeGenerator initialized successfully")

    def configure_verification(
        self,
        code_verification_on: bool,
        allowed_modules: Optional[List[str]] = None,
        blocked_functions: Optional[List[str]] = None,
    ):
        self.allowed_modules = allowed_modules if allowed_modules is not None else []
        self.code_verification_on = code_verification_on
        self.blocked_functions = blocked_functions

    def compose_verification_requirements(
        self,
    ) -> str:
        requirements: List[str] = []
        if not self.code_verification_on:
            return ""

        if len(self.allowed_modules) > 0:
            requirements.append(
                f"- {self.role_name} can only import the following Python modules: "
                + ", ".join([f"{module}" for module in self.allowed_modules]),
            )

        if len(self.allowed_modules) == 0:
            requirements.append(f"- {self.role_name} cannot import any Python modules.")

        if len(self.blocked_functions) > 0:
            requirements.append(
                f"- {self.role_name} cannot use the following Python functions: "
                + ", ".join([f"{function}" for function in self.blocked_functions]),
            )
        return "\n".join(requirements)

    def compose_sys_prompt(self, context: str):
        return self.instruction_template.format(
            ENVIRONMENT_CONTEXT=context,
            ROLE_NAME=self.role_name,
            RESPONSE_JSON_SCHEMA=json.dumps(self.response_json_schema),
        )

    def get_env_context(self):
        # get date and time
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        return f"- Current time: {current_time}"

    def compose_prompt(
        self,
        rounds: List[Round],
        plugins: List[PluginEntry],
        selected_experiences: Optional[List[Experience]] = None,
    ) -> List[ChatMessageType]:
        experiences = (
            self.experience_generator.format_experience_in_prompt(
                self.prompt_data["experience_instruction"],
                selected_experiences,
            )
            if self.config.use_experience
            else ""
        )

        chat_history = [
            format_chat_message(
                role="system",
                message=f"{self.compose_sys_prompt(context=self.get_env_context())}" f"\n{experiences}",
            ),
        ]

        if self.examples is None:
            self.examples = self.load_examples()
        for i, example in enumerate(self.examples):
            chat_history.extend(
                self.compose_conversation(example.rounds, example.plugins, add_requirements=False),
            )

        summary = None
        if self.config.prompt_compression:
            summary, rounds = self.round_compressor.compress_rounds(
                rounds,
                rounds_formatter=lambda _rounds: str(
                    self.compose_conversation(_rounds, plugins, add_requirements=False),
                ),
                prompt_template=self.compression_template,
            )

        chat_history.extend(
            self.compose_conversation(
                rounds,
                add_requirements=True,
                summary=summary,
                plugins=plugins,
            ),
        )
        return chat_history

    def format_attachment(self, attachment: Attachment):
        if attachment.type == AttachmentType.thought:
            return attachment.content.format(ROLE_NAME=self.role_name)
        else:
            return attachment.content

    def compose_conversation(
        self,
        rounds: List[Round],
        plugins: List[PluginEntry],
        add_requirements: bool = False,
        summary: Optional[str] = None,
    ) -> List[ChatMessageType]:
        cur_round = rounds[-1]
        chat_history: List[ChatMessageType] = []
        ignored_types = [
            AttachmentType.revise_message,
            AttachmentType.verification,
            AttachmentType.code_error,
            AttachmentType.execution_status,
            AttachmentType.execution_result,
        ]

        is_first_post = True
        last_post: Post = None
        for round_index, conversation_round in enumerate(rounds):
            for post_index, post in enumerate(conversation_round.post_list):
                # compose user query
                user_message = ""
                assistant_message = ""
                is_final_post = round_index == len(rounds) - 1 and post_index == len(conversation_round.post_list) - 1
                if is_first_post:
                    user_message = (
                        self.conversation_head_template.format(
                            SUMMARY="None" if summary is None else summary,
                            PLUGINS="None" if len(plugins) == 0 else self.format_plugins(plugins),
                            ROLE_NAME=self.role_name,
                        )
                        + "\n"
                    )
                    is_first_post = False

                if post.send_from == "Planner" and post.send_to == self.alias:
                    # to avoid planner imitating the below handcrafted format,
                    # we merge plan and query message in the code generator here
                    user_query = conversation_round.user_query
                    enrichment = f"The user request is: {user_query}\n\n"

                    supplementary_info_dict = cur_round.read_board()
                    supplementary_info = "\n".join([bulletin for bulletin in supplementary_info_dict.values()])
                    if supplementary_info != "":
                        enrichment += (
                            f"To better understand the user request, here is some additional information:\n"
                            f" {supplementary_info}\n\n"
                        )

                    user_feedback = "None"
                    if last_post is not None and last_post.send_from == self.alias:
                        user_feedback = format_code_feedback(last_post)

                    user_message += self.user_message_head_template.format(
                        FEEDBACK=user_feedback,
                        MESSAGE=f"{enrichment}{post.message}",
                    )
                elif post.send_from == post.send_to == self.alias:
                    # for code correction
                    user_message += self.user_message_head_template.format(
                        FEEDBACK=format_code_feedback(post),
                        MESSAGE=f"{post.get_attachment(AttachmentType.revise_message)[0]}",
                    )

                    assistant_message = self.post_translator.post_to_raw_text(
                        post=post,
                        content_formatter=self.format_attachment,
                        if_format_message=False,
                        if_format_send_to=False,
                        ignored_types=ignored_types,
                    )
                elif post.send_from == self.alias and post.send_to == "Planner":
                    if is_final_post:
                        # This user message is added to make the conversation complete
                        # It is used to make sure the last assistant message has a feedback
                        # This is only used for examples or context summarization
                        user_message += self.user_message_head_template.format(
                            FEEDBACK=format_code_feedback(post),
                            MESSAGE="This is the feedback.",
                        )

                    assistant_message = self.post_translator.post_to_raw_text(
                        post=post,
                        content_formatter=self.format_attachment,
                        if_format_message=False,
                        if_format_send_to=False,
                        ignored_types=ignored_types,
                    )
                else:
                    raise ValueError(f"Invalid post: {post}")
                last_post = post

                if len(assistant_message) > 0:
                    chat_history.append(
                        format_chat_message(
                            role="assistant",
                            message=assistant_message,
                        ),
                    )
                if len(user_message) > 0:
                    # add requirements to the last user message
                    if is_final_post and add_requirements:
                        user_message += "\n" + self.query_requirements_template.format(
                            CODE_GENERATION_REQUIREMENTS=self.compose_verification_requirements(),
                            ROLE_NAME=self.role_name,
                        )
                    chat_history.append(
                        format_chat_message(role="user", message=user_message),
                    )

        return chat_history

    def select_plugins_for_prompt(
        self,
        query: str,
    ) -> List[PluginEntry]:
        selected_plugins = self.plugin_selector.plugin_select(
            query,
            self.config.auto_plugin_selection_topk,
        )
        self.selected_plugin_pool.add_selected_plugins(selected_plugins)
        self.logger.info(f"Selected plugins: {[p.name for p in selected_plugins]}")
        self.logger.info(
            f"Selected plugin pool: {[p.name for p in self.selected_plugin_pool.get_plugins()]}",
        )

        return self.selected_plugin_pool.get_plugins()

    @tracing_decorator
    def reply(
        self,
        memory: Memory,
        post_proxy: Optional[PostEventProxy] = None,
        prompt_log_path: Optional[str] = None,
    ) -> Post:
        assert post_proxy is not None, "Post proxy is not provided."

        # extract all rounds from memory
        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )

        # obtain the query from the last round
        query = rounds[-1].post_list[-1].message

        self.tracing.set_span_attribute("query", query)
        self.tracing.set_span_attribute("enable_auto_plugin_selection", self.config.enable_auto_plugin_selection)
        self.tracing.set_span_attribute("use_experience", self.config.use_experience)

        if self.config.enable_auto_plugin_selection:
            self.plugin_pool = self.select_plugins_for_prompt(query)

        if self.config.use_experience:
            selected_experiences = self.experience_generator.retrieve_experience(query)
        else:
            selected_experiences = None

        prompt = self.compose_prompt(rounds, self.plugin_pool, selected_experiences)
        self.tracing.set_span_attribute("prompt", json.dumps(prompt, indent=2))
        prompt_size = self.tracing.count_tokens(json.dumps(prompt))
        self.tracing.set_span_attribute("prompt_size", prompt_size)
        self.tracing.add_prompt_size(
            size=prompt_size,
            labels={
                "direction": "input",
            },
        )

        def early_stop(_type: AttachmentType, value: str) -> bool:
            if _type in [AttachmentType.reply_content]:
                return True
            else:
                return False

        self.post_translator.raw_text_to_post(
            llm_output=self.llm_api.chat_completion_stream(
                prompt,
                use_smoother=True,
                llm_alias=self.config.llm_alias,
                json_schema=self.response_json_schema,
            ),
            post_proxy=post_proxy,
            early_stop=early_stop,
        )

        post_proxy.update_send_to("Planner")
        generated_code = ""
        reply_type: Optional[str] = None
        for attachment in post_proxy.post.attachment_list:
            if attachment.type == AttachmentType.reply_type:
                reply_type = attachment.content
                break
        for attachment in post_proxy.post.attachment_list:
            if attachment.type == AttachmentType.reply_content:
                if reply_type == "python":
                    generated_code = attachment.content
                    break
                elif reply_type == "text":
                    post_proxy.update_message(attachment.content)
                    break

        if self.config.enable_auto_plugin_selection:
            # filter out plugins that are not used in the generated code
            self.selected_plugin_pool.filter_unused_plugins(code=generated_code)

        if prompt_log_path is not None:
            self.logger.dump_log_file(prompt, prompt_log_path)

        self.tracing.set_span_attribute("code", generated_code)

        return post_proxy.post

    def format_plugins(
        self,
        plugin_list: List[PluginEntry],
    ) -> str:
        if self.config.load_plugin:
            return "\n".join(
                [plugin.format_prompt() for plugin in plugin_list],
            )
        return ""

    def load_examples(
        self,
    ) -> List[Conversation]:
        if self.config.load_example:
            return load_examples(
                folder=self.config.example_base_path,
                role_set={self.alias, "Planner"},
            )
        return []

    def get_plugin_pool(self) -> List[PluginEntry]:
        return self.plugin_pool

    def format_code_revision_message(self) -> str:
        return (
            "The execution of the previous generated code has failed. "
            "If you think you can fix the problem by rewriting the code, "
            "please generate code and run it again.\n"
            "Otherwise, please explain the problem to me."
        )

    def format_output_revision_message(self) -> str:
        return (
            "Your previous message is not following the output format. "
            "You must generate the output as a JSON object following the schema provided:\n"
            f"{self.response_json_schema}\n"
            "Please try again."
        )


def format_code_feedback(post: Post) -> str:
    feedback = ""
    verification_status = ""
    execution_status = ""
    for attachment in post.attachment_list:
        if attachment.type == AttachmentType.verification and attachment.content == "CORRECT":
            feedback += "## Verification\nCode verification has been passed.\n"
            verification_status = "CORRECT"
        elif attachment.type == AttachmentType.verification and attachment.content == "NONE":
            feedback += "## Verification\nNo code verification.\n"
            verification_status = "NONE"
        elif attachment.type == AttachmentType.verification and attachment.content == "INCORRECT":
            feedback += "## Verification\nCode verification detected the following issues:\n"
            verification_status = "INCORRECT"
        elif attachment.type == AttachmentType.code_error and verification_status == "INCORRECT":
            feedback += f"{attachment.content}\n"
        elif attachment.type == AttachmentType.execution_status and attachment.content == "NONE":
            feedback += "## Execution\nNo code execution.\n"
            execution_status = "NONE"
        elif attachment.type == AttachmentType.execution_status and attachment.content == "SUCCESS":
            feedback += "## Execution\nYour code has been executed successfully with the following result:\n"
            execution_status = "SUCCESS"
        elif attachment.type == AttachmentType.execution_status and attachment.content == "FAILURE":
            feedback += "## Execution\nYour code has failed to execute with the following error:\n"
            execution_status = "FAILURE"
        elif attachment.type == AttachmentType.execution_result and execution_status != "NONE":
            feedback += f"{attachment.content}\n"
    return feedback
