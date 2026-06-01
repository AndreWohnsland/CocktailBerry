from collections.abc import Callable

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import Tab, shared

master_password_header = APIKeyHeader(name="x-master-key", scheme_name="Master Password", auto_error=False)
maker_password_header = APIKeyHeader(name="x-maker-key", scheme_name="Maker Password", auto_error=False)


def _parse_password(password: str | None) -> int:
    if password is None:
        raise HTTPException(status_code=403, detail="Missing Password")
    try:
        return int(password)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid Password")


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
    if master_password is None or cfg.UI_MASTERPASSWORD == 0:
        return False
    try:
        return int(master_password) == cfg.UI_MASTERPASSWORD
    except ValueError:
        return False


def master_protected_dependency(master_password: str | None = Security(master_password_header)) -> None:
    if cfg.UI_MASTERPASSWORD == 0:
        return
    if cfg.waiter_mode_active and _waiter_has_options_permission():
        return
    password = _parse_password(master_password)
    if password != cfg.UI_MASTERPASSWORD:
        raise HTTPException(status_code=403, detail="Invalid Master Password")


def maker_protected(tab: Tab) -> Callable[..., None]:
    def dependency(
        maker_password: str | None = Security(maker_password_header),
        master_password: str | None = Security(master_password_header),
    ) -> None:
        if cfg.UI_MAKER_PASSWORD == 0:
            return
        if not cfg.UI_LOCKED_TABS[tab]:
            return
        if cfg.waiter_mode_active and _waiter_has_tab_permission(tab):
            return
        # an admin (valid master key) can do anything an operator can, so master auth satisfies maker
        if _has_master_privilege(master_password):
            return
        password = _parse_password(maker_password)
        if password != cfg.UI_MAKER_PASSWORD:
            raise HTTPException(status_code=403, detail="Invalid Maker Password")

    return dependency
