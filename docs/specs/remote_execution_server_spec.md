# Technical Specification: Server-First Execution Architecture

**Version:** 1.0  
**Date:** 2026-01-27  
**Status:** Approved for Implementation

## 1. Overview

This specification describes a server-first architecture for TaskWeaver's code execution system. The execution server provides an HTTP API that wraps the Jupyter kernel, enabling both local and remote execution through a unified interface.

## 2. Design Principles

1. **Server-Only**: All execution goes through the HTTP API
2. **Local by Default**: Server auto-starts locally, providing full filesystem access
3. **Container as Wrapper**: Container mode wraps the entire server, not just the kernel
4. **Minimal Duplication**: Server reuses existing `Environment` class internally

---

## 3. Architecture

### 3.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TASKWEAVER CLIENT                                  │
│                                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────────────┐  │
│  │ CodeInterpreter │───▶│   CodeExecutor   │───▶│   ExecutionServiceProvider│  │
│  └─────────────────┘    └──────────────────┘    └─────────────┬─────────────┘  │
│                                                               │                 │
│                                                               ▼                 │
│                                                    ┌───────────────────┐        │
│                                                    │ ExecutionClient   │        │
│                                                    │ (HTTP)            │        │
│                                                    └─────────┬─────────┘        │
│                                                               │                 │
└───────────────────────────────────┼─────────────────────────────────────────────┘
                                    │
                                    │ HTTP (localhost:8000 or remote)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EXECUTION SERVER                                     │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI Application                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐   │   │
│  │  │ /sessions   │  │ /plugins    │  │ /execute    │  │ /artifacts    │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                         │
│                                       ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      ServerSessionManager                               │   │
│  │                                                                         │   │
│  │   sessions: Dict[session_id, ServerSession]                             │   │
│  │                                                                         │   │
│  │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │   │ ServerSession                                                   │   │   │
│  │   │   - session_id: str                                             │   │   │
│  │   │   - environment: Environment (EnvMode.Local)                    │   │   │
│  │   │   - created_at: datetime                                        │   │   │
│  │   │   - last_activity: datetime                                     │   │   │
│  │   └─────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                         │
│                                       ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     Environment (Existing Code)                         │   │
│  │                                                                         │   │
│  │   - EnvMode.Local only (container isolation at server level)            │   │
│  │   - Jupyter kernel management                                           │   │
│  │   - Plugin loading via magic commands                                   │   │
│  │   - Code execution                                                      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Deployment Configurations

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT A: Local Process (Default)                                          │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          User's Machine                                 │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐              ┌─────────────────────────────────┐   │   │
│  │  │ TaskWeaver      │    HTTP      │ Execution Server (subprocess)  │   │   │
│  │  │ Main Process    │◄────────────▶│                                 │   │   │
│  │  │                 │  localhost   │ - Full filesystem access        │   │   │
│  │  │ (auto-starts    │   :8000      │ - Local Python packages         │   │   │
│  │  │  server)        │              │ - User's environment vars       │   │   │
│  │  └─────────────────┘              └─────────────────────────────────┘   │   │
│  │                                                                         │   │
│  │  Config: auto_start=true, container=false                               │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT B: Local Container                                                  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          User's Machine                                 │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐              ┌─────────────────────────────────┐   │   │
│  │  │ TaskWeaver      │    HTTP      │ Docker Container                │   │   │
│  │  │ Main Process    │◄────────────▶│ ┌─────────────────────────────┐ │   │   │
│  │  │                 │  localhost   │ │ Execution Server            │ │   │   │
│  │  │ (auto-starts    │   :8000      │ │                             │ │   │   │
│  │  │  container)     │              │ │ - Isolated filesystem       │ │   │   │
│  │  └─────────────────┘              │ │ - Controlled packages       │ │   │   │
│  │                                   │ └─────────────────────────────┘ │   │   │
│  │                                   │                                 │   │   │
│  │                                   │ Volumes:                        │   │   │
│  │                                   │ - ./workspace:/app/workspace    │   │   │
│  │                                   └─────────────────────────────────┘   │   │
│  │                                                                         │   │
│  │  Config: auto_start=true, container=true                                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT C: Remote Server                                                    │
│                                                                                 │
│  ┌──────────────────────────────┐    ┌──────────────────────────────────────┐  │
│  │      User's Machine          │    │         Remote Machine               │  │
│  │                              │    │                                      │  │
│  │  ┌────────────────────────┐  │HTTP│  ┌────────────────────────────────┐  │  │
│  │  │ TaskWeaver             │  │    │  │ Execution Server               │  │  │
│  │  │ Main Process           │◄─┼────┼─▶│                                │  │  │
│  │  │                        │  │    │  │ - Server's filesystem          │  │  │
│  │  │ (connects to remote)   │  │    │  │ - Server's packages            │  │  │
│  │  └────────────────────────┘  │    │  │ - GPU access (if available)    │  │  │
│  │                              │    │  └────────────────────────────────┘  │  │
│  └──────────────────────────────┘    └──────────────────────────────────────┘  │
│                                                                                 │
│  Config: auto_start=false, url="http://remote:8000", api_key="xxx"             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. File Structure

