# Plugin Execution Output Streaming - Design Document

**Generated:** 2026-01-26 | **Author:** AI Agent | **Status:** Analysis Complete

## Problem

When a plugin (Python function) executes long-running operations with `print()` statements or `ctx.log()` calls, the output only appears **after** execution completes, not during. This creates a poor user experience for operations that take seconds or minutes.

**Example scenario:**
```python
# Plugin function
def long_running_analysis(ctx: PluginContext, data: pd.DataFrame):
    print("Starting analysis...")  # User doesn't see this until end
    for i in range(100):
        # ... heavy computation ...
        print(f"Progress: {i}%")    # User doesn't see this until end
    print("Done!")
    return result
```

The user sees nothing for the entire execution duration, then all output appears at once.

## Root Cause Analysis

### Execution Flow

```
CodeInterpreter.reply()
    └── CodeExecutor.execute_code()
            └── Environment._execute_code_on_kernel()
                    └── BlockingKernelClient.execute()
                    └── while loop: kc.get_iopub_msg()
                            ├── msg_type == "stream" → stdout/stderr COLLECTED
                            └── msg_type == "status" idle → break (done)
```

### The Bottleneck: `_execute_code_on_kernel()`

In `taskweaver/ces/environment.py` (lines 518-595), the kernel message loop:

```python
def _execute_code_on_kernel(self, code: str, ...) -> ExecutionResult:
    exec_result = ExecutionResult()
    
    # ... setup ...
    
    while True:
        msg = kc.get_iopub_msg()  # Jupyter sends messages AS they happen
        msg_type = msg["msg_type"]
        
        if msg_type == "stream":
            stream_name = msg["content"]["name"]
            stream_text = msg["content"]["text"]
            if stream_name == "stdout":
                exec_result.stdout.append(stream_text)  # <-- BATCHED, not streamed
            elif stream_name == "stderr":
                exec_result.stderr.append(stream_text)  # <-- BATCHED, not streamed
        
        elif msg_type == "status":
            if msg["content"]["execution_state"] == "idle":
                break  # Only returns AFTER execution completes
    
    return exec_result  # All output returned at once
```

**Key insight**: The Jupyter kernel **does** send `stream` messages in real-time as `print()` is called. TaskWeaver receives them but **collects** them into lists instead of forwarding them immediately.

### Why It's Batched

The current architecture has no mechanism to push intermediate output to the UI during execution:

1. **No callback/event mechanism** in `_execute_code_on_kernel()`
2. **Synchronous return** - function returns only when execution completes
3. **No event emission** for partial stdout/stderr
4. **UI thread isolation** - execution runs in separate thread from animation

## Current Architecture

### Relevant Components

| Component | File | Role |
|-----------|------|------|
| `Environment._execute_code_on_kernel()` | `ces/environment.py` | Receives kernel messages, batches stdout |
| `ExecutionResult` | `ces/common.py` | Dataclass holding stdout/stderr lists |
| `CodeExecutor.execute_code()` | `code_interpreter/code_executor.py` | Wraps Environment, formats output |
| `CodeInterpreter.reply()` | `code_interpreter/code_interpreter/code_interpreter.py` | Orchestrates execution, emits events |
| `SessionEventEmitter` | `module/event_emitter.py` | Event dispatch to handlers |
| `PostEventProxy` | `module/event_emitter.py` | Per-post event wrapper |
| `TaskWeaverRoundUpdater` | `chat/console/chat.py` | Console UI event handler |
| `ExecutorPluginContext` | `ces/runtime/context.py` | Plugin's `ctx.log()` implementation |

### Event System

The event system already supports real-time updates:

```python
class PostEventType(Enum):
    post_status_update = "post_status_update"      # Status text changes
    post_message_update = "post_message_update"    # Message content streaming
    post_attachment_update = "post_attachment_update"  # Attachment updates
    # ... others
```

LLM response streaming uses `post_message_update` to show tokens as they arrive. The same pattern could work for execution output.

### Threading Model

```
┌─────────────────────────────┐   ┌─────────────────────────────┐
│    Execution Thread (t_ex)  │   │   Animation Thread (t_ui)   │
│                             │   │                             │
│  session.send_message()     │   │  _animate_thread()          │
│    ├── Planner.reply()      │   │    ├── Process updates      │
│    ├── CodeInterpreter      │   │    ├── Render status bar    │
│         .reply()            │   │    └── Display messages     │
│         └── execute_code()  │   │                             │
│              └── BLOCKED    │   │                             │
│                 waiting     │   │                             │
│                 for kernel  │   │                             │
│                             │   │                             │
│    Event emission ──────────┼───┼──► pending_updates queue    │
└─────────────────────────────┘   └─────────────────────────────┘
```

