from __future__ import annotations

import time
from typing import TYPE_CHECKING

from src import SupportedStepperDriverType, SupportedStepperStepType
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser, ProgressCallback

if TYPE_CHECKING:
    from src.machine.scale import ScaleInterface

_logger = LoggerHandler("StepperDispenser")

try:
    from RpiMotorLib import RpiMotorLib as rpi_motor_lib

    MOTOR_LIB_AVAILABLE = True
except (ModuleNotFoundError, ImportError, RuntimeError):
    MOTOR_LIB_AVAILABLE = False

_CHUNK_INTERVAL = 0.01
"""Target interval between callback updates (~100Hz), matching DC dispenser."""

_DEFAULT_STEP_DELAY = 0.002
"""Fixed step delay in seconds for maximum motor speed (each step = 2 * delay)."""


class StepperDispenser(BaseDispenser):
    """Dispenser for stepper motor pumps controlled via step/dir drivers.

    Uses RpiMotorLib to generate step pulses. Supports A4988, DRV8825,
    A3967, LV8729, and other step/dir driver boards. When a scale is
    provided, dispensing stops as soon as the measured weight reaches the
    target amount; total_steps then acts only as a safety cap.
    """

    def __init__(
        self,
        slot: int,
        volume_flow: float,
        step_pin: int,
        dir_pin: int,
        driver_type: SupportedStepperDriverType,
        step_type: SupportedStepperStepType,
        scale: ScaleInterface | None = None,
        carriage_position: int = 0,
    ) -> None:
        super().__init__(slot, volume_flow, scale, carriage_position)
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.driver_type = driver_type
        self.step_type = step_type
        self._motor: rpi_motor_lib.A4988Nema | None = None

    @property
    def _log_label(self) -> str:
        return f"{self.driver_type:<14}"

    def setup(self) -> None:
        if not MOTOR_LIB_AVAILABLE:
            _logger.warning(f"RpiMotorLib not installed. Will not be able to control slot stepper slot {self.slot}")
            return
        # mode_pins (-1,-1,-1) means micro stepping is hardwired on the driver board
        try:
            self._motor = rpi_motor_lib.A4988Nema(self.dir_pin, self.step_pin, (-1, -1, -1), self.driver_type)
        except Exception as e:
            _logger.error(f"Failed to initialize stepper motor for slot {self.slot}: {e}")

    def dispense(self, amount_ml: float, pump_speed: int, callback: ProgressCallback) -> float:
        self._stop_event.clear()
        flow_rate = self.volume_flow * pump_speed / 100
        # Run stepper at max speed for the duration needed to dispense the volume
        duration = amount_ml / flow_rate if flow_rate > 0 else 0.0
        step_delay = _DEFAULT_STEP_DELAY
        # motor_go sleeps twice per step (HIGH + LOW), so each step = 2 * step_delay
        total_steps = max(1, int(duration / (2 * step_delay)))
        # How many steps per chunk to maintain ~100Hz callback rate
        steps_per_chunk = max(1, int(_CHUNK_INTERVAL / (2 * step_delay)))

        mode = "scale" if self._scale is not None else f"{duration:.1f}s"
        _logger.info(
            f"<o> Slot {self.slot:<2} {self._log_label}| dispensing {amount_ml:.0f}ml, "
            f"{total_steps} steps @ {step_delay * 1000:.3f}ms/step ({mode})"
        )

        if self._scale is not None:
            self._scale.tare()

        steps_done = 0
        consumption = 0.0
        start = time.perf_counter()
        try:
            while steps_done < total_steps and not self._stop_event.is_set():
                chunk = min(steps_per_chunk, total_steps - steps_done)
                if self._motor is not None:
                    self._motor.motor_go(
                        False,  # clockwise
                        self.step_type,
                        chunk,
                        step_delay,
                        False,  # verbose off
                        0.0,  # init_delay
                    )
                steps_done += chunk
                step_estimate = (steps_done / total_steps) * amount_ml
                consumption = self._get_consumption(step_estimate)
                if consumption >= amount_ml:
                    break
                callback(consumption, False)
        finally:
            pass

        elapsed = time.perf_counter() - start
        _logger.info(f"<x> Slot {self.slot:<2} {self._log_label}| dispensed {consumption:.0f}ml in {elapsed:.1f}s")
        callback(consumption, True)
        return consumption

    def stop(self) -> None:
        self._stop_event.set()

    def cleanup(self) -> None:
        self.stop()
