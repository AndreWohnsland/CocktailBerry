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
                pump_config.volume_flow,
                pump_config.pin_id,
                hardware.pin_controller,
                scale,
                pump_config.carriage_position,
            )
        case StepperPumpConfig():
            return StepperDispenser(
                slot=slot,
                volume_flow=pump_config.volume_flow,
                step_pin=pump_config.pin,
                dir_pin=pump_config.dir_pin,
                driver_type=pump_config.driver_type,
                step_type=pump_config.step_type,
                scale=scale,
                carriage_position=pump_config.carriage_position,
            )
        case _:
            msg = f"Unknown pump config type: {type(pump_config)}"
            raise ValueError(msg)
