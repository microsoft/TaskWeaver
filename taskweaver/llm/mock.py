import hashlib
import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Literal, Optional

import yaml
from injector import inject

from taskweaver.llm.util import ChatMessageRoleType, ChatMessageType, format_chat_message

from .base import CompletionService, EmbeddingService, LLMServiceConfig

MockServiceModeType = Literal[
    "fixed",
    "record_only",
    "playback_only",
    "playback_or_record",
]


class MockApiServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("mock")

        mock_mode = self._get_enum(
            "mode",
            options=["fixed", "record_only", "playback_only", "playback_or_record"],
            default="playback_or_record",
        )

        assert mock_mode in [
            "fixed",
            "record_only",
            "playback_only",
            "playback_or_record",
        ]
        self.mode: MockServiceModeType = mock_mode  # type: ignore

        self.fixed_chat_responses: str = self._get_str(
            "fixed_chat_responses",
            json.dumps(format_chat_message("assistant", "Hello!")),
        )

        self.fixed_embedding_responses: str = self._get_str(
            "fixed_embedding_responses",
            json.dumps([[0.0] * 64]),
        )

        self.cache_path: str = self._get_path(
            "cache_path",
            os.path.join(self.src.app_base_path, "cache", "mock.yaml"),
        )

        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        # split the chat completion response into chunks and delay each chunk by this amount
        # if negative, return the whole response at once
        self.playback_delay: float = self._get_float(
            "playback_delay",
            -1,
        )


@dataclass
class MockCacheEntry:
    value: str
    query: str
    created_at: float
    last_accessed_at: float


class MockCacheStore:
    def __init__(self, path: str):
        self.path = path
        self.completion_store: Dict[str, MockCacheEntry] = {}
        self.embedding_store: Dict[str, MockCacheEntry] = {}

        if os.path.exists(self.path):
            self._init_from_disk()

    def get_completion(self, query: List[ChatMessageType]) -> Optional[ChatMessageType]:
        serialized_query = self._serialize_completion_query(query)
        serialized_value = self._get_from_store(self.completion_store, serialized_query)
        if serialized_value is None:
            return None
        return self._deserialize_completion_response(serialized_value)

    def get_embedding(self, query: str) -> Optional[List[float]]:
        serialized_query = self._serialize_embedding_query(query)
        serialized_value = self._get_from_store(self.embedding_store, serialized_query)
        if serialized_value is None:
            return None
        return self._deserialize_embedding_response(serialized_value)

    def _get_from_store(
        self,
        store: Dict[str, MockCacheEntry],
        query: str,
    ) -> Optional[str]:
        key = self._query_to_key(query)
        if key in store:
            entry = store[key]
            entry.last_accessed_at = time.time()
            return entry.value
        return None

    def set_completion(
        self,
        query: List[ChatMessageType],
        value: ChatMessageType,
    ) -> None:
        serialized_query = self._serialize_completion_query(query)
        serialized_value = self._serialize_completion_response(value)
        self._set_to_store(self.completion_store, serialized_query, serialized_value)

    def set_embedding(self, query: str, value: List[float]) -> None:
        serialized_query = self._serialize_embedding_query(query)
        serialized_value = self._serialize_embedding_response(value)
        self._set_to_store(self.embedding_store, serialized_query, serialized_value)

    def _set_to_store(
        self,
        store: Dict[str, MockCacheEntry],
        query: str,
        value: str,
    ) -> None:
        key = self._query_to_key(query)
        store[key] = MockCacheEntry(
            value=value,
            query=query,
            created_at=time.time(),
            last_accessed_at=time.time(),
        )
        self._save_to_disk()

    def _serialize_completion_query(self, query: List[ChatMessageType]) -> str:
        return "\n".join([self._serialize_completion_response(x) for x in query])

    def _serialize_completion_response(self, response: ChatMessageType) -> str:
        return f"{response['role']}:{response['content']}"

    def _deserialize_completion_response(self, response: str) -> ChatMessageType:
        segment = response.split(":", 1)
        role = segment[0] if len(segment) > 0 else "assistant"
        if role not in ["assistant", "user", "system"]:
            raise ValueError(f"Invalid role {role}")
        content = segment[1] if len(segment) > 1 else ""
        return format_chat_message(role, content)  # type: ignore

    def _serialize_embedding_query(self, query: str) -> str:
        return query

    def _serialize_embedding_response(self, response: List[float]) -> str:
        return ",".join([str(x) for x in response])

    def _deserialize_embedding_response(self, response: str) -> List[float]:
        return [float(x) for x in response.split(",")]

    def _query_to_key(self, query: str) -> str:
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def _init_from_disk(self):
        try:
            cache = yaml.safe_load(open(self.path, "r"))
        except Exception as e:
            print(f"Error loading cache file {self.path}: {e}")
            return

        try:
            completion_store = cache["completion_store"]
            for key, value in completion_store.items():
                try:
                    self.completion_store[key] = MockCacheEntry(**value)
                except Exception as e:
                    print(f"Error loading cache entry {key}: {e}")
        except Exception as e:
            print(f"Error loading completion store: {e}")

        try:
            embedding_store = cache["embedding_store"]
            for key, value in embedding_store.items():
                try:
                    self.embedding_store[key] = MockCacheEntry(**value)
                except Exception as e:
                    print(f"Error loading cache entry {key}: {e}")
        except Exception as e:
            print(f"Error loading embedding store: {e}")

    def _save_to_disk(self):
        # TODO: postpone immediate update and periodically save to disk
        try:
            yaml.safe_dump(
                {
                    "completion_store": {k: v.__dict__ for k, v in self.completion_store.items()},
                    "embedding_store": {k: v.__dict__ for k, v in self.embedding_store.items()},
                },
                open(self.path, "w"),
            )
        except Exception as e:
            print(f"Error saving cache file {self.path}: {e}")


