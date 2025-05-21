from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.models import Ingredient
from src.tabs import bottles
from src.ui_elements import Ui_RefillPrompt

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class RefillDialog(QMainWindow, Ui_RefillPrompt):
    """Class for the Team selection Screen."""

    def __init__(self, parent: MainScreen, ingredient: Ingredient) -> None:
        """Initialize the RefillDialog."""
        super().__init__()
        self.setupUi(self)
        self.main_window = parent
        self.ingredient = ingredient
        DP_CONTROLLER.initialize_window_object(self)
        self.button_later.clicked.connect(self.close)
        self.button_to_bottles.clicked.connect(self._go_to_bottle_tab)
        self.button_apply.clicked.connect(self.apply_refill)
        self.checkbox_done.stateChanged.connect(self.checkbox_done_changed)

        UI_LANGUAGE.adjust_refill_prompt(self, ingredient.name, ingredient.bottle_volume, ingredient.amount)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def apply_refill(self):
        """Apply the refill to the bottle."""
        # usually, the bottle have to be set, otherwise we would not be at this window
        self.close()
        if self.ingredient.bottle is not None:
            bottles.renew_bottles(self.main_window, [self.ingredient.bottle])

    def checkbox_done_changed(self):
        """Only enables the apply button if the checkbox is checked."""
        self.button_apply.setEnabled(self.checkbox_done.isChecked())

    def _go_to_bottle_tab(self):
        """Switch to the bottle tab."""
        DP_CONTROLLER.set_tabwidget_tab(self.main_window, "bottles")
        self.close()
