from typing import Any, Generator, List, Optional

from injector import inject

from taskweaver.llm.base import CompletionService, EmbeddingService, LLMServiceConfig
from taskweaver.llm.util import ChatMessageType


class QWenServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("qwen")

        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key,
        )

        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "qwen-max-1201",
        )

        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else self.model,
        )


class QWenService(CompletionService, EmbeddingService):
    dashscope = None

    @inject
    def __init__(self, config: QWenServiceConfig):
        self.config = config

        if QWenService.dashscope is None:
            try:
                import dashscope

                QWenService.dashscope = dashscope
            except Exception:
                raise Exception(
                    "Package dashscope is required for using QWen API. ",
                )
        QWenService.dashscope.api_key = self.config.api_key

    def chat_completion(
        self,
        messages: List[ChatMessageType],
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Generator[ChatMessageType, None, None]:
        response = QWenService.dashscope.Generation.call(
            model=self.config.model,
            messages=messages,
            result_format="message",  # set the result to be "message" format.
            max_tokens=max_tokens,
            top_p=top_p,
            temperature=temperature,
            stop=stop,
            stream=True,
            incremental_output=True,
        )

        from http import HTTPStatus

        for msg_chunk in response:
            if msg_chunk.status_code == HTTPStatus.OK:
                yield msg_chunk.output.choices[0]["message"]

            else:
                raise Exception(
                    f"QWen API call failed with status code {msg_chunk.status_code} and error message {msg_chunk.code}",
                )

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        resp = QWenService.dashscope.TextEmbedding.call(
            model=self.config.embedding_model,
            input=strings,
        )
        embeddings = []

        from http import HTTPStatus

        if resp.status_code == HTTPStatus.OK:
            for emb in resp["output"]["embeddings"]:
                embeddings.append(emb["embedding"])
            return embeddings
        else:
            raise Exception(
                f"QWen API call failed with status code {resp.status_code} and error message {resp.error}",
            )
