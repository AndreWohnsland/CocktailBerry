from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from threading import Timer
from typing import Self

from src.api.models import WaiterResponse
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.logger_handler import LoggerHandler
from src.machine.rfid import RFIDReader

_logger = LoggerHandler("WaiterService")


class WaiterService:
    """Singleton service for waiter NFC sensing and state management.

    Mirrors the NFCPaymentService pattern: starts a continuous NFC sensing loop,
    manages callbacks for UI updates, and handles auto-logout timers.
    """

    _instance: Self | None = None

    def __new__(cls) -> Self:
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.rfid_reader = RFIDReader()
        self._callbacks: dict[str, Callable[[], None]] = {}
        self._auto_logout_timer: Timer | None = None
        self._pause_callbacks: bool = False
        self._initialized = True

    def __del__(self) -> None:
        self._cancel_auto_logout_timer()
        self.rfid_reader.cancel_reading()

    def start_continuous_sensing(self) -> None:
        """Start continuous NFC sensing for waiter identification.

        Should be called once at program start.
        """
        if not cfg.nfc_enabled:
            _logger.error("No NFC reader type specified. Disabling waiter mode.")
            cfg.WAITER_MODE = False
            return
        _logger.info("Starting continuous NFC sensing for WaiterService.")
        self.rfid_reader.read_rfid(self._handle_nfc_read, read_delay_s=1.0)

    def _handle_nfc_read(self, _text: str, nfc_id: str) -> None:
        """Handle NFC read events from the reader thread."""
        _logger.debug(f"NFC ID read for waiter: {nfc_id}")
        self._cancel_auto_logout_timer()
        shared.current_waiter_nfc_id = nfc_id
        # Look up waiter in DB
        waiter = DatabaseCommander().get_waiter_by_nfc_id(nfc_id)
        shared.current_waiter = WaiterResponse.from_db(waiter) if waiter else None
        if waiter:
            _logger.debug(f"Service Personnel found: {waiter.name}")
        else:
            _logger.debug(f"No registered waiter for NFC ID: {nfc_id}")
        # Start auto-logout timer if configured
        if cfg.WAITER_AUTO_LOGOUT_S > 0:
            self._start_auto_logout_timer()
        self._run_callbacks()

    def logout_waiter(self) -> None:
        """Log out the current waiter and notify callbacks."""
        _logger.debug("Logging out current waiter.")
        shared.current_waiter_nfc_id = None
        shared.current_waiter = None
        self._cancel_auto_logout_timer()
        self._run_callbacks()

    def add_callback(self, name: str, callback: Callable[[], None]) -> None:
        """Add a named callback invoked when waiter state changes."""
        if name in self._callbacks:
            return
        _logger.debug(f"Adding callback: {name}")
        self._callbacks[name] = callback

    def remove_callback(self, name: str) -> None:
        """Remove a specific callback by name."""
        _logger.debug(f"Removing callback: {name}")
        self._callbacks.pop(name, None)

    @contextmanager
    def paused_callbacks(self) -> Iterator[None]:
        """Context manager to temporarily pause callbacks."""
        self._pause_callbacks = True
        try:
            yield
        finally:
            self._pause_callbacks = False

    def _run_callbacks(self) -> None:
        """Run all registered callbacks."""
        if self._pause_callbacks:
            _logger.debug("Callbacks are paused; not running any callbacks.")
            return
        for callback in self._callbacks.values():
            callback()

    def _cancel_auto_logout_timer(self) -> None:
        """Cancel the auto-logout timer if it exists."""
        if self._auto_logout_timer is not None:
            _logger.debug("Cancelling auto-logout timer.")
            self._auto_logout_timer.cancel()
            self._auto_logout_timer = None

    def _start_auto_logout_timer(self) -> None:
        """Start the auto-logout timer."""
        _logger.debug(f"Starting auto-logout timer ({cfg.WAITER_AUTO_LOGOUT_S}s).")
        self._auto_logout_timer = Timer(cfg.WAITER_AUTO_LOGOUT_S, self.logout_waiter)
        self._auto_logout_timer.daemon = True
        self._auto_logout_timer.start()
