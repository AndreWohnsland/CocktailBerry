# I2C Relay Controller Implementation Summary

## Overview

This document provides a technical summary of the I2C relay controller implementation for CocktailBerry, designed to support controlling pumps via I2C relay modules instead of direct GPIO pins.

## Architecture

### Controller Hierarchy

The implementation follows CocktailBerry's existing controller architecture:

```
PinController (Protocol/Interface)
├── RpiController (Raspberry Pi GPIO)
├── Rpi5Controller (Raspberry Pi 5 GPIO with gpiozero)
├── GenericController (Generic Linux GPIO via python-periphery)
└── I2CController (NEW: I2C relay control via smbus2)
```

All controllers implement the same `PinController` interface, ensuring compatibility and allowing seamless switching between control methods.

### Key Design Decisions

1. **Interface Compliance**: `I2CController` implements the same `PinController` interface as GPIO controllers, requiring no changes to existing code.

2. **Logical Pin Mapping**: Uses 1-based logical pin numbers (pump numbers) that map to I2C device addresses and bit positions:
   - Pin 1-8 → Device 0, bits 0-7
   - Pin 9-16 → Device 1, bits 0-7
   - Formula: `device_index = (pin - 1) // 8`, `bit_position = (pin - 1) % 8`

3. **State Management**: Maintains device state in memory for efficient bit manipulation without read operations.

4. **No Mixed Mode**: System uses either GPIO OR I2C control exclusively, not both simultaneously. This simplifies configuration and avoids conflicts.

5. **Minimal Boilerplate**: Configuration is straightforward with only 3 new config fields needed.

## Implementation Details

### New Files

1. **`src/machine/i2c_board.py`** (221 lines)
   - `I2CController` class implementing `PinController` interface
   - Pin-to-device/bit mapping logic
   - State management for multiple I2C devices
   - Comprehensive error handling with specific exception types

2. **`tests/test_i2c_controller.py`** (257 lines)
   - 15 comprehensive test cases
   - Coverage includes: pin mapping, activation, deactivation, inverted logic, state preservation, cleanup, error handling

3. **`docs/i2c_setup.md`** (236 lines)
   - Complete hardware setup guide
   - Software configuration instructions
   - Pin mapping explanation
   - Example configurations
   - Troubleshooting section

4. **`docs/examples/i2c_controller_examples.py`** (290 lines)
   - 9 practical examples demonstrating usage patterns
   - Includes diagnostic tool for testing I2C relay boards

### Modified Files

1. **`src/config/config_types.py`**
   - Added `I2CConfig` class for I2C device configuration
   - Added to config exports

2. **`src/config/config_manager.py`**
   - Added `I2C_ENABLE` boolean flag
   - Added `I2C_BUS_NUMBER` integer config
   - Added `I2C_DEVICES` list of I2CConfig objects
   - Added validation rules for I2C configuration

3. **`src/machine/controller.py`**
   - Updated `_chose_controller()` to check `I2C_ENABLE` and instantiate `I2CController` when enabled
   - Added import for `I2CController`

## Configuration

### Required Config Changes

Users only need to add 3 new configuration options:

```yaml
# Enable I2C relay control
I2C_ENABLE: true

# I2C bus number (usually 1 for Raspberry Pi)
I2C_BUS_NUMBER: 1

# List of I2C device addresses
I2C_DEVICES:
  - address: 0x20  # First device (pumps 1-8)
  - address: 0x21  # Second device (pumps 9-16)
```

### Pump Configuration

Pumps are configured using logical pin numbers in `PUMP_CONFIG`:

```yaml
PUMP_CONFIG:
  - pin: 1          # Maps to device 0x20, bit 0
    volume_flow: 30.0
    tube_volume: 0
  - pin: 9          # Maps to device 0x21, bit 0
    volume_flow: 30.0
    tube_volume: 0
```

## Key Features

### 1. Multiple Device Support

- Supports up to 16 I2C devices (128 relays) per bus
- Each PCF8574 provides 8 relays
- MCP23017 provides 16 relays (uses 2 addresses)
- Devices operate independently

### 2. State Preservation

- Maintains current state of each I2C device in memory
- Allows selective bit control without affecting other relays
- Fast state queries via `read_pin()` without I2C reads

### 3. Inverted Logic Support

- Supports active-high and active-low relay modules
- Controlled via `MAKER_PINS_INVERTED` config option
- Most relay modules are active-low (inverted=True)

### 4. Error Handling

Specific exception handling for different failure scenarios:
- `FileNotFoundError`: I2C not enabled
- `PermissionError`: User not in i2c group
- `IOError/OSError`: Communication errors
- Individual device cleanup continues even if one fails

### 5. Development Mode

- Gracefully degrades when smbus2 not available
- Logs warnings instead of crashing
- Allows development on non-I2C systems

