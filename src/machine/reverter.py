from __future__ import annotations

from src.config.config_types import ReversionConfig
from src.logger_handler import LoggerHandler
from src.machine.pin_controller import PinController

_logger = LoggerHandler("Reverter")


class Reverter:
    def __init__(self, config: ReversionConfig) -> None:
        self._pin_controller = PinController()
        # only init if reversion is enabled, otherwise it may be an invalid pin
        self.use_reversion = config.use_reversion
        self.revert_pin = config.pin_id
        self.inverted = config.inverted

    def initialize_pin(self) -> None:
        if self.use_reversion:
            _logger.info(f"<i> Initializing Reversion Pin: {self.revert_pin}")
            self._pin_controller.initialize_pin(self.revert_pin, invert_override=self.inverted)

    def revert_on(self) -> None:
        """Reverts the pump to be inverted."""
        if not self.use_reversion:
            return
        self._pin_controller.activate_pin(self.revert_pin)

    def revert_off(self) -> None:
        """Disables the reversion pin."""
        if not self.use_reversion:
            return
        self._pin_controller.close_pin(self.revert_pin)
