from abc import ABC, abstractmethod
from typing import List


class PinController(ABC):
    """Interface to controll the pins"""
    @abstractmethod
    def initialize_pinlist(self, pinlist: List[int]):
        pass

    @abstractmethod
    def activate_pinlist(self, pinlist: List[int]):
        pass

    @abstractmethod
    def close_pinlist(self, pinlist: List[int]):
        pass
