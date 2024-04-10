from typing import Any, Generator, List, Optional

from injector import inject

from taskweaver.llm.base import CompletionService, EmbeddingService, LLMServiceConfig
from taskweaver.llm.util import ChatMessageType, format_chat_message


class GroqServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("groq")

        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key,
        )

        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "groq",
        )

        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else self.model,
        )


class GroqService(CompletionService, EmbeddingService):
    client = None

    @inject
    def __init__(self, config: GroqServiceConfig):
        self.config = config

        if GroqService.client is None:
            try:
                from groq import Groq

                GroqService.client = Groq(
                    api_key=self.config.api_key,
                )
            except Exception:
                raise Exception(
                    "Package groq is required for using Groq API. ",
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
    ) -> Generator[ChatMessageType, None, None]:
        response = GroqService.client.chat.completions.create(
            messages=messages,
            model=self.config.model,
        )

        yield format_chat_message("assistant", response.choices[0].message.content)

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        pass
