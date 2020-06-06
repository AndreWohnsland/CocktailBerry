from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import time

from config.config_manager import ConfigManager

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    devenvironment = False
except:
    devenvironment = True


class RpiController(ConfigManager):
    """Controler Class for all RPi related GPIO routines """

    def __init__(self):
        self.NUMBER_BOTTLES = 10
        self.CLEAN_TIME = 20
        self.SLEEP_TIME = 0.1

    def clean_pumps(self):
        active_pins = self.usedpins[: self.NUMBER_BOTTLES]
        print(f"Opening Pins: {active_pins}")
        for pin in active_pins:
            if not devenvironment:
                GPIO.setup(pin, 0)
                GPIO.output(pin, 0)
        t_cleaned = 0
        while t_cleaned < self.CLEAN_TIME:
            if t_cleaned % 5 == 0:
                print(f"cleaning: {t_cleaned} of {self.CLEAN_TIME} s {'.' * int(t_cleaned)}")
            t_cleaned += self.SLEEP_TIME
            t_cleaned = round(t_cleaned, 1)
            time.sleep(self.SLEEP_TIME)
            qApp.processEvents()
        print(f"Closing Pins: {active_pins}")
        for pin in active_pins:
            if not devenvironment:
                GPIO.output(pin, 1)
