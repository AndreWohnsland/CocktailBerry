from __future__ import annotations

import atexit
import datetime
import os
import shutil
from typing import TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMainWindow

from src.config.config_manager import CONFIG as cfg
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.machine.controller import MachineController
from src.migration.backup import BACKUP_FILES, NEEDED_BACKUP_FILES
from src.programs.calibration import CalibrationScreen
from src.ui.create_backup_restore_window import BackupRestoreWindow
from src.ui.create_config_window import ConfigWindow
from src.ui.creation_utils import setup_worker_thread
from src.ui.setup_addon_window import AddonWindow
from src.ui.setup_data_window import DataWindow
from src.ui.setup_log_window import LogWindow
from src.ui.setup_resource_window import ResourceWindow
from src.ui.setup_rfid_writer_window import RFIDWriterWindow
from src.ui.setup_wifi_window import WiFiWindow
from src.ui_elements import Ui_Optionwindow
from src.updater import UpdateInfo, Updater
from src.utils import get_platform_data, has_connection, update_os

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("option_window")
_platform_data = get_platform_data()


class _Worker(QObject):
    """Worker to get full system update on a thread."""

    done = pyqtSignal()

    def __init__(self, parent: None | QObject = None) -> None:
        super().__init__(parent)

    def run(self) -> None:
        update_os()
        self.done.emit()


class OptionWindow(QMainWindow, Ui_Optionwindow):
    """Class for the Option selection window."""

    def __init__(self, parent: MainScreen) -> None:
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
        self.button_resources.clicked.connect(self._resource_insights)

        self.button_rfid.setEnabled(cfg.RFID_READER != "No")

        self.config_window: ConfigWindow | None = None
        self.log_window: LogWindow | None = None
        self.rfid_writer_window: RFIDWriterWindow | None = None
        self.wifi_window: WiFiWindow | None = None
        self.addon_window: AddonWindow | None = None
        self.data_window: DataWindow | None = None
        self.backup_restore_window: BackupRestoreWindow | None = None
        self.resource_window: ResourceWindow | None = None
        self.calibration_screen: CalibrationScreen | None = None
        UI_LANGUAGE.adjust_option_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _open_config(self) -> None:
        """Open the config window."""
        # self.close()
        self.config_window = ConfigWindow(self.mainscreen)

    def _init_clean_machine(self) -> None:
        """Start clean process if user confirms the action."""
        if not DP_CONTROLLER.ask_to_start_cleaning():
            return
        # bottles.clean_machine(self.mainscreen)
        _logger.log_header("INFO", "Cleaning the Pumps")
        revert_pumps = False
        if cfg.MAKER_PUMP_REVERSION:
            revert_pumps = DP_CONTROLLER.ask_to_use_reverted_pump()
        mc = MachineController()
        mc.clean_pumps(self.mainscreen, revert_pumps)
        DP_CONTROLLER.say_done()

    def _reboot_system(self) -> None:
        """Reboots the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_reboot():
            return
        if self._is_windows("reboot"):
            return
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        os.system("sudo reboot")
        self.close()

    def _shutdown_system(self) -> None:
        """Shutdown the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_shutdown():
            return
        if self._is_windows("shutdown"):
            return
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        os.system("sudo shutdown now")
        self.close()

    def _data_insights(self) -> None:
        """Open the data window."""
        self.data_window = DataWindow()

    def _resource_insights(self) -> None:
        """Open the resource window."""
        self.resource_window = ResourceWindow()

    def _open_calibration(self) -> None:
        """Open the calibration window."""
        self.calibration_screen = CalibrationScreen()

    def _create_backup(self) -> None:
        """Prompt the user for a folder path to save the backup to.

        Saves the config, custom database and version to the location.
        """
        location = DP_CONTROLLER.ask_for_backup_location()
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

    def _upload_backup(self) -> None:
        """Open the backup restore window."""
        location = DP_CONTROLLER.ask_for_backup_location()
        if not location:
            return
        for _file in NEEDED_BACKUP_FILES:
            file_name = _file.name
            if not (location / file_name).exists():
                DP_CONTROLLER.say_backup_failed(file_name)
                return
        self.backup_restore_window = BackupRestoreWindow(self.mainscreen, location)

    def _show_logs(self) -> None:
        """Open the logs window."""
        # self.close()
        self.log_window = LogWindow()

    def _open_rfid_writer(self) -> None:
        """Open the rfid writer window."""
        self.close()
        self.rfid_writer_window = RFIDWriterWindow(self.mainscreen)

    def _open_wifi_window(self) -> None:
        """Open a window to configure wifi."""
        # self.close()
        self.wifi_window = WiFiWindow(self.mainscreen)

    def _open_addon_window(self) -> None:
        """Open a window to configure wifi."""
        # self.close()
        self.addon_window = AddonWindow(self.mainscreen)

    def _check_internet_connection(self) -> None:
        """Check if there is a active internet connection."""
        is_connected = has_connection()
        DP_CONTROLLER.say_internet_connection_status(is_connected)

    def _update_system(self) -> None:
        """Make a system update and upgrade."""
        if not DP_CONTROLLER.ask_to_update_system():
            return
        if self._is_windows("update system"):
            return

        self._worker = _Worker()  # pylint: disable=attribute-defined-outside-init
        self._thread = setup_worker_thread(  # pylint: disable=attribute-defined-outside-init
            self._worker, self, self._finish_update_worker
        )

    def _update_software(self) -> None:
        """First asks and then updates the software."""
        updater = Updater()
        info = updater.check_for_updates()
        if info.status == UpdateInfo.Status.UP_TO_DATE:
            DP_CONTROLLER.say_cocktailberry_up_to_date()
            return
        if info.status == UpdateInfo.Status.ERROR:
            DP_CONTROLLER.standard_box(info.message)
            return
        if DP_CONTROLLER.ask_to_update(
            release_information=info.message,
            major_update=info.status == UpdateInfo.Status.MAJOR_UPDATE,
        ):
            updater.update()

    def _finish_update_worker(self) -> None:
        """End the spinner, checks if installation was successful."""
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        os.system("sudo reboot")

    def _is_windows(self, action: str) -> bool:
        """Linux things cannot be done on windows.

        Print a msg and return true if win.
        """
        is_win = _platform_data.system == "Windows"
        if is_win:
            _logger.info(f"Cannot do {action} on windows")
        return is_win
