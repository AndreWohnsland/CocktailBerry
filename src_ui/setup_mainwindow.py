"""Connects all the functions to the Buttons as well the Lists
of the passed window. Also defines the Mode for controls.
"""
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow

from config.config_manager import ConfigManager
from src.maker import *
from src.ingredients import *
from src.recipes import *
from src.bottles import *
from src.bottles import set_fill_level_bars
from src.supporter import plusminus, generate_lineedit_recipes, generate_CBB_names
from src.save_handler import SaveHandler
from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander
from src.logger_handler import LoggerHandler
from src_ui.setup_team_window import TeamScreen

from ui_elements.Cocktailmanager_2 import Ui_MainWindow
from src_ui.setup_progress_screen import ProgressScreen
from src_ui.setup_password_screen import PasswordScreen
from src_ui.setup_bottle_window import BottleWindow
from src_ui.setup_get_ingredients_window import GetIngredientWindow
from src_ui.setup_keyboard_widget import KeyboardWidget
from src_ui.setup_handadd_widget import HandaddWidget
from src_ui.setup_avialable_window import AvailableWindow

SAVE_HANDLER = SaveHandler()
DP_HANDLER = DisplayHandler()
DB_COMMANDER = DatabaseCommander()


class MainScreen(QMainWindow, Ui_MainWindow, ConfigManager):
    """ Creates the Mainscreen. """

    def __init__(self, parent=None):
        """ Init. Many of the button and List connects are in pass_setup. """
        super(MainScreen, self).__init__(parent)
        self.setupUi(self)
        self.handaddlist = []
        # Get the basic Logger
        self.logger_handler = LoggerHandler("cocktail_application", "production_logs")
        self.logger_handler.log_start_program()
        self.connect_objects()
        self.connect_other_windows()
        self.icon_path = os.path.join(os.path.dirname(__file__), "..", "ui_elements", "Cocktail-icon.png")
        # as long as its not DEVENVIRONMENT (usually touchscreen) hide the cursor
        if not self.DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
        # Code for hide the curser. Still experimental!
        # for count in range(1,10):
        # 	CBSname = getattr(self, "CBB" + str(count))
        # 	CBSname.setCursor(Qt.BlankCursor)
        # init the empty further screens
        self.pww: PasswordScreen = None
        self.kbw: KeyboardWidget = None
        self.prow: ProgressScreen = None
        self.botw: BottleWindow = None
        self.ingd: GetIngredientWindow = None
        self.handw: HandaddWidget = None
        self.availw: AvailableWindow = None
        self.teamw: TeamScreen = None

    def passwordwindow(self, le_to_write, x_pos=0, y_pos=0, headertext=None):
        """ Opens up the PasswordScreen connected to the lineedit offset from the left upper side """
        self.pww = PasswordScreen(self, x_pos=x_pos, y_pos=y_pos, le_to_write=le_to_write)
        if headertext is not None:
            self.pww.setWindowTitle(headertext)
        self.pww.show()

    def keyboard(self, le_to_write, headertext=None, max_char_len=30):
        """ Opens up the Keyboard connected to the lineedit """
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

    def teamwindow(self):
        self.teamw = TeamScreen(self)
        self.teamw.exec_()

    def prow_change(self, pbvalue):
        """ Changes the value of the Progressionbar of the ProBarWindow. """
        self.prow.progressBar.setValue(pbvalue)

    def prow_close(self):
        """ Closes the Progressionwindow at the end of the cyclus. """
        self.prow.close()

    def bottleswindow(self):
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
            handadd_data = DB_COMMANDER.get_recipe_handadd_window_properties(self.LWRezepte.currentItem().text())
            self.handaddlist.extend([list(x) for x in handadd_data])
        self.handw = HandaddWidget(self)
        self.handw.show()

    def availablewindow(self):
        self.availw = AvailableWindow(self)
        self.availw.showFullScreen()

    def connect_other_windows(self):
        """Links the buttons and lineedits to the other ui elements"""
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
        for obj in generate_lineedit_recipes(self):
            obj.clicked.connect(lambda o=obj: self.passwordwindow(
                le_to_write=o, x_pos=400, y_pos=50, headertext="Zutatenmenge eingeben!",))
            obj.setValidator(QIntValidator(0, 300))
            obj.setMaxLength(3)
        # Setting up Validators for all the the fields (length and/or Types):
        self.LEGehaltRezept.setValidator(QIntValidator(0, 99))
        self.LEGehaltRezept.setMaxLength(2)
        self.LEZutatRezept.setMaxLength(20)
        self.LEFlaschenvolumen.setValidator(QIntValidator(100, 2000))
        self.LECocktail.setMaxLength(30)

    def connect_objects(self):
        """ Connect all the functions with the Buttons. """
        # First, connect all the Pushbuttons with the Functions
        self.PBZutathinzu.clicked.connect(lambda: enter_ingredient(self))
        self.PBRezepthinzu.clicked.connect(lambda: enter_recipe(self, True))
        self.PBBelegung.clicked.connect(lambda: customlevels(self))
        self.PBZeinzelnd.clicked.connect(lambda: custom_ingredient_output(self))
        self.PBclear.clicked.connect(lambda: DP_HANDLER.clear_recipe_data_recipes(self, False))
        self.PBRezeptaktualisieren.clicked.connect(lambda: enter_recipe(self, False))
        self.PBdelete.clicked.connect(lambda: delete_recipe(self))
        self.PBZdelete.clicked.connect(lambda: delete_ingredient(self))
        self.PBZclear.clicked.connect(lambda: clear_ingredient_information(self))
        self.PBZaktualisieren.clicked.connect(lambda: enter_ingredient(self, False))
        self.PBZubereiten_custom.clicked.connect(lambda: prepare_cocktail(self))
        self.PBCleanMachine.clicked.connect(lambda: clean_machine(self))
        self.PBFlanwenden.clicked.connect(lambda: renew_checked_bottles(self))
        self.PBZplus.clicked.connect(lambda: plusminus(self.LEFlaschenvolumen, "+", 500, 1500, 50))
        self.PBZminus.clicked.connect(lambda: plusminus(self.LEFlaschenvolumen, "-", 500, 1500, 50))
        self.PBMplus.clicked.connect(lambda: plusminus(self.LCustomMenge, "+", 100, 400, 25))
        self.PBMminus.clicked.connect(lambda: plusminus(self.LCustomMenge, "-", 100, 400, 25))
        self.PBSetnull.clicked.connect(lambda: reset_alcohollevel(self))
        self.PBZnull.clicked.connect(lambda: SAVE_HANDLER.export_ingredients(self))
        self.PBRnull.clicked.connect(lambda: SAVE_HANDLER.export_recipes(self))
        self.PBenable.clicked.connect(lambda: enableall_recipes(self))

        # Connect the Lists with the Functions
        self.LWZutaten.itemClicked.connect(lambda: display_selected_ingredient(self))
        self.LWZutaten.currentTextChanged.connect(lambda: display_selected_ingredient(self))
        self.LWMaker.itemClicked.connect(lambda: updated_clicked_recipe_maker(self))
        self.LWMaker.currentTextChanged.connect(lambda: updated_clicked_recipe_maker(self))
        self.LWRezepte.itemClicked.connect(lambda: load_selected_recipe_data(self))
        self.LWRezepte.currentTextChanged.connect(lambda: load_selected_recipe_data(self))

        # Connects the slider
        self.HSIntensity.valueChanged.connect(lambda: handle_alcohollevel_change(self))

        # Disable some of the Tabs (for the PARTYMODE, no one can access the recipes)
        if self.PARTYMODE:
            self.tabWidget.setTabEnabled(2, False)

        # gets the bottle ingredients into the global list
        get_bottle_ingredients()
        # Clear Help Marker
        DP_HANDLER.clear_recipe_data_maker(self)
        # Load ingredients
        load_ingredients(self)
        # Load Bottles into the Labels
        refresh_bottle_information(self)
        # Load Combobuttons Recipes
        fill_recipe_box_with_ingredients(self)
        # Load Combobuttons Bottles
        calculate_combobox_bottles(self)
        # Load current Bottles into the Combobuttons
        read_in_bottles(self)
        # Load Existing Recipes from DB into Recipe List
        update_recipe_view(self)
        # Load Possible Recipes Into Maker List
        refresh_recipe_maker_view(self)
        # Load the Progressbar
        set_fill_level_bars(self)

        for combobox in generate_CBB_names(self):
            combobox.activated.connect(lambda _, window=self: refresh_bottle_cb(w=window))
