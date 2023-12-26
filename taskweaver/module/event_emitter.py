import abc
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, ParamSpec, TypeVar, Union


class EventScope(Enum):
    session = "session"
    round = "round"
    post = "post"


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
class TaskWeaverEvent:
    scope: EventScope
    t: Union[SessionEventType, RoundEventType, PostEventType]
    session_id: str
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
                event.session_id,
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
                event.session_id,
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
                event.session_id,
            )

    def handle_session(
        self,
        type: SessionEventType,
        msg: str,
        extra: Any,
        session_id: str,
        **kwargs: Any,
    ):
        pass

    def handle_round(
        self,
        type: RoundEventType,
        msg: str,
        extra: Any,
        round_id: str,
        session_id: str,
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
        session_id: str,
        **kwargs: Any,
    ):
        pass


_ParamType = ParamSpec("_ParamType")
_ReturnType = TypeVar("_ReturnType")


class SessionEventEmitter:
    def __init__(self):
        self.handlers: List[SessionEventHandler] = []

    def emit(self, event: TaskWeaverEvent):
        for handler in self.handlers:
            handler.handle(event)

    def emit_compat(self, t: str, msg: str, extra: Any = None):
        print(f"[{t}] {msg}")
        self.emit(
            TaskWeaverEvent(
                EventScope.session,
                SessionEventType(t),
                "",
                None,
                None,
                msg,
                extra,
            ),
        )

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
