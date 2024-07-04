from random import randint
from typing import Iterator

import pytest
from injector import Injector

from taskweaver.llm.util import format_chat_message
from taskweaver.logging import LoggingModule
from taskweaver.memory import Attachment, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.role import PostTranslator

response_str1 = """{
    "response": {
        "thought": "This is the thought",
        "python": "print('This is the code')",
        "text": "This is the text",
        "execution_status": "SUCCESS",
        "execution_result": "This is the execution result",
        "send_to": "Planner",
        "message": "This is the message"
    }
}"""

response_err_str1 = """{
    "response": {
        "thought": "This is the thought",
        "python": "print('This is the code')",
        "text": {"error": {"type": "t1", "content": "This is the error"}},
        "execution_status": 1,
        "execution_result": ["This", "is the execution", "result"],
        "send_to": "Planner",
        "message": "This is the message",
        "obj_in_arr": [{"key1": "value1"}, {"key2": "value2"}],
        "arr_in_obj": {"key1": ["value1", "value2"], "key2": ["value3", "value4"]}
    }
}"""

role_name = "ProgramApe"
executor_name = "CodeExecutor"

app_injector = Injector(
    [LoggingModule],
)
translator = app_injector.create_object(PostTranslator)


def response_str(response: str) -> Iterator[str]:
    words = response.split(" ")
    # everytime return random number (max 10) of words from response_str1
    pos = 0

    while True:
        n = randint(1, 10)
        part = " ".join(words[pos : pos + n]) + " "
        yield part
        pos += n
        if pos >= len(words):
            break


def test_parse_llm_stream():
    attachments = translator.parse_llm_output_stream(response_str(response_str1))
    attachment_list = list(attachments)
    assert len(attachment_list) == 7

    attachments = translator.parse_llm_output_stream_v2(response_str(response_str1))
    attachment_list = list(a for a in attachments if a[2])  # only count is_end is true
    assert len(attachment_list) == 7


def test_parse_err_llm_stream():
    attachments = translator.parse_llm_output_stream(response_str(response_err_str1))
    attachment_list = list(attachments)
    assert len(attachment_list) == 4

    attachments = list(translator.parse_llm_output_stream_v2(response_str(response_err_str1)))
    attachment_list = [a for a in attachments if a[2]]  # only count is_end is true
    assert len(attachment_list) == 9

    text_attachment = [a for a in attachments if a[0] == "text"]
    text_value = "".join(str(a[1]) for a in text_attachment)
    assert text_value == '{"error": {"type": "t1", "content": "This is the error"}}'

    text_attachment = [a for a in attachments if a[0] == "execution_result"]
    text_value = "".join(str(a[1]) for a in text_attachment)
    assert text_value == '["This", "is the execution", "result"]'

    text_attachment = [a for a in attachments if a[0] == "execution_status"]
    text_value = "".join(str(a[1]) for a in text_attachment)
    assert text_value == "1"

    text_attachment = [a for a in attachments if a[0] == "obj_in_arr"]
    text_value = "".join(str(a[1]) for a in text_attachment)
    assert text_value == '[{"key1": "value1"}, {"key2": "value2"}]'

    text_attachment = [a for a in attachments if a[0] == "arr_in_obj"]
    text_value = "".join(str(a[1]) for a in text_attachment)
    assert text_value == '{"key1": ["value1", "value2"], "key2": ["value3", "value4"]}'


response_err_str2 = """{
    "response": {
        "thought": "This is the thought",
        "python": "print('This is the code')",
        "text": {"error": "This is the error",
        "execution_status": "ERROR",
        "execution_result": ["This", "is the execution", "result"],
        "send_to": "Planner",
        "message": "This is the message",
        "obj_in_arr": [{"key1": "value1"}, {"key2": "value2"}],
        "arr_in_obj": {"key1": ["value1", "value2"], "key2": ["value3", "value4"]}
    }
}"""


def test_parse_err_llm_stream2():
    attachments = list(translator.parse_llm_output_stream_v2(response_str(response_err_str2)))
    attachment_list = [a for a in attachments if a[2]]  # only count is_end is true
    assert len(attachment_list) == 3


response_str2 = (
    '{"response": {"thought": "This is the thought", "reply_type": "python", '
    '"reply_content": "print(\'This is the code\')", "execution_status": '
    '"SUCCESS", "execution_result": "This is the execution result", "send_to": '
    '"Planner", "message": "This is the message"}}'
)


