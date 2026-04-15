from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.config_types import BaseScaleConfig, ConfigInterface, IntType
from src.config.validators import build_number_limiter
from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# This is a scale extension skeleton.
# For more information see: https://docs.cocktailberry.org/hardware-extensions/#scales
# Your custom extension needs four exports:
#   EXTENSION_NAME - unique name shown in the scale type dropdown
#   CONFIG_FIELDS  - dict of extra config fields (beyond the shared BaseScaleConfig fields)
#   ExtensionConfig - config class inheriting from BaseScaleConfig
#   Implementation - scale class inheriting from ScaleInterface
#
# Shared fields (scale_type, enabled, calibration_factor, zero_raw_offset)
# are auto-injected — only define your EXTRA fields in CONFIG_FIELDS.


EXTENSION_NAME = "EXTENSION_NAME_HOLDER"
_logger = LoggerHandler("EXTENSION_NAME_HOLDER")


class ExtensionConfig(BaseScaleConfig):
    """Custom configuration for this scale type.

    Add any extra attributes your scale needs beyond the shared ones.
    """

    sample_pin: int

    def __init__(
        self,
        sample_pin: int = 0,
        scale_type: str = EXTENSION_NAME,
        enabled: bool = False,
        calibration_factor: float = 1.0,
        zero_raw_offset: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            scale_type=scale_type,
            enabled=enabled,
            calibration_factor=calibration_factor,
            zero_raw_offset=zero_raw_offset,
        )
        self.sample_pin = sample_pin

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update({"sample_pin": self.sample_pin})
        return config


# Only define the EXTRA fields here. Shared fields (enabled, calibration_factor,
# zero_raw_offset) and the scale_type dropdown are auto-injected by the extension manager.
CONFIG_FIELDS: dict[str, ConfigInterface] = {
    "sample_pin": IntType([build_number_limiter(0)], prefix="Pin:"),
}


class Implementation(ScaleInterface):
    """Custom scale implementation.

    Implement the abstract methods of ScaleInterface to drive your hardware.

    Inherited attributes from ScaleInterface:
      self.config               — your ExtensionConfig instance
      self.hardware            — HardwareContext with pin_controller, led_controller,
                                 and extra (dict of hardware extension instances)
      self._calibration_factor — raw-units-per-gram, from config
      self._zero_raw_offset    — raw ADC reading of empty scale, from config

    Abstract methods you MUST implement:
      tare(samples)            — capture current raw reading as tare offset
      read_grams()             — return weight in grams relative to last tare()
      read_raw(samples)        — return raw ADC reading (no offset, no calibration)
      cleanup()                — release any hardware resources
      get_gross_grams()        — return absolute weight relative to _zero_raw_offset

    Base class helpers you may use or override:
      calibrate_with_known_weight(weight_g, zero_raw_offset, samples)
      set_calibration_factor(factor)
      set_zero_raw_offset(offset)
    """

    def __init__(
        self,
        config: ExtensionConfig,
        hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self._sample_pin = config.sample_pin
        self._offset = 0
        # >>> Initialize your hardware here (e.g. open GPIO, SPI, I2C) <<<
        _logger.info(f"Scale '{EXTENSION_NAME}' initialized (sample_pin={self._sample_pin})")

    def _sample_raw(self, samples: int) -> int:
        """Read the ADC ``samples`` times and return the average raw value."""
        # >>> Replace this with your real hardware read <<<
        readings = [0 for _ in range(max(1, samples))]
        return int(sum(readings) / len(readings))

    def tare(self, samples: int = 3) -> int:
        """Set the dynamic tare offset to the current raw reading."""
        self._offset = self._sample_raw(samples)
        _logger.debug(f"Scale tare set, new offset: {self._offset}")
        return self._offset

    def read_grams(self) -> float:
        """Return weight in grams, relative to the last tare() call."""
        return (self._sample_raw(1) - self._offset) / self._calibration_factor

    def read_raw(self, samples: int = 1) -> int:
        """Return the averaged raw ADC reading (without tare/calibration)."""
        return self._sample_raw(samples)

    def get_gross_grams(self) -> float:
        """Return weight in grams, relative to the one-time _zero_raw_offset."""
        return (self._sample_raw(1) - self._zero_raw_offset) / self._calibration_factor

    def cleanup(self) -> None:
        """Release hardware resources."""
        # >>> Close your hardware here (e.g. release GPIO, close bus) <<<
        _logger.info(f"Scale '{EXTENSION_NAME}' cleaned up")
