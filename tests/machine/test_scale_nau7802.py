import time

from src.machine.scale.nau7802 import NAU7802Scale


class _DeadNAU:
    """Chip that never signals a ready sample (wedged bus / wiring glitch)."""

    def available(self) -> bool:
        return False

    def read(self) -> int:
        raise AssertionError("read() must not be called when no sample is available")


def test_wait_and_read_times_out_and_reads_as_zero_grams() -> None:
    scale = object.__new__(NAU7802Scale)
    scale._nau = _DeadNAU()
    scale._zero_offset = 12345
    start = time.monotonic()
    assert scale._wait_and_read() == 12345
    assert time.monotonic() - start < 2.0, "timeout must bound the wait instead of spinning forever"
