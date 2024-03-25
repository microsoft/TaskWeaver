from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import List

from taskweaver.memory.plugin import PluginEntry
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
    plugins: List[PluginEntry] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    enabled: bool = True
    plugin_only: bool = False

    @staticmethod
    def init():
        """init a conversation with empty rounds and plugins."""
        return Conversation(
            id="conv-" + create_id(),
            rounds=[],
            plugins=[],
            roles=[],
            enabled=True,
        )

    def add_round(self, round: Round):
        self.rounds.append(round)

    def to_dict(self):
        """Convert the conversation to a dict."""
        return {
            "id": self.id,
            "plugins": [plugin.to_dict() for plugin in self.plugins],
            "roles": self.roles,
            "enabled": self.enabled,
            "rounds": [_round.to_dict() for _round in self.rounds],
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
                plugins = [PluginEntry.from_yaml_content(plugin) for plugin in content["plugins"]]
            else:
                plugins = []

            rounds = [Round.from_dict(r) for r in content["rounds"]]
            roles = set()
            for round in rounds:
                for post in round.post_list:
                    roles.add(post.send_from)
                    roles.add(post.send_to)
            if "plugin_only" in content.keys():
                plugin_only = content["plugin_only"]
            else:
                plugin_only = False
            return Conversation(
                id="conv-" + secrets.token_hex(6),
                rounds=rounds,
                plugins=plugins,
                roles=list(roles),
                enabled=enabled,
                plugin_only=plugin_only,
            )
        raise ValueError("Yaml validation failed.")
