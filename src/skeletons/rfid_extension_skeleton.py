from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.config_types import BaseRfidConfig, ConfigInterface, FloatType
from src.config.validators import build_number_limiter
from src.logger_handler import LoggerHandler
from src.machine.rfid.base import RFIDInterface

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# This is an RFID extension skeleton.
# For more information see: https://docs.cocktailberry.org/hardware-extensions/#rfid
# Your custom extension needs four exports:
#   EXTENSION_NAME - unique name shown in the rfid type dropdown
#   CONFIG_FIELDS  - dict of extra config fields (beyond the shared BaseRfidConfig fields)
#   ExtensionConfig - config class inheriting from BaseRfidConfig
#   Implementation - rfid class inheriting from RFIDInterface
#
# Shared fields (rfid_type, enabled) are auto-injected — only define your EXTRA
# fields in CONFIG_FIELDS.


EXTENSION_NAME = "EXTENSION_NAME_HOLDER"
_logger = LoggerHandler("EXTENSION_NAME_HOLDER")


class ExtensionConfig(BaseRfidConfig):
    """Custom configuration for this RFID reader type.

    Add any extra attributes your reader needs beyond the shared ones.
    """

    read_delay_s: float

    def __init__(
        self,
        read_delay_s: float = 0.5,
        rfid_type: str = EXTENSION_NAME,
        enabled: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            rfid_type=rfid_type,
            enabled=enabled,
        )
        self.read_delay_s = read_delay_s

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update({"read_delay_s": self.read_delay_s})
        return config


# Only define the EXTRA fields here. Shared fields (enabled) and the rfid_type
# dropdown are auto-injected by the extension manager.
CONFIG_FIELDS: dict[str, ConfigInterface] = {
    "read_delay_s": FloatType([build_number_limiter(0.0, 60.0)], suffix="s"),
}


class Implementation(RFIDInterface):
    """Custom RFID reader implementation.

    Implement the abstract methods of RFIDInterface to drive your hardware.

    Inherited attributes from RFIDInterface:
      self.config    — your ExtensionConfig instance
      self.hardware  — HardwareContext with pin_controller, led_controller,
                       scale, carriage, and extra (dict of hardware extension
                       instances)

    Abstract methods you MUST implement:
      read_card()    — return (text, id) tuple for a present card or (None, None)
      write_card(t)  — write text to the next card; return success bool

    Optional override:
      cleanup()      — release any held GPIO/SPI/USB handles (no-op by default)
    """

    def __init__(
        self,
        config: ExtensionConfig,
        hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self._read_delay_s = config.read_delay_s
        # >>> Initialize your hardware here (e.g. open SPI, USB, serial) <<<
        _logger.info(f"RFID reader '{EXTENSION_NAME}' initialized (read_delay_s={self._read_delay_s})")

    def read_card(self) -> tuple[str | None, str | None]:
        """Return ``(text, id)`` for a card if one is currently in range."""
        # >>> Replace this with your real hardware read <<<
        return None, None

    def write_card(self, text: str) -> bool:
        """Write ``text`` to the next card seen and return whether it succeeded."""
        # >>> Replace this with your real hardware write <<<
        _logger.warning(f"RFID '{EXTENSION_NAME}' write not implemented")
        return False

    def cleanup(self) -> None:
        """Release hardware resources."""
        # >>> Close your hardware here (e.g. release SPI/USB) <<<
        _logger.info(f"RFID reader '{EXTENSION_NAME}' cleaned up")
