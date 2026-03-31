from unittest.mock import MagicMock, patch

import pytest

from src.config.config_manager import CONFIG
from src.config.config_types import PumpConfig
from src.machine.controller import MachineController
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.scheduler import (
    DispenserScheduler,
    PreparationItem,
    _estimate_group_time,
    _group_by_recipe_order,
    _run_dispenser,
)
from src.models import Ingredient


def _mock_dispenser(slot: int, volume_flow: float = 10.0) -> MagicMock:
    """Create a mock dispenser with working estimated_time."""
    mock = MagicMock(spec=BaseDispenser)
    mock.slot = slot
    mock.volume_flow = volume_flow
    mock.estimated_time.side_effect = lambda amount, pump_speed: amount / (volume_flow * pump_speed / 100)
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
            assert prep_data[0].amount_ml == 100.0
            assert prep_data[0].recipe_order == 1
            assert prep_data[0].ingredient is ingredients[0]

            assert prep_data[1].dispenser is dispensers[2]
            assert prep_data[1].pump_speed == 50
            assert prep_data[1].estimated_time == pytest.approx(20.0)  # 200ml / (20ml/s * 50%)
            assert prep_data[1].amount_ml == 200.0
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

        assert result == 100.0
        assert data.consumption == 100.0
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
