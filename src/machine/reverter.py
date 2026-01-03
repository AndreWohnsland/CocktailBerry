from src.logger_handler import LoggerHandler
from src.machine.interface import PinController

_logger = LoggerHandler("Reverter")


class Reverter:
    def __init__(self, pin_controller: PinController, use_reversion: bool, revert_pin: int) -> None:
        self._pin_controller = pin_controller
        # only init if reversion is enabled, otherwise it may be an invalid pin
        self.use_reversion = use_reversion
        self.revert_pin = revert_pin

    def initialize_pin(self) -> None:
        if self.use_reversion:
            _logger.info(f"<i> Initializing Reversion Pin: {self.revert_pin}")
            self._pin_controller.initialize_pin_list([self.revert_pin])

    def revert_on(self) -> None:
        """Reverts the pump to be inverted."""
        if not self.use_reversion:
            return
        self._pin_controller.activate_pin_list([self.revert_pin])

    def revert_off(self) -> None:
        """Disables the reversion pin."""
        if not self.use_reversion:
            return
        self._pin_controller.close_pin_list([self.revert_pin])
