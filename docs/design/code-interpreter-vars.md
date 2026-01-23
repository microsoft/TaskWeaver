# Code Interpreter Visible Variable Surfacing

## Problem
The code interpreter generates Python in a persistent kernel but the prompt does not explicitly remind the model which variables already exist in that kernel. This can lead to redundant redefinitions or missed reuse of prior results. We want to surface only the newly defined (non-library) variables to the model in subsequent turns.

## Goals
- Capture the current user/kernel-visible variables after each execution (excluding standard libs and plugins).
- Propagate these variables to the code interpreter’s prompt so it can reuse them.
- Keep noise low: skip modules/functions and internal/builtin names; truncate large reprs.
- Maintain backward compatibility; do not break existing attachments or execution flow.

## Non-Goals
- Full introspection of module internals or large data snapshots.
- Persisting variables across sessions beyond current conversation.

## Design Overview
1) **Collect kernel variables after execution**
   - In the IPython magics layer (`_taskweaver_exec_post_check`) call a context helper to extract visible variables from `local_ns`.
   - Filtering rules:
     - Skip names starting with `_`.
     - Skip builtins and common libs: `__builtins__`, `In`, `Out`, `get_ipython`, `exit`, `quit`, `pd`, `np`, `plt`.
     - Skip modules and any defined functions (only keep data-bearing variables).
     - For other values, store `(name, repr(value))`, truncated to 500 chars and fall back to `<unrepresentable>` on repr errors.
   - Store the snapshot on `ExecutorPluginContext.latest_variables`.

2) **Return variables with execution result**
   - `Executor.get_post_execution_state` now includes `variables` (list of `(name, repr)` tuples).
   - `Environment._parse_exec_result` copies these into `ExecutionResult.variables` (added to dataclass).

3) **Surface variables to user and prompt**
   - `CodeExecutor.format_code_output` renders available variables when there is no explicit result/output, using `pretty_repr` to keep lines concise.
   - `CodeInterpreter.reply` attaches a new `session_variables` attachment (JSON list of tuples) when variables are present.
   - `CodeGenerator.compose_conversation` ignores this attachment in assistant-message rendering but includes it in feedback via `format_code_feedback`, adding an “Available Variables” section for the model’s context.

4) **Attachment type**
   - Added `AttachmentType.session_variables` to carry the variable snapshot per execution.

## Open Items / Next Steps
- Wire the variables directly into the final user turn’s prompt text (e.g., under a “Currently available variables” block) to make reuse even clearer.
- Revisit filtering to ensure we skip large data/DF previews (could add size/type caps).
- Validate end-to-end with unit tests for: variable capture, attachment propagation, prompt inclusion, and formatting.

## Files Touched
- `taskweaver/ces/runtime/context.py` — collect and store visible variables.
- `taskweaver/ces/runtime/executor.py` — expose variables in post-execution state.
- `taskweaver/ces/environment.py` — carry variables into `ExecutionResult`.
- `taskweaver/ces/common.py` — add `variables` to `ExecutionResult` dataclass.
- `taskweaver/memory/attachment.py` — add `session_variables` attachment type.
- `taskweaver/code_interpreter/code_interpreter/code_interpreter.py` — attach captured vars to posts.
- `taskweaver/code_interpreter/code_interpreter/code_generator.py` — ignore var attachments in assistant text; include in feedback.
- `taskweaver/code_interpreter/code_executor.py` — display available variables when no explicit output.
- `taskweaver/utils/__init__.py` — add `pretty_repr` helper for safe truncation.

## Rationale
- Keeps the model aware of live state without inflating prompts with full outputs.
- Avoids re-importing/recomputing when variables already exist.
- Uses attachments so downstream consumers (UI/logs) can also show the state.

## Risks / Mitigations
- **Large values**: truncated repr and filtered types keep prompt size bounded; consider type-based caps later.
- **Noise from libs**: explicit ignore list for common imports; can expand as needed.
- **Compatibility**: new attachment type is additive; existing flows remain unchanged.
