from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QMainWindow, QTableWidgetItem

from src.data_utils import CouldNotInstallAddonError, get_addon_data, install_addon, remove_addon
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.models import AddonData
from src.programs.addons import ADDONS
from src.ui_elements import Ui_AddonManager
from src.utils import restart_program

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("AddonManager")


class AddonManager(QMainWindow, Ui_AddonManager):
    """Creates A window to display addon GUI for the user."""

    def __init__(self, parent: "MainScreen") -> None:
        """Initialize the object."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        # connects all the buttons
        self.button_back.clicked.connect(self.close)
        self.button_apply.clicked.connect(self._apply_changes)
        self._installed_addons = ADDONS.addons
        self._addon_information = get_addon_data()
        self._gui_addons: dict[str, QTableWidgetItem] = {}
        self._fill_addon_list()

        UI_LANGUAGE.adjust_addon_manager(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _fill_addon_list(self) -> None:
        """Fill the addon list widget with all the addon data."""
        self.table_addons.setRowCount(len(self._addon_information))
        self.table_addons.setColumnCount(1)
        for i, addon in enumerate(self._addon_information):
            content = f"{addon.name} ({addon.file_name})\n{addon.description}"
            description_cell = QTableWidgetItem(content)
            # if its an official addon, add checkable box to the left
            # if it's not installable, only show the box, if it's installed
            can_remove = addon.official and addon.installed and not addon.is_installable
            if (addon.official and addon.is_installable) or can_remove:
                description_cell.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)  # type: ignore
                description_cell.setCheckState(Qt.Checked if addon.installed else Qt.Unchecked)  # type: ignore
            self.table_addons.setItem(i, 0, description_cell)
            # Add to control, that we can retrieve check state later
            self._gui_addons[addon.name] = description_cell

        # Style settings that the table is full width and makes line wraps and no ellipsis
        self.table_addons.horizontalHeader().setStretchLastSection(True)
        self.table_addons.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore
        self.table_addons.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # type: ignore
        self.table_addons.resizeColumnsToContents()
        self.table_addons.resizeRowsToContents()

    def _apply_changes(self) -> None:
        # First apply all the user checked settings
        for addon in self._addon_information:
            # ignore unofficial addons here
            if not addon.official:
                continue
            addon.installed = self._gui_addons[addon.name].checkState() == Qt.Checked  # type: ignore
            # Download from source if user did check
            # Also overwrite current files, so new version of the addons will be fetched
            if addon.installed:
                self._install_addon(addon)
            # remove or ignore (if not exists) if its not checked
            else:
                remove_addon(addon)

        # Ask to restart
        if DP_CONTROLLER.ask_to_restart_for_config():
            restart_program(is_v1=True)

    def _install_addon(self, addon: AddonData) -> None:
        """Try to install addon, log if req is not ok or no connection."""
        try:
            install_addon(addon)
        except CouldNotInstallAddonError as e:
            _logger.log_event("ERROR", str(e))
