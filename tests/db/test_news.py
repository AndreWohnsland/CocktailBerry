from __future__ import annotations

import pytest

from src.database_commander import DatabaseCommander, ElementNotFoundError


class TestNews:
    def test_get_unacknowledged_news_keys_empty_list(self, db_commander: DatabaseCommander):
        """Test that empty list returns empty list."""
        result = db_commander.get_unacknowledged_news_keys([])
        assert result == []

    def test_get_unacknowledged_news_keys_new_keys(self, db_commander: DatabaseCommander):
        """Test that new news keys are returned as unacknowledged."""
        news_keys = ["news_v2_available", "news_feature_update"]
        result = db_commander.get_unacknowledged_news_keys(news_keys)
        assert len(result) == 2
        assert "news_v2_available" in result
        assert "news_feature_update" in result

    def test_acknowledge_news(self, db_commander: DatabaseCommander):
        """Test that news can be acknowledged and won't be returned again."""
        news_keys = ["news_v2_available", "news_feature_update"]

        # First call - should return all keys
        result = db_commander.get_unacknowledged_news_keys(news_keys)
        assert len(result) == 2

        # Acknowledge one news
        db_commander.acknowledge_news("news_v2_available")

        # Second call - should only return unacknowledged
        result = db_commander.get_unacknowledged_news_keys(news_keys)
        assert len(result) == 1
        assert "news_feature_update" in result
        assert "news_v2_available" not in result

    def test_acknowledge_nonexistent_news(self, db_commander: DatabaseCommander):
        """Test that acknowledging non-existent news doesn't raise an error."""
        with pytest.raises(ElementNotFoundError):
            db_commander.acknowledge_news("nonexistent_news_key")

    def test_news_persistence_across_calls(self, db_commander: DatabaseCommander):
        """Test that news state persists across multiple calls."""
        news_keys = ["news_v2_available"]

        # Get unacknowledged news
        result1 = db_commander.get_unacknowledged_news_keys(news_keys)
        assert len(result1) == 1

        # Call again without acknowledging - should still return same
        result2 = db_commander.get_unacknowledged_news_keys(news_keys)
        assert len(result2) == 1
        assert result1 == result2

        # Acknowledge
        db_commander.acknowledge_news("news_v2_available")

        # Call again - should return empty
        result3 = db_commander.get_unacknowledged_news_keys(news_keys)
        assert len(result3) == 0
