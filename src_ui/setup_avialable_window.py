from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow


from ui_elements.available import Ui_available
from src.maker import refresh_recipe_maker_view
from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander

DP_HANDLER = DisplayHandler()
DB_COMMANDER = DatabaseCommander()


class AvailableWindow(QMainWindow, Ui_available):
    """ Opens a window where the user can select all available ingredients. """

    def __init__(self, parent):
        super(AvailableWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.mainscreen = parent
        # somehow the ui dont accept without _2 for those two buttons so they are _2
        self.PBAbbruch_2.clicked.connect(self.abbrechen_clicked)
        self.PBOk_2.clicked.connect(self.accepted_clicked)
        self.PBAdd.clicked.connect(lambda: self.changeingredient(self.LWVorhanden, self.LWAlle))
        self.PBRemove.clicked.connect(lambda: self.changeingredient(self.LWAlle, self.LWVorhanden))
        # gets the available ingredients out of the DB and assigns them to the LW
        ingredient_available = DB_COMMANDER.get_available_ingredient_names()
        ingredient_all = DB_COMMANDER.get_ingredient_names()
        entrylist = list(set(ingredient_all) - set(ingredient_available))
        DP_HANDLER.fill_list_widget(self.LWVorhanden, ingredient_available)
        DP_HANDLER.fill_list_widget(self.LWAlle, entrylist)

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
        refresh_recipe_maker_view(self.mainscreen)
        DP_HANDLER.clear_recipe_data_maker(self.mainscreen)
        self.close()

    def changeingredient(self, lwadd, lwremove):
        if not lwremove.selectedItems():
            return

        ingredientname = lwremove.currentItem().text()
        lwadd.addItem(ingredientname)
        DP_HANDLER.delete_list_widget_item(lwremove, ingredientname)
        DP_HANDLER.unselect_list_widget_items(lwremove)
