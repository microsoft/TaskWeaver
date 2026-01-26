# Code Interpreter - AGENTS.md

Code generation and execution roles with multiple variants.

## Structure

```
code_interpreter/
├── interpreter.py              # Interpreter ABC (update_session_variables)
├── code_executor.py            # CodeExecutor - bridges to CES
├── code_verification.py        # AST-based code validation
├── plugin_selection.py         # Plugin selection logic
├── code_interpreter/           # Full code interpreter
│   ├── code_interpreter.py     # CodeInterpreter role (~320 lines)
│   ├── code_generator.py       # LLM-based code generation
│   └── code_interpreter.role.yaml
├── code_interpreter_cli_only/  # CLI-only variant (no plugins)
│   ├── code_interpreter_cli_only.py
│   ├── code_generator_cli_only.py
│   └── code_interpreter_cli_only.role.yaml
└── code_interpreter_plugin_only/  # Plugin-only variant (no free-form code)
    ├── code_interpreter_plugin_only.py
    ├── code_generator_plugin_only.py
    └── code_interpreter_plugin_only.role.yaml
```

## Role Variants

| Variant | Plugins | Free-form Code | Use Case |
|---------|---------|----------------|----------|
| `code_interpreter` | Yes | Yes | Full capability |
| `code_interpreter_cli_only` | No | Yes | Restricted to CLI |
| `code_interpreter_plugin_only` | Yes | No | Only plugin calls |

## Key Classes

### CodeInterpreter (Role, Interpreter)
- Orchestrates: CodeGenerator -> verification -> CodeExecutor
- Retry logic: up to `max_retry_count` (default 3) on failures
- Config: `CodeInterpreterConfig` (verification settings, blocked functions)

### CodeGenerator
- LLM-based code generation from conversation context
- Outputs: code + explanation via PostEventProxy
- Configurable verification: allowed_modules, blocked_functions

### CodeExecutor
- Wraps CES Environment
- Plugin loading from PluginRegistry
- Session variable management

## Code Verification (code_verification.py)

AST-based checks:
- `allowed_modules`: Whitelist of importable modules
- `blocked_functions`: Blacklist (default: `eval`, `exec`, `open`, etc.)

```python
code_verify_errors = code_snippet_verification(
    code,
    code_verification_on=True,
    allowed_modules=["pandas", "numpy"],
    blocked_functions=["eval", "exec"],
)
```

## Role YAML Schema

```yaml
module: taskweaver.code_interpreter.code_interpreter.code_interpreter.CodeInterpreter
alias: CodeInterpreter  # Used in message routing
intro: |
  - Description of capabilities
  - {plugin_description} placeholder for dynamic plugin list
```

## Execution Flow

1. `reply()` called with Memory context
2. CodeGenerator produces code via LLM
3. Code verification (if enabled)
4. CodeExecutor runs code in CES kernel
5. Results formatted back to Post
