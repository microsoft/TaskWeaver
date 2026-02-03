"""
Background context compaction for long conversations.

This module provides non-blocking compression of conversation history,
running in a background thread to avoid blocking user interaction.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, List, Optional, Protocol

from taskweaver.llm.util import ChatMessageType, format_chat_message
from taskweaver.utils import read_yaml

if TYPE_CHECKING:
    from taskweaver.llm import LLMApi
    from taskweaver.memory.round import Round


@dataclass
class CompactedMessage:
    """Single compacted message representing summarized conversation history.

    Attributes:
        start_index: First round index (1-based, typically always 1)
        end_index: Last compacted round index (1-based, inclusive)
        summary: LLM-generated summary of the compacted rounds
    """

    start_index: int
    end_index: int
    summary: str

    def to_system_message(self) -> str:
        """Format as a system message for inclusion in prompts."""
        return f"[Conversation History Summary (Rounds {self.start_index}-{self.end_index})]\n" f"{self.summary}"


class CompactionProvider(Protocol):
    """Interface that compactors implement for Memory integration."""

    def get_compaction(self) -> Optional[CompactedMessage]:
        """Returns current compaction if available."""
        ...

    def notify_rounds_changed(self) -> None:
        """Called when rounds change, may trigger background compaction."""
        ...


@dataclass
class CompactorConfig:
    """Configuration for ContextCompactor.

    Attributes:
        threshold: Trigger compaction when uncompacted rounds reach this count
        retain_recent: Keep last N rounds uncompacted
        prompt_template_path: Path to YAML file with compaction prompt
        enabled: Whether compaction is enabled
    """

    threshold: int = 10
    retain_recent: int = 3
    prompt_template_path: str = ""
    enabled: bool = True


class ContextCompactor:
    """Background compactor using a simple worker thread model.

    Design:
        - Single daemon thread processes compaction requests
        - notify_rounds_changed() is non-blocking, just signals the worker
        - Worker thread checks if compaction is needed and performs it
        - No lock needed: worker writes complete immutable objects, main thread reads

    The compactor only considers role-specific rounds (via rounds_getter),
    not the entire conversation history.
    """

    def __init__(
        self,
        config: CompactorConfig,
        llm_api: "LLMApi",
        rounds_getter: Callable[[], List["Round"]],
        logger: Optional[Callable[[str], None]] = None,
        llm_alias: str = "",
    ):
        self.config = config
        self.llm_api = llm_api
        self.rounds_getter = rounds_getter
        self.logger = logger or (lambda msg: None)
        self.llm_alias = llm_alias

        self._compacted_queue: List[CompactedMessage] = []

        self._worker: Optional[threading.Thread] = None
        self._shutdown = threading.Event()
        self._work_available = threading.Event()

        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        if not self.config.prompt_template_path:
            return self._default_prompt_template()

        try:
            data = read_yaml(self.config.prompt_template_path)
            return data.get("content", self._default_prompt_template())
        except Exception:
            return self._default_prompt_template()

    def _default_prompt_template(self) -> str:
        return """Summarize the following conversation history concisely.
Focus on: key decisions made, important information exchanged, and current state.
Preserve any critical details that would be needed to continue the conversation.

## Previous summary
{PREVIOUS_SUMMARY}

## Conversation to summarize
{content}

Provide a clear, structured summary:"""

    def start(self) -> None:
        """Start the background worker thread. Safe to call multiple times."""
        if not self.config.enabled:
            return

        if self._worker is not None:
            return
        self._shutdown.clear()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        self.logger("ContextCompactor: Worker thread started")

    def stop(self) -> None:
        """Stop the background worker thread gracefully."""
        self._shutdown.set()
        self._work_available.set()
        if self._worker is not None:
            self._worker.join(timeout=5)
            self._worker = None
        self.logger("ContextCompactor: Worker thread stopped")

    def get_compaction(self) -> Optional[CompactedMessage]:
        return self._compacted_queue[-1] if self._compacted_queue else None

    def notify_rounds_changed(self) -> None:
        """Signal that rounds have changed. Non-blocking."""
        if not self.config.enabled:
            return
        self._work_available.set()

    def _worker_loop(self) -> None:
        while not self._shutdown.is_set():
            self._work_available.wait()
            self._work_available.clear()

            if self._shutdown.is_set():
                break

            self._try_compact()

    def _try_compact(self) -> None:
        try:
            rounds = self.rounds_getter()
            total = len(rounds)

            if total == 0:
                return

            compacted = self.get_compaction()
            compacted_end = compacted.end_index if compacted else 0

            uncompacted_count = total - compacted_end

            if uncompacted_count < self.config.threshold:
                return

            new_end = total - self.config.retain_recent
            if new_end <= 0 or compacted_end >= new_end:
                return

            self.logger(
                f"ContextCompactor: Compacting rounds 1-{new_end} "
                f"(uncompacted={uncompacted_count}, threshold={self.config.threshold})",
            )

            self._do_compaction(rounds, new_end)

        except Exception as e:
            self.logger(f"ContextCompactor: Compaction failed: {e}")

    def _do_compaction(self, rounds: List["Round"], new_end: int) -> None:
        prev_compacted = self.get_compaction()

        previous_summary = "None"
        start_from = 0
        if prev_compacted:
            previous_summary = prev_compacted.summary
            start_from = prev_compacted.end_index

        content_parts: List[str] = []
        for i in range(start_from, new_end):
            round_obj = rounds[i]
            round_num = i + 1
            content_parts.append(f"\n--- Round {round_num} ---")
            content_parts.append(f"User Query: {round_obj.user_query}")

            for post in round_obj.post_list:
                msg_preview = post.message[:1024] + "..." if len(post.message) > 1024 else post.message
                content_parts.append(f"  {post.send_from} -> {post.send_to}: {msg_preview}")

        content = "\n".join(content_parts)

        summary = self._call_llm_for_summary(content, previous_summary)

        if not summary or not summary.strip():
            raise ValueError("LLM returned empty summary")

        new_compacted = CompactedMessage(
            start_index=1,
            end_index=new_end,
            summary=summary,
        )

        self._compacted_queue.append(new_compacted)

        self.logger(f"ContextCompactor: Compaction complete (rounds 1-{new_end})")

    def _call_llm_for_summary(self, content: str, previous_summary: str) -> str:
        prompt = self._prompt_template.format(content=content, PREVIOUS_SUMMARY=previous_summary)

        messages: List[ChatMessageType] = [
            format_chat_message("system", "You are a helpful assistant that summarizes conversations."),
            format_chat_message("user", prompt),
        ]

        response = self.llm_api.chat_completion(
            messages=messages,
            stream=False,
            temperature=0.3,
            llm_alias=self.llm_alias if self.llm_alias else None,
        )

        raw_content = response.get("content", "")
        if isinstance(raw_content, str):
            return raw_content
        return ""
