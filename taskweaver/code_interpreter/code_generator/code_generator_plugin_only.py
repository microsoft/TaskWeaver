import json
import os
from typing import Any, Dict, List, Optional, Tuple

from injector import inject

from taskweaver.code_interpreter.code_generator.plugin_selection import PluginSelector, SelectedPluginPool
from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm import LLMApi, format_chat_message
from taskweaver.llm.util import ChatMessageType
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post, Round
from taskweaver.memory.attachment import AttachmentType
from taskweaver.memory.plugin import PluginEntry, PluginRegistry
from taskweaver.module.event_emitter import PostEventProxy, SessionEventEmitter
from taskweaver.module.tracing import Tracing, tracing_decorator
from taskweaver.role import PostTranslator, Role
from taskweaver.utils import read_yaml


class CodeGeneratorPluginOnlyConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("code_generator")
        self.role_name = self._get_str("role_name", "ProgramApe")

        self.prompt_file_path = self._get_path(
            "prompt_file_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "code_generator_prompt_plugin_only.yaml",
            ),
        )
        self.prompt_compression = self._get_bool("prompt_compression", False)
        assert self.prompt_compression is False, "Compression is not supported for plugin only mode."

        self.compression_prompt_path = self._get_path(
            "compression_prompt_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "compression_prompt.yaml",
            ),
        )
        self.enable_auto_plugin_selection = self._get_bool("enable_auto_plugin_selection", False)
        self.auto_plugin_selection_topk = self._get_int("auto_plugin_selection_topk", 3)

        self.llm_alias = self._get_str("llm_alias", default="", required=False)


class CodeGeneratorPluginOnly(Role):
    @inject
    def __init__(
        self,
        config: CodeGeneratorPluginOnlyConfig,
        plugin_registry: PluginRegistry,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        llm_api: LLMApi,
    ):
        self.config = config
        self.logger = logger
        self.tracing = tracing
        self.llm_api = llm_api
        self.event_emitter = event_emitter

        self.role_name = self.config.role_name

        self.post_translator = PostTranslator(logger, event_emitter)
        self.prompt_data = read_yaml(self.config.prompt_file_path)
        self.plugin_pool = [p for p in plugin_registry.get_list() if p.plugin_only is True]
        self.instruction_template = self.prompt_data["content"]

        if self.config.enable_auto_plugin_selection:
            self.plugin_selector = PluginSelector(plugin_registry, self.llm_api)
            self.plugin_selector.load_plugin_embeddings()
            logger.info("Plugin embeddings loaded")
            self.selected_plugin_pool = SelectedPluginPool()

    def select_plugins_for_prompt(
        self,
        user_query: str,
    ) -> List[PluginEntry]:
        selected_plugins = self.plugin_selector.plugin_select(
            user_query,
            self.config.auto_plugin_selection_topk,
        )
        self.selected_plugin_pool.add_selected_plugins(selected_plugins)
        self.logger.info(f"Selected plugins: {[p.name for p in selected_plugins]}")
        self.logger.info(f"Selected plugin pool: {[p.name for p in self.selected_plugin_pool.get_plugins()]}")

        return self.selected_plugin_pool.get_plugins()

    @tracing_decorator
    def reply(
        self,
        memory: Memory,
        post_proxy: Optional[PostEventProxy] = None,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: bool = False,
    ) -> Post:
        assert post_proxy is not None, "Post proxy is not provided."

        # extract all rounds from memory
        rounds = memory.get_role_rounds(
            role="CodeInterpreter",
            include_failure_rounds=False,
        )

        user_query = rounds[-1].user_query
        self.tracing.set_span_attribute("user_query", user_query)
        self.tracing.set_span_attribute("enable_auto_plugin_selection", self.config.enable_auto_plugin_selection)
        if self.config.enable_auto_plugin_selection:
            self.plugin_pool = self.select_plugins_for_prompt(user_query)

        # obtain the user query from the last round
        prompt, tools = _compose_prompt(
            system_instructions=self.instruction_template.format(
                ROLE_NAME=self.role_name,
            ),
            rounds=rounds,
            plugin_pool=self.plugin_pool,
        )
        post_proxy.update_send_to("Planner")

        if prompt_log_path is not None:
            self.logger.dump_log_file({"prompt": prompt, "tools": tools}, prompt_log_path)

        prompt_size = self.tracing.count_tokens(json.dumps(prompt)) + self.tracing.count_tokens(json.dumps(tools))
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
            tools=tools,
            tool_choice="auto",
            response_format=None,
            stream=False,
            llm_alias=self.config.llm_alias,
        )

        output_size = self.tracing.count_tokens(llm_response["content"])
        self.tracing.set_span_attribute("output_size", output_size)
        self.tracing.add_prompt_size(
            size=output_size,
            labels={
                "direction": "output",
            },
        )

        if llm_response["role"] == "assistant":
            post_proxy.update_message(llm_response["content"])
            return post_proxy.end()
        elif llm_response["role"] == "function":
            post_proxy.update_attachment(llm_response["content"], AttachmentType.function)
            self.tracing.set_span_attribute("functions", llm_response["content"])

            if self.config.enable_auto_plugin_selection:
                # here the code is in json format, not really code
                self.selected_plugin_pool.filter_unused_plugins(code=llm_response["content"])
            return post_proxy.end()
        else:
            self.tracing.set_span_status(
                "ERROR",
                f"Unexpected response from LLM {llm_response}",
            )
            raise ValueError(f"Unexpected response from LLM: {llm_response}")


def _compose_prompt(
    system_instructions: str,
    rounds: List[Round],
    plugin_pool: List[PluginEntry],
) -> Tuple[List[ChatMessageType], List[Dict[str, Any]]]:
    functions = [plugin.format_function_calling() for plugin in plugin_pool]
    prompt = [format_chat_message(role="system", message=system_instructions)]
    for _round in rounds:
        for post in _round.post_list:
            if post.send_from == "Planner" and post.send_to == "CodeInterpreter":
                prompt.append(format_chat_message(role="user", message=post.message))
            elif post.send_from == "CodeInterpreter" and post.send_to == "Planner":
                prompt.append(format_chat_message(role="assistant", message=post.message))

    return prompt, functions
