from typing import Any, Generator, List, Optional

from injector import Injector, inject

from taskweaver.llm.base import CompletionService, EmbeddingService, LLMModuleConfig
from taskweaver.llm.openai import OpenAIService

from .util import ChatMessageType, format_chat_message


class LLMApi(object):
    @inject
    def __init__(self, config: LLMModuleConfig, injector: Injector) -> None:
        self.config = config

        if self.config.api_type in ["openai", "azure", "azure_ad"]:
            self.completion_service: CompletionService = injector.get(OpenAIService)
            injector.binder.bind(OpenAIService, to=self.completion_service)
        else:
            raise ValueError(f"API type {self.config.api_type} is not supported")

        if self.config.embedding_api_type in ["openai", "azure", "azure_ad"]:
            self.embedding_service: EmbeddingService = injector.get(OpenAIService)
            injector.binder.bind(OpenAIService, to=self.embedding_service)
        else:
            raise ValueError(
                f"Embedding API type {self.config.embedding_api_type} is not supported",
            )

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
        for msg_chunk in self.completion_service.chat_completion(
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

    def chat_completion_stream(
        self,
        messages: List[ChatMessageType],
        use_backup_engine: bool = False,
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Generator[ChatMessageType, None, None]:
        return self.completion_service.chat_completion(
            messages,
            use_backup_engine,
            stream,
            temperature,
            max_tokens,
            top_p,
            stop,
            **kwargs,
        )

    def get_embedding(self, string: str) -> List[float]:
        return self.embedding_service.get_embeddings([string])[0]

    def get_embedding_list(self, strings: List[str]) -> List[List[float]]:
        return self.embedding_service.get_embeddings(strings)
