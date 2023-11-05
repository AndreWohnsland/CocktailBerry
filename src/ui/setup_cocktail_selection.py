from __future__ import annotations
from typing import Callable, TypeVar, TYPE_CHECKING
from PyQt5.QtWidgets import QDialog, QWidget, QLabel, QSizePolicy
from PyQt5.QtGui import QFont, QPixmap
from src.image_utils import find_cocktail_image

from src.models import Cocktail, Ingredient
from src.ui_elements import Ui_CocktailSelection
from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.tabs import maker
from src.config_manager import CONFIG as cfg, shared
from src.ui.icons import ICONS

T = TypeVar('T', int, float)
PICTURE_SIZE = int(min(cfg.UI_WIDTH * 0.5, cfg.UI_HEIGHT * 0.65))

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class CocktailSelection(QDialog, Ui_CocktailSelection):
    """ Class for the Cocktail selection view. """

    def __init__(
        self,
        mainscreen: MainScreen,
        cocktail: Cocktail,
        maker_screen_activate: Callable
    ):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.maker_screen_activate = maker_screen_activate
        self.cocktail = cocktail
        self.mainscreen = mainscreen
        # build the image
        self.image_container.setScaledContents(True)
        self.image_container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # type: ignore
        self.image_container.setMinimumSize(PICTURE_SIZE, PICTURE_SIZE)
        self.image_container.setMaximumSize(PICTURE_SIZE, PICTURE_SIZE)
        ICONS.set_cocktail_selection_icons(self)
        self.hide_necessary_elements()

        UI_LANGUAGE.adjust_cocktail_selection_screen(self)
        self.clear_recipe_data_maker()
        # Also resets the alcohol factor
        self.reset_alcohol_factor()
        DP_CONTROLLER.set_display_settings(self, False)
        self._connect_elements()

    def _back(self):
        self.maker_screen_activate()

    def _set_image(self):
        """Sets the image of the cocktail"""
        image_path = find_cocktail_image(self.cocktail)
        pixmap = QPixmap(str(image_path))
        self.image_container.setPixmap(pixmap)

    def _connect_elements(self):
        """Init all the needed buttons"""
        self.button_back.clicked.connect(self._back)
        self.prepare_button.clicked.connect(self._prepare_cocktail)
        self.increase_volume.clicked.connect(lambda: self.adjust_volume(25))
        self.decrease_volume.clicked.connect(lambda: self.adjust_volume(-25))
        self.increase_alcohol.clicked.connect(lambda: self.adjust_alcohol(0.15))
        self.decrease_alcohol.clicked.connect(lambda: self.adjust_alcohol(-0.15))
        self.virgin_checkbox.stateChanged.connect(self.update_cocktail_data)
        self.button_search_cocktail.clicked.connect(self.mainscreen.open_search_window)
        self.adjust_maker_label_size_cocktaildata()

    def set_cocktail(self, cocktail: Cocktail):
        """Gets the latest info from the db, gets the cocktails"""
        self.clear_recipe_data_maker()
        # need to refetch the cocktail from db, because the db might have changed
        # this is because the gui elements have a reference to the cocktail object
        # and when it changes, the gui elements will not update
        db_cocktail = DB_COMMANDER.get_cocktail(cocktail.id)
        if db_cocktail is not None:
            cocktail = db_cocktail
        self.cocktail = cocktail
        self._set_image()

    def _prepare_cocktail(self):
        """Prepares the cocktail and switches to the maker screen, if successful"""
        # same applies here, need to refetch the cocktail from db
        db_cocktail = DB_COMMANDER.get_cocktail(self.cocktail.id)
        if db_cocktail is not None:
            self.cocktail = db_cocktail
        self._scale_cocktail()
        success = maker.prepare_cocktail(self.mainscreen, self.cocktail)
        print(f"{success=}")
        if not success:
            return
        self.virgin_checkbox.setChecked(False)
        self.mainscreen.container_maker.setCurrentWidget(self.mainscreen.cocktail_view)

    def _scale_cocktail(self):
        """Scale the cocktail to given conditions for volume and alcohol"""
        amount = shared.cocktail_volume
        factor = shared.alcohol_factor
        is_virgin = self.virgin_checkbox.isChecked()
        if is_virgin:
            factor = 0
        if cfg.MAKER_USE_RECIPE_VOLUME:
            amount = self.cocktail.amount
        self.cocktail.scale_cocktail(amount, factor)

    def update_cocktail_data(self):
        """Updates the cocktail data in the selection view"""
        self._scale_cocktail()
        amount = self.cocktail.adjusted_amount
        self.LAlkoholname.setText(self.cocktail.name)
        display_volume = self._decide_rounding(amount * cfg.EXP_MAKER_FACTOR, 20)
        self.LMenge.setText(f"{display_volume} {cfg.EXP_MAKER_UNIT}")
        self.LAlkoholgehalt.setText(f"{self.cocktail.adjusted_alcohol:.1f}%")
        display_data = self.cocktail.machineadds
        hand = self.cocktail.handadds
        # Activates or deactivates the virgin checkbox, depending on the virgin flag
        self.virgin_checkbox.setEnabled(self.cocktail.virgin_available)
        # Styles does not work on strikeout, so we use internal qt things
        # To be precise, they do work at start, but does not support dynamic changes
        self._set_strike_through(self.virgin_checkbox, not self.cocktail.virgin_available)
        # when there is handadd, also build some additional data
        if hand:
            display_data.extend([Ingredient(-1, "", 0, 0, 0, False, False)] + hand)
        fields_ingredient = self.get_labels_maker_ingredients()
        fields_volume = self.get_labels_maker_volume()
        for field_ingredient, field_volume, ing in zip(fields_ingredient, fields_volume, display_data):
            # -1 indicates no ingredient
            if ing.id == -1:
                ingredient_name = UI_LANGUAGE.get_add_self()
                field_ingredient.setProperty("cssClass", "hand-separator")
                field_ingredient.setStyleSheet(f"color: {ICONS.color.neutral};")
                self._set_underline(field_ingredient, True)
            else:
                field_ingredient.setProperty("cssClass", None)
                field_ingredient.setStyleSheet("")
                self._set_underline(field_ingredient, False)
                display_amount = self._decide_rounding(ing.amount * cfg.EXP_MAKER_FACTOR)
                field_volume.setText(f" {display_amount} {cfg.EXP_MAKER_UNIT}")
                ingredient_name = ing.name
            field_ingredient.setText(f"{ingredient_name} ")

    def _decide_rounding(self, val: float, threshold=8):
        """Helper to get the right rounding for numbers displayed to the user"""
        if val >= threshold:
            return int(val)
        return round(val, 1)

    def _set_underline(self, element: QWidget, underline: bool):
        """Set the strike through property of the font"""
        font = element.font()
        font.setUnderline(underline)
        element.setFont(font)

    def _set_strike_through(self, element: QWidget, strike_through: bool):
        """Set the strike through property of the font"""
        font = element.font()
        font.setStrikeOut(strike_through)
        element.setFont(font)

    def clear_recipe_data_maker(self):
        """Clear the cocktail data in the maker view, only clears selection if no other item was selected"""
        self.LAlkoholgehalt.setText("")
        self.LAlkoholname.setText(UI_LANGUAGE.get_cocktail_dummy())
        self.LMenge.setText("")
        self.virgin_checkbox.setChecked(False)
        for field_ingredient, field_volume in zip(
            self.get_labels_maker_ingredients(),
            self.get_labels_maker_volume()
        ):
            field_ingredient.setText("")
            field_volume.setText("")

    def reset_alcohol_factor(self):
        """Sets the alcohol slider to default (100%) value"""
        shared.alcohol_factor = 1.0

    def adjust_maker_label_size_cocktaildata(self):
        """Adjusts the font size for larger screens"""
        # iterate over all size types and adjust size relative to window height
        # default height was 480 for provided UI
        # so if its larger, the font should also be larger here
        height = cfg.UI_HEIGHT
        # no need to adjust if its near to the original height
        default_height = 480
        if height <= default_height + 20:
            return
        # creating list of all labels
        big_labels = [self.LAlkoholname]
        medium_labels = [self.LMenge, self.LAlkoholgehalt]
        small_labels = self.get_labels_maker_volume()
        small_labels_bold = self.get_labels_maker_ingredients()
        all_labels = [big_labels, medium_labels, small_labels_bold, small_labels]

        diff_from_default_height = height / default_height
        # from large to small
        default_sizes = [22, 16, 12, 12]
        is_bold_list = [True, True, True, False]
        for default_size, is_bold, labels in zip(default_sizes, is_bold_list, all_labels):
            new_size = int(diff_from_default_height * default_size)
            font = QFont()
            font.setPointSize(new_size)
            font.setBold(is_bold)
            font.setWeight(50 + is_bold * 25)
            for label in labels:
                label.setFont(font)

    def get_labels_maker_volume(self) -> list[QLabel]:
        """Returns all maker label objects for volumes of ingredients"""
        return [getattr(self, f"LMZutat{x}") for x in range(1, 10)]

    def get_labels_maker_ingredients(self) -> list[QLabel]:
        """Returns all maker label objects for ingredient name"""
        return [getattr(self, f"LZutat{x}") for x in range(1, 10)]

    def adjust_alcohol(self, amount: float):
        """changes the alcohol factor"""
        new_factor = shared.alcohol_factor + amount
        shared.alcohol_factor = _limit_number(new_factor, 0.7, 1.3)
        self.update_cocktail_data()

    def adjust_volume(self, amount: int):
        """changes the volume amount"""
        # Do not scale the recipe volume if the option is activated
        if cfg.MAKER_USE_RECIPE_VOLUME:
            return
        new_volume = shared.cocktail_volume + amount
        shared.cocktail_volume = _limit_number(new_volume, 100, 400)
        self.update_cocktail_data()

    def hide_necessary_elements(self):
        """Depending on the config, hide some of the unused elements"""
        if cfg.MAKER_USE_RECIPE_VOLUME:
            self.decrease_volume.hide()
            self.increase_volume.hide()


def _limit_number(val: T, min_val: T, max_val: T) -> T:
    """Limits the number in the boundaries"""
    limited = max(min_val, val)
    limited = min(max_val, limited)
    return limited
