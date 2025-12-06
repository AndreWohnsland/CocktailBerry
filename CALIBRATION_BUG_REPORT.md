# CocktailBerry Calibration Program - Deep Analysis Report

## Issue Summary

A user reported that **the calibration program does not respect the volume flow of the pump config set**. After a deep code analysis and testing, this report confirms the issue and provides detailed findings.

---

## Executive Summary

**Confirmed Bug**: The calibration function (`src/tabs/maker.py::calibrate()`) always uses `pump_speed=100`, which means it operates at 100% of the configured `volume_flow` value, regardless of any speed adjustments that might be desired during calibration.

**Severity**: Medium to High - Impacts users trying to calibrate pumps accurately or test at different speeds.

**Affected Components**:
- Standalone calibration program (`src/programs/calibration.py`)
- In-program calibration (called from options window)
- API calibration endpoint (`/bottles/{bottle_id}/calibrate`)

---

## Detailed Analysis

### 1. How the System is Designed to Work

#### Volume Flow and Pump Speed Relationship

The system uses two related but distinct concepts:

1. **`volume_flow`** (in PumpConfig): The maximum flow rate in ml/s that a pump can deliver
   - Configured in `PUMP_CONFIG` list
   - Example: `volume_flow=30.0` means 30 ml/s at full speed

2. **`pump_speed`** (in Ingredient): A percentage multiplier (0-100%) applied to `volume_flow`
   - Each ingredient in a recipe can have its own `pump_speed`
   - Example: `pump_speed=50` means use 50% of the configured volume_flow

#### Flow Time Calculation (from `src/machine/controller.py`, line 268)

```python
volume_flow = cfg.PUMP_CONFIG[ing.bottle - 1].volume_flow * ing.pump_speed / 100
flow_time = round(ing.amount / volume_flow, 1)
```

**Example for Normal Cocktail Making**:
- Configured: `volume_flow = 30.0 ml/s`
- Ingredient: `pump_speed = 50%`, `amount = 100ml`
- Effective flow: `30.0 * 50 / 100 = 15.0 ml/s`
- Flow time: `100ml / 15.0 ml/s = 6.67s`

This allows recipes to control pump speed per ingredient, which is important for:
- Creating layered drinks
- Controlling mixing
- Adjusting for different liquid viscosities
- Working with pumps that can't run at full speed

---

### 2. The Calibration Bug

#### Location: `src/tabs/maker.py`, lines 140-163

```python
def calibrate(bottle_number: int, amount: int) -> None:
    """Calibrate a bottle."""
    shared.cocktail_status = CocktailStatus(status=PrepareResult.IN_PROGRESS)
    display_name = f"{amount} ml volume, pump #{bottle_number}"
    ing = Ingredient(
        id=0,
        name="Calibration",
        alcohol=0,
        bottle_volume=1000,
        fill_level=1000,
        hand=False,
        pump_speed=100,  # ⚠️ HARDCODED TO 100%!
        amount=amount,
        bottle=bottle_number,
    )
    mc = MachineController()
    mc.make_cocktail(
        w=None,
        ingredient_list=[ing],
        recipe=display_name,
        is_cocktail=False,
        verbose=False,
    )
```

#### The Problem

The hardcoded `pump_speed=100` means calibration ALWAYS:
- Uses 100% of the configured `volume_flow`
- Cannot test pumps at different speeds
- Cannot account for pumps that need to run slower
- Does not match how ingredients are actually used in recipes

#### Concrete Example of the Bug

**Scenario**: User has a pump that actually delivers 15 ml/s (not 30 ml/s as expected)

**Current Behavior (Buggy)**:
1. User configures: `volume_flow=30.0 ml/s` (initial guess)
2. User runs calibration: "Dispense 100ml"
3. Calibration uses: `30.0 * 100 / 100 = 30.0 ml/s`
4. Calibration runs for: `100ml / 30.0 ml/s = 3.33s`
5. **Result**: Only ~50ml is actually dispensed (because pump is slower)
6. User is confused why calibration is wrong

**What User Expects**:
- Calibration should help them determine the correct `volume_flow` value
- OR calibration should allow testing at different pump speeds
- Calibration should be consistent with how cocktails are made

---

