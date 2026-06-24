from __future__ import annotations

import atexit
import datetime
import shutil
import subprocess
from typing import TYPE_CHECKING

from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QMainWindow, QPushButton

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DatabaseCommander
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.machine.controller import MachineController
from src.migration.backup import BACKUP_FILES, NEEDED_BACKUP_FILES
from src.models import EventType
from src.programs.blacklist import BLACKLIST
from src.programs.calibration import CalibrationScreen
from src.programs.scale_calibration import ScaleCalibrationScreen
from src.ui.create_backup_restore_window import BackupRestoreWindow
from src.ui.create_config_window import ConfigWindow
from src.ui.creation_utils import NARROW_WIDTH_THRESHOLD, repack_grid
from src.ui.qt_worker import CallableWorker, run_with_spinner
from src.ui.setup_addon_window import AddonWindow
from src.ui.setup_data_window import DataWindow
from src.ui.setup_event_window import EventWindow
from src.ui.setup_log_window import LogWindow
from src.ui.setup_news_window import NewsWindow
from src.ui.setup_resource_window import ResourceWindow
from src.ui.setup_rfid_writer_window import RFIDWriterWindow
from src.ui.setup_sumup_window import SumupWindow
from src.ui.setup_waiter_window import WaiterWindow
from src.ui.setup_wifi_window import WiFiWindow
from src.ui_elements import Ui_Optionwindow
from src.updater import UpdateInfo, Updater
from src.utils import get_platform_data, has_connection, update_os

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("option_window")
_platform_data = get_platform_data()


