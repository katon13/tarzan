from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from editor.EHR.tarzanEhrMultiAxisModel import (
    AxisCurveModel,
    DEFAULT_AXIS_DEFINITIONS,
    EhrEditorConfig,
    MECHANICS_PRESETS,
    StepTuning,
)


@dataclass
class AxisViewportRect:
    left: int
    top: int
    right: int
    bottom: int

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom


@dataclass
class GearRect:
    left: int
    top: int
    right: int
    bottom: int

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom


class AxisSettingsDialog(tk.Toplevel):
    def __init__(self, master: "TarzanEhrMultiAxisWindow", axis_index: int) -> None:
        super().__init__(master)
        self.master_window = master
        self.axis_index = axis_index
        self.model = master.axis_models[axis_index]

        self.title(f"Ustawienia osi — {self.model.axis_def.axis_name}")
        self.geometry("1760x1120")
        self.minsize(1500, 960)
        self.configure(bg=master.BG)
        self.transient(master)

        self.display_y_scale = tk.DoubleVar(value=self.model.sandbox.display_y_scale)
        self.mouse_y_precision = tk.DoubleVar(value=self.model.sandbox.mouse_y_precision)
        self.top_bottom_margin = tk.IntVar(value=self.model.sandbox.top_bottom_margin)
        self.mechanics_preset_var = tk.StringVar(value=self.model.mechanics.axis_name)
        self.axis_take_ms = tk.IntVar(value=self.model.take_duration_ms)
        self.status_var = tk.StringVar(value="Gotowy.")
        self.metrics_var = tk.StringVar(value="")

        defaults = copy.deepcopy(self.model.step_tuning)
        self.step_vars = {
            "dead_zone_y": tk.DoubleVar(value=defaults.dead_zone_y),
            "input_max_y": tk.DoubleVar(value=defaults.input_max_y),
            "input_gamma": tk.DoubleVar(value=defaults.input_gamma),
            "step_rate_gain": tk.DoubleVar(value=defaults.step_rate_gain),
            "step_rate_max_percent": tk.DoubleVar(value=defaults.step_rate_max_percent),
            "preview_rate_smoothing": tk.DoubleVar(value=defaults.preview_rate_smoothing),
            "bucket_width_px": tk.IntVar(value=defaults.bucket_width_px),
            "off_bar_height": tk.IntVar(value=defaults.off_bar_height),
            "low_zone_gain": tk.DoubleVar(value=defaults.low_zone_gain),
            "mid_zone_gain": tk.DoubleVar(value=defaults.mid_zone_gain),
            "high_zone_gain": tk.DoubleVar(value=defaults.high_zone_gain),
            "accumulator_bias": tk.DoubleVar(value=defaults.accumulator_bias),
            "emit_threshold": tk.DoubleVar(value=defaults.emit_threshold),
            "node_hit_radius_px": tk.IntVar(value=defaults.node_hit_radius_px),
            "time_drag_threshold_samples": tk.IntVar(value=defaults.time_drag_threshold_samples),
        }

        self.selected_index: int | None = None
        self.drag_mode: str | None = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self.drag_anchor_node_time = 0
        self.drag_anchor_node_y = 0.0

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self.update_idletasks()
        self.after_idle(self._refresh_all)
        self.grab_set()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.master_window.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.master_window.BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(
            top,
            text="TARZAN — SANDBOX OSI",
            bg=self.master_window.BG,
            fg=self.master_window.FG,
            font=("Segoe UI Semibold", 16),
        ).pack(side="left")

        btns = tk.Frame(top, bg=self.master_window.BG)
        btns.pack(side="right")
        self._btn(btns, "SINUS TEST", self._sinus_test, "#2D6CDF").pack(side="left", padx=3)
        self._btn(btns, "NEG TEST", self._negative_test, "#6F42C1").pack(side="left", padx=3)
        self._btn(btns, "ZERO CROSS", self._zero_cross_test, "#0F766E").pack(side="left", padx=3)
        self._btn(btns, "FLAT 0", self._flat_zero, "#C78B2A").pack(side="left", padx=3)
        self._btn(btns, "RESET", self._reset_nodes, "#BE185D").pack(side="left", padx=3)
        self._btn(btns, "ZAMKNIJ", self._on_close, "#4B5563").pack(side="left", padx=3)

        body = tk.Frame(outer, bg=self.master_window.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.master_window.BG, width=300)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=self.master_window.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(left)

        self.curve_canvas = tk.Canvas(right, bg="#1B2028", height=420, highlightthickness=0)
        self.curve_canvas.pack(fill="x", pady=(0, 8))
        self.curve_canvas.bind("<Button-1>", self._on_curve_press)
        self.curve_canvas.bind("<B1-Motion>", self._on_curve_drag)
        self.curve_canvas.bind("<ButtonRelease-1>", self._on_curve_release)
        self.curve_canvas.bind("<Double-Button-1>", self._on_curve_double_click)
        self.curve_canvas.bind("<Button-3>", self._on_curve_right_click)

        self.step_canvas = tk.Canvas(right, bg="#1A1E24", height=255, highlightthickness=0)
        self.step_canvas.pack(fill="both", expand=True)

        self._build_step_tuning_panel(right)

        status = tk.Label(
            outer,
            textvariable=self.status_var,
            bg=self.master_window.PANEL2,
            fg=self.master_window.FG,
            anchor="w",
            padx=10,
            pady=8,
            font=("Segoe UI", 9),
        )
        status.pack(fill="x", pady=(8, 0))

    def _build_left_panel(self, parent: tk.Misc) -> None:
        tk.Label(
            parent,
            text=self.model.axis_def.axis_name.upper(),
            bg=self.master_window.BG,
            fg=self.master_window.FG,
            anchor="w",
            font=("Segoe UI Semibold", 12),
        ).pack(fill="x", pady=(0, 8))
        tk.Label(
            parent,
            textvariable=self.metrics_var,
            bg=self.master_window.BG,
            fg=self.master_window.MUTED,
            justify="left",
            anchor="w",
            font=("Consolas", 9),
        ).pack(fill="x", pady=(0, 12))

        mechanics_box = tk.Frame(parent, bg=self.master_window.PANEL)
        mechanics_box.pack(fill="x", pady=(0, 10))
        tk.Label(
            mechanics_box,
            text="MECHANIKA OSI",
            bg=self.master_window.PANEL,
            fg=self.master_window.FG,
            anchor="w",
            font=("Segoe UI Semibold", 9),
        ).pack(fill="x", padx=10, pady=(8, 4))
        available_mechanics = [name for name in MECHANICS_PRESETS.keys() if name != "oś wzorcowa"]
        om = tk.OptionMenu(mechanics_box, self.mechanics_preset_var, *available_mechanics)
        om.configure(
            bg="#39424E",
            fg=self.master_window.FG,
            activebackground="#39424E",
            activeforeground=self.master_window.FG,
            relief="flat",
            highlightthickness=0,
        )
        om["menu"].configure(bg="#2A3038", fg=self.master_window.FG)
        om.pack(fill="x", padx=10, pady=(0, 8))
        self._btn(mechanics_box, "WCZYTAJ Z MECHANIKI", self._apply_mechanics_preset, "#2563EB").pack(fill="x", padx=10, pady=(0, 10))

        take_box = tk.Frame(parent, bg=self.master_window.PANEL)
        take_box.pack(fill="x", pady=(0, 10))
        tk.Label(
            take_box,
            text="CZAS TAKE OSI (ms)",
            bg=self.master_window.PANEL,
            fg=self.master_window.FG,
            anchor="w",
            font=("Segoe UI Semibold", 9),
        ).pack(fill="x", padx=10, pady=(8, 4))
        take_entry = tk.Entry(
            take_box,
            textvariable=self.axis_take_ms,
            bg="#39424E",
            fg=self.master_window.FG,
            relief="flat",
            insertbackground=self.master_window.FG,
        )
        take_entry.pack(fill="x", padx=10, pady=(0, 6))
        take_entry.bind("<Return>", lambda _e: self._apply_take_time())
        self._btn(take_box, "ZASTOSUJ CZAS TAKE OSI", self._apply_take_time, "#0F766E").pack(fill="x", padx=10, pady=(0, 10))

        box = tk.Frame(parent, bg=self.master_window.PANEL)
        box.pack(fill="x", pady=(0, 10))
        self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._apply_visual_settings)
        self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._apply_visual_settings)
        self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._apply_visual_settings)

    def _build_step_tuning_panel(self, parent: tk.Misc) -> None:
        panel = tk.Frame(parent, bg=self.master_window.PANEL, padx=10, pady=10)
        panel.pack(fill="x", pady=(8, 0))
        tk.Label(
            panel,
            text="STROJENIE DRUGIEGO WYKRESU / STEP PREVIEW",
            bg=self.master_window.PANEL,
            fg=self.master_window.FG,
            anchor="w",
            font=("Segoe UI Semibold", 10),
        ).pack(fill="x", pady=(0, 8))

        grid = tk.Frame(panel, bg=self.master_window.PANEL)
        grid.pack(fill="x")

        sliders = [
            ("dead_zone_y", "DEAD ZONE Y", 0.0, 30.0, 0.5),
            ("input_max_y", "INPUT MAX Y", 20.0, 100.0, 1.0),
            ("input_gamma", "INPUT GAMMA", 0.1, 12.0, 0.1),
            ("step_rate_gain", "STEP GAIN", 0.1, 5.0, 0.05),
            ("step_rate_max_percent", "MAX RATE %", 1.0, 100.0, 1.0),
            ("preview_rate_smoothing", "RATE SMOOTH", 0.0, 0.95, 0.01),
            ("bucket_width_px", "BUCKET PX", 1, 16, 1),
            ("off_bar_height", "OFF BAR H", 1, 40, 1),
            ("low_zone_gain", "ZONE 0-33%", 0.0, 2.0, 0.01),
            ("mid_zone_gain", "ZONE 33-66%", 0.0, 2.0, 0.01),
            ("high_zone_gain", "ZONE 66-100%", 0.0, 2.0, 0.01),
            ("accumulator_bias", "ACC BIAS", 0.0, 0.99, 0.01),
            ("emit_threshold", "EMIT THRESH", 0.2, 2.0, 0.01),
            ("node_hit_radius_px", "HIT RADIUS", 6, 30, 1),
            ("time_drag_threshold_samples", "TIME DRAG THR", 0, 10, 1),
        ]
        for idx, (key, label, start, end, res) in enumerate(sliders):
            col = idx % 3
            row = idx // 3
            self._scale_row_grid(grid, row, col, label, self.step_vars[key], start, end, res, self._apply_step_tuning_live)

        btn_row = tk.Frame(panel, bg=self.master_window.PANEL)
        btn_row.pack(fill="x", pady=(10, 0))
        self._btn(btn_row, "ZAPISZ TXT", self._save_tuning_txt, "#047857").pack(side="left", padx=(0, 6))
        self._btn(btn_row, "WCZYTAJ TXT", self._load_tuning_txt, "#7C3AED").pack(side="left", padx=6)
        self._btn(btn_row, "RESET STEP", self._reset_step_tuning, "#B45309").pack(side="left", padx=6)

    def _scale_row(self, parent, label, var, from_, to, resolution, command):
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.pack(fill="x", padx=10, pady=8)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        scale = tk.Scale(
            wrap,
            variable=var,
            from_=from_,
            to=to,
            resolution=resolution,
            orient="horizontal",
            command=lambda _v: command(),
            bg=self.master_window.PANEL,
            fg=self.master_window.FG,
            troughcolor="#39424E",
            highlightthickness=0,
            bd=0,
            length=240,
        )
        scale.pack(fill="x")

    def _scale_row_grid(self, parent, row, col, label, var, from_, to, resolution, command):
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI", 8, "bold")).pack(fill="x")
        scale = tk.Scale(
            wrap,
            variable=var,
            from_=from_,
            to=to,
            resolution=resolution,
            orient="horizontal",
            command=lambda _v: command(),
            bg=self.master_window.PANEL,
            fg=self.master_window.FG,
            troughcolor="#39424E",
            highlightthickness=0,
            bd=0,
            length=300,
        )
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color, activeforeground="white", relief="flat", bd=0, padx=10, pady=6, font=("Segoe UI Semibold", 9), cursor="hand2")

    def _curve_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.curve_canvas.winfo_width() or 1200))
        h = max(220, int(self.curve_canvas.winfo_height() or 430))
        return 70, 14, w - 20, h - 20

    def _step_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.step_canvas.winfo_width() or 1200))
        h = max(120, int(self.step_canvas.winfo_height() or 260))
        return 70, 16, w - 20, h - 24

    def _time_to_x(self, t_ms: int, left: int, right: int) -> float:
        span = max(1, self.model.take_duration_ms)
        return left + (t_ms / span) * (right - left)

    def _x_to_time(self, x: float, left: int, right: int) -> int:
        rel = (x - left) / max(1.0, (right - left))
        rel = max(0.0, min(1.0, rel))
        return self.model.snap_time(rel * self.model.take_duration_ms)

    def _logical_y_to_canvas(self, y: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(self.model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(self.model.config.y_limit))
        operator_y = float(y) * (operator_range / logical_limit)
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.model.sandbox.top_bottom_margin)
        return mid - (operator_y / operator_range) * usable

    def _canvas_to_logical_y(self, py: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(self.model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(self.model.config.y_limit))
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.model.sandbox.top_bottom_margin)
        operator_y = ((mid - py) / max(1.0, usable)) * operator_range
        logical_y = operator_y * (logical_limit / operator_range)
        return self.model.clamp_y(logical_y)

    def _drag_delta_to_logical_y(self, delta_py: float, top: int, bottom: int) -> float:
        logical_limit = max(1.0, float(self.model.config.y_limit))
        usable = (bottom - top) / 2.0 - float(self.model.sandbox.top_bottom_margin)
        precision = max(0.05, float(self.model.sandbox.mouse_y_precision))
        logical_per_px = logical_limit / max(1.0, usable)
        return float(delta_py) * logical_per_px * precision

    def _read_step_tuning_from_ui(self) -> StepTuning:
        tuning = StepTuning(
            dead_zone_y=float(self.step_vars["dead_zone_y"].get()),
            input_max_y=float(self.step_vars["input_max_y"].get()),
            input_gamma=float(self.step_vars["input_gamma"].get()),
            step_rate_gain=float(self.step_vars["step_rate_gain"].get()),
            step_rate_max_percent=float(self.step_vars["step_rate_max_percent"].get()),
            preview_rate_smoothing=float(self.step_vars["preview_rate_smoothing"].get()),
            bucket_width_px=int(self.step_vars["bucket_width_px"].get()),
            off_bar_height=int(self.step_vars["off_bar_height"].get()),
            low_zone_gain=float(self.step_vars["low_zone_gain"].get()),
            mid_zone_gain=float(self.step_vars["mid_zone_gain"].get()),
            high_zone_gain=float(self.step_vars["high_zone_gain"].get()),
            accumulator_bias=float(self.step_vars["accumulator_bias"].get()),
            emit_threshold=float(self.step_vars["emit_threshold"].get()),
            node_hit_radius_px=int(self.step_vars["node_hit_radius_px"].get()),
            time_drag_threshold_samples=int(self.step_vars["time_drag_threshold_samples"].get()),
        )
        tuning.clamp()
        return tuning

    def _write_step_tuning_to_ui(self, tuning: StepTuning) -> None:
        tuning.clamp()
        for key in self.step_vars:
            self.step_vars[key].set(getattr(tuning, key))

    def _default_data_dir(self) -> Path:
        editor_dir = Path(__file__).resolve().parent.parent
        project_dir = editor_dir.parent
        data_dir = project_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def _apply_visual_settings(self) -> None:
        self.model.sandbox.display_y_scale = float(self.display_y_scale.get())
        self.model.sandbox.mouse_y_precision = float(self.mouse_y_precision.get())
        self.model.sandbox.top_bottom_margin = int(self.top_bottom_margin.get())
        self._refresh_all("Zastosowano ustawienia osi.")
        self.master_window._refresh_all()

    def _apply_step_tuning_live(self) -> None:
        self.model.set_step_tuning(self._read_step_tuning_from_ui())
        self._refresh_all("Zastosowano strojenie STEP.")
        self.master_window._refresh_all()

    def _apply_mechanics_preset(self) -> None:
        mechanics = copy.deepcopy(MECHANICS_PRESETS[self.mechanics_preset_var.get()])
        self.model.set_mechanics(mechanics)
        self.axis_take_ms.set(self.model.take_duration_ms)
        self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.")
        self.master_window._refresh_all()

    def _apply_take_time(self) -> None:
        try:
            value = int(self.axis_take_ms.get())
        except (tk.TclError, ValueError):
            self.status_var.set("Nieprawidłowy czas TAKE osi.")
            return
        if value < self.model.sample_ms * 10:
            self.status_var.set("Czas TAKE osi jest za mały.")
            return
        self.model.set_axis_take_duration_ms(value)
        self.axis_take_ms.set(self.model.take_duration_ms)
        self._refresh_all("Zastosowano czas TAKE osi.")
        self.master_window._refresh_all()

    def _save_tuning_txt(self) -> None:
        tuning = self._read_step_tuning_from_ui()
        default_name = self.model.axis_def.axis_name.replace(" ", "_") + "_step_preset.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialdir=str(self._default_data_dir()),
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Zapisz preset STEP do TXT",
        )
        if not path:
            return
        Path(path).write_text(tuning.to_text(self.model.mechanics), encoding="utf-8")
        self.status_var.set(f"Zapisano preset TXT: {path}")

    def _load_tuning_txt(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(self._default_data_dir()),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Wczytaj preset STEP z TXT",
        )
        if not path:
            return
        tuning, mechanics = StepTuning.from_text(Path(path).read_text(encoding="utf-8"))
        if mechanics is not None:
            self.model.set_mechanics(mechanics)
            self.mechanics_preset_var.set(mechanics.axis_name)
        self._write_step_tuning_to_ui(tuning)
        self.model.set_step_tuning(tuning)
        self._refresh_all(f"Wczytano preset TXT: {path}")
        self.master_window._refresh_all()

    def _reset_step_tuning(self) -> None:
        tuning = StepTuning()
        self._write_step_tuning_to_ui(tuning)
        self.model.set_step_tuning(tuning)
        self._refresh_all("Przywrócono domyślne parametry STEP.")
        self.master_window._refresh_all()

    def _sinus_test(self) -> None:
        self.model.set_sinus_test()
        self.model.clone_original_state()
        self._refresh_all("Sinus test ustawiony.")
        self.master_window._refresh_all()

    def _negative_test(self) -> None:
        self.model.set_negative_test()
        self.model.clone_original_state()
        self._refresh_all("Negative test ustawiony.")
        self.master_window._refresh_all()

    def _zero_cross_test(self) -> None:
        self.model.set_zero_cross_test()
        self.model.clone_original_state()
        self._refresh_all("Zero cross test ustawiony.")
        self.master_window._refresh_all()

    def _flat_zero(self) -> None:
        self.model.set_flat_zero()
        self.model.clone_original_state()
        self._refresh_all("Linia wyzerowana.")
        self.master_window._refresh_all()

    def _reset_nodes(self) -> None:
        self.model.reset_to_original_state()
        self._refresh_all("Przywrócono ostatni stan bazowy.")
        self.master_window._refresh_all()

    def _refresh_metrics(self) -> None:
        self.metrics_var.set(self.model.metrics_summary())

    def _draw_curve(self) -> None:
        c = self.curve_canvas
        c.delete("all")
        left, top, right, bottom = self._curve_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="")

        settle = self.model.mechanics.start_settle_ms
        ramp = self.model.mechanics.start_ramp_ms
        start_total = settle + ramp
        stop_from = self.model.take_duration_ms - start_total
        sx = self._time_to_x(start_total, left, right)
        ex = self._time_to_x(stop_from, left, right)
        c.create_rectangle(left, top, sx, bottom, fill=self.master_window.WARN, outline="")
        c.create_rectangle(ex, top, right, bottom, fill=self.master_window.WARN, outline="")
        c.create_rectangle(sx, top, ex, bottom, fill=self.master_window.SAFE, outline="")

        for yv, color in [(100, self.master_window.DANGER), (50, self.master_window.WARN), (0, "#FF3030"), (-50, self.master_window.WARN), (-100, self.master_window.DANGER)]:
            py = self._logical_y_to_canvas(yv, top, bottom)
            width = 3 if yv == 0 else 1
            dash = None if yv == 0 else (5, 4)
            c.create_line(left, py, right, py, fill=color if yv != 0 else "#FF3030", width=width, dash=dash)
            c.create_text(left - 8, py, text=str(yv), fill=self.master_window.MUTED, anchor="e", font=("Consolas", 8))

        total_minutes = max(1, self.model.take_duration_ms // 60_000)
        for minute in range(0, total_minutes + 1):
            t_ms = minute * 60_000
            if t_ms > self.model.take_duration_ms:
                continue
            px = self._time_to_x(t_ms, left, right)
            c.create_line(px, top, px, bottom, fill="#43505C", dash=(2, 6))
            c.create_text(px, bottom + 10, text=f"{minute}m", fill=self.master_window.MUTED, anchor="n", font=("Consolas", 8))

        samples = self.model.sample_curve(1000)
        pts: list[float] = []
        for t, y in samples:
            pts.extend([self._time_to_x(t, left, right), self._logical_y_to_canvas(y, top, bottom)])
        if len(pts) >= 4:
            c.create_line(*pts, fill=self.master_window.CURVE, width=3, smooth=True)

        hit_radius = self._read_step_tuning_from_ui().node_hit_radius_px
        r = max(4, min(10, hit_radius // 2))
        for i, n in enumerate(self.model.nodes):
            px = self._time_to_x(n.time_ms, left, right)
            py = self._logical_y_to_canvas(n.y, top, bottom)
            fill = self.master_window.NODE_SEL if i == self.selected_index else self.master_window.NODE
            if i == 0 or i == len(self.model.nodes) - 1:
                fill = "#D6EAF8"
            c.create_oval(px - r, py - r, px + r, py + r, fill=fill, outline="black")

        x0 = self._time_to_x(0, left, right)
        x1 = self._time_to_x(self.model.take_duration_ms, left, right)
        c.create_line(x0, top, x0, bottom, fill="#45C46B", width=3)
        c.create_line(x1, top, x1, bottom, fill="#E65D5D", width=3)
        c.create_text(x0 + 4, top + 8, text="START", fill="#45C46B", anchor="w", font=("Segoe UI", 8, "bold"))
        c.create_text(x1 - 4, top + 8, text="STOP", fill="#E65D5D", anchor="e", font=("Segoe UI", 8, "bold"))

    def _draw_step(self) -> None:
        c = self.step_canvas
        c.delete("all")
        left, top, right, bottom = self._step_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1A1E24", outline="#303A45")
        rows = self.model.build_step_rows()
        if not rows:
            return
        tuning = self.model.step_tuning
        y_mid = (top + bottom) / 2.0
        c.create_line(left, y_mid, right, y_mid, fill="#55606D")
        bucket = max(1, tuning.bucket_width_px)
        px_bucket = {}
        for row in rows:
            raw_x = int(round(self._time_to_x(row["time_ms"], left, right)))
            x = ((raw_x - left) // bucket) * bucket + left
            item = px_bucket.setdefault(x, {"step": 0, "count": 0})
            item["step"] = max(item["step"], int(row["step"]))
            item["count"] = int(row["count"])
        for x in sorted(px_bucket.keys()):
            row = px_bucket[x]
            if row["step"] == 1:
                c.create_line(x, y_mid, x, top + 12, fill=self.master_window.STEP_ON, width=max(1, bucket))
            else:
                c.create_line(x, y_mid, x, y_mid + tuning.off_bar_height, fill=self.master_window.STEP_OFF, width=max(1, bucket))
        c.create_text(left, top - 2, text="STEP 0/1 preview (strojony suwakami poniżej)", fill=self.master_window.FG, anchor="sw", font=("Segoe UI Semibold", 9))
        c.create_text(right, top - 2, text=f"rows={len(rows)}  pulses={rows[-1]['count']}", fill=self.master_window.MUTED, anchor="se", font=("Consolas", 8))

    def _refresh_all(self, status: str | None = None) -> None:
        self.model.sort_and_fix_nodes()
        self._refresh_metrics()
        self._draw_curve()
        self._draw_step()
        self.status_var.set(status if status is not None else "Sandbox osi gotowy do strojenia.")

    def _hit_node(self, x: float, y: float) -> int | None:
        left, top, right, bottom = self._curve_rect()
        radius = self._read_step_tuning_from_ui().node_hit_radius_px
        for i, n in enumerate(self.model.nodes):
            px = self._time_to_x(n.time_ms, left, right)
            py = self._logical_y_to_canvas(n.y, top, bottom)
            if abs(px - x) <= radius and abs(py - y) <= radius:
                return i
        return None

    def _on_curve_press(self, event) -> None:
        idx = self._hit_node(event.x, event.y)
        if idx is not None:
            self.selected_index = idx
            self.drag_mode = "node"
            self.drag_anchor_x = event.x
            self.drag_anchor_y = event.y
            self.drag_anchor_node_time = int(self.model.nodes[idx].time_ms)
            self.drag_anchor_node_y = float(self.model.nodes[idx].y)
            self._refresh_all(f"Wybrano punkt {idx}.")
            return
        self.selected_index = None
        self.drag_mode = "pan"
        self.drag_anchor_x = event.x
        self._refresh_all("PAN linii.")

    def _on_curve_drag(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        tuning = self._read_step_tuning_from_ui()
        if self.drag_mode == "node" and self.selected_index is not None:
            delta_y = self.drag_anchor_y - event.y
            new_y = self.drag_anchor_node_y + self._drag_delta_to_logical_y(delta_y, top, bottom)
            delta_t = self._x_to_time(event.x, left, right) - self._x_to_time(self.drag_anchor_x, left, right)
            threshold_ms = self.model.sample_ms * tuning.time_drag_threshold_samples
            new_t = self.drag_anchor_node_time if abs(delta_t) < threshold_ms else self.drag_anchor_node_time + delta_t
            self.model.move_node(self.selected_index, new_t, new_y)
            self._draw_curve()
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(event.x, left, right)
            old_time = self._x_to_time(self.drag_anchor_x, left, right)
            delta = new_time - old_time
            self.drag_anchor_x = event.x
            self.model.shift_all(delta)
            self._draw_curve()

    def _on_curve_release(self, _event) -> None:
        self.drag_mode = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._refresh_all("Gotowy.")
        self.master_window._refresh_all()

    def _on_curve_double_click(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        t = self._x_to_time(event.x, left, right)
        y = self._canvas_to_logical_y(event.y, top, bottom)
        self.model.add_node(t, y)
        self._refresh_all("Dodano punkt.")
        self.master_window._refresh_all()

    def _on_curve_right_click(self, event) -> None:
        idx = self._hit_node(event.x, event.y)
        if idx is None:
            return
        self.model.remove_node(idx)
        self.selected_index = None
        self._refresh_all("Usunięto punkt.")
        self.master_window._refresh_all()

    def _on_close(self) -> None:
        self.master_window.settings_dialogs.pop(self.axis_index, None)
        self.destroy()


class TarzanEhrMultiAxisWindow(tk.Tk):
    BG = "#16181C"
    PANEL = "#23272E"
    PANEL2 = "#2A3038"
    FG = "#F3F6F8"
    MUTED = "#AEB7C2"
    CURVE = "#D9E7F5"
    NODE = "#FFD166"
    NODE_SEL = "#FF9F1C"
    STEP_ON = "#45C46B"
    STEP_OFF = "#48525E"
    SAFE = "#1E3A2F"
    WARN = "#5A4A1B"
    DANGER = "#4A2222"

    def __init__(self) -> None:
        super().__init__()
        self.title("TARZAN — tarzanEHR")
        self.geometry("1780x1080")
        self.minsize(1500, 920)
        self.configure(bg=self.BG)

        self.config_model = EhrEditorConfig()
        self.global_take_duration_ms = 60000
        self.axis_models = [AxisCurveModel(axis_def, self.config_model) for axis_def in DEFAULT_AXIS_DEFINITIONS]
        self.active_axis_index = 0
        self.selected_index: int | None = None
        self.drag_axis_index: int | None = None
        self.drag_mode: str | None = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self.drag_anchor_node_time = 0
        self.drag_anchor_node_y = 0.0
        self.axis_rects: dict[int, AxisViewportRect] = {}
        self.gear_rects: dict[int, GearRect] = {}
        self.settings_dialogs: dict[int, AxisSettingsDialog] = {}
        self.drag_release_anchor_time = 0

        self.axis_info_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Gotowy.")
        self.smooth_strength_var = tk.DoubleVar(value=0.35)
        self.smooth_passes_var = tk.IntVar(value=2)

        self._build_ui()
        self.update_idletasks()
        self.after_idle(self._refresh_all)

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="TARZAN — EHR", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 16)).pack(side="left")
        tk.Button(
            top,
            text="⚙",
            command=self._open_take_settings,
            bg="#39424E",
            fg=self.FG,
            activebackground="#39424E",
            activeforeground=self.FG,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            font=("Segoe UI Symbol", 12),
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))

        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.BG, width=300)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(left)

        self.timeline_canvas = tk.Canvas(right, bg="#1B2028", highlightthickness=0)
        self.timeline_canvas.pack(fill="both", expand=True)
        self.timeline_canvas.bind("<Configure>", self._on_canvas_configure)
        self.timeline_canvas.bind("<Button-1>", self._on_canvas_press)
        self.timeline_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.timeline_canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        self.timeline_canvas.bind("<Button-3>", self._on_canvas_right_click)

        status = tk.Label(outer, textvariable=self.status_var, bg=self.PANEL2, fg=self.FG, anchor="w", padx=10, pady=8, font=("Segoe UI", 9))
        status.pack(fill="x", pady=(8, 0))

    def _open_take_settings(self) -> None:
        win = tk.Toplevel(self)
        win.title("Ustawienia TAKE")
        win.configure(bg=self.BG)
        win.transient(self)
        win.grab_set()

        minutes_var = tk.DoubleVar(value=self.global_take_duration_ms / 60000.0)

        frame = tk.Frame(win, bg=self.PANEL, padx=16, pady=16)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(
            frame,
            text="GLOBALNY CZAS TAKE (min)",
            bg=self.PANEL,
            fg=self.FG,
            anchor="w",
            font=("Segoe UI Semibold", 10),
        ).pack(fill="x", pady=(0, 6))

        entry = tk.Entry(
            frame,
            textvariable=minutes_var,
            bg="#39424E",
            fg=self.FG,
            relief="flat",
            insertbackground=self.FG,
        )
        entry.pack(fill="x", pady=(0, 10))

        def save() -> None:
            try:
                minutes = float(minutes_var.get())
            except (tk.TclError, ValueError):
                self.status_var.set("Nieprawidłowy globalny czas TAKE.")
                return
            if minutes <= 0:
                self.status_var.set("Globalny czas TAKE musi być dodatni.")
                return
            take_ms = max(1000, int(round(minutes * 60000.0)))
            self.global_take_duration_ms = take_ms
            for axis in self.axis_models:
                axis.set_axis_take_duration_ms(take_ms)
            self._refresh_all(f"Ustawiono globalny czas TAKE: {minutes:.2f} min.")
            for dlg in list(self.settings_dialogs.values()):
                if dlg.winfo_exists():
                    dlg.axis_take_ms.set(dlg.model.take_duration_ms)
                    dlg._refresh_all()
            win.destroy()

        btns = tk.Frame(frame, bg=self.PANEL)
        btns.pack(fill="x")
        self._btn(btns, "ZASTOSUJ DO CAŁEGO TAKE", save, "#0F766E").pack(side="left")
        self._btn(btns, "ZAMKNIJ", win.destroy, "#4B5563").pack(side="right")
        entry.focus_set()

    def _build_left_panel(self, parent: tk.Misc) -> None:
        tk.Label(parent, text="AKTYWNA OŚ", bg=self.BG, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 12)).pack(fill="x", pady=(0, 8))
        active_box = tk.Frame(parent, bg=self.PANEL)
        active_box.pack(fill="x", pady=(0, 10))
        self.active_axis_name_var = tk.StringVar(value=self._active_model().axis_def.axis_name)
        tk.Label(active_box, textvariable=self.active_axis_name_var, bg=self.PANEL, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 10), padx=10, pady=10).pack(fill="x")
        tk.Label(parent, textvariable=self.axis_info_var, bg=self.BG, fg=self.MUTED, justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x", pady=(0, 12))

        self.protocol_label_var = tk.StringVar(value=f"PODGLĄD PROTOKOŁU — {self._active_model().axis_def.axis_name}")
        protocol_label = tk.Label(parent, textvariable=self.protocol_label_var, bg=self.BG, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 11))
        protocol_label.pack(fill="x", pady=(0, 6))

        protocol_box = tk.Frame(parent, bg=self.PANEL)
        protocol_box.pack(fill="both", expand=True, pady=(0, 10))
        self.protocol_text = tk.Text(protocol_box, height=24, bg=self.PANEL, fg=self.FG, relief="flat", wrap="none", font=("Consolas", 8))
        self.protocol_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        protocol_scroll = tk.Scrollbar(protocol_box, orient="vertical", command=self.protocol_text.yview)
        protocol_scroll.pack(side="right", fill="y", padx=(0, 8), pady=8)
        self.protocol_text.configure(yscrollcommand=protocol_scroll.set, state="disabled")

        smooth_box = tk.Frame(parent, bg=self.PANEL)
        smooth_box.pack(fill="x", pady=(0, 10))
        self._btn(smooth_box, "WYGŁADŹ OŚ", self._smooth_active, "#2563EB").pack(fill="x", padx=10, pady=(10, 8))
        self._scale_row(smooth_box, "SIŁA WYGŁADZANIA", self.smooth_strength_var, 0.0, 1.0, 0.05)
        self._scale_row(smooth_box, "ILOŚĆ PRZEJŚĆ", self.smooth_passes_var, 1, 8, 1)

    def _scale_row(self, parent, label, var, from_, to, resolution):
        wrap = tk.Frame(parent, bg=self.PANEL)
        wrap.pack(fill="x", padx=10, pady=6)
        tk.Label(wrap, text=label, bg=self.PANEL, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal", command=lambda _v: self._refresh_all(), bg=self.PANEL, fg=self.FG, troughcolor="#39424E", highlightthickness=0, bd=0, length=280)
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color, activeforeground="white", relief="flat", bd=0, padx=10, pady=6, font=("Segoe UI Semibold", 9), cursor="hand2")

    def _active_model(self) -> AxisCurveModel:
        return self.axis_models[self.active_axis_index]

    def _curve_area_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.timeline_canvas.winfo_width() or 1200))
        h = max(300, int(self.timeline_canvas.winfo_height() or 820))
        return 190, 24, w - 28, h - 38

    def _time_to_x(self, model: AxisCurveModel, t_ms: int, left: int, right: int) -> float:
        span = max(1, model.take_duration_ms)
        return left + (t_ms / span) * (right - left)

    def _x_to_time(self, model: AxisCurveModel, x: float, left: int, right: int) -> int:
        rel = (x - left) / max(1.0, (right - left))
        rel = max(0.0, min(1.0, rel))
        step = model.sample_ms
        return int(round((rel * model.take_duration_ms) / step) * step)

    def _logical_y_to_canvas(self, model: AxisCurveModel, y: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(model.config.y_limit))
        operator_y = float(y) * (operator_range / logical_limit)
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(model.sandbox.top_bottom_margin)
        return mid - (operator_y / operator_range) * usable

    def _canvas_to_logical_y(self, model: AxisCurveModel, py: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(model.config.y_limit))
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(model.sandbox.top_bottom_margin)
        operator_y = ((mid - py) / max(1.0, usable)) * operator_range
        logical_y = operator_y * (logical_limit / operator_range)
        return max(-logical_limit, min(logical_limit, logical_y))

    def _drag_delta_to_logical_y(self, model: AxisCurveModel, delta_py: float, top: int, bottom: int) -> float:
        logical_limit = max(1.0, float(model.config.y_limit))
        usable = (bottom - top) / 2.0 - float(model.sandbox.top_bottom_margin)
        precision = max(0.05, float(model.sandbox.mouse_y_precision))
        logical_per_px = logical_limit / max(1.0, usable)
        return float(delta_py) * logical_per_px * precision

    def _axis_index_from_point(self, x: float, y: float) -> int | None:
        for axis_index, rect in self.axis_rects.items():
            if rect.contains(x, y):
                return axis_index
        return None

    def _gear_axis_from_point(self, x: float, y: float) -> int | None:
        for axis_index, rect in self.gear_rects.items():
            if rect.contains(x, y):
                return axis_index
        return None

    def _hit_node(self, axis_index: int, x: float, y: float) -> int | None:
        if axis_index not in self.axis_rects:
            return None
        rect = self.axis_rects[axis_index]
        model = self.axis_models[axis_index]
        if model.is_release_axis:
            return None
        radius = model.step_tuning.node_hit_radius_px
        for i, n in enumerate(model.nodes):
            px = self._time_to_x(model, n.time_ms, rect.left, rect.right)
            py = self._logical_y_to_canvas(model, n.y, rect.top, rect.bottom)
            if abs(px - x) <= radius and abs(py - y) <= radius:
                return i
        return None

    def _hit_release(self, axis_index: int, x: float, y: float) -> bool:
        if axis_index not in self.axis_rects:
            return False
        model = self.axis_models[axis_index]
        if not model.is_release_axis or model.release_time_ms is None:
            return False
        rect = self.axis_rects[axis_index]
        px = self._time_to_x(model, model.release_time_ms, rect.left, rect.right)
        py = (rect.top + rect.bottom) / 2.0
        return abs(px - x) <= 14 and abs(py - y) <= 14

    def _axis_layout(self) -> list[tuple[int, AxisViewportRect]]:
        left, top, right, bottom = self._curve_area_rect()
        total_h = bottom - top
        gap = 10
        n = max(1, len(self.axis_models))
        band_h = max(72, int((total_h - gap * (n - 1)) / n))
        layout = []
        cur_top = top
        for axis_index in range(n):
            rect = AxisViewportRect(left, cur_top, right, cur_top + band_h)
            layout.append((axis_index, rect))
            cur_top += band_h + gap
        return layout

    def _draw_main_canvas(self) -> None:
        c = self.timeline_canvas
        c.delete("all")
        self.axis_rects.clear()
        self.gear_rects.clear()
        left, top, right, bottom = self._curve_area_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="#303A45")

        active = self._active_model()
        active_total_minutes = max(1, active.take_duration_ms // 60_000)
        for minute in range(0, active_total_minutes + 1):
            t_ms = minute * 60_000
            if t_ms > active.take_duration_ms:
                continue
            px = self._time_to_x(active, t_ms, left, right)
            c.create_line(px, top, px, bottom, fill="#36414C", dash=(2, 6))
            c.create_text(px, bottom + 8, text=f"{minute}m", fill=self.MUTED, anchor="n", font=("Consolas", 8))

        for axis_index, rect in self._axis_layout():
            self.axis_rects[axis_index] = rect
            model = self.axis_models[axis_index]
            is_active = axis_index == self.active_axis_index
            panel_fill = "#232A33" if is_active else "#1C2128"
            c.create_rectangle(rect.left, rect.top, rect.right, rect.bottom, fill=panel_fill, outline="")

            if is_active:
                c.create_line(rect.left, rect.top + 2, rect.left, rect.bottom - 2, fill=model.axis_def.color, width=3)

            mid = (rect.top + rect.bottom) / 2.0
            c.create_line(rect.left, mid, rect.right, mid, fill="#48525E", dash=(4, 5))
            c.create_text(rect.left - 12, mid, text=model.axis_def.axis_name, fill=self.FG, anchor="e", font=("Segoe UI", 9, "bold"))

            if not model.is_release_axis:
                gear = GearRect(rect.left - 44, rect.top + 8, rect.left - 16, rect.top + 36)
                self.gear_rects[axis_index] = gear
                c.create_rectangle(gear.left, gear.top, gear.right, gear.bottom, fill="#39424E", outline="#55606D")
                c.create_text((gear.left + gear.right) / 2.0, (gear.top + gear.bottom) / 2.0, text="⚙", fill=self.FG, font=("Segoe UI Symbol", 12))

            minute_count = max(1, model.take_duration_ms // 60_000)
            for minute in range(0, minute_count + 1):
                t_ms = minute * 60_000
                if t_ms > model.take_duration_ms:
                    continue
                px = self._time_to_x(model, t_ms, rect.left, rect.right)
                c.create_line(px, rect.top, px, rect.bottom, fill="#303842", dash=(2, 6))
                if minute < minute_count:
                    c.create_text(px + 2, rect.top + 4, text=f"{minute}m", fill=self.MUTED, anchor="nw", font=("Consolas", 7))

            if not model.is_release_axis:
                samples = model.sample_curve(900)
                pts: list[float] = []
                for t_ms, y in samples:
                    pts.extend([self._time_to_x(model, t_ms, rect.left, rect.right), self._logical_y_to_canvas(model, y, rect.top, rect.bottom)])
                if len(pts) >= 4:
                    c.create_line(*pts, fill=model.axis_def.color, width=3 if is_active else 2, smooth=True)

                node_r = max(4, min(9, model.step_tuning.node_hit_radius_px // 2))
                for i, n in enumerate(model.nodes):
                    px = self._time_to_x(model, n.time_ms, rect.left, rect.right)
                    py = self._logical_y_to_canvas(model, n.y, rect.top, rect.bottom)
                    fill = self.NODE_SEL if (axis_index == self.drag_axis_index and i == self.selected_index) else self.NODE
                    if i == 0 or i == len(model.nodes) - 1:
                        fill = "#D6EAF8"
                    c.create_oval(px - node_r, py - node_r, px + node_r, py + node_r, fill=fill, outline="black")

            if model.is_release_axis and model.release_time_ms is not None:
                rx = self._time_to_x(model, model.release_time_ms, rect.left, rect.right)
                ry = (rect.top + rect.bottom) / 2.0
                r = 9
                fill = "#F59E0B" if self.drag_mode == 'release' and axis_index == self.drag_axis_index else "#F472B6"
                c.create_polygon(rx, ry - r, rx + r, ry, rx, ry + r, rx - r, ry, fill=fill, outline='black')
                c.create_text(rx + 14, ry - 12, text='RELEASE', fill='#F9A8D4', anchor='w', font=('Segoe UI', 8, 'bold'))

    def _on_canvas_configure(self, _event=None) -> None:
        self._refresh_all()

    def _refresh_axis_info(self) -> None:
        self.active_axis_name_var.set(self._active_model().axis_def.axis_name)
        self.axis_info_var.set(self._active_model().metrics_summary())

    def _refresh_protocol_preview(self) -> None:
        model = self._active_model()
        rows = model.protocol_rows()
        self.protocol_label_var.set(f"PODGLĄD PROTOKOŁU — {model.axis_def.axis_name}")

        if not rows:
            lines = [f"OŚ: {model.axis_def.axis_name}\n", "Brak danych protokołu.\n"]
        else:
            first_active_idx = 0
            for idx, row in enumerate(rows):
                if int(row['step']) == 1 or str(row['event']).strip():
                    first_active_idx = idx
                    break

            pre_roll = 40
            main_window = 420
            start_idx = max(0, first_active_idx - pre_roll)
            end_idx = min(len(rows), start_idx + main_window)
            window_rows = rows[start_idx:end_idx]

            bit_chunks = []
            chunk_size = 64
            for i in range(0, len(window_rows), chunk_size):
                chunk_rows = window_rows[i:i + chunk_size]
                chunk_bits = ''.join(str(int(r['step'])) for r in chunk_rows)
                chunk_time = chunk_rows[0]['time_ms'] if chunk_rows else 0
                bit_chunks.append(f"{chunk_time:7d} ms | {chunk_bits}\n")

            lines = [
                f"OŚ ZAZNACZONA: {model.axis_def.axis_name}\n",
                f"PODGLĄD TEJ OSI — próbka {model.sample_ms} ms\n",
                f"OKNO PODGLĄDU: {window_rows[0]['time_ms']} ms .. {window_rows[-1]['time_ms']} ms\n",
                "\n",
                "STEP STRUMIEŃ 0/1 (każdy znak = 10 ms)\n",
                "----------------------------------------\n",
                *bit_chunks,
                "\n",
                "TIME_MS | DIR | STEP | EVENT\n",
            ]
            for row in window_rows:
                lines.append(f"{row['time_ms']:7d} |  {row['dir']}  |   {row['step']}  | {row['event']}\n")

            if end_idx < len(rows):
                lines.append("...\n")
                tail = rows[-1]
                lines.append(f"{tail['time_ms']:7d} |  {tail['dir']}  |   {tail['step']}  | {tail['event']}\n")

        self.protocol_text.configure(state='normal')
        self.protocol_text.delete('1.0', 'end')
        self.protocol_text.insert('1.0', ''.join(lines))
        self.protocol_text.configure(state='disabled')

    def _refresh_all(self, status: str | None = None) -> None:
        self._refresh_axis_info()
        self._refresh_protocol_preview()
        self._draw_main_canvas()
        self.status_var.set(status if status is not None else "EHR gotowy.")

    def _open_settings(self, axis_index: int) -> None:
        self.active_axis_index = axis_index
        if self.axis_models[axis_index].is_release_axis:
            self._refresh_all(f"Oś {self.axis_models[axis_index].axis_def.axis_name} nie ma okna ustawień.")
            return
        dlg = self.settings_dialogs.get(axis_index)
        if dlg is not None and dlg.winfo_exists():
            dlg.lift()
            dlg.focus_force()
            self._refresh_all(f"Wybrano oś: {self._active_model().axis_def.axis_name}.")
            return
        self.settings_dialogs[axis_index] = AxisSettingsDialog(self, axis_index)
        self._refresh_all(f"Otwarto ustawienia osi: {self._active_model().axis_def.axis_name}.")

    def _on_canvas_press(self, event) -> None:
        gear_axis = self._gear_axis_from_point(event.x, event.y)
        if gear_axis is not None:
            self._open_settings(gear_axis)
            return

        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        self.active_axis_index = axis_index
        model = self.axis_models[axis_index]
        if self._hit_release(axis_index, event.x, event.y):
            self.drag_axis_index = axis_index
            self.selected_index = None
            self.drag_mode = "release"
            self.drag_anchor_x = event.x
            self.drag_release_anchor_time = int(model.release_time_ms or 0)
            self._refresh_all(f"Wybrano RELEASE osi: {model.axis_def.axis_name}.")
            return
        node_index = self._hit_node(axis_index, event.x, event.y)
        if node_index is not None:
            self.drag_axis_index = axis_index
            self.selected_index = node_index
            self.drag_mode = "node"
            self.drag_anchor_x = event.x
            self.drag_anchor_y = event.y
            self.drag_anchor_node_time = int(model.nodes[node_index].time_ms)
            self.drag_anchor_node_y = float(model.nodes[node_index].y)
            self._refresh_all(f"Wybrano punkt osi: {model.axis_def.axis_name}.")
            return
        self.drag_axis_index = axis_index
        self.selected_index = None
        self.drag_mode = "pan"
        self.drag_anchor_x = event.x
        self._refresh_all(f"PAN osi: {model.axis_def.axis_name}.")

    def _on_canvas_drag(self, event) -> None:
        axis_index = self.drag_axis_index
        if axis_index is None or axis_index not in self.axis_rects:
            return
        model = self.axis_models[axis_index]
        rect = self.axis_rects[axis_index]
        if self.drag_mode == "node" and self.selected_index is not None:
            delta_y = self.drag_anchor_y - event.y
            new_y = self.drag_anchor_node_y + self._drag_delta_to_logical_y(model, delta_y, rect.top, rect.bottom)
            delta_t = self._x_to_time(model, event.x, rect.left, rect.right) - self._x_to_time(model, self.drag_anchor_x, rect.left, rect.right)
            threshold_ms = model.sample_ms * model.step_tuning.time_drag_threshold_samples
            new_t = self.drag_anchor_node_time if abs(delta_t) < threshold_ms else self.drag_anchor_node_time + delta_t
            model.move_node(self.selected_index, new_t, new_y)
            self._draw_main_canvas()
        elif self.drag_mode == "release":
            new_time = self._x_to_time(model, event.x, rect.left, rect.right)
            model.set_release_time(new_time)
            self._draw_main_canvas()
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(model, event.x, rect.left, rect.right)
            old_time = self._x_to_time(model, self.drag_anchor_x, rect.left, rect.right)
            delta = new_time - old_time
            self.drag_anchor_x = event.x
            model.shift_all(delta)
            self._draw_main_canvas()

    def _on_canvas_release(self, _event) -> None:
        self.drag_axis_index = None
        self.selected_index = None
        self.drag_mode = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._refresh_all("Gotowy.")

    def _on_canvas_double_click(self, event) -> None:
        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        if self._gear_axis_from_point(event.x, event.y) is not None:
            return
        model = self.axis_models[axis_index]
        rect = self.axis_rects[axis_index]
        self.active_axis_index = axis_index
        t_ms = self._x_to_time(model, event.x, rect.left, rect.right)
        if model.is_release_axis and abs(event.y - ((rect.top + rect.bottom) / 2.0)) <= 20:
            model.set_release_time(t_ms)
            self._refresh_all(f"Ustawiono RELEASE na osi: {model.axis_def.axis_name}.")
            return
        y = self._canvas_to_logical_y(model, event.y, rect.top, rect.bottom)
        model.add_node(t_ms, y)
        self._refresh_all(f"Dodano punkt na osi: {model.axis_def.axis_name}.")

    def _on_canvas_right_click(self, event) -> None:
        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        if self._gear_axis_from_point(event.x, event.y) is not None:
            return
        node_index = self._hit_node(axis_index, event.x, event.y)
        if node_index is None:
            return
        model = self.axis_models[axis_index]
        model.remove_node(node_index)
        self._refresh_all(f"Usunięto punkt z osi: {model.axis_def.axis_name}.")

    def _smooth_active(self) -> None:
        model = self._active_model()
        strength = max(0.0, min(1.0, float(self.smooth_strength_var.get())))
        passes = max(1, min(8, int(self.smooth_passes_var.get())))
        model.smooth_all(strength=strength, passes=passes)
        self._refresh_all(f"Wygładzono przebieg osi: {model.axis_def.axis_name}. siła={strength:.2f} przejścia={passes}.")


def main() -> None:
    app = TarzanEhrMultiAxisWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