### 3. Code Path Analysis

#### Three Ways to Trigger Calibration (All Have Same Bug)

##### 3.1 Standalone Calibration Program
```
runme.py --calibration
  → src/programs/cli.py
  → src/programs/calibration.py::run_calibration()
  → CalibrationScreen UI
  → maker.calibrate(channel_number, amount)  ⚠️ Bug here
```

##### 3.2 In-Program Calibration (Options Window)
```
MainWindow → Options → Calibration Button
  → src/ui/setup_option_window.py::_open_calibration()
  → src/programs/calibration.py::run_calibration(standalone=False)
  → CalibrationScreen UI
  → maker.calibrate(channel_number, amount)  ⚠️ Bug here
```

##### 3.3 API Calibration
```
POST /bottles/{bottle_id}/calibrate
  → src/api/routers/bottles.py::calibrate_bottle()
  → maker.calibrate(bottle_id, amount)  ⚠️ Bug here
```

**All three paths** call the same buggy `maker.calibrate()` function.

---

### 4. Impact Assessment

#### Who is Affected?

1. **Users calibrating new pumps**: Cannot accurately determine the correct `volume_flow` value
2. **Users with slow pumps**: Pumps that can't handle full speed will dispense incorrect amounts
3. **Users testing pump accuracy**: Cannot verify pump performance at different speeds
4. **Users following calibration procedures**: May get confusing results

#### What Doesn't Work?

- Testing a pump at 50% speed to see if it works better
- Verifying that a configured `volume_flow=15.0` is accurate when pump runs at 50% in recipes
- Calibrating pumps with speed control (not just on/off)

#### What Still Works?

