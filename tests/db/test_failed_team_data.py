from __future__ import annotations

import pytest

from src.database_commander import DatabaseCommander, ElementNotFoundError


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
