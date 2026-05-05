from unittest.mock import MagicMock, patch

import pytest

from src.config.config_manager import CONFIG
from src.config.config_types import PumpConfig
from src.machine.controller import MachineController
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.scheduler import (
    DispenserScheduler,
    PreparationItem,
    _estimate_carriage_time,
    _estimate_group_time,
    _group_by_recipe_order,
    _order_by_carriage_position,
    _run_dispenser,
    _total_travel,
)
from src.models import Ingredient


def _mock_dispenser(slot: int, volume_flow: float = 10.0, carriage_position: int = 0) -> MagicMock:
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
                PumpConfig(pin=1, volume_flow=10.0, tube_volume=0),
                PumpConfig(pin=2, volume_flow=20.0, tube_volume=0),
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

    def test_run_dispenser(self):
        mock_disp = _mock_dispenser(1)
        mock_disp.dispense.return_value = 100.0

        data = PreparationItem(
            dispenser=mock_disp,
            amount_ml=100,
            pump_speed=100,
            estimated_time=10,
        )

        result = _run_dispenser(data)

        assert result == pytest.approx(100.0)
        assert data.consumption == pytest.approx(100.0)
        assert data.done is True
        mock_disp.dispense.assert_called_once()
        call_args = mock_disp.dispense.call_args
        assert call_args[0][0] == 100  # amount_ml
        assert call_args[0][1] == 100  # pump_speed

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
        _current_time, max_time = scheduler.run(items, lambda p, c: None, lambda: False)

        # Verify max_time estimation: 1.0s + 1.0s for two sequential groups
        assert max_time == pytest.approx(2.0)
        # Both dispensers should have been called
        mock_disp1.dispense.assert_called_once()
        mock_disp2.dispense.assert_called_once()
        # Both should be marked done
        assert items[0].done is True
        assert items[1].done is True


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

    def test_estimate_carriage_time(self):
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
        assert _estimate_carriage_time([items1, items2], mock_carriage, home_position=0) == pytest.approx(10.0)

    def test_estimate_carriage_time_with_travel(self):
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
        result = _estimate_carriage_time([items], mock_carriage, home_position=0)
        assert result == pytest.approx(14.0)


class TestCarriageScheduler:
    @patch("src.machine.dispensers.scheduler.time.sleep")
    def test_scheduler_carriage_all_sequential(self, mock_sleep: MagicMock):
        """When carriage is active, all items run sequentially even if they could be parallel."""
        mock_carriage = MagicMock()
        mock_carriage.travel_time.return_value = 0.0
        mock_carriage.wait_after_dispense = 0.0
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

        scheduler = DispenserScheduler(max_concurrent=2, carriage=mock_carriage, home_position=0)
        _current_time, max_time = scheduler.run(items, lambda p, c: None, lambda: False)

        # Sequential: 1.0 + 1.0 = 2.0
        assert max_time == pytest.approx(2.0)
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

        scheduler = DispenserScheduler(max_concurrent=2, carriage=mock_carriage, home_position=0)
        scheduler.run(items, lambda p, c: None, lambda: False)

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
        _current_time, max_time = scheduler.run(items, lambda p, c: None, lambda: False)

        # Parallel: max(1.0, 1.0) = 1.0
        assert max_time == pytest.approx(1.0)
        mock_disp1.dispense.assert_called_once()
        mock_disp2.dispense.assert_called_once()
