from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from src.config.config_manager import CONFIG as cfg
from src.dialog_handler import DIALOG_HANDLER as DH
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
            message=DH.get_translation("payment_inactive"),
            result=cls.Result.INACTIVE,
        )

    @classmethod
    def successful_booking(cls) -> "CocktailBooking":
        """Create a successful booking instance."""
        return cls(
            message=DH.get_translation("payment_successful"),
            result=cls.Result.SUCCESS,
        )

    @classmethod
    def insufficient_balance(cls) -> "CocktailBooking":
        """Create an insufficient balance booking instance."""
        return cls(
            message=DH.get_translation("payment_insufficient_balance"),
            result=cls.Result.INSUFFICIENT_BALANCE,
        )

    @classmethod
    def too_young(cls) -> "CocktailBooking":
        """Create a too young booking instance."""
        return cls(
            message=DH.get_translation("payment_too_young"),
            result=cls.Result.NOT_ALLOWED_ALCOHOL,
        )

    @classmethod
    def no_user_logged_in(cls) -> "CocktailBooking":
        """Create a no user logged in booking instance."""
        return cls(
            message=DH.get_translation("payment_no_user"),
            result=cls.Result.NO_USER,
        )

    @classmethod
    def api_not_reachable(cls) -> "CocktailBooking":
        """Create an API not reachable booking instance."""
        return cls(
            message=DH.get_translation("payment_api_not_reachable"),
            result=cls.Result.API_NOT_REACHABLE,
        )

    @classmethod
    def canceled(cls) -> "CocktailBooking":
        """Create a canceled booking instance."""
        return cls(
            message=DH.get_translation("payment_canceled"),
            result=cls.Result.CANCELED,
        )


class NFCPaymentService:
    _instance = None

    def __new__(cls) -> "NFCPaymentService":
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
            cls.uid: str | None = None
            cls.rfid_reader = RFIDReader()
            cls._user_callback: Callable[[User | None, str], None] | None = None
            cls._is_polling: bool = False
            cls.user_db: dict[str, User] = {
                "CAD3B515": User(uid="CAD3B515", balance=5.0, can_get_alcohol=False),
                "33DFE41D": User(uid="33DFE41D", balance=10.0, can_get_alcohol=True),
            }
        return cls._instance

    def __del__(self) -> None:
        self.rfid_reader.cancel_reading()

    def start_continuous_sensing(self) -> None:
        """Start continuous NFC sensing in the background.

        This should be called once at program start and runs continuously.
        Callbacks can be added/removed dynamically without stopping the sensing.
        """
        time_print("Starting continuous NFC sensing for NFCPaymentService.")
        self.rfid_reader.read_rfid(self._handle_nfc_read, read_delay_s=1.0)

    def add_callback(self, callback: Callable[[User | None, str], None]) -> None:
        """Add a callback to be invoked when a user is detected."""
        self._user_callback = callback

    def clear_callback(self) -> None:
        """Remove the current user callback."""
        self._user_callback = None

    def get_user_for_id(self, nfc_id: str) -> User | None:
        """Get the user associated with the given NFC ID."""
        # TODO: will call user instead from api
        return self.user_db.get(nfc_id, None)

    def _handle_nfc_read(self, _: str, _id: str) -> None:
        """Handle NFC read events."""
        time_print(f"NFC ID read: {_id}")
        user = self.get_user_for_id(_id)
        if user is None:
            time_print("No user found for this NFC ID.")
            self.uid = None
        else:
            time_print(f"User found: for NFC ID: {_id}")
            self.uid = _id

        if self._user_callback is not None:
            self._user_callback(user, _id)

    def book_cocktail_for_user(self, user: User | None, cocktail: Cocktail) -> CocktailBooking:
        """Book a cocktail for the given user if they have enough balance."""
        if user is None:
            return CocktailBooking.no_user_logged_in()
        if not user.can_get_alcohol and not cocktail.is_virgin:
            return CocktailBooking.too_young()
        multiplier = cfg.PAYMENT_VIRGIN_MULTIPLIER / 100 if cocktail.is_virgin else 1.0
        price = cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, price_multiplier=multiplier)
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
