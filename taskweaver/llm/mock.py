from typing import Any, Generator, List, Optional

from injector import inject

from taskweaver.llm.util import ChatMessageType

from .base import CompletionService, EmbeddingService, LLMServiceConfig


class MockApiServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("mock")

        self.mode: str = self._get_enum(
            "use",
            options=["fixed", "record_only", "playback_only", "playback_or_record"],
            default="playback_or_record",
        )

        self.fixed_chat_responses: str = self._get_str(
            "fixed_chat_responses",
            "",
        )

        self.fixed_embedding_responses: str = self._get_str(
            "fixed_embedding_responses",
            "",
        )


class MockApiService(CompletionService, EmbeddingService):
    @inject
    def __init__(self, config: MockApiServiceConfig):
        self.config = config
        self.base_completion_service: Optional[CompletionService] = None
        self.base_embedding_service: Optional[EmbeddingService] = None

    def set_base_completion_service(
        self,
        base_completion_service: Optional[CompletionService],
    ):
        self.base_completion_service = base_completion_service

    def set_base_embedding_service(
        self,
        base_embedding_service: Optional[EmbeddingService],
    ):
        self.base_embedding_service = base_embedding_service

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
    ) -> Generator[ChatMessageType, None, None]:
        if self.base_completion_service is None:
            raise Exception("base_completion_service is not set")
        return self.base_completion_service.chat_completion(
            messages=messages,
            use_backup_engine=use_backup_engine,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            **kwargs,
        )

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        if self.base_embedding_service is None:
            raise Exception("base_embedding_service is not set")
        return self.base_embedding_service.get_embeddings(strings)
