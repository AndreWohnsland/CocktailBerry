from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import time

from ui_elements.bonusingredient import Ui_addingredient

from src.supporter import plusminus
from src.display_handler import DisplayHandler
from src.display_controller import DisplayController
from src.database_commander import DatabaseCommander
from src.rpi_controller import RpiController
from src.bottles import set_fill_level_bars

DP_HANDLER = DisplayHandler()
DB_COMMANDER = DatabaseCommander()
RPI_CONTROLLER = RpiController()
DP_CONTROLLER = DisplayController()


class GetIngredientWindow(QDialog, Ui_addingredient):
    """ Creates a Dialog to chose an additional ingredient and the amount
    to spend this ingredient.
    """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons and get values for the Combobox. """
        super(GetIngredientWindow, self).__init__(parent)
        self.setupUi(self)
        # Set window properties
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint |
                            Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon(parent.icon_path))
        self.mainscreen = parent
        if not self.mainscreen.DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
        # Connect all the buttons
        self.PBplus.clicked.connect(lambda: plusminus(self.LAmount, "+", 20, 100, 10))
        self.PBminus.clicked.connect(lambda: plusminus(self.LAmount, "-", 20, 100, 10))
        self.PBAusgeben.clicked.connect(self.ausgeben_clicked)
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        bottles = DB_COMMANDER.get_ingredients_at_bottles_without_empty_ones()
        DP_HANDLER.fill_single_combobox(self.CBingredient, bottles, first_empty=False)

    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def ausgeben_clicked(self):
        """ Calls the Progressbarwindow and spends the given amount of the ingredient. """
        import globalvars

        globalvars.make_cocktail = True
        ingredient_name, volume = DP_CONTROLLER.get_data_ingredient_window(self)
        bottle, level = DB_COMMANDER.get_ingredient_bottle_and_level_by_name(ingredient_name)
        print(f"Ausgabemenge von {self.CBingredient.currentText()}: {volume}")

        self.close()
        if volume > level:
            DP_HANDLER.standard_box(f"{ingredient_name} hat nicht genug Volumen! {level}/{volume} ml vorhanden.")
            self.mainscreen.tabWidget.setCurrentIndex(3)
            return

        volume, _, _ = RPI_CONTROLLER.make_cocktail(
            self.mainscreen, [bottle], [volume], labelchange="Zutat wird ausgegeben!\nFortschritt:")
        DB_COMMANDER.set_ingredient_consumption(ingredient_name, volume[0])
        set_fill_level_bars(self.mainscreen)
        self.mainscreen.prow_close()
