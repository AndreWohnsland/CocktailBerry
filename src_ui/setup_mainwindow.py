""" Connects all the functions to the Buttons as well the Lists 
of the passed window. Also defines the Mode for controls. 
"""
import sys
import sqlite3
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import string

import globals
from src.maker import *
from src.ingredients import *
from src.recipes import *
from src.bottles import *
from src.bottles import Belegung_progressbar
from config.config_manager import ConfigManager
from src.supporter import plusminus
from src.save_handler import SaveHandler
from src.display_handler import DisplayHandler

from ui_elements.Cocktailmanager_2 import Ui_MainWindow

from src_ui.setup_progress_screen import ProgressScreen
from src_ui.setup_password_screen import PasswordScreen
from src_ui.setup_bottle_window import BottleWindow
from src_ui.setup_get_ingredients_window import GetIngredientWindow
from src_ui.setup_keyboard_widget import KeyboardWidget
from src_ui.setup_handadd_widget import HandaddWidget
from src_ui.setup_avialable_window import AvailableWindow

save_handler = SaveHandler()
display_handler = DisplayHandler()


class MainScreen(QMainWindow, Ui_MainWindow, ConfigManager):
    """ Creates the Mainscreen. """

    def __init__(self, devenvironment, DB=None, parent=None):
        """ Init. Many of the button and List connects are in pass_setup. """
        super(MainScreen, self).__init__(parent)
        self.setupUi(self)
        # as long as its not devenvironment (usually touchscreen) hide the cursor
        if not self.DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
        self.devenvironment = self.DEVENVIRONMENT
        # connect to the DB, if one is given (you should always give one!)
        if DB is not None:
            self.DB = sqlite3.connect(DB)
            self.c = self.DB.cursor()
        self.handaddlist = []
        # the connection method here is defined in a seperate file "clickablelineedit.py"
        # even if it belongs to the UI if its moved there, there will be an import error.
        # Till this problem is resolved, this file will stay in the main directory
        self.LEpw.clicked.connect(lambda: self.passwordwindow(self.LEpw))
        self.LEpw2.clicked.connect(lambda: self.passwordwindow(self.LEpw2))
        self.LECleanMachine.clicked.connect(lambda: self.passwordwindow(self.LECleanMachine))
        self.LECocktail.clicked.connect(lambda: self.keyboard(self.LECocktail))
        self.LEGehaltRezept.clicked.connect(
            lambda: self.passwordwindow(self.LEGehaltRezept, y_pos=50, headertext="Alkoholgehalt eingeben!")
        )
        self.LEZutatRezept.clicked.connect(lambda: self.keyboard(self.LEZutatRezept, max_char_len=20))
        self.LEKommentar.clicked.connect(self.handwindow)
        self.PBAvailable.clicked.connect(self.availablewindow)
        # connects all the Lineedits from the Recipe amount and gives them the validator
        LER_obj = [getattr(self, "LER" + str(x)) for x in range(1, 9)]
        for obj in LER_obj:
            obj.clicked.connect(lambda o=obj: self.passwordwindow(le_to_write=o, x_pos=400, y_pos=50, headertext="Zutatenmenge eingeben!",))
            obj.setValidator(QIntValidator(0, 300))
            obj.setMaxLength(3)
        # Setting up Validators for all the the fields (length and/or Types):
        self.LEGehaltRezept.setValidator(QIntValidator(0, 99))
        self.LEGehaltRezept.setMaxLength(2)
        self.LEZutatRezept.setMaxLength(20)
        self.LEFlaschenvolumen.setValidator(QIntValidator(100, 2000))
        self.LECocktail.setMaxLength(30)

    def passwordwindow(self, le_to_write, x_pos=0, y_pos=0, headertext=None):
        """ Opens up the PasswordScreen/ a Numpad to enter Numeric Values (no commas!). 
        Needs a Lineedit where the text is put in. In addition, the header of the window can be changed. 
        This is only relevant if you dont show the window in Fullscreen!
        In addition, if its not fullscreen, the postion of the upper left edge can be set in x- and y-direction.
        """
        self.pww = PasswordScreen(self, x_pos=x_pos, y_pos=y_pos, le_to_write=le_to_write)
        if headertext is not None:
            self.pww.setWindowTitle(headertext)
        self.pww.show()

    def keyboard(self, le_to_write, headertext=None, max_char_len=30):
        """ Opens up the Keyboard to seperate Enter a Name or similar.
        Needs a Lineedit where the text is put in. In addition, the header of the window can be changed. 
        This is only relevant if you dont show the window in Fullscreen!
        """
        self.kbw = KeyboardWidget(self, le_to_write=le_to_write, max_char_len=max_char_len)
        if headertext is not None:
            self.kbw.setWindowTitle(headertext)
        self.kbw.showFullScreen()

    def progressionqwindow(self, labelchange=""):
        """ Opens up the progressionwindow to show the Cocktail status. """
        self.prow = ProgressScreen(self)
        if labelchange:
            self.prow.Lheader.setText(labelchange)
        self.prow.show()

    def prow_change(self, pbvalue):
        """ Changes the value of the Progressionbar of the ProBarWindow. """
        self.prow.progressBar.setValue(pbvalue)

    def prow_close(self):
        """ Closes the Progressionwindow at the end of the cyclus. """
        self.prow.close()

    def bottleswindow(self, bot_names=[], vol_values=[]):
        """ Opens the bottlewindow to change the volumelevels. """
        self.botw = BottleWindow(self)
        self.botw.show()

    def ingredientdialog(self):
        """ Opens a window to spend one single ingredient. """
        self.ingd = GetIngredientWindow(self)
        self.ingd.show()

    def handwindow(self):
        """ Opens a window to enter additional ingrediends added by hand. """
        if self.LWRezepte.selectedItems() and self.handaddlist == []:
            storeval = self.c.execute(
                "SELECT Z.Zutaten_ID, Z.Menge, Z.Alkoholisch FROM Zusammen AS Z INNER JOIN Rezepte AS R ON R.ID=Z.Rezept_ID WHERE R.Name = ? AND Z.Hand=1",
                (self.LWRezepte.currentItem().text(),),
            )
            for row in storeval:
                self.handaddlist.append(list(row))
        self.handw = HandaddWidget(self)
        self.handw.show()

    def availablewindow(self):
        self.availw = AvailableWindow(self)
        self.availw.showFullScreen()


