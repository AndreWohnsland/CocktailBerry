"""The logged-in waiter state must follow waiter and role edits.

``shared.current_waiter`` holds a snapshot of the role permissions taken at scan time
(see :meth:`WaiterResponse.from_db`), and the tab/tile gating in both UIs reads that
snapshot. Without a refresh after an edit, access keeps being granted by permissions
that no longer exist.

The endpoints are driven directly so the tests fail if a call site drops the refresh,
not just if the refresh itself breaks.
"""

from __future__ import annotations

import asyncio

import pytest

from src.api.models import RoleUpdate, TabPermission, WaiterResponse
from src.api.routers.roles import update_role
from src.api.routers.waiters import delete_waiter
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander


@pytest.fixture
def logged_in(monkeypatch: pytest.MonkeyPatch, db_commander: DatabaseCommander) -> DatabaseCommander:
    """Register a waiter on a maker-only role and put them in the shared state."""
    for module in ("src.service.waiter_service", "src.api.routers.roles", "src.api.routers.waiters"):
        monkeypatch.setattr(f"{module}.DatabaseCommander", lambda: db_commander)
    role = db_commander.create_role("bartender", permissions={"maker": True})
    waiter = db_commander.create_waiter("nfc_001", "Alice", role_id=role.id)
    monkeypatch.setattr(shared, "current_waiter_nfc_id", waiter.nfc_id)
    monkeypatch.setattr(shared, "current_waiter", WaiterResponse.from_db(waiter))
    return db_commander


def test_role_edit_reaches_the_logged_in_waiter(logged_in: DatabaseCommander) -> None:
    assert shared.current_waiter is not None
    assert shared.current_waiter.permissions.recipes is False

    role_id = logged_in.get_all_roles()[0].id
    asyncio.run(update_role(role_id, RoleUpdate(permissions=TabPermission(maker=True, recipes=True))))

    assert shared.current_waiter is not None
    assert shared.current_waiter.permissions.recipes is True


def test_deleting_the_logged_in_waiter_clears_the_state(logged_in: DatabaseCommander) -> None:
    asyncio.run(delete_waiter("nfc_001"))

    assert shared.current_waiter is None
    # the card is still on the reader, so the scanned id stays: the holder is now unregistered
    assert shared.current_waiter_nfc_id == "nfc_001"
