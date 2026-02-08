# pyright: reportMissingImports=false
import os
import time
from collections.abc import Callable, Iterator
from itertools import cycle
from threading import Thread
from typing import ClassVar, Self

from src.config.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.machine.interface import RFIDController

_logger = LoggerHandler("RFIDReader")


_BASE_NOT_POSSIBLE = "Could not import {}, either it's not installed or it is not for your OS! RFID will not work."

_ERROR_SELECTION_NOT_POSSIBLE = {
    "No": "Please select RFID type other than 'No' to use RFID",
    "MFRC522": _BASE_NOT_POSSIBLE.format("mfrc522"),
    "USB": _BASE_NOT_POSSIBLE.format("pyscard"),
}

_RFID_TYPES: tuple[str, ...] = ("No", "MFRC522", "USB")
_NO_MODULE: dict[str, bool] = dict.fromkeys(_RFID_TYPES, True)
_ERROR: dict[str, str | None] = dict.fromkeys(_RFID_TYPES)

try:
    from mfrc522 import SimpleMFRC522

    _NO_MODULE["MFRC522"] = False
except (AttributeError, ModuleNotFoundError, RuntimeError):
    _ERROR["MFRC522"] = _ERROR_SELECTION_NOT_POSSIBLE["MFRC522"]

try:
    from smartcard.CardRequest import CardRequest
    from smartcard.CardType import AnyCardType
    from smartcard.PassThruCardService import PassThruCardService
    from smartcard.pcsc.PCSCReader import PCSCReader
    from smartcard.System import readers
    from smartcard.util import toHexString

    _NO_MODULE["USB"] = False
except (AttributeError, ModuleNotFoundError, RuntimeError):
    _ERROR["USB"] = _ERROR_SELECTION_NOT_POSSIBLE["USB"]


class RFIDReader:
    _instance: Self | None = None

    def __new__(cls) -> Self:
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.is_active = False
        err = _ERROR.get(cfg.RFID_READER)
        if err is not None:
            _logger.log_event("ERROR", err)
        self.rfid = self._select_rfid()
        self._initialized = True

    @classmethod
    def _select_rfid(cls) -> RFIDController | None:
        """Select the controller defined in config."""
        if "MOCK_RFID" in os.environ:
            _logger.warning("Using mock RFID reader.")
            return _MockReader()
        no_module = _NO_MODULE.get(cfg.RFID_READER, True)
        if no_module:
            return None
        reader: dict[str, Callable[[], RFIDController | None]] = {
            "No": lambda: None,
            "USB": _UsbReader,
            "MFRC522": _BasicMFRC522,
        }
        return reader.get(cfg.RFID_READER, lambda: None)()

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


class _BasicMFRC522(RFIDController):
    """Reader for common RC522 modules."""

    def __init__(self) -> None:
        self.rfid = SimpleMFRC522()  # pylint: disable=E0601

    def read_card(self) -> tuple[str | None, str | None]:
        _id, text = self.rfid.read_no_block()
        if text is not None:
            text = text.strip()
        return text, _id

    def write_card(self, text: str) -> bool:
        _id, _ = self.rfid.write_no_block(text)
        return _id is not None


# NOTE: usb reader pyscard lib makes it super hard to read/write content, so this is currently only reading UID
class _UsbReader(RFIDController):
    """Reader for USB connected RFID readers."""

    GET_UID: ClassVar[list[int]] = [0xFF, 0xCA, 0x00, 0x00, 0x00]

    def __init__(self) -> None:
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


class _MockReader(RFIDController):
    """Mock RFID reader for testing purposes."""

    def __init__(self) -> None:
        self.mocked_ids: Iterator[str] = cycle(["33DFE41A", "9A853011"])
        self.current_id: str | None = None
        self.last_changed: float = 0

    def read_card(self) -> tuple[str | None, str | None]:
        text = "Mocked RFID Data"  # we will not use this usually
        # change the id every 1 minute
        time_window_sec = 60
        time.sleep(5)
        if time.time() - self.last_changed > time_window_sec:
            self.current_id = next(self.mocked_ids)
            self.last_changed = time.time()
        return text, self.current_id

    # Do not support writing in mock (writing is almost not used in application)
    def write_card(self, text: str) -> bool:
        return False