The execution thread blocks in `_execute_code_on_kernel()` while the animation thread is ready to display updates - but no updates are sent during execution.

## Proposed Solution

### Design Approach

Add an **optional callback** to `_execute_code_on_kernel()` that fires for each `stream` message. This callback can emit events to the UI in real-time.

### Changes Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Proposed Changes                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Environment._execute_code_on_kernel()                                │
│     └── Add: on_output callback parameter                                │
│     └── Call: on_output(stream_name, text) for each stream message       │
│                                                                          │
│  2. CodeExecutor.execute_code()                                          │
│     └── Add: on_output parameter, pass to Environment                    │
│                                                                          │
│  3. CodeInterpreter.reply()                                              │
│     └── Create callback that emits PostEventType.post_execution_output   │
│     └── Pass callback to execute_code()                                  │
│                                                                          │
│  4. PostEventType (event_emitter.py)                                     │
│     └── Add: post_execution_output event type                            │
│                                                                          │
│  5. TaskWeaverRoundUpdater (chat.py)                                     │
│     └── Handle: post_execution_output events                             │
│     └── Display: incremental stdout/stderr in console                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Detailed Design

#### 1. Environment Layer

```python
# ces/environment.py

def _execute_code_on_kernel(
    self,
    code: str,
    session_id: str,
    ...,
    on_output: Optional[Callable[[str, str], None]] = None,  # NEW
) -> ExecutionResult:
    """
    Args:
        on_output: Optional callback(stream_name, text) called for each stdout/stderr chunk
    """
    exec_result = ExecutionResult()
    
    while True:
        msg = kc.get_iopub_msg()
        msg_type = msg["msg_type"]
        
        if msg_type == "stream":
            stream_name = msg["content"]["name"]
            stream_text = msg["content"]["text"]
            
            # NEW: Fire callback for real-time streaming
            if on_output is not None:
                on_output(stream_name, stream_text)
            
            # Still collect for final result (backward compatibility)
            if stream_name == "stdout":
                exec_result.stdout.append(stream_text)
            elif stream_name == "stderr":
                exec_result.stderr.append(stream_text)
        
        # ... rest unchanged
```

#### 2. CodeExecutor Layer

```python
# code_interpreter/code_executor.py

def execute_code(
    self,
    exec_id: str,
    code: str,
    on_output: Optional[Callable[[str, str], None]] = None,  # NEW
) -> Tuple[ExecutionResult, str]:
    """
    Args:
        on_output: Optional callback for streaming stdout/stderr during execution
    """
    result = self.env.execute_code(
        code,
        session_id=self.session_id,
        on_output=on_output,  # Pass through
    )
    # ... format output ...
```

#### 3. Event Type

```python
# module/event_emitter.py

class PostEventType(Enum):
    post_status_update = "post_status_update"
    post_message_update = "post_message_update"
    post_attachment_update = "post_attachment_update"
    post_execution_output = "post_execution_output"  # NEW
    # ...
```

#### 4. CodeInterpreter Layer

```python
# code_interpreter/code_interpreter/code_interpreter.py

def reply(self, ...):
    # ... code generation, verification ...
    
    # Create streaming callback
    def on_execution_output(stream_name: str, text: str):
        self.post_proxy.emit_execution_output(stream_name, text)
    
    # Execute with streaming
    exec_result, output = self.executor.execute_code(
        exec_id=exec_id,
        code=code,
        on_output=on_execution_output,  # NEW
    )
```

#### 5. PostEventProxy Extension

```python
# module/event_emitter.py

class PostEventProxy:
    def emit_execution_output(self, stream_name: str, text: str):
        """Emit real-time execution output (stdout/stderr)."""
        self.event_emitter.emit(
            TaskWeaverEvent(
                scope=EventScope.post,
                event_type=PostEventType.post_execution_output.value,
                post_id=self.post_id,
                extra={"stream": stream_name, "text": text},
            ),
        )
```

#### 6. Console UI Handler

