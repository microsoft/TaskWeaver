from typing import Any, Generator, List, Optional
from injector import inject
from taskweaver.llm.util import ChatMessageType, format_chat_message
from .base import CompletionService, EmbeddingService, LLMServiceConfig

DEFAULT_STOP_TOKEN: List[str] = ["</s>"]


class ZhipuAIServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("zhipuai")

        # shared common config
        self.api_type = self.llm_module_config.api_type
        shared_api_base = self.llm_module_config.api_base

        self.api_base = self._get_str(
            "api_base",
            shared_api_base if shared_api_base is not None else "https://open.bigmodel.cn/api/paas/v4",
        )
        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key,
        )

        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "glm-4",
        )

        shared_backup_model = self.llm_module_config.backup_model
        self.backup_model = self._get_str(
            "backup_model",
            shared_backup_model if shared_backup_model is not None else self.model,
        )
        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else "embedding-2",
        )
        self.stop_token = self._get_list("stop_token", DEFAULT_STOP_TOKEN)
        self.max_tokens = self._get_int("max_tokens", 4096)

        # ChatGLM are not allow use temperature as 0
        # set do_samples to False to disable sampling, top_p and temperature will be ignored
        # self.do_samples = False
        self.top_p = self._get_float("top_p", 0.1)
        self.temperature = self._get_float("temperature", 0.1)
        self.seed = self._get_int("seed", 2024)


class ZhipuAIService(CompletionService, EmbeddingService):
    zhipuai = None

    @inject
    def __init__(self, config: ZhipuAIServiceConfig):

        if ZhipuAIService.zhipuai is None:
            try:
                import zhipuai
                ZhipuAIService.zhipuai = zhipuai
            except Exception:
                raise Exception(
                    "Package zhipuai>=2.0.0 is required for using ZhipuAI API.",
                )

        self.config = config
        self.client = (
            ZhipuAIService.zhipuai.ZhipuAI(
                base_url=self.config.api_base,
                api_key=self.config.api_key,
            )
        )

    def chat_completion(
            self,
            messages: List[ChatMessageType],
            use_backup_engine: bool = False,
            stream: bool = False,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            top_p: Optional[float] = None,
            stop: Optional[List[str]] = None,
            **kwargs: Any,
    ) -> Generator[ChatMessageType, None, None]:
        engine = self.config.model
        backup_engine = self.config.backup_model

        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        top_p = top_p if top_p is not None else self.config.top_p
        stop = stop if stop is not None else self.config.stop_token
        seed = self.config.seed

        try:
            if use_backup_engine:
                engine = backup_engine

            tools_kwargs = {}
            if "tools" in kwargs and "tool_choice" in kwargs:
                tools_kwargs["tools"] = kwargs["tools"]
                tools_kwargs["tool_choice"] = kwargs["tool_choice"]
            res: Any = self.client.chat.completions.create(
                model=engine,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stop=stop,
                stream=stream,
                seed=seed,
                **tools_kwargs,
            )
            if stream:
                role: Any = None
                for stream_res in res:
                    if not stream_res.choices:
                        continue
                    delta = stream_res.choices[0].delta
                    if delta is None:
                        continue

                    role = delta.role if delta.role is not None else role
                    content = delta.content if delta.content is not None else ""
                    if content is None:
                        continue
                    yield format_chat_message(role, content)
            else:
                zhipuai_response = res.choices[0].message
                if zhipuai_response is None:
                    raise Exception("ZhipuAI API returned an empty response")
                response: ChatMessageType = format_chat_message(
                    role=zhipuai_response.role if zhipuai_response.role is not None else "assistant",
                    message=zhipuai_response.content if zhipuai_response.content is not None else "",
                )
                if zhipuai_response.tool_calls is not None:
                    response["role"] = "function"
                    response["content"] = (
                            "["
                            + ",".join(
                        [t.function.model_dump_json() for t in zhipuai_response.tool_calls],
                    )
                            + "]"
                    )
                yield response
        except Exception as e:
            raise Exception(f"ZhipuAI API call failed with status code: {e}")

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        embeddings = []
        for string in strings:
            embedding_result = self.client.embeddings.create(
                input=string,
                model=self.config.embedding_model,
            ).data
            embeddings.append(embedding_result[0].embedding)
        return embeddings
