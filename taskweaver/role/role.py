import abc

from taskweaver.memory import Memory, Post


class Role(abc.ABC):
    @abc.abstractmethod
    def reply(self, memory: Memory) -> Post:
        pass
