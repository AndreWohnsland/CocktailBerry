from __future__ import annotations

import contextlib
import multiprocessing
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

_SCALE_HEALTH_CHECK_TIMEOUT = 2.0


def _forked_read(scale: ScaleInterface, queue: multiprocessing.Queue) -> None:  # type: ignore[type-arg]
    """Target for the health-check subprocess: put True on success, False on error."""
    try:
        scale.read_raw(1)
        queue.put(True)
    except Exception:
        queue.put(False)


def _health_check(scale: ScaleInterface) -> ScaleInterface | None:
    """Verify the scale responds within the timeout by calling read_raw(1).

    Returns the scale on success, or None (after cleanup) if the call blocks
    or raises — indicating the hardware is not connected or not working.
    The check runs in a forked subprocess so it can be forcefully killed if
    the driver blocks indefinitely (e.g. HX711 with no hardware present).
    """
    ctx = multiprocessing.get_context("fork")
    queue: multiprocessing.Queue = ctx.Queue()  # type: ignore[type-arg]
    proc = ctx.Process(target=_forked_read, args=(scale, queue), daemon=True)  # ty:ignore[unresolved-attribute]
    proc.start()
    proc.join(timeout=_SCALE_HEALTH_CHECK_TIMEOUT)
    if proc.is_alive():
        proc.kill()
        proc.join()
        _logger.log_event(
            "ERROR",
            f"Scale health check timed out after {_SCALE_HEALTH_CHECK_TIMEOUT}s — "
            "no hardware connected? Deactivating scale.",
        )
        with contextlib.suppress(Exception):
            scale.cleanup()
        return None
    success = not queue.empty() and queue.get_nowait()
    if not success:
        _logger.log_event("ERROR", "Scale health check failed — Deactivating scale.")
        with contextlib.suppress(Exception):
            scale.cleanup()
        return None
    return scale


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
