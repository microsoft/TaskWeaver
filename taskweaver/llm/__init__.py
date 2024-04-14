import types
from typing import Any, Callable, Generator, List, Optional, Type

from injector import Injector, Module, inject, provider

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.llm.azure_ml import AzureMLService
from taskweaver.llm.base import (
    CompletionService,
    EmbeddingService,
    ExtLLMModuleConfig,
    LLMModuleConfig,
    LLMServiceConfig,
)
from taskweaver.llm.google_genai import GoogleGenAIService
from taskweaver.llm.groq import GroqService, GroqServiceConfig
from taskweaver.llm.mock import MockApiService
from taskweaver.llm.ollama import OllamaService
from taskweaver.llm.openai import OpenAIService
from taskweaver.llm.placeholder import PlaceholderEmbeddingService
from taskweaver.llm.qwen import QWenService, QWenServiceConfig
from taskweaver.llm.sentence_transformer import SentenceTransformerService
from taskweaver.llm.util import ChatMessageType, format_chat_message
from taskweaver.llm.zhipuai import ZhipuAIService

llm_completion_config_map = {
    "openai": OpenAIService,
    "azure": OpenAIService,
    "azure_ad": OpenAIService,
    "azure_ml": AzureMLService,
    "ollama": OllamaService,
    "google_genai": GoogleGenAIService,
    "qwen": QWenService,
    "zhipuai": ZhipuAIService,
    "groq": GroqService,
}

# TODO
llm_embedding_config_map = {}


