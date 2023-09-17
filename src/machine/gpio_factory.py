"""Module to create the according GPIO controller for the appropriate Board"""
from src.machine.interface import GPIOController
from src.config_manager import CONFIG as cfg


class GPIOFactory:
    def __init__(self, inverted: bool) -> None:
        self.inverted = inverted
        # flag if the import warning was already triggered,
        # used to prevent the warning multiple times
        self.import_warning = False

    def generate_gpio(self, inverted: bool) -> GPIOController:
        """Return the appropriate GPIO"""
        board = cfg.MAKER_BOARD
        if board == "RPI":
            return RaspberryGPIO(1, 0, inverted)
        else:
            return GenericGPIO(1, 0, inverted)


class GenericGPIO(GPIOController):
    def initialize(self):
        raise NotImplementedError

    def activate(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError


class RaspberryGPIO(GPIOController):
    def initialize(self):
        raise NotImplementedError

    def activate(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError
