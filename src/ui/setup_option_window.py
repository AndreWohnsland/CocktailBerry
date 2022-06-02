
import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from src.ui.create_config_window import ConfigWindow
from src.ui_elements.optionwindow import Ui_Optionwindow
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.tabs import bottles
from src.programs.calibration import run_calibration


class OptionWindow(QMainWindow, Ui_Optionwindow):
    """ Class for the Option selection window. """

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        DP_CONTROLLER.inject_stylesheet(self)
        self.setWindowIcon(QIcon(parent.icon_path))
        self.mainscreen = parent
        self.move(0, 0)

        self.button_back.clicked.connect(self.close)
        self.button_clean.clicked.connect(self._init_clean_machine)
        self.button_config.clicked.connect(self._open_config)
        self.button_reboot.clicked.connect(self._reboot_system)
        self.button_shutdown.clicked.connect(self._shutdown_system)
        self.button_calibration.clicked.connect(self._open_calibration)

        self.config_window: Optional[ConfigWindow] = None
        UI_LANGUAGE.adjust_option_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _open_config(self):
        """Opens the config window."""
        self.close()
        self.config_window = ConfigWindow(self.mainscreen)

    def _init_clean_machine(self):
        """Starting clean process if user confirms the action."""
        if not DP_CONTROLLER.ask_to_start_cleaning():
            return
        self.close()
        bottles.clean_machine()

    def _reboot_system(self):
        """Reboots the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_reboot():
            return
        os.system("sudo reboot")
        self.close()

    def _shutdown_system(self):
        """Shutdown the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_shutdow():
            return
        os.system("sudo shutdown now")
        self.close()

    def _open_calibration(self):
        """Opens the calibration window."""
        self.close()
        run_calibration(standalone=False)
