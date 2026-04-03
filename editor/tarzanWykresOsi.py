from __future__ import annotations

import copy
import tkinter as tk
from dataclasses import dataclass

from editor.tarzanPanelOsi import TarzanPanelOsi
from editor.tarzanEdycjaPunktow import TarzanEdycjaPunktow
from motion.tarzanTakeModel import TarzanAxisTake, TarzanControlPoint, TarzanCurve, TarzanEvent


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


AXIS_DEFINITIONS: list[TarzanAxisDefinition] = [
    TarzanAxisDefinition("camera_horizontal", "oś pozioma kamery", "tarzanCameraHorizontal", 28800, 3.0, 7200, 1800, 24),
    TarzanAxisDefinition("camera_vertical", "oś pionowa kamery", "tarzanCameraVertical", 12800, 2.0, 6400, 1600, 24),
    TarzanAxisDefinition("camera_tilt", "oś pochyłu kamery", "tarzanCameraTilt", 3200, 1.0, 3200, 900, 12),
    TarzanAxisDefinition("camera_focus", "oś ostrości kamery", "tarzanCameraFocus", 30764, 1.0, 9600, 2400, 12),
    TarzanAxisDefinition("arm_vertical", "oś pionowa ramienia", "tarzanArmVertical", 28485, 10.0, 3200, 900, 36),
    TarzanAxisDefinition("arm_horizontal", "oś pozioma ramienia", "tarzanArmHorizontal", 92273, 15.0, 2400, 700, 36),
]

DRONE_KEY = "drone_release"


def ensure_take_axes(take) -> None:
    start = int(getattr(take.timeline, "take_start", 0))
    end = int(getattr(take.timeline, "take_end", 0))
    if end <= start:
        end = start + 10000
        take.timeline.take_end = end
        take.timeline.take_duration = end - start

    for definition in AXIS_DEFINITIONS:
        axis = take.axes.get(definition.key)
        if axis is None:
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
                        TarzanControlPoint(time=end, amplitude=0.0),
                    ],
                ),
                generated_protocol={},
            )
        elif not getattr(axis.curve, "control_points", None):
            axis.curve.control_points = [
                TarzanControlPoint(time=start, amplitude=0.0),
                TarzanControlPoint(time=end, amplitude=0.0),
            ]


