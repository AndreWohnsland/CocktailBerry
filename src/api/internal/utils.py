from typing import Optional, overload

from fastapi import Depends, HTTPException, Request

from src.api.models import Bottle, Cocktail, CocktailIngredient, CocktailInput, Ingredient
from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER as DBC
from src.database_commander import ElementNotFoundError
from src.filepath import DEFAULT_IMAGE_FOLDER
from src.image_utils import find_cocktail_image, find_default_cocktail_image
from src.models import Cocktail as DBCocktail
from src.models import Ingredient as DBIngredient


@overload
def map_cocktail(cocktail: None, scale: bool = True) -> None: ...
@overload
def map_cocktail(cocktail: DBCocktail, scale: bool = True) -> Cocktail: ...
def map_cocktail(cocktail: Optional[DBCocktail], scale: bool = True) -> Optional[Cocktail]:
    if cocktail is None:
        return None
    # scale by the middle of the cocktail amount data, apply user specified alcohol factor
    default_amount = cfg.MAKER_PREPARE_VOLUME[len(cfg.MAKER_PREPARE_VOLUME) // 2]
    if cfg.MAKER_USE_RECIPE_VOLUME:
        default_amount = cocktail.amount
    if scale:
        cocktail.scale_cocktail(default_amount, cfg.MAKER_ALCOHOL_FACTOR / 100)
    return Cocktail(
        id=cocktail.id,
        name=cocktail.name,
        alcohol=int(cocktail.adjusted_alcohol),
        amount=cocktail.adjusted_amount,
        enabled=cocktail.enabled,
        virgin_available=cocktail.virgin_available,
        only_virgin=cocktail.only_virgin,
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
        default_image=create_image_url(cocktail, default=True),
    )


@overload
def map_ingredient(ingredient: None) -> None: ...
@overload
def map_ingredient(ingredient: DBIngredient) -> Ingredient: ...
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
        bottle=ingredient.bottle,
        fill_level=ingredient.fill_level,
        pump_speed=ingredient.pump_speed,
        cost=ingredient.cost,
    )


def map_bottles(ing: DBIngredient) -> Bottle:
    return Bottle(number=ing.bottle or 0, ingredient=map_ingredient(ing) if ing.id > 0 else None)


def calculate_cocktail_volume_and_concentration(cocktail: CocktailInput) -> tuple[int, int]:
    recipe_volume_concentration = 0
    recipe_volume = 0
    for ing in cocktail.ingredients:
        db_ingredient = DBC.get_ingredient(ing.id)
        if db_ingredient is None:
            raise ElementNotFoundError(f"Ingredient Id {ing.id}")
        recipe_volume_concentration += db_ingredient.alcohol * ing.amount
        recipe_volume += ing.amount

    recipe_alcohol_level = int(recipe_volume_concentration / recipe_volume)
    return recipe_volume, recipe_alcohol_level


def create_image_url(cocktail: DBCocktail, default: bool = False) -> str:
    # get the folder name of the path
    default_folder_name = DEFAULT_IMAGE_FOLDER.name
    image_path = find_default_cocktail_image(cocktail) if default else find_cocktail_image(cocktail)
    # check if the image is in the default folder
    if default_folder_name in image_path.parts:
        return f"/static/default/{image_path.name}"
    return f"/static/user/{image_path.name}"


def demo_mode_protection() -> None:
    if cfg.EXP_DEMO_MODE:
        raise HTTPException(status_code=403, detail="Not allowed in demo mode")


async def only_change_theme_on_demo(request: Request) -> None:
    if cfg.EXP_DEMO_MODE:
        options: dict = await request.json()
        if any(key != "MAKER_THEME" for key in options):
            raise HTTPException(status_code=403, detail="Cannot do that on demo mode")


not_on_demo = Depends(demo_mode_protection)
