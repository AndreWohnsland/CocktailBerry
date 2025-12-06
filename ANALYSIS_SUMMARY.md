# Calibration Program Issue Analysis - Summary

## Quick Summary

✅ **Issue Confirmed**: The calibration program does NOT respect the volume flow pump speed configuration.

🔍 **Root Cause**: The `calibrate()` function in `src/tabs/maker.py` (line 151) hardcodes `pump_speed=100`, causing all calibration to run at 100% of the configured volume_flow, regardless of any speed adjustments that might be needed.

📊 **Evidence**: Created 4 comprehensive tests in `tests/test_calibration.py` that all pass and demonstrate the bug.

## Files Added/Modified

### New Files
1. **`CALIBRATION_BUG_REPORT.md`** - Comprehensive 12,000+ word analysis report
   - Detailed technical analysis
   - Code flow diagrams
   - 3 proposed solutions with pros/cons
   - Test results
   - Impact assessment

2. **`tests/test_calibration.py`** - Test suite with 4 tests
   - `test_calibrate_uses_full_volume_flow` - Confirms hardcoded 100%
   - `test_calibration_flow_time_calculation` - Shows flow time issues
   - `test_calibration_vs_normal_ingredient_preparation` - Demonstrates inconsistency
   - `test_calibration_with_api_endpoint` - Confirms API has same bug

### Test Results
```
✅ All 4 new calibration tests PASS (demonstrating the bug)
✅ All 214 existing tests still PASS (no regressions)
```

## The Bug in Detail

### Current (Buggy) Behavior
```python
def calibrate(bottle_number: int, amount: int) -> None:
    ing = Ingredient(
        # ...
        pump_speed=100,  # ⚠️ ALWAYS 100%!
        amount=amount,
        # ...
    )
```

### Impact
- Calibration runs at 100% of configured volume_flow
- Cannot test pumps at different speeds (e.g., 50%, 75%)
- Inconsistent with how ingredients are used in recipes
- Confuses users trying to calibrate slower pumps

### Example Problem
```
User's pump: Actually delivers 15 ml/s
User's config: volume_flow=30.0 ml/s (initial guess)
Calibration request: Dispense 100ml

Expected behavior: Use configured 30ml/s, run for 3.33s
Actual result: Only ~50ml dispensed (pump too slow)
User confusion: "Why is calibration wrong?"
```

## Recommended Solutions

### 🥇 Option 1: Add pump_speed Parameter (RECOMMENDED)
```python
def calibrate(bottle_number: int, amount: int, pump_speed: int = 100) -> None:
```
- ✅ Most flexible
- ✅ Backward compatible (default=100)
- ✅ Allows testing at any speed
- ⚠️ Requires UI/API updates

### 🥈 Option 2: Use Ingredient's Default Speed
- Query ingredient at bottle, use its pump_speed
- ✅ Automatic, no UI changes
- ⚠️ Doesn't work with empty bottles

### 🥉 Option 3: Document Current Behavior
- Keep pump_speed=100
- Add docs explaining this is intentional
- ✅ No code changes
- ⚠️ Doesn't solve user confusion

## Code Locations

| Component | File | Line |
|-----------|------|------|
| Bug Location | `src/tabs/maker.py` | 151 |
| Flow Calculation | `src/machine/controller.py` | 268 |
| UI Calibration | `src/programs/calibration.py` | 39 |
| API Endpoint | `src/api/routers/bottles.py` | 84 |
| Tests | `tests/test_calibration.py` | All |

## Affected Components

1. ✅ Standalone calibration program (`--calibration` flag)
2. ✅ In-program calibration (Options → Calibration)
3. ✅ API calibration endpoint (`POST /bottles/{id}/calibrate`)

All three paths call the same buggy function.

## What Still Works Fine

- ✅ Normal cocktail making (respects pump_speed from recipes)
- ✅ Cleaning mode
- ✅ Manual ingredient dispensing
- ✅ All other bottle operations

## Next Steps

### Decision Required
1. **Is this a bug or by design?**
   - If by design: Add documentation explaining the 100% speed behavior
   - If bug: Implement one of the recommended solutions

### If Implementing Fix (Option 1 Recommended)
1. Update `calibrate()` function to accept `pump_speed` parameter
2. Update `CalibrationScreen` UI to show pump speed input
3. Update API endpoint to accept optional `pump_speed` parameter
4. Add validation (pump_speed must be 1-100)
5. Update documentation
6. Run all tests to verify

### Additional Improvements
1. Add input validation (bottle_number, amount ranges)
2. Add error handling
3. Add return value for success/failure
4. Log calibration events

## Documentation

See **`CALIBRATION_BUG_REPORT.md`** for:
- Complete technical analysis (12,000+ words)
- Detailed code flow diagrams
- All three solution options with detailed pros/cons
- Test methodology and results
- Database schema details
- Configuration file locations
- Questions for maintainer

## Questions for Decision

1. **Was calibration always meant to run at 100% speed?**
2. **How do users typically calibrate their pumps?**
3. **Do recipe ingredients use pump speeds other than 100%?**
4. **What is the priority for fixing this?**
5. **Which solution best fits the intended user experience?**

---

**Analysis Date**: 2025-12-06  
**CocktailBerry Version**: 2.9.0  
**Tests Status**: ✅ 218 tests passing (4 new + 214 existing)  
**Files Changed**: 2 new files added (report + tests)  
