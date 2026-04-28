from __future__ import annotations

import time
from collections.abc import Iterator
from itertools import cycle
from typing import TYPE_CHECKING

from src.machine.rfid.base import RFIDInterface

if TYPE_CHECKING:
    from src.config.config_types import BaseRfidConfig
    from src.machine.hardware import HardwareContext


class MockReader(RFIDInterface):
    """Mock RFID reader for testing purposes."""

    def __init__(self, config: BaseRfidConfig, hardware: HardwareContext) -> None:
        super().__init__(config, hardware)
        self.mocked_ids: Iterator[str] = cycle(["33DFE41A", "9A853011"])
        self.current_id: str | None = None
        self.last_changed: float = 0

    def read_card(self) -> tuple[str | None, str | None]:
        text = "Mocked RFID Data"  # we will not use this usually
        # change the id every 1 minute
        time_window_sec = 60
        time.sleep(5)
        if time.time() - self.last_changed > time_window_sec:
            self.current_id = next(self.mocked_ids)
            self.last_changed = time.time()
        return text, self.current_id

    # Do not support writing in mock (writing is almost not used in application)
    def write_card(self, text: str) -> bool:
        return False
