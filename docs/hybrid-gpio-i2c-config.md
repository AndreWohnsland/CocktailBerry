# Hybrid GPIO/I2C Controller Configuration

## Overview

The CocktailBerry system now supports hybrid GPIO and I2C-based pin control, allowing you to use GPIO pins (for Raspberry Pi and generic boards) alongside I2C GPIO expanders (MCP23017 and PCF8574) for controlling relays and pumps.

## Supported Pin Types

- **GPIO**: Traditional GPIO pins on Raspberry Pi or generic boards using `python-periphery`
- **MCP23017**: 16-pin I2C GPIO expander
- **PCF8574**: 8-pin I2C GPIO expander

## Configuration

### PumpConfig Structure

Each pump in `PUMP_CONFIG` now supports the following fields:

```yaml
PUMP_CONFIG:
  - pin: 14              # GPIO pin number OR I2C expander pin number (0-indexed)
    volume_flow: 30.0    # Flow rate in ml/s
    tube_volume: 0       # Volume in tube for calibration (ml)
    pin_type: GPIO       # Pin type: "GPIO", "MCP23017", or "PCF8574"
    i2c_address: 0x20    # I2C address (only required for I2C pin types)
```

### GPIO Configuration Example

For traditional GPIO pins (default behavior):

```yaml
PUMP_CONFIG:
  - pin: 14
    volume_flow: 30.0
    tube_volume: 0
    pin_type: GPIO
```

The `pin_type` and `i2c_address` fields are optional and default to GPIO operation.

### MCP23017 Configuration Example

For MCP23017 I2C expander (16 pins, numbered 0-15):

```yaml
PUMP_CONFIG:
  - pin: 0               # First relay on MCP23017
    volume_flow: 30.0
    tube_volume: 0
    pin_type: MCP23017
    i2c_address: 0x20
  - pin: 1               # Second relay on MCP23017
    volume_flow: 30.0
    tube_volume: 0
    pin_type: MCP23017
    i2c_address: 0x20
```

### PCF8574 Configuration Example

For PCF8574 I2C expander (8 pins, numbered 0-7):

```yaml
PUMP_CONFIG:
  - pin: 0               # First relay on PCF8574
    volume_flow: 30.0
    tube_volume: 0
    pin_type: PCF8574
    i2c_address: 0x21
  - pin: 1               # Second relay on PCF8574
    volume_flow: 30.0
    tube_volume: 0
    pin_type: PCF8574
    i2c_address: 0x21
```

### Mixed Configuration Example

You can mix GPIO and I2C pins in the same configuration:

```yaml
PUMP_CONFIG:
  # GPIO pins
  - pin: 14
    volume_flow: 30.0
    tube_volume: 0
    pin_type: GPIO
  
  - pin: 15
    volume_flow: 30.0
    tube_volume: 0
    pin_type: GPIO
  
  # MCP23017 pins at address 0x20
  - pin: 0
    volume_flow: 30.0
    tube_volume: 0
    pin_type: MCP23017
    i2c_address: 0x20
  
  - pin: 1
    volume_flow: 30.0
    tube_volume: 0
    pin_type: MCP23017
    i2c_address: 0x20
  
  # PCF8574 pins at address 0x21
  - pin: 0
    volume_flow: 30.0
    tube_volume: 0
    pin_type: PCF8574
    i2c_address: 0x21
```

## I2C Addressing

### Default Addresses

- **MCP23017**: 0x20 (can be configured from 0x20 to 0x27)
- **PCF8574**: 0x20 (can be configured from 0x20 to 0x27)
- **PCF8574A**: 0x38 (can be configured from 0x38 to 0x3F)

### Multiple Devices

You can use multiple I2C expanders by configuring different I2C addresses:

