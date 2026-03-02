from __future__ import annotations

import datetime

import pytest

from src.database_commander import DatabaseCommander


class TestResourceUsage:
    def test_save_and_get_resource_stats(self, db_commander: DatabaseCommander):
        """Test saving resource usage and retrieving resource stats."""
        # Prepare test data
        cpu_values = [10.5, 20.0, 15.0]
        ram_values = [10.0, 20.0, 15.0]
        session_number = 33
        now = datetime.datetime.now()
        for cpu, ram in zip(cpu_values, ram_values):
            db_commander.save_resource_usage(cpu, ram, session_number, timestamp=now)

        # Retrieve resource stats for session 1
        stats = db_commander.get_resource_stats(session_number)
        assert stats is not None
        assert stats.samples == len(cpu_values)
        assert stats.min_cpu == min(cpu_values)
        assert stats.max_cpu == max(cpu_values)
        assert pytest.approx(stats.mean_cpu) == round(sum(cpu_values) / len(cpu_values), 1)
        assert stats.min_ram == min(ram_values)
        assert stats.max_ram == max(ram_values)
        assert pytest.approx(stats.mean_ram) == round(sum(ram_values) / len(ram_values), 1)
        # When below max_raw_points, all values should be returned
        assert len(stats.raw_cpu) == len(cpu_values)
        assert len(stats.raw_ram) == len(ram_values)
        assert set(stats.raw_cpu) == set(cpu_values)
        assert set(stats.raw_ram) == set(ram_values)

    def test_save_and_get_resource_stats_returns_empty_data(self, db_commander: DatabaseCommander):
        """Test saving resource usage and retrieving empty resource stats."""
        stats = db_commander.get_resource_stats(1)
        assert stats is not None
        assert stats.samples == 0
        assert stats.min_cpu == pytest.approx(0.0)
        assert stats.max_cpu == pytest.approx(0.0)
        assert stats.mean_cpu == pytest.approx(0.0)
        assert stats.min_ram == pytest.approx(0.0)
        assert stats.max_ram == pytest.approx(0.0)
        assert stats.mean_ram == pytest.approx(0.0)
        assert len(stats.raw_cpu) == 0
        assert len(stats.raw_ram) == 0

    def test_get_resource_session_numbers(self, db_commander: DatabaseCommander):
        """Test getting resource session numbers."""
        cpu_values = [10.5, 20.0, 15.0]
        ram_values = [10.0, 20.0, 15.0]
        session_numbers = [2, 1, 3]
        now = datetime.datetime.now()
        for cpu, ram, session_number in zip(cpu_values, ram_values, session_numbers):
            db_commander.save_resource_usage(cpu, ram, session_number, timestamp=now)

        inserted_numbers = db_commander.get_resource_session_numbers()
        assert len(inserted_numbers) == 3
        assert [x.session_id for x in inserted_numbers] == sorted(session_numbers)
        # check that the date string second element is "%Y-%m-%d %H:%M"
        assert all(now.strftime("%Y-%m-%d %H:%M") == x.start_time for x in inserted_numbers)

    def test_get_highest_session_number(self, db_commander: DatabaseCommander):
        """Test getting the highest session number."""
        cpu_values = [10.5, 20.0, 15.0]
        ram_values = [10.0, 20.0, 15.0]
        session_numbers = [1, 2, 3]
        now = datetime.datetime.now()
        for cpu, ram, session_number in zip(cpu_values, ram_values, session_numbers):
            db_commander.save_resource_usage(cpu, ram, session_number, timestamp=now)

        highest_session_number = db_commander.get_highest_session_number()
        assert highest_session_number == max(session_numbers)

    def test_get_resource_stats_samples_large_datasets(self, db_commander: DatabaseCommander):
        """Test that large datasets are sampled to prevent OOM."""
        session_number = 99
        now = datetime.datetime.now()
        # Create more data points than max_raw_points
        total_points = 100
        max_raw_points = 20
        cpu_values = [float(i % 100) for i in range(total_points)]
        ram_values = [float((i + 10) % 100) for i in range(total_points)]

        for cpu, ram in zip(cpu_values, ram_values):
            db_commander.save_resource_usage(cpu, ram, session_number, timestamp=now)

        stats = db_commander.get_resource_stats(session_number, max_raw_points=max_raw_points)

        # Samples should reflect total count
        assert stats.samples == total_points
        # Raw data should be limited to max_raw_points
        assert len(stats.raw_cpu) <= max_raw_points
        assert len(stats.raw_ram) <= max_raw_points
        # Aggregated stats should still be accurate (computed from all data in SQL)
        assert stats.min_cpu == min(cpu_values)
        assert stats.max_cpu == max(cpu_values)
        assert stats.min_ram == min(ram_values)
        assert stats.max_ram == max(ram_values)
        assert pytest.approx(stats.mean_cpu, rel=0.1) == sum(cpu_values) / len(cpu_values)
        assert pytest.approx(stats.mean_ram, rel=0.1) == sum(ram_values) / len(ram_values)

    def test_cleanup_resource_stats_does_not_remove_if_50_or_less(self, db_commander: DatabaseCommander):
        """Test that cleanup does not remove sessions if we have 50 or fewer."""
        now = datetime.datetime.now()
        # Create exactly 50 sessions
        for session_number in range(1, 51):
            db_commander.save_resource_usage(10.0, 20.0, session_number, timestamp=now)

        deleted_count = db_commander.cleanup_resource_stats(keep_sessions=50)
        assert deleted_count == 0

        # All sessions should still exist
        session_numbers = db_commander.get_resource_session_numbers()
        assert len(session_numbers) == 50

    def test_cleanup_resource_stats_removes_older_sessions(self, db_commander: DatabaseCommander):
        """Test that cleanup removes sessions older than the latest 50."""
        now = datetime.datetime.now()
        # Create 55 sessions (should remove the 5 oldest)
        for session_number in range(1, 56):
            db_commander.save_resource_usage(10.0, 20.0, session_number, timestamp=now)
            db_commander.save_resource_usage(15.0, 25.0, session_number, timestamp=now)  # 2 records per session

        deleted_count = db_commander.cleanup_resource_stats(keep_sessions=50)
        # 5 sessions with 2 records each = 10 deleted records
        assert deleted_count == 10

        # Only 50 sessions should remain
        session_numbers = db_commander.get_resource_session_numbers()
        assert len(session_numbers) == 50

        # The oldest sessions (1-5) should be removed, keeping 6-55
        session_ids = [s.session_id for s in session_numbers]
        assert min(session_ids) == 6
        assert max(session_ids) == 55

    def test_cleanup_resource_stats_with_no_data(self, db_commander: DatabaseCommander):
        """Test that cleanup works correctly when there's no data."""
        deleted_count = db_commander.cleanup_resource_stats(keep_sessions=50)
        assert deleted_count == 0

    def test_cleanup_resource_stats_with_custom_keep_sessions(self, db_commander: DatabaseCommander):
        """Test cleanup with a custom number of sessions to keep."""
        now = datetime.datetime.now()
        # Create 10 sessions
        for session_number in range(1, 11):
            db_commander.save_resource_usage(10.0, 20.0, session_number, timestamp=now)

        # Keep only 5 sessions
        deleted_count = db_commander.cleanup_resource_stats(keep_sessions=5)
        assert deleted_count == 5  # 5 sessions with 1 record each

        # Only 5 sessions should remain
        session_numbers = db_commander.get_resource_session_numbers()
        assert len(session_numbers) == 5

        # Sessions 6-10 should remain (the latest 5)
        session_ids = [s.session_id for s in session_numbers]
        assert session_ids == [6, 7, 8, 9, 10]
