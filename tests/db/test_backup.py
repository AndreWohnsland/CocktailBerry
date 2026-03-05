from __future__ import annotations

from unittest.mock import patch

from src.database_commander import DatabaseCommander


class TestBackup:
    def test_create_backup(self, db_commander: DatabaseCommander):
        """Test the create_backup method."""
        with patch("shutil.copy") as mock_shutil_copy:
            db_commander.create_backup()
            mock_shutil_copy.assert_called_once()
