from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow, QLineEdit

from src.ui_elements import Ui_SearchWindow

from src.models import Cocktail
from src.display_controller import DP_CONTROLLER, ItemDelegate
from src.database_commander import DB_COMMANDER
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.dialog_handler import UI_LANGUAGE

if TYPE_CHECKING:
    from src.ui.setup_cocktail_selection import CocktailSelection


class SearchWindow(QMainWindow, Ui_SearchWindow):
    """ Class for the Progress screen during Cocktail making. """

    def __init__(self, parent, available_cocktails: list[Cocktail], cocktail_selection: CocktailSelection):
        super().__init__()
        self.setupUi(self)
        self.cocktail_selection = cocktail_selection
        self.available_cocktails = available_cocktails
        self.list_widget_cocktails.setItemDelegate(ItemDelegate(self))
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)
        self.button_enter.clicked.connect(self.enter_search)
        self.input_cocktail.clicked.connect(lambda: self._open_keyboard(self.input_cocktail))
        self.input_cocktail.textChanged.connect(self._apply_search_to_list)
        self.mainscreen = parent
        UI_LANGUAGE.adjust_search_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
        DP_CONTROLLER.fill_list_widget(self.list_widget_cocktails, available_cocktails)

    def enter_search(self):
        """ Enters the search into the main window"""
        search = DP_CONTROLLER.get_list_widget_selection(self.list_widget_cocktails)
        if search:
            cocktail = DB_COMMANDER.get_cocktail(search)
            if cocktail is None:
                return
            self.cocktail_selection.set_cocktail(cocktail)
            self.cocktail_selection.update_cocktail_data()
        self.close()

    def _open_keyboard(self, le_to_write: QLineEdit, max_char_len: int = 64):
        """ Opens up the keyboard connected to the lineedit """
        self.keyboard_window = KeyboardWidget(self.mainscreen, le_to_write=le_to_write, max_char_len=max_char_len)

    def _apply_search_to_list(self):
        """ Applies the search to the list widget"""
        search = self.input_cocktail.text()
        DP_CONTROLLER.clear_list_widget(self.list_widget_cocktails)
        # if the search is empty, just fill all possible cocktails
        if not search:
            DP_CONTROLLER.fill_list_widget(self.list_widget_cocktails, self.available_cocktails)
            return
        # else, search for the cocktails
        search = search.lower()
        to_fill = []
        for cocktail in self.available_cocktails:
            # also search if any of the ingredient match search
            ingredient_match = any(search in ing.name.lower() for ing in cocktail.ingredients)
            if search in cocktail.name.lower() or ingredient_match:
                to_fill.append(cocktail)
        DP_CONTROLLER.fill_list_widget(self.list_widget_cocktails, to_fill)
