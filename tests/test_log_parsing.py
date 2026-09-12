from pathlib import Path

import pytest

from src.logger_handler import LogFiles
from src.utils import LogLevel, _parse_log, read_log_file

LOG = """2024-01-01 10:00:00 | DEBUG    | probe [x]
2024-01-01 10:00:01 | INFO     | started [x]
2024-01-01 10:00:02 | WARNING  | low volume [x]
2024-01-01 10:00:03 | ERROR    | pump failed [x]
2024-01-01 10:00:04 | CRITICAL | fire [x]
2024-01-01 10:00:05 | INFO     | started [x]"""


@pytest.mark.parametrize(
    ("min_level", "expected"),
    [
        ("DEBUG", ["started", "fire", "pump failed", "low volume", "probe"]),
        ("INFO", ["started", "fire", "pump failed", "low volume"]),
        ("WARNING", ["fire", "pump failed", "low volume"]),
        ("ERROR", ["fire", "pump failed"]),
    ],
)
def test_parse_log_filters_by_min_level(min_level: LogLevel, expected: list[str]) -> None:
    lines = _parse_log(LOG, min_level)
    assert [line.split(" | ")[1].split(" [")[0] for line in lines] == expected


def test_parse_log_dedupes_repeated_messages() -> None:
    lines = _parse_log(LOG, "INFO")
    assert lines[0].startswith("INFO     | started [x] (2x, latest: 2024-01-01 10:00:05)")


def test_read_log_file_missing_file_is_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.logger_handler.LOG_FOLDER", tmp_path)
    assert read_log_file(LogFiles.SERVICE) == []
