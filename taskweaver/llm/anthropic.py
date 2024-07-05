import os
from typing import Any, Generator, List, Optional

from injector import inject

from taskweaver.llm.util import ChatMessageType, format_chat_message

from .base import CompletionService, EmbeddingService, LLMServiceConfig

DEFAULT_STOP_TOKEN: List[str] = ["<EOS>"]

class AnthropicServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            os.environ.get("ANTHROPIC_API_KEY", shared_api_key)
        )
        self.model = self._get_str("model", "claude-3-opus-20240229")
        self.max_tokens = self._get_int("max_tokens", 1024)
        self.temperature = self._get_float("temperature", 0)
        self.top_p = self._get_float("top_p", 1)
        self.stop_token = self._get_list("stop_token", DEFAULT_STOP_TOKEN)

class AnthropicService(CompletionService):
    client = None

    @inject
    def __init__(self, config: AnthropicServiceConfig):
        self.config = config
        if AnthropicService.client is None:
            try:
                from anthropic import Anthropic
                AnthropicService.client = Anthropic(api_key=self.config.api_key)
            except Exception :
                raise Exception(
                    "Package anthropic is required for using Anthropic API. Run 'pip install anthropic' to install.",
                )

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
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        top_p = top_p if top_p is not None else self.config.top_p
        stop = stop if stop is not None else self.config.stop_token

        try:
            # Extract system message if present
            system_message = None
            anthropic_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

            # Prepare kwargs for Anthropic API
            anthropic_kwargs = {
                "model": self.config.model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stop_sequences": stop,
            }
            
            # Add system message if present
            if system_message:
                anthropic_kwargs["system"] = system_message

            if stream:
                with self.client.messages.stream(**anthropic_kwargs) as stream:
                    for response in stream:
                        if response.type == "content_block_delta":
                            yield format_chat_message("assistant", response.delta.text)
            else:
                response = self.client.messages.create(**anthropic_kwargs)
                yield format_chat_message("assistant", response.content[0].text)

        except Exception as e:
            raise Exception(f"Anthropic API request failed: {str(e)}")

# Note: Anthropic doesn't provide a native embedding service.
# If you need embeddings, you might want to use a different service or library for that functionality.

