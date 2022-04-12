from abc import ABC, abstractmethod
from typing import List


class PinController(ABC):
    @abstractmethod
    def initialize_pinlist(self, pinlist: List[int]):
        pass

    @abstractmethod
    def activate_pinlist(self, pinlist: List[int]):
        pass

    @abstractmethod
    def close_pinlist(self, pinlist: List[int]):
        pass
