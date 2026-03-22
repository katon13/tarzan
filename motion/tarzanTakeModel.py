"""
tarzanTakeModel.py

Podstawowy model danych TAKE dla systemu TARZAN.
Zawiera klasy dataclass zgodne z dokumentacją:
- format pliku TAKE
- model klas Python dla edytora choreografii ruchu

Wersja początkowa:
- przechowywanie danych
- zapis do JSON
- odczyt z JSON
- podstawowa walidacja struktury
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class TarzanTakeMetadata:
    take_id: str
    version: str
    title: str
    author: str
    created_at: str
    edited_at: str
    description: str = ""
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanTakeMetadata":
        return cls(
            take_id=data["take_id"],
            version=data["version"],
            title=data["title"],
            author=data["author"],
            created_at=data["created_at"],
            edited_at=data["edited_at"],
            description=data.get("description", ""),
            notes=data.get("notes", ""),
        )


@dataclass
class TarzanTimeline:
    time_unit: str = "ms"
    sample_step: int = 10
    take_start: int = 0
    take_end: int = 0
    take_duration: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanTimeline":
        return cls(
            time_unit=data.get("time_unit", "ms"),
            sample_step=int(data.get("sample_step", 10)),
            take_start=int(data.get("take_start", 0)),
            take_end=int(data.get("take_end", 0)),
            take_duration=int(data.get("take_duration", 0)),
        )


@dataclass
class TarzanSegment:
    segment_id: str
    start_time: int
    end_time: int
    direction: int
    pulse_count: int
    is_pause: bool = False
    is_direction_change: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanSegment":
        return cls(
            segment_id=data["segment_id"],
            start_time=int(data["start_time"]),
            end_time=int(data["end_time"]),
            direction=int(data["direction"]),
            pulse_count=int(data["pulse_count"]),
            is_pause=bool(data.get("is_pause", False)),
            is_direction_change=bool(data.get("is_direction_change", False)),
        )


@dataclass
class TarzanControlPoint:
    time: int
    amplitude: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanControlPoint":
        return cls(
            time=int(data["time"]),
            amplitude=float(data["amplitude"]),
        )


@dataclass
class TarzanCurve:
    curve_type: str = "motion_intensity"
    interpolation: str = "spline"
    preserve_distance: bool = True
    ghost_enabled: bool = True
    control_points: list[TarzanControlPoint] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanCurve":
        return cls(
            curve_type=data.get("curve_type", "motion_intensity"),
            interpolation=data.get("interpolation", "spline"),
            preserve_distance=bool(data.get("preserve_distance", True)),
            ghost_enabled=bool(data.get("ghost_enabled", True)),
            control_points=[
                TarzanControlPoint.from_dict(point)
                for point in data.get("control_points", [])
            ],
        )


@dataclass
class TarzanEvent:
    event_id: str
    event_type: str
    event_time: int
    enabled: bool = True
    note: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanEvent":
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            event_time=int(data["event_time"]),
            enabled=bool(data.get("enabled", True)),
            note=data.get("note", ""),
        )


@dataclass
class TarzanSourceInfo:
    record_mode: str = "tREC"
    source_protocol_file: str = ""
    source_notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanSourceInfo":
        return cls(
            record_mode=data.get("record_mode", "tREC"),
            source_protocol_file=data.get("source_protocol_file", ""),
            source_notes=data.get("source_notes", ""),
        )


@dataclass
class TarzanValidation:
    status: str = "unknown"
    checked_at: str = ""
    max_speed_ok: bool = False
    max_acceleration_ok: bool = False
    start_zero_ok: bool = False
    end_zero_ok: bool = False
    direction_change_ok: bool = False
    events_ok: bool = False
    messages: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanValidation":
        return cls(
            status=data.get("status", "unknown"),
            checked_at=data.get("checked_at", ""),
            max_speed_ok=bool(data.get("max_speed_ok", False)),
            max_acceleration_ok=bool(data.get("max_acceleration_ok", False)),
            start_zero_ok=bool(data.get("start_zero_ok", False)),
            end_zero_ok=bool(data.get("end_zero_ok", False)),
            direction_change_ok=bool(data.get("direction_change_ok", False)),
            events_ok=bool(data.get("events_ok", False)),
            messages=list(data.get("messages", [])),
        )


@dataclass
class TarzanAxisTake:
    axis_name: str
    axis_enabled: bool
    mechanics_ref: str
    full_cycle_pulses: int
    min_full_cycle_time_s: float
    max_pulse_rate: int
    max_acceleration: int
    backlash_compensation: int
    start_must_be_zero: bool = True
    end_must_be_zero: bool = True
    raw_signal: dict[str, Any] = field(default_factory=dict)
    segments: list[TarzanSegment] = field(default_factory=list)
    curve: TarzanCurve = field(default_factory=TarzanCurve)
    generated_protocol: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanAxisTake":
        return cls(
            axis_name=data["axis_name"],
            axis_enabled=bool(data.get("axis_enabled", True)),
            mechanics_ref=data["mechanics_ref"],
            full_cycle_pulses=int(data["full_cycle_pulses"]),
            min_full_cycle_time_s=float(data["min_full_cycle_time_s"]),
            max_pulse_rate=int(data["max_pulse_rate"]),
            max_acceleration=int(data["max_acceleration"]),
            backlash_compensation=int(data.get("backlash_compensation", 0)),
            start_must_be_zero=bool(data.get("start_must_be_zero", True)),
            end_must_be_zero=bool(data.get("end_must_be_zero", True)),
            raw_signal=dict(data.get("raw_signal", {})),
            segments=[
                TarzanSegment.from_dict(segment)
                for segment in data.get("segments", [])
            ],
            curve=TarzanCurve.from_dict(data.get("curve", {})),
            generated_protocol=dict(data.get("generated_protocol", {})),
        )

    def total_pulses(self) -> int:
        return sum(segment.pulse_count for segment in self.segments)

    def validate_axis_basic(self) -> list[str]:
        errors: list[str] = []

        if self.full_cycle_pulses <= 0:
            errors.append(f"{self.axis_name}: full_cycle_pulses musi być > 0")

        if self.min_full_cycle_time_s <= 0:
            errors.append(f"{self.axis_name}: min_full_cycle_time_s musi być > 0")

        if self.max_pulse_rate <= 0:
            errors.append(f"{self.axis_name}: max_pulse_rate musi być > 0")

        if self.max_acceleration <= 0:
            errors.append(f"{self.axis_name}: max_acceleration musi być > 0")

        for segment in self.segments:
            if segment.end_time < segment.start_time:
                errors.append(
                    f"{self.axis_name}: segment {segment.segment_id} ma end_time < start_time"
                )

            if segment.direction not in (-1, 0, 1):
                errors.append(
                    f"{self.axis_name}: segment {segment.segment_id} ma nieprawidłowy direction"
                )

        return errors


@dataclass
class TarzanTake:
    metadata: TarzanTakeMetadata
    timeline: TarzanTimeline
    axes: dict[str, TarzanAxisTake] = field(default_factory=dict)
    events: list[TarzanEvent] = field(default_factory=list)
    simulation: dict[str, Any] = field(default_factory=dict)
    source: TarzanSourceInfo = field(default_factory=TarzanSourceInfo)
    validation: TarzanValidation = field(default_factory=TarzanValidation)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TarzanTake":
        axes_dict = {
            axis_key: TarzanAxisTake.from_dict(axis_data)
            for axis_key, axis_data in data.get("axes", {}).items()
        }

        return cls(
            metadata=TarzanTakeMetadata.from_dict(data["metadata"]),
            timeline=TarzanTimeline.from_dict(data["timeline"]),
            axes=axes_dict,
            events=[
                TarzanEvent.from_dict(event)
                for event in data.get("events", [])
            ],
            simulation=dict(data.get("simulation", {})),
            source=TarzanSourceInfo.from_dict(data.get("source", {})),
            validation=TarzanValidation.from_dict(data.get("validation", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save_json(self, file_path: str | Path, indent: int = 2) -> None:
        import json

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=indent)

    @classmethod
    def load_json(cls, file_path: str | Path) -> "TarzanTake":
        import json

        path = Path(file_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def validate_basic(self) -> list[str]:
        errors: list[str] = []

        if self.timeline.take_end < self.timeline.take_start:
            errors.append("timeline: take_end nie może być mniejsze od take_start")

        if self.timeline.take_duration < 0:
            errors.append("timeline: take_duration nie może być ujemne")

        if self.metadata.take_id.strip() == "":
            errors.append("metadata: take_id nie może być puste")

        if not self.axes:
            errors.append("take: brak osi w strukturze TAKE")

        for axis_key, axis_take in self.axes.items():
            axis_errors = axis_take.validate_axis_basic()
            errors.extend([f"{axis_key}: {msg}" for msg in axis_errors])

        for event in self.events:
            if event.event_time < self.timeline.take_start or event.event_time > self.timeline.take_end:
                errors.append(
                    f"event {event.event_id}: event_time jest poza zakresem TAKE"
                )

        return errors


def build_example_take() -> TarzanTake:
    """
    Tworzy przykładowy TAKE zgodny z dokumentacją projektu.
    Przydatne do pierwszych testów zapisu / odczytu.
    """
    return TarzanTake(
        metadata=TarzanTakeMetadata(
            take_id="TAKE_001",
            version="v01",
            title="Wejście aktora",
            author="Jacek Joniec",
            created_at="2026-03-21T18:30:00",
            edited_at="2026-03-21T19:12:00",
            description="Pierwsza wersja ruchu",
            notes="Wersja surowa",
        ),
        timeline=TarzanTimeline(
            time_unit="ms",
            sample_step=10,
            take_start=0,
            take_end=12840,
            take_duration=12840,
        ),
        axes={
            "camera_horizontal": TarzanAxisTake(
                axis_name="oś pozioma kamery",
                axis_enabled=True,
                mechanics_ref="tarzanCameraHorizontal",
                full_cycle_pulses=28800,
                min_full_cycle_time_s=4.0,
                max_pulse_rate=7200,
                max_acceleration=1800,
                backlash_compensation=24,
                raw_signal={
                    "source_take": "REC_2026_03_21_01",
                    "step_count_total": 8420,
                },
                segments=[
                    TarzanSegment(
                        segment_id="SEG_001",
                        start_time=0,
                        end_time=1850,
                        direction=1,
                        pulse_count=1240,
                        is_pause=False,
                        is_direction_change=False,
                    )
                ],
                curve=TarzanCurve(
                    curve_type="motion_intensity",
                    interpolation="spline",
                    preserve_distance=True,
                    ghost_enabled=True,
                    control_points=[
                        TarzanControlPoint(time=0, amplitude=0.0),
                        TarzanControlPoint(time=420, amplitude=0.35),
                        TarzanControlPoint(time=900, amplitude=0.72),
                        TarzanControlPoint(time=1450, amplitude=0.20),
                        TarzanControlPoint(time=1850, amplitude=0.0),
                    ],
                ),
                generated_protocol={
                    "export_file": "TAKE_001_v01_protocol.txt",
                    "step_count_total": 8420,
                    "validated": True,
                },
            )
        },
        events=[
            TarzanEvent(
                event_id="EV_001",
                event_type="drone_release",
                event_time=6240,
                enabled=True,
                note="Zwolnienie elektromagnesu",
            )
        ],
        simulation={
            "playhead_start": 0,
            "playhead_last_position": 4120,
            "zoom_level": 1.5,
            "ghost_visible": True,
            "show_all_axes": True,
        },
        source=TarzanSourceInfo(
            record_mode="tREC",
            source_protocol_file="REC_2026_03_21_01.txt",
            source_notes="Nagranie z próby 3",
        ),
        validation=TarzanValidation(
            status="ok",
            checked_at="2026-03-21T19:10:00",
            max_speed_ok=True,
            max_acceleration_ok=True,
            start_zero_ok=True,
            end_zero_ok=True,
            direction_change_ok=True,
            events_ok=True,
            messages=[],
        ),
    )


if __name__ == "__main__":
    example_take = build_example_take()
    errors = example_take.validate_basic()

    output_file = Path("TAKE_001_v01.json")
    example_take.save_json(output_file)

    print(f"Zapisano przykładowy TAKE do: {output_file}")
    if errors:
        print("Wykryto błędy walidacji:")
        for err in errors:
            print(f"- {err}")
    else:
        print("Walidacja podstawowa OK.")
