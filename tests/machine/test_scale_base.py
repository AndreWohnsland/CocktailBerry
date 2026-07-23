import pytest

from src.machine.scale.base import ScaleInterface


class _FakeScale(ScaleInterface):
    """Scale returning a scripted sequence of raw readings (last value repeats)."""

    def __init__(self, readings: list[int]) -> None:
        class _Config:
            calibration_factor = 1.0
            zero_raw_offset = 0

        super().__init__(_Config(), hardware=None)  # ty:ignore[invalid-argument-type]
        self._readings = readings

    def read_raw(self, samples: int = 1) -> int:
        if len(self._readings) > 1:
            return self._readings.pop(0)
        return self._readings[0]

    def tare(self, samples: int = 3) -> int:
        return 0

    def read_grams(self) -> float:
        return 0.0

    def get_gross_grams(self) -> float:
        return 0.0

    def cleanup(self) -> None:
        pass


def test_calibrate_stable_reading_sets_factor() -> None:
    scale = _FakeScale([100_000])
    factor = scale.calibrate_with_known_weight(100.0, zero_raw_offset=20_000, samples=5)
    assert factor == pytest.approx(800.0)
    assert scale._calibration_factor == pytest.approx(800.0)
    assert scale._zero_raw_offset == 20_000


def test_calibrate_waits_for_settling() -> None:
    # settling transient first, then stable values: only the stable window may enter the factor
    scale = _FakeScale([150_000, 130_000, 110_000, 100_000, 100_000, 100_000, 100_000, 100_000, 100_000])
    factor = scale.calibrate_with_known_weight(100.0, zero_raw_offset=20_000, samples=5)
    assert factor == pytest.approx(800.0)


def test_calibrate_unstable_reading_raises() -> None:
    # permanently oscillating load never satisfies the stability gate
    scale = _FakeScale([100_000, 200_000] * 100)
    with pytest.raises(RuntimeError, match="did not stabilize"):
        scale.calibrate_with_known_weight(100.0, zero_raw_offset=20_000, samples=5)


def test_calibrate_invalid_weight_keeps_factor() -> None:
    scale = _FakeScale([100_000])
    assert scale.calibrate_with_known_weight(0, zero_raw_offset=20_000) == 1.0
