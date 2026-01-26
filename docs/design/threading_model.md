# TaskWeaver Threading Model - Design Document

**Generated:** 2026-01-26 | **Author:** AI Agent | **Status:** Documentation

## Overview

TaskWeaver employs a **dual-thread architecture** for console-based user interaction. When a user submits a request, the main process spawns two threads:

1. **Execution Thread** - Runs the actual task processing (LLM calls, code execution)
2. **Animation Thread** - Handles real-time console display with status updates and animations

These threads communicate via an **event-driven architecture** using a shared update queue protected by threading primitives.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Main Thread                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  TaskWeaverChatApp.run()                                            │    │
│  │    └── _handle_message(input)                                       │    │
│  │          └── TaskWeaverRoundUpdater.handle_message()                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│  ┌─────────────────────────────┐   ┌─────────────────────────────┐         │
│  │    Execution Thread (t_ex)  │   │   Animation Thread (t_ui)   │         │
│  │                             │   │                             │         │
│  │  session.send_message()     │   │  _animate_thread()          │         │
│  │    ├── Planner.reply()      │   │    ├── Process updates      │         │
│  │    ├── CodeInterpreter      │   │    ├── Render status bar    │         │
│  │    │     .reply()           │   │    ├── Display messages     │         │
│  │    └── Event emission ──────┼───┼──► └── Animate spinner      │         │
│  │                             │   │                             │         │
│  └─────────────────────────────┘   └─────────────────────────────┘         │
│                    │                               │                        │
│                    └───────────────┬───────────────┘                        │
│                                    ▼                                         │
│                         exit_event.set()                                     │
│                         Main thread joins                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. TaskWeaverRoundUpdater (chat/console/chat.py)

The central coordinator that manages both threads and handles events.

```python
class TaskWeaverRoundUpdater(SessionEventHandlerBase):
    def __init__(self):
        self.exit_event = threading.Event()      # Signals completion
        self.update_cond = threading.Condition() # Wakes animation thread
        self.lock = threading.Lock()             # Protects shared state
        
        self.pending_updates: List[Tuple[str, str]] = []  # Event queue
        self.result: Optional[str] = None
```

### 2. Thread Spawning (handle_message)

```python
def handle_message(self, session, message, files):
    def execution_thread():
        try:
            round = session.send_message(message, event_handler=self, files=files)
            last_post = round.post_list[-1]
            if last_post.send_to == "User":
                self.result = last_post.message
        finally:
            self.exit_event.set()
            with self.update_cond:
                self.update_cond.notify_all()

    t_ui = threading.Thread(target=lambda: self._animate_thread(), daemon=True)
    t_ex = threading.Thread(target=execution_thread, daemon=True)

    t_ui.start()
    t_ex.start()
    
    # Main thread waits for completion
    while True:
        self.exit_event.wait(0.1)
        if self.exit_event.is_set():
            break
```

### 3. Event Flow

```
┌──────────────────┐    emit()    ┌──────────────────┐   handle()   ┌──────────────────┐
│  PostEventProxy  │─────────────►│ SessionEventEmitter│────────────►│TaskWeaverRoundUpdater│
└──────────────────┘              └──────────────────┘              └──────────────────┘
                                                                              │
                                                                              ▼
                                                                    ┌──────────────────┐
                                                                    │  pending_updates │
                                                                    │     (queue)      │
                                                                    └──────────────────┘
                                                                              │
                                                                              ▼
                                                                    ┌──────────────────┐
                                                                    │ Animation Thread │
                                                                    │   (consumer)     │
                                                                    └──────────────────┘
```

## Event Types

### Session Events (EventScope.session)
| Event | Description |
|-------|-------------|
| `session_start` | Session initialization |
| `session_end` | Session termination |
| `session_new_round` | New conversation round |

### Round Events (EventScope.round)
| Event | Description |
|-------|-------------|
| `round_start` | User query processing begins |
| `round_end` | User query processing complete |
| `round_error` | Error during processing |
| `round_new_post` | New message in round |

### Post Events (EventScope.post)
| Event | Description |
|-------|-------------|
| `post_start` | Role begins generating response |
| `post_end` | Role finished response |
| `post_error` | Error in post generation |
| `post_status_update` | Status text change ("generating code", "executing") |
| `post_send_to_update` | Recipient change |
| `post_message_update` | Message content streaming |
| `post_attachment_update` | Attachment (code, plan, etc.) update |

## Animation Thread Details

The animation thread (`_animate_thread`) runs a continuous loop:

```python
def _animate_thread(self):
    while True:
        clear_line()
        
        # Process all pending updates atomically
        with self.lock:
            for action, opt in self.pending_updates:
                if action == "start_post":
                    # Display role header: ╭───< Planner >
                elif action == "end_post":
                    # Display completion: ╰──● sending to User
                elif action == "attachment_start":
                    # Begin attachment display
                elif action == "attachment_add":
                    # Append to current attachment
                elif action == "attachment_end":
                    # Finalize and render attachment
                elif action == "status_update":
                    # Update status message
            self.pending_updates.clear()
        
        if self.exit_event.is_set():
            break
        
        # Display animated status bar
        # " TaskWeaver ▶ [Planner] generating code <=💡=>"
        display_status_bar(role, status, get_ani_frame(counter))
        
        # Rate limit animation (~30Hz visual, 5Hz animation)
        with self.update_cond:
            self.update_cond.wait(0.2)
```

