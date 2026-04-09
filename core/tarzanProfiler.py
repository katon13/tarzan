# -*- coding: utf-8 -*-
"""
TARZAN - lekki profiler runtime do diagnostyki spowolnień.

Cel:
- pokazać które metody i bloki kodu najbardziej obciążają działający skrypt
- działać bez zmiany logiki projektu
- wypisywać czytelny raport do konsoli / terminala

Mierzy:
- czas ścienny (wall time)
- czas CPU procesu w wątku wywołania
- liczbę wywołań
- średni czas
- max czas
- ostatni czas

Użycie:
1) Oznacz metodę dekoratorem:
    from core.tarzanProfiler import profile_method

    @profile_method()
    def moja_metoda(...):
        ...

2) Albo mierz blok:
    from core.tarzanProfiler import profile_block

    with profile_block("EHR.refresh_protocol_preview"):
        self._refresh_protocol_preview()

3) Włącz raport okresowy:
    from core.tarzanProfiler import start_profiler_reporting
    start_profiler_reporting(interval_s=2.0, top_n=12)

4) Raport końcowy:
    from core.tarzanProfiler import print_profiler_report
    print_profiler_report()
"""

from __future__ import annotations

import atexit
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Dict, Optional


@dataclass
class _Stat:
    name: str
    calls: int = 0
    total_wall_s: float = 0.0
    total_cpu_s: float = 0.0
    max_wall_s: float = 0.0
    max_cpu_s: float = 0.0
    last_wall_s: float = 0.0
    last_cpu_s: float = 0.0

    @property
    def avg_wall_s(self) -> float:
        return self.total_wall_s / self.calls if self.calls else 0.0

    @property
    def avg_cpu_s(self) -> float:
        return self.total_cpu_s / self.calls if self.calls else 0.0


class TarzanProfiler:
    def __init__(self) -> None:
        self._stats: Dict[str, _Stat] = {}
        self._lock = threading.RLock()
        self._enabled = False
        self._report_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._report_interval_s = 2.0
        self._report_top_n = 12
        self._print_fn: Callable[[str], None] = print
        self._start_wall = time.perf_counter()
        self._start_cpu = time.process_time()

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = enabled

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def set_print_function(self, print_fn: Callable[[str], None]) -> None:
        with self._lock:
            self._print_fn = print_fn

    def record(self, name: str, wall_s: float, cpu_s: float) -> None:
        if not self.is_enabled():
            return
        with self._lock:
            stat = self._stats.get(name)
            if stat is None:
                stat = _Stat(name=name)
                self._stats[name] = stat

            stat.calls += 1
            stat.total_wall_s += wall_s
            stat.total_cpu_s += cpu_s
            stat.last_wall_s = wall_s
            stat.last_cpu_s = cpu_s
            if wall_s > stat.max_wall_s:
                stat.max_wall_s = wall_s
            if cpu_s > stat.max_cpu_s:
                stat.max_cpu_s = cpu_s

    def snapshot(self) -> Dict[str, _Stat]:
        with self._lock:
            return {
                name: _Stat(
                    name=s.name,
                    calls=s.calls,
                    total_wall_s=s.total_wall_s,
                    total_cpu_s=s.total_cpu_s,
                    max_wall_s=s.max_wall_s,
                    max_cpu_s=s.max_cpu_s,
                    last_wall_s=s.last_wall_s,
                    last_cpu_s=s.last_cpu_s,
                )
                for name, s in self._stats.items()
            }

    def clear(self) -> None:
        with self._lock:
            self._stats.clear()
            self._start_wall = time.perf_counter()
            self._start_cpu = time.process_time()

    def format_report(self, top_n: int = 12, sort_by: str = "total_wall") -> str:
        stats = list(self.snapshot().values())

        if sort_by == "total_cpu":
            stats.sort(key=lambda s: s.total_cpu_s, reverse=True)
        elif sort_by == "avg_wall":
            stats.sort(key=lambda s: s.avg_wall_s, reverse=True)
        elif sort_by == "avg_cpu":
            stats.sort(key=lambda s: s.avg_cpu_s, reverse=True)
        elif sort_by == "max_wall":
            stats.sort(key=lambda s: s.max_wall_s, reverse=True)
        elif sort_by == "max_cpu":
            stats.sort(key=lambda s: s.max_cpu_s, reverse=True)
        else:
            stats.sort(key=lambda s: s.total_wall_s, reverse=True)

        uptime_wall = time.perf_counter() - self._start_wall
        uptime_cpu = time.process_time() - self._start_cpu

        lines = []
        lines.append("")
        lines.append("=" * 118)
        lines.append("TARZAN PROFILER REPORT")
        lines.append(
            f"UPTIME wall={uptime_wall:9.3f}s | cpu={uptime_cpu:9.3f}s | items={len(stats)}"
        )
        lines.append("-" * 118)
        lines.append(
            f"{'LP':>3} | {'NAZWA':<42} | {'CALLS':>7} | {'TOTAL WALL ms':>13} | {'TOTAL CPU ms':>12} | "
            f"{'AVG WALL ms':>11} | {'MAX WALL ms':>11} | {'LAST WALL ms':>12}"
        )
        lines.append("-" * 118)

        for index, s in enumerate(stats[:top_n], start=1):
            lines.append(
                f"{index:>3} | "
                f"{s.name[:42]:<42} | "
                f"{s.calls:>7} | "
                f"{s.total_wall_s * 1000:>13.3f} | "
                f"{s.total_cpu_s * 1000:>12.3f} | "
                f"{s.avg_wall_s * 1000:>11.3f} | "
                f"{s.max_wall_s * 1000:>11.3f} | "
                f"{s.last_wall_s * 1000:>12.3f}"
            )

        lines.append("=" * 118)
        return "\n".join(lines)

    def print_report(self, top_n: int = 12, sort_by: str = "total_wall") -> None:
        report = self.format_report(top_n=top_n, sort_by=sort_by)
        with self._lock:
            self._print_fn(report)

    def start_reporting(self, interval_s: float = 2.0, top_n: int = 12) -> None:
        with self._lock:
            self._report_interval_s = max(0.25, float(interval_s))
            self._report_top_n = max(1, int(top_n))

            if self._report_thread and self._report_thread.is_alive():
                return

            self._stop_event.clear()
            self._report_thread = threading.Thread(
                target=self._report_loop,
                name="TarzanProfilerReporter",
                daemon=True,
            )
            self._report_thread.start()

    def stop_reporting(self) -> None:
        self._stop_event.set()

    def _report_loop(self) -> None:
        while not self._stop_event.wait(self._report_interval_s):
            try:
                self.print_report(top_n=self._report_top_n, sort_by="total_wall")
            except Exception as exc:
                try:
                    self._print_fn(f"[TARZAN PROFILER] report error: {exc}")
                except Exception:
                    pass


