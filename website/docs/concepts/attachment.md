# Attachment

An attachment is a data concept in TaskWeaver which contains additional data other than the text message in the post.

```python
@dataclass
class Attachment:
    """Attachment is the unified interface for responses attached to the text massage.

    Args:
        type: the type of the attachment, which can be "thought", "code", "markdown", or "execution_result".
        content: the content of the response element.
        id: the unique id of the response element.
    """

    id: str
    type: AttachmentType
    content: str
    extra: Optional[Any] = None
```


`AttachmentType` is an Enum class that contains the types of the attachment, which can be "thought", "code", "markdown", or "execution_result".
Among the types, "board" is used to store the information in the board of the round.
When the type is set to "board", the `content` will be updated to the key of the board.
`content` is the content of the response element, which can be the code snippet, the markdown text, or the execution result.


