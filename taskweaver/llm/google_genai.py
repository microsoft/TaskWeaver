from typing import Any, Generator, List, Optional

from injector import inject

from taskweaver.llm.base import CompletionService, EmbeddingService, LLMServiceConfig
from taskweaver.llm.util import ChatMessageType, format_chat_message


class GoogleGenAIServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("google_genai")

        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key if shared_api_key is not None else "",
        )
        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "gemini-pro",
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
            options=["json_object", "text"],
            default=shared_response_format if shared_response_format is not None else "text",
        )
        self.temperature = self._get_float("temperature", 0.9)
        self.max_output_tokens = self._get_int("max_output_tokens", 1000)
        self.top_k = self._get_int("top_k", 1)
        self.top_p = self._get_float("top_p", 0)


class GoogleGenAIService(CompletionService, EmbeddingService):
    @inject
    def __init__(self, config: GoogleGenAIServiceConfig):
        self.config = config
        genai = self.import_genai_module()
        genai.configure(api_key=self.config.api_key)
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
        ]

        self.model = genai.GenerativeModel(
            model_name=self.config.model,
            generation_config={
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_output_tokens": self.config.max_output_tokens,
            },
            safety_settings=safety_settings,
        )

    def import_genai_module(self):
        try:
            import google.generativeai as genai
        except Exception:
            raise Exception(
                "Package google-generativeai is required for using Google Gemini API. "
                "Please install it manually by running: `pip install google-generativeai`",
            )
        return genai

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
        return self._chat_completion(
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
        from google.generativeai.types import GenerateContentResponse

        genai_messages = []
        prev_role = ""
        for msg in messages:
            if msg["role"] == "system":
                genai_messages.append({"role": "user", "parts": [msg["content"]]})
                genai_messages.append(
                    {
                        "role": "model",
                        "parts": ["I understand your requirements, and I will assist you in the conversations."],
                    },
                )
                prev_role = "model"
            elif msg["role"] == "user":
                if prev_role == "user":
                    # a placeholder to create alternating user and model messages
                    genai_messages.append({"role": "model", "parts": ["  "]})
                genai_messages.append({"role": "user", "parts": [msg["content"]]})
                prev_role = "user"
            elif msg["role"] == "assistant":
                genai_messages.append({"role": "model", "parts": [msg["content"]]})
                prev_role = "model"
            else:
                raise Exception(f"Invalid role: {msg['role']}")

        if stream is False:
            response: GenerateContentResponse = self.model.generate_content(genai_messages, stream=False)
            yield format_chat_message("assistant", response.text)
        else:
            response: GenerateContentResponse = self.model.generate_content(genai_messages, stream=True)
            for chunk_obj in response:
                yield format_chat_message("assistant", chunk_obj.text)

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        genai = self.import_genai_module()
        embedding_results = genai.embed_content(
            model=self.config.embedding_model,
            content=strings,
            task_type="semantic_similarity",
        )
        return embedding_results["embedding"]
