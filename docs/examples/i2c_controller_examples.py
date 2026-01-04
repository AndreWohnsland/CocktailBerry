"""Example: Using I2C Relay Controller with CocktailBerry

This example demonstrates how to control pumps using I2C relay modules.
It shows the configuration and basic usage patterns.
"""

# Example 1: Basic I2C Controller Setup
# ======================================

from src.machine.i2c_board import I2CController

# Create an I2C controller with two PCF8574 devices
# Device 0x20 controls pumps 1-8
# Device 0x21 controls pumps 9-16
controller = I2CController(
    inverted=True,  # Most relay modules are active-low
    i2c_addresses=[0x20, 0x21],  # Two PCF8574 at addresses 0x20 and 0x21
    bus_number=1  # I2C bus 1 on Raspberry Pi
)

# Initialize the pins you'll be using
controller.initialize_pin_list([1, 2, 3, 4, 5, 6, 7, 8])

# Activate pumps 1 and 2
controller.activate_pin_list([1, 2])

# Wait for operation
import time
time.sleep(2)

# Close pump 1, keep pump 2 running
controller.close_pin_list([1])

time.sleep(1)

# Close all pumps
controller.close_pin_list([2])

# Clean up when done
controller.cleanup_pin_list()


# Example 2: Testing Individual Relays
# =====================================

def test_relay(controller, pin_number, duration=1.0):
    """Test a single relay by activating it for a specified duration."""
    print(f"Testing relay {pin_number}...")
    controller.activate_pin_list([pin_number])
    time.sleep(duration)
    controller.close_pin_list([pin_number])
    print(f"Relay {pin_number} test complete")


# Test each pump individually
controller = I2CController(inverted=True, i2c_addresses=[0x20], bus_number=1)
controller.initialize_pin_list(list(range(1, 9)))  # Pins 1-8

for pin in range(1, 9):
    test_relay(controller, pin, duration=0.5)
    time.sleep(0.2)  # Small delay between tests

controller.cleanup_pin_list()


# Example 3: Pattern Testing
# ===========================

def run_pattern(controller, pins, duration=0.5):
    """Run a pattern by activating pins in sequence."""
    for pin in pins:
        controller.activate_pin_list([pin])
        time.sleep(duration)
        controller.close_pin_list([pin])


# Create a wave pattern across all 8 pumps
controller = I2CController(inverted=True, i2c_addresses=[0x20], bus_number=1)
controller.initialize_pin_list(list(range(1, 9)))

print("Running wave pattern...")
for _ in range(3):  # Repeat 3 times
    run_pattern(controller, list(range(1, 9)), duration=0.2)
    run_pattern(controller, list(range(8, 0, -1)), duration=0.2)

controller.cleanup_pin_list()


# Example 4: Parallel Pump Control
# =================================

def make_cocktail_simulation(controller):
    """Simulate making a cocktail with multiple pumps."""
    print("Starting cocktail preparation...")
    
    # Activate pumps 1, 3, and 5
    pumps = [1, 3, 5]
    controller.activate_pin_list(pumps)
    print(f"Pumps {pumps} activated")
    
    time.sleep(1.0)
    
    # Stop pump 1 first
    controller.close_pin_list([1])
    print("Pump 1 stopped")
    
    time.sleep(0.5)
    
    # Stop pump 3
    controller.close_pin_list([3])
    print("Pump 3 stopped")
    
    time.sleep(0.5)
    
    # Stop pump 5
    controller.close_pin_list([5])
    print("Pump 5 stopped")
    
    print("Cocktail complete!")


controller = I2CController(inverted=True, i2c_addresses=[0x20], bus_number=1)
controller.initialize_pin_list([1, 2, 3, 4, 5, 6, 7, 8])
make_cocktail_simulation(controller)
controller.cleanup_pin_list()


# Example 5: State Monitoring
# ============================

def monitor_and_control(controller):
    """Demonstrate state monitoring while controlling pumps."""
    controller.initialize_pin_list([1, 2, 3])
    
    # Activate pump 1
    controller.activate_pin_list([1])
    print(f"Pump 1 active: {controller.read_pin(1)}")  # Should be True
    print(f"Pump 2 active: {controller.read_pin(2)}")  # Should be False
    
    # Activate pump 2 while 1 is still running
    controller.activate_pin_list([2])
    print(f"Pump 1 active: {controller.read_pin(1)}")  # Should be True
    print(f"Pump 2 active: {controller.read_pin(2)}")  # Should be True
    
    # Close pump 1
    controller.close_pin_list([1])
    print(f"Pump 1 active: {controller.read_pin(1)}")  # Should be False
    print(f"Pump 2 active: {controller.read_pin(2)}")  # Should be True
    
    # Close pump 2
    controller.close_pin_list([2])
    controller.cleanup_pin_list()


