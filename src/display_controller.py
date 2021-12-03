from typing import Any, Callable, List
from PyQt5.QtCore import Qt

from src.database_commander import DB_COMMANDER
from src.dialog_handler import DialogHandler, UI_LANGUAGE
from src.models import Cocktail, Ingredient
from config.config_manager import shared


class DisplayController(DialogHandler):
    """ Controler Class to get Values from the UI"""

    # def __init__(self):
    #     super().__init__()

    ########################
    # UI "EXTRACT" METHODS #
    ########################
    def get_current_combobox_items(self, combobox_list):
        return [combobox.currentText() for combobox in combobox_list]

    def get_toggle_status(self, button_list):
        return [button.isChecked() for button in button_list]

    def get_lineedit_text(self, lineedit_list):
        return [lineedit.text().strip() for lineedit in lineedit_list]

    def get_list_widget_selection(self, list_widget):
        if not list_widget.selectedItems():
            return ""
        return list_widget.currentItem().text()

    def get_ingredient_data(self, lineedit_list, checkbox, list_widget):
        ingredient_name, alcohollevel, volume = self.get_lineedit_text(lineedit_list)
        hand_add = int(checkbox.isChecked())
        selected_ingredient = ""
        if list_widget.selectedItems():
            selected_ingredient = list_widget.currentItem().text()
        return Ingredient(None, ingredient_name, int(alcohollevel), int(volume), None, hand_add, selected_ingredient)

    def get_cocktail_data(self, w):
        """Returns [name, volume, factor] from maker"""
        cocktail_volume = int(w.LCustomMenge.text())
        alcohol_faktor = 1 + (w.HSIntensity.value() / 100)
        cocktailname = ""
        if w.LWMaker.selectedItems():
            cocktailname = w.LWMaker.currentItem().text()
        return cocktailname, cocktail_volume, alcohol_faktor

    def get_recipe_field_data(self, w):
        recipe_name = w.LECocktail.text().strip()
        selected_recipe = self.get_list_widget_selection(w.LWRezepte)
        ingredient_volumes = self.get_lineedit_text(self.get_lineedits_recipe(w))
        ingredient_names = self.get_current_combobox_items(self.get_comboboxes_recipes(w))
        enabled = int(w.CHBenabled.isChecked())
        comment = w.LEKommentar.text()
        return recipe_name, selected_recipe, ingredient_names, ingredient_volumes, enabled, comment

    def validate_ingredient_data(self, lineedit_list) -> bool:
        if self.lineedit_is_missing(lineedit_list):
            self.say_some_value_missing()
            return False
        _, ingredient_percentage, ingredient_volume = lineedit_list
        if self.lineedit_is_no_int([ingredient_percentage, ingredient_volume]):
            self.say_needs_to_be_int()
            return False
        if int(ingredient_percentage.text()) > 100:
            self.say_alcohollevel_max_limit()
            return False
        return True

    def get_ingredient_window_data(self, w):
        ingredient_name = w.CBingredient.currentText()
        volume = int(w.LAmount.text())
        return ingredient_name, volume

    def check_password(self, lineedit):
        password = lineedit.text()
        lineedit.setText("")
        if password == self.UI_MASTERPASSWORD:
            return True
        return False

    def check_recipe_password(self, w):
        return self.check_password(w.LEpw)

    def check_bottles_password(self, w):
        return self.check_password(w.LECleanMachine)

    def check_ingredient_password(self, w):
        return self.check_password(w.LEpw2)

    def lineedit_is_missing(self, lineedit_list) -> bool:
        for lineedit in lineedit_list:
            if lineedit.text().strip() == "":
                return True
        return False

    def lineedit_is_no_int(self, lineedits) -> bool:
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

    def set_display_settings(self, window_object, resize=True):
        """Checks dev environment, adjust cursor and resize accordingly, if resize is wished"""
        if not self.UI_DEVENVIRONMENT:
            window_object.setCursor(Qt.BlankCursor)
        if resize:
            window_object.setFixedSize(self.UI_WIDTH, self.UI_HEIGHT)
            window_object.resize(self.UI_WIDTH, self.UI_HEIGHT)

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
        w.tabWidget.setCurrentIndex(tabs[tab])

    # Slider
    def __set_slider_value(self, slider, value):
        slider.setValue(value)

    def reset_alcohol_slider(self, w):
        self.__set_slider_value(w.HSIntensity, 0)

    # LineEdit
    def clean_multiple_lineedit(self, lineedit_list):
        for lineedit in lineedit_list:
            lineedit.clear()

    def fill_multiple_lineedit(self, lineedit_list, text_list):
        for lineedit, text in zip(lineedit_list, text_list):
            lineedit.setText(str(text))

    # Combobox
    def fill_single_combobox(self, combobox, itemlist, clear_first=False, sort_items=True, first_empty=True):
        if clear_first:
            combobox.clear()
        if combobox.count() == 0 and first_empty:
            combobox.addItem("")
        combobox.addItems(itemlist)
        if sort_items:
            combobox.model().sort(0)

    def fill_multiple_combobox(self, combobox_list, itemlist, clear_first=False, sort_items=True, first_empty=True):
        for combobox in combobox_list:
            self.fill_single_combobox(combobox, itemlist, clear_first, sort_items, first_empty)

    def fill_multiple_combobox_individually(self, combobox_list, list_of_itemlist, clear_first=False, sort_items=True, first_empty=True):
        for combobox, itemlist in zip(combobox_list, list_of_itemlist):
            self.fill_single_combobox(combobox, itemlist, clear_first, sort_items, first_empty)

    def delete_single_combobox_item(self, combobox, item):
        index = combobox.findText(item, Qt.MatchFixedString)
        if index >= 0:
            combobox.removeItem(index)

    def delete_multiple_combobox_item(self, combobox, itemlist):
        for item in itemlist:
            self.delete_single_combobox_item(combobox, item)

    def delete_item_in_multiple_combobox(self, combobox_list, item):
        for combobox in combobox_list:
            self.delete_single_combobox_item(combobox, item)

    def sort_multiple_combobox(self, combobox_list):
        for combobox in combobox_list:
            combobox.sort()

    def set_multiple_combobox_to_top_item(self, combobox_list):
        for combobox in combobox_list:
            combobox.setCurrentIndex(0)

    def set_multiple_combobox_items(self, combobox_list, items_to_set):
        for combobox, item in zip(combobox_list, items_to_set):
            self.set_combobox_item(combobox, item)

    def set_combobox_item(self, combobox, item):
        index = combobox.findText(item, Qt.MatchFixedString)
        combobox.setCurrentIndex(index)

    def adjust_bottle_comboboxes(self, combobox_list, old_item, new_item):
        for combobox in combobox_list:
            if (old_item != "") and (combobox.findText(old_item, Qt.MatchFixedString) < 0):
                combobox.addItem(old_item)
            if (new_item != "") and (new_item != combobox.currentText()):
                self.delete_single_combobox_item(combobox, new_item)
            combobox.model().sort(0)

    def rename_single_combobox(self, combobox, old_item, new_item):
        index = combobox.findText(old_item, Qt.MatchFixedString)
        if index >= 0:
            combobox.setItemText(index, new_item)
            combobox.model().sort(0)

    def rename_multiple_combobox(self, combobox_list, old_item, new_item):
        for combobox in combobox_list:
            self.rename_single_combobox(combobox, old_item, new_item)

    # buttons / togglebuttons
    def untoggle_buttons(self, button_list):
        for button in button_list:
            button.setChecked(False)

    # progress bars
    def set_progress_bar_values(self, progress_bar_list, value_list):
        for progress_bar, value in zip(progress_bar_list, value_list):
            progress_bar.setValue(value)

    # listwidget
    def unselect_list_widget_items(self, list_widget):
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(False)

    def delete_list_widget_item(self, list_widget, item):
        index_to_delete = list_widget.findItems(item, Qt.MatchExactly)
        if len(index_to_delete) > 0:
            for index in index_to_delete:
                list_widget.takeItem(list_widget.row(index))

    def fill_list_widget(self, list_widget, item_list: List[Any]):
        for item in item_list:
            list_widget.addItem(item)

    def __clear_list_widget(self, listwidget):
        listwidget.clear()

    def clear_list_widget_maker(self, w):
        self.__clear_list_widget(w.LWMaker)

    def clear_list_widget_ingredients(self, w):
        self.__clear_list_widget(w.LWZutaten)

    def fill_list_widget_maker(self, w, recipe_names: List[str]):
        self.fill_list_widget(w.LWMaker, recipe_names)

    def fill_list_widget_recipes(self, w, recipe_names: List[str]):
        self.fill_list_widget(w.LWRezepte, recipe_names)

    # checkboxes
    def set_checkbox_value(self, checkbox, value):
        checkbox.setChecked(bool(value))

    # others
    def fill_recipe_data_maker(self, w, cocktail: Cocktail, total_volume: int):
        w.LAlkoholname.setText(cocktail.name)
        # w.LIngredientHeader.setText("_" * 40)
        w.LMenge.setText(f"{total_volume} ml")
        w.LAlkoholgehalt.setText(f"{cocktail.adjusted_alcohol:.0f}%")
        display_data = cocktail.get_machineadds()
        hand = cocktail.get_handadds()
        # when there is handadd, also build some additional data
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
        w.LAlkoholgehalt.setText("")
        w.LAlkoholname.setText(UI_LANGUAGE.get_cocktail_dummy())
        w.LMenge.setText("")
        # w.LIngredientHeader.setText("")
        if not select_other_item:
            w.LWMaker.clearSelection()
        for field_ingredient, field_volume in zip(self.get_labels_maker_ingredients(w), self.get_labels_maker_volume(w)):
            field_ingredient.setText("")
            field_ingredient.setStyleSheet("color: rgb(0, 123, 255)")
            field_volume.setText("")

    def clear_recipe_data_recipes(self, w, select_other_item):
        w.LECocktail.clear()
        w.LEKommentar.clear()
        if not select_other_item:
            w.LWRezepte.clearSelection()
        self.set_multiple_combobox_to_top_item(self.get_comboboxes_recipes(w))
        self.clean_multiple_lineedit(self.get_lineedits_recipe(w))
        shared.handaddlist = []

    def refill_recipes_list_widget(self, w, items):
        w.LWRezepte.clear()
        self.fill_list_widget(w.LWRezepte, items)

    def remove_recipe_from_list_widgets(self, w, recipe_name):
        # block that trigger that no refetching of data (and shared.handadd overwrite) occurs
        w.LWRezepte.blockSignals(True)
        w.LWMaker.blockSignals(True)
        w.LWRezepte.clearSelection()
        w.LWMaker.clearSelection()
        self.delete_list_widget_item(w.LWRezepte, recipe_name)
        self.delete_list_widget_item(w.LWMaker, recipe_name)
        w.LWRezepte.blockSignals(False)
        w.LWMaker.blockSignals(False)

    def set_recipe_handadd_comment(self, w, handadd_data):
        comment = ""
        for ingredient_name, volume, ingredient_id, alcoholic, alcohol_level in handadd_data:
            comment += f"{volume} ml {ingredient_name}, "
            shared.handaddlist.append([ingredient_id, volume, alcoholic, 1, alcohol_level])
        comment = comment[:-2]
        w.LEKommentar.setText(comment)

    def set_recipe_data(self, w, recipe_name, ingredient_names, ingredient_volumes, enabled, handadd_data):
        w.CHBenabled.setChecked(bool(enabled))
        self.set_multiple_combobox_items(self.get_comboboxes_recipes(w)[: len(ingredient_names)], ingredient_names)
        self.fill_multiple_lineedit(self.get_lineedits_recipe(w)[: len(ingredient_volumes)], ingredient_volumes)
        w.LECocktail.setText(recipe_name)
        self.set_recipe_handadd_comment(w, handadd_data)

    # Some more "specific" function, not using generic but specified field sets
    def set_label_bottles(self, w, label_names):
        labels = self.get_label_bottles(w)
        self.fill_multiple_lineedit(labels, label_names)

    # Migration from supporter.py
    def get_pushbottons_newbottle(self, w, get_all=False):
        number = self.__choose_bottle_number(get_all)
        return [getattr(w, f"PBneu{x}") for x in range(1, number + 1)]

    def get_levelbar_bottles(self, w, get_all=False):
        number = self.__choose_bottle_number(get_all)
        return [getattr(w, f"ProBBelegung{x}") for x in range(1, number + 1)]

    def get_comboboxes_bottles(self, w, get_all=False):
        number = self.__choose_bottle_number(get_all)
        return [getattr(w, f"CBB{x}") for x in range(1, number + 1)]

    def get_comboboxes_recipes(self, w):
        return [getattr(w, f"CBR{x}") for x in range(1, 8)]

    def get_lineedits_recipe(self, w):
        return [getattr(w, f"LER{x}") for x in range(1, 8)]

    def get_ingredient_fields(self, w):
        """Returns [Name, Alcohol, Volume], CheckedHand, ListWidget Elements for Ingredients"""
        return [[w.LEZutatRezept, w.LEGehaltRezept, w.LEFlaschenvolumen], w.CHBHand, w.LWZutaten]

    def get_label_bottles(self, w, get_all=False):
        number = self.__choose_bottle_number(get_all)
        return [getattr(w, f"LBelegung{x}") for x in range(1, number + 1)]

    def get_labels_maker_volume(self, w):
        return [getattr(w, f"LMZutat{x}") for x in range(1, 10)]

    def get_labels_maker_ingredients(self, w):
        return [getattr(w, f"LZutat{x}") for x in range(1, 10)]

    def __choose_bottle_number(self, get_all):
        """Selects the number of Bottles in the bottles tab, all is ten"""
        if get_all:
            return 10
        return min(self.MAKER_NUMBER_BOTTLES, 10)

    def get_numberlabel_bottles(self, w, get_all=False):
        number = self.__choose_bottle_number(get_all)
        return [getattr(w, f"bottleLabel{x}") for x in range(1, number + 1)]

    def adjust_bottle_number_displayed(self, w):
        """Removes the UI elements if not all ten bottles are used per config"""
        used_bottles = min(self.MAKER_NUMBER_BOTTLES, 10)
        # This needs to be done to get rid of registered bottles in the then removed bottles
        all_bottles = DB_COMMANDER.get_ingredients_at_bottles()
        DB_COMMANDER.set_bottleorder(all_bottles[:used_bottles] + [""] * (10 - used_bottles))
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


DP_CONTROLLER = DisplayController()
