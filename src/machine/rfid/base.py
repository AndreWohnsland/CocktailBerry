from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.config_types import BaseRfidConfig
    from src.machine.hardware import HardwareContext


class RFIDInterface(ABC):
    """Abstract interface for an RFID/NFC reader.

    A single reader instance is shared across the machine via ``HardwareContext``
    and reused by the NFC payment service, the waiter service, and the Qt RFID
    setup windows.

    The ``hardware`` argument gives access to the full HardwareContext (pin
    controller, LEDs, scale, carriage, and the ``extra`` dict of hardware
    extension instances). Built-in drivers may ignore it; custom RFID
    extensions from ``addons/rfid/`` can use it to access pins or shared
    hardware.
    """

    def __init__(self, config: BaseRfidConfig, hardware: HardwareContext) -> None:
        self.config = config
        self.hardware = hardware

    @abstractmethod
    def read_card(self) -> tuple[str | None, str | None]:
        """Return ``(text, id)`` for a card if one is currently in range.

        Should be non-blocking (or use a short timeout) so the read loop can be
        cancelled. Return ``(None, None)`` if no card is available.
        """

    @abstractmethod
    def write_card(self, text: str) -> bool:
        """Write ``text`` to the next card seen and return whether it succeeded."""

    def cleanup(self) -> None:
        """Release any hardware resources held by the reader.

        Default implementation is a no-op. Override if your driver needs to
        close GPIO, SPI, or USB handles.
        """
