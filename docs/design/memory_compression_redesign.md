# Memory Compression Redesign

**Status:** Phase 2 Design Finalized  
**Author:** AI Assistant  
**Date:** 2026-01-29  
**Last Updated:** 2026-01-30  
**Reviewers:** [Pending]

## Executive Summary

This document describes a redesign of TaskWeaver's memory compression system based on these principles:

1. **Background Processing** - Compaction runs in a separate thread, never blocking user interaction
2. **Non-invasive** - Memory stores raw rounds unchanged; compaction is a separate view layer
3. **Per-Agent** - Each agent can have its own compactor with customized prompts
4. **Single Compacted Message** - Only one compacted message maintained, updated incrementally

---

## Current System Analysis

### How It Works Today

The current `RoundCompressor` in `taskweaver/memory/compression.py`:

1. Triggers when `remaining_rounds >= rounds_to_compress + rounds_to_retain`
2. Calls LLM **synchronously** during `compose_prompt()` to summarize older rounds
3. Replaces older rounds with summary text inline in the prompt
4. Summary accumulates over time (`previous_summary` state)

### Problems with Current Approach

| Issue | Impact |
|-------|--------|
| **Synchronous blocking** | LLM summarization call blocks the conversation flow |
| **Coupled to agent** | Compression logic embedded inside agent's compose_prompt |
| **Per-role duplication** | Both Planner and CodeGenerator have separate compression logic |
| **No customization** | Same compression for all agents |

---

## Proposed Architecture

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Background** | Compaction runs in separate thread, triggered by round count |
| **Non-invasive** | Memory.conversation.rounds never modified |
| **Hookable** | Memory provides minimal hooks; compactor is external |
| **Per-agent** | Each agent registers its own compactor with custom prompt |
| **Single message** | One compacted message per agent, incrementally updated |

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Memory (Core)                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  conversation.rounds: List[Round]     ← Raw data, NEVER modified    │
│                                                                      │
│  Hooks (minimal additions):                                          │
│  - on_round_added(callback)           ← Notify when round added     │
│  - register_compaction_provider(role, provider)                      │
│  - get_role_rounds(role) → (rounds, compaction)                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
         │                                         │
         │ notifies                                │ returns
         ▼                                         ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│   ContextCompactor      │              │   Agent                 │
│   (Background Thread)   │              │                         │
├─────────────────────────┤              ├─────────────────────────┤
│                         │              │                         │
│ Watches round count     │              │ rounds, compaction =    │
│ Triggers compaction     │   provides   │   memory.get_role_rounds│
│ Maintains ONE compacted │ ──────────►  │                         │
│   message per agent     │  compaction  │ Assembles view:         │
│ Custom prompt per agent │              │   [compacted] + rounds  │
│                         │              │                         │
└─────────────────────────┘              └─────────────────────────┘
```

### Compaction Flow (Example)

```
Timeline:
─────────────────────────────────────────────────────────────────────────────

