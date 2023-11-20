
from __future__ import annotations
import os
import datetime
import shutil
import atexit
from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QObject, pyqtSignal

from src.ui.create_config_window import ConfigWindow
from src.ui.create_backup_restore_window import BackupRestoreWindow, BACKUP_FILES, NEEDED_BACKUP_FILES
from src.ui.setup_data_window import DataWindow
from src.ui.setup_log_window import LogWindow
from src.ui.setup_rfid_writer_window import RFIDWriterWindow
from src.ui.setup_wifi_window import WiFiWindow
from src.ui.setup_addon_window import AddonWindow
from src.ui.creation_utils import setup_worker_thread
from src.ui_elements import Ui_Optionwindow
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.machine.controller import MACHINE
from src.programs.calibration import run_calibration
from src.logger_handler import LoggerHandler
from src.updater import Updater
from src.utils import has_connection, get_platform_data, time_print
from src.config_manager import CONFIG as cfg


if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("option_window")
_platform_data = get_platform_data()


class _Worker(QObject):
    """Worker to install qtsass on a thread"""
    done = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        os.system("sudo apt-get update && sudo apt-get -y upgrade")
        self.done.emit()


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
        self.button_export.clicked.connect(self._data_insights)
        self.button_logs.clicked.connect(self._show_logs)
        self.button_rfid.clicked.connect(self._open_rfid_writer)
        self.button_wifi.clicked.connect(self._open_wifi_window)
        self.button_addons.clicked.connect(self._open_addon_window)
        self.button_check_internet.clicked.connect(self._check_internet_connection)
        self.button_update_system.clicked.connect(self._update_system)
        self.button_update_software.clicked.connect(self._update_software)

        self.button_rfid.setEnabled(cfg.RFID_READER != "No")

        self.config_window: Optional[ConfigWindow] = None
        self.log_window: Optional[LogWindow] = None
        self.rfid_writer_window: Optional[RFIDWriterWindow] = None
        self.wifi_window: Optional[WiFiWindow] = None
        self.addon_window: Optional[AddonWindow] = None
        self.data_window: Optional[DataWindow] = None
        self.backup_restore_window: Optional[BackupRestoreWindow] = None
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
        # bottles.clean_machine(self.mainscreen)
        _logger.log_header("INFO", "Cleaning the Pumps")
        revert_pumps = False
        if cfg.MAKER_PUMP_REVERSION:
            revert_pumps = DP_CONTROLLER.ask_to_use_reverted_pump()
        MACHINE.clean_pumps(self.mainscreen, revert_pumps)
        DP_CONTROLLER.say_done()

    def _reboot_system(self):
        """Reboots the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_reboot():
            return
        if self._is_windows():
            return
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        os.system("sudo reboot")
        self.close()

    def _shutdown_system(self):
        """Shutdown the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_shutdown():
            return
        if self._is_windows():
            return
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        os.system("sudo shutdown now")
        self.close()

    def _data_insights(self):
        """Opens the data window"""
        self.data_window = DataWindow()

    def _open_calibration(self):
        """Opens the calibration window."""
        self.close()
        run_calibration(standalone=False)

    def _create_backup(self):
        """Prompts the user for a folder path to save the backup to.
        Saves the config, custom database and version to the location."""
        location = DP_CONTROLLER.ask_for_backup_location(self)
        if not location:
            return
        backup_folder_name = f"CocktailBerry_backup_{datetime.datetime.now().strftime('%Y-%m-%d')}"
        backup_folder = location / backup_folder_name

        # Logs if the backup folder already exists
        # also deletes the folder if it already exists
        if backup_folder.exists():
            _logger.log_event("INFO", "Backup folder for today already exists, overwriting current data within")
            shutil.rmtree(backup_folder)
        backup_folder.mkdir()

        # copy all files to the backup folder
        for _file in BACKUP_FILES:
            # needs to differentiate between files and folders
            if _file.is_file():
                shutil.copy(_file, backup_folder)
            if _file.is_dir():
                shutil.copytree(_file, backup_folder / _file.name)

        DP_CONTROLLER.say_backup_created(str(backup_folder))

    def _upload_backup(self):
        """Opens the backup restore window."""
        location = DP_CONTROLLER.ask_for_backup_location(self)
        if not location:
            return
        for _file in NEEDED_BACKUP_FILES:
            file_name = _file.name
            if not (location / file_name).exists():
                DP_CONTROLLER.say_backup_failed(file_name)
                return
        self.backup_restore_window = BackupRestoreWindow(self.mainscreen, location)

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

    def _open_addon_window(self):
        """Opens a window to configure wifi"""
        # self.close()
        self.addon_window = AddonWindow(self.mainscreen)

    def _check_internet_connection(self):
        """Checks if there is a active internet connection"""
        is_connected = has_connection()
        DP_CONTROLLER.say_internet_connection_status(is_connected)

    def _update_system(self):
        """Makes a system update and upgrade"""
        if not DP_CONTROLLER.ask_to_update_system():
            return
        if self._is_windows():
            return

        self._worker = _Worker()  # pylint: disable=attribute-defined-outside-init
        self._thread = setup_worker_thread(  # pylint: disable=attribute-defined-outside-init
            self._worker,
            self,
            self._finish_update_worker
        )

    def _update_software(self):
        """First asks and then updates the software"""
        updater = Updater()
        update_available, info = updater.check_for_updates()
        # If there is no update available, but there is info, show it
        # this is usually only if there is an error or something
        if not update_available and not info:
            DP_CONTROLLER.say_cocktailberry_up_to_date()
            return
        # else inform the user about that he is up to date
        if not update_available and info:
            DP_CONTROLLER.standard_box(info)
            return
        # if there is an update available, ask the user if he wants to update
        if DP_CONTROLLER.ask_to_update(info):
            updater.update()

    def _finish_update_worker(self):
        """Ends the spinner, checks if installation was successful"""
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        os.system("sudo reboot")

    def _is_windows(self):
        """Linux things cannot be done on windows.
        Print a msg and return true if win."""
        is_win = _platform_data.system == "Windows"
        if is_win:
            time_print("Cannot do that on windows")
        return is_win
