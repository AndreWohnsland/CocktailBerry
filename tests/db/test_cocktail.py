from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.database_commander import (
    DatabaseCommander,
    DatabaseTransactionError,
    ElementAlreadyExistsError,
    ElementNotFoundError,
)
from src.db_models import DbRecipe


class TestCocktail:
    def test_get_cocktail(self, db_commander: DatabaseCommander):
        """Test the get_cocktail method."""
        cocktail = db_commander.get_cocktail(1)
        assert cocktail is not None
        assert cocktail.name == "Cuba Libre"
        assert cocktail.alcohol == 11
        assert cocktail.amount == 290
        assert cocktail.enabled is True
        assert cocktail.virgin_available is False
        assert len(cocktail.ingredients) == 2

        ingredient = cocktail.ingredients[0]
        assert ingredient.name == "Cola"
        assert ingredient.alcohol == 0
        assert ingredient.amount == 210

    def test_get_all_cocktails(self, db_commander: DatabaseCommander):
        """Test the get_all_cocktails method."""
        cocktails = db_commander.get_all_cocktails()
        assert len(cocktails) == 5

        cuba_libre = next((c for c in cocktails if c.name == "Cuba Libre"), None)
        assert cuba_libre is not None
        assert cuba_libre.alcohol == 11
        assert cuba_libre.amount == 290
        assert cuba_libre.enabled is True
        assert cuba_libre.virgin_available is False
        assert len(cuba_libre.ingredients) == 2

    def test_get_possible_cocktails(self, db_commander: DatabaseCommander):
        """Test the get_possible_cocktails method."""
        possible_cocktails = db_commander.get_possible_cocktails(max_hand_ingredients=1)
        # Now we should have 3 possible cocktails: Cuba Libre, With Handadd, and Virgin Only Possible
        assert len(possible_cocktails) == 3
        # Check that Cuba Libre is in the list
        cuba_libre = next((c for c in possible_cocktails if c.name == "Cuba Libre"), None)
        assert cuba_libre is not None
        assert cuba_libre.only_virgin is False

    def test_get_possible_cocktail_virgin_only(self, db_commander: DatabaseCommander):
        """Test that a cocktail that can only be made in virgin form is properly flagged."""
        possible_cocktails = db_commander.get_possible_cocktails(max_hand_ingredients=1)

        virgin_only = next((c for c in possible_cocktails if c.name == "Virgin Only Possible"), None)
        assert virgin_only is not None
        assert virgin_only.only_virgin is True

        # Verify that this cocktail has an alcoholic ingredient that's not available
        alcoholic_ingredients = [ing for ing in virgin_only.ingredients if ing.alcohol > 0]
        assert len(alcoholic_ingredients) > 0

        # Check that the virgin ingredients are available either via machine or hand
        virgin_ingredients = [ing for ing in virgin_only.ingredients if ing.alcohol == 0]
        assert len(virgin_ingredients) > 0

        for ing in virgin_ingredients:
            # Either the ingredient is connected to a bottle or it's in the available handadd list
            assert ing.bottle is not None or ing.id in db_commander.get_available_ids()

    def test_get_disabled_cocktails(self, db_commander: DatabaseCommander):
        """Test that we can get only not enabled cocktails."""
        disabled_cocktails = db_commander.get_all_cocktails(status="disabled")
        assert len(disabled_cocktails) == 1
        tequila_sunrise = next((c for c in disabled_cocktails if c.name == "Tequila Sunrise"), None)
        assert tequila_sunrise is not None

    def test_increment_recipe_counter(self, db_commander: DatabaseCommander):
        """Test the increment_recipe_counter method."""
        db_commander.increment_recipe_counter("Cuba Libre", virgin=False)
        session = Session(db_commander.engine)
        recipe = session.query(DbRecipe).filter_by(name="Cuba Libre").first()
        session.close()
        assert recipe is not None
        assert recipe.counter == 1
        assert recipe.counter_virgin == 0

    def test_increment_recipe_counter_virgin(self, db_commander: DatabaseCommander):
        """Test the increment_recipe_counter method."""
        db_commander.increment_recipe_counter("Cuba Libre", virgin=True)
        session = Session(db_commander.engine)
        recipe = session.query(DbRecipe).filter_by(name="Cuba Libre").first()
        session.close()
        assert recipe is not None
        assert recipe.counter == 0
        assert recipe.counter_virgin == 1

    def test_set_recipe(self, db_commander: DatabaseCommander):
        """Test the set_recipe method."""
        db_commander.set_recipe(1, "Cuba Libre 2", 11, 290, 1.0, True, False, [(1, 80, 1), (2, 210, 2)])
        cocktail = db_commander.get_cocktail(1)
        assert cocktail is not None
        assert cocktail.name == "Cuba Libre 2"
        assert cocktail.price_per_100_ml == pytest.approx(1.0)

    def test_insert_new_recipe(self, db_commander: DatabaseCommander):
        """Test the insert_new_recipe method."""
        db_commander.insert_new_recipe("New Recipe", 0, 1000, 8.5, True, False, [(1, 80, 1)])
        cocktail = db_commander.get_cocktail("New Recipe")
        assert cocktail is not None
        assert cocktail.name == "New Recipe"
        assert cocktail.price_per_100_ml == pytest.approx(8.5)

    def test_insert_recipe_data(self, db_commander: DatabaseCommander):
        """Test the insert_recipe_data method."""
        ingredient_data = [(1, 80, 1), (2, 100, 2), (3, 50, 3)]
        cocktail = db_commander.insert_new_recipe("New Recipe", 0, 250, 4.0, True, False, ingredient_data)
        assert cocktail is not None
        cocktail = db_commander.get_cocktail(cocktail.id)
        assert cocktail is not None
        assert len(cocktail.ingredients) == 3
        # test that each ingredient is existing (first integer is id)
        # sort ingredients by id
        cocktail.ingredients.sort(key=lambda x: x.id)
        for ingredient, data in zip(cocktail.ingredients, ingredient_data):
            assert ingredient.id is data[0]
            assert ingredient.amount is data[1]
            assert ingredient.recipe_order is data[2]

    def test_delete_recipe(self, db_commander: DatabaseCommander):
        """Test the delete_recipe method."""
        db_commander.delete_recipe("Cuba Libre")
        cocktail = db_commander.get_cocktail("Cuba Libre")
        assert cocktail is None

    def test_delete_recipe_ingredient_data(self, db_commander: DatabaseCommander):
        """Test the delete_recipe_ingredient_data method."""
        db_commander.delete_recipe_ingredient_data(1)
        cocktail = db_commander.get_cocktail(1)
        assert cocktail is not None
        assert len(cocktail.ingredients) == 0

    def test_get_nonexistent_cocktail(self, db_commander: DatabaseCommander):
        """Test getting a cocktail that does not exist."""
        cocktail = db_commander.get_cocktail(999)
        assert cocktail is None

    def test_insert_duplicate_recipe(self, db_commander: DatabaseCommander):
        """Test inserting a recipe with a duplicate name."""
        with pytest.raises(ElementAlreadyExistsError):
            db_commander.insert_new_recipe("Cuba Libre", 11, 290, 5.0, True, False, [(1, 80, 1), (2, 210, 2)])

    def test_delete_nonexistent_recipe(self, db_commander: DatabaseCommander):
        """Test deleting a recipe that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.delete_recipe(999)

    def test_set_nonexistent_recipe(self, db_commander: DatabaseCommander):
        """Test setting a recipe that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.set_recipe(999, "Nonexistent", 0, 0, 1.0, False, False, [])

    def test_increment_nonexistent_recipe_counter(self, db_commander: DatabaseCommander):
        """Test incrementing the counter of a recipe that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.increment_recipe_counter("Nonexistent", virgin=False)

    def test_delete_recipe_still_in_use(self, db_commander: DatabaseCommander):
        """Test deleting a recipe that is still in use."""
        db_commander.insert_new_recipe("Test Recipe", 0, 100, 2.5, True, False, [(1, 50, 1)])
        with pytest.raises(DatabaseTransactionError):
            db_commander.delete_ingredient(1)

    def test_enable_all_recipes(self, db_commander: DatabaseCommander):
        """Test enabling all recipes."""
        db_commander.set_all_recipes_enabled()
        cocktails = db_commander.get_all_cocktails()
        assert all(cocktail.enabled for cocktail in cocktails)

    def test_optimal_ingredient_selection(self, db_commander: DatabaseCommander):
        """Test the optimal_ingredient_selection method."""
        for i in range(5):
            db_commander.insert_new_recipe(f"rumAndCola {i}", 10, 250, 5.0, True, False, [(1, 50, 1), (2, 200, 2)])
        top_ing_ids = db_commander.get_most_used_ingredient_ids(k=2)
        assert top_ing_ids == {1, 2}
