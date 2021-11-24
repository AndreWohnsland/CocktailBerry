import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.uic import loadUi

try:
    # pylint: disable=import-error
    from RPi import GPIO
    GPIO.setmode(GPIO.BCM)
    DEV = False
except ModuleNotFoundError:
    DEV = True


ui_path = os.path.dirname(os.path.abspath(__file__))
pinvector = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 20]
volumeflow = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
SLEEP_INTERVALL = 0.05


def activate_pins():
    for pin in pinvector:
        if not DEV:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)


def starbutton_click():
    channel_number = w.sB_Kanal.value()
    amount = w.sB_Menge.value()
    ind = channel_number - 1
    print(f"Using pin number: {pinvector[ind]}")
    t_pump = amount / volumeflow[ind]
    print(f"Needed time is: {t_pump:.2f}s")
    t_current = 0
    while t_current < t_pump:
        if not DEV:
            GPIO.output(pinvector[ind], 0)
        t_current += SLEEP_INTERVALL
        t_current = round(t_current, 2)
        time.sleep(SLEEP_INTERVALL)
        if (t_current * 100) % 10 == 0:
            print(f"{t_current}s done ...", end="\r")
    print("Finished!")
    if not DEV:
        GPIO.output(pinvector[ind], 1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = loadUi(os.path.join(ui_path, "Calibration.ui"))
    # Connect the Button
    w.PB_start.clicked.connect(starbutton_click)
    activate_pins()
    w.showFullScreen()
    w.setFixedSize(800, 480)
    sys.exit(app.exec_())
