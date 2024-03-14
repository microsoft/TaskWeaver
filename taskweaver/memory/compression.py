import json
from typing import Callable, List, Set, Tuple

from injector import inject

from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm import LLMApi
from taskweaver.llm.util import format_chat_message
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Round
from taskweaver.module.tracing import Tracing, tracing_decorator


class RoundCompressorConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("round_compressor")
        self.rounds_to_compress = self._get_int("rounds_to_compress", 2)
        self.rounds_to_retain = self._get_int("rounds_to_retain", 3)

        assert self.rounds_to_compress > 0, "rounds_to_compress must be greater than 0"
        assert self.rounds_to_retain > 0, "rounds_to_retain must be greater than 0"

        self.llm_alias = self._get_str("llm_alias", default="", required=False)


class RoundCompressor:
    @inject
    def __init__(
        self,
        llm_api: LLMApi,
        config: RoundCompressorConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
    ):
        self.config = config
        self.processed_rounds: Set[str] = set()
        self.rounds_to_compress = self.config.rounds_to_compress
        self.rounds_to_retain = self.config.rounds_to_retain
        self.previous_summary: str = "None"
        self.llm_api = llm_api
        self.logger = logger
        self.tracing = tracing

    @tracing_decorator
    def compress_rounds(
        self,
        rounds: List[Round],
        rounds_formatter: Callable,
        prompt_template: str = "{PREVIOUS_SUMMARY}, please compress the following rounds",
    ) -> Tuple[str, List[Round]]:
        remaining_rounds = len(rounds)
        for _round in rounds:
            if _round.id in self.processed_rounds:
                remaining_rounds -= 1
                continue
            break

        # not enough rounds to compress
        if remaining_rounds < (self.rounds_to_compress + self.rounds_to_retain):
            return self.previous_summary, rounds[-remaining_rounds:]

        chat_summary = self._summarize(
            rounds[-remaining_rounds : -self.rounds_to_retain],
            rounds_formatter,
            prompt_template=prompt_template,
        )

        self.tracing.set_span_attribute("chat_summary", chat_summary)

        if len(chat_summary) > 0:  # if the compression is successful
            self.previous_summary = chat_summary
            return chat_summary, rounds[-self.rounds_to_retain :]
        else:
            return self.previous_summary, rounds[-remaining_rounds:]

    @tracing_decorator
    def _summarize(
        self,
        rounds: List[Round],
        rounds_formatter: Callable,
        prompt_template: str = "{PREVIOUS_SUMMARY}, please compress the following rounds",
    ) -> str:
        assert "{PREVIOUS_SUMMARY}" in prompt_template, "Prompt template must contain {PREVIOUS_SUMMARY}"
        try:
            chat_history_str = rounds_formatter(rounds)
            system_instruction = prompt_template.format(
                PREVIOUS_SUMMARY=self.previous_summary,
            )
            prompt = [
                format_chat_message("system", system_instruction),
                format_chat_message("user", chat_history_str),
            ]

            prompt_size = self.tracing.count_tokens(json.dumps(prompt))
            self.tracing.add_prompt_size(
                size=prompt_size,
                labels={
                    "direction": "input",
                },
            )
            self.tracing.set_span_attribute("prompt", json.dumps(prompt, indent=2))
            self.tracing.set_span_attribute("prompt_size", prompt_size)

            new_summary = self.llm_api.chat_completion(prompt, llm_alias=self.config.llm_alias)["content"]

            self.tracing.set_span_attribute("summary", new_summary)
            output_size = self.tracing.count_tokens(new_summary)
            self.tracing.set_span_attribute("output_size", output_size)
            self.tracing.add_prompt_size(
                size=output_size,
                labels={
                    "direction": "output",
                },
            )

            self.processed_rounds.update([_round.id for _round in rounds])
            return new_summary
        except Exception as e:
            self.logger.warning(f"Failed to compress rounds: {e}")
            return ""
