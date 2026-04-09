from __future__ import annotations

import time
from typing import Any

from src import ConsumptionEstimationType
from src.config.config_types import BasePumpConfig, StringType
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser, ProgressCallback
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

    Inherited attributes and methods from BaseDispenser:
      self.slot              — pump slot number (int)
      self.config            — your ConfigClass instance
      self.volume_flow       — configured flow rate in ml/s
      self.carriage_position — carriage position (0-100)
      self._stop_event       — threading.Event, set by stop() to signal cancellation.
                               Must be cleared at the start of dispense() via
                               self._stop_event.clear(). Check it in your dispense loop.
      self._scale            — ScaleInterface or None when no scale is connected

      self._get_consumption(estimate) — returns scale reading (ml) if a scale
          is present, otherwise returns the passed time/step-based estimate.
      self.needs_exclusive   — property, True when a scale is attached (used for scheduling).

    Methods with sensible defaults (override only if needed):
      stop()    — sets _stop_event. Override and call super().stop() if you
                  need additional hardware cleanup on emergency stop.
      cleanup() — does nothing by default. Override to release hardware resources
                  at program shutdown.
    """

    def __init__(self, slot: int, config: ConfigClass, scale: ScaleInterface | None = None) -> None:
        super().__init__(slot, config, scale)
        self.label = config.label

    def setup(self) -> None:
        """Initialize hardware resources for this dispenser."""
        _logger.info(f"Dispenser '{self.label}' slot {self.slot} set up")

    def dispense(self, amount_ml: float, pump_speed: int, callback: ProgressCallback) -> float:
        """Dispense the given amount at the given pump speed.

        Must be blocking. Return the actual consumption in ml.
        Check self._stop_event to support cancellation.
        """
        # Clear the stop event from any previous stop() call
        self._stop_event.clear()
        effective_flow = self.volume_flow * pump_speed / 100
        step_interval = 0.1  # update every 100ms
        elapsed = 0.0

        # If a scale is connected, tare it before dispensing
        if self._scale is not None:
            self._scale.tare()

        _logger.info(f"Dispenser '{self.label}' slot {self.slot}: dispensing {amount_ml:.1f} ml")
        consumption = 0.0
        while not self._stop_event.is_set():
            time.sleep(step_interval)
            elapsed += step_interval
            # _get_consumption uses the scale reading if available,
            # otherwise falls back to the time-based estimate
            time_estimate = min(elapsed * effective_flow, amount_ml)
            consumption = self._get_consumption(time_estimate)
            callback(consumption, False)
            if consumption >= amount_ml:
                break

        callback(consumption, True)
        _logger.info(f"Dispenser '{self.label}' slot {self.slot}: done, dispensed {consumption:.1f} ml")
        return consumption

    def stop(self) -> None:
        """Emergency stop / cancel current dispensing."""
        super().stop()

    def cleanup(self) -> None:
        """Release hardware resources."""
        _logger.info(f"Dispenser '{self.label}' slot {self.slot} cleaned up")
