import os
from typing import Any, Callable, Generator, Iterator, List, Literal, Optional, TypeVar, Union, overload

import openai
from injector import inject
from openai import AzureOpenAI, OpenAI

from taskweaver.config.module_config import ModuleConfig
from taskweaver.utils.llm_api import ChatMessageType, format_chat_message

DEFAULT_STOP_TOKEN: List[str] = ["<EOS>"]

# TODO: retry logic

_FuncType = TypeVar("_FuncType", bound=Callable[..., Any])


def _cassette_mode_check(f: _FuncType) -> _FuncType:
    try:
        from vcr import VCR, record_mode
    except ImportError:
        # no decoration when no cassette available
        return f

    AZURE_OPEN_AI_HOST = "azure-open-ai-host"

    def normalize_openai_uri(original_uri: str) -> str:
        import re

        uri = original_uri

        host = uri.split("//")[1].split("/")[0]
        if host.lower().endswith("openai.azure.com") or host.lower().endswith(
            "openai.azure-api.net",
        ):
            host = AZURE_OPEN_AI_HOST
        if not host == AZURE_OPEN_AI_HOST:
            return original_uri

        deployment: str = "Unknown"
        if "deployments" in uri:
            deployment_match = re.match(r".*?/deployments/([^/]+)/.*", uri)
            if deployment_match is not None:
                deployment = deployment_match.group(1)

        if re.match(r"gpt[\-_]?3[\-_\.]?5[\-_]?turbo.*", deployment, re.IGNORECASE) is not None:
            deployment = "gpt-35-turbo"
        elif re.match(r"gpt[\-_]?4[\-_\.]?32k.*", deployment, re.IGNORECASE) is not None:
            deployment = "gpt-4-32k"
        elif re.match(r"gpt[\-_]?4.*", deployment, re.IGNORECASE) is not None:
            deployment = "gpt-4"

        # check whether chat/completions or completions
        endpoint = "chat/completions" if "chat/completions" in uri else "completions"

        return f"https://{host}/openai/deployments/{deployment}/{endpoint}"

    def response_scrubber(response):
        response["headers"] = {
            k: v
            for k, v in response["headers"].items()
            if k.lower() in ["content-type", "transfer-encoding", "content-length"]
        }
        return response

    def request_scrubber(request):
        request.headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() in ["content-type", "accept", "accept-encoding", "content-length"]
        }
        request.uri = normalize_openai_uri(request.uri)
        return request

    def should_record_host(request):
        return AZURE_OPEN_AI_HOST in request.uri or "openai.azure.com" in request.uri

    def before_record_request(request):
        request = request_scrubber(request)
        if should_record_host(request):
            return request
        else:
            return None

    def openai_uri_matcher(r1, r2):
        return normalize_openai_uri(r1.uri) == normalize_openai_uri(r2.uri)

    def openai_body_matcher(r1, r2):
        def parse_body(r):
            import json

            try:
                body = r.body.decode("utf-8")
                assert len(body) > 0
                body = json.loads(body)
                return True, body
            except Exception:
                return False, r.body

        return parse_body(r1) == parse_body(r2)

    def decorator_path_generator(func):
        import inspect
        from pathlib import Path

        # func = openai_uri_matcher
        path = Path(inspect.getabsfile(func))
        path = path.parent / (path.stem + func.__name__ + ".yaml")
        return str(path)

    def init_vcr(cassette_mode: record_mode.RecordMode):
        vcr = VCR(
            before_record_request=before_record_request,
            before_record_response=response_scrubber,
            record_mode=cassette_mode,
            path_transformer=VCR.ensure_suffix(".yaml"),
            func_path_generator=decorator_path_generator,
            match_on=["openai_uri", "method", "openai_body", "query"],
        )
        vcr.register_matcher("openai_uri", openai_uri_matcher)
        vcr.register_matcher("openai_body", openai_body_matcher)
        return vcr

    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        has_cassette_mode = False
        try:
            import os

            cassette_mode = os.environ.get(
                "__TASK_WEAVER_LLM_CASSETTE_MODE__",
                None,
            )
            cassette_path = os.environ.get(
                "__TASK_WEAVER_LLM_CASSETTE_PATH__",
                None,
            )

            if cassette_mode is not None or cassette_path is not None:
                has_cassette_mode = True

            if cassette_mode is None or cassette_path is None:
                raise Exception("cassette_mode or cassette_path is not set")

            # convert string to enum
            cassette_mode = record_mode.RecordMode(cassette_mode)

            vcr = init_vcr(cassette_mode)
            with vcr.use_cassette(cassette_path):
                print(
                    f"Using cassette: {cassette_path} for LLM API call in mode {cassette_mode}",
                )
                return f(*args, **kwargs)
        except Exception as e:
            if has_cassette_mode:
                print(f"Error: {e}")
            return f(*args, **kwargs)

    return wrapper


class LLMModuleConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("llm")
        self.api_type = self._get_enum(
            "api_type",
            ["openai", "azure", "azure_ad"],
            "openai",
        )
        self.api_base = self._get_str("api_base", "https://api.openai.com")
        self.api_key = self._get_str(
            "api_key",
            None if self.api_type != "azure_ad" else "",
        )

        self.model = self._get_str("model", "gpt-4")
        self.backup_model = self._get_str("backup_model", self.model)

        self.api_version = self._get_str("api_version", "2023-07-01-preview")

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
        self.response_format = self._get_enum(
            "response_format",
            options=["json_object", "text", None],
            default="json_object",
        )