### 4.1 New Files

```
taskweaver/ces/
├── __init__.py                      # Update exports
├── common.py                        # Existing - no changes needed
├── environment.py                   # Existing - no changes needed
│
├── manager/
│   ├── __init__.py                  # Update exports
│   ├── sub_proc.py                  # Internal - used by server for kernel management
│   └── execution_service.py         # NEW - ExecutionServiceProvider
│
├── server/                          # NEW - Server package
│   ├── __init__.py
│   ├── app.py                       # FastAPI application
│   ├── routes.py                    # API route handlers
│   ├── session_manager.py           # Server-side session management
│   ├── models.py                    # Pydantic request/response models
│   └── __main__.py                  # CLI entry point: python -m taskweaver.ces.server
│
├── client/                          # NEW - Client package
│   ├── __init__.py
│   ├── execution_client.py          # HTTP client implementation
│   └── server_launcher.py           # Auto-start server process/container
│
├── kernel/                          # Existing - no changes
└── runtime/                         # Existing - no changes
```

### 4.2 Modified Files

```
taskweaver/
├── config/
│   └── config_mgt.py                # Add execution server config options
│
├── code_interpreter/
│   └── code_executor.py             # Update to use ExecutionServiceProvider
│
└── app/
    └── app.py                       # Wire up new execution service
```

---

## 5. Configuration

### 5.1 Configuration Schema

```python
# New configuration options in config_mgt.py

class ExecutionConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("execution")
        
        # Server configuration
        self.server_url = self._get_str("server.url", "http://localhost:8000")
        self.server_api_key = self._get_str("server.api_key", "")
        self.server_auto_start = self._get_bool("server.auto_start", True)
        self.server_container = self._get_bool("server.container", False)
        self.server_container_image = self._get_str(
            "server.container_image",
            "taskweavercontainers/taskweaver-executor:latest"
        )
        self.server_host = self._get_str("server.host", "localhost")
        self.server_port = self._get_int("server.port", 8000)
        self.server_timeout = self._get_int("server.timeout", 300)
```

### 5.2 Configuration Examples

```json
// Example 1: Default - Local auto-started server
{
  // No configuration needed, uses defaults
}

// Example 2: Local container
{
  "execution.server.container": true
}

// Example 3: Remote server
{
  "execution.server.url": "http://192.168.1.100:8000",
  "execution.server.api_key": "your-secret-key",
  "execution.server.auto_start": false
}
```

---

## 6. API Specification

### 6.1 Base URL and Authentication

```
Base URL: http://{host}:{port}/api/v1
Authentication: X-API-Key header (optional for localhost)
```

### 6.2 Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no auth required) |
| POST | `/sessions` | Create new session |
| DELETE | `/sessions/{session_id}` | Stop and remove session |
| GET | `/sessions/{session_id}` | Get session info |
| POST | `/sessions/{session_id}/plugins` | Load plugin |
| POST | `/sessions/{session_id}/execute` | Execute code |
| GET | `/sessions/{session_id}/execute/{exec_id}/stream` | Stream execution output (SSE) |
| POST | `/sessions/{session_id}/variables` | Update session variables |
| GET | `/sessions/{session_id}/artifacts/{filename}` | Download artifact file |

