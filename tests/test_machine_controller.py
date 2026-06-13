from unittest.mock import MagicMock, patch

import pytest

from src.config.config_manager import CONFIG
from src.config.config_types import DCGPIOPumpConfig
from src.machine.controller import MachineController
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.scheduler import (
    _CLEANING_LARGE_AMOUNT,
    BaseScheduler,
    CleaningItem,
    CleaningScheduler,
    DispenserScheduler,
    PreparationItem,
    _dispense_item,
    _estimate_group_time,
    _group_by_recipe_order,
    _order_by_carriage_position,
    _total_travel,
    estimate_carriage_time,
    estimate_total_time,
)
from src.models import Ingredient


def _mock_dispenser(slot: int, volume_flow: float = 10.0, carriage_position: float = 0) -> MagicMock:
    """Create a mock dispenser."""
    mock = MagicMock(spec=BaseDispenser)
    mock.slot = slot
    mock.volume_flow = volume_flow
    mock.carriage_position = carriage_position
    mock.dispense.return_value = 0.0
    return mock


class TestController:
    def test_build_preparation_items(self):
        original_pump_config = CONFIG.PUMP_CONFIG.copy()
        original_maker_number_bottles = CONFIG.MAKER_NUMBER_BOTTLES

        try:
            CONFIG.PUMP_CONFIG = [  # type: ignore
                DCGPIOPumpConfig(pin=1, volume_flow=10.0, tube_volume=0),
                DCGPIOPumpConfig(pin=2, volume_flow=20.0, tube_volume=0),
            ]
            CONFIG.MAKER_NUMBER_BOTTLES = 2

            dispensers = {1: _mock_dispenser(1, 10.0), 2: _mock_dispenser(2, 20.0)}

            # Create actual Ingredient objects
            ingredients = [
                Ingredient(
                    id=1,
                    name="Test Ing 1",
                    alcohol=40,
                    bottle_volume=750,
                    fill_level=500,
                    hand=False,
                    pump_speed=100,
                    amount=100,
                    bottle=1,
                    recipe_order=1,
                ),
                Ingredient(
                    id=2,
                    name="Test Ing 2",
                    alcohol=0,
                    bottle_volume=750,
                    fill_level=500,
                    hand=False,
                    pump_speed=50,
                    amount=200,
                    bottle=2,
                    recipe_order=2,
                ),
                Ingredient(
                    id=3,
                    name="Hand Ing",
                    alcohol=0,
                    bottle_volume=750,
                    fill_level=500,
                    hand=True,
                    pump_speed=100,
                    amount=50,
                    bottle=None,
                    recipe_order=1,
                ),
            ]

            mc = MachineController()
            mc.dispensers = dispensers  # type: ignore
            prep_data = mc._build_preparation_items(ingredients)

            # Verify results
            assert len(prep_data) == 2
            assert prep_data[0].dispenser is dispensers[1]
            assert prep_data[0].pump_speed == 100
            assert prep_data[0].estimated_time == pytest.approx(10.0)  # 100ml / (10ml/s * 100%)
            assert prep_data[0].amount_ml == pytest.approx(100.0)
            assert prep_data[0].recipe_order == 1
            assert prep_data[0].ingredient is ingredients[0]

            assert prep_data[1].dispenser is dispensers[2]
            assert prep_data[1].pump_speed == 50
            assert prep_data[1].estimated_time == pytest.approx(20.0)  # 200ml / (20ml/s * 50%)
            assert prep_data[1].amount_ml == pytest.approx(200.0)
            assert prep_data[1].recipe_order == 2
            assert prep_data[1].ingredient is ingredients[1]

        finally:
            # Restore original configuration
            CONFIG.PUMP_CONFIG = original_pump_config  # type: ignore
            CONFIG.MAKER_NUMBER_BOTTLES = original_maker_number_bottles

    def test_group_by_recipe_order(self):
        dispensers = [_mock_dispenser(i) for i in range(1, 5)]

        prep_data = [
            PreparationItem(dispenser=dispensers[0], amount_ml=50, pump_speed=100, estimated_time=5, recipe_order=1),
            PreparationItem(dispenser=dispensers[1], amount_ml=50, pump_speed=100, estimated_time=5, recipe_order=1),
            PreparationItem(dispenser=dispensers[2], amount_ml=50, pump_speed=100, estimated_time=5, recipe_order=1),
            PreparationItem(dispenser=dispensers[3], amount_ml=50, pump_speed=100, estimated_time=5, recipe_order=2),
        ]

        groups = _group_by_recipe_order(prep_data)

        # Should have 2 groups (by recipe_order)
        assert len(groups) == 2
        assert len(groups[0]) == 3
        assert all(d.recipe_order == 1 for d in groups[0])
        assert len(groups[1]) == 1
        assert groups[1][0].recipe_order == 2

    def test_group_sorts_by_estimated_time_desc(self):
        dispensers = [_mock_dispenser(i) for i in range(1, 4)]

        prep_data = [
            PreparationItem(dispenser=dispensers[0], amount_ml=30, pump_speed=100, estimated_time=3, recipe_order=1),
            PreparationItem(dispenser=dispensers[1], amount_ml=70, pump_speed=100, estimated_time=7, recipe_order=1),
            PreparationItem(dispenser=dispensers[2], amount_ml=50, pump_speed=100, estimated_time=5, recipe_order=1),
        ]

        groups = _group_by_recipe_order(prep_data)
        assert [d.estimated_time for d in groups[0]] == [7, 5, 3]

    def test_estimate_group_time(self):
        # 3 items [7, 5, 3] with max_concurrent=2
        # Schedule: slot0=7, slot1=5+3=8 → makespan=8
        assert _estimate_group_time([5, 7, 3], 2) == pytest.approx(8.0)

        # All concurrent → makespan = max = 5
        assert _estimate_group_time([5, 3, 2], 3) == pytest.approx(5.0)

        # Single slot → sum = 8
        assert _estimate_group_time([5, 3], 1) == pytest.approx(8.0)

        # Empty
        assert _estimate_group_time([], 2) == pytest.approx(0.0)

    def test_dispense_item(self):
        mock_disp = _mock_dispenser(1)
        mock_disp.dispense.return_value = 100.0

        data = PreparationItem(
            dispenser=mock_disp,
            amount_ml=100,
            pump_speed=100,
            estimated_time=10,
        )

        _dispense_item(data)

        assert data.consumption == pytest.approx(100.0)
        assert data.done is True
        mock_disp.dispense.assert_called_once()
        call_args = mock_disp.dispense.call_args
        assert call_args.kwargs["amount_ml"] == 100
        assert call_args.kwargs["pump_speed"] == 100
        assert call_args.kwargs["revert"] is False

    def test_dispense_item_calls_on_step(self):
        """Exclusive path passes on_step to emit aggregate progress per update."""
        mock_disp = _mock_dispenser(1)

        def fake_dispense(amount_ml: float, pump_speed: int, revert: bool, callback) -> float:  # noqa: ANN001
            callback(50.0, False)
            callback(100.0, True)
            return 100.0

        mock_disp.dispense.side_effect = fake_dispense
        data = PreparationItem(dispenser=mock_disp, amount_ml=100, pump_speed=100, estimated_time=10)
        on_step = MagicMock()

        _dispense_item(data, on_step=on_step)

        assert on_step.call_count == 2
        assert data.consumption == pytest.approx(100.0)
        assert data.done is True

    def test_dispense_item_swallows_exceptions(self):
        mock_disp = _mock_dispenser(1)
        mock_disp.dispense.side_effect = RuntimeError("boom")
        data = PreparationItem(dispenser=mock_disp, amount_ml=100, pump_speed=100, estimated_time=10)

        _dispense_item(data)  # must not raise

        # consumption stays at default; done not set when an exception occurs
        assert data.done is False

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_scheduler_run(self, mock_sleep: MagicMock):
        # Two dispensers with different recipe orders (sequential groups)
        mock_disp1 = _mock_dispenser(1)
        mock_disp2 = _mock_dispenser(2)
        mock_disp1.dispense.return_value = 10.0
        mock_disp2.dispense.return_value = 10.0
        mock_disp1.needs_exclusive = False
        mock_disp2.needs_exclusive = False

        items = [
            PreparationItem(dispenser=mock_disp1, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=1),
            PreparationItem(dispenser=mock_disp2, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=2),
        ]

        scheduler = DispenserScheduler(max_concurrent=2)
        scheduler.run(items, lambda _p: None, lambda: False)

        # Verify max_time estimation: 1.0s + 1.0s for two sequential groups
        groups = _group_by_recipe_order(items)
        assert estimate_total_time(groups, 2) == pytest.approx(2.0)
        # Both dispensers should have been called
        mock_disp1.dispense.assert_called_once()
        mock_disp2.dispense.assert_called_once()
        # Both should be marked done
        assert items[0].done is True
        assert items[1].done is True

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_scheduler_first_progress_is_zero_before_carriage_move(self, _mock_sleep: MagicMock):
        """First on_progress emit is 0% and fires before the carriage moves.

        Regression: with carriage enabled, the initial 0% must appear before
        ``_carriage.move_to(...)`` so the UI refreshes immediately rather than
        waiting for the (potentially seconds-long) move to the first position.
        """
        mock_carriage = MagicMock()
        mock_carriage.wait_after_dispense = 0.0
        mock_carriage.home_position = 0
        mock_disp = _mock_dispenser(1, carriage_position=50)
        mock_disp.needs_exclusive = False
        mock_disp.dispense.return_value = 10.0

        events: list[str] = []
        mock_carriage.move_to.side_effect = lambda *_: events.append("move")

        def on_progress(progress: int) -> None:
            events.append(f"progress={progress}")

        items = [PreparationItem(dispenser=mock_disp, amount_ml=10, pump_speed=100, estimated_time=1.0)]
        DispenserScheduler(max_concurrent=1, carriage=mock_carriage).run(items, on_progress, lambda: False)

        assert events[0] == "progress=0"
        assert events.index("progress=0") < events.index("move")


