from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QLineEdit, QMainWindow, qApp

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.ui.icons import ICONS
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui_elements import Ui_WiFiWindow
from src.utils import get_platform_data, time_print

if TYPE_CHECKING:
    from src.ui_elements import Ui_MainWindow


_logger = LoggerHandler("WiFiSetup")
_WPA_FILE_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"
_platform_data = get_platform_data()


class WiFiWindow(QMainWindow, Ui_WiFiWindow):
    """Class for the enter wifi window."""

    def __init__(self, mainscreen: Ui_MainWindow):
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

    def _check_valid_inputs(self):
        """Check if both, name and password are at least one character, otherwise enter is disabled."""
        is_valid = len(self.input_password.text()) > 0 and len(self.input_ssid.text()) > 0
        if is_valid:
            self.button_enter.setDisabled(False)
            return
        self.button_enter.setDisabled(True)

    def _open_keyboard(self, le_to_write: QLineEdit, max_char_len: int = 64):
        """Open up the keyboard connected to the lineedit."""
        self.keyboard_window = KeyboardWidget(self.mainscreen, le_to_write=le_to_write, max_char_len=max_char_len)

    def _wifi_enter_process(self):
        """Start to enter wifi, uses a spinner during progress."""
        ICONS.set_wait_icon(self.button_enter)
        qApp.processEvents()
        self._enter_wifi()
        ICONS.remove_icon(self.button_enter)
        qApp.processEvents()

    def _enter_wifi(self):
        """Enter the wifi credentials into the wpa_supplicant.conf.

        Restarts wlan0 interface, checks for internet after that.
        """
        if _platform_data.system == "Windows":
            time_print("Cannot do that on windows")
            return
        if not Path(_WPA_FILE_PATH).exists():
            self._make_wpa_file()
        os.popen(f"sudo chmod a+rw {_WPA_FILE_PATH}")
        # Wait short, otherwise, it may not be applied below
        time.sleep(1)

        ssid = self.input_ssid.text()
        password = self.input_password.text()
        cmd = ["wpa_passphrase", ssid, password]
        try:
            with open(_WPA_FILE_PATH, "a", encoding="utf-8") as wpa_file:
                subprocess.run(cmd, stdout=wpa_file, check=False)
        except PermissionError:
            _logger.log_event(
                "ERROR",
                "Could not write to wpa_supplicant.conf, check if the file got write access for all users. "
                + "You can change it with: 'sudo chmod a+rw {_WPA_FILE_PATH}'",
            )
            DP_CONTROLLER.say_wifi_setup_failed()
            return
        # This can happen if on Win / wpa_passphrase not installed
        except FileNotFoundError:
            _logger.log_event(
                "ERROR",
                "Got a FileNotFoundError, this is most likely because the wpa_passphrase command is not recognized. "
                + "Run 'sudo apt-get install wpasupplicant' to install it.",
            )
            DP_CONTROLLER.say_wifi_setup_failed()
            return

        cmd = ["wpa_cli", "-i", "wlan0", "reconfigure"]
        wpa_response = subprocess.run(cmd, stdout=subprocess.PIPE, check=False)
        wpa_text = wpa_response.stdout.decode("utf-8")
        response_ok = "ok" in wpa_text.lower()
        if not response_ok:
            _logger.log_event("WARNING", "Could not reconfigure wlan0, maybe a restart will solve this.")
        # Try up to x5 to check for connection
        tries = 0
        is_connected = False
        while tries < 5 and not is_connected:
            ssid_output = subprocess.run(["iwgetid"], stdout=subprocess.PIPE, check=False).stdout.decode("utf-8")
            is_connected = ssid in ssid_output
            time.sleep(3)
            tries += 1
        DP_CONTROLLER.say_wifi_entered(is_connected, ssid, password)

    def _make_wpa_file(self):
        """Create the bare bone wpa file."""
        file_path = Path(_WPA_FILE_PATH)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        config_lines = [
            "ctrl_interface=DIR=/var/run/wpa_supplicant/wpa_supplicant.conf",
            "update_config=1",
            "",
        ]
        config = "\n".join(config_lines)

        with file_path.open("w", encoding="utf-8") as config_file:
            config_file.write(config)
