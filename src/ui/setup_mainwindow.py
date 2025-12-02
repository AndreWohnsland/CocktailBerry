"""Connect all the functions to the Buttons as well the Lists of the passed window.

Also defines the Mode for controls.
"""

# pylint: disable=unnecessary-lambda
import platform
from typing import Any, Optional

from PyQt5.QtCore import QEventLoop
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QLineEdit, QMainWindow

from src import FUTURE_PYTHON_VERSION
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import Tab
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER, ItemDelegate
from src.logger_handler import LoggerHandler
from src.models import Cocktail
from src.programs.addons import ADDONS
from src.programs.nfc_payment_service import NFCPaymentService
from src.startup_checks import can_update, connection_okay, is_python_deprecated
from src.tabs import bottles, ingredients, recipes
from src.ui.cocktail_view import CocktailView
from src.ui.icons import BUTTON_SIZE, IconSetter
from src.ui.setup_available_window import AvailableWindow
from src.ui.setup_bottle_window import BottleWindow
from src.ui.setup_cocktail_selection import CocktailSelection
from src.ui.setup_datepicker import DatePicker
from src.ui.setup_get_ingredients_window import GetIngredientWindow
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui.setup_numpad_widget import NumpadWidget
from src.ui.setup_option_window import OptionWindow
from src.ui.setup_picture_window import PictureWindow
from src.ui.setup_progress_screen import ProgressScreen
from src.ui.setup_refill_dialog import RefillDialog
from src.ui.setup_team_window import TeamScreen
from src.ui_elements import Ui_MainWindow
from src.updater import Updater


