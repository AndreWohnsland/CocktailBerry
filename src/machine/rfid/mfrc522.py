# pyright: reportMissingImports=false
from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.rfid.base import RFIDInterface

if TYPE_CHECKING:
    from src.config.config_types import BaseRfidConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("MFRC522Reader")

_NOT_AVAILABLE_MSG = "Could not import mfrc522, either it's not installed or it is not for your OS! RFID will not work."

try:
    from mfrc522 import SimpleMFRC522

    MFRC522_AVAILABLE = True
except (AttributeError, ModuleNotFoundError, RuntimeError):
    MFRC522_AVAILABLE = False


class MFRC522Reader(RFIDInterface):
    """Reader for common RC522 modules (SPI)."""

    def __init__(self, config: BaseRfidConfig, hardware: HardwareContext) -> None:
        super().__init__(config, hardware)
        if not MFRC522_AVAILABLE:
            raise RuntimeError(_NOT_AVAILABLE_MSG)
        self.rfid = SimpleMFRC522()  # pylint: disable=E0601

    def read_card(self) -> tuple[str | None, str | None]:
        _id, text = self.rfid.read_no_block()
        if text is not None:
            text = text.strip()
        return text, _id

    def write_card(self, text: str) -> bool:
        _id, _ = self.rfid.write_no_block(text)
        return _id is not None
