import os.path

from taskweaver.memory import Memory, Post
from taskweaver.utils import read_yaml


class Role:
    def get_intro(self) -> str:
        name = self.config.name
        intro_file = os.path.join(
            os.path.dirname(__file__),
            f"{name}_intro.yaml",
        )
        intro = ""
        if os.path.exists(intro_file):
            meta_intro = read_yaml(intro_file)
            name = meta_intro.get("name_in_prompt")
            description = meta_intro.get("intro")
            intro = f"{name}:\n {description}"
        return intro

    def reply(self, memory: Memory, **kwargs) -> Post:
        pass
