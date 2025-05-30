from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Literal

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from src import MAX_SUPPORTED_BOTTLES
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE, DialogHandler
from src.filepath import APP_ICON_FILE, STYLE_FOLDER
from src.models import Cocktail, Ingredient
from src.ui.icons import ICONS
from src.ui_elements.bonusingredient import Ui_addingredient
from src.ui_elements.cocktailmanager import Ui_MainWindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        option.decorationPosition = QStyleOptionViewItem.Right  # type: ignore
        super().paint(painter, option, index)


@dataclass
class RecipeInput:
    recipe_name: str
    selected_recipe: str
    ingredient_names: list[str]
    ingredient_volumes: list[str]
    ingredient_order: list[str]
    enabled: bool
    virgin: bool


@dataclass
class IngredientInputFields:
    ingredient_name: QLineEdit
    selected_ingredient: QListWidget
    alcohol_level: QLineEdit
    volume: QLineEdit
    ingredient_cost: QLineEdit
    hand_add: QCheckBox
    pump_speed: QLineEdit
    unit: QLineEdit


class DisplayController(DialogHandler):
    """Controller Class to get Values from the UI."""

    ########################
    # UI "EXTRACT" METHODS #
    ########################
    def get_current_combobox_items(self, combobox_list: list[QComboBox]) -> list[str]:
        """Get a list of the current combo box items."""
        return [combobox.currentText() for combobox in combobox_list]

    def get_toggle_status(self, button_list: list[QPushButton]) -> list[bool]:
        """Get a list of if the buttons are checked."""
        return [button.isChecked() for button in button_list]

    def get_lineedit_text(self, lineedit_list: list[QLineEdit]) -> list[str]:
        """Get a list of the text of the lineedits."""
        return [lineedit.text().strip() for lineedit in lineedit_list]

    def get_list_widget_selection(self, list_widget: QListWidget) -> str:
        """Return the current selected item of the list widget."""
        selected = list_widget.selectedItems()
        if not selected:
            return ""
        # use selected items because currentItem is sometimes still last and not the current one ...
        # The widget got only single select, so there is always (if there is a selection) one item
        first_selected = selected[0]
        user_data: Cocktail | None = first_selected.data(Qt.UserRole)  # type: ignore
        if user_data:
            # If the user data is a cocktail object, return the name, else the user data
            # Usually the data should be a cocktail object, but fallback if it may set differently
            return user_data.name if isinstance(user_data, Cocktail) else user_data
        return first_selected.text()

    def get_list_widget_items(self, list_widget: QListWidget) -> list[str] | list[Cocktail]:
        """Return the items of the list widget."""
        # usually will have only one of both types in list, no mix.
        # In the future, there should be an argument in the function to define cocktail or str
        list_widget_data: list[str] | list[Cocktail] = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            data: Cocktail | None = item.data(Qt.UserRole)  # type: ignore
            if data:
                list_widget_data.append(data)  # type: ignore
            else:
                list_widget_data.append(item.text())  # type: ignore
        return list_widget_data

    def get_ingredient_data(self, w: Ui_MainWindow) -> Ingredient:
        """Return an Ingredient Object from the ingredient data fields."""
        ingredient_input = self.get_ingredient_fields(w)
        ingredient_name, alcohol_level, volume, ingredient_cost, unit, speed = self.get_lineedit_text(
            [
                ingredient_input.ingredient_name,
                ingredient_input.alcohol_level,
                ingredient_input.volume,
                ingredient_input.ingredient_cost,
                ingredient_input.unit,
                ingredient_input.pump_speed,
            ]
        )
        hand_add = ingredient_input.hand_add.isChecked()
        selected_ingredient = self.get_list_widget_selection(ingredient_input.selected_ingredient)
        return Ingredient(
            id=-1,
            name=ingredient_name,
            alcohol=int(alcohol_level),
            bottle_volume=int(volume),
            fill_level=0,
            hand=hand_add,
            pump_speed=int(speed),
            selected=selected_ingredient,
            cost=int(ingredient_cost),
            unit=unit,
        )

    def get_recipe_field_data(self, w: Ui_MainWindow) -> RecipeInput:
        """Return [name, selected, [ingredients], [volumes], enabled, virgin]."""
        recipe_name: str = w.LECocktail.text().strip()
        selected_recipe = self.get_list_widget_selection(w.LWRezepte)
        # this is also a str, because user may type non int char into box
        ingredient_volumes = self.get_lineedit_text(self.get_lineedits_recipe(w))
        ingredient_names = self.get_current_combobox_items(self.get_comboboxes_recipes(w))
        ingredient_order = self.get_lineedit_text(self.get_lineedits_recipe_order(w))
        enabled = w.CHBenabled.isChecked()
        virgin = w.offervirgin_checkbox.isChecked()
        return RecipeInput(
            recipe_name,
            selected_recipe,
            ingredient_names,
            ingredient_volumes,
            ingredient_order,
            enabled,
            virgin,
        )

    def remove_recipe_from_list_widget(self, w: Ui_MainWindow, recipe_name: str) -> None:
        """Remove a recipe from the list widget."""
        self.delete_list_widget_item(w.LWRezepte, recipe_name)

    def validate_ingredient_data(self, w: Ui_MainWindow) -> bool:
        """Validate the data from the ingredient window."""
        ing_input = self.get_ingredient_fields(w)
        if self._lineedit_is_missing(
            [
                ing_input.ingredient_name,
                ing_input.alcohol_level,
                ing_input.volume,
                ing_input.ingredient_cost,
                ing_input.pump_speed,
            ]
        ):
            self.say_some_value_missing()
            return False
        if self._lineedit_is_no_int(
            [
                ing_input.alcohol_level,
                ing_input.volume,
                ing_input.ingredient_cost,
                ing_input.pump_speed,
            ]
        ):
            self.say_needs_to_be_int()
            return False
        max_alcohol_level = 100
        if int(ing_input.alcohol_level.text()) > max_alcohol_level:
            self.say_alcohol_level_max_limit()
            return False
        # if the unit is other than ml, the ingredient need to be handadd
        if ing_input.unit.text().strip() != "ml" and not ing_input.hand_add.isChecked():
            self.say_ingredient_must_be_handadd()
            return False
        return True

    def get_ingredient_window_data(self, w: Ui_addingredient) -> tuple[str, int]:
        """Return the needed data from the ingredient window."""
        ingredient_name = self.get_list_widget_selection(w.ingredient_selection)
        volume = int(w.LAmount.text())
        return ingredient_name, volume

    def _lineedit_is_missing(self, lineedit_list: list[QLineEdit]) -> bool:
        """Check if a lineedit is empty."""
        return any(lineedit.text().strip() == "" for lineedit in lineedit_list)

    def _lineedit_is_no_int(self, lineedit_list: list[QLineEdit]) -> bool:
        """Check if a lineedit is no valid int."""
        for lineedit in lineedit_list:
            try:
                int(lineedit.text())
            except ValueError:
                return True
        return False

    ###########################
    # UI "MANIPULATE" METHODS #
    ###########################
    # Misc
    def change_input_value(
        self,
        label: QLabel | QLineEdit,
        minimal: int = 0,
        maximal: int = 1000,
        delta: int = 10,
        side_effect: Callable | None = None,
    ) -> None:
        """Increase or decreases the value by a given amount in the boundaries.

        Also executes a side effect function, if one is given.
        """
        try:
            value_ = int(label.text(), base=10)
            value_ = value_ + delta
            value_ = min(maximal, max(minimal, (value_ // delta) * delta))
        except ValueError:
            value_ = maximal if delta > 0 else minimal
        label.setText(str(value_))
        if side_effect is not None:
            side_effect()

    def set_display_settings(self, window_object: QWidget, resize: bool = True) -> None:
        """Check dev environment, adjust cursor and resize accordingly, if resize is wished."""
        if not cfg.UI_DEVENVIRONMENT:
            window_object.setCursor(Qt.BlankCursor)  # type: ignore
        if resize:
            window_object.setFixedSize(cfg.UI_WIDTH, cfg.UI_HEIGHT)
            window_object.resize(cfg.UI_WIDTH, cfg.UI_HEIGHT)

    def initialize_window_object(self, window_object: QWidget, x_pos: int = 0, y_pos: int = 0) -> None:
        """Initialize the window, set according flags, sets icon and stylesheet."""
        window_object.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint  # type: ignore
        )
        window_object.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        self.inject_stylesheet(window_object)
        icon_path = str(APP_ICON_FILE)
        window_object.setWindowIcon(QIcon(icon_path))
        window_object.move(x_pos, y_pos)

    def inject_stylesheet(self, window_object: QWidget) -> None:
        """Add the central stylesheet to the gui."""
        style_file = f"{cfg.MAKER_THEME}.css"
        with (STYLE_FOLDER / style_file).open(encoding="utf-8") as file_handler:
            window_object.setStyleSheet(file_handler.read())

    def set_tab_width(self, mainscreen: MainScreen) -> None:
        """Hack to set tabs to full screen width, inheritance, change the with to approximately match full width."""
        total_width = mainscreen.frameGeometry().width()
        first_tab_width = 40
        # especially on the rpi, we need a little bit more space than mathematically calculated
        width_buffer = 15
        width = round((total_width - first_tab_width) / 4, 0) - width_buffer
        mainscreen.tabWidget.setStyleSheet(  # type: ignore
            "QTabBar::tab {"
            + f"width: {width}px;"
            + "}"
            + "QTabBar::tab:first {"
            + f"width: {first_tab_width}px;"
            + "padding: 5px 0px 5px 15px;}"
        )

    # TabWidget
    def set_tabwidget_tab(
        self, w: Ui_MainWindow, tab: Literal["search", "maker", "ingredients", "recipes", "bottles"]
    ) -> None:
        """Set the tabwidget to the given tab.

        tab: ['maker', 'ingredients', 'recipes', 'bottles'].
        """
        tabs = {"search": 0, "maker": 1, "ingredients": 2, "recipes": 3, "bottles": 4}
        w.tabWidget.setCurrentIndex(tabs.get(tab, 1))

    def reset_alcohol_factor(self) -> None:
        """Set the alcohol slider to default (100%) value."""
        shared.alcohol_factor = 1.0

    # LineEdit
    def clean_multiple_lineedit(self, lineedit_list: list[QLineEdit]) -> None:
        """Clear a list of line edits."""
        for lineedit in lineedit_list:
            lineedit.clear()

    def fill_multiple_lineedit(self, lineedit_list: list[QLineEdit], text_list: Sequence[str | int]) -> None:
        """Fill a list of line edits."""
        for lineedit, text in zip(lineedit_list, text_list):
            lineedit.setText(str(text))

    # Combobox
    def fill_single_combobox(
        self,
        combobox: QComboBox,
        item_list: list[str],
        clear_first: bool = False,
        sort_items: bool = True,
        first_empty: bool = True,
    ) -> None:
        """Fill a combobox with given items, with the option to sort and fill a empty element as first element."""
        if clear_first:
            combobox.clear()
        if combobox.count() == 0 and first_empty:
            combobox.addItem("")
        combobox.addItems(item_list)
        if sort_items:
            combobox.model().sort(0)

    def fill_multiple_combobox(
        self,
        combobox_list: list[QComboBox],
        item_list: list[str],
        clear_first: bool = False,
        sort_items: bool = True,
        first_empty: bool = True,
    ) -> None:
        """Fill multiple comboboxes with identical items, can sort and insert filler as first item."""
        for combobox in combobox_list:
            self.fill_single_combobox(combobox, item_list, clear_first, sort_items, first_empty)

    def fill_multiple_combobox_individually(
        self,
        combobox_list: list[QComboBox],
        list_of_item_list: list[list[str]],
        clear_first: bool = False,
        sort_items: bool = True,
        first_empty: bool = True,
    ) -> None:
        """Fill multiple comboboxes with different items, can sort and insert filler as first item."""
        for combobox, item_list in zip(combobox_list, list_of_item_list):
            self.fill_single_combobox(combobox, item_list, clear_first, sort_items, first_empty)

    def delete_single_combobox_item(self, combobox: QComboBox, item: str) -> None:
        """Delete the given item from a combobox."""
        index = combobox.findText(item, Qt.MatchFixedString)  # type: ignore
        if index >= 0:
            combobox.removeItem(index)

    # This seems to be currently unused
    def delete_multiple_combobox_item(self, combobox: QComboBox, item_list: list[str]) -> None:
        """Delete the given items from a combobox."""
        for item in item_list:
            self.delete_single_combobox_item(combobox, item)

    def delete_item_in_multiple_combobox(self, combobox_list: list[QComboBox], item: str) -> None:
        """Delete the given item from multiple comboboxes."""
        for combobox in combobox_list:
            self.delete_single_combobox_item(combobox, item)

    def set_multiple_combobox_to_top_item(self, combobox_list: list[QComboBox]) -> None:
        """Set the list of comboboxes to the top item."""
        for combobox in combobox_list:
            combobox.setCurrentIndex(0)

    def set_multiple_combobox_items(self, combobox_list: list[QComboBox], items_to_set: list[str]) -> None:
        """Set a list of comboboxes to the according item."""
        for combobox, item in zip(combobox_list, items_to_set):
            self.set_combobox_item(combobox, item)

    def set_combobox_item(self, combobox: QComboBox, item: str) -> None:
        """Set the combobox to the given item."""
        index = combobox.findText(item, Qt.MatchFixedString)  # type: ignore
        combobox.setCurrentIndex(index)

    def adjust_bottle_comboboxes(self, combobox_list: list[QComboBox], old_item: str, new_item: str) -> None:
        """Remove the old item name and add new one in given comboboxes, sorting afterwards."""
        for combobox in combobox_list:
            if (old_item != "") and (combobox.findText(old_item, Qt.MatchFixedString) < 0):  # type: ignore
                combobox.addItem(old_item)
            if (new_item != "") and (new_item != combobox.currentText()):
                self.delete_single_combobox_item(combobox, new_item)
            combobox.model().sort(0)

    def rename_single_combobox(self, combobox: QComboBox, old_item: str, new_item: str) -> None:
        """Rename the old item to new one in given box."""
        index = combobox.findText(old_item, Qt.MatchFixedString)  # type: ignore
        if index >= 0:
            combobox.setItemText(index, new_item)
            combobox.model().sort(0)

    def rename_multiple_combobox(self, combobox_list: list[QComboBox], old_item: str, new_item: str) -> None:
        """Rename an item in multiple comboboxes."""
        for combobox in combobox_list:
            self.rename_single_combobox(combobox, old_item, new_item)

    # buttons / toggle buttons
    def untoggle_buttons(self, button_list: list[QPushButton]) -> None:
        """Set toggle to false in given button list."""
        for button in button_list:
            button.setChecked(False)

    # progress bars
    def set_progress_bar_values(self, progress_bar_list: list[QProgressBar], value_list: list[int]) -> None:
        """Set values of progress bars to given value."""
        for progress_bar, value in zip(progress_bar_list, value_list):
            progress_bar.setValue(value)

    # list widget
    def unselect_list_widget_items(self, list_widget: QListWidget) -> None:
        """Unselect all items in the list widget."""
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(False)

    def select_list_widget_item(self, list_widget: QListWidget, to_select: str | Cocktail) -> None:
        """Select the first item in the list widget."""
        if isinstance(to_select, Cocktail):
            to_select = to_select.name
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            data = item.data(Qt.UserRole)  # type: ignore
            current_name = data.name if data else item.text()
            if current_name == to_select:
                list_widget.setCurrentItem(item)
                break

    def delete_list_widget_item(self, list_widget: QListWidget, item: str) -> None:
        """Delete an item in the list widget."""
        index_to_delete = list_widget.findItems(item, Qt.MatchExactly)  # type: ignore
        if len(index_to_delete) > 0:
            for index in index_to_delete:
                list_widget.takeItem(list_widget.row(index))

    def fill_list_widget(self, list_widget: QListWidget, item_list: list[str] | list[Cocktail]) -> None:
        """Add item list to list widget."""
        for item in item_list:
            lw_item = self._generate_list_widget_item(item)
            list_widget.addItem(lw_item)

    def _generate_list_widget_item(self, item_data: str | Cocktail) -> QListWidgetItem:
        """Add the element to the list widget item.

        If is is a cocktail object, build in the virgin possibility as indicator.
        """
        if isinstance(item_data, Cocktail):
            cocktail_icon = QIcon()
            if item_data.virgin_available:
                cocktail_icon = ICONS.generate_icon(ICONS.presets.virgin, ICONS.color.primary, ICONS.color.secondary)
            lw_item = QListWidgetItem(cocktail_icon, item_data.name)

        else:
            lw_item = QListWidgetItem(item_data)
        lw_item.setData(Qt.UserRole, item_data)  # type: ignore
        return lw_item

    def clear_list_widget(self, list_widget: QListWidget) -> None:
        """Clear the given list widget."""
        list_widget.clear()

    def clear_list_widget_recipes(self, w: Ui_MainWindow) -> None:
        """Clear the recipes list widget."""
        w.LWRezepte.clear()

    def clear_list_widget_ingredients(self, w: Ui_MainWindow) -> None:
        """Clear the ingredients list widget."""
        w.LWZutaten.clear()

    def fill_list_widget_recipes(self, w: Ui_MainWindow, recipe_names: list[str]) -> None:
        """Fill the recipe list widget with given recipes."""
        self.fill_list_widget(w.LWRezepte, recipe_names)

    # checkboxes
    def set_checkbox_value(self, checkbox: QCheckBox, value: int | bool) -> None:
        """Set the checked state of the checkbox to given value."""
        checkbox.setChecked(bool(value))

    # Layouts
    def delete_items_of_layout(self, layout: QLayout | None = None) -> None:
        """Recursively delete all items of the given layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)  # type: ignore
                else:
                    self.delete_items_of_layout(item.layout())

    def _decide_rounding(self, val: float, threshold: int = 8) -> int | float:
        """Get the right rounding for numbers displayed to the user."""
        if val >= threshold:
            return int(val)
        return round(val, 1)

    def _set_strike_through(self, element: QWidget, strike_through: bool) -> None:
        """Set the strike through property of the font."""
        font = element.font()
        font.setStrikeOut(strike_through)
        element.setFont(font)

    def _set_underline(self, element: QWidget, underline: bool) -> None:
        """Set the strike through property of the font."""
        font = element.font()
        font.setUnderline(underline)
        element.setFont(font)

    def clear_recipe_data_recipes(self, w: Ui_MainWindow, select_other_item: bool) -> None:
        """Clear the recipe data in recipe view, only clears selection if no other item was selected."""
        w.LECocktail.clear()
        w.offervirgin_checkbox.setChecked(False)
        if not select_other_item:
            w.LWRezepte.clearSelection()
        self.set_multiple_combobox_to_top_item(self.get_comboboxes_recipes(w))
        self.clean_multiple_lineedit(self.get_lineedits_recipe(w))
        line_edit_order = self.get_lineedits_recipe_order(w)
        self.fill_multiple_lineedit(line_edit_order, [1] * len(line_edit_order))

    def set_recipe_data(self, w: Ui_MainWindow, cocktail: Cocktail) -> None:
        """Fill the recipe data in the recipe view with the cocktail object."""
        w.CHBenabled.setChecked(bool(cocktail.enabled))
        w.offervirgin_checkbox.setChecked(bool(cocktail.virgin_available))
        ingredients = cocktail.ingredients
        names = [x.name for x in ingredients]
        volumes = [x.amount for x in ingredients]
        order = [x.recipe_order for x in ingredients]
        self.set_multiple_combobox_items(self.get_comboboxes_recipes(w)[: len(names)], names)
        self.fill_multiple_lineedit(self.get_lineedits_recipe(w)[: len(volumes)], volumes)
        self.fill_multiple_lineedit(self.get_lineedits_recipe_order(w)[: len(order)], order)
        w.LECocktail.setText(cocktail.name)

    def update_maker_view(self, w: MainScreen) -> None:
        """Refresh the maker view, sets tab also to maker and not selection."""
        w.cocktail_view.populate_cocktails()
        w.container_maker.setCurrentWidget(w.cocktail_view)

    # Some more "specific" function, not using generic but specified field sets
    def set_label_bottles(self, w: Ui_MainWindow, label_names: list[str]) -> None:
        """Set the bottle label text to given names."""
        labels = self.get_label_bottles(w)
        self.fill_multiple_lineedit(labels, label_names)  # type: ignore

    # Migration from supporter.py
    def get_pushbuttons_newbottle(self, w: Ui_MainWindow, get_all: bool = False) -> list[QPushButton]:
        """Return all new bottles toggle button objects."""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"PBneu{x}") for x in range(1, number + 1)]

    def get_levelbar_bottles(self, w: Ui_MainWindow, get_all: bool = False) -> list[QProgressBar]:
        """Return all bottles progress bar objects."""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"ProBBelegung{x}") for x in range(1, number + 1)]

    def get_comboboxes_bottles(self, w: Ui_MainWindow, get_all: bool = False) -> list[QComboBox]:
        """Return all bottles combo box objects."""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"CBB{x}") for x in range(1, number + 1)]

    def get_comboboxes_recipes(self, w: Ui_MainWindow) -> list[QComboBox]:
        """Return all recipe combo box objects."""
        return [getattr(w, f"CBR{x}") for x in range(1, 9)]

    def get_lineedits_recipe(self, w: Ui_MainWindow) -> list[QLineEdit]:
        """Return all recipe line edit objects."""
        return [getattr(w, f"LER{x}") for x in range(1, 9)]

    def get_lineedits_recipe_order(self, w: Ui_MainWindow) -> list[QLineEdit]:
        """Return all recipe line edit objects."""
        return [getattr(w, f"line_edit_recipe_order_{x}") for x in range(1, 9)]

    def get_ingredient_fields(self, w: Ui_MainWindow) -> IngredientInputFields:
        """Return all needed Elements for Ingredients."""
        return IngredientInputFields(
            w.line_edit_ingredient_name,
            w.LWZutaten,
            w.LEGehaltRezept,
            w.LEFlaschenvolumen,
            w.line_edit_ingredient_cost,
            w.CHBHand,
            w.line_edit_pump_speed,
            w.line_edit_ingredient_unit,
        )

    def get_label_bottles(self, w: Ui_MainWindow, get_all: bool = False) -> list[QLabel]:
        """Return all bottles label objects."""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"LBelegung{x}") for x in range(1, number + 1)]

    def get_labels_maker_volume(self, w: Ui_MainWindow) -> list[QLabel]:
        """Return all maker label objects for volumes of ingredients."""
        return [getattr(w, f"LMZutat{x}") for x in range(1, 10)]

    def get_labels_maker_ingredients(self, w: Ui_MainWindow) -> list[QLabel]:
        """Return all maker label objects for ingredient name."""
        return [getattr(w, f"LZutat{x}") for x in range(1, 10)]

    def get_number_label_bottles(self, w: Ui_MainWindow, get_all: bool = False) -> list[QLabel]:
        """Return all label object for the number of the bottle."""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"bottleLabel{x}") for x in range(1, number + 1)]

    def adjust_bottle_number_displayed(self, w: MainScreen) -> None:
        """Remove the UI elements if not all ten bottles are used per config."""
        # give the ui a little time to build up, it might happen that we get a
        # QPaintDevice: Cannot destroy paint device that is being painted otherwise
        time.sleep(0.1)
        used_bottles = cfg.choose_bottle_number()
        # This needs to be done to get rid of registered bottles in the then removed bottles
        all_bottles = DB_COMMANDER.get_ingredient_names_at_bottles()
        DB_COMMANDER.set_bottle_order(all_bottles[:used_bottles] + [""] * (MAX_SUPPORTED_BOTTLES - used_bottles))
        comboboxes_bottles = self.get_comboboxes_bottles(w, True)
        self.set_multiple_combobox_to_top_item(comboboxes_bottles[used_bottles::])
        to_adjust: list[list[QPushButton] | list[QProgressBar] | list[QLabel] | list[QComboBox]] = [
            self.get_pushbuttons_newbottle(w, True),
            self.get_levelbar_bottles(w, True),
            comboboxes_bottles,
            self.get_label_bottles(w, True),
            self.get_number_label_bottles(w, True),
        ]
        for elements in to_adjust:
            for element in elements[used_bottles::]:
                element.hide()  # Hide element first
                element.deleteLater()
            QApplication.processEvents()

    def set_ingredient_add_label(self, w: Ui_MainWindow, item_selected: bool) -> None:
        """Change the label of the ingredient button."""
        self._choose_button_label(w.PBZutathinzu, item_selected)

    def set_recipe_add_label(self, w: Ui_MainWindow, item_selected: bool) -> None:
        """Change the label of the ingredient button."""
        self._choose_button_label(w.PBRezepthinzu, item_selected)

    def _choose_button_label(self, button: QPushButton, item_selected: bool) -> None:
        """Chooses the right labeling for the button."""
        if item_selected:
            button.setText(UI_LANGUAGE.get_change_text())
        else:
            button.setText(UI_LANGUAGE.get_add_text())


DP_CONTROLLER = DisplayController()
