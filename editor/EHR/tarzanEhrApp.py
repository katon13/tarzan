from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from editor.EHR.tarzanEhrMainTakeSettings import MainTakeSettings
from editor.EHR.tarzanEhrMainTakeSettingsDialog import MainTakeSettingsDialog
from editor.EHR.tarzanEhrMultiAxisModel import (
    AxisCurveModel,
    DEFAULT_AXIS_DEFINITIONS,
    EhrEditorConfig,
    MECHANICS_PRESETS,
    StepTuning,
)
from editor.EHR.tarzanEhrTakeModel import EhrTakeModel

try:
    from core.tarzanProfiler import profile_method
except Exception:
    def profile_method(name=None):
        def decorator(func):
            return func
        return decorator


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


@dataclass
class WaveRect:
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
        self.geometry("1880x1120")
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
        self._drag_zero_snap_locked = False
        self.drag_anchor_node_time = 0
        self.drag_anchor_node_y = 0.0
        self._drag_zero_snap_locked = False
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._curve_redraw_after_id = None

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
            text="TARZAN — USTAWIENIA OSI",
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
        self._btn(btns, "SET UP -> MAIN TAKE", self._apply_to_main_take, "#047857").pack(side="left", padx=3)
        self._btn(btns, "ZAMKNIJ", self._on_close, "#4B5563").pack(side="left", padx=3)

        body = tk.Frame(outer, bg=self.master_window.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.master_window.BG, width=210)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=self.master_window.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(left)

        self.curve_canvas = tk.Canvas(right, bg="#1B2028", width=1520, height=420, highlightthickness=0)
        self.curve_canvas.pack(fill="both", expand=True, pady=(0, 8))
        self.curve_canvas.bind("<Button-1>", self._on_curve_press)
        self.curve_canvas.bind("<B1-Motion>", self._on_curve_drag)
        self.curve_canvas.bind("<ButtonRelease-1>", self._on_curve_release)
        self.curve_canvas.bind("<Double-Button-1>", self._on_curve_double_click)
        self.curve_canvas.bind("<Button-3>", self._on_curve_right_click)

        self.step_canvas = tk.Canvas(right, bg="#1A1E24", width=1520, height=255, highlightthickness=0)
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
        tk.Label(parent, text=self.model.axis_def.axis_name.upper(), bg=self.master_window.BG, fg=self.master_window.FG,
                 anchor="w", font=("Segoe UI Semibold", 12)).pack(fill="x", pady=(0, 8))
        tk.Label(parent, textvariable=self.metrics_var, bg=self.master_window.BG, fg=self.master_window.MUTED,
                 justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x", pady=(0, 12))

        mechanics_box = tk.Frame(parent, bg=self.master_window.PANEL)
        mechanics_box.pack(fill="x", pady=(0, 10))
        tk.Label(mechanics_box, text="MECHANIKA OSI", bg=self.master_window.PANEL, fg=self.master_window.FG,
                 anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x", padx=10, pady=(8, 4))
        available_mechanics = [name for name in MECHANICS_PRESETS.keys() if name != "oś wzorcowa"]
        om = tk.OptionMenu(mechanics_box, self.mechanics_preset_var, *available_mechanics)
        om.configure(bg="#39424E", fg=self.master_window.FG, activebackground="#39424E",
                     activeforeground=self.master_window.FG, relief="flat", highlightthickness=0)
        om["menu"].configure(bg="#2A3038", fg=self.master_window.FG)
        om.pack(fill="x", padx=10, pady=(0, 8))
        self._btn(mechanics_box, "WCZYTAJ Z MECHANIKI", self._apply_mechanics_preset, "#2563EB").pack(fill="x", padx=10, pady=(0, 10))

        box = tk.Frame(parent, bg=self.master_window.PANEL)
        box.pack(fill="x", pady=(0, 10))
        self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._apply_visual_settings)
        self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._apply_visual_settings)
        self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._apply_visual_settings)

        save_row = tk.Frame(parent, bg=self.master_window.BG)
        save_row.pack(fill="x", pady=(0, 10))
        self._small_btn(save_row, "SAVE JSON", self._save_axis_settings_json, "#0F766E").pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._small_btn(save_row, "LOAD JSON", self._load_axis_settings_json, "#7C3AED").pack(side="left", fill="x", expand=True)

    def _build_step_tuning_panel(self, parent: tk.Misc) -> None:
        panel = tk.Frame(parent, bg=self.master_window.PANEL, padx=10, pady=10)
        panel.pack(fill="x", pady=(8, 0))
        tk.Label(panel, text="STROJENIE DRUGIEGO WYKRESU / STEP PREVIEW", bg=self.master_window.PANEL,
                 fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 10)).pack(fill="x", pady=(0, 8))
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
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                         command=lambda _v: command(), bg=self.master_window.PANEL, fg=self.master_window.FG,
                         troughcolor="#39424E", highlightthickness=0, bd=0, length=240)
        scale.pack(fill="x")

    def _scale_row_grid(self, parent, row, col, label, var, from_, to, resolution, command):
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w",
                 font=("Segoe UI", 8, "bold")).pack(fill="x")
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                         command=lambda _v: command(), bg=self.master_window.PANEL, fg=self.master_window.FG,
                         troughcolor="#39424E", highlightthickness=0, bd=0, length=300)
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=10, pady=6,
                         font=("Segoe UI Semibold", 9), cursor="hand2")

    def _small_btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=8, pady=4,
                         font=("Segoe UI Semibold", 8), cursor="hand2")

    def _curve_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.curve_canvas.winfo_width() or 1200))
        h = max(220, int(self.curve_canvas.winfo_height() or 430))
        return 70, 14, w - 20, h - 20

    def _step_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.step_canvas.winfo_width() or 1200))
        h = max(120, int(self.step_canvas.winfo_height() or 260))
        return 70, 16, w - 20, h - 24

    def _time_to_x(self, t_ms: int, left: int, right: int) -> float:
        span = max(1, self.master_window.global_take_duration_ms)
        return left + (t_ms / span) * (right - left)

    def _x_to_time(self, x: float, left: int, right: int) -> int:
        rel = (x - left) / max(1.0, (right - left))
        rel = max(0.0, min(1.0, rel))
        return self.model.snap_time(rel * self.master_window.global_take_duration_ms)

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
        return self.model.apply_zero_snap(self.master_window.main_take_settings, self.model.clamp_y(logical_y))

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

    def _mark_main_take_dirty(self, status: str | None = None) -> None:
        self.master_window.mark_axis_dirty(self.axis_index, status=status)

    def _apply_to_main_take(self) -> None:
        self.master_window.sync_axis_from_dialog(self.axis_index, status=f"Zaktualizowano MAIN TAKE z osi: {self.model.axis_def.axis_name}.")

    def _apply_visual_settings(self) -> None:
        self.model.sandbox.display_y_scale = float(self.display_y_scale.get())
        self.model.sandbox.mouse_y_precision = float(self.mouse_y_precision.get())
        self.model.sandbox.top_bottom_margin = int(self.top_bottom_margin.get())
        self._curve_needs_redraw = True
        self._refresh_all("Zastosowano ustawienia osi.")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _apply_step_tuning_live(self) -> None:
        self.model.set_step_tuning(self._read_step_tuning_from_ui())
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Zastosowano strojenie STEP.")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _apply_mechanics_preset(self) -> None:
        mechanics = copy.deepcopy(MECHANICS_PRESETS[self.mechanics_preset_var.get()])
        self.model.set_mechanics(mechanics)
        self.model.set_axis_take_duration_ms(self.master_window.global_take_duration_ms)
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.")
        self._mark_main_take_dirty(f"Mechanika osi gotowa. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE: {mechanics.axis_name}.")


    def _axis_settings_to_json_text(self) -> str:
        payload = {
            "format": "AXIS_SANDBOX_SETTINGS_JSON_V1",
            "axis_id": self.model.axis_def.axis_id,
            "axis_name": self.model.axis_def.axis_name,
            "visual": {
                "display_y_scale": float(self.display_y_scale.get()),
                "mouse_y_precision": float(self.mouse_y_precision.get()),
                "top_bottom_margin": int(self.top_bottom_margin.get()),
            },
            "step_tuning": {key: getattr(self.model.step_tuning, key) for key in self.step_vars},
            "mechanics": {
                "axis_name": self.model.mechanics.axis_name,
                "full_cycle_pulses": self.model.mechanics.full_cycle_pulses,
                "min_full_cycle_time_s": self.model.mechanics.min_full_cycle_time_s,
                "start_settle_ms": self.model.mechanics.start_settle_ms,
                "start_ramp_ms": self.model.mechanics.start_ramp_ms,
                "sample_ms": self.model.mechanics.sample_ms,
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    def _load_axis_settings_from_json_text(self, text: str) -> None:
        data = json.loads(text)
        visual = dict(data.get("visual") or {})
        if "display_y_scale" in visual:
            self.display_y_scale.set(float(visual["display_y_scale"]))
        if "mouse_y_precision" in visual:
            self.mouse_y_precision.set(float(visual["mouse_y_precision"]))
        if "top_bottom_margin" in visual:
            self.top_bottom_margin.set(int(float(visual["top_bottom_margin"])))

        self.model.sandbox.display_y_scale = float(self.display_y_scale.get())
        self.model.sandbox.mouse_y_precision = float(self.mouse_y_precision.get())
        self.model.sandbox.top_bottom_margin = int(self.top_bottom_margin.get())

        step_data = dict(data.get("step_tuning") or {})
        tuning = StepTuning()
        for key, value in step_data.items():
            if hasattr(tuning, key):
                setattr(tuning, key, value)
        tuning.clamp()
        self._write_step_tuning_to_ui(tuning)
        self.model.set_step_tuning(tuning)

        mechanics_data = dict(data.get("mechanics") or {})
        if mechanics_data:
            try:
                mechanics = self.model.mechanics.__class__(
                    axis_name=str(mechanics_data.get("axis_name", self.model.mechanics.axis_name)),
                    full_cycle_pulses=int(mechanics_data.get("full_cycle_pulses", self.model.mechanics.full_cycle_pulses)),
                    min_full_cycle_time_s=float(mechanics_data.get("min_full_cycle_time_s", self.model.mechanics.min_full_cycle_time_s)),
                    start_settle_ms=int(mechanics_data.get("start_settle_ms", self.model.mechanics.start_settle_ms)),
                    start_ramp_ms=int(mechanics_data.get("start_ramp_ms", self.model.mechanics.start_ramp_ms)),
                    sample_ms=int(mechanics_data.get("sample_ms", self.model.mechanics.sample_ms)),
                )
                self.model.set_mechanics(mechanics)
                self.mechanics_preset_var.set(mechanics.axis_name)
                self.model.set_axis_take_duration_ms(self.master_window.global_take_duration_ms)
            except Exception:
                pass

    def _save_axis_settings_json(self) -> None:
        default_name = self.model.axis_def.axis_name.replace(" ", "_") + "_axis_settings.json"
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir=str(self._default_data_dir()),
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Zapisz ustawienia osi do JSON",
        )
        if not path:
            return
        Path(path).write_text(self._axis_settings_to_json_text(), encoding="utf-8")
        self.status_var.set(f"Zapisano ustawienia osi: {path}")

    def _load_axis_settings_json(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(self._default_data_dir()),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Wczytaj ustawienia osi z JSON",
        )
        if not path:
            return
        self._load_axis_settings_from_json_text(Path(path).read_text(encoding="utf-8"))
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all(f"Wczytano ustawienia osi: {path}")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _save_tuning_txt(self) -> None:
        tuning = self.model.step_tuning
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
            self.model.set_axis_take_duration_ms(self.master_window.global_take_duration_ms)
        self._write_step_tuning_to_ui(tuning)
        self.model.set_step_tuning(tuning)
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all(f"Wczytano preset TXT: {path}")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _reset_step_tuning(self) -> None:
        tuning = StepTuning()
        self._write_step_tuning_to_ui(tuning)
        self.model.set_step_tuning(tuning)
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Przywrócono domyślne parametry STEP.")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _sinus_test(self) -> None:
        self.model.set_sinus_test()
        self.model.clone_original_state()
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Sinus test ustawiony.")
        self._mark_main_take_dirty("Sinus test gotowy lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _negative_test(self) -> None:
        self.model.set_negative_test()
        self.model.clone_original_state()
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Negative test ustawiony.")
        self._mark_main_take_dirty("Negative test gotowy lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _zero_cross_test(self) -> None:
        self.model.set_zero_cross_test()
        self.model.clone_original_state()
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Zero cross test ustawiony.")
        self._mark_main_take_dirty("Zero cross test gotowy lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _flat_zero(self) -> None:
        self.model.set_flat_zero()
        self.model.clone_original_state()
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Linia wyzerowana.")
        self._mark_main_take_dirty("Linia osi wyzerowana lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _reset_nodes(self) -> None:
        self.model.reset_to_original_state()
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Przywrócono ostatni stan bazowy.")
        self._mark_main_take_dirty("Stan bazowy osi przywrócony lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _refresh_metrics(self) -> None:
        cache_key = (
            self.master_window.global_take_duration_ms,
            self.model.release_time_ms,
            tuple((n.time_ms, round(n.y, 4)) for n in self.model.nodes),
            self.model.step_tuning.dead_zone_y,
            self.model.step_tuning.input_max_y,
            self.model.step_tuning.input_gamma,
            self.model.step_tuning.step_rate_gain,
            self.model.step_tuning.step_rate_max_percent,
            self.model.step_tuning.preview_rate_smoothing,
        )
        if cache_key != self._metrics_cache_key:
            self._metrics_cache_text = self.model.metrics_summary(duration_ms=self.master_window.global_take_duration_ms)
            self._metrics_cache_key = cache_key
        self.metrics_var.set(self._metrics_cache_text)

    def _draw_curve(self) -> None:
        c = self.curve_canvas
        c.delete("all")
        left, top, right, bottom = self._curve_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="")

        settle = self.model.mechanics.start_settle_ms
        ramp = self.model.mechanics.start_ramp_ms
        start_total = settle + ramp
        stop_from = self.master_window.global_take_duration_ms - start_total
        sx = self._time_to_x(start_total, left, right)
        ex = self._time_to_x(stop_from, left, right)
        c.create_rectangle(left, top, sx, bottom, fill=self.master_window.WARN, outline="")
        c.create_rectangle(ex, top, right, bottom, fill=self.master_window.WARN, outline="")
        c.create_rectangle(sx, top, ex, bottom, fill=self.master_window.SAFE, outline="")

        for yv in [100, 50, 0, -50, -100]:
            py = self._logical_y_to_canvas(yv, top, bottom)
            width = self.master_window.main_take_settings.zero_line_width if yv == 0 else 1
            dash = None if yv == 0 else (5, 4)
            color = self.master_window.main_take_settings.zero_line_color if yv == 0 else self.master_window.WARN
            c.create_line(left, py, right, py, fill=color, width=width, dash=dash)
            c.create_text(left - 8, py, text=str(yv), fill=self.master_window.MUTED, anchor="e", font=("Consolas", 8))

        total_minutes = max(1, int(self.master_window.global_take_duration_ms // 60000))
        for minute in range(0, total_minutes + 1):
            t_ms = minute * 60000
            if t_ms > self.master_window.global_take_duration_ms:
                continue
            px = self._time_to_x(t_ms, left, right)
            c.create_line(px, top, px, bottom, fill="#43505C", dash=(2, 6))
            c.create_text(px, bottom + 10, text=f"{minute}m", fill=self.master_window.MUTED, anchor="n", font=("Consolas", 8))

        samples = self.model.sample_curve(1000, duration_ms=self.master_window.global_take_duration_ms)
        pts = []
        for t, y in samples:
            pts.extend([self._time_to_x(t, left, right), self._logical_y_to_canvas(y, top, bottom)])
        if len(pts) >= 4:
            c.create_line(*pts, fill=self.master_window.CURVE, width=self.master_window.main_take_settings.curve_line_width, smooth=True)

        hit_radius = self.model.step_tuning.node_hit_radius_px
        r = max(4, min(10, hit_radius // 2))
        for i, n in enumerate(self.model.nodes):
            px = self._time_to_x(n.time_ms, left, right)
            py = self._logical_y_to_canvas(n.y, top, bottom)
            fill = self.master_window.NODE_SEL if i == self.selected_index else self.master_window.NODE
            if i == 0 or i == len(self.model.nodes) - 1:
                fill = "#D6EAF8"
            c.create_oval(px - r, py - r, px + r, py + r, fill=fill, outline="black")

        x0 = self._time_to_x(0, left, right)
        x1 = self._time_to_x(self.master_window.global_take_duration_ms, left, right)
        c.create_line(x0, top, x0, bottom, fill="#45C46B", width=3)
        c.create_line(x1, top, x1, bottom, fill="#E65D5D", width=3)
        c.create_text(x0 + 4, top + 8, text="START", fill="#45C46B", anchor="w", font=("Segoe UI", 8, "bold"))
        c.create_text(x1 - 4, top + 8, text="STOP", fill="#E65D5D", anchor="e", font=("Segoe UI", 8, "bold"))

    def _draw_step(self) -> None:
        c = self.step_canvas
        c.delete("all")
        left, top, right, bottom = self._step_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1A1E24", outline="#303A45")
        rows = self.model.build_step_rows(duration_ms=self.master_window.global_take_duration_ms)
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
        c.create_text(left, top - 2, text="STEP 0/1 preview", fill=self.master_window.FG, anchor="sw", font=("Segoe UI Semibold", 9))
        c.create_text(right, top - 2, text=f"rows={len(rows)}  pulses={rows[-1]['count']}", fill=self.master_window.MUTED, anchor="se", font=("Consolas", 8))

    def _set_status(self, status: str | None = None) -> None:
        self.status_var.set(status if status is not None else "Sandbox osi gotowy do strojenia.")

    def _request_curve_redraw(self) -> None:
        self._curve_needs_redraw = True
        if self._curve_redraw_after_id is not None:
            return
        self._curve_redraw_after_id = self.after(16, self._flush_curve_redraw)

    def _flush_curve_redraw(self) -> None:
        self._curve_redraw_after_id = None
        if self._curve_needs_redraw:
            self._draw_curve()
            self._curve_needs_redraw = False

    def _apply_drag_zero_snap(self, value: float) -> float:
        value = self.model.clamp_y(value)
        if not getattr(self.master_window.main_take_settings, "snap_to_zero_enabled", False):
            self._drag_zero_snap_locked = False
            return value
        threshold = max(0.0, float(getattr(self.master_window.main_take_settings, "snap_to_zero_threshold", 0.0)))
        enter_threshold = threshold * 0.35
        release_threshold = max(enter_threshold, threshold)
        if self._drag_zero_snap_locked:
            if abs(value) <= release_threshold:
                return 0.0
            self._drag_zero_snap_locked = False
            return value
        if abs(value) <= enter_threshold:
            self._drag_zero_snap_locked = True
            return 0.0
        return value

    @profile_method('EHR._refresh_all')
    def _refresh_all(self, status: str | None = None) -> None:
        self.model.sort_and_fix_nodes()
        self._refresh_metrics()
        if self._curve_needs_redraw:
            self._draw_curve()
            self._curve_needs_redraw = False
        if self._step_needs_redraw:
            self._draw_step()
            self._step_needs_redraw = False
        self._set_status(status)

    def _hit_node(self, x: float, y: float) -> int | None:
        left, top, right, bottom = self._curve_rect()
        radius = self.model.step_tuning.node_hit_radius_px
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
            self._drag_zero_snap_locked = abs(self.drag_anchor_node_y) <= 1e-9
            self._request_curve_redraw()
            self._set_status(f"Wybrano punkt {idx}.")
            return
        self.selected_index = None
        self.drag_mode = "pan"
        self.drag_anchor_x = event.x
        self._request_curve_redraw()
        self._set_status("PAN linii.")

    def _on_curve_drag(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        tuning = self.model.step_tuning
        if self.drag_mode == "node" and self.selected_index is not None:
            delta_y = self.drag_anchor_y - event.y
            new_y = self.drag_anchor_node_y + self._drag_delta_to_logical_y(delta_y, top, bottom)
            new_y = self._apply_drag_zero_snap(new_y)
            delta_t = self._x_to_time(event.x, left, right) - self._x_to_time(self.drag_anchor_x, left, right)
            threshold_ms = self.model.sample_ms * tuning.time_drag_threshold_samples
            new_t = self.drag_anchor_node_time if abs(delta_t) < threshold_ms else self.drag_anchor_node_time + delta_t
            if self.model.move_node(self.selected_index, new_t, new_y):
                self._curve_needs_redraw = True
                self._step_needs_redraw = True
                self._request_curve_redraw()
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(event.x, left, right)
            old_time = self._x_to_time(self.drag_anchor_x, left, right)
            delta = new_time - old_time
            self.drag_anchor_x = event.x
            if self.model.shift_all(delta):
                self._curve_needs_redraw = True
                self._step_needs_redraw = True
                self._request_curve_redraw()

    def _on_curve_release(self, _event) -> None:
        self.drag_mode = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._drag_zero_snap_locked = False
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Gotowy.")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _on_curve_double_click(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        t = self._x_to_time(event.x, left, right)
        y = self._canvas_to_logical_y(event.y, top, bottom)
        self.model.add_node(t, y)
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Dodano punkt.")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _on_curve_right_click(self, event) -> None:
        idx = self._hit_node(event.x, event.y)
        if idx is None:
            return
        self.model.remove_node(idx)
        self.selected_index = None
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._refresh_all("Usunięto punkt.")
        self._mark_main_take_dirty("Oś zmieniona lokalnie. Użyj SET UP lub zamknij okno, aby zsynchronizować MAIN TAKE.")

    def _on_close(self) -> None:
        self.master_window.sync_axis_from_dialog(self.axis_index, status=f"Zamknięto edytor osi i zsynchronizowano MAIN TAKE: {self.model.axis_def.axis_name}.")
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
        self.settings_path = self._settings_path()
        self.main_take_settings = MainTakeSettings.load_or_default(self.settings_path)
        self.global_take_duration_ms = self.main_take_settings.take_duration_ms()
        self.axis_models = [AxisCurveModel(axis_def, self.config_model) for axis_def in DEFAULT_AXIS_DEFINITIONS]
        for axis in self.axis_models:
            axis.set_axis_take_duration_ms(self.global_take_duration_ms)
        self.take_model = EhrTakeModel.from_runtime(self.global_take_duration_ms, self.main_take_settings, self.axis_models)
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
        self.wave_rects: dict[int, WaveRect] = {}
        self.settings_dialogs: dict[int, AxisSettingsDialog] = {}
        self.drag_release_anchor_time = 0
        self._drag_zero_snap_locked = False
        self.dirty_axis_indices: set[int] = set()
        self._axis_data_versions = [0 for _ in self.axis_models]
        self._axis_selection_version = 0
        self._take_model_version = 0

        self.axis_info_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Gotowy.")
        self.protocol_cache_key = None
        self.protocol_cache_text = ""
        self.axis_info_cache_key = None
        self.axis_info_cache_text = ""
        self._main_canvas_needs_redraw = True
        self._take_model_dirty = False
        self._axis_info_dirty = True
        self._protocol_dirty = True
        self._configure_after_id = None
        self._main_canvas_redraw_after_id = None

        self._build_ui()
        self.update_idletasks()
        self.after_idle(self._refresh_all)

    def _settings_path(self) -> Path:
        editor_dir = Path(__file__).resolve().parent.parent
        project_dir = editor_dir.parent
        return project_dir / "data" / "ehr" / "main_take_settings.json"

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="TARZAN — EHR", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 16)).pack(side="left")
        tk.Button(top, text="⚙", command=self._open_take_settings, bg="#39424E", fg=self.FG,
                  activebackground="#39424E", activeforeground=self.FG, relief="flat", bd=0, padx=10, pady=4,
                  font=("Segoe UI Symbol", 12), cursor="hand2").pack(side="left", padx=(8, 0))

        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True)

        self.left = tk.Frame(body, bg=self.BG, width=300)
        self.left.pack(side="left", fill="y", padx=(0, 8))
        self.left.pack_propagate(False)
        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(self.left)

        self.timeline_canvas = tk.Canvas(right, bg="#1B2028", highlightthickness=0)
        self.timeline_canvas.pack(fill="both", expand=True)
        self.timeline_canvas.bind("<Configure>", self._on_canvas_configure)
        self.timeline_canvas.bind("<Button-1>", self._on_canvas_press)
        self.timeline_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.timeline_canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        self.timeline_canvas.bind("<Button-3>", self._on_canvas_right_click)

        self.status = tk.Label(outer, textvariable=self.status_var, bg=self.PANEL2, fg=self.FG, anchor="w",
                               padx=10, pady=8, font=("Segoe UI", 9))
        self.status.pack(fill="x", pady=(8, 0))
        self._apply_visibility_settings()

    def _build_left_panel(self, parent: tk.Misc) -> None:
        self.active_axis_name_var = tk.StringVar(value=self._active_model().axis_def.axis_name)
        self.axis_info_label = tk.Label(parent, textvariable=self.axis_info_var, bg=self.BG, fg=self.MUTED,
                                        justify="left", anchor="w", font=("Consolas", 9))
        self.axis_info_label.pack(fill="x", pady=(0, 12))

        self.protocol_label_var = tk.StringVar(value=f"PODGLĄD PROTOKOŁU — {self._active_model().axis_def.axis_name}")
        self.protocol_label = tk.Label(parent, textvariable=self.protocol_label_var, bg=self.BG, fg=self.FG,
                                       anchor="w", font=("Segoe UI Semibold", 11))
        self.protocol_label.pack(fill="x", pady=(0, 6))

        self.protocol_box = tk.Frame(parent, bg=self.PANEL)
        self.protocol_box.pack(fill="both", expand=True, pady=(0, 10))
        self.protocol_text = tk.Text(self.protocol_box, height=24, bg=self.PANEL, fg=self.FG, relief="flat",
                                     wrap="none", font=("Consolas", 8))
        self.protocol_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        protocol_scroll = tk.Scrollbar(self.protocol_box, orient="vertical", command=self.protocol_text.yview)
        protocol_scroll.pack(side="right", fill="y", padx=(0, 8), pady=8)
        self.protocol_text.configure(yscrollcommand=protocol_scroll.set, state="disabled")

    def _apply_visibility_settings(self) -> None:
        self.axis_info_label.pack_forget()
        self.protocol_label.pack_forget()
        self.protocol_box.pack_forget()
        if self.main_take_settings.show_axis_metrics:
            self.axis_info_label.pack(fill="x", pady=(0, 12))
        if self.main_take_settings.show_protocol_preview:
            self.protocol_label.pack(fill="x", pady=(0, 6))
            self.protocol_box.pack(fill="both", expand=True, pady=(0, 10))
        if self.main_take_settings.show_status_bar:
            self.status.pack(fill="x", pady=(8, 0))
        else:
            self.status.pack_forget()

    def _bump_axis_data_version(self, axis_index: int) -> None:
        self._axis_data_versions[axis_index] += 1

    def _mark_take_model_dirty(self) -> None:
        self._take_model_dirty = True
        self._take_model_version += 1

    def _mark_axis_metrics_dirty(self) -> None:
        self._axis_info_dirty = True

    def _mark_protocol_dirty(self) -> None:
        self._protocol_dirty = True

    def _set_active_axis(self, axis_index: int) -> bool:
        if axis_index == self.active_axis_index:
            return False
        self.active_axis_index = axis_index
        self._axis_selection_version += 1
        self._mark_axis_metrics_dirty()
        self._mark_protocol_dirty()
        self._main_canvas_needs_redraw = True
        return True

    def _mark_axis_data_changed(self, axis_index: int, *, mark_take_model: bool = True, mark_protocol: bool = True, mark_axis_info: bool = True) -> None:
        self._bump_axis_data_version(axis_index)
        if mark_take_model:
            self._mark_take_model_dirty()
        if axis_index == self.active_axis_index:
            if mark_protocol:
                self._mark_protocol_dirty()
            if mark_axis_info:
                self._mark_axis_metrics_dirty()

    def mark_axis_dirty(self, axis_index: int, status: str | None = None) -> None:
        self.dirty_axis_indices.add(axis_index)
        self._mark_axis_data_changed(axis_index)
        self._configure_after_id = None
        self._set_status(status or f"Oś zmieniona lokalnie: {self.axis_models[axis_index].axis_def.axis_name}.")

    def _rebuild_take_model(self) -> None:
        self.take_model = EhrTakeModel.from_runtime(self.global_take_duration_ms, self.main_take_settings, self.axis_models)

    def sync_axis_from_dialog(self, axis_index: int, status: str | None = None) -> None:
        self.dirty_axis_indices.discard(axis_index)
        self.protocol_cache_key = None
        self._main_canvas_needs_redraw = True
        self._mark_axis_data_changed(axis_index)
        self._configure_after_id = None
        self._refresh_all(light=False, status=status)

    def _open_take_settings(self) -> None:
        dlg = MainTakeSettingsDialog(
            self,
            copy.deepcopy(self.main_take_settings),
            save_callback=self._save_take_settings,
            apply_callback=self._apply_take_settings,
        )
        dlg.focus_force()

    def _apply_take_settings(self, settings: MainTakeSettings) -> None:
        self.main_take_settings = settings
        new_take_ms = settings.take_duration_ms()
        self.global_take_duration_ms = new_take_ms
        for axis in self.axis_models:
            axis.set_axis_take_duration_ms(new_take_ms)
        self._apply_visibility_settings()
        self.protocol_cache_key = None
        self.axis_info_cache_key = None
        self._main_canvas_needs_redraw = True
        self._mark_take_model_dirty()
        self._mark_protocol_dirty()
        self._mark_axis_metrics_dirty()
        self._configure_after_id = None
        for dlg in list(self.settings_dialogs.values()):
            if dlg.winfo_exists():
                dlg._curve_needs_redraw = True
                dlg._step_needs_redraw = True
                dlg._refresh_all()
        self._refresh_all(light=False, status="Zastosowano ustawienia MAIN TAKE.")

    def _save_take_settings(self, settings: MainTakeSettings) -> None:
        self._apply_take_settings(settings)
        settings.save(self.settings_path)
        self.status_var.set(f"Zapisano ustawienia MAIN TAKE: {self.settings_path}")

    def _scale_row(self, parent, label, var, from_, to, resolution):
        wrap = tk.Frame(parent, bg=self.PANEL)
        wrap.pack(fill="x", padx=10, pady=6)
        tk.Label(wrap, text=label, bg=self.PANEL, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                         command=lambda _v: self._refresh_all(light=True), bg=self.PANEL, fg=self.FG,
                         troughcolor="#39424E", highlightthickness=0, bd=0, length=280)
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=10, pady=6,
                         font=("Segoe UI Semibold", 9), cursor="hand2")

    def _small_btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=8, pady=4,
                         font=("Segoe UI Semibold", 8), cursor="hand2")

    def _active_model(self) -> AxisCurveModel:
        return self.axis_models[self.active_axis_index]

    def _curve_area_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.timeline_canvas.winfo_width() or 1200))
        h = max(300, int(self.timeline_canvas.winfo_height() or 820))
        return 190, 24, w - 28, h - 38

    def _time_to_x(self, t_ms: int, left: int, right: int) -> float:
        span = max(1, self.global_take_duration_ms)
        return left + (t_ms / span) * (right - left)

    def _x_to_time(self, x: float, left: int, right: int) -> int:
        rel = (x - left) / max(1.0, (right - left))
        rel = max(0.0, min(1.0, rel))
        step = self._active_model().sample_ms
        return int(round((rel * self.global_take_duration_ms) / step) * step)

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
        logical_y = max(-logical_limit, min(logical_limit, logical_y))
        return model.apply_zero_snap(self.main_take_settings, logical_y)

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

    def _wave_axis_from_point(self, x: float, y: float) -> int | None:
        for axis_index, rect in self.wave_rects.items():
            if rect.contains(x, y):
                return axis_index
        return None

    def _smooth_axis_idx(self, axis_index: int) -> None:
        model = self.axis_models[axis_index]
        strength = float(getattr(self.main_take_settings, "smooth_strength_default", 0.35))
        passes = int(getattr(self.main_take_settings, "smooth_passes_default", 2))
        model.smooth_all(strength=strength, passes=passes)
        self._set_active_axis(axis_index)
        self._main_canvas_needs_redraw = True
        self._mark_axis_data_changed(axis_index)
        self._refresh_all(light=False, status=f"Wygładzono przebieg osi: {model.axis_def.axis_name}. siła={strength:.2f} przejścia={passes}.")

    def _schedule_configure_refresh(self) -> None:
        if self._configure_after_id is not None:
            try:
                self.after_cancel(self._configure_after_id)
            except Exception:
                pass
        self._configure_after_id = self.after(40, self._flush_configure_refresh)

    def _flush_configure_refresh(self) -> None:
        self._configure_after_id = None
        self._main_canvas_needs_redraw = True
        self._refresh_all(light=True)

    def _hit_node(self, axis_index: int, x: float, y: float) -> int | None:
        if axis_index not in self.axis_rects:
            return None
        rect = self.axis_rects[axis_index]
        model = self.axis_models[axis_index]
        if model.is_release_axis:
            return None
        radius = model.step_tuning.node_hit_radius_px
        for i, n in enumerate(model.nodes):
            px = self._time_to_x(n.time_ms, rect.left, rect.right)
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
        px = self._time_to_x(model.release_time_ms, rect.left, rect.right)
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

    def _hex_to_rgb(self, color: str) -> tuple[int, int, int]:
        color = (color or "#000000").strip()
        if color.startswith("#") and len(color) == 7:
            try:
                return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            except ValueError:
                return 0, 0, 0
        return 0, 0, 0

    def _blend_hex(self, base: str, overlay: str, strength_percent: int) -> str:
        strength = max(0.0, min(1.0, float(strength_percent) / 100.0))
        br, bg, bb = self._hex_to_rgb(base)
        or_, og, ob = self._hex_to_rgb(overlay)
        rr = int(round(br * (1.0 - strength) + or_ * strength))
        rg = int(round(bg * (1.0 - strength) + og * strength))
        rb = int(round(bb * (1.0 - strength) + ob * strength))
        return f"#{rr:02X}{rg:02X}{rb:02X}"

    def _axis_curve_color(self, model: AxisCurveModel) -> str:
        return self.main_take_settings.axis_color(model.axis_def.axis_id, model.axis_def.color)

    def _axis_panel_fill(self, axis_color: str, is_active: bool) -> str:
        base = "#232A33" if is_active else "#1C2128"
        if not self.main_take_settings.show_axis_background_tint:
            return base
        strength = self.main_take_settings.axis_background_strength_percent
        if is_active:
            strength = min(40, strength + int(getattr(self.main_take_settings, "active_axis_emphasis_percent", 10)))
        return self._blend_hex(base, axis_color, strength)

    @profile_method('EHR._draw_main_canvas')
    def _draw_main_canvas(self) -> None:
        c = self.timeline_canvas
        c.delete("all")
        self.axis_rects.clear()
        self.gear_rects.clear()
        self.wave_rects.clear()
        left, top, right, bottom = self._curve_area_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="#303A45")

        total_minutes = max(1, int(self.global_take_duration_ms // 60000))
        if self.main_take_settings.show_minute_grid:
            for minute in range(0, total_minutes + 1):
                t_ms = minute * 60000
                if t_ms > self.global_take_duration_ms:
                    continue
                px = self._time_to_x(t_ms, left, right)
                c.create_line(px, top, px, bottom, fill="#36414C", dash=(2, 6))

        for axis_index, rect in self._axis_layout():
            self.axis_rects[axis_index] = rect
            model = self.axis_models[axis_index]
            is_active = axis_index == self.active_axis_index
            axis_color = self._axis_curve_color(model)
            panel_fill = self._axis_panel_fill(axis_color, is_active)
            c.create_rectangle(rect.left, rect.top, rect.right, rect.bottom, fill=panel_fill, outline="")
            if is_active:
                c.create_line(rect.left, rect.top + 2, rect.left, rect.bottom - 2, fill=axis_color, width=max(1, int(getattr(self.main_take_settings, "active_axis_border_width", 3))))

            mid = (rect.top + rect.bottom) / 2.0
            c.create_line(rect.left, mid, rect.right, mid,
                          fill=self.main_take_settings.zero_line_color,
                          width=self.main_take_settings.zero_line_width)
            if self.main_take_settings.show_axis_labels:
                c.create_text(rect.left - 12, mid, text=model.axis_def.axis_name, fill=self.FG, anchor="e",
                              font=("Segoe UI", 9, "bold"))

            if not model.is_release_axis:
                if self.main_take_settings.show_axis_gears:
                    gear = GearRect(rect.left - 44, rect.top + 8, rect.left - 16, rect.top + 36)
                    self.gear_rects[axis_index] = gear
                    c.create_rectangle(gear.left, gear.top, gear.right, gear.bottom, fill="#39424E", outline="#55606D")
                    c.create_text((gear.left + gear.right) / 2.0, (gear.top + gear.bottom) / 2.0, text="⚙", fill=self.FG,
                                  font=("Segoe UI Symbol", 12))
                wave = WaveRect(rect.left - 76, rect.top + 8, rect.left - 48, rect.top + 36)
                self.wave_rects[axis_index] = wave
                c.create_rectangle(wave.left, wave.top, wave.right, wave.bottom, fill="#39424E", outline="#55606D")
                c.create_text((wave.left + wave.right) / 2.0, (wave.top + wave.bottom) / 2.0, text="≈", fill=self.FG,
                              font=("Segoe UI Semibold", 12))

            if self.main_take_settings.show_minute_grid:
                for minute in range(0, total_minutes + 1):
                    t_ms = minute * 60000
                    if t_ms > self.global_take_duration_ms:
                        continue
                    px = self._time_to_x(t_ms, rect.left, rect.right)
                    c.create_line(px, rect.top, px, rect.bottom, fill="#303842", dash=(2, 6))

            if not model.is_release_axis:
                if self.main_take_settings.show_axis_activity_markers and len(model.nodes) >= 4:
                    first_edit = model.nodes[1]
                    last_edit = model.nodes[-2]
                    for node in (first_edit, last_edit):
                        mx = self._time_to_x(node.time_ms, rect.left, rect.right)
                        c.create_line(mx, rect.top + 4, mx, rect.bottom - 4, fill=axis_color, width=1, dash=(3, 5))

                samples = model.sample_curve(900, duration_ms=self.global_take_duration_ms)
                pts = []
                for t_ms, y in samples:
                    pts.extend([self._time_to_x(t_ms, rect.left, rect.right),
                                self._logical_y_to_canvas(model, y, rect.top, rect.bottom)])
                if len(pts) >= 4:
                    c.create_line(*pts, fill=axis_color,
                                  width=self.main_take_settings.active_curve_line_width if is_active else self.main_take_settings.curve_line_width,
                                  smooth=True)

                node_r = max(4, min(9, model.step_tuning.node_hit_radius_px // 2))
                square_half = max(5, node_r)
                for i, n in enumerate(model.nodes):
                    px = self._time_to_x(n.time_ms, rect.left, rect.right)
                    py = self._logical_y_to_canvas(model, n.y, rect.top, rect.bottom)
                    fill = self.NODE_SEL if (axis_index == self.drag_axis_index and i == self.selected_index) else self.NODE
                    if i == 0 or i == len(model.nodes) - 1:
                        if self.main_take_settings.show_start_stop_squares:
                            c.create_rectangle(px - square_half, py - square_half, px + square_half, py + square_half, fill=self.main_take_settings.zero_line_color, outline="black")
                        else:
                            c.create_oval(px - node_r, py - node_r, px + node_r, py + node_r, fill="#D6EAF8", outline="black")
                    else:
                        c.create_oval(px - node_r, py - node_r, px + node_r, py + node_r, fill=fill, outline="black")

            if model.is_release_axis and model.release_time_ms is not None:
                inner_top = rect.top + max(12, (rect.bottom - rect.top) // 3)
                inner_bottom = rect.bottom - max(12, (rect.bottom - rect.top) // 3)
                inner_mid = (inner_top + inner_bottom) / 2.0
                c.create_rectangle(rect.left, inner_top, rect.right, inner_bottom, fill=panel_fill, outline="")
                c.create_line(rect.left, inner_mid, rect.right, inner_mid,
                              fill=self.main_take_settings.zero_line_color,
                              width=self.main_take_settings.zero_line_width)
                rx = self._time_to_x(model.release_time_ms, rect.left, rect.right)
                ry = inner_mid
                r = 7
                fill = "#F59E0B" if self.drag_mode == 'release' and axis_index == self.drag_axis_index else axis_color
                c.create_polygon(rx, ry - r, rx + r, ry, rx, ry + r, rx - r, ry, fill=fill, outline='black')
                c.create_text(rx + 14, ry - 10, text='RELEASE', fill=axis_color, anchor='w', font=('Segoe UI', 8, 'bold'))

        for minute in range(0, total_minutes + 1):
            t_ms = minute * 60000
            if t_ms > self.global_take_duration_ms:
                continue
            px = self._time_to_x(t_ms, left, right)
            c.create_text(px, bottom + 8, text=f"{minute}m", fill=self.MUTED, anchor="n", font=("Consolas", 8))

    def _on_canvas_configure(self, _event=None) -> None:
        self._schedule_configure_refresh()

    @profile_method('EHR._refresh_axis_info')
    def _refresh_axis_info(self, force: bool = False) -> None:
        model = self._active_model()
        self.active_axis_name_var.set(model.axis_def.axis_name)
        if not self.main_take_settings.show_axis_metrics:
            self.axis_info_var.set("")
            self._axis_info_dirty = False
            return
        cache_key = (
            self.active_axis_index,
            self._axis_selection_version,
            self._axis_data_versions[self.active_axis_index],
            self.global_take_duration_ms,
            model.step_tuning.dead_zone_y,
            model.step_tuning.input_max_y,
            model.step_tuning.input_gamma,
            model.step_tuning.step_rate_gain,
            model.step_tuning.step_rate_max_percent,
            model.step_tuning.preview_rate_smoothing,
        )
        if force or self._axis_info_dirty or cache_key != self.axis_info_cache_key:
            self.axis_info_cache_text = model.metrics_summary(duration_ms=self.global_take_duration_ms)
            self.axis_info_cache_key = cache_key
            self._axis_info_dirty = False
        self.axis_info_var.set(self.axis_info_cache_text)

    @profile_method('EHR._refresh_protocol_preview')
    def _refresh_protocol_preview(self, force: bool = False) -> None:
        if not self.main_take_settings.show_protocol_preview:
            return
        model = self._active_model()
        cache_key = (
            self.active_axis_index,
            self._axis_selection_version,
            self._axis_data_versions[self.active_axis_index],
            self.global_take_duration_ms,
        )
        self.protocol_label_var.set(f"PODGLĄD PROTOKOŁU — {model.axis_def.axis_name}")
        if (not force) and cache_key == self.protocol_cache_key:
            return

        rows = model.protocol_rows(duration_ms=self.global_take_duration_ms)
        if not rows:
            text = f"OŚ: {model.axis_def.axis_name}\n\nBrak danych protokołu.\n"
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
            text = ''.join(lines)

        self.protocol_cache_key = cache_key
        self.protocol_cache_text = text
        self.protocol_text.configure(state='normal')
        self.protocol_text.delete('1.0', 'end')
        self.protocol_text.insert('1.0', text)
        self.protocol_text.configure(state='disabled')

    def _set_status(self, status: str | None = None) -> None:
        self.status_var.set(status if status is not None else "EHR gotowy.")

    def _request_main_canvas_redraw(self) -> None:
        self._main_canvas_needs_redraw = True
        if self._main_canvas_redraw_after_id is not None:
            return
        self._main_canvas_redraw_after_id = self.after(16, self._flush_main_canvas_redraw)

    def _flush_main_canvas_redraw(self) -> None:
        self._main_canvas_redraw_after_id = None
        if self._main_canvas_needs_redraw:
            self._draw_main_canvas()
            self._main_canvas_needs_redraw = False

    def _apply_drag_zero_snap(self, model: AxisCurveModel, value: float) -> float:
        value = model.clamp_y(value)
        if not getattr(self.main_take_settings, "snap_to_zero_enabled", False):
            self._drag_zero_snap_locked = False
            return value
        threshold = max(0.0, float(getattr(self.main_take_settings, "snap_to_zero_threshold", 0.0)))
        enter_threshold = threshold * 0.35
        release_threshold = max(enter_threshold, threshold)
        if self._drag_zero_snap_locked:
            if abs(value) <= release_threshold:
                return 0.0
            self._drag_zero_snap_locked = False
            return value
        if abs(value) <= enter_threshold:
            self._drag_zero_snap_locked = True
            return 0.0
        return value

    def _refresh_light_ui(self, status: str | None = None, refresh_axis_info: bool = False) -> None:
        if refresh_axis_info or self._axis_info_dirty:
            self._refresh_axis_info(force=False)
        self._request_main_canvas_redraw()
        self._set_status(status)

    @profile_method('EHR._refresh_all')
    def _refresh_all(self, light: bool = False, status: str | None = None) -> None:
        if self._main_canvas_needs_redraw:
            self._draw_main_canvas()
            self._main_canvas_needs_redraw = False
        if light:
            if self._axis_info_dirty:
                self._refresh_axis_info(force=False)
            self._set_status(status)
            return
        if self._take_model_dirty:
            self._rebuild_take_model()
            self._take_model_dirty = False
        if self._axis_info_dirty:
            self._refresh_axis_info(force=False)
        if self._protocol_dirty or self.protocol_cache_key is None:
            self._refresh_protocol_preview(force=False)
            self._protocol_dirty = False
        self._set_status(status)

    def _open_settings(self, axis_index: int) -> None:
        self._set_active_axis(axis_index)
        if self.axis_models[axis_index].is_release_axis:
            self._refresh_light_ui(status=f"Oś {self.axis_models[axis_index].axis_def.axis_name} nie ma okna ustawień.", refresh_axis_info=True)
            return
        dlg = self.settings_dialogs.get(axis_index)
        if dlg is not None and dlg.winfo_exists():
            dlg.lift()
            dlg.focus_force()
            self._refresh_light_ui(status=f"Wybrano oś: {self._active_model().axis_def.axis_name}.", refresh_axis_info=True)
            return
        self.settings_dialogs[axis_index] = AxisSettingsDialog(self, axis_index)
        self._refresh_light_ui(status=f"Otwarto ustawienia osi: {self._active_model().axis_def.axis_name}.", refresh_axis_info=True)

    def _on_canvas_press(self, event) -> None:
        gear_axis = self._gear_axis_from_point(event.x, event.y)
        if gear_axis is not None:
            self._open_settings(gear_axis)
            return
        wave_axis = self._wave_axis_from_point(event.x, event.y)
        if wave_axis is not None:
            self._smooth_axis_idx(wave_axis)
            return

        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        axis_changed = self._set_active_axis(axis_index)
        self._configure_after_id = None
        if axis_changed:
            self._refresh_axis_info(force=False)
        model = self.axis_models[axis_index]
        if self._hit_release(axis_index, event.x, event.y):
            self.drag_axis_index = axis_index
            self.selected_index = None
            self.drag_mode = "release"
            self.drag_anchor_x = event.x
            self.drag_release_anchor_time = int(model.release_time_ms or 0)
            self._drag_zero_snap_locked = False
            self._request_main_canvas_redraw()
            self._set_status(f"Wybrano RELEASE osi: {model.axis_def.axis_name}.")
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
            self._drag_zero_snap_locked = abs(self.drag_anchor_node_y) <= 1e-9
            self._request_main_canvas_redraw()
            self._set_status(f"Wybrano punkt osi: {model.axis_def.axis_name}.")
            return
        self.drag_axis_index = axis_index
        self.selected_index = None
        self.drag_mode = "pan"
        self.drag_anchor_x = event.x
        self._drag_zero_snap_locked = False
        self._request_main_canvas_redraw()
        self._set_status(f"PAN osi: {model.axis_def.axis_name}.")

    def _on_canvas_drag(self, event) -> None:
        axis_index = self.drag_axis_index
        if axis_index is None or axis_index not in self.axis_rects:
            return
        model = self.axis_models[axis_index]
        rect = self.axis_rects[axis_index]
        if self.drag_mode == "node" and self.selected_index is not None:
            delta_y = self.drag_anchor_y - event.y
            new_y = self.drag_anchor_node_y + self._drag_delta_to_logical_y(model, delta_y, rect.top, rect.bottom)
            new_y = self._apply_drag_zero_snap(model, new_y)
            delta_t = self._x_to_time(event.x, rect.left, rect.right) - self._x_to_time(self.drag_anchor_x, rect.left, rect.right)
            threshold_ms = model.sample_ms * model.step_tuning.time_drag_threshold_samples
            new_t = self.drag_anchor_node_time if abs(delta_t) < threshold_ms else self.drag_anchor_node_time + delta_t
            if model.move_node(self.selected_index, new_t, new_y):
                self._request_main_canvas_redraw()
        elif self.drag_mode == "release":
            new_time = self._x_to_time(event.x, rect.left, rect.right)
            if model.set_release_time(new_time):
                self._request_main_canvas_redraw()
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(event.x, rect.left, rect.right)
            old_time = self._x_to_time(self.drag_anchor_x, rect.left, rect.right)
            delta = new_time - old_time
            self.drag_anchor_x = event.x
            if model.shift_all(delta):
                self._request_main_canvas_redraw()

    def _on_canvas_release(self, _event) -> None:
        changed_axis_index = self.drag_axis_index
        had_drag_mode = self.drag_mode is not None
        self.drag_axis_index = None
        self.selected_index = None
        self.drag_mode = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._main_canvas_needs_redraw = True
        if had_drag_mode and changed_axis_index is not None:
            self._mark_axis_data_changed(changed_axis_index)
        self._configure_after_id = None
        self._refresh_all(light=False, status="Gotowy.")

    def _on_canvas_double_click(self, event) -> None:
        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        if self._gear_axis_from_point(event.x, event.y) is not None or self._wave_axis_from_point(event.x, event.y) is not None:
            return
        model = self.axis_models[axis_index]
        rect = self.axis_rects[axis_index]
        self._set_active_axis(axis_index)
        t_ms = self._x_to_time(event.x, rect.left, rect.right)
        if model.is_release_axis and abs(event.y - ((rect.top + rect.bottom) / 2.0)) <= 20:
            if model.set_release_time(t_ms):
                self._main_canvas_needs_redraw = True
                self._mark_axis_data_changed(axis_index)
            self._refresh_all(light=False, status=f"Ustawiono RELEASE na osi: {model.axis_def.axis_name}.")
            return
        y = self._canvas_to_logical_y(model, event.y, rect.top, rect.bottom)
        model.add_node(t_ms, y)
        self._main_canvas_needs_redraw = True
        self._mark_axis_data_changed(self.active_axis_index)
        self._configure_after_id = None
        self._refresh_all(light=False, status=f"Dodano punkt na osi: {model.axis_def.axis_name}.")

    def _on_canvas_right_click(self, event) -> None:
        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        if self._gear_axis_from_point(event.x, event.y) is not None or self._wave_axis_from_point(event.x, event.y) is not None:
            return
        node_index = self._hit_node(axis_index, event.x, event.y)
        if node_index is None:
            return
        model = self.axis_models[axis_index]
        model.remove_node(node_index)
        self._main_canvas_needs_redraw = True
        self._mark_axis_data_changed(axis_index)
        self._configure_after_id = None
        self._refresh_all(light=False, status=f"Usunięto punkt z osi: {model.axis_def.axis_name}.")

    def _smooth_active(self) -> None:
        model = self._active_model()
        strength = max(0.0, min(1.0, float(getattr(self.main_take_settings, "smooth_strength_default", 0.35))))
        passes = max(1, min(8, int(getattr(self.main_take_settings, "smooth_passes_default", 2))))
        model.smooth_all(strength=strength, passes=passes)
        self._main_canvas_needs_redraw = True
        self._mark_axis_data_changed(self.active_axis_index)
        self._configure_after_id = None
        self._refresh_all(light=False, status=f"Wygładzono przebieg osi: {model.axis_def.axis_name}. siła={strength:.2f} przejścia={passes}.")


def main() -> None:
    app = TarzanEhrMultiAxisWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
