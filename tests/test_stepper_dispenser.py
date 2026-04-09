"""Tests for StepperDispenser."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from src.config.config_types import StepperPumpConfig
from src.machine.dispensers.stepper import StepperDispenser
from src.machine.hardware import HardwareContext


class TestStepperDispenser:
    def _make_dispenser(self, **kwargs: Any) -> StepperDispenser:
        defaults = {
            "pin": 17,
            "dir_pin": 27,
            "volume_flow": 30.0,
            "tube_volume": 5,
            "driver_type": "A4988",
            "step_type": "Full",
        }
        defaults.update(kwargs)
        config = StepperPumpConfig(**defaults)
        hardware = MagicMock(spec=HardwareContext)
        hardware.scale = None
        return StepperDispenser(slot=1, config=config, hardware=hardware)

    @patch("src.machine.dispensers.stepper.StepperDispenser.setup")
    def test_dispense_calculates_correct_steps(self, mock_setup: MagicMock) -> None:
        d = self._make_dispenser()
        d._motor = MagicMock()
        callback = MagicMock()
        consumption = d.dispense(10.0, 100, callback)
        # Steps are based on duration / (2 * step_delay), not steps_per_ml
        total_steps_called = sum(call.args[2] for call in d._motor.motor_go.call_args_list)
        assert total_steps_called > 0
        assert consumption > 0
        # callback should have been called with done=True at the end
        callback.assert_called()
        last_call = callback.call_args_list[-1]
        assert last_call[0][1] is True  # is_done=True

    @patch("src.machine.dispensers.stepper.StepperDispenser.setup")
    def test_dispense_respects_stop_event(self, mock_setup: MagicMock) -> None:
        d = self._make_dispenser()
        d._motor = MagicMock()
        callback = MagicMock()

        # Stop after the first callback
        def stop_on_callback(consumption: float, is_done: bool) -> None:
            if not is_done:
                d._stop_event.set()

        callback.side_effect = stop_on_callback
        consumption = d.dispense(10.0, 100, callback)
        # Should have dispensed much less than the full 10ml
        assert consumption < 10.0

    @patch("src.machine.dispensers.stepper.StepperDispenser.setup")
    def test_dispense_pump_speed_affects_delay(self, mock_setup: MagicMock) -> None:
        d = self._make_dispenser()
        d._motor = MagicMock()
        callback = MagicMock()

        # Full speed - fewer steps (shorter duration)
        d.dispense(1.0, 100, callback)
        full_speed_steps = sum(call.args[2] for call in d._motor.motor_go.call_args_list)

        d._motor.reset_mock()
        callback.reset_mock()

        # Half speed - more steps (longer duration)
        d.dispense(1.0, 50, callback)
        half_speed_steps = sum(call.args[2] for call in d._motor.motor_go.call_args_list)

        # Half speed should take twice as long (double the steps at same step delay)
        assert half_speed_steps > full_speed_steps * 1.9

    def test_stop_sets_event(self) -> None:
        d = self._make_dispenser()
        d.stop()
        assert d._stop_event.is_set()

    def test_cleanup_calls_stop(self) -> None:
        d = self._make_dispenser()
        d.cleanup()
        assert d._stop_event.is_set()
