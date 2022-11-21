from abc import abstractmethod
from typing import List

# Grace period, will be switched once Python 3.8+ is mandatory
try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol


class PinController(Protocol):  # type: ignore
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
