#!/usr/bin/env python3
"""Demo script to demonstrate UnionType LED configuration."""

import json
from src.config.config_manager import CONFIG
from src.config.config_types import NormalLedConfig, WsLedConfig


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_current_config() -> None:
    """Demonstrate getting current LED config."""
    print_section("Current LED Configuration")
    
    config = CONFIG.get_config()
    led_config = config.get("LED_CONFIG", [])
    
    print(f"\nNumber of LED configurations: {len(led_config)}")
    for i, led in enumerate(led_config, 1):
        print(f"\nLED Config #{i}:")
        print(json.dumps(led, indent=2))


def demo_ui_metadata() -> None:
    """Demonstrate UI metadata for LED config."""
    print_section("UI Metadata for LED Configuration")
    
    config = CONFIG.get_config_with_ui_information()
    led_config_meta = config.get("LED_CONFIG", {})
    
    print(f"\nType Field: {led_config_meta.get('type_field')}")
    print(f"\nDescription: {led_config_meta.get('description')}")
    print(f"\nImmutable: {led_config_meta.get('immutable')}")
    
    variants = led_config_meta.get("variants", {})
    print(f"\nAvailable Variants: {list(variants.keys())}")
    
    for variant_name, variant_fields in variants.items():
        print(f"\n{variant_name.upper()} Fields:")
        for field_name in variant_fields.keys():
            print(f"  - {field_name}")


def demo_set_normal_led() -> None:
    """Demonstrate setting normal LED configuration."""
    print_section("Setting Normal LED Configuration")
    
    new_config = {
        "LED_CONFIG": [
            {"type": "normal", "pins": [14, 15, 18, 23]}
        ]
    }
    
    print("\nSetting config:")
    print(json.dumps(new_config, indent=2))
    
    CONFIG.set_config(new_config, validate=True)
    
    print("\nVerifying...")
    assert len(CONFIG.LED_CONFIG) == 1
    assert isinstance(CONFIG.LED_CONFIG[0], NormalLedConfig)
    assert CONFIG.LED_CONFIG[0].pins == [14, 15, 18, 23]
    print("✓ Successfully set normal LED config")


def demo_set_ws_led() -> None:
    """Demonstrate setting WS281x LED configuration."""
    print_section("Setting WS281x LED Configuration")
    
    new_config = {
        "LED_CONFIG": [
            {
                "type": "ws281x",
                "pin": 18,
                "count": 30,
                "brightness": 150,
                "number_rings": 2
            }
        ]
    }
    
    print("\nSetting config:")
    print(json.dumps(new_config, indent=2))
    
    CONFIG.set_config(new_config, validate=True)
    
    print("\nVerifying...")
    assert len(CONFIG.LED_CONFIG) == 1
    assert isinstance(CONFIG.LED_CONFIG[0], WsLedConfig)
    assert CONFIG.LED_CONFIG[0].pin == 18
    assert CONFIG.LED_CONFIG[0].count == 30
    assert CONFIG.LED_CONFIG[0].brightness == 150
    print("✓ Successfully set WS281x LED config")


def demo_set_mixed_led() -> None:
    """Demonstrate setting mixed LED configuration."""
    print_section("Setting Mixed LED Configuration")
    
    new_config = {
        "LED_CONFIG": [
            {
                "type": "ws281x",
                "pin": 18,
                "count": 24,
                "brightness": 100,
                "number_rings": 1
            },
            {
                "type": "normal",
                "pins": [14, 15]
            },
            {
                "type": "ws281x",
                "pin": 12,
                "count": 60,
                "brightness": 200,
                "number_rings": 1
            }
        ]
    }
    
    print("\nSetting config:")
    print(json.dumps(new_config, indent=2))
    
    CONFIG.set_config(new_config, validate=True)
    
    print("\nVerifying...")
    assert len(CONFIG.LED_CONFIG) == 3
    assert isinstance(CONFIG.LED_CONFIG[0], WsLedConfig)
    assert isinstance(CONFIG.LED_CONFIG[1], NormalLedConfig)
    assert isinstance(CONFIG.LED_CONFIG[2], WsLedConfig)
    print("✓ Successfully set mixed LED config")
    
    print("\nLED configs:")
    for i, led in enumerate(CONFIG.LED_CONFIG, 1):
        if isinstance(led, WsLedConfig):
            print(f"  #{i}: WS281x LED - Pin {led.pin}, {led.count} LEDs, {led.brightness} brightness")
        else:
            print(f"  #{i}: Normal LED - Pins {led.pins}")


def demo_validation_error() -> None:
    """Demonstrate validation error handling."""
    print_section("Validation Error Handling")
    
    invalid_configs = [
        {
            "name": "Invalid type",
            "config": {"LED_CONFIG": [{"type": "invalid", "pins": [14]}]}
        },
        {
            "name": "Missing required field",
            "config": {"LED_CONFIG": [{"type": "ws281x", "pin": 18}]}  # missing count, brightness, etc.
        },
        {
            "name": "Out of range value",
            "config": {"LED_CONFIG": [{"type": "ws281x", "pin": 300, "count": 24, "brightness": 100, "number_rings": 1}]}
        }
    ]
    
    from src.config.errors import ConfigError
    
    for test in invalid_configs:
        print(f"\nTesting: {test['name']}")
        try:
            CONFIG.set_config(test['config'], validate=True)
            print("  ✗ Should have raised ConfigError!")
        except ConfigError as e:
            print(f"  ✓ Correctly rejected: {str(e)[:60]}...")


def main() -> None:
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  UnionType LED Configuration Demo")
    print("=" * 60)
    
    # Save original config
    original_config = CONFIG.LED_CONFIG
    
    try:
        demo_current_config()
        demo_ui_metadata()
        demo_set_normal_led()
        demo_set_ws_led()
        demo_set_mixed_led()
        demo_validation_error()
        
        print("\n" + "=" * 60)
        print("  All demonstrations completed successfully! ✓")
        print("=" * 60 + "\n")
        
    finally:
        # Restore original config
        CONFIG.LED_CONFIG = original_config


if __name__ == "__main__":
    main()