class TestCarriageOrdering:
    def test_order_ascending_from_home_zero(self):
        items = [
            PreparationItem(
                dispenser=_mock_dispenser(1, carriage_position=50), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(2, carriage_position=10), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(3, carriage_position=80), amount_ml=10, pump_speed=100, estimated_time=1
            ),
        ]
        result = _order_by_carriage_position(items, home_position=0)
        positions = [x.dispenser.carriage_position for x in result]
        assert positions == [10, 50, 80]

    def test_order_descending_from_home_100(self):
        # On a 1D line with return-to-home, ascending and descending always
        # have equal total travel. The tiebreaker (<=) picks ascending.
        items = [
            PreparationItem(
                dispenser=_mock_dispenser(1, carriage_position=10), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(2, carriage_position=70), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(3, carriage_position=90), amount_ml=10, pump_speed=100, estimated_time=1
            ),
        ]
        result = _order_by_carriage_position(items, home_position=100)
        positions = [x.dispenser.carriage_position for x in result]
        assert positions == [10, 70, 90]

    def test_order_from_middle_home(self):
        # Home at 50, items at 10, 40, 60, 90
        # Ascending travel: |10-50| + |40-10| + |60-40| + |90-60| + |90-50| = 40+30+20+30+40 = 160
        # Descending travel: |90-50| + |60-90| + |40-60| + |10-40| + |10-50| = 40+30+20+30+40 = 160
        # Tie → ascending wins (<=)
        items = [
            PreparationItem(
                dispenser=_mock_dispenser(1, carriage_position=60), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(2, carriage_position=10), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(3, carriage_position=90), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(4, carriage_position=40), amount_ml=10, pump_speed=100, estimated_time=1
            ),
        ]
        result = _order_by_carriage_position(items, home_position=50)
        positions = [x.dispenser.carriage_position for x in result]
        assert positions == [10, 40, 60, 90]

    def test_order_empty(self):
        assert _order_by_carriage_position([], home_position=0) == []

    def test_total_travel(self):
        items = [
            PreparationItem(
                dispenser=_mock_dispenser(1, carriage_position=10), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(2, carriage_position=50), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(3, carriage_position=80), amount_ml=10, pump_speed=100, estimated_time=1
            ),
        ]
        # home(0) -> 10 -> 50 -> 80 -> home(0) = 10 + 40 + 30 + 80 = 160
        assert _total_travel(items, home_position=0) == 160

    def test_total_travel_with_float_home(self):
        items = [
            PreparationItem(
                dispenser=_mock_dispenser(1, carriage_position=10), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(2, carriage_position=50), amount_ml=10, pump_speed=100, estimated_time=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(3, carriage_position=80), amount_ml=10, pump_speed=100, estimated_time=1
            ),
        ]
        # home(12.5) -> 10 -> 50 -> 80 -> home(12.5) = 2.5 + 40 + 30 + 67.5 = 140
        assert _total_travel(items, home_position=12.5) == pytest.approx(140.0)

    def testestimate_carriage_time(self):
        mock_carriage = MagicMock()
        mock_carriage.travel_time.return_value = 0.0
        mock_carriage.wait_after_dispense = 0.0
        items1 = [
            PreparationItem(
                dispenser=_mock_dispenser(1), amount_ml=10, pump_speed=100, estimated_time=5.0, recipe_order=1
            ),
            PreparationItem(
                dispenser=_mock_dispenser(2), amount_ml=10, pump_speed=100, estimated_time=3.0, recipe_order=1
            ),
        ]
        items2 = [
            PreparationItem(
                dispenser=_mock_dispenser(3), amount_ml=10, pump_speed=100, estimated_time=2.0, recipe_order=2
            ),
        ]
        assert estimate_carriage_time([items1, items2], mock_carriage, home_position=0) == pytest.approx(10.0)

    def testestimate_carriage_time_with_travel(self):
        mock_carriage = MagicMock()
        mock_carriage.wait_after_dispense = 0.0
        # travel_time returns |to - from| / 10 (simulating speed_pct_per_s=10)
        mock_carriage.travel_time.side_effect = lambda f, t: abs(t - f) / 10.0
        items = [
            PreparationItem(
                dispenser=_mock_dispenser(1, carriage_position=20),
                amount_ml=10,
                pump_speed=100,
                estimated_time=1.0,
                recipe_order=1,
            ),
            PreparationItem(
                dispenser=_mock_dispenser(2, carriage_position=60),
                amount_ml=10,
                pump_speed=100,
                estimated_time=1.0,
                recipe_order=1,
            ),
        ]
        # home(0)->20: 2.0s travel + 1.0s dispense + 20->60: 4.0s travel + 1.0s dispense + 60->0: 6.0s travel
        result = estimate_carriage_time([items], mock_carriage, home_position=0)
        assert result == pytest.approx(14.0)


