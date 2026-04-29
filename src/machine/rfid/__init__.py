from __future__ import annotations

import os
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.rfid.base import RFIDInterface
from src.machine.rfid.mfrc522 import MFRC522Reader
from src.machine.rfid.mock import MockReader
from src.machine.rfid.reader import RFIDReader
from src.machine.rfid.usb import USBReader

if TYPE_CHECKING:
    from src.config.config_types import BaseRfidConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("rfid")

__all__ = ["MFRC522Reader", "MockReader", "RFIDInterface", "RFIDReader", "USBReader", "create_rfid"]


def create_rfid(config: BaseRfidConfig, hardware: HardwareContext) -> RFIDInterface | None:
    """Create an RFID controller from config, returning None if unavailable.

    Every RFID controller — built-in or from ``addons/rfid/`` — receives the
    full ``HardwareContext`` so it can reach pins, LEDs, scale, carriage, or
    hardware extension instances if needed. A disabled config (``enabled=False``)
    resolves to ``None``.
    """
    if "MOCK_RFID" in os.environ:
        _logger.warning("Using mock RFID reader.")
        return MockReader(config, hardware)
    if not config.enabled:
        return None
    try:
        if config.rfid_type == "MFRC522":
            return MFRC522Reader(config, hardware)
        if config.rfid_type == "USB":
            return USBReader(config, hardware)
        # Custom RFID extensions from addons/rfid/ — dispatch by rfid_type.
        from src.programs.addons.rfid_extensions import RFID_ADDONS

        entry = RFID_ADDONS.entries.get(config.rfid_type)
        if entry is not None:
            return entry.implementation_class(config, hardware)
        _logger.error(f"Unknown rfid type: {config.rfid_type}")
    except Exception:
        _logger.warning("RFID initialization failed, continuing without RFID")
        _logger.log_exception("RFID initialization traceback")
    return None