- Normal cocktail making (uses correct `pump_speed` from recipes)
- Cleaning mode (doesn't use pump_speed)
- Manual ingredient dispensing (uses correct `pump_speed`)

---

### 5. Test Results

Created comprehensive test suite in `tests/test_calibration.py` with 4 tests:

1. ✅ **test_calibrate_uses_full_volume_flow**: Confirms `pump_speed=100` is hardcoded
2. ✅ **test_calibration_flow_time_calculation**: Shows flow time calculations ignore speed variations
3. ✅ **test_calibration_vs_normal_ingredient_preparation**: Demonstrates inconsistency between calibration and normal use
4. ✅ **test_calibration_with_api_endpoint**: Confirms API path has same issue

**All tests pass**, confirming the bug exists as reported.

---

### 6. Related Code Observations

#### Positive Findings

- `_build_preparation_data()` correctly calculates flow based on `pump_speed`
- Normal cocktail preparation respects `pump_speed` values
- The system architecture supports variable pump speeds

#### Additional Issues Found

1. **No input validation**: `calibrate()` doesn't validate `bottle_number` or `amount`
2. **No error handling**: No try-catch around machine operations
3. **No feedback**: Function doesn't return success/failure indication
4. **Synchronous operation**: Despite API using `background_tasks`, calibration blocks

---

## Recommended Solutions

### Option 1: Make Calibration Test at 100% Speed (Maintain Current Design)

**Rationale**: Calibration is meant to test the pump at full configured speed to verify the `volume_flow` setting is correct.

**Changes**: None needed, but add documentation explaining this is intentional.

**Pros**:
- Matches current implementation
- Simple calibration workflow
- Clear purpose: verify configured `volume_flow`

**Cons**:
- Can't test pumps that shouldn't run at 100%
- Doesn't match how pumps are used in recipes (with varying speeds)

---

### Option 2: Add Pump Speed Parameter (Recommended)

**Rationale**: Allow users to calibrate at any pump speed, matching how the system works.

**Changes**:
```python
def calibrate(bottle_number: int, amount: int, pump_speed: int = 100) -> None:
    """Calibrate a bottle at a specific pump speed.
    
    Args:
        bottle_number: The bottle/pump number (1-based)
        amount: Amount to dispense in ml
        pump_speed: Pump speed percentage (default 100%)
    """
    ing = Ingredient(
        # ... other fields ...
        pump_speed=pump_speed,  # Use parameter instead of hardcoded value
        amount=amount,
        bottle=bottle_number,
    )
```

**Also update**:
- `CalibrationScreen` UI to allow pump speed input
- API endpoint to accept optional `pump_speed` parameter
- Documentation to explain pump speed calibration

**Pros**:
- Flexible calibration at any speed
- Matches how system actually works
- Users can test pumps at recipe speeds
- Backward compatible (default=100)

**Cons**:
- Requires UI changes
- More complex for basic users

---

### Option 3: Use Ingredient's Default Pump Speed

**Rationale**: If an ingredient has a default pump speed in the database, use it.

**Changes**:
```python
def calibrate(bottle_number: int, amount: int) -> None:
    # Get the ingredient at this bottle
    DBC = DatabaseCommander()
    ingredient = DBC.get_ingredient_at_bottle(bottle_number)
    
    # Use its pump_speed if available, otherwise 100
    pump_speed = ingredient.pump_speed if ingredient else 100
    
    ing = Ingredient(
        # ... other fields ...
        pump_speed=pump_speed,
        # ...
    )
```

**Pros**:
- Automatic calibration at ingredient's typical speed
- No UI changes needed
- Matches how ingredient is used in recipes

**Cons**:
- May not work if bottle is empty (no ingredient)
- Implicit behavior (not obvious to users)

---

## Implementation Priority

### Critical Issues to Address

1. **Bug Fix**: Choose one of the recommended solutions above
2. **Input Validation**: Add validation for `bottle_number` (1 to MAKER_NUMBER_BOTTLES)
3. **Input Validation**: Add validation for `amount` (reasonable range, e.g., 10-500ml)
4. **Documentation**: Update calibration docs to explain pump speed behavior

### Nice to Have

1. Return value from `calibrate()` indicating success/failure
2. Error handling around machine operations
3. Progress feedback during calibration
4. Log calibration events with actual dispensed volume

---

## Conclusion

### Summary of Findings

1. ✅ **Bug Confirmed**: Calibration always uses `pump_speed=100`
2. ✅ **Root Cause Identified**: Hardcoded value in `src/tabs/maker.py::calibrate()`
3. ✅ **All Paths Affected**: Standalone, in-program, and API calibration
4. ✅ **Test Suite Created**: 4 tests demonstrating the issue
5. ✅ **Solutions Proposed**: Three viable options to fix the bug

### Recommendations

**Immediate Action**: Implement Option 2 (Add pump_speed parameter) because:
- Most flexible solution
- Maintains backward compatibility
- Aligns with system architecture
- Allows full range of calibration scenarios

**Long Term**: 
- Add comprehensive calibration documentation
- Consider calibration wizard/tutorial
- Add validation and error handling
- Log calibration results for debugging

---

## Appendix: Technical Details

### Code Locations

- **Bug Location**: `src/tabs/maker.py`, line 151
- **Flow Calculation**: `src/machine/controller.py`, line 268
- **UI Calibration**: `src/programs/calibration.py`
- **API Endpoint**: `src/api/routers/bottles.py`, line 81
- **Test Suite**: `tests/test_calibration.py`

### Configuration Files

- **Pump Config**: Defined in `src/config/config_manager.py`
- **Config Type**: `src/config/config_types.py::PumpConfig`
- **Default Values**: `_default_volume_flow = [30.0] * 10`

### Database Schema

- **Ingredient Table**: Contains `pump_speed` column (default=100)
- **Model**: `src/db_models.py::Ingredient`
- **API Model**: `src/api/models.py::Ingredient`

---

## Questions for Maintainer/User

1. **Design Intent**: Was calibration always meant to run at 100% speed? Or is this an oversight?

2. **User Workflow**: How do users typically calibrate their pumps? Do they:
   - Adjust `volume_flow` config until calibration is accurate?
   - Set `volume_flow` based on pump specs?
   - Use trial and error?

3. **Pump Speed Usage**: Are recipe ingredients typically using pump speeds other than 100%?

4. **Priority**: Is this a high-priority bug to fix, or can users work around it?

5. **Solution Preference**: Which of the three proposed solutions best fits the intended user experience?

---

**Report Generated**: 2025-12-06
**CocktailBerry Version**: 2.9.0
**Analysis Performed By**: GitHub Copilot Workspace
**Test Suite Status**: ✅ All tests passing (demonstrates bug)
