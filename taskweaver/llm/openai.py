import os
from typing import Any, Generator, List, Optional

import openai
from injector import inject
from openai import AzureOpenAI, OpenAI

from taskweaver.llm.util import ChatMessageType, format_chat_message

from .base import CompletionService, EmbeddingService, LLMServiceConfig

DEFAULT_STOP_TOKEN: List[str] = ["<EOS>"]


class OpenAIServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("openai")

        # shared common config
        self.api_type = self.llm_module_config.api_type
        assert self.api_type in ["openai", "azure", "azure_ad"], "Invalid API type"

        shared_api_base = self.llm_module_config.api_base
        self.api_base = self._get_str(
            "api_base",
            shared_api_base if shared_api_base is not None else "https://api.openai.com/v1",
        )
        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key if shared_api_base is not None else "" if self.api_type == "azure_ad" else None,
        )

        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "gpt-4",
        )
        shared_backup_model = self.llm_module_config.backup_model
        self.backup_model = self._get_str(
            "backup_model",
            shared_backup_model if shared_backup_model is not None else self.model,
        )
        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else "text-embedding-ada-002",
        )

        self.response_format = self.llm_module_config.response_format

        # openai specific config
        self.api_version = self._get_str("api_version", "2023-12-01-preview")
        self.api_auth_type = self._get_enum(
            "api_auth_type",
            ["openai", "azure", "azure_ad"],
            "openai",
        )
        is_azure_ad_login = self.api_type == "azure_ad"
        self.aad_auth_mode = self._get_enum(
            "aad_auth_mode",
            ["device_login", "aad_app"],
            None if is_azure_ad_login else "device_login",
        )

        is_app_login = is_azure_ad_login and self.aad_auth_mode == "aad_app"
        self.aad_tenant_id = self._get_str(
            "aad_tenant_id",
            None if is_app_login else "common",
        )
        self.aad_api_resource = self._get_str(
            "aad_api_resource",
            None if is_app_login else "https://cognitiveservices.azure.com/",
        )
        self.aad_api_scope = self._get_str(
            "aad_api_scope",
            None if is_app_login else ".default",
        )
        self.aad_client_id = self._get_str(
            "aad_client_id",
            None if is_app_login else "",
        )
        self.aad_client_secret = self._get_str(
            "aad_client_secret",
            None if is_app_login else "",
        )
        self.aad_use_token_cache = self._get_bool("aad_use_token_cache", True)
        self.aad_token_cache_path = self._get_str(
            "aad_token_cache_path",
            "cache/token_cache.bin",
        )
        self.aad_token_cache_full_path = os.path.join(
            self.src.app_base_path,
            self.aad_token_cache_path,
        )

        self.stop_token = self._get_list("stop_token", DEFAULT_STOP_TOKEN)
        self.temperature = self._get_float("temperature", 0)
        self.max_tokens = self._get_int("max_tokens", 1024)
        self.top_p = self._get_float("top_p", 0)
        self.frequency_penalty = self._get_float("frequency_penalty", 0)
        self.presence_penalty = self._get_float("presence_penalty", 0)
        self.seed = self._get_int("seed", 123456)


