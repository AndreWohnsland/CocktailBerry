from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from src.database_commander import DatabaseCommander
from src.db_models import DbEvent
from src.models import EventType


class TestEvents:
    def test_save_event_basic(self, db_commander: DatabaseCommander):
        """Test saving a basic event without additional info."""
        db_commander.save_event(EventType.CLEANING)
        events = db_commander.get_events()
        assert len(events) == 1
        assert events[0].event_type == EventType.CLEANING
        assert events[0].additional_info is None

    def test_save_event_with_additional_info(self, db_commander: DatabaseCommander):
        """Test saving an event with additional info."""
        db_commander.save_event(EventType.COCKTAIL_PREPARATION, additional_info='{"cocktail": "Cuba Libre"}')
        events = db_commander.get_events()
        assert len(events) == 1
        assert events[0].event_type == EventType.COCKTAIL_PREPARATION
        assert events[0].additional_info == '{"cocktail": "Cuba Libre"}'

    def test_save_multiple_events(self, db_commander: DatabaseCommander):
        """Test saving multiple events of different types."""
        db_commander.save_event(EventType.CLEANING)
        db_commander.save_event(EventType.COCKTAIL_PREPARATION, additional_info="Cuba Libre")
        db_commander.save_event(EventType.SHUTDOWN)

        events = db_commander.get_events()
        assert len(events) == 3
        # Events are ordered by timestamp descending
        event_types = [e.event_type for e in events]
        assert EventType.CLEANING in event_types
        assert EventType.COCKTAIL_PREPARATION in event_types
        assert EventType.SHUTDOWN in event_types

    def test_get_events_filter_by_type(self, db_commander: DatabaseCommander):
        """Test filtering events by type."""
        db_commander.save_event(EventType.CLEANING)
        db_commander.save_event(EventType.COCKTAIL_PREPARATION)
        db_commander.save_event(EventType.CLEANING)
        db_commander.save_event(EventType.SHUTDOWN)

        # Filter for CLEANING only
        cleaning_events = db_commander.get_events(event_types=[EventType.CLEANING])
        assert len(cleaning_events) == 2
        assert all(e.event_type == EventType.CLEANING for e in cleaning_events)

        # Filter for multiple types
        filtered_events = db_commander.get_events(event_types=[EventType.CLEANING, EventType.SHUTDOWN])
        assert len(filtered_events) == 3

    def test_get_events_filter_by_date(self, db_commander: DatabaseCommander):
        """Test filtering events by date range."""
        db_commander.save_event(EventType.CLEANING)

        # Get events with future start_date should return empty
        future_date = datetime.datetime.now() + datetime.timedelta(days=1)
        events = db_commander.get_events(start_date=future_date)
        assert len(events) == 0

        # Get events with past start_date should return all
        past_date = datetime.datetime.now() - datetime.timedelta(days=1)
        events = db_commander.get_events(start_date=past_date)
        assert len(events) == 1

    def test_all_event_types_can_be_saved(self, db_commander: DatabaseCommander):
        """Test that all EventType values can be saved and retrieved."""
        for event_type in EventType:
            db_commander.save_event(event_type)

        events = db_commander.get_events()
        assert len(events) == len(EventType)
        saved_types = {e.event_type for e in events}
        assert saved_types == set(EventType)

    def test_event_timestamp_auto_generated(self, db_commander: DatabaseCommander):
        """Test that timestamp is automatically generated."""
        before = datetime.datetime.now()
        db_commander.save_event(EventType.CLEANING)
        after = datetime.datetime.now()

        events = db_commander.get_events()
        assert len(events) == 1
        event_timestamp = datetime.datetime.fromisoformat(events[0].timestamp)
        assert before.replace(microsecond=0) <= event_timestamp <= after.replace(microsecond=0)

    def test_get_events_handles_legacy_renamed_event_type(self, db_commander: DatabaseCommander):
        """Test that legacy renamed event values can still be loaded from DB."""
        session = Session(db_commander.engine)
        try:
            session.add(DbEvent(event_type="COCKTAIL_CANCELLATION", additional_info="legacy"))
            session.commit()
        finally:
            session.close()

        events = db_commander.get_events()
        assert len(events) == 1
        assert events[0].event_type == EventType.COCKTAIL_CANCELED
        assert events[0].additional_info == "legacy"

    def test_get_events_handles_removed_or_unknown_event_type(self, db_commander: DatabaseCommander):
        """Test that removed/unknown historic event values do not crash loading."""
        session = Session(db_commander.engine)
        try:
            session.add(DbEvent(event_type="SOME_REMOVED_EVENT", additional_info="historic"))
            session.commit()
        finally:
            session.close()

        events = db_commander.get_events()
        assert len(events) == 1
        assert events[0].event_type == EventType.UNKNOWN
        assert events[0].additional_info == "historic"
