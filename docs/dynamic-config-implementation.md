# Dynamic Config Class Implementation

## Overview

This implementation adds a new `DynamicConfigType` to the CocktailBerry configuration system. This allows a single configuration option to dynamically change its schema based on a discriminator field (type selector).

## Key Features

- **Type Discriminator**: A special field (e.g., `led_type`) determines which schema variant to use
- **Multiple Schemas**: Each discriminator value maps to a different set of fields and validation rules
- **Dynamic UI**: Both PyQt and React UIs automatically show/hide fields based on the selected type
- **Validation**: Each schema variant has its own validation rules
- **Migration**: Automatically migrates legacy LED_* configs to the new LED_CONFIG structure

## Architecture

### Core Classes

#### `DynamicConfigType`
Located in `src/config/config_types.py`

A configuration type that supports multiple schemas based on a discriminator field.

```python
DynamicConfigType(
    discriminator_field="led_type",  # Field that determines the type
    type_mapping={
        "normal": DictType(schema_dict, NormalLedConfig),
        "ws281x": DictType(schema_dict, WS281xLedConfig),
    }
)
```

**Key Methods**:
- `validate()`: Validates config dict using the appropriate DictType
- `from_config()`: Deserializes dict to the appropriate ConfigClass
- `to_config()`: Serializes ConfigClass to dict
- `get_discriminator_options()`: Returns list of valid type values
- `get_schema_for_type()`: Returns schema for a specific type

#### `NormalLedConfig`
ConfigClass for normal (non-controllable) LEDs

**Fields**:
- `led_type`: "normal"
- `pins`: List of GPIO pins
- `brightness`: LED brightness (1-255)
- `default_on`: Whether LEDs are on by default
- `preparation_state`: State during cocktail preparation

#### `WS281xLedConfig`
ConfigClass for WS281x controllable LEDs

**Fields**:
- `led_type`: "ws281x"
- `pins`: List of GPIO pins
- `brightness`: LED brightness (1-255)
- `count`: Number of LEDs in the strip
- `number_rings`: Number of LED rings
- `default_on`: Whether LEDs are on by default
- `preparation_state`: State during cocktail preparation

### Configuration Manager

The `LED_CONFIG` replaces the individual `LED_*` configuration options:

**Old Structure**:
```yaml
LED_PINS: [18]
LED_BRIGHTNESS: 100
LED_COUNT: 24
LED_NUMBER_RINGS: 1
LED_DEFAULT_ON: false
LED_PREPARATION_STATE: Effect
LED_IS_WS: true
```

**New Structure**:
```yaml
LED_CONFIG:
  - led_type: ws281x
    pins: [18]
    brightness: 100
    count: 24
    number_rings: 1
    default_on: false
    preparation_state: Effect
```

### Migration

Legacy configurations are automatically migrated on first load:

1. Check if `LED_CONFIG` exists in loaded config file
2. If not, check if any legacy LED_* values are non-default
3. Create appropriate LED config (normal or ws281x) based on `LED_IS_WS`
4. Add to `LED_CONFIG` list

## UI Implementation

### PyQt UI

Located in `src/ui/create_config_window.py`

**Key Method**: `_build_dynamic_config_field()`

1. Creates a type selector dropdown
2. Builds input fields for all type variants
3. Shows/hides fields based on selected type
4. Uses signals to handle type changes dynamically

**User Experience**:
- User sees a "Type" dropdown with available options
- When type changes, fields automatically update
- Only relevant fields for selected type are shown

### React UI

Located in `web_client/src/components/options/ConfigWindow.tsx`

**Key Methods**:
- `renderDynamicConfigField()`: Renders the dynamic config component
- `renderDynamicFieldInput()`: Renders individual fields based on schema

1. Detects dynamic configs by checking for `discriminator_field`
2. Renders type selector dropdown
3. Dynamically renders fields based on selected type
4. Handles type changes by rebuilding object with new schema defaults

**User Experience**:
- User sees a "Type" dropdown
- Fields update automatically when type changes
- Default values are provided for new type selection

## API Integration

### GET /api/options

Returns config with UI information including:

```json
{
  "LED_CONFIG": {
    "value": [
      {
        "led_type": "ws281x",
        "pins": [],
        "brightness": 100,
        "count": 24,
        "number_rings": 1,
        "default_on": false,
        "preparation_state": "Effect"
      }
    ],
    "discriminator_field": "led_type",
    "type_options": ["normal", "ws281x"],
    "type_schemas": {
      "normal": { /* schema */ },
      "ws281x": { /* schema */ }
    }
  }
}
```

