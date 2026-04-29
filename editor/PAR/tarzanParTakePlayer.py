"""Odtwarzacz TAKE TXT dla PAR/SignalBus."""
from __future__ import annotations

import csv
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
from core.tarzanSignalBus import TarzanSignalBus
from editor.PAR.tarzanParProtocolMapper import TarzanParProtocolMapper


@dataclass
class TarzanTakeData:
    path: str
    header: Dict[str, str] = field(default_factory=dict)
    axes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, str]] = field(default_factory=list)

    @property
    def duration_ms(self) -> int:
        try:
            return int(self.header.get("DURATION_MS", "0"))
        except Exception:
            return 0


class TarzanParTakePlayer:
    def __init__(self, bus: TarzanSignalBus, mapper: TarzanParProtocolMapper) -> None:
        self.bus = bus
        self.mapper = mapper
        self.take: Optional[TarzanTakeData] = None
        self.index = 0
        self.playing = False
        self.loop = False
        self.speed = 1.0
        self.on_row: Optional[Callable[[Dict[str, str]], None]] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def load(self, path: str | Path) -> TarzanTakeData:
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        take = TarzanTakeData(path=str(path))
        current_axis: Optional[str] = None
        in_protocol = False
        protocol_lines: List[str] = []

        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if line == "[PROTOCOL]":
                in_protocol = True
                current_axis = None
                continue
            if in_protocol:
                protocol_lines.append(line)
                continue
            if line.startswith("DURATION_MS="):
                take.header["DURATION_MS"] = line.split("=", 1)[1]
                continue
            if line.startswith("[AXIS]"):
                spec = line.replace("[AXIS]", "", 1)
                parts = spec.split("|", 1)
                current_axis = parts[0].strip()
                take.axes[current_axis] = {"label": parts[1].strip() if len(parts) > 1 else current_axis, "nodes": []}
                continue
            if current_axis and line.startswith("NODE|"):
                _, t, v = line.split("|", 2)
                take.axes[current_axis]["nodes"].append((int(float(t)), float(v)))
                continue
            if current_axis and line.startswith("RELEASE_MS="):
                take.axes[current_axis]["release_ms"] = int(float(line.split("=", 1)[1]))
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                take.header[k] = v

        if protocol_lines:
            reader = csv.DictReader(protocol_lines, delimiter=";")
            take.columns = list(reader.fieldnames or [])
            take.rows = [dict(row) for row in reader]

        self.take = take
        self.index = 0
        self.bus.loaded_take_path = str(path)
        self.bus.log("TAKE", f"Załadowano TAKE: {path.name}, rows={len(take.rows)}, duration={take.duration_ms} ms")
        return take

    def unload(self) -> None:
        self.stop()
        self.take = None
        self.index = 0
        self.bus.loaded_take_path = None
        self.bus.log("TAKE", "Odłączono TAKE")

    def step_to_index(self, index: int) -> Optional[Dict[str, str]]:
        if not self.take or not self.take.rows:
            return None
        self.index = max(0, min(index, len(self.take.rows) - 1))
        row = self.take.rows[self.index]
        self.apply_row(row)
        return row

    def step_time(self, time_ms: int) -> Optional[Dict[str, str]]:
        if not self.take or not self.take.rows:
            return None
        idx = int(round(time_ms / max(1, CZAS_PROBKOWANIA_MS)))
        return self.step_to_index(idx)

    def apply_row(self, row: Dict[str, str]) -> None:
        time_ms = self._row_time(row)
        self.bus.set_take_time(time_ms)
        mapped = self.mapper.map_row(row)
        self.bus.write_many_outputs(mapped, source="TAKE", time_ms=time_ms)
        if self.on_row:
            self.on_row(row)

    def play(self) -> None:
        if not self.take or not self.take.rows or self.playing:
            return
        self.playing = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.bus.log("TAKE", "PLAY")

    def pause(self) -> None:
        self.playing = False
        self._stop_event.set()
        self.bus.log("TAKE", "PAUSE")

    def stop(self) -> None:
        self.playing = False
        self._stop_event.set()
        self.index = 0
        self.bus.log("TAKE", "STOP")

    def _run(self) -> None:
        sample_s = max(0.001, CZAS_PROBKOWANIA_MS / 1000.0 / max(0.01, self.speed))
        while self.playing and self.take and self.take.rows and not self._stop_event.is_set():
            if self.index >= len(self.take.rows):
                if self.loop:
                    self.index = 0
                else:
                    self.playing = False
                    break
            row = self.take.rows[self.index]
            self.apply_row(row)
            self.index += 1
            time.sleep(sample_s)

    def _row_time(self, row: Dict[str, str]) -> int:
        try:
            return int(float(row.get("TIME_MS", 0)))
        except Exception:
            return 0
