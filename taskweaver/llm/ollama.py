import json
from contextlib import contextmanager
from typing import Any, Generator, List, Optional

import requests
from injector import inject

from taskweaver.llm.base import CompletionService, EmbeddingService, LLMServiceConfig
from taskweaver.llm.util import ChatMessageType, format_chat_message


class OllamaServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("ollama")

        shared_api_base = self.llm_module_config.api_base
        self.api_base = self._get_str(
            "api_base",
            shared_api_base if shared_api_base is not None else "http://localhost:11434",
        )

        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "llama2",
        )
        shared_backup_model = self.llm_module_config.backup_model
        self.backup_model = self._get_str(
            "backup_model",
            shared_backup_model if shared_backup_model is not None else self.model,
        )
        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else self.model,
        )

        shared_response_format = self.llm_module_config.response_format
        self.response_format = self._get_enum(
            "response_format",
            options=["json", "json_object", "text"],
            default=shared_response_format if shared_response_format is not None else "text",
        )
        if self.response_format == "json_object":
            self.response_format = "json"


class OllamaService(CompletionService, EmbeddingService):
    @inject
    def __init__(self, config: OllamaServiceConfig):
        self.config = config

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
        try:
            return self._chat_completion(
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stop=stop,
                **kwargs,
            )
        except Exception:
            return self._completion(
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stop=stop,
                **kwargs,
            )

    def _chat_completion(
        self,
        messages: List[ChatMessageType],
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Generator[ChatMessageType, None, None]:
        api_endpoint = "/api/chat"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream,
        }

        if self.config.response_format == "json":
            payload["format"] = "json"

        if stream is False:
            with self._request_api(api_endpoint, payload) as resp:
                if resp.status_code != 200:
                    raise Exception(
                        f"Failed to get completion with error code {resp.status_code}: {resp.text}",
                    )
                response: str = resp.json()["response"]
            yield format_chat_message("assistant", response)

        with self._request_api(api_endpoint, payload, stream=True) as resp:
            if resp.status_code != 200:
                raise Exception(
                    f"Failed to get completion with error code {resp.status_code}: {resp.text}",
                )
            for chunk_obj in self._stream_process(resp):
                if "error" in chunk_obj:
                    raise Exception(
                        f"Failed to get completion with error: {chunk_obj['error']}",
                    )
                if "message" in chunk_obj:
                    message = chunk_obj["message"]
                    yield format_chat_message("assistant", message["content"])

    def _completion(
        self,
        messages: List[ChatMessageType],
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Generator[ChatMessageType, None, None]:
        api_endpoint = "/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": "",
            "stream": stream,
        }

        if self.config.response_format == "json":
            payload["format"] = "json"

        for message in messages:
            content: str = message["content"]
            if message["role"] == "system":
                payload["system"] = content
            else:
                payload["prompt"] = f"{payload['prompt']}\n{content}"

        if stream is False:
            with self._request_api(api_endpoint, payload) as resp:
                if resp.status_code != 200:
                    raise Exception(
                        f"Failed to get completion with error code {resp.status_code}: {resp.text}",
                    )
                response: str = resp.json()["response"]
            yield format_chat_message("assistant", response)

        with self._request_api(api_endpoint, payload, stream=True) as resp:
            if resp.status_code != 200:
                raise Exception(
                    f"Failed to get completion with error code {resp.status_code}: {resp.text}",
                )
            for chunk_obj in self._stream_process(resp):
                if "error" in chunk_obj:
                    raise Exception(
                        f"Failed to get completion with error: {chunk_obj['error']}",
                    )
                if "response" in chunk_obj:
                    response = chunk_obj["response"]
                    yield format_chat_message("assistant", response)

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        return [self._get_embedding(string) for string in strings]

    def _stream_process(self, resp: requests.Response) -> Generator[Any, None, None]:
        for line in resp.iter_lines():
            line_str = line.decode("utf-8")
            if line_str and line_str.strip() != "":
                yield json.loads(line_str)

    def _get_embedding(self, string: str) -> List[float]:
        payload = {"model": self.config.embedding_model, "prompt": string}

        with self._request_api("/api/embeddings", payload) as resp:
            if resp.status_code != 200:
                raise Exception(
                    f"Failed to get embedding with error code {resp.status_code}: {resp.text}",
                )
            return resp.json()["embedding"]

    @contextmanager
    def _request_api(self, api_path: str, payload: Any, stream: bool = False):
        url = f"{self.config.api_base}{api_path}"
        with requests.Session() as session:
            with session.post(url, json=payload, stream=stream) as resp:
                yield resp
