import time
from collections.abc import Iterator

from src.config.config_types import BaseLedConfig
from src.machine.leds.base import LedInterface


class _FakeLed(LedInterface):
    def __init__(self, config: BaseLedConfig) -> None:
        super().__init__(config, hardware=None)  # ty:ignore[invalid-argument-type]
        self.calls: list[str] = []

    def turn_on(self) -> None:
        self.calls.append("on")

    def turn_off(self) -> None:
        self.calls.append("off")

    def end_frames(self) -> Iterator[float]:
        yield 0.0
        yield 0.0


def _wait_for_effect(led: _FakeLed) -> None:
    thread = led._effect_thread
    assert thread is not None
    thread.join(timeout=2.0)
    assert not thread.is_alive()


def test_finished_end_effect_restores_default_on() -> None:
    led = _FakeLed(BaseLedConfig(default_on=True, preparation_state="Effect"))
    led.preparation_end()
    _wait_for_effect(led)
    assert led.calls[-1] == "on", "end effect finished but LED was not restored to default on"


def test_finished_end_effect_restores_default_off() -> None:
    led = _FakeLed(BaseLedConfig(default_on=False, preparation_state="Effect"))
    led.preparation_end()
    _wait_for_effect(led)
    assert led.calls[-1] == "off"


def test_cancelled_end_effect_does_not_restore() -> None:
    led = _FakeLed(BaseLedConfig(default_on=True, preparation_state="Effect"))

    def slow_frames() -> Iterator[float]:
        while True:
            yield 10.0

    led.end_frames = slow_frames  # type: ignore[method-assign]
    led.preparation_end()
    time.sleep(0.05)
    led.cleanup()
    assert "on" not in led.calls, "cancelled effect must not fight the caller over LED state"
