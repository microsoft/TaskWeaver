from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from taskweaver.memory.attachment import Attachment, AttachmentType
from taskweaver.memory.type_vars import RoleName
from taskweaver.utils import create_id


@dataclass
class Post:
    """
    A post is the message used to communicate between two roles.
    It should always have a text_message to denote the string message,
    while other data formats should be put in the attachment.
    The role can be either a User, a Planner, or a CodeInterpreter.

    Args:
        id: the unique id of the post.
        send_from: the role who sends the post.
        send_to: the role who receives the post.
        text_message: the text message in the post.
        attachment_list: a list of attachments in the post.

    """

    id: str
    send_from: RoleName
    send_to: RoleName
    message: str
    attachment_list: List[Attachment]

    @staticmethod
    def create(
        message: Optional[str],
        send_from: RoleName,
        send_to: RoleName = "Unknown",
        attachment_list: Optional[List[Attachment]] = None,
    ) -> Post:
        """create a post with the given message, send_from, send_to, and attachment_list."""
        return Post(
            id="post-" + create_id(),
            message=message is not None and message or "",
            send_from=send_from,
            send_to=send_to,
            attachment_list=attachment_list if attachment_list is not None else [],
        )

    def __repr__(self):
        return "\n".join(
            [
                f"* Post: {self.send_from} -> {self.send_to}:",
                f"    # Message: {self.message}",
                f"    # Attachment List: {self.attachment_list}",
            ],
        )

    def __str__(self):
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the post to a dict."""
        return {
            "id": self.id,
            "message": self.message,
            "send_from": self.send_from,
            "send_to": self.send_to,
            "attachment_list": [attachment.to_dict() for attachment in self.attachment_list],
        }

    @staticmethod
    def from_dict(content: Dict[str, Any]) -> Post:
        """Convert the dict to a post. Will assign a new id to the post."""
        return Post(
            id="post-" + secrets.token_hex(6),
            message=content["message"],
            send_from=content["send_from"],
            send_to=content["send_to"],
            attachment_list=[Attachment.from_dict(attachment) for attachment in content["attachment_list"]]
            if content["attachment_list"] is not None
            else [],
        )

    def add_attachment(self, attachment: Attachment) -> None:
        """Add an attachment to the post."""
        self.attachment_list.append(attachment)

    def get_attachment(self, type: AttachmentType) -> List[Any]:
        """Get all the attachments of the given type."""
        return [attachment.content for attachment in self.attachment_list if attachment.type == type]

    def del_attachment(self, type_list: List[AttachmentType]) -> None:
        """Delete all the attachments of the given type."""
        self.attachment_list = [attachment for attachment in self.attachment_list if attachment.type not in type_list]
