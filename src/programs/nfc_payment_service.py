import time
from dataclasses import dataclass
from enum import StrEnum
from threading import Event, Thread

from src.config.config_manager import CONFIG as cfg
from src.machine.rfid import RFIDReader
from src.models import Cocktail
from src.utils import time_print


@dataclass
class User:
    uid: str
    balance: float
    can_get_alcohol: bool


@dataclass
class CocktailBooking:
    message: str
    result: "Result"

    class Result(StrEnum):
        """Enumeration of possible cocktail booking results."""

        SUCCESS = "success"
        INACTIVE = "inactive"
        INSUFFICIENT_BALANCE = "insufficient_balance"
        NOT_ALLOWED_ALCOHOL = "not_allowed_alcohol"
        NO_USER = "no_user"
        API_NOT_REACHABLE = "api_not_reachable"
        CANCELED = "canceled"

    @classmethod
    def inactive(cls) -> "CocktailBooking":
        """Create an inactive booking instance."""
        return cls(
            message="Cocktail booking is currently inactive.",
            result=cls.Result.INACTIVE,
        )

    @classmethod
    def successful_booking(cls) -> "CocktailBooking":
        """Create a successful booking instance."""
        return cls(
            message="Cocktail booked successfully.",
            result=cls.Result.SUCCESS,
        )

    @classmethod
    def insufficient_balance(cls) -> "CocktailBooking":
        """Create an insufficient balance booking instance."""
        return cls(
            message="Insufficient balance to book cocktail.",
            result=cls.Result.INSUFFICIENT_BALANCE,
        )

    @classmethod
    def too_young(cls) -> "CocktailBooking":
        """Create a too young booking instance."""
        return cls(
            message="User is not allowed to get alcohol.",
            result=cls.Result.NOT_ALLOWED_ALCOHOL,
        )

    @classmethod
    def no_user_logged_in(cls) -> "CocktailBooking":
        """Create a no user logged in booking instance."""
        return cls(
            message="Please scan a NFC tag.",
            result=cls.Result.NO_USER,
        )

    @classmethod
    def api_not_reachable(cls) -> "CocktailBooking":
        """Create an API not reachable booking instance."""
        return cls(
            message="API not reachable.",
            result=cls.Result.API_NOT_REACHABLE,
        )

    @classmethod
    def canceled(cls) -> "CocktailBooking":
        """Create a canceled booking instance."""
        return cls(
            message="Payment canceled by user.",
            result=cls.Result.CANCELED,
        )


class NFCPaymentService:
    _instance = None
    _initialized = False

    def __new__(cls) -> "NFCPaymentService":
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
            cls.uid: str | None = None
            cls.current_user: User | None = None
            cls.rfid_reader = RFIDReader()
            cls.clear_thread: Thread | None = None
            cls._clear_event: Event | None = None
            cls.user_db: dict[str, User] = {
                "CAD3B515": User(uid="CAD3B515", balance=1.0, can_get_alcohol=True),
                "33DFE41D": User(uid="33DFE41D", balance=10.0, can_get_alcohol=True),
            }
        return cls._instance

    def __del__(self) -> None:
        time_print("Cleaning up NFCService...")
        self._cancel_clear_thread()
        self.rfid_reader.cancel_reading()

    def continuous_sense_nfc_id(self) -> None:
        """Continuously sense NFC ID tags."""
        time_print("Starting NFC ID sensing.")
        self.rfid_reader.read_rfid(self.set_uid, read_delay_s=1.0)

    def get_user_for_id(self, nfc_id: str) -> User | None:
        """Get the user associated with the given NFC ID."""
        # TODO: will call user instead from api
        return self.user_db.get(nfc_id, None)

    def set_uid(self, _: str, _id: str) -> None:
        """Set the UID when read."""
        time_print(f"NFC ID read: {_id}")
        self._cancel_clear_thread()
        self.current_user = self.get_user_for_id(_id)
        if self.current_user is None:
            time_print("No user found for this NFC ID.")
            self.uid = None
            return
        time_print(f"User found: {self.current_user} for NFC ID: {_id}\n")
        self.uid = _id
        self._clear_event = Event()
        self.clear_thread = Thread(
            target=self.clear_data_after,
            args=(cfg.PAYMENT_AUTO_LOGOUT_TIME_S, self._clear_event),
            daemon=True,
        )
        self.clear_thread.start()

    def clear_data_after(self, seconds: int, cancel_event: Event | None = None) -> None:
        """Clear the UID after x seconds."""
        if cancel_event is not None:
            canceled = cancel_event.wait(timeout=seconds)
            if canceled:
                time_print("Clearing UID canceled.")
                return
        else:
            time.sleep(seconds)
        time_print("Clearing Data.")
        self.uid = None
        self.current_user = None

    def _cancel_clear_thread(self) -> None:
        """Cancel the pending clear thread if it is running."""
        if self._clear_event is not None:
            self._clear_event.set()
            self._clear_event = None

    def book_cocktail_for_current_user(self, cocktail: Cocktail) -> CocktailBooking:
        """Book a cocktail for the current user if they have enough balance."""
        user = self.current_user
        if user is None:
            return CocktailBooking.no_user_logged_in()
        if not user.can_get_alcohol:
            return CocktailBooking.too_young()
        price = cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING)
        if user.balance < price:
            return CocktailBooking.insufficient_balance()
        try:
            # TODO: API call to book the cocktail
            user.balance -= price
            # TODO: API might also return not enough balance or not allowed alcohol (edge case)
        except Exception as e:
            time_print(f"API not reachable: {e}")
            return CocktailBooking.api_not_reachable()
        time_print(f"Cocktail {cocktail.name} booked. New balance: {user.balance}")
        return CocktailBooking.successful_booking()
