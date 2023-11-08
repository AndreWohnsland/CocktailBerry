from __future__ import annotations
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QDialog
from src.models import Ingredient

from src.ui_elements.bonusingredient import Ui_addingredient

from src.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from src.machine.controller import MACHINE
from src.tabs.bottles import set_fill_level_bars
from src.dialog_handler import UI_LANGUAGE
from src.utils import time_print

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("additional_ingredient")


class GetIngredientWindow(QDialog, Ui_addingredient):
    """ Creates a Dialog to chose an additional ingredient and the amount
    to spend this ingredient.
    """

    def __init__(self, parent: MainScreen):
        """ Init. Connects all the buttons and get values for the Combobox. """
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        # Connect all the buttons
        self.PBplus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.LAmount, 10, 100, 10))
        self.PBminus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.LAmount, 10, 100, -10))
        self.PBAusgeben.clicked.connect(self._spend_clicked)
        self.PBAbbrechen.clicked.connect(self._cancel_clicked)
        all_bottles = DB_COMMANDER.get_ingredients_at_bottles()
        bottles = [x for x in all_bottles if x != ""]
        DP_CONTROLLER.fill_list_widget(self.ingredient_selection, bottles)
        self.ingredient_selection.setCurrentRow(0)
        UI_LANGUAGE.adjust_bonusingredient_screen(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _cancel_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def _spend_clicked(self):
        """ Calls the progress bar window and spends the given amount of the ingredient. """
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
            if cfg.UI_MAKER_PASSWORD == 0:
                DP_CONTROLLER.set_tabwidget_tab(self.mainscreen, "bottles")
            return

        time_print(f"Spending {volume} ml {ingredient_name}")
        made_volume, _, _ = MACHINE.make_cocktail(self.mainscreen, [ingredient_data], ingredient_name, False)
        DB_COMMANDER.increment_ingredient_consumption(ingredient_name, made_volume[0])
        set_fill_level_bars(self.mainscreen)
        volume_string = f"{volume} ml"
        _logger.log_event("INFO", f"{volume_string:6} | {ingredient_name}")
