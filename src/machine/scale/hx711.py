from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface

if TYPE_CHECKING:
    from src.config.config_types import HX711ScaleConfig

_logger = LoggerHandler("HX711Scale")

try:
    from hx711 import HX711  # type: ignore[import-untyped]

    HX711_AVAILABLE = True
except (ModuleNotFoundError, ImportError, RuntimeError):
    HX711_AVAILABLE = False


class HX711Scale(ScaleInterface):
    """Scale using HX711 load cell amplifier (2-wire bit-bang protocol)."""

    def __init__(self, config: HX711ScaleConfig) -> None:
        if not HX711_AVAILABLE:
            msg = "hx711 library is not available. Cannot initialize HX711 scale."
            raise ImportError(msg)
        self._calibration_factor = config.calibration_factor
        self._hx = HX711(dout_pin=config.data_pin, pd_sck_pin=config.clock_pin)
        self._hx.set_scale_ratio(config.calibration_factor)
        _logger.log_event("INFO", f"HX711 scale initialized (data={config.data_pin}, clock={config.clock_pin})")

    def tare(self) -> None:
        self._hx.tare()

    def read_grams(self) -> float:
        return self._hx.get_weight_mean(readings=5) / self._calibration_factor

    def read_raw(self) -> float:
        return self._hx.get_weight_mean(readings=5)

    def cleanup(self) -> None:
        self._hx.power_down()
