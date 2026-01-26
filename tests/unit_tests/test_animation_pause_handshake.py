"""Tests for the animation pause handshake pattern in TaskWeaverRoundUpdater.

The handshake uses two events:
- pause_animation: Main thread requests animation to pause
- animation_paused: Animation thread acknowledges it has paused
"""

import threading
import time


class MockAnimationPauseHandshake:
    """Minimal implementation of the handshake pattern for testing."""

    def __init__(self):
        self.pause_animation = threading.Event()
        self.animation_paused = threading.Event()
        self.animation_paused.set()  # Initially paused (not running yet)

        self.exit_event = threading.Event()
        self.update_cond = threading.Condition()

        # Track what animation thread does
        self.output_count = 0
        self.output_log = []

    def animation_thread_loop(self):
        """Simulates the animation thread loop."""
        while not self.exit_event.is_set():
            # Check pause at START of loop
            if self.pause_animation.is_set():
                self.animation_paused.set()
                while self.pause_animation.is_set():
                    if self.exit_event.is_set():
                        return
                    with self.update_cond:
                        self.update_cond.wait(0.01)
                continue

            self.animation_paused.clear()

            # Simulate output
            self.output_count += 1
            self.output_log.append(f"output-{self.output_count}")

            with self.update_cond:
                self.update_cond.wait(0.05)

    def request_pause(self, timeout: float = 1.0) -> bool:
        """Request animation to pause and wait for acknowledgment."""
        self.pause_animation.set()
        return self.animation_paused.wait(timeout=timeout)

    def release_pause(self):
        """Release the pause and allow animation to resume."""
        self.animation_paused.clear()
        self.pause_animation.clear()

    def stop(self):
        """Stop the animation thread."""
        self.exit_event.set()
        with self.update_cond:
            self.update_cond.notify_all()


def test_handshake_pauses_animation():
    """Animation should stop outputting when pause is requested."""
    handler = MockAnimationPauseHandshake()

    t = threading.Thread(target=handler.animation_thread_loop, daemon=True)
    t.start()

    # Let animation run for a bit
    time.sleep(0.1)
    count_before_pause = handler.output_count
    assert count_before_pause > 0, "Animation should have produced output"

    # Request pause
    assert handler.request_pause(), "Pause should be acknowledged"

    # Record count and wait
    count_at_pause = handler.output_count
    time.sleep(0.1)
    count_after_wait = handler.output_count

    # No new output during pause
    assert count_after_wait == count_at_pause, "Animation should not output while paused"

    # Release and verify animation resumes
    handler.release_pause()
    time.sleep(0.1)
    count_after_release = handler.output_count

    assert count_after_release > count_at_pause, "Animation should resume after release"

    handler.stop()
    t.join(timeout=1)


def test_handshake_blocks_until_acknowledged():
    """request_pause should block until animation acknowledges."""
    handler = MockAnimationPauseHandshake()
    handler.animation_paused.clear()  # Simulate animation running

    acknowledged = threading.Event()

    def delayed_acknowledge():
        time.sleep(0.1)
        handler.animation_paused.set()
        acknowledged.set()

    t = threading.Thread(target=delayed_acknowledge, daemon=True)
    t.start()

    start = time.time()
    result = handler.request_pause(timeout=1.0)
    elapsed = time.time() - start

    assert result is True
    assert elapsed >= 0.1, "Should have waited for acknowledgment"
    assert acknowledged.is_set()

    t.join(timeout=1)


def test_handshake_timeout():
    """request_pause should timeout if animation doesn't acknowledge."""
    handler = MockAnimationPauseHandshake()
    handler.animation_paused.clear()  # Simulate animation that never acknowledges

    start = time.time()
    result = handler.request_pause(timeout=0.1)
    elapsed = time.time() - start

    # Event.wait returns False on timeout
    assert result is False
    assert elapsed >= 0.1


def test_handshake_multiple_pause_resume_cycles():
    """Handshake should work correctly across multiple pause/resume cycles."""
    handler = MockAnimationPauseHandshake()

    t = threading.Thread(target=handler.animation_thread_loop, daemon=True)
    t.start()

    for i in range(3):
        # Let animation run
        time.sleep(0.05)
        handler.output_count

        # Pause
        assert handler.request_pause(), f"Cycle {i}: Pause should be acknowledged"
        count_at_pause = handler.output_count
        time.sleep(0.05)
        assert handler.output_count == count_at_pause, f"Cycle {i}: Should not output while paused"

        # Resume
        handler.release_pause()
        time.sleep(0.05)
        assert handler.output_count > count_at_pause, f"Cycle {i}: Should resume after release"

    handler.stop()
    t.join(timeout=1)


def test_handshake_exit_during_pause():
    """Animation thread should exit cleanly even while paused."""
    handler = MockAnimationPauseHandshake()

    t = threading.Thread(target=handler.animation_thread_loop, daemon=True)
    t.start()

    # Pause animation
    time.sleep(0.05)
    handler.request_pause()

    # Exit while paused
    handler.stop()

    # Thread should exit
    t.join(timeout=1)
    assert not t.is_alive(), "Thread should have exited"


def test_handshake_no_output_race():
    """Verify no output occurs between pause request and acknowledgment."""
    handler = MockAnimationPauseHandshake()

    t = threading.Thread(target=handler.animation_thread_loop, daemon=True)
    t.start()

    # Let it run
    time.sleep(0.05)

    # Pause and immediately record
    handler.pause_animation.set()
    handler.animation_paused.wait(timeout=1.0)
    count_at_ack = handler.output_count

    # Wait and verify no change
    time.sleep(0.1)
    assert handler.output_count == count_at_ack, "No output should occur after acknowledgment"

    handler.release_pause()
    handler.stop()
    t.join(timeout=1)


def test_animation_paused_initially_set():
    """animation_paused should be set initially (before animation starts)."""
    handler = MockAnimationPauseHandshake()
    assert handler.animation_paused.is_set(), "Should be paused initially"


def test_animation_paused_cleared_when_running():
    """animation_paused should be cleared when animation is actively running."""
    handler = MockAnimationPauseHandshake()

    t = threading.Thread(target=handler.animation_thread_loop, daemon=True)
    t.start()

    # Wait for animation to start running
    time.sleep(0.1)

    # Should be cleared (running)
    assert not handler.animation_paused.is_set(), "Should be cleared when running"

    handler.stop()
    t.join(timeout=1)
