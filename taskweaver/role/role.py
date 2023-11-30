from taskweaver.memory import Memory, Post


class Role:
    def reply(self, memory: Memory, event_handler: callable) -> Post:
        pass
