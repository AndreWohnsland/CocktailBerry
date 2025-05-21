from typing import TYPE_CHECKING, Callable, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.programs.addons import ADDONS
from src.ui.creation_utils import MEDIUM_FONT, adjust_font, create_button
from src.ui.setup_addon_manager import AddonManager
from src.ui_elements import Ui_Addonwindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class AddonWindow(QMainWindow, Ui_Addonwindow):
    """Creates A window to display addon GUI for the user."""

    def __init__(self, parent: MainScreen) -> None:
        """Initialize the object."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        self.addon_manager: Optional[AddonManager] = None
        # connects all the buttons
        self.button_back.clicked.connect(self.close)
        self.button_manage.clicked.connect(self._open_manager)
        self.selection_addon.activated.connect(self._set_up_addon_gui)
        DP_CONTROLLER.fill_single_combobox(self.selection_addon, list(ADDONS.addons.keys()), first_empty=False)
        self._set_up_addon_gui()

        UI_LANGUAGE.adjust_addon_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _set_up_addon_gui(self) -> None:
        addon_name = self.selection_addon.currentText()
        # If there is no addon, there will be not text.
        if not addon_name:
            return
        # first need to clean old elements for layout
        layout = self.addon_container
        DP_CONTROLLER.delete_items_of_layout(layout)
        # build the custom gui
        gui_provided = ADDONS.build_addon_gui(
            addon_name,
            self.addon_container,
            self._button_generator,
        )
        # informs the user if the addon got no gui
        if not gui_provided:
            info = UI_LANGUAGE.get_no_addon_gui_info()
            label = QLabel(info, self)
            adjust_font(label, MEDIUM_FONT)
            label.setAlignment(Qt.AlignCenter)  # type: ignore
            self.addon_container.addWidget(label)

    def _button_generator(self, label: str, func: Callable[[], None]) -> None:
        button = create_button(label, self)
        button.clicked.connect(func)
        self.addon_container.addWidget(button)

    def _open_manager(self) -> None:
        self.addon_manager = AddonManager(self.mainscreen)
