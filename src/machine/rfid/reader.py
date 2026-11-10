from __future__ import annotations

import time
from collections.abc import Callable
from threading import Lock, Thread
from typing import TYPE_CHECKING, Self

from src.logger_handler import FailureStreak, LoggerHandler

if TYPE_CHECKING:
    from src.machine.rfid.base import RFIDInterface

_logger = LoggerHandler("RFIDReader")
# one poll iteration: returns True when the loop is done, gets a probe whether it still owns the reader
_Step = Callable[["RFIDInterface", Callable[[], bool]], bool]
# a failing reader (unplugged, SPI hiccup) is polled slowly until it answers again
_ERROR_BACKOFF_S = 2.0


class RFIDReader:
    """Singleton facade around the active :class:`RFIDInterface` controller.

    The concrete controller is wired in by ``MachineController.init_machine()``
    via :meth:`attach`. Callers can hold a reference to ``RFIDReader()`` even
    before the machine is initialized — :attr:`rfid` simply stays ``None``
    until a controller is attached.

    Only one loop (read or write) owns the reader at a time. Every start and cancel
    bumps a generation counter; a loop finishes its current step, then exits when it
    is no longer the current generation, and a card read during that last step is
    not handed to its handler. The lock only guards the flag and the counter: keep
    the critical sections free of calls and allocations, a garbage-collected Qt
    window cancels from ``__del__`` and must never re-enter them.
    """

    _instance: Self | None = None

    def __new__(cls) -> Self:
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.is_active = False
        self.rfid: RFIDInterface | None = None
        self._generation = 0
        self._lock = Lock()
        self._initialized = True

    def attach(self, controller: RFIDInterface | None) -> None:
        """Wire the active RFID controller. Pass ``None`` to detach."""
        self.rfid = controller

    def read_rfid(self, side_effect: Callable[[str, str], None], read_delay_s: float = 0.5) -> bool:
        """Start reading in the background, calling ``side_effect`` with text and id of every card.

        Returns False when no reader is attached or a loop is already running.
        """

        def step(rfid: RFIDInterface, is_current: Callable[[], bool]) -> bool:
            text, _id = rfid.read_card()
            if text is None or _id is None:
                # small sleep in case the reader has no internal sensing
                time.sleep(0.1)
                return False
            if is_current():
                side_effect(text, _id)
                time.sleep(read_delay_s)
            return False

        return self._start(step)

    def write_rfid(self, value: str, side_effect: Callable[[str], None] | None = None) -> bool:
        """Write ``value`` to the next card in the background. Returns False when the reader is busy or missing."""

        def step(rfid: RFIDInterface, is_current: Callable[[], bool]) -> bool:
            if not rfid.write_card(value):
                time.sleep(0.1)
                return False
            if side_effect and is_current():
                try:
                    side_effect(value)
                except Exception as e:  # the card is written, a failing handler must not write it again
                    _logger.error("The RFID write handler failed")
                    _logger.log_exception(e)
            return True

        return self._start(step)

    def cancel_reading(self) -> None:
        """Stop the running loop after its current step."""
        with self._lock:
            self._generation += 1
            self.is_active = False

    def _start(self, step: _Step) -> bool:
        with self._lock:
            if self.rfid is None or self.is_active:
                return False
            self._generation += 1
            self.is_active = True
            generation, rfid = self._generation, self.rfid
        # outside the lock: starting a thread allocates, which can run a window's __del__
        Thread(target=self._poll, args=(generation, rfid, step), daemon=True).start()
        return True

    def _poll(self, generation: int, rfid: RFIDInterface, step: _Step) -> None:
        """Call ``step`` until it returns True or the loop is cancelled, surviving driver and handler errors."""
        streak = FailureStreak(_logger, "RFID loop")

        def is_current() -> bool:
            return self._generation == generation

        try:
            while is_current():
                try:
                    done = step(rfid, is_current)
                except Exception as e:
                    streak.failed(e)
                    time.sleep(_ERROR_BACKOFF_S)
                    continue
                streak.recovered()
                if done:
                    return
        finally:
            with self._lock:
                # a newer loop owns the flag once cancel_reading or a restart bumped the generation
                if self._generation == generation:
                    self.is_active = False
