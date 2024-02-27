import os

from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.llm import LLMApi
from taskweaver.logging import LoggingModule


def test_multi_llm():
    app_injector = Injector(
        [LoggingModule],
    )
    app_config = AppConfigSource(
        config={
            "llm.api_type": "openai",
            "llm.api_base": "https://api.openai.com/v1",
            "llm.api_key": "YOUR_API_KEY",
            "llm.model": "gpt-3.5-turbo-1106",
            "llm.response_format": "json_object",
            "app_dir": os.path.dirname(os.path.abspath(__file__)),
            "ext_llms.llm_list": [
                {
                    "llm.api_type": "openai",
                    "llm.api_base": "https://api.openai.com/v1",
                    "llm.api_key": "YOUR_API_KEY",
                    "llm.model": "gpt-4-1106-preview",
                    "llm.response_format": "json_object",
                },
                {
                    "llm.api_type": "google_genai",
                    "llm.api_key": "YOUR_API_KEY",
                    "llm.model": "gemini-pro",
                },
            ],
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)

    llm_api = app_injector.get(LLMApi)

    assert len(llm_api.ext_llms) == 2, "llm list should have 2 items"
    assert "openai.gpt-4-1106-preview" in llm_api.ext_llms, "openai.gpt-4-1106-preview should be in llm dict"
    assert "google_genai.gemini-pro" in llm_api.ext_llms, "google_genai.gemini-pro should be in llm dict"
