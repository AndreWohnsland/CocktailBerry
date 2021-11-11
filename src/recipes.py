# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the recipes Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

from collections import Counter

from src.maker import refresh_recipe_maker_view
from src.error_suppression import logerror

from src.display_controller import DisplayController
from src.database_commander import DatabaseCommander

DP_CONTROLLER = DisplayController()
DB_COMMANDER = DatabaseCommander()


@logerror
def fill_recipe_box_with_ingredients(w):
    """ Asigns all ingredients to the Comboboxes in the recipe tab """
    comboboxes_recipe = DP_CONTROLLER.get_comboboxes_recipes(w)
    ingredient_list = DB_COMMANDER.get_ingredient_names_machine()
    DP_CONTROLLER.fill_multiple_combobox(comboboxes_recipe, ingredient_list, clear_first=True)


def prepare_enter_new_recipe(recipe_name):
    recipe_id = DB_COMMANDER.get_recipe_id_by_name(recipe_name)
    if recipe_id:
        return recipe_id, "Dieser Name existiert schon in der Datenbank!"
    return recipe_id, ""


def prepare_update_existing_recipe(w, selected_name):
    if not selected_name:
        return 0, "Es ist kein Rezept ausgewählt!"
    recipe_id = DB_COMMANDER.get_recipe_id_by_name(selected_name)
    DB_COMMANDER.delete_recipe_ingredient_data(recipe_id)
    DP_CONTROLLER.remove_recipe_from_list_widgets(w, selected_name)
    return recipe_id, ""


def reason_check_ingredients(ingredient_names, ingredient_volumes):
    names, volumes = [], []
    for name, volume in zip(ingredient_names, ingredient_volumes):
        if (name == "" and volume != "") or (name != "" and volume == ""):
            return [], [], "Irgendwo ist ein wert vergessen worden"
        if name != "":
            names.append(name)
            volumes.append(volume)
    if len(names) == 0:
        return [], [], "Es muss mindestens eine Zutat eingetragen sein!"
    conter_names = Counter(names)
    double_names = [x[0] for x in conter_names.items() if x[1] > 1]
    if len(double_names) != 0:
        return [], [], f"Eine der Zutaten:\n<{double_names[0]}>\nwurde doppelt verwendet!"
    try:
        volumes = [int(x) for x in volumes]
    except ValueError:
        return [], [], "Menge muss eine Zahl sein!"
    return names, volumes, ""


def enter_or_update_recipe(w, recipe_id, recipe_name, recipe_volume, recipe_alcohollevel, enabled, ingredient_data, handadd_data):
    comment = w.LEKommentar.text()
    if recipe_id:
        DB_COMMANDER.set_recipe(recipe_id, recipe_name, recipe_alcohollevel, recipe_volume, comment, enabled)
    else:
        DB_COMMANDER.insert_new_recipe(recipe_name, recipe_alcohollevel, recipe_volume, comment, enabled)
        recipe_id = DB_COMMANDER.get_recipe_id_by_name(recipe_name)
    for data in ingredient_data:
        is_alcoholic = 1 if data["alcohollevel"] > 0 else 0
        DB_COMMANDER.insert_recipe_data(recipe_id, data["ID"], data["recipe_volume"], is_alcoholic, 0)
    for hand_id, hand_volume, hand_alcoholic, _, _ in handadd_data:
        DB_COMMANDER.insert_recipe_data(recipe_id, hand_id, hand_volume, hand_alcoholic, 1)
    return recipe_id


