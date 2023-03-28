from collections import Counter
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set
import re
import typer

from src.database_commander import DB_COMMANDER
from src.models import Ingredient


@dataclass
class _IngredientInformation:
    name: str
    volume: int

    def __repr__(self) -> str:
        return f"{self.volume} ml {self.name}"


@dataclass
class _RecipeInformation:
    name: str
    ingredients: List[_IngredientInformation] = field(default_factory=list, init=False)

    def __repr__(self) -> str:
        return f"{self.name}: {self.ingredients}"


def importer(file_path: Path, factor: float = 1.0, no_unit=False, sep="\n"):
    """Imports the recipe data from the file into the database"""
    _check_file(file_path)
    print(f"Loading data from: {file_path.absolute()}\nUsing factor: {factor}, data got no unit: {no_unit}\n")
    recipe_text = file_path.read_text()
    recipes = _parse_recipe_text(recipe_text, factor, no_unit, sep)
    distinct_ingredients = _data_inspection(recipes)
    _insert_not_existing_ingredients(distinct_ingredients)
    _insert_recipes(recipes)


def _check_file(file_path: Path):
    """Check if path exists and path is a file"""
    if not file_path.exists():
        _abort("ERROR: This file does not exists!")
    if not file_path.is_file():
        _abort("ERROR: The path does not lead to a file!")


def _parse_recipe_text(recipe_text: str, factor: float, no_unit=False, sep="\n"):
    """Extracts the recipe information out of the given text"""
    # split by newline, remove empty lines
    line_list = [x.strip() for x in recipe_text.split(sep) if x.strip()]
    # Define regex for recipes and ingredients
    # Usually a recipe name should contain one or more words
    # A ingredient line should contain an amount, the unit and a name consisting of one or more words
    volume_part = r"((\d+)\s*[a-zA-Z]{1,3})\s*"
    if no_unit:
        volume_part = r"((\d+))\s*"
    name_part = r"([a-zA-Z0-9_\- ]*)"
    # structure is g1: (volume unit) g2: (volume) g3: (name)
    ingredient_regex = volume_part + name_part
    # build list of recipes, iterate over data
    recipe_data: List[_RecipeInformation] = []
    recipe = None
    for line in line_list:
        # if no match for an ingredient is found this is the name. build a new object then.
        regex_match = re.match(ingredient_regex, line)
        if regex_match is None:
            recipe = _RecipeInformation(line)
            recipe_data.append(recipe)
        # Only triggers in case the first line is not a recipe name, then skip until name is found
        elif recipe is None:
            continue
        else:
            ingredient = _IngredientInformation(regex_match.group(3), int(factor * float(regex_match.group(2))))
            recipe.ingredients.append(ingredient)
    return recipe_data


def _data_inspection(recipes: List[_RecipeInformation]):
    """Print some information of the data
    Checks if there are duplicates in the provided, abort if this is the case.
    Also checks if some of the data is already present in the DB.
    If this is the case, asks the user if to insert only the rest.
    """
    _check_data_length(recipes)
    # build ingredient names, list distinct ones
    all_ingredient_names: List[str] = []
    for recipe in recipes:
        all_ingredient_names.extend([x.name for x in recipe.ingredients])
    unique_ingredients = set(all_ingredient_names)
    print(f"{len(unique_ingredients)} unique ingredients found:")
    print(sorted(unique_ingredients), "\n")
    # get all recipe names, check if there is a duplicate
    recipe_names = [x.name for x in recipes]
    unique_recipes = set(recipe_names)
    print(f"{len(recipe_names)} recipes found, {len(unique_recipes)} have unique names:")
    print(sorted(recipe_names), "\n")
    # if duplicate recipes are in data, abort
    if len(unique_recipes) != len(recipes):
        duplicates = [x for (x, y) in Counter(recipe_names).items() if y > 1]
        print(f"Duplicates are: {duplicates}")
        _abort("There are duplicate recipes, remove or rename them")
    _check_intersection(recipes, unique_recipes)
    return list(unique_ingredients)


