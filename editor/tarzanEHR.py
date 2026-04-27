from __future__ import annotations

# ======================================================================================
# TARZAN EHR — ENTRY POINT
# ======================================================================================
# Ten plik pełni rolę lekkiego entry pointu dla modułu UI.
# Cała logika Tkinter i okien znajduje się w editor/EHR/tarzanEhrUi.py.

import sys
from pathlib import Path

# --- KONFIGURACJA PROFILERA ---
ENABLE_EHR_PROFILER = 0
EHR_PROFILER_INTERVAL_S = 2.0
EHR_PROFILER_TOP_N = 12

if ENABLE_EHR_PROFILER:
    try:
        from core.tarzanProfiler import clear_profiler, enable_profiler, start_profiler_reporting
        enable_profiler(True)
        clear_profiler()
        start_profiler_reporting(interval_s=EHR_PROFILER_INTERVAL_S, top_n=EHR_PROFILER_TOP_N)
    except Exception:
        pass

# --- IMPORTY UI ---
try:
    from editor.EHR.tarzanEhrUi import main as ui_main
except ImportError:
    # W razie problemów ze ścieżkami, gdyby ktoś odpalał inaczej
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))
    from editor.EHR.tarzanEhrUi import main as ui_main

def main() -> None:
    ui_main()

if __name__ == "__main__":
    main()

