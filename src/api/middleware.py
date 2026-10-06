import time
from collections.abc import Callable

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import Tab, shared

master_password_header = APIKeyHeader(name="x-master-key", scheme_name="Master Password", auto_error=False)
maker_password_header = APIKeyHeader(name="x-maker-key", scheme_name="Maker Password", auto_error=False)

MAX_FAILED_LOGINS = 5
LOGIN_LOCK_SECONDS = 30


class FailedLoginTracker:
    """Locks a client out for a while after too many wrong passwords in a row."""

    def __init__(self) -> None:
        # ponytail: entries below the threshold never expire, fine for a LAN-sized client set
        self._attempts: dict[str, tuple[int, float]] = {}  # client -> (failures, locked_until)

    def check(self, client: str) -> None:
        _, locked_until = self._attempts.get(client, (0, 0.0))
        if time.monotonic() < locked_until:
            raise HTTPException(status_code=429, detail="Too many failed attempts, try again later")

    def fail(self, client: str) -> None:
        failures, _ = self._attempts.get(client, (0, 0.0))
        failures += 1
        if failures >= MAX_FAILED_LOGINS:
            self._attempts[client] = (0, time.monotonic() + LOGIN_LOCK_SECONDS)
        else:
            self._attempts[client] = (failures, 0.0)

    def clear(self, client: str) -> None:
        self._attempts.pop(client, None)


FAILED_LOGINS = FailedLoginTracker()


def _client_address(request: Request) -> str:
    # nginx forwards the real client, a direct hit on uvicorn only has the socket address
    return request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")


def _matches(password: str | None, expected: int) -> bool:
    try:
        return password is not None and int(password) == expected
    except ValueError:
        return False


def verify_password_attempt(request: Request, valid: bool, error: str) -> None:
    """Record the outcome for the client: 429 while locked out, 403 on a wrong password."""
    client = _client_address(request)
    FAILED_LOGINS.check(client)
    if not valid:
        FAILED_LOGINS.fail(client)
        raise HTTPException(status_code=403, detail=error)
    FAILED_LOGINS.clear(client)


def _waiter_has_tab_permission(tab: Tab) -> bool:
    waiter = shared.current_waiter
    if waiter is None:
        return False

    permission_by_tab = {
        Tab.MAKER: waiter.permissions.maker,
        Tab.INGREDIENTS: waiter.permissions.ingredients,
        Tab.RECIPES: waiter.permissions.recipes,
        Tab.BOTTLES: waiter.permissions.bottles,
    }
    return permission_by_tab.get(tab, False)


def _waiter_has_options_permission() -> bool:
    waiter = shared.current_waiter
    if waiter is None:
        return False
    return waiter.permissions.options


def _has_master_privilege(master_password: str | None) -> bool:
    """Whether the caller presented admin credentials, used to let master also satisfy maker auth.

    Unlike :func:`master_protected_dependency`, a *disabled* master password (0) does NOT grant this
    — it must not silently bypass a maker-locked tab. Requires a presented valid master key, or a
    waiter holding the options permission.
    """
    if cfg.waiter_mode_active and _waiter_has_options_permission():
        return True
    return cfg.UI_MASTERPASSWORD != 0 and _matches(master_password, cfg.UI_MASTERPASSWORD)


def master_protected_dependency(
    request: Request, master_password: str | None = Security(master_password_header)
) -> None:
    if cfg.UI_MASTERPASSWORD == 0:
        return
    if cfg.waiter_mode_active and _waiter_has_options_permission():
        return
    if master_password is None:
        raise HTTPException(status_code=403, detail="Missing Password")
    verify_password_attempt(request, _matches(master_password, cfg.UI_MASTERPASSWORD), "Invalid Master Password")


def maker_protected(tab: Tab) -> Callable[..., None]:
    def dependency(
        request: Request,
        maker_password: str | None = Security(maker_password_header),
        master_password: str | None = Security(master_password_header),
    ) -> None:
        if cfg.UI_MAKER_PASSWORD == 0:
            return
        if not cfg.UI_LOCKED_TABS[tab]:
            return
        if cfg.waiter_mode_active and _waiter_has_tab_permission(tab):
            return
        if maker_password is None and master_password is None:
            raise HTTPException(status_code=403, detail="Missing Password")
        # an admin (valid master key) can do anything an operator can, so master auth satisfies maker
        valid = _has_master_privilege(master_password) or _matches(maker_password, cfg.UI_MAKER_PASSWORD)
        verify_password_attempt(request, valid, "Invalid Maker Password")

    return dependency