class LLMApi(object):
    @inject
    def __init__(self, config: LLMModuleConfig):
        self.config = config

    def _get_aad_token(self) -> str:
        # TODO: migrate to azure-idnetity module
        import msal

        config = self.config

        cache = msal.SerializableTokenCache()

        token_cache_file: Optional[str] = None
        if config.aad_use_token_cache:
            token_cache_file = config.aad_token_cache_full_path
            if not os.path.exists(token_cache_file):
                os.makedirs(os.path.dirname(token_cache_file), exist_ok=True)
            if os.path.exists(token_cache_file):
                with open(token_cache_file, "r") as cache_file:
                    cache.deserialize(cache_file.read())

        def save_cache():
            if token_cache_file is not None and config.aad_use_token_cache:
                with open(token_cache_file, "w") as cache_file:
                    cache_file.write(cache.serialize())

        authority = "https://login.microsoftonline.com/" + config.aad_tenant_id
        api_resource = config.aad_api_resource
        api_scope = config.aad_api_scope
        auth_mode = config.aad_auth_mode

        if auth_mode == "aad_app":
            app = msal.ConfidentialClientApplication(
                client_id=config.aad_client_id,
                client_credential=config.aad_client_secret,
                authority=authority,
                token_cache=cache,
            )
            result = app.acquire_token_for_client(
                scopes=[
                    api_resource + "/" + api_scope,
                ],
            )
            if "access_token" in result:
                return result["access_token"]
            else:
                raise Exception(
                    "Authentication failed for acquiring AAD token for application login: " + str(result),
                )

        scopes = [
            api_resource + "/" + api_scope,
        ]
        app = msal.PublicClientApplication(
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

        if result is None:
            print("no token available from cache, acquiring token from AAD")
            # The pattern to acquire a token looks like this.
            flow = app.initiate_device_flow(scopes=scopes)
            print(flow["message"])
            result = app.acquire_token_by_device_flow(flow=flow)
            if result is not None and "access_token" in result:
                save_cache()
                return result["access_token"]
            else:
                print(result.get("error"))
                print(result.get("error_description"))
                raise Exception(
                    "Authentication failed for acquiring AAD token for AAD auth",
                )

    def chat_completion_stream(self, prompt: List[ChatMessageType]) -> Iterator[str]:
        message = ""
        try:
            response = self.chat_completion(prompt, stream=True)
            for chunk in response:
                message += chunk["content"]
                yield chunk["content"]
        except Exception as e:
            raise e

    @overload
    def chat_completion(
        self,
        messages: List[ChatMessageType],
        engine: str = ...,
        temperature: float = ...,
        max_tokens: int = ...,
        top_p: float = ...,
        frequency_penalty: float = ...,
        presence_penalty: float = ...,
        stop: Union[str, List[str]] = ...,
        stream: Literal[False] = ...,
        backup_engine: str = ...,
        use_backup_engine: bool = ...,
    ) -> ChatMessageType:
        ...

    @overload
    def chat_completion(
        self,
        messages: List[ChatMessageType],
        engine: str = ...,
        temperature: float = ...,
        max_tokens: int = ...,
        top_p: float = ...,
        frequency_penalty: float = ...,
        presence_penalty: float = ...,
        stop: Union[str, List[str]] = ...,
        stream: Literal[True] = ...,
        backup_engine: str = ...,
        use_backup_engine: bool = ...,
    ) -> Generator[ChatMessageType, None, None]:
        ...

    @_cassette_mode_check
    def chat_completion(
        self,
        messages: List[ChatMessageType],
        engine: Optional[str] = None,
        temperature: float = 0,
        max_tokens: int = 1024,
        top_p: float = 0,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        stop: Union[str, List[str]] = DEFAULT_STOP_TOKEN,
        stream: bool = False,
        backup_engine: Optional[str] = None,
        use_backup_engine: bool = False,
    ) -> Union[ChatMessageType, Generator[ChatMessageType, None, None]]:
        api_type = self.config.api_type
        if api_type == "azure":
            client = AzureOpenAI(
                api_version=self.config.api_version,
                azure_endpoint=self.config.api_base,
                api_key=self.config.api_key,
            )
        elif api_type == "azure_ad":
            client = AzureOpenAI(
                api_version=self.config.api_version,
                azure_endpoint=self.config.api_base,
                api_key=self._get_aad_token(),
            )
        elif api_type == "openai":
            client = OpenAI(
                api_key=self.config.api_key,
            )

        engine = self.config.model if engine is None else engine
        backup_engine = self.config.backup_model if backup_engine is None else backup_engine

        def handle_stream_result(res):
            for stream_res in res:
                if not stream_res.choices:
                    continue
                delta = stream_res.choices[0].delta
                yield delta.content

        try:
            if use_backup_engine:
                engine = backup_engine
            res: Any = client.chat.completions.create(
                model=engine,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                stream=stream,
                seed=123456,
                response_format={"type": self.config.response_format} if self.config.response_format else None,
            )
            if stream:
                return handle_stream_result(res)
            else:
                oai_response = res.choices[0].message
                if oai_response is None:
                    raise Exception("OpenAI API returned an empty response")
                response: ChatMessageType = format_chat_message(
                    role=oai_response.role if oai_response.role is not None else "assistant",
                    message=oai_response.content if oai_response.content is not None else "",
                )
                return response

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
