import time
from threading import Thread

import pytest

from src.programs.addons import addons as addons_module
from src.programs.addons.addons import AddOnManager


def test_trigger_loop_survives_an_addon_bug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(addons_module, "_TRIGGER_POLL_S", 0.001)
    monkeypatch.setattr(addons_module, "_TRIGGER_ERROR_BACKOFF_S", 0.001)
    manager = AddOnManager.__new__(AddOnManager)
    manager.addon_thread_ids = {"Buggy": 1}
    calls: list[int] = []

    class Addon:
        def cocktail_trigger(self, _prepare: object) -> None:
            calls.append(1)
            if len(calls) == 1:
                raise AttributeError("'NoneType' object has no attribute 'read'")

    thread = Thread(target=manager._run_in_background, args=("Buggy", Addon(), lambda _c: (True, ""), 1), daemon=True)
    thread.start()
    end = time.monotonic() + 2.0
    while len(calls) < 3 and time.monotonic() < end:
        time.sleep(0.005)
    assert len(calls) >= 3, "the loop stopped after the exception"

    manager.addon_thread_ids["Buggy"] = 2  # a newer thread took over, this one must exit
    thread.join(timeout=1.0)
    assert not thread.is_alive()
