from __future__ import annotations

import copy
import math
import tkinter as tk
from dataclasses import dataclass

from editor.tarzanPanelOsi import TarzanPanelOsi
from editor.tarzanEdycjaPunktow import TarzanEdycjaPunktow
from motion.tarzanTakeModel import TarzanAxisTake, TarzanControlPoint, TarzanCurve

try:
    from mechanics.tarzanMechanikaOsi import TarzanMechanics
except Exception:
    TarzanMechanics = None


@dataclass(frozen=True)
class TarzanAxisDefinition:
    key: str
    axis_name: str
    mechanics_ref: str
    full_cycle_pulses: int
    min_full_cycle_time_s: float
    max_pulse_rate: int
    max_acceleration: int
    backlash_compensation: int


@dataclass
class AxisValidationResult:
    pulses_total: float
    pulses_limit: float
    peak_rate: float
    rate_limit: float
    peak_acceleration: float
    acceleration_limit: float
    duration_ms: int
    violations: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.violations


DRONE_KEY = "drone_release"


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return default


def _derive_acceleration(rate_start: float, rate_ramp: float, time_start: float, time_ramp: float, fallback: int) -> int:
    total_time = max(0.05, _safe_float(time_start) + _safe_float(time_ramp))
    delta_rate = max(0.0, _safe_float(rate_ramp) - _safe_float(rate_start))
    if delta_rate <= 0:
        return int(fallback)
    return max(int(fallback), _safe_int(delta_rate / total_time, fallback))


def _build_axis_definitions() -> list[TarzanAxisDefinition]:
    if TarzanMechanics is None:
        return [
            TarzanAxisDefinition("camera_horizontal", "oś pozioma kamery", "tarzanCameraHorizontal", 28800, 3.0, 7200, 1800, 24),
            TarzanAxisDefinition("camera_vertical", "oś pionowa kamery", "tarzanCameraVertical", 12800, 2.0, 6400, 1600, 24),
            TarzanAxisDefinition("camera_tilt", "oś pochyłu kamery", "tarzanCameraTilt", 3200, 1.0, 3200, 900, 12),
            TarzanAxisDefinition("camera_focus", "oś ostrości kamery", "tarzanCameraFocus", 30764, 1.0, 9600, 2400, 12),
            TarzanAxisDefinition("arm_vertical", "oś pionowa ramienia", "tarzanArmVertical", 28485, 10.0, 3200, 900, 36),
            TarzanAxisDefinition("arm_horizontal", "oś pozioma ramienia", "tarzanArmHorizontal", 92273, 15.0, 2400, 700, 36),
        ]

    mechanics = TarzanMechanics
    return [
        TarzanAxisDefinition(
            "camera_horizontal",
            "oś pozioma kamery",
            "tarzanCameraHorizontal",
            _safe_int(getattr(mechanics, "cameraHorizontalPulsesPerCycle")()),
            _safe_float(getattr(mechanics, "CAMERA_HORIZONTAL_MIN_CYCLE_TIME_SEC", 3.0)),
            _safe_int(getattr(mechanics, "cameraHorizontalCruiseMaxPulsesPerSecond")()),
            _derive_acceleration(
                getattr(mechanics, "CAMERA_HORIZONTAL_START_SETTLE_MAX_PULSES_PER_SEC", 300.0),
                getattr(mechanics, "CAMERA_HORIZONTAL_START_RAMP_MAX_PULSES_PER_SEC", 1500.0),
                getattr(mechanics, "CAMERA_HORIZONTAL_START_SETTLE_TIME_SEC", 0.30),
                getattr(mechanics, "CAMERA_HORIZONTAL_START_RAMP_TIME_SEC", 0.90),
                1800,
            ),
            _safe_int(getattr(mechanics, "CAMERA_HORIZONTAL_BACKLASH_COMPENSATION_PULSES", 24)),
        ),
        TarzanAxisDefinition(
            "camera_vertical",
            "oś pionowa kamery",
            "tarzanCameraVertical",
            _safe_int(getattr(mechanics, "cameraVerticalPulsesPerCycle")()),
            _safe_float(getattr(mechanics, "CAMERA_VERTICAL_MIN_CYCLE_TIME_SEC", 2.0)),
            _safe_int(getattr(mechanics, "cameraVerticalCruiseMaxPulsesPerSecond")()),
            _derive_acceleration(
                getattr(mechanics, "CAMERA_VERTICAL_START_SETTLE_MAX_PULSES_PER_SEC", 250.0),
                getattr(mechanics, "CAMERA_VERTICAL_START_RAMP_MAX_PULSES_PER_SEC", 1200.0),
                getattr(mechanics, "CAMERA_VERTICAL_START_SETTLE_TIME_SEC", 0.30),
                getattr(mechanics, "CAMERA_VERTICAL_START_RAMP_TIME_SEC", 0.90),
                1600,
            ),
            _safe_int(getattr(mechanics, "CAMERA_VERTICAL_BACKLASH_COMPENSATION_PULSES", 24)),
        ),
        TarzanAxisDefinition(
            "camera_tilt",
            "oś pochyłu kamery",
            "tarzanCameraTilt",
            _safe_int(getattr(mechanics, "cameraTiltPulsesPerCycle")()),
            _safe_float(getattr(mechanics, "CAMERA_TILT_MIN_CYCLE_TIME_SEC", 1.0)),
            _safe_int(getattr(mechanics, "cameraTiltCruiseMaxPulsesPerSecond")()),
            _derive_acceleration(
                getattr(mechanics, "CAMERA_TILT_START_SETTLE_MAX_PULSES_PER_SEC", 150.0),
                getattr(mechanics, "CAMERA_TILT_START_RAMP_MAX_PULSES_PER_SEC", 600.0),
                getattr(mechanics, "CAMERA_TILT_START_SETTLE_TIME_SEC", 0.25),
                getattr(mechanics, "CAMERA_TILT_START_RAMP_TIME_SEC", 0.75),
                900,
            ),
            _safe_int(getattr(mechanics, "CAMERA_TILT_BACKLASH_COMPENSATION_PULSES", 12)),
        ),
        TarzanAxisDefinition(
            "camera_focus",
            "oś ostrości kamery",
            "tarzanCameraFocus",
            _safe_int(getattr(mechanics, "cameraFocusPulsesPerCycle")()),
            _safe_float(getattr(mechanics, "CAMERA_FOCUS_MIN_CYCLE_TIME_SEC", 1.0)),
            _safe_int(getattr(mechanics, "cameraFocusCruiseMaxPulsesPerSecond")()),
            _derive_acceleration(
                getattr(mechanics, "CAMERA_FOCUS_START_SETTLE_MAX_PULSES_PER_SEC", 400.0),
                getattr(mechanics, "CAMERA_FOCUS_START_RAMP_MAX_PULSES_PER_SEC", 2000.0),
                getattr(mechanics, "CAMERA_FOCUS_START_SETTLE_TIME_SEC", 0.20),
                getattr(mechanics, "CAMERA_FOCUS_START_RAMP_TIME_SEC", 0.50),
                2400,
            ),
            _safe_int(getattr(mechanics, "CAMERA_FOCUS_BACKLASH_COMPENSATION_PULSES", 12)),
        ),
        TarzanAxisDefinition(
            "arm_vertical",
            "oś pionowa ramienia",
            "tarzanArmVertical",
            _safe_int(getattr(mechanics, "armVerticalPulsesPerCycle")()),
            _safe_float(getattr(mechanics, "ARM_VERTICAL_MIN_CYCLE_TIME_SEC", 10.0)),
            _safe_int(getattr(mechanics, "armVerticalCruiseMaxPulsesPerSecond")()),
            _derive_acceleration(
                getattr(mechanics, "ARM_VERTICAL_START_SETTLE_MAX_PULSES_PER_SEC", 150.0),
                getattr(mechanics, "ARM_VERTICAL_START_RAMP_MAX_PULSES_PER_SEC", 900.0),
                getattr(mechanics, "ARM_VERTICAL_START_SETTLE_TIME_SEC", 0.50),
                getattr(mechanics, "ARM_VERTICAL_START_RAMP_TIME_SEC", 1.00),
                900,
            ),
            _safe_int(getattr(mechanics, "ARM_VERTICAL_BACKLASH_COMPENSATION_PULSES", 36)),
        ),
        TarzanAxisDefinition(
            "arm_horizontal",
            "oś pozioma ramienia",
            "tarzanArmHorizontal",
            _safe_int(getattr(mechanics, "armHorizontalPulsesPerCycle")()),
            _safe_float(getattr(mechanics, "ARM_HORIZONTAL_MIN_CYCLE_TIME_SEC", 15.0)),
            _safe_int(getattr(mechanics, "armHorizontalCruiseMaxPulsesPerSecond")()),
            _derive_acceleration(
                getattr(mechanics, "ARM_HORIZONTAL_START_SETTLE_MAX_PULSES_PER_SEC", 200.0),
                getattr(mechanics, "ARM_HORIZONTAL_START_RAMP_MAX_PULSES_PER_SEC", 1200.0),
                getattr(mechanics, "ARM_HORIZONTAL_START_SETTLE_TIME_SEC", 0.60),
                getattr(mechanics, "ARM_HORIZONTAL_START_RAMP_TIME_SEC", 1.20),
                700,
            ),
            _safe_int(getattr(mechanics, "ARM_HORIZONTAL_BACKLASH_COMPENSATION_PULSES", 36)),
        ),
    ]


