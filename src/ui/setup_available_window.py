from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QListWidget, QMainWindow

from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.available import Ui_available

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class AvailableWindow(QMainWindow, Ui_available):
    """Opens a window where the user can select all available ingredients."""

    def __init__(self, parent: "MainScreen") -> None:
        super().__init__()
        self.setupUi(self)
        self.mainscreen = parent
        DP_CONTROLLER.initialize_window_object(self)
        # somehow the ui don't accept without _2 for those two buttons so they are _2
        self.PBAbbruch_2.clicked.connect(self._cancel_click)
        self.PBOk_2.clicked.connect(self._accepted_clicked)
        self.PBAdd.clicked.connect(lambda: self._change_ingredient(self.LWVorhanden, self.LWAlle))
        self.PBRemove.clicked.connect(lambda: self._change_ingredient(self.LWAlle, self.LWVorhanden))
        # gets the available ingredients out of the DB and assigns them to the LW
        ingredient_available = DB_COMMANDER.get_available_ingredient_names()
        ingredients = DB_COMMANDER.get_all_ingredients()
        entry_list = list({x.name for x in ingredients} - set(ingredient_available))
        DP_CONTROLLER.fill_list_widget(self.LWVorhanden, ingredient_available)
        DP_CONTROLLER.fill_list_widget(self.LWAlle, entry_list)
        UI_LANGUAGE.adjust_available_windows(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _cancel_click(self) -> None:
        """Close the window without any further action."""
        self.close()

    def _accepted_clicked(self) -> None:
        """Write the new availability into the DB."""
        DB_COMMANDER.delete_existing_handadd_ingredient()
        ingredient_names = [
            self.LWVorhanden.item(i).text()  # ty:ignore[possibly-missing-attribute] # pyright: ignore[reportOptionalMemberAccess]
            for i in range(self.LWVorhanden.count())
        ]
        # only add ingredients if there are any
        if ingredient_names:
            DB_COMMANDER.insert_multiple_existing_handadd_ingredients(ingredient_names)
        # reloads the maker screen and updates the shown available recipes
        DP_CONTROLLER.update_maker_view(self.mainscreen)
        self.close()

    def _change_ingredient(self, lw_to_add: QListWidget, lw_removed: QListWidget) -> None:
        if not lw_removed.selectedItems():
            return

        ingredient_names = [x.text() for x in lw_removed.selectedItems()]
        lw_to_add.addItems(ingredient_names)

        for ingredient in ingredient_names:
            DP_CONTROLLER.delete_list_widget_item(lw_removed, ingredient)
        DP_CONTROLLER.unselect_list_widget_items(lw_removed)
