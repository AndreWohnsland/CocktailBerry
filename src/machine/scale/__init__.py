from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface
from src.machine.scale.hx711 import HX711Scale
from src.machine.scale.nau7802 import NAU7802Scale

if TYPE_CHECKING:
    from src.config.config_types import BaseScaleConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("scale")

__all__ = ["HX711Scale", "NAU7802Scale", "ScaleInterface", "create_scale"]


def create_scale(config: BaseScaleConfig, hardware: HardwareContext) -> ScaleInterface | None:
    """Create a scale instance from config, returning None on failure.

    The *hardware* context is available for future scale extensions
    that need access to pin controllers or hardware extension instances.
    Built-in drivers currently ignore it.
    """
    from src.config.config_types import HX711ScaleConfig, NAU7802ScaleConfig

    if not config.enabled:
        return None
    try:
        if isinstance(config, HX711ScaleConfig):
            return HX711Scale(config)
        if isinstance(config, NAU7802ScaleConfig):
            return NAU7802Scale(config)
        _logger.log_event("ERROR", f"Unknown scale config type: {type(config)}")
        return None
    except Exception:
        _logger.log_event("WARNING", "Scale initialization failed, falling back to time-based dispensing")
        return None
