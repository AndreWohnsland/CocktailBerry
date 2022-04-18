from typing import Union
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from src.ui.create_config_window import ConfigWindow
from src.ui_elements.optionwindow import Ui_Optionwindow
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.tabs import bottles


class OptionWindow(QMainWindow, Ui_Optionwindow):
    """ Class for the Team selection Screen. """

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

        self.config_window: Union[None, ConfigWindow] = None
        UI_LANGUAGE.adjust_option_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _open_config(self):
        self.config_window = ConfigWindow(self.mainscreen)
        self.close()

    def _init_clean_machine(self):
        if not DP_CONTROLLER.user_okay("Starting Cleaning Progress?"):
            return
        self.close()
        bottles.clean_machine(self.mainscreen)
