from typing import Any, Generator, List, Optional, Type

from injector import Injector, inject

from taskweaver.llm.azure_ml import AzureMLService
from taskweaver.llm.base import CompletionService, EmbeddingService, LLMModuleConfig
from taskweaver.llm.google_genai import GoogleGenAIService
from taskweaver.llm.mock import MockApiService
from taskweaver.llm.ollama import OllamaService
from taskweaver.llm.openai import OpenAIService
from taskweaver.llm.placeholder import PlaceholderEmbeddingService
from taskweaver.llm.sentence_transformer import SentenceTransformerService

from .qwen import QWenService
from .util import ChatMessageType, format_chat_message


class LLMApi(object):
    @inject
    def __init__(self, config: LLMModuleConfig, injector: Injector) -> None:
        self.config = config
        self.injector = injector

        if self.config.api_type in ["openai", "azure", "azure_ad"]:
            self._set_completion_service(OpenAIService)
        elif self.config.api_type == "ollama":
            self._set_completion_service(OllamaService)
        elif self.config.api_type == "azure_ml":
            self._set_completion_service(AzureMLService)
        elif self.config.api_type == "google_genai":
            self._set_completion_service(GoogleGenAIService)
        elif self.config.api_type == "qwen":
            self._set_completion_service(QWenService)
        else:
            raise ValueError(f"API type {self.config.api_type} is not supported")

        if self.config.embedding_api_type in ["openai", "azure", "azure_ad"]:
            self._set_embedding_service(OpenAIService)
        elif self.config.embedding_api_type == "ollama":
            self._set_embedding_service(OllamaService)
        elif self.config.embedding_api_type == "google_genai":
            self._set_embedding_service(GoogleGenAIService)
        elif self.config.embedding_api_type == "sentence_transformers":
            self._set_embedding_service(SentenceTransformerService)
        elif self.config.embedding_api_type == "qwen":
            self._set_embedding_service(QWenService)
        elif self.config.embedding_api_type == "azure_ml":
            self.embedding_service = PlaceholderEmbeddingService(
                "Azure ML does not support embeddings yet. Please configure a different embedding API.",
            )
        elif self.config.embedding_api_type == "qwen":
            self.embedding_service = PlaceholderEmbeddingService(
                "QWen does not support embeddings yet. Please configure a different embedding API.",
            )
        else:
            raise ValueError(
                f"Embedding API type {self.config.embedding_api_type} is not supported",
            )

        if self.config.use_mock:
            # add mock proxy layer to the completion and embedding services
            base_completion_service = self.completion_service
            base_embedding_service = self.embedding_service
            mock = self.injector.get(MockApiService)
            mock.set_base_completion_service(base_completion_service)
            mock.set_base_embedding_service(base_embedding_service)
            self._set_completion_service(MockApiService)
            self._set_embedding_service(MockApiService)

    def _set_completion_service(self, svc: Type[CompletionService]) -> None:
        self.completion_service: CompletionService = self.injector.get(svc)
        self.injector.binder.bind(svc, to=self.completion_service)

    def _set_embedding_service(self, svc: Type[EmbeddingService]) -> None:
        self.embedding_service: EmbeddingService = self.injector.get(svc)
        self.injector.binder.bind(svc, to=self.embedding_service)

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
            if "name" in msg_chunk:
                msg["name"] = msg_chunk["name"]
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