def pass_setup(w, DB, c, PARTYMODE, devenvironment):
    """ Connect all the functions with the Buttons. """
    # First, connect all the Pushbuttons with the Functions
    w.PBZutathinzu.clicked.connect(lambda: enter_ingredient(w))
    w.PBRezepthinzu.clicked.connect(lambda: Rezept_eintragen(w, True))
    w.PBBelegung.clicked.connect(lambda: customlevels(w))
    w.PBZeinzelnd.clicked.connect(lambda: custom_output(w))
    w.PBclear.clicked.connect(lambda: Rezepte_clear(w, False))
    w.PBRezeptaktualisieren.clicked.connect(lambda: Rezept_eintragen(w, False))
    w.PBdelete.clicked.connect(lambda: Rezepte_delete(w))
    w.PBZdelete.clicked.connect(lambda: Zutaten_delete(w))
    w.PBZclear.clicked.connect(lambda: Zutaten_clear(w))
    w.PBZaktualisieren.clicked.connect(lambda: enter_ingredient(w, False))
    w.PBZubereiten_custom.clicked.connect(lambda: Maker_Zubereiten(w))
    w.PBCleanMachine.clicked.connect(lambda: CleanMachine(w))
    w.PBFlanwenden.clicked.connect(lambda: Belegung_Flanwenden(w))
    w.PBZplus.clicked.connect(lambda: plusminus(w.LEFlaschenvolumen, "+", 500, 1500, 50))
    w.PBZminus.clicked.connect(lambda: plusminus(w.LEFlaschenvolumen, "-", 500, 1500, 50))
    w.PBMplus.clicked.connect(lambda: plusminus(w.LCustomMenge, "+", 100, 400, 25))
    w.PBMminus.clicked.connect(lambda: plusminus(w.LCustomMenge, "-", 100, 400, 25))
    w.PBSetnull.clicked.connect(lambda: Maker_nullProB(w))
    w.PBZnull.clicked.connect(lambda: save_handler.export_ingredients(w))
    w.PBRnull.clicked.connect(lambda: save_handler.export_recipes(w))
    w.PBenable.clicked.connect(lambda: enableall(w))

    # Connect the Lists with the Functions
    w.LWZutaten.itemClicked.connect(lambda: Zutaten_Zutaten_click(w))
    w.LWZutaten.currentTextChanged.connect(lambda: Zutaten_Zutaten_click(w))
    w.LWMaker.itemClicked.connect(lambda: Maker_Rezepte_click(w))
    w.LWMaker.currentTextChanged.connect(lambda: Maker_Rezepte_click(w))
    w.LWRezepte.itemClicked.connect(lambda: Rezepte_Rezepte_click(w))
    w.LWRezepte.currentTextChanged.connect(lambda: Rezepte_Rezepte_click(w))

    # Connects the slider
    w.HSIntensity.valueChanged.connect(lambda: Maker_ProB_change(w))

    # Disable some of the Tabs (for the PARTYMODE, no one can access the recipes)
    if PARTYMODE:
        w.tabWidget.setTabEnabled(2, False)

    # gets the bottle ingredients into the global list
    get_bottle_ingredients(w)
    # Clear Help Marker
    Maker_List_null(w)
    # Load ingredients
    Zutaten_a(w)
    # Load Bottles into the Labels
    Belegung_a(w)
    # Load Combobuttons Recipes
    ZutatenCB_Rezepte(w)
    # Load Combobuttons Bottles
    newCB_Bottles(w)
    # Load current Bottles into the Combobuttons
    Belegung_einlesen(w)
    # Load Existing Recipes from DB into Recipe List
    Rezepte_a_R(w)
    # Load Possible Recipes Into Maker List
    Rezepte_a_M(w)
    # Load the Progressbar
    Belegung_progressbar(w)

    for combobox in [getattr(w, "CBB" + str(x)) for x in range(1, 11)]:
        combobox.activated.connect(lambda _, window=w: refresh_bottle_cb(w=window))