@logerror
def enter_recipe(w, newrecipe):
    """ Enters or updates the recipe into the db
    """
    recipe_name, selected_name, ingredient_names, ingredient_volumes, enabled = DP_CONTROLLER.get_recipe_field_data(
        w)
    handadd_data = w.handaddlist
    if not recipe_name:
        DP_CONTROLLER.standard_box("Bitte Cocktailnamen eingeben!")
        return
    ingredient_names, ingredient_volumes, error_message = reason_check_ingredients(ingredient_names, ingredient_volumes)
    if error_message:
        DP_CONTROLLER.standard_box(error_message)
        return

    if newrecipe:
        recipe_id, error_message = prepare_enter_new_recipe(recipe_name)
    else:
        recipe_id, error_message = prepare_update_existing_recipe(w, selected_name)
    if error_message:
        DP_CONTROLLER.standard_box(error_message)
        return

    recipe_volume = sum(ingredient_volumes)
    ingredient_data = []
    recipe_volume_concentration = 0
    for ingredient_name, ingredient_volume in zip(ingredient_names, ingredient_volumes):
        data = DB_COMMANDER.get_ingredient_data(ingredient_name)
        data["recipe_volume"] = ingredient_volume
        recipe_volume_concentration += data["alcohollevel"] * ingredient_volume
        ingredient_data.append(data)
    for _, hand_volume, _, _, hand_alcohollevel in handadd_data:  # id, volume, alcoholic, 1, alcohol_con
        recipe_volume += hand_volume
        recipe_volume_concentration += hand_volume * hand_alcohollevel
    recipe_alcohollevel = int(recipe_volume_concentration / recipe_volume)

    recipe_id = enter_or_update_recipe(
        w, recipe_id, recipe_name, recipe_volume, recipe_alcohollevel, enabled, ingredient_data, handadd_data
    )
    w.LWRezepte.addItem(recipe_name)
    if enabled:
        refresh_recipe_maker_view(w, [recipe_id])
    DP_CONTROLLER.clear_recipe_data_recipes(w, False)

    if newrecipe:
        message = f"Rezept unter der ID und dem Namen:\n<{recipe_id}> <{recipe_name}>\neingetragen!"
        DP_CONTROLLER.standard_box(message)
    else:
        message = f"Rezept mit der ID und dem Namen:\n<{recipe_id}> <{selected_name}>\nunter dem Namen:\n<{recipe_name}>\naktualisiert!"
        DP_CONTROLLER.standard_box(message)


@logerror
def update_recipe_view(w):
    """ Updates the ListWidget in the recipe Tab. """
    recipe_list = DB_COMMANDER.get_recipes_name()
    DP_CONTROLLER.refill_recipes_list_widget(w, recipe_list)


@logerror
def load_selected_recipe_data(w):
    """ Loads all Data from the recipe DB into the according Fields in the recipe tab. """
    recipe_name = DP_CONTROLLER.get_list_widget_selection(w.LWRezepte)
    if not recipe_name:
        return

    DP_CONTROLLER.clear_recipe_data_recipes(w, True)
    machineadd_data, _ = DB_COMMANDER.get_recipe_ingredients_by_name_seperated_data(recipe_name)
    ingredient_names = [data[0] for data in machineadd_data]
    ingredient_volumes = [data[1] for data in machineadd_data]
    handadd_data = DB_COMMANDER.get_recipe_ingredients_for_comment(recipe_name)
    enabled = DB_COMMANDER.get_enabled_status(recipe_name)
    DP_CONTROLLER.set_recipe_data(w, recipe_name, ingredient_names, ingredient_volumes, enabled, handadd_data)


@logerror
def delete_recipe(w):
    """ Deletes the selected recipe, requires the Password """
    if not DP_CONTROLLER.check_recipe_password(w):
        DP_CONTROLLER.standard_box("Falsches Passwort!")
        return
    recipe_name = DP_CONTROLLER.get_list_widget_selection(w.LWRezepte)
    if not recipe_name:
        DP_CONTROLLER.standard_box("Kein Rezept ausgewählt!")
        return

    DB_COMMANDER.delete_recipe(recipe_name)
    DP_CONTROLLER.remove_recipe_from_list_widgets(w, recipe_name)
    DP_CONTROLLER.clear_recipe_data_recipes(w, False)
    DP_CONTROLLER.clear_recipe_data_maker(w)
    DP_CONTROLLER.standard_box(f"Rezept mit dem Namen <{recipe_name}> wurde gelöscht!")


@logerror
def enableall_recipes(w):
    """Set all recipes to enabled """
    disabled_ids = DB_COMMANDER.get_disabled_recipes_id()
    DB_COMMANDER.set_all_recipes_enabled()
    refresh_recipe_maker_view(w, disabled_ids)
    DP_CONTROLLER.clear_recipe_data_recipes(w, True)
    DP_CONTROLLER.standard_box("Alle Rezepte wurden wieder aktiv gesetzt!")
