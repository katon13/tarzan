from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class MainTakeSettings:
    take_duration_minutes: float = 1.0
    zero_line_color: str = "#E03A3A"
    zero_line_width: int = 1
    curve_line_width: int = 4
    active_curve_line_width: int = 5
    snap_to_zero_enabled: bool = True
    snap_to_zero_threshold: float = 9.0
    show_protocol_preview: bool = True
    show_axis_metrics: bool = True
    show_axis_labels: bool = True
    show_axis_gears: bool = True
    show_status_bar: bool = True
    show_minute_grid: bool = True

    def clamp(self) -> None:
        self.take_duration_minutes = max(0.1, min(240.0, float(self.take_duration_minutes)))
        self.zero_line_width = max(1, min(3, int(self.zero_line_width)))
        self.curve_line_width = max(1, min(10, int(self.curve_line_width)))
        self.active_curve_line_width = max(self.curve_line_width, min(12, int(self.active_curve_line_width)))
        self.snap_to_zero_threshold = max(0.0, min(30.0, float(self.snap_to_zero_threshold)))

    def take_duration_ms(self) -> int:
        self.clamp()
        return max(1000, int(round(self.take_duration_minutes * 60000.0)))

    def to_json_text(self) -> str:
        self.clamp()
        return json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n"

    @classmethod
    def from_json_text(cls, text: str) -> "MainTakeSettings":
        data = json.loads(text)
        settings = cls()
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        settings.clamp()
        return settings

    @classmethod
    def load_or_default(cls, path: Path) -> "MainTakeSettings":
        try:
            return cls.from_json_text(path.read_text(encoding="utf-8"))
        except Exception:
            return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json_text(), encoding="utf-8")
