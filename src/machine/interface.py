from abc import abstractmethod
from typing import Any, Protocol


class SinglePin(Protocol):
    """Interface for individual pin control.

    This protocol defines the interface that all single-pin implementations must follow,
    regardless of the underlying hardware (GPIO, MCP23017, PCF8574).
    """

    pin: int

    @abstractmethod
    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the pin for input or output.

        Args:
            is_input: True for input pin, False for output pin.
            pull_down: True for pull-down resistor, False for pull-up (for input pins).

        """
        raise NotImplementedError

    @abstractmethod
    def activate(self) -> None:
        """Activate the pin (set high for output)."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Deactivate the pin (set low for output)."""
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources associated with the pin."""
        raise NotImplementedError

    @abstractmethod
    def read(self) -> bool:
        """Read the pin state (for input pins).

        Returns:
            True if pin is high, False if low.

        """
        raise NotImplementedError


class PinController(Protocol):
    """Interface to control the pins."""

    @abstractmethod
    def initialize_pin_list(self, pin_list: list[int], is_input: bool = False, pull_down: bool = True) -> None:
        raise NotImplementedError

    @abstractmethod
    def activate_pin_list(self, pin_list: list[int]) -> None:
        raise NotImplementedError

    @abstractmethod
    def close_pin_list(self, pin_list: list[int]) -> None:
        raise NotImplementedError

    @abstractmethod
    def cleanup_pin_list(self, pin_list: list[int] | None = None) -> None:
        pass

    @abstractmethod
    def read_pin(self, pin: int) -> bool:
        pass


class GPIOController:
    def __init__(self, high: Any, low: Any, inverted: bool, pin: int) -> None:
        self.high = high
        self.low = low
        self.inverted = inverted
        self.pin = pin
        if self.inverted:
            self.high, self.low = self.low, self.high

    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def activate(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        raise NotImplementedError


class RFIDController(Protocol):
    """Interface for the RFID reader."""

    @abstractmethod
    def read_card(self) -> tuple[str | None, str | None]:
        raise NotImplementedError

    @abstractmethod
    def write_card(self, text: str) -> bool:
        raise NotImplementedError
