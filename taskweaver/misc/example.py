import glob
from os import path
from typing import List

from taskweaver.memory.conversation import Conversation


def load_examples(folder: str, has_plugins: bool = False, plugin_name_list: List[str] = []) -> List[Conversation]:
    """
    Load all the examples from a folder.
    If has_plugins is True, then the plugin_name_list is required to check
    if the example uses plugins that are not defined.

    Args:
        folder: the folder path.
        has_plugins: whether the example uses plugins.
        plugin_name_list: the list of plugins that have been defined/loaded.
    """
    example_file_list: List[str] = glob.glob(path.join(folder, "*.yaml"))
    example_conv_pool: List[Conversation] = []
    for yaml_path in example_file_list:
        conversation = Conversation.from_yaml(yaml_path)
        if has_plugins and len(plugin_name_list) > 0:
            plugin_exists = True
            for plugin in conversation.plugins:
                if plugin not in plugin_name_list:
                    plugin_exists = False
            if plugin_exists:
                example_conv_pool.append(conversation)
            else:
                raise ValueError(
                    f"Example {yaml_path} relies on plugins that do not exist.\n"
                    f"Existing plugins: {plugin_name_list}\nRequired plugins: {conversation.plugins}\n",
                )
        else:
            example_conv_pool.append(conversation)
    return example_conv_pool


# def validate_single_example(example_path: str) -> Tuple[bool, List[str]]:
#     error_list: List[str] = []
#     conversation = Conversation.from_yaml(path=example_path, error_list=error_list)
#     if not conversation:
#         return False, error_list
#     required_plugins = conversation.plugins
#     plugin_list = [p.name for p in get_plugin_from_path()]
#     unavailable_plugin_list = [p for p in required_plugins if p not in plugin_list]
#     plugin_not_available = len(unavailable_plugin_list) > 0
#     if plugin_not_available:
#         error_list.append(
#             f"""Example {conversation.name} {example_path} is invalid.
# - containing plugins that are not validated or defined: {unavailable_plugin_list}""",
#         )
#         return False, error_list
#     else:
#         return True, error_list
