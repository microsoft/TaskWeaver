# Code Execution Service (CES) - AGENTS.md

Jupyter kernel-based code execution with local and container modes.

## Structure

```
ces/
├── environment.py    # Environment class - kernel management (~700 lines)
├── common.py         # ExecutionResult, ExecutionArtifact, EnvPlugin dataclasses
├── client.py         # CES client for remote execution
├── __init__.py       # Exports
├── kernel/           # Custom Jupyter kernel implementation
│   └── ext.py        # IPython magic commands for TaskWeaver
├── runtime/          # Runtime support files
└── manager/          # Session/kernel lifecycle management
```

## Key Classes

### Environment (environment.py)
Main orchestrator for code execution:
- `EnvMode.Local`: Direct kernel via `MultiKernelManager`
- `EnvMode.Container`: Docker container with mounted volumes

### ExecutionResult (common.py)
```python
@dataclass
class ExecutionResult:
    execution_id: str
    code: str
    is_success: bool
    error: str
    output: str
    stdout: List[str]
    stderr: List[str]
    log: List[str]
    artifact: List[ExecutionArtifact]
    variables: Dict[str, str]  # Session variables from execution
```

## Execution Flow

1. `start_session()` - Creates kernel (local or container)
2. `load_plugin()` - Registers plugins in kernel namespace
3. `execute_code()` - Runs code, captures output/artifacts
4. `stop_session()` - Cleanup kernel/container

## Container Mode Specifics

- Image: `taskweavercontainers/taskweaver-executor:latest`
- Ports: 5 ports mapped (shell, iopub, stdin, hb, control)
- Volumes: `ces/` and `cwd/` mounted read-write
- Connection file written to `ces/conn-{session}-{kernel}.json`

## Custom Kernel Magics (kernel/ext.py)

```python
%_taskweaver_session_init {session_id}
%_taskweaver_plugin_register {name}
%_taskweaver_plugin_load {name}
%_taskweaver_exec_pre_check {index} {exec_id}
%_taskweaver_exec_post_check {index} {exec_id}
%%_taskweaver_update_session_var
```

## Adding Plugin Support

Plugins are loaded via magic commands:
1. `_taskweaver_plugin_register` - Registers plugin class
2. `_taskweaver_plugin_load` - Instantiates with config

Session variables updated via `%%_taskweaver_update_session_var` magic.
