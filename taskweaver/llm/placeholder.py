from typing import Any, List, Optional

from taskweaver.llm.base import CompletionService, EmbeddingService
from taskweaver.llm.util import ChatMessageType


class PlaceholderCompletionService(CompletionService):
    def __init__(
        self,
        error_message: str = "PlaceholderCompletionService is not implemented yet.",
    ):
        self.error_message = error_message

    def chat_completion(
        self,
        messages: List[ChatMessageType],
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ...:
        raise NotImplementedError(self.error_message)


class PlaceholderEmbeddingService(EmbeddingService):
    def __init__(
        self,
        error_message: str = "PlaceholderEmbeddingService is not implemented yet.",
    ):
        self.error_message = error_message

    def get_embeddings(self, strings: List[str]) -> ...:
        raise NotImplementedError(self.error_message)
