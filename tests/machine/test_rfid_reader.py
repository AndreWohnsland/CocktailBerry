import time
from collections.abc import Callable, Iterator
from itertools import chain, repeat
from threading import Event

import pytest

from src.machine.rfid import reader as reader_module
from src.machine.rfid.base import RFIDInterface
from src.machine.rfid.reader import RFIDReader

Card = tuple[str | None, str | None]
NO_CARD: Card = (None, None)


class FakeReader(RFIDInterface):
    """Yields the given read results in order, raising the exceptions among them; writes always succeed."""

    def __init__(self, results: Iterator[Card | Exception]) -> None:
        self._results = results
        self.reads = 0
        self.written: list[str] = []

    def read_card(self) -> Card:
        self.reads += 1
        result = next(self._results)
        if isinstance(result, Exception):
            raise result
        return result

    def write_card(self, text: str) -> bool:
        self.written.append(text)
        return True


def _cards(*ids: str) -> Iterator[Card | Exception]:
    return chain((("", _id) for _id in ids), repeat(NO_CARD))


@pytest.fixture
def reader(monkeypatch: pytest.MonkeyPatch) -> Iterator[RFIDReader]:
    monkeypatch.setattr(RFIDReader, "_instance", None)
    monkeypatch.setattr(reader_module, "_ERROR_BACKOFF_S", 0.01)
    reader = RFIDReader()
    yield reader
    reader.cancel_reading()


def _wait_for(condition: Callable[[], bool], timeout: float = 2.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


def test_read_loop_survives_a_driver_error(reader: RFIDReader) -> None:
    reader.attach(FakeReader(chain([RuntimeError("spi")], _cards("CARD"))))
    seen: list[str] = []
    assert reader.read_rfid(lambda _t, _id: seen.append(_id), read_delay_s=0.01)
    assert _wait_for(lambda: seen == ["CARD"])
    assert reader.is_active


def test_cancel_stops_the_loop(reader: RFIDReader) -> None:
    driver = FakeReader(_cards())
    reader.attach(driver)
    assert reader.read_rfid(lambda _t, _id: None)
    assert _wait_for(lambda: driver.reads > 2)
    reader.cancel_reading()
    assert not reader.is_active
    time.sleep(0.05)  # the current step may still finish
    reads = driver.reads
    time.sleep(0.15)
    assert driver.reads == reads


def test_restart_after_cancel_keeps_exactly_one_loop(reader: RFIDReader) -> None:
    reader.attach(FakeReader(_cards(*["CARD"] * 10_000)))
    first: list[str] = []
    second: list[str] = []

    assert reader.read_rfid(lambda _t, _id: first.append(_id), read_delay_s=0.01)
    assert _wait_for(lambda: len(first) > 2)
    assert not reader.read_rfid(lambda _t, _id: second.append(_id)), "the reader is a single slot"

    reader.cancel_reading()
    assert reader.read_rfid(lambda _t, _id: second.append(_id), read_delay_s=0.01)
    assert _wait_for(lambda: len(second) > 2)
    time.sleep(0.05)
    first_count = len(first)
    time.sleep(0.1)
    assert len(first) == first_count, "the cancelled loop kept delivering"
    assert not reader.read_rfid(lambda _t, _id: None), "the finished old loop freed the slot of the new one"


def test_card_read_during_cancel_is_not_delivered(reader: RFIDReader) -> None:
    reading = Event()
    release = Event()

    class BlockingReader(FakeReader):
        def read_card(self) -> Card:
            reading.set()
            release.wait(2.0)
            return ("", "LATE")

    reader.attach(BlockingReader(_cards()))
    seen: list[str] = []
    assert reader.read_rfid(lambda _t, _id: seen.append(_id))
    assert reading.wait(2.0)
    reader.cancel_reading()
    release.set()
    time.sleep(0.1)
    assert seen == []


def test_write_frees_the_reader_even_if_the_handler_fails(reader: RFIDReader) -> None:
    driver = FakeReader(_cards())
    reader.attach(driver)
    called = Event()

    def handler(_text: str) -> None:
        called.set()
        raise RuntimeError("widget gone")

    assert reader.write_rfid("label", handler)
    assert called.wait(2.0)
    assert _wait_for(lambda: not reader.is_active)
    assert driver.written == ["label"]
    assert reader.read_rfid(lambda _t, _id: None)
