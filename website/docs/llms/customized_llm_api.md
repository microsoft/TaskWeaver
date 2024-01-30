# Customized LLM API

We welcome developers to use your customized LLM API in TaskWeaver. 
In this tutorial, we will show you how to contribute your LLM API to TaskWeaver.

1. Create a new Python script `<your_LLM_name>.py` in the `taskweaver/llm` folder. 
2. Import the `CompletionService`, `LLMServiceConfig` and `EmbeddingService` from `taskweaver.llm.base` and other necessary libraries.
```python
from injector import inject
from taskweaver.llm.base import CompletionService, EmbeddingService, LLMServiceConfig
from taskweaver.llm.util import ChatMessageType
...
```
3. Create a new class `YourLLMServiceConfig` that inherits from `LLMServiceConfig` and implements the `_configure` method.
In this method, you can set the name, API key, model name, backup model name, and embedding model name of your LLM.
```python
class YourLLMServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("your_llm_name")

        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key,
        )

        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "your_llm_model_name",
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
```
4. Create a new class `YourLLMService` that inherits from `CompletionService` and `EmbeddingService` and implements the `chat_completion` and `get_embeddings` methods.
```python
class YourLLMService(CompletionService, EmbeddingService):
    @inject
    def __init__(self, config: YourLLMServiceConfig):
        self.config = config
        pass

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
        pass
    
    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        pass
```
Note:
- We set stream mode by default in `chat_completion`.
- You need to use `self.config` to get the configuration variables of your LLM API (e.g., api key/model name) in `YourLLMService` class.
- The `get_embeddings` method is optional. 
- If you need to import other libraries for your LLM API, please import them in `__init__` function of `YourLLMService` class.
You can refer to [QWen dashscope library import](https://github.com/microsoft/TaskWeaver/blob/main/taskweaver/llm/qwen.py) for an example.


5. Register your LLM service in `taskweaver/llm/__init__.py` by adding your LLM service to the `LLMApi` `__init__` function .
```python 
......
from .your_llm_name import YourLLMService # import your LLM service here

class LLMApi(object):
    @inject
    def __init__(self, config: LLMModuleConfig, injector: Injector) -> None:
        self.config = config
        self.injector = injector

        if self.config.api_type in ["openai", "azure", "azure_ad"]:
            self._set_completion_service(OpenAIService)
            
        ......
        
        elif self.config.api_type == "your_llm_name":
            self._set_completion_service(YourLLMService) # register your LLM service here
        else:
            raise ValueError(f"API type {self.config.api_type} is not supported")

        if self.config.embedding_api_type in ["openai", "azure", "azure_ad"]:
            self._set_embedding_service(OpenAIService)
            
        ......
        
        elif self.config.embedding_api_type == "azure_ml":
            self.embedding_service = PlaceholderEmbeddingService(
                "Azure ML does not support embeddings yet. Please configure a different embedding API.",
            )
        # register your embedding service here, if do not have embedding service, please use `PlaceholderEmbeddingService` referring to the above line
        elif self.config.embedding_api_type == "your_llm_name": 
            self._set_embedding_service(YourLLMService)
        else:
            raise ValueError(
                f"Embedding API type {self.config.embedding_api_type} is not supported",
            )
```

5. Configurate `taskweaver_config.json` file in the `project` dir based on your implemented LLM API.
6. Run the following command to test your LLM API. If the LLM API is successfully set up, you will see the response from your LLM API.
```bash
cd ./scripts
python llm_api_test.py
```
You also can specify the project dir and query to be sent to your LLM API by using the following command:
```bash
python llm_api_test.py --project <your_project_path> --query "hello, what can you do?" 
```







