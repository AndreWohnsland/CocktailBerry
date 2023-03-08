
import time
from typing import Callable
from threading import Thread

from src.logger_handler import LoggerHandler

_logger = LoggerHandler("RFIDReader")

_NO_MODULE = True
_ERROR = None
try:
    from PiicoDev_RFID import PiicoDev_RFID
    _NO_MODULE = False
except AttributeError:
    _ERROR = "Could not import PiicoDev, if it's installed it is probably not for your OS!"
except ModuleNotFoundError:
    _ERROR = "Please install piicodev to use the RFID reader."


class RFIDReader:
    _instance = None

    def __init__(self) -> None:
        self.check_id = False
        if _NO_MODULE:
            self.rfid = None
            return
        if _ERROR is not None:
            _logger.log_event("ERROR", _ERROR)
        self.rfid = PiicoDev_RFID()

    def __new__(cls):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def read_rfid(self, side_effect: Callable[[str], None]):
        """Start the rfid reader, calls an side effect with the read value"""
        if _NO_MODULE:
            return
        self.check_id = True
        rfid_thread = Thread(target=self._read_thread, args=(side_effect,), daemon=True)
        rfid_thread.start()

    def _read_thread(self, side_effect: Callable[[str], None]):
        """Execute the reading until reads a value or got canceled"""
        if self.rfid is None:
            return
        text = None
        while self.check_id:
            if self.rfid.tagPresent():
                text = self.rfid.readText()
                print(f"Read {text=} from RFID")
                break
            time.sleep(0.5)
        # If no text, execute no side effect
        # TODO: Check the logic here, it is probably necessary to read until canceled
        if text is None:
            return
        side_effect(text)

    def cancel_reading(self):
        """Cancels the reading loop"""
        self.check_id = False
