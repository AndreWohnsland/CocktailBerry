from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import time

from ui_elements.bonusingredient import Ui_addingredient

from src.supporter import plusminus
from src.display_handler import DisplayHandler
from src.display_controler import DisplayControler
from src.database_commander import DatabaseCommander
from src.rpi_controller import RpiController
from src.bottles import Belegung_progressbar

display_handler = DisplayHandler()
database_commander = DatabaseCommander()
rpi_controller = RpiController()
display_controler = DisplayControler()


class GetIngredientWindow(QDialog, Ui_addingredient):
    """ Creates a Dialog to chose an additional ingredient and the amount
    to spend this ingredient.
    """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons and get values for the Combobox. """
        super(GetIngredientWindow, self).__init__(parent)
        self.setupUi(self)
        # Set window properties
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon(parent.icon_path))
        self.ms = parent
        if not self.ms.DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
        # Connect all the buttons
        self.PBplus.clicked.connect(lambda: plusminus(self.LAmount, "+", 20, 100, 10))
        self.PBminus.clicked.connect(lambda: plusminus(self.LAmount, "-", 20, 100, 10))
        self.PBAusgeben.clicked.connect(self.ausgeben_clicked)
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        # Get the DB and fill Combobox
        self.DB = self.ms.DB
        self.c = self.ms.c
        bottles = database_commander.get_ingredients_at_bottles_without_empty_ones()
        display_handler.fill_single_combobox(self.CBingredient, bottles, first_empty=False)

    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def ausgeben_clicked(self):
        """ Calls the Progressbarwindow and spends the given amount of the ingredient. """
        import globals

        globals.loopcheck = True
        ingredient_name, volume = display_controler.get_data_ingredient_window(self)
        bottle, level = database_commander.get_ingredient_bottle_and_level_by_name(ingredient_name)
        print(f"Ausgabemenge von {self.CBingredient.currentText()}: {volume}")

        self.close()
        if volume > level:
            display_handler.standard_box(f"{ingredient_name} hat nicht genug Volumen! {level}/{volume} ml vorhanden.")
            self.ms.tabWidget.setCurrentIndex(3)
            return

        volume, _, _ = rpi_controller.make_cocktail(self.ms, [bottle], [volume], labelchange="Zutat wird ausgegeben!\nFortschritt:")
        database_commander.set_ingredient_consumption(ingredient_name, volume[0])
        Belegung_progressbar(self.ms)
        self.ms.prow_close()
