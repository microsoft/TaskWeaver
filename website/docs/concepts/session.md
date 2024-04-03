# Session

A session is a conversation instance that the user has with the TaskWeaver app.
A new session is created when the user interacts with the app.
When the user finishes interacting with the app, the session should be closed.
TaskWeaver allows multiple sessions to be created and managed by the app.
Therefore, multiple users can interact with the app at the same time in different sessions.

![sessions](../../static/img/sessions.png)

A new session is created by calling the `get_session` method of the `TaskWeaverApp` class.
In the background, the `get_session` method creates a new `Session` instance.
```python
class Session:
    @inject
    def __init__(
        self,
        session_id: str,
        workspace: Workspace,
        app_injector: Injector,
        logger: TelemetryLogger,
        tracing: Tracing,
        config: AppSessionConfig,  
        role_registry: RoleRegistry,
    ) -> None:
        """
        Initialize the session.
        :param session_id: The session ID.
        :param workspace: The workspace.
        :param app_injector: The app injector.
        :param logger: The logger.
        :param tracing: The tracing.
        :param config: The configuration.
        :param role_registry: The role registry.
        """
```

:::info
In TaskWeaver, we use an `injector` to take care of most dependency injection.
:::

The `Session` class has the following methods:

```python
def send_message(
    self,
    message: str,
    event_handler: Optional[SessionEventHandler] = None,
    files: Optional[List[Dict[Literal["name", "path", "content"], Any]]] = None,
) -> Round:
    """
    Send a message.
    :param message: The message.
    :param event_handler: The event handler.
    :param files: The files.
    :return: The chat round.
    """
```
`send_message` is used to send a message to the app.
The `message` parameter is the text message that the user sends to the app.
The `event_handler` parameter is a function that handles events during the conversation.
We have defined a variety of events that can be handled by the event handler.
Each event has a specific type and a message.
By implementing the event handler, you can customize the display of events during the conversation.
A very simple example of an event handler is shown below:
```python
class ConsoleEventHandler(SessionEventHandler):
    def handle(self, event: TaskWeaverEvent):
        print(event.t, event.msg)

session.send_message("Hello, how can I help you?", ConsoleEventHandler())
```
The `ConsoleEventHandler` class is a simple event handler that prints the event type and message to the console.

The `files` parameter is used to upload files to the app for processing.

```python
def stop(self) -> None:
    """
    Stop the session.
    This function must be called before the session exits.
    """
```
The `stop` method is used to stop the session.


```python
def update_session_var(
        self,
        variables: Dict[str, str]
):
    """
    Update the session variables.
    :param variables: The variables to update.
    """
```
The `update_session_var` method is used to update the session variables.
A session variable is a key-value pair that is only available in a specific session.
Session variables can be used in the plugins to store information that is specific to the session.
For example, you can store different user names in the session variables of different sessions.
Then, in the plugin, you can access the user name by using the session variable.

```python
@register_plugin
class PluginClass(Plugin):

    def __call__(self, argument1: str):
        ...
        # this line of code in the plugin implementation
        self.ctx.get_session_var("user_name", "anonymous")
        ...
```

The `update_session_var` method can be called multiple times to update multiple session variables.


