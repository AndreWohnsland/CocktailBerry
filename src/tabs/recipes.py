"""Module with all necessary functions for the recipes Tab.

This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from collections import Counter

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.display_controller import DP_CONTROLLER
from src.error_handler import logerror
from src.models import Cocktail, Ingredient


def fill_recipe_box_with_ingredients(w):
    """Assign all ingredients to the Comboboxes in the recipe tab."""
    comboboxes_recipe = DP_CONTROLLER.get_comboboxes_recipes(w)
    ingredient_list = [x.name for x in DB_COMMANDER.get_all_ingredients()]
    DP_CONTROLLER.fill_multiple_combobox(comboboxes_recipe, ingredient_list, clear_first=True)


@logerror
def handle_enter_recipe(w):
    """Enters or updates the recipe into the db."""
    recipe_input = DP_CONTROLLER.get_recipe_field_data(w)
    # destructure each element from recipe input to the variables
    recipe_name = recipe_input.recipe_name
    selected_name = recipe_input.selected_recipe
    ingredient_names = recipe_input.ingredient_names
    ingredient_volumes = recipe_input.ingredient_volumes
    ingredient_order = recipe_input.ingredient_order
    enabled = recipe_input.enabled
    virgin = recipe_input.virgin

    new_recipe = not bool(selected_name)

    if not recipe_name:
        DP_CONTROLLER.say_enter_cocktail_name()
        return
    names, volumes, order, valid = _validate_extract_ingredients(ingredient_names, ingredient_volumes, ingredient_order)
    if not valid:
        return

    recipe_id, error_message = _check_enter_constraints(selected_name, recipe_name, new_recipe)
    if error_message:
        return

    recipe_volume, ingredient_data, recipe_alcohol_level = _build_recipe_data(names, volumes, order)

    cocktail = _enter_or_update_recipe(
        recipe_id, recipe_name, recipe_volume, recipe_alcohol_level, enabled, virgin, ingredient_data
    )

    DP_CONTROLLER.remove_recipe_from_list_widget(w, selected_name)
    DP_CONTROLLER.fill_list_widget_recipes(w, [cocktail.name])
    DP_CONTROLLER.clear_recipe_data_recipes(w, False)
    DP_CONTROLLER.update_maker_view(w)

    if new_recipe:
        DP_CONTROLLER.say_recipe_added(cocktail.name)
    else:
        DP_CONTROLLER.say_recipe_updated(selected_name, cocktail.name)


def _validate_extract_ingredients(
    ingredient_names: list[str],
    ingredient_volumes: list[str],
    ingredient_order: list[str],
) -> tuple[list[str], list[int], list[int], bool]:
    """Give a list for names and volume of ingredients.

    If some according value is missing, informs the user.
    Returns [names], [volumes], [orders] is_valid.
    """
    names: list[str] = []
    volumes: list[str] = []
    orders: list[str] = []
    for name, volume, order in zip(ingredient_names, ingredient_volumes, ingredient_order):
        # if one is missing, break
        if any([name, volume]) and not all([name, volume, order]):
            DP_CONTROLLER.say_some_value_missing()
            return [], [], [], False
        if name != "":
            names.append(name)
            volumes.append(volume)
            orders.append(order)
    if len(names) == 0:
        DP_CONTROLLER.say_recipe_at_least_one_ingredient()
        return [], [], [], False
    counter_names = Counter(names)
    double_names = [x[0] for x in counter_names.items() if x[1] > 1]
    if len(double_names) != 0:
        DP_CONTROLLER.say_ingredient_double_usage(double_names[0])
        return [], [], [], False
    try:
        int_volumes = [int(x) for x in volumes]
        int_orders = [int(x) for x in orders]
    except ValueError:
        DP_CONTROLLER.say_needs_to_be_int()
        return [], [], [], False
    return names, int_volumes, int_orders, True


def _check_enter_constraints(current_recipe_name: str, new_recipe_name: str, new_recipe: bool) -> tuple[int, bool]:
    """Check if either the recipe already exists (new recipe) or if one is selected (update).

    Returns cocktail, got_error.
    """
    # First checks if the new cocktail already exists
    cocktail_new = DB_COMMANDER.get_cocktail(new_recipe_name)
    if cocktail_new is not None and new_recipe:
        DP_CONTROLLER.say_name_already_exists()
        return cocktail_new.id, True
    # then gets the current cocktail, if it's none, we got a new recipe
    cocktail_current = DB_COMMANDER.get_cocktail(current_recipe_name)
    if cocktail_current is None:
        return 0, False
    # also need to check if the new cocktail name collides with another existing one
    # this would be the case if we are finding a cocktail for the new name but got an different old name
    if cocktail_new is not None and cocktail_new.name != cocktail_current.name:
        DP_CONTROLLER.say_name_already_exists()
        return cocktail_new.id, True
    return cocktail_current.id, False


def _build_recipe_data(names: list[str], volumes: list[int], orders: list[int]):
    """Get volume, ingredient objects and concentration of cocktails."""
    recipe_volume = sum(volumes)
    ingredient_data: list[Ingredient] = []
    recipe_volume_concentration = 0

    # first build the ingredient objects for machine add
    for ingredient_name, ingredient_volume, order_number in zip(names, volumes, orders):
        ingredient: Ingredient = DB_COMMANDER.get_ingredient(ingredient_name)  # type: ignore
        ingredient.amount = ingredient_volume
        ingredient.recipe_order = order_number
        recipe_volume_concentration += ingredient.alcohol * ingredient_volume
        ingredient_data.append(ingredient)

    recipe_alcohol_level = int(recipe_volume_concentration / recipe_volume)

    return recipe_volume, ingredient_data, recipe_alcohol_level


def _enter_or_update_recipe(
    recipe_id: int,
    recipe_name: str,
    recipe_volume: int,
    recipe_alcohol_level: int,
    enabled: int,
    virgin: int,
    ingredient_data: list[Ingredient],
) -> Cocktail:
    """Logic to insert/update data into DB."""
    if recipe_id:
        DB_COMMANDER.delete_recipe_ingredient_data(recipe_id)
        DB_COMMANDER.set_recipe(recipe_id, recipe_name, recipe_alcohol_level, recipe_volume, enabled, virgin)
    else:
        DB_COMMANDER.insert_new_recipe(recipe_name, recipe_alcohol_level, recipe_volume, enabled, virgin)
    cocktail: Cocktail = DB_COMMANDER.get_cocktail(recipe_name)  # type: ignore
    for ingredient in ingredient_data:
        DB_COMMANDER.insert_recipe_data(cocktail.id, ingredient.id, ingredient.amount, ingredient.recipe_order)
    # important to get the cocktail again, since the first time getting it, we only got it for its id
    # at this time the cocktail got no recipe data. Getting it again will fix this
    return DB_COMMANDER.get_cocktail(recipe_name)  # type: ignore


def load_recipe_view_names(w):
    """Update the ListWidget in the recipe Tab."""
    cocktails = DB_COMMANDER.get_all_cocktails()
    recipe_list = [x.name for x in cocktails]
    DP_CONTROLLER.clear_list_widget_recipes(w)
    DP_CONTROLLER.fill_list_widget_recipes(w, recipe_list)


@logerror
def load_selected_recipe_data(w):
    """Load all Data from the recipe DB into the according Fields in the recipe tab."""
    recipe_input = DP_CONTROLLER.get_recipe_field_data(w)
    recipe_name = recipe_input.selected_recipe
    DP_CONTROLLER.set_recipe_add_label(w, bool(recipe_name))
    if not recipe_name:
        return

    DP_CONTROLLER.clear_recipe_data_recipes(w, True)
    cocktail = DB_COMMANDER.get_cocktail(recipe_name)
    if cocktail is None:
        return
    DP_CONTROLLER.set_recipe_data(w, cocktail)


@logerror
def delete_recipe(w):
    """Delete the selected recipe, requires the Password."""
    recipe_input = DP_CONTROLLER.get_recipe_field_data(w)
    recipe_name = recipe_input.selected_recipe
    if not recipe_name:
        DP_CONTROLLER.say_no_recipe_selected()
        return
    if not DP_CONTROLLER.ask_to_delete_x(recipe_name):
        return
    if not DP_CONTROLLER.password_prompt(cfg.UI_MASTERPASSWORD):
        return

    DB_COMMANDER.delete_recipe(recipe_name)
    DP_CONTROLLER.remove_recipe_from_list_widget(w, recipe_name)
    DP_CONTROLLER.clear_recipe_data_recipes(w, False)
    DP_CONTROLLER.update_maker_view(w)
    DP_CONTROLLER.say_recipe_deleted(recipe_name)


@logerror
def enable_all_recipes(w):
    """Set all recipes to enabled."""
    if not DP_CONTROLLER.ask_enable_all_recipes():
        return
    DB_COMMANDER.set_all_recipes_enabled()
    DP_CONTROLLER.update_maker_view(w)
    DP_CONTROLLER.clear_recipe_data_recipes(w, True)
    DP_CONTROLLER.say_all_recipes_enabled()
