from src.config.config_manager import CONFIG as cfg
from src.machine.interface import PinController
from src.utils import time_print


class Reverter:
    def __init__(self, pin_controller: PinController):
        self._pin_controller = pin_controller
        # only init if reversion is enabled, otherwise it may be an invalid pin
        self.revert_pin = cfg.MAKER_REVERSION_PIN

    def initialize_pin(self):
        if cfg.MAKER_PUMP_REVERSION:
            time_print(f"Initializing Reversion Pin: {self.revert_pin}")
            self._pin_controller.initialize_pin_list([self.revert_pin])

    def revert_on(self):
        """Reverts the pump to be inverted."""
        if not cfg.MAKER_PUMP_REVERSION:
            return
        self._pin_controller.activate_pin_list([self.revert_pin])

    def revert_off(self):
        """Disables the reversion pin."""
        if not cfg.MAKER_PUMP_REVERSION:
            return
        self._pin_controller.close_pin_list([self.revert_pin])
