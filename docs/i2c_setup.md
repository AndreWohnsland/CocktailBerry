# I2C Relay Controller Setup Guide

## Overview

CocktailBerry now supports controlling pumps via I2C relay modules instead of direct GPIO pins. This is useful for:
- Reducing GPIO pin usage
- Using relay boards with I2C interfaces (e.g., PCF8574, MCP23017)
- Supporting more pumps with fewer connections
- Better electrical isolation

## Supported Devices

The I2C controller is designed to work with standard I2C relay modules:
- **PCF8574**: 8-bit I/O expander (8 relays per device)
- **MCP23017**: 16-bit I/O expander (16 relays per device, uses 2 addresses)
- Any I2C device that accepts simple byte writes for relay control

## Hardware Setup

### 1. Connect I2C Devices

Connect your I2C relay board(s) to the Raspberry Pi:
- **SDA** → Pin 3 (GPIO 2)
- **SCL** → Pin 5 (GPIO 3)
- **VCC** → 5V or 3.3V (check your module)
- **GND** → Ground

### 2. Enable I2C on Raspberry Pi

```bash
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
sudo reboot
```

### 3. Verify I2C Devices

Check that your devices are detected:
```bash
sudo apt-get install i2c-tools
sudo i2cdetect -y 1
```

You should see your device addresses (e.g., `20`, `21` for addresses 0x20, 0x21).

### 4. Install Required Python Package

```bash
pip install smbus2
```

## Software Configuration

### Configuration File Structure

Add the following to your `config.yaml` file:

```yaml
# Enable I2C relay control
I2C_ENABLE: true

# I2C bus number (usually 1 for Raspberry Pi)
I2C_BUS_NUMBER: 1

# List of I2C device addresses
# Each device controls 8 relays (bits 0-7)
I2C_DEVICES:
  - address: 0x20  # First PCF8574 - controls pumps 1-8
  - address: 0x21  # Second PCF8574 - controls pumps 9-16

# Pin configuration - use logical pin numbers 1-16
# Pump 1 → Bit 0 of device 0x20
# Pump 2 → Bit 1 of device 0x20
# ...
# Pump 8 → Bit 7 of device 0x20
# Pump 9 → Bit 0 of device 0x21
# Pump 10 → Bit 1 of device 0x21
# ...
PUMP_CONFIG:
  - pin: 1          # Maps to bit 0 of first I2C device (0x20)
    volume_flow: 30.0
    tube_volume: 0
  - pin: 2          # Maps to bit 1 of first I2C device (0x20)
    volume_flow: 30.0
    tube_volume: 0
  - pin: 3          # Maps to bit 2 of first I2C device (0x20)
    volume_flow: 30.0
    tube_volume: 0
  # ... continue for all pumps ...
  - pin: 9          # Maps to bit 0 of second I2C device (0x21)
    volume_flow: 30.0
    tube_volume: 0
  - pin: 10         # Maps to bit 1 of second I2C device (0x21)
    volume_flow: 30.0
    tube_volume: 0

# Number of bottles/pumps you have
MAKER_NUMBER_BOTTLES: 8

# Set to true if your relay module is active-low
MAKER_PINS_INVERTED: true
```

## Pin Mapping

The I2C controller uses a simple logical mapping:

| Logical Pin | I2C Device Index | Bit Position | Device Address (example) |
|------------|------------------|--------------|-------------------------|
| 1          | 0                | 0            | 0x20                   |
| 2          | 0                | 1            | 0x20                   |
| ...        | ...              | ...          | ...                    |
| 8          | 0                | 7            | 0x20                   |
| 9          | 1                | 0            | 0x21                   |
| 10         | 1                | 1            | 0x21                   |
| ...        | ...              | ...          | ...                    |
| 16         | 1                | 7            | 0x21                   |

**Formula**: For pin N (1-based):
- Device Index = (N - 1) // 8
- Bit Position = (N - 1) % 8