### 6.3 Endpoint Details

#### 6.3.1 Health Check

```
GET /api/v1/health

Response 200:
{
  "status": "healthy",
  "version": "0.1.0",
  "active_sessions": 2
}
```

#### 6.3.2 Create Session

```
POST /api/v1/sessions
Content-Type: application/json
X-API-Key: {api_key}

Request:
{
  "session_id": "session-abc123",
  "cwd": "/optional/working/directory"  // Optional, server decides default
}

Response 201:
{
  "session_id": "session-abc123",
  "status": "created",
  "cwd": "/actual/working/directory"
}

Response 409 (session exists):
{
  "detail": "Session session-abc123 already exists"
}
```

#### 6.3.3 Stop Session

```
DELETE /api/v1/sessions/{session_id}
X-API-Key: {api_key}

Response 200:
{
  "session_id": "session-abc123",
  "status": "stopped"
}

Response 404:
{
  "detail": "Session session-abc123 not found"
}
```

#### 6.3.4 Get Session Info

```
GET /api/v1/sessions/{session_id}
X-API-Key: {api_key}

Response 200:
{
  "session_id": "session-abc123",
  "status": "running",
  "created_at": "2024-01-15T10:30:00Z",
  "last_activity": "2024-01-15T11:45:30Z",
  "loaded_plugins": ["sql_pull_data", "anomaly_detection"],
  "execution_count": 15,
  "cwd": "/path/to/working/directory"
}
```

#### 6.3.5 Load Plugin

```
POST /api/v1/sessions/{session_id}/plugins
Content-Type: application/json
X-API-Key: {api_key}

Request:
{
  "name": "sql_pull_data",
  "code": "from taskweaver.plugin import register_plugin\n\n@register_plugin\nclass SqlPullData:\n    def __call__(self, query: str):\n        ...",
  "config": {
    "api_type": "openai",
    "api_key": "sk-xxxxx",
    "sqlite_db_path": "sqlite:///data/mydb.db"
  }
}

Response 200:
{
  "name": "sql_pull_data",
  "status": "loaded"
}

Response 400 (load error):
{
  "detail": "Failed to load plugin sql_pull_data: SyntaxError at line 15"
}
```

#### 6.3.6 Execute Code

```
POST /api/v1/sessions/{session_id}/execute
Content-Type: application/json
X-API-Key: {api_key}

Request:
{
  "exec_id": "exec-001",
  "code": "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2, 3]})\nprint('Created DataFrame')\ndf",
  "stream": false  // Optional, default false
}

Response 200 (stream=false):
{
  "execution_id": "exec-001",
  "is_success": true,
  "error": null,
  "output": "   a\n0  1\n1  2\n2  3",
  "stdout": ["Created DataFrame\n"],
  "stderr": [],
  "log": [],
  "artifact": [],
  "variables": [
    ["df", "DataFrame(3 rows × 1 columns)"]
  ]
}

Response 202 (stream=true):
{
  "execution_id": "exec-001",
  "stream_url": "/api/v1/sessions/session-abc123/execute/exec-001/stream"
}
```

#### 6.3.7 Stream Execution Output

```
GET /api/v1/sessions/{session_id}/execute/{exec_id}/stream
Accept: text/event-stream
X-API-Key: {api_key}

Response (SSE stream):
event: output
data: {"type": "stdout", "text": "Processing step 1...\n"}

event: output
data: {"type": "stdout", "text": "Processing step 2...\n"}

event: output
data: {"type": "stderr", "text": "Warning: deprecated function\n"}

event: result
data: {"execution_id": "exec-001", "is_success": true, "output": "Done", ...}

event: done
data: {}
```

#### 6.3.8 Update Session Variables

