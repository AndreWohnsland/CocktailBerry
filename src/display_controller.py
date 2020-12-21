import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from config.config_manager import ConfigManager
from src.database_commander import DatabaseCommander
from src.supporter import generate_lineedit_recipes, generate_CBR_names


class DisplayController(ConfigManager):
    """ Controler Class to get Values from the UI"""

    def __init__(self):
        self.database_commander = DatabaseCommander()

    def get_current_combobox_items(self, combobox_list):
        return [combobox.currentText() for combobox in combobox_list]

    def get_toggle_status(self, button_list):
        return [True if button.isChecked() else False for button in button_list]

    def get_lineedit_text(self, lineedit_list):
        return [lineedit.text() for lineedit in lineedit_list]

    def get_list_widget_selection(self, list_widget):
        if not list_widget.selectedItems():
            return ""
        return list_widget.currentItem().text()

    def get_ingredient_data(self, lineedit_list, checkbox, list_widget):
        ingredient_name, alcohollevel, volume = self.get_lineedit_text(lineedit_list)
        hand_add = 1 if checkbox.isChecked() else 0
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
        recipe_name = w.LECocktail.text()
        selected_recipe = ""
        if w.LWRezepte.selectedItems():
            selected_recipe = w.LWRezepte.currentItem().text()
        ingredient_volumes = self.get_lineedit_text(generate_lineedit_recipes(w))
        ingredient_names = self.get_current_combobox_items(generate_CBR_names(w))
        enabled = 0
        if w.CHBenabled.isChecked():
            enabled = 1
        return recipe_name, selected_recipe, ingredient_names, ingredient_volumes, enabled

    def check_ingredient_data(self, lineedit_list):
        error_messages = self.missing_check(
            lineedit_list, ["Der Zutatenname fehlt", "Der Alkoholgehalt fehlt", "Das Flaschenvolumen fehlt"]
        )
        ingredient_name, ingredient_percentage, ingredient_volume = lineedit_list
        error_messages.extend(self.valid_check_int([ingredient_percentage, ingredient_volume], ["Alkoholgehalt", "Flaschenvolumen"]))
        try:
            if int(ingredient_percentage.text()) > 100:
                error_messages.append("Alkoholgehalt kann nicht größer als 100 sein!")
        except:
            pass
        return error_messages

    def get_data_ingredient_window(self, w):
        ingredient_name = w.CBingredient.currentText()
        volume = int(w.LAmount.text())
        return ingredient_name, volume

    def check_password(self, lineedit):
        password = lineedit.text()
        lineedit.setText("")
        if password == self.MASTERPASSWORD:
            return True
        return False

    def check_recipe_password(self, w):
        return self.check_password(w.LEpw)

    def check_bottles_password(self, w):
        return self.check_password(w.LECleanMachine)

    def check_ingredient_password(self, w):
        return self.check_password(w.LEpw2)

    def missing_check(self, lineedit_list, message_list=[]):
        error_messages = []
        standard_message = "Es wurde ein Wert vergessen, bitte nachtragen"
        if not message_list:
            message_list = [standard_message for x in lineedit_list]
        for lineedit, message in zip(lineedit_list, message_list):
            if lineedit.text() == "":
                error_messages.append(message)
        return error_messages

    def valid_check_int(self, lineedits, wrongvals):
        error_messages = []
        for lineedit, wrongval in zip(lineedits, wrongvals):
            try:
                int(lineedit.text())
            except ValueError:
                error_messages.append(f"{wrongval} muss eine Zahl sein")
        return error_messages
