# -*- coding: utf-8 -*-
"""
TARZAN - KHR UI

Okno testowe KHR:
LEWO   - wejście / śledzony obiekt
ŚRODEK - korekta KHR
PRAWO  - wynik / oś pozioma kamery z czerwoną flagą

Ten plik jest UI/test.
Logika KHR jest w motion/.
"""

from __future__ import annotations

import math
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from motion.tarzanKHR import TarzanKHR
from motion.tarzanKHRProfiles import load_khr_settings, profile_from_settings, profile_names
from motion.tarzanKHRTracking import KHRTracking
from motion.tarzanKHRStepPreview import KHRStepPreview


class TarzanKHRWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.settings = load_khr_settings(PROJECT_ROOT)
        self.axis_name = self.settings.get("axis_name", "oś pozioma kamery")
        self.sample_time_ms = int(self.settings.get("sample_time_ms", 10))
        self.profile = profile_from_settings(self.settings)

        self.title("TARZAN - KHR / Korektor Choreografii Ruchu")
        self.geometry("1380x820")
        self.configure(bg="#111111")

        self.tracking = KHRTracking()
        self.tracking.apply_profile(self.profile)

        self.khr = TarzanKHR(plugins=[self.tracking], max_output=1.0)
        self.step_preview = KHRStepPreview()

        self.running = False
        self.t0 = time.time()
        self.time_ms = 0

        self.object_x = 0.0
        self.object_y = 0.0
        self.error_x = 0.0
        self.target_visible = True

        self.a_base = 0.0
        self.a_final = 0.0
        self.a_corr = 0.0

        self.dir_value = 1
        self.step_value = 0
        self.axis_angle = 0.0
        self.step_count = 0

        self._build_ui()
        self._apply_profile_to_ui(self.profile)
        self._draw_all()

    def _build_ui(self) -> None:
        top = tk.Frame(self, bg="#111111")
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        title = tk.Label(
            top,
            text="KHR - Korektor Choreografii Ruchu",
            bg="#111111",
            fg="#eeeeee",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(side=tk.LEFT)

        subtitle = tk.Label(
            top,
            text=f"  /  {self.axis_name}",
            bg="#111111",
            fg="#aaaaaa",
            font=("Segoe UI", 12),
        )
        subtitle.pack(side=tk.LEFT)

        self.profile_var = tk.StringVar(value=self.profile.name)
        profile_box = ttk.Combobox(
            top,
            textvariable=self.profile_var,
            values=profile_names(self.settings),
            width=16,
            state="readonly",
        )
        profile_box.pack(side=tk.RIGHT, padx=8)
        profile_box.bind("<<ComboboxSelected>>", self._on_profile_change)

        tk.Label(top, text="Profil:", bg="#111111", fg="#cccccc").pack(side=tk.RIGHT)

        self.btn_start = tk.Button(top, text="START", width=10, command=self.start)
        self.btn_start.pack(side=tk.RIGHT, padx=4)

        self.btn_stop = tk.Button(top, text="STOP", width=10, command=self.stop)
        self.btn_stop.pack(side=tk.RIGHT, padx=4)

        body = tk.Frame(self, bg="#111111")
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.left = self._make_panel(body, "WEJŚCIE - OBIEKT / TRACKING")
        self.middle = self._make_panel(body, "KOREKTA - KHR")
        self.right = self._make_panel(body, "WYNIK - OŚ POZIOMA KAMERY")

        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.middle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.input_canvas = tk.Canvas(self.left, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.input_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.khr_canvas = tk.Canvas(self.middle, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.khr_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.output_canvas = tk.Canvas(self.right, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.output_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        bottom = tk.Frame(self, bg="#111111")
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)

        self.profile_desc = tk.Label(
            bottom,
            text=self.profile.description,
            bg="#111111",
            fg="#d6d6d6",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.profile_desc.pack(fill=tk.X)

        self.status = tk.Label(
            bottom,
            text="STOP",
            bg="#111111",
            fg="#aaaaaa",
            font=("Consolas", 11),
            anchor="w",
        )
        self.status.pack(fill=tk.X, pady=(4, 0))

        self._make_settings_rows(bottom)

    def _make_panel(self, parent: tk.Widget, title: str) -> tk.Frame:
        frame = tk.Frame(parent, bg="#181818", highlightthickness=1, highlightbackground="#333333")
        label = tk.Label(
            frame,
            text=title,
            bg="#181818",
            fg="#f0f0f0",
            font=("Segoe UI", 11, "bold"),
        )
        label.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)
        return frame

    def _make_settings_rows(self, parent: tk.Widget) -> None:
        row1 = tk.Frame(parent, bg="#111111")
        row1.pack(fill=tk.X, pady=(8, 0))

        row2 = tk.Frame(parent, bg="#111111")
        row2.pack(fill=tk.X, pady=(4, 0))

        self.gain_var = tk.DoubleVar()
        self.dead_var = tk.DoubleVar()
        self.smooth_var = tk.DoubleVar()
        self.max_var = tk.DoubleVar()
        self.delta_var = tk.DoubleVar()
        self.pred_var = tk.DoubleVar()
        self.damp_var = tk.DoubleVar()
        self.speed_var = tk.DoubleVar()

        self._slider(row1, "gain", self.gain_var, 0.0005, 0.0100, 0.0005)
        self._slider(row1, "dead zone", self.dead_var, 0, 80, 1)
        self._slider(row1, "smooth", self.smooth_var, 0.02, 0.80, 0.01)
        self._slider(row1, "max corr", self.max_var, 0.05, 1.50, 0.05)

        self._slider(row2, "max delta", self.delta_var, 0.005, 0.150, 0.005)
        self._slider(row2, "prediction", self.pred_var, 0.0, 0.40, 0.01)
        self._slider(row2, "damping", self.damp_var, 0.0, 0.35, 0.01)
        self._slider(row2, "object speed", self.speed_var, 0.005, 0.080, 0.005)

    def _slider(self, parent: tk.Widget, label: str, variable: tk.DoubleVar, from_: float, to: float, resolution: float) -> None:
        box = tk.Frame(parent, bg="#111111")
        box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        tk.Label(box, text=label, bg="#111111", fg="#bbbbbb").pack(anchor="w")
        tk.Scale(
            box,
            variable=variable,
            from_=from_,
            to=to,
            resolution=resolution,
            orient=tk.HORIZONTAL,
            bg="#111111",
            fg="#eeeeee",
            troughcolor="#333333",
            highlightthickness=0,
            length=190,
        ).pack(fill=tk.X)

    def _on_profile_change(self, event=None) -> None:
        self.profile = profile_from_settings(self.settings, self.profile_var.get())
        self.tracking.apply_profile(self.profile)
        self._apply_profile_to_ui(self.profile)
        self.profile_desc.config(text=self.profile.description)

    def _apply_profile_to_ui(self, profile) -> None:
        self.gain_var.set(profile.gain)
        self.dead_var.set(profile.dead_zone_px)
        self.smooth_var.set(profile.smooth)
        self.max_var.set(profile.max_correction)
        self.delta_var.set(profile.max_delta_per_tick)
        self.pred_var.set(profile.prediction)
        self.damp_var.set(profile.damping)
        self.speed_var.set(profile.object_speed)

    def start(self) -> None:
        if self.running:
            return

        self.running = True
        self.t0 = time.time()
        self.step_preview = KHRStepPreview()
        self.axis_angle = 0.0
        self.step_count = 0
        self._loop()

    def stop(self) -> None:
        self.running = False
        self.status.config(text="STOP")

    def _loop(self) -> None:
        if not self.running:
            return

        self._apply_ui_settings()
        self.time_ms = int((time.time() - self.t0) * 1000)

        self._update_model()
        self._draw_all()
        self._update_status()

        self.after(self.sample_time_ms, self._loop)

    def _apply_ui_settings(self) -> None:
        self.tracking.update_manual_settings(
            gain=float(self.gain_var.get()),
            dead_zone_px=float(self.dead_var.get()),
            smooth=float(self.smooth_var.get()),
            max_correction=float(self.max_var.get()),
            max_delta_per_tick=float(self.delta_var.get()),
            prediction=float(self.pred_var.get()),
            damping=float(self.damp_var.get()),
            return_to_zero=self.profile.return_to_zero,
            lost_target_decay=self.profile.lost_target_decay,
        )

    def _update_model(self) -> None:
        phase = self.time_ms * float(self.speed_var.get()) / 1000.0

        self.object_x = math.sin(phase * 2.0 * math.pi) * 155.0
        self.object_y = math.sin(phase * 4.0 * math.pi) * 40.0

        # Symulacja chwilowej utraty celu co pewien czas, tylko w trybach testowych.
        self.target_visible = not (7000 < (self.time_ms % 12000) < 8000)

        self.error_x = self.object_x
        self.tracking.set_error(self.error_x, visible=self.target_visible)

        self.a_final = self.khr.update(self.axis_name, self.time_ms, self.a_base)
        self.a_corr = self.a_final - self.a_base

        self.dir_value, self.step_value = self.step_preview.sample(self.a_final)

        if self.step_value:
            self.step_count += 1
            step_angle = self.profile.step_angle_deg
            if self.dir_value == 1:
                self.axis_angle += step_angle
            else:
                self.axis_angle -= step_angle

    def _draw_all(self) -> None:
        self._draw_input()
        self._draw_khr()
        self._draw_output()

    def _draw_input(self) -> None:
        c = self.input_canvas
        c.delete("all")
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 320)
        cx = w / 2
        cy = h / 2

        c.create_line(cx, 20, cx, h - 20, fill="#666666", dash=(4, 4))
        c.create_line(20, cy, w - 20, cy, fill="#333333")
        c.create_text(cx, 34, text="środek kadru", fill="#aaaaaa", font=("Segoe UI", 10))

        dz = float(self.dead_var.get())
        c.create_rectangle(cx - dz, 55, cx + dz, h - 55, outline="#555555", dash=(3, 3))
        c.create_text(cx, 62, text="dead zone", fill="#777777", font=("Segoe UI", 9))

        ox = cx + self.object_x
        oy = cy + self.object_y
        size = 24

        if self.target_visible:
            points = [ox, oy - size, ox - size, oy + size, ox + size, oy + size]
            c.create_polygon(points, fill="#cc2222", outline="#ff7777", width=2)
            c.create_text(ox, oy + 42, text="obiekt", fill="#ff9999", font=("Segoe UI", 10))
        else:
            c.create_text(cx, cy, text="CEL UTRACONY", fill="#ff5555", font=("Segoe UI", 18, "bold"))

        c.create_line(cx, cy + 80, ox, cy + 80, fill="#ffaa00", width=2)
        c.create_text(cx, h - 48, text=f"error_x = {self.error_x:+.1f} px", fill="#eeeeee", font=("Consolas", 13, "bold"))

    def _draw_khr(self) -> None:
        c = self.khr_canvas
        c.delete("all")
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 320)
        cx = w / 2

        values = [("A_base", self.a_base), ("A_corr", self.a_corr), ("A_final", self.a_final)]
        y0 = 76
        gap = 82
        scale = 180

        for i, (name, value) in enumerate(values):
            y = y0 + i * gap
            c.create_text(36, y, text=name, fill="#cccccc", anchor="w", font=("Segoe UI", 11, "bold"))
            c.create_line(115, y, w - 35, y, fill="#444444")
            c.create_line(cx, y - 25, cx, y + 25, fill="#666666", dash=(3, 3))
            x = cx + value * scale
            c.create_rectangle(cx, y - 10, x, y + 10, fill="#2d7dff", outline="")
            c.create_text(w - 42, y, text=f"{value:+.3f}", fill="#eeeeee", anchor="e", font=("Consolas", 12))

        c.create_text(cx, h - 170, text=f"DIR = {self.dir_value}     STEP = {self.step_value}", fill="#ffffff", font=("Consolas", 18, "bold"))

        if abs(self.a_final) > 0.30:
            density_text = "gęściej"
        elif abs(self.a_final) > 0.05:
            density_text = "rzadziej"
        else:
            density_text = "stop"

        c.create_text(cx, h - 128, text=f"gęstość impulsów: {density_text}", fill="#ffaa00", font=("Segoe UI", 13, "bold"))

        c.create_text(
            cx,
            h - 88,
            text=f"profile={self.profile.name}  pred={self.pred_var.get():.2f}  damping={self.damp_var.get():.2f}",
            fill="#bbbbbb",
            font=("Consolas", 11),
        )

        c.create_text(
            cx,
            h - 58,
            text=f"max_delta={self.delta_var.get():.3f}  visible={int(self.target_visible)}",
            fill="#bbbbbb",
            font=("Consolas", 11),
        )

    def _draw_output(self) -> None:
        c = self.output_canvas
        c.delete("all")
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 320)
        cx = w / 2
        cy = h / 2 - 10
        radius = min(w, h) * 0.25

        c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#aaaaaa", width=3)
        c.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill="#cccccc", outline="#ffffff")

        for deg in range(0, 360, 45):
            a = math.radians(deg)
            x1 = cx + math.cos(a) * (radius - 12)
            y1 = cy + math.sin(a) * (radius - 12)
            x2 = cx + math.cos(a) * radius
            y2 = cy + math.sin(a) * radius
            c.create_line(x1, y1, x2, y2, fill="#555555", width=2)

        a = math.radians(self.axis_angle)
        flag_len = radius + 42
        x_tip = cx + math.cos(a) * flag_len
        y_tip = cy + math.sin(a) * flag_len
        c.create_line(cx, cy, x_tip, y_tip, fill="#ff3333", width=5)

        perp = a + math.pi / 2.0
        p1 = (x_tip, y_tip)
        p2 = (x_tip + math.cos(perp) * 24, y_tip + math.sin(perp) * 24)
        p3 = (x_tip + math.cos(a) * 26 + math.cos(perp) * 8, y_tip + math.sin(a) * 26 + math.sin(perp) * 8)
        c.create_polygon([p1, p2, p3], fill="#cc2222", outline="#ff8888")

        c.create_text(cx, h - 110, text=f"kąt osi = {self.axis_angle:+.1f}°", fill="#eeeeee", font=("Consolas", 14, "bold"))
        c.create_text(cx, h - 78, text=f"STEP count = {self.step_count}", fill="#cccccc", font=("Consolas", 12))
        c.create_text(cx, h - 48, text="flaga obraca się tylko przy STEP = 1", fill="#aaaaaa", font=("Segoe UI", 10))

    def _update_status(self) -> None:
        self.status.config(
            text=(
                f"RUN | t={self.time_ms} ms | "
                f"profile={self.profile.name} | "
                f"error_x={self.error_x:+.1f} | "
                f"A_corr={self.a_corr:+.3f} | "
                f"A_final={self.a_final:+.3f} | "
                f"DIR={self.dir_value} STEP={self.step_value}"
            )
        )


def main() -> None:
    app = TarzanKHRWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
