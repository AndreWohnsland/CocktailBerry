from typing import Callable, List, Literal, Optional, Tuple, Union
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QWidget, QComboBox, QLabel,
    QLineEdit, QPushButton, QListWidget,
    QCheckBox, QMainWindow, QProgressBar,
    QListWidgetItem, QLayout,
    QStyledItemDelegate, QStyleOptionViewItem
)

from src.filepath import STYLE_FOLDER, APP_ICON_FILE
from src.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import DialogHandler, UI_LANGUAGE
from src.models import Cocktail, Ingredient
from src.config_manager import shared
from src import MAX_SUPPORTED_BOTTLES
from src.ui_elements.cocktailmanager import Ui_MainWindow
from src.ui_elements.bonusingredient import Ui_addingredient
from src.ui.icons import ICONS


class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.decorationPosition = QStyleOptionViewItem.Right  # type: ignore
        super().paint(painter, option, index)


class DisplayController(DialogHandler):
    """ Controller Class to get Values from the UI"""

    ########################
    # UI "EXTRACT" METHODS #
    ########################
    def get_current_combobox_items(self, combobox_list: List[QComboBox]) -> List[str]:
        """Get a list of the current combo box items"""
        return [combobox.currentText() for combobox in combobox_list]

    def get_toggle_status(self, button_list: List[QPushButton]) -> List[bool]:
        """Get a list of if the buttons are checked"""
        return [button.isChecked() for button in button_list]

    def get_lineedit_text(self, lineedit_list: List[QLineEdit]) -> List[str]:
        """Get a list of the text of the lineedits"""
        return [lineedit.text().strip() for lineedit in lineedit_list]

    def get_list_widget_selection(self, list_widget: QListWidget) -> str:
        """Returns the current selected item of the list widget"""
        selected = list_widget.selectedItems()
        if not selected:
            return ""
        # use selected items because currentItem is sometimes still last and not the current one ...
        # The widget got only single select, so there is always (if there is a selection) one item
        first_selected = selected[0]
        user_data = first_selected.data(Qt.UserRole)  # type: ignore
        if user_data:
            # If the user data is a cocktail object, return the name, else the user data
            # Usually the data should be a cocktail object, but fallback if it may set differently
            return user_data.name if isinstance(user_data, Cocktail) else user_data
        return first_selected.text()

    def get_list_widget_items(self, list_widget: QListWidget) -> Union[List[str], List[Cocktail]]:
        """Returns the items of the list widget"""
        list_widget_data = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            data = item.data(Qt.UserRole)  # type: ignore
            if data:
                list_widget_data.append(data)
            else:
                list_widget_data.append(item.text())
        return list_widget_data

    def get_ingredient_data(self, w: Ui_MainWindow):
        """Returns an Ingredient Object from the ingredient data fields"""
        line_edits, checkbox_hand, checkbox_slow, list_widget = self.get_ingredient_fields(w)
        ingredient_name, alcohol_level, volume = self.get_lineedit_text(list(line_edits))
        hand_add = checkbox_hand.isChecked()
        is_slow = checkbox_slow.isChecked()
        selected_ingredient = self.get_list_widget_selection(list_widget)
        return Ingredient(
            id=-1,
            name=ingredient_name,
            alcohol=int(alcohol_level),
            bottle_volume=int(volume),
            fill_level=0,
            hand=hand_add,
            slow=is_slow,
            selected=selected_ingredient
        )

    def get_cocktail_data(self, w: Ui_MainWindow) -> Tuple[str, int, float]:
        """Returns [name, volume, factor] from maker"""
        cocktail_volume = shared.cocktail_volume
        alcohol_factor = shared.alcohol_factor
        # If virgin is selected, just set alcohol_factor to 0
        if w.virgin_checkbox.isChecked():
            alcohol_factor = 0.0
        cocktail_name = self.get_list_widget_selection(w.LWMaker)
        return cocktail_name, cocktail_volume, alcohol_factor

    def get_recipe_field_data(self, w: Ui_MainWindow) -> Tuple[str, str, List[str], List[str], int, int]:
        """ Return [name, selected, [ingredients], [volumes], enabled, virgin] """
        recipe_name: str = w.LECocktail.text().strip()
        selected_recipe = self.get_list_widget_selection(w.LWRezepte)
        # this is also a str, because user may type non int char into box
        ingredient_volumes = self.get_lineedit_text(self.get_lineedits_recipe(w))
        ingredient_names = self.get_current_combobox_items(self.get_comboboxes_recipes(w))
        enabled = int(w.CHBenabled.isChecked())
        virgin = int(w.offervirgin_checkbox.isChecked())
        return recipe_name, selected_recipe, ingredient_names, ingredient_volumes, enabled, virgin

    def validate_ingredient_data(self, w: Ui_MainWindow) -> bool:
        """Validate the data from the ingredient window"""
        line_edits, *_ = self.get_ingredient_fields(w)
        lineedit_list = line_edits
        if self._lineedit_is_missing(list(lineedit_list)):
            self.say_some_value_missing()
            return False
        _, ingredient_percentage, ingredient_volume = lineedit_list
        if self._lineedit_is_no_int([ingredient_percentage, ingredient_volume]):
            self.say_needs_to_be_int()
            return False
        if int(ingredient_percentage.text()) > 100:
            self.say_alcohol_level_max_limit()
            return False
        return True

    def get_ingredient_window_data(self, w: Ui_addingredient) -> Tuple[str, int]:
        """Returns the needed data from the ingredient window"""
        ingredient_name = self.get_list_widget_selection(w.ingredient_selection)
        volume = int(w.LAmount.text())
        return ingredient_name, volume

    def _lineedit_is_missing(self, lineedit_list: List[QLineEdit]) -> bool:
        """Checks if a lineedit is empty"""
        for lineedit in lineedit_list:
            if lineedit.text().strip() == "":
                return True
        return False

    def _lineedit_is_no_int(self, lineedit_list: List[QLineEdit]) -> bool:
        """Checks if a lineedit is no valid int"""
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
        self, label: Union[QLabel, QLineEdit], minimal=0, maximal=1000,
        delta=10, side_effect: Optional[Callable] = None
    ):
        """ increases or decreases the value by a given amount in the boundaries
        Also executes a side effect function, if one is given
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

    def set_display_settings(self, window_object: QWidget, resize=True):
        """Checks dev environment, adjust cursor and resize accordingly, if resize is wished"""
        if not cfg.UI_DEVENVIRONMENT:
            window_object.setCursor(Qt.BlankCursor)  # type: ignore
        if resize:
            window_object.setFixedSize(cfg.UI_WIDTH, cfg.UI_HEIGHT)
            window_object.resize(cfg.UI_WIDTH, cfg.UI_HEIGHT)

    def initialize_window_object(self, window_object: QWidget, x_pos: int = 0, y_pos: int = 0):
        """Initialize the window, set according flags, sets icon and stylesheet"""
        window_object.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint  # type: ignore
        )
        window_object.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        self.inject_stylesheet(window_object)
        icon_path = str(APP_ICON_FILE)
        window_object.setWindowIcon(QIcon(icon_path))
        window_object.move(x_pos, y_pos)

    def inject_stylesheet(self, window_object: QWidget):
        """Adds the central stylesheet to the gui"""
        style_file = f"{cfg.MAKER_THEME}.css"
        with open(STYLE_FOLDER / style_file, "r", encoding="utf-8") as file_handler:
            window_object.setStyleSheet(file_handler.read())

    def set_tab_width(self, mainscreen: QMainWindow):
        """Hack to set tabs to full screen width, inheritance, change the with to approximately match full width"""
        total_width = mainscreen.frameGeometry().width()
        width = round(total_width / 4, 0) - 10
        mainscreen.tabWidget.setStyleSheet(  # type: ignore
            "QTabBar::tab {" +
            f"width: {width}px;" + "}"
        )

    # TabWidget
    def set_tabwidget_tab(self, w: Ui_MainWindow, tab: Literal["maker", 'ingredients', 'recipes', 'bottles']):
        """Sets the tabwidget to the given tab.
        tab: ['maker', 'ingredients', 'recipes', 'bottles']
        """
        tabs = {
            "maker": 0,
            "ingredients": 1,
            "recipes": 2,
            "bottles": 3
        }
        w.tabWidget.setCurrentIndex(tabs.get(tab, 0))

    def reset_alcohol_factor(self):
        """Sets the alcohol slider to default (100%) value"""
        shared.alcohol_factor = 1.0

    def reset_virgin_setting(self, w: Ui_MainWindow):
        """Resets the virgin checkbox"""
        w.virgin_checkbox.setChecked(False)

    # LineEdit
    def clean_multiple_lineedit(self, lineedit_list: List[QLineEdit]):
        """Clear a list of line edits"""
        for lineedit in lineedit_list:
            lineedit.clear()

    def fill_multiple_lineedit(self, lineedit_list: List[QLineEdit], text_list: List[Union[str, int]]):
        """Fill a list of line edits"""
        for lineedit, text in zip(lineedit_list, text_list):
            lineedit.setText(str(text))

    # Combobox
    def fill_single_combobox(
            self, combobox: QComboBox, item_list: List[str],
            clear_first=False, sort_items=True, first_empty=True
    ):
        """Fill a combobox with given items, with the option to sort and fill a empty element as first element"""
        if clear_first:
            combobox.clear()
        if combobox.count() == 0 and first_empty:
            combobox.addItem("")
        combobox.addItems(item_list)
        if sort_items:
            combobox.model().sort(0)

    def fill_multiple_combobox(
            self, combobox_list: List[QComboBox], item_list: List[str],
            clear_first=False, sort_items=True, first_empty=True
    ):
        """Fill multiple comboboxes with identical items, can sort and insert filler as first item"""
        for combobox in combobox_list:
            self.fill_single_combobox(combobox, item_list, clear_first, sort_items, first_empty)

    def fill_multiple_combobox_individually(
        self, combobox_list: List[QComboBox], list_of_item_list: List[List[str]],
        clear_first=False, sort_items=True, first_empty=True
    ):
        """Fill multiple comboboxes with different items, can sort and insert filler as first item"""
        for combobox, item_list in zip(combobox_list, list_of_item_list):
            self.fill_single_combobox(combobox, item_list, clear_first, sort_items, first_empty)

    def delete_single_combobox_item(self, combobox: QComboBox, item: str):
        """Delete the given item from a combobox"""
        index = combobox.findText(item, Qt.MatchFixedString)  # type: ignore
        if index >= 0:
            combobox.removeItem(index)

    # This seems to be currently unused
    def delete_multiple_combobox_item(self, combobox: QComboBox, item_list: List[str]):
        """Delete the given items from a combobox"""
        for item in item_list:
            self.delete_single_combobox_item(combobox, item)

    def delete_item_in_multiple_combobox(self, combobox_list: List[QComboBox], item: str):
        """Delete the given item from multiple comboboxes"""
        for combobox in combobox_list:
            self.delete_single_combobox_item(combobox, item)

    def set_multiple_combobox_to_top_item(self, combobox_list: List[QComboBox]):
        """Set the list of comboboxes to the top item"""
        for combobox in combobox_list:
            combobox.setCurrentIndex(0)

    def set_multiple_combobox_items(self, combobox_list: List[QComboBox], items_to_set: List[str]):
        """Set a list of comboboxes to the according item"""
        for combobox, item in zip(combobox_list, items_to_set):
            self.set_combobox_item(combobox, item)

    def set_combobox_item(self, combobox: QComboBox, item: str):
        """Set the combobox to the given item"""
        index = combobox.findText(item, Qt.MatchFixedString)  # type: ignore
        combobox.setCurrentIndex(index)

    def adjust_bottle_comboboxes(self, combobox_list: List[QComboBox], old_item: str, new_item: str):
        """Remove the old item name and add new one in given comboboxes, sorting afterwards"""
        for combobox in combobox_list:
            if (old_item != "") and (combobox.findText(old_item, Qt.MatchFixedString) < 0):  # type: ignore
                combobox.addItem(old_item)
            if (new_item != "") and (new_item != combobox.currentText()):
                self.delete_single_combobox_item(combobox, new_item)
            combobox.model().sort(0)

    def rename_single_combobox(self, combobox: QComboBox, old_item: str, new_item: str):
        """Rename the old item to new one in given box"""
        index = combobox.findText(old_item, Qt.MatchFixedString)  # type: ignore
        if index >= 0:
            combobox.setItemText(index, new_item)
            combobox.model().sort(0)

    def rename_multiple_combobox(self, combobox_list: List[QComboBox], old_item: str, new_item: str):
        """Renames an item in multiple comboboxes"""
        for combobox in combobox_list:
            self.rename_single_combobox(combobox, old_item, new_item)

    # buttons / toggle buttons
    def untoggle_buttons(self, button_list: List[QPushButton]):
        """Set toggle to false in given button list"""
        for button in button_list:
            button.setChecked(False)

    # progress bars
    def set_progress_bar_values(self, progress_bar_list: List[QProgressBar], value_list: List[int]):
        """Set values of progress bars to given value"""
        for progress_bar, value in zip(progress_bar_list, value_list):
            progress_bar.setValue(value)

    # list widget
    def unselect_list_widget_items(self, list_widget: QListWidget):
        """Unselect all items in the list widget"""
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(False)

    def select_list_widget_item(self, list_widget: QListWidget, to_select: Union[str, Cocktail]):
        """Select the first item in the list widget"""
        if isinstance(to_select, Cocktail):
            to_select = to_select.name
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            data = item.data(Qt.UserRole)  # type: ignore
            if data:
                current_name = data.name
            else:
                current_name = item.text()
            if current_name == to_select:
                list_widget.setCurrentItem(item)
                break

    def delete_list_widget_item(self, list_widget: QListWidget, item: str):
        """Deletes an item in the list widget"""
        index_to_delete = list_widget.findItems(item, Qt.MatchExactly)  # type: ignore
        if len(index_to_delete) > 0:
            for index in index_to_delete:
                list_widget.takeItem(list_widget.row(index))

    def fill_list_widget(self, list_widget: QListWidget, item_list: Union[List[str], List[Cocktail]]):
        """Adds item list to list widget"""
        for item in item_list:
            lw_item = self._generate_list_widget_item(item)
            list_widget.addItem(lw_item)

    def _generate_list_widget_item(self, item_data: Union[str, Cocktail]):
        """Adds the element to the list widget item
        If is is a cocktail object, build in the virgin possibility as indicator"""
        if isinstance(item_data, Cocktail):
            cocktail_icon = QIcon()
            if item_data.virgin_available:
                cocktail_icon = ICONS.generate_icon(
                    ICONS.presets.virgin,
                    ICONS.color.primary,
                    ICONS.color.secondary
                )
            lw_item = QListWidgetItem(cocktail_icon, item_data.name)

        else:
            lw_item = QListWidgetItem(item_data)
        lw_item.setData(Qt.UserRole, item_data)  # type: ignore
        return lw_item

    def clear_list_widget(self, list_widget: QListWidget):
        """Clears the given list widget"""
        list_widget.clear()

    def clear_list_widget_maker(self, w: Ui_MainWindow):
        """Clears the maker list widget"""
        w.LWMaker.clear()

    def clear_list_widget_recipes(self, w: Ui_MainWindow):
        """Clears the recipes list widget"""
        w.LWRezepte.clear()

    def clear_list_widget_ingredients(self, w: Ui_MainWindow):
        """Clears the ingredients list widget"""
        w.LWZutaten.clear()

    def fill_list_widget_maker(self, w: Ui_MainWindow, recipe_names: List[Cocktail]):
        """Fill the maker list widget with given recipes"""
        self.fill_list_widget(w.LWMaker, recipe_names)

    def fill_list_widget_recipes(self, w: Ui_MainWindow, recipe_names: List[str]):
        """Fill the recipe list widget with given recipes"""
        self.fill_list_widget(w.LWRezepte, recipe_names)

    # checkboxes
    def set_checkbox_value(self, checkbox: QCheckBox, value: Union[int, bool]):
        """Set the checked state of the checkbox to given value"""
        checkbox.setChecked(bool(value))

    # Layouts
    def delete_items_of_layout(self, layout: Optional[QLayout] = None):
        """Recursively delete all items of the given layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)  # type: ignore
                else:
                    self.delete_items_of_layout(item.layout())

    # others
    def fill_recipe_data_maker(self, w: Ui_MainWindow, cocktail: Cocktail, total_volume: int):
        """Fill all the maker view data with the data from the given cocktail"""
        w.LAlkoholname.setText(cocktail.name)
        display_volume = self._decide_rounding(total_volume * cfg.EXP_MAKER_FACTOR, 20)
        w.LMenge.setText(f"{display_volume} {cfg.EXP_MAKER_UNIT}")
        w.LAlkoholgehalt.setText(f"{cocktail.adjusted_alcohol:.1f}%")
        display_data = cocktail.machineadds
        hand = cocktail.handadds
        # Activates or deactivates the virgin checkbox, depending on the virgin flag
        w.virgin_checkbox.setEnabled(cocktail.virgin_available)
        # Styles does not work on strikeout, so we use internal qt things
        # To be precise, they do work at start, but does not support dynamic changes
        self._set_strike_through(w.virgin_checkbox, not cocktail.virgin_available)
        # when there is handadd, also build some additional data
        if hand:
            display_data.extend([Ingredient(-1, "", 0, 0, 0, False, False)] + hand)
        fields_ingredient = self.get_labels_maker_ingredients(w)
        fields_volume = self.get_labels_maker_volume(w)
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

    def _set_strike_through(self, element: QWidget, strike_through: bool):
        """Set the strike through property of the font"""
        font = element.font()
        font.setStrikeOut(strike_through)
        element.setFont(font)

    def _set_underline(self, element: QWidget, underline: bool):
        """Set the strike through property of the font"""
        font = element.font()
        font.setUnderline(underline)
        element.setFont(font)

    def clear_recipe_data_maker(self, w: Ui_MainWindow, select_other_item=True):
        """Clear the cocktail data in the maker view, only clears selection if no other item was selected"""
        w.LAlkoholgehalt.setText("")
        w.LAlkoholname.setText(UI_LANGUAGE.get_cocktail_dummy())
        w.LMenge.setText("")
        w.virgin_checkbox.setChecked(False)
        # Also resets the alcohol factor
        self.reset_alcohol_factor()
        if not select_other_item:
            w.LWMaker.clearSelection()
        for field_ingredient, field_volume in zip(
            self.get_labels_maker_ingredients(w),
            self.get_labels_maker_volume(w)
        ):
            field_ingredient.setText("")
            field_volume.setText("")

    def clear_recipe_data_recipes(self, w: Ui_MainWindow, select_other_item: bool):
        """Clear the recipe data in recipe view, only clears selection if no other item was selected"""
        w.LECocktail.clear()
        w.offervirgin_checkbox.setChecked(False)
        if not select_other_item:
            w.LWRezepte.clearSelection()
        self.set_multiple_combobox_to_top_item(self.get_comboboxes_recipes(w))
        self.clean_multiple_lineedit(self.get_lineedits_recipe(w))

    def remove_recipe_from_list_widgets(self, w: Ui_MainWindow, recipe_name: str):
        """Remove the recipe from the list widgets, suppress signals during process"""
        # block that trigger that no refetching of data (and shared.handadd overwrite) occurs
        w.LWRezepte.blockSignals(True)
        w.LWMaker.blockSignals(True)
        w.LWRezepte.clearSelection()
        w.LWMaker.clearSelection()
        self.delete_list_widget_item(w.LWRezepte, recipe_name)
        self.delete_list_widget_item(w.LWMaker, recipe_name)
        w.LWRezepte.blockSignals(False)
        w.LWMaker.blockSignals(False)

    def set_recipe_data(self, w: Ui_MainWindow, cocktail: Cocktail):
        """Fills the recipe data in the recipe view with the cocktail object"""
        w.CHBenabled.setChecked(bool(cocktail.enabled))
        w.offervirgin_checkbox.setChecked(bool(cocktail.virgin_available))
        ingredients = cocktail.ingredients
        names = [x.name for x in ingredients]
        volumes = [x.amount for x in ingredients]
        self.set_multiple_combobox_items(self.get_comboboxes_recipes(w)[: len(names)], names)
        self.fill_multiple_lineedit(self.get_lineedits_recipe(w)[: len(volumes)], volumes)  # type: ignore
        w.LECocktail.setText(cocktail.name)

    # Some more "specific" function, not using generic but specified field sets
    def set_label_bottles(self, w: Ui_MainWindow, label_names: List[str]):
        """Set the bottle label text to given names"""
        labels = self.get_label_bottles(w)
        self.fill_multiple_lineedit(labels, label_names)  # type: ignore

    # Migration from supporter.py
    def get_pushbuttons_newbottle(self, w: Ui_MainWindow, get_all=False) -> List[QPushButton]:
        """Returns all new bottles toggle button objects"""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"PBneu{x}") for x in range(1, number + 1)]

    def get_levelbar_bottles(self, w: Ui_MainWindow, get_all=False) -> List[QProgressBar]:
        """Returns all bottles progress bar objects"""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"ProBBelegung{x}") for x in range(1, number + 1)]

    def get_comboboxes_bottles(self, w: Ui_MainWindow, get_all=False) -> List[QComboBox]:
        """Returns all bottles combo box objects"""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"CBB{x}") for x in range(1, number + 1)]

    def get_comboboxes_recipes(self, w: Ui_MainWindow) -> List[QComboBox]:
        """Returns all recipe combo box objects"""
        return [getattr(w, f"CBR{x}") for x in range(1, 9)]

    def get_lineedits_recipe(self, w: Ui_MainWindow) -> List[QLineEdit]:
        """Returns all recipe line edit objects"""
        return [getattr(w, f"LER{x}") for x in range(1, 9)]

    def get_ingredient_fields(
        self, w: Ui_MainWindow
    ) -> Tuple[Tuple[QLineEdit, QLineEdit, QLineEdit], QCheckBox, QCheckBox, QListWidget]:
        """Returns [Name, Alcohol, Volume], CheckedHand, ListWidget Elements for Ingredients"""
        return (w.LEZutatRezept, w.LEGehaltRezept, w.LEFlaschenvolumen), w.CHBHand, w.check_slow_ingredient, w.LWZutaten

    def get_label_bottles(self, w: Ui_MainWindow, get_all=False) -> List[QLabel]:
        """Returns all bottles label objects"""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"LBelegung{x}") for x in range(1, number + 1)]

    def get_labels_maker_volume(self, w: Ui_MainWindow) -> List[QLabel]:
        """Returns all maker label objects for volumes of ingredients"""
        return [getattr(w, f"LMZutat{x}") for x in range(1, 10)]

    def get_labels_maker_ingredients(self, w: Ui_MainWindow) -> List[QLabel]:
        """Returns all maker label objects for ingredient name"""
        return [getattr(w, f"LZutat{x}") for x in range(1, 10)]

    def get_number_label_bottles(self, w: Ui_MainWindow, get_all=False) -> List[QLabel]:
        """Returns all label object for the number of the bottle"""
        number = cfg.choose_bottle_number(get_all)
        return [getattr(w, f"bottleLabel{x}") for x in range(1, number + 1)]

    def adjust_bottle_number_displayed(self, w: Ui_MainWindow):
        """Removes the UI elements if not all ten bottles are used per config"""
        used_bottles = cfg.choose_bottle_number()
        # This needs to be done to get rid of registered bottles in the then removed bottles
        all_bottles = DB_COMMANDER.get_ingredients_at_bottles()
        DB_COMMANDER.set_bottle_order(all_bottles[: used_bottles] + [""] * (MAX_SUPPORTED_BOTTLES - used_bottles))
        comboboxes_bottles = self.get_comboboxes_bottles(w, True)
        self.set_multiple_combobox_to_top_item(comboboxes_bottles[used_bottles::])
        to_adjust: list[Union[list[QPushButton], list[QProgressBar], list[QLabel], list[QComboBox]]] = [
            self.get_pushbuttons_newbottle(w, True),
            self.get_levelbar_bottles(w, True),
            comboboxes_bottles,
            self.get_label_bottles(w, True),
            self.get_number_label_bottles(w, True),
        ]
        for elements in to_adjust:
            for element in elements[used_bottles::]:
                element.deleteLater()

    def adjust_maker_label_size_cocktaildata(self, w: Ui_MainWindow):
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
        big_labels = [w.LAlkoholname]
        medium_labels = [w.LMenge, w.LAlkoholgehalt]
        small_labels = self.get_labels_maker_volume(w)
        small_labels_bold = self.get_labels_maker_ingredients(w)
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

    def set_ingredient_add_label(self, w: Ui_MainWindow, item_selected: bool):
        """Changes the label of the ingredient button"""
        self._choose_button_label(w.PBZutathinzu, item_selected)

    def set_recipe_add_label(self, w: Ui_MainWindow, item_selected: bool):
        """Changes the label of the ingredient button"""
        self._choose_button_label(w.PBRezepthinzu, item_selected)

    def _choose_button_label(self, button: QPushButton, item_selected: bool):
        """Chooses the right labeling for the button"""
        if item_selected:
            button.setText(UI_LANGUAGE.get_change_text())
        else:
            button.setText(UI_LANGUAGE.get_add_text())


DP_CONTROLLER = DisplayController()