```
POST /api/v1/sessions/{session_id}/variables
Content-Type: application/json
X-API-Key: {api_key}

Request:
{
  "variables": {
    "user_name": "Alice",
    "project_id": "proj-123"
  }
}

Response 200:
{
  "status": "updated",
  "variables": {
    "user_name": "Alice",
    "project_id": "proj-123"
  }
}
```

#### 6.3.9 Download Artifact

```
GET /api/v1/sessions/{session_id}/artifacts/{filename}
X-API-Key: {api_key}

Response 200:
Content-Type: application/octet-stream (or appropriate mime type)
Content-Disposition: attachment; filename="chart.png"

<binary file content>

Response 404:
{
  "detail": "Artifact chart.png not found"
}
```

---

## 7. Data Models

### 7.1 Request Models

```python
# taskweaver/ces/server/models.py

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class CreateSessionRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    cwd: Optional[str] = Field(None, description="Working directory for code execution")

class LoadPluginRequest(BaseModel):
    name: str = Field(..., description="Plugin name")
    code: str = Field(..., description="Plugin source code")
    config: Dict[str, Any] = Field(default_factory=dict, description="Plugin configuration")

class ExecuteCodeRequest(BaseModel):
    exec_id: str = Field(..., description="Unique execution identifier")
    code: str = Field(..., description="Python code to execute")
    stream: bool = Field(False, description="Enable streaming output")

class UpdateVariablesRequest(BaseModel):
    variables: Dict[str, str] = Field(..., description="Session variables to update")
```

### 7.2 Response Models

```python
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from datetime import datetime

class HealthResponse(BaseModel):
    status: Literal["healthy"]
    version: str
    active_sessions: int

class CreateSessionResponse(BaseModel):
    session_id: str
    status: Literal["created"]
    cwd: str

class StopSessionResponse(BaseModel):
    session_id: str
    status: Literal["stopped"]

class SessionInfoResponse(BaseModel):
    session_id: str
    status: Literal["running", "stopped"]
    created_at: datetime
    last_activity: datetime
    loaded_plugins: List[str]
    execution_count: int
    cwd: str

class LoadPluginResponse(BaseModel):
    name: str
    status: Literal["loaded"]

class ArtifactModel(BaseModel):
    name: str
    type: str  # "image", "file", "chart", "svg", etc.
    mime_type: str
    original_name: str
    file_name: str
    file_content: Optional[str] = None  # Base64 for small files
    file_content_encoding: Optional[str] = None
    preview: str
    download_url: Optional[str] = None  # For large files

class ExecuteCodeResponse(BaseModel):
    execution_id: str
    is_success: bool
    error: Optional[str]
    output: Any
    stdout: List[str]
    stderr: List[str]
    log: List[Tuple[str, str, str]]
    artifact: List[ArtifactModel]
    variables: List[Tuple[str, str]]

class ExecuteStreamResponse(BaseModel):
    execution_id: str
    stream_url: str

class UpdateVariablesResponse(BaseModel):
    status: Literal["updated"]
    variables: Dict[str, str]

class ErrorResponse(BaseModel):
    detail: str
```

### 7.3 SSE Event Models

```python
class OutputEvent(BaseModel):
    type: Literal["stdout", "stderr"]
    text: str

class ResultEvent(BaseModel):
    execution_id: str
    is_success: bool
    error: Optional[str]
    output: Any
    stdout: List[str]
    stderr: List[str]
    log: List[Tuple[str, str, str]]
    artifact: List[ArtifactModel]
    variables: List[Tuple[str, str]]
```

---

## 8. Sequence Diagrams

### 8.1 Auto-Start Local Server Flow

