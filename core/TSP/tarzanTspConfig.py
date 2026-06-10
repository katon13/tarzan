"""
Stała konfiguracja TSP — TARZAN Signal Protocol.

Ten moduł nie uruchamia połączeń i nie dotyka działającego TARZANA.
Zawiera tylko domyślne parametry protokołu i sieci.
"""

from __future__ import annotations

from pathlib import Path


TSP_PROTOCOL_NAME = "TSP"
TSP_PROTOCOL_VERSION = "1.0"

# Stałe adresy ustalone dla projektu TARZAN/TSP.
TSP_MINI_PC_HOST = "192.168.1.26"   # tarzanMiniPC — serwer TSP / TARZAN Signal Node
TSP_STACJA_HOST = "192.168.1.12"    # tarzanStacja — klient PAR/EHR
TSP_BIND_HOST = "0.0.0.0"           # serwer nasłuchuje na wszystkich interfejsach
TSP_PORT = 7777

# Rytm protokołu.
TSP_FAST_INTERVAL_MS = 10
TSP_NORMAL_INTERVAL_MS = 50
TSP_SLOW_INTERVAL_MS = 500
TSP_HEALTH_INTERVAL_MS = 1000
TSP_PING_INTERVAL_MS = 1000

# Debug i logi.
TSP_RING_RX_SIZE = 200
TSP_RING_TX_SIZE = 200
TSP_RING_ERROR_SIZE = 100
TSP_STATS_LOG_INTERVAL_MS = 30000
TSP_DEFAULT_TRACE_SECONDS = 15

# Katalog logów w repo. Na mini PC można później przekierować do /var/log/tarzan.
TSP_REPO_ROOT = Path(__file__).resolve().parents[2]
TSP_LOG_DIR = TSP_REPO_ROOT / "data" / "logi" / "tsp"
TSP_MAIN_LOG_FILE = TSP_LOG_DIR / "tsp.log"