```yaml
PUMP_CONFIG:
  # First MCP23017 at 0x20
  - pin: 0
    pin_type: MCP23017
    i2c_address: 0x20
    volume_flow: 30.0
    tube_volume: 0
  
  # Second MCP23017 at 0x21
  - pin: 0
    pin_type: MCP23017
    i2c_address: 0x21
    volume_flow: 30.0
    tube_volume: 0
  
  # PCF8574 at 0x22
  - pin: 0
    pin_type: PCF8574
    i2c_address: 0x22
    volume_flow: 30.0
    tube_volume: 0
```

## Hardware Setup

### I2C Bus on Raspberry Pi

1. Enable I2C:
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options > I2C > Enable
   ```

2. Verify I2C devices are detected:
   ```bash
   sudo i2cdetect -y 1
   ```
   
   This will show a grid with detected I2C addresses.

### Wiring

#### MCP23017 Wiring
- VDD: 3.3V or 5V
- VSS: Ground
- SCL: I2C Clock (GPIO 3 on Raspberry Pi)
- SDA: I2C Data (GPIO 2 on Raspberry Pi)
- A0-A2: Address pins (configure I2C address)
- GPA0-GPA7, GPB0-GPB7: GPIO pins (connect to relay modules)

#### PCF8574 Wiring
- VDD: 5V
- VSS: Ground
- SCL: I2C Clock (GPIO 3 on Raspberry Pi)
- SDA: I2C Data (GPIO 2 on Raspberry Pi)
- A0-A2: Address pins (configure I2C address)
- P0-P7: GPIO pins (connect to relay modules)

## Migration Guide

### Migrating from GPIO-Only Configuration

If you have an existing configuration using GPIO pins, your configuration will continue to work without changes. The system defaults to GPIO mode.

To migrate to I2C expanders:

1. **Backup your configuration**:
   ```bash
   cp custom_config.yaml custom_config.yaml.backup
   ```

2. **Update pump configurations** for pins you want to move to I2C:
   ```yaml
   # Before (GPIO):
   - pin: 14
     volume_flow: 30.0
     tube_volume: 0
   
   # After (I2C):
   - pin: 0               # New relay position on expander
     volume_flow: 30.0
     tube_volume: 0
     pin_type: MCP23017   # or PCF8574
     i2c_address: 0x20
   ```

3. **Test your configuration** with a small number of pumps first.

## Troubleshooting

### I2C Device Not Detected

If your I2C device is not detected:

1. Check wiring connections
2. Verify I2C is enabled: `sudo raspi-config`
3. Check for device: `sudo i2cdetect -y 1`
4. Check logs: Look for I2C initialization messages in the CocktailBerry logs

### Pin Not Working

If a pin doesn't activate:

1. Verify the `pin` number is within range:
   - GPIO: Valid Raspberry Pi GPIO pin number
   - MCP23017: 0-15
   - PCF8574: 0-7
2. Check the `i2c_address` matches your hardware configuration
3. Verify relay module is powered and connected correctly
4. Check logs for error messages

### Inverted Logic

If relays are activating when they should be off (or vice versa):

- Use the `MAKER_PINS_INVERTED` setting to invert all pins globally
- The inversion applies to both GPIO and I2C pins

## Dependencies

The following Python packages are required for I2C support (automatically installed on Linux):

- `adafruit-circuitpython-mcp230xx>=2.5.13`
- `adafruit-circuitpython-pcf8574>=1.0.4`

These are automatically installed when you install CocktailBerry on Linux systems.

## Performance Considerations

- **GPIO**: Direct hardware access, fastest response time
- **I2C**: Slightly slower than GPIO due to I2C bus communication, but still more than adequate for relay control
- Multiple I2C devices on the same bus are managed efficiently
- I2C bus supports simultaneous control of all devices

## Safety Notes

1. **Always power off** before making wiring changes
2. **Use proper isolation** when controlling high-voltage relays
3. **Test with low-power loads** before connecting to pumps
4. **Verify relay orientation** (normally open vs normally closed)
5. **Use appropriate current ratings** for your relay modules

## Support

For issues or questions:
- GitHub Issues: https://github.com/AndreWohnsland/CocktailBerry/issues
- Documentation: https://cocktailberry.readthedocs.io
