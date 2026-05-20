"""
TARZAN PAR — Pulpit Anatomii Ruchu.
Entry zgodny z projektem: python editor/tarzanPAR.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent

# Czyścimy sys.path, aby uniknąć kolizji modułu 'editor' z folderem 'editor/editor'
sys.path = [p for p in sys.path if p not in {str(ROOT_DIR), str(SCRIPT_DIR)}]
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
        enable_profiler(0)
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
    # START SERWERA TFD DLA OBS OVERLAY
    print("TFD Overlay Server: Initializing...")
    try:
        # Próbujemy różnych wariantów importu ze względu na specyficzną strukturę folderów
        start_tfd_server = None
        
        # 1. Próba standardowa (z ROOT_DIR w sys.path)
        try:
            from editor.TFD.tarzanTfdOverlayServer import start_tfd_server
        except (ModuleNotFoundError, ImportError):
            pass
            
        # 2. Próba z SCRIPT_DIR/TFD
        if not start_tfd_server:
            try:
                tfd_path = str(SCRIPT_DIR / "TFD")
                if tfd_path not in sys.path:
                    sys.path.insert(0, tfd_path)
                from tarzanTfdOverlayServer import start_tfd_server
            except (ModuleNotFoundError, ImportError):
                pass
                
        # 3. Próba z editor.TFD (bezpośrednio)
        if not start_tfd_server:
            try:
                from TFD.tarzanTfdOverlayServer import start_tfd_server
            except (ModuleNotFoundError, ImportError):
                pass

        if start_tfd_server:
            start_tfd_server()
            print("TFD Overlay Server: STARTED (http://127.0.0.1:8765/tfd)")
        else:
            print("CRITICAL ERROR: Could not find TFD Overlay Server module (editor.TFD.tarzanTfdOverlayServer)")
            
    except Exception as e:
        print(f"CRITICAL WARNING: Could not start TFD Overlay Server: {e}")
        import traceback
        traceback.print_exc()

    app = TarzanParApp()
    app.mainloop()


if __name__ == "__main__":
    launch_par()