class TestCarriageScheduler:
    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_scheduler_carriage_all_sequential(self, mock_sleep: MagicMock):
        """When carriage is active, all items run sequentially even if they could be parallel."""
        mock_carriage = MagicMock()
        mock_carriage.travel_time.return_value = 0.0
        mock_carriage.wait_after_dispense = 0.0
        mock_carriage.home_position = 0
        mock_disp1 = _mock_dispenser(1, carriage_position=20)
        mock_disp2 = _mock_dispenser(2, carriage_position=60)
        mock_disp1.dispense.return_value = 10.0
        mock_disp2.dispense.return_value = 10.0
        mock_disp1.needs_exclusive = False
        mock_disp2.needs_exclusive = False

        items = [
            PreparationItem(dispenser=mock_disp1, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=1),
            PreparationItem(dispenser=mock_disp2, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=1),
        ]

        scheduler = DispenserScheduler(max_concurrent=2, carriage=mock_carriage)
        scheduler.run(items, lambda _p: None, lambda: False)

        # Sequential: 1.0 + 1.0 = 2.0
        groups = _group_by_recipe_order(items)
        assert estimate_carriage_time(groups, mock_carriage, mock_carriage.home_position) == pytest.approx(2.0)
        # Carriage should move to each position then home
        assert mock_carriage.move_to.call_count == 2
        mock_carriage.home.assert_called_once()
        # Both dispensers called
        mock_disp1.dispense.assert_called_once()
        mock_disp2.dispense.assert_called_once()

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_scheduler_carriage_orders_by_position(self, mock_sleep: MagicMock):
        """Carriage scheduler reorders items by position to minimize travel."""
        mock_carriage = MagicMock()
        mock_carriage.travel_time.return_value = 0.0
        mock_carriage.wait_after_dispense = 0.0
        mock_carriage.home_position = 0
        mock_disp1 = _mock_dispenser(1, carriage_position=80)
        mock_disp2 = _mock_dispenser(2, carriage_position=20)
        mock_disp1.dispense.return_value = 10.0
        mock_disp2.dispense.return_value = 10.0
        mock_disp1.needs_exclusive = False
        mock_disp2.needs_exclusive = False

        items = [
            PreparationItem(dispenser=mock_disp1, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=1),
            PreparationItem(dispenser=mock_disp2, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=1),
        ]

        scheduler = DispenserScheduler(max_concurrent=2, carriage=mock_carriage)
        scheduler.run(items, lambda _p: None, lambda: False)

        # Should move to position 20 first (closer to home=0), then 80
        move_calls = [call.args[0] for call in mock_carriage.move_to.call_args_list]
        assert move_calls == [20, 80]

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_scheduler_no_carriage_unchanged(self, mock_sleep: MagicMock):
        """Without carriage, scheduler behavior is unchanged (parallel)."""
        mock_disp1 = _mock_dispenser(1)
        mock_disp2 = _mock_dispenser(2)
        mock_disp1.dispense.return_value = 10.0
        mock_disp2.dispense.return_value = 10.0
        mock_disp1.needs_exclusive = False
        mock_disp2.needs_exclusive = False

        items = [
            PreparationItem(dispenser=mock_disp1, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=1),
            PreparationItem(dispenser=mock_disp2, amount_ml=10, pump_speed=100, estimated_time=1.0, recipe_order=1),
        ]

        scheduler = DispenserScheduler(max_concurrent=2)
        scheduler.run(items, lambda _p: None, lambda: False)

        # Parallel: max(1.0, 1.0) = 1.0
        groups = _group_by_recipe_order(items)
        assert estimate_total_time(groups, 2) == pytest.approx(1.0)
        mock_disp1.dispense.assert_called_once()
        mock_disp2.dispense.assert_called_once()


