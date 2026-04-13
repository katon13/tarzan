from __future__ import annotations

ENABLE_EHR_PROFILER = True
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

from editor.EHR.tarzanEhrApp import main


if __name__ == "__main__":
    main()
