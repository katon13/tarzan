from __future__ import annotations

from hardware.tarzanNextion.bridge import TarzanNextionBridge


class TarzanNextion70:
    """Kompatybilna nakładka dla Nextion 7\"."""

    def __init__(self, bus):
        self.bridge = TarzanNextionBridge(bus)

    def snapshot(self):
        return self.bridge.snapshot()