class MockApiService(CompletionService, EmbeddingService):
    @inject
    def __init__(self, config: MockApiServiceConfig):
        self.config = config
        self.base_completion_service: Optional[CompletionService] = None
        self.base_embedding_service: Optional[EmbeddingService] = None
        self.cache = MockCacheStore(self.config.cache_path)

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
        if self.config.mode == "fixed":
            return self._get_from_fixed_completion()

        cached_value = self.cache.get_completion(messages)

        # playback
        if cached_value is None:
            if self.config.mode == "playback_only":
                raise Exception("No cached value found")
        else:
            if self.config.mode != "record_only":
                return self._get_from_playback_completion(cached_value)

        # record
        def get_from_base() -> Generator[ChatMessageType, None, None]:
            if self.base_completion_service is None:
                raise Exception("base_completion_service is not set")
            new_value = format_chat_message("assistant", "")
            for chunk in self.base_completion_service.chat_completion(
                messages,
                use_backup_engine,
                stream,
                temperature,
                max_tokens,
                top_p,
                stop,
                **kwargs,
            ):
                new_value["role"] = chunk["role"]
                new_value["content"] += chunk["content"]
                yield chunk

            self.cache.set_completion(messages, new_value)

        return get_from_base()

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        if self.config.mode == "fixed":
            return [self._get_from_fixed_embedding() for _ in strings]

        cached_values = [self.cache.get_embedding(x) for x in strings]

        cache_missed_values = [strings[i] for i, v in enumerate(cached_values) if v is None]

        if len(cache_missed_values) > 0:
            if self.config.mode == "playback_only":
                raise Exception("Not all cached values found")

        if self.base_embedding_service is None:
            raise Exception("base_embedding_service is not set")

        new_values = self.base_embedding_service.get_embeddings(cache_missed_values)

        cache_missed_values_index = 0
        result_values: List[List[float]] = []
        for i, v in enumerate(cached_values):
            if v is None:
                self.cache.set_embedding(
                    strings[i],
                    new_values[cache_missed_values_index],
                )
                result_values.append(new_values[cache_missed_values_index])
                cache_missed_values_index += 1
            else:
                result_values.append(v)

        return result_values

    def _get_from_fixed_completion(
        self,
    ) -> Generator[ChatMessageType, None, None]:
        fixed_responses: ChatMessageType = json.loads(
            self.config.fixed_chat_responses,
        )
        return self._get_from_playback_completion(fixed_responses)

    def _get_from_fixed_embedding(
        self,
    ) -> List[float]:
        fixed_responses: List[float] = json.loads(self.config.fixed_embedding_responses)
        return fixed_responses

    def _get_from_playback_completion(
        self,
        cached_value: ChatMessageType,
    ) -> Generator[ChatMessageType, None, None]:
        if self.config.playback_delay < 0:
            yield cached_value
            return

        role: ChatMessageRoleType = cached_value["role"]  # type: ignore
        content = cached_value["content"]
        cur_pos = 0
        while cur_pos < len(content):
            chunk_size = random.randint(3, 20)
            next_pos = min(cur_pos + chunk_size, len(content))
            yield format_chat_message(role, content[cur_pos:next_pos])
            cur_pos = next_pos
            time.sleep(self.config.playback_delay)
