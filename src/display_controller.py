from PyQt5.QtCore import Qt

from src.database_commander import DatabaseCommander
from src.dialog_handler import DialogHandler, ui_language


class DisplayController(DialogHandler):
    """ Controler Class to get Values from the UI"""

    def __init__(self):
        super().__init__()
        self.database_commander = DatabaseCommander()

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
        return {
            "ingredient_name": ingredient_name,
            "alcohollevel": int(alcohollevel),
            "volume": int(volume),
            "hand_add": hand_add,
            "selected_ingredient": selected_ingredient,
        }

    def get_cocktail_data(self, w):
        cocktail_volume = int(w.LCustomMenge.text())
        alcohol_faktor = 1 + (w.HSIntensity.value() / 100)
        cocktailname = ""
        if w.LWMaker.selectedItems():
            cocktailname = w.LWMaker.currentItem().text()
        return cocktailname, cocktail_volume, alcohol_faktor

    def get_recipe_field_data(self, w):
        recipe_name = w.LECocktail.text().strip()
        selected_recipe = w.LWRezepte.currentItem().text() if w.LWRezepte.selectedItems() else ""
        ingredient_volumes = self.get_lineedit_text(self.get_lineedits_recipe(w))
        ingredient_names = self.get_current_combobox_items(self.get_comboboxes_recipes(w))
        enabled = int(w.CHBenabled.isChecked())
        return recipe_name, selected_recipe, ingredient_names, ingredient_volumes, enabled

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

    def fill_list_widget(self, list_widget, item_list):
        for item in item_list:
            list_widget.addItem(item)

    # checkboxes
    def set_checkbox_value(self, checkbox, value):
        if value:
            checkbox.setChecked(True)
        else:
            checkbox.setChecked(False)

    # label
    def set_alcohol_level(self, w, value):
        w.LAlkoholgehalt.setText(ui_language.get_volpc_for_dynamic(value))

    # others
    def fill_recipe_data_maker(self, w, display_data, total_volume, cocktailname):
        w.LAlkoholname.setText(cocktailname)
        w.LMenge.setText(ui_language.get_volume_for_dynamic(total_volume))
        fields_ingredient = self.get_labels_maker_ingredients(w)[: len(display_data)]
        fields_volume = self.get_labels_maker_volume(w)[: len(display_data)]
        for field_ingredient, field_volume, (ingredient_name, volume) in zip(fields_ingredient, fields_volume, display_data):
            if volume != "":
                field_volume.setText(f" {volume} ml")
            if ingredient_name == "HEADER":
                ingredient_name = ui_language.get_add_self()
                field_ingredient.setStyleSheet("color: rgb(170, 170, 170)")
            field_ingredient.setText(f"{ingredient_name} ")

    def clear_recipe_data_maker(self, w):
        w.LAlkoholgehalt.setText("")
        w.LAlkoholname.setText("")
        w.LMenge.setText("")
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
        w.handaddlist = []

    def refill_recipes_list_widget(self, w, items):
        w.LWRezepte.clear()
        self.fill_list_widget(w.LWRezepte, items)

    def remove_recipe_from_list_widgets(self, w, recipe_name):
        self.delete_list_widget_item(w.LWRezepte, recipe_name)
        self.delete_list_widget_item(w.LWMaker, recipe_name)
        w.LWRezepte.clearSelection()
        w.LWMaker.clearSelection()

    def set_recipe_handadd_comment(self, w, handadd_data):
        comment = ""
        for ingredient_name, volume, ingredient_id, alcoholic, alcohol_level in handadd_data:
            comment += f"{volume} ml {ingredient_name}, "
            w.handaddlist.append([ingredient_id, volume, alcoholic, 1, alcohol_level])
        comment = comment[:-2]
        w.LEKommentar.setText(comment)

    def set_recipe_data(self, w, recipe_name, ingredient_names, ingredient_volumes, enabled, handadd_data):
        if enabled:
            w.CHBenabled.setChecked(True)
        else:
            w.CHBenabled.setChecked(False)
        self.set_multiple_combobox_items(self.get_comboboxes_recipes(w)[: len(ingredient_names)], ingredient_names)
        self.fill_multiple_lineedit(self.get_lineedits_recipe(w)[: len(ingredient_volumes)], ingredient_volumes)
        w.LECocktail.setText(recipe_name)
        self.set_recipe_handadd_comment(w, handadd_data)

    # Some more "specific" function, not using generic but specified field sets
    def set_label_bottles(self, w, label_names):
        labels = self.get_label_bottles(w)
        self.fill_multiple_lineedit(labels, label_names)

    # Migration from supporter.py
    def get_pushbottons_newbottle(self, w):
        return [getattr(w, f"PBneu{x}") for x in range(1, 11)]

    def get_levelbar_bottles(self, w):
        return [getattr(w, f"ProBBelegung{x}") for x in range(1, 11)]

    def get_comboboxes_bottles(self, w):
        return [getattr(w, f"CBB{x}") for x in range(1, 11)]

    def get_comboboxes_recipes(self, w):
        return [getattr(w, f"CBR{x}") for x in range(1, 9)]

    def get_lineedits_recipe(self, w):
        return [getattr(w, f"LER{x}") for x in range(1, 9)]

    def get_ingredient_fields(self, w):
        return [[w.LEZutatRezept, w.LEGehaltRezept, w.LEFlaschenvolumen], w.CHBHand, w.LWZutaten]

    def get_label_bottles(self, w):
        return [getattr(w, f"LBelegung{x}") for x in range(1, 11)]

    def get_labels_maker_volume(self, w):
        return [getattr(w, f"LMZutat{x}") for x in range(1, 11)]

    def get_labels_maker_ingredients(self, w):
        return [getattr(w, f"LZutat{x}") for x in range(1, 11)]