```
┌────────────┐     ┌──────────────────────┐     ┌─────────────────┐     ┌────────────┐
│ TaskWeaver │     │ExecutionServiceProv. │     │ ServerLauncher  │     │  Server    │
│   Main     │     │                      │     │                 │     │  Process   │
└─────┬──────┘     └──────────┬───────────┘     └────────┬────────┘     └──────┬─────┘
      │                       │                          │                     │
      │  initialize()         │                          │                     │
      │──────────────────────▶│                          │                     │
      │                       │                          │                     │
      │                       │  is_server_running()?    │                     │
      │                       │─────────────────────────▶│                     │
      │                       │                          │                     │
      │                       │  No                      │                     │
      │                       │◀─────────────────────────│                     │
      │                       │                          │                     │
      │                       │  start()                 │                     │
      │                       │─────────────────────────▶│                     │
      │                       │                          │                     │
      │                       │                          │  subprocess.Popen   │
      │                       │                          │────────────────────▶│
      │                       │                          │                     │
      │                       │                          │  (server starts)    │
      │                       │                          │                     │
      │                       │                          │  wait for ready     │
      │                       │                          │─ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│
      │                       │                          │                     │
      │                       │                          │  health check OK    │
      │                       │                          │◀─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
      │                       │                          │                     │
      │                       │  ready                   │                     │
      │                       │◀─────────────────────────│                     │
      │                       │                          │                     │
      │  ready                │                          │                     │
      │◀──────────────────────│                          │                     │
      │                       │                          │                     │
```

### 8.2 Code Execution Flow

```
┌────────────┐     ┌────────────────┐     ┌─────────────────┐     ┌────────────┐
│ CodeExec.  │     │ExecutionClient │     │    Server       │     │Environment │
└─────┬──────┘     └───────┬────────┘     └────────┬────────┘     └──────┬─────┘
      │                    │                       │                     │
      │  execute_code()    │                       │                     │
      │───────────────────▶│                       │                     │
      │                    │                       │                     │
      │                    │  POST /execute        │                     │
      │                    │──────────────────────▶│                     │
      │                    │                       │                     │
      │                    │                       │  execute_code()     │
      │                    │                       │────────────────────▶│
      │                    │                       │                     │
      │                    │                       │   (Jupyter kernel   │
      │                    │                       │    executes code)   │
      │                    │                       │                     │
      │                    │                       │  ExecutionResult    │
      │                    │                       │◀────────────────────│
      │                    │                       │                     │
      │                    │  200 {result}         │                     │
      │                    │◀──────────────────────│                     │
      │                    │                       │                     │
      │  ExecutionResult   │                       │                     │
      │◀───────────────────│                       │                     │
      │                    │                       │                     │
```

### 8.3 Plugin Loading Flow

```
┌────────────┐     ┌────────────────┐     ┌─────────────────┐     ┌────────────┐
│ CodeExec.  │     │ExecutionClient │     │    Server       │     │Environment │
└─────┬──────┘     └───────┬────────┘     └────────┬────────┘     └──────┬─────┘
      │                    │                       │                     │
      │  Plugin source     │                       │                     │
      │  read from disk    │                       │                     │
      │                    │                       │                     │
      │  load_plugin(      │                       │                     │
      │    name, code,     │                       │                     │
      │    config)         │                       │                     │
      │───────────────────▶│                       │                     │
      │                    │                       │                     │
      │                    │  POST /plugins        │                     │
      │                    │  {name, code, config} │                     │
      │                    │──────────────────────▶│                     │
      │                    │                       │                     │
      │                    │                       │  load_plugin()      │
      │                    │                       │────────────────────▶│
      │                    │                       │                     │
      │                    │                       │  (magic commands    │
      │                    │                       │   register plugin)  │
      │                    │                       │                     │
      │                    │                       │  OK                 │
      │                    │                       │◀────────────────────│
      │                    │                       │                     │
      │                    │  200 {loaded}         │                     │
      │                    │◀──────────────────────│                     │
      │                    │                       │                     │
      │  OK                │                       │                     │
      │◀───────────────────│                       │                     │
```

---

## 9. Multi-Session Architecture

### 9.1 Session Isolation Model