State 1: Memory has rounds [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
         Threshold = 7, Retain = 3
         
         Compaction triggered:
         - Input to LLM: rounds [1..7]
         - Output: CompactedMessage(start=1, end=7, summary="...")
         
         Agent sees: [CompactedMessage(1..7)] + [8, 9, 10]

─────────────────────────────────────────────────────────────────────────────

State 2: Memory has rounds [1..15]
         
         Compaction triggered again:
         - Input to LLM: CompactedMessage(1..7) + rounds [8..12]
         - Output: CompactedMessage(start=1, end=12, summary="...")
         
         Agent sees: [CompactedMessage(1..12)] + [13, 14, 15]
         
         Note: Previous compacted message is REPLACED, not accumulated

─────────────────────────────────────────────────────────────────────────────

State 3: Memory has rounds [1..20]
         
         Compaction triggered again:
         - Input to LLM: CompactedMessage(1..12) + rounds [13..17]
         - Output: CompactedMessage(start=1, end=17, summary="...")
         
         Agent sees: [CompactedMessage(1..17)] + [18, 19, 20]

─────────────────────────────────────────────────────────────────────────────
```

---

## Detailed Design

### 1. Data Structures

```python
from dataclasses import dataclass
from typing import List, Optional, Protocol, Callable


@dataclass
class CompactedMessage:
    """Single compacted message representing summarized conversation history."""
    start_index: int      # Always 1 (first round)
    end_index: int        # Last compacted round index (inclusive)
    summary: str          # LLM-generated summary
    
    def to_system_message(self) -> str:
        return f"[Conversation History Summary (Rounds {self.start_index}-{self.end_index})]\n{self.summary}"


class CompactionProvider(Protocol):
    """Interface that compactor implements. Memory calls this."""
    
    def get_compaction(self) -> Optional[CompactedMessage]:
        """Returns current compaction if available."""
        ...
    
    def notify_rounds_changed(self, total_rounds: int) -> None:
        """Called when rounds change, may trigger background compaction."""
        ...
```

### 2. Memory Hooks

Minimal additions to `Memory` class:

```python
class Memory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.conversation = Conversation.init()
        # NEW: Hook infrastructure
        self._compaction_providers: Dict[str, CompactionProvider] = {}
        self._on_round_added_callbacks: List[Callable[[int], None]] = []
    
    # NEW: Register compactor for a role
    def register_compaction_provider(self, role: str, provider: CompactionProvider) -> None:
        self._compaction_providers[role] = provider
        # Also register for round-added notifications
        self._on_round_added_callbacks.append(provider.notify_rounds_changed)
    
    # MODIFIED: Notify callbacks when round added
    def create_round(self, user_query: str) -> Round:
        round = Round.create(user_query=user_query)
        self.conversation.add_round(round)
        # Notify all listeners
        total = len(self.conversation.rounds)
        for cb in self._on_round_added_callbacks:
            cb(total)
        return round
    
    # MODIFIED: Return both rounds and compaction
    def get_role_rounds(
        self, 
        role: str, 
        include_failure_rounds: bool = False,
    ) -> tuple[List[Round], Optional[CompactedMessage]]:
        """Returns (rounds, compaction). Agent assembles the final view."""
        rounds = self._filter_rounds_for_role(role, include_failure_rounds)
        compaction = None
        if role in self._compaction_providers:
            compaction = self._compaction_providers[role].get_compaction()
        return rounds, compaction
```

### 3. ContextCompactor

```python
import threading
from typing import List, Optional, Callable


@dataclass
class CompactorConfig:
    threshold: int = 10        # Trigger when total rounds > threshold
    retain_recent: int = 3     # Keep last N rounds uncompacted
    prompt_template_path: str = ""  # Customizable per-agent


class ContextCompactor:
    """Background compactor - one instance per agent."""
    
    def __init__(
        self, 
        config: CompactorConfig,
        llm_api: LLMApi,
        rounds_getter: Callable[[], List[Round]],  # Function to get current rounds
    ):
        self.config = config
        self.llm_api = llm_api
        self.rounds_getter = rounds_getter
        
        self._compacted: Optional[CompactedMessage] = None
        self._lock = threading.Lock()
        self._compacting = False
        self._stop_event = threading.Event()
        self._trigger_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start background compaction thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop background thread."""
        self._stop_event.set()
        self._trigger_event.set()
        if self._thread:
            self._thread.join(timeout=5)
    
    def get_compaction(self) -> Optional[CompactedMessage]:
        """Called by Memory - returns current compaction."""
        with self._lock:
            return self._compacted
    
    def notify_rounds_changed(self, total_rounds: int) -> None:
        """Called by Memory when round added."""
        with self._lock:
            if self._compacting:
                return
            # Check if compaction needed
            compacted_end = self._compacted.end_index if self._compacted else 0
            uncompacted_count = total_rounds - compacted_end
            if uncompacted_count > self.config.threshold:
                self._trigger_event.set()
    
    def _run(self) -> None:
        """Background thread loop."""
        while not self._stop_event.is_set():
            self._trigger_event.wait()
            self._trigger_event.clear()
            
            if self._stop_event.is_set():
                break
            
            with self._lock:
                if self._compacting:
                    continue
                self._compacting = True
            
            try:
                self._do_compaction()
            finally:
                with self._lock:
                    self._compacting = False
    
    def _do_compaction(self) -> None:
        """Perform compaction."""
        rounds = self.rounds_getter()
        total = len(rounds)
        
        # Calculate range to compact
        new_end = total - self.config.retain_recent
        if new_end <= 0:
            return
        
        # Build LLM input
        content_parts = []
        
        with self._lock:
            prev_compacted = self._compacted
        
        if prev_compacted:
            # Include previous summary
            content_parts.append(
                f"[Previous Summary (Rounds 1-{prev_compacted.end_index})]:\n"
                f"{prev_compacted.summary}"
            )
            start_from = prev_compacted.end_index  # 0-based index
        else:
            start_from = 0
        
        # Add new rounds to compact
        for i, r in enumerate(rounds[start_from:new_end], start=start_from + 1):
            content_parts.append(f"Round {i}: {r.user_query}")
            for post in r.post_list:
                content_parts.append(f"  {post.send_from} -> {post.send_to}: {post.message[:200]}")
        
        # Call LLM
        summary = self._call_llm_for_summary("\n\n".join(content_parts))
        
        # Update compacted message (replace previous)
        new_compacted = CompactedMessage(
            start_index=1,
            end_index=new_end,
            summary=summary,
        )
        
        with self._lock:
            self._compacted = new_compacted
    
    def _call_llm_for_summary(self, content: str) -> str:
        """Call LLM with customizable prompt."""
        # Load prompt template, format with content, call LLM
        # ... implementation ...
        pass
```

### 4. Agent Integration

```python
class Planner(Role):
    def __init__(self, ..., memory: Memory, llm_api: LLMApi):
        # Create and register compactor
        self.compactor = ContextCompactor(
            config=CompactorConfig(
                threshold=10,
                retain_recent=3,
                prompt_template_path="planner_compaction_prompt.yaml",
            ),
            llm_api=llm_api,
            rounds_getter=lambda: memory.conversation.rounds,
        )
        memory.register_compaction_provider(self.alias, self.compactor)
        self.compactor.start()
    
    def compose_prompt(self, memory: Memory) -> List[ChatMessageType]:
        rounds, compaction = memory.get_role_rounds(self.alias)
        
        messages = [self._system_prompt()]
        
        if compaction:
            # Add compacted history as system message
            messages.append(format_chat_message(
                role="system",
                message=compaction.to_system_message(),
            ))
            # Only format rounds after compaction
            rounds_to_format = rounds[compaction.end_index:]
        else:
            rounds_to_format = rounds
        
        messages.extend(self._format_rounds(rounds_to_format))
        return messages
```

---

## Configuration

```json
{
  "compaction.enabled": true,
  "compaction.threshold": 10,
  "compaction.retain_recent": 3,
  
  "planner.compaction_prompt_path": "planner_compaction_prompt.yaml",
  "code_interpreter.compaction_prompt_path": "code_interpreter_compaction_prompt.yaml"
}
```

### Per-Agent Prompt Customization

**planner_compaction_prompt.yaml:**
```yaml
content: |
  Summarize the following conversation history for a task planning agent.
  Focus on: task progress, decisions made, pending items.
  
  {content}
```

**code_interpreter_compaction_prompt.yaml:**
```yaml
content: |
  Summarize the following conversation history for a code execution agent.
  Focus on: variables created, data transformations, code execution results.
  
  {content}
```

---

## Migration Plan

### Phase 1: Infrastructure ✅ COMPLETE (Partial)
- ✅ `RoundArchiver` service (archival approach - may repurpose or deprecate)
- ✅ `ArchiveRetriever` role
- ✅ Unit tests

### Phase 2: Background Compaction (This Design)
- [ ] `CompactedMessage` data structure
- [ ] `CompactionProvider` protocol
- [ ] Memory hooks (`register_compaction_provider`, modified `get_role_rounds`)
- [ ] `ContextCompactor` class with background thread
- [ ] Integration with Planner
- [ ] Integration with CodeInterpreter
- [ ] Per-agent prompt templates
- [ ] Unit tests

### Phase 3: Deprecation
- [ ] Mark `RoundCompressor` as deprecated
- [ ] Migration guide for existing users

---

## Comparison: Old vs New

| Aspect | Old (RoundCompressor) | New (ContextCompactor) |
|--------|----------------------|------------------------|
| **Execution** | Synchronous in compose_prompt | Background thread |
| **Blocking** | Blocks user interaction | Non-blocking |
| **Memory modification** | Mutates round list | Memory unchanged |
| **Per-agent** | Duplicated logic | Shared component, custom prompts |
| **Compacted state** | Accumulating summary string | Single CompactedMessage with indices |
| **Re-compaction** | N/A | Previous message + new rounds |

---

## Key Design Decisions

1. **Memory stays clean**: `conversation.rounds` is never modified. Compaction is a view layer.

2. **Hooks are minimal**: Only `on_round_added`, `register_compaction_provider`, and modified return for `get_role_rounds`.

3. **Agent assembles view**: Agent receives `(rounds, compaction)` and decides how to combine them.

4. **Single compacted message**: Only one `CompactedMessage` per agent, replaced on each compaction cycle.

5. **Incremental compaction**: New compaction takes previous compacted message + new rounds as input.

6. **Index-based assembly**: `CompactedMessage.end_index` tells agent where compaction ends; agent uses `rounds[end_index:]` for remaining rounds.
