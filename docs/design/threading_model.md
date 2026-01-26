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
│  │                ├── Polls for confirmation requests                  │    │
│  │                └── Handles user confirmation input                  │    │
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
│  │    │     ├── generate code  │   │    ├── Animate spinner      │         │
│  │    │     ├── verify code    │   │    └── Pause on confirm     │         │
│  │    │     ├── WAIT confirm ◄─┼───┼──────────────────────────── │         │
│  │    │     └── execute code   │   │                             │         │
│  │    └── Event emission ──────┼───┼──► pending_updates queue    │         │
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
        
        # Pause/resume handshake for animation thread
        self.pause_animation = threading.Event()    # Main requests pause
        self.animation_paused = threading.Event()   # Animation acknowledges pause
        
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

The animation thread (`_animate_thread`) runs a continuous loop with confirmation-aware synchronization:

```python
def _animate_thread(self):
    while True:
        # Check if pause is requested FIRST, before any output
        if self.pause_animation.is_set():
            # Signal that animation has paused
            self.animation_paused.set()
            # Wait until pause is lifted
            while self.pause_animation.is_set():
                if self.exit_event.is_set():
                    break
                with self.update_cond:
                    self.update_cond.wait(0.1)
            continue
        
        # Animation is running, clear the paused signal
        self.animation_paused.clear()
        
        clear_line()
        
        # Process all pending updates atomically
        with self.lock:
            for action, opt in self.pending_updates:
                if action == "start_post":
                    # Display role header: ╭───< Planner >
                elif action == "end_post":
                    # Display completion: ╰──● sending to User
                # ... other actions
            self.pending_updates.clear()
        
        if self.exit_event.is_set():
            break
        
        # Check again before printing status line
        if self.pause_animation.is_set():
            continue
        
        # Display animated status bar
        display_status_bar(role, status, get_ani_frame(counter))
        
        # Rate limit animation
        with self.update_cond:
            self.update_cond.wait(0.2)
```

### Console Output Format

```
 ╭───< Planner >
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
| `threading.Lock` (`lock`) | Protects `pending_updates` queue during read/write |
| `threading.Event` (`exit_event`) | Signals execution completion |
| `threading.Event` (`pause_animation`) | Main requests animation to pause |
| `threading.Event` (`animation_paused`) | Animation acknowledges it has paused |
| `threading.Condition` (`update_cond`) | Wakes animation thread when updates available |

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
Time ──────────────────────────────────────────────────────────────────────────────────►

Main      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████░░░░░░░░░░░░░░░░░████████████████
          spawn    wait(exit_event)          confirm?      wait        confirm?   join

Execution ░░░░██████████████████████████████░░░░░░░░░░░░██████████████████░░░░░░░░░░░░░░
               Planner → CodeInterpreter    WAIT(cond)  continue→result

Animation ░░░░██░██░██░██░██░██░██░██░██░██░░░░░░░░░░░░░██░██░██░██░██░██░░░░░░░░░░░░░░░
               render → sleep → render       PAUSED     resume → render

Legend: █ = active, ░ = waiting/idle
```

### With Confirmation Flow

```
Time ──────────────────────────────────────────────────────────────────►

Main      ████░░░░░░░░░░░░░░░░████████████████░░░░░░░░░░░░████████████████
          spawn   polling      show code      polling      join
                               get input

Execution ░░░░██████████████████░░░░░░░░░░░░░██████████████░░░░░░░░░░░░░░
               generate code   BLOCKED       execute code  done
               request confirm (waiting)     (if approved)

Animation ░░░░██░██░██░██░██░░░░░░░░░░░░░░░░░░██░██░██░██░░░░░░░░░░░░░░░░
               animate        STOPPED         resume
                              (no output)     animation

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

## Animation Pause Handshake Pattern

The console UI uses a simple, extensible handshake pattern to temporarily pause animation output when exclusive console access is needed.

### The Pattern

```python
# Two events form the handshake
pause_animation = threading.Event()   # Request: "please pause"
animation_paused = threading.Event()  # Acknowledgment: "I have paused"
```

### How It Works

**Requester (main thread or any code needing exclusive console):**
```python
# 1. Request pause
self.pause_animation.set()

