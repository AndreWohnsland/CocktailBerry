from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow


from src.ui_elements.available import Ui_available
from src.maker import evaluate_recipe_maker_view
from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE


class AvailableWindow(QMainWindow, Ui_available):
    """ Opens a window where the user can select all available ingredients. """

    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.mainscreen = parent
        # somehow the ui dont accept without _2 for those two buttons so they are _2
        self.PBAbbruch_2.clicked.connect(self.abbrechen_clicked)
        self.PBOk_2.clicked.connect(self.accepted_clicked)
        self.PBAdd.clicked.connect(lambda: self.changeingredient(self.LWVorhanden, self.LWAlle))
        self.PBRemove.clicked.connect(lambda: self.changeingredient(self.LWAlle, self.LWVorhanden))
        # gets the available ingredients out of the DB and assigns them to the LW
        ingredient_available = DB_COMMANDER.get_available_ingredient_names()
        ingredients = DB_COMMANDER.get_all_ingredients()
        entrylist = list({x.name for x in ingredients} - set(ingredient_available))
        DP_CONTROLLER.fill_list_widget(self.LWVorhanden, ingredient_available)
        DP_CONTROLLER.fill_list_widget(self.LWAlle, entrylist)
        UI_LANGUAGE.adjust_available_windos(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def abbrechen_clicked(self):
        """ Closes the window without any furter action. """
        self.close()

    def accepted_clicked(self):
        """ Writes the new availibility into the DB. """
        DB_COMMANDER.delete_existing_handadd_ingredient()
        ingredient_names = [self.LWVorhanden.item(i).text() for i in range(self.LWVorhanden.count())]
        DB_COMMANDER.insert_multiple_existing_handadd_ingredients_by_name(ingredient_names)
        # reloads the maker screen and updates the shown available recipes
        self.mainscreen.LWMaker.clear()
        evaluate_recipe_maker_view(self.mainscreen)
        DP_CONTROLLER.clear_recipe_data_maker(self.mainscreen)
        self.close()

    def changeingredient(self, lwadd, lwremove):
        if not lwremove.selectedItems():
            return

        ingredientname = lwremove.currentItem().text()
        lwadd.addItem(ingredientname)
        DP_CONTROLLER.delete_list_widget_item(lwremove, ingredientname)
        DP_CONTROLLER.unselect_list_widget_items(lwremove)
