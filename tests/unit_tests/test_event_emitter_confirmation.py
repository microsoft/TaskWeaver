import threading
import time

from taskweaver.module.event_emitter import ConfirmationHandler, PostEventType, SessionEventEmitter


class MockConfirmationHandler(ConfirmationHandler):
    def __init__(self, auto_approve: bool = True):
        self.auto_approve = auto_approve
        self.confirmation_requested = False
        self.last_code = None
        self.last_round_id = None
        self.last_post_id = None

    def request_confirmation(self, code: str, round_id: str, post_id: str | None) -> bool:
        self.confirmation_requested = True
        self.last_code = code
        self.last_round_id = round_id
        self.last_post_id = post_id
        return self.auto_approve


def test_confirmation_auto_approve_when_no_handler():
    emitter = SessionEventEmitter()
    emitter.start_round("test-round-1")

    result = emitter.request_code_confirmation("print('hello')", "post-1")

    assert result is True
    assert not emitter.confirmation_pending


def test_confirmation_pending_property():
    emitter = SessionEventEmitter()
    emitter.start_round("test-round-1")
    handler = MockConfirmationHandler(auto_approve=True)
    emitter.confirmation_handler = handler

    def request_thread():
        emitter.request_code_confirmation("print('hello')", "post-1")

    def provide_thread():
        while not emitter.confirmation_pending:
            time.sleep(0.01)

        assert emitter.confirmation_pending
        assert emitter.pending_confirmation_code == "print('hello')"

        emitter.provide_confirmation(True)

    t1 = threading.Thread(target=request_thread)
    t2 = threading.Thread(target=provide_thread)

    t1.start()
    t2.start()

    t1.join(timeout=2)
    t2.join(timeout=2)

    assert not t1.is_alive()
    assert not t2.is_alive()


def test_confirmation_approved():
    emitter = SessionEventEmitter()
    emitter.start_round("test-round-1")
    handler = MockConfirmationHandler()
    emitter.confirmation_handler = handler

    result = None

    def request_thread():
        nonlocal result
        result = emitter.request_code_confirmation("print('test')", "post-1")

    def provide_thread():
        while not emitter.confirmation_pending:
            time.sleep(0.01)
        emitter.provide_confirmation(True)

    t1 = threading.Thread(target=request_thread)
    t2 = threading.Thread(target=provide_thread)

    t1.start()
    t2.start()

    t1.join(timeout=2)
    t2.join(timeout=2)

    assert result is True


def test_confirmation_rejected():
    emitter = SessionEventEmitter()
    emitter.start_round("test-round-1")
    handler = MockConfirmationHandler()
    emitter.confirmation_handler = handler

    result = None

    def request_thread():
        nonlocal result
        result = emitter.request_code_confirmation("rm -rf /", "post-1")

    def provide_thread():
        while not emitter.confirmation_pending:
            time.sleep(0.01)
        emitter.provide_confirmation(False)

    t1 = threading.Thread(target=request_thread)
    t2 = threading.Thread(target=provide_thread)

    t1.start()
    t2.start()

    t1.join(timeout=2)
    t2.join(timeout=2)

    assert result is False


def test_confirmation_events_emitted():
    emitter = SessionEventEmitter()
    emitter.start_round("test-round-1")
    handler = MockConfirmationHandler()
    emitter.confirmation_handler = handler

    events_captured = []

    class EventCapture:
        def handle(self, event):
            events_captured.append(event)

    emitter.register(EventCapture())

    def request_thread():
        emitter.request_code_confirmation("test_code", "post-1")

    def provide_thread():
        while not emitter.confirmation_pending:
            time.sleep(0.01)
        emitter.provide_confirmation(True)

    t1 = threading.Thread(target=request_thread)
    t2 = threading.Thread(target=provide_thread)

    t1.start()
    t2.start()

    t1.join(timeout=2)
    t2.join(timeout=2)

    request_events = [e for e in events_captured if e.t == PostEventType.post_confirmation_request]
    response_events = [e for e in events_captured if e.t == PostEventType.post_confirmation_response]

    assert len(request_events) == 1
    assert request_events[0].msg == "test_code"
    assert request_events[0].extra["code"] == "test_code"

    assert len(response_events) == 1
    assert response_events[0].msg == "approved"
    assert response_events[0].extra["approved"] is True


def test_confirmation_state_cleared_after_response():
    emitter = SessionEventEmitter()
    emitter.start_round("test-round-1")
    handler = MockConfirmationHandler()
    emitter.confirmation_handler = handler

    def request_thread():
        emitter.request_code_confirmation("code1", "post-1")

    def provide_thread():
        while not emitter.confirmation_pending:
            time.sleep(0.01)
        emitter.provide_confirmation(True)

    t1 = threading.Thread(target=request_thread)
    t2 = threading.Thread(target=provide_thread)

    t1.start()
    t2.start()

    t1.join(timeout=2)
    t2.join(timeout=2)

    assert not emitter.confirmation_pending
    assert emitter.pending_confirmation_code is None
