import threading
import time
from dataclasses import dataclass
from typing import List
from unittest.mock import MagicMock

from taskweaver.memory.compaction import CompactedMessage, CompactorConfig, ContextCompactor


@dataclass
class MockPost:
    send_from: str
    send_to: str
    message: str


@dataclass
class MockRound:
    user_query: str
    post_list: List[MockPost]


def create_mock_rounds(n: int) -> List[MockRound]:
    rounds = []
    for i in range(n):
        posts = [
            MockPost("User", "Planner", f"Query {i + 1}"),
            MockPost("Planner", "User", f"Response {i + 1}"),
        ]
        rounds.append(MockRound(user_query=f"Question {i + 1}", post_list=posts))
    return rounds


class TestCompactedMessage:
    def test_to_system_message(self):
        msg = CompactedMessage(start_index=1, end_index=5, summary="Test summary")
        result = msg.to_system_message()
        assert "Rounds 1-5" in result
        assert "Test summary" in result


class TestCompactorConfig:
    def test_default_values(self):
        config = CompactorConfig()
        assert config.threshold == 10
        assert config.retain_recent == 3
        assert config.prompt_template_path == ""
        assert config.enabled is True

    def test_custom_values(self):
        config = CompactorConfig(threshold=5, retain_recent=2, enabled=False)
        assert config.threshold == 5
        assert config.retain_recent == 2
        assert config.enabled is False


class TestContextCompactorInit:
    def test_init_with_defaults(self):
        config = CompactorConfig()
        compactor = ContextCompactor(
            config=config,
            llm_api=MagicMock(),
            rounds_getter=lambda: [],
        )
        assert compactor.get_compaction() is None
        assert compactor._worker is None

    def test_init_with_custom_logger(self):
        logs = []
        config = CompactorConfig()
        compactor = ContextCompactor(
            config=config,
            llm_api=MagicMock(),
            rounds_getter=lambda: [],
            logger=lambda msg: logs.append(msg),
        )
        compactor.logger("test message")
        assert "test message" in logs


class TestContextCompactorStart:
    def test_start_creates_worker(self):
        config = CompactorConfig(enabled=True)
        compactor = ContextCompactor(
            config=config,
            llm_api=MagicMock(),
            rounds_getter=lambda: [],
        )

        compactor.start()
        assert compactor._worker is not None
        assert compactor._worker.is_alive()

        compactor.stop()

    def test_start_is_idempotent(self):
        config = CompactorConfig(enabled=True)
        compactor = ContextCompactor(
            config=config,
            llm_api=MagicMock(),
            rounds_getter=lambda: [],
        )

        compactor.start()
        first_worker = compactor._worker

        compactor.start()
        assert compactor._worker is first_worker

        compactor.stop()

    def test_start_disabled(self):
        config = CompactorConfig(enabled=False)
        compactor = ContextCompactor(
            config=config,
            llm_api=MagicMock(),
            rounds_getter=lambda: [],
        )

        compactor.start()
        assert compactor._worker is None


