from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


DEFAULT_AXIS_COLORS = {
    "cam_h": "#78DCE8",
    "cam_v": "#FFD866",
    "cam_t": "#FF6188",
    "cam_f": "#A9DC76",
    "arm_v": "#AB9DF2",
    "arm_h": "#FC9867",
    "dron": "#F472B6",
}


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
    show_axis_background_tint: bool = True
    axis_background_strength_percent: int = 10
    active_axis_emphasis_percent: int = 10
    active_axis_border_width: int = 3
    show_start_stop_squares: bool = True
    show_axis_activity_markers: bool = True
    smooth_strength_default: float = 0.35
    smooth_passes_default: int = 2
    axis_color_overrides: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_AXIS_COLORS))
    show_ghost_line: bool = True
    ghost_line_color: str = "#EAB308"
    ghost_line_width: int = 1
    ghost_line_dash_on: int = 4
    ghost_line_dash_off: int = 4

    def clamp(self) -> None:
        self.take_duration_minutes = max(0.1, min(240.0, float(self.take_duration_minutes)))
        self.zero_line_width = max(1, min(3, int(self.zero_line_width)))
        self.curve_line_width = max(1, min(10, int(self.curve_line_width)))
        self.active_curve_line_width = max(self.curve_line_width, min(12, int(self.active_curve_line_width)))
        self.snap_to_zero_threshold = max(0.0, min(30.0, float(self.snap_to_zero_threshold)))
        self.axis_background_strength_percent = max(0, min(30, int(self.axis_background_strength_percent)))
        self.active_axis_emphasis_percent = max(0, min(40, int(self.active_axis_emphasis_percent)))
        self.active_axis_border_width = max(0, min(8, int(self.active_axis_border_width)))
        self.smooth_strength_default = max(0.0, min(1.0, float(self.smooth_strength_default)))
        self.smooth_passes_default = max(1, min(8, int(self.smooth_passes_default)))
        self.ghost_line_width = max(1, min(5, int(self.ghost_line_width)))
        self.ghost_line_dash_on = max(1, min(20, int(self.ghost_line_dash_on)))
        self.ghost_line_dash_off = max(1, min(20, int(self.ghost_line_dash_off)))
        merged = dict(DEFAULT_AXIS_COLORS)
        raw = dict(self.axis_color_overrides or {})
        for key, default in DEFAULT_AXIS_COLORS.items():
            value = str(raw.get(key, default)).strip() or default
            merged[key] = value
        self.axis_color_overrides = merged


    def axis_color(self, axis_id: str, fallback: str) -> str:
        self.clamp()
        return self.axis_color_overrides.get(axis_id, fallback) or fallback

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
