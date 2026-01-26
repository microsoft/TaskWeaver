# LLM Module - AGENTS.md

Provider abstraction layer for LLM and embedding services.

## Structure

```
llm/
├── base.py           # Abstract base: CompletionService, EmbeddingService, LLMModuleConfig
├── util.py           # ChatMessageType, format_chat_message, token counting
├── openai.py         # OpenAI/Azure OpenAI provider (largest file ~430 lines)
├── anthropic.py      # Anthropic Claude provider
├── google_genai.py   # Google Generative AI provider
├── ollama.py         # Ollama local LLM provider
├── qwen.py           # Alibaba Qwen provider
├── zhipuai.py        # ZhipuAI provider
├── groq.py           # Groq provider
├── azure_ml.py       # Azure ML endpoints
├── sentence_transformer.py  # Local embedding via sentence_transformers
├── mock.py           # Mock provider for testing
├── placeholder.py    # Placeholder when no LLM configured
└── __init__.py       # LLMApi facade class
```

## Key Patterns

### Provider Registration
New providers must:
1. Subclass `CompletionService` or `EmbeddingService` from `base.py`
2. Implement `chat_completion()` generator or `get_embeddings()` 
3. Register in `__init__.py` LLMApi class's provider mapping

### Config Hierarchy
```python
class MyProviderConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("my_provider")  # creates llm.my_provider.* namespace
        self.custom_setting = self._get_str("custom_setting", "default")
```

### ChatMessageType
```python
ChatMessageType = TypedDict("ChatMessageType", {
    "role": str,        # "system", "user", "assistant"
    "content": str,
    "name": NotRequired[str],
})
```

## Adding a New LLM Provider

1. Create `taskweaver/llm/newprovider.py`
2. Implement config class extending `LLMServiceConfig`
3. Implement service class extending `CompletionService`
4. Add to `_completion_service_map` in `__init__.py`
5. Document in `llm.api_type` config options

## Common Gotchas

- `response_format` options: `"json_object"`, `"text"`, `"json_schema"`
- Streaming: All providers return `Generator[ChatMessageType, None, None]`
- OpenAI file is largest (~430 lines) - handles both OpenAI and Azure OpenAI
