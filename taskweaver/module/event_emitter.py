from dataclasses import dataclass
from enum import Enum


class SessionEventType(Enum):
    session_start = "session_start"
    session_end = "session_end"
    session_round_update = "session_round_update"


class RoundEventType(Enum):
    round_start = "round_start"
    round_end = "round_end"
    round_error = "round_error"
    round_post_update = "round_post_update"


class PostEventType(Enum):
    post_start = "post_start"
    post_end = "post_end"
    post_error = "post_error"
    post_attachment_update = "post_attachment_update"


@dataclass
class SessionEvent:
    t: SessionEventType
    session_id: str
    message: str


@dataclass
class RoundEvent:
    t: RoundEventType
    session_id: str
    round_id: str
    message: str


@dataclass
class PostEvent:
    t: PostEventType
    session_id: str
    round_id: str
    post_id: str
    message: str


class SessionEventEmitter:
    def __init__(self):
        self.handlers = []

    def emit(self, event: SessionEvent):
        for handler in self.handlers:
            handler(event)