class LLMApi(object):
    @inject
    def __init__(
        self,
        config: LLMModuleConfig,
        injector: Injector,
        ext_llms_config: Optional[ExtLLMModuleConfig] = None,
    ):
        self.config = config
        self.injector = injector
        self.ext_llm_injector = Injector([])
        self.ext_llms = {}  # extra llm models

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
        elif self.config.api_type == "zhipuai":
            self._set_completion_service(ZhipuAIService)
        elif self.config.api_type == "groq":
            self._set_completion_service(GroqService)
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
        elif self.config.embedding_api_type == "zhipuai":
            self._set_embedding_service(ZhipuAIService)
        elif self.config.embedding_api_type == "azure_ml":
            self.embedding_service = PlaceholderEmbeddingService(
                "Azure ML does not support embeddings yet. Please configure a different embedding API.",
            )
        elif self.config.embedding_api_type == "groq":
            self.embedding_service = PlaceholderEmbeddingService(
                "Groq does not support embeddings yet. Please configure a different embedding API.",
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

        if ext_llms_config is not None:
            for key, config in ext_llms_config.ext_llm_config_mapping.items():
                api_type = config.get_str("llm.api_type")
                assert api_type in llm_completion_config_map, f"API type {api_type}  is not supported"
                llm_completion_service = self._get_completion_service(config)
                self.ext_llms[key] = llm_completion_service

    def _set_completion_service(self, svc: Type[CompletionService]) -> None:
        self.completion_service: CompletionService = self.injector.get(svc)
        self.injector.binder.bind(svc, to=self.completion_service)

    def _set_embedding_service(self, svc: Type[EmbeddingService]) -> None:
        self.embedding_service: EmbeddingService = self.injector.get(svc)
        self.injector.binder.bind(svc, to=self.embedding_service)

    def _get_completion_service(self, config) -> CompletionService:
        self.ext_llm_injector.binder.bind(AppConfigSource, to=config)
        api_type = config.get_str("llm.api_type")
        return self.ext_llm_injector.get(llm_completion_config_map[api_type])

    def _get_embedding_service(self, svc: Type[EmbeddingService]) -> EmbeddingService:
        # TODO
        pass

    def chat_completion(
        self,
        messages: List[ChatMessageType],
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        llm_alias: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatMessageType:
        msg: ChatMessageType = format_chat_message("assistant", "")
        if llm_alias is not None and llm_alias != "":
            if llm_alias in self.ext_llms:
                completion_service = self.ext_llms[llm_alias]
            else:
                raise ValueError(
                    f"Cannot import extra LLM model {llm_alias}, ",
                )
        else:
            completion_service = self.completion_service
        for msg_chunk in completion_service.chat_completion(
            messages,
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
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        use_smoother: bool = True,
        llm_alias: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[ChatMessageType, None, None]:
        def get_generator() -> Generator[ChatMessageType, None, None]:
            if llm_alias is not None and llm_alias != "":
                if llm_alias in self.ext_llms:
                    completion_service = self.ext_llms[llm_alias]
                else:
                    raise ValueError(
                        f"Cannot import extra LLM model {llm_alias}, ",
                    )
            else:
                completion_service = self.completion_service
            return completion_service.chat_completion(
                messages,
                stream,
                temperature,
                max_tokens,
                top_p,
                stop,
                **kwargs,
            )

        if use_smoother:
            return self._stream_smoother(get_generator)
        return get_generator()

    def _stream_smoother(
        self,
        stream_init: Callable[[], Generator[ChatMessageType, None, None]],
    ) -> Generator[ChatMessageType, None, None]:
        import random
        import threading
        import time

        min_sleep_interval = 0.1
        min_chunk_size = 2
        min_update_interval = 1 / 30  # 30Hz

        recv_start = time.time()
        buffer_message: Optional[ChatMessageType] = None
        buffer_content: str = ""
        finished = False
        llm_thread_interrupt: bool = False
        llm_source_failed: bool = False
        llm_source_error: Optional[Exception] = None

        update_lock = threading.Lock()
        update_cond = threading.Condition()
        cur_base_speed: float = 10.0

        def non_zero(num: float) -> float:
            return num + 1e-6

        def speed_normalize(speed: float):
            return min(max(speed, 5), 600)

        def base_stream_puller():
            nonlocal buffer_message, buffer_content, finished, cur_base_speed
            nonlocal llm_source_failed, llm_source_error, llm_thread_interrupt
            stream: Optional[Generator[ChatMessageType, None, None]] = None
            try:
                stream = stream_init()

                for msg in stream:
                    if llm_thread_interrupt:
                        # early interrupt from drainer side
                        break

                    if msg["content"] == "":
                        continue

                    with update_lock:
                        buffer_message = msg
                        buffer_content += msg["content"]
                        cur_time = time.time()

                        new_speed = min(
                            2e3,
                            len(buffer_content) / non_zero(cur_time - recv_start),
                        )
                        weight = min(1.0, len(buffer_content) / 80)
                        cur_base_speed = new_speed * weight + cur_base_speed * (1 - weight)

                    with update_cond:
                        update_cond.notify()
            except Exception as e:
                llm_source_failed = True
                llm_source_error = e
            finally:
                if stream is not None and isinstance(stream, types.GeneratorType):
                    try:
                        stream.close()
                    except GeneratorExit:
                        pass
                try:
                    with update_lock:
                        finished = True
                    with update_cond:
                        update_cond.notify()
                except Exception:
                    pass

        thread = threading.Thread(target=base_stream_puller)
        thread.start()

        sent_content: str = ""
        sent_start: float = time.time()
        next_update_time = time.time()
        cur_update_speed = cur_base_speed

        try:
            while True:
                if llm_source_failed:
                    if llm_source_error is not None:
                        # raise the error from execution thread again
                        raise llm_source_error  # type:ignore
                    else:
                        raise Exception("calling LLM failed")
                if finished and len(buffer_content) - len(sent_content) < min_chunk_size * 5:
                    if buffer_message is not None and len(sent_content) < len(
                        buffer_content,
                    ):
                        new_pack = buffer_content[len(sent_content) :]
                        sent_content += new_pack
                        yield format_chat_message(
                            role=buffer_message["role"],
                            message=new_pack,
                            name=buffer_message["name"] if "name" in buffer_message else None,
                        )
                    break

                if time.time() < next_update_time:
                    with update_cond:
                        update_cond.wait(
                            min(min_sleep_interval, next_update_time - time.time()),
                        )
                    continue

                with update_lock:
                    cur_buf_message = buffer_message
                    total_len = len(buffer_content)
                    sent_len = len(sent_content)
                    rem_len = total_len - sent_len

                if cur_buf_message is None or len(buffer_content) - len(sent_content) < min_chunk_size:
                    # wait for more buffer
                    with update_cond:
                        update_cond.wait(min_sleep_interval)
                    continue

                if sent_start == 0.0:
                    # first chunk time
                    sent_start = time.time()

                cur_base_speed_norm = speed_normalize(cur_base_speed)
                cur_actual_speed_norm = speed_normalize(
                    sent_len
                    / non_zero(
                        time.time() - (sent_start if not finished else recv_start),
                    ),
                )
                target_speed = cur_base_speed_norm + (cur_base_speed_norm - cur_actual_speed_norm) * 0.25
                cur_update_speed = speed_normalize(
                    0.5 * cur_update_speed + target_speed * 0.5,
                )

                if cur_update_speed > min_chunk_size / non_zero(min_update_interval):
                    chunk_time_target = min_update_interval
                    new_pack_size_target = chunk_time_target * cur_update_speed
                else:
                    new_pack_size_target = min_chunk_size
                    chunk_time_target = new_pack_size_target / non_zero(
                        cur_update_speed,
                    )

                rand_min = max(
                    min(rem_len, min_chunk_size),
                    int(0.8 * new_pack_size_target),
                )
                rand_max = min(rem_len, int(1.2 * new_pack_size_target))
                new_pack_size = random.randint(rand_min, rand_max) if rand_max - rand_min > 1 else rand_min

                chunk_time = chunk_time_target / non_zero(new_pack_size_target) * new_pack_size

                new_pack = buffer_content[sent_len : (sent_len + new_pack_size)]
                sent_content += new_pack

                yield format_chat_message(
                    role=cur_buf_message["role"],
                    message=new_pack,
                    name=cur_buf_message["name"] if "name" in cur_buf_message else None,
                )

                next_update_time = time.time() + chunk_time
                with update_cond:
                    update_cond.wait(min(min_sleep_interval, chunk_time))
        finally:
            # when the exception is from drainer side (such as client side generator close)
            # mark the label to interrupt the execution thread
            llm_thread_interrupt = True

            if thread.is_alive():
                try:
                    # try to join the thread if it has not finished
                    thread.join(timeout=1)
                except Exception:
                    pass

    def get_embedding(self, string: str) -> List[float]:
        return self.embedding_service.get_embeddings([string])[0]

    def get_embedding_list(self, strings: List[str]) -> List[List[float]]:
        return self.embedding_service.get_embeddings(strings)
