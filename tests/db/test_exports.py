from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from src.database_commander import VIRGIN_NAME_TEMPLATE, DatabaseCommander
from src.db_models import DbIngredient, DbRecipe


class TestExports:
    def test_export_recipe_data(self, db_commander: DatabaseCommander):
        """Test that recipe counters are exported correctly."""
        number_cocktails = 3
        for _ in range(number_cocktails):
            db_commander.increment_recipe_counter("Cuba Libre", virgin=False)

        db_commander.export_recipe_data()
        export_data = db_commander.get_export_data()
        today = datetime.date.today().strftime("%Y-%m-%d")
        assert today in export_data

        # Check if the recipe counter was exported correctly
        assert "Cuba Libre" in export_data[today].recipes
        assert export_data[today].recipes["Cuba Libre"] == number_cocktails

        # Check that the counter was reset in the database (need to check directly in DB)
        session = Session(db_commander.engine)
        recipe = session.query(DbRecipe).filter_by(name="Cuba Libre").first()
        session.close()
        assert recipe is not None
        assert recipe.counter == 0

    def test_export_ingredient_data(self, db_commander: DatabaseCommander):
        """Test that ingredient consumption and cost are exported correctly."""
        consumption = 100
        db_commander.increment_ingredient_consumption("White Rum", consumption)
        db_commander.export_ingredient_data()
        export_data = db_commander.get_export_data()
        today = datetime.date.today().strftime("%Y-%m-%d")
        assert today in export_data

        # Check if the ingredient consumption was exported correctly
        assert "White Rum" in export_data[today].ingredients
        assert export_data[today].ingredients["White Rum"] == consumption
        today_cost = export_data[today].cost
        assert today_cost is not None
        assert "White Rum" in today_cost

        # Get the ingredient to calculate the expected cost
        ingredient = db_commander.get_ingredient("White Rum")
        assert ingredient is not None
        expected_cost = int(round(ingredient.cost / ingredient.bottle_volume * consumption, 0))
        assert today_cost["White Rum"] == expected_cost

        # Check that the consumption was reset (directly in DB)
        session = Session(db_commander.engine)
        db_ingredient = session.query(DbIngredient).filter_by(name="White Rum").first()
        assert db_ingredient is not None
        session.close()
        assert db_ingredient.consumption == 0
        assert db_ingredient.cost_consumption == 0

    def test_export_zero_cost_ingredient(self, db_commander: DatabaseCommander):
        """Test that ingredients with zero cost are not included in cost exports."""
        # Set the cost of an ingredient to 0
        ingredient = db_commander.get_ingredient("Cola")
        assert ingredient is not None
        db_commander.set_ingredient_data(
            ingredient.name,
            ingredient.alcohol,
            ingredient.bottle_volume,
            ingredient.fill_level,
            ingredient.hand,
            ingredient.pump_speed,
            ingredient.id,
            0,
            ingredient.unit,
        )

        consumption = 200
        db_commander.increment_ingredient_consumption("Cola", consumption)
        db_commander.export_ingredient_data()
        export_data = db_commander.get_export_data()
        today = datetime.date.today().strftime("%Y-%m-%d")

        assert "Cola" in export_data[today].ingredients
        assert export_data[today].ingredients["Cola"] == consumption
        today_cost = export_data[today].cost
        assert today_cost is not None
        assert "Cola" not in today_cost

    def test_export_only_if_consumption_greater_than_zero(self, db_commander: DatabaseCommander):
        """Test that only ingredients with consumption > 0 are exported."""
        ingredient_name = "Fanta"
        db_commander.export_ingredient_data()
        export_data = db_commander.get_export_data()
        today = datetime.date.today().strftime("%Y-%m-%d")

        # Check that the ingredient without consumption is not in the export
        if today in export_data:
            assert ingredient_name not in export_data[today].ingredients

    def test_export_dates(self, db_commander: DatabaseCommander):
        """Test that export dates are returned correctly."""
        db_commander.increment_recipe_counter("Cuba Libre", virgin=False)
        db_commander.export_recipe_data()
        export_dates = db_commander.get_export_dates()

        # Today's date should be in the list
        today = datetime.date.today().strftime("%Y-%m-%d")
        assert today in export_dates

    def test_multiple_exports_same_day(self, db_commander: DatabaseCommander):
        """Test that multiple exports on the same day are combined correctly."""
        today = datetime.date.today()

        # First export
        db_commander.increment_recipe_counter("Cuba Libre", virgin=False)
        db_commander.increment_ingredient_consumption("White Rum", 50)
        db_commander.export_recipe_data()
        db_commander.export_ingredient_data()

        # Second export on the same day
        db_commander.increment_recipe_counter("Cuba Libre", virgin=False)
        db_commander.increment_recipe_counter("Cuba Libre", virgin=True)
        db_commander.increment_ingredient_consumption("White Rum", 100)
        db_commander.export_recipe_data()
        db_commander.export_ingredient_data()

        # Verify exports were combined
        export_data = db_commander.get_export_data()
        today_str = today.strftime("%Y-%m-%d")

        # Check that the recipe counter was combined (1 + 2 = 3)
        assert today_str in export_data
        assert "Cuba Libre" in export_data[today_str].recipes
        assert export_data[today_str].recipes["Cuba Libre"] == 2
        assert export_data[today_str].recipes.get(VIRGIN_NAME_TEMPLATE.format("Cuba Libre"), 0) == 1

        # Check that the ingredient consumption was combined (50 + 100 = 150)
        assert "White Rum" in export_data[today_str].ingredients
        assert export_data[today_str].ingredients["White Rum"] == 150

        # Check that the cost consumption was also combined correctly
        ingredient = db_commander.get_ingredient("White Rum")
        assert ingredient is not None
        expected_cost = int(round(ingredient.cost / ingredient.bottle_volume * 150, 0))
        today_cost = export_data[today_str].cost
        assert today_cost is not None
        assert "White Rum" in today_cost
        assert today_cost["White Rum"] == expected_cost

    def test_same_cocktail_counter_only_if_greater_zero(self, db_commander: DatabaseCommander):
        """Test that virgin and normal cocktail are only exported if consumption > 0."""
        db_commander.increment_recipe_counter("Cuba Libre", virgin=False)
        db_commander.increment_recipe_counter("Tequila Sunrise", virgin=True)
        db_commander.export_recipe_data()
        export_data = db_commander.get_export_data()
        today = datetime.date.today().strftime("%Y-%m-%d")

        assert today in export_data
        assert "Cuba Libre" in export_data[today].recipes
        assert VIRGIN_NAME_TEMPLATE.format("Cuba Libre") not in export_data[today].recipes
        assert "Tequila Sunrise" not in export_data[today].recipes
        assert VIRGIN_NAME_TEMPLATE.format("Tequila Sunrise") in export_data[today].recipes