AXIS_DEFINITIONS: list[TarzanAxisDefinition] = _build_axis_definitions()
AXIS_DEFINITION_MAP: dict[str, TarzanAxisDefinition] = {item.key: item for item in AXIS_DEFINITIONS}


def ensure_take_axes(take) -> None:
    start = int(getattr(take.timeline, "take_start", 0))
    sample_step = int(getattr(getattr(take, "timeline", None), "sample_step", 10) or 10)

    if not hasattr(take, "axes") or take.axes is None:
        take.axes = {}

    max_end = start + sample_step

    for definition in AXIS_DEFINITIONS:
        mechanical_end = start + int(definition.full_cycle_pulses) * sample_step
        max_end = max(max_end, mechanical_end)
        axis = take.axes.get(definition.key)
        if axis is None or not hasattr(axis, "curve"):
            take.axes[definition.key] = TarzanAxisTake(
                axis_name=definition.axis_name,
                axis_enabled=True,
                mechanics_ref=definition.mechanics_ref,
                full_cycle_pulses=definition.full_cycle_pulses,
                min_full_cycle_time_s=definition.min_full_cycle_time_s,
                max_pulse_rate=definition.max_pulse_rate,
                max_acceleration=definition.max_acceleration,
                backlash_compensation=definition.backlash_compensation,
                start_must_be_zero=True,
                end_must_be_zero=True,
                raw_signal={},
                segments=[],
                curve=TarzanCurve(
                    curve_type="motion_intensity",
                    interpolation="spline",
                    preserve_distance=True,
                    ghost_enabled=True,
                    control_points=[
                        TarzanControlPoint(time=start, amplitude=0.0),
                        TarzanControlPoint(time=mechanical_end, amplitude=0.0),
                    ],
                ),
                generated_protocol={},
            )
        else:
            axis.full_cycle_pulses = int(definition.full_cycle_pulses)
            axis.min_full_cycle_time_s = float(definition.min_full_cycle_time_s)
            axis.max_pulse_rate = int(definition.max_pulse_rate)
            axis.max_acceleration = int(definition.max_acceleration)
            axis.backlash_compensation = int(definition.backlash_compensation)

            if not getattr(axis.curve, "control_points", None):
                axis.curve.control_points = [
                    TarzanControlPoint(time=start, amplitude=0.0),
                    TarzanControlPoint(time=mechanical_end, amplitude=0.0),
                ]

    take.timeline.take_start = start
    take.timeline.take_end = max_end
    take.timeline.take_duration = int(max_end - start)