### Console Output Format

```
 ╭───< Planner >
 ├─► [init_plan] Analyze the user request...
 ├─► [plan] 1. Parse input data...
 ├──● The task involves processing the CSV file...
 ╰──● sending message to CodeInterpreter

 ╭───< CodeInterpreter >
 ├─► [reply_content] import pandas as pd...
 ├─► [verification] CORRECT
 ├─► [execution_status] SUCCESS
 ├──● [Execution result]...
 ╰──● sending message to Planner
```

## Synchronization Primitives

| Primitive | Purpose |
|-----------|---------|
| `threading.Lock` | Protects `pending_updates` queue during read/write |
| `threading.Event` | Signals execution completion (`exit_event`) |
| `threading.Condition` | Wakes animation thread when updates available |

### Critical Sections

1. **Event emission** (execution thread writes):
```python
with self.lock:
    self.pending_updates.append(("status_update", msg))
```

2. **Update processing** (animation thread reads):
```python
with self.lock:
    for action, opt in self.pending_updates:
        # Process...
    self.pending_updates.clear()
```

## Additional Threading: Stream Smoother

The LLM module (`llm/__init__.py`) uses a separate threading model for **LLM response streaming**:

```python
def _stream_smoother(self, stream_init):
    """
    Smooths LLM token streaming for better UX.
    
    Problem: LLM tokens arrive in bursts (fast) then pauses (slow).
    Solution: Buffer tokens and emit at normalized rate.
    """
    buffer_content = ""
    finished = False
    
    def base_stream_puller():
        # Thread: Pull from LLM, add to buffer
        for msg in stream_init():
            with update_lock:
                buffer_content += msg["content"]
    
    thread = threading.Thread(target=base_stream_puller)
    thread.start()
    
    # Main: Drain buffer at smoothed rate
    while not finished:
        yield normalized_chunk()
```

## Thread Lifecycle

```
Time ──────────────────────────────────────────────────────────►

Main      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████
          spawn    wait(exit_event)                   join threads

Execution ░░░░████████████████████████████████████████░░░░░░░░░░
               send_message() → Planner → CodeInterpreter → result

Animation ░░░░██░██░██░██░██░██░██░██░██░██░██░██░██░░░░░░░░░░░░
               render → sleep(0.2) → render → sleep → render

Legend: █ = active, ░ = waiting/idle
```

## Error Handling

### Keyboard Interrupt
```python
try:
    while True:
        self.exit_event.wait(0.1)
        if self.exit_event.is_set():
            break
except KeyboardInterrupt:
    error_message("Interrupted by user")
    exit(1)  # Immediate exit - session state unknown
```

### Execution Errors
```python
def execution_thread():
    try:
        round = session.send_message(...)
    except Exception as e:
        self.response.append("Error")
        raise e
    finally:
        self.exit_event.set()  # Always signal completion
```

## Design Rationale

### Why Two Threads?

1. **Non-blocking UI**: LLM calls and code execution can take seconds/minutes. Animation thread keeps UI responsive.

2. **Real-time feedback**: Users see incremental progress (streaming text, status updates) rather than waiting for complete response.

3. **Clean separation**: Execution logic doesn't need to know about display; display doesn't block execution.

### Why Event Queue?

1. **Decoupling**: Event emitters (Planner, CodeInterpreter) don't know about console display.

2. **Batching**: Multiple rapid events can be processed in single animation frame.

3. **Thread safety**: Queue with lock is simpler than direct UI updates from multiple threads.

## Comparison with Other Modes

| Mode | Threading | Display |
|------|-----------|---------|
| Console (`chat_taskweaver`) | 2 threads (exec + anim) | Real-time animated |
| Web/API | Single thread per request | WebSocket/SSE streaming |
| Programmatic | Caller's thread | Event callbacks |

## File References

| File | Component |
|------|-----------|
| `chat/console/chat.py` | `TaskWeaverRoundUpdater`, `_animate_thread` |
| `module/event_emitter.py` | `SessionEventEmitter`, `TaskWeaverEvent`, `PostEventProxy` |
| `llm/__init__.py` | `_stream_smoother` (LLM streaming) |
| `ces/manager/defer.py` | `deferred_var` (kernel warm-up) |

## Summary

TaskWeaver's console interface uses a clean dual-thread model:
- **Execution thread**: Runs the agent pipeline (Planner → CodeInterpreter → result)
- **Animation thread**: Consumes events and renders real-time console output

Communication happens via an event queue (`pending_updates`) protected by a lock, with a condition variable for efficient wake-up. This design provides responsive UI feedback during long-running AI operations while maintaining clean separation of concerns.
