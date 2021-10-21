import time
from typing import List
from PyQt5.QtWidgets import qApp

from config.config_manager import shared
from config.config_manager import ConfigManager


try:
    from RPi import GPIO
    GPIO.setmode(GPIO.BCM)
    DEV = False
except ModuleNotFoundError:
    DEV = True


class RpiController(ConfigManager):
    """Controler Class for all RPi related GPIO routines """

    def __init__(self):
        self.devenvironment = DEV
        print(f"Devenvironment is {self.devenvironment}")

    def clean_pumps(self):
        """Clean the pumps for the defined time in the config.
        Acitvates all pumps for the given time
        """
        active_pins = self.USEDPINS[: self.NUMBER_BOTTLES]
        self.activate_pinlist(active_pins)
        t_cleaned = 0
        while t_cleaned < self.CLEAN_TIME:
            self.clean_print(t_cleaned)
            t_cleaned += self.SLEEP_TIME
            t_cleaned = round(t_cleaned, 2)
            time.sleep(self.SLEEP_TIME)
            qApp.processEvents()
        self.close_pinlist(active_pins)

    def make_cocktail(self, w, bottle_list: List[int], volume_list: List[float], labelchange=""):
        """RPI Logic to prepare the cocktail.
        Calculates needed time for each slot according to data and config.
        Updates Progressbar status. Returns data for DB updates.

        Args:
            w (QtMainWindow): MainWindow Object
            bottle_list (List[int]): Number of bottles to be used
            volume_list (List[float]): Corresponding Volumens needed of bottles
            labelchange (str, optional): Option to change the display text of Progress Screen. Defaults to "".

        Returns:
            tuple(List[int], float, float): Consumption of each bottle, taken time, max needed time
        """
        # Only shwo team dialog if it is enabled
        if self.USE_TEAMS:
            w.teamwindow()
        shared.cocktail_started = True
        shared.make_cocktail = True
        w.progressionqwindow(labelchange)
        already_closed_pins = set()
        indexes = [x - 1 for x in bottle_list]
        pins = [self.USEDPINS[i] for i in indexes]
        volume_flows = [self.PUMP_VOLUMEFLOW[i] for i in indexes]
        pin_times = [round(volume / flow, 1) for volume, flow in zip(volume_list, volume_flows)]
        max_time = max(pin_times)
        current_time = 0
        consumption = [0] * len(indexes)
        self.activate_pinlist(pins)

        print("---- Starting Cocktail ----")
        while current_time < max_time and shared.make_cocktail:
            for element, (pin, pin_time, volume_flow) in enumerate(zip(pins, pin_times, volume_flows)):
                if pin_time > current_time:
                    consumption[element] += volume_flow * self.SLEEP_TIME
                elif pin not in already_closed_pins:
                    self.close_pin(pin, current_time)
                    already_closed_pins.add(pin)

            self.consumption_print(consumption, current_time, max_time)
            current_time += self.SLEEP_TIME
            current_time = round(current_time, 2)
            time.sleep(self.SLEEP_TIME)
            w.prow_change(current_time / max_time * 100)
            qApp.processEvents()

        print("---- Done ----")
        self.close_pinlist(pins)
        w.prow_close()
        return [round(x) for x in consumption], current_time, max_time

    def close_pin(self, pin: int, current_time: float):
        if not self.devenvironment:
            GPIO.output(pin, 1)
        print(f"{current_time}s: Pin number <{pin}> is closed")

    def activate_pinlist(self, pinlist: List[int]):
        print(f"Opening Pins: {pinlist}")
        if not self.devenvironment:
            for pin in pinlist:
                GPIO.setup(pin, 0)
                GPIO.output(pin, 0)

    def close_pinlist(self, pinlist: List[int]):
        print(f"Closing Pins: {pinlist}")
        if not self.devenvironment:
            for pin in pinlist:
                GPIO.output(pin, 1)

    def consumption_print(self, consumption: List[float], current_time: float, max_time: float, interval=1):
        if current_time % interval == 0:
            print(
                f"Making Cocktail, {current_time}/{max_time} s:\tThe consumption is currently {[round(x) for x in consumption]}")

    def clean_print(self, t_cleaned: float, interval=2):
        if t_cleaned % interval == 0:
            print(f"Cleaning, {t_cleaned}/{self.CLEAN_TIME} s\t{'.' * int(t_cleaned)}")
