# Round

A round is a data concept in TaskWeaver which contains a single round of chat between the user and the TaskWeaver app.

```python
@dataclass
class Round:
    """A round is the basic unit of conversation in the project, which is a collection of posts.

    Args:
        id: the unique id of the round.
        post_list: a list of posts in the round.
        user_query: the query of the user.
        state: the state of the round.
    """

    id: str
    user_query: str
    state: RoundState
    post_list: List[Post]
```

`user_query` is the query of the user, and `post_list` is a list of [posts](post.md) in the round.
The `state` is among "finished", "failed", "created". When the round is created, the state is "created".
When the round is finished successfully, the state is "finished". When the round is failed, the state is "failed".
