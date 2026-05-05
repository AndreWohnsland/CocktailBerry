from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.carriage.base import CarriageInterface

if TYPE_CHECKING:
    from src.config.config_types import BaseCarriageConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("carriage")

__all__ = ["CarriageInterface", "create_carriage"]


def create_carriage(config: BaseCarriageConfig, hardware: HardwareContext) -> CarriageInterface | None:
    """Create a carriage instance from config, returning None if unavailable.

    Every carriage — currently only from ``addons/carriages/`` — receives the
    full ``HardwareContext`` so it can reach pins, LEDs, the scale, or hardware
    extension instances if needed. Built-in sentinels like ``"NoCarriage"``
    resolve to ``None``, equivalent to a disabled carriage.
    """
    if not config.enabled or config.carriage_type == "NoCarriage":
        return None
    try:
        # Custom carriage extensions from addons/carriages/ — dispatch by carriage_type.
        from src.programs.addons.carriage_extensions import CARRIAGE_ADDONS

        entry = CARRIAGE_ADDONS.entries.get(config.carriage_type)
        if entry is not None:
            return entry.implementation_class(config, hardware)
        _logger.error(f"Unknown carriage type: {config.carriage_type}")
        return None
    except Exception:
        _logger.warning("Carriage initialization failed, continuing without carriage")
        _logger.log_exception("Carriage initialization traceback")
        return None
