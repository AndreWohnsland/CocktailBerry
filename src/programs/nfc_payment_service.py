from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from threading import Timer

import requests
from pydantic.dataclasses import dataclass as api_dataclass

from src.config.config_manager import CONFIG as cfg
from src.dialog_handler import DIALOG_HANDLER as DH
from src.logger_handler import LoggerHandler
from src.machine.rfid import RFIDReader
from src.models import Cocktail
from src.utils import time_print

_logger = LoggerHandler("NFCPaymentService")


@api_dataclass
class User:
    nfc_id: str
    balance: float
    is_adult: bool


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
    def successful_booking(cls, current_balance: float) -> "CocktailBooking":
        """Create a successful booking instance."""
        return cls(
            message=DH.get_translation("payment_successful", current_balance=current_balance),
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
    def api_interface_conflict(cls) -> "CocktailBooking":
        """Create a machine issue booking instance."""
        return cls(
            message=DH.get_translation("api_interface_conflict"),
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
            cls.user: User | None = None
            cls.rfid_reader = RFIDReader()
            cls._user_callbacks: dict[str, Callable[[User | None, str], None]] = {}
            cls._is_polling: bool = False
            cls._auto_logout_timer: Timer | None = None
            cls._pause_callbacks: bool = False
            cls.api_client = requests.Session()
            cls.api_client.headers.update({"x-api-key": cfg.PAYMENT_SECRET_KEY})
            cls.api_base_url = f"{cfg.PAYMENT_SERVICE_URL}/api"
            cls.response_code_errors: dict[int, CocktailBooking] = {
                401: CocktailBooking.api_interface_conflict(),  # no key or invalid key
                402: CocktailBooking.insufficient_balance(),
                403: CocktailBooking.too_young(),
                404: CocktailBooking.no_user_logged_in(),
                422: CocktailBooking.api_interface_conflict(),
                500: CocktailBooking.api_not_reachable(),
            }
        return cls._instance

    def __del__(self) -> None:
        self._cancel_auto_logout_timer()
        self.rfid_reader.cancel_reading()

    def _run_callbacks(self, user: User | None, nfc_id: str) -> None:
        """Run all registered user callbacks."""
        if self._pause_callbacks:
            time_print("Callbacks are paused; not running any callbacks.")
            return
        for callback in self._user_callbacks.values():
            callback(user, nfc_id)

    def _cancel_auto_logout_timer(self) -> None:
        """Cancel the auto-logout timer if it exists."""
        if self._auto_logout_timer is not None:
            time_print("Cancelling auto-logout timer.")
            self._auto_logout_timer.cancel()
            self._auto_logout_timer = None

    def _start_auto_logout_timer(self) -> None:
        """Start the auto-logout timer if configured."""
        if cfg.PAYMENT_AUTO_LOGOUT_TIME_S > 0:
            time_print("Starting auto-logout timer.")
            self._auto_logout_timer = Timer(cfg.PAYMENT_AUTO_LOGOUT_TIME_S, self.logout_user)
            self._auto_logout_timer.daemon = True
            self._auto_logout_timer.start()

    def logout_user(self) -> None:
        """Handle auto-logout when timer expires."""
        time_print("Logging out the current user.")
        if self._auto_logout_timer is not None:
            self._auto_logout_timer.cancel()
        self._auto_logout_timer = None
        self.user = None
        self.uid = None
        self._run_callbacks(None, "")

    def start_continuous_sensing(self) -> None:
        """Start continuous NFC sensing in the background.

        This should be called once at program start and runs continuously.
        Callbacks can be added/removed dynamically without stopping the sensing.
        """
        time_print("Starting continuous NFC sensing for NFCPaymentService.")
        self.rfid_reader.read_rfid(self._handle_nfc_read, read_delay_s=1.0)

    def add_callback(self, name: str, callback: Callable[[User | None, str], None]) -> None:
        """Add a named callback to be invoked when a user is detected."""
        # skip noisy logs: it is not planned to "update" callbacks since name should point to unique function
        if name in self._user_callbacks:
            return
        time_print(f"Adding callback: {name}")
        self._user_callbacks[name] = callback

    def remove_callback(self, name: str) -> None:
        """Remove a specific callback by name."""
        time_print(f"Removing callback: {name}")
        self._user_callbacks.pop(name, None)

    def remove_all_callbacks(self) -> None:
        """Remove all registered callbacks."""
        time_print("Removing all user callbacks.")
        self._user_callbacks.clear()

    @contextmanager
    def paused_callbacks(self) -> Iterator[None]:
        """Context manager to temporarily pause callbacks."""
        self._pause_callbacks = True
        try:
            yield
        finally:
            self._pause_callbacks = False

    def get_user_for_id(self, nfc_id: str) -> User | None:
        """Get the user associated with the given NFC ID."""
        try:
            resp = self.api_client.get(f"{self.api_base_url}/users/{nfc_id}")
            if resp.status_code == 401:  # noqa: PLR2004
                msg = "Wrong api key when fetching user data. Check PAYMENT_SECRET_KEY."
                time_print(msg)
                _logger.warning(msg)
            resp.raise_for_status()
            return User(**resp.json())
        except requests.exceptions.ConnectionError as e:
            time_print(f"API not reachable when fetching user for NFC ID: {nfc_id}, error: {e}")
            return None
        except Exception as e:
            time_print(f"Failed to get user for NFC ID: {nfc_id}, error: {e}")
            return None

    def _handle_nfc_read(self, _: str, _id: str) -> None:
        """Handle NFC read events."""
        time_print(f"NFC ID read: {_id}")
        self.user = self.get_user_for_id(_id)
        self._cancel_auto_logout_timer()

        if self.user is None:
            time_print("No user found for this NFC ID.")
            self.uid = None
        else:
            time_print(f"User found: for NFC ID: {_id}")
            self.uid = _id

        self._start_auto_logout_timer()
        self._run_callbacks(self.user, _id)

    def book_cocktail_for_user(self, user: User | None, cocktail: Cocktail) -> CocktailBooking:
        """Book a cocktail for the given user if they have enough balance."""
        if user is None:
            return CocktailBooking.no_user_logged_in()
        if not user.is_adult and not cocktail.is_virgin:
            return CocktailBooking.too_young()
        multiplier = cfg.PAYMENT_VIRGIN_MULTIPLIER / 100 if cocktail.is_virgin else 1.0
        price = cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, price_multiplier=multiplier)
        if user.balance < price:
            return CocktailBooking.insufficient_balance()
        try:
            resp = self.api_client.post(
                f"{self.api_base_url}/users/{user.nfc_id}/cocktails/book",
                json={
                    "name": cocktail.name,
                    "cocktail_id": cocktail.id,
                    "amount": cocktail.adjusted_amount,
                    "price_per_100_ml": cocktail.price_per_100_ml,
                    "price": price,
                    "is_alcoholic": not cocktail.is_virgin,
                },
            )
            if resp.status_code in self.response_code_errors:
                return self.response_code_errors[resp.status_code]
            # make sure we do not forget errors here
            resp.raise_for_status()
            user = User(**resp.json())
        except Exception as e:
            time_print(f"API not reachable: {e}")
            return CocktailBooking.api_not_reachable()
        time_print(f"Cocktail {cocktail.name} booked. New balance: {user.balance}")
        return CocktailBooking.successful_booking(current_balance=user.balance)
