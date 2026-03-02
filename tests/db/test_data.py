from __future__ import annotations

from src.database_commander import DatabaseCommander


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

    def test_delete_database_data(self, db_commander: DatabaseCommander):
        """Test the delete_database_data method."""
        db_commander.delete_database_data()
        cocktails = db_commander.get_all_cocktails()
        ingredients = db_commander.get_all_ingredients()
        assert len(cocktails) == 0
        assert len(ingredients) == 0
