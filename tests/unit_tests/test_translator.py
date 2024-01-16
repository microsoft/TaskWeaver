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

response_str1 = (
    '{"response": [{"type": "thought", "content": "This is the thought"}, {"type": "python", '
    '"content": "print(\'This is the code\')"}, {"type": "text", "content": "This '
    'is the text"}, {"type": "sample", "content": "print(\'This is the '
    'sample code\')"}, {"type": "execution_status", "content": "SUCCESS"}, '
    '{"type": "execution_result", "content": "This is the execution result"}, '
    '{"type": "send_to", "content": "Planner"}, {"type": "message", "content": '
    '"This is the message"}]}'
)

role_name = "ProgramApe"
executor_name = "CodeExecutor"

app_injector = Injector(
    [LoggingModule],
)
translator = app_injector.create_object(PostTranslator)


def test_parse_llm_stream():
    def response_str() -> Iterator[str]:
        words = response_str1.split(" ")
        # everytime return random number (max 10) of words from response_str1
        pos = 0

        while True:
            n = randint(1, 10)
            part = " ".join(words[pos : pos + n]) + " "
            yield part
            pos += n
            if pos >= len(words):
                break

    attachments = translator.parse_llm_output_stream(response_str())
    attachment_list = list(attachments)
    assert len(attachment_list) == 8

    attachments = translator.parse_llm_output_stream_v2(response_str())
    attachment_list = list(a for a in attachments if a[2])  # only count is_end is true
    assert len(attachment_list) == 8


@pytest.mark.parametrize("use_v2_parser", [True, False])
def test_parse_llm(use_v2_parser: bool):
    def early_stop(type: AttachmentType, text: str) -> bool:
        if type in [AttachmentType.python, AttachmentType.sample, AttachmentType.text]:
            return True
        return False

    event_emitter = SessionEventEmitter()
    event_emitter.start_round("test_round")

    post_proxy = event_emitter.create_post_proxy("CodeInterpreter")
    translator.raw_text_to_post(
        llm_output=[format_chat_message("assistant", response_str1)],
        post_proxy=post_proxy,
        early_stop=early_stop,
        use_v2_parser=use_v2_parser,
    )
    response = post_proxy.end()
    assert response.message == ""
    assert response.send_to is "Unknown"
    assert response.send_from == "CodeInterpreter"
    assert len(response.attachment_list) == 2
    assert response.attachment_list[0].type == AttachmentType.thought
    assert response.attachment_list[0].content == "This is the thought"

    assert response.attachment_list[1].type == AttachmentType.python
    assert response.attachment_list[1].content == "print('This is the code')"

    post_proxy = event_emitter.create_post_proxy("CodeInterpreter")
    translator.raw_text_to_post(
        llm_output=[format_chat_message("assistant", response_str1)],
        post_proxy=post_proxy,
        use_v2_parser=use_v2_parser,
    )
    response = post_proxy.end()

    assert len(response.attachment_list) == 6
    assert response.attachment_list[4].type == AttachmentType.execution_status
    assert response.attachment_list[4].content == "SUCCESS"
    assert response.attachment_list[5].type == AttachmentType.execution_result
    assert response.attachment_list[5].content == "This is the execution result"


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
    assert prompt == (
        '{"response": [{"type": "send_to", "content": "Planner"}, {"type": "message", '
        '"content": "This is the message"}]}'
    )

    prompt = translator.post_to_raw_text(
        post=post,
        if_format_message=False,
        if_format_send_to=False,
    )
    assert prompt == '{"response": []}'

    post.add_attachment(
        Attachment.create(type="thought", content="This is the thought"),
    )
    post.add_attachment(
        Attachment.create(type="python", content="print('This is the code')"),
    )
    post.add_attachment(Attachment.create(type="text", content="This is the text"))
    post.add_attachment(
        Attachment.create(type="sample", content="print('This is the sample code')"),
    )
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
    assert prompt == response_str1
