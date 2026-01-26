# Extended Roles - AGENTS.md

Custom role definitions extending TaskWeaver capabilities.

## Structure

```
ext_role/
├── __init__.py
├── web_search/           # Web search role
│   ├── web_search.py
│   └── web_search.role.yaml
├── web_explorer/         # Browser automation role
│   ├── web_explorer.py
│   ├── driver.py         # Selenium/Playwright driver
│   ├── planner.py        # Web action planning
│   └── web_explorer.role.yaml
├── image_reader/         # Image analysis role
│   ├── image_reader.py
│   └── image_reader.role.yaml
├── document_retriever/   # Document RAG role
│   ├── document_retriever.py
│   └── document_retriever.role.yaml
├── recepta/              # Custom tool orchestration
│   ├── recepta.py
│   └── recepta.role.yaml
└── echo/                 # Debug/test echo role
    ├── echo.py
    └── echo.role.yaml
```

## Role YAML Schema

Each role requires a `.role.yaml` file:

```yaml
module: taskweaver.ext_role.{name}.{name}.{ClassName}
alias: {DisplayName}  # Used in message routing
intro: |
  - Capability description line 1
  - Capability description line 2
```

## Creating a New Extended Role

1. Create directory: `ext_role/my_role/`
2. Create `my_role.py`:
```python
from taskweaver.role import Role
from taskweaver.role.role import RoleConfig, RoleEntry

class MyRoleConfig(RoleConfig):
    def _configure(self):
        # Config inherits from parent dir name
        self.custom_setting = self._get_str("custom", "default")

class MyRole(Role):
    @inject
    def __init__(
        self,
        config: MyRoleConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        role_entry: RoleEntry,
    ):
        super().__init__(config, logger, tracing, event_emitter, role_entry)
    
    def reply(self, memory: Memory, **kwargs) -> Post:
        # Implement role logic
        post_proxy = self.event_emitter.create_post_proxy(self.alias)
        # ... process and respond
        return post_proxy.end()
```

3. Create `my_role.role.yaml`:
```yaml
module: taskweaver.ext_role.my_role.my_role.MyRole
alias: MyRole
intro: |
  - This role does X
  - It can handle Y
```

4. Enable in session config:
```json
{
  "session.roles": ["planner", "code_interpreter", "my_role"]
}
```

## Role Discovery

RoleRegistry scans:
- `ext_role/*/\*.role.yaml`
- `code_interpreter/*/\*.role.yaml`

Registry refreshes every 5 minutes (TTL).

## Naming Convention

- Directory name = role name = config namespace
- Class name = PascalCase of directory name
- Alias used for `send_to`/`send_from` in Posts
