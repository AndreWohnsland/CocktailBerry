# Union Type Configuration

## Overview

The `UnionType` configuration class enables polymorphic configuration values that can have different structures based on a discriminator field. This is particularly useful for configurations where different "types" require different sets of parameters.

## Use Case: LED Configuration

The primary use case implemented is the LED configuration, which combines two previously separate configuration approaches into a single, unified system.

### Before (Legacy)
```yaml
LED_PINS: [14, 15, 18]
LED_IS_WS: false
LED_BRIGHTNESS: 100
LED_COUNT: 24
LED_NUMBER_RINGS: 1
```

### After (New)
```yaml
LED_CONFIG:
  - type: normal
    pins: [14, 15, 18]
  
  - type: ws281x
    pin: 18
    count: 24
    brightness: 100
    number_rings: 1
```

## Benefits

1. **Type Safety**: Each variant has its own validation rules
2. **Clarity**: Configuration structure makes it clear what fields apply to each LED type
3. **Flexibility**: Can have multiple LED configurations of different types
4. **Extensibility**: Easy to add new LED types in the future

## Implementation Details

### Config Classes

Two LED config classes are provided:

1. **NormalLedConfig**: For simple on/off LEDs
   - `type`: "normal"
   - `pins`: List of GPIO pins

2. **WsLedConfig**: For WS281x addressable LEDs
   - `type`: "ws281x"
   - `pin`: GPIO pin for data line
   - `count`: Number of LEDs
   - `brightness`: Brightness level (1-255)
   - `number_rings`: Number of LED rings

### UnionType Definition

```python
UnionType[WsLedConfig | NormalLedConfig](
    type_field="type",
    variants={
        "normal": (
            NormalLedConfig,
            {
                "type": StringType(),
                "pins": ListType(IntType([build_number_limiter(0, 200)]), 0),
            },
        ),
        "ws281x": (
            WsLedConfig,
            {
                "type": StringType(),
                "pin": IntType([build_number_limiter(0, 200)]),
                "count": IntType([build_number_limiter(1, 500)]),
                "brightness": IntType([build_number_limiter(1, 255)]),
                "number_rings": IntType([build_number_limiter(1, 10)]),
            },
        ),
    },
)
```

## UI Support

### PyQt UI

The PyQt UI automatically renders UnionType configs with:
- A dropdown selector for the type field
- Dynamic field rendering based on selected type
- Field rebuilding when type changes

### React UI

The React UI renders UnionType configs with:
- A dropdown selector for type selection
- Dynamic field display based on selected type
- Proper TypeScript typing for variant fields

## Adding New Variants

To add a new LED type (e.g., "neopixel"):

1. Create a new config class:
```python
class NeopixelConfig(ConfigClass):
    def __init__(self, led_type: str = "neopixel", pin: int = 10, ...):
        self.type = led_type
        # ... other fields
    
    def to_config(self) -> dict[str, Any]:
        return {"type": self.type, ...}
    
    @classmethod
    def from_config(cls, config: dict) -> NeopixelConfig:
        return cls(led_type=config.get("type", "neopixel"), ...)
```

2. Add to variants in ConfigManager:
```python
"neopixel": (
    NeopixelConfig,
    {
        "type": StringType(),
        # ... field definitions
    },
),
```

3. Update TypeScript types (for React UI):
```typescript
export interface NeopixelConfig {
  type: 'neopixel';
  // ... other fields
}

export type LedConfig = NormalLedConfig | WsLedConfig | NeopixelConfig;
```

## Migration

The legacy LED configuration fields are kept for backward compatibility:
- `LED_PINS`
- `LED_IS_WS`
- `LED_BRIGHTNESS`
- `LED_COUNT`
- `LED_NUMBER_RINGS`

Users can migrate to the new `LED_CONFIG` format at their convenience.

## API Example

### Getting Config
```python
from src.config.config_manager import CONFIG

# Get current LED config
led_configs = CONFIG.LED_CONFIG
for led in led_configs:
    if isinstance(led, WsLedConfig):
        print(f"WS LED on pin {led.pin} with {led.count} LEDs")
    elif isinstance(led, NormalLedConfig):
        print(f"Normal LEDs on pins {led.pins}")
```

### Setting Config
```python
# Set new LED config
CONFIG.set_config({
    "LED_CONFIG": [
        {"type": "ws281x", "pin": 18, "count": 30, "brightness": 150, "number_rings": 1},
        {"type": "normal", "pins": [14, 15]},
    ]
}, validate=True)

# Save to file
CONFIG.sync_config_to_file()
```

## Testing

Comprehensive tests are provided in:
- `tests/test_config_union_type.py`: Core UnionType and LED config tests
- `tests/test_config_api.py`: API endpoint tests

Run tests with:
```bash
pytest tests/test_config_union_type.py tests/test_config_api.py -v
```
