import os
from json import JSONDecodeError
from typing import List, Optional

from injector import inject

from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm import LLMApi
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Conversation, Memory, Post, Round
from taskweaver.memory.plugin import PluginRegistry
from taskweaver.misc.example import load_examples
from taskweaver.role import PostTranslator, Role
from taskweaver.utils import read_yaml
from taskweaver.utils.llm_api import ChatMessageType, format_chat_message


class PlannerConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("planner")
        app_dir = self.src.app_base_path
        self.use_example = self._get_bool("use_example", True)
        self.prompt_file_path = self._get_path(
            "prompt_file_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "planner_prompt.yaml",
            ),
        )
        self.example_base_path = self._get_path(
            "example_base_path",
            os.path.join(
                app_dir,
                "planner_examples",
            ),
        )


class Planner(Role):
    conversation_delimiter_message: str = "Let's start the new conversation!"
    ROLE_NAME: str = "Planner"

    @inject
    def __init__(
        self,
        config: PlannerConfig,
        logger: TelemetryLogger,
        llm_api: LLMApi,
        plugin_registry: PluginRegistry,
    ):
        self.config = config
        self.logger = logger
        self.llm_api = llm_api
        self.plugin_registry = plugin_registry

        self.planner_post_translator = PostTranslator(logger)

        self.prompt_data = read_yaml(self.config.prompt_file_path)

        if self.config.use_example:
            self.examples = self.get_examples()
        if len(self.plugin_registry.get_list()) == 0:
            self.logger.warning("No plugin is loaded for Planner.")
            self.plugin_description = "No plugin functions loaded."
        else:
            self.plugin_description = "\t" + "\n\t".join(
                [f"- {plugin.name}: " + f"{plugin.spec.description}" for plugin in self.plugin_registry.get_list()],
            )
        self.instruction_template = self.prompt_data["instruction_template"]
        self.code_interpreter_introduction = self.prompt_data["code_interpreter_introduction"].format(
            plugin_description=self.plugin_description,
        )
        self.response_schema = self.prompt_data["planner_response_schema"]

        self.instruction = self.instruction_template.format(
            planner_response_schema=self.response_schema,
            CI_introduction=self.code_interpreter_introduction,
        )
        self.ask_self_cnt = 0
        self.max_self_ask_num = 3

        self.logger.info("Planner initialized successfully")

    def compose_example_for_prompt(self) -> List[ChatMessageType]:
        assert len(self.examples) != 0, "No examples found."
        example_chat_history: List[ChatMessageType] = []

        for _, conversation in enumerate(self.examples):
            for rnd_idx, chat_round in enumerate(conversation.rounds):
                if rnd_idx == 0:
                    example_chat_history.append(
                        format_chat_message(
                            role="user",
                            message=Planner.conversation_delimiter_message,
                        ),
                    )
                for post in chat_round.post_list:
                    if post.send_from == "Planner":
                        message = self.planner_post_translator.post_to_raw_text(
                            post=post,
                        )  # add planner tags here
                        example_chat_history.append(
                            format_chat_message(role="assistant", message=message),
                        )
                    else:
                        message = post.send_from + ": " + post.message
                        example_chat_history.append(
                            format_chat_message(role="user", message=message),
                        )

        example_chat_history.append(
            format_chat_message(role="user", message=Planner.conversation_delimiter_message),
        )

        return example_chat_history

    def compose_prompt(self, rounds: List[Round]) -> List[ChatMessageType]:
        chat_history = [format_chat_message(role="system", message=self.instruction)]

        if self.config.use_example and len(self.examples) != 0:
            example_chat_history = self.compose_example_for_prompt()
            chat_history += example_chat_history

        for round in rounds:
            for post in round.post_list:
                if post.send_from == "User":
                    chat_history.append(
                        format_chat_message(
                            role="user",
                            message="User: " + post.message,
                        ),
                    )
                elif post.send_from == "CodeInterpreter":
                    chat_history.append(
                        format_chat_message(
                            role="user",
                            message="CodeInterpreter: " + post.message,
                        ),
                    )
                elif post.send_from == "Planner":
                    if post.send_to == "User" or post.send_to == "CodeInterpreter":
                        planner_message = self.planner_post_translator.post_to_raw_text(
                            post=post,
                        )  # add planner tags here
                        chat_history.append(
                            format_chat_message(
                                role="assistant",
                                message=planner_message,
                            ),
                        )
                    elif post.send_to == "Planner":
                        chat_history.append(
                            format_chat_message(
                                role="user",
                                message="Planner: " + post.message,
                            ),
                        )

        return chat_history

    def reply(
        self,
        memory: Memory,
        event_handler,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: bool = False,
    ) -> Post:
        rounds = memory.get_role_rounds(role="Planner")
        assert len(rounds) != 0, "No chat rounds found for planner"
        chat_history = self.compose_prompt(rounds)

        def check_post_validity(post: Post):
            assert post.send_to is not None, "Post send_to field is None"
            assert post.message is not None, "Post message field is None"
            assert post.attachment_list[0].type == "init_plan", "Post attachment type is not init_plan"
            assert post.attachment_list[1].type == "plan", "Post attachment type is not plan"
            assert post.attachment_list[2].type == "current_plan_step", "Post attachment type is not current_plan_step"

        llm_output = self.llm_api.chat_completion(chat_history, use_backup_engine=use_back_up_engine)["content"]
        try:
            response_post = self.planner_post_translator.raw_text_to_post(
                llm_output=llm_output,
                send_from="Planner",
                event_handler=event_handler,
                validation_func=check_post_validity,
            )
            if response_post.send_to == "User":
                event_handler("final_reply_message", response_post.message)
        except (JSONDecodeError, AssertionError) as e:
            self.logger.error(f"Failed to parse LLM output due to {str(e)}")
            response_post = Post.create(
                message=f"The output of Planner is invalid."
                f"The output format should follow the below format:"
                f"{self.prompt_data['planner_response_schema']}"
                "Please try to regenerate the Planner output.",
                send_to="Planner",
                send_from="Planner",
            )
            self.ask_self_cnt += 1
            if self.ask_self_cnt > self.max_self_ask_num:  # if ask self too many times, return error message
                self.ask_self_cnt = 0
                raise Exception(f"Planner failed to generate response because {str(e)}")
        if prompt_log_path is not None:
            self.logger.dump_log_file(chat_history, prompt_log_path)

        return response_post

    def get_examples(self) -> List[Conversation]:
        example_conv_list = load_examples(self.config.example_base_path)
        return example_conv_list
