from __future__ import annotations

import time
from collections.abc import Generator
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser, DispenseContext
from src.machine.i2c.MotorKit import get_motorkit

if TYPE_CHECKING:
    from adafruit_motor.stepper import StepperMotor
    from adafruit_motorkit import MotorKit

    from src.config.config_types import StepperMotorKitPumpConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("StepperMotorKitDispenser")

try:
    from adafruit_motor.stepper import BACKWARD, FORWARD, SINGLE
# Fallback for the values (they are literals, but better use library-provided ones if available)
except (ImportError, RuntimeError, NameError):
    FORWARD = 1
    BACKWARD = 2
    SINGLE = 1

_CHUNK_INTERVAL = 0.01
"""Target interval between callback updates (~100Hz)."""


class StepperMotorKitDispenser(BaseDispenser):
    """Dispenser for stepper motors connected to an Adafruit MotorKit board over I2C.

    Drives the stepper as fast as possible using ``onestep()`` in a tight loop
    (the I2C bus latency is the natural rate limiter). When a scale is provided,
    dispensing stops as soon as the measured weight reaches the target amount.
    """

    def __init__(
        self,
        slot: int,
        config: StepperMotorKitPumpConfig,
        hardware: HardwareContext,
    ) -> None:
        super().__init__(slot, config, hardware)
        self._stepper_number = config.pin  # 1 or 2
        self._address = config.address_hex
        self._kit: MotorKit | None = get_motorkit(self._address)
        if self._kit is None:
            _logger.warning(
                f"Slot {self.slot}: MotorKit board at 0x{self._address:02x} is not available. "
                f"Stepper {self._stepper_number} will not dispense."
            )
        self._step_direction: int = FORWARD

    def _before_dispense(self, ctx: DispenseContext) -> None:
        self._step_direction = BACKWARD if ctx.revert else FORWARD

    def _after_dispense(self, ctx: DispenseContext) -> None:
        self._step_direction = FORWARD

    def _get_stepper(self) -> StepperMotor | None:
        if self._kit is None:
            return None
        return getattr(self._kit, f"stepper{self._stepper_number}", None)

    def _dispense_steps(self, amount_ml: float, pump_speed: int) -> Generator[float]:
        flow_rate = self.volume_flow
        flow_time = amount_ml / flow_rate if flow_rate > 0 else 0.0
        mode = "scale" if self._scale is not None else f"{flow_time:.1f}s"
        _logger.info(
            f"<o> Slot {self.slot:<2} MotorKit-0x{self._address:02x}-S{self._stepper_number:<2}"
            f" | dispensing {amount_ml:.0f}ml ({mode})"
        )
        stepper = self._get_stepper()
        direction = self._step_direction
        consumption = 0.0
        start = time.perf_counter()
        last_yield = start
        try:
            while True:
                if stepper is not None:
                    stepper.onestep(direction=direction, style=SINGLE)
                now = time.perf_counter()
                elapsed = now - start
                consumption = self._get_consumption(flow_rate * elapsed)
                if now - last_yield >= _CHUNK_INTERVAL:
                    yield consumption
                    last_yield = now
                    if consumption >= amount_ml:
                        return
        finally:
            if stepper is not None:
                stepper.release()
            _logger.info(
                f"<x> Slot {self.slot:<2} MotorKit-0x{self._address:02x}-S{self._stepper_number:<2}"
                f" | dispensed {consumption:.0f}ml"
            )

    def stop(self) -> None:
        super().stop()
        stepper = self._get_stepper()
        if stepper is not None:
            stepper.release()

    def cleanup(self) -> None:
        self.stop()