class OpenAIService(CompletionService, EmbeddingService):
    @inject
    def __init__(self, config: OpenAIServiceConfig):
        self.config = config

        api_type = self.config.api_type

        assert api_type in ["openai", "azure", "azure_ad"], "Invalid API type"

        self.client: OpenAI = (
            OpenAI(
                base_url=self.config.api_base,
                api_key=self.config.api_key,
            )
            if api_type == "openai"
            else AzureOpenAI(
                api_version=self.config.api_version,
                azure_endpoint=self.config.api_base,
                api_key=(self.config.api_key if api_type == "azure" else self._get_aad_token()),
            )
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
            res: Any = self.client.chat.completions.create(
                model=engine,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                stop=stop,
                stream=stream,
                seed=seed,
                response_format=(
                    {"type": "json_object"} if self.config.response_format == "json_object" else None  # type: ignore
                ),
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
                oai_response = res.choices[0].message
                if oai_response is None:
                    raise Exception("OpenAI API returned an empty response")
                response: ChatMessageType = format_chat_message(
                    role=oai_response.role if oai_response.role is not None else "assistant",
                    message=oai_response.content if oai_response.content is not None else "",
                )
                yield response

        except openai.APITimeoutError as e:
            # Handle timeout error, e.g. retry or log
            raise Exception(f"OpenAI API request timed out: {e}")
        except openai.APIConnectionError as e:
            # Handle connection error, e.g. check network or log
            raise Exception(f"OpenAI API request failed to connect: {e}")
        except openai.BadRequestError as e:
            # Handle invalid request error, e.g. validate parameters or log
            raise Exception(f"OpenAI API request was invalid: {e}")
        except openai.AuthenticationError as e:
            # Handle authentication error, e.g. check credentials or log
            raise Exception(f"OpenAI API request was not authorized: {e}")
        except openai.PermissionDeniedError as e:
            # Handle permission error, e.g. check scope or log
            raise Exception(f"OpenAI API request was not permitted: {e}")
        except openai.RateLimitError as e:
            # Handle rate limit error, e.g. wait or log
            raise Exception(f"OpenAI API request exceeded rate limit: {e}")
        except openai.APIError as e:
            # Handle API error, e.g. retry or log
            raise Exception(f"OpenAI API returned an API Error: {e}")

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        embedding_results = self.client.embeddings.create(
            input=strings,
            model=self.config.embedding_model,
        ).data
        return [r.embedding for r in embedding_results]

    def _get_aad_token(self) -> str:
        try:
            import msal  # type: ignore
        except ImportError:
            raise Exception(
                "AAD authentication requires msal module to be installed, please run `pip install msal`",
            )

        config = self.config

        cache: Any = msal.SerializableTokenCache()

        token_cache_file: Optional[str] = None
        if config.aad_use_token_cache:
            token_cache_file = config.aad_token_cache_full_path
            if not os.path.exists(token_cache_file):
                os.makedirs(os.path.dirname(token_cache_file), exist_ok=True)
            if os.path.exists(token_cache_file):
                with open(token_cache_file, "r") as cache_file:
                    cache.deserialize(cache_file.read())  # type: ignore

        def save_cache():
            if token_cache_file is not None and config.aad_use_token_cache:
                with open(token_cache_file, "w") as cache_file:
                    cache_file.write(cache.serialize())

        authority = "https://login.microsoftonline.com/" + config.aad_tenant_id
        api_resource = config.aad_api_resource
        api_scope = config.aad_api_scope
        auth_mode = config.aad_auth_mode

        if auth_mode == "aad_app":
            app: Any = msal.ConfidentialClientApplication(
                client_id=config.aad_client_id,
                client_credential=config.aad_client_secret,
                authority=authority,
                token_cache=cache,
            )
            result: Any = app.acquire_token_for_client(
                scopes=[
                    api_resource + "/" + api_scope,
                ],
            )
            if "access_token" in result:
                return result["access_token"]

            raise Exception(
                "Authentication failed for acquiring AAD token for application login: " + str(result),
            )

        scopes = [
            api_resource + "/" + api_scope,
        ]
        app: Any = msal.PublicClientApplication(
            "feb7b661-cac7-44a8-8dc1-163b63c23df2",  # default id in Azure Identity module
            authority=authority,
            token_cache=cache,
        )
        result = None
        try:
            account = app.get_accounts()[0]
            result = app.acquire_token_silent(scopes, account=account)
            if result is not None and "access_token" in result:
                save_cache()
                return result["access_token"]
            result = None
        except Exception:
            pass

        try:
            account = cache.find(cache.CredentialType.ACCOUNT)[0]
            refresh_token = cache.find(
                cache.CredentialType.REFRESH_TOKEN,
                query={
                    "home_account_id": account["home_account_id"],
                },
            )[0]
            result = app.acquire_token_by_refresh_token(
                refresh_token["secret"],
                scopes=scopes,
            )
            if result is not None and "access_token" in result:
                save_cache()
                return result["access_token"]
            result = None
        except Exception:
            pass

        flow = app.initiate_device_flow(scopes=scopes)
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow=flow)
        if result is not None and "access_token" in result:
            save_cache()
            return result["access_token"]

        error_details = "\n".join(
            [
                result.get("error"),
                result.get("error_description"),
            ],
        )
        raise Exception(
            f"Authentication failed for acquiring AAD token for AAD auth: {error_details}",
        )
