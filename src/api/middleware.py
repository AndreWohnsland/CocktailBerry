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


def master_protected_dependency(master_password: str | None = Security(master_password_header)) -> None:
    if cfg.UI_MASTERPASSWORD == 0:
        return
    password = _parse_password(master_password)
    if password != cfg.UI_MASTERPASSWORD:
        raise HTTPException(status_code=403, detail="Invalid Master Password")


def maker_protected(tab: Tab) -> Callable[[str], None]:
    def dependency(maker_password: str | None = Security(maker_password_header)) -> None:
        if cfg.UI_MAKER_PASSWORD == 0:
            return
        if not cfg.UI_LOCKED_TABS[tab]:
            return
        if cfg.waiter_mode_active and _waiter_has_tab_permission(tab):
            return
        password = _parse_password(maker_password)
        if password != cfg.UI_MAKER_PASSWORD:
            raise HTTPException(status_code=403, detail="Invalid Maker Password")

    return dependency
