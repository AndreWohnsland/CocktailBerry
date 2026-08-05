from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Generator
from dataclasses import dataclass
from threading import Event
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler

if TYPE_CHECKING:
    from src.config.config_types import BasePumpConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("BaseDispenser")

ProgressCallback = Callable[[float, bool], None]
"""Callback signature: (consumption_ml, is_done) -> None"""

# Overshoot compensation tuning. Module constants on purpose (no user config for now);
# if per-run latency measurement proves unstable on real machines, a config fallback
# (fixed per-pump stop lead) is the escape hatch.
_SCALE_JITTER_G = 1.0
"""Weight changes at or below this are treated as scale noise, not liquid."""
_GRADIENT_WINDOW_S = 0.5
"""Time span of scale samples used to estimate the flow gradient (ml/s)."""
_MIN_GRADIENT_SAMPLES = 3
"""Minimum samples in the window before the gradient is trusted."""
_MAX_STOP_LEAD_S = 0.5
"""Cap for the measured start latency.

Physics bound: fall time over the <0.5m outlet-to-glass distance is ~0.2-0.3s, plus scale
reading lag. It also bounds the error from an unprimed first pour, where the pump pulls
air for 1-2s before liquid arrives and the measured latency would otherwise be way too long.
If the start-side measurement proves unreliable, the settle phase already measures the true
in-flight amount (settled - cutoff) and could provide the lead instead.
"""
_SETTLE_TIMEOUT_S = 1.5
"""Hard upper bound for waiting on a stable reading after the pump stopped."""
_STALL_TIMEOUT_S = 5.0
"""Abort a scale-based dispense when the weight made no new high for this long.

Catches empty bottles, blocked tubes and lost prime, where the pump would
otherwise run forever waiting for weight that never arrives. Generous enough
to cover the 1-2s unprimed start; raise if field priming times demand it.
"""
_SETTLE_POLL_S = 0.05
"""Poll interval while waiting for the reading to settle."""


class _StopPredictor:
    """Predicts when to cut the pump so in-flight liquid lands exactly on target.

    Stopping a pump at the moment the scale reads the target overshoots: the liquid
    already falling still adds weight. The start transient mirrors the stop transient,
    so the time between pump activation and the first reliable weight increase
    ("start latency") is used as the stop lead. The flow gradient (ml/s) is estimated
    over a sliding window that starts only after liquid arrived - including the dead
    time would drag the gradient down and stop too late. Until both latency and a
    trustworthy gradient exist (small amounts, blocked tube, revert), nothing happens
    and the caller's own target check applies unchanged.
    """

    def __init__(self, target_ml: float) -> None:
        self._target = target_ml
        self._start: float | None = None
        self.lead_s: float | None = None
        self.gradient: float | None = None
        self._samples: deque[tuple[float, float]] = deque()

    def should_stop(self, consumption: float) -> bool:
        now = time.monotonic()
        if self._start is None:
            self._start = now
        if self.lead_s is None:
            if consumption <= _SCALE_JITTER_G:
                return False
            self.lead_s = min(now - self._start, _MAX_STOP_LEAD_S)
        self._samples.append((now, consumption))
        # keep the window just above _GRADIENT_WINDOW_S: drop the oldest sample only
        # while the second-oldest still spans the full window
        while len(self._samples) >= _MIN_GRADIENT_SAMPLES and now - self._samples[1][0] >= _GRADIENT_WINDOW_S:
            self._samples.popleft()
        first_t, first_w = self._samples[0]
        span = now - first_t
        if span < _GRADIENT_WINDOW_S or len(self._samples) < _MIN_GRADIENT_SAMPLES:
            return False
        gradient = (consumption - first_w) / span
        if gradient <= 0:
            return False
        self.gradient = gradient
        return (self._target - consumption) / gradient <= self.lead_s


class _StallWatchdog:
    """Detects a pour where the scale weight stopped rising (empty bottle, blocked tube).

    Tracks the consumption high-water mark; trips when no new high beyond the
    jitter threshold arrived within _STALL_TIMEOUT_S.
    """

    def __init__(self) -> None:
        self._high = 0.0
        self._last_rise = time.monotonic()

    def tripped(self, consumption: float) -> bool:
        now = time.monotonic()
        if consumption > self._high + _SCALE_JITTER_G:
            self._high = consumption
            self._last_rise = now
            return False
        return now - self._last_rise > _STALL_TIMEOUT_S