class AxisTrack(tk.Frame):
    BG = "#171A1F"
    AREA_BG = "#1B2028"
    FG = "#F3F6F8"
    MUTED = "#8E98A4"
    CURVE = "#D9E7F5"
    CURVE_INVALID = "#FF8080"
    NODE = "#FFD166"
    NODE_SELECTED = "#FF9F1C"
    START = "#45C46B"
    STOP = "#E65D5D"
    SEGMENT_FILL = "#253040"
    LIMIT_OK = "#6BD08B"
    LIMIT_WARN = "#E6B450"
    LIMIT_BAD = "#FF6B6B"
    SEGMENT_COLORS = {
        "camera_horizontal": "#2D6CDF",
        "camera_vertical": "#0E9F6E",
        "camera_tilt": "#7C3AED",
        "camera_focus": "#C2410C",
        "arm_vertical": "#BE185D",
        "arm_horizontal": "#0891B2",
    }

    def __init__(self, parent, axis_key, axis_take, line, krzywe, edycja: TarzanEdycjaPunktow, on_change, on_select, on_status) -> None:
        super().__init__(parent, bg=self.BG, highlightthickness=1, highlightbackground="#222833")
        self.axis_key = axis_key
        self.axis_take = axis_take
        self.axis_definition = AXIS_DEFINITION_MAP[axis_key]
        self.line = line
        self.original_line = copy.deepcopy(line)
        self.krzywe = krzywe
        self.edycja = edycja
        self.on_change = on_change
        self.on_select = on_select
        self.on_status = on_status

        self.view_start = 0
        self.view_end = 10000
        self.selected = False
        self.pan_mode = False
        self.drag_mode = None
        self.drag_index = None
        self.selected_node_index = None
        self.drag_original = None
        self.preview_line = None
        self.preview_validation_result: AxisValidationResult | None = None
        self.validation_result: AxisValidationResult | None = None
        self.last_curve_points = []
        self.original_area = 0.0
        self.pan_anchor_x = 0
        self.canvas_width = 1100
        self.canvas_height = 156

        self.panel = TarzanPanelOsi(
            self,
            axis_name=axis_take.axis_name,
            on_select=self._select,
            on_pan=self._toggle_pan,
            on_smooth=self._smooth,
            on_reset=self._reset,
            on_auto=self._auto,
            on_add_node=self._add_node,
            on_remove_node=self._remove_node,
        )
        self.panel.pack(side="left", fill="y")

        self.limit_panel = tk.Frame(self, bg=self.BG, width=128)
        self.limit_panel.pack(side="left", fill="y", padx=(4, 0))
        self.limit_panel.pack_propagate(False)

        self.limit_canvas = tk.Canvas(self.limit_panel, width=124, height=76, bg="#1A1E24", highlightthickness=0, bd=0)
        self.limit_canvas.pack(fill="both", expand=False, pady=(8, 0))

        right = tk.Frame(self, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        self.title = tk.Label(
            right,
            text=str(axis_take.axis_name).upper(),
            bg=self.BG,
            fg=self.FG,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        )
        # Axis title moved to the left vertical panel.

        self.meta_var = tk.StringVar(value="")
        self.meta_label = tk.Label(
            right,
            textvariable=self.meta_var,
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 7),
            anchor="w",
            justify="left",
        )
        # Mechanical descriptions removed from main view; preview window is the reference.

        self.canvas = tk.Canvas(
            right,
            height=self.canvas_height,
            bg=self.AREA_BG,
            highlightthickness=0,
            bd=0,
            relief="flat",
            cursor="crosshair",
        )
        self.canvas.pack(fill="x", padx=10, pady=(0, 8))

        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self._update_canvas_cursor()

    def _update_canvas_cursor(self) -> None:
        self.canvas.configure(cursor="hand2" if self.dragging else "crosshair")

    def set_view(self, view_start: int, view_end: int) -> None:
        self.view_start = int(view_start)
        self.view_end = int(view_end)
        self.redraw()

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self.configure(highlightbackground="#5B6A7D" if selected else "#222833")
        self.panel.set_selected(selected)

    def set_line(self, line) -> None:
        self.line = line
        if self.selected_node_index is not None and self.selected_node_index >= len(self.line.nodes):
            self.selected_node_index = None
        self.validation_result = self.validate_line(self.line)
        self.redraw()

    def get_validation_result(self) -> AxisValidationResult:
        return self.validate_line(self.line)

    def _display_line(self):
        return self.preview_line if self.preview_line is not None else self.line

    def _display_validation(self) -> AxisValidationResult:
        if self.preview_line is not None and self.preview_validation_result is not None:
            return self.preview_validation_result
        if self.validation_result is None:
            self.validation_result = self.validate_line(self.line)
        return self.validation_result

    def _select(self) -> None:
        self.on_select(self.axis_key)

    def _update_canvas_cursor(self) -> None:
        self.canvas.configure(cursor="hand2" if self.pan_mode else "crosshair")

    def _is_inside_active_area(self, x: float, y: float, x0: float, x1: float) -> bool:
        return float(x0) <= float(x) <= float(x1) and 0 <= float(y) <= float(self.canvas_height)

    def _toggle_pan(self) -> None:
        self.pan_mode = not self.pan_mode
        self.panel.set_pan_active(self.pan_mode)
        self._update_canvas_cursor()
        self.on_status(f"PAN {'ON' if self.pan_mode else 'OFF'} dla osi: {self.axis_take.axis_name}")

    def _smooth(self) -> None:
        try:
            try:
                candidate = self.krzywe.smooth_line(self.line, strength=0.35, preserve_distance=True, axis=self.axis_take)
            except Exception:
                candidate = self._smooth_line_local(self.line)
            candidate = self._preserve_motion_area(candidate, self.line, locked_index=None)
            result = self.validate_line(candidate)
            self.line = candidate
            self.validation_result = result
            self.preview_line = None
            self.preview_validation_result = None
            self.on_change(self.axis_key, self.line)
            self.redraw()
            self.on_status(f"Wygładzono oś: {self.axis_take.axis_name}")
        except Exception as exc:
            self.on_status(f"Błąd wygładzania: {exc}")

    def _reset(self) -> None:
        self.line = copy.deepcopy(self.original_line)
        self.preview_line = None
        self.preview_validation_result = None
        self.validation_result = self.validate_line(self.line)
        self.selected_node_index = None
        self.on_change(self.axis_key, self.line)
        self.redraw()
        self.on_status(f"Zresetowano oś: {self.axis_take.axis_name}")

    def _auto(self) -> None:
        self.on_status(f"AUTO dla osi {self.axis_take.axis_name} będzie dopięte później.")

    def _add_node(self) -> None:
        try:
            start = self.line.nodes[0].time_ms
            stop = self.line.nodes[-1].time_ms
            mid = (start + stop) // 2
            sampled = self.krzywe.sample_line(self.line, sample_count=180)
            nearest = min(sampled, key=lambda item: abs(item[0] - mid))
            before_count = len(self.line.nodes)
            try:
                candidate = self.krzywe.add_node(self.line, mid, nearest[1], axis=self.axis_take)
            except TypeError:
                candidate = self.krzywe.add_node(self.line, mid, nearest[1])
            if len(candidate.nodes) > before_count:
                self.selected_node_index = len(candidate.nodes) - 2
            candidate = self._preserve_motion_area(candidate, self.line, locked_index=self.selected_node_index)
            self.line = candidate
            self.validation_result = self.validate_line(self.line)
            self.on_change(self.axis_key, self.line)
            self.redraw()
            self.on_status(f"Dodano węzeł osi: {self.axis_take.axis_name}")
        except Exception as exc:
            self.on_status(f"Błąd dodawania węzła: {exc}")

    def _remove_node(self) -> None:
        if self.selected_node_index is None:
            self.on_status(f"Najpierw wybierz węzeł osi: {self.axis_take.axis_name}")
            return
        if self.selected_node_index <= 0 or self.selected_node_index >= len(self.line.nodes) - 1:
            self.on_status("Nie można usunąć START ani STOP.")
            return
        try:
            try:
                candidate = self.krzywe.remove_node(self.line, self.selected_node_index, axis=self.axis_take)
            except TypeError:
                candidate = self.krzywe.remove_node(self.line, self.selected_node_index)
            candidate = self._preserve_motion_area(candidate, self.line, locked_index=None)
            self.line = candidate
            self.validation_result = self.validate_line(self.line)
            self.selected_node_index = None
            self.on_change(self.axis_key, self.line)
            self.redraw()
            self.on_status(f"Usunięto węzeł osi: {self.axis_take.axis_name}")
        except Exception as exc:
            self.on_status(f"Błąd usuwania węzła: {exc}")

    def _on_configure(self, event) -> None:
        self.canvas_width = max(200, int(event.width))
        self.canvas_height = max(60, int(event.height))
        self.redraw()

    def _rate_to_color(self, ratio: float) -> str:
        if ratio > 1.0:
            return self.LIMIT_BAD
        if ratio >= 0.95:
            return self.LIMIT_WARN
        return self.LIMIT_OK

    def _format_metrics_text(self, result: AxisValidationResult) -> str:
        return (
            f"cykl {self.axis_definition.full_cycle_pulses} imp | "
            f"max {self.axis_definition.max_pulse_rate} imp/s | "
            f"acc {self.axis_definition.max_acceleration} imp/s² | "
            f"luz {self.axis_definition.backlash_compensation} imp"
        )

    def _format_violation_status(self, result: AxisValidationResult) -> str:
        return (
            f"{self.axis_take.axis_name}: "
            f"P={int(round(result.pulses_total))}/{int(round(result.pulses_limit))} | "
            f"R={int(round(result.peak_rate))}/{int(round(result.rate_limit))} | "
            f"A={int(round(result.peak_acceleration))}/{int(round(result.acceleration_limit))}"
        )

    def _safe_sample(self, line, sample_count: int = 260):
        try:
            return self.krzywe.sample_line(line, sample_count=sample_count)
        except Exception:
            if not getattr(line, 'nodes', None):
                return []
            return [(int(n.time_ms), float(n.value)) for n in line.nodes]

    def _compute_area(self, line) -> float:
        try:
            return float(self.krzywe.compute_area(line))
        except Exception:
            samples = self._safe_sample(line, 240)
            if len(samples) < 2:
                return 0.0
            area = 0.0
            for idx in range(1, len(samples)):
                t0, v0 = samples[idx - 1]
                t1, v1 = samples[idx]
                area += ((abs(v0) + abs(v1)) * 0.5) * max(1, (t1 - t0))
            return float(area)

    def _scale_line_duration(self, line, factor: float, locked_index: int | None = None):
        candidate = copy.deepcopy(line)
        nodes = getattr(candidate, "nodes", [])
        if len(nodes) < 2:
            return candidate
        factor = max(0.15, min(8.0, float(factor)))
        start_time = int(nodes[0].time_ms)
        step = max(1, getattr(self.edycja, "step_ms", 10))

        locked_time = None
        if locked_index is not None and 0 <= locked_index < len(nodes):
            locked_time = int(nodes[locked_index].time_ms)

        for idx, node in enumerate(nodes):
            if idx == 0:
                node.time_ms = start_time
                node.value = 0.0
                continue
            offset = int(node.time_ms) - start_time
            new_offset = self.edycja.snap(offset * factor)
            node.time_ms = start_time + new_offset

        if locked_time is not None and 0 < locked_index < len(nodes) - 1:
            shift = locked_time - int(nodes[locked_index].time_ms)
            for idx in range(locked_index, len(nodes)):
                nodes[idx].time_ms = int(nodes[idx].time_ms) + shift

        for idx in range(1, len(nodes)):
            min_time = int(nodes[idx - 1].time_ms) + step
            if int(nodes[idx].time_ms) < min_time:
                nodes[idx].time_ms = min_time

        nodes[-1].value = 0.0
        return candidate

    def _preserve_motion_area(self, candidate, reference, locked_index: int | None = None):
        ref_area = self._compute_area(reference)
        cand_area = self._compute_area(candidate)
        if ref_area <= 0 or cand_area <= 0:
            return candidate
        factor = ref_area / cand_area
        if abs(factor - 1.0) < 0.03:
            return candidate
        return self._scale_line_duration(candidate, factor, locked_index=locked_index)

    def _scale_line_values(self, line, factor: float):
        candidate = copy.deepcopy(line)
        factor = max(0.05, min(20.0, float(factor)))
        for idx, node in enumerate(candidate.nodes):
            if idx in (0, len(candidate.nodes) - 1):
                node.value = 0.0
            else:
                node.value = max(-1.0, min(1.0, float(node.value) * factor))
        return candidate

    def _max_abs_amplitude(self, line) -> float:
        if not getattr(line, "nodes", None):
            return 0.0
        return max(abs(float(node.value)) for node in line.nodes[1:-1]) if len(line.nodes) > 2 else 0.0

    def _fit_edge_motion(self, desired, reference, moved_index: int):
        ref_area = self._compute_area(reference)
        desired_area = self._compute_area(desired)
        if ref_area <= 0 or desired_area <= 0:
            return desired

        scale = ref_area / desired_area
        scaled = self._scale_line_values(desired, scale)
        if self._compute_area(scaled) > 0 and self._max_abs_amplitude(scaled) <= 1.0 + 1e-6:
            return scaled

        original_edge = int(reference.nodes[moved_index].time_ms)
        target_edge = int(desired.nodes[moved_index].time_ms)
        if original_edge == target_edge:
            return self._scale_line_values(reference, 1.0)

        low = original_edge
        high = target_edge
        if target_edge < original_edge:
            low, high = target_edge, original_edge

        best = copy.deepcopy(reference)
        for _ in range(28):
            mid = self.edycja.snap((low + high) / 2)
            probe = self._move_edge(reference, moved_index, mid)
            probe_area = self._compute_area(probe)
            if probe_area <= 0:
                break
            scaled_probe = self._scale_line_values(probe, ref_area / probe_area)
            if self._max_abs_amplitude(scaled_probe) <= 1.0 + 1e-6:
                best = scaled_probe
                if target_edge >= original_edge:
                    low = mid
                else:
                    high = mid
            else:
                if target_edge >= original_edge:
                    high = mid
                else:
                    low = mid
        return best

    def _smooth_line_local(self, line):
        candidate = copy.deepcopy(line)
        nodes = getattr(candidate, "nodes", [])
        if len(nodes) <= 2:
            return candidate
        original_values = [float(node.value) for node in nodes]
        for index in range(1, len(nodes) - 1):
            prev_value = original_values[index - 1]
            current_value = original_values[index]
            next_value = original_values[index + 1]
            nodes[index].value = (prev_value * 0.25) + (current_value * 0.5) + (next_value * 0.25)
        nodes[0].value = 0.0
        nodes[-1].value = 0.0
        return candidate

    def _shift_line_local(self, line, delta_ms: int):
        candidate = copy.deepcopy(line)
        nodes = getattr(candidate, "nodes", [])
        if not nodes:
            return candidate
        snapped_delta = self.edycja.snap(delta_ms)
        for node in nodes:
            node.time_ms = int(node.time_ms) + snapped_delta
        return candidate

    def _resolve_target_pulses(self) -> float:
        full_cycle = float(getattr(self.axis_take, "full_cycle_pulses", 0) or 0)
        if full_cycle > 0:
            return full_cycle
        return float(getattr(self.axis_definition, "full_cycle_pulses", 0) or 0)

    def validate_line(self, line) -> AxisValidationResult:
        generated = getattr(self.axis_take, "generated_protocol", {}) or {}
        protocol_rows = list(generated.get("protocol_rows", []) or [])
        if protocol_rows and line is self.line:
            return self._validation_from_protocol(protocol_rows)

        samples = self._safe_sample(line, sample_count=min(240, max(120, len(getattr(line, 'nodes', [])) * 24)))
        if len(samples) < 2:
            return AxisValidationResult(0.0, max(1.0, self._resolve_target_pulses()), 0.0, float(self.axis_definition.max_pulse_rate), 0.0, float(self.axis_definition.max_acceleration), 0, [])

        duration_ms = max(0, int(line.nodes[-1].time_ms) - int(line.nodes[0].time_ms))
        max_rate = float(self.axis_definition.max_pulse_rate)
        rate_limit = float(self.axis_definition.max_pulse_rate)
        acceleration_limit = float(self.axis_definition.max_acceleration)
        pulses_limit = float(self._resolve_target_pulses())

        pulses_total = 0.0
        peak_rate = 0.0
        peak_acceleration = 0.0
        prev_rate = None

        for index in range(1, len(samples)):
            t0, v0 = samples[index - 1]
            t1, v1 = samples[index]
            dt_ms = max(1, int(t1) - int(t0))
            dt_s = dt_ms / 1000.0
            rate0 = abs(float(v0)) * max_rate
            rate1 = abs(float(v1)) * max_rate
            avg_rate = (rate0 + rate1) * 0.5
            pulses_total += avg_rate * dt_s
            peak_rate = max(peak_rate, rate0, rate1)
            if prev_rate is not None:
                peak_acceleration = max(peak_acceleration, abs(rate1 - prev_rate) / max(0.001, dt_s))
            prev_rate = rate1

        if pulses_limit <= 0:
            pulses_limit = max(1.0, pulses_total)

        violations: list[str] = []
        if peak_rate > rate_limit + max(5.0, rate_limit * 0.01):
            violations.append(f"za duża prędkość {int(round(peak_rate))}>{int(round(rate_limit))} imp/s")
        if peak_acceleration > acceleration_limit + max(10.0, acceleration_limit * 0.02):
            violations.append(f"za duże przyspieszenie {int(round(peak_acceleration))}>{int(round(acceleration_limit))} imp/s²")
        if abs(float(line.nodes[0].value)) > 1e-6:
            violations.append("START musi być 0")
        if abs(float(line.nodes[-1].value)) > 1e-6:
            violations.append("STOP musi być 0")

        return AxisValidationResult(
            pulses_total=pulses_total,
            pulses_limit=pulses_limit,
            peak_rate=peak_rate,
            rate_limit=rate_limit,
            peak_acceleration=peak_acceleration,
            acceleration_limit=acceleration_limit,
            duration_ms=duration_ms,
            violations=violations,
        )

    def _validation_from_protocol(self, protocol_rows) -> AxisValidationResult:
        sample_ms = max(1, int(protocol_rows[1]["time_ms"] - protocol_rows[0]["time_ms"])) if len(protocol_rows) > 1 else 10
        rate_limit = float(self.axis_definition.max_pulse_rate)
        acceleration_limit = float(self.axis_definition.max_acceleration)
        pulses_limit = float(self._resolve_target_pulses())
        pulses_total = float((getattr(self.axis_take, 'generated_protocol', {}) or {}).get('step_count_total', 0) or protocol_rows[-1].get('count', 0) or 0)
        peak_rate = 0.0
        peak_acceleration = 0.0
        prev_rate = None
        for row in protocol_rows:
            rate = float(int(row.get("step_events", 0) or 0)) * (1000.0 / sample_ms)
            peak_rate = max(peak_rate, rate)
            if prev_rate is not None:
                peak_acceleration = max(peak_acceleration, abs(rate - prev_rate) / max(0.001, sample_ms / 1000.0))
            prev_rate = rate
        violations: list[str] = []
        if peak_rate > rate_limit + max(5.0, rate_limit * 0.01):
            violations.append(f"za duża prędkość {int(round(peak_rate))}>{int(round(rate_limit))} imp/s")
        if peak_acceleration > acceleration_limit + max(10.0, acceleration_limit * 0.02):
            violations.append(f"za duże przyspieszenie {int(round(peak_acceleration))}>{int(round(acceleration_limit))} imp/s²")
        duration_ms = int(protocol_rows[-1]["time_ms"] - protocol_rows[0]["time_ms"]) if len(protocol_rows) > 1 else 0
        return AxisValidationResult(
            pulses_total=pulses_total,
            pulses_limit=max(1.0, pulses_limit),
            peak_rate=peak_rate,
            rate_limit=rate_limit,
            peak_acceleration=peak_acceleration,
            acceleration_limit=acceleration_limit,
            duration_ms=duration_ms,
            violations=violations,
        )

    def _draw_limit_panel(self, result: AxisValidationResult) -> None:
        c = self.limit_canvas
        c.delete("all")
        width = max(120, int(c.winfo_width() or 124))
        c.create_rectangle(0, 0, width, 76, fill="#1A1E24", outline="#2A3038")
        bars = [
            ("P", result.pulses_total, result.pulses_limit, 12),
            ("R", result.peak_rate, result.rate_limit, 32),
            ("A", result.peak_acceleration, result.acceleration_limit, 52),
        ]
        for label, value, limit, y in bars:
            ratio = 0.0 if limit <= 0 else value / limit
            c.create_text(12, y, text=label, fill=self.FG, anchor="w", font=("Consolas", 8, "bold"))
            c.create_rectangle(28, y - 5, width - 10, y + 5, fill="#222833", outline="#3A434E")
            fill_to = 28 + min(1.0, ratio) * (width - 38)
            c.create_rectangle(28, y - 5, fill_to, y + 5, fill=self._rate_to_color(ratio), outline="")
            c.create_text(width - 8, y, text=f"{int(round(value))}/{int(round(limit))}", fill=self.MUTED, anchor="e", font=("Consolas", 7))

    def redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        line = self._display_line()
        result = self._display_validation()

        self.panel.set_axis_name(self.axis_take.axis_name)
        self.meta_var.set(self._format_metrics_text(result))
        self._draw_limit_panel(result)
        self._update_canvas_cursor()

        x0 = self.edycja.time_to_x(line.nodes[0].time_ms, self.view_start, self.view_end, self.canvas_width)
        x1 = self.edycja.time_to_x(line.nodes[-1].time_ms, self.view_start, self.view_end, self.canvas_width)
        segment_color = self.SEGMENT_COLORS.get(self.axis_key, self.SEGMENT_FILL)
        c.create_rectangle(x0, 6, x1, self.canvas_height - 6, fill=segment_color, outline="#6F42C1" if self.pan_mode else "", width=1 if self.pan_mode else 0, stipple="gray25")

        y0 = self.edycja.value_to_y(0.0, self.canvas_height)
        c.create_line(0, y0, self.canvas_width, y0, fill="#FF3030", width=4)

        c.create_line(x0, 0, x0, self.canvas_height, fill=self.START, width=4)
        c.create_line(x1, 0, x1, self.canvas_height, fill=self.STOP, width=4)
        c.create_text(x0 + 4, 10, anchor="w", text="START", fill=self.START, font=("Segoe UI", 8, "bold"))
        c.create_text(x1 - 4, 10, anchor="e", text="STOP", fill=self.STOP, font=("Segoe UI", 8, "bold"))

        ghost_line = self.original_line
        ghost_sampled = self._safe_sample(ghost_line, 260)
        ghost_points = []
        for time_ms, value in ghost_sampled:
            x = self.edycja.time_to_x(time_ms, self.view_start, self.view_end, self.canvas_width)
            y = self.edycja.value_to_y(value, self.canvas_height)
            ghost_points.extend([x, y])
        if len(ghost_points) >= 4:
            c.create_line(*ghost_points, fill="#FFD84A", width=2, dash=(14, 6), smooth=True)

        sampled = self._safe_sample(line, 260)
        self.last_curve_points = []
        points = []
        for time_ms, value in sampled:
            x = self.edycja.time_to_x(time_ms, self.view_start, self.view_end, self.canvas_width)
            y = self.edycja.value_to_y(value, self.canvas_height)
            points.extend([x, y])
            self.last_curve_points.append((x, y, time_ms, value))
        if len(points) >= 4:
            c.create_line(*points, fill=self.CURVE if result.is_valid else self.CURVE_INVALID, width=3, smooth=True)

        for idx, node in enumerate(line.nodes):
            x = self.edycja.time_to_x(node.time_ms, self.view_start, self.view_end, self.canvas_width)
            y = self.edycja.value_to_y(node.value, self.canvas_height)
            r = 7 if idx not in (0, len(line.nodes) - 1) else 6
            fill = self.NODE_SELECTED if idx == self.selected_node_index else (self.NODE if idx not in (0, len(line.nodes) - 1) else "#D6EAF8")
            c.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="black", width=1)


    def _nearest_curve_hit(self, x: float, y: float):
        if len(self.last_curve_points) < 2:
            return None
        best = None
        best_dist = math.inf
        for idx in range(len(self.last_curve_points) - 1):
            x1, y1, *_ = self.last_curve_points[idx]
            x2, y2, *_ = self.last_curve_points[idx + 1]
            seg_len2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
            if seg_len2 <= 0:
                continue
            t = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / seg_len2
            t = max(0.0, min(1.0, t))
            px = x1 + t * (x2 - x1)
            py = y1 + t * (y2 - y1)
            dist = math.hypot(x - px, y - py)
            if dist < best_dist:
                best_dist = dist
                best = (idx, dist)
        if best is None or best[1] > self.edycja.LINE_TOL:
            return None
        return best[0]

    def _nearest_node_by_curve_index(self, curve_index: int):
        if len(self.line.nodes) <= 2:
            return None
        sample_ratio = curve_index / max(1, len(self.last_curve_points) - 1)
        target_time = self.line.nodes[0].time_ms + sample_ratio * (self.line.nodes[-1].time_ms - self.line.nodes[0].time_ms)
        interior = list(range(1, len(self.line.nodes) - 1))
        if not interior:
            return None
        return min(interior, key=lambda idx: abs(self.line.nodes[idx].time_ms - target_time))

    def _on_press(self, event) -> None:
        self.on_select(self.axis_key)
        current = self._display_line()
        hit = self.edycja.hit_node(current, event.x, event.y, self.view_start, self.view_end, self.canvas_width, self.canvas_height)
        x0 = self.edycja.time_to_x(current.nodes[0].time_ms, self.view_start, self.view_end, self.canvas_width)
        x1 = self.edycja.time_to_x(current.nodes[-1].time_ms, self.view_start, self.view_end, self.canvas_width)
        hit_start = self.edycja.hit_vertical_marker(x0, event.x)
        hit_stop = self.edycja.hit_vertical_marker(x1, event.x)
        curve_hit = self._nearest_curve_hit(event.x, event.y)
        hit_active_area = self._is_inside_active_area(event.x, event.y, x0, x1)

        if hit is not None:
            self.selected_node_index = hit

        if self.pan_mode and hit_active_area:
            self.drag_mode = "pan"
            self.drag_original = copy.deepcopy(current)
            self.pan_anchor_x = event.x
            self.preview_line = copy.deepcopy(current)
            self.preview_validation_result = self.validate_line(self.preview_line)
            return

        if hit_start:
            self.drag_mode = "start_edge"
            self.drag_index = 0
            self.drag_original = copy.deepcopy(current)
            self.preview_line = copy.deepcopy(current)
            self.preview_validation_result = self.validate_line(self.preview_line)
            self.selected_node_index = 0
            return

        if hit_stop:
            self.drag_mode = "stop_edge"
            self.drag_index = len(current.nodes) - 1
            self.drag_original = copy.deepcopy(current)
            self.preview_line = copy.deepcopy(current)
            self.preview_validation_result = self.validate_line(self.preview_line)
            self.selected_node_index = self.drag_index
            return

        if hit is not None:
            self.drag_mode = "node"
            self.drag_index = hit
            self.drag_original = copy.deepcopy(current)
            self.preview_line = copy.deepcopy(current)
            self.preview_validation_result = self.validate_line(self.preview_line)
            self.original_area = self._compute_area(current)
            return

        if curve_hit is not None:
            nearest_node_index = self._nearest_node_by_curve_index(curve_hit)
            if nearest_node_index is not None:
                self.drag_mode = "node"
                self.drag_index = nearest_node_index
                self.drag_original = copy.deepcopy(current)
                self.preview_line = copy.deepcopy(current)
                self.preview_validation_result = self.validate_line(self.preview_line)
                self.selected_node_index = nearest_node_index
                self.original_area = self._compute_area(current)
                return

        self.drag_mode = None
        self.drag_index = None
        self.drag_original = None
        self.preview_line = None
        self.preview_validation_result = None
        self.redraw()

    def _move_edge(self, line, index: int, new_time: int):
        updated = copy.deepcopy(line)
        step = max(1, getattr(self.edycja, "step_ms", 10))
        if index == 0:
            max_time = updated.nodes[1].time_ms - step if len(updated.nodes) > 1 else updated.nodes[-1].time_ms - step
            updated.nodes[0].time_ms = min(max_time, new_time)
            updated.nodes[0].value = 0.0
        else:
            min_time = updated.nodes[-2].time_ms + step if len(updated.nodes) > 1 else updated.nodes[0].time_ms + step
            updated.nodes[-1].time_ms = max(min_time, new_time)
            updated.nodes[-1].value = 0.0
        return updated

    def _on_drag(self, event) -> None:
        if self.drag_mode is None or self.drag_original is None:
            return
        try:
            if self.drag_mode == "pan":
                t0 = self.edycja.x_to_time(self.pan_anchor_x, self.view_start, self.view_end, self.canvas_width)
                t1 = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
                delta = t1 - t0
                try:
                    candidate = self.krzywe.shift_line_in_time(self.drag_original, delta, axis=self.axis_take)
                except Exception:
                    candidate = self._shift_line_local(self.drag_original, delta)
            elif self.drag_mode == "node":
                new_time = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
                new_value = self.edycja.y_to_value(event.y, self.canvas_height)
                candidate = self.krzywe.move_node(
                    self.drag_original,
                    index=self.drag_index,
                    new_time_ms=new_time,
                    new_value=new_value,
                    axis=self.axis_take,
                    preserve_area=False,
                )
                if self.drag_index not in (0, len(candidate.nodes) - 1):
                    candidate = self._preserve_motion_area(candidate, self.drag_original, locked_index=self.drag_index)
            elif self.drag_mode == "start_edge":
                new_time = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
                candidate = self._move_edge(self.drag_original, 0, new_time)
            elif self.drag_mode == "stop_edge":
                new_time = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
                candidate = self._move_edge(self.drag_original, len(self.drag_original.nodes) - 1, new_time)
            else:
                return

            result = self.validate_line(candidate)
            self.preview_line = candidate
            self.preview_validation_result = result
            self.redraw()
        except Exception as exc:
            self.on_status(f"Błąd edycji osi {self.axis_take.axis_name}: {exc}")

    def _on_release(self, _event) -> None:
        if self.drag_mode is None:
            return
        try:
            if self.preview_line is not None and self.preview_validation_result is not None:
                self.line = copy.deepcopy(self.preview_line)
                self.validation_result = self.preview_validation_result
                self.on_change(self.axis_key, self.line)
            self.preview_line = None
            self.preview_validation_result = None
            self.redraw()
        finally:
            self.drag_mode = None
            self.drag_index = None
            self.drag_original = None


