from __future__ import annotations

import pytest

from src.database_commander import DatabaseCommander


class TestBottle:
    def test_get_bottle_fill_levels(self, db_commander: DatabaseCommander):
        """Test the get_bottle_fill_levels method."""
        fill_levels = db_commander.get_bottle_fill_levels()
        assert len(fill_levels) == 24
        assert fill_levels[0] == 100
        assert fill_levels[1] == 0

    def test_get_bottle_data(self, db_commander: DatabaseCommander):
        ingredients = db_commander.get_ingredients_at_bottles()
        assert len(ingredients) == 24
        assert ingredients[0].name == "White Rum"
        assert ingredients[1].name == "Cola"

    @pytest.mark.parametrize(
        "ingredient_id, expected_usage",
        [
            (1, True),
            (4, False),
        ],
    )
    def test_get_bottle_usage(self, db_commander: DatabaseCommander, ingredient_id: int, expected_usage: bool):
        """Test the get_bottle_usage method."""
        usage = db_commander.get_bottle_usage(ingredient_id)
        assert usage is expected_usage

    def test_set_bottle_order(self, db_commander: DatabaseCommander):
        """Test the set_bottle_order method."""
        db_commander.set_bottle_order(["White Rum", "Cola"])
        data = db_commander.get_ingredients_at_bottles()
        assert data[0].name == "White Rum"

    def test_get_ingredient_at_bottle(self, db_commander: DatabaseCommander):
        """Test the get_ingredient_at_bottle method."""
        ingredient = db_commander.get_ingredient_at_bottle(1)
        assert ingredient is not None
        assert ingredient.name == "White Rum"

    def test_get_ingredient_at_bottle_not_set(self, db_commander: DatabaseCommander):
        """Test the get_ingredient_at_bottle method when no ingredient is set."""
        ingredient = db_commander.get_ingredient_at_bottle(10)
        assert ingredient is None

    @pytest.mark.parametrize("ing", [6, "Fanta"])
    def test_set_bottle_at_slot(self, db_commander: DatabaseCommander, ing: int | str):
        """Test the set_bottle_at_slot method."""
        db_commander.set_bottle_at_slot(ing, 1)
        ingredient = db_commander.get_ingredient_at_bottle(1)
        assert ingredient is not None
        assert ingredient.name == "Fanta"

    def test_set_bottle_volumelevel_to_max(self, db_commander: DatabaseCommander):
        """Test the set_bottle_volumelevel_to_max method."""
        db_commander.set_bottle_volumelevel_to_max([1])
        fill_levels = db_commander.get_bottle_fill_levels()
        assert fill_levels[0] == 100

    def test_get_ingredient_names_at_bottles_with_empty(self, db_commander: DatabaseCommander):
        """Test the get_ingredient_names_at_bottles method with empty bottles."""
        ingredient_names = db_commander.get_ingredient_names_at_bottles()
        assert len(ingredient_names) == 24  # Includes the empty bottle
        assert ingredient_names[3] == ""  # Bottle 4 is empty
        # we have 4 bottles with ingredients
        assert len([name for name in ingredient_names if name != ""]) == 4
