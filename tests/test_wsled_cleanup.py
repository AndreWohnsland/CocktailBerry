import atexit

import pytest

from src.config.config_types import WS281xLedConfig
from src.machine import leds as leds_pkg
from src.machine.leds import wsled


class _FakeStrip:
    """Stand-in for rpi_ws281x.Adafruit_NeoPixel that registers atexit in __init__.

    Mirrors the real library: it registers ``_cleanup`` before ``begin()``. A failing
    ``begin()`` must not leave that handler behind — in the real library its ``_cleanup``
    calls ``ws2811_fini`` on an uninitialized handle, which segfaults the process on the
    next atexit run (our restart flow calls ``atexit._run_exitfuncs()``).
    """

    ran_cleanup = False

    def __init__(self, *args: object) -> None:
        atexit.register(self._cleanup)

    def _cleanup(self) -> None:
        type(self).ran_cleanup = True

    def begin(self) -> None:
        raise RuntimeError("ws2811_init failed (e.g. not root)")


def _install_fake_pwm(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeStrip.ran_cleanup = False
    monkeypatch.setattr(wsled, "PWM_AVAILABLE", True)
    monkeypatch.setattr(wsled, "Adafruit_NeoPixel", _FakeStrip, raising=False)


def test_failed_pwm_begin_unregisters_orphaned_atexit(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_pwm(monkeypatch)
    config = WS281xLedConfig(pin=18)  # PWM pin -> rpi_ws281x backend

    with pytest.raises(RuntimeError):
        wsled.WSLed(config, hardware=None)  # ty:ignore[invalid-argument-type]

    atexit._run_exitfuncs()  # simulate the restart flow
    assert not _FakeStrip.ran_cleanup, "orphaned rpi_ws281x cleanup survived a failed begin()"


def test_skipped_led_does_not_leave_atexit_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_pwm(monkeypatch)
    config = WS281xLedConfig(pin=18)

    controller = leds_pkg.create_led_controller([config], hardware=None)  # ty:ignore[invalid-argument-type]

    assert controller.led_list == []  # failed LED is skipped
    atexit._run_exitfuncs()
    assert not _FakeStrip.ran_cleanup
