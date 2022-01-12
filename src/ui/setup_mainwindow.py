"""Connects all the functions to the Buttons as well the Lists
of the passed window. Also defines the Mode for controls.
"""
import os
from typing import Union
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtWidgets import QMainWindow

from src.config_manager import ConfigManager
from src import maker
from src import ingredients
from src import recipes
from src import bottles
from src.save_handler import SAVE_HANDLER
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.logger_handler import LoggerHandler
from src.updater import Updater

from src.ui_elements.Cocktailmanager_2 import Ui_MainWindow
from src.ui.setup_progress_screen import ProgressScreen
from src.ui.setup_password_screen import PasswordScreen
from src.ui.setup_bottle_window import BottleWindow
from src.ui.setup_get_ingredients_window import GetIngredientWindow
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui.setup_handadd_widget import HandaddWidget
from src.ui.setup_avialable_window import AvailableWindow
from src.ui.setup_team_window import TeamScreen


class MainScreen(QMainWindow, Ui_MainWindow, ConfigManager):
    """ Creates the Mainscreen. """

    def __init__(self):
        """ Init the main window. Many of the button and List connects are in pass_setup. """
        super().__init__()
        ConfigManager.__init__(self)
        self.setupUi(self)
        # Get the basic Logger
        self.logger_handler = LoggerHandler("cocktail_application", "production_logs")
        self.logger_handler.log_start_program()
        self.connect_objects()
        self.connect_other_windows()
        self.icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "ui_elements", "Cocktail-icon.png")
        self.setWindowIcon(QIcon(self.icon_path))
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        # init the empty further screens
        self.pww: Union[PasswordScreen, None] = None
        self.kbw: Union[KeyboardWidget, None] = None
        self.prow: Union[ProgressScreen, None] = None
        self.botw: Union[BottleWindow, None] = None
        self.ingd: Union[GetIngredientWindow, None] = None
        self.handw: Union[HandaddWidget, None] = None
        self.availw: Union[AvailableWindow, None] = None
        self.teamw: Union[TeamScreen, None] = None
        UI_LANGUAGE.adjust_mainwindow(self)
        self.showFullScreen()
        # as long as its not UI_DEVENVIRONMENT (usually touchscreen) hide the cursor
        DP_CONTROLLER.set_display_settings(self)
        DP_CONTROLLER.set_tab_width(self)
        self.update_check()

    def update_check(self):
        if not self.MAKER_SEARCH_UPDATES:
            return
        updater = Updater()
        if not updater.check_for_updates():
            return
        if DP_CONTROLLER.ask_to_update():
            updater.update()

    def passwordwindow(self, le_to_write, x_pos=0, y_pos=0, headertext="Password"):
        """ Opens up the PasswordScreen connected to the lineedit offset from the left upper side """
        self.pww = PasswordScreen(self, x_pos, y_pos, le_to_write, headertext)

    def keyboard(self, le_to_write, max_char_len=30):
        """ Opens up the Keyboard connected to the lineedit """
        self.kbw = KeyboardWidget(self, le_to_write=le_to_write, max_char_len=max_char_len)

    def progressionqwindow(self, cocktail_type: str = "Cocktail"):
        """ Opens up the progressionwindow to show the Cocktail status. """
        self.prow = ProgressScreen(self, cocktail_type)

    def teamwindow(self):
        self.teamw = TeamScreen(self)
        # don't abstract .exec_() into class otherwise you will get NameError in class!
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

    def ingredientdialog(self):
        """ Opens a window to spend one single ingredient. """
        self.ingd = GetIngredientWindow(self)

    def handwindow(self):
        """ Opens a window to enter additional ingrediends added by hand. """
        self.handw = HandaddWidget(self)

    def availablewindow(self):
        self.availw = AvailableWindow(self)

    def connect_other_windows(self):
        """Links the buttons and lineedits to the other ui elements"""
        password = UI_LANGUAGE.generate_password_header("password")
        self.LEpw.clicked.connect(lambda: self.passwordwindow(self.LEpw, 50, 50, password))
        self.LEpw2.clicked.connect(lambda: self.passwordwindow(self.LEpw2, 50, 50, password))
        self.LECleanMachine.clicked.connect(lambda: self.passwordwindow(self.LECleanMachine, 50, 50, password))
        self.LECocktail.clicked.connect(lambda: self.keyboard(self.LECocktail))
        alcohol = UI_LANGUAGE.generate_password_header("alcohol")
        self.LEGehaltRezept.clicked.connect(
            lambda: self.passwordwindow(self.LEGehaltRezept, 50, 50, alcohol)
        )
        self.LEZutatRezept.clicked.connect(lambda: self.keyboard(self.LEZutatRezept, max_char_len=20))
        self.LEKommentar.clicked.connect(self.handwindow)
        self.PBAvailable.clicked.connect(self.availablewindow)
        # connects all the Lineedits from the Recipe amount and gives them the validator
        amount = UI_LANGUAGE.generate_password_header("amount")
        for obj in DP_CONTROLLER.get_lineedits_recipe(self):
            obj.clicked.connect(lambda o=obj: self.passwordwindow(o, 50, 50, amount))
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
        self.PBZutathinzu.clicked.connect(lambda: ingredients.enter_ingredient(self))
        self.PBRezepthinzu.clicked.connect(lambda: recipes.enter_recipe(self, True))
        self.PBBelegung.clicked.connect(self.bottleswindow)
        self.PBZeinzelnd.clicked.connect(self.ingredientdialog)
        self.PBclear.clicked.connect(lambda: DP_CONTROLLER.clear_recipe_data_recipes(self, False))
        self.PBRezeptaktualisieren.clicked.connect(lambda: recipes.enter_recipe(self, False))
        self.PBdelete.clicked.connect(lambda: recipes.delete_recipe(self))
        self.PBZdelete.clicked.connect(lambda: ingredients.delete_ingredient(self))
        self.PBZclear.clicked.connect(lambda: ingredients.clear_ingredient_information(self))
        self.PBZaktualisieren.clicked.connect(lambda: ingredients.enter_ingredient(self, False))
        self.PBZubereiten_custom.clicked.connect(lambda: maker.prepare_cocktail(self))
        self.PBCleanMachine.clicked.connect(lambda: bottles.clean_machine(self))
        self.PBFlanwenden.clicked.connect(lambda: bottles.renew_checked_bottles(self))
        self.PBZplus.clicked.connect(lambda: DP_CONTROLLER.plusminus(self.LEFlaschenvolumen, "+", 500, 1500, 50))
        self.PBZminus.clicked.connect(lambda: DP_CONTROLLER.plusminus(self.LEFlaschenvolumen, "-", 500, 1500, 50))
        self.PBMplus.clicked.connect(lambda: DP_CONTROLLER.plusminus(
            self.LCustomMenge, "+", 100, 400, 25, lambda: maker.update_shown_recipe(self)))
        self.PBMminus.clicked.connect(lambda: DP_CONTROLLER.plusminus(
            self.LCustomMenge, "-", 100, 400, 25, lambda: maker.update_shown_recipe(self)))
        self.PBSetnull.clicked.connect(lambda: DP_CONTROLLER.reset_alcohol_slider(self))
        self.PBZnull.clicked.connect(lambda: SAVE_HANDLER.export_ingredients(self))
        self.PBRnull.clicked.connect(lambda: SAVE_HANDLER.export_recipes(self))
        self.PBenable.clicked.connect(lambda: recipes.enableall_recipes(self))

        # Connect the Lists with the Functions
        self.LWZutaten.itemClicked.connect(lambda: ingredients.display_selected_ingredient(self))
        self.LWZutaten.currentTextChanged.connect(lambda: ingredients.display_selected_ingredient(self))
        self.LWMaker.itemClicked.connect(lambda: maker.update_shown_recipe(self))
        self.LWMaker.currentTextChanged.connect(lambda: maker.update_shown_recipe(self))
        self.LWRezepte.itemClicked.connect(lambda: recipes.load_selected_recipe_data(self))
        self.LWRezepte.currentTextChanged.connect(lambda: recipes.load_selected_recipe_data(self))

        # Connects the slider
        self.HSIntensity.valueChanged.connect(lambda: maker.update_shown_recipe(self))

        # Disable some of the Tabs (for the UI_PARTYMODE, no one can access the recipes)
        if self.UI_PARTYMODE:
            self.tabWidget.setTabEnabled(2, False)

        # Removes the elements not used depending on number of bottles in bottle tab
        # This also does adjust DB inserting data, since in the not used bottles may a ingredient be registered
        DP_CONTROLLER.adjust_bottle_number_displayed(self)
        DP_CONTROLLER.adjust_maker_label_size_cocktaildata(self)

        # gets the bottle ingredients into the global list
        bottles.get_bottle_ingredients()
        # Clear Help Marker
        DP_CONTROLLER.clear_recipe_data_maker(self)
        # Load ingredients
        ingredients.load_ingredients(self)
        # Load Bottles into the Labels
        bottles.refresh_bottle_information(self)
        # Load Combobuttons Recipes
        recipes.fill_recipe_box_with_ingredients(self)
        # Load Combobuttons Bottles
        bottles.calculate_combobox_bottles(self)
        # Load current Bottles into the Combobuttons
        bottles.read_in_bottles(self)
        # Load Existing Recipes from DB into Recipe List
        recipes.load_recipe_view_names(self)
        # Load Possible Recipes Into Maker List
        maker.evaluate_recipe_maker_view(self)
        # Load the Progressbar
        bottles.set_fill_level_bars(self)

        for combobox in DP_CONTROLLER.get_comboboxes_bottles(self):
            combobox.activated.connect(lambda _, window=self: bottles.refresh_bottle_cb(w=window))