# 2. Wait for acknowledgment
self.animation_paused.wait()

# 3. Safe to use console exclusively
do_exclusive_console_work()

# 4. Release
self.animation_paused.clear()
self.pause_animation.clear()
```

**Animation thread (responder):**
```python
while True:
    # Check at START of loop, before any output
    if self.pause_animation.is_set():
        self.animation_paused.set()  # Acknowledge
        while self.pause_animation.is_set():  # Wait for release
            wait()
        continue
    
    self.animation_paused.clear()  # Signal "I'm running"
    do_animation_output()
```

### Timing Diagram

```
Main Thread                              Animation Thread
───────────                              ────────────────
                                         [Loop start]
                                         pause_animation? → NO
                                         Clear animation_paused
                                         Print status line...
Set pause_animation ─────────────────────────────────────────►
Wait for animation_paused                [Loop start]
        │                                pause_animation? → YES
        │                                Set animation_paused
        ◄────────────────────────────────────────────────────┘
(wait returns)                           Wait in loop...
Show prompt, get input                   (no output)
Clear animation_paused
Clear pause_animation ───────────────────────────────────────►
                                         [Loop continues]
                                         pause_animation? → NO
                                         Resume output
```

### Why This Pattern

1. **Simple**: Two events, clear semantics
2. **Safe**: Animation always checks before output
3. **Extensible**: Any code can use it, not just confirmation
4. **No locks needed**: Handshake guarantees ordering

### Current Usage

| Feature | Uses Handshake |
|---------|----------------|
| Code confirmation prompt | ✓ |
| (Future) Interactive debugging | Can use same pattern |
| (Future) Multi-line input | Can use same pattern |

### Adding New Features

To add a new feature that needs exclusive console access:

```python
def my_new_feature(self):
    # Pause animation
    self.pause_animation.set()
    self.animation_paused.wait(timeout=5.0)
    
    try:
        # Your exclusive console work here
        result = get_user_input()
    finally:
        # Always release, even on error
        self.animation_paused.clear()
        self.pause_animation.clear()
    
    return result
```

---

## Code Execution Confirmation

When `code_interpreter.require_confirmation` is enabled, TaskWeaver will pause before executing generated code to get user confirmation.

### Confirmation Flow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Execution Thread│      │   Main Thread   │      │Animation Thread │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         │ generate code          │                        │ [Loop start]
         │ verify code            │                        │ Check confirmation_active
         │                        │                        │ → false, continue
         │                        │                        │ Clear animation_stopped
         │                        │                        │ Acquire output_lock
         │                        │                        │ Print status line
         │                        │                        │ Release output_lock
         │                        │                        │    │
         │ set _confirmation_event│                        │ [Loop start]
         │ emit confirmation_req  │                        │ Check confirmation_active
         │ WAIT on _confirm_cond ─┼────────────────────────┼─→ true!
         │      (blocked)         │                        │ Set animation_stopped ◄──┐
         │                        │ detect confirmation    │ Wait in loop             │
         │                        │ set confirmation_active│                          │
         │                        │ wait animation_stopped ─────────────────────────────┘
         │                        │ acquire output_lock    │ (cannot acquire lock)
         │                        │ clear line, show code  │    │
         │                        │ get user input [y/N]   │    │  (waiting)
         │                        │ show result            │    │
         │                        │ release output_lock    │    │
         │                        │ clear animation_stopped│    │
         │                        │ clear confirmation_active   │
         │                        │ set _confirmation_result    │
         │                        │ notify _confirm_cond   │    │
         │ ◄──────────────────────┼────────────────────────┤    │
         │ (unblocked)            │                        │ [Loop continues]
         │ read & clear result    │                        │ confirmation_active=false
         │                        │                        │ Resume normal animation
         │ if approved:           │                        │    │
         │   execute code         │                        │    │
         │ else:                  │                        │    │
         │   cancel execution     │                        │    │
         ▼                        ▼                        ▼
```

### Configuration

Enable confirmation in your `taskweaver_config.json`:

