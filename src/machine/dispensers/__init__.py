from __future__ import annotations

from src.config.config_types import PumpConfig
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.dc import DCDispenser
from src.machine.hardware import HardwareContext


def create_dispenser(slot: int, pump_config: PumpConfig, hardware: HardwareContext) -> BaseDispenser:
    """Create a dispenser instance based on the pump configuration."""
    match pump_config.pump_type:
        case "DC":
            return DCDispenser(slot, pump_config.volume_flow, pump_config.pin_id, hardware.pin_controller)
        case _:
            msg = f"Unknown pump type: {pump_config.pump_type}"
            raise ValueError(msg)
