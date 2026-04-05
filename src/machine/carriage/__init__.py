from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.carriage.base import CarriageInterface

if TYPE_CHECKING:
    from src.config.config_types import BaseCarriageConfig

_logger = LoggerHandler("carriage")

__all__ = ["CarriageInterface", "create_carriage"]


def create_carriage(config: BaseCarriageConfig) -> CarriageInterface | None:
    """Create a carriage instance from config, returning None if disabled.

    No concrete implementations exist yet — this always returns None.
    """
    if not config.enabled:
        return None
    _logger.log_event("WARNING", "Carriage is enabled but no driver implementation is available yet")
    return None
