from __future__ import annotations

from src.config.config_types import BasePumpConfig, DCPumpConfig, StepperPumpConfig
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.dc import DCDispenser
from src.machine.dispensers.stepper import StepperDispenser
from src.machine.hardware import HardwareContext
from src.machine.scale import ScaleInterface


def create_dispenser(slot: int, pump_config: BasePumpConfig, hardware: HardwareContext) -> BaseDispenser:
    """Create a dispenser instance based on the pump configuration."""
    scale: ScaleInterface | None = hardware.scale if pump_config.consumption_estimation == "weight" else None
    match pump_config:
        case DCPumpConfig():
            return DCDispenser(
                slot,
                pump_config,
                hardware.pin_controller,
                scale,
            )
        case StepperPumpConfig():
            return StepperDispenser(
                slot=slot,
                config=pump_config,
                scale=scale,
            )
        case _:
            msg = f"Unknown pump config type: {type(pump_config)}"
            raise ValueError(msg)
