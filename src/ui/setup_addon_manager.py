import json
from dataclasses import dataclass
from pathlib import Path

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QMainWindow, QTableWidgetItem
from requests.exceptions import ConnectionError as ReqConnectionError

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.filepath import ADDON_FOLDER
from src.logger_handler import LoggerHandler
from src.programs.addons import ADDONS
from src.ui_elements import Ui_AddonManager
from src.utils import restart_program

_logger = LoggerHandler("AddonManager")
_GITHUB_ADDON_SOURCE = "https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry-Addons/main/addon_data.json"
_NOT_SET = "Not Set"


@dataclass
class _AddonData:
    name: str = _NOT_SET
    description: str = _NOT_SET
    url: str = _NOT_SET
    file_name: str = ""
    installed: bool = False
    official: bool = True

    def __post_init__(self):
        if self.file_name:
            return
        self.file_name = self.url.rsplit("/", maxsplit=1)[-1]


class AddonManager(QMainWindow, Ui_AddonManager):
    """Creates A window to display addon GUI for the user."""

    def __init__(self, parent=None):
        """Initialize the object."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        # connects all the buttons
        self.button_back.clicked.connect(self.close)
        self.button_apply.clicked.connect(self._apply_changes)
        self._installed_addons = ADDONS.addons
        self._addon_information = self._generate_addon_information()
        self._gui_addons: dict[str, QTableWidgetItem] = {}
        self._fill_addon_list()

        UI_LANGUAGE.adjust_addon_manager(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _fill_addon_list(self):
        """Fill the addon list widget with all the addon data."""
        self.table_addons.setRowCount(len(self._addon_information))
        self.table_addons.setColumnCount(1)
        for i, addon in enumerate(self._addon_information):
            content = f"{addon.name} ({addon.file_name})\n{addon.description}"
            description_cell = QTableWidgetItem(content)
            # if its an official addon, add checkable box to the left
            if addon.official:
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

    def _generate_addon_information(self):
        """Get all the addon data from source and locally installed ones, build the data objects."""
        # get the addon data from the source
        # This should provide name, description and url
        official_addons: list[_AddonData] = []
        try:
            req = requests.get(_GITHUB_ADDON_SOURCE, allow_redirects=True, timeout=5)
            if req.ok:
                gh_data = json.loads(req.text)
                official_addons = [_AddonData(**data) for data in gh_data]
        except ReqConnectionError:
            _logger.log_event("WARNING", "Could not fetch addon data from source, is there an internet connection?")

        # Check if the addon is installed
        low_case_installed_addons = [x.lower() for x in self._installed_addons]
        for addon in official_addons:
            if addon.name.lower() in low_case_installed_addons:
                addon.installed = True

        possible_addons = official_addons
        # also add local addons, which are not official ones to the list
        for local_addon_name, addon_class in self._installed_addons.items():
            if local_addon_name.lower() not in [a.name.lower() for a in possible_addons]:
                file_name = f"{addon_class.__module__.split('.')[-1]}.py"
                possible_addons.append(
                    _AddonData(
                        local_addon_name,
                        "Installed addon is not in the list of official addons. Please manage over file system.",
                        file_name,
                        file_name,
                        True,
                        False,
                    )
                )
        return possible_addons

    def _apply_changes(self):
        # First apply all the user checked settings
        for addon in self._addon_information:
            # ignore unofficial addons here
            if not addon.official:
                continue
            user_say_installed = self._gui_addons[addon.name].checkState() == Qt.Checked  # type: ignore
            addon.installed = user_say_installed
            addon_file = ADDON_FOLDER / addon.file_name
            # Download from source if user did check
            # Also overwrite current files, so new version of the addons will be fetched
            if addon.installed:
                self._install_addon(addon, addon_file)
            # remove or ignore (if not exists) if its not checked
            else:
                addon_file.unlink(missing_ok=True)

        # Ask to restart
        if DP_CONTROLLER.ask_to_restart_for_config():
            restart_program()

    def _install_addon(self, addon: _AddonData, addon_file: Path):
        """Try to install addon, log if req is not ok or no connection."""
        try:
            req = requests.get(addon.url, allow_redirects=True, timeout=5)
            if req.ok:
                addon_file.write_bytes(req.content)
            else:
                _logger.log_event(
                    "ERROR", f"Could not get {addon.name} from {addon.url}: {req.status_code} {req.reason}"
                )
        except ReqConnectionError:
            _logger.log_event("ERROR", f"Could not get {addon.name} from {addon.url}: No internet connection")
