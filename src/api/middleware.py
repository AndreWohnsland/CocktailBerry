from typing import Callable, Literal, Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from src.config.config_manager import CONFIG as cfg

master_password_header = APIKeyHeader(name="x-master-key", scheme_name="Master Password", auto_error=False)
maker_password_header = APIKeyHeader(name="x-maker-key", scheme_name="Maker Password", auto_error=False)


def _parse_password(password: Optional[str]) -> int:
    if password is None:
        raise HTTPException(status_code=403, detail="Missing Password")
    try:
        return int(password)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid Password")


def master_protected_dependency(master_password: Optional[str] = Security(master_password_header)) -> None:
    if cfg.UI_MASTERPASSWORD == 0:
        return
    password = _parse_password(master_password)
    if password != cfg.UI_MASTERPASSWORD:
        raise HTTPException(status_code=403, detail="Invalid Master Password")


def maker_protected(tab: Literal[0, 1, 2] = 1) -> Callable[[str], None]:
    def dependency(maker_password: Optional[str] = Security(maker_password_header)) -> None:
        if cfg.UI_MAKER_PASSWORD == 0:
            return
        if not cfg.UI_LOCKED_TABS[tab]:
            return
        password = _parse_password(maker_password)
        if password != cfg.UI_MAKER_PASSWORD:
            raise HTTPException(status_code=403, detail="Invalid Maker Password")

    return dependency
