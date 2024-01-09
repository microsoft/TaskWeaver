import io
import itertools
import json
from json import JSONDecodeError
from typing import Any, Callable, Dict, Iterator, List, Literal, Optional, Union

import ijson
from injector import inject

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
        llm_output: str,
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
        self.logger.info(f"LLM output: {llm_output}")
        for d in self.parse_llm_output_stream([llm_output]):
            type_str = d["type"]
            type: Optional[AttachmentType] = None
            value = d["content"]
            if type_str == "message":
                post_proxy.update_message(value)
            elif type_str == "send_to":
                assert value in [
                    "User",
                    "Planner",
                    "CodeInterpreter",
                ], f"Invalid send_to value: {value}"
                post_proxy.update_send_to(value)  # type: ignore
            else:
                try:
                    type = AttachmentType(type_str)
                    post_proxy.update_attachment(value, type)
                except Exception as e:
                    self.logger.warning(f"Failed to parse attachment: {d} due to {str(e)}")
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
            if early_stop is not None and early_stop(parsed_type, value):
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
    ) -> Iterator[Dict[str, str]]:
        json_data_stream = io.StringIO("".join(itertools.chain(llm_output)))
        parser = ijson.parse(json_data_stream)
        element = {}
        try:
            for prefix, event, value in parser:
                if prefix == "response.item" and event == "map_key" and value == "type":
                    element["type"] = None
                elif prefix == "response.item.type" and event == "string":
                    element["type"] = value
                elif prefix == "response.item" and event == "map_key" and value == "content":
                    element["content"] = None
                elif prefix == "response.item.content" and event == "string":
                    element["content"] = value

                if len(element) == 2 and None not in element.values():
                    yield element
                    element = {}
        except ijson.JSONError as e:
            self.logger.warning(
                f"Failed to parse LLM output stream due to JSONError: {str(e)}",
            )
