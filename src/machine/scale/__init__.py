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

    Every scale — built-in or from ``addons/scales/`` — receives the full
    ``HardwareContext`` so it can reach pins, LEDs, or hardware extension
    instances if needed.
    """
    from src.config.config_types import HX711ScaleConfig, NAU7802ScaleConfig

    if not config.enabled:
        return None
    try:
        if isinstance(config, HX711ScaleConfig):
            return HX711Scale(config, hardware)
        if isinstance(config, NAU7802ScaleConfig):
            return NAU7802Scale(config, hardware)
        # Custom scale extensions from addons/scales/ — dispatch by scale_type.
        from src.programs.addons.scale_extensions import SCALE_ADDONS

        entry = SCALE_ADDONS.entries.get(config.scale_type)
        if entry is not None:
            return entry.implementation_class(config, hardware)
        _logger.log_event("ERROR", f"Unknown scale config type: {type(config)}")
        return None
    except Exception:
        _logger.log_event("WARNING", "Scale initialization failed, falling back to time-based dispensing")
        return None