@dataclass
class DispenseContext:
    """Contextual information passed to dispenser hooks.

    Passed to ``_before_dispense`` and ``_after_dispense``. New fields
    added here with defaults will never break existing extension code.
    """

    revert: bool
    """Whether this dispense run should reverse the motor direction."""


class BaseDispenser(ABC):
    """Base class for all dispenser types.

    Each dispenser controls one pump slot. Subclasses implement
    ``_dispense_steps()`` as a generator that yields consumption values.
    The concrete ``dispense()`` method handles stop-event management,
    scale taring, and progress callbacks automatically.
    """

    last_dispense_stalled = False
    """True when the previous dispense was aborted by the stall watchdog (e.g. empty bottle)."""

    def __init__(
        self,
        slot: int,
        config: BasePumpConfig,
        hardware: HardwareContext,
    ) -> None:
        self.slot = slot
        self.config = config
        self.volume_flow = config.volume_flow
        self._stop_event = Event()
        self.hardware = hardware
        # _scale is what the config wires up; _active_scale is what the current
        # dispense run actually uses (None for time-based runs, e.g. cleaning)
        self._scale = hardware.scale if config.consumption_estimation == "weight" else None
        self._active_scale = self._scale
        self.carriage_position = config.carriage_position

    @property
    def needs_exclusive(self) -> bool:
        """True when this dispenser requires exclusive scheduling (i.e. it uses a scale)."""
        return self._scale is not None

    def _before_dispense(self, ctx: DispenseContext) -> None: ...  # noop
    def _after_dispense(self, ctx: DispenseContext) -> None: ...  # noop

    def dispense(
        self,
        amount_ml: float,
        pump_speed: int,
        revert: bool,
        callback: ProgressCallback,
        use_scale: bool = True,
    ) -> float:
        """Dispense the given amount at the given pump speed.

        This is a template method that drives ``_dispense_steps()``.
        It handles clearing/checking the stop event, taring the scale,
        and calling the progress callback. Subclasses normally only need
        to implement ``_dispense_steps()``.

        pump_speed is the percentage of the pump's configured volume_flow
        (100 = full speed). Returns actual consumption in ml.

        With a scale, a _StopPredictor cuts the pump early so falling liquid
        lands on target instead of overshooting, the final consumption is
        read after the scale settled (single-shot: a small undershoot is
        accepted, there is no top-up pass), and a stall watchdog aborts the
        pour when the weight makes no progress (empty bottle, blocked tube),
        flagging it via ``last_dispense_stalled``.

        ``use_scale=False`` runs the whole dispense time-based even when a
        scale is configured — no tare, reads, watchdog or settle. Cleaning
        uses this: it is wall-clock driven and its flush water may never hit
        the scale (also, parallel cleaning pumps must not share the scale bus).
        """
        self._stop_event.clear()
        self.last_dispense_stalled = False
        self._active_scale = self._scale if use_scale else None
        if self._active_scale is not None:
            self._active_scale.tare()
        consumption = 0.0
        ctx = DispenseContext(revert=revert)
        self._before_dispense(ctx)
        callback(consumption, False)
        predictor = _StopPredictor(amount_ml) if self._active_scale is not None else None
        watchdog = _StallWatchdog() if self._active_scale is not None else None
        steps = self._dispense_steps(amount_ml, pump_speed)
        for consumption in steps:
            if self._stop_event.is_set():
                break
            if predictor is not None and predictor.should_stop(consumption):
                break
            if watchdog is not None and watchdog.tripped(consumption):
                self._mark_stalled(consumption, amount_ml)
                break
            callback(consumption, False)
        # close explicitly so the dispenser's finally block shuts the hardware off
        # before the settle reading starts
        steps.close()
        # If a scale was used, wait for the reading to settle and log the final consumption.
        # This is important since otherwise we cannot know how much liquid still fell after a stop
        if self._active_scale is not None and predictor is not None:
            consumption = self._settle_and_log(consumption, amount_ml, predictor, callback)
        callback(consumption, True)
        self._after_dispense(ctx)
        return consumption

    def _mark_stalled(self, consumption: float, amount_ml: float) -> None:
        """Flag the current dispense as stalled and log the abort."""
        self.last_dispense_stalled = True
        _logger.warning(
            f"Slot {self.slot} | no weight increase for {_STALL_TIMEOUT_S}s at "
            f"{consumption:.1f}/{amount_ml:.1f}ml, stopping (empty bottle or blocked tube?)"
        )

    def _settle_and_log(
        self,
        cutoff: float,
        amount_ml: float,
        predictor: _StopPredictor,
        callback: ProgressCallback,
    ) -> float:
        """Wait for the settled scale reading and log how the pour landed."""
        settled = self._read_settled_consumption(cutoff, callback)
        lead = f"{predictor.lead_s:.2f}s" if predictor.lead_s is not None else "n/a"
        gradient = f"{predictor.gradient:.1f}ml/s" if predictor.gradient is not None else "n/a"
        _logger.debug(
            f"Slot {self.slot} | target {amount_ml:.1f}ml | lead {lead} | gradient {gradient} | "
            f"stopped at {cutoff:.1f}ml | settled {settled:.1f}ml | miss {settled - amount_ml:+.1f}ml"
        )
        return settled

    def _read_settled_consumption(self, at_cutoff: float, callback: ProgressCallback) -> float:
        """Wait until the scale reading stops changing (no more falling liquid), return it.

        Runs after every scale-based dispense ending (early stop, target reached,
        cancel) so the reported consumption is the weight that actually landed in
        the glass. Settled means the reading moved at most _SCALE_JITTER_G over a
        _GRADIENT_WINDOW_S span; _SETTLE_TIMEOUT_S bounds the wait. A cancel
        arriving during the wait aborts it (a dispense already canceled before the
        wait still settles normally). Each reading is emitted through the progress
        callback so the progress bar keeps moving while in-flight liquid lands.
        """
        scale = self._active_scale
        if scale is None:
            return at_cutoff
        start = time.monotonic()
        was_stopped = self._stop_event.is_set()
        stable_since = start
        reading = at_cutoff
        while time.monotonic() - start < _SETTLE_TIMEOUT_S:
            if not was_stopped and self._stop_event.is_set():
                break
            previous = reading
            reading = scale.read_grams()
            callback(reading, False)
            now = time.monotonic()
            if abs(reading - previous) > _SCALE_JITTER_G:
                stable_since = now
            if now - stable_since >= _GRADIENT_WINDOW_S:
                break
            time.sleep(_SETTLE_POLL_S)
        return reading

    @abstractmethod
    def _dispense_steps(self, amount_ml: float, pump_speed: int) -> Generator[float]:
        """Yield consumption values during dispensing.

        The base ``dispense()`` iterates this generator and handles:
        - Clearing / checking the stop event (cancellation)
        - Taring the scale (if present)
        - Calling progress callbacks

        Implementations should:
        1. Activate hardware, then yield consumption updates in a loop.
        2. Use ``self._get_consumption(estimate)`` to read the scale when
           available or fall back to a time/step-based estimate.
        3. Use ``try/finally`` for hardware cleanup — the generator is
           automatically closed on cancellation, so ``finally`` runs
           in both normal and stop scenarios.

        Minimal example::

            def _dispense_steps(self, amount_ml, pump_speed):
                flow = self.volume_flow * pump_speed / 100
                elapsed = 0.0
                try:
                    self._activate()
                    while True:
                        time.sleep(0.01)
                        elapsed += 0.01
                        consumption = self._get_consumption(elapsed * flow)
                        yield consumption
                        if consumption >= amount_ml:
                            return
                finally:
                    self._deactivate()
        """

    def stop(self) -> None:
        """Emergency stop / cancel current dispensing.

        Sets the stop event so the dispense loop exits.
        Override this if you need additional hardware cleanup on stop
        (e.g. closing a relay pin), but always call super().stop().
        """
        self._stop_event.set()

    def cleanup(self) -> None:
        """Release hardware resources.

        Called at program shutdown. Override if your dispenser holds
        hardware resources that need explicit release.
        The default implementation does nothing.
        """

    def _get_consumption(self, current_estimate: float) -> float:
        """Return current consumption in ml.

        When a scale is present and in use for this dispense, reads grams
        directly (density assumed ~1 g/ml). Otherwise returns the caller's
        time/step-based estimate.
        """
        if self._active_scale is not None:
            return self._active_scale.read_grams()
        return current_estimate
