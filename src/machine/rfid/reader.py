from __future__ import annotations

import time
from collections.abc import Callable
from threading import Thread
from typing import TYPE_CHECKING, Self

from src.logger_handler import LoggerHandler

if TYPE_CHECKING:
    from src.machine.rfid.base import RFIDInterface

_logger = LoggerHandler("RFIDReader")


class RFIDReader:
    """Singleton facade around the active :class:`RFIDInterface` controller.

    The concrete controller is wired in by ``MachineController.init_machine()``
    via :meth:`attach`. Callers can hold a reference to ``RFIDReader()`` even
    before the machine is initialized — :attr:`rfid` simply stays ``None``
    until a controller is attached.
    """

    _instance: Self | None = None

    def __new__(cls) -> Self:
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.is_active = False
        self.rfid: RFIDInterface | None = None
        self._initialized = True

    def attach(self, controller: RFIDInterface | None) -> None:
        """Wire the active RFID controller. Pass ``None`` to detach."""
        self.rfid = controller

    def read_rfid(self, side_effect: Callable[[str, str], None], read_delay_s: float = 0.5) -> None:
        """Start the rfid reader, calls an side effect with the read value and id."""
        if self.is_active:
            return
        rfid_thread = Thread(target=self._read_thread, args=(side_effect, read_delay_s), daemon=True)
        rfid_thread.start()

    def _read_thread(self, side_effect: Callable[[str, str], None], read_delay_s: float = 0.5) -> None:
        """Execute the reading until reads a value or got canceled."""
        if self.rfid is None or self.is_active:
            return
        text = None
        self.is_active = True
        while self.is_active:
            text, _id = self.rfid.read_card()
            if text is not None and _id is not None:
                side_effect(text, _id)
                time.sleep(read_delay_s)
            else:
                # do a small sleep in case reader have no internal sensing
                time.sleep(0.1)
        self.is_active = False

    def write_rfid(self, value: str, side_effect: Callable[[str], None] | None = None) -> None:
        """Write the value to the RFID."""
        if self.is_active:
            return
        rfid_thread = Thread(
            target=self._write_thread,
            args=(
                value,
                side_effect,
            ),
            daemon=True,
        )
        rfid_thread.start()

    def _write_thread(self, text: str, side_effect: Callable[[str], None] | None = None) -> None:
        """Execute the writing until successful or canceled."""
        if self.rfid is None or self.is_active:
            return
        self.is_active = True
        while self.is_active:
            success = self.rfid.write_card(text)
            if success:
                if side_effect:
                    side_effect(text)
                break
            time.sleep(0.1)
        self.is_active = False

    def cancel_reading(self) -> None:
        """Cancel the reading loop."""
        self.is_active = False
