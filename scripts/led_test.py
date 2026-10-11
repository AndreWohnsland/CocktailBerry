#!/usr/bin/env python3
"""WS2812B test script for the Raspberry Pi.

GPIO pin and number of LEDs are required:
  sudo python3 led_test.py --pin 18 --count 5
  sudo python3 led_test.py --pin 10 --count 5 --brightness 80

Supported pins (BCM): 10 (SPI), 12, 13, 18, 19 (PWM), 21 (PCM)
Brightness optional: 0-255, default 50

Sequence:
  1. Each LED individually red, green, blue
     -> checks data line, LED order and color order (GRB)
  2. All LEDs at once red, green, blue, white
  3. Rainbow chase
  4. All LEDs off
Abort anytime with Ctrl+C (LEDs are switched off).
"""

import argparse
import time

from rpi_ws281x import Color, PixelStrip

LED_FREQ_HZ = 800_000  # WS2812B signal frequency
LED_DMA = 10  # DMA channel (10 is safe on the Pi 4)
LED_INVERT = False  # True only with an inverting level shifter (e.g. NPN transistor)
SUPPORTED_PINS = {10, 12, 13, 18, 19, 21}  # SPI, PWM0/PWM1, PCM
MAX_BRIGHTNESS = 255
WHEEL_SEGMENT = 85  # color wheel is split into three segments of 85 steps


def channel_for_pin(pin: int) -> int:
    # GPIO 13, 19, 41, 45, 53 use PWM channel 1, everything else channel 0
    return 1 if pin in (13, 19, 41, 45, 53) else 0


def fill(strip: PixelStrip, color: int) -> None:
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


def single_led_test(strip: PixelStrip) -> None:
    print("1) Single LED test: each LED in turn RED -> GREEN -> BLUE")
    colors = [("red", Color(255, 0, 0)), ("green", Color(0, 255, 0)), ("blue", Color(0, 0, 255))]
    for i in range(strip.numPixels()):
        for name, color in colors:
            fill(strip, Color(0, 0, 0))
            strip.setPixelColor(i, color)
            strip.show()
            print(f"   LED {i + 1}: {name}")
            time.sleep(0.6)
    fill(strip, Color(0, 0, 0))


def all_leds_test(strip: PixelStrip) -> None:
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


def rainbow_chase(strip: PixelStrip, rounds: int = 3) -> None:
    print("3) Rainbow chase")
    n = strip.numPixels()
    for j in range(256 * rounds):
        for i in range(n):
            strip.setPixelColor(i, wheel((i * 256 // n + j) & 255))
        strip.show()
        time.sleep(0.01)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WS2812B test",
        epilog="Example: sudo python3 led_test.py --pin 18 --count 5",
    )
    parser.add_argument("--pin", type=int, help="GPIO number (BCM), e.g. 18 or 10 (required)")
    parser.add_argument("--count", type=int, help="Number of LEDs on the strip (required)")
    parser.add_argument("--brightness", type=int, default=50, help="Brightness 0-255, default 50")
    args = parser.parse_args()

    missing = []
    if args.pin is None:
        missing.append("--pin <GPIO number>")
    if args.count is None:
        missing.append("--count <number of LEDs>")
    if missing:
        parser.error(
            "Missing argument(s): " + ", ".join(missing) + "\nExample: sudo python3 led_test.py --pin 18 --count 5"
        )

    if args.pin not in SUPPORTED_PINS:
        parser.error(
            f"GPIO {args.pin} is not supported for WS2812B. "
            f"Supported pins (BCM): {', '.join(map(str, sorted(SUPPORTED_PINS)))}"
        )
    if args.count < 1:
        parser.error("The number of LEDs must be at least 1.")
    if not 0 <= args.brightness <= MAX_BRIGHTNESS:
        parser.error("Brightness must be between 0 and 255.")

    strip = PixelStrip(
        args.count,
        args.pin,
        LED_FREQ_HZ,
        LED_DMA,
        LED_INVERT,
        args.brightness,
        channel_for_pin(args.pin),
    )
    strip.begin()
    print(f"Strip started: {args.count} LEDs on GPIO {args.pin}, brightness {args.brightness}")

    try:
        single_led_test(strip)
        all_leds_test(strip)
        rainbow_chase(strip)
        print("4) Done, LEDs off.")
    except KeyboardInterrupt:
        print("\nAborted.")
    finally:
        fill(strip, Color(0, 0, 0))


if __name__ == "__main__":
    main()
