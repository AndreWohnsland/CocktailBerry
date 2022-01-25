import sys
import time
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

from src.config_manager import ConfigManager
from src.display_controller import DP_CONTROLLER

try:
    # pylint: disable=import-error
    from RPi import GPIO
    GPIO.setmode(GPIO.BCM)
    DEV = False
except ModuleNotFoundError:
    DEV = True


ui_file = Path(__file__).parent.absolute() / "ui_elements" / "Calibration.ui"


class CalibrationScreen(QMainWindow, ConfigManager):
    def __init__(self):
        """ Init the calibration Screen. """
        super().__init__()
        ConfigManager.__init__(self)
        loadUi(ui_file, self)
        # Connect the Button
        bottles = self.MAKER_NUMBER_BOTTLES
        self.PB_start.clicked.connect(self.output_volume)
        self.channel_plus.clicked.connect(lambda: DP_CONTROLLER.plusminus(self.channel, "+", 1, bottles, 1))
        self.channel_minus.clicked.connect(lambda: DP_CONTROLLER.plusminus(self.channel, "-", 1, bottles, 1))
        self.amount_plus.clicked.connect(lambda: DP_CONTROLLER.plusminus(self.amount, "+", 10, 200, 10))
        self.amount_minus.clicked.connect(lambda: DP_CONTROLLER.plusminus(self.amount, "-", 10, 200, 10))
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def output_volume(self):
        """Outputs the set number of volume according to defined volume flow"""
        channel_number = int(self.channel.text())
        amount = int(self.amount.text())
        ind = channel_number - 1
        used_pin = self.PUMP_PINS[ind]
        print(f"Using pin number: {used_pin}")
        t_pump = amount / self.PUMP_VOLUMEFLOW[ind]
        print(f"Needed time is: {t_pump:.2f}s")
        t_current = 0
        while t_current < t_pump:
            if not DEV:
                GPIO.output(used_pin, 0)
            t_current += self.MAKER_SLEEP_TIME
            t_current = round(t_current, 2)
            time.sleep(self.MAKER_SLEEP_TIME)
            if (t_current * 100) % 10 == 0:
                print(f"{t_current}s done ...", end="\r")
        print("Finished!       ")
        if not DEV:
            GPIO.output(used_pin, 1)


def run_calibration():
    app = QApplication(sys.argv)
    # this asignment is needed, otherwise the window will close in an instant
    # pylint: disable=unused-variable
    cali = CalibrationScreen()
    sys.exit(app.exec_())
