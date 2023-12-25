import abc
from typing import Any, Generator, List, Optional

from injector import inject

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.config.module_config import ModuleConfig
from taskweaver.llm.util import ChatMessageType


class LLMModuleConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("llm")
        self.api_type = self._get_str(
            "api_type",
            "openai",
        )
        self.embedding_api_type = self._get_str(
            "embedding_api_type",
            "sentence_transformer",
        )
        self.api_base: Optional[str] = self._get_str("api_base", None, required=False)
        self.api_key: Optional[str] = self._get_str(
            "api_key",
            None,
            required=False,
        )

        self.model: Optional[str] = self._get_str("model", None, required=False)
        self.backup_model: Optional[str] = self._get_str(
            "backup_model",
            None,
            required=False,
        )
        self.embedding_model: Optional[str] = self._get_str(
            "embedding_model",
            None,
            required=False,
        )

        self.response_format: Optional[str] = self._get_enum(
            "response_format",
            options=["json_object", "text"],
            default="json_object",
        )

        self.use_mock: bool = self._get_bool("use_mock", False)


class LLMServiceConfig(ModuleConfig):
    @inject
    def __init__(
        self,
        src: AppConfigSource,
        llm_module_config: LLMModuleConfig,
    ) -> None:
        self.llm_module_config = llm_module_config
        super().__init__(src)

    def _set_name(self, name: str) -> None:
        self.name = f"llm.{name}"


class CompletionService(abc.ABC):
    @abc.abstractmethod
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
        """
        Chat completion API

        :param messages: list of messages

        :param use_backup_engine: whether to use back up engine
        :param stream: whether to stream the response

        :param temperature: temperature
        :param max_tokens: maximum number of tokens
        :param top_p: top p

        :param kwargs: other model specific keyword arguments

        :return: generator of messages
        """

        raise NotImplementedError


class EmbeddingService(abc.ABC):
    @abc.abstractmethod
    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        """
        Embedding API

        :param strings: list of strings to be embedded
        :return: list of embeddings
        """
        raise NotImplementedError
