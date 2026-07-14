from __future__ import annotations

import sys
import types

# spidev is a linux-only dependency; stub it so the encoder is testable anywhere.
if "spidev" not in sys.modules:
    stub = types.ModuleType("spidev")
    stub.SpiDev = object  # type: ignore[attr-defined]
    sys.modules["spidev"] = stub

from src.machine.leds.ws_spi import _RESET, _SPI_HZ, Color, NeoPixelSPI


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
    # Frame layout: low preamble (phantom-edge guard), 24 data bits as one SPI byte each,
    # then the reset latch.
    assert data[: len(_RESET)] == _RESET
    assert data[-len(_RESET) :] == _RESET
    body = data[len(_RESET) : len(data) - len(_RESET)]
    assert len(body) == 24
    # GRB order: green byte (0xFF) first -> first 8 symbols are all "1" (0xF8).
    assert body[0:8] == [0xF8] * 8
    # red+blue are 0 -> remaining symbols all "0" (0xC0).
    assert body[8:] == [0xC0] * 16


def test_reset_latch_covers_newer_ws2812b() -> None:
    # Newer WS2812B revisions need >280 us low to latch; keep _RESET scaled to _SPI_HZ.
    assert len(_RESET) * 8 / _SPI_HZ >= 280e-6


def test_brightness_scales_down() -> None:
    strip = NeoPixelSPI(1, brightness=0)
    strip._spi = _FakeSpi()
    strip.setPixelColor(0, Color(255, 255, 255))
    strip.show()
    body = strip._spi.last[len(_RESET) : -len(_RESET)]  # type: ignore[attr-defined]
    # brightness 0 -> all channels 0 -> every symbol is the "0" byte.
    assert set(body) == {0xC0}
