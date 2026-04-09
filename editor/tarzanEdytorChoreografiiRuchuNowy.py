from __future__ import annotations

import copy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from dataclasses import dataclass

from editor.tarzanEhrMultiAxisModel import (
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
        self._refresh_all()
        self.grab_set()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.master_window.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.master_window.BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="TARZAN — SANDBOX OSI", bg=self.master_window.BG, fg=self.master_window.FG, font=("Segoe UI Semibold", 16)).pack(side="left")

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

        status = tk.Label(outer, textvariable=self.status_var, bg=self.master_window.PANEL2, fg=self.master_window.FG, anchor="w", padx=10, pady=8, font=("Segoe UI", 9))
        status.pack(fill="x", pady=(8, 0))

    def _build_left_panel(self, parent: tk.Misc) -> None:
        tk.Label(parent, text=self.model.axis_def.axis_name.upper(), bg=self.master_window.BG, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 12)).pack(fill="x", pady=(0, 8))
        tk.Label(parent, textvariable=self.metrics_var, bg=self.master_window.BG, fg=self.master_window.MUTED, justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x", pady=(0, 12))

        mechanics_box = tk.Frame(parent, bg=self.master_window.PANEL)
        mechanics_box.pack(fill="x", pady=(0, 10))
        tk.Label(mechanics_box, text="MECHANIKA OSI", bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x", padx=10, pady=(8, 4))
        om = tk.OptionMenu(mechanics_box, self.mechanics_preset_var, *MECHANICS_PRESETS.keys())
        om.configure(bg="#39424E", fg=self.master_window.FG, activebackground="#39424E", activeforeground=self.master_window.FG, relief="flat", highlightthickness=0)
        om["menu"].configure(bg="#2A3038", fg=self.master_window.FG)
        om.pack(fill="x", padx=10, pady=(0, 8))
        self._btn(mechanics_box, "WCZYTAJ Z MECHANIKI", self._apply_mechanics_preset, "#2563EB").pack(fill="x", padx=10, pady=(0, 10))

        box = tk.Frame(parent, bg=self.master_window.PANEL)
        box.pack(fill="x", pady=(0, 10))
        self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._apply_view_settings)
        self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._apply_view_settings)
        self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._apply_view_settings)

        info = tk.Text(parent, height=18, bg=self.master_window.PANEL2, fg=self.master_window.FG, relief="flat", wrap="word", font=("Segoe UI", 9))
        info.pack(fill="both", expand=True)
        info.insert(
            "1.0",
            "MODEL SANDBOX\n\n"
            "• amplituda logiczna: -100 .. +100\n"
            "• STEP w próbce 10 ms: tylko 0 lub 1\n"
            "• START = 0, STOP = 0\n"
            "• przejście przez 0 = stop lub zmiana kierunku\n"
            "• pod drugim wykresem są same suwaki\n"
            "• można wczytać bazowe parametry z mechaniki osi\n\n"
            "OBSŁUGA\n\n"
            "• drag punktu = edycja węzła\n"
            "• drag na pustym polu = PAN całej linii\n"
            "• double click = dodaj punkt\n"
            "• right click na punkcie = usuń punkt\n"
            "• zapis TXT zawiera też parametry mechaniki\n"
        )
        info.configure(state="disabled")

    def _build_step_tuning_panel(self, parent: tk.Misc) -> None:
        panel = tk.Frame(parent, bg=self.master_window.PANEL, padx=10, pady=10)
        panel.pack(fill="x", pady=(8, 0))
        tk.Label(panel, text="STROJENIE DRUGIEGO WYKRESU / STEP PREVIEW", bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 10)).pack(fill="x", pady=(0, 8))

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
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal", command=lambda _v: command(), bg=self.master_window.PANEL, fg=self.master_window.FG, troughcolor="#39424E", highlightthickness=0, bd=0, length=240)
        scale.pack(fill="x")

    def _scale_row_grid(self, parent, row, col, label, var, from_, to, resolution, command):
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI", 8, "bold")).pack(fill="x")
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal", command=lambda _v: command(), bg=self.master_window.PANEL, fg=self.master_window.FG, troughcolor="#39424E", highlightthickness=0, bd=0, length=300)
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color, activeforeground="white", relief="flat", bd=0, padx=10, pady=6, font=("Segoe UI Semibold", 9), cursor="hand2")

    def _curve_rect(self):
        w = max(300, int(self.curve_canvas.winfo_width() or 1200))
        h = max(220, int(self.curve_canvas.winfo_height() or 430))
        return 70, 14, w - 20, h - 20

    def _step_rect(self):
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
        operator_range = max(200.0, float(self.display_y_scale.get()))
        logical_limit = max(1.0, float(self.model.config.y_limit))
        operator_y = float(y) * (operator_range / logical_limit)
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.top_bottom_margin.get())
        return mid - (operator_y / operator_range) * usable

    def _canvas_to_logical_y(self, py: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(self.display_y_scale.get()))
        logical_limit = max(1.0, float(self.model.config.y_limit))
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.top_bottom_margin.get())
        operator_y = ((mid - py) / max(1.0, usable)) * operator_range
        logical_y = operator_y * (logical_limit / operator_range)
        return self.model.clamp_y(logical_y)

    def _drag_delta_to_logical_y(self, delta_py: float, top: int, bottom: int) -> float:
        logical_limit = max(1.0, float(self.model.config.y_limit))
        usable = (bottom - top) / 2.0 - float(self.top_bottom_margin.get())
        precision = max(0.05, float(self.mouse_y_precision.get()))
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

    def _apply_view_settings(self) -> None:
        self.model.sandbox.display_y_scale = float(self.display_y_scale.get())
        self.model.sandbox.mouse_y_precision = float(self.mouse_y_precision.get())
        self.model.sandbox.top_bottom_margin = int(self.top_bottom_margin.get())
        self._refresh_all("Zmieniono ustawienia widoku osi.")
        self.master_window._refresh_all(f"Zmieniono ustawienia SANDBOX dla osi: {self.model.axis_def.axis_name}.")

    def _apply_step_tuning_live(self) -> None:
        tuning = self._read_step_tuning_from_ui()
        self.model.set_step_tuning(tuning)
        self._refresh_all("Zastosowano strojenie STEP.")

    def _apply_mechanics_preset(self) -> None:
        mechanics = copy.deepcopy(MECHANICS_PRESETS[self.mechanics_preset_var.get()])
        self.model.set_mechanics(mechanics)
        self.display_y_scale.set(self.model.sandbox.display_y_scale)
        self.mouse_y_precision.set(self.model.sandbox.mouse_y_precision)
        self.top_bottom_margin.set(self.model.sandbox.top_bottom_margin)
        self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.")
        self.master_window._refresh_all(f"Wczytano parametry mechaniki dla osi: {self.model.axis_def.axis_name}.")

    def _save_tuning_txt(self) -> None:
        tuning = self._read_step_tuning_from_ui()
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], title="Zapisz preset STEP do TXT")
        if not path:
            return
        Path(path).write_text(tuning.to_text(self.model.mechanics), encoding="utf-8")
        self.status_var.set(f"Zapisano preset TXT: {path}")

    def _load_tuning_txt(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")], title="Wczytaj preset STEP z TXT")
        if not path:
            return
        tuning, mechanics = StepTuning.from_text(Path(path).read_text(encoding="utf-8"))
        if mechanics is not None:
            self.model.set_mechanics(mechanics)
            self.mechanics_preset_var.set(mechanics.axis_name)
        self._write_step_tuning_to_ui(tuning)
        self.model.set_step_tuning(tuning)
        self._refresh_all(f"Wczytano preset TXT: {path}")
        self.master_window._refresh_all(f"Wczytano preset osi: {self.model.axis_def.axis_name}.")

    def _reset_step_tuning(self) -> None:
        tuning = StepTuning()
        self._write_step_tuning_to_ui(tuning)
        self.model.set_step_tuning(tuning)
        self._refresh_all("Przywrócono domyślne parametry STEP.")

    def _draw_curve(self) -> None:
        c = self.curve_canvas
        c.delete("all")
        left, top, right, bottom = self._curve_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="#303A45")

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

        for minute in range(0, int(self.model.mechanics.min_full_cycle_time_s // 60) + 1):
            t_ms = minute * 60_000
            if t_ms > self.model.take_duration_ms:
                continue
            px = self._time_to_x(t_ms, left, right)
            c.create_line(px, top, px, bottom, fill="#43505C", dash=(2, 6))
            c.create_text(px, bottom + 10, text=f"{minute}m", fill=self.master_window.MUTED, anchor="n", font=("Consolas", 8))

        samples = self.model.sample_curve(1000)
        pts = []
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

    def _refresh_metrics(self) -> None:
        self.metrics_var.set(self.model.metrics_summary())

    def _refresh_all(self, status: str | None = None) -> None:
        self.model.sort_and_fix_nodes()
        self._draw_curve()
        self._refresh_metrics()
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

    def _sinus_test(self) -> None:
        self.model.set_sinus_test()
        self.model.clone_original_state()
        self._refresh_all("Sinus test ustawiony.")
        self.master_window._refresh_all(f"Sinus test ustawiony dla osi: {self.model.axis_def.axis_name}.")

    def _negative_test(self) -> None:
        self.model.set_negative_test()
        self.model.clone_original_state()
        self._refresh_all("Negative test ustawiony.")
        self.master_window._refresh_all(f"Negative test ustawiony dla osi: {self.model.axis_def.axis_name}.")

    def _zero_cross_test(self) -> None:
        self.model.set_zero_cross_test()
        self.model.clone_original_state()
        self._refresh_all("Zero cross test ustawiony.")
        self.master_window._refresh_all(f"Zero cross test ustawiony dla osi: {self.model.axis_def.axis_name}.")

    def _flat_zero(self) -> None:
        self.model.set_flat_zero()
        self.model.clone_original_state()
        self._refresh_all("Linia wyzerowana.")
        self.master_window._refresh_all(f"Linia wyzerowana dla osi: {self.model.axis_def.axis_name}.")

    def _reset_nodes(self) -> None:
        self.model.reset_to_original_state()
        self._refresh_all("Przywrócono ostatni stan bazowy.")
        self.master_window._refresh_all(f"Przywrócono stan bazowy osi: {self.model.axis_def.axis_name}.")

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
        self.master_window._refresh_all(f"Zakończono edycję osi: {self.model.axis_def.axis_name}.")

    def _on_curve_double_click(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        t = self._x_to_time(event.x, left, right)
        y = self._canvas_to_logical_y(event.y, top, bottom)
        self.model.add_node(t, y)
        self._refresh_all("Dodano punkt.")
        self.master_window._refresh_all(f"Dodano punkt na osi: {self.model.axis_def.axis_name}.")

    def _on_curve_right_click(self, event) -> None:
        idx = self._hit_node(event.x, event.y)
        if idx is None:
            return
        self.model.remove_node(idx)
        self.selected_index = None
        self._refresh_all("Usunięto punkt.")
        self.master_window._refresh_all(f"Usunięto punkt z osi: {self.model.axis_def.axis_name}.")

    def _on_close(self) -> None:
        self.master_window._unregister_settings_dialog(self.axis_index)
        self.destroy()


class TarzanEhrMultiAxisWindow(tk.Tk):
    BG = "#16181C"
    PANEL = "#23272E"
    PANEL2 = "#2A3038"
    FG = "#F3F6F8"
    MUTED = "#AEB7C2"
    GRID = "#3C4652"
    STRIP_BG = "#1C222B"
    STRIP_ACTIVE = "#232B36"
    ZERO = "#A94442"
    START = "#45C46B"
    STOP = "#E65D5D"
    NODE = "#FFD166"
    NODE_SEL = "#FF9F1C"
    TEXT_DARK = "#0D1117"
    GEAR_BG = "#374151"
    GEAR_BG_ACTIVE = "#4B5563"
    CURVE = "#D9E7F5"
    STEP_ON = "#45C46B"
    STEP_OFF = "#48525E"
    SAFE = "#1E3A2F"
    WARN = "#5A4A1B"
    DANGER = "#4A2222"

    def __init__(self) -> None:
        super().__init__()
        self.title("TARZAN — Nowy EHR Multi Axis")
        self.geometry("1850x980")
        self.configure(bg=self.BG)
        self.minsize(1500, 860)

        self.config_model = EhrEditorConfig()
        self.axis_models: list[AxisCurveModel] = [AxisCurveModel(axis_def, self.config_model) for axis_def in DEFAULT_AXIS_DEFINITIONS]
        for model in self.axis_models:
            model.clone_original_state()

        self.active_axis_index = 0
        self.selected_index: int | None = None
        self.drag_axis_index: int | None = None
        self.drag_mode: str | None = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self.drag_anchor_node_time = 0
        self.drag_anchor_node_y = 0.0

        self.status_var = tk.StringVar(value="Gotowy.")
        self.axis_info_var = tk.StringVar(value="")
        self.smooth_strength = tk.DoubleVar(value=0.45)
        self.smooth_passes = tk.IntVar(value=1)

        self.canvas_axis_rects: list[AxisViewportRect] = []
        self.axis_gear_rects: dict[int, GearRect] = {}
        self.axis_dialogs: dict[int, AxisSettingsDialog] = {}

        self._build_ui()
        self._refresh_all()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="TARZAN — NOWY EHR MULTI AXIS", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 16)).pack(side="left")

        actions = tk.Frame(top, bg=self.BG)
        actions.pack(side="right")
        self._btn(actions, "WYGŁADŹ AKTYWNĄ OŚ", self._smooth_active, "#2F855A").pack(side="left", padx=3)
        self._btn(actions, "USTAWIENIA AKTYWNEJ OSI", self._open_active_axis_settings, "#4B5563").pack(side="left", padx=3)

        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.BG, width=340)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(left)

        self.timeline_canvas = tk.Canvas(right, bg="#1B2028", highlightthickness=0, relief="flat")
        self.timeline_canvas.pack(fill="both", expand=True)
        self.timeline_canvas.bind("<Button-1>", self._on_canvas_press)
        self.timeline_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.timeline_canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        self.timeline_canvas.bind("<Button-3>", self._on_canvas_right_click)

        status = tk.Label(outer, textvariable=self.status_var, bg=self.PANEL2, fg=self.FG, anchor="w", padx=10, pady=8, font=("Segoe UI", 9))
        status.pack(fill="x", pady=(8, 0))

    def _build_left_panel(self, parent: tk.Misc) -> None:
        tk.Label(parent, text="OSIE", bg=self.BG, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 12)).pack(fill="x", pady=(0, 8))

        axis_list_wrap = tk.Frame(parent, bg=self.PANEL)
        axis_list_wrap.pack(fill="x", pady=(0, 10))

        self.axis_listbox = tk.Listbox(axis_list_wrap, height=8, activestyle="none", bg=self.PANEL, fg=self.FG, selectbackground="#364152", selectforeground=self.FG, highlightthickness=0, relief="flat", font=("Segoe UI", 10), exportselection=False)
        self.axis_listbox.pack(fill="x", padx=8, pady=8)
        for model in self.axis_models:
            self.axis_listbox.insert("end", model.axis_def.axis_name)
        self.axis_listbox.selection_set(0)
        self.axis_listbox.bind("<<ListboxSelect>>", self._on_axis_list_select)

        tk.Label(parent, textvariable=self.axis_info_var, bg=self.BG, fg=self.MUTED, justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x", pady=(0, 12))

        smooth_box = tk.Frame(parent, bg=self.PANEL)
        smooth_box.pack(fill="x", pady=(0, 10))
        self._scale_row(smooth_box, "WYGŁADŹ STRENGTH", self.smooth_strength, 0.05, 0.95, 0.05)
        self._scale_row(smooth_box, "WYGŁADŹ PASSES", self.smooth_passes, 1, 8, 1)

        info = tk.Text(parent, height=16, bg=self.PANEL2, fg=self.FG, relief="flat", wrap="word", font=("Segoe UI", 9))
        info.pack(fill="both", expand=True)
        info.insert(
            "1.0",
            "NOWY EHR\n\n"
            "• wiele osi jednocześnie na wspólnej osi czasu\n"
            "• każda oś ma własną ciągłą linię i własne węzły\n"
            "• zachowanie myszy jak w SANDBOX\n"
            "• drag pustego pola w pasku osi = PAN tylko tej osi\n"
            "• każda oś ma pełne ustawienia SANDBOX pod ikoną zębatki\n"
            "• Wygładź działa na cały przebieg bez dodawania punktów\n"
            "• brak TAKE / STEP / hardware na tym etapie\n"
        )
        info.configure(state="disabled")

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

    def _build_axis_rects(self) -> list[AxisViewportRect]:
        left, top, right, bottom = self._curve_area_rect()
        count = max(1, len(self.axis_models))
        gap = 10
        usable_h = bottom - top
        strip_h = max(76, int((usable_h - gap * (count - 1)) / count))
        rects: list[AxisViewportRect] = []
        cur_top = top
        for _ in range(count):
            cur_bottom = min(bottom, cur_top + strip_h)
            rects.append(AxisViewportRect(left, cur_top, right, cur_bottom))
            cur_top = cur_bottom + gap
        return rects

    def _draw_gear_button(self, axis_index: int, rect: AxisViewportRect, active: bool) -> None:
        c = self.timeline_canvas
        size = 24
        pad = 8
        gear = GearRect(left=rect.left + pad, top=rect.top + pad, right=rect.left + pad + size, bottom=rect.top + pad + size)
        self.axis_gear_rects[axis_index] = gear
        fill = self.GEAR_BG_ACTIVE if active else self.GEAR_BG
        c.create_rectangle(gear.left, gear.top, gear.right, gear.bottom, fill=fill, outline="#6B7280", width=1)
        c.create_text((gear.left + gear.right) / 2.0, (gear.top + gear.bottom) / 2.0, text="⚙", fill=self.FG, font=("Segoe UI Symbol", 11))

    def _draw_axes(self) -> None:
        c = self.timeline_canvas
        c.delete("all")
        left, top, right, bottom = self._curve_area_rect()
        self.canvas_axis_rects = self._build_axis_rects()
        self.axis_gear_rects = {}

        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="#303A45")

        max_duration = max((m.take_duration_ms for m in self.axis_models), default=0)
        for minute in range(0, int(max_duration // 60000) + 1):
            t_ms = minute * 60_000
            px = left + ((t_ms / max(1, max_duration)) * (right - left))
            c.create_line(px, top, px, bottom, fill=self.GRID, dash=(2, 6))
            c.create_text(px, bottom + 10, text=f"{minute}m", fill=self.MUTED, anchor="n", font=("Consolas", 8))

        c.create_line(left, top, left, bottom, fill=self.START, width=3)
        c.create_line(right, top, right, bottom, fill=self.STOP, width=3)
        c.create_text(left + 4, top - 8, text="START", fill=self.START, anchor="sw", font=("Segoe UI", 8, "bold"))
        c.create_text(right - 4, top - 8, text="STOP", fill=self.STOP, anchor="se", font=("Segoe UI", 8, "bold"))

        for axis_index, (model, rect) in enumerate(zip(self.axis_models, self.canvas_axis_rects)):
            active = axis_index == self.active_axis_index
            strip_fill = self.STRIP_ACTIVE if active else self.STRIP_BG
            c.create_rectangle(rect.left, rect.top, rect.right, rect.bottom, fill=strip_fill, outline="#2F3843")
            self._draw_gear_button(axis_index, rect, active)

            mid_y = (rect.top + rect.bottom) / 2.0
            c.create_line(rect.left, mid_y, rect.right, mid_y, fill=self.ZERO, width=1)
            c.create_text(rect.left - 12, rect.top + (rect.bottom - rect.top) / 2.0, text=model.axis_def.axis_name, fill=model.axis_def.color, anchor="e", font=("Segoe UI Semibold", 9))

            for yv in (-100, 100):
                py = self._logical_y_to_canvas(model, yv, rect.top, rect.bottom)
                c.create_line(rect.left, py, rect.right, py, fill="#343C48", dash=(4, 4))

            samples = model.sample_curve(700)
            pts = []
            for t_ms, y in samples:
                pts.extend([self._time_to_x(model, t_ms, rect.left, rect.right), self._logical_y_to_canvas(model, y, rect.top, rect.bottom)])
            if len(pts) >= 4:
                c.create_line(*pts, fill=model.axis_def.color, width=3, smooth=True)

            hit_radius = model.step_tuning.node_hit_radius_px
            r = max(4, min(10, hit_radius // 2)) if active else 5
            for node_index, node in enumerate(model.nodes):
                px = self._time_to_x(model, node.time_ms, rect.left, rect.right)
                py = self._logical_y_to_canvas(model, node.y, rect.top, rect.bottom)
                fill = self.NODE
                if axis_index == self.drag_axis_index and node_index == self.selected_index:
                    fill = self.NODE_SEL
                if node_index == 0 or node_index == len(model.nodes) - 1:
                    fill = "#D6EAF8"
                c.create_oval(px - r, py - r, px + r, py + r, fill=fill, outline=self.TEXT_DARK)

    def _refresh_axis_info(self) -> None:
        self.axis_info_var.set(self._active_model().metrics_summary())

    def _refresh_all(self, status: str | None = None) -> None:
        for model in self.axis_models:
            model.sort_and_fix_nodes()
        self._draw_axes()
        self._refresh_axis_info()
        self.status_var.set("Nowy EHR gotowy." if status is None else status)

    def _set_active_axis(self, axis_index: int) -> None:
        axis_index = max(0, min(len(self.axis_models) - 1, axis_index))
        self.active_axis_index = axis_index
        self.axis_listbox.selection_clear(0, "end")
        self.axis_listbox.selection_set(axis_index)
        self.axis_listbox.activate(axis_index)

    def _on_axis_list_select(self, _event) -> None:
        selection = self.axis_listbox.curselection()
        if not selection:
            return
        self._set_active_axis(selection[0])
        self.selected_index = None
        self.drag_axis_index = None
        self._refresh_all("Wybrano oś z listy.")

    def _axis_index_from_point(self, x: float, y: float) -> int | None:
        for idx, rect in enumerate(self.canvas_axis_rects):
            if rect.left <= x <= rect.right and rect.top <= y <= rect.bottom:
                return idx
        return None

    def _gear_axis_from_point(self, x: float, y: float) -> int | None:
        for axis_index, gear in self.axis_gear_rects.items():
            if gear.contains(x, y):
                return axis_index
        return None

    def _hit_node(self, axis_index: int, x: float, y: float) -> int | None:
        rect = self.canvas_axis_rects[axis_index]
        model = self.axis_models[axis_index]
        radius = model.step_tuning.node_hit_radius_px
        for node_index, node in enumerate(model.nodes):
            px = self._time_to_x(model, node.time_ms, rect.left, rect.right)
            py = self._logical_y_to_canvas(model, node.y, rect.top, rect.bottom)
            if abs(px - x) <= radius and abs(py - y) <= radius:
                return node_index
        return None

    def _open_axis_settings(self, axis_index: int) -> None:
        self._set_active_axis(axis_index)
        existing = self.axis_dialogs.get(axis_index)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return
        dialog = AxisSettingsDialog(self, axis_index)
        self.axis_dialogs[axis_index] = dialog

    def _open_active_axis_settings(self) -> None:
        self._open_axis_settings(self.active_axis_index)

    def _unregister_settings_dialog(self, axis_index: int) -> None:
        self.axis_dialogs.pop(axis_index, None)

    def _on_canvas_press(self, event) -> None:
        gear_axis_index = self._gear_axis_from_point(event.x, event.y)
        if gear_axis_index is not None:
            self._open_axis_settings(gear_axis_index)
            self.selected_index = None
            self.drag_axis_index = None
            self.drag_mode = None
            return

        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return

        self._set_active_axis(axis_index)
        self.drag_axis_index = axis_index

        node_index = self._hit_node(axis_index, event.x, event.y)
        model = self.axis_models[axis_index]

        if node_index is not None:
            self.selected_index = node_index
            self.drag_mode = "node"
            self.drag_anchor_x = event.x
            self.drag_anchor_y = event.y
            self.drag_anchor_node_time = int(model.nodes[node_index].time_ms)
            self.drag_anchor_node_y = float(model.nodes[node_index].y)
            self._refresh_all(f"Wybrano punkt {node_index} na osi: {model.axis_def.axis_name}.")
            return

        self.selected_index = None
        self.drag_mode = "pan"
        self.drag_anchor_x = event.x
        self.drag_anchor_y = event.y
        self._refresh_all(f"PAN osi: {model.axis_def.axis_name}.")

    def _on_canvas_drag(self, event) -> None:
        if self.drag_axis_index is None:
            return
        axis_index = self.drag_axis_index
        rect = self.canvas_axis_rects[axis_index]
        model = self.axis_models[axis_index]
        tuning = model.step_tuning

        if self.drag_mode == "node" and self.selected_index is not None:
            delta_y = self.drag_anchor_y - event.y
            new_y = self.drag_anchor_node_y + self._drag_delta_to_logical_y(model, delta_y, rect.top, rect.bottom)
            delta_t = self._x_to_time(model, event.x, rect.left, rect.right) - self._x_to_time(model, self.drag_anchor_x, rect.left, rect.right)
            threshold_ms = model.sample_ms * tuning.time_drag_threshold_samples
            new_t = self.drag_anchor_node_time if abs(delta_t) < threshold_ms else self.drag_anchor_node_time + delta_t
            model.move_node(self.selected_index, new_t, new_y)
            self._draw_axes()
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(model, event.x, rect.left, rect.right)
            old_time = self._x_to_time(model, self.drag_anchor_x, rect.left, rect.right)
            delta = new_time - old_time
            self.drag_anchor_x = event.x
            model.shift_all(delta)
            self._draw_axes()

    def _on_canvas_release(self, _event) -> None:
        self.drag_mode = None
        self.drag_axis_index = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._refresh_all("Gotowy.")

    def _on_canvas_double_click(self, event) -> None:
        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        if self._gear_axis_from_point(event.x, event.y) is not None:
            return
        self._set_active_axis(axis_index)
        rect = self.canvas_axis_rects[axis_index]
        model = self.axis_models[axis_index]
        t_ms = self._x_to_time(model, event.x, rect.left, rect.right)
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
        self.selected_index = None
        self.drag_axis_index = None
        self._refresh_all(f"Usunięto punkt z osi: {model.axis_def.axis_name}.")

    def _smooth_active(self) -> None:
        model = self._active_model()
        model.smooth_all(strength=float(self.smooth_strength.get()), passes=int(self.smooth_passes.get()))
        self._refresh_all(f"Wygładzono przebieg osi: {model.axis_def.axis_name}.")


def main() -> None:
    app = TarzanEhrMultiAxisWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
