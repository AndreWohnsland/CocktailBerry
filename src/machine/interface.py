from abc import abstractmethod
from typing import Protocol, List


class PinController(Protocol):
    """Interface to controll the pins"""
    @abstractmethod
    def initialize_pinlist(self, pinlist: List[int]):
        raise NotImplementedError

    @abstractmethod
    def activate_pinlist(self, pinlist: List[int]):
        raise NotImplementedError

    @abstractmethod
    def close_pinlist(self, pinlist: List[int]):
        raise NotImplementedError
