import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

from src.config_manager import ConfigManager
from src.display_controller import DP_CONTROLLER
from src.error_handler import logerror
from src.logger_handler import LoggerHandler
from src.rpi_controller import RPI_CONTROLLER


ui_file = Path(__file__).parent.absolute() / "ui_elements" / "Calibration.ui"
logger = LoggerHandler("calibration_module", "production_logs")


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
        RPI_CONTROLLER.initializing_pins()
        logger.log_start_program("calibration")

    def output_volume(self):
        """Outputs the set number of volume according to defined volume flow"""
        channel_number = int(self.channel.text())
        amount = int(self.amount.text())
        display_name = f"{amount} ml volume, pump #{channel_number}"
        RPI_CONTROLLER.make_cocktail(None, [channel_number], [amount], display_name, False)


@logerror
def run_calibration():
    """Executes the calibration screen"""
    app = QApplication(sys.argv)
    # this asignment is needed, otherwise the window will close in an instant
    # pylint: disable=unused-variable
    cali = CalibrationScreen()
    sys.exit(app.exec_())
