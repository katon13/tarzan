from __future__ import annotations

from hardware.tarzanNextion.bridge import TarzanNextionBridge


class TarzanNextion50:
    """Kompatybilna nakładka dla Nextion 5\"."""

    def __init__(self, bus):
        self.bridge = TarzanNextionBridge(bus)

    def snapshot(self):
        return self.bridge.snapshot()
