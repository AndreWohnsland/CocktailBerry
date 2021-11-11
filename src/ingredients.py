# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the ingredients Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""
from src.bottles import set_fill_level_bars, refresh_bottle_information

from src.display_controller import DisplayController
from src.database_commander import DatabaseCommander


DP_CONTROLLER = DisplayController()
DB_COMMANDER = DatabaseCommander()


def custom_ingredient_output(w):
    """Calls an additional window to make a single ingredient output"""
    w.ingredientdialog()


def enter_ingredient(w, newingredient=True):
    """ Insert the new ingredient into the DB, if all values are given and its name is not already in the DB.
    Also can change the current selected ingredient (newingredient = False)
    """
    ingredient_lineedits, ingredient_checkbox, ingredient_list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    error = DP_CONTROLLER.check_ingredient_data(ingredient_lineedits)
    if error:
        DP_CONTROLLER.standard_box(error[0])
        return
    ingredient_data = DP_CONTROLLER.get_ingredient_data(
        ingredient_lineedits, ingredient_checkbox, ingredient_list_widget)

    if newingredient:
        succesfull = add_new_ingredient(w, ingredient_data)
    else:
        succesfull = change_existing_ingredient(w, ingredient_list_widget, ingredient_data)
    if not succesfull:
        return

    clear_ingredient_information(w)
    ingredient_list_widget.addItem(ingredient_data["ingredient_name"])
    set_fill_level_bars(w)
    refresh_bottle_information(w)
    DP_CONTROLLER.standard_box(succesfull)


def add_new_ingredient(w, ingredient_data):
    """Adds the ingredient into the database """

    given_name_ingredient_data = DB_COMMANDER.get_ingredient_data(ingredient_data["ingredient_name"])
    if given_name_ingredient_data:
        DP_CONTROLLER.standard_box("Dieser Name existiert schon in der Datenbank!")
        return ""

    DB_COMMANDER.insert_new_ingredient(
        ingredient_data["ingredient_name"],
        ingredient_data["alcohollevel"],
        ingredient_data["volume"],
        ingredient_data["hand_add"]
    )
    if not ingredient_data["hand_add"]:
        combobox_recipes = DP_CONTROLLER.get_comboboxes_recipes(w)
        combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
        DP_CONTROLLER.fill_multiple_combobox(combobox_recipes + combobox_bottles, [ingredient_data["ingredient_name"]])
    return f"Zutat mit dem Namen: <{ingredient_data['ingredient_name']}> eingetragen"


def change_existing_ingredient(w, ingredient_list_widget, ingredient_data):
    """Changes the existing ingredient """
    selected_ingredient_data = DB_COMMANDER.get_ingredient_data(ingredient_data["selected_ingredient"])
    if not ingredient_data["selected_ingredient"]:
        DP_CONTROLLER.standard_box("Es ist keine Zutat ausgewählt!")
        return ""

    bottle_used = DB_COMMANDER.get_bottle_usage(selected_ingredient_data["ID"])
    if ingredient_data["hand_add"] and bottle_used:
        DP_CONTROLLER.standard_box(
            "Die Zutat ist noch in der Belegung registriert und kann somit nicht auf selbst hinzufügen gesetzt werden!")
        return ""

    volume_level = min(selected_ingredient_data["volume_level"], ingredient_data["volume"])
    DB_COMMANDER.set_ingredient_data(
        ingredient_data["ingredient_name"],
        ingredient_data["alcohollevel"],
        ingredient_data["volume"],
        volume_level,
        ingredient_data["hand_add"],
        selected_ingredient_data["ID"],
    )

    DP_CONTROLLER.delete_list_widget_item(ingredient_list_widget, ingredient_data["selected_ingredient"])
    combobox_recipes = DP_CONTROLLER.get_comboboxes_recipes(w)
    combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
    both_boxes = combobox_recipes + combobox_bottles

    if selected_ingredient_data["hand_add"] and not ingredient_data["hand_add"]:
        DP_CONTROLLER.fill_multiple_combobox(both_boxes, [ingredient_data["ingredient_name"]])
    elif not ingredient_data["hand_add"]:
        DP_CONTROLLER.rename_multiple_combobox(
            both_boxes,
            ingredient_data["selected_ingredient"],
            ingredient_data["ingredient_name"]
        )
    else:
        DP_CONTROLLER.delete_item_in_multiple_combobox(both_boxes, ingredient_data["selected_ingredient"])

    return f"Zutat mit dem Namen: <{ingredient_data['selected_ingredient']}> unter <{ingredient_data['ingredient_name']}> aktualisiert"


def load_ingredients(w):
    """ Load all ingredientnames into the ListWidget """
    w.LWZutaten.clear()
    ingredient_names = DB_COMMANDER.get_ingredient_names()
    DP_CONTROLLER.fill_list_widget(w.LWZutaten, ingredient_names)


def delete_ingredient(w):
    """ Deletes an ingredient out of the DB if its not needed in any recipe."""
    _, _, ingredient_list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    if not DP_CONTROLLER.check_ingredient_password(w):
        DP_CONTROLLER.standard_box("Falsches Passwort!")
        return
    if not ingredient_list_widget.selectedItems():
        DP_CONTROLLER.standard_box("Keine Zutat ausgewählt!")
        return
    ingredient_data = DB_COMMANDER.get_ingredient_data(ingredient_list_widget.currentItem().text())
    if DB_COMMANDER.get_bottle_usage(ingredient_data["ID"]):
        DP_CONTROLLER.standard_box("Achtung, die Zutat ist noch in der Belegung registriert!")
        return
    recipe_list = DB_COMMANDER.get_recipe_usage_list(ingredient_data["ID"])
    if recipe_list:
        recipe_string = ", ".join(recipe_list[:10])
        DP_CONTROLLER.standard_box(f"Zutat kann nicht gelöscht werden, da sie in:\n{recipe_string}\ngenutzt wird!")
        return

    DB_COMMANDER.delete_ingredient(ingredient_data["ID"])
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_bottles(w), ingredient_data["name"])
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_recipes(w), ingredient_data["name"])
    clear_ingredient_information(w)
    load_ingredients(w)
    DP_CONTROLLER.standard_box(
        f"Zutat mit der ID und dem Namen:\n<{ingredient_data['ID']}> <{ingredient_data['name']}>\ngelöscht!")


def display_selected_ingredient(w):
    """ Search the DB entry for the ingredient and displays them """
    ingredient_lineedits, ingredient_checkbox, ingredient_list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    if ingredient_list_widget.selectedItems():
        ingredient_data = DB_COMMANDER.get_ingredient_data(ingredient_list_widget.currentItem().text())
        DP_CONTROLLER.fill_multiple_lineedit(
            ingredient_lineedits, [ingredient_data["name"], ingredient_data["alcohollevel"], ingredient_data["volume"]]
        )
        DP_CONTROLLER.set_checkbox_value(ingredient_checkbox, ingredient_data["hand_add"])


def clear_ingredient_information(w):
    """ Clears all entries in the ingredient windows. """
    ingredient_lineedits, ingredient_checkbox, ingredient_list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    DP_CONTROLLER.clean_multiple_lineedit(ingredient_lineedits)
    ingredient_list_widget.clearSelection()
    ingredient_checkbox.setChecked(False)
