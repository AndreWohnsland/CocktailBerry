import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from itertools import cycle
from threading import Timer
from typing import Protocol

import requests
from pydantic.dataclasses import dataclass as api_dataclass

from src.config.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.machine.rfid import RFIDReader
from src.models import Cocktail
from src.service.booking import CocktailBooking

_logger = LoggerHandler("NFCPaymentService")


@api_dataclass
class User:
    nfc_id: str
    balance: float
    is_adult: bool


class UserLookupResult(StrEnum):
    """Enumeration of possible user lookup results."""

    USER_FOUND = "USER_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    USER_REMOVED = "USER_REMOVED"


@dataclass
class UserLookup:
    """Result of a user lookup operation."""

    user: User | None
    result: UserLookupResult

    @classmethod
    def found(cls, user: User) -> "UserLookup":
        """Create a successful lookup instance."""
        return cls(user=user, result=UserLookupResult.USER_FOUND)

    @classmethod
    def not_found(cls) -> "UserLookup":
        """Create a user not found lookup instance."""
        return cls(user=None, result=UserLookupResult.USER_NOT_FOUND)

    @classmethod
    def service_unavailable(cls) -> "UserLookup":
        """Create a service unavailable lookup instance."""
        return cls(user=None, result=UserLookupResult.SERVICE_UNAVAILABLE)

    @classmethod
    def removed(cls) -> "UserLookup":
        """Create a user removed lookup instance."""
        return cls(user=None, result=UserLookupResult.USER_REMOVED)


class NFCPaymentService:
    _instance = None

    def __new__(cls) -> "NFCPaymentService":
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
            cls.user_lookup: UserLookup = UserLookup.removed()
            cls.rfid_reader = RFIDReader()
            cls._user_callbacks: dict[str, Callable[[UserLookup], None]] = {}
            cls._is_polling: bool = False
            cls._auto_logout_timer: Timer | None = None
            cls._pause_callbacks: bool = False
            cls._api_client = _choose_payment_service_client()
        return cls._instance

    def __del__(self) -> None:
        self._cancel_auto_logout_timer()
        self.rfid_reader.cancel_reading()

    def _run_callbacks(self, lookup: UserLookup) -> None:
        """Run all registered user callbacks."""
        if self._pause_callbacks:
            _logger.debug("Callbacks are paused; not running any callbacks.")
            return
        for callback in self._user_callbacks.values():
            callback(lookup)

    def _cancel_auto_logout_timer(self) -> None:
        """Cancel the auto-logout timer if it exists."""
        if self._auto_logout_timer is not None:
            _logger.debug("Cancelling auto-logout timer.")
            self._auto_logout_timer.cancel()
            self._auto_logout_timer = None

    def _start_auto_logout_timer(self) -> None:
        """Start the auto-logout timer if configured."""
        if cfg.PAYMENT_AUTO_LOGOUT_TIME_S > 0:
            _logger.debug("Starting auto-logout timer.")
            self._auto_logout_timer = Timer(cfg.PAYMENT_AUTO_LOGOUT_TIME_S, self.logout_user)
            self._auto_logout_timer.daemon = True
            self._auto_logout_timer.start()

    def logout_user(self) -> None:
        """Handle auto-logout when timer expires."""
        _logger.debug("Logging out the current user.")
        if self._auto_logout_timer is not None:
            self._auto_logout_timer.cancel()
        self._auto_logout_timer = None
        self.user_lookup = UserLookup.removed()
        self._run_callbacks(self.user_lookup)

    def start_continuous_sensing(self) -> None:
        """Start continuous NFC sensing in the background.

        This should be called once at program start and runs continuously.
        Callbacks can be added/removed dynamically without stopping the sensing.
        """
        # need to check that the right nfc reader is connected only USB is supported
        if cfg.RFID_READER == "No":
            _logger.error("No NFC reader type specified. Disabling payment service.")
            cfg.PAYMENT_TYPE = "Disabled"
            return
        _logger.info("Starting continuous NFC sensing for NFCPaymentService.")
        self.rfid_reader.read_rfid(self._handle_nfc_read, read_delay_s=1.0)

    def add_callback(self, name: str, callback: Callable[[UserLookup], None]) -> None:
        """Add a named callback to be invoked when a user is detected."""
        # skip noisy logs: it is not planned to "update" callbacks since name should point to unique function
        if name in self._user_callbacks:
            return
        _logger.debug(f"Adding callback: {name}")
        self._user_callbacks[name] = callback

    def remove_callback(self, name: str) -> None:
        """Remove a specific callback by name."""
        _logger.debug(f"Removing callback: {name}")
        self._user_callbacks.pop(name, None)

    def remove_all_callbacks(self) -> None:
        """Remove all registered callbacks."""
        _logger.debug("Removing all user callbacks.")
        self._user_callbacks.clear()

    @contextmanager
    def paused_callbacks(self) -> Iterator[None]:
        """Context manager to temporarily pause callbacks."""
        self._pause_callbacks = True
        try:
            yield
        finally:
            self._pause_callbacks = False

    def get_user_for_id(self, nfc_id: str) -> UserLookup:
        """Get the user associated with the given NFC ID."""
        return self._api_client.get_user_for_id(nfc_id)

    def _handle_nfc_read(self, _: str, _id: str) -> None:
        """Handle NFC read events."""
        _logger.debug(f"NFC ID read: {_id}")
        self.user_lookup = self.get_user_for_id(_id)
        self._cancel_auto_logout_timer()

        if self.user_lookup.user is None:
            _logger.debug(f"No user found for this NFC ID. Reason: {self.user_lookup.result}")
        else:
            _logger.debug(f"User found for NFC ID: {_id}")

        if self.user_lookup.result == UserLookupResult.USER_FOUND:
            self._start_auto_logout_timer()
        self._run_callbacks(self.user_lookup)

    def book_cocktail_for_user(self, user_lookup: UserLookup, cocktail: Cocktail) -> CocktailBooking:
        """Book a cocktail for the given user if they have enough balance."""
        if user_lookup.result == UserLookupResult.USER_NOT_FOUND:
            return CocktailBooking.user_not_known()
        if user_lookup.result == UserLookupResult.SERVICE_UNAVAILABLE:
            return CocktailBooking.api_not_reachable()
        user = user_lookup.user
        if user is None:
            return CocktailBooking.no_user_logged_in()
        if not user.is_adult and not cocktail.is_virgin:
            return CocktailBooking.too_young()
        multiplier = cfg.PAYMENT_VIRGIN_MULTIPLIER / 100 if cocktail.is_virgin else 1.0
        price = cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, price_multiplier=multiplier)
        if user.balance < price:
            return CocktailBooking.insufficient_balance()
        return self._api_client.book_cocktail_for_user(user, cocktail, price)


