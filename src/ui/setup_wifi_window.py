from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QLineEdit, QMainWindow, qApp

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui.icons import ICONS
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui_elements import Ui_WiFiWindow
from src.utils import get_platform_data, setup_wifi, time_print

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_platform_data = get_platform_data()


class WiFiWindow(QMainWindow, Ui_WiFiWindow):
    """Class for the enter wifi window."""

    def __init__(self, mainscreen: MainScreen) -> None:
        """Init the window and connect the elements."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)

        # Init objects
        self.mainscreen = mainscreen
        self.keyboard_window: KeyboardWidget | None = None
        self.button_enter.setDisabled(True)
        # Connecting elements
        self.button_back.clicked.connect(self.close)
        self.button_enter.clicked.connect(self._wifi_enter_process)
        self.input_ssid.clicked.connect(lambda: self._open_keyboard(self.input_ssid))
        self.input_ssid.textChanged.connect(self._check_valid_inputs)
        self.input_password.clicked.connect(lambda: self._open_keyboard(self.input_password))
        self.input_password.textChanged.connect(self._check_valid_inputs)

        UI_LANGUAGE.adjust_wifi_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _check_valid_inputs(self) -> None:
        """Check if both, name and password are at least one character, otherwise enter is disabled."""
        is_valid = len(self.input_password.text()) > 0 and len(self.input_ssid.text()) > 0
        if is_valid:
            self.button_enter.setDisabled(False)
            return
        self.button_enter.setDisabled(True)

    def _open_keyboard(self, le_to_write: QLineEdit, max_char_len: int = 64) -> None:
        """Open up the keyboard connected to the lineedit."""
        self.keyboard_window = KeyboardWidget(self.mainscreen, le_to_write=le_to_write, max_char_len=max_char_len)

    def _wifi_enter_process(self) -> None:
        """Start to enter wifi, uses a spinner during progress."""
        ICONS.set_wait_icon(self.button_enter)
        qApp.processEvents()
        self._enter_wifi()
        ICONS.remove_icon(self.button_enter)
        qApp.processEvents()

    def _enter_wifi(self) -> None:
        """Enter the wifi data into the system and check if the connection was successful."""
        if _platform_data.system == "Windows":
            time_print("Cannot do that on windows")
            return

        ssid = self.input_ssid.text()
        password = self.input_password.text()
        success = setup_wifi(ssid, password)
        if not success:
            DP_CONTROLLER.say_wifi_setup_failed()
            return

        tries = 0
        is_connected = False
        while tries < 5 and not is_connected:
            ssid_output = subprocess.run(["iwgetid"], stdout=subprocess.PIPE, check=False).stdout.decode("utf-8")
            is_connected = ssid in ssid_output
            time.sleep(3)
            tries += 1
        DP_CONTROLLER.say_wifi_entered(is_connected, ssid, password)