## Example Configurations

### Single PCF8574 (8 pumps)

```yaml
I2C_ENABLE: true
I2C_BUS_NUMBER: 1
I2C_DEVICES:
  - address: 0x20

MAKER_NUMBER_BOTTLES: 8
PUMP_CONFIG:
  - pin: 1
    volume_flow: 30.0
    tube_volume: 0
  - pin: 2
    volume_flow: 30.0
    tube_volume: 0
  # ... pins 3-8 ...
```

### Two PCF8574 (16 pumps)

```yaml
I2C_ENABLE: true
I2C_BUS_NUMBER: 1
I2C_DEVICES:
  - address: 0x20
  - address: 0x21

MAKER_NUMBER_BOTTLES: 16
PUMP_CONFIG:
  - pin: 1   # Device 0x20, bit 0
    volume_flow: 30.0
    tube_volume: 0
  # ... pins 2-8 (device 0x20) ...
  - pin: 9   # Device 0x21, bit 0
    volume_flow: 30.0
    tube_volume: 0
  # ... pins 10-16 (device 0x21) ...
```

### Mixed Setup (Not Currently Supported)

**Note**: Mixing GPIO and I2C control is not currently supported. You must use either GPIO pins OR I2C control, not both simultaneously.

## Troubleshooting

### I2C devices not detected

```bash
# Check if I2C kernel modules are loaded
lsmod | grep i2c

# Check I2C bus
sudo i2cdetect -y 1

# Enable I2C if not already enabled
sudo raspi-config
```

### Permission errors

```bash
# Add user to i2c group
sudo usermod -a -G i2c $USER
# Log out and log back in, or reboot
```

### Relays not switching

1. Check `MAKER_PINS_INVERTED` setting - many relay modules are active-low
2. Verify I2C addresses match your hardware
3. Check wiring (SDA, SCL, power, ground)
4. Test with `i2cset` command:
   ```bash
   # Turn on all relays (device 0x20, value 0xFF)
   sudo i2cset -y 1 0x20 0xFF
   
   # Turn off all relays (device 0x20, value 0x00)
   sudo i2cset -y 1 0x20 0x00
   ```

### ImportError: smbus2

```bash
pip install smbus2
```

## Technical Details

### Controller Architecture

The I2C controller implements the same `PinController` interface as GPIO controllers, ensuring compatibility with the existing codebase:

```python
class I2CController(PinController):
    def initialize_pin_list(self, pin_list: list[int], ...) -> None
    def activate_pin_list(self, pin_list: list[int]) -> None
    def close_pin_list(self, pin_list: list[int]) -> None
    def cleanup_pin_list(self, pin_list: list[int] | None = None) -> None
    def read_pin(self, pin: int) -> bool
```

### State Management

The controller maintains the current state of each I2C device in memory to support:
- Selective bit control (turn on/off individual relays without affecting others)
- Fast state queries via `read_pin()`
- Proper cleanup on shutdown

### Performance

I2C communication is fast enough for cocktail preparation:
- Single byte write: ~1ms
- Multiple relay control: handled in parallel within same device
- No noticeable delay in pump control

## Migration from GPIO

To migrate an existing GPIO setup to I2C:

1. Install I2C relay board(s)
2. Connect to Raspberry Pi I2C pins
3. Update `config.yaml`:
   - Set `I2C_ENABLE: true`
   - Add `I2C_DEVICES` with your addresses
   - Update `PUMP_CONFIG` pins to use logical numbers 1-N
4. Test with a cleaning cycle first
5. Adjust `MAKER_PINS_INVERTED` if needed

## Limitations

- **No mixed mode**: Cannot use both GPIO and I2C simultaneously
- **Input pins not supported**: I2C controller is output-only for relays
- **Device limit**: Maximum 16 devices (128 relays) per I2C bus
- **Linux only**: Requires I2C kernel support (Raspberry Pi, Linux SBCs)
