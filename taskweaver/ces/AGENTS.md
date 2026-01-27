# Code Execution Service (CES) - AGENTS.md

Jupyter kernel-based code execution with server architecture supporting local, container, and remote deployment modes.

## Structure

```
ces/
├── __init__.py           # Factory: code_execution_service_factory()
├── common.py             # Client/Manager ABCs, ExecutionResult, ExecutionArtifact
├── environment.py        # Environment class - kernel management (~700 lines)
│
├── server/               # HTTP server package (FastAPI)
│   ├── __init__.py       # Exports
│   ├── models.py         # Pydantic request/response models
│   ├── session_manager.py # ServerSessionManager - wraps Environment
│   ├── routes.py         # API route handlers with SSE streaming
│   ├── app.py            # FastAPI application factory
│   └── __main__.py       # CLI: python -m taskweaver.ces.server
│
├── client/               # HTTP client package
│   ├── __init__.py       # Exports
│   ├── execution_client.py # ExecutionClient - implements Client ABC
│   └── server_launcher.py  # Auto-start server subprocess/container
│
├── manager/              # Manager implementations
│   ├── __init__.py       # Exports
│   ├── sub_proc.py       # SubProcessManager (used internally by server)
│   └── execution_service.py # ExecutionServiceProvider
│
├── kernel/               # Custom Jupyter kernel implementation
│   └── ext.py            # IPython magic commands for TaskWeaver
│
└── runtime/              # Runtime support files
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TASKWEAVER CLIENT                                  │
│                                                                             │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────────┐  │
│  │ CodeInterpreter │───▶│   CodeExecutor   │───▶│ExecutionServiceProv. │  │
│  └─────────────────┘    └──────────────────┘    └───────────┬───────────┘  │
│                                                             │               │
│                                                             ▼               │
│                                                ┌───────────────────┐        │
│                                                │ ExecutionClient   │        │
│                                                │ (HTTP)            │        │
│                                                └─────────┬─────────┘        │
└──────────────────────────────────────────────────────────┼──────────────────┘
                                                           │
                                                           │ HTTP (localhost:8000 or remote)
                                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION SERVER                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       FastAPI Application                             │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────────┐     │  │
│  │  │ /sessions │  │ /plugins  │  │ /execute  │  │ /artifacts      │     │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └─────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    ServerSessionManager                               │  │
│  │   sessions: Dict[session_id, ServerSession]                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                   Environment (EnvMode.Local)                         │  │
│  │   - Jupyter kernel management via MultiKernelManager                  │  │
│  │   - Plugin loading via magic commands                                 │  │
│  │   - Code execution and output capture                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Classes

### ABCs (common.py)

```python
class Client(ABC):
    """Interface for execution clients."""
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def load_plugin(self, name: str, code: str, config: Dict) -> None: ...
    def execute_code(self, exec_id: str, code: str, on_output: Callable = None) -> ExecutionResult: ...

class Manager(ABC):
    """Interface for execution managers."""
    def initialize(self) -> None: ...
    def clean_up(self) -> None: ...
    def get_session_client(self, session_id: str, ...) -> Client: ...
    def get_kernel_mode(self) -> KernelModeType: ...
```

### ExecutionResult (common.py)

```python
@dataclass
class ExecutionResult:
    execution_id: str
    code: str
    is_success: bool = False
    error: Optional[str] = None
    output: Union[str, List[Tuple[str, str]]] = ""
    stdout: List[str] = field(default_factory=list)
    stderr: List[str] = field(default_factory=list)
    log: List[Tuple[str, str, str]] = field(default_factory=list)
    artifact: List[ExecutionArtifact] = field(default_factory=list)
    variables: List[Tuple[str, str]] = field(default_factory=list)
```

### Server-Side Classes

| Class | File | Purpose |
|-------|------|---------|
| `ServerSessionManager` | `server/session_manager.py` | Manages multiple sessions, wraps Environment |
| `ServerSession` | `server/session_manager.py` | Per-session state (environment, plugins, stats) |
| Pydantic Models | `server/models.py` | Request/response models for HTTP API |

### Client-Side Classes

| Class | File | Purpose |
|-------|------|---------|
| `ExecutionClient` | `client/execution_client.py` | HTTP client implementing Client ABC |
| `ServerLauncher` | `client/server_launcher.py` | Auto-start server as subprocess/container |
| `ExecutionServiceProvider` | `manager/execution_service.py` | Manager implementation using HTTP client |
| `ExecutionServiceClient` | `manager/execution_service.py` | Client wrapper for Provider |

## Deployment Modes

### 1. Local Process (Default)
```
TaskWeaver ──HTTP──▶ Server (subprocess) ──▶ Jupyter Kernel
                     localhost:8000
