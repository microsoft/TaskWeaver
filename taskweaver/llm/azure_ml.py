from typing import Any, Generator, List, Optional

import requests
from injector import inject

from taskweaver.llm.base import CompletionService, LLMServiceConfig
from taskweaver.llm.util import ChatMessageType, format_chat_message


class AzureMLServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("azure_ml")

        shared_api_base = self.llm_module_config.api_base
        self.api_base = self._get_str(
            "api_base",
            shared_api_base,
        )

        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key,
        )

        self.chat_mode = self._get_bool(
            "chat_mode",
            True,
        )


class AzureMLService(CompletionService):
    @inject
    def __init__(self, config: AzureMLServiceConfig):
        self.config = config

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
        endpoint = self.config.api_base
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]

        if endpoint.endswith(".ml.azure.com"):
            endpoint += "/score"

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        params = {
            # "temperature": 0.0,
            "max_new_tokens": 100,
            # "top_p": 0.0,
            "do_sample": True,
        }
        if self.config.chat_mode:
            prompt = messages
        else:
            prompt = ""
            for msg in messages:
                prompt += f"{msg['role']}: {msg['content']}\n\n"
            prompt = [prompt]

        data = {
            "input_data": {
                "input_string": prompt,
                "parameters": params,
            },
        }
        with requests.Session() as session:
            with session.post(
                endpoint,
                headers=headers,
                json=data,
            ) as response:
                if response.status_code != 200:
                    raise Exception(
                        f"status code {response.status_code}: {response.text}",
                    )
                response_json = response.json()
                print(response_json)
                if "output" not in response_json:
                    raise Exception(f"output is not in response: {response_json}")
                outputs = response_json["output"]
                generation = outputs[0]

        # close connection before yielding
        yield format_chat_message("assistant", generation)
