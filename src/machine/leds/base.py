from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from threading import Event, Lock, Thread
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler

if TYPE_CHECKING:
    from src.config.config_types import BaseLedConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("LedInterface")

_JOIN_TIMEOUT_S = 0.5


class LedInterface(ABC):
    """Abstract interface for one LED (or LED group) in the machine.

    Each LED entry in ``cfg.LED_CONFIG`` resolves to one ``LedInterface``
    instance owned by the :class:`LedController` singleton. The controller
    iterates the list and forwards lifecycle events (preparation start/end,
    default on, shutdown) to each LED.

    Extensions implement at most four things:

    * :meth:`turn_on` / :meth:`turn_off` — steady on/off (required).
    * :meth:`active_frames` — generator yielding seconds-to-sleep between
      animation frames during preparation. Default: empty (falls back to
      :meth:`turn_on`).
    * :meth:`end_frames` — same shape, for the post-preparation animation.
      Default: empty (falls back to :meth:`turn_on` or :meth:`turn_off`
      depending on :attr:`default_on`).

    Threading, cancellation, and the ``preparation_state`` switch are
    handled by this base class — extensions never spawn threads or check
    cancel flags. When a new effect needs to start, the previously running
    one is cancelled and joined first, eliminating concurrent writes to
    shared hardware (e.g. a WS281x strip).
    """

    default_on: bool

    def __init__(self, config: BaseLedConfig, hardware: HardwareContext) -> None:
        self.config = config
        self.hardware = hardware
        self.default_on = config.default_on
        self.preparation_state = config.preparation_state
        self._stop_effect = Event()
        self._effect_thread: Thread | None = None
        # Guards _effect_thread + _stop_effect transitions so concurrent
        # callers (e.g. preparation_end + cleanup from different threads)
        # cannot interleave and leak running effects.
        self._effect_lock = Lock()

    @abstractmethod
    def turn_on(self) -> None:
        """Switch the LED on with its default appearance."""

    @abstractmethod
    def turn_off(self) -> None:
        """Switch the LED off."""

    def active_frames(self) -> Iterator[float]:
        """Yield seconds-to-sleep between frames of the preparation animation.

        Implement this for animated indicators during a cocktail run. The base
        class drives the iterator in a daemon thread and stops it (closing the
        generator) when preparation ends or the LED is cleaned up. Yielded
        sleeps may be any duration — they are interrupted immediately on
        cancellation. The real constraint is the **frame body**: the work
        between yields (and inside :meth:`turn_on` / :meth:`turn_off`) cannot
        be interrupted, so keep it non-blocking (sub-100 ms is a sensible
        target). Avoid ``time.sleep`` or blocking I/O between yields.

        Default implementation yields nothing — the LED stays at :meth:`turn_on`.
        """
        return iter(())

    def end_frames(self) -> Iterator[float]:
        """Yield seconds-to-sleep between frames of the post-preparation animation.

        The implementation decides how long the animation runs (built-in LEDs
        use 5 s). The base class still cancels the iterator if a new
        preparation starts, the controller turns off, or shutdown is triggered.
        The same frame-body constraint as :meth:`active_frames` applies: keep
        the work between yields non-blocking; the yielded sleep itself is
        unconstrained.

        Default implementation yields nothing — the LED snaps back to
        :meth:`turn_on` or :meth:`turn_off` depending on :attr:`default_on`.
        """
        return iter(())

    # ----- final lifecycle -- extensions should not override below -----

    def preparation_start(self) -> None:
        """Drive the LED into its preparation state.

        Cancels any previously running effect, then dispatches based on
        :attr:`preparation_state`:

        * ``"On"``   → :meth:`turn_on`.
        * ``"Off"``  → :meth:`turn_off`.
        * ``"Effect"`` → run :meth:`active_frames` on a daemon thread; if the
          generator is empty, falls back to :meth:`turn_on`.
        """
        self._stop_active_effect()
        if self.preparation_state == "Off":
            self.turn_off()
            return
        if self.preparation_state == "On":
            self.turn_on()
            return
        # Effect
        self._spawn_effect(lambda: self._run_iter(self.active_frames(), fallback=self.turn_on))

    def preparation_end(self) -> None:
        """Drive the LED out of its preparation state.

        Cancels any previously running effect, then dispatches based on
        :attr:`preparation_state`:

        * ``"Effect"`` → run :meth:`end_frames` on a daemon thread; if the
          generator is empty, falls back to :meth:`turn_on` / :meth:`turn_off`
          based on :attr:`default_on`. The implementation decides the
          animation duration.
        * non-Effect modes snap straight to the idle state.
        """
        self._stop_active_effect()
        if self.preparation_state == "Effect":
            self._spawn_effect(lambda: self._run_iter(self.end_frames(), fallback=self._restore_idle))
            return
        self._restore_idle()

    def cleanup(self) -> None:
        """Stop any running effect and release driver-specific handles.

        Pin cleanup is handled centrally by ``HardwareContext``. Override if
        your driver holds extra resources (SPI, USB, timers).
        """
        self._stop_active_effect()

    # ----- internals -----

    def _restore_idle(self) -> None:
        if self.default_on:
            self.turn_on()
        else:
            self.turn_off()

    def _spawn_effect(self, target: Callable[[], None]) -> None:
        with self._effect_lock:
            self._stop_effect.clear()
            thread = Thread(target=target, daemon=True)
            self._effect_thread = thread
            thread.start()

    def _stop_active_effect(self) -> None:
        with self._effect_lock:
            thread = self._effect_thread
            if thread is None:
                return
            self._stop_effect.set()
            self._effect_thread = None
        # Join outside the lock so a stuck thread cannot deadlock new callers
        # waiting on the same lock; only this caller observes ``thread`` because
        # we already cleared the field above.
        if thread.is_alive():
            thread.join(timeout=_JOIN_TIMEOUT_S)
            if thread.is_alive():
                _logger.warning(
                    f"LED effect thread for {type(self).__name__} did not stop within "
                    f"{_JOIN_TIMEOUT_S}s; it will keep running until it next observes the stop event "
                    "(check that frame bodies are non-blocking and turn_on/turn_off do not block)"
                )

    def _run_iter(self, iterator: Iterator[float], fallback: Callable[[], None]) -> None:
        """Drive a frame iterator, sleeping per yielded value, honouring the stop event.

        Cancellation is event-driven: ``Event.wait(timeout=sleep_s)`` returns
        immediately when ``_stop_effect`` is set, so latency is bounded by the
        per-frame yield rather than a fixed poll interval. If the iterator
        yields no frames, ``fallback()`` is invoked so static LEDs end up in
        the right idle state without any per-extension code.
        """
        produced_frame = False
        try:
            for sleep_s in iterator:
                produced_frame = True
                if self._stop_effect.is_set():
                    return
                # Event.wait returns True if the event was set during the wait.
                if self._stop_effect.wait(timeout=max(0.0, float(sleep_s))):
                    return
        except Exception:
            _logger.log_exception("LED effect iterator raised")
        finally:
            close = getattr(iterator, "close", None)
            if callable(close):
                with contextlib.suppress(Exception):
                    close()
            if not produced_frame and not self._stop_effect.is_set():
                try:
                    fallback()
                except Exception:
                    _logger.log_exception("LED fallback after empty effect raised")
