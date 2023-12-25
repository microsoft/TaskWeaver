import glob
from os import path
from typing import List

from taskweaver.memory.conversation import Conversation


def load_examples(folder: str) -> List[Conversation]:
    """
    Load all the examples from a folder.

    Args:
        folder: the folder path.
    """
    example_file_list: List[str] = glob.glob(path.join(folder, "*.yaml"))
    example_conv_pool: List[Conversation] = []
    for yaml_path in example_file_list:
        conversation = Conversation.from_yaml(yaml_path)
        example_conv_pool.append(conversation)
    return example_conv_pool
