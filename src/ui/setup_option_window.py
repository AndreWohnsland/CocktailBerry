
import os
import sys
import datetime
import shutil
from typing import Optional
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from src.ui.create_config_window import ConfigWindow
from src.ui_elements.optionwindow import Ui_Optionwindow
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.tabs import bottles
from src.programs.calibration import run_calibration
from src.logger_handler import LogFiles, LoggerHandler


_ROOT_PATH = Path(__file__).parents[2].absolute()
_DATABASE_NAME = "Cocktail_database.db"
_CONFIG_NAME = "custom_config.yaml"
_VERSION_NAME = ".version.ini"
_NEEDED_FILES = [_DATABASE_NAME, _CONFIG_NAME, _VERSION_NAME]
_EXECUTABLE = _ROOT_PATH / "runme.py"
_logger = LoggerHandler("option_window", LogFiles.PRODUCTION)


class OptionWindow(QMainWindow, Ui_Optionwindow):
    """ Class for the Option selection window. """

    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
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
        self.button_backup.clicked.connect(self._create_backup)
        self.button_restore.clicked.connect(self._upload_backup)

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
        bottles.clean_machine(self.mainscreen)

    def _reboot_system(self):
        """Reboots the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_reboot():
            return
        os.system("sudo reboot")
        self.close()

    def _shutdown_system(self):
        """Shutdown the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_shutdown():
            return
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
            shutil.copy(_ROOT_PATH / _file, backup_folder)
        DP_CONTROLLER.say_backup_created(str(backup_folder))
        self.close()

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
            shutil.copy(location / _file, _ROOT_PATH)
        os.execl(sys.executable, _EXECUTABLE, *sys.argv)

    def _get_user_folder_response(self):
        """Returns the user selected folder path."""
        # Qt will return empty string if user cancels the dialog
        selected_path = DP_CONTROLLER.ask_for_backup_location(self)
        if not selected_path:
            return None
        return Path(selected_path).absolute()
