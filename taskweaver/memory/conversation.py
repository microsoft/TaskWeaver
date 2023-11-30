from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import List

from taskweaver.memory.round import Round
from taskweaver.utils import create_id

from ..utils import read_yaml, validate_yaml


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
    plugins: List[str] = field(default_factory=list)
    enabled: bool = True

    @staticmethod
    def init():
        """init a conversation with empty rounds and plugins."""
        return Conversation(
            id="conv-" + create_id(),
            rounds=[],
            plugins=[],
            enabled=True,
        )

    def add_round(self, round: Round):
        self.rounds.append(round)

    def to_dict(self):
        """Convert the conversation to a dict."""
        return {
            "id": self.id,
            "plugins": self.plugins,
            "enabled": self.enabled,
            "rounds": [round.to_dict() for round in self.rounds],
        }

    @staticmethod
    def from_yaml(path: str) -> Conversation:  # It is the same as from_dict
        content = read_yaml(path)
        do_validate = False
        valid_state = False
        if do_validate:
            valid_state = validate_yaml(content, schema="example_schema")
        if not do_validate or valid_state:
            enabled = content["enabled"]
            if "plugins" in content.keys():
                plugins = list(content["plugins"])
            else:
                plugins = []
            rounds = [Round.from_dict(r) for r in content["rounds"]]
            return Conversation(id="conv-" + secrets.token_hex(6), rounds=rounds, plugins=plugins, enabled=enabled)
        raise ValueError("Yaml validation failed.")