_PROFILER = TarzanProfiler()


def get_profiler() -> TarzanProfiler:
    return _PROFILER


def enable_profiler(enabled: bool = True) -> None:
    _PROFILER.set_enabled(enabled)


def set_profiler_print(print_fn: Callable[[str], None]) -> None:
    _PROFILER.set_print_function(print_fn)


def clear_profiler() -> None:
    _PROFILER.clear()


def print_profiler_report(top_n: int = 12, sort_by: str = "total_wall") -> None:
    _PROFILER.print_report(top_n=top_n, sort_by=sort_by)


def start_profiler_reporting(interval_s: float = 2.0, top_n: int = 12) -> None:
    _PROFILER.start_reporting(interval_s=interval_s, top_n=top_n)


def stop_profiler_reporting() -> None:
    _PROFILER.stop_reporting()


def profile_method(name: Optional[str] = None):
    def decorator(func):
        metric_name = name or func.__qualname__

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _PROFILER.is_enabled():
                return func(*args, **kwargs)

            start_wall = time.perf_counter()
            start_cpu = time.process_time()
            try:
                return func(*args, **kwargs)
            finally:
                end_wall = time.perf_counter()
                end_cpu = time.process_time()
                _PROFILER.record(
                    metric_name,
                    wall_s=end_wall - start_wall,
                    cpu_s=end_cpu - start_cpu,
                )

        return wrapper

    return decorator


@contextmanager
def profile_block(name: str):
    if not _PROFILER.is_enabled():
        yield
        return

    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    try:
        yield
    finally:
        end_wall = time.perf_counter()
        end_cpu = time.process_time()
        _PROFILER.record(
            name,
            wall_s=end_wall - start_wall,
            cpu_s=end_cpu - start_cpu,
        )


@atexit.register
def _print_report_on_exit() -> None:
    try:
        if _PROFILER.is_enabled():
            _PROFILER.print_report(top_n=20, sort_by="total_wall")
    except Exception:
        pass