from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

from taskweaver.memory.type_vars import RoundState
from taskweaver.utils import create_id

from .post import Post


@dataclass
class Round:
    """A round is the basic unit of conversation in the project, which is a collection of posts.

    Args:
        id: the unique id of the round.
        post_list: a list of posts in the round.
    """

    id: str
    user_query: str
    state: RoundState
    post_list: List[Post]
    board: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def create(
        user_query: str,
        id: Optional[Union[str, None]] = None,
        state: RoundState = "created",
        post_list: Optional[List[Post]] = None,
        board: Optional[Dict[str, str]] = None,
    ) -> Round:
        """Create a round with the given user query, id, and state."""
        return Round(
            id="round-" + create_id() if id is None else id,
            user_query=user_query,
            state=state,
            post_list=post_list if post_list is not None else [],
            board=board if board is not None else dict(),
        )

    def __repr__(self):
        post_list_str = "\n".join([" " * 2 + str(item) for item in self.post_list])
        return "\n".join(
            [
                "Round:",
                f"- Query: {self.user_query}",
                f"- State: {self.state}",
                f"- Post Num:{len(self.post_list)}",
                f"- Post List: \n{post_list_str}\n\n",
            ],
        )

    def __str__(self):
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the round to a dict."""
        return {
            "id": self.id,
            "user_query": self.user_query,
            "state": self.state,
            "post_list": [post.to_dict() for post in self.post_list],
        }

    @staticmethod
    def from_dict(content: Dict[str, Any]) -> Round:
        """Convert the dict to a round. Will assign a new id to the round."""
        return Round(
            id="round-" + secrets.token_hex(6),
            user_query=content["user_query"],
            state=content["state"],
            post_list=[Post.from_dict(post) for post in content["post_list"]]
            if content["post_list"] is not None
            else [],
        )

    def add_post(self, post: Post):
        """Add a post to the post list."""
        self.post_list.append(post)

    def change_round_state(self, new_state: Literal["finished", "failed", "created"]):
        """Change the state of the round."""
        self.state = new_state

    def write_board(self, role_alias: str, bulletin: str) -> None:
        """Add a bulletin to the round."""
        self.board[role_alias] = bulletin

    def read_board(self, role_alias: Optional[str] = None) -> Union[Dict[str, str], str]:
        """Read the bulletin of the round."""
        if role_alias is None:
            return self.board
        return self.board.get(role_alias, None)
