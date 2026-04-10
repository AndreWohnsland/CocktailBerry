from __future__ import annotations

from src.config.config_types import BasePumpConfig, DCPumpConfig, StepperPumpConfig
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.dc import DCDispenser
from src.machine.dispensers.stepper import StepperDispenser
from src.machine.hardware import HardwareContext

_logger = LoggerHandler("dispenser_factory")


def create_dispenser(slot: int, pump_config: BasePumpConfig, hardware: HardwareContext) -> BaseDispenser:
    """Create a dispenser instance based on the pump configuration."""
    # need to log if the scale is none (usually because it couldn't be initialized)
    # but the pump is configured for weight-based estimation
    if pump_config.consumption_estimation == "weight" and hardware.scale is None:
        _logger.log_event(
            "WARNING",
            f"Pump {slot} configured for weight-based estimation but no scale is available, "
            "falling back to time-based estimation",
        )
    match pump_config:
        case DCPumpConfig():
            return DCDispenser(
                slot,
                pump_config,
                hardware,
            )
        case StepperPumpConfig():
            return StepperDispenser(
                slot=slot,
                config=pump_config,
                hardware=hardware,
            )
        case _:
            from src.programs.addons.dispenser_extensions import DISPENSER_ADDONS

            entry = DISPENSER_ADDONS.entries.get(pump_config.pump_type)
            if entry is not None:
                return entry.implementation_class(slot, pump_config, hardware)
            msg = f"Unknown pump config type: {type(pump_config)}"
            raise ValueError(msg)
