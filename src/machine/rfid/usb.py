# pyright: reportMissingImports=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from src.logger_handler import LoggerHandler
from src.machine.rfid.base import RFIDInterface

if TYPE_CHECKING:
    from src.config.config_types import BaseRfidConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("USBReader")

_NOT_AVAILABLE_MSG = "Could not import pyscard, either it's not installed or it is not for your OS! RFID will not work."

try:
    from smartcard.CardRequest import CardRequest
    from smartcard.CardType import AnyCardType
    from smartcard.PassThruCardService import PassThruCardService
    from smartcard.pcsc.PCSCReader import PCSCReader
    from smartcard.System import readers
    from smartcard.util import toHexString

    USB_AVAILABLE = True
except (AttributeError, ModuleNotFoundError, RuntimeError):
    USB_AVAILABLE = False


# NOTE: usb reader pyscard lib makes it super hard to read/write content, so this is currently only reading UID
class USBReader(RFIDInterface):
    """Reader for USB-connected RFID readers (PC/SC)."""

    GET_UID: ClassVar[list[int]] = [0xFF, 0xCA, 0x00, 0x00, 0x00]

    def __init__(self, config: BaseRfidConfig, hardware: HardwareContext) -> None:
        super().__init__(config, hardware)
        if not USB_AVAILABLE:
            raise RuntimeError(_NOT_AVAILABLE_MSG)
        available: list[PCSCReader] = readers()
        if not available:
            raise RuntimeError("No PC/SC reader found")
        self.reader_name = available[0]

    def read_card(self) -> tuple[str | None, str | None]:
        card_request = CardRequest(cardType=AnyCardType(), timeout=5)
        try:
            service = card_request.waitforcard()
            if not isinstance(service, PassThruCardService):
                return None, None
            conn = service.connection  # pyright: ignore[reportOptionalMemberAccess]
            conn.connect()
            response, sw1, sw2 = conn.transmit(self.GET_UID)
        except Exception:
            # Timeout or other error — no card detected in given interval
            return None, None
        if (sw1, sw2) == (0x90, 0x00):
            return "", toHexString(response).replace(" ", "")
        return None, None

    def write_card(self, text: str) -> bool:
        _logger.log_event("WARNING", "Writing to USB RFID is not supported.")
        return False
