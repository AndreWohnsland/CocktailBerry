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
    """Create a carriage instance from config, returning None if disabled.

    The *hardware* context is available for future carriage extensions
    that need access to pin controllers, scale, or hardware extension instances.
    No concrete implementations exist yet — this always returns None.
    """
    if not config.enabled:
        return None
    _logger.log_event("WARNING", "Carriage is enabled but no driver implementation is available yet")
    return None
