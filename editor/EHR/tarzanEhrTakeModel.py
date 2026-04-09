from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AxisTakeSnapshot:
    axis_id: str
    axis_name: str
    is_release_axis: bool
    take_duration_ms: int
    release_time_ms: int | None
    nodes: list[dict[str, Any]]
    protocol_rows: list[dict[str, Any]]
    metrics_text: str


@dataclass
class EhrTakeModel:
    main_take_duration_ms: int
    settings: dict[str, Any]
    axes: list[AxisTakeSnapshot]

    @classmethod
    def from_runtime(cls, main_take_duration_ms: int, main_take_settings, axis_models: list[Any]) -> "EhrTakeModel":
        axes: list[AxisTakeSnapshot] = []
        settings_payload = {
            "take_duration_minutes": getattr(main_take_settings, "take_duration_minutes", 1.0),
            "zero_line_color": getattr(main_take_settings, "zero_line_color", "#E03A3A"),
            "zero_line_width": getattr(main_take_settings, "zero_line_width", 1),
            "curve_line_width": getattr(main_take_settings, "curve_line_width", 4),
            "active_curve_line_width": getattr(main_take_settings, "active_curve_line_width", 5),
            "snap_to_zero_enabled": getattr(main_take_settings, "snap_to_zero_enabled", True),
            "snap_to_zero_threshold": getattr(main_take_settings, "snap_to_zero_threshold", 9.0),
            "show_protocol_preview": getattr(main_take_settings, "show_protocol_preview", True),
            "show_axis_metrics": getattr(main_take_settings, "show_axis_metrics", True),
            "show_axis_labels": getattr(main_take_settings, "show_axis_labels", True),
            "show_axis_gears": getattr(main_take_settings, "show_axis_gears", True),
            "show_status_bar": getattr(main_take_settings, "show_status_bar", True),
            "show_minute_grid": getattr(main_take_settings, "show_minute_grid", True),
        }
        for model in axis_models:
            nodes = [{"time_ms": int(node.time_ms), "y": float(node.y)} for node in model.nodes]
            protocol_rows = model.protocol_rows(duration_ms=main_take_duration_ms)
            axes.append(
                AxisTakeSnapshot(
                    axis_id=model.axis_def.axis_id,
                    axis_name=model.axis_def.axis_name,
                    is_release_axis=bool(model.is_release_axis),
                    take_duration_ms=int(main_take_duration_ms),
                    release_time_ms=None if model.release_time_ms is None else int(model.release_time_ms),
                    nodes=nodes,
                    protocol_rows=protocol_rows,
                    metrics_text=model.metrics_summary(duration_ms=main_take_duration_ms),
                )
            )
        return cls(
            main_take_duration_ms=int(main_take_duration_ms),
            settings=settings_payload,
            axes=axes,
        )
