from typing import Dict, List

from src.models import Cocktail, Ingredient
from src.database_commander import DatabaseCommander


def add_new_recipes_for_1_10():
    """Adds the new recipes from 1.10.0"""
    new_names = [
        "Beachbum",
        "Bay Breeze",
        "Belladonna",
        "Black-Eyed Susan",
        "Blue Hawaii",
        "Blue Ricardo",
        "Flamingo",
        "Orange Crush",
        "Bocce Ball",
        "Fuzzy Navel",
        "Madras",
        "Woo Woo",
        "Vodka Tonic",
        "Sidewinder’s Fang",
        "212",
        "Cantarito",
        "Paloma",
    ]
    # build connection to provided and local db
    # gets the new recipe data, check whats missing and insert it
    default_db = DatabaseCommander(use_default=True)
    local_db = DatabaseCommander()
    cocktails_to_add = _get_new_cocktails(new_names, default_db, local_db)
    ingredient_to_add = _get_new_ingredients(local_db, cocktails_to_add)
    _insert_new_ingredients(default_db, local_db, ingredient_to_add)
    _insert_new_recipes(local_db, cocktails_to_add)


def _insert_new_recipes(local_db: DatabaseCommander, cocktails_to_add: List[Cocktail]):
    """Inserts the data for the new recipes into the db"""
    all_ingredients = local_db.get_all_ingredients()
    ing_mapping: Dict[str, Ingredient] = {}
    for ing in all_ingredients:
        ing_mapping[ing.name] = ing
    for rec in cocktails_to_add:
        local_db.insert_new_recipe(
            rec.name, rec.alcohol, rec.amount,
            rec.comment, rec.enabled, rec.virgin_available
        )
        new_cocktail = local_db.get_cocktail(rec.name)
        if new_cocktail is None:
            continue
        for ing in rec.ingredients:
            ing_data = ing_mapping[ing.name]
            local_db.insert_recipe_data(new_cocktail.id, ing_data.id, ing.amount, bool(ing.hand))


def _insert_new_ingredients(default_db: DatabaseCommander, local_db: DatabaseCommander, ingredient_to_add: List[str]):
    """Gets and inserts the given ingredients into the local db"""
    for ingredient in ingredient_to_add:
        ing = default_db.get_ingredient(ingredient)
        if ing is None:
            continue
        local_db.insert_new_ingredient(ing.name, ing.alcohol, ing.bottle_volume, bool(ing.hand))


def _get_new_ingredients(local_db: DatabaseCommander, cocktails_to_add: List[Cocktail]) -> List[str]:
    """Returns the names of the missing ingredients for the given cocktails"""
    ingredients_in_new = []
    for cocktail in cocktails_to_add:
        ingredients_in_new.extend([i.name for i in cocktail.ingredients])
    existing_ingredients = [i.name for i in local_db.get_all_ingredients()]
    ingredient_to_add = list(set(ingredients_in_new).difference(set(existing_ingredients)))
    return ingredient_to_add


def _get_new_cocktails(new_names: List[str], default_db: DatabaseCommander, local_db: DatabaseCommander):
    """Returns the cocktails that are not already in the local db by the given names"""
    already_existing_names = [x.name for x in local_db.get_all_cocktails() if x.name in new_names]
    cocktail_difference = list(set(new_names).difference(set(already_existing_names)))
    cocktails_to_add = [x for x in default_db.get_all_cocktails() if x.name in cocktail_difference]
    return cocktails_to_add
