import json

import pytest
from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.llm import LLMApi, format_chat_message
from taskweaver.llm.mock import LLMMockApiException
from taskweaver.llm.util import ChatMessageType


@pytest.mark.app_config(
    {
        "llm.use_mock": True,
        "llm.mock.mode": "playback_only",
    },
)
def test_llm_exception_with_smoother(app_injector: Injector):
    api = app_injector.get(LLMApi)
    with pytest.raises(LLMMockApiException):
        s = api.chat_completion_stream(
            [format_chat_message("user", "Hi")],
            use_smoother=True,
        )
        for _ in s:
            pass


@pytest.mark.app_config(
    {
        "llm.use_mock": True,
        "llm.mock.mode": "fixed",
    },
)
@pytest.mark.parametrize(
    "use_smoother",
    [True, False],
)
@pytest.mark.parametrize(
    "playback_delay",
    [-1, 0, 0.01],
)
@pytest.mark.parametrize(
    "chat_response",
    [
        # empty message chunk
        format_chat_message("assistant", ""),
        # short message chunk
        format_chat_message("assistant", "Hi"),
        # long message chunk
        format_chat_message("assistant", "Hi, " * 100),
    ],
)
def test_llm_output_format(
    app_injector: Injector,
    use_smoother: bool,
    playback_delay: float,
    chat_response: ChatMessageType,
):
    config_source = app_injector.get(AppConfigSource)
    config_source.set_config_value(
        "llm.mock.playback_delay",
        "float",
        playback_delay,
        "override",
    )
    config_source.set_config_value(
        "llm.mock.fixed_chat_responses",
        "str",
        json.dumps(chat_response),
        "override",
    )
    api = app_injector.get(LLMApi)
    s = api.chat_completion_stream(
        [format_chat_message("user", "Hi")],
        use_smoother=use_smoother,
    )
    recv_msg = ""
    for chunk in s:
        recv_msg += chunk["content"]

    assert recv_msg == chat_response["content"]
