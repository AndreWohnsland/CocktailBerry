import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from src.supporter import generate_maker_ingredients_fields, generate_maker_volume_fields, generate_CBR_names, generate_lineedit_recipes


class DisplayHandler:
    """Handler Class to set/remove elements from to UI """

    def __init__(self):
        pass

    def standard_box(self, textstring):
        """ The default messagebox for the Maker. Uses a QMessageBox with OK-Button """
        msgBox = QMessageBox()
        msgBox.setStandardButtons(QMessageBox.Ok)
        buttonok = msgBox.button(QMessageBox.Ok)
        buttonok.setText("     OK     ")
        fillstring = "-" * 70
        msgBox.setText(f"{fillstring}\n{textstring}\n{fillstring}")
        msgBox.setStyleSheet(
            "QMessageBox QPushButton{background-color: rgb(0, 123, 255); color: rgb(0, 0, 0); font-size: 30pt;} QMessageBox{background-color: rgb(10, 10, 10); font-size: 16pt;} QMessageBox QLabel{color: rgb(0, 123, 255);}"
        )
        msgBox.showFullScreen()
        msgBox.exec_()

    # LineEdit
    def clean_multiple_lineedit(self, lineedit_list):
        for lineedit in lineedit_list:
            lineedit.clear()

    def fill_multiple_lineedit(self, lineedit_list, text_list):
        for lineedit, text in zip(lineedit_list, text_list):
            lineedit.setText(str(text))

    # Combobox
    def fill_single_combobox(self, combobox, itemlist, clear_first=False):
        if clear_first:
            combobox.clear()
        if combobox.count() == 0:
            combobox.addItem("")
        combobox.addItems(itemlist)
        combobox.model().sort(0)

    def fill_multiple_combobox(self, combobox_list, itemlist, clear_first=False):
        for combobox in combobox_list:
            self.fill_single_combobox(combobox, itemlist, clear_first)

    def fill_multiple_combobox_individually(self, combobox_list, list_of_itemlist, clear_first=False):
        for combobox, itemlist in zip(combobox_list, list_of_itemlist):
            self.fill_single_combobox(combobox, itemlist, clear_first)

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

    def set_multiple_combobox_items(self, combobox_list, item_to_set):
        for combobox, item in zip(combobox_list, item_to_set):
            index = combobox.findText(item, Qt.MatchFixedString)
            combobox.setCurrentIndex(index)

    def adjust_bottle_comboboxes(self, combobox_list, old_item, new_item):
        for combobox in combobox_list:
            if (old_item != "") and (new_item != combobox.currentText()):
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
        w.LAlkoholgehalt.setText(f"Alkohol: {value:.0f}%")

    # others
    def fill_recipe_data_maker(self, w, display_data, total_volume, cocktailname):
        w.LAlkoholname.setText(cocktailname)
        w.LMenge.setText(f"Menge: {total_volume} ml")
        fields_ingredient = generate_maker_ingredients_fields(w)[: len(display_data)]
        fields_volume = generate_maker_volume_fields(w)[: len(display_data)]
        for field_ingredient, field_volume, (ingredient_name, volume) in zip(fields_ingredient, fields_volume, display_data):
            field_ingredient.setText(f"{ingredient_name} ")
            if volume != "":
                field_volume.setText(f" {volume} ml")
            if ingredient_name == "Selbst hinzufügen:":
                field_ingredient.setStyleSheet("color: rgb(170, 170, 170)")

    def clear_recipe_data_maker(self, w):
        w.LAlkoholgehalt.setText("")
        w.LAlkoholname.setText("")
        w.LMenge.setText("")
        for field_ingredient, field_volume in zip(generate_maker_ingredients_fields(w), generate_maker_volume_fields(w)):
            field_ingredient.setText("")
            field_ingredient.setStyleSheet("color: rgb(0, 123, 255)")
            field_volume.setText("")

    def clear_recipe_data_recipes(self, w, select_other_item):
        w.LECocktail.clear()
        w.LEKommentar.clear()
        if not select_other_item:
            w.LWRezepte.clearSelection()
        self.set_multiple_combobox_to_top_item(generate_CBR_names(w))
        self.clean_multiple_lineedit(generate_lineedit_recipes(w))
        w.handaddlist = []

    def refill_recipes_list_widget(self, w, items):
        w.LWRezepte.clear()
        self.fill_list_widget(w.LWRezepte, items)

    def remove_recipe_from_list_widgets(self, w, recipe_name):
        self.delete_list_widget_item(w.LWRezepte, recipe_name)
        self.delete_list_widget_item(w.LWMaker, recipe_name)
        self.unselect_list_widget_items(w.LWRezepte)
        self.unselect_list_widget_items(w.LWMaker)

    def set_recipe_handadd_comment(self, w, handadd_data):
        comment = ""
        for ingredient_name, volume, ingredient_id, alcoholic, alcohol_level in handadd_data:
            comment += f"{volume} ml {ingredient_name}, "
            w.handaddlist.append([ingredient_id, volume, alcoholic, 1, alcohol_level])
        comment = comment[:-2]
        w.LEKommentar.setText(comment)

    def set_recipe_data(self, w, recipe_name, ingredient_names, ingredient_volumes, enaled, handadd_data):
        if enaled:
            w.CHBenabled.setChecked(True)
        else:
            w.CHBenabled.setChecked(False)
        self.set_multiple_combobox_items(generate_CBR_names(w)[: len(ingredient_names)], ingredient_names)
        self.fill_multiple_lineedit(generate_lineedit_recipes(w)[: len(ingredient_volumes)], ingredient_volumes)
        w.LECocktail.setText(recipe_name)
        self.set_recipe_handadd_comment(w, handadd_data)