```json
{
  "code_interpreter.require_confirmation": true
}
```

### Synchronization Primitives

The confirmation system uses a two-level synchronization approach to prevent race conditions where the animation thread could overwrite user input:

#### Event Emitter Primitives (in `SessionEventEmitter`)

| Primitive | Set By | Cleared By | Purpose |
|-----------|--------|------------|---------|
| `_confirmation_event` | Execution thread | Main thread | Signals that confirmation is pending |
| `_confirmation_cond` | Main thread | - | Condition variable for blocking/waking execution thread |
| `_confirmation_result` | Main thread | Execution thread | Stores user's decision (True/False) |

#### Console UI Primitives (in `TaskWeaverRoundUpdater`)

| Primitive | Set By | Cleared By | Purpose |
|-----------|--------|------------|---------|
| `pause_animation` | Main thread | Main thread | Requests animation to pause |
| `animation_paused` | Animation thread | Main thread | Confirms animation has paused |

### Thread Responsibilities

**Execution Thread:**
- Sets `_confirmation_event` when code needs confirmation
- Emits `post_confirmation_request` event
- Waits on `_confirmation_cond` until user responds
- Reads and clears `_confirmation_result`

**Main Thread (`_handle_confirmation`):**
1. Sets `pause_animation` to signal animation thread
2. Waits for `animation_paused` to ensure animation has paused
3. Displays code and gets user input (safe from interference)
4. Clears `animation_paused` and `pause_animation`
5. Sets `_confirmation_result` and notifies `_confirmation_cond`

**Animation Thread (`_animate_thread`):**
1. Checks `pause_animation` at **start of each loop iteration**
2. If set: sets `animation_paused` and waits in a loop until `pause_animation` cleared
3. If not set: clears `animation_paused` and proceeds with output

### Why This Design Prevents Race Conditions

The handshake guarantees animation has stopped before main thread shows the prompt:

```
Animation Thread                          Main Thread
────────────────                          ───────────
[Loop iteration]
Check pause_animation → false
Clear animation_paused
Print status line
                                          Set pause_animation
                                          Wait for animation_paused
[Next loop iteration]
Check pause_animation → TRUE
Set animation_paused ───────────────────► animation_paused.wait() returns
Wait in loop                              Show prompt, get input
(no output)                               Clear animation_paused
                                          Clear pause_animation
Check pause_animation → false
Resume normal operation
```

### Key Implementation Points

1. **Early check**: Animation thread checks `pause_animation` at the **very start** of its loop, before any output operations
2. **Explicit acknowledgment**: `animation_paused` confirms animation has paused (not just signaled to pause)
3. **Clean display**: Main thread clears any leftover animation before showing code
4. **Extensible**: Any code needing exclusive console access can use the same handshake

## File References

| File | Component |
|------|-----------|
| `chat/console/chat.py` | `TaskWeaverRoundUpdater`, `_animate_thread`, `_handle_confirmation` |
| `module/event_emitter.py` | `SessionEventEmitter`, `TaskWeaverEvent`, `PostEventProxy`, `ConfirmationHandler` |
| `code_interpreter/code_interpreter/code_interpreter.py` | `CodeInterpreter.reply()` (confirmation request) |
| `llm/__init__.py` | `_stream_smoother` (LLM streaming) |
| `ces/manager/defer.py` | `deferred_var` (kernel warm-up) |

## Summary

TaskWeaver's console interface uses a clean dual-thread model:
- **Execution thread**: Runs the agent pipeline (Planner → CodeInterpreter → result)
- **Animation thread**: Consumes events and renders real-time console output

Communication happens via an event queue (`pending_updates`) protected by a lock, with a condition variable for efficient wake-up. This design provides responsive UI feedback during long-running AI operations while maintaining clean separation of concerns.

### Animation Pause Handshake

When exclusive console access is needed (e.g., confirmation prompts), use the handshake:
1. Set `pause_animation` → wait for `animation_paused`
2. Do exclusive work
3. Clear `animation_paused` → clear `pause_animation`

This pattern is simple, safe, and extensible to future features.
