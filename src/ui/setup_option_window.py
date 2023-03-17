
from __future__ import annotations
import os
import datetime
import shutil
from typing import Optional, TYPE_CHECKING
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow

from src.filepath import ROOT_PATH
from src.ui.create_config_window import ConfigWindow
from src.ui.setup_log_window import LogWindow
from src.ui.setup_rfid_writer_window import RFIDWriterWindow
from src.ui.setup_wifi_window import WiFiWindow
from src.ui_elements import Ui_Optionwindow
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.tabs import bottles
from src.programs.calibration import run_calibration
from src.machine.controller import MACHINE
from src.logger_handler import LoggerHandler
from src.save_handler import SAVE_HANDLER
from src.utils import has_connection, restart_program
from src.config_manager import CONFIG as cfg


if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_DATABASE_NAME = "Cocktail_database.db"
_CONFIG_NAME = "custom_config.yaml"
_VERSION_NAME = ".version.ini"
_NEEDED_FILES = [_DATABASE_NAME, _CONFIG_NAME, _VERSION_NAME]
_logger = LoggerHandler("option_window")


class OptionWindow(QMainWindow, Ui_Optionwindow):
    """ Class for the Option selection window. """

    def __init__(self, parent: MainScreen):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent

        self.button_back.clicked.connect(self.close)
        self.button_clean.clicked.connect(self._init_clean_machine)
        self.button_config.clicked.connect(self._open_config)
        self.button_reboot.clicked.connect(self._reboot_system)
        self.button_shutdown.clicked.connect(self._shutdown_system)
        self.button_calibration.clicked.connect(self._open_calibration)
        self.button_backup.clicked.connect(self._create_backup)
        self.button_restore.clicked.connect(self._upload_backup)
        self.button_export.clicked.connect(SAVE_HANDLER.export_data)
        self.button_logs.clicked.connect(self._show_logs)
        self.button_rfid.clicked.connect(self._open_rfid_writer)
        self.button_wifi.clicked.connect(self._open_wifi_window)
        self.button_check_internet.clicked.connect(self._check_internet_connection)

        self.button_rfid.setEnabled(cfg.RFID_READER != "No")

        self.config_window: Optional[ConfigWindow] = None
        self.log_window: Optional[LogWindow] = None
        self.rfid_writer_window: Optional[RFIDWriterWindow] = None
        self.wifi_window: Optional[WiFiWindow] = None
        UI_LANGUAGE.adjust_option_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _open_config(self):
        """Opens the config window."""
        # self.close()
        self.config_window = ConfigWindow(self.mainscreen)

    def _init_clean_machine(self):
        """Starting clean process if user confirms the action."""
        if not DP_CONTROLLER.ask_to_start_cleaning():
            return
        self.close()
        bottles.clean_machine(self.mainscreen)

    def _reboot_system(self):
        """Reboots the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_reboot():
            return
        MACHINE.cleanup()
        os.system("sudo reboot")
        self.close()

    def _shutdown_system(self):
        """Shutdown the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_shutdown():
            return
        MACHINE.cleanup()
        os.system("sudo shutdown now")
        self.close()

    def _open_calibration(self):
        """Opens the calibration window."""
        self.close()
        run_calibration(standalone=False)

    def _create_backup(self):
        """Prompts the user for a folder path to save the backup to.
        Saves the config, custom database and version to the location."""
        location = self._get_user_folder_response()
        if not location:
            return
        backup_folder_name = f"CocktailBerry_backup_{datetime.datetime.now().strftime('%Y-%m-%d')}"
        backup_folder = location / backup_folder_name
        # Logs if the backup folder already exists
        try:
            backup_folder.mkdir()
        except FileExistsError:
            _logger.log_event("INFO", "Backup folder for today already exists, overwriting current data within")

        for _file in _NEEDED_FILES:
            shutil.copy(ROOT_PATH / _file, backup_folder)
        DP_CONTROLLER.say_backup_created(str(backup_folder))

    def _upload_backup(self):
        """Prompts the user for a folder path to load the backup from.
        Loads the config, custom database and version from the location."""
        location = self._get_user_folder_response()
        if not location:
            return
        if not DP_CONTROLLER.ask_backup_overwrite():
            return
        for _file in _NEEDED_FILES:
            if not (location / _file).exists():
                DP_CONTROLLER.say_backup_failed(_file)
                return
        for _file in _NEEDED_FILES:
            shutil.copy(location / _file, ROOT_PATH)
        restart_program()

    def _get_user_folder_response(self):
        """Returns the user selected folder path."""
        # Qt will return empty string if user cancels the dialog
        selected_path = DP_CONTROLLER.ask_for_backup_location(self)
        if not selected_path:
            return None
        return Path(selected_path).absolute()

    def _show_logs(self):
        """Opens the logs window"""
        # self.close()
        self.log_window = LogWindow()

    def _open_rfid_writer(self):
        """Opens the rfid writer window"""
        self.close()
        self.rfid_writer_window = RFIDWriterWindow(self.mainscreen)

    def _open_wifi_window(self):
        """Opens a window to configure wifi"""
        # self.close()
        self.wifi_window = WiFiWindow(self.mainscreen)

    def _check_internet_connection(self):
        """Checks if there is a active internet connection"""
        is_connected = has_connection()
        DP_CONTROLLER.say_internet_connection_status(is_connected)
