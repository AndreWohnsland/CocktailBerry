from __future__ import annotations

import random
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtGui import QPixmap, QResizeEvent
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QSizePolicy

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.filepath import DEFAULT_COCKTAIL_IMAGE
from src.image_utils import find_cocktail_image
from src.models import Cocktail, Ingredient
from src.ui.creation_utils import (
    LARGE_FONT,
    NARROW_WIDTH_THRESHOLD,
    apply_responsive_layouts,
    create_button,
    create_label,
    set_underline,
)
from src.ui.icons import IconSetter
from src.ui.shared import qt_prepare_flow
from src.ui_elements import Ui_CocktailSelection

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class CocktailSelection(QDialog, Ui_CocktailSelection):
    """Class for the Cocktail selection view."""

    def __init__(
        self,
        mainscreen: MainScreen,
        cocktail: Cocktail,
        random_mode: bool = False,
        random_pool: list[Cocktail] | None = None,
    ) -> None:
        super().__init__(parent=mainscreen)
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.cocktail = cocktail
        self.mainscreen = mainscreen
        self.random_mode = random_mode
        self.random_pool = random_pool or []
        # Prepare-button layout: single designer button vs multiple dynamically-built buttons.
        # Single-button mode reuses self.prepare_button from the .ui file.
        # Multi-button mode deletes that widget and fills _volume_buttons instead.
        self._multi_button: bool = not cfg.MAKER_USE_RECIPE_VOLUME and len(cfg.MAKER_PREPARE_VOLUME) > 1
        self._volume_buttons: list[tuple[int, QPushButton]] = []
        # build the image
        self.image_container.setScaledContents(True)
        self.icons = IconSetter()
        self.icons.set_cocktail_selection_icons(self)
        self._adjust_preparation_buttons()

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

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        """Flip layout_maker_detail based on window width and resize image to fit its container."""
        # Clear fixed-size constraints so the layout can freely allocate space for image_container.
        self.image_container.setMinimumSize(QSize(0, 0))
        self.image_container.setMaximumSize(QSize(16777215, 16777215))
        super().resizeEvent(a0)
        apply_responsive_layouts(self.width(), [self.layout_maker_detail])
        self._update_image_spacers()
        QTimer.singleShot(0, self._update_image_size)
        # Re-scale the fonts to the real rendered window size (deferred so the layout has settled).
        QTimer.singleShot(0, self.adjust_maker_label_size_cocktaildata)

    def _update_image_spacers(self) -> None:
        """Make image spacers expanding in portrait mode (centers image), fixed in landscape."""
        is_portrait = self.width() < NARROW_WIDTH_THRESHOLD
        h_policy = QSizePolicy.Policy.Expanding if is_portrait else QSizePolicy.Policy.Fixed
        for idx in (0, 2):
            item = self.horizontalLayout.itemAt(idx)
            if item and item.spacerItem():
                spacer = item.spacerItem()
                if not spacer:
                    continue
                spacer.changeSize(5, 20, h_policy, QSizePolicy.Policy.Minimum)
        self.horizontalLayout.invalidate()

    def _update_image_size(self) -> None:
        """Set image_container to 92% of the smaller dimension of its allocated space."""
        w = self.layout_maker_detail.geometry().width()
        h = self.layout_maker_detail.geometry().height()
        side = int(min(w, h) * 0.9)
        # limit to 45% of long side:
        side = min(side, int(max(w, h) * 0.45))
        if side > 0:
            self.image_container.setFixedSize(side, side)

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

    def update_random_display(self) -> None:
        """Update the display for random cocktail mode."""
        pixmap = QPixmap(str(DEFAULT_COCKTAIL_IMAGE))
        self.image_container.setPixmap(pixmap)
        random_label = UI_LANGUAGE.get_translation("random_cocktail_label", "main_window")
        surprise_label = UI_LANGUAGE.get_translation("random_be_surprised", "main_window")
        self.LAlkoholname.setText(random_label)
        self.LAlkoholgehalt.setText("?")
        # hide alcohol low/high buttons
        self.increase_alcohol.setVisible(False)
        self.decrease_alcohol.setVisible(False)
        # show virgin toggle only if any cocktail in pool has virgin_available
        has_virgin = any(c.virgin_available for c in self.random_pool)
        self.virgin_toggle.setVisible(has_virgin)
        self.virgin_toggle.setChecked(False)
        # show surprise message in first ingredient label, clear rest
        fields_ingredient = self.get_labels_maker_ingredients()
        fields_volume = self.get_labels_maker_volume()
        for field_ingredient, field_volume in zip(fields_ingredient, fields_volume):
            field_ingredient.setText("")
            field_ingredient.setVisible(False)
            field_volume.setText("")
            field_volume.setVisible(False)
        if fields_ingredient:
            fields_ingredient[0].setText(surprise_label)
            fields_ingredient[0].setVisible(True)
        self._render_prepare_buttons()

    def _prepare_random_cocktail(self, amount: int) -> None:
        """Pick a random cocktail from the pool and prepare it."""
        if self.is_virgin:
            pool = [c for c in self.random_pool if c.virgin_available]
        else:
            pool = [c for c in self.random_pool if not c.only_virgin]
        if not pool:
            return
        chosen = random.choice(pool)
        # Re-fetch from DB for up-to-date data
        db_cocktail = DB_COMMANDER.get_cocktail(chosen.id)
        if db_cocktail is not None:
            chosen = db_cocktail
        self.cocktail = chosen
        self._scale_cocktail(amount)
        qt_prepare_flow(self.mainscreen, self.cocktail)

    def _prepare_cocktail(self, amount: int) -> None:
        """Prepare the cocktail and switches to the maker screen, if successful."""
        if self.random_mode:
            self._prepare_random_cocktail(amount)
            return
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
        virgin_prefix = "Virgin " if self.is_virgin else ""
        self.LAlkoholname.setText(f"{virgin_prefix}{self.cocktail.name}")
        self.LAlkoholgehalt.setText(f"{self.cocktail.adjusted_alcohol:.1f}%")
        display_data = self.cocktail.machineadds
        hand = self.cocktail.handadds
        self._apply_button_visibility()
        self._render_prepare_buttons()
        if hand:
            display_data.extend([Ingredient(-1, "", 0, 0, 0, False, 100, 100), *hand])
        fields_ingredient = self.get_labels_maker_ingredients()
        fields_volume = self.get_labels_maker_volume()
        # hide all rows first, then show only the needed ones
        for field_ingredient, field_volume in zip(fields_ingredient, fields_volume):
            field_ingredient.setText("")
            field_ingredient.setVisible(False)
            field_volume.setText("")
            field_volume.setVisible(False)
        for field_ingredient, field_volume, ing in zip(fields_ingredient, fields_volume, display_data):
            field_ingredient.setVisible(True)
            field_volume.setVisible(True)
            # -1 indicates no ingredient
            if ing.id == -1:
                ingredient_name = UI_LANGUAGE.get_add_self()
                field_ingredient.setProperty("cssClass", "hand-separator")
                field_ingredient.setStyleSheet(f"color: {self.icons.color.neutral};")
                set_underline(field_ingredient, True)
            else:
                field_ingredient.setProperty("cssClass", "bold")
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
        self.virgin_toggle.setChecked(self.cocktail.only_virgin)
        for field_ingredient, field_volume in zip(self.get_labels_maker_ingredients(), self.get_labels_maker_volume()):
            field_ingredient.setText("")
            field_ingredient.setVisible(False)
            field_volume.setText("")
            field_volume.setVisible(False)

    def adjust_maker_label_size_cocktaildata(self) -> None:
        """Adjust the font size relative to the real rendered window size.

        Scales relative to the actual top-level window (`self.window()`) instead of the
        configured `UI_WIDTH`/`UI_HEIGHT`, so it stays correct when the OS does not honor the
        requested fullscreen size or the config does not match the panel. Because both the window
        geometry and `setPointSize` live in logical pixels, the font-to-window ratio is
        device-pixel-ratio neutral, i.e. fonts stay a constant fraction of the screen on any DPI.
        """
        # iterate over all size types and adjust size relative to window height
        # default height was 480 for provided UI
        # so if its larger, the font should also be larger here
        window = self.window()
        if window is None:
            return
        short_side = min(window.height(), window.width())
        # no need to adjust if its near to the original height
        default_height = 480
        if short_side <= default_height + 20:
            return
        prepare_buttons = [btn for _, btn in self._volume_buttons] if self._multi_button else [self.prepare_button]
        # creating nested list of all labels
        all_labels = [
            [self.LAlkoholname],
            [self.LAlkoholgehalt],
            self.get_labels_maker_volume() + self.get_labels_maker_ingredients(),
            prepare_buttons,
        ]
        default_sizes = [
            22,  # title
            16,  # alcohol
            15,  # ingredients and volumes
            18,  # prepare button(s)
        ]

        diff_from_default_height = short_side / default_height
        scale_factor = 1.05  # grow a bit faster than the window size to better use the space on larger screens
        for default_size, labels in zip(default_sizes, all_labels):
            new_size = int(diff_from_default_height * default_size * scale_factor)
            for label in labels:
                font = label.font()
                font.setPointSize(new_size)
                label.setFont(font)

        # scale button icons 1:1 with the screen (no extra scale_factor)
        default_icon_size = 36
        icon_px = int(diff_from_default_height * default_icon_size)
        scaled_icon = QSize(icon_px, icon_px)
        for button in prepare_buttons:
            button.setIconSize(scaled_icon)

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
        if self.random_mode:
            # Random mode keeps placeholder header but still re-renders buttons for consistency.
            self._render_prepare_buttons()
            return
        self.update_cocktail_data()

    def _adjust_preparation_buttons(self) -> None:
        """Build the prepare-button widgets and connect them.

        Single-button mode reuses the designer `prepare_button`. Multi-button mode replaces it
        with one button per configured volume. Labels are rendered by the next update_* call,
        not here.
        """
        if not self._multi_button:
            volume = self._single_button_volume()
            self.prepare_button.clicked.connect(lambda: self._prepare_cocktail(volume))
            return
        # multi-button mode: drop the designer button and build one per volume
        DP_CONTROLLER.delete_items_of_layout(self.container_prepare_button)
        volume_list = sorted(int(x) for x in cfg.MAKER_PREPARE_VOLUME)
        icon_list = _generate_needed_cocktail_icons(self.icons, len(volume_list))

        # First add the label, we don't need it in every button
        volume_label = create_label(
            f"{cfg.EXP_MAKER_UNIT}:", LARGE_FONT, centered=True, bold=True, max_w=50, css_class="secondary"
        )
        self.container_prepare_button.addWidget(volume_label)

        self._volume_buttons = []
        for volume, icon_name in zip(volume_list, icon_list):
            button = create_button(
                "",  # filled in by _render_prepare_buttons after construction
                self,
                css_class="btn-inverted ml round",
                min_h=60,
                max_h=80,
            )
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.clicked.connect(lambda _, v=volume: self._prepare_cocktail(v))
            icon = self.icons.generate_icon(icon_name, self.icons.color.background)
            self.icons.set_icon(button, icon, False)
            self.container_prepare_button.addWidget(button)
            self._volume_buttons.append((volume, button))

    def _single_button_volume(self) -> int:
        """Volume targeted by the single prepare button (recipe amount or first configured volume)."""
        return self.cocktail.amount if cfg.MAKER_USE_RECIPE_VOLUME else cfg.MAKER_PREPARE_VOLUME[0]

    def _render_prepare_buttons(self) -> None:
        """Render labels on all prepare buttons for current cocktail/mode state.

        Single source of truth for prepare-button text in both single- and multi-button modes,
        and in both normal and random flows.
        """
        if self._multi_button:
            for volume, button in self._volume_buttons:
                button.setText(self._format_prepare_label(volume, include_unit=False))
            return
        # Single-button mode: the per-cocktail recipe volume is unknown until a random pick,
        # so render it as "?" in that combination.
        if self.random_mode and cfg.MAKER_USE_RECIPE_VOLUME:
            volume: int | None = None
        else:
            volume = self._single_button_volume() if self.random_mode else self.cocktail.adjusted_amount
        self.prepare_button.setText(self._format_prepare_label(volume, include_unit=True))

    def _format_prepare_label(self, volume: int | None, *, include_unit: bool) -> str:
        """Build a prepare-button label of the form `{volume}[ {unit}][: {price}€]`.

        Pass `volume=None` when the volume is unknown (random mode with per-cocktail recipe
        volume in single-button mode) — both volume and price then render as `?`. The unit is
        embedded only when `include_unit` is True; multi-button mode shows it once in a
        sidebar label instead.
        """
        volume_str = "?" if volume is None else f"{self._decide_rounding(volume * cfg.EXP_MAKER_FACTOR, 20)}"
        label = f"{volume_str} {cfg.EXP_MAKER_UNIT}" if include_unit else volume_str
        if cfg.payment_enabled:
            label += f": {self._format_button_price(volume)}€"
        return label

    def _format_button_price(self, volume: int | None) -> str:
        """Compute the price string for a prepare button. Returns `?` when the price is unknown."""
        if volume is None or self.random_mode:
            return "?"
        multiplier = cfg.PAYMENT_VIRGIN_MULTIPLIER / 100 if self.is_virgin else 1.0
        price = self.cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, volume, price_multiplier=multiplier)
        return f"{price}".rstrip("0").rstrip(".")


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
