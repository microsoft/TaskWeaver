# Post

The post is a data concept in TaskWeaver which contains a single message in the conversation.

```python
@dataclass
class Post:
    """
    A post is the message used to communicate between two roles.
    It should always have a text_message to denote the string message,
    while other data formats should be put in the attachment.
    The role can be either a User, a Planner, or others.

    Args:
        id: the unique id of the post.
        send_from: the role who sends the post.
        send_to: the role who receives the post.
        message: the text message in the post.
        attachment_list: a list of attachments in the post.

    """

    id: str
    send_from: RoleName
    send_to: RoleName
    message: str
    attachment_list: List[Attachment]
```

A post is the message used to communicate between two roles. It should always have a text `message` to denote the string message.
In addition, a post has `send_from` and `send_to` roles, which are the roles who send and receive the post, respectively.
In some cases, the `send_from` and `send_to` roles are the same, to denote the self-communication of the role.

The `attachment_list` is a list of [attachments](attachment.md) in the post. 
The attachment is used to store various data other than the text message, such as the code snippet or an artifact file path.
An attachment may be used only by the role who sends the post, or it may be used by the role who receives the post.

In usual cases, the `message` will present in the prompt as the past chat rounds. 
However, the message can sometimes be too long and should only be kept in the current round.
In the next round, the message will be deleted from the prompt to keep the prompt short.
As an example, the CodeInterpreter may generate a long execution result, which only needs to be kept in the current round.
In this case, we provide a way of annotating the message (or part of the message) to be kept in the current round only.

```python
message = PromptUtil.wrap_text_with_delimiter(message, delimiter=PromptUtil.DELIMITER_TEMPORAL)
```

In this way, the message will be kept in the current round only, and will not be presented in the prompt since the next round.