controller = I2CController(inverted=True, i2c_addresses=[0x20], bus_number=1)
monitor_and_control(controller)


# Example 6: Multiple I2C Devices
# ================================

def test_multiple_devices():
    """Test controlling 16 pumps across two I2C devices."""
    controller = I2CController(
        inverted=True,
        i2c_addresses=[0x20, 0x21],  # Two devices
        bus_number=1
    )
    
    # Initialize all 16 pins
    controller.initialize_pin_list(list(range(1, 17)))
    
    print("Testing first device (pumps 1-8)...")
    for pin in range(1, 9):
        controller.activate_pin_list([pin])
        time.sleep(0.2)
        controller.close_pin_list([pin])
    
    print("Testing second device (pumps 9-16)...")
    for pin in range(9, 17):
        controller.activate_pin_list([pin])
        time.sleep(0.2)
        controller.close_pin_list([pin])
    
    print("Testing cross-device control...")
    # Activate pump 1 from first device and pump 9 from second device
    controller.activate_pin_list([1, 9])
    time.sleep(1.0)
    controller.close_pin_list([1, 9])
    
    controller.cleanup_pin_list()


test_multiple_devices()


# Example 7: Error Handling
# ==========================

def safe_pump_control():
    """Demonstrate safe pump control with error handling."""
    controller = I2CController(inverted=True, i2c_addresses=[0x20], bus_number=1)
    
    try:
        controller.initialize_pin_list([1, 2, 3])
        
        # Control pumps
        controller.activate_pin_list([1, 2])
        time.sleep(2.0)
        controller.close_pin_list([1, 2])
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Always clean up, even if an error occurred
        controller.cleanup_pin_list()
        print("Cleanup complete")


safe_pump_control()


# Example 8: Integration with Existing Config
# ============================================

"""
To integrate with your existing CocktailBerry setup:

1. Add to your config.yaml:

I2C_ENABLE: true
I2C_BUS_NUMBER: 1
I2C_DEVICES:
  - address: 0x20
  - address: 0x21

PUMP_CONFIG:
  - pin: 1
    volume_flow: 30.0
    tube_volume: 0
  - pin: 2
    volume_flow: 30.0
    tube_volume: 0
  # ... continue for all pumps

MAKER_NUMBER_BOTTLES: 8
MAKER_PINS_INVERTED: true

2. The system will automatically use I2CController instead of GPIO

3. No code changes needed - the controller implements the same interface!
"""


# Example 9: Diagnostic Tool
# ===========================

def run_diagnostics():
    """Run diagnostic checks on I2C relay setup."""
    print("I2C Relay Diagnostic Tool")
    print("=" * 40)
    
    controller = I2CController(inverted=True, i2c_addresses=[0x20, 0x21], bus_number=1)
    
    if controller.devenvironment:
        print("ERROR: smbus2 not installed or I2C not available")
        print("Install with: pip install smbus2")
        return
    
    print("✓ smbus2 module available")
    
    try:
        controller.initialize_pin_list([1])
        print("✓ I2C devices initialized successfully")
        print(f"  Addresses: {[hex(addr) for addr in controller.i2c_addresses]}")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return
    
    # Test each relay
    print("\nTesting relays (you should hear clicks):")
    for device_idx, addr in enumerate(controller.i2c_addresses):
        start_pin = device_idx * 8 + 1
        end_pin = start_pin + 8
        print(f"\nDevice {hex(addr)} (pins {start_pin}-{end_pin-1}):")
        
        for pin in range(start_pin, end_pin):
            print(f"  Testing pin {pin}...", end=" ")
            controller.activate_pin_list([pin])
            time.sleep(0.3)
            state = controller.read_pin(pin)
            controller.close_pin_list([pin])
            print("✓" if state else "✗")
            time.sleep(0.1)
    
    controller.cleanup_pin_list()
    print("\nDiagnostics complete!")


# Uncomment to run diagnostics
# run_diagnostics()
