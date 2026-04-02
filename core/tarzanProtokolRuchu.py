from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
from core.tarzanZmienneSygnalowe import WSZYSTKIE_SYGNALY


@dataclass
class TarzanProtokolNaglowek:
    """
    Nagłówek pliku protokołu ruchu TARZANA.
    """
    take_id: str
    version: str
    title: str
    time_unit: str
    sample_step_ms: int
    active_mode: str


class TarzanProtokolRuchu:
    """
    Protokół ruchu TARZANA.

    Założenie architektoniczne:
    protokół ma docelowo nieść pełny pakiet danych systemu,
    a nie tylko STEP/DIR/ENABLE jednej osi.

    Ta wersja:
    - zapisuje warstwę ruchu osi z globalnego timeline,
    - zapisuje aktywny tryb,
    - zapisuje zdarzenia TAKE,
    - niesie pełną listę znanych sygnałów z mapy sygnałowej
      jako szkielet pod dalsze mapowanie sprzętowe.
    """

    def __init__(self, sample_step_ms: int = CZAS_PROBKOWANIA_MS) -> None:
        self.sample_step_ms = sample_step_ms

    def build_header(self, take) -> TarzanProtokolNaglowek:
        active_mode = getattr(take.source, "record_mode", "") or "UNKNOWN"

        return TarzanProtokolNaglowek(
            take_id=take.metadata.take_id,
            version=take.metadata.version,
            title=take.metadata.title,
            time_unit=take.timeline.time_unit,
            sample_step_ms=self.sample_step_ms,
            active_mode=active_mode,
        )

    def build_protocol_rows(
        self,
        take,
        global_timeline: Dict[int, Dict[str, Dict[str, int | str]]],
    ) -> List[Dict[str, int | float | str]]:
        """
        Buduje wiersze protokołu z globalnego timeline.

        Każdy wiersz niesie:
        - czas
        - identyfikację TAKE
        - aktywny tryb
        - zdarzenia
        - stan osi
        - pełny pakiet nazw sygnałów systemu
        """
        axis_order = list(take.axes.keys())
        signal_template = self._build_signal_template()
        event_map = self._build_event_map(take)

        rows: List[Dict[str, int | float | str]] = []

        for time_ms in sorted(global_timeline.keys()):
            axes_state = global_timeline[time_ms]

            row: Dict[str, int | float | str] = {
                "TIME_MS": time_ms,
                "TAKE_ID": take.metadata.take_id,
                "VERSION": take.metadata.version,
                "ACTIVE_MODE": getattr(take.source, "record_mode", "") or "UNKNOWN",
                "EVENT_DRONE_RELEASE": event_map.get(time_ms, {}).get("drone_release", 0),
            }

            self._inject_motion_state(
                row=row,
                axis_order=axis_order,
                axes_state=axes_state,
            )

            self._inject_signal_template(
                row=row,
                signal_template=signal_template,
            )

            rows.append(row)

        return rows

    def export_txt(
        self,
        take,
        global_timeline: Dict[int, Dict[str, Dict[str, int | str]]],
        file_path: str | Path,
    ) -> Path:
        """
        Eksportuje protokół do pliku TXT.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        header = self.build_header(take)
        rows = self.build_protocol_rows(take, global_timeline)
        axis_order = list(take.axes.keys())
        signal_names = list(WSZYSTKIE_SYGNALY.keys())

        columns = self._build_column_order(
            axis_order=axis_order,
            signal_names=signal_names,
        )

        with path.open("w", encoding="utf-8") as file:
            file.write("=== TARZAN PROTOKÓŁ RUCHU ===\n")
            file.write(f"TAKE_ID={header.take_id}\n")
            file.write(f"VERSION={header.version}\n")
            file.write(f"TITLE={header.title}\n")
            file.write(f"TIME_UNIT={header.time_unit}\n")
            file.write(f"SAMPLE_STEP_MS={header.sample_step_ms}\n")
            file.write(f"ACTIVE_MODE={header.active_mode}\n")
            file.write(f"SIGNAL_COUNT={len(signal_names)}\n")
            file.write("\n")

            file.write(";".join(columns) + "\n")

            for row in rows:
                values = [str(row.get(column, "")) for column in columns]
                file.write(";".join(values) + "\n")

        return path

    def _build_event_map(self, take) -> Dict[int, Dict[str, int]]:
        """
        Buduje prostą mapę zdarzeń po czasie.
        """
        event_map: Dict[int, Dict[str, int]] = {}

        for event in getattr(take, "events", []):
            if not getattr(event, "enabled", True):
                continue

            event_time = int(event.event_time)
            event_type = str(event.event_type)

            if event_time not in event_map:
                event_map[event_time] = {}

            if event_type == "drone_release":
                event_map[event_time]["drone_release"] = 1

        return event_map

    def _build_signal_template(self) -> Dict[str, int | float | str]:
        """
        Buduje szkielet pełnego pakietu sygnałów systemu.

        Uwaga:
        Na tym etapie większość sygnałów nie jest jeszcze mapowana
        z wykonaniem ruchu i pozostaje w stanie domyślnym / pustym.
        To jest celowy etap architektoniczny przygotowujący pełny protokół.
        """
        template: Dict[str, int | float | str] = {}

        for signal_name, signal in WSZYSTKIE_SYGNALY.items():
            template[f"SIGNAL__{signal_name}"] = self._normalize_default_value(signal.default)

        return template

    def _normalize_default_value(self, default_value: str) -> int | float | str:
        value = str(default_value).strip()

        if value == "1":
            return 1

        if value == "0":
            return 0

        if value in {"~", "brak", "1010...", ""}:
            return ""

        return value

    def _inject_motion_state(
        self,
        row: Dict[str, int | float | str],
        axis_order: List[str],
        axes_state: Dict[str, Dict[str, int | str]],
    ) -> None:
        for axis_key in axis_order:
            axis_signals = axes_state.get(axis_key)

            if axis_signals is None:
                row[f"MOTION__{axis_key}__STEP_COUNT"] = 0
                row[f"MOTION__{axis_key}__STEP"] = 0
                row[f"MOTION__{axis_key}__DIR"] = 0
                row[f"MOTION__{axis_key}__ENABLE"] = 0
                continue

            row[f"MOTION__{axis_key}__STEP_COUNT"] = int(axis_signals["STEP_COUNT"])
            row[f"MOTION__{axis_key}__STEP"] = int(axis_signals["STEP"])
            row[f"MOTION__{axis_key}__DIR"] = int(axis_signals["DIR"])
            row[f"MOTION__{axis_key}__ENABLE"] = int(axis_signals["ENABLE"])

    def _inject_signal_template(
        self,
        row: Dict[str, int | float | str],
        signal_template: Dict[str, int | float | str],
    ) -> None:
        row.update(signal_template)

    def _build_column_order(
        self,
        axis_order: List[str],
        signal_names: List[str],
    ) -> List[str]:
        columns: List[str] = [
            "TIME_MS",
            "TAKE_ID",
            "VERSION",
            "ACTIVE_MODE",
            "EVENT_DRONE_RELEASE",
        ]

        for axis_key in axis_order:
            columns.extend(
                [
                    f"MOTION__{axis_key}__STEP_COUNT",
                    f"MOTION__{axis_key}__STEP",
                    f"MOTION__{axis_key}__DIR",
                    f"MOTION__{axis_key}__ENABLE",
                ]
            )

        for signal_name in signal_names:
            columns.append(f"SIGNAL__{signal_name}")

        return columns