### POST /api/options

Accepts LED_CONFIG in request body:

```json
{
  "LED_CONFIG": [
    {
      "led_type": "normal",
      "pins": [14, 15],
      "brightness": 150,
      "default_on": true,
      "preparation_state": "On"
    }
  ]
}
```

## Testing

### Unit Tests

Located in `tests/config/test_dynamic_config_type.py`

- Tests for NormalLedConfig class
- Tests for WS281xLedConfig class
- Tests for DynamicConfigType validation
- Tests for serialization/deserialization
- Tests for schema retrieval

### Integration Tests

Located in `tests/config/test_led_config_integration.py`

- Tests for ConfigManager with LED_CONFIG
- Tests for get/set config
- Tests for UI information generation
- Tests for legacy migration
- Tests for multiple LED configs

### All Tests
- **130 tests passing** (98 existing + 32 new)

## Usage Examples

### Creating a Normal LED Config

```python
from src.config.config_types import NormalLedConfig

led = NormalLedConfig(
    led_type="normal",
    pins=[14, 15],
    brightness=150,
    default_on=True,
    preparation_state="On"
)
```

### Creating a WS281x LED Config

```python
from src.config.config_types import WS281xLedConfig

led = WS281xLedConfig(
    led_type="ws281x",
    pins=[18],
    brightness=200,
    count=50,
    number_rings=2,
    default_on=False,
    preparation_state="Effect"
)
```

### Setting LED Config

```python
from src.config.config_manager import CONFIG

new_config = {
    "LED_CONFIG": [
        {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 200,
            "count": 50,
            "number_rings": 2,
            "default_on": False,
            "preparation_state": "Effect"
        }
    ]
}

CONFIG.set_config(new_config, validate=True)
CONFIG.sync_config_to_file()
```

### Multiple LED Configurations

```python
new_config = {
    "LED_CONFIG": [
        {
            "led_type": "normal",
            "pins": [14],
            "brightness": 100,
            "default_on": False,
            "preparation_state": "On"
        },
        {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 150,
            "count": 30,
            "number_rings": 1,
            "default_on": True,
            "preparation_state": "Effect"
        }
    ]
}

CONFIG.set_config(new_config, validate=True)
```

## Extending to Other Config Types

The `DynamicConfigType` can be used for any configuration that needs type variants:

```python
# Example: Different pump types
DynamicConfigType(
    discriminator_field="pump_type",
    type_mapping={
        "peristaltic": DictType(
            {
                "pump_type": ChooseType(allowed=["peristaltic", "gear"]),
                "pin": IntType(),
                "volume_flow": FloatType(),
                "tube_volume": IntType(),
            },
            PeristalticPumpConfig,
        ),
        "gear": DictType(
            {
                "pump_type": ChooseType(allowed=["peristaltic", "gear"]),
                "pin": IntType(),
                "rpm": IntType(),
                "displacement": FloatType(),
            },
            GearPumpConfig,
        ),
    },
)
```

## Backward Compatibility

- Legacy LED_* configs are kept in ConfigManager for backward compatibility
- Automatic migration on first load ensures smooth transition
- Old configs in custom_config.yaml are preserved but not used if LED_CONFIG exists
- PyQt and React UIs only show LED_CONFIG, hiding legacy options

## Future Improvements

1. **UI Enhancements**:
   - Add visual indicators for type-specific fields
   - Improve field layout in dynamic configs
   - Add tooltips explaining field differences

2. **Migration Tools**:
   - Add admin endpoint to force migration
   - Add validation tool to check config integrity
   - Add export/import for configs

3. **Documentation**:
   - Add inline help text for each LED type
   - Create video tutorials
   - Add more examples to docs

4. **Type System**:
   - Support nested dynamic configs
   - Add conditional field visibility
   - Support computed default values

## Performance Considerations

- Schema validation occurs on config load/save
- UI type switching is instantaneous (no API calls)
- Config serialization is efficient (direct dict conversion)
- No performance impact on non-dynamic configs

## Security Considerations

- All input is validated against schemas
- Invalid discriminator values are rejected
- Missing required fields trigger validation errors
- Type coercion is handled safely

## Conclusion

The DynamicConfigType implementation provides a flexible, type-safe way to handle configurations with multiple variants. It maintains backward compatibility while providing a better user experience and cleaner code structure.