```python
# chat/console/chat.py

class TaskWeaverRoundUpdater(SessionEventHandlerBase):
    def handle(self, event: TaskWeaverEvent):
        # ... existing handlers ...
        
        elif event.event_type == PostEventType.post_execution_output.value:
            stream_name = event.extra["stream"]
            text = event.extra["text"]
            with self.lock:
                # Display immediately without clearing status line
                self.pending_updates.append(("execution_output", (stream_name, text)))
            with self.update_cond:
                self.update_cond.notify_all()
    
    def _animate_thread(self):
        # ... in update processing loop ...
        
        for action, opt in self.pending_updates:
            if action == "execution_output":
                stream_name, text = opt
                # Print execution output inline
                prefix = "" if stream_name == "stdout" else "[stderr] "
                sys.stdout.write(f"  {prefix}{text}")
                sys.stdout.flush()
```

### Console Output Format

```
 ╭───< CodeInterpreter >
 ├─► [code] import time; print("Starting..."); time.sleep(5); print("Done")
 ├─► [verification] CORRECT
 │   Starting...              ← NEW: Appears immediately when print() executes
 │   Done                     ← NEW: Appears when print() executes
 ├─► [execution_status] SUCCESS
 ╰──● sending message to Planner
```

## Alternative Approaches Considered

### 1. Async/Generator Pattern

Instead of callbacks, make `_execute_code_on_kernel()` a generator:

```python
def _execute_code_on_kernel(self, code: str, ...) -> Generator[Tuple[str, str], None, ExecutionResult]:
    while True:
        msg = kc.get_iopub_msg()
        if msg_type == "stream":
            yield ("stream", stream_name, text)  # Yield intermediate output
        elif msg_type == "status" and idle:
            return exec_result  # Return final result
```

**Rejected because**: Requires significant refactoring of callers; callback is simpler and backward-compatible.

### 2. Separate Thread for Streaming

Spawn a dedicated thread to poll kernel messages and emit events:

```python
def _execute_code_on_kernel(self, ...):
    def stream_poller():
        while not done:
            msg = kc.get_iopub_msg(timeout=0.1)
            if msg_type == "stream":
                emit_event(...)
    
    thread = Thread(target=stream_poller)
    thread.start()
    # ... wait for execution ...
```

**Rejected because**: Adds threading complexity; callback achieves same result more simply.

### 3. Plugin Context Enhancement (`ctx.log()`)

Enhance `ctx.log()` to stream immediately instead of batching:

```python
# In ExecutorPluginContext
def log(self, message: str):
    # Instead of appending to list, emit event immediately
    self._emit_log_event(message)
```

**Partial solution**: Only helps plugins using `ctx.log()`, not raw `print()`. Should be done as follow-up.

## Execution Mode Support

### Both Local and Container Modes Supported

The proposed design works identically for both execution modes because **both use the same `_execute_code_on_kernel()` method**.

#### Architecture Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     _execute_code_on_kernel() [lines 518-595]               │
│                                                                             │
│    while True:                                                              │
│        msg = kc.get_iopub_msg()  ◄─────┬─────────────────────────────────┐  │
│        if msg_type == "stream":        │                                 │  │
│            on_output(stream_name, text)│                                 │  │
│                                        │                                 │  │
└────────────────────────────────────────┼─────────────────────────────────┼──┘
                                         │                                 │
                    ┌────────────────────┴────────────────┐   ┌────────────┴───────────┐
                    │          Local Mode                 │   │     Container Mode     │
                    ├─────────────────────────────────────┤   ├────────────────────────┤
                    │ BlockingKernelClient                │   │ BlockingKernelClient   │
                    │   └── Direct ZMQ connection         │   │   └── TCP to localhost │
                    │       to local kernel               │   │       port (mapped)    │
                    │                                     │   │                        │
                    │ MultiKernelManager                  │   │ Docker Container       │
                    │   └── Spawns kernel process         │   │   └── iopub port 12346 │
                    │       locally                       │   │       mapped to host   │
                    └─────────────────────────────────────┘   └────────────────────────┘
```

#### Why Both Modes Work

1. **Same message loop**: Both modes call `kc.get_iopub_msg()` in the same `while` loop
2. **Same message format**: Jupyter's ZMQ protocol is identical regardless of transport
3. **Transparent routing**: Container mode uses Docker port mapping - the `BlockingKernelClient` doesn't know it's talking to a container

From `_get_client()` (environment.py lines 489-511):
```python
if self.mode == EnvMode.Container:
    client.ip = "127.0.0.1"
    client.iopub_port = ports["iopub_port"]  # Mapped host port
