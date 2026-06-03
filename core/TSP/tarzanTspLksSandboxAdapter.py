from __future__ import annotations

"""DEPRECATED — nie używać w runtime LKS-N5.

ETAP 12 został zmieniony: LKS-N5 nie bazuje na dawnym
``tarzanMiniPcSandbox.py``. Sandbox jest tylko historycznym źródłem wiedzy.
Produkcja używa suwerennego modułu:

    core.TSP.tarzanTspLksHardwareTests

Ten plik zostaje tylko po to, aby wcześniejszy błędny patch nie wciągał
sandboxa jako zależności produkcyjnej.
"""

class TarzanTspLksSandboxAdapter:  # pragma: no cover
    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeError(
            "tarzanTspLksSandboxAdapter jest wyłączony. "
            "Użyj core.TSP.tarzanTspLksHardwareTests.TarzanTspLksHardwareTests."
        )
