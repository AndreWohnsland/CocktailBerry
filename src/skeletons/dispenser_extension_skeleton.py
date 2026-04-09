from __future__ import annotations

import time
from collections.abc import Generator
from typing import Any

from src import ConsumptionEstimationType
from src.config.config_types import BasePumpConfig, StringType
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser
from src.machine.scale import ScaleInterface

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# This is a hardware extension skeleton.
# For more information see: https://docs.cocktailberry.org/hardware-extensions/
# Your custom extension needs four exports:
#   EXTENSION_NAME - unique name shown in the hardware type dropdown
#   CONFIG_FIELDS  - dict of extra config fields (beyond the shared BasePumpConfig fields)
#   ConfigClass    - config class inheriting from BasePumpConfig
#   Implementation - dispenser class inheriting from BaseDispenser
#
# Shared fields (volume_flow, tube_volume, consumption_estimation, carriage_position)
# are auto-injected — only define your EXTRA fields in CONFIG_FIELDS.


EXTENSION_NAME = "EXTENSION_NAME_HOLDER"
_logger = LoggerHandler("EXTENSION_NAME_HOLDER")


class ConfigClass(BasePumpConfig):
    """Custom configuration for this dispenser type.

    Add any extra attributes your dispenser needs beyond the shared ones.
    """

    label: str

    def __init__(
        self,
        label: str = "default",
        pump_type: str = EXTENSION_NAME,
        volume_flow: float = 30.0,
        tube_volume: int = 0,
        consumption_estimation: ConsumptionEstimationType = "time",
        carriage_position: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            pump_type=pump_type,
            volume_flow=volume_flow,
            tube_volume=tube_volume,
            consumption_estimation=consumption_estimation,
            carriage_position=carriage_position,
        )
        self.label = label

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update({"label": self.label})
        return config


# Only define the EXTRA fields here. Shared fields (volume_flow, tube_volume, etc.)
# and the pump_type dropdown are auto-injected by the extension manager.
CONFIG_FIELDS: dict[str, Any] = {
    "label": StringType(default="default"),
}


class Implementation(BaseDispenser):
    """Custom dispenser implementation.

    Override ``_dispense_steps()`` to implement your dispensing logic as a
    generator. The base class handles stop-event management, scale taring,
    and progress callbacks automatically — you only yield consumption values.

    Inherited attributes from BaseDispenser:
      self.slot              — pump slot number (int)
      self.config            — your ConfigClass instance
      self.volume_flow       — configured flow rate in ml/s
      self.carriage_position — carriage position (0-100)
      self._scale            — ScaleInterface or None when no scale is connected

    Key inherited methods:
      self._get_consumption(estimate) — returns scale reading (ml) if a scale
          is present, otherwise returns the passed time/step-based estimate.

    Optionally override (sensible defaults provided):
      stop()    — for immediate hardware shutdown on emergency stop.
                  Always call super().stop(). Runs from another thread.
      cleanup() — release hardware at program shutdown.
    """

    def __init__(self, slot: int, config: ConfigClass, scale: ScaleInterface | None = None) -> None:
        super().__init__(slot, config, scale)
        self.label = config.label

    def setup(self) -> None:
        """Initialize hardware resources for this dispenser."""
        _logger.info(f"Dispenser '{self.label}' slot {self.slot} set up")

    def _dispense_steps(self, amount_ml: float, pump_speed: int) -> Generator[float]:
        """Yield consumption values while dispensing.

        The base class iterates this generator and handles:
        - Cancellation (stop event) — generator is closed, triggering finally
        - Scale taring (if a scale is connected)
        - Progress callbacks to the scheduler

        Use try/finally for hardware cleanup — it runs on both normal
        completion and cancellation.
        """
        effective_flow = self.volume_flow * pump_speed / 100
        step_interval = 0.1  # update every 100ms
        elapsed = 0.0

        _logger.info(f"Dispenser '{self.label}' slot {self.slot}: dispensing {amount_ml:.1f} ml")
        consumption = 0.0
        try:
            # >>> Activate your hardware here <<<
            while True:
                time.sleep(step_interval)
                elapsed += step_interval
                # _get_consumption uses the scale reading if available,
                # otherwise falls back to the time-based estimate
                time_estimate = min(elapsed * effective_flow, amount_ml)
                consumption = self._get_consumption(time_estimate)
                yield consumption
                if consumption >= amount_ml:
                    return
        finally:
            # >>> Deactivate your hardware here <<<
            _logger.info(f"Dispenser '{self.label}' slot {self.slot}: done, dispensed {consumption:.1f} ml")

    def cleanup(self) -> None:
        """Release hardware resources."""
        _logger.info(f"Dispenser '{self.label}' slot {self.slot} cleaned up")
