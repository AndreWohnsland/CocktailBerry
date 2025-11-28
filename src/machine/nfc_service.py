import time
from dataclasses import dataclass
from threading import Event, Thread

from src.machine.rfid import RFIDReader
from src.utils import time_print


@dataclass
class User:
    balance: float
    can_get_alcohol: bool


class NFCService:
    _instance = None

    def __new__(cls) -> "NFCService":
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.rfid_reader = RFIDReader()
        self.uid: str | None = None
        self.clear_thread: Thread | None = None
        self._clear_event: Event | None = None
        self.current_user: User | None = None
        # Simulated user database
        # TODO: will call user instead from api
        self.user_db: dict[str, User] = {
            "CAD3B515": User(balance=1.0, can_get_alcohol=True),
            "33DFE41D": User(balance=10.0, can_get_alcohol=True),
        }

    def __del__(self) -> None:
        time_print("Cleaning up NFCService...")
        self._cancel_clear_thread()
        self.rfid_reader.cancel_reading()

    def continuous_sense_nfc_id(self) -> None:
        """Continuously sense NFC ID tags."""
        time_print("Starting NFC ID sensing.")
        self.rfid_reader.read_rfid(self.set_uid, read_delay_s=1.0)

    def set_uid(self, _: str, _id: str) -> None:
        """Set the UID when read."""
        time_print(f"NFC ID read: {_id}")
        self._cancel_clear_thread()
        self.user = self.user_db.get(_id, None)
        if self.user is None:
            time_print("No user found for this NFC ID.")
            self.uid = None
            return
        time_print(f"User found: {self.user} for NFC ID: {_id}\n")
        self.uid = _id
        self._clear_event = Event()
        self.clear_thread = Thread(
            target=self.clear_uid_after,
            args=(120, self._clear_event),
            daemon=True,
        )
        self.clear_thread.start()

    def clear_uid_after(self, seconds: int, cancel_event: Event | None = None) -> None:
        """Clear the UID after x seconds."""
        if cancel_event is not None:
            canceled = cancel_event.wait(timeout=seconds)
            if canceled:
                time_print("Clearing UID canceled.")
                return
        else:
            time.sleep(seconds)
        time_print("Clearing UID.")
        self.uid = None

    def _cancel_clear_thread(self) -> None:
        """Cancel the pending clear thread if it is running."""
        if self._clear_event is not None:
            self._clear_event.set()
            self._clear_event = None