The execution server supports multiple concurrent sessions, each with complete isolation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION SERVER (FastAPI)                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     ServerSessionManager                              │  │
│  │                                                                       │  │
│  │   _sessions: Dict[str, ServerSession]                                 │  │
│  │   _lock: threading.RLock()  ← Thread-safe access                      │  │
│  │                                                                       │  │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │  │
│  │   │ ServerSession   │  │ ServerSession   │  │ ServerSession   │      │  │
│  │   │ "session-001"   │  │ "session-002"   │  │ "session-003"   │      │  │
│  │   │                 │  │                 │  │                 │      │  │
│  │   │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │      │  │
│  │   │ │ Environment │ │  │ │ Environment │ │  │ │ Environment │ │      │  │
│  │   │ └──────┬──────┘ │  │ └──────┬──────┘ │  │ └──────┬──────┘ │      │  │
│  │   └────────┼────────┘  └────────┼────────┘  └────────┼────────┘      │  │
│  └────────────┼────────────────────┼────────────────────┼───────────────┘  │
│               │                    │                    │                  │
└───────────────┼────────────────────┼────────────────────┼──────────────────┘
                │                    │                    │
                ▼                    ▼                    ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│   Jupyter Kernel 1    │ │   Jupyter Kernel 2    │ │   Jupyter Kernel 3    │
│   (isolated process)  │ │   (isolated process)  │ │   (isolated process)  │
│                       │ │                       │ │                       │
│   session_var: {...}  │ │   session_var: {...}  │ │   session_var: {...}  │
│   plugins: [...]      │ │   plugins: [...]      │ │   plugins: [...]      │
│   cwd: /sessions/001  │ │   cwd: /sessions/002  │ │   cwd: /sessions/003  │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
```

### 9.2 Key Components

#### ServerSessionManager

Central coordinator for all sessions:

```python
class ServerSessionManager:
    _sessions: Dict[str, ServerSession] = {}  # Session storage
    _lock: threading.RLock()                   # Thread-safe access
    work_dir: str                              # Base directory for session data
```

| Responsibility | Implementation |
|----------------|----------------|
| Session storage | `Dict[str, ServerSession]` keyed by session_id |
| Thread safety | `threading.RLock()` for all session access |
| Session isolation | Each session has its own `Environment` instance |
| Async execution | `run_in_executor()` to avoid blocking FastAPI event loop |

#### ServerSession

Per-session state container:

```python
@dataclass
class ServerSession:
    session_id: str
    environment: Environment      # Own kernel instance
    created_at: datetime
    last_activity: datetime
    loaded_plugins: List[str]
    execution_count: int
    cwd: str                      # Isolated working directory
    session_dir: str              # Session data directory
```

#### Environment

Wraps Jupyter kernel management:

```python
class Environment:
    session_dict: Dict[str, EnvSession] = {}     # Kernel sessions
    client_dict: Dict[str, BlockingKernelClient] # Kernel clients
    multi_kernel_manager: MultiKernelManager     # Jupyter kernel manager
```

### 9.3 Session Isolation

| Aspect | How Isolated |
|--------|--------------|
| **Jupyter Kernel** | Each session runs in a separate OS process |
| **Working Directory** | `{work_dir}/sessions/{session_id}/cwd/` |
| **Session Variables** | Stored per-session in kernel memory |
| **Plugins** | Loaded independently per-session |
| **Artifacts** | Saved to session-specific `cwd` directory |
| **Memory** | Kernel process has its own memory space |

### 9.4 Directory Structure

```
work_dir/
└── sessions/
    ├── session-001/
    │   ├── ces/
    │   │   ├── conn-session-001-knl-xxx.json  # Kernel connection file
    │   │   └── kernel_logging.log              # Kernel logs
    │   └── cwd/
    │       ├── output.png                      # Artifacts saved here
    │       └── data.csv
    ├── session-002/
    │   ├── ces/
    │   └── cwd/
    └── session-003/
        ├── ces/
        └── cwd/
```

### 9.5 Thread Safety

All session access is protected by a reentrant lock:

```python
def create_session(self, session_id: str, ...) -> ServerSession:
    with self._lock:                          # Lock acquired
        if session_id in self._sessions:
            raise ValueError(...)
        # ... create session ...
        self._sessions[session_id] = session  # Safe write
    return session                            # Lock released

