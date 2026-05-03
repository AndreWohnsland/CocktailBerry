from __future__ import annotations

import concurrent.futures
import contextlib
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

_SCALE_HEALTH_CHECK_TIMEOUT = 1.0


def _health_check(scale: ScaleInterface) -> ScaleInterface | None:
    """Verify the scale responds within the timeout by calling read_raw(1).

    Returns the scale on success, or None (after cleanup) if the call blocks
    or raises — indicating the hardware is not connected or not working.
    This is necessary because some scale drivers (especially HX711) will block indefinitely
    if the hardware is not present, which would break the entire program on use.
    """
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(scale.read_raw, 1)
    try:
        future.result(timeout=_SCALE_HEALTH_CHECK_TIMEOUT)
        executor.shutdown(wait=False)
        return scale
    except concurrent.futures.TimeoutError:
        _logger.log_event(
            "ERROR",
            f"Scale health check timed out after {_SCALE_HEALTH_CHECK_TIMEOUT}s — "
            "no hardware connected? Deactivating scale.",
        )
    except Exception as exc:
        _logger.log_event("ERROR", f"Scale health check failed: {exc} — Deactivating scale.")
    executor.shutdown(wait=False)
    with contextlib.suppress(Exception):
        scale.cleanup()
    return None


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
            scale = HX711Scale(config, hardware)
        elif isinstance(config, NAU7802ScaleConfig):
            scale = NAU7802Scale(config, hardware)
        else:
            # Custom scale extensions from addons/scales/ — dispatch by scale_type.
            from src.programs.addons.scale_extensions import SCALE_ADDONS

            entry = SCALE_ADDONS.entries.get(config.scale_type)
            if entry is not None:
                scale = entry.implementation_class(config, hardware)
            else:
                _logger.log_event("ERROR", f"Unknown scale config type: {type(config)}")
                return None
        return _health_check(scale)
    except Exception:
        _logger.log_event("WARNING", "Scale initialization failed, falling back to time-based dispensing")
        _logger.log_exception("Scale initialization traceback")
        return None
