from unittest.mock import ANY, MagicMock, patch

import pytest

from src.config.config_manager import CONFIG
from src.config.config_types import PumpConfig
from src.machine.controller import MachineController, _build_preparation_data, _PreparationData
from src.models import Ingredient


class TestController:
    def test_build_preparation_data(self):
        original_pump_config = CONFIG.PUMP_CONFIG.copy()
        original_maker_number_bottles = CONFIG.MAKER_NUMBER_BOTTLES

        try:
            CONFIG.PUMP_CONFIG = [  # type: ignore
                PumpConfig(pin=1, volume_flow=10.0, tube_volume=0),
                PumpConfig(pin=2, volume_flow=20.0, tube_volume=0),
            ]
            CONFIG.MAKER_NUMBER_BOTTLES = 2

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

            prep_data = _build_preparation_data(ingredients)

            # Verify results
            assert len(prep_data) == 2
            assert prep_data[0].pin == 1
            assert prep_data[0].volume_flow == pytest.approx(10.0)
            assert prep_data[0].flow_time == pytest.approx(10.0)  # 100ml / 10ml/s
            assert prep_data[0].recipe_order == 1

            assert prep_data[1].pin == 2
            assert prep_data[1].volume_flow == pytest.approx(10.0)  # 20.0 * 0.5 (pump_speed 50%)
            assert prep_data[1].flow_time == pytest.approx(20.0)  # 200ml / 10ml/s
            assert prep_data[1].recipe_order == 2

        finally:
            # Restore original configuration
            CONFIG.PUMP_CONFIG = original_pump_config  # type: ignore
            CONFIG.MAKER_NUMBER_BOTTLES = original_maker_number_bottles

    def test_chunk_preparation_data(self):
        # Set original value to restore later
        original_simultaneous_pumps = CONFIG.MAKER_SIMULTANEOUSLY_PUMPS

        try:
            # Set test configuration
            CONFIG.MAKER_SIMULTANEOUSLY_PUMPS = 2

            # Create test data
            prep_data = [
                _PreparationData(pin=1, volume_flow=10, flow_time=5, recipe_order=1),
                _PreparationData(pin=2, volume_flow=10, flow_time=5, recipe_order=1),
                _PreparationData(pin=3, volume_flow=10, flow_time=5, recipe_order=1),
                _PreparationData(pin=4, volume_flow=10, flow_time=5, recipe_order=2),
            ]

            mc = MachineController()
            chunks = mc._chunk_preparation_data(prep_data)

            # Should split first three into two chunks (2+1), and one chunk for order=2
            assert len(chunks) == 3
            assert [len(chunk) for chunk in chunks] == [2, 1, 1]
            assert chunks[0][0].recipe_order == 1
            assert chunks[1][0].recipe_order == 1
            assert chunks[2][0].recipe_order == 2

        finally:
            # Restore original configuration
            CONFIG.MAKER_SIMULTANEOUSLY_PUMPS = original_simultaneous_pumps

    def test_process_preparation_section(self):
        # Create test section data
        section = [
            _PreparationData(pin=1, volume_flow=10, flow_time=5),
            _PreparationData(pin=2, volume_flow=20, flow_time=3),
        ]

        mc = MachineController()
        # Mock only the internal _stop_pumps method
        mc._stop_pumps = MagicMock()

        # First call: section_time < all flow_times
        mc._process_preparation_section(0, 10, section, section_time=2)
        assert section[0].consumption == 20  # 10 ml/s * 2s
        assert section[1].consumption == 40  # 20 ml/s * 2s
        assert not section[0].closed
        assert not section[1].closed
        mc._stop_pumps.assert_not_called()

        # Second call: section_time > flow_time for pin=2
        mc._process_preparation_section(0, 10, section, section_time=4)
        assert section[0].consumption == 40  # 10 ml/s * 4s
        assert section[1].closed
        mc._stop_pumps.assert_called_once_with([2], ANY)

        # Third call: section_time > flow_time for pin=1
        mc._process_preparation_section(0, 10, section, section_time=6)
        assert section[0].closed
        assert mc._stop_pumps.call_count == 2
        mc._stop_pumps.assert_any_call([1], ANY)

    @patch("time.perf_counter")
    def test_start_preparation(self, mock_time: MagicMock):
        # Mock time to simulate passage of time during preparation
        # First call is for cocktail_start_time, then section_start_time, then repeatedly in the while loop
        mock_time.side_effect = [
            0.0,  # cocktail_start_time
            0.0,  # First section_start_time
            1.0,  # Time checks during first preparation
            1.0,  # Second section_start_time
            2.0,  # Time checks during second preparation
        ]

        # Create test data with two ingredients with different recipe orders
        prep_data = [
            _PreparationData(pin=1, volume_flow=10, flow_time=1.0, recipe_order=1),
            _PreparationData(pin=2, volume_flow=10, flow_time=1.0, recipe_order=2),
        ]

        mc = MachineController()
        mc._start_pumps = MagicMock()
        mc._stop_pumps = MagicMock()
        mc._process_preparation_section = MagicMock()
        mc._consumption_print = MagicMock()

        # Call the method under test (w is None as requested)
        current_time, max_time = mc._start_preparation(None, prep_data, True)

        # Verify the method worked correctly
        assert max_time == pytest.approx(2.0)  # 1.0s + 1.0s for the two ingredients
        assert current_time == pytest.approx(2.0)  # Last time value from our mock

        # Verify _start_pumps was called for both chunks with correct pins
        assert mc._start_pumps.call_count == 2
        mc._start_pumps.assert_any_call([1], ANY)  # First ingredient
        mc._start_pumps.assert_any_call([2], ANY)  # Second ingredient

        # Verify _stop_pumps was called for both chunks with correct pins
        assert mc._stop_pumps.call_count == 2
        mc._stop_pumps.assert_any_call([1], ANY)  # First ingredient
        mc._stop_pumps.assert_any_call([2], ANY)  # Second ingredient

        # Verify _process_preparation_section was called multiple times for each chunk
        assert mc._process_preparation_section.call_count >= 2

        # Verify calls were in the right sequence (first processing ingredient 1, then ingredient 2)
        first_call = mc._process_preparation_section.call_args_list[0]
        assert first_call[0][2] == [prep_data[0]]  # First call with first ingredient

        # Find first call with second ingredient
        second_ingredient_calls = [
            call for call in mc._process_preparation_section.call_args_list if call[0][2] == [prep_data[1]]
        ]
        assert len(second_ingredient_calls) > 0  # Should have at least one call with second ingredient
