from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface
from src.machine.scale.hx711 import HX711Scale
from src.machine.scale.nau7802 import NAU7802Scale

if TYPE_CHECKING:
    from src.config.config_types import BaseScaleConfig

_logger = LoggerHandler("scale")

__all__ = ["HX711Scale", "NAU7802Scale", "ScaleInterface", "create_scale"]


def create_scale(config: BaseScaleConfig) -> ScaleInterface | None:
    """Create a scale instance from config, returning None on failure."""
    from src.config.config_types import HX711ScaleConfig, NAU7802ScaleConfig

    if not config.enabled:
        return None
    try:
        if isinstance(config, HX711ScaleConfig):
            return HX711Scale(config.data_pin, config.clock_pin, config.calibration_factor)
        if isinstance(config, NAU7802ScaleConfig):
            return NAU7802Scale(config.i2c_address, config.calibration_factor)
        _logger.log_event("ERROR", f"Unknown scale config type: {type(config)}")
        return None
    except Exception:
        _logger.log_event("WARNING", "Scale initialization failed, falling back to time-based dispensing")
        return None
