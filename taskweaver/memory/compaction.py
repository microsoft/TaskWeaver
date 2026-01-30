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
        threshold: Trigger compaction when uncompacted rounds exceed this
        retain_recent: Keep last N rounds uncompacted
        prompt_template_path: Path to YAML file with compaction prompt
        enabled: Whether compaction is enabled
    """

    threshold: int = 10
    retain_recent: int = 3
    prompt_template_path: str = ""
    enabled: bool = True


class ContextCompactor:
    """Background compactor - maintains one compacted message per agent.

    This compactor runs in a daemon thread, triggered when round count exceeds
    threshold. It incrementally compacts conversation history by combining
    the previous compaction with new rounds.

    Thread safety:
        - Only one thread is ever created (singleton pattern for thread)
        - Triggers during active compaction are queued via _pending_trigger flag
        - All shared state access is protected by _lock
    """

    def __init__(
        self,
        config: CompactorConfig,
        llm_api: "LLMApi",
        rounds_getter: Callable[[], List["Round"]],
        logger: Optional[Callable[[str], None]] = None,
    ):
        self.config = config
        self.llm_api = llm_api
        self.rounds_getter = rounds_getter
        self.logger = logger or (lambda msg: None)

        self._compacted: Optional[CompactedMessage] = None
        self._lock = threading.Lock()
        self._compacting = False
        self._pending_trigger = False
        self._started = False
        self._stop_event = threading.Event()
        self._trigger_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
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
        """Start background compaction thread. Safe to call multiple times."""
        if not self.config.enabled:
            return

        with self._lock:
            if self._started:
                return
            self._started = True

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.logger("ContextCompactor: Background thread started")

    def stop(self) -> None:
        """Stop background thread gracefully."""
        self._stop_event.set()
        self._trigger_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self.logger("ContextCompactor: Background thread stopped")

    def get_compaction(self) -> Optional[CompactedMessage]:
        """Get current compaction (thread-safe)."""
        with self._lock:
            return self._compacted

    def notify_rounds_changed(self) -> None:
        """Called by Memory when rounds change."""
        if not self.config.enabled:
            return

        with self._lock:
            role_rounds = len(self.rounds_getter())
            compacted_end = self._compacted.end_index if self._compacted else 0
            uncompacted_count = role_rounds - compacted_end

            if uncompacted_count < self.config.threshold:
                return

            if self._compacting:
                self._pending_trigger = True
                self.logger("ContextCompactor: Compaction in progress, queued trigger")
                return

            self.logger(
                f"ContextCompactor: Triggering compaction "
                f"(uncompacted={uncompacted_count}, threshold={self.config.threshold})",
            )
            self._trigger_event.set()

    def _run(self) -> None:
        """Background thread loop."""
        while not self._stop_event.is_set():
            self._trigger_event.wait()
            self._trigger_event.clear()

            if self._stop_event.is_set():
                break

            self._process_compaction()

    def _process_compaction(self) -> None:
        """Process compaction with pending trigger handling."""
        with self._lock:
            if self._compacting:
                return
            self._compacting = True
            self._pending_trigger = False

        try:
            self._do_compaction()
        except Exception as e:
            self.logger(f"ContextCompactor: Compaction failed: {e}")
        finally:
            with self._lock:
                self._compacting = False
                if self._pending_trigger:
                    self._pending_trigger = False
                    self._trigger_event.set()

    def _do_compaction(self) -> None:
        """Perform the actual compaction."""
        rounds = self.rounds_getter()
        total = len(rounds)

        if total == 0:
            return

        new_end = total - self.config.retain_recent
        if new_end <= 0:
            return

        with self._lock:
            prev_compacted = self._compacted

        if prev_compacted and prev_compacted.end_index >= new_end:
            return

        previous_summary = "None"
        start_from = 0
        if prev_compacted:
            previous_summary = prev_compacted.summary
            start_from = prev_compacted.end_index

        content_parts = []
        for i in range(start_from, new_end):
            round_obj = rounds[i]
            round_num = i + 1
            content_parts.append(f"\n--- Round {round_num} ---")
            content_parts.append(f"User Query: {round_obj.user_query}")

            for post in round_obj.post_list:
                msg_preview = post.message[:500] + "..." if len(post.message) > 500 else post.message
                content_parts.append(f"  {post.send_from} -> {post.send_to}: {msg_preview}")

        content = "\n".join(content_parts)
        self.logger(f"ContextCompactor: Compacting rounds 1-{new_end}")

        summary = self._call_llm_for_summary(content, previous_summary)

        if not summary or not summary.strip():
            raise ValueError("LLM returned empty summary")

        new_compacted = CompactedMessage(
            start_index=1,
            end_index=new_end,
            summary=summary,
        )

        with self._lock:
            self._compacted = new_compacted

        self.logger(f"ContextCompactor: Compaction complete (rounds 1-{new_end})")

    def _call_llm_for_summary(self, content: str, previous_summary: str) -> str:
        """Call LLM to generate summary."""
        prompt = self._prompt_template.format(content=content, PREVIOUS_SUMMARY=previous_summary)

        messages: List[ChatMessageType] = [
            format_chat_message("system", "You are a helpful assistant that summarizes conversations."),
            format_chat_message("user", prompt),
        ]

        response = self.llm_api.chat_completion(
            messages=messages,
            stream=False,
            temperature=0.3,
        )

        raw_content = response.get("content", "")
        if isinstance(raw_content, str):
            return raw_content
        return ""