def stop_session(self, session_id: str) -> None:
    with self._lock:                          # Lock acquired
        session = self._sessions[session_id]
        session.environment.stop_session(...)
        del self._sessions[session_id]        # Safe delete
```

### 9.6 Async Execution

Code execution is CPU-bound (runs in Jupyter kernel), so it's offloaded to a thread pool to avoid blocking the FastAPI async event loop:

```python
async def execute_code_async(self, session_id, exec_id, code, on_output):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # Default thread pool
        lambda: self.execute_code(session_id, exec_id, code, on_output),
    )
```

### 9.7 Artifact Handling

Artifacts (images, charts, files) are automatically:

1. **Captured** from Jupyter kernel display outputs
2. **Saved** to the session's `cwd` directory
3. **Served** via HTTP at `/api/v1/sessions/{session_id}/artifacts/{filename}`

```python
def _save_inline_artifacts(self, session: ServerSession, result: ExecutionResult):
    for artifact in result.artifact:
        if artifact.file_content and not artifact.file_name:
            # Decode base64 content and save to disk
            file_path = os.path.join(session.cwd, f"{artifact.name}_image.png")
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(artifact.file_content))
            artifact.file_name = file_name  # Update for download URL
```

---

## 10. Error Handling

### 9.1 Error Categories

| Category | HTTP Status | Client Exception | Description |
|----------|-------------|------------------|-------------|
| Authentication | 401 | `ExecutionClientError` | Invalid/missing API key |
| Not Found | 404 | `ExecutionClientError` | Session/artifact not found |
| Conflict | 409 | `ExecutionClientError` | Session already exists |
| Bad Request | 400 | `ExecutionClientError` | Plugin load failed, invalid request |
| Execution Error | 200 | None (in result) | Code execution failed (normal flow) |
| Server Error | 500 | `ExecutionClientError` | Unexpected server failure |
| Connection Error | N/A | `ExecutionClientError` | Cannot connect to server |
| Timeout | N/A | `httpx.TimeoutException` | Request/execution timeout |

---

## 10. Implementation Order

1. **Phase 1: Server Core**
   - `taskweaver/ces/server/models.py`
   - `taskweaver/ces/server/session_manager.py`
   - `taskweaver/ces/server/routes.py`
   - `taskweaver/ces/server/app.py`
   - `taskweaver/ces/server/__main__.py`

2. **Phase 2: Client**
   - `taskweaver/ces/client/execution_client.py`
   - `taskweaver/ces/client/server_launcher.py`

3. **Phase 3: Integration**
   - `taskweaver/ces/manager/execution_service.py`
   - Configuration updates
   - DI module updates

4. **Phase 4: Testing**
   - Unit tests
   - Integration tests

5. **Phase 5: Documentation & Deployment**
   - Update AGENTS.md
   - Dockerfile
   - User documentation

---

## 11. Deployment

### 12.1 Standalone Server

```bash
# Install dependencies
pip install fastapi uvicorn httpx

# Start server
python -m taskweaver.ces.server \
    --host 0.0.0.0 \
    --port 8000 \
    --api-key "your-secret-key" \
    --work-dir /var/taskweaver/sessions
```

### 12.2 Docker Image

```dockerfile
# Dockerfile.executor
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy TaskWeaver package
COPY taskweaver/ ./taskweaver/

# Create workspace directory
RUN mkdir -p /app/workspace

# Environment variables
ENV TASKWEAVER_SERVER_HOST=0.0.0.0
ENV TASKWEAVER_SERVER_PORT=8000
ENV TASKWEAVER_SERVER_WORK_DIR=/app/workspace

EXPOSE 8000

# Run server
CMD ["python", "-m", "taskweaver.ces.server"]
```

### 12.3 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  executor:
    build:
      context: .
      dockerfile: Dockerfile.executor
    ports:
      - "8000:8000"
    volumes:
      - ./workspace:/app/workspace
    environment:
      - TASKWEAVER_SERVER_API_KEY=${API_KEY:-}
      - TASKWEAVER_SERVER_SESSION_TIMEOUT=3600
    restart: unless-stopped
```
