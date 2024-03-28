import json
import os
import types
from json import JSONDecodeError
from typing import Dict, Iterable, List, Optional

from injector import inject

from taskweaver.llm import LLMApi
from taskweaver.llm.util import ChatMessageType, format_chat_message
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Conversation, Memory, Post, Round, RoundCompressor
from taskweaver.memory.attachment import AttachmentType
from taskweaver.memory.experience import Experience, ExperienceGenerator
from taskweaver.misc.example import load_examples
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.module.tracing import Tracing, tracing_decorator
from taskweaver.role import PostTranslator, Role
from taskweaver.role.role import RoleConfig
from taskweaver.utils import read_yaml


class PlannerConfig(RoleConfig):
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
        self.prompt_compression = self._get_bool("prompt_compression", False)
        self.compression_prompt_path = self._get_path(
            "compression_prompt_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "compression_prompt.yaml",
            ),
        )

        self.use_experience = self._get_bool("use_experience", False)

        self.llm_alias = self._get_str("llm_alias", default="", required=False)


class Planner(Role):
    conversation_delimiter_message: str = "Let's start the new conversation!"

    @inject
    def __init__(
        self,
        config: PlannerConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        llm_api: LLMApi,
        workers: Dict[str, Role],
        round_compressor: Optional[RoundCompressor],
        post_translator: PostTranslator,
        experience_generator: Optional[ExperienceGenerator] = None,
    ):
        super().__init__(config, logger, tracing, event_emitter)
        self.alias = "Planner"

        self.llm_api = llm_api

        self.workers = workers
        self.recipient_alias_set = set([alias for alias, _ in self.workers.items()])

        self.planner_post_translator = post_translator

        self.prompt_data = read_yaml(self.config.prompt_file_path)

        if self.config.use_example:
            self.examples = self.get_examples()

        self.instruction_template = self.prompt_data["instruction_template"]

        self.response_schema = self.prompt_data["planner_response_schema"]

        self.instruction = self.compose_sys_prompt()

        self.ask_self_cnt = 0
        self.max_self_ask_num = 3

        self.round_compressor = round_compressor
        self.compression_prompt_template = read_yaml(self.config.compression_prompt_path)["content"]

        if self.config.use_experience:
            self.experience_generator = experience_generator
            self.experience_generator.refresh()
            self.experience_generator.load_experience()
            self.logger.info(
                "Experience loaded successfully, "
                "there are {} experiences".format(len(self.experience_generator.experience_list)),
            )

        self.logger.info("Planner initialized successfully")

    def compose_sys_prompt(self):
        worker_description = ""
        for alias, role in self.workers.items():
            worker_description += f"{alias}:\n{role.get_intro()}\n\n"

        instruction = self.instruction_template.format(
            planner_response_schema=self.response_schema,
            worker_intro=worker_description,
        )

        return instruction

    def compose_conversation_for_prompt(
        self,
        conv_rounds: List[Round],
        summary: Optional[str] = None,
    ) -> List[ChatMessageType]:
        conversation: List[ChatMessageType] = []

        for rnd_idx, chat_round in enumerate(conv_rounds):
            conv_init_message = None
            if rnd_idx == 0:
                conv_init_message = Planner.conversation_delimiter_message
                if summary is not None:
                    self.logger.debug(f"Summary: {summary}")
                    summary_message = (
                        f"\nThe context summary of the Planner's previous rounds" f" can refer to:\n{summary}\n\n"
                    )
                    conv_init_message += "\n" + summary_message

            for post in chat_round.post_list:
                if post.send_from == self.alias:
                    if post.send_to == "User" or post.send_to in self.recipient_alias_set:
                        planner_message = self.planner_post_translator.post_to_raw_text(
                            post=post,
                        )
                        conversation.append(
                            format_chat_message(
                                role="assistant",
                                message=planner_message,
                            ),
                        )
                    elif (
                        post.send_to == self.alias
                    ):  # self correction for planner response, e.g., format error/field check error
                        conversation.append(
                            format_chat_message(
                                role="assistant",
                                message=post.get_attachment(
                                    type=AttachmentType.invalid_response,
                                )[0],
                            ),
                        )  # append the invalid response to chat history
                        conversation.append(
                            format_chat_message(
                                role="user",
                                message="User: " + post.get_attachment(type=AttachmentType.revise_message)[0],
                            ),
                        )  # append the self correction instruction message to chat history

                else:
                    if conv_init_message is not None:
                        message = post.send_from + ": " + conv_init_message + "\n" + post.message
                        conversation.append(
                            format_chat_message(role="user", message=message),
                        )
                        conv_init_message = None
                    else:
                        conversation.append(
                            format_chat_message(
                                role="user",
                                message=post.send_from + ": " + post.message,
                            ),
                        )

        return conversation

    def compose_prompt(
        self,
        rounds: List[Round],
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
        chat_history = [format_chat_message(role="system", message=f"{self.instruction}\n{experiences}")]

        if self.config.use_example and len(self.examples) != 0:
            for conv_example in self.examples:
                conv_example_in_prompt = self.compose_conversation_for_prompt(
                    conv_example.rounds,
                )
                chat_history += conv_example_in_prompt

        summary = None
        if self.config.prompt_compression and self.round_compressor is not None:
            summary, rounds = self.round_compressor.compress_rounds(
                rounds,
                rounds_formatter=lambda _rounds: str(
                    self.compose_conversation_for_prompt(_rounds),
                ),
                prompt_template=self.compression_prompt_template,
            )

        chat_history.extend(
            self.compose_conversation_for_prompt(
                rounds,
                summary=summary,
            ),
        )

        return chat_history

    @tracing_decorator
    def reply(
        self,
        memory: Memory,
        prompt_log_path: Optional[str] = None,
    ) -> Post:
        rounds = memory.get_role_rounds(role=self.alias)
        assert len(rounds) != 0, "No chat rounds found for planner"

        user_query = rounds[-1].user_query
        self.tracing.set_span_attribute("user_query", user_query)
        self.tracing.set_span_attribute("use_experience", self.config.use_experience)

        if self.config.use_experience:
            selected_experiences = self.experience_generator.retrieve_experience(user_query)
        else:
            selected_experiences = None

        post_proxy = self.event_emitter.create_post_proxy(self.alias)

        post_proxy.update_status("composing prompt")
        chat_history = self.compose_prompt(rounds, selected_experiences)

        def check_post_validity(post: Post):
            missing_elements = []
            validation_errors = []
            if post.send_to is None or post.send_to == "Unknown":
                missing_elements.append("send_to")
            if post.send_to == self.alias:
                validation_errors.append("The `send_to` field must not be `Planner` itself")
            if post.message is None or post.message.strip() == "":
                missing_elements.append("message")

            attachment_types = [attachment.type for attachment in post.attachment_list]
            if AttachmentType.init_plan not in attachment_types:
                missing_elements.append("init_plan")
            if AttachmentType.plan not in attachment_types:
                missing_elements.append("plan")
            if AttachmentType.current_plan_step not in attachment_types:
                missing_elements.append("current_plan_step")

            if len(missing_elements) > 0:
                validation_errors.append(f"Missing elements: {', '.join(missing_elements)} in the `response` element")
            assert len(validation_errors) == 0, ";".join(validation_errors)

        post_proxy.update_status("calling LLM endpoint")

        llm_stream = self.llm_api.chat_completion_stream(
            chat_history,
            use_smoother=True,
        )

        llm_output: List[str] = []
        try:

            def stream_filter(s: Iterable[ChatMessageType]):
                is_first_chunk = True
                try:
                    for c in s:
                        if is_first_chunk:
                            post_proxy.update_status("receiving LLM response")
                            is_first_chunk = False
                        llm_output.append(c["content"])
                        yield c
                finally:
                    if isinstance(s, types.GeneratorType):
                        try:
                            s.close()
                        except GeneratorExit:
                            pass

            self.tracing.set_span_attribute("prompt", json.dumps(chat_history, indent=2))
            prompt_size = self.tracing.count_tokens(json.dumps(chat_history))
            self.tracing.set_span_attribute("prompt_size", prompt_size)
            self.tracing.add_prompt_size(
                size=prompt_size,
                labels={
                    "direction": "input",
                },
            )

            self.planner_post_translator.raw_text_to_post(
                post_proxy=post_proxy,
                llm_output=stream_filter(llm_stream),
                validation_func=check_post_validity,
            )

        except (JSONDecodeError, AssertionError) as e:
            self.logger.error(f"Failed to parse LLM output due to {str(e)}")
            self.tracing.set_span_status("ERROR", str(e))
            self.tracing.set_span_exception(e)
            post_proxy.error(f"Failed to parse LLM output due to {str(e)}")
            post_proxy.update_attachment(
                "".join(llm_output),
                AttachmentType.invalid_response,
            )
            post_proxy.update_attachment(
                f"Your JSON output has errors. {str(e)}."
                # "The output format should follow the below format:"
                # f"{self.prompt_data['planner_response_schema']}"
                "You must add or missing elements at in one go and send the response again.",
                AttachmentType.revise_message,
            )
            if self.ask_self_cnt > self.max_self_ask_num:  # if ask self too many times, return error message
                self.ask_self_cnt = 0
                post_proxy.end(f"Planner failed to generate response because {str(e)}")
                raise Exception(f"Planner failed to generate response because {str(e)}")
            else:
                post_proxy.update_send_to(self.alias)
                self.ask_self_cnt += 1
        if prompt_log_path is not None:
            self.logger.dump_log_file(chat_history, prompt_log_path)

        reply_post = post_proxy.end()
        self.tracing.set_span_attribute("out.from", reply_post.send_from)
        self.tracing.set_span_attribute("out.to", reply_post.send_to)
        self.tracing.set_span_attribute("out.message", reply_post.message)
        self.tracing.set_span_attribute("out.attachments", str(reply_post.attachment_list))

        return reply_post

    def get_examples(self) -> List[Conversation]:
        example_conv_list = load_examples(
            self.config.example_base_path,
            role_set=set(self.recipient_alias_set) | {self.alias, "User"},
        )
        return example_conv_list
