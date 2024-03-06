import os.path
from typing import Optional

from taskweaver.memory import Memory, Post
from taskweaver.utils import read_yaml


class Role:
    def __init__(self, name: str, description_file: Optional[str] = None):
        self.name = name

        default_description_file = os.path.join(os.path.abspath("."), f"{name}_intro.yaml")
        if os.path.exists(os.path.join(default_description_file)):
            self.description_file = default_description_file
        else:
            self.description_file = description_file

    def get_description(self) -> str:
        if self.description_file is not None:
            role_description = read_yaml(self.description_file)["intro"]
            return role_description
        else:
            return f"{self.name} has no description."

    def reply(self, memory: Memory) -> Post:
        pass