@pytest.mark.parametrize("use_v2_parser", [True, False])
def test_parse_llm(use_v2_parser: bool):
    def early_stop(type: AttachmentType, text: str) -> bool:
        if type in [AttachmentType.reply_content]:
            return True
        return False

    event_emitter = SessionEventEmitter()
    event_emitter.start_round("test_round")

    post_proxy = event_emitter.create_post_proxy("CodeInterpreter")
    translator.raw_text_to_post(
        llm_output=[format_chat_message("assistant", response_str2)],
        post_proxy=post_proxy,
        early_stop=early_stop,
        use_v2_parser=use_v2_parser,
    )
    response = post_proxy.end()
    assert response.message == ""
    assert response.send_to is "Unknown"
    assert response.send_from == "CodeInterpreter"
    assert len(response.attachment_list) == 3
    assert response.attachment_list[0].type == AttachmentType.thought
    assert response.attachment_list[0].content == "This is the thought"

    assert response.attachment_list[1].type == AttachmentType.reply_type
    assert response.attachment_list[1].content == "python"

    assert response.attachment_list[2].type == AttachmentType.reply_content
    assert response.attachment_list[2].content == "print('This is the code')"

    post_proxy = event_emitter.create_post_proxy("CodeInterpreter")
    translator.raw_text_to_post(
        llm_output=[format_chat_message("assistant", response_str2)],
        post_proxy=post_proxy,
        use_v2_parser=use_v2_parser,
    )
    response = post_proxy.end()

    assert len(response.attachment_list) == 5
    assert response.attachment_list[3].type == AttachmentType.execution_status
    assert response.attachment_list[3].content == "SUCCESS"
    assert response.attachment_list[4].type == AttachmentType.execution_result
    assert response.attachment_list[4].content == "This is the execution result"


response_str_non_stop = (
    '{"response": {"thought": "This is the thought", "reply_type": "python", '
    '"reply_content": "print(\'This is the code\')", "execution_status": '
    '"SUCCESS", "execution_result": "This is the execution result", "send_to": '
    '"Planner", "message": "This is '
)


def test_parse_llm2():
    def early_stop(type: AttachmentType, text: str) -> bool:
        if type in [AttachmentType.reply_content]:
            return True
        return False

    event_emitter = SessionEventEmitter()
    event_emitter.start_round("test_round")

    post_proxy = event_emitter.create_post_proxy("CodeInterpreter")
    translator.raw_text_to_post(
        llm_output=[format_chat_message("assistant", response_str_non_stop)],
        post_proxy=post_proxy,
        early_stop=early_stop,
        use_v2_parser=True,
    )
    response = post_proxy.end()
    assert response.message == ""
    assert response.send_to is "Unknown"
    assert response.send_from == "CodeInterpreter"
    assert len(response.attachment_list) == 3
    assert response.attachment_list[0].type == AttachmentType.thought
    assert response.attachment_list[0].content == "This is the thought"

    assert response.attachment_list[1].type == AttachmentType.reply_type
    assert response.attachment_list[1].content == "python"

    assert response.attachment_list[2].type == AttachmentType.reply_content
    assert response.attachment_list[2].content == "print('This is the code')"

    post_proxy = event_emitter.create_post_proxy("CodeInterpreter")
    translator.raw_text_to_post(
        llm_output=[format_chat_message("assistant", response_str_non_stop)],
        post_proxy=post_proxy,
        use_v2_parser=True,
    )
    response = post_proxy.end()

    assert len(response.attachment_list) == 5
    assert response.attachment_list[3].type == AttachmentType.execution_status
    assert response.attachment_list[3].content == "SUCCESS"
    assert response.attachment_list[4].type == AttachmentType.execution_result
    assert response.attachment_list[4].content == "This is the execution result"
    assert response.send_to == "Planner"
    assert response.message == "This is "


def test_post_to_raw_text():
    post = Post.create(
        message="This is the message",
        send_from="CodeInterpreter",
        send_to="Planner",
    )

    prompt = translator.post_to_raw_text(
        post=post,
        if_format_message=True,
        if_format_send_to=True,
    )
    assert prompt == '{"response": {"send_to": "Planner", "message": "This is the message"}}'

    prompt = translator.post_to_raw_text(
        post=post,
        if_format_message=False,
        if_format_send_to=False,
    )
    assert prompt == '{"response": {}}'

    post.add_attachment(
        Attachment.create(type="thought", content="This is the thought"),
    )
    post.add_attachment(
        Attachment.create(type="reply_type", content="python"),
    )
    post.add_attachment(Attachment.create(type="reply_content", content="print('This is the code')"))
    post.add_attachment(Attachment.create(type="execution_status", content="SUCCESS"))
    post.add_attachment(
        Attachment.create(
            type="execution_result",
            content="This is the execution result",
        ),
    )

    prompt = translator.post_to_raw_text(
        post=post,
        if_format_message=True,
        if_format_send_to=True,
    )
    assert prompt == response_str2
