from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from ui_elements.available import Ui_available
from src.maker import Maker_List_null, Rezepte_a_M


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
        cursor_buffer = self.ms.c.execute("SELECT Z.Name FROM Zutaten AS Z INNER JOIN Vorhanden AS V ON V.ID = Z.ID")
        ingredient_available = []
        for name in cursor_buffer:
            self.LWVorhanden.addItem(name[0])
            ingredient_available.append(name[0])
        # gets the names of all ingredients out of the DB calculates the not used ones and assigns them to the LW
        cursor_buffer = self.ms.c.execute("SELECT Name FROM Zutaten")
        ingredient_all = []
        for name in cursor_buffer:
            ingredient_all.append(name[0])
        entrylist = list(set(ingredient_all) - set(ingredient_available))
        for name in entrylist:
            self.LWAlle.addItem(name)
        # generates two list for values to remove and add from the db when the accept button is clicked
        # self.add_db = []
        # self.remove_db = []

    def abbrechen_clicked(self):
        """ Closes the window without any furter action. """
        self.close()

    def accepted_clicked(self):
        """ Writes the new availibility into the DB. """
        self.ms.c.execute("DELETE FROM Vorhanden")
        for i in range(self.LWVorhanden.count()):
            ing_id = self.ms.c.execute("SELECT ID FROM Zutaten WHERE Name=?", (self.LWVorhanden.item(i).text(),),).fetchone()[0]
            self.ms.c.execute("INSERT OR IGNORE INTO Vorhanden(ID) VALUES(?)", (ing_id,))
        self.ms.DB.commit()
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
        delfind = lwremove.findItems(ingredientname, Qt.MatchExactly)
        if len(delfind) > 0:
            for item in delfind:
                lwremove.takeItem(lwremove.row(item))
        for i in range(lwremove.count()):
            lwremove.item(i).setSelected(False)
