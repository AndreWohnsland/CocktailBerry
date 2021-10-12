import time
from PyQt5.QtWidgets import qApp

from config.config_manager import shared
from config.config_manager import ConfigManager


class RpiController(ConfigManager):
    """Controler Class for all RPi related GPIO routines """

    def __init__(self):
        try:
            import RPi.GPIO as GPIO

            GPIO.setmode(GPIO.BCM)
            self.devenvironment = False
        except ModuleNotFoundError:
            self.devenvironment = True

    def clean_pumps(self):
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

    def make_cocktail(self, w, bottle_list: list[int], volume_list: list[float], labelchange=""):
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

    def activate_pinlist(self, pinlist: list[int]):
        print(f"Opening Pins: {pinlist}")
        if not self.devenvironment:
            for pin in pinlist:
                GPIO.setup(pin, 0)
                GPIO.output(pin, 0)

    def close_pinlist(self, pinlist: list[int]):
        print(f"Closing Pins: {pinlist}")
        if not self.devenvironment:
            for pin in pinlist:
                GPIO.output(pin, 1)

    def consumption_print(self, consumption: list[float], current_time: float, max_time: float, interval=1):
        if current_time % interval == 0:
            print(
                f"Making Cocktail, {current_time}/{max_time} s:\tThe consumption is currently {[round(x) for x in consumption]}")

    def clean_print(self, t_cleaned: float, interval=2):
        if t_cleaned % interval == 0:
            print(f"Cleaning, {t_cleaned}/{self.CLEAN_TIME} s\t{'.' * int(t_cleaned)}")