def _check_data_length(recipes: List[_RecipeInformation]):
    """print first and last element, abort if no data"""
    if len(recipes):
        print(f"{'First parsed recipe':-^30}")
        print(recipes[0])
        print(f"{'Last parsed recipe':-^30}")
        print(recipes[-1])
        print("")
    else:
        _abort("No recipes found in file")


def _check_intersection(recipes: List[_RecipeInformation], unique_recipes: Set[str]):
    """Check if there is an intersection with existing data in the database
    If an intersection exists, ask the user to continue.
    If all recipes already exist, abort.
    """
    # also check if there are already existing recipes
    cocktails = DB_COMMANDER.get_all_cocktails()
    existing_recipe_names = [c.name for c in cocktails]
    collision_recipes = set(existing_recipe_names).intersection(unique_recipes)
    # if no new recipes will be added, abort
    # This means the len of intersection == amount of data
    if len(collision_recipes) == len(recipes):
        _abort("All recipes from the file already exist in the DB")
    # if some already exists, ask the user if continue is ok
    if len(collision_recipes):
        typer.echo(typer.style("Some of the recipes already exist in the DB:", fg=typer.colors.RED, bold=True))
        print(list(collision_recipes), "\n")
        typer.confirm("Will ignore existing recipes, continue?", abort=True)
        # modify the list, remove duplicate elements
        for item in recipes.copy():
            if item.name in list(collision_recipes):
                recipes.remove(item)
        typer.echo(typer.style("Ok, Using remaining recipes:", fg=typer.colors.GREEN, bold=True))
        print([r.name for r in recipes], "\n")


def _insert_not_existing_ingredients(ingredients: List[str]):
    """Checks the given ingredients with the DB and insert missing ones"""
    existing_ingredients = DB_COMMANDER.get_all_ingredients()
    existing_names = [x.name for x in existing_ingredients]
    not_existing_names = list(set(ingredients).difference(set(existing_names)))
    typer.echo(typer.style("Ingredients, that will be added to the DB:", fg=typer.colors.GREEN, bold=True))
    print(sorted(not_existing_names), "\n")
    print("Please note that a default alcohol of 0, bottle volume of 1000 ml and no handadd will be used.")
    print("This can be changed later over the CocktailBerry program")
    typer.confirm("Does everything looks all right? If so, continue?", abort=True)
    print("Inserting ingredients:", end=" ")
    for ingredient in not_existing_names:
        print(ingredient, end=", ")
        DB_COMMANDER.insert_new_ingredient(ingredient, 0, 1000, False)
    print("")


def _insert_recipes(recipes: List[_RecipeInformation]):
    """Uses the given recipe information to insert the data into the DB
    Gets missing ingredient data from the database.
    Only using handadd at recipe data if ingredient is handadd only.
    """
    # first get all ingredient data and map them for later fast access to a dict
    ingredients = DB_COMMANDER.get_all_ingredients()
    ingredient_mapping: Dict[str, Ingredient] = {}
    for ingredient in ingredients:
        ingredient_mapping[ingredient.name] = ingredient
    print("Inserting recipe:", end=" ")
    for rec in recipes:
        print(rec.name, end=", ")
        volume = int(sum(x.volume for x in rec.ingredients))
        DB_COMMANDER.insert_new_recipe(rec.name, 0, volume, "", 1, 0)
        _insert_recipe_data(rec, ingredient_mapping)
    print("\nImport finished!")


def _insert_recipe_data(recipe: _RecipeInformation, ingredient_mapping: Dict[str, Ingredient]):
    """Uses the given information to create the columns in the data table"""
    for ing in recipe.ingredients:
        ing_data = ingredient_mapping[ing.name]
        cocktail = DB_COMMANDER.get_cocktail(recipe.name)
        if cocktail is None:
            continue
        DB_COMMANDER.insert_recipe_data(cocktail.id, ing_data.id, int(ing.volume))


def _abort(msg: str):
    """Raising typer exit, with given message before"""
    typer.echo(typer.style(f"{msg}, aborting...", fg=typer.colors.RED, bold=True))
    raise typer.Exit()
