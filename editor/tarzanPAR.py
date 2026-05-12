"""
TARZAN PAR — Pulpit Anatomii Ruchu.
Entry zgodny z projektem: python editor/tarzanPAR.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# PROFILER PAR
# Domyślnie włączony, bo PAR jest symulatorem I/O i musi pokazywać, co obciąża UI.
# Wyłączenie awaryjne: set TARZAN_PAR_PROFILER=0
ENABLE_EHR_PROFILER = os.environ.get("TARZAN_PAR_PROFILER", "1") not in {"0", "false", "False", "NO", "no"}
EHR_PROFILER_INTERVAL_S = float(os.environ.get("TARZAN_PAR_PROFILER_INTERVAL_S", "2.0"))
EHR_PROFILER_TOP_N = int(os.environ.get("TARZAN_PAR_PROFILER_TOP_N", "20"))

if ENABLE_EHR_PROFILER:
    try:
        from core.tarzanProfiler import clear_profiler, enable_profiler, start_profiler_reporting
        enable_profiler(1)
        clear_profiler()
        start_profiler_reporting(interval_s=EHR_PROFILER_INTERVAL_S, top_n=EHR_PROFILER_TOP_N)
    except Exception:
        pass

try:
    from editor.PAR.tarzanParApp import TarzanParApp
except ModuleNotFoundError:
    # Twardy fallback dla uruchamiania bez poprawnego PYTHONPATH / po ręcznej podmianie plików.
    PAR_DIR = Path(__file__).resolve().parent / "PAR"
    if str(PAR_DIR) not in sys.path:
        sys.path.insert(0, str(PAR_DIR))
    from tarzanParApp import TarzanParApp


def launch_par() -> None:
    app = TarzanParApp()
    app.mainloop()


if __name__ == "__main__":
    launch_par()
