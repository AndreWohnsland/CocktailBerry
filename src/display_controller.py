from pathlib import Path
from typing import Any, Callable, List, Tuple, Union
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget

from src.database_commander import DB_COMMANDER
from src.dialog_handler import DialogHandler, UI_LANGUAGE
from src.models import Cocktail, Ingredient
from src.config_manager import shared
from src import MAX_SUPPORTED_BOTTLES

STYLE_FILE = Path(__file__).parents[0].absolute() / "ui" / "styles" / "styles.qss"


class DisplayController(DialogHandler):
    """ Controler Class to get Values from the UI"""

    ########################
    # UI "EXTRACT" METHODS #
    ########################
    def get_current_combobox_items(self, combobox_list: List[Any]) -> List[str]:
        """Get a list of the current combobox items"""
        return [combobox.currentText() for combobox in combobox_list]

    def get_toggle_status(self, button_list: List[Any]) -> List[bool]:
        """Get a list of if the buttons are checked"""
        return [button.isChecked() for button in button_list]

    def get_lineedit_text(self, lineedit_list: List[Any]) -> List[str]:
        """Get a list of the text of the lineedits"""
        return [lineedit.text().strip() for lineedit in lineedit_list]

    def get_list_widget_selection(self, list_widget) -> str:
        """Returns the curent selected item of the list widget"""
        if not list_widget.selectedItems():
            return ""
        return list_widget.currentItem().text()

    def get_ingredient_data(self, lineedit_list: List[Any], checkbox, list_widget):
        """Returns an Ingredient Object from the ingredient data fields"""
        ingredient_name, alcohollevel, volume = self.get_lineedit_text(lineedit_list)
        hand_add = checkbox.isChecked()
        selected_ingredient = ""
        if list_widget.selectedItems():
            selected_ingredient = list_widget.currentItem().text()
        return Ingredient(None, ingredient_name, int(alcohollevel), int(volume), None, hand_add, selected=selected_ingredient)

    def get_cocktail_data(self, w) -> Tuple[str, int, int]:
        """Returns [name, volume, factor] from maker"""
        cocktail_volume = int(w.LCustomMenge.text())
        # when pulling, the slider can reach every integer value (eg, 1,2,...)
        # but whe only want stepsize of *5 -> therefore it ranges from -5 to 5 but we
        # multiply by *5 to get an effective range from -25 to 25 with a stepsize of 5
        alcohol_faktor = 1 + (w.HSIntensity.value() * 5 / 100)
        cocktailname = ""
        if w.LWMaker.selectedItems():
            cocktailname = w.LWMaker.currentItem().text()
        return cocktailname, cocktail_volume, alcohol_faktor

    def get_recipe_field_data(self, w) -> Tuple[str, str, List[str], List[str], int, str]:
        """ Return [name, selected, [ingredients], [volumes], enabled, comment] """
        recipe_name = w.LECocktail.text().strip()
        selected_recipe = self.get_list_widget_selection(w.LWRezepte)
        # this is also a str, because user may type non int char into box
        ingredient_volumes = self.get_lineedit_text(self.get_lineedits_recipe(w))
        ingredient_names = self.get_current_combobox_items(self.get_comboboxes_recipes(w))
        enabled = int(w.CHBenabled.isChecked())
        comment = w.LEKommentar.text()
        return recipe_name, selected_recipe, ingredient_names, ingredient_volumes, enabled, comment

    def validate_ingredient_data(self, lineedit_list) -> bool:
        """Validate the data from the ingredient window"""
        if self.__lineedit_is_missing(lineedit_list):
            self.say_some_value_missing()
            return False
        _, ingredient_percentage, ingredient_volume = lineedit_list
        if self.__lineedit_is_no_int([ingredient_percentage, ingredient_volume]):
            self.say_needs_to_be_int()
            return False
        if int(ingredient_percentage.text()) > 100:
            self.say_alcohollevel_max_limit()
            return False
        return True

    def get_ingredient_window_data(self, w) -> Tuple[str, int]:
        """Returns the needed data from the ingredient window"""
        ingredient_name = w.CBingredient.currentText()
        volume = int(w.LAmount.text())
        return ingredient_name, volume

    def __check_password(self, lineedit):
        """Compares the given lineedit to the master password"""
        password = lineedit.text()
        lineedit.setText("")
        if password == self.UI_MASTERPASSWORD:
            return True
        return False

    def check_recipe_password(self, w):
        """Checks if the password in the recipe window is right"""
        return self.__check_password(w.LEpw)

    def check_bottles_password(self, w):
        """Checks if the password in the bottle window is right"""
        return self.__check_password(w.LECleanMachine)

    def check_ingredient_password(self, w):
        """Checks if the password in the ingredient window is right"""
        return self.__check_password(w.LEpw2)

    def __lineedit_is_missing(self, lineedit_list) -> bool:
        """Checks if a lineedit is empty"""
        for lineedit in lineedit_list:
            if lineedit.text().strip() == "":
                return True
        return False

    def __lineedit_is_no_int(self, lineedits) -> bool:
        """Checks if a lineedit is no valid int"""
        for lineedit in lineedits:
            try:
                int(lineedit.text())
            except ValueError:
                return True
        return False

    ###########################
    # UI "MANIPULATE" METHODS #
    ###########################
    # Misc
    def plusminus(self, label, operator: str, minimal=0, maximal=1000, delta=10, side_effect: Callable = None):
        """ increases or decreases the value by a given amount in the boundaries
        operator: '+' or '-'
        Also executes a sideeffect function, if one is given
        """
        try:
            value_ = int(label.text())
            value_ = value_ + (delta if operator == "+" else -delta)
            value_ = min(maximal, max(minimal, (value_ // delta) * delta))
        except ValueError:
            value_ = maximal if operator == "+" else minimal
        label.setText(str(value_))
        if side_effect is not None:
            side_effect()

    def set_display_settings(self, window_object: QWidget, resize=True):
        """Checks dev environment, adjust cursor and resize accordingly, if resize is wished
        Also injects the stylesheet.
        """
        if not self.UI_DEVENVIRONMENT:
            window_object.setCursor(Qt.BlankCursor)
        if resize:
            window_object.setFixedSize(self.UI_WIDTH, self.UI_HEIGHT)
            window_object.resize(self.UI_WIDTH, self.UI_HEIGHT)

    def inject_stylesheet(self, window_object: QWidget):
        """Adds the central stylesheet to the gui"""
        with open(STYLE_FILE, "r", encoding="utf-8") as filehandler:
            window_object.setStyleSheet(filehandler.read())

    def set_tab_width(self, mainscreen):
        """Hack to set tabs to full screen width, inheritance of custom tabBars dont work
        This is incredibly painfull, since all the CSS from the ui needs to be copied here,
        it will overwrite the whole class sheet and missing parts will not be used.
        Any changes to the .ui file for the tab needs to be applied here as well"""
        total_width = mainscreen.frameGeometry().width()
        width = round(total_width / 4, 0) - 10
        mainscreen.tabWidget.setStyleSheet(
            "QTabBar::tab {" +
            "background-color: rgb(97, 97, 97);" +
            "color: rgb(255, 255, 255);" +
            "border-width: 1px;" +
            "border-color: rgb(255, 255, 255);" +
            "border-style: solid;" +
            "border-top-left-radius: 10px;" +
            "border-top-right-radius: 10px;" +
            "padding: 5px 0px 5px 0px;" +
            f"width: {width}px;" + "}" +
            "QTabBar::tab:selected {" +
            "color: rgb(255, 255, 255);	" +
            "background-color: rgb(0, 123, 255)};"
        )

    # TabWidget
    def set_tabwidget_tab(self, w, tab: str):
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

    # Slider
    def __set_slider_value(self, slider, value):
        slider.setValue(value)

    def reset_alcohol_slider(self, w):
        """Sets the alcohol slider to defaul (100%) value"""
        self.__set_slider_value(w.HSIntensity, 0)

    # LineEdit
    def clean_multiple_lineedit(self, lineedit_list: List[Any]):
        """Clear a list of line edits"""
        for lineedit in lineedit_list:
            lineedit.clear()

    def fill_multiple_lineedit(self, lineedit_list: List[Any], text_list: List[Union[str, int]]):
        """Fill a list of line edits"""
        for lineedit, text in zip(lineedit_list, text_list):
            lineedit.setText(str(text))

    # Combobox
    def fill_single_combobox(self, combobox, itemlist: List[str], clear_first=False, sort_items=True, first_empty=True):
        """Fill a combobox with given items, with the option to sort and fill a empty element as first element"""
        if clear_first:
            combobox.clear()
        if combobox.count() == 0 and first_empty:
            combobox.addItem("")
        combobox.addItems(itemlist)
        if sort_items:
            combobox.model().sort(0)

    def fill_multiple_combobox(self, combobox_list: List[Any], itemlist: List[str],
                               clear_first=False, sort_items=True, first_empty=True):
        """Fill multiple comboboxes with identical items, can sort and insert filler as first item"""
        for combobox in combobox_list:
            self.fill_single_combobox(combobox, itemlist, clear_first, sort_items, first_empty)

    def fill_multiple_combobox_individually(self, combobox_list: List[Any], list_of_itemlist: List[List[str]],
                                            clear_first=False, sort_items=True, first_empty=True):
        """Fill multiple comboboxes with different items, can sort and insert filler as first item"""
        for combobox, itemlist in zip(combobox_list, list_of_itemlist):
            self.fill_single_combobox(combobox, itemlist, clear_first, sort_items, first_empty)

    def delete_single_combobox_item(self, combobox, item: str):
        """Delete the given item from a combobox"""
        index = combobox.findText(item, Qt.MatchFixedString)
        if index >= 0:
            combobox.removeItem(index)

    # This seeems to be currently unused
    def delete_multiple_combobox_item(self, combobox, itemlist: List[str]):
        """Delete the given items from a combobox"""
        for item in itemlist:
            self.delete_single_combobox_item(combobox, item)

    def delete_item_in_multiple_combobox(self, combobox_list: List[Any], item: str):
        """Delete the given item from multiple comboboxed"""
        for combobox in combobox_list:
            self.delete_single_combobox_item(combobox, item)

    def set_multiple_combobox_to_top_item(self, combobox_list: List[Any]):
        """Set the list of comboboxes to the top item"""
        for combobox in combobox_list:
            combobox.setCurrentIndex(0)

    def set_multiple_combobox_items(self, combobox_list: List[Any], items_to_set: List[str]):
        """Set a list of comboboxes to the according item"""
        for combobox, item in zip(combobox_list, items_to_set):
            self.set_combobox_item(combobox, item)

    def set_combobox_item(self, combobox, item: str):
        """Set the combobox to the given item"""
        index = combobox.findText(item, Qt.MatchFixedString)
        combobox.setCurrentIndex(index)

    def adjust_bottle_comboboxes(self, combobox_list: List[Any], old_item: str, new_item: str):
        """Remove the old itemname and add new one in given comboboxex, sorting afterwards"""
        for combobox in combobox_list:
            if (old_item != "") and (combobox.findText(old_item, Qt.MatchFixedString) < 0):
                combobox.addItem(old_item)
            if (new_item != "") and (new_item != combobox.currentText()):
                self.delete_single_combobox_item(combobox, new_item)
            combobox.model().sort(0)

    def rename_single_combobox(self, combobox, old_item: str, new_item: str):
        """Rename the old item to new one in given box"""
        index = combobox.findText(old_item, Qt.MatchFixedString)
        if index >= 0:
            combobox.setItemText(index, new_item)
            combobox.model().sort(0)

    def rename_multiple_combobox(self, combobox_list: List[Any], old_item: str, new_item: str):
        """Renames an item in multiple comboboxes"""
        for combobox in combobox_list:
            self.rename_single_combobox(combobox, old_item, new_item)

    # buttons / togglebuttons
    def untoggle_buttons(self, button_list: List[Any]):
        """Set toggle to false in given button list"""
        for button in button_list:
            button.setChecked(False)

    # progress bars
    def set_progress_bar_values(self, progress_bar_list: List[Any], value_list: List[int]):
        """Set values of progress bars to given value"""
        for progress_bar, value in zip(progress_bar_list, value_list):
            progress_bar.setValue(value)

    # listwidget
    def unselect_list_widget_items(self, list_widget: Any):
        """Unselect all items in the list widget"""
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(False)

    def delete_list_widget_item(self, list_widget: Any, item: str):
        """Deletes an item in the list widget"""
        index_to_delete = list_widget.findItems(item, Qt.MatchExactly)
        if len(index_to_delete) > 0:
            for index in index_to_delete:
                list_widget.takeItem(list_widget.row(index))

    def fill_list_widget(self, list_widget, item_list: List[str]):
        """Adds item list to list widget"""
        for item in item_list:
            list_widget.addItem(item)

    def clear_list_widget_maker(self, w):
        """Clears the maker list widget"""
        w.LWMaker.clear()

    def clear_list_widget_ingredients(self, w):
        """Clears the ingredients list widget"""
        w.LWZutaten.clear()

    def fill_list_widget_maker(self, w, recipe_names: List[str]):
        """Fill the maker list widget with given recipes"""
        self.fill_list_widget(w.LWMaker, recipe_names)

    def fill_list_widget_recipes(self, w, recipe_names: List[str]):
        """Fill the recipe list widget with given recipes"""
        self.fill_list_widget(w.LWRezepte, recipe_names)

    # checkboxes
    def set_checkbox_value(self, checkbox, value: Union[int, bool]):
        """Set the checked state of the checkbox to given value"""
        checkbox.setChecked(bool(value))

    # others
    def fill_recipe_data_maker(self, w, cocktail: Cocktail, total_volume: int):
        """Fill all the maker view data with the data from the given cocktail"""
        w.LAlkoholname.setText(cocktail.name)
        w.LMenge.setText(f"{total_volume} ml")
        w.LAlkoholgehalt.setText(f"{cocktail.adjusted_alcohol:.0f}%")
        display_data = cocktail.get_machineadds()
        hand = cocktail.get_handadds()
        # when there is handadd, also build some additional data
        # TODO: typing mixing here is probably not the best thing
        if hand:
            display_data.extend([""] + hand)
        fields_ingredient = self.get_labels_maker_ingredients(w)
        fields_volume = self.get_labels_maker_volume(w)
        for field_ingredient, field_volume, ing in zip(fields_ingredient, fields_volume, display_data):
            if isinstance(ing, str):
                ingredient_name = UI_LANGUAGE.get_add_self()
                field_ingredient.setStyleSheet("color: rgb(170, 170, 170);")  # margin-top: 5px;
            else:
                field_volume.setText(f" {ing.amount} ml")
                ingredient_name = ing.name
            field_ingredient.setText(f"{ingredient_name} ")

    def clear_recipe_data_maker(self, w, select_other_item=True):
        """Clear the cocktail data in the maker view, only clears selection if no other item was selected"""
        w.LAlkoholgehalt.setText("")
        w.LAlkoholname.setText(UI_LANGUAGE.get_cocktail_dummy())
        w.LMenge.setText("")
        if not select_other_item:
            w.LWMaker.clearSelection()
        for field_ingredient, field_volume in zip(self.get_labels_maker_ingredients(w), self.get_labels_maker_volume(w)):
            field_ingredient.setText("")
            field_ingredient.setStyleSheet("color: rgb(0, 123, 255)")
            field_volume.setText("")

    def clear_recipe_data_recipes(self, w, select_other_item: bool):
        """Clear the recipe data in recipe view, only clears selection if no other item was selected"""
        w.LECocktail.clear()
        w.LEKommentar.clear()
        if not select_other_item:
            w.LWRezepte.clearSelection()
        self.set_multiple_combobox_to_top_item(self.get_comboboxes_recipes(w))
        self.clean_multiple_lineedit(self.get_lineedits_recipe(w))
        shared.handaddlist = []

    def refill_recipes_list_widget(self, w, items: List[str]):
        """Clear and fill again the recipes list widget"""
        w.LWRezepte.clear()
        self.fill_list_widget(w.LWRezepte, items)

    def remove_recipe_from_list_widgets(self, w, recipe_name: str):
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

    def __set_recipe_handadd_comment(self, w, handadd_data: List[Ingredient]):
        """Build the comment for the view from the handadd data"""
        comment = ""
        for ing in handadd_data:
            comment += f"{ing.amount} ml {ing.name}, "
            shared.handaddlist.append(ing)
        comment = comment[:-2]
        w.LEKommentar.setText(comment)

    def set_recipe_data(self, w, cocktail: Cocktail):
        """Fills the recipe data in the recipe view with the cocktail object"""
        w.CHBenabled.setChecked(bool(cocktail.enabled))
        machine_adds = cocktail.get_machineadds()
        names = [x.name for x in machine_adds]
        volumes = [x.amount for x in machine_adds]
        self.set_multiple_combobox_items(self.get_comboboxes_recipes(w)[: len(names)], names)
        self.fill_multiple_lineedit(self.get_lineedits_recipe(w)[: len(volumes)], volumes)
        w.LECocktail.setText(cocktail.name)
        self.__set_recipe_handadd_comment(w, cocktail.get_handadds())

    # Some more "specific" function, not using generic but specified field sets
    def set_label_bottles(self, w, label_names: List[str]):
        """Set the bottle label text to given names"""
        labels = self.get_label_bottles(w)
        self.fill_multiple_lineedit(labels, label_names)

    # Migration from supporter.py
    def get_pushbottons_newbottle(self, w, get_all=False):
        """Returns all new bottles toggle button objects"""
        number = self._choose_bottle_number(get_all)
        return [getattr(w, f"PBneu{x}") for x in range(1, number + 1)]

    def get_levelbar_bottles(self, w, get_all=False):
        """Returns all bottles progress bar objects"""
        number = self._choose_bottle_number(get_all)
        return [getattr(w, f"ProBBelegung{x}") for x in range(1, number + 1)]

    def get_comboboxes_bottles(self, w, get_all=False):
        """Returns all bottles combo box objects"""
        number = self._choose_bottle_number(get_all)
        return [getattr(w, f"CBB{x}") for x in range(1, number + 1)]

    def get_comboboxes_recipes(self, w):
        """Returns all recipe combo box objects"""
        return [getattr(w, f"CBR{x}") for x in range(1, 8)]

    def get_lineedits_recipe(self, w):
        """Returns all recipe line edit objects"""
        return [getattr(w, f"LER{x}") for x in range(1, 8)]

    def get_ingredient_fields(self, w):
        """Returns [Name, Alcohol, Volume], CheckedHand, ListWidget Elements for Ingredients"""
        return [[w.LEZutatRezept, w.LEGehaltRezept, w.LEFlaschenvolumen], w.CHBHand, w.LWZutaten]

    def get_label_bottles(self, w, get_all=False):
        """Returns all bottles label objects"""
        number = self._choose_bottle_number(get_all)
        return [getattr(w, f"LBelegung{x}") for x in range(1, number + 1)]

    def get_labels_maker_volume(self, w):
        """Returns all maker label objects for volumes of ingredients"""
        return [getattr(w, f"LMZutat{x}") for x in range(1, 10)]

    def get_labels_maker_ingredients(self, w):
        """Returns all maker label objects for ingredient name"""
        return [getattr(w, f"LZutat{x}") for x in range(1, 10)]

    def get_numberlabel_bottles(self, w, get_all=False):
        """Returns all label object for the number of the bottle"""
        number = self._choose_bottle_number(get_all)
        return [getattr(w, f"bottleLabel{x}") for x in range(1, number + 1)]

    def adjust_bottle_number_displayed(self, w):
        """Removes the UI elements if not all ten bottles are used per config"""
        used_bottles = self._choose_bottle_number()
        # This needs to be done to get rid of registered bottles in the then removed bottles
        all_bottles = DB_COMMANDER.get_ingredients_at_bottles()
        DB_COMMANDER.set_bottleorder(all_bottles[:used_bottles] + [""] * (MAX_SUPPORTED_BOTTLES - used_bottles))
        comboboxes_bottles = self.get_comboboxes_bottles(w, True)
        self.set_multiple_combobox_to_top_item(comboboxes_bottles[used_bottles::])
        to_adjust = [
            self.get_pushbottons_newbottle(w, True),
            self.get_levelbar_bottles(w, True),
            comboboxes_bottles,
            self.get_label_bottles(w, True),
            self.get_numberlabel_bottles(w, True),
        ]
        for elements in to_adjust:
            for element in elements[used_bottles::]:
                element.deleteLater()

    def adjust_maker_label_size_cocktaildata(self, w):
        """Adjusts the fontsize for larger screens"""
        # iterate over all size types and adjust size relative to window height
        # default height was 480 for provided UI
        # so if its larger, the font should also be larger here
        height = self.UI_HEIGHT
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


DP_CONTROLLER = DisplayController()
