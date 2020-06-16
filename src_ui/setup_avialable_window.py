from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from ui_elements.available import Ui_available
from src.maker import Maker_List_null, Rezepte_a_M
from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander

display_handler = DisplayHandler()
database_commander = DatabaseCommander()


class AvailableWindow(QMainWindow, Ui_available):
    """ Opens a window where the user can select all available ingredients. """

    def __init__(self, parent):
        super(AvailableWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ms = parent
        # somehow the ui dont accept without _2 for those two buttons so they are _2
        self.PBAbbruch_2.clicked.connect(self.abbrechen_clicked)
        self.PBOk_2.clicked.connect(self.accepted_clicked)
        self.PBAdd.clicked.connect(lambda: self.changeingredient(self.LWVorhanden, self.LWAlle))
        self.PBRemove.clicked.connect(lambda: self.changeingredient(self.LWAlle, self.LWVorhanden))
        # gets the available ingredients out of the DB and assigns them to the LW
        ingredient_available = database_commander.get_available_ingredient_names()
        ingredient_all = database_commander.get_ingredient_names()
        entrylist = list(set(ingredient_all) - set(ingredient_available))
        display_handler.fill_list_widget(self.LWVorhanden, ingredient_available)
        display_handler.fill_list_widget(self.LWAlle, entrylist)

    def abbrechen_clicked(self):
        """ Closes the window without any furter action. """
        self.close()

    def accepted_clicked(self):
        """ Writes the new availibility into the DB. """
        database_commander.delete_existing_handadd_ingredient()
        ingredient_names = [self.LWVorhanden.item(i).text() for i in range(self.LWVorhanden.count())]
        database_commander.insert_multiple_existing_handadd_ingredients_by_name(ingredient_names)
        # reloads the maker screen and updates the shown available recipes
        self.ms.LWMaker.clear()
        Rezepte_a_M(self.ms)
        Maker_List_null(self.ms)
        self.close()

    def changeingredient(self, lwadd, lwremove):
        if not lwremove.selectedItems():
            return

        ingredientname = lwremove.currentItem().text()
        lwadd.addItem(ingredientname)
        display_handler.delete_list_widget_item(lwremove, ingredientname)
        display_handler.unselect_list_widget_items(lwremove)
