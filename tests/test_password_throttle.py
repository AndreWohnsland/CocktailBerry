import pytest
from fastapi import HTTPException

from src.api import middleware
from src.api.middleware import LOGIN_LOCK_SECONDS, MAX_FAILED_LOGINS, FailedLoginTracker


def test_lockout_after_repeated_failures_expires(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 1000.0
    monkeypatch.setattr(middleware.time, "monotonic", lambda: now)
    tracker = FailedLoginTracker()

    for _ in range(MAX_FAILED_LOGINS - 1):
        tracker.fail("phone")
    tracker.check("phone")
    tracker.fail("phone")
    with pytest.raises(HTTPException) as exc:
        tracker.check("phone")
    assert exc.value.status_code == 429
    tracker.check("kiosk")

    now += LOGIN_LOCK_SECONDS
    tracker.check("phone")


def test_success_clears_failures() -> None:
    tracker = FailedLoginTracker()
    for _ in range(MAX_FAILED_LOGINS - 1):
        tracker.fail("phone")
    tracker.clear("phone")
    for _ in range(MAX_FAILED_LOGINS - 1):
        tracker.fail("phone")
    tracker.check("phone")
