from __future__ import annotations

import time
from collections.abc import Generator
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser, DispenseContext
from src.machine.i2c.MotorKit import get_motorkit

if TYPE_CHECKING:
    from adafruit_motor.motor import DCMotor

    from src.config.config_types import DCMotorKitPumpConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("DCMotorKitDispenser")

_LOOP_INTERVAL = 0.01
"""Sleep interval in seconds for the dispense loop (~100Hz)."""


class DCMotorKitDispenser(BaseDispenser):
    """Dispenser for DC pumps connected to an Adafruit MotorKit board over I2C.

    Uses time-based dispensing by default: runs the motor at full throttle for a
    calculated duration. When a scale is provided, dispensing stops as soon as the
    measured weight reaches the target amount instead.
    """

    def __init__(
        self,
        slot: int,
        config: DCMotorKitPumpConfig,
        hardware: HardwareContext,
    ) -> None:
        super().__init__(slot, config, hardware)
        self._motor_number = config.pin  # 1-4
        self._address = config.address_hex
        self._kit = get_motorkit(self._address)
        if self._kit is None:
            _logger.warning(
                f"Slot {self.slot}: MotorKit board at 0x{self._address:02x} is not available. "
                f"Motor {self._motor_number} will not dispense."
            )
        self._throttle_direction: float = 1.0

    def _before_dispense(self, ctx: DispenseContext) -> None:
        self._throttle_direction = -1.0 if ctx.revert else 1.0

    def _after_dispense(self, ctx: DispenseContext) -> None:
        self._throttle_direction = 1.0

    def _get_motor(self) -> DCMotor | None:
        if self._kit is None:
            return None
        return getattr(self._kit, f"motor{self._motor_number}", None)

    def _dispense_steps(self, amount_ml: float, pump_speed: int) -> Generator[float]:
        flow_rate = self.volume_flow
        flow_time = amount_ml / flow_rate
        mode = "scale" if self._scale is not None else f"{flow_time:.1f}s"
        _logger.info(
            f"<o> Slot {self.slot:<2} MotorKit-0x{self._address:02x}-M{self._motor_number:<2}"
            f" | dispensing {amount_ml:.0f}ml ({mode})"
        )
        motor = self._get_motor()
        if motor is not None:
            motor.throttle = self._throttle_direction
        start = time.perf_counter()
        try:
            while True:
                elapsed = time.perf_counter() - start
                consumption = self._get_consumption(flow_rate * elapsed)
                yield consumption
                if consumption >= amount_ml:
                    return
                time.sleep(_LOOP_INTERVAL)
        finally:
            if motor is not None:
                motor.throttle = 0.0
            _logger.info(
                f"<x> Slot {self.slot:<2} MotorKit-0x{self._address:02x}-M{self._motor_number:<2}"
                f" | dispensed {consumption:.0f}ml"
            )

    def stop(self) -> None:
        super().stop()
        motor = self._get_motor()
        if motor is not None:
            motor.throttle = 0.0

    def cleanup(self) -> None:
        self.stop()