class DroneTrack(tk.Frame):
    BG = "#171A1F"
    AREA_BG = "#1B2028"
    FG = "#F3F6F8"
    DRONE = "#E65D5D"

    def __init__(self, parent, event_time_ms, on_change, edycja: TarzanEdycjaPunktow) -> None:
        super().__init__(parent, bg=self.BG, highlightthickness=1, highlightbackground="#222833")
        self.event_time_ms = event_time_ms
        self.on_change = on_change
        self.edycja = edycja
        self.view_start = 0
        self.view_end = 10000
        self.canvas_width = 1100
        self.selected = False
        self.dragging = False

        left = tk.Frame(self, width=124, bg="#23272E")
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="◆", bg="#23272E", fg=self.DRONE, font=("Segoe UI Symbol", 14)).pack(anchor="center", pady=(14, 4))

        spacer = tk.Frame(self, width=128, bg=self.BG)
        spacer.pack(side="left", fill="y")
        spacer.pack_propagate(False)

        right = tk.Frame(self, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="DRON", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 10), anchor="w").pack(fill="x", padx=10, pady=(6, 2))

        self.canvas = tk.Canvas(right, height=72, bg=self.AREA_BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="x", padx=10, pady=(0, 8))
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self._update_canvas_cursor()

    def set_view(self, view_start: int, view_end: int) -> None:
        self.view_start = int(view_start)
        self.view_end = int(view_end)
        self.redraw()

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self.configure(highlightbackground="#5B6A7D" if selected else "#222833")

    def _update_canvas_cursor(self) -> None:
        self.canvas.configure(cursor="hand2" if self.dragging else "crosshair")

    def _on_configure(self, event) -> None:
        self.canvas_width = max(200, int(event.width))
        self.redraw()

    def redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        x = self.edycja.time_to_x(self.event_time_ms, self.view_start, self.view_end, self.canvas_width)
        y = 36
        c.create_line(0, y, self.canvas_width, y, fill="#8E98A4", width=1)
        c.create_line(x, 0, x, 72, fill=self.DRONE, width=2, dash=(4, 3))
        c.create_polygon(x, y - 10, x + 10, y, x, y + 10, x - 10, y, fill=self.DRONE, outline="black")
        c.create_text(x + 14, y - 14, anchor="w", text="release", fill=self.DRONE, font=("Segoe UI", 8, "bold"))

    def _on_press(self, event) -> None:
        x = self.edycja.time_to_x(self.event_time_ms, self.view_start, self.view_end, self.canvas_width)
        self.dragging = abs(event.x - x) <= 14
        self._update_canvas_cursor()

    def _on_drag(self, event) -> None:
        if not self.dragging:
            return
        self.event_time_ms = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
        self.redraw()

    def _on_release(self, _event) -> None:
        if self.dragging:
            self.on_change(self.event_time_ms)
        self.dragging = False
        self._update_canvas_cursor()
