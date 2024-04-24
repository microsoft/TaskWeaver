from abc import ABC, abstractmethod
from typing import Dict


class Interpreter(ABC):
    
    @abstractmethod
    def update_session_variables(self, session_variables: Dict[str, str]):
        ...