class TestCleaningScheduler:
    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_cleaning_runs_each_dispenser(self, _mock_sleep: MagicMock):
        """Each dispenser is invoked with the sentinel amount and stopped after duration."""
        mock_disp1 = _mock_dispenser(1)
        mock_disp2 = _mock_dispenser(2)
        items = [
            CleaningItem(dispenser=mock_disp1, duration_seconds=0.0),
            CleaningItem(dispenser=mock_disp2, duration_seconds=0.0),
        ]

        CleaningScheduler(max_concurrent=2).run(items, lambda _p: None, lambda: False)

        mock_disp1.dispense.assert_called_once()
        mock_disp2.dispense.assert_called_once()
        # First positional arg passed to dispense is the sentinel amount.
        assert mock_disp1.dispense.call_args.args[0] == _CLEANING_LARGE_AMOUNT
        mock_disp1.stop.assert_called()
        mock_disp2.stop.assert_called()

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_cleaning_carriage_orders_by_position(self, _mock_sleep: MagicMock):
        """Carriage cleaning reorders items by position to minimize travel."""
        mock_carriage = MagicMock()
        mock_carriage.wait_after_dispense = 0.0
        mock_carriage.home_position = 0
        mock_disp1 = _mock_dispenser(1, carriage_position=80)
        mock_disp2 = _mock_dispenser(2, carriage_position=20)
        items = [
            CleaningItem(dispenser=mock_disp1, duration_seconds=0.0),
            CleaningItem(dispenser=mock_disp2, duration_seconds=0.0),
        ]

        CleaningScheduler(max_concurrent=1, carriage=mock_carriage).run(items, lambda _p: None, lambda: False)

        move_calls = [call.args[0] for call in mock_carriage.move_to.call_args_list]
        assert move_calls == [20, 80]
        mock_carriage.home.assert_called_once()

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_cleaning_progress_increases(self, _mock_sleep: MagicMock):
        """Progress values are monotone non-decreasing and finish at 100."""
        items = [
            CleaningItem(dispenser=_mock_dispenser(1), duration_seconds=0.0),
            CleaningItem(dispenser=_mock_dispenser(2), duration_seconds=0.0),
        ]
        seen: list[int] = []

        CleaningScheduler(max_concurrent=1).run(items, seen.append, lambda: False)

        assert seen, "progress should have been emitted at least once"
        assert seen == sorted(seen)
        assert seen[0] == 0
        assert seen[-1] == 100

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_cleaning_first_progress_is_zero_before_carriage_move(self, _mock_sleep: MagicMock):
        """First on_progress emit is 0% and fires before the carriage moves."""
        mock_carriage = MagicMock()
        mock_carriage.wait_after_dispense = 0.0
        mock_carriage.home_position = 0
        items = [CleaningItem(dispenser=_mock_dispenser(1, carriage_position=20), duration_seconds=0.0)]

        events: list[str] = []
        mock_carriage.move_to.side_effect = lambda *_: events.append("move")

        def on_progress(progress: int) -> None:
            events.append(f"progress={progress}")

        CleaningScheduler(max_concurrent=1, carriage=mock_carriage).run(items, on_progress, lambda: False)

        assert events[0] == "progress=0"
        assert events.index("progress=0") < events.index("move")

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_cleaning_cancellation_stops_dispensers(self, _mock_sleep: MagicMock):
        """When is_cancelled returns True mid-run, stop() is called on the active batch."""
        mock_disp1 = _mock_dispenser(1)
        mock_disp2 = _mock_dispenser(2)
        items = [
            CleaningItem(dispenser=mock_disp1, duration_seconds=10.0),
            CleaningItem(dispenser=mock_disp2, duration_seconds=10.0),
        ]
        # Cancel after the first poll so the timed loop exits and triggers stop.
        cancel_calls = iter([False, True, True, True, True])
        CleaningScheduler(max_concurrent=2).run(items, lambda _p: None, lambda: next(cancel_calls, True))

        mock_disp1.stop.assert_called()
        mock_disp2.stop.assert_called()

    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_base_carriage_sequence_call_order(self, mock_sleep: MagicMock):
        """BaseScheduler._run_carriage_sequence preserves move → on_each → sleep order."""
        mock_carriage = MagicMock()
        mock_carriage.wait_after_dispense = 0.5
        mock_carriage.home_position = 0
        disp = _mock_dispenser(1, carriage_position=30)
        item = CleaningItem(dispenser=disp, duration_seconds=0.0)
        scheduler = BaseScheduler(max_concurrent=1, carriage=mock_carriage)

        events: list[str] = []
        mock_carriage.move_to.side_effect = lambda *_: events.append("move")
        mock_sleep.side_effect = lambda *_: events.append("sleep")

        def on_each(_item: CleaningItem, _idx: int, _total: int) -> None:
            events.append("on_each")

        scheduler._run_carriage_sequence([item], on_each=on_each, is_cancelled=lambda: False)  # ty:ignore[invalid-argument-type]

        assert events == ["move", "on_each", "sleep"]
