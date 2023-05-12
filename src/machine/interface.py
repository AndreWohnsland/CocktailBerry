from abc import abstractmethod
from typing import List, Optional

# Grace period, will be switched once Python 3.8+ is mandatory
try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol


class PinController(Protocol):  # type: ignore
    """Interface to control the pins"""
    @abstractmethod
    def initialize_pin_list(self, pin_list: List[int]):
        raise NotImplementedError

    @abstractmethod
    def activate_pin_list(self, pin_list: List[int]):
        raise NotImplementedError

    @abstractmethod
    def close_pin_list(self, pin_list: List[int]):
        raise NotImplementedError

    @abstractmethod
    def cleanup_pin_list(self, pin_list: Optional[List[int]] = None):
        pass


class RFIDController(Protocol):
    """Interface for the RFID reader"""
    @abstractmethod
    def read_card(self) -> tuple[Optional[str], Optional[str]]:
        raise NotImplementedError

    @abstractmethod
    def write_card(self, text: str) -> bool:
        raise NotImplementedError
