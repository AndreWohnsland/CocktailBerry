# pyright: reportMissingImports=false
"""WS281x / NeoPixel driver over SPI (DIN on GPIO10 / MOSI, physical pin 19).

Replaces ``rpi_ws281x`` for the bits we use. ``rpi_ws281x`` drives the strip via
the BCM DMA/PWM/PCM peripherals, which do not exist on the Pi 5 (RP1 chip) — its
init guard fails there even when wired to SPI. This bit-bangs the WS2812 protocol
over SPI instead. The strip is driven from the 40-pin header SPI0 (``/dev/spidev0.0``,
GPIO10 = MOSI) on every Pi, including the Pi 5. SPI must be enabled (raspi-config).
Only the MOSI pin is usable; the ``pin`` arg is kept for API parity but ignored.

WS2812 runs at 800 kHz (1.25 us/bit). We send 3 SPI bits per data bit at 2.4 MHz:
a 0 bit -> ``0b100``, a 1 bit -> ``0b110``.
"""

from __future__ import annotations

import spidev

from src.logger_handler import LoggerHandler

_logger = LoggerHandler("WSLedSPI")

_SPI_HZ = 2_400_000
_SYM = (0b100, 0b110)  # data bit 0 / 1 as a 3-bit SPI symbol
_RESET = [0] * 100  # trailing low bytes (>50 us) latch the strip
_BYTE = 8


def Color(red: int, green: int, blue: int, white: int = 0) -> int:
    """Pack to a 0xWWRRGGBB int, matching ``rpi_ws281x.Color``."""
    return (white << 24) | (red << 16) | (green << 8) | blue


def _open_spi() -> spidev.SpiDev:
    # The 40-pin header SPI0 (GPIO10 = MOSI) is /dev/spidev0.0 on every Pi (3/4/5).
    # Deliberately NOT falling back to /dev/spidev10.0: on the Pi 5 that is an internal
    # controller not wired to the header, so opening it would silently light nothing.
    try:
        spi = spidev.SpiDev()
        spi.open(0, 0)
        return spi
    except OSError as err:  # FileNotFoundError (no device) is an OSError subclass
        raise RuntimeError(
            "Could not open /dev/spidev0.0. Enable SPI (sudo raspi-config -> Interface -> SPI, "
            "then reboot) and wire DIN to GPIO10 (MOSI, physical pin 19)."
        ) from err


class NeoPixelSPI:
    """Minimal spidev-backed stand-in for ``rpi_ws281x.Adafruit_NeoPixel``."""

    def __init__(
        self,
        num: int,
        pin: int = 10,
        freq_hz: int = 800000,
        dma: int = 10,
        invert: bool = False,
        brightness: int = 255,
        channel: int = 0,
    ) -> None:
        # Only num and brightness matter; the rest exist for rpi_ws281x API parity.
        self.num = num
        self.brightness = brightness
        self._colors = [0] * num
        self._spi: spidev.SpiDev | None = None

    def begin(self) -> None:
        self._spi = _open_spi()
        self._spi.max_speed_hz = _SPI_HZ
        self._spi.mode = 0
        # Log the negotiated clock. WS2812 needs ~2.4 MHz for correct bit timing; on the
        # Pi 3/4 the SPI clock is a power-of-2 divisor of the core clock and may round off,
        # so a value far from _SPI_HZ here is the prime suspect when LEDs flicker / mis-colour.
        achieved = self._spi.max_speed_hz
        msg = f"<i> WS281x SPI ready: {self.num} px on /dev/spidev0.0 @ {achieved} Hz (target {_SPI_HZ})"
        if achieved == _SPI_HZ:
            _logger.info(msg)
        else:
            _logger.warning(f"{msg} -- clock differs from target, may cause flicker / wrong colours")

    def numPixels(self) -> int:
        return self.num

    def setPixelColor(self, pos: int, color: int) -> None:
        if 0 <= pos < self.num:
            self._colors[pos] = color

    def show(self) -> None:
        if self._spi is None:
            raise RuntimeError("begin() must be called before show().")
        b = self.brightness
        bits: list[int] = []
        for c in self._colors:
            r = ((c >> 16) & 0xFF) * b // 255
            g = ((c >> 8) & 0xFF) * b // 255
            blue = (c & 0xFF) * b // 255
            for byte in (g, r, blue):  # WS2812 wire order is GRB
                for i in range(7, -1, -1):
                    bits.append(_SYM[(byte >> i) & 1])
        out, acc, n = bytearray(), 0, 0
        for sym in bits:  # pack 3-bit symbols into bytes
            acc = (acc << 3) | sym
            n += 3
            while n >= _BYTE:
                n -= _BYTE
                out.append((acc >> n) & 0xFF)
        if n:
            out.append((acc << (_BYTE - n)) & 0xFF)
        self._spi.xfer2(list(out) + _RESET)
