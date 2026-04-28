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
