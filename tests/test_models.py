"""Tests for virgin related logic on the Cocktail model."""

from src.models import Cocktail, Ingredient


def _ingredient(_id: int, name: str, *, alcohol: int, bottle: int | None = 1, amount: int = 100) -> Ingredient:
    return Ingredient(
        id=_id,
        name=name,
        alcohol=alcohol,
        bottle_volume=1000,
        fill_level=1000,
        hand=bottle is None,
        pump_speed=100,
        amount=amount,
        bottle=bottle,
    )


def _cocktail(ingredients: list[Ingredient], virgin_available: bool = False) -> Cocktail:
    return Cocktail(
        id=1,
        name="Test",
        alcohol=10,
        amount=sum(i.amount for i in ingredients),
        enabled=True,
        price_per_100_ml=0,
        virgin_available=virgin_available,
        ingredients=ingredients,
    )


def test_is_naturally_virgin_for_alcohol_free_recipe() -> None:
    cocktail = _cocktail([_ingredient(1, "Cola", alcohol=0), _ingredient(2, "Juice", alcohol=0)])
    assert cocktail.is_naturally_virgin is True


def test_is_not_naturally_virgin_with_alcoholic_ingredient() -> None:
    cocktail = _cocktail([_ingredient(1, "Cola", alcohol=0), _ingredient(2, "Rum", alcohol=40)])
    assert cocktail.is_naturally_virgin is False


def test_single_ingredient_recipe_is_not_naturally_virgin() -> None:
    cocktail = _cocktail([_ingredient(1, "Cola", alcohol=0)])
    assert cocktail.is_naturally_virgin is False


def test_is_possible_sets_only_virgin_for_naturally_virgin() -> None:
    cocktail = _cocktail([_ingredient(1, "Cola", alcohol=0), _ingredient(2, "Juice", alcohol=0)])
    assert cocktail.is_possible(hand_available=[], max_hand_ingredients=0) is True
    assert cocktail.only_virgin is True


def test_is_possible_keeps_only_virgin_false_for_alcoholic_cocktail() -> None:
    cocktail = _cocktail([_ingredient(1, "Cola", alcohol=0), _ingredient(2, "Rum", alcohol=40)])
    assert cocktail.is_possible(hand_available=[], max_hand_ingredients=0) is True
    assert cocktail.only_virgin is False


def test_display_name_has_no_virgin_tag_for_naturally_virgin() -> None:
    cocktail = _cocktail([_ingredient(1, "Cola", alcohol=0), _ingredient(2, "Juice", alcohol=0)])
    cocktail.scale_cocktail(200, 1.0)
    assert cocktail.is_virgin is True
    assert cocktail.display_name == "Test"


def test_display_name_has_virgin_tag_for_virginized_cocktail() -> None:
    cocktail = _cocktail([_ingredient(1, "Cola", alcohol=0), _ingredient(2, "Rum", alcohol=40)], virgin_available=True)
    cocktail.scale_cocktail(200, 0.0)
    assert cocktail.is_virgin is True
    assert cocktail.display_name == "Test (Virgin)"
