import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

from src.config.config_manager import CONFIG as cfg
from src.display_controller import DP_CONTROLLER
from src.error_handler import logerror
from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE
from src.models import Ingredient
from src.ui_elements.calibration import Ui_CalibrationWindow

logger = LoggerHandler("calibration_module")


class CalibrationScreen(QMainWindow, Ui_CalibrationWindow):
    def __init__(self, standalone: bool):
        """Init the calibration Screen."""
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        # Connect the Button
        bottles = cfg.MAKER_NUMBER_BOTTLES
        self.PB_start.clicked.connect(self.output_volume)
        self.channel_plus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.channel, 1, bottles, 1))
        self.channel_minus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.channel, 1, bottles, -1))
        self.amount_plus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.amount, 10, 200, 10))
        self.amount_minus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.amount, 10, 200, -10))
        self.button_exit.clicked.connect(self.close)
        self.showFullScreen()
        DP_CONTROLLER.inject_stylesheet(self)
        DP_CONTROLLER.set_display_settings(self)
        if standalone:
            MACHINE.set_up_pumps()
        logger.log_start_program("calibration")

    def output_volume(self):
        """Output the set number of volume according to defined volume flow."""
        channel_number = int(self.channel.text())
        amount = int(self.amount.text())
        display_name = f"{amount} ml volume, pump #{channel_number}"
        ing = Ingredient(
            id=0,
            name="Calibration",
            alcohol=0,
            bottle_volume=1000,
            fill_level=1000,
            hand=False,
            pump_speed=100,
            amount=amount,
            bottle=channel_number,
        )
        MACHINE.make_cocktail(
            w=None,
            ingredient_list=[ing],
            recipe=display_name,
            is_cocktail=False,
            verbose=False,
        )


@logerror
def run_calibration(standalone=True):
    """Execute the calibration screen."""
    if standalone:
        app = QApplication(sys.argv)
    # this assignment is needed, otherwise the window will close in an instant
    # pylint: disable=unused-variable
    calibration = CalibrationScreen(standalone)  # noqa
    if standalone:
        sys.exit(app.exec_())  # type: ignore
