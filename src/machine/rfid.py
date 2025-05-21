import time
from threading import Thread
from typing import Callable, Optional

from src.config.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.machine.interface import RFIDController

_logger = LoggerHandler("RFIDReader")


_NOT_ACTIVATED = "Please select RFID type other than 'No' to use RFID"
_BASE_NOT_POSSIBLE = "Could not import {}, if it's installed it is probably not for your OS! RFID will not work."

_ERROR_SELECTION_NOT_INSTALLED = {
    "No": _NOT_ACTIVATED,
    "PiicoDev": "Please install piicodev to use the RFID reader.",
    "MFRC522": "Please install mfrc522 to use the RFID reader.",
}

_ERROR_SELECTION_NOT_POSSIBLE = {
    "No": _NOT_ACTIVATED,
    "PiicoDev": _BASE_NOT_POSSIBLE.format(cfg.RFID_READER),
    "MFRC522": _BASE_NOT_POSSIBLE.format(cfg.RFID_READER),
}

_NO_MODULE = True
_ERROR = None
try:
    if cfg.RFID_READER == "PiicoDev":
        from PiicoDev_RFID import PiicoDev_RFID
    elif cfg.RFID_READER == "MFRC522":
        # pylint: disable=import-error
        from mfrc522 import SimpleMFRC522  # type: ignore
    _NO_MODULE = False
except AttributeError:
    _ERROR = _ERROR_SELECTION_NOT_POSSIBLE[cfg.RFID_READER]
except ModuleNotFoundError:
    _ERROR = _ERROR_SELECTION_NOT_INSTALLED[cfg.RFID_READER]


class RFIDReader:
    _instance = None

    def __init__(self) -> None:
        """Initialize the RFID reader."""
        self.is_active = False
        if _ERROR is not None:
            _logger.log_event("ERROR", _ERROR)
        self.rfid = self._select_rfid()

    def _select_rfid(self) -> Optional[RFIDController]:
        """Select the controller defined in config."""
        if _NO_MODULE or cfg.RFID_READER == "No":
            return None
        if cfg.RFID_READER == "PiicoDev":
            return _PiicoDevReader()
        if cfg.RFID_READER == "MFRC522":
            return _BasicMFRC522()
        return None

    def __new__(cls) -> "RFIDReader":
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def read_rfid(self, side_effect: Callable[[str, str], None]) -> None:
        """Start the rfid reader, calls an side effect with the read value and id."""
        rfid_thread = Thread(target=self._read_thread, args=(side_effect,), daemon=True)
        rfid_thread.start()

    def _read_thread(self, side_effect: Callable[[str, str], None]) -> None:
        """Execute the reading until reads a value or got canceled."""
        if self.rfid is None or self.is_active:
            return
        text = None
        self.is_active = True
        while self.is_active:
            text, _id = self.rfid.read_card()
            if text is not None and _id is not None:
                side_effect(text, _id)
            time.sleep(0.5)
        self.is_active = False

    def write_rfid(self, value: str, side_effect: Optional[Callable[[str], None]] = None) -> None:
        """Write the value to the RFID."""
        rfid_thread = Thread(
            target=self._write_thread,
            args=(
                value,
                side_effect,
            ),
            daemon=True,
        )
        rfid_thread.start()

    def _write_thread(self, text: str, side_effect: Optional[Callable[[str], None]] = None) -> None:
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


class _PiicoDevReader(RFIDController):
    """Reader for the PiicoDev RFID Module."""

    def __init__(self) -> None:
        self.rfid = PiicoDev_RFID()  # pylint: disable=E0601

    def read_card(self) -> tuple[Optional[str], Optional[str]]:
        text = None
        _id = None
        if self.rfid.tagPresent():
            text = self.rfid.readText()
            _id: Optional[str] = self.rfid.readID()  # type: ignore
            if text is not None:
                text = text.strip()
        return text, _id

    def write_card(self, text: str) -> bool:
        return self.rfid.writeText(text)


class _BasicMFRC522(RFIDController):
    """Reader for common RC522 modules."""

    def __init__(self) -> None:
        self.rfid = SimpleMFRC522()  # pylint: disable=E0601

    def read_card(self) -> tuple[Optional[str], Optional[str]]:
        _id, text = self.rfid.read_no_block()
        if text is not None:
            text = text.strip()
        return text, _id

    def write_card(self, text: str) -> bool:
        _id, _ = self.rfid.write_no_block(text)
        return _id is not None
