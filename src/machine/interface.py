from abc import abstractmethod
from typing import Any, Optional

# Grace period, will be switched once Python 3.8+ is mandatory
try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore[assignment]


class PinController(Protocol):  # type: ignore
    """Interface to control the pins."""

    @abstractmethod
    def initialize_pin_list(self, pin_list: list[int], is_input: bool = False, pull_down: bool = True):
        raise NotImplementedError

    @abstractmethod
    def activate_pin_list(self, pin_list: list[int]):
        raise NotImplementedError

    @abstractmethod
    def close_pin_list(self, pin_list: list[int]):
        raise NotImplementedError

    @abstractmethod
    def cleanup_pin_list(self, pin_list: Optional[list[int]] = None):
        pass

    @abstractmethod
    def read_pin(self, pin: int) -> bool:
        pass


class GPIOController:
    def __init__(
        self,
        high: Any,
        low: Any,
        inverted: bool,
        pin: int
    ):
        self.high = high
        self.low = low
        self.inverted = inverted
        self.pin = pin
        if self.inverted:
            self.high, self.low = self.low, self.high

    @abstractmethod
    def initialize(self):
        raise NotImplementedError

    @abstractmethod
    def activate(self):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError

    @abstractmethod
    def cleanup(self):
        raise NotImplementedError


class RFIDController(Protocol):
    """Interface for the RFID reader."""

    @abstractmethod
    def read_card(self) -> tuple[Optional[str], Optional[str]]:
        raise NotImplementedError

    @abstractmethod
    def write_card(self, text: str) -> bool:
        raise NotImplementedError
