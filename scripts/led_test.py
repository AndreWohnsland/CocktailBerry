#!/usr/bin/env python3
"""WS281x LED test script for CocktailBerry.

Tests the LED strip independently of the CocktailBerry app, using the same SPI driver as CocktailBerry.
The data wire must be connected to GPIO 10 (SPI MOSI, physical pin 19), SPI must be enabled.
Works on every Raspberry Pi, including the Pi 5.

Run it from the CocktailBerry folder with uv, so the exact machine setup is used:
  cd ~/CocktailBerry
  uv run --no-dev scripts/led_test.py --count 5
  uv run --no-dev scripts/led_test.py --count 5 --brightness 80

Sequence:
  1. Each LED individually red, green, blue
     -> checks data line, LED order and color order (GRB)
  2. All LEDs at once red, green, blue, white
  3. Rainbow chase
  4. All LEDs off
Abort anytime with Ctrl+C (LEDs are switched off).
"""

import argparse
import sys
import time
from pathlib import Path

# Make the CocktailBerry `src` package importable when started as `uv run scripts/led_test.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.machine.leds.ws_spi import Color, NeoPixelSPI

LED_PIN = 10  # SPI MOSI, physical pin 19
DEFAULT_BRIGHTNESS = 50
MAX_BRIGHTNESS = 255
WHEEL_SEGMENT = 85  # color wheel is split into three segments of 85 steps
OFF = Color(0, 0, 0)
USAGE_EXAMPLE = "Example: uv run --no-dev scripts/led_test.py --count 5"


def fill(strip: NeoPixelSPI, color: int) -> None:
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()


def wheel(pos: int) -> int:
    """Color on the color wheel (0-255)."""
    pos = 255 - pos
    if pos < WHEEL_SEGMENT:
        return Color(255 - pos * 3, 0, pos * 3)
    if pos < 2 * WHEEL_SEGMENT:
        pos -= WHEEL_SEGMENT
        return Color(0, pos * 3, 255 - pos * 3)
    pos -= 2 * WHEEL_SEGMENT
    return Color(pos * 3, 255 - pos * 3, 0)


def single_led_test(strip: NeoPixelSPI) -> None:
    print("1) Single LED test: each LED in turn RED -> GREEN -> BLUE")
    colors = [("red", Color(255, 0, 0)), ("green", Color(0, 255, 0)), ("blue", Color(0, 0, 255))]
    for i in range(strip.numPixels()):
        for name, color in colors:
            fill(strip, OFF)
            strip.setPixelColor(i, color)
            strip.show()
            print(f"   LED {i + 1}: {name}")
            time.sleep(0.6)
    fill(strip, OFF)


def all_leds_test(strip: NeoPixelSPI) -> None:
    print("2) All LEDs at once")
    for name, color in [
        ("red", Color(255, 0, 0)),
        ("green", Color(0, 255, 0)),
        ("blue", Color(0, 0, 255)),
        ("white", Color(255, 255, 255)),
    ]:
        print(f"   all {name}")
        fill(strip, color)
        time.sleep(1.5)


def rainbow_chase(strip: NeoPixelSPI, rounds: int = 3) -> None:
    print("3) Rainbow chase")
    n = strip.numPixels()
    for j in range(256 * rounds):
        for i in range(n):
            strip.setPixelColor(i, wheel((i * 256 // n + j) & 255))
        strip.show()
        time.sleep(0.01)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"WS281x LED test on GPIO {LED_PIN} (SPI MOSI, physical pin 19)",
        epilog=USAGE_EXAMPLE,
    )
    parser.add_argument("--count", type=int, help="Number of LEDs on the strip (required)")
    parser.add_argument(
        "--brightness",
        type=int,
        default=DEFAULT_BRIGHTNESS,
        help=f"Brightness 0-{MAX_BRIGHTNESS}, default {DEFAULT_BRIGHTNESS}",
    )
    args = parser.parse_args()

    if args.count is None:
        parser.error(f"Missing argument: --count <number of LEDs>\n{USAGE_EXAMPLE}")
    if args.count < 1:
        parser.error("The number of LEDs must be at least 1.")
    if not 0 <= args.brightness <= MAX_BRIGHTNESS:
        parser.error(f"Brightness must be between 0 and {MAX_BRIGHTNESS}.")
    return args


def main() -> None:
    args = parse_args()

    strip = NeoPixelSPI(args.count, LED_PIN, brightness=args.brightness)
    try:
        strip.begin()
    except RuntimeError as err:
        sys.exit(f"Error: {err}")
    print(f"Strip started: {args.count} LEDs on GPIO {LED_PIN}, brightness {args.brightness}")

    try:
        single_led_test(strip)
        all_leds_test(strip)
        rainbow_chase(strip)
        print("4) Done, LEDs off.")
    except KeyboardInterrupt:
        print("\nAborted.")
    finally:
        fill(strip, OFF)


if __name__ == "__main__":
    main()
