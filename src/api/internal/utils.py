from typing import Optional

from src.api.models import Cocktail, CocktailIngredient, CocktailInput, Ingredient
from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER as DBC
from src.filepath import DEFAULT_IMAGE_FOLDER
from src.image_utils import find_cocktail_image
from src.models import Cocktail as DBCocktail
from src.models import Ingredient as DBIngredient


def map_cocktail(cocktail: Optional[DBCocktail]) -> Optional[Cocktail]:
    if cocktail is None:
        return None
    # scale by the middle of the cocktail amount data, apply user specified alcohol factor
    default_amount = cfg.MAKER_PREPARE_VOLUME[len(cfg.MAKER_PREPARE_VOLUME) // 2]
    cocktail.scale_cocktail(default_amount, cfg.MAKER_ALCOHOL_FACTOR / 100)
    return Cocktail(
        id=cocktail.id,
        name=cocktail.name,
        alcohol=int(cocktail.adjusted_alcohol),
        amount=cocktail.adjusted_amount,
        enabled=cocktail.enabled,
        virgin_available=cocktail.virgin_available,
        # ingredient hand is if it is currently not on a bottle
        ingredients=[
            CocktailIngredient(
                id=i.id,
                name=i.name,
                alcohol=i.alcohol,
                hand=i.bottle is None,
                amount=i.amount,
                recipe_order=i.recipe_order,
                unit=i.unit,
            )
            for i in cocktail.adjusted_ingredients
        ],
        image=create_image_url(cocktail),
    )


def map_ingredient(ingredient: Optional[DBIngredient]) -> Optional[Ingredient]:
    if ingredient is None:
        return None
    return Ingredient(
        id=ingredient.id,
        name=ingredient.name,
        alcohol=ingredient.alcohol,
        hand=bool(ingredient.hand),
        amount=ingredient.amount,
        recipe_order=ingredient.recipe_order,
        unit=ingredient.unit,
        bottle_volume=ingredient.bottle_volume,
        fill_level=ingredient.fill_level,
        pump_speed=ingredient.pump_speed,
        cost=ingredient.cost,
    )


def calculate_cocktail_volume_and_concentration(cocktail: CocktailInput):
    recipe_volume_concentration = 0
    recipe_volume = 0
    for ing in cocktail.ingredients:
        db_ingredient: DBIngredient = DBC.get_ingredient(ing.name)  # type: ignore
        recipe_volume_concentration += db_ingredient.alcohol * ing.amount
        recipe_volume += ing.amount

    recipe_alcohol_level = int(recipe_volume_concentration / recipe_volume)
    return recipe_volume, recipe_alcohol_level


def create_image_url(cocktail: DBCocktail):
    # get the folder name of the path
    default_folder_name = DEFAULT_IMAGE_FOLDER.name
    image_path = find_cocktail_image(cocktail)
    # check if the image is in the default folder
    if default_folder_name in image_path.parts:
        return f"/static/default/{image_path.name}"
    return f"/static/user/{image_path.name}"
