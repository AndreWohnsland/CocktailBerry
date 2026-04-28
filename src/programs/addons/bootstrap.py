from __future__ import annotations

from src.programs.addons.addons import ADDONS
from src.programs.addons.carriage_extensions import CARRIAGE_ADDONS
from src.programs.addons.dispenser_extensions import DISPENSER_ADDONS
from src.programs.addons.hardware_extensions import HARDWARE_ADDONS
from src.programs.addons.rfid_extensions import RFID_ADDONS
from src.programs.addons.scale_extensions import SCALE_ADDONS


def initialize_addon_configs() -> None:
    """Discover addons and register all addon-contributed config with the config manager.

    Must be called once at program startup *before* :func:`cfg.read_local_config`
    so that custom hardware, scale, carriage, and dispenser variants (and addon
    configuration fields) are known to the config validator. Wired into both app
    versions:

    - v1 (Qt) — ``src/programs/cli.py``
    - v2 (Web) — ``src/api/api.py`` lifespan

    Keeping the order here centralised means both entrypoints stay in sync, and
    any future addon type only needs to be wired in one place.
    """
    HARDWARE_ADDONS.build_config()
    SCALE_ADDONS.build_full_config_fields()
    CARRIAGE_ADDONS.build_full_config_fields()
    RFID_ADDONS.build_full_config_fields()
    DISPENSER_ADDONS.build_full_config_fields()
    ADDONS.define_addon_configuration()
