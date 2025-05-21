from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QSizePolicy

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.image_utils import find_cocktail_image
from src.models import Cocktail, Ingredient
from src.ui.creation_utils import LARGE_FONT, create_button, create_label, set_strike_through, set_underline
from src.ui.icons import ICONS
from src.ui.shared import qt_prepare_flow
from src.ui_elements import Ui_CocktailSelection

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class CocktailSelection(QDialog, Ui_CocktailSelection):
    """Class for the Cocktail selection view."""

    def __init__(self, mainscreen: MainScreen, cocktail: Cocktail, maker_screen_activate: Callable) -> None:
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.maker_screen_activate = maker_screen_activate
        self.cocktail = cocktail
        self.mainscreen = mainscreen
        # build the image
        self.image_container.setScaledContents(True)
        self.image_container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # type: ignore
        picture_size = int(min(cfg.UI_WIDTH * 0.5, cfg.UI_HEIGHT * 0.60))
        self.image_container.setMinimumSize(picture_size, picture_size)
        self.image_container.setMaximumSize(picture_size, picture_size)
        ICONS.set_cocktail_selection_icons(self)
        self._adjust_preparation_buttons()

        UI_LANGUAGE.adjust_cocktail_selection_screen(self)
        self.clear_recipe_data_maker()
        # Also resets the alcohol factor
        self.reset_alcohol_factor()
        DP_CONTROLLER.set_display_settings(self, False)
        self._connect_elements()

    def _back(self) -> None:
        self.maker_screen_activate()

    def _set_image(self) -> None:
        """Set the image of the cocktail."""
        image_path = find_cocktail_image(self.cocktail)
        pixmap = QPixmap(str(image_path))
        self.image_container.setPixmap(pixmap)

    def _connect_elements(self) -> None:
        """Init all the needed buttons."""
        self.button_back.clicked.connect(self._back)
        self.increase_alcohol.clicked.connect(self._higher_alcohol)
        self.decrease_alcohol.clicked.connect(self._lower_alcohol)
        self.virgin_checkbox.stateChanged.connect(self.update_cocktail_data)
        self.adjust_maker_label_size_cocktaildata()

    def set_cocktail(self, cocktail: Cocktail):
        """Get the latest info from the db, gets the cocktails."""
        self.clear_recipe_data_maker()
        # need to refetch the cocktail from db, because the db might have changed
        # this is because the gui elements have a reference to the cocktail object
        # and when it changes, the gui elements will not update
        db_cocktail = DB_COMMANDER.get_cocktail(cocktail.id)
        if db_cocktail is not None:
            # need to revaluate if there is only the virgin version available
            db_cocktail.is_possible(DB_COMMANDER.get_available_ids(), cfg.MAKER_MAX_HAND_INGREDIENTS)
            cocktail = db_cocktail
        self.cocktail = cocktail
        self._set_image()

    def _prepare_cocktail(self, amount: int) -> None:
        """Prepare the cocktail and switches to the maker screen, if successful."""
        # same applies here, need to refetch the cocktail from db
        db_cocktail = DB_COMMANDER.get_cocktail(self.cocktail.id)
        if db_cocktail is not None:
            self.cocktail = db_cocktail
        self._scale_cocktail(amount)
        qt_prepare_flow(self.mainscreen, self.cocktail)

    def _scale_cocktail(self, amount: int | None = None) -> None:
        """Scale the cocktail to given conditions for volume and alcohol."""
        # if no amount is given, take the middle of the volume list
        # this will give the first element if there is only one element
        if amount is None:
            amount = cfg.MAKER_PREPARE_VOLUME[len(cfg.MAKER_PREPARE_VOLUME) // 2]
        # overwrite the amount if the cocktail has a fixed volume
        if cfg.MAKER_USE_RECIPE_VOLUME:
            amount = self.cocktail.amount
        factor = shared.alcohol_factor * (cfg.MAKER_ALCOHOL_FACTOR / 100)  # remember this is percent
        is_virgin = self.virgin_checkbox.isChecked()
        if is_virgin:
            factor = 0
        self.cocktail.scale_cocktail(amount, factor)

    def update_cocktail_data(self):
        """Update the cocktail data in the selection view."""
        self._scale_cocktail()
        amount = self.cocktail.adjusted_amount
        # Need to set the button text here, since we need cocktail
        self.prepare_button.setText(
            UI_LANGUAGE.get_translation("prepare_button", "cocktail_selection", amount=amount, unit=cfg.EXP_MAKER_UNIT)
        )
        virgin_prefix = "Virgin " if self.cocktail.is_virgin else ""
        self.LAlkoholname.setText(f"{virgin_prefix}{self.cocktail.name}")
        display_volume = self._decide_rounding(amount * cfg.EXP_MAKER_FACTOR, 20)
        self.LMenge.setText(f"{display_volume} {cfg.EXP_MAKER_UNIT}")
        self.LAlkoholgehalt.setText(f"{self.cocktail.adjusted_alcohol:.1f}%")
        display_data = self.cocktail.machineadds
        hand = self.cocktail.handadds
        self._apply_virgin_setting()
        if hand:
            display_data.extend([Ingredient(-1, "", 0, 0, 0, False, 100, 100), *hand])
        fields_ingredient = self.get_labels_maker_ingredients()
        fields_volume = self.get_labels_maker_volume()
        # clean the ui elements
        for field_ingredient, field_volume in zip(fields_ingredient, fields_volume):
            field_ingredient.setText("")
            field_volume.setText("")
        for field_ingredient, field_volume, ing in zip(fields_ingredient, fields_volume, display_data):
            # -1 indicates no ingredient
            if ing.id == -1:
                ingredient_name = UI_LANGUAGE.get_add_self()
                field_ingredient.setProperty("cssClass", "hand-separator")
                field_ingredient.setStyleSheet(f"color: {ICONS.color.neutral};")
                set_underline(field_ingredient, True)
            else:
                field_ingredient.setProperty("cssClass", None)
                field_ingredient.setStyleSheet("")
                set_underline(field_ingredient, False)
                amount = ing.amount
                if ing.unit == "ml":
                    amount = ing.amount * cfg.EXP_MAKER_FACTOR
                # do always cut decimal if there is another unit than ml
                rounding_threshold = 8 if ing.unit == "ml" else 0
                display_amount = self._decide_rounding(amount, rounding_threshold)
                unit = cfg.EXP_MAKER_UNIT if ing.unit == "ml" else ing.unit
                field_volume.setText(f" {display_amount} {unit}")
                ingredient_name = ing.name
            field_ingredient.setText(f"{ingredient_name} ")

    def _apply_virgin_setting(self) -> None:
        # hide the strong/weak buttons, since they are not needed
        self.increase_alcohol.setVisible(not self.cocktail.only_virgin)
        self.decrease_alcohol.setVisible(not self.cocktail.only_virgin)
        can_change_virgin = self.cocktail.virgin_available and not self.cocktail.only_virgin
        self.virgin_checkbox.setEnabled(can_change_virgin)
        # Styles does not work on strikeout, so we use internal qt things
        # To be precise, they do work at start, but does not support dynamic changes
        set_strike_through(self.virgin_checkbox, not can_change_virgin)

    def _decide_rounding(self, val: float, threshold: int = 8) -> int | float:
        """Return the right rounding for numbers displayed to the user."""
        if val >= threshold:
            # needs to be int, otherwise we would need to format .0 or .1 which is difficult
            return int(round(val, 0))
        return round(val, 1)

    def clear_recipe_data_maker(self):
        """Clear the cocktail data in the maker view, only clears selection if no other item was selected."""
        self.LAlkoholgehalt.setText("")
        self.LAlkoholname.setText(UI_LANGUAGE.get_cocktail_dummy())
        self.LMenge.setText("")
        self.virgin_checkbox.setChecked(self.cocktail.only_virgin)
        for field_ingredient, field_volume in zip(self.get_labels_maker_ingredients(), self.get_labels_maker_volume()):
            field_ingredient.setText("")
            field_volume.setText("")

    def reset_alcohol_factor(self):
        """Set the alcohol slider to default (100%) value."""
        if self.cocktail.only_virgin:
            shared.alcohol_factor = 0.0
        else:
            shared.alcohol_factor = 1.0

    def adjust_maker_label_size_cocktaildata(self):
        """Adjust the font size for larger screens."""
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
        """Return all maker label objects for volumes of ingredients."""
        return [getattr(self, f"LMZutat{x}") for x in range(1, 10)]

    def get_labels_maker_ingredients(self) -> list[QLabel]:
        """Return all maker label objects for ingredient name."""
        return [getattr(self, f"LZutat{x}") for x in range(1, 10)]

    def _higher_alcohol(self, checked: bool) -> None:
        """Increases the alcohol factor."""
        self.decrease_alcohol.setChecked(False)
        if checked:
            self.adjust_alcohol(1.3)
        else:
            self.adjust_alcohol(1.0)

    def _lower_alcohol(self, checked: bool) -> None:
        """Decreases the alcohol factor."""
        self.increase_alcohol.setChecked(False)
        if checked:
            self.adjust_alcohol(0.7)
        else:
            self.adjust_alcohol(1.0)

    def adjust_alcohol(self, amount: float):
        """Change the alcohol factor to the given value."""
        shared.alcohol_factor = amount
        self.update_cocktail_data()

    def _adjust_preparation_buttons(self) -> None:
        """Decide if to use a single or multiple buttons and adjusts the text accordingly.

        Also connects the functions to the buttons.
        """
        # if there is a fixed volume, use a single button
        # this is either due to the user has only one volume
        # or using the default cocktail recipe volume
        if cfg.MAKER_USE_RECIPE_VOLUME or len(cfg.MAKER_PREPARE_VOLUME) == 1:
            volume = self.cocktail.amount if cfg.MAKER_USE_RECIPE_VOLUME else cfg.MAKER_PREPARE_VOLUME[0]
            self.prepare_button.clicked.connect(lambda: self._prepare_cocktail(volume))
            return
        # if there are multiple volumes, use one button for each volume
        # in addition, we need to clean the button container of the button first
        DP_CONTROLLER.delete_items_of_layout(self.container_prepare_button)
        volume_list = sorted(int(x) for x in cfg.MAKER_PREPARE_VOLUME)
        icon_list = _generate_needed_cocktail_icons(len(volume_list))

        # First add the label, we don't need it in every button
        volume_label = create_label(
            f"{cfg.EXP_MAKER_UNIT}:", LARGE_FONT, centered=True, bold=True, max_w=50, css_class="secondary"
        )
        self.container_prepare_button.addWidget(volume_label)

        # Then create a button for each volume
        for volume, icon_name in zip(volume_list, icon_list):
            volume_converted = self._decide_rounding(volume * cfg.EXP_MAKER_FACTOR, 20)
            button = create_button(
                f"{volume_converted}",  # \n  {cfg.EXP_MAKER_UNIT}
                self,
                css_class="btn-inverted ml round",
                min_h=60,
                max_h=80,
            )
            button.clicked.connect(lambda _, v=volume: self._prepare_cocktail(v))
            icon = ICONS.generate_icon(icon_name, ICONS.color.background)
            ICONS.set_icon(button, icon, False)
            self.container_prepare_button.addWidget(button)


def _generate_needed_cocktail_icons(amount: int) -> list[str]:
    icon_list = [
        ICONS.presets.tiny_glass,
        ICONS.presets.small_glass,
        ICONS.presets.medium_glass,
        ICONS.presets.big_glass,
        ICONS.presets.huge_glass,
    ]
    length = len(icon_list)
    if amount <= length:
        start = (length - amount) // 2
        return icon_list[start : start + amount]
    result = icon_list[:]
    remaining = amount - length
    for i in range(remaining):
        if i % 2 == 0:
            result.insert(0, icon_list[0])
        else:
            result.append(icon_list[-1])
    return result