## Testing

### Test Coverage

15 comprehensive tests covering:
- Pin-to-device/bit mapping (3 tests)
- Initialization and cleanup (3 tests)
- Pin activation and deactivation (4 tests)
- State management (2 tests)
- Inverted logic (2 tests)
- Error handling (1 test)

All tests use mocking to avoid requiring actual I2C hardware.

### Test Results

- ✅ All 15 I2C controller tests pass
- ✅ All 4 existing machine controller tests pass
- ✅ No regressions introduced
- ✅ No security vulnerabilities detected (CodeQL scan)

## Backward Compatibility

The implementation maintains full backward compatibility:

1. **Default Behavior**: GPIO control remains the default when `I2C_ENABLE` is not set or false
2. **No Breaking Changes**: Existing configurations continue to work unchanged
3. **Interface Compliance**: `I2CController` implements the same `PinController` interface
4. **Gradual Migration**: Users can migrate at their own pace

## Performance

### I2C Communication Speed

- Single byte write: ~1ms (typical)
- Multiple relays on same device: Single write operation
- No noticeable delay in cocktail preparation
- State queries are instant (no I2C read required)

### Comparison with GPIO

| Aspect | GPIO | I2C |
|--------|------|-----|
| Setup complexity | Simple | Moderate |
| Pin usage | 1 pin per pump | 2 pins total (SDA/SCL) |
| Max pumps (typical) | ~26 (available GPIO) | 128 (16 devices × 8 bits) |
| Speed | Faster (~μs) | Fast enough (~ms) |
| Electrical isolation | Depends on circuit | Better with relay modules |
| Wiring | More wires | Fewer wires (daisy chain) |

## Limitations

1. **No Mixed Mode**: Cannot use GPIO and I2C simultaneously
2. **Output Only**: I2C controller doesn't support input pins (not needed for pumps)
3. **Linux Only**: Requires I2C kernel support
4. **Bus Limit**: 16 devices maximum per I2C bus (hardware limitation)
5. **Dependency**: Requires smbus2 Python package

## Dependencies

### New Dependency

- **smbus2**: Pure Python I2C library
  - Installation: `pip install smbus2`
  - License: MIT
  - Maintainer: kplindegaard
  - Status: Actively maintained

### System Requirements

- I2C enabled in kernel (Raspberry Pi: `raspi-config`)
- User in `i2c` group for permissions
- I2C relay hardware (PCF8574, MCP23017, etc.)

## Migration Guide

### From GPIO to I2C

1. Install I2C relay board(s)
2. Connect to Raspberry Pi I2C pins
3. Enable I2C: `sudo raspi-config`
4. Install smbus2: `pip install smbus2`
5. Update config.yaml:
   ```yaml
   I2C_ENABLE: true
   I2C_BUS_NUMBER: 1
   I2C_DEVICES:
     - address: 0x20
   PUMP_CONFIG:
     - pin: 1  # Now maps to I2C, not GPIO
       volume_flow: 30.0
       tube_volume: 0
   ```
6. Test with cleaning cycle
7. Adjust `MAKER_PINS_INVERTED` if needed

## Future Enhancements

Possible future improvements (not in scope):

1. **Mixed Mode Support**: Allow GPIO + I2C simultaneously
2. **Input Pin Support**: Support reading from I2C GPIO expanders
3. **MCP23017 Optimization**: Use full 16-bit writes for MCP23017
4. **Auto-detection**: Scan I2C bus and auto-configure devices
5. **Hot-swap**: Support adding/removing I2C devices at runtime
6. **Diagnostic CLI**: Built-in command-line diagnostic tool

## Code Quality

- ✅ All tests passing (100% test success rate)
- ✅ Linting passed (ruff)
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Error handling with specific exceptions
- ✅ No security vulnerabilities (CodeQL)
- ✅ Follows project coding standards

## Documentation

Complete documentation includes:

1. **Setup Guide** (`docs/i2c_setup.md`)
   - Hardware connection instructions
   - Software configuration
   - Pin mapping explanation
   - Troubleshooting guide

2. **Example Code** (`docs/examples/i2c_controller_examples.py`)
   - 9 practical examples
   - Diagnostic tool
   - Integration examples

3. **API Documentation** (inline docstrings)
   - Class and method documentation
   - Parameter descriptions
   - Return value documentation

## Conclusion

This implementation provides a robust, well-tested, and documented solution for I2C relay control in CocktailBerry. It:

- Maintains full backward compatibility
- Requires minimal configuration changes
- Follows existing architectural patterns
- Includes comprehensive testing and documentation
- Provides better error handling and user feedback
- Enables scaling to more pumps with fewer pins

The implementation is production-ready and requires no additional changes to be merged.
