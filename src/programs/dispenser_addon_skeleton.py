from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src import ConsumptionEstimationType
from src.config.config_types import BasePumpConfig, FloatType, IntType
from src.config.validators import build_number_limiter
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


class ConfigClass(BasePumpConfig):
    """Custom configuration for this dispenser type.

    Add any extra attributes your dispenser needs beyond the shared ones.
    """

    pin: int

    def __init__(
        self,
        pin: int = 0,
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
        self.pin = pin

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update({"pin": self.pin})
        return config


# Only define the EXTRA fields here. Shared fields (volume_flow, tube_volume, etc.)
# and the pump_type dropdown are auto-injected by the addon manager.
CONFIG_FIELDS: dict[str, Any] = {
    "pin": IntType([build_number_limiter(0)], prefix="Pin:"),
}


class Implementation(BaseDispenser):
    """Custom dispenser implementation."""

    def __init__(self, slot: int, config: ConfigClass, scale: ScaleInterface | None = None) -> None:
        super().__init__(slot, config, scale)
        # Access your custom config fields:
        # self.pin = config.pin

    def setup(self) -> None:
        """Initialize hardware resources for this dispenser."""

    def dispense(self, amount_ml: float, pump_speed: int, callback: ProgressCallback) -> float:
        """Dispense the given amount at the given pump speed.

        Must be blocking. Return the actual consumption in ml.
        Check self._stop_event to support cancellation.
        """
        raise NotImplementedError("Implement dispense logic")

    def stop(self) -> None:
        """Emergency stop / cancel current dispensing."""
        self._stop_event.set()

    def cleanup(self) -> None:
        """Release hardware resources."""
