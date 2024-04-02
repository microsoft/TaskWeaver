# Role

The role is a concept in TaskWeaver which represents the different roles in the conversation system.
The Planner and CodeInterpreter are two examples of roles in TaskWeaver.

```python
class Role:
    @inject
    def __init__(
        self,
        config: ModuleConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        role_entry: Optional[RoleEntry] = None,
    ):
        """
        The base class for all roles.
        """
```
:::info
We use the `inject` decorator from the `injector` package to inject the dependencies into the role class.
:::

We allow adding extra roles into the system by inheriting the `Role` class and implementing the role in
the `taskweaver.ext_role` module. 