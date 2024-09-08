from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE
from src.models import Ingredient
from src.tabs.bottles import set_fill_level_bars
from src.ui_elements.bonusingredient import Ui_addingredient
from src.utils import time_print

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("additional_ingredient")


class GetIngredientWindow(QMainWindow, Ui_addingredient):
    """Create a Dialog to chose an additional ingredient and the amount to spend this ingredient."""

    def __init__(self, parent: MainScreen):
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
        _, level = DB_COMMANDER.get_ingredient_bottle_and_level_by_name(ingredient_name)
        ingredient_data: Ingredient = DB_COMMANDER.get_ingredient(ingredient_name)  # type: ignore
        # need to set amount, otherwise it will be 0
        ingredient_data.amount = volume

        self.close()
        if volume > level and cfg.MAKER_CHECK_BOTTLE:
            DP_CONTROLLER.say_not_enough_ingredient_volume(ingredient_name, level, volume)
            if cfg.UI_MAKER_PASSWORD == 0 or not cfg.UI_LOCKED_TABS[2]:
                DP_CONTROLLER.set_tabwidget_tab(self.mainscreen, "bottles")
            return

        time_print(f"Spending {volume} ml {ingredient_name}")
        made_volume, _, _ = MACHINE.make_cocktail(self.mainscreen, [ingredient_data], ingredient_name, False)
        consumed_volume = made_volume[0]
        DB_COMMANDER.increment_ingredient_consumption(ingredient_name, consumed_volume)
        set_fill_level_bars(self.mainscreen)
        volume_string = f"{consumed_volume} ml"
        _logger.log_event("INFO", f"{volume_string:6} | {ingredient_name}")
