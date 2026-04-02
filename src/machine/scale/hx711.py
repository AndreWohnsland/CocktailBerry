from __future__ import annotations

from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface

_logger = LoggerHandler("HX711Scale")

try:
    from hx711 import HX711  # type: ignore[import-untyped]

    HX711_AVAILABLE = True
except (ModuleNotFoundError, ImportError, RuntimeError):
    HX711_AVAILABLE = False


class HX711Scale(ScaleInterface):
    """Scale using HX711 load cell amplifier (2-wire bit-bang protocol)."""

    def __init__(self, data_pin: int, clock_pin: int, calibration_factor: float) -> None:
        if not HX711_AVAILABLE:
            msg = "hx711 library is not available. Cannot initialize HX711 scale."
            raise ImportError(msg)
        self._calibration_factor = calibration_factor
        self._hx = HX711(dout_pin=data_pin, pd_sck_pin=clock_pin)
        self._hx.set_scale_ratio(calibration_factor)
        _logger.log_event("INFO", f"HX711 scale initialized (data={data_pin}, clock={clock_pin})")

    def tare(self) -> None:
        self._hx.tare()

    def read_grams(self) -> float:
        return self._hx.get_weight_mean(readings=5) / self._calibration_factor

    def read_raw(self) -> float:
        return self._hx.get_weight_mean(readings=5)

    def cleanup(self) -> None:
        self._hx.power_down()
