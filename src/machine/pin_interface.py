"""Pin abstraction interface for GPIO and I2C expanders."""

from abc import abstractmethod
from typing import Protocol


class PinInterface(Protocol):
    """Interface for controlling individual pins (GPIO or I2C expander pins)."""

    @abstractmethod
    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the pin for input or output.

        Args:
        ----
            is_input: True for input mode, False for output mode
            pull_down: True for pull-down, False for pull-up (only for input mode)

        """
        raise NotImplementedError

    @abstractmethod
    def activate(self) -> None:
        """Activate the pin (set to HIGH/ON state)."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the pin (set to LOW/OFF state)."""
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources associated with the pin."""
        raise NotImplementedError

    @abstractmethod
    def read(self) -> bool:
        """Read the current state of the pin.

        Returns
        -------
            bool: True if pin is HIGH, False if LOW

        """
        raise NotImplementedError
