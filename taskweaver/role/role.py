from typing import Optional

from taskweaver.memory import Memory, Post


class Role:
    def reply(
        self,
        memory: Memory,
        event_handler,
        prompt_log_path: Optional[str] = None,
        use_back_up_engine: bool = False,
    ) -> Post:
        pass
