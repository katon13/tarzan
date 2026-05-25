"""
Logi, statystyki i ring buffer dla TSP.

FAST nie jest zapisywany pakiet po pakiecie do pliku. Do debugowania służą:
- statystyki,
- ring buffer w RAM,
- snapshot na żądanie,
- trace wybranego sygnału.
"""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Deque, Dict, Iterable, Optional

from .tarzanTspConfig import (
    TSP_MAIN_LOG_FILE,
    TSP_RING_ERROR_SIZE,
    TSP_RING_RX_SIZE,
    TSP_RING_TX_SIZE,
)
from .tarzanTspProtocol import now_ms


class TarzanTspRingBuffer:
    def __init__(self, maxlen: int) -> None:
        self._items: Deque[Dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = Lock()

    def append(self, item: Dict[str, Any]) -> None:
        with self._lock:
            self._items.append(dict(item))

    def snapshot(self) -> list[Dict[str, Any]]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


@dataclass
class TarzanTspStats:
    packets_tx: int = 0
    packets_rx: int = 0
    bytes_tx: int = 0
    bytes_rx: int = 0
    errors: int = 0
    dropped: int = 0
    lane_packets: Dict[str, int] = field(default_factory=dict)
    lane_signals: Dict[str, int] = field(default_factory=dict)

    def on_tx(self, lane: str, size: int, signal_count: int = 0) -> None:
        self.packets_tx += 1
        self.bytes_tx += size
        self.lane_packets[lane] = self.lane_packets.get(lane, 0) + 1
        if signal_count:
            self.lane_signals[lane] = self.lane_signals.get(lane, 0) + signal_count

    def on_rx(self, size: int) -> None:
        self.packets_rx += 1
        self.bytes_rx += size

    def on_error(self) -> None:
        self.errors += 1

    def as_dict(self) -> Dict[str, Any]:
        return {
            "packets_tx": self.packets_tx,
            "packets_rx": self.packets_rx,
            "bytes_tx": self.bytes_tx,
            "bytes_rx": self.bytes_rx,
            "errors": self.errors,
            "dropped": self.dropped,
            "lane_packets": dict(self.lane_packets),
            "lane_signals": dict(self.lane_signals),
        }


class TarzanTspDebug:
    def __init__(self) -> None:
        self.rx = TarzanTspRingBuffer(TSP_RING_RX_SIZE)
        self.tx = TarzanTspRingBuffer(TSP_RING_TX_SIZE)
        self.errors = TarzanTspRingBuffer(TSP_RING_ERROR_SIZE)
        self.stats = TarzanTspStats()
        self._lock = Lock()

    def record_rx(self, message: Dict[str, Any], size: int = 0) -> None:
        self.rx.append({"ts": now_ms(), "message": message})
        with self._lock:
            self.stats.on_rx(size)

    def record_tx(self, message: Dict[str, Any], size: int = 0) -> None:
        lane = str(message.get("lane") or message.get("event") or message.get("cmd") or "cmd")
        signal_count = 0
        values = message.get("values")
        if isinstance(values, dict):
            signal_count = len(values)
        self.tx.append({"ts": now_ms(), "message": message})
        with self._lock:
            self.stats.on_tx(lane, size, signal_count)

    def record_error(self, error: str, context: Optional[Dict[str, Any]] = None) -> None:
        item = {"ts": now_ms(), "error": error}
        if context:
            item["context"] = context
        self.errors.append(item)
        with self._lock:
            self.stats.on_error()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            stats = self.stats.as_dict()
        return {
            "created_ts": now_ms(),
            "stats": stats,
            "rx": self.rx.snapshot(),
            "tx": self.tx.snapshot(),
            "errors": self.errors.snapshot(),
        }

    def dump_snapshot(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = directory / f"tsp_debug_snapshot_{stamp}.jsonl"
        snapshot = self.snapshot()
        with path.open("w", encoding="utf-8") as f:
            for section in ("stats", "rx", "tx", "errors"):
                f.write(json.dumps({"section": section, "data": snapshot[section]}, ensure_ascii=False) + "\n")
        return path


def setup_tsp_logger(name: str = "TSP") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    TSP_MAIN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(TSP_MAIN_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