class TestContextCompactorCompaction:
    def test_basic_compaction(self):
        rounds = create_mock_rounds(5)
        config = CompactorConfig(threshold=3, retain_recent=1, enabled=True)

        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = {"content": "Test summary"}

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.2)

        result = compactor.get_compaction()
        assert result is not None
        assert result.start_index == 1
        assert result.end_index == 4
        assert result.summary == "Test summary"

        compactor.stop()

    def test_incremental_compaction(self):
        rounds = create_mock_rounds(5)
        config = CompactorConfig(threshold=3, retain_recent=1, enabled=True)

        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = {"content": "First summary"}

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.2)

        first_result = compactor.get_compaction()
        assert first_result.end_index == 4

        rounds.extend(create_mock_rounds(5))
        mock_llm.chat_completion.return_value = {"content": "Second summary"}

        compactor.notify_rounds_changed()
        time.sleep(0.2)

        second_result = compactor.get_compaction()
        assert second_result.end_index == 9
        assert second_result.summary == "Second summary"

        compactor.stop()

    def test_no_compaction_below_threshold(self):
        rounds = create_mock_rounds(5)
        config = CompactorConfig(threshold=10, retain_recent=2, enabled=True)

        mock_llm = MagicMock()

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.2)

        assert compactor.get_compaction() is None
        mock_llm.chat_completion.assert_not_called()

        compactor.stop()

    def test_compaction_at_exact_threshold(self):
        rounds = create_mock_rounds(10)
        config = CompactorConfig(threshold=10, retain_recent=2, enabled=True)

        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = {"content": "Summary"}

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.2)

        result = compactor.get_compaction()
        assert result is not None
        assert result.end_index == 8

        compactor.stop()

    def test_compaction_failure_does_not_update_state(self):
        rounds = create_mock_rounds(10)
        config = CompactorConfig(threshold=5, retain_recent=2, enabled=True)

        mock_llm = MagicMock()
        mock_llm.chat_completion.side_effect = Exception("LLM error")

        logs = []
        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
            logger=lambda msg: logs.append(msg),
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.2)

        assert compactor.get_compaction() is None
        assert any("failed" in log.lower() for log in logs)

        compactor.stop()

    def test_empty_summary_raises_error(self):
        rounds = create_mock_rounds(10)
        config = CompactorConfig(threshold=5, retain_recent=2, enabled=True)

        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = {"content": ""}

        logs = []
        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
            logger=lambda msg: logs.append(msg),
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.2)

        assert compactor.get_compaction() is None
        assert any("failed" in log.lower() for log in logs)

        compactor.stop()

    def test_no_compaction_when_disabled(self):
        rounds = create_mock_rounds(20)
        config = CompactorConfig(threshold=5, enabled=False)

        mock_llm = MagicMock()

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.1)

        assert compactor.get_compaction() is None
        mock_llm.chat_completion.assert_not_called()


class TestContextCompactorMultipleNotifications:
    def test_multiple_rapid_notifications(self):
        rounds_list = [create_mock_rounds(10)]
        config = CompactorConfig(threshold=3, retain_recent=1, enabled=True)

        call_count = [0]
        mock_llm = MagicMock()

        def counting_llm(*args, **kwargs):
            call_count[0] += 1
            time.sleep(0.1)
            return {"content": f"Summary {call_count[0]}"}

        mock_llm.chat_completion.side_effect = counting_llm

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds_list[0],
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.05)

        rounds_list[0] = create_mock_rounds(20)
        compactor.notify_rounds_changed()

        time.sleep(0.5)

        assert call_count[0] >= 1
        assert compactor.get_compaction() is not None

        compactor.stop()


class TestContextCompactorThreadSafety:
    def test_get_compaction_thread_safe(self):
        config = CompactorConfig(threshold=3, retain_recent=1, enabled=True)
        mock_llm = MagicMock()
        mock_llm.chat_completion.return_value = {"content": "Summary"}

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: create_mock_rounds(10),
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.2)

        results = []
        errors = []

        def reader():
            for _ in range(100):
                try:
                    results.append(compactor.get_compaction())
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        compactor.stop()


class TestContextCompactorStop:
    def test_stop_gracefully(self):
        config = CompactorConfig(enabled=True)
        compactor = ContextCompactor(
            config=config,
            llm_api=MagicMock(),
            rounds_getter=lambda: [],
        )

        compactor.start()
        worker = compactor._worker
        assert worker.is_alive()

        compactor.stop()
        time.sleep(0.1)
        assert compactor._worker is None

    def test_stop_during_compaction(self):
        rounds = create_mock_rounds(10)
        config = CompactorConfig(threshold=3, retain_recent=1, enabled=True)

        mock_llm = MagicMock()

        def slow_llm(*args, **kwargs):
            time.sleep(1)
            return {"content": "Summary"}

        mock_llm.chat_completion.side_effect = slow_llm

        compactor = ContextCompactor(
            config=config,
            llm_api=mock_llm,
            rounds_getter=lambda: rounds,
        )

        compactor.start()
        compactor.notify_rounds_changed()
        time.sleep(0.1)

        compactor.stop()
        assert compactor._worker is None
