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
        board: a dict to store the bulletin of the round.
    """

    id: str
    user_query: str
    state: RoundState
    post_list: List[Post]
    board: Dict[str, str] = field(default_factory=dict)
```

`user_query` is the query of the user, and `post_list` is a list of [posts](post.md) in the round.
The `state` is among "finished", "failed", "created". When the round is created, the state is "created".
When the round is finished successfully, the state is "finished". When the round is failed, the state is "failed".

The `board` is a dictionary to store the bulletin of the round, which can be used to store the information of the round.
This may sound confusing, given that different roles already have their messages in the posts. 
However, the board is used to store critical information that must be aware of in the round context.
A very simple example would be the original user query. 
When the user issues a request to the Planner, the Planner will decompose the task and send a subtask to the CodeInterpreter.
However, the CodeInterpreter needs to know the original user query and the full plan of the Planner to provide a more accurate response.
In this case, the Planner can store the original user query in the board, and the CodeInterpreter can access it when needed.
We provide two methods to access the board: `write_board` and `read_board`.

:::tip
The `board` is a dictionary, and you can store any information you want in the board for the current round.
This is useful to eliminate the issue of information loss between different roles.
:::
