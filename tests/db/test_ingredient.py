from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.database_commander import (
    DatabaseCommander,
    DatabaseTransactionError,
    ElementAlreadyExistsError,
    ElementNotFoundError,
)
from src.db_models import DbIngredient


class TestIngredient:
    def test_get_ingredient(self, db_commander: DatabaseCommander):
        """Test the get_ingredient method."""
        ingredient = db_commander.get_ingredient(1)
        assert ingredient is not None
        assert ingredient.name == "White Rum"
        assert ingredient.alcohol == 40
        assert ingredient.bottle_volume == 1000
        assert ingredient.fill_level == 1000
        assert ingredient.hand is False
        assert ingredient.pump_speed == 100

    def test_get_all_ingredients(self, db_commander: DatabaseCommander):
        """Test the get_all_ingredients method."""
        ingredients = db_commander.get_all_ingredients()
        assert len(ingredients) == 7

        cola = next((i for i in ingredients if i.name == "Cola"), None)
        assert cola is not None
        assert cola.alcohol == 0
        assert cola.bottle_volume == 1000
        assert cola.fill_level == 0
        assert cola.hand is False
        assert cola.pump_speed == 100

    def test_get_all_machine_ingredients(self, db_commander: DatabaseCommander):
        """Test the get_all_machine_ingredients method."""
        ingredients = db_commander.get_all_ingredients(get_hand=False)
        assert len(ingredients) == 6

        cola = next((i for i in ingredients if i.name == "Cola"), None)
        assert cola is not None

    def test_get_all_hand_ingredients(self, db_commander: DatabaseCommander):
        """Test the get_all_hand_ingredients method."""
        ingredients = db_commander.get_all_ingredients(get_machine=False)
        assert len(ingredients) == 1

        blue_curacao = next((i for i in ingredients if i.name == "Blue Curacao"), None)
        assert blue_curacao is not None

    def test_get_all_ingredients_return_empty_if_both_false(self, db_commander: DatabaseCommander):
        """Test the get_all_ingredients method."""
        ingredients = db_commander.get_all_ingredients(get_hand=False, get_machine=False)
        assert len(ingredients) == 0

    def test_get_ingredient_at_bottle(self, db_commander: DatabaseCommander):
        """Test the get_ingredient_at_bottle method."""
        ingredient = db_commander.get_ingredient_at_bottle(1)
        assert ingredient is not None
        assert ingredient.name == "White Rum"

    def test_get_ingredient_names_at_bottles(self, db_commander: DatabaseCommander):
        """Test the get_ingredient_names_at_bottles method."""
        ingredient_names = db_commander.get_ingredient_names_at_bottles()
        assert len(ingredient_names) == 24
        assert ingredient_names[1] == "Cola"

    def test_set_ingredient_data(self, db_commander: DatabaseCommander):
        """Test the set_ingredient_data method."""
        db_commander.set_ingredient_data("New Unique Name", 40, 1000, 800, False, 10, 1, 100, "cl")
        ingredient = db_commander.get_ingredient(1)
        assert ingredient is not None
        assert ingredient.name == "New Unique Name"
        assert ingredient.alcohol == 40
        assert ingredient.bottle_volume == 1000
        assert ingredient.fill_level == 800
        assert ingredient.hand is False
        assert ingredient.pump_speed == 10
        assert ingredient.id == 1
        assert ingredient.cost == 100
        assert ingredient.unit == "cl"

    def test_set_ingredient_level_to_value(self, db_commander: DatabaseCommander):
        """Test the set_ingredient_level_to_value method."""
        db_commander.set_ingredient_level_to_value(1, 500)
        ingredient = db_commander.get_ingredient(1)
        assert ingredient is not None
        assert ingredient.fill_level == 500

    def test_raise_not_found_on_set_ingredient_level_to_value(self, db_commander: DatabaseCommander):
        """Test the set_ingredient_level_to_value method."""
        with pytest.raises(ElementNotFoundError):
            db_commander.set_ingredient_level_to_value(999, 500)

    def test_insert_new_ingredient(self, db_commander: DatabaseCommander):
        """Test the insert_new_ingredient method."""
        db_commander.insert_new_ingredient("New Ingredient", 0, 1000, False, 10, 100, "ml")
        ingredient = db_commander.get_ingredient("New Ingredient")
        assert ingredient is not None
        assert ingredient.name == "New Ingredient"

    def test_increment_ingredient_consumption(self, db_commander: DatabaseCommander):
        """Test the increment_ingredient_consumption method."""
        consumption = 100
        db_commander.increment_ingredient_consumption("White Rum", consumption)
        session = Session(db_commander.engine)
        ingredient = session.query(DbIngredient).filter_by(name="White Rum").first()
        session.close()
        assert ingredient is not None
        assert ingredient.consumption == consumption
        assert ingredient.consumption_lifetime == consumption
        cost = int(round(ingredient.cost / ingredient.volume * consumption, 0))
        assert ingredient.cost_consumption == cost
        assert ingredient.cost_consumption_lifetime == cost
        # check multiple times works as well
        db_commander.increment_ingredient_consumption("White Rum", consumption)
        ingredient = session.query(DbIngredient).filter_by(name="White Rum").first()
        session.close()
        assert ingredient is not None
        assert ingredient.consumption == 2 * consumption
        assert ingredient.consumption_lifetime == 2 * consumption
        assert ingredient.cost_consumption == 2 * cost
        assert ingredient.cost_consumption_lifetime == 2 * cost

    def test_set_multiple_ingredient_consumption(self, db_commander: DatabaseCommander):
        """Test the set_multiple_ingredient_consumption method."""
        ingredients = ["White Rum", "Cola"]
        amount_1 = 100
        amount_2 = 50
        amounts = [amount_1, amount_2]
        db_commander.set_multiple_ingredient_consumption(ingredients, amounts)
        session = Session(db_commander.engine)
        ingredient_1 = session.query(DbIngredient).filter_by(name=ingredients[0]).first()
        ingredient_2 = session.query(DbIngredient).filter_by(name=ingredients[1]).first()
        session.close()
        assert ingredient_1 is not None
        assert ingredient_1.consumption == amount_1
        assert ingredient_1.consumption_lifetime == amount_1
        cost_1 = int(round(ingredient_1.cost / ingredient_1.volume * amount_1, 0))
        assert ingredient_1.cost_consumption == cost_1
        assert ingredient_1.cost_consumption_lifetime == cost_1
        assert ingredient_2 is not None
        assert ingredient_2.consumption == amount_2
        assert ingredient_2.consumption_lifetime == amount_2
        cost_2 = int(round(ingredient_2.cost / ingredient_2.volume * amount_2, 0))
        assert ingredient_2.cost_consumption == cost_2
        assert ingredient_2.cost_consumption_lifetime == cost_2

    @pytest.mark.parametrize("ingredient_id", (1, 4, 6))
    def test_delete_ingredient_fails(self, db_commander: DatabaseCommander, ingredient_id: int):
        """Test the delete_ingredient method."""
        with pytest.raises(DatabaseTransactionError):
            db_commander.delete_ingredient(ingredient_id)
        ingredient = db_commander.get_ingredient(ingredient_id)
        assert ingredient is not None

    def test_delete_ingredient(self, db_commander: DatabaseCommander):
        """Test the delete_ingredient method."""
        db_commander.insert_new_ingredient("New Ingredient", 0, 1000, False, 10, 100, "ml")
        ingredient = db_commander.get_ingredient("New Ingredient")
        assert ingredient is not None
        db_commander.delete_ingredient(ingredient.id)
        ingredient = db_commander.get_ingredient(ingredient.id)
        assert ingredient is None

    @pytest.mark.parametrize("ing", ([1, 2], ["White Rum", "Cola"]))
    def test_insert_multiple_existing_handadd_ingredients(
        self, db_commander: DatabaseCommander, ing: list[str] | list[int]
    ):
        """Test the insert_multiple_existing_handadd_ingredients method."""
        db_commander.insert_multiple_existing_handadd_ingredients(ing)
        names = db_commander.get_available_ingredient_names()
        assert "White Rum" in names
        assert "Cola" in names

    def test_delete_existing_handadd_ingredient(self, db_commander: DatabaseCommander):
        """Test the delete_existing_handadd_ingredient method."""
        db_commander.delete_existing_handadd_ingredient()
        names = db_commander.get_available_ingredient_names()
        assert len(names) == 0

    def test_get_nonexistent_ingredient(self, db_commander: DatabaseCommander):
        """Test getting an ingredient that does not exist."""
        ingredient = db_commander.get_ingredient(999)
        assert ingredient is None

    def test_insert_duplicate_ingredient(self, db_commander: DatabaseCommander):
        """Test inserting an ingredient with a duplicate name."""
        with pytest.raises(ElementAlreadyExistsError):
            db_commander.insert_new_ingredient("White Rum", 40, 1000, False, 100, 100, "ml")

    def test_delete_nonexistent_ingredient(self, db_commander: DatabaseCommander):
        """Test deleting an ingredient that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.delete_ingredient(999)

    def test_set_nonexistent_ingredient(self, db_commander: DatabaseCommander):
        """Test setting an ingredient that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.set_ingredient_data("Nonexistent", 0, 0, 0, False, 0, 999, 0, "ml")

    def test_increment_nonexistent_ingredient_consumption(self, db_commander: DatabaseCommander):
        """Test incrementing the consumption of an ingredient that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.increment_ingredient_consumption("Nonexistent", 100)

    def test_delete_ingredient_still_in_use(self, db_commander: DatabaseCommander):
        """Test deleting an ingredient that is still in use."""
        with pytest.raises(DatabaseTransactionError):
            db_commander.delete_ingredient(1)
