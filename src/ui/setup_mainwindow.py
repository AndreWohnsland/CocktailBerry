"""Connects all the functions to the Buttons as well the Lists
of the passed window. Also defines the Mode for controls.
"""
# pylint: disable=unnecessary-lambda
import sys
import platform
from pathlib import Path
from typing import Optional
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtWidgets import QMainWindow, QLineEdit

from src.config_manager import CONFIG as cfg
from src.machine.controller import MACHINE
from src.tabs import maker, ingredients, recipes, bottles
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.logger_handler import LoggerHandler
from src.ui.setup_option_window import OptionWindow
from src.updater import Updater
from src.utils import has_connection

from src.ui_elements.cocktailmanager import Ui_MainWindow
from src.ui.setup_progress_screen import ProgressScreen
from src.ui.setup_numpad_widget import NumpadWidget
from src.ui.setup_bottle_window import BottleWindow
from src.ui.setup_get_ingredients_window import GetIngredientWindow
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui.setup_handadd_widget import HandaddWidget
from src.ui.setup_available_window import AvailableWindow
from src.ui.setup_team_window import TeamScreen
from src.ui.setup_datepicker import DatePicker
from src.ui.icons import ICONS

from src import FUTURE_PYTHON_VERSION


class MainScreen(QMainWindow, Ui_MainWindow):
    """ Creates the Mainscreen. """

    def __init__(self):
        """ Init the main window. Many of the button and List connects are in pass_setup. """
        super().__init__()
        self.setupUi(self)
        # Get the basic Logger
        self.logger = LoggerHandler("cocktail_application")
        self.logger.log_start_program()
        self.connect_objects()
        self.connect_other_windows()
        self.icon_path = str(Path(__file__).parents[1].absolute() / "ui_elements" / "Cocktail-icon.png")
        self.setWindowIcon(QIcon(self.icon_path))
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        DP_CONTROLLER.inject_stylesheet(self)
        # init the empty further screens
        self.numpad_window: Optional[NumpadWidget] = None
        self.keyboard_window: Optional[KeyboardWidget] = None
        self.progress_window: Optional[ProgressScreen] = None
        self.bottle_window: Optional[BottleWindow] = None
        self.ingredient_window: Optional[GetIngredientWindow] = None
        self.handadd_window: Optional[HandaddWidget] = None
        self.available_window: Optional[AvailableWindow] = None
        self.team_window: Optional[TeamScreen] = None
        self.option_window: Optional[OptionWindow] = None
        self.datepicker: Optional[DatePicker] = None
        UI_LANGUAGE.adjust_mainwindow(self)
        MACHINE.set_up_pumps()
        self.showFullScreen()
        # as long as its not UI_DEVENVIRONMENT (usually touchscreen) hide the cursor
        DP_CONTROLLER.set_display_settings(self)
        DP_CONTROLLER.set_tab_width(self)
        ICONS.set_mainwindow_icons(self)
        self.update_check()
        self._connection_check()
        self._deprecation_check()

    def update_check(self):
        """Checks if there is an update and asks to update, if exists"""
        if not cfg.MAKER_SEARCH_UPDATES:
            return
        updater = Updater()
        update_available, info = updater.check_for_updates()
        if not update_available:
            return
        if DP_CONTROLLER.ask_to_update():
            updater.update()

    def _connection_check(self):
        """Checks if there is an internet connection
        Asks user to adjust time, if there is no no connection
        """
        # only needed if microservice is also active
        if not cfg.MAKER_CHECK_INTERNET or not cfg.MICROSERVICE_ACTIVE:
            return
        # Also first check if there is no connection b4 using this
        if has_connection():
            return
        # And also asks the user if he want to adjust the time
        if DP_CONTROLLER.ask_to_adjust_time():
            self.datepicker = DatePicker()

    def _deprecation_check(self):
        """Checks if to display the deprecation warning for newer python version install"""
        sys_python = sys.version_info
        if FUTURE_PYTHON_VERSION > sys_python:
            DP_CONTROLLER.say_python_deprecated(
                platform.python_version(),
                f"{FUTURE_PYTHON_VERSION[0]}.{FUTURE_PYTHON_VERSION[1]}"
            )

    def open_numpad(self, le_to_write: QLineEdit, x_pos=0, y_pos=0, header_text="Password"):
        """ Opens up the NumpadWidget connected to the lineedit offset from the left upper side """
        self.numpad_window = NumpadWidget(self, le_to_write, x_pos, y_pos, header_text)

    def open_keyboard(self, le_to_write, max_char_len=30):
        """ Opens up the keyboard connected to the lineedit """
        self.keyboard_window = KeyboardWidget(self, le_to_write=le_to_write, max_char_len=max_char_len)

    def open_progression_window(self, cocktail_type: str = "Cocktail"):
        """ Opens up the progression window to show the Cocktail status. """
        self.progress_window = ProgressScreen(self, cocktail_type)

    def change_progression_window(self, pb_value):
        """ Changes the value of the progression bar of the ProBarWindow. """
        if self.progress_window is None:
            return
        self.progress_window.progressBar.setValue(pb_value)

    def close_progression_window(self):
        """ Closes the progression window at the end of the cycle. """
        if self.progress_window is None:
            return
        self.progress_window.close()

    def open_team_window(self):
        self.team_window = TeamScreen(self)
        # don't abstract .exec_() into class otherwise you will get NameError in class!
        self.team_window.exec_()

    def open_option_window(self):
        """Opens up the options"""
        if not DP_CONTROLLER.password_prompt():
            return
        self.option_window = OptionWindow(self)

    def open_bottle_window(self):
        """ Opens the bottle window to change the volume levels. """
        self.bottle_window = BottleWindow(self)

    def open_ingredient_window(self):
        """ Opens a window to spend one single ingredient. """
        self.ingredient_window = GetIngredientWindow(self)

    def open_handadd_window(self):
        """ Opens a window to enter additional ingredients added by hand. """
        self.handadd_window = HandaddWidget(self)

    def open_available_window(self):
        self.available_window = AvailableWindow(self)

    def connect_other_windows(self):
        """Links the buttons and lineedits to the other ui elements"""
        self.LECocktail.clicked.connect(lambda: self.open_keyboard(self.LECocktail))
        self.option_button.clicked.connect(self.open_option_window)
        alcohol = UI_LANGUAGE.generate_numpad_header("alcohol")
        self.LEGehaltRezept.clicked.connect(
            lambda: self.open_numpad(self.LEGehaltRezept, 50, 50, alcohol)
        )
        self.LEZutatRezept.clicked.connect(lambda: self.open_keyboard(self.LEZutatRezept, max_char_len=20))
        self.LEKommentar.clicked.connect(self.open_handadd_window)
        self.PBAvailable.clicked.connect(self.open_available_window)
        # connects all the Lineedits from the Recipe amount and gives them the validator
        amount = UI_LANGUAGE.generate_numpad_header("amount")
        for obj in DP_CONTROLLER.get_lineedits_recipe(self):
            obj.clicked.connect(lambda o=obj: self.open_numpad(o, 50, 50, amount))  # type: ignore
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
        # First, connect all the push buttons with the Functions
        self.PBZutathinzu.clicked.connect(lambda: ingredients.handle_enter_ingredient(self))
        self.PBRezepthinzu.clicked.connect(lambda: recipes.handle_enter_recipe(self))
        self.PBBelegung.clicked.connect(self.open_bottle_window)
        self.PBZeinzelnd.clicked.connect(self.open_ingredient_window)
        self.PBclear.clicked.connect(lambda: DP_CONTROLLER.clear_recipe_data_recipes(self, False))
        self.PBdelete.clicked.connect(lambda: recipes.delete_recipe(self))
        self.PBZdelete.clicked.connect(lambda: ingredients.delete_ingredient(self))
        self.PBZclear.clicked.connect(lambda: ingredients.clear_ingredient_information(self))
        self.prepare_button.clicked.connect(lambda: maker.prepare_cocktail(self))
        self.PBFlanwenden.clicked.connect(lambda: bottles.renew_checked_bottles(self))
        self.PBZplus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.LEFlaschenvolumen, 500, 1500, 50))
        self.PBZminus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.LEFlaschenvolumen, 500, 1500, -50))

        self.increase_volume.clicked.connect(lambda: maker.adjust_volume(self, 25))
        self.decrease_volume.clicked.connect(lambda: maker.adjust_volume(self, -25))
        self.increase_alcohol.clicked.connect(lambda: maker.adjust_alcohol(self, 0.15))
        self.decrease_alcohol.clicked.connect(lambda: maker.adjust_alcohol(self, -0.15))
        self.PBenable.clicked.connect(lambda: recipes.enable_all_recipes(self))

        # Connect the Lists with the Functions
        self.LWZutaten.itemSelectionChanged.connect(lambda: ingredients.display_selected_ingredient(self))
        self.LWMaker.itemSelectionChanged.connect(lambda: maker.update_shown_recipe(self))
        self.LWRezepte.itemSelectionChanged.connect(lambda: recipes.load_selected_recipe_data(self))

        # Connects the virgin checkbox
        self.virgin_checkbox.stateChanged.connect(lambda: maker.update_shown_recipe(self, False))

        # Protect other tabs with password in party mode
        if cfg.UI_PARTYMODE:
            self.tabWidget.currentChanged.connect(self.handle_tab_bar_clicked)

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
        # Load combo buttons Recipes
        recipes.fill_recipe_box_with_ingredients(self)
        # Load combo buttons Bottles
        bottles.calculate_combobox_bottles(self)
        # Load current Bottles into the combo buttons
        bottles.read_in_bottles(self)
        # Load Existing Recipes from DB into Recipe List
        recipes.load_recipe_view_names(self)
        # Load Possible Recipes Into Maker List
        maker.evaluate_recipe_maker_view(self)
        # Load the Progressbar
        bottles.set_fill_level_bars(self)

        for combobox in DP_CONTROLLER.get_comboboxes_bottles(self):
            combobox.activated.connect(lambda _, window=self: bottles.refresh_bottle_cb(w=window))

    def handle_tab_bar_clicked(self, index):
        """Protects tabs other than maker tab with a password"""
        if index == 0:
            return
        if DP_CONTROLLER.password_prompt():
            return
        # Set back to 1st tab if password not right
        self.tabWidget.setCurrentIndex(0)