```

The client connects to `127.0.0.1:{mapped_port}` which Docker routes to the container's iopub socket. **Stream messages arrive identically.**

#### No Mode-Specific Code Needed

The callback addition is purely in `_execute_code_on_kernel()`, which is mode-agnostic:

```python
def _execute_code_on_kernel(self, ..., on_output: Optional[Callable] = None):
    # No mode checks needed - kc.get_iopub_msg() works the same way
    while True:
        msg = kc.get_iopub_msg()
        if msg_type == "stream":
            if on_output:
                on_output(stream_name, stream_text)  # Works for both modes
```

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **High-frequency output** (tight loops with print) | Rate-limit events; batch rapid messages |
| **Console flicker** | Buffer updates; use ANSI escape for smooth rendering |
| **Thread safety** | Callback executes in execution thread; use lock for UI state |
| **Backward compatibility** | Callback is optional; existing code unchanged |
| **Network latency (container)** | Docker localhost routing adds negligible latency (<1ms) |

### Rate Limiting Strategy

For rapid output (e.g., progress bars), batch messages:

```python
class OutputBatcher:
    def __init__(self, emit_fn, interval=0.1):
        self.buffer = []
        self.last_emit = time.time()
        self.emit_fn = emit_fn
    
    def add(self, stream_name, text):
        self.buffer.append((stream_name, text))
        if time.time() - self.last_emit > self.interval:
            self.flush()
    
    def flush(self):
        if self.buffer:
            # Combine buffered text
            combined = "".join(text for _, text in self.buffer)
            self.emit_fn("stdout", combined)
            self.buffer.clear()
            self.last_emit = time.time()
```

## Testing Strategy

### Unit Tests

1. **Callback invocation**: Verify `on_output` called for each stream message
2. **Event emission**: Verify `post_execution_output` events emitted
3. **Backward compatibility**: Verify existing code works without callback

### Integration Tests

1. **Console display**: Verify streaming output appears during execution
2. **Multi-line output**: Verify proper formatting of multi-line prints
3. **Mixed stdout/stderr**: Verify both streams handled correctly
4. **Long-running execution**: Verify output appears incrementally over time
5. **Local mode**: Test with `EnvMode.Local` configuration
6. **Container mode**: Test with `EnvMode.Container` configuration (requires Docker)

### Manual Testing

```python
# Test plugin
def test_streaming(ctx):
    import time
    for i in range(5):
        print(f"Progress: {i+1}/5")
        time.sleep(1)
    return "Done"
```

Expected: "Progress: 1/5" appears after 1s, "Progress: 2/5" after 2s, etc.

## Implementation Plan

### Phase 1: Core Streaming (MVP)
1. Add `on_output` callback to `Environment._execute_code_on_kernel()`
2. Add `post_execution_output` event type
3. Wire callback through `CodeExecutor` → `CodeInterpreter`
4. Handle event in `TaskWeaverRoundUpdater`

### Phase 2: Polish
1. Add rate limiting for high-frequency output
2. Improve console formatting (indentation, colors)
3. Handle stderr distinctly (red text?)

### Phase 3: Extended Support
1. Enhance `ctx.log()` to use same streaming mechanism
2. Add web UI support for streaming execution output
3. Consider progress bar support (detect and render specially)

## Files to Modify

| File | Changes |
|------|---------|
| `taskweaver/ces/environment.py` | Add `on_output` callback to `_execute_code_on_kernel()` |
| `taskweaver/ces/common.py` | No changes needed (ExecutionResult unchanged) |
| `taskweaver/code_interpreter/code_executor.py` | Pass `on_output` through to Environment |
| `taskweaver/code_interpreter/code_interpreter/code_interpreter.py` | Create and pass callback |
| `taskweaver/module/event_emitter.py` | Add `post_execution_output` event type, `emit_execution_output()` method |
| `taskweaver/chat/console/chat.py` | Handle `post_execution_output` events in UI |

## Open Questions

1. ~~**Container mode**: Does output streaming work through Docker container boundary?~~ **RESOLVED**: Yes, both modes use the same `_execute_code_on_kernel()` with identical message handling. See "Execution Mode Support" section.
2. **Web UI**: Should this be extended to web interface? (SSE/WebSocket)
3. **Truncation**: Should very long output be truncated during streaming?
4. **Interactivity**: Could this enable input prompts during execution? (Future)

## References

- [Threading Model Design Doc](./threading_model.md)
- [Code Interpreter Variables Design Doc](./code-interpreter-vars.md)
- [Jupyter Messaging Protocol](https://jupyter-client.readthedocs.io/en/stable/messaging.html)
- `taskweaver/ces/environment.py` - Core execution logic
- `taskweaver/module/event_emitter.py` - Event system
- `taskweaver/chat/console/chat.py` - Console UI
