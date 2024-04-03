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
the `taskweaver.ext_role` module. We have provided examples on how to implement a new role.
A very simple example is the `Echo` role which echoes the user's message back to the user.

A role should have at least two files: `role_name.py` and `role_name.role.yaml`. 
The files of the role should be put in the `taskweaver/ext_role/role_name` folder.
We need to follow the convention of the role name, which is exactly the same as the folder name,
otherwise an exception will be raised.
We typically use the style of `snake_case` for the role name.

In the `role_name.role.yaml` file, we define the role's configuration. 
This following is `echo.role.yaml` of the `Echo` role configuration.

```yaml
alias: Echo
module: taskweaver.ext_role.echo.echo.Echo
intro : |-
  - Echo is responsible for echoing the user input.
```
The configuration file contains the following fields:
- `alias`: the alias of the role, which is the name of role shown in the prompt and the conversation.
- `module`: the module path of the role class. TaskWeaver will import the module and instantiate the role class.
- `intro`: the introduction of the role, which will be shown in Planner's prompt for choosing the role for certain tasks.

In the `role_name.py` file, we define the role class. The following is `echo.py` of the `Echo` role class.

```python
class EchoConfig(RoleConfig):
    def _configure(self):
        # configuration for the Echo role
        # can be configured in the project configuration file with `echo.decorator`
        self.decorator = self._get_str("decorator", "")


class Echo(Role):
    @inject
    def __init__(
        self,
        config: EchoConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        role_entry: RoleEntry,
    ):
        # configuration for the parent class; this is required
        super().__init__(config, logger, tracing, event_emitter, role_entry)

    def reply(self, memory: Memory, **kwargs) -> Post:
        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )

        # obtain the query from the last round
        last_post = rounds[-1].post_list[-1]

        post_proxy = self.event_emitter.create_post_proxy(self.alias)

        post_proxy.update_send_to(last_post.send_from)
        post_proxy.update_message(
            self.config.decorator +
            last_post.message +
            self.config.decorator
        )

        return post_proxy.end()
```

The role implementation should inherit the `Role` class and implement the `reply` method.
The above example demonstrates how to get the query from the last round.
The `reply` function of the Echo role is simply echoing the user's message back to the user with optional decoration.
The `reply` function should return a `Post` object, which is the response of the role to the user.

We provide facilities to help the role to interact with the memory, the event emitter, and the logger.
For example, the `event_emitter.create_post_proxy` function is used to create a `PostProxy` object, which is a helper class to create a `Post` object.
The `PostProxy` object is used to update the `Post` object with the new message, send_to, and other attributes.
Once the `PostProxy` object is updated, the event emitter will send this event to a handler to display the event to a frontend.

To enable the role in TaskWeaver, we need to add the role configuration to the `taskweaver_config.json` file.
The following is an example of the `taskweaver_config.json` file with the `Echo` role configuration
in addition to the `Planner` and `CodeInterpreter` roles. Note that the name of the role should be 
the same as the folder name of the role, **not** the alias.

```json
{
    "session.roles": ["planner", "echo", "code_interpreter"]
}
```

:::tip
**How to determine if I should create a new role? or implement a new plugin for the CodeInterpreter?**
The answer depends on the functionality you want to implement.
If the functionality is to reply in text message given a user query, and you don't envision the need to process the reply text in code, 
you should create a new role.
In contrast, if the functionality is to process the user query and return the result in a structured format, 
or if both input and output are in a structured format, you should implement a new plugin for the CodeInterpreter.
:::
