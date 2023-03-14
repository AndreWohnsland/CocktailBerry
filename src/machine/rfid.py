
import time
from typing import Callable, Optional, Union
from threading import Thread

from src.logger_handler import LoggerHandler
from src.machine.interface import RFIDController
from src.config_manager import CONFIG as cfg

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
        self.is_active = False
        if _ERROR is not None:
            _logger.log_event("ERROR", _ERROR)
        self.rfid = self._select_rfid()

    def _select_rfid(self) -> Union[RFIDController, None]:
        """Selects the controller defined in config"""
        if _NO_MODULE or cfg.RFID_READER == "No":
            return None
        if cfg.RFID_READER == "PiicoDev":
            return PiicoDevReader()
        if cfg.RFID_READER == "MFRC522":
            return BasicMFRC522()

    def __new__(cls):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def read_rfid(self, side_effect: Callable[[str], None]):
        """Start the rfid reader, calls an side effect with the read value"""
        if _NO_MODULE or self.is_active:
            return
        self.is_active = True
        rfid_thread = Thread(target=self._read_thread, args=(side_effect,), daemon=True)
        rfid_thread.start()

    def _read_thread(self, side_effect: Callable[[str], None]):
        """Execute the reading until reads a value or got canceled"""
        if self.rfid is None:
            return
        text = None
        # It's important to not have infinite reads (hence the break)
        # because it seems some frameworks can not be canceled during write / read
        # This would result in them still happily reading even it's canceled.
        # The new read would not work and we would get a segmentation fault >.<
        while self.is_active:
            text = self.rfid.read_card()
            if text is not None:
                side_effect(text)
                break
            time.sleep(0.5)
        self.is_active = False

    def write_rfid(self, value: str, side_effect: Optional[Callable[[str], None]] = None):
        """Writes the value to the RFID"""
        if _NO_MODULE or self.is_active:
            return
        self.is_active = True
        rfid_thread = Thread(target=self._write_thread, args=(value, side_effect,), daemon=True)
        rfid_thread.start()

    def _write_thread(self, text: str, side_effect: Optional[Callable[[str], None]] = None):
        """Executes the writing until successful or canceled"""
        if self.rfid is None:
            return
        while self.is_active:
            success = self.rfid.write_card(text)
            if success:
                if side_effect:
                    side_effect(text)
                break
            time.sleep(0.1)
        self.is_active = False

    def cancel_reading(self):
        """Cancels the reading loop"""
        self.is_active = False


class PiicoDevReader(RFIDController):
    def __init__(self) -> None:
        self.rfid = PiicoDev_RFID()

    def read_card(self) -> Union[str, None]:
        text = None
        if self.rfid.tagPresent():
            text = self.rfid.readText()
            if text is not None:
                text.strip()
        return text

    def write_card(self, text: str) -> bool:
        return self.rfid.writeText(text)


class BasicMFRC522(RFIDController):
    def __init__(self) -> None:
        self.rfid = SimpleMFRC522()

    def read_card(self) -> Union[str, None]:
        _, text = self.rfid.read()
        if text is not None:
            text = text.strip()
        return text

    def write_card(self, text: str) -> bool:
        _id, _ = self.rfid.write(text)
        return _id is not None


RFID = None
if cfg.RFID_READER != "No":
    RFID = RFIDReader()
