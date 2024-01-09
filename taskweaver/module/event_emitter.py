from __future__ import annotations

import abc
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from taskweaver.memory.attachment import Attachment, AttachmentType
from taskweaver.memory.post import Post
from taskweaver.memory.type_vars import RoleName


class EventScope(Enum):
    session = "session"
    round = "round"
    post = "post"


class SessionEventType(Enum):
    session_start = "session_start"
    session_end = "session_end"
    session_new_round = "session_new_round"


class RoundEventType(Enum):
    round_start = "round_start"
    round_end = "round_end"
    round_error = "round_error"
    round_new_post = "round_new_post"


class PostEventType(Enum):
    post_start = "post_start"
    post_end = "post_end"
    post_error = "post_error"

    post_status_update = "post_status_update"
    post_send_to_update = "post_send_to_update"
    post_message_update = "post_message_update"
    post_attachment_update = "post_attachment_update"


@dataclass
class TaskWeaverEvent:
    scope: EventScope
    t: Union[SessionEventType, RoundEventType, PostEventType]
    round_id: Optional[str]
    post_id: Optional[str]
    msg: str
    extra: Any = None


class SessionEventHandler(abc.ABC):
    @abc.abstractmethod
    def handle(self, event: TaskWeaverEvent):
        pass


class SessionEventHandlerBase(SessionEventHandler):
    def handle(self, event: TaskWeaverEvent):
        if event.scope == EventScope.session:
            assert isinstance(event.t, SessionEventType)
            session_event_type: SessionEventType = event.t
            self.handle_session(
                session_event_type,
                event.msg,
                event.extra,
            )
        elif event.scope == EventScope.round:
            assert isinstance(event.t, RoundEventType)
            assert event.round_id is not None
            round_event_type: RoundEventType = event.t
            self.handle_round(
                round_event_type,
                event.msg,
                event.extra,
                event.round_id,
            )

        elif event.scope == EventScope.post:
            assert isinstance(event.t, PostEventType)
            assert event.post_id is not None
            assert event.round_id is not None
            post_event_type: PostEventType = event.t
            self.handle_post(
                post_event_type,
                event.msg,
                event.extra,
                event.post_id,
                event.round_id,
            )

    def handle_session(
        self,
        type: SessionEventType,
        msg: str,
        extra: Any,
        **kwargs: Any,
    ):
        pass

    def handle_round(
        self,
        type: RoundEventType,
        msg: str,
        extra: Any,
        round_id: str,
        **kwargs: Any,
    ):
        pass

    def handle_post(
        self,
        type: PostEventType,
        msg: str,
        extra: Any,
        post_id: str,
        round_id: str,
        **kwargs: Any,
    ):
        pass


class PostEventProxy:
    def __init__(self, emitter: SessionEventEmitter, round_id: str, post: Post) -> None:
        self.emitter = emitter
        self.round_id = round_id
        self.post = post
        self.message_is_end = False
        self.create("Post created")

    def create(self, message: str):
        self._emit(
            PostEventType.post_start,
            message,
            {
                "role": self.post.send_from,
            },
        )

    def update_send_to(self, send_to: RoleName):
        self.post.send_to = send_to
        self._emit(
            PostEventType.post_send_to_update,
            "",
            {
                "role": send_to,
            },
        )

    def update_status(self, status: str):
        self._emit(PostEventType.post_status_update, status)

    def update_message(self, message: str, is_end: bool = True):
        assert not self.message_is_end, "Cannot update message when update is finished"
        self.post.message += message
        self.message_is_end = is_end
        self._emit(PostEventType.post_message_update, message, {"is_end": is_end})

    def update_attachment(
        self,
        message: str,
        type: Optional[AttachmentType] = None,
        extra: Any = None,
        id: Optional[str] = None,
        is_end: bool = True,
    ) -> Attachment:
        if id is not None:
            attachment = self.post.attachment_list[-1]
            assert id == attachment.id
        else:
            assert type is not None, "type is required when creating new attachment"
            attachment = Attachment.create(
                type=type,
                content=message,
                extra=extra,
                id=id,
            )
            self.post.add_attachment(attachment)
        self._emit(
            PostEventType.post_attachment_update,
            message,
            {
                "type": type,
                "extra": extra,
                "id": id,
                "is_end": is_end,
            },
        )
        return attachment

    def error(self, msg: str):
        self.post.attachment_list = []
        self.post.message = msg
        self._emit(PostEventType.post_error, msg)

    def end(self, msg: str = ""):
        self._emit(PostEventType.post_end, msg)
        return self.post

    def _emit(
        self,
        event_type: PostEventType,
        message: str,
        extra: Dict[str, Any] = {},
    ):
        self.emitter.emit(
            TaskWeaverEvent(
                EventScope.post,
                event_type,
                self.round_id,
                self.post.id,
                message,
                extra=extra,
            ),
        )


class SessionEventEmitter:
    def __init__(self):
        self.handlers: List[SessionEventHandler] = []
        self.current_round_id: Optional[str] = None

    def emit(self, event: TaskWeaverEvent):
        for handler in self.handlers:
            handler.handle(event)

    def start_round(self, round_id: str):
        self.current_round_id = round_id
        self.emit(
            TaskWeaverEvent(
                EventScope.round,
                RoundEventType.round_start,
                round_id,
                None,
                "Round started",
            ),
        )

    def create_post_proxy(self, send_from: RoleName) -> PostEventProxy:
        assert self.current_round_id is not None, "Cannot create post proxy without a round in active"
        return PostEventProxy(
            self,
            self.current_round_id,
            Post.create(message="", send_from=send_from),
        )

    def emit_error(self, msg: str):
        self.emit(
            TaskWeaverEvent(
                EventScope.round,
                RoundEventType.round_error,
                self.current_round_id,
                None,
                msg,
            ),
        )

    def end_round(self, round_id: str):
        assert self.current_round_id == round_id, "Cannot end round that is not in active"
        self.emit(
            TaskWeaverEvent(
                EventScope.round,
                RoundEventType.round_end,
                round_id,
                None,
                "Round ended",
            ),
        )
        self.current_round_id = None

    def register(self, handler: SessionEventHandler):
        self.handlers.append(handler)

    def unregister(self, handler: SessionEventHandler):
        self.handlers.remove(handler)

    @contextmanager
    def handle_events_ctx(self, handler: Optional[SessionEventHandler] = None):
        if handler is None:
            yield
        else:
            self.register(handler)
            yield
            self.unregister(handler)
