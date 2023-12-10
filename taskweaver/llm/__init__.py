from typing import Any, Generator, List, Optional

from injector import Injector, inject

from taskweaver.llm.base import LLMModuleConfig
from taskweaver.llm.openai import OpenAIService

from .util import ChatMessageType, format_chat_message


class LLMApi(object):
    @inject
    def __init__(self, config: LLMModuleConfig, injector: Injector) -> None:
        self.config = config

        if self.config.api_type in ["openai", "azure", "azure_ad"]:
            self.client = injector.get(OpenAIService)
            injector.binder.bind(OpenAIService, to=self.client)
            assert self.client == injector.get(OpenAIService), "OpenAIService is not a singleton"
        else:
            raise ValueError(f"API type {self.config.api_type} is not supported")

    def chat_completion(
        self,
        messages: List[ChatMessageType],
        use_backup_engine: bool = False,
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatMessageType:
        msg: ChatMessageType = format_chat_message("assistant", "")
        for msg_chunk in self.client.chat_completion(
            messages,
            use_backup_engine,
            stream,
            temperature,
            max_tokens,
            top_p,
            stop,
            **kwargs,
        ):
            msg["role"] = msg_chunk["role"]
            msg["content"] += msg_chunk["content"]
        return msg