```

Server auto-starts when needed. Full filesystem access.

### 2. Local Container
```
TaskWeaver ──HTTP──▶ Docker Container ──▶ Jupyter Kernel
                     localhost:8000
```

Isolated filesystem. Volumes mapped for workspace.

### 3. Remote Server
```
TaskWeaver ──HTTP──▶ Remote Machine ──▶ Jupyter Kernel
                     remote:8000
```

Connect to pre-started server. API key required.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/sessions` | Create session |
| DELETE | `/api/v1/sessions/{id}` | Stop session |
| GET | `/api/v1/sessions/{id}` | Get session info |
| POST | `/api/v1/sessions/{id}/plugins` | Load plugin |
| POST | `/api/v1/sessions/{id}/execute` | Execute code |
| GET | `/api/v1/sessions/{id}/stream/{exec_id}` | SSE stream |
| POST | `/api/v1/sessions/{id}/variables` | Update variables |
| GET | `/api/v1/sessions/{id}/artifacts/{file}` | Download artifact |

## Usage

### Starting the Server Manually

```bash
# Basic
python -m taskweaver.ces.server

# With options
python -m taskweaver.ces.server \
    --host 0.0.0.0 \
    --port 8000 \
    --work-dir /var/taskweaver \
    --api-key "secret"
```

### Using the Factory

```python
from taskweaver.ces import code_execution_service_factory

# Default: local server with auto-start
manager = code_execution_service_factory(env_dir="/tmp/work")

# Containerized server
manager = code_execution_service_factory(
    env_dir="/tmp/work",
    server_container=True,
)

# Remote server
manager = code_execution_service_factory(
    env_dir="/tmp/work",
    server_url="http://remote:8000",
    server_api_key="secret",
    server_auto_start=False,
)
```

### Using the Client Directly

```python
from taskweaver.ces.client import ExecutionClient

with ExecutionClient(
    session_id="my-session",
    server_url="http://localhost:8000",
) as client:
    client.start()
    client.load_plugin("my_plugin", plugin_code, {"key": "value"})
    result = client.execute_code("exec-1", "print('Hello')")
    print(result.stdout)  # ['Hello\n']
    client.stop()
```

## Execution Flow

1. **Session Creation**: `POST /sessions` → ServerSessionManager creates Environment
2. **Plugin Loading**: `POST /sessions/{id}/plugins` → Environment.load_plugin()
3. **Code Execution**: `POST /sessions/{id}/execute` → Environment.execute_code()
4. **Streaming**: SSE events for stdout/stderr during execution
5. **Session Cleanup**: `DELETE /sessions/{id}` → Environment.stop_session()

## Custom Kernel Magics (kernel/ext.py)

```python
%_taskweaver_session_init {session_id}
%_taskweaver_plugin_register {name}
%_taskweaver_plugin_load {name}
%_taskweaver_exec_pre_check {index} {exec_id}
%_taskweaver_exec_post_check {index} {exec_id}
%%_taskweaver_update_session_var
```

## Error Handling

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success (execution errors in response body) |
| 201 | Session created |
| 400 | Bad request (plugin load failed, invalid request) |
| 401 | Unauthorized (invalid API key) |
| 404 | Session/artifact not found |
| 409 | Session already exists |
| 500 | Internal server error |

## Testing

Unit tests in `tests/unit_tests/ces/`:

| File | Coverage |
|------|----------|
| `test_server_models.py` | Pydantic models, utility functions |
| `test_session_manager.py` | ServerSessionManager (mocked Environment) |
| `test_execution_client.py` | ExecutionClient (mocked HTTP) |
| `test_server_launcher.py` | ServerLauncher (mocked subprocess/docker) |
| `test_execution_service.py` | ExecutionServiceProvider |

Run tests:
```bash
pytest tests/unit_tests/ces/ -v
```

## Configuration

Configuration options (in `taskweaver_config.json`):

```json
{
  "execution.server.url": "http://localhost:8000",
  "execution.server.api_key": "",
  "execution.server.auto_start": true,
  "execution.server.container": false,
  "execution.server.container_image": "taskweavercontainers/taskweaver-executor:latest",
  "execution.server.timeout": 300
}
```

## Container Mode Details

When `server_container=true`:
- Image: `taskweavercontainers/taskweaver-executor:latest`
- Port mapping: `8000/tcp` → host port
- Volume: `{env_dir}` → `/app/workspace`
- Server runs inside container with local kernel
