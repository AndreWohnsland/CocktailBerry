"""Tests for calibration functionality to demonstrate and verify the volume flow bug."""
from unittest.mock import MagicMock, patch

import pytest

from src.config.config_manager import CONFIG
from src.config.config_types import PumpConfig
from src.machine.controller import _build_preparation_data
from src.models import Ingredient
from src.tabs import maker


class TestCalibration:
    """Test calibration functionality."""

    def test_calibrate_uses_full_volume_flow(self):
        """Test that calibration currently uses 100% pump speed (demonstrating the bug).
        
        This test documents the current behavior where calibration always uses 100% pump speed,
        regardless of any pump speed adjustments that might be needed.
        """
        # Save original config
        original_pump_config = CONFIG.PUMP_CONFIG.copy()
        original_maker_number_bottles = CONFIG.MAKER_NUMBER_BOTTLES

        try:
            # Set up test pump configuration
            CONFIG.PUMP_CONFIG = [  # type: ignore
                PumpConfig(pin=1, volume_flow=30.0, tube_volume=0),  # 30 ml/s configured
                PumpConfig(pin=2, volume_flow=20.0, tube_volume=0),
            ]
            CONFIG.MAKER_NUMBER_BOTTLES = 2

            # Mock the MachineController to intercept the make_cocktail call
            with patch('src.tabs.maker.MachineController') as mock_mc_class:
                mock_mc = MagicMock()
                mock_mc_class.return_value = mock_mc
                mock_mc.make_cocktail.return_value = ([100], 3.33, 3.33)

                # Call calibrate function
                maker.calibrate(bottle_number=1, amount=100)

                # Verify make_cocktail was called
                mock_mc.make_cocktail.assert_called_once()
                
                # Extract the ingredient list passed to make_cocktail
                call_args = mock_mc.make_cocktail.call_args
                ingredient_list = call_args[1]['ingredient_list']
                
                assert len(ingredient_list) == 1
                ingredient = ingredient_list[0]
                
                # THE BUG: Calibration always uses pump_speed=100
                assert ingredient.pump_speed == 100, "Calibration uses hardcoded 100% pump speed"
                assert ingredient.amount == 100
                assert ingredient.bottle == 1
                
        finally:
            # Restore original configuration
            CONFIG.PUMP_CONFIG = original_pump_config  # type: ignore
            CONFIG.MAKER_NUMBER_BOTTLES = original_maker_number_bottles

    def test_calibration_flow_time_calculation(self):
        """Test that flow time calculation in calibration doesn't respect pump speed variations.
        
        This test demonstrates that if a user wants to calibrate at a different pump speed
        (e.g., 50% because the actual pump is slower), the current implementation doesn't support it.
        """
        # Save original config
        original_pump_config = CONFIG.PUMP_CONFIG.copy()
        original_maker_number_bottles = CONFIG.MAKER_NUMBER_BOTTLES

        try:
            # Set up test configuration
            # User has configured volume_flow=30.0 ml/s
            CONFIG.PUMP_CONFIG = [  # type: ignore
                PumpConfig(pin=1, volume_flow=30.0, tube_volume=0),
            ]
            CONFIG.MAKER_NUMBER_BOTTLES = 1

            # Mock MachineController
            with patch('src.tabs.maker.MachineController') as mock_mc_class:
                mock_mc = MagicMock()
                mock_mc_class.return_value = mock_mc
                
                # Capture what ingredient is created
                def capture_ingredient(*args, **kwargs):
                    ingredient_list = kwargs['ingredient_list']
                    # Build preparation data to see what flow_time would be calculated
                    prep_data = _build_preparation_data(ingredient_list)
                    return ([100], prep_data[0].flow_time, prep_data[0].flow_time)
                
                mock_mc.make_cocktail.side_effect = capture_ingredient

                # Call calibrate
                maker.calibrate(bottle_number=1, amount=100)
                
                # Extract the ingredient
                call_args = mock_mc.make_cocktail.call_args
                ingredient_list = call_args[1]['ingredient_list']
                
                # Calculate what the preparation data would be
                prep_data = _build_preparation_data(ingredient_list)
                
                # With pump_speed=100 and volume_flow=30.0:
                # effective_flow = 30.0 * 100 / 100 = 30.0 ml/s
                # flow_time = 100ml / 30.0 ml/s = 3.33s
                assert prep_data[0].volume_flow == pytest.approx(30.0)
                assert prep_data[0].flow_time == pytest.approx(3.33, rel=0.01)
                
                # If the user wanted to calibrate at 50% pump speed (because their pump
                # actually delivers 15 ml/s, not 30), they CANNOT do it with current implementation
                # The flow time would need to be 100ml / 15 ml/s = 6.67s
                # But current implementation always calculates: 100ml / 30 ml/s = 3.33s
                
        finally:
            # Restore original configuration
            CONFIG.PUMP_CONFIG = original_pump_config  # type: ignore
            CONFIG.MAKER_NUMBER_BOTTLES = original_maker_number_bottles

    def test_calibration_vs_normal_ingredient_preparation(self):
        """Compare calibration preparation with normal ingredient preparation.
        
        This test shows the difference between how calibration works vs how
        normal ingredient preparation works, highlighting the inconsistency.
        """
        # Save original config
        original_pump_config = CONFIG.PUMP_CONFIG.copy()
        original_maker_number_bottles = CONFIG.MAKER_NUMBER_BOTTLES

        try:
            CONFIG.PUMP_CONFIG = [  # type: ignore
                PumpConfig(pin=1, volume_flow=30.0, tube_volume=0),
            ]
            CONFIG.MAKER_NUMBER_BOTTLES = 1

            # Create a normal ingredient with 50% pump speed (as might be in a recipe)
            normal_ingredient = Ingredient(
                id=1,
                name="Test Ingredient",
                alcohol=0,
                bottle_volume=1000,
                fill_level=500,
                hand=False,
                pump_speed=50,  # 50% speed
                amount=100,
                bottle=1,
            )
            
            # Build preparation data for normal ingredient
            normal_prep_data = _build_preparation_data([normal_ingredient])
            
            # The normal ingredient respects pump_speed:
            # effective_flow = 30.0 * 50 / 100 = 15.0 ml/s
            # flow_time = 100ml / 15.0 ml/s = 6.67s
            assert normal_prep_data[0].volume_flow == pytest.approx(15.0)
            assert normal_prep_data[0].flow_time == pytest.approx(6.67, rel=0.01)

            # Now create an ingredient as calibration does
            with patch('src.tabs.maker.MachineController') as mock_mc_class:
                mock_mc = MagicMock()
                mock_mc_class.return_value = mock_mc
                mock_mc.make_cocktail.return_value = ([100], 3.33, 3.33)

                maker.calibrate(bottle_number=1, amount=100)
                
                call_args = mock_mc.make_cocktail.call_args
                calib_ingredient_list = call_args[1]['ingredient_list']
                
                # Build preparation data for calibration ingredient
                calib_prep_data = _build_preparation_data(calib_ingredient_list)
                
                # Calibration does NOT respect pump_speed adjustments:
                # effective_flow = 30.0 * 100 / 100 = 30.0 ml/s (always 100%)
                # flow_time = 100ml / 30.0 ml/s = 3.33s
                assert calib_prep_data[0].volume_flow == pytest.approx(30.0)
                assert calib_prep_data[0].flow_time == pytest.approx(3.33, rel=0.01)
                
                # THE ISSUE: Calibration flow_time (3.33s) != Normal ingredient flow_time (6.67s)
                # for the SAME amount (100ml) from the SAME bottle!
                # This is because calibration ignores pump_speed variations.
                assert calib_prep_data[0].flow_time != normal_prep_data[0].flow_time
                
        finally:
            CONFIG.PUMP_CONFIG = original_pump_config  # type: ignore
            CONFIG.MAKER_NUMBER_BOTTLES = original_maker_number_bottles

    def test_calibration_with_api_endpoint(self):
        """Test that API calibration endpoint has the same issue.
        
        The API endpoint at POST /bottles/{bottle_id}/calibrate calls maker.calibrate()
        which has the same hardcoded pump_speed=100 issue.
        """
        # Save original config
        original_pump_config = CONFIG.PUMP_CONFIG.copy()
        original_maker_number_bottles = CONFIG.MAKER_NUMBER_BOTTLES

        try:
            CONFIG.PUMP_CONFIG = [  # type: ignore
                PumpConfig(pin=1, volume_flow=30.0, tube_volume=0),
            ]
            CONFIG.MAKER_NUMBER_BOTTLES = 1

            with patch('src.tabs.maker.MachineController') as mock_mc_class:
                mock_mc = MagicMock()
                mock_mc_class.return_value = mock_mc
                mock_mc.make_cocktail.return_value = ([100], 3.33, 3.33)

                # Simulate what API endpoint does: maker.calibrate(bottle_id, amount)
                bottle_id = 1
                amount = 100
                maker.calibrate(bottle_id, amount)
                
                # Verify the issue exists in API path too
                call_args = mock_mc.make_cocktail.call_args
                ingredient_list = call_args[1]['ingredient_list']
                
                assert len(ingredient_list) == 1
                assert ingredient_list[0].pump_speed == 100  # Hardcoded 100%
                
        finally:
            CONFIG.PUMP_CONFIG = original_pump_config  # type: ignore
            CONFIG.MAKER_NUMBER_BOTTLES = original_maker_number_bottles
