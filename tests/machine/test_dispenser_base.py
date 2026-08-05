"""Tests for the scale overshoot compensation in BaseDispenser.dispense().

Uses a fake clock (patched into the dispenser base module) and a scripted scale
that models liquid physics: liquid pumped at time t lands on the scale at
t + fall_time, so stopping the pump at the target weight would overshoot by
flow * fall_time.
"""

from __future__ import annotations

from threading import Event

import pytest

import src.machine.dispensers.base as dispenser_base
from src.machine.dispensers.base import BaseDispenser


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def perf_counter(self) -> float:
        return self.now


class FakeScale:
    """Scale over a pump with constant flow and a constant fall time.

    Weight on the scale at time t is all liquid that left the pump before
    t - fall_time. Each read advances the clock by the ADC sample interval,
    like a real rate-limited load cell amplifier.
    """

    def __init__(self, clock: FakeClock, flow_ml_s: float, fall_time_s: float, sample_interval_s: float = 0.08) -> None:
        self.clock = clock
        self.flow = flow_ml_s
        self.fall_time = fall_time_s
        self.sample_interval = sample_interval_s
        self.pump_started_at: float | None = None
        self.pump_stopped_at: float | None = None
        self.noise_g = 0.0
        self._noise_sign = 1

    def tare(self, samples: int = 3) -> int:
        return 0

    def read_grams(self) -> float:
        self.clock.sleep(self.sample_interval)
        now = self.clock.monotonic()
        weight = 0.0
        if self.pump_started_at is not None:
            pump_end = self.pump_stopped_at if self.pump_stopped_at is not None else now
            landed_until = min(now - self.fall_time, pump_end)
            weight = self.flow * max(0.0, landed_until - self.pump_started_at)
        self._noise_sign = -self._noise_sign
        return weight + self.noise_g * self._noise_sign


class DummyDispenser(BaseDispenser):
    """Minimal concrete dispenser wired directly to the fake scale, no hardware."""

    def __init__(self, scale: FakeScale) -> None:
        self.slot = 1
        self.volume_flow = scale.flow
        self._stop_event = Event()
        self._scale = scale
        self.pump_on = False

    def _dispense_steps(self, amount_ml: float, pump_speed: int):
        self.pump_on = True
        self._scale.pump_started_at = self._scale.clock.monotonic()  # ty:ignore[unresolved-attribute, invalid-assignment]
        try:
            while True:
                consumption = self._get_consumption(0.0)
                yield consumption
                if consumption >= amount_ml:
                    return
        finally:
            self.pump_on = False
            self._scale.pump_stopped_at = self._scale.clock.monotonic()  # ty:ignore[unresolved-attribute, invalid-assignment]


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(dispenser_base, "time", fake)
    return fake


def _collect_progress() -> tuple[list[tuple[float, bool]], dispenser_base.ProgressCallback]:
    calls: list[tuple[float, bool]] = []

    def callback(consumption: float, done: bool) -> None:
        calls.append((consumption, done))

    return calls, callback


def test_early_stop_lands_on_target(clock: FakeClock) -> None:
    # 25 ml/s with 0.5s fall time: naive stop-at-target would overshoot by ~12.5 ml
    scale = FakeScale(clock, flow_ml_s=25.0, fall_time_s=0.5)
    dispenser = DummyDispenser(scale)
    calls, callback = _collect_progress()

    result = dispenser.dispense(40.0, 100, revert=False, callback=callback)

    assert scale.pump_stopped_at is not None
    cutoff = scale.flow * max(0.0, scale.pump_stopped_at - scale.pump_started_at - scale.fall_time)  # ty:ignore[unsupported-operator]
    assert cutoff < 40.0  # pump was cut before the scale read the target
    assert result == pytest.approx(40.0, abs=3.0)  # settled weight lands on target
    assert calls[-1] == (result, True)


def test_tiny_amount_uses_backstop(clock: FakeClock) -> None:
    # target is reached before latency + gradient window can arm the predictor
    scale = FakeScale(clock, flow_ml_s=25.0, fall_time_s=0.5)
    dispenser = DummyDispenser(scale)
    calls, callback = _collect_progress()

    result = dispenser.dispense(5.0, 100, revert=False, callback=callback)

    assert not dispenser.pump_on
    assert result >= 5.0  # today's behavior: stop at target, overshoot settles on top
    assert calls[-1] == (result, True)


