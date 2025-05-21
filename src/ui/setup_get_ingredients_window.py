from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.models import Cocktail, PrepareResult
from src.tabs import maker
from src.tabs.bottles import set_fill_level_bars
from src.ui_elements.bonusingredient import Ui_addingredient

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class GetIngredientWindow(QMainWindow, Ui_addingredient):
    """Create a Dialog to chose an additional ingredient and the amount to spend this ingredient."""

    def __init__(self, parent: MainScreen) -> None:
        """Init. Connects all the buttons and get values for the Combobox."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        # Connect all the buttons
        volume_step = 10
        max_volume = 300
        self.PBplus.clicked.connect(
            lambda: DP_CONTROLLER.change_input_value(self.LAmount, volume_step, max_volume, volume_step)
        )
        self.PBminus.clicked.connect(
            lambda: DP_CONTROLLER.change_input_value(self.LAmount, volume_step, max_volume, -volume_step)
        )
        self.PBAusgeben.clicked.connect(self._spend_clicked)
        self.PBAbbrechen.clicked.connect(self._cancel_clicked)
        all_bottles = DB_COMMANDER.get_ingredient_names_at_bottles()
        bottles = [x for x in all_bottles if x != ""]
        DP_CONTROLLER.fill_list_widget(self.ingredient_selection, bottles)
        self.ingredient_selection.setCurrentRow(0)
        UI_LANGUAGE.adjust_bonusingredient_screen(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _cancel_clicked(self):
        """Close the Window without a change."""
        self.close()

    def _spend_clicked(self):
        """Call the progress bar window and spends the given amount of the ingredient."""
        ingredient_name, volume = DP_CONTROLLER.get_ingredient_window_data(self)
        # if there is nothing selected, just do nothing
        if ingredient_name == "":
            return
        ingredient = DB_COMMANDER.get_ingredient(ingredient_name)
        if ingredient is None:
            return
        # need to set amount, otherwise it will be 0
        ingredient.amount = volume

        cocktail = Cocktail(0, ingredient_name, 0, volume, True, True, [ingredient])
        result, message, _ = maker.validate_cocktail(cocktail)
        self.close()

        # Go to refill dialog, if this window is not locked
        if (result == PrepareResult.NOT_ENOUGH_INGREDIENTS) and (
            cfg.UI_MAKER_PASSWORD == 0 or not cfg.UI_LOCKED_TABS[2]
        ):
            self.mainscreen.open_refill_dialog(cocktail)
            return

        # No special case: just show the message
        if result != PrepareResult.VALIDATION_OK:
            DP_CONTROLLER.standard_box(message, close_time=60)
            return

        maker.prepare_ingredient(ingredient, self.mainscreen)
        set_fill_level_bars(self.mainscreen)
