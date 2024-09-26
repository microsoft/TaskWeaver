import glob
from os import path
from typing import List, Optional, Set

from taskweaver.memory.conversation import Conversation


def load_examples(
    folder: str,
    sub_path: Optional[str] = None,
    role_set: Optional[Set[str]] = None,
) -> List[Conversation]:
    """
    Load all the examples from a folder.

    Args:
        folder: the folder path.
        sub_path: the sub-folder path.
        role_set: the roles should be included in the examples.
    """
    if sub_path:
        folder = path.join(folder, sub_path)
    if not path.exists(folder):
        raise FileNotFoundError(f"Folder {folder} does not exist.")

    example_file_list: List[str] = glob.glob(path.join(folder, "*.yaml"))
    example_conv_pool: List[Conversation] = []
    for yaml_path in example_file_list:
        conversation = Conversation.from_yaml(yaml_path)
        if conversation.enabled:
            if not role_set:
                example_conv_pool.append(conversation)
            else:
                roles = conversation.roles
                if set(roles).issubset(role_set):
                    example_conv_pool.append(conversation)

    return example_conv_pool