def test_settle_keeps_progress_updating(clock: FakeClock) -> None:
    # after the early cut, in-flight liquid still lands; the progress callback
    # must keep reporting during the settle wait instead of freezing at the cutoff
    scale = FakeScale(clock, flow_ml_s=25.0, fall_time_s=0.5)
    dispenser = DummyDispenser(scale)
    during_settle: list[float] = []

    def callback(consumption: float, done: bool) -> None:
        if not dispenser.pump_on and not done:
            during_settle.append(consumption)

    result = dispenser.dispense(40.0, 100, revert=False, callback=callback)

    assert during_settle  # progress kept flowing after the pump was cut
    assert max(during_settle) == pytest.approx(result, abs=1.0)  # crept up to the settled value


def test_cancel_still_settles(clock: FakeClock) -> None:
    scale = FakeScale(clock, flow_ml_s=25.0, fall_time_s=0.5)
    dispenser = DummyDispenser(scale)

    def cancel_at_10(consumption: float, done: bool) -> None:
        if not done and consumption > 10.0:
            dispenser.stop()

    result = dispenser.dispense(100.0, 100, revert=False, callback=cancel_at_10)

    assert not dispenser.pump_on
    # settle picked up the liquid still in the air when the cancel hit
    assert result > 10.0
    assert result < 100.0


def test_noisy_scale_settle_hits_timeout(clock: FakeClock) -> None:
    scale = FakeScale(clock, flow_ml_s=25.0, fall_time_s=0.5)
    dispenser = DummyDispenser(scale)
    _, callback = _collect_progress()

    original_read = scale.read_grams

    def noisy_after_pump_off() -> float:
        if scale.pump_stopped_at is not None:
            scale.noise_g = 2.0  # above jitter threshold: reading never counts as stable
        return original_read()

    scale.read_grams = noisy_after_pump_off  # ty:ignore[invalid-assignment]

    settle_start_max = 10.0  # generous bound for the dispense itself
    result = dispenser.dispense(40.0, 100, revert=False, callback=callback)

    assert not dispenser.pump_on
    assert result == pytest.approx(40.0, abs=5.0)
    # the settle wait gave up at the timeout instead of hanging forever
    assert clock.now < settle_start_max + dispenser_base._SETTLE_TIMEOUT_S


def test_stall_watchdog_stops_on_empty_bottle(clock: FakeClock) -> None:
    scale = FakeScale(clock, flow_ml_s=25.0, fall_time_s=0.5)
    dispenser = DummyDispenser(scale)
    _, callback = _collect_progress()

    original_read = scale.read_grams

    def bottle_empty_at_15ml() -> float:
        return min(original_read(), 15.0)

    scale.read_grams = bottle_empty_at_15ml  # ty:ignore[invalid-assignment]

    result = dispenser.dispense(100.0, 100, revert=False, callback=callback)

    assert dispenser.last_dispense_stalled
    assert not dispenser.pump_on
    assert result == pytest.approx(15.0, abs=2.0)  # honest consumption, not the target
    # tripped roughly one stall timeout after the weight went flat, not much later
    assert clock.now < 15.0


def test_cleaning_ignores_scale(clock: FakeClock) -> None:
    scale = FakeScale(clock, flow_ml_s=25.0, fall_time_s=0.5)
    dispenser = DummyDispenser(scale)

    scale_calls = 0

    def counting_read() -> float:
        nonlocal scale_calls
        scale_calls += 1
        return 0.0

    scale.read_grams = counting_read  # ty:ignore[invalid-assignment]
    scale.tare = counting_read  # ty:ignore[invalid-assignment]

    # without scale reads nothing advances the clock, so the callback drives it
    def advance_and_stop_after_8s(consumption: float, done: bool) -> None:
        clock.sleep(0.08)
        if not done and clock.now > 8.0:
            dispenser.stop()

    result = dispenser.dispense(2000.0, 100, revert=False, callback=advance_and_stop_after_8s, use_scale=False)

    assert scale_calls == 0  # no tare, no reads, no settle: scale untouched
    assert not dispenser.last_dispense_stalled  # ran well past the stall timeout without tripping
    assert clock.now > 8.0
    assert result == 0.0  # time-based estimate from the dummy, not a scale value
