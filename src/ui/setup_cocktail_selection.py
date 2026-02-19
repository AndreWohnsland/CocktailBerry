from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QSizePolicy

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.image_utils import find_cocktail_image
from src.models import Cocktail, Ingredient
from src.ui.creation_utils import LARGE_FONT, create_button, create_label, set_underline
from src.ui.icons import IconSetter
from src.ui.shared import qt_prepare_flow
from src.ui_elements import Ui_CocktailSelection

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class CocktailSelection(QDialog, Ui_CocktailSelection):
    """Class for the Cocktail selection view."""

    def __init__(self, mainscreen: MainScreen, cocktail: Cocktail) -> None:
        super().__init__(parent=mainscreen)
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.cocktail = cocktail
        self.mainscreen = mainscreen
        # Store references for dynamic button label updates
        self._volume_buttons: list[tuple[int, QPushButton]] = []  # list of (volume, button) tuples
        # build the image
        self.image_container.setScaledContents(True)
        self.image_container.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        picture_size = int(min(cfg.UI_WIDTH * 0.5, cfg.UI_HEIGHT * 0.60))
        self.image_container.setMinimumSize(picture_size, picture_size)
        self.image_container.setMaximumSize(picture_size, picture_size)
        self.icons = IconSetter()
        self.icons.set_cocktail_selection_icons(self)
        self._adjust_preparation_buttons()

        UI_LANGUAGE.adjust_cocktail_selection_screen(self)
        self.clear_recipe_data_maker()
        DP_CONTROLLER.set_display_settings(self, False)
        self._connect_elements()

    @property
    def can_change_virgin(self) -> bool:
        """Return if the cocktail can have a virgin option."""
        return self.cocktail.virgin_available and not self.cocktail.only_virgin

    @property
    def alcohol_factor(self) -> float:
        if self.virgin_toggle.isChecked():
            return 0.0
        if self.increase_alcohol.isChecked():
            return 1.3
        if self.decrease_alcohol.isChecked():
            return 0.7
        return 1.0

    @property
    def is_virgin(self) -> bool:
        return self.virgin_toggle.isChecked()

    def _set_image(self) -> None:
        """Set the image of the cocktail."""
        image_path = find_cocktail_image(self.cocktail)
        pixmap = QPixmap(str(image_path))
        self.image_container.setPixmap(pixmap)

    def _connect_elements(self) -> None:
        """Init all the needed buttons."""
        self.button_back.clicked.connect(self.mainscreen.switch_to_cocktail_list)
        self.increase_alcohol.clicked.connect(self._higher_alcohol)
        self.decrease_alcohol.clicked.connect(self._lower_alcohol)
        self.virgin_toggle.clicked.connect(self._toggle_virgin)
        self._apply_button_visibility()
        self.adjust_maker_label_size_cocktaildata()

    def set_cocktail(self, cocktail: Cocktail) -> None:
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
        self.cocktail.scale_cocktail(amount, self.alcohol_factor * (cfg.MAKER_ALCOHOL_FACTOR / 100))

    def update_cocktail_data(self) -> None:
        """Update the cocktail data in the selection view."""
        self._scale_cocktail()
        amount: int | float = self.cocktail.adjusted_amount
        # Need to set the button text here, since we need cocktail
        self.prepare_button.setText(
            UI_LANGUAGE.get_translation("prepare_button", "cocktail_selection", amount=amount, unit=cfg.EXP_MAKER_UNIT)
        )
        virgin_prefix = "Virgin " if self.is_virgin else ""
        self.LAlkoholname.setText(f"{virgin_prefix}{self.cocktail.name}")
        display_volume = self._decide_rounding(amount * cfg.EXP_MAKER_FACTOR, 20)
        self.LMenge.setText(f"{display_volume} {cfg.EXP_MAKER_UNIT}")
        self.LAlkoholgehalt.setText(f"{self.cocktail.adjusted_alcohol:.1f}%")
        display_data = self.cocktail.machineadds
        hand = self.cocktail.handadds
        self._apply_button_visibility()
        self._update_volume_button_labels()
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
                field_ingredient.setStyleSheet(f"color: {self.icons.color.neutral};")
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

    def _apply_button_visibility(self) -> None:
        """Hide or show the toggle buttons for alcohol and virgin mode, depending on the cocktail and config."""
        is_single_ingredient_recipe = len(self.cocktail.ingredients) == 1
        # hide the strong/weak buttons, when they are not needed or possible
        show_alcohol_buttons = (
            not is_single_ingredient_recipe and not self.cocktail.only_virgin and not cfg.payment_enabled
        )
        self.increase_alcohol.setVisible(show_alcohol_buttons)
        self.decrease_alcohol.setVisible(show_alcohol_buttons)
        self.LAlkoholgehalt.setVisible(not is_single_ingredient_recipe)
        self.virgin_toggle.setVisible(self.can_change_virgin)
        # Update button labels if payment is active (price may change with virgin mode)

    def _decide_rounding(self, val: float, threshold: int = 8) -> int | float:
        """Return the right rounding for numbers displayed to the user."""
        if val >= threshold:
            # needs to be int, otherwise we would need to format .0 or .1 which is difficult
            return int(round(val, 0))
        return round(val, 1)

    def clear_recipe_data_maker(self) -> None:
        """Clear the cocktail data in the maker view, only clears selection if no other item was selected."""
        self.LAlkoholgehalt.setText("")
        self.LAlkoholname.setText(UI_LANGUAGE.get_cocktail_dummy())
        self.LMenge.setText("")
        self.virgin_toggle.setChecked(self.cocktail.only_virgin)
        for field_ingredient, field_volume in zip(self.get_labels_maker_ingredients(), self.get_labels_maker_volume()):
            field_ingredient.setText("")
            field_volume.setText("")

    def adjust_maker_label_size_cocktaildata(self) -> None:
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

    def _higher_alcohol(self, _: bool) -> None:
        """Increases the alcohol factor."""
        self.decrease_alcohol.setChecked(False)
        self.virgin_toggle.setChecked(False)
        self.update_cocktail_data()

    def _lower_alcohol(self, _: bool) -> None:
        """Decreases the alcohol factor."""
        self.increase_alcohol.setChecked(False)
        self.virgin_toggle.setChecked(False)
        self.update_cocktail_data()

    def _toggle_virgin(self, _: bool) -> None:
        """Toggle the virgin option."""
        self.decrease_alcohol.setChecked(False)
        self.increase_alcohol.setChecked(False)
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
        icon_list = _generate_needed_cocktail_icons(self.icons, len(volume_list))

        # First add the label, we don't need it in every button
        volume_label = create_label(
            f"{cfg.EXP_MAKER_UNIT}:", LARGE_FONT, centered=True, bold=True, max_w=50, css_class="secondary"
        )
        self.container_prepare_button.addWidget(volume_label)

        # Clear stored button references
        self._volume_buttons = []

        # Then create a button for each volume
        for volume, icon_name in zip(volume_list, icon_list):
            button = create_button(
                "",  # Label will be set by _update_volume_button_labels
                self,
                css_class="btn-inverted ml round",
                min_h=60,
                max_h=80,
            )
            button.clicked.connect(lambda _, v=volume: self._prepare_cocktail(v))
            icon = self.icons.generate_icon(icon_name, self.icons.color.background)
            self.icons.set_icon(button, icon, False)
            self.container_prepare_button.addWidget(button)
            # Store reference for later label updates
            self._volume_buttons.append((volume, button))

        # Set initial button labels
        self._update_volume_button_labels()

    def _update_volume_button_labels(self) -> None:
        """Update the labels of volume buttons, recalculating prices if payment is active."""
        for volume, button in self._volume_buttons:
            volume_converted = self._decide_rounding(volume * cfg.EXP_MAKER_FACTOR, 20)
            label = f"{volume_converted}"
            if cfg.payment_enabled:
                multiplier = cfg.PAYMENT_VIRGIN_MULTIPLIER / 100 if self.is_virgin else 1.0
                price = self.cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, volume, price_multiplier=multiplier)
                price_str = f"{price}".rstrip("0").rstrip(".")
                label += f": {price_str}€"
            button.setText(label)


def _generate_needed_cocktail_icons(icon_setter: IconSetter, amount: int) -> list[str]:
    icon_list = [
        icon_setter.presets.tiny_glass,
        icon_setter.presets.small_glass,
        icon_setter.presets.medium_glass,
        icon_setter.presets.big_glass,
        icon_setter.presets.huge_glass,
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
