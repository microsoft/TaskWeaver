import io
import json
from json import JSONDecodeError
from typing import Any, Callable, Dict, Iterable, Iterator, List, Literal, Optional, Tuple, Union

import ijson
from injector import inject

from taskweaver.llm.util import ChatMessageType
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Attachment, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import PostEventProxy, SessionEventEmitter


class PostTranslator:
    """
    PostTranslator is used to parse the output of the LLM or convert it to a Post object.
    The core function is post_to_raw_text and raw_text_to_post.
    """

    @inject
    def __init__(
        self,
        logger: TelemetryLogger,
        event_emitter: SessionEventEmitter,
    ):
        self.logger = logger
        self.event_emitter = event_emitter

    def raw_text_to_post(
        self,
        llm_output: Iterable[ChatMessageType],
        post_proxy: PostEventProxy,
        early_stop: Optional[Callable[[Union[AttachmentType, Literal["message", "send_to"]], str], bool]] = None,
        validation_func: Optional[Callable[[Post], None]] = None,
    ) -> None:
        """
        Convert the raw text output of LLM to a Post object.
        :param llm_output_stream:
        :param send_from:
        :param early_stop:
        :return: Post
        """

        # llm_output_list = [token for token in llm_output_stream]  # collect all the llm output via iterator
        # llm_output = "".join(llm_output_list)
        def stream_filter(s: Iterable[ChatMessageType]) -> Iterator[str]:
            full_llm_content = ""
            for c in s:
                full_llm_content += c["content"]
                yield c["content"]
            self.logger.info(f"LLM output: {llm_output}")

        value_buf: str = ""
        for type_str, value, is_end in self.parse_llm_output_stream(stream_filter(llm_output)):
            value_buf += value
            type: Optional[AttachmentType] = None
            if type_str == "message":
                post_proxy.update_message(value_buf, is_end=is_end)
                value_buf = ""
            elif type_str == "send_to":
                if is_end:
                    assert value in [
                        "User",
                        "Planner",
                        "CodeInterpreter",
                    ], f"Invalid send_to value: {value}"
                    post_proxy.update_send_to(value)  # type: ignore
                else:
                    # collect the whole content before updating post
                    pass
            else:
                try:
                    type = AttachmentType(type_str)
                    post_proxy.update_attachment(value_buf, type, is_end=is_end)
                    value_buf = ""
                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse attachment: {type_str}-{value_buf} due to {str(e)}",
                    )
                    continue
            parsed_type = (
                type
                if type is not None
                else "message"
                if type_str == "message"
                else "send_to"
                if type_str == "send_to"
                else None
            )
            assert parsed_type is not None, f"Invalid type: {type_str}"

            # check whether parsing should be triggered prematurely when each key parsing is finished
            if is_end and early_stop is not None and early_stop(parsed_type, value):
                break

        if validation_func is not None:
            validation_func(post_proxy.post)

    def post_to_raw_text(
        self,
        post: Post,
        content_formatter: Callable[[Attachment], str] = lambda x: x.content,
        if_format_message: bool = True,
        if_format_send_to: bool = True,
        ignored_types: Optional[List[AttachmentType]] = None,
    ) -> str:
        """
        Convert a Post object to raw text in the format of LLM output.
        :param post:
        :param content_formatter:
        :param if_format_message:
        :param if_format_send_to:
        :param ignored_types:
        :return: str
        """
        structured_llm: List[Dict[str, str]] = []
        for attachment in post.attachment_list:
            attachments_dict = {}
            if ignored_types is not None and attachment.type in ignored_types:
                continue
            attachments_dict["type"] = attachment.type.value
            attachments_dict["content"] = content_formatter(attachment)
            structured_llm.append(attachments_dict)
        if if_format_send_to:
            structured_llm.append({"type": "send_to", "content": post.send_to})
        if if_format_message:
            structured_llm.append({"type": "message", "content": post.message})
        structured_llm_text = json.dumps({"response": structured_llm})
        return structured_llm_text

    def parse_llm_output(self, llm_output: str) -> List[Dict[str, str]]:
        try:
            structured_llm_output: Any = json.loads(llm_output)["response"]
            assert isinstance(
                structured_llm_output,
                list,
            ), "LLM output should be a list object"
            return structured_llm_output  # type: ignore
        except (JSONDecodeError, AssertionError) as e:
            self.logger.error(
                f"Failed to parse LLM output due to {str(e)}. LLM output:\n {llm_output}",
            )
            raise e

    def parse_llm_output_stream(
        self,
        llm_output: Iterator[str],
    ) -> Iterator[Tuple[str, str, bool]]:
        class StringIteratorIO(io.TextIOBase):
            def __init__(self, iter: Iterator[str]):
                self._iter = iter
                self._left: str = ""

            def readable(self):
                return True

            def _read1(self, n: Optional[int] = None):
                while not self._left:
                    try:
                        self._left = next(self._iter)
                    except StopIteration:
                        break
                ret = self._left[:n]
                self._left = self._left[len(ret) :]
                return ret

            def read(self, n: Optional[int] = None):
                l: List[str] = []
                if n is None or n < 0:
                    while True:
                        m = self._read1()
                        if not m:
                            break
                        l.append(m)
                else:
                    while n > 0:
                        m = self._read1(n)
                        if not m:
                            break
                        n -= len(m)
                        l.append(m)
                return "".join(l)

        json_data_stream = StringIteratorIO(llm_output)
        # use small buffer to get parse result as soon as acquired from LLM
        parser = ijson.parse(json_data_stream, buf_size=5)

        cur_type: Optional[str] = None
        cur_content: Optional[str] = None
        try:
            for prefix, event, value in parser:
                if prefix == "response.item" and event == "map_key" and value == "type":
                    cur_type = None
                elif prefix == "response.item.type" and event == "string":
                    cur_type = value
                elif prefix == "response.item" and event == "map_key" and value == "content":
                    cur_content = None
                elif prefix == "response.item.content" and event == "string":
                    cur_content = value

                if cur_type is not None and cur_content is not None:
                    yield cur_type, cur_content, True
                    cur_type, cur_content = None, None
        except ijson.JSONError as e:
            self.logger.warning(
                f"Failed to parse LLM output stream due to JSONError: {str(e)}",
            )
