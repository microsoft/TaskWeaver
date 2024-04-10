# Conversation

A conversation is a data concept in TaskWeaver which contains a dialog between the user and the TaskWeaver app.
Each [session](session.md) has a corresponding conversation.

```python
@dataclass
class Conversation:
    """A conversation denotes the interaction with the user, which is a collection of rounds.
    The conversation is also used to construct the Examples.

    Args:
        id: the unique id of the conversation.
        rounds: a list of rounds.
        plugins: a list of plugins that are used in the conversation.
        enabled: whether the conversation is enabled, used for Example only.
    """

    id: str = ""
    rounds: List[Round] = field(default_factory=list)
    plugins: List[PluginEntry] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    enabled: bool = True
```

A conversation is a collection of [rounds](round.md), where each round starts with the user's input and ends with the TaskWeaver app's response to the user.
The `plugins` are the [plugins](plugin.md) available in the conversation, and the `roles` are the [roles](role.md) that the conversation is associated with.


In TaskWeaver, the conversation is also used to store the [Examples](../customization/example/example.md).
The examples in the project folder are parsed into Conversations in the memory, and then composed into the prompt
of the Planner or the CodeInterpreter.
The `enabled` flag is used to control if this conversation is presented in the prompt.





