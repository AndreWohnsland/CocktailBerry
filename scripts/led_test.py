#!/usr/bin/env python3
"""WS281x LED test script for CocktailBerry.

Tests the LED strip independently of the CocktailBerry app, using the same SPI driver as CocktailBerry.
The data wire must be connected to GPIO 10 (SPI MOSI, physical pin 19), SPI must be enabled.
Works on every Raspberry Pi, including the Pi 5.

Run it from the CocktailBerry folder with uv, so the exact machine setup is used:
  cd ~/CocktailBerry
  uv run --no-dev scripts/led_test.py --count 5
  uv run --no-dev scripts/led_test.py --count 5 --brightness 60

Sequence:
  1. Each LED individually red, green, blue
     -> checks data line, LED order and color order (GRB)
  2. All LEDs at once red, green, blue, white
  3. Rainbow chase
  4. All LEDs off
Abort anytime with Ctrl+C (LEDs are switched off).
"""

import sys
import time
from pathlib import Path

import typer

# Make the CocktailBerry `src` package importable when started as `uv run scripts/led_test.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.machine.leds.ws_spi import Color, NeoPixelSPI

LED_PIN = 10  # SPI MOSI, physical pin 19
DEFAULT_BRIGHTNESS = 20  # percent
WHEEL_SEGMENT = 85  # color wheel is split into three segments of 85 steps
OFF = Color(0, 0, 0)


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


def percent_to_brightness(percent: int) -> int:
    """Convert brightness in percent (0-100) to the 0-255 range of the driver, same as CocktailBerry does."""
    return min(int(255 * percent / 100), 255)


def main(
    count: int = typer.Option(..., "--count", "-c", min=1, help="Number of LEDs on the strip."),
    brightness: int = typer.Option(
        DEFAULT_BRIGHTNESS, "--brightness", "-b", min=0, max=100, help="Brightness in percent (0-100)."
    ),
) -> None:
    """WS281x LED test on GPIO 10 (SPI MOSI, physical pin 19).

    Example: uv run --no-dev scripts/led_test.py --count 5
    """
    strip = NeoPixelSPI(count, LED_PIN, brightness=percent_to_brightness(brightness))
    try:
        strip.begin()
    except RuntimeError as err:
        typer.echo(f"Error: {err}", err=True)
        raise typer.Exit(1) from err
    print(f"Strip started: {count} LEDs on GPIO {LED_PIN}, brightness {brightness} %")

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
    typer.run(main)
