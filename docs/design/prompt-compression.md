# Prompt Compression

## Problem
After multiple conversation rounds, chat history grows long—especially with code and execution results. This risks exceeding LLM context windows and degrading response quality due to attention dilution over lengthy contexts.

## Goals
- Keep prompt size bounded regardless of conversation length.
- Preserve essential context: what user requested, what was executed, what variables exist.
- Maintain code generation correctness by not losing intermediate state references.
- Minimize additional latency and cost from compression overhead.

## Non-Goals
- Real-time streaming compression during generation.
- Vector DB retrieval for selective history (breaks code continuity).
- Cross-session memory persistence.

## Design Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Conversation                              │
├─────────────────────────────────────────────────────────────────┤
│  ConversationSummary  │  Round(n-4) │ Round(n-3) │ ... │ Round(n)│
│  (compressed history) │←─ compress ─→│←────── retain ──────────→│
└─────────────────────────────────────────────────────────────────┘
```

1. **Trigger Condition**: When total rounds reach `rounds_to_compress + rounds_to_retain`
2. **Compression**: Oldest `rounds_to_compress` rounds are summarized via LLM
3. **Retention**: Latest `rounds_to_retain` rounds kept verbatim for context continuity
4. **Accumulation**: Next compression merges new rounds with existing summary

### Components

**RoundCompressor** (`taskweaver/memory/compression.py`)
- Tracks processed rounds to avoid re-compression
- Maintains rolling `previous_summary` state
- Uses configurable LLM (can differ from main model via `llm_alias`)

**Prompt Templates**
- Planner: `taskweaver/planner/compression_prompt.yaml`
  - Focuses on plan steps and execution status
  - Output: `{"ConversationSummary": "..."}`
  
- Code Generator: `taskweaver/code_interpreter/code_interpreter/compression_prompt.yaml`
  - Tracks conversation + variable definitions
  - Output: `{"ConversationSummary": "...", "Variables": [...]}`

### Data Flow

```
compress_rounds(rounds, formatter, template)
    │
    ├─► Check: remaining_rounds < threshold? → return previous_summary + all rounds
    │
    ├─► Extract rounds to compress (oldest N)
    │
    ├─► _summarize()
    │       ├─► Format rounds via rounds_formatter
    │       ├─► Build prompt with PREVIOUS_SUMMARY
    │       ├─► LLM call → new_summary
    │       └─► Update processed_rounds set
    │
    └─► Return (new_summary, retained_rounds)
```

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `round_compressor.rounds_to_compress` | 2 | Rounds summarized per compression cycle |
| `round_compressor.rounds_to_retain` | 3 | Recent rounds kept verbatim |
| `round_compressor.llm_alias` | "" | Optional separate LLM for compression |
| `planner.prompt_compression` | false | Enable for Planner role |
| `code_generator.prompt_compression` | false | Enable for CodeGenerator role |

## Files Touched
- `taskweaver/memory/compression.py` — RoundCompressor implementation
- `taskweaver/planner/compression_prompt.yaml` — Planner summary template
- `taskweaver/code_interpreter/code_interpreter/compression_prompt.yaml` — CodeGen summary template
- `taskweaver/planner/planner.py` — Integration with Planner role
- `taskweaver/code_interpreter/code_interpreter/code_generator.py` — Integration with CodeGenerator

## Rationale
- **Why summarization over retrieval?** Code generation requires continuous context—skipping intermediate code/results breaks execution state references.
- **Why separate templates?** Planner needs plan-centric summaries; CodeGenerator needs variable tracking for reuse.
- **Why configurable LLM?** Compression can use cheaper/faster models since it's less critical than main generation.

## Risks / Mitigations
| Risk | Mitigation |
|------|------------|
| Summary loses critical details | Variables explicitly tracked; recent rounds retained verbatim |
| Additional latency per compression | Triggered infrequently (every N rounds); can use faster LLM |
| Cost overhead | Compression prompts are small; configurable cheaper model |
| Summary quality degrades over time | Rolling summary preserves cumulative context |

---

## Future Improvements

### 1. Adaptive Compression Threshold
**Current**: Fixed `rounds_to_compress` + `rounds_to_retain` trigger.

**Improvement**: Token-based triggering instead of round-based.
```python
# Trigger when estimated prompt exceeds threshold
if estimate_tokens(rounds) > max_prompt_tokens * 0.8:
    compress()
