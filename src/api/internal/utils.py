from src.api.models import CocktailInput
from src.database_commander import DB_COMMANDER as DBC
from src.models import Ingredient as DbIngredient


def calculate_cocktail_volume_and_concentration(cocktail: CocktailInput):
    recipe_volume_concentration = 0
    recipe_volume = 0
    for ing in cocktail.ingredients:
        db_ingredient: DbIngredient = DBC.get_ingredient(ing.name)  # type: ignore
        recipe_volume_concentration += db_ingredient.alcohol * ing.amount
        recipe_volume += ing.amount

    recipe_alcohol_level = int(recipe_volume_concentration / recipe_volume)
    return recipe_volume, recipe_alcohol_level
