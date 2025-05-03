from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from src.database_commander import (
    DatabaseCommander,
    DatabaseTransactionError,
    ElementAlreadyExistsError,
    ElementNotFoundError,
)
from src.db_models import DbIngredient, DbRecipe


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
        db_commander.increment_recipe_counter("Cuba Libre")
        session = Session(db_commander.engine)
        recipe = session.query(DbRecipe).filter_by(name="Cuba Libre").first()
        session.close()
        assert recipe is not None
        assert recipe.counter == 1

    def test_set_recipe(self, db_commander: DatabaseCommander):
        """Test the set_recipe method."""
        db_commander.set_recipe(1, "Cuba Libre", 11, 290, True, False, [(1, 80, 1), (2, 210, 2)])
        cocktail = db_commander.get_cocktail(1)
        assert cocktail is not None
        assert cocktail.name == "Cuba Libre"

    def test_insert_new_recipe(self, db_commander: DatabaseCommander):
        """Test the insert_new_recipe method."""
        db_commander.insert_new_recipe("New Recipe", 0, 1000, True, False, [(1, 80, 1)])
        cocktail = db_commander.get_cocktail("New Recipe")
        assert cocktail is not None
        assert cocktail.name == "New Recipe"

    def test_insert_recipe_data(self, db_commander: DatabaseCommander):
        """Test the insert_recipe_data method."""
        ingredient_data = [(1, 80, 1), (2, 100, 2), (3, 50, 3)]
        cocktail = db_commander.insert_new_recipe("New Recipe", 0, 250, True, False, ingredient_data)
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
            db_commander.insert_new_recipe("Cuba Libre", 11, 290, True, False, [(1, 80, 1), (2, 210, 2)])

    def test_delete_nonexistent_recipe(self, db_commander: DatabaseCommander):
        """Test deleting a recipe that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.delete_recipe(999)

    def test_set_nonexistent_recipe(self, db_commander: DatabaseCommander):
        """Test setting a recipe that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.set_recipe(999, "Nonexistent", 0, 0, False, False, [])

    def test_increment_nonexistent_recipe_counter(self, db_commander: DatabaseCommander):
        """Test incrementing the counter of a recipe that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.increment_recipe_counter("Nonexistent")

    def test_delete_recipe_still_in_use(self, db_commander: DatabaseCommander):
        """Test deleting a recipe that is still in use."""
        db_commander.insert_new_recipe("Test Recipe", 0, 100, True, False, [(1, 50, 1)])
        with pytest.raises(DatabaseTransactionError):
            db_commander.delete_ingredient(1)

    def test_enable_all_recipes(self, db_commander: DatabaseCommander):
        """Test enabling all recipes."""
        db_commander.set_all_recipes_enabled()
        cocktails = db_commander.get_all_cocktails()
        assert all(cocktail.enabled for cocktail in cocktails)


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


class TestBackup:
    def test_create_backup(self, db_commander: DatabaseCommander):
        """Test the create_backup method."""
        with patch("shutil.copy") as mock_shutil_copy:
            db_commander.create_backup()
            mock_shutil_copy.assert_called_once()


class TestAvailable:
    def test_get_available_ingredient_names(self, db_commander: DatabaseCommander):
        """Test the get_available_ingredient_names method."""
        names = db_commander.get_available_ingredient_names()
        assert len(names) == 1
        assert names[0] == "Blue Curacao"

    def test_get_available_ids(self, db_commander: DatabaseCommander):
        """Test the get_available_ids method."""
        ids = db_commander.get_available_ids()
        assert len(ids) == 1
        assert ids[0] == 4


class TestData:
    def test_get_consumption_data_lists_recipes(self, db_commander: DatabaseCommander):
        """Test the get_consumption_data_lists_recipes method."""
        data = db_commander.get_consumption_data_lists_recipes()
        assert len(data) == 3
        assert data[0][1] == "Cuba Libre"

    def test_get_consumption_data_lists_ingredients(self, db_commander: DatabaseCommander):
        """Test the get_consumption_data_lists_ingredients method."""
        data = db_commander.get_consumption_data_lists_ingredients()
        assert len(data) == 3
        assert data[0][1] == "White Rum"

    def test_get_cost_data_lists_ingredients(self, db_commander: DatabaseCommander):
        """Test the get_cost_data_lists_ingredients method."""
        data = db_commander.get_cost_data_lists_ingredients()
        assert len(data) == 3
        assert data[0][1] == "White Rum"

    def test_delete_consumption_recipes(self, db_commander: DatabaseCommander):
        """Test the delete_consumption_recipes method."""
        db_commander.increment_recipe_counter("Cuba Libre")
        db_commander.delete_consumption_recipes()
        data = db_commander.get_consumption_data_lists_recipes()
        assert data[1][1] == 0

    def test_delete_consumption_ingredients(self, db_commander: DatabaseCommander):
        """Test the delete_consumption_ingredients method."""
        db_commander.increment_ingredient_consumption("White Rum", 100)
        db_commander.delete_consumption_ingredients()
        data = db_commander.get_consumption_data_lists_ingredients()
        assert data[1][1] == 0

    def test_delete_database_data(self, db_commander: DatabaseCommander):
        """Test the delete_database_data method."""
        db_commander.delete_database_data()
        cocktails = db_commander.get_all_cocktails()
        ingredients = db_commander.get_all_ingredients()
        assert len(cocktails) == 0
        assert len(ingredients) == 0


class TestFailedTeamData:
    def test_save_failed_teamdata(self, db_commander: DatabaseCommander):
        """Test the save_failed_teamdata method."""
        db_commander.save_failed_teamdata("test_payload")
        data = db_commander.get_failed_teamdata()
        assert data is not None
        assert data[1] == "test_payload"

    def test_get_failed_teamdata(self, db_commander: DatabaseCommander):
        """Test the get_failed_teamdata method."""
        db_commander.save_failed_teamdata("test_payload")
        data = db_commander.get_failed_teamdata()
        assert data is not None
        assert data[1] == "test_payload"

    def test_get_nonexistent_failed_teamdata(self, db_commander: DatabaseCommander):
        """Test getting failed teamdata that does not exist."""
        data = db_commander.get_failed_teamdata()
        assert data is None

    def test_delete_failed_teamdata(self, db_commander: DatabaseCommander):
        """Test the delete_failed_teamdata method."""
        db_commander.save_failed_teamdata("test_payload")
        data = db_commander.get_failed_teamdata()
        assert data is not None
        db_commander.delete_failed_teamdata(data[0])
        data = db_commander.get_failed_teamdata()
        assert data is None

    def test_delete_nonexistent_failed_teamdata(self, db_commander: DatabaseCommander):
        """Test deleting failed teamdata that does not exist."""
        with pytest.raises(ElementNotFoundError):
            db_commander.delete_failed_teamdata(999)