```
**Benefit**: Adapts to variable round sizes (some rounds have large outputs, others minimal).

### 2. Hierarchical Summarization
**Current**: Single-level rolling summary.

**Improvement**: Multi-level summaries for very long conversations.
```
Level 0: Recent rounds (verbatim)
Level 1: Summary of last ~10 rounds  
Level 2: Summary of last ~50 rounds (summary of summaries)
```
**Benefit**: Better preservation of older but important context in extended sessions.

### 3. Selective Compression
**Current**: All rounds in compression window treated equally.

**Improvement**: Importance-weighted compression.
- Preserve rounds with errors/retries (learning signal)
- Preserve rounds with new variable definitions
- Aggressively compress successful single-shot rounds

**Benefit**: Retains debugging-relevant context; reduces noise from routine operations.

### 4. Incremental Variable Tracking
**Current**: Variables tracked in compression summary only.

**Improvement**: Maintain separate, always-current variable registry.
```python
class VariableRegistry:
    def update_from_execution(self, result: ExecutionResult):
        # Track: name, type, shape/size, last_modified_round
        pass
    
    def get_relevant_vars(self, query: str) -> List[VarInfo]:
        # Semantic similarity to current request
        pass
```
**Benefit**: More accurate variable availability; supports "which variables can I use?" queries.

### 5. Compression Quality Validation
**Current**: No validation of summary quality.

**Improvement**: Automated checks before accepting summary.
- Verify mentioned variables actually exist
- Check summary length is within bounds
- Validate JSON structure
- Optional: LLM self-consistency check

**Benefit**: Prevents corrupted summaries from propagating.

### 6. Async/Background Compression
**Current**: Synchronous compression blocks response generation.

**Improvement**: Compress in background after response sent.
```python
async def reply(...):
    response = await generate_response(recent_rounds, previous_summary)
    # Fire-and-forget compression for next turn
    asyncio.create_task(compress_if_needed(rounds))
    return response
```
**Benefit**: Removes compression latency from user-perceived response time.

### 7. Compression Caching
**Current**: Re-summarizes if compression fails or context changes.

**Improvement**: Cache compression results keyed by round IDs.
```python
cache_key = hash(tuple(r.id for r in rounds_to_compress))
if cache_key in compression_cache:
    return compression_cache[cache_key]
```
**Benefit**: Avoids redundant LLM calls on retries or re-runs.

### 8. Domain-Specific Compression Templates
**Current**: Generic templates for Planner and CodeGenerator.

**Improvement**: Task-type aware templates.
- Data analysis: Emphasize DataFrame schemas, column names
- Visualization: Track figure types, customizations applied
- ML workflows: Preserve model configs, metric history

**Benefit**: Higher-fidelity summaries for specialized use cases.

### 9. User-Controllable Compression
**Current**: Fully automatic, user has no visibility.

**Improvement**: Expose compression to users.
- Show "[Summarized N rounds]" indicator in UI
- Allow "expand summary" to see what was compressed
- Let user mark rounds as "important—don't compress"

**Benefit**: Transparency; user control over context preservation.

### 10. Streaming-Compatible Compression
**Current**: Operates on complete rounds only.

**Improvement**: Progressive compression during long outputs.
- Compress stdout/stderr streams in real-time
- Summarize partial results before full execution completes

**Benefit**: Keeps prompts bounded even during long-running executions.
