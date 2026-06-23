from __future__ import annotations

import sys
import types

# spidev is a linux-only dependency; stub it so the encoder is testable anywhere.
if "spidev" not in sys.modules:
    stub = types.ModuleType("spidev")
    stub.SpiDev = object  # type: ignore[attr-defined]
    sys.modules["spidev"] = stub

from src.machine.leds.ws_spi import _RESET, Color, NeoPixelSPI


class _FakeSpi:
    def __init__(self) -> None:
        self.last: list[int] = []

    def xfer2(self, data: list[int]) -> None:
        self.last = data


def test_color_packs_rgb() -> None:
    assert Color(0x12, 0x34, 0x56) == 0x123456
    assert Color(0, 0, 0, white=0xFF) == 0xFF000000


def test_show_encodes_one_green_pixel_grb() -> None:
    strip = NeoPixelSPI(1, brightness=255)
    strip._spi = _FakeSpi()  # bypass begin()/hardware
    strip.setPixelColor(0, Color(0, 255, 0))  # pure green
    strip.show()
    data = strip._spi.last  # type: ignore[attr-defined]
    # 24 data bits -> 24 3-bit symbols -> 9 bytes, then the reset latch.
    body = data[: len(data) - len(_RESET)]
    assert data[-len(_RESET) :] == _RESET
    assert len(body) == 9
    # GRB order: green byte (0xFF) first -> first 8 symbols are all "1" (0b110).
    # 8x 0b110 = 0b110110110110110110110110 -> bytes 0xDB 0x6D 0xB6
    assert body[0:3] == [0xDB, 0x6D, 0xB6]
    # red+blue are 0 -> remaining symbols all "0" (0b100).
    assert body[3:] == [0x92, 0x49, 0x24, 0x92, 0x49, 0x24]


def test_brightness_scales_down() -> None:
    strip = NeoPixelSPI(1, brightness=0)
    strip._spi = _FakeSpi()
    strip.setPixelColor(0, Color(255, 255, 255))
    strip.show()
    body = strip._spi.last[: -len(_RESET)]  # type: ignore[attr-defined]
    # brightness 0 -> all channels 0 -> every symbol is 0b100.
    assert set(body) == {0x92, 0x49, 0x24}