class OptionWindow(QMainWindow, Ui_Optionwindow):
    """Class for the Option selection window."""

    def __init__(self, parent: MainScreen) -> None:
        super().__init__()
        self._tile_columns = 2
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent

        self.button_back.clicked.connect(self.close)
        self.button_clean.clicked.connect(self._init_clean_machine)
        self.button_initialize_bottles.clicked.connect(self._init_initialize_bottles)
        self.button_config.clicked.connect(self._open_config)
        self.button_reboot.clicked.connect(self._reboot_system)
        self.button_shutdown.clicked.connect(self._shutdown_system)
        self.button_calibration.clicked.connect(self._open_calibration)
        self.button_scale_calibration.clicked.connect(self._open_scale_calibration)
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
        self.button_about.clicked.connect(DP_CONTROLLER.say_welcome_message)
        self.button_news.clicked.connect(self._open_news_window)
        self.button_sumup.clicked.connect(self._open_sumup_window)
        self.button_waiter.clicked.connect(self._open_waiter_window)
        self.button_events.clicked.connect(self._open_event_window)

        self.button_rfid.setEnabled(cfg.nfc_enabled)
        self.button_sumup.setEnabled(cfg.sumup_payment)
        self.button_scale_calibration.setEnabled(cfg.SCALE_CONFIG.enabled)

        self._apply_tile_blacklist()

        self.config_window: ConfigWindow | None = None
        self.log_window: LogWindow | None = None
        self.rfid_writer_window: RFIDWriterWindow | None = None
        self.wifi_window: WiFiWindow | None = None
        self.addon_window: AddonWindow | None = None
        self.data_window: DataWindow | None = None
        self.backup_restore_window: BackupRestoreWindow | None = None
        self.resource_window: ResourceWindow | None = None
        self.calibration_screen: CalibrationScreen | None = None
        self.scale_calibration_screen: ScaleCalibrationScreen | None = None
        self.sumup_window: SumupWindow | None = None
        self.event_window: EventWindow | None = None
        UI_LANGUAGE.adjust_option_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _apply_tile_blacklist(self) -> None:
        """Repack the option tile grid, dropping blacklisted tiles.

        Delegates to ``repack_grid``. Column count tracks ``self._tile_columns``
        so the same code handles both blacklist filtering and responsive
        column-count changes triggered from ``resizeEvent``.
        """
        order = self._TILE_ORDER
        attr_by_button = {button: attr for button, attr, _ in order}
        items = [(button, span) for button, _attr, span in order]
        show_initialize = MachineController.has_tube_volume()

        def skip(widget: QPushButton) -> bool:
            if widget is self.button_initialize_bottles and not show_initialize:
                return True
            return BLACKLIST.is_tile_blacklisted(attr_by_button[widget])

        repack_grid(
            self.gridLayout_2,
            items,
            self._tile_columns,
            skip=skip,  # ty: ignore[invalid-argument-type]
        )

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        target_columns = 1 if self.width() < NARROW_WIDTH_THRESHOLD else 2
        if target_columns != self._tile_columns:
            self._tile_columns = target_columns
            self._apply_tile_blacklist()

    @property
    def _TILE_ORDER(self) -> list[tuple[QPushButton, str, int]]:
        """Canonical tile ordering (button, OptionTiles attribute, column span).

        Order matches the original ``optionwindow.ui`` grid reading top-to-bottom,
        left-to-right. Span is 2 for full-width tiles, otherwise 1.
        """
        return [
            (self.button_clean, "cleaning", 1),
            (self.button_initialize_bottles, "initialize_bottles", 1),
            (self.button_calibration, "calibration", 1),
            (self.button_config, "configuration", 1),
            (self.button_export, "data", 1),
            (self.button_backup, "backup", 1),
            (self.button_restore, "restore", 1),
            (self.button_reboot, "reboot", 1),
            (self.button_shutdown, "shutdown", 1),
            (self.button_logs, "logs", 1),
            (self.button_resources, "system_resource_usage", 1),
            (self.button_events, "events", 1),
            (self.button_update_system, "update_system", 1),
            (self.button_update_software, "update_software", 2),
            (self.button_wifi, "wifi", 1),
            (self.button_check_internet, "internet_check", 1),
            (self.button_addons, "addons", 1),
            (self.button_rfid, "rfid", 1),
            (self.button_news, "news", 1),
            (self.button_sumup, "sumup", 1),
            (self.button_waiter, "waiters", 1),
            (self.button_scale_calibration, "scale_calibration", 1),
            (self.button_about, "about", 2),
        ]

    def _open_config(self) -> None:
        """Open the config window."""
        self.config_window = ConfigWindow(self.mainscreen)

    def _init_clean_machine(self) -> None:
        """Start clean process if user confirms the action."""
        if not DP_CONTROLLER.ask_to_start_cleaning():
            return
        _logger.info("Cleaning requested over option UI, starting cleaning process")
        revert_pumps = False
        if cfg.MAKER_PUMP_REVERSION_CONFIG.enabled:
            revert_pumps = DP_CONTROLLER.ask_to_use_reverted_pump()
        mc = MachineController()
        mc.clean_pumps(self.mainscreen, revert_pumps)
        DP_CONTROLLER.say_done()

    def _init_initialize_bottles(self) -> None:
        """Prime all pump tubes if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_initialize_bottles():
            return
        _logger.info("Bottle initialization requested over option UI")
        MachineController().initialize_bottles(self.mainscreen)
        DP_CONTROLLER.say_done()

    def _reboot_system(self) -> None:
        """Reboots the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_reboot():
            return
        if self._is_windows("reboot"):
            return
        DatabaseCommander().save_event(EventType.REBOOT)
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        subprocess.run(["sudo", "reboot"], check=False)
        self.close()

    def _shutdown_system(self) -> None:
        """Shutdown the system if the user confirms the action."""
        if not DP_CONTROLLER.ask_to_shutdown():
            return
        if self._is_windows("shutdown"):
            return
        DatabaseCommander().save_event(EventType.SHUTDOWN)
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        subprocess.run(["sudo", "shutdown", "now"], check=False)
        self.close()

    def _data_insights(self) -> None:
        """Open the data window."""
        self.data_window = DataWindow()

    def _resource_insights(self) -> None:
        """Open the resource window."""
        self.resource_window = ResourceWindow()

    def _open_calibration(self) -> None:
        """Open the calibration window."""
        self.calibration_screen = CalibrationScreen(self.mainscreen)

    def _open_scale_calibration(self) -> None:
        """Open the scale calibration window."""
        self.scale_calibration_screen = ScaleCalibrationScreen()

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
        self.log_window = LogWindow()

    def _open_rfid_writer(self) -> None:
        """Open the rfid writer window."""
        self.close()
        self.rfid_writer_window = RFIDWriterWindow(self.mainscreen)

    def _open_wifi_window(self) -> None:
        """Open a window to configure wifi."""
        self.wifi_window = WiFiWindow(self.mainscreen)

    def _open_addon_window(self) -> None:
        """Open a window to configure wifi."""
        self.addon_window = AddonWindow(self.mainscreen)

    def _open_news_window(self) -> None:
        """Open the news window."""
        self.news_window = NewsWindow(self.mainscreen)

    def _open_sumup_window(self) -> None:
        """Open the SumUp configuration window."""
        self.sumup_window = SumupWindow(self.mainscreen)

    def _open_waiter_window(self) -> None:
        """Open the waiter configuration window."""
        self.waiter_window = WaiterWindow(self.mainscreen)

    def _open_event_window(self) -> None:
        """Open the events window."""
        self.event_window = EventWindow()

    def _check_internet_connection(self) -> None:
        """Check if there is an active internet connection."""
        is_connected = has_connection()
        DP_CONTROLLER.say_internet_connection_status(is_connected)

    def _update_system(self) -> None:
        """Make a system update and upgrade."""
        if not DP_CONTROLLER.ask_to_update_system():
            return
        if self._is_windows("update system"):
            return

        self._worker: CallableWorker[None] = run_with_spinner(
            update_os,
            parent=self,
            on_finish=lambda _: self._finish_update_worker(),
        )

    def _update_software(self) -> None:
        """Let the user pick a version from the available updates, then update."""
        updater = Updater()
        info = updater.check_for_updates()
        if info.status == UpdateInfo.Status.UP_TO_DATE:
            DP_CONTROLLER.say_cocktailberry_up_to_date()
            return
        if info.status == UpdateInfo.Status.ERROR:
            DP_CONTROLLER.standard_box(info.message)
            return
        selected = DP_CONTROLLER.ask_to_update_version(info.versions)
        if selected is None:
            return
        if not updater.update(selected):
            DP_CONTROLLER.say_update_failed()

    def _finish_update_worker(self) -> None:
        """End the spinner, checks if installation was successful."""
        atexit._run_exitfuncs()  # pylint: disable=protected-access
        subprocess.run(["sudo", "reboot"], check=False)

    def _is_windows(self, action: str) -> bool:
        """Linux things cannot be done on windows.

        Print a msg and return true if win.
        """
        is_win = _platform_data.system == "Windows"
        if is_win:
            _logger.info(f"Cannot do {action} on windows")
        return is_win
