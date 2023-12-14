from http import HTTPStatus
from typing import Any, Generator, List, Optional

from injector import inject

from taskweaver.llm.base import CompletionService, LLMServiceConfig
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


class QWenService(CompletionService):
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
        QWenService.dashscope.api_key = self.config.api_key

        response = QWenService.dashscope.Generation.call(
            model=self.config.model,
            messages=messages,
            result_format="message",  # set the result to be "message" format.
            max_tokens=max_tokens,
            top_p=top_p,
            temperature=temperature,
            stop=stop,
            stream=False,
        )

        if response.status_code == HTTPStatus.OK:
            yield response.output.choices[0]["message"]

        else:
            raise Exception(
                f"QWen API call failed with status code {response.status_code} and error message {response.error}",
            )
