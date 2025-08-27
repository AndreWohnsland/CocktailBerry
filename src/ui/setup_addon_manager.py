from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow, QPushButton

from src.dialog_handler import DIALOG_HANDLER, UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.models import AddonData
from src.programs.addons import ADDONS, CouldNotInstallAddonError
from src.ui.creation_utils import SMALL_FONT, create_button, create_label
from src.ui_elements import Ui_AddonManager

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
        self._installed_addons = ADDONS.addons
        self._addon_information = ADDONS.get_addon_data()
        self._fill_addon_list()

        UI_LANGUAGE.adjust_addon_manager(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _fill_addon_list(self) -> None:
        """Fill the gridLayout_2 with all the addon data, using action buttons and text."""
        while self.gridLayout_2.count():
            item = self.gridLayout_2.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for i, addon in enumerate(self._addon_information):
            if addon.installed and addon.official and not addon.is_installable:
                btn = create_button("Remove", font_size=16, max_w=150, css_class="btn-inverted destructive")
                btn.clicked.connect(lambda _, a=addon, b=btn, c=i: self._remove_addon(a, b, c))
            elif addon.official and addon.is_installable:
                btn = create_button("Install", font_size=16, max_w=150, css_class="btn-inverted")
                btn.clicked.connect(lambda _, a=addon, b=btn, c=i: self._install_addon(a, b, c))
            else:
                if addon.disabled:
                    text = "Disabled"
                elif not addon.official:
                    text = "Unofficial"
                else:
                    text = f"needs {addon.minimal_version}+"
                btn = create_button(text, font_size=16, max_w=150, css_class="neutral btn-inverted")
                btn.setEnabled(False)

            self.gridLayout_2.addWidget(btn, i, 0)
            content = f"{addon.name} ({addon.file_name})\n{addon.description}"
            label = create_label(content, SMALL_FONT)
            label.setWordWrap(True)
            self.gridLayout_2.addWidget(label, i, 1)

    def _install_addon(self, addon: AddonData, btn: QPushButton, pos: int) -> None:
        """Try to install addon, log if req is not ok or no connection."""
        try:
            ADDONS.install_addon(addon)
            DIALOG_HANDLER.standard_box("Addon installed successfully", "Success")
            btn.deleteLater()
            btn = create_button("Remove", font_size=16, max_w=200, css_class="btn-inverted destructive")
            btn.clicked.connect(lambda _, a=addon, b=btn, c=pos: self._remove_addon(a, b, c))
            self.gridLayout_2.addWidget(btn, pos, 0)
        except CouldNotInstallAddonError as e:
            _logger.log_event("ERROR", str(e))

    def _remove_addon(self, addon: AddonData, btn: QPushButton, pos: int) -> None:
        """Try to remove addon, log if req is not ok or no connection."""
        if not DIALOG_HANDLER.user_okay(f"Are you sure you want to remove this addon: {addon.name}?"):
            return
        ADDONS.remove_addon(addon)
        DIALOG_HANDLER.standard_box("Addon removed successfully", "Success")
        btn.deleteLater()
        btn = create_button("Install", font_size=16, max_w=200, css_class="btn-inverted")
        btn.clicked.connect(lambda _, a=addon, b=btn, c=pos: self._install_addon(a, b, c))
        self.gridLayout_2.addWidget(btn, pos, 0)