class _ExternalServiceClient(Protocol):
    def get_user_for_id(self, nfc_id: str) -> UserLookup: ...

    def book_cocktail_for_user(self, user: User, cocktail: Cocktail, price: float) -> CocktailBooking: ...


class _MockPaymentService:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self._adult_iterator = cycle([True, False])

    def get_user_for_id(self, nfc_id: str) -> UserLookup:
        user = self.users.get(nfc_id)
        if user is None:
            user = User(nfc_id=nfc_id, balance=20.0, is_adult=next(self._adult_iterator))
        self.users[nfc_id] = user
        return UserLookup.found(user)

    def book_cocktail_for_user(self, user: User, cocktail: Cocktail, price: float) -> CocktailBooking:
        user.balance -= price
        _logger.info(f"Cocktail {cocktail.name} booked. New balance for {user.nfc_id}: {user.balance}")
        return CocktailBooking.successful_booking(current_balance=user.balance)


class _ApiPaymentService:
    def __init__(self) -> None:
        self.api_client = requests.Session()
        self.api_client.headers.update({"x-api-key": cfg.PAYMENT_SECRET_KEY})
        self.api_base_url = f"{cfg.PAYMENT_SERVICE_URL}/api"
        self.response_code_errors: dict[int, CocktailBooking] = {
            401: CocktailBooking.api_interface_conflict(),  # no key or invalid key
            402: CocktailBooking.insufficient_balance(),
            403: CocktailBooking.too_young(),
            404: CocktailBooking.no_user_logged_in(),
            422: CocktailBooking.api_interface_conflict(),
            500: CocktailBooking.api_not_reachable(),
        }

    def get_user_for_id(self, nfc_id: str) -> UserLookup:
        try:
            resp = self.api_client.get(f"{self.api_base_url}/users/{nfc_id}")
            if resp.status_code == 401:  # noqa: PLR2004
                _logger.warning("Wrong api key when fetching user data. Check PAYMENT_SECRET_KEY.")
            if resp.status_code == 404:  # noqa: PLR2004
                _logger.debug(f"User not found in payment service for NFC ID: {nfc_id}")
                return UserLookup.not_found()
            resp.raise_for_status()
            return UserLookup.found(User(**resp.json()))
        except requests.exceptions.ConnectionError as e:
            _logger.error(f"API not reachable when fetching user for NFC ID: {nfc_id}, error: {e}")
            return UserLookup.service_unavailable()
        except Exception as e:
            _logger.error(f"Failed to get user for NFC ID: {nfc_id}, error: {e}")
            return UserLookup.service_unavailable()

    def book_cocktail_for_user(self, user: User, cocktail: Cocktail, price: float) -> CocktailBooking:
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
            _logger.error(f"API not reachable: {e}")
            return CocktailBooking.api_not_reachable()
        _logger.info(f"Cocktail {cocktail.name} booked. New balance for {user.nfc_id}: {user.balance}")
        return CocktailBooking.successful_booking(current_balance=user.balance)


def _choose_payment_service_client() -> _ExternalServiceClient:
    if "MOCK_PAYMENT_SERVICE" in os.environ:
        _logger.warning("Using mock payment service.")
        return _MockPaymentService()
    return _ApiPaymentService()
