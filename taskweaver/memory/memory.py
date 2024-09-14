from __future__ import annotations

import copy
import os
from typing import Dict, List, Tuple

from taskweaver.memory import SharedMemoryEntry
from taskweaver.memory.attachment import AttachmentType
from taskweaver.memory.conversation import Conversation
from taskweaver.memory.round import Round
from taskweaver.memory.type_vars import RoleName, SharedMemoryEntryType
from taskweaver.module.prompt_util import PromptUtil
from taskweaver.utils import write_yaml


class Memory:
    """
    Memory is used to store all the conversations in the system,
    which should be initialized when creating a session.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.conversation = Conversation.init()

    def create_round(self, user_query: str) -> Round:
        """Create a round with the given query."""
        round = Round.create(user_query=user_query)
        self.conversation.add_round(round)
        return round

    def get_role_rounds(self, role: RoleName, include_failure_rounds: bool = False) -> List[Round]:
        """Get all the rounds of the given role in the memory.
        TODO: better do cache here to avoid recreating the round list (new object) every time.

        Args:
            role: the role of the memory.
            include_failure_rounds: whether to include the failure rounds.
        """
        rounds_from_role: List[Round] = []
        for round in self.conversation.rounds:
            if round.state == "failed" and not include_failure_rounds:
                continue
            new_round = Round.create(
                user_query=round.user_query,
                id=round.id,
                state=round.state,
            )
            for post in round.post_list:
                if post.send_from == role or post.send_to == role:
                    new_round.add_post(copy.deepcopy(post))
            rounds_from_role.append(new_round)
        # Remove the temporal parts from the text of the posts of rounds
        for round in rounds_from_role[:-1]:
            for post in round.post_list:
                post.message = PromptUtil.remove_parts(
                    post.message,
                    delimiter=PromptUtil.DELIMITER_TEMPORAL,
                )
        # Remove the delimiters from the text of the posts of the last round
        for post in rounds_from_role[-1].post_list:
            post.message = PromptUtil.remove_all_delimiters(post.message)

        return rounds_from_role

    def save_experience(self, exp_dir: str, thin_mode: bool = True) -> None:
        raw_exp_path = os.path.join(exp_dir, f"raw_exp_{self.session_id}.yaml")
        if thin_mode:
            import copy

            conversation = copy.deepcopy(self.conversation)
            for round in conversation.rounds:
                for post in round.post_list:
                    post.attachment_list = [x for x in post.attachment_list if x.type == AttachmentType.plan]
            write_yaml(raw_exp_path, conversation.to_dict())
        else:
            write_yaml(raw_exp_path, self.conversation.to_dict())

    def get_shared_memory_entries(
        self,
        entry_type: SharedMemoryEntryType,
    ) -> List[SharedMemoryEntry]:
        """Get the shared memory entries of the given type and scope.
        entry_scope: "round" or "conversation"
        """
        entry_dict: Dict[str, Tuple[SharedMemoryEntry, int]] = {}
        order_at = 0

        for round in self.conversation.rounds:
            # Check if the round is the last round
            is_last_round = round.id == self.conversation.rounds[-1].id
            for post in round.post_list:
                for attachment in post.attachment_list:
                    if attachment.type == AttachmentType.shared_memory_entry:
                        assert attachment.extra is not None
                        entry: SharedMemoryEntry = attachment.extra
                        if entry.type == entry_type:
                            if entry.scope == "conversation" or is_last_round:
                                # if multiple entries with the same role, only keep the last one
                                entry_dict[post.send_from] = (entry, order_at)
                                order_at += 1

        # Sort the entries by the order_at
        entries_with_order = list(entry_dict.values())
        entries_with_order.sort(key=lambda x: x[1])
        return [e[0] for e in entries_with_order]

    def from_yaml(self, session_id: str, path: str) -> Memory:
        """Load the memory from a yaml file."""
        conversation = Conversation.from_yaml(path)
        self.conversation = conversation
        self.session_id = session_id
        return self