class AxisTrack(tk.Frame):
    BG = "#171A1F"
    AREA_BG = "#1B2028"
    FG = "#F3F6F8"
    MUTED = "#8E98A4"
    CURVE = "#7DC4FF"
    NODE = "#FFD166"
    START = "#45C46B"
    STOP = "#E65D5D"
    SEGMENT_FILL = "#253040"

    def __init__(self, parent, axis_key, axis_take, line, krzywe, edycja: TarzanEdycjaPunktow, on_change, on_select, on_status) -> None:
        super().__init__(parent, bg=self.BG, highlightthickness=1, highlightbackground="#222833")
        self.axis_key = axis_key
        self.axis_take = axis_take
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
        self.drag_original = None
        self.drag_area = 0.0
        self.preview_line = None
        self.canvas_width = 1100
        self.canvas_height = 92

        self.panel = TarzanPanelOsi(
            self,
            axis_name=axis_take.axis_name,
            on_select=self._select,
            on_pan=self._toggle_pan,
            on_smooth=self._smooth,
            on_reset=self._reset,
            on_auto=self._auto,
        )
        self.panel.pack(side="left", fill="y")

        right = tk.Frame(self, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        self.title = tk.Label(
            right,
            text=axis_take.axis_name,
            bg=self.BG,
            fg=self.FG,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        )
        self.title.pack(fill="x", padx=10, pady=(6, 2))

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
        self.redraw()

    def _select(self) -> None:
        self.on_select(self.axis_key)

    def _toggle_pan(self) -> None:
        self.pan_mode = not self.pan_mode
        self.panel.set_pan_active(self.pan_mode)
        self.on_status(f"PAN {'ON' if self.pan_mode else 'OFF'} dla osi: {self.axis_take.axis_name}")

    def _smooth(self) -> None:
        try:
            self.line = self.krzywe.smooth_line(self.line, strength=0.35, preserve_distance=True, axis=self.axis_take)
            self.on_change(self.axis_key, self.line)
            self.redraw()
            self.on_status(f"Wygładzono oś: {self.axis_take.axis_name}")
        except Exception as exc:
            self.on_status(f"Błąd wygładzania: {exc}")

    def _reset(self) -> None:
        self.line = copy.deepcopy(self.original_line)
        self.preview_line = None
        self.on_change(self.axis_key, self.line)
        self.redraw()
        self.on_status(f"Zresetowano oś: {self.axis_take.axis_name}")

    def _auto(self) -> None:
        self.on_status(f"AUTO dla osi {self.axis_take.axis_name} będzie dopięte w kolejnym kroku.")

    def _on_configure(self, event) -> None:
        self.canvas_width = max(200, int(event.width))
        self.canvas_height = max(60, int(event.height))
        self.redraw()

    def _display_line(self):
        return self.preview_line if self.preview_line is not None else self.line

    def redraw(self) -> None:
        c = self.canvas
        c.delete("all")
        line = self._display_line()

        # kolorowe tło odcinka ruchu
        x0 = self.edycja.time_to_x(line.nodes[0].time_ms, self.view_start, self.view_end, self.canvas_width)
        x1 = self.edycja.time_to_x(line.nodes[-1].time_ms, self.view_start, self.view_end, self.canvas_width)
        c.create_rectangle(x0, 6, x1, self.canvas_height - 6, fill=self.SEGMENT_FILL, outline="")

        # linia zero
        y0 = self.edycja.value_to_y(0.0, self.canvas_height)
        c.create_line(0, y0, self.canvas_width, y0, fill=self.MUTED, width=1)

        # start / stop
        c.create_line(x0, 0, x0, self.canvas_height, fill=self.START, width=2)
        c.create_line(x1, 0, x1, self.canvas_height, fill=self.STOP, width=2)
        c.create_text(x0 + 4, 10, anchor="w", text="START", fill=self.START, font=("Segoe UI", 8, "bold"))
        c.create_text(x1 - 4, 10, anchor="e", text="STOP", fill=self.STOP, font=("Segoe UI", 8, "bold"))

        sampled = self.krzywe.sample_line(line, sample_count=260)
        points = []
        for time_ms, value in sampled:
            x = self.edycja.time_to_x(time_ms, self.view_start, self.view_end, self.canvas_width)
            y = self.edycja.value_to_y(value, self.canvas_height)
            points.extend([x, y])
        if len(points) >= 4:
            c.create_line(*points, fill=self.CURVE, width=3, smooth=True)

        for idx, node in enumerate(line.nodes):
            x = self.edycja.time_to_x(node.time_ms, self.view_start, self.view_end, self.canvas_width)
            y = self.edycja.value_to_y(node.value, self.canvas_height)
            r = 7 if idx not in (0, len(line.nodes) - 1) else 6
            fill = self.NODE if idx not in (0, len(line.nodes) - 1) else "#D6EAF8"
            c.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="black", width=1)

    def _on_press(self, event) -> None:
        self.on_select(self.axis_key)
        current = self._display_line()

        if self.pan_mode:
            self.drag_mode = "pan"
            self.drag_original = copy.deepcopy(current)
            self.pan_anchor_x = event.x
            return

        hit = self.edycja.hit_test_node(current, event.x, event.y, self.view_start, self.view_end, self.canvas_width, self.canvas_height)
        if hit is not None:
            self.drag_mode = "node"
            self.drag_index = hit
            self.drag_original = copy.deepcopy(current)
            self.drag_area = self.krzywe.compute_area(current)
            self.preview_line = copy.deepcopy(current)
            return

        line_hit = self.edycja.hit_test_start_stop(current, event.x, self.view_start, self.view_end, self.canvas_width)
        if line_hit is not None:
            self.drag_mode = line_hit
            self.drag_original = copy.deepcopy(current)
            self.preview_line = copy.deepcopy(current)
            return

        self.drag_mode = None

    def _on_drag(self, event) -> None:
        if self.drag_mode is None or self.drag_original is None:
            return

        try:
            if self.drag_mode == "pan":
                t0 = self.edycja.x_to_time(self.pan_anchor_x, self.view_start, self.view_end, self.canvas_width)
                t1 = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
                delta = t1 - t0
                self.preview_line = self.krzywe.shift_line_in_time(self.drag_original, delta, axis=self.axis_take)

            elif self.drag_mode == "node":
                new_time = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
                new_value = self.edycja.y_to_value(event.y, self.canvas_height)
                self.preview_line = self.krzywe.move_node(
                    self.drag_original,
                    index=self.drag_index,
                    new_time_ms=new_time,
                    new_value=new_value,
                    axis=self.axis_take,
                    preserve_area=False,
                )

            elif self.drag_mode in ("start", "stop"):
                new_time = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
                start_ms = self.drag_original.nodes[0].time_ms
                stop_ms = self.drag_original.nodes[-1].time_ms
                if self.drag_mode == "start":
                    start_ms = new_time
                else:
                    stop_ms = new_time
                self.preview_line = self.krzywe.set_line_start_stop(
                    self.drag_original,
                    new_start_ms=start_ms,
                    new_stop_ms=stop_ms,
                    axis=self.axis_take,
                    preserve_distance=True,
                )

            self.redraw()
        except Exception as exc:
            self.on_status(f"Błąd edycji osi {self.axis_take.axis_name}: {exc}")

    def _on_release(self, _event) -> None:
        if self.drag_mode is None:
            return
        try:
            if self.preview_line is not None:
                committed = self.preview_line
                if self.drag_mode == "node" and hasattr(self.krzywe, "fit_line_to_area_keep_node_locked"):
                    committed = self.krzywe.fit_line_to_area_keep_node_locked(
                        self.preview_line,
                        target_area=self.drag_area,
                        locked_index=self.drag_index,
                        axis=self.axis_take,
                    )
                self.line = committed
                self.on_change(self.axis_key, self.line)
            self.preview_line = None
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

        left = tk.Frame(self, width=150, bg="#23272E")
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="DRON", bg="#23272E", fg=self.FG, font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=8, pady=(8, 6))
        tk.Label(left, text="release", bg="#23272E", fg="#C9D3DF", font=("Segoe UI", 8)).pack(anchor="w", padx=8)

        right = tk.Frame(self, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="DRON", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 10), anchor="w").pack(fill="x", padx=10, pady=(6, 2))

        self.canvas = tk.Canvas(right, height=72, bg=self.AREA_BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="x", padx=10, pady=(0, 8))
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def set_view(self, view_start: int, view_end: int) -> None:
        self.view_start = int(view_start)
        self.view_end = int(view_end)
        self.redraw()

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self.configure(highlightbackground="#5B6A7D" if selected else "#222833")

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

    def _on_drag(self, event) -> None:
        if not self.dragging:
            return
        self.event_time_ms = self.edycja.x_to_time(event.x, self.view_start, self.view_end, self.canvas_width)
        self.redraw()

    def _on_release(self, _event) -> None:
        if self.dragging:
            self.on_change(self.event_time_ms)
        self.dragging = False