class MainScreen(QMainWindow, Ui_MainWindow):
    """Creates the Mainscreen."""

    def __init__(self) -> None:
        """Init the main window. Many of the button and List connects are in pass_setup."""
        super().__init__()
        self.setupUi(self)

        # Get the basic Logger
        self.logger = LoggerHandler("CocktailBerry")
        self.logger.log_start_program()

        # limit bottles to 24 for this QT app (web can handle any number)
        cfg.MAKER_NUMBER_BOTTLES = min(cfg.MAKER_NUMBER_BOTTLES, 24)

        # Removes the elements not used depending on number of bottles in bottle tab
        # This also does adjust DB inserting data, since in the not used bottles may a ingredient be registered
        DP_CONTROLLER.adjust_bottle_number_displayed(self)

        # init the empty further screens
        self.numpad_window: Optional[NumpadWidget] = None
        self.keyboard_window: Optional[KeyboardWidget] = None
        self.progress_window: Optional[ProgressScreen] = None
        self.bottle_window: Optional[BottleWindow] = None
        self.ingredient_window: Optional[GetIngredientWindow] = None
        self.available_window: Optional[AvailableWindow] = None
        self.team_window: Optional[TeamScreen] = None
        self.option_window: Optional[OptionWindow] = None
        self.datepicker: Optional[DatePicker] = None
        self.picture_window: Optional[PictureWindow] = None
        self.refill_dialog: Optional[RefillDialog] = None
        self.cocktail_view = CocktailView(self)
        # building the fist page as a stacked widget
        # this is quite similar to the tab widget, but we don't need the tabs
        self.cocktail_selection: Optional[CocktailSelection] = None
        if cfg.PAYMENT_ACTIVE:
            NFCPaymentService().start_continuous_sensing()
        self.cocktail_view.populate_cocktails()
        self.container_maker.addWidget(self.cocktail_view)

        # if maker tab is locked, we need to start with another tab
        if cfg.UI_LOCKED_TABS[Tab.MAKER] and cfg.UI_MAKER_PASSWORD != 0:
            self.tabWidget.setCurrentIndex(0)
        # keep track of previous index for index changed signal,
        # we need this because the signal does not emit the previous index
        self.previous_tab_index = self.tabWidget.currentIndex()
        # also keep a list of available cocktails for search in cocktails
        self.available_cocktails = DB_COMMANDER.get_possible_cocktails(cfg.MAKER_MAX_HAND_INGREDIENTS)
        self._apply_search_to_list()

        # internal initialization
        self.connect_objects()
        self.connect_other_windows()
        DP_CONTROLLER.initialize_window_object(self)

        UI_LANGUAGE.adjust_mainwindow(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
        DP_CONTROLLER.set_tab_width(self)
        icons = IconSetter()
        icons.set_mainwindow_icons(self)
        DP_CONTROLLER.say_welcome_message()
        self.update_check()
        self._deprecation_check()
        self._connection_check()
        ADDONS.start_trigger_loop(self)

    def update_check(self) -> None:
        """Check if there is an update and asks to update, if exists."""
        update_available, info = can_update()
        if not update_available:
            return
        if not DP_CONTROLLER.ask_to_update(info):
            return
        updater = Updater()
        success = updater.update()
        if not success:
            DP_CONTROLLER.say_update_failed()

    def _connection_check(self) -> None:
        """Check if there is an internet connection.

        Asks user to adjust time, if there is no no connection.
        """
        if connection_okay():
            return
        # Asks the user if he want to adjust the time
        if DP_CONTROLLER.ask_to_adjust_time():
            self.datepicker = DatePicker(self)

    def _deprecation_check(self) -> None:
        """Check if to display the deprecation warning for newer python version install."""
        if is_python_deprecated():
            DP_CONTROLLER.say_python_deprecated(
                platform.python_version(), f"{FUTURE_PYTHON_VERSION[0]}.{FUTURE_PYTHON_VERSION[1]}"
            )

    def open_cocktail_detail(self, cocktail: Cocktail) -> None:
        """Open the cocktail selection screen."""
        if self.cocktail_selection is not None:
            # Clean up all internal layouts and widgets recursively
            DP_CONTROLLER.delete_items_of_layout(self.cocktail_selection.layout())
            # Remove from stacked widget
            self.container_maker.removeWidget(self.cocktail_selection)
            # Schedule for deletion and remove reference
            self.cocktail_selection.deleteLater()
            self.cocktail_selection = None
        self.cocktail_selection = CocktailSelection(self, cocktail)
        self.container_maker.addWidget(self.cocktail_selection)
        self.cocktail_selection.set_cocktail(cocktail)
        self.cocktail_selection.update_cocktail_data()
        self.switch_to_cocktail_detail()

    def switch_to_cocktail_detail(self) -> None:
        if self.cocktail_selection is None:
            return
        if cfg.PAYMENT_ACTIVE:
            NFCPaymentService().clear_callback()
        self.container_maker.setCurrentWidget(self.cocktail_selection)

    def switch_to_cocktail_list(self) -> None:
        self.container_maker.setCurrentWidget(self.cocktail_view)
        if cfg.PAYMENT_ACTIVE:
            NFCPaymentService().add_callback(self.cocktail_view.emit_user_change)

    def open_numpad(
        self,
        le_to_write: QLineEdit,
        x_pos: int = 0,
        y_pos: int = 0,
        header_text: str = "Password",
        overwrite_number: bool = False,
        use_float: bool = False,
    ) -> None:
        """Open up the NumpadWidget connected to the lineedit offset from the left upper side."""
        self.numpad_window = NumpadWidget(
            self,
            le_to_write,
            x_pos,
            y_pos,
            header_text,
            overwrite_number=overwrite_number,
            use_float=use_float,
        )

    def open_keyboard(self, le_to_write: QLineEdit, max_char_len: int = 30) -> None:
        """Open up the keyboard connected to the lineedit."""
        self.keyboard_window = KeyboardWidget(self, le_to_write=le_to_write, max_char_len=max_char_len)

    def open_progression_window(self, cocktail_type: str = "Cocktail") -> None:
        """Open up the progression window to show the Cocktail status."""
        self.progress_window = ProgressScreen(self, cocktail_type)
        self.progress_window.show_screen(cocktail_type)

    def change_progression_window(self, pb_value: int) -> None:
        """Change the value of the progression bar of the ProBarWindow."""
        if self.progress_window is None:
            return
        self.progress_window.progressBar.setValue(pb_value)

    def close_progression_window(self) -> None:
        """Close the progression window at the end of the cycle."""
        if self.progress_window is None:
            return
        self.progress_window.hide()

    def open_team_window(self) -> None:
        self.team_window = TeamScreen(self)
        loop = QEventLoop()

        def wait_for_selection(_: Any) -> None:
            """Just wait for the selection to be done."""
            loop.quit()

        # this is needed to block the further execution until the selection is done
        # otherwise, the cocktail will be done before the team is selected
        self.team_window.selection_done.connect(wait_for_selection)
        loop.exec_()

    def open_option_window(self) -> None:
        """Open up the options."""
        if not DP_CONTROLLER.password_prompt(cfg.UI_MASTERPASSWORD):
            return
        self.option_window = OptionWindow(self)

    def open_bottle_window(self) -> None:
        """Open the bottle window to change the volume levels."""
        self.bottle_window = BottleWindow(self)

    def open_ingredient_window(self) -> None:
        """Open a window to spend one single ingredient."""
        self.ingredient_window = GetIngredientWindow(self)

    def open_available_window(self) -> None:
        self.available_window = AvailableWindow(self)

    def open_picture_window(self) -> None:
        cocktail_name = DP_CONTROLLER.get_list_widget_selection(self.LWRezepte)
        if not cocktail_name:
            DP_CONTROLLER.say_create_cocktail_first()
            return
        cocktail = DB_COMMANDER.get_cocktail(cocktail_name)
        # usually we get a cocktail because the name was from the list
        if not cocktail:
            return
        self.picture_window = PictureWindow(cocktail, self.cocktail_view.populate_cocktails)

    def open_refill_dialog(self, cocktail: Cocktail) -> None:
        """Open the refill dialog for the given ingredient."""
        empty_ingredient = cocktail.enough_fill_level()
        if empty_ingredient is None:
            return
        self.refill_dialog = RefillDialog(self, empty_ingredient)

    def connect_other_windows(self) -> None:
        """Links the buttons and lineedits to the other ui elements."""
        self.LECocktail.clicked.connect(lambda: self.open_keyboard(self.LECocktail))
        self.option_button.clicked.connect(self.open_option_window)
        alcohol = UI_LANGUAGE.generate_numpad_header("alcohol")
        self.LEGehaltRezept.clicked.connect(lambda: self.open_numpad(self.LEGehaltRezept, 50, 50, alcohol))
        price = UI_LANGUAGE.generate_numpad_header("price")
        self.line_edit_cocktail_price.clicked.connect(
            lambda: self.open_numpad(self.line_edit_cocktail_price, 400, 50, price, use_float=True)
        )
        self.line_edit_ingredient_name.clicked.connect(
            lambda: self.open_keyboard(self.line_edit_ingredient_name, max_char_len=20)
        )
        self.PBAvailable.clicked.connect(self.open_available_window)
        # connects all the Lineedits from the Recipe amount and gives them the validator
        amount = UI_LANGUAGE.generate_numpad_header("amount")
        for obj in DP_CONTROLLER.get_lineedits_recipe(self):
            obj.clicked.connect(lambda o=obj: self.open_numpad(o, 50, 50, amount))  # type: ignore
            obj.setValidator(QIntValidator(0, 300))
            obj.setMaxLength(3)
        number = UI_LANGUAGE.generate_numpad_header("number")
        # connect the lineedit for the recipe order
        for obj in DP_CONTROLLER.get_lineedits_recipe_order(self):
            obj.clicked.connect(  # type: ignore
                lambda o=obj: self.open_numpad(o, 50, 50, number, True)
            )
            obj.setValidator(QIntValidator(1, 9))
            obj.setMaxLength(1)
        # Setting up Validators for all the the fields (length and/or Types):
        self.LEGehaltRezept.setValidator(QIntValidator(0, 99))
        self.LEGehaltRezept.setMaxLength(2)
        self.line_edit_ingredient_name.setMaxLength(20)
        self.LEFlaschenvolumen.clicked.connect(lambda: self.open_numpad(self.LEFlaschenvolumen, 50, 50, amount))
        self.LEFlaschenvolumen.setMaxLength(5)
        self.line_edit_pump_speed.clicked.connect(lambda: self.open_numpad(self.line_edit_pump_speed, 50, 50, number))
        self.line_edit_pump_speed.setMaxLength(3)
        self.line_edit_ingredient_cost.clicked.connect(
            lambda: self.open_numpad(self.line_edit_ingredient_cost, 50, 50, number)
        )
        self.LECocktail.setMaxLength(30)
        self.input_search_cocktail.clicked.connect(lambda: self.open_keyboard(self.input_search_cocktail))
        self.line_edit_ingredient_unit.clicked.connect(
            lambda: self.open_keyboard(self.line_edit_ingredient_unit, max_char_len=20)
        )

    def connect_objects(self) -> None:
        """Connect all the functions with the Buttons."""
        # First, connect all the push buttons with the Functions
        self.PBZutathinzu.clicked.connect(lambda: ingredients.handle_enter_ingredient(self))
        self.PBRezepthinzu.clicked.connect(lambda: recipes.handle_enter_recipe(self))
        self.PBBelegung.clicked.connect(self.open_bottle_window)
        self.PBZeinzelnd.clicked.connect(self.open_ingredient_window)
        self.PBclear.clicked.connect(lambda: DP_CONTROLLER.clear_recipe_data_recipes(self, False))
        self.PBdelete.clicked.connect(lambda: recipes.delete_recipe(self))
        self.PBZdelete.clicked.connect(lambda: ingredients.delete_ingredient(self))
        self.PBZclear.clicked.connect(lambda: ingredients.clear_ingredient_information(self))
        self.PBFlanwenden.clicked.connect(lambda: bottles.renew_checked_bottles(self))
        self.button_set_picture.clicked.connect(self.open_picture_window)
        self.button_info_recipes.clicked.connect(DP_CONTROLLER.show_recipe_help)
        self.button_enter_to_maker.clicked.connect(self._enter_search_to_maker)
        self.input_search_cocktail.textChanged.connect(self._apply_search_to_list)

        self.PBenable.clicked.connect(lambda: recipes.enable_all_recipes(self))

        # Connect the Lists with the Functions
        self.LWZutaten.itemSelectionChanged.connect(lambda: ingredients.display_selected_ingredient(self))
        self.LWRezepte.itemSelectionChanged.connect(lambda: recipes.load_selected_recipe_data(self))

        # Protect other tabs with password
        # since it's now a password, using 0 = no password will not trigger password window
        # so we don't need to set this up conditionally
        self.tabWidget.currentChanged.connect(self.handle_tab_bar_clicked)

        # add custom icon delegate to search list
        self.list_widget_found_cocktails.setItemDelegate(ItemDelegate(self))
        self.list_widget_found_cocktails.setIconSize(BUTTON_SIZE)

        # gets the bottle ingredients into the global list
        bottles.get_bottle_ingredients()
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
        # Load the Progressbar
        bottles.set_fill_level_bars(self)

        for combobox in DP_CONTROLLER.get_comboboxes_bottles(self):
            combobox.activated.connect(lambda _, window=self: bottles.refresh_bottle_cb(w=window))  # type: ignore[attr-defined]

    def handle_tab_bar_clicked(self, index: int) -> None:
        """Protects tabs other than maker tab with a password."""
        old_index = self.previous_tab_index
        unprotected_tabs = [0] + [i for i, x in enumerate(cfg.UI_LOCKED_TABS, 1) if not x]
        # since the search window lives in the main window now,
        # switching to it needs to get the current available cocktails
        if index == 0:
            self.available_cocktails = DB_COMMANDER.get_possible_cocktails(cfg.MAKER_MAX_HAND_INGREDIENTS)
            self._apply_search_to_list()
        if index in unprotected_tabs:
            self.previous_tab_index = index
            return
        if DP_CONTROLLER.password_prompt(cfg.UI_MAKER_PASSWORD, header_type="maker"):
            self.previous_tab_index = index
            return
        # Set back to the prev tab if password not right
        self.tabWidget.setCurrentIndex(old_index)

    def _apply_search_to_list(self) -> None:
        """Apply the search to the list widget."""
        search = self.input_search_cocktail.text()
        DP_CONTROLLER.clear_list_widget(self.list_widget_found_cocktails)
        # if the search is empty, just fill all possible cocktails
        if not search:
            DP_CONTROLLER.fill_list_widget(self.list_widget_found_cocktails, self.available_cocktails)
            return
        # else, search for the cocktails
        search = search.lower()
        to_fill = []
        for cocktail in self.available_cocktails:
            # also search if any of the ingredient match search
            ingredient_match = any(search in ing.name.lower() for ing in cocktail.ingredients)
            if search in cocktail.name.lower() or ingredient_match:
                to_fill.append(cocktail)
        DP_CONTROLLER.fill_list_widget(self.list_widget_found_cocktails, to_fill)

    def _enter_search_to_maker(self) -> None:
        """Switches to the cocktail selection of the given search."""
        search = DP_CONTROLLER.get_list_widget_selection(self.list_widget_found_cocktails)
        if not search:
            return
        cocktail = DB_COMMANDER.get_cocktail(search)
        if cocktail is None:
            return
        self.open_cocktail_detail(cocktail)
        DP_CONTROLLER.set_tabwidget_tab(self, "maker")
