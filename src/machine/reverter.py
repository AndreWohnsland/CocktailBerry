from __future__ import annotations

from src.config.config_types import BaseReversionConfig, GlobalReversionConfig
from src.logger_handler import LoggerHandler
from src.machine.pin_controller import PinController

_logger = LoggerHandler("Reverter")


class Reverter:
    def __init__(self, pin_controller: PinController, config: GlobalReversionConfig) -> None:
        self._pin_controller = pin_controller
        self.revert_pin = config.pin_id
        self.inverted = config.inverted

    def initialize_pin(self) -> None:
        _logger.info(f"<i> Initializing Reversion Pin: {self.revert_pin}")
        self._pin_controller.initialize_pin(self.revert_pin, invert_override=self.inverted)

    def revert_on(self) -> None:
        """Reverts the pump to be inverted."""
        self._pin_controller.activate_pin(self.revert_pin)

    def revert_off(self) -> None:
        """Disables the reversion pin."""
        self._pin_controller.close_pin(self.revert_pin)

    def cleanup(self) -> None:
        """Clean up the reversion pin."""
        self._pin_controller.cleanup_pin(self.revert_pin)


def create_reverter(config: BaseReversionConfig, pin_controller: PinController) -> Reverter | None:
    """Create a Reverter from config, returning None when not active or not global.

    Returns a Reverter only when the config is a GlobalReversionConfig with active=True.
    DispenserControlledReversionConfig returns None because each dispenser
    manages its own direction; nothing needs a shared reverter instance.
    """
    if not config.enabled or not isinstance(config, GlobalReversionConfig):
        return None
    return Reverter(pin_controller, config)
