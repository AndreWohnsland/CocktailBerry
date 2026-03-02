from __future__ import annotations

from src.database_commander import DatabaseCommander


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

    def test_insert_empty_silently_skip(self, db_commander: DatabaseCommander):
        db_commander.delete_existing_handadd_ingredient()
        db_commander.insert_multiple_existing_handadd_ingredients([])
        assert db_commander.get_available_ingredient_names() == []
