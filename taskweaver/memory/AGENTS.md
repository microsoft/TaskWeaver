# Memory Module - AGENTS.md

Conversation history data model: Post, Round, Conversation, Attachment.

## Structure

```
memory/
├── memory.py         # Memory class - session conversation store
├── conversation.py   # Conversation - list of Rounds
├── round.py          # Round - single user query + responses
├── post.py           # Post - single message between roles
├── attachment.py     # Attachment - typed data on Posts
├── type_vars.py      # Type aliases (RoleName, etc.)
├── experience.py     # Experience storage and retrieval
├── compression.py    # RoundCompressor for prompt compression
├── plugin.py         # PluginModule for DI
├── shared_memory_entry.py  # SharedMemoryEntry for cross-role data
└── utils.py          # Utility functions
```

## Data Model Hierarchy

```
Memory
└── Conversation
    └── Round[]
        ├── user_query: str
        ├── state: "created" | "finished" | "failed"
        └── Post[]
            ├── send_from: str (role name)
            ├── send_to: str (role name)
            ├── message: str
            └── Attachment[]
                ├── type: AttachmentType
                ├── content: str
                └── extra: Any
```

## Key Classes

### Post (post.py)
```python
@dataclass
class Post:
    id: str
    send_from: str
    send_to: str
    message: str
    attachment_list: List[Attachment]
    
    @staticmethod
    def create(message: str, send_from: str, send_to: str) -> Post
```

### AttachmentType (attachment.py)
```python
class AttachmentType(str, Enum):
    # Planning
    plan = "plan"
    current_plan_step = "current_plan_step"
    
    # Code execution
    reply_content = "reply_content"  # Generated code
    verification = "verification"
    execution_status = "execution_status"
    execution_result = "execution_result"
    
    # Control flow
    revise_message = "revise_message"
    invalid_response = "invalid_response"
    
    # Shared state
    shared_memory_entry = "shared_memory_entry"
    session_variables = "session_variables"
```

### SharedMemoryEntry (shared_memory_entry.py)
Cross-role communication:
```python
@dataclass
class SharedMemoryEntry:
    type: str           # "plan", "experience_sub_path", etc.
    scope: str          # "round" or "conversation"
    content: str
```

## Memory Patterns

### Role-specific Round Filtering
```python
# Get rounds relevant to a specific role
rounds = memory.get_role_rounds(role="Planner", include_failure_rounds=False)
```

### Shared Memory Queries
```python
# Get shared entries by type
entries = memory.get_shared_memory_entries(entry_type="plan")
```

## Serialization

All dataclasses support `to_dict()` and `from_dict()` for YAML/JSON persistence.
Experience saving: `memory.save_experience(exp_dir, thin_mode=True)`
