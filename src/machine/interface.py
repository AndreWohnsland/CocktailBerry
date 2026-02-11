from __future__ import annotations

from abc import abstractmethod
from typing import Protocol


class SinglePinController(Protocol):
    @abstractmethod
    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
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

    @abstractmethod
    def read(self) -> bool:
        raise NotImplementedError


class RFIDController(Protocol):
    """Interface for the RFID reader."""

    @abstractmethod
    def read_card(self) -> tuple[str | None, str | None]:
        raise NotImplementedError

    @abstractmethod
    def write_card(self, text: str) -> bool:
        raise NotImplementedError
