"""TARZAN TSP — TARZAN Signal Protocol.

Pakiet ma być lekki przy imporcie. Nie importujemy tu serwera ani modułów
LKS-N5 na starcie pakietu, bo uruchamianie modułów przez ``python -m`` może
wtedy powodować ostrzeżenia runpy typu:

    module found in sys.modules after import of package, but prior to execution

Publiczne klasy są nadal dostępne przez leniwe ``__getattr__``.
"""

from __future__ import annotations

try:
    from .tarzanTspConfig import TSP_MINI_PC_HOST, TSP_PORT, TSP_STACJA_HOST
except Exception:  # pragma: no cover - pakiet może być importowany podczas instalacji
    TSP_MINI_PC_HOST = "0.0.0.0"
    TSP_STACJA_HOST = "127.0.0.1"
    TSP_PORT = 7777

__all__ = [
    "TSP_MINI_PC_HOST",
    "TSP_STACJA_HOST",
    "TSP_PORT",
    "TarzanTspClient",
    "TarzanTspServer",
    "TarzanTspSignalProvider",
]


def __getattr__(name: str):
    """Leniwy import cięższych obiektów TSP.

    Dzięki temu ``python3 -m core.TSP.tarzanTspLksNextion5`` nie importuje
    po drodze ``tarzanTspServer.py`` i nie ładuje ponownie modułu LKS-N5 przed
    właściwym wykonaniem.
    """

    if name == "TarzanTspClient":
        from .tarzanTspClient import TarzanTspClient

        return TarzanTspClient
    if name == "TarzanTspServer":
        from .tarzanTspServer import TarzanTspServer

        return TarzanTspServer
    if name == "TarzanTspSignalProvider":
        from .tarzanTspSignals import TarzanTspSignalProvider

        return TarzanTspSignalProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
