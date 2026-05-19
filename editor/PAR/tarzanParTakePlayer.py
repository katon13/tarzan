"""Odtwarzacz TAKE TXT dla PAR/SignalBus.

Zasada bezpieczeństwa PAR:
- brak threading.Thread w odtwarzaniu TAKE,
- PLAY działa przez Tkinter app.after(CZAS_PROBKOWANIA_MS),
- SignalBus.notify() i aktualizacje paneli Tkinter zostają w głównym wątku UI.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
from core.tarzanSignalBus import TarzanSignalBus
try:
    from editor.PAR.tarzanParProtocolMapper import TarzanParProtocolMapper
except ModuleNotFoundError:
    from tarzanParProtocolMapper import TarzanParProtocolMapper


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

        # Scheduler Tkintera podawany przez TarzanParApp/Bridge.
        # Nie używać wątków: SignalBus.notify() dochodzi do Tkinter UI.
        self._after: Optional[Callable[..., Any]] = None
        self._after_cancel: Optional[Callable[[Any], Any]] = None
        self._after_id: Any = None

    def set_scheduler(self, after: Callable[..., Any], after_cancel: Callable[[Any], Any]) -> None:
        self._after = after
        self._after_cancel = after_cancel

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

        self.stop(reset_to_zero=False, log_stop=False)
        self.take = take
        self.index = 0
        self.bus.loaded_take_path = str(path)
        # Numer i wersja TAKE muszą przejść przez BUS, bo Snajper odpala cele
        # fizycznego Nextiona z fire_from_signal(...), bez ręcznego sync.
        self.bus.force_signal("take_number", path.name, source="TAKE_LOAD")
        self.bus.force_signal("loaded_take_path", str(path), source="TAKE_LOAD")
        self.bus.force_signal("take_status", "LOADED", source="TAKE_LOAD")
        self.bus.set_take_time(0)
        self.bus.log("TAKE", f"Załadowano TAKE: {path.name}, rows={len(take.rows)}, duration={take.duration_ms} ms")
        return take

    def unload(self) -> None:
        self.stop(reset_to_zero=False)
        self.take = None
        self.index = 0
        self.bus.loaded_take_path = None
        self.bus.force_signal("take_number", "BRAK", source="TAKE_UNLOAD")
        self.bus.force_signal("loaded_take_path", "", source="TAKE_UNLOAD")
        self.bus.force_signal("take_status", "EMPTY", source="TAKE_UNLOAD")
        self.bus.set_take_time(0)
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
        if self._after is None:
            self.bus.log("TAKE", "PLAY zablokowany: brak app.after()")
            return
        self.playing = True
        self.bus.force_signal("take_status", "PLAY", source="TAKE_PLAY")
        self.bus.log("TAKE", "PLAY")
        self._schedule_next(delay_ms=0)

    def pause(self) -> None:
        if not self.playing:
            return
        self.playing = False
        self._cancel_after()
        self.bus.force_signal("take_status", "PAUSE", source="TAKE_PAUSE")
        self.bus.log("TAKE", "PAUSE")

    def stop(self, *, reset_to_zero: bool = True, log_stop: bool = True) -> None:
        self.playing = False
        self._cancel_after()
        self.index = 0
        if reset_to_zero and self.take and self.take.rows:
            self.apply_row(self.take.rows[0])
        if log_stop:
            self.bus.log("TAKE", "STOP")

    def _schedule_next(self, delay_ms: Optional[int] = None) -> None:
        if not self.playing or self._after is None:
            return
        delay = self._sample_delay_ms() if delay_ms is None else max(0, int(delay_ms))
        self._after_id = self._after(delay, self._tick)

    def _cancel_after(self) -> None:
        if self._after_id is not None and self._after_cancel is not None:
            try:
                self._after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def _tick(self) -> None:
        self._after_id = None
        if not self.playing or not self.take or not self.take.rows:
            return
        if self.index >= len(self.take.rows):
            if self.loop:
                self.index = 0
            else:
                self.playing = False
                self.bus.force_signal("take_status", "END", source="TAKE_END")
                self.bus.log("TAKE", "KONIEC")
                return
        row = self.take.rows[self.index]
        self.apply_row(row)
        self.index += 1
        self._schedule_next()

    def _sample_delay_ms(self) -> int:
        try:
            speed = max(0.01, float(self.speed))
        except Exception:
            speed = 1.0
        return max(1, int(round(CZAS_PROBKOWANIA_MS / speed)))

    def _row_time(self, row: Dict[str, str]) -> int:
        try:
            return int(float(row.get("TIME_MS", 0)))
        except Exception:
            return 0
