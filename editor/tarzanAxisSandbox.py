from __future__ import annotations

import copy
import math
import tkinter as tk
from dataclasses import dataclass
from typing import List


@dataclass
class AxisNode:
    time_ms: int
    y: float  # logical range -100..100


@dataclass
class AxisMechanics:
    axis_name: str = "oś wzorcowa"
    full_cycle_pulses: int = 9000
    min_full_cycle_time_s: float = 180.0  # 3 min
    start_settle_ms: int = 12000
    start_ramp_ms: int = 24000
    sample_ms: int = 10

    @property
    def take_duration_ms(self) -> int:
        return int(round(self.min_full_cycle_time_s * 1000.0))

    @property
    def max_step_per_sample(self) -> int:
        # Ustalony kontrakt sandboxu: STEP w próbce 10 ms może być tylko 0 albo 1.
        return 1

    @property
    def max_step_rate_per_s(self) -> float:
        return 1000.0 / float(self.sample_ms)


class AxisSandboxModel:
    """
    Sandbox jednej osi TARZAN.

    Założenia:
    - logika linii pozostaje oddzielona od widoku operatora,
    - amplituda y jest w zakresie -100..100,
    - MODEL B: gęstość impulsów ~ (|y|/100)^2,
    - pełny dodatni cykl ma budżet full_cycle_pulses,
    - STEP w każdej próbce 10 ms może być tylko 0 albo 1.
    """

    Y_LIMIT = 100.0
    MIN_NODE_GAP_MS = 500

    def __init__(self, mechanics: AxisMechanics) -> None:
        self.mechanics = mechanics
        self.nodes: List[AxisNode] = self._build_default_nodes()
        self._curve_cache: tuple[tuple[int, float], ...] | None = None
        self._step_cache: tuple[dict, ...] | None = None


    def _invalidate_cache(self) -> None:
        self._curve_cache = None
        self._step_cache = None

    def _build_default_nodes(self) -> List[AxisNode]:
        d = self.mechanics.take_duration_ms
        return [
            AxisNode(0, 0.0),
            AxisNode(int(d * 0.18), 18.0),
            AxisNode(int(d * 0.40), 42.0),
            AxisNode(int(d * 0.68), 16.0),
            AxisNode(d, 0.0),
        ]

    def set_flat_zero(self) -> None:
        d = self.mechanics.take_duration_ms
        self.nodes = [AxisNode(0, 0.0), AxisNode(d, 0.0)]
        self._invalidate_cache()

    def set_sinus_test(self) -> None:
        d = self.mechanics.take_duration_ms
        self.nodes = [
            AxisNode(0, 0.0),
            AxisNode(int(d * 0.16), 22.0),
            AxisNode(int(d * 0.30), 52.0),
            AxisNode(int(d * 0.50), 78.0),
            AxisNode(int(d * 0.72), 34.0),
            AxisNode(d, 0.0),
        ]
        self._invalidate_cache()

    def set_negative_test(self) -> None:
        d = self.mechanics.take_duration_ms
        self.nodes = [
            AxisNode(0, 0.0),
            AxisNode(int(d * 0.15), -18.0),
            AxisNode(int(d * 0.38), -48.0),
            AxisNode(int(d * 0.62), -22.0),
            AxisNode(d, 0.0),
        ]
        self._invalidate_cache()

    def clamp_y(self, value: float) -> float:
        return max(-self.Y_LIMIT, min(self.Y_LIMIT, float(value)))

    def snap_time(self, value_ms: float) -> int:
        step = self.mechanics.sample_ms
        return int(round(float(value_ms) / step) * step)

    def sort_and_fix_nodes(self) -> None:
        self.nodes.sort(key=lambda n: n.time_ms)
        if not self.nodes:
            self.nodes = [AxisNode(0, 0.0), AxisNode(self.mechanics.take_duration_ms, 0.0)]
            return

        self.nodes[0].time_ms = 0
        self.nodes[0].y = 0.0
        self.nodes[-1].time_ms = self.mechanics.take_duration_ms
        self.nodes[-1].y = 0.0

        for i in range(1, len(self.nodes) - 1):
            left = self.nodes[i - 1].time_ms + self.MIN_NODE_GAP_MS
            right = self.nodes[i + 1].time_ms - self.MIN_NODE_GAP_MS if i + 1 < len(self.nodes) else self.mechanics.take_duration_ms
            self.nodes[i].time_ms = self.snap_time(self.nodes[i].time_ms)
            self.nodes[i].time_ms = max(left, min(right, self.nodes[i].time_ms))
            self.nodes[i].y = self.clamp_y(self.nodes[i].y)

    def add_node(self, time_ms: int, y: float) -> None:
        t = self.snap_time(time_ms)
        y = self.clamp_y(y)
        self.nodes.append(AxisNode(t, y))
        self.sort_and_fix_nodes()
        self._invalidate_cache()

    def remove_node(self, index: int) -> None:
        if index <= 0 or index >= len(self.nodes) - 1:
            return
        del self.nodes[index]
        self.sort_and_fix_nodes()
        self._invalidate_cache()

    def move_node(self, index: int, time_ms: int | None = None, y: float | None = None) -> None:
        if index < 0 or index >= len(self.nodes):
            return
        node = self.nodes[index]
        if time_ms is not None:
            node.time_ms = self.snap_time(time_ms)
        if y is not None:
            node.y = self.clamp_y(y)
        if index == 0 or index == len(self.nodes) - 1:
            node.y = 0.0
        self.sort_and_fix_nodes()
        self._invalidate_cache()

    def shift_all(self, delta_ms: int) -> None:
        if len(self.nodes) <= 2:
            return
        delta_ms = self.snap_time(delta_ms)
        inner = copy.deepcopy(self.nodes[1:-1])
        for n in inner:
            n.time_ms += delta_ms
        left_limit = self.MIN_NODE_GAP_MS
        right_limit = self.mechanics.take_duration_ms - self.MIN_NODE_GAP_MS
        if inner:
            min_shifted = min(n.time_ms for n in inner)
            max_shifted = max(n.time_ms for n in inner)
            correction = 0
            if min_shifted < left_limit:
                correction = left_limit - min_shifted
            if max_shifted > right_limit:
                correction = right_limit - max_shifted if correction == 0 else correction
            for n in inner:
                n.time_ms += correction
        self.nodes = [self.nodes[0]] + inner + [self.nodes[-1]]
        self.sort_and_fix_nodes()
        self._invalidate_cache()

    def _pchip_slopes(self, xs: List[float], ys: List[float]) -> List[float]:
        n = len(xs)
        if n < 2:
            return [0.0] * n
        h = [xs[i + 1] - xs[i] for i in range(n - 1)]
        delta = [(ys[i + 1] - ys[i]) / h[i] if h[i] != 0 else 0.0 for i in range(n - 1)]
        m = [0.0] * n
        if n == 2:
            m[0] = delta[0]
            m[1] = delta[0]
            return m
        for i in range(1, n - 1):
            if delta[i - 1] == 0.0 or delta[i] == 0.0 or (delta[i - 1] > 0) != (delta[i] > 0):
                m[i] = 0.0
            else:
                w1 = 2 * h[i] + h[i - 1]
                w2 = h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / ((w1 / delta[i - 1]) + (w2 / delta[i]))
        m[0] = self._edge_slope(h[0], h[1], delta[0], delta[1])
        m[-1] = self._edge_slope(h[-1], h[-2], delta[-1], delta[-2])
        return m

    def _edge_slope(self, h0: float, h1: float, d0: float, d1: float) -> float:
        m = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1) if (h0 + h1) != 0 else 0.0
        if (m > 0) != (d0 > 0):
            return 0.0
        if (d0 > 0) != (d1 > 0) and abs(m) > abs(3 * d0):
            return 3 * d0
        return m

    def sample_curve(self, steps: int = 800) -> List[tuple[int, float]]:
        self.sort_and_fix_nodes()
        if self._curve_cache is not None:
            return list(self._curve_cache)
        xs = [float(n.time_ms) for n in self.nodes]
        ys = [float(n.y) for n in self.nodes]
        if len(xs) < 2:
            return []
        m = self._pchip_slopes(xs, ys)
        result: List[tuple[int, float]] = []
        duration = self.mechanics.take_duration_ms
        dense = max(steps, 120)
        seg = 0
        for k in range(dense + 1):
            t = duration * (k / dense)
            while seg < len(xs) - 2 and t > xs[seg + 1]:
                seg += 1
            x0, x1 = xs[seg], xs[seg + 1]
            y0, y1 = ys[seg], ys[seg + 1]
            if x1 <= x0:
                y = y1
            else:
                h = x1 - x0
                u = (t - x0) / h
                h00 = 2 * u**3 - 3 * u**2 + 1
                h10 = u**3 - 2 * u**2 + u
                h01 = -2 * u**3 + 3 * u**2
                h11 = u**3 - u**2
                y = h00 * y0 + h10 * h * m[seg] + h01 * y1 + h11 * h * m[seg + 1]
            result.append((int(round(t)), self.clamp_y(y)))
        self._curve_cache = tuple(result)
        return list(self._curve_cache)

    def y_at(self, time_ms: int) -> float:
        samples = self.sample_curve(800)
        if not samples:
            return 0.0
        t = int(time_ms)
        if t <= samples[0][0]:
            return samples[0][1]
        if t >= samples[-1][0]:
            return samples[-1][1]
        prev_t, prev_y = samples[0]
        for cur_t, cur_y in samples[1:]:
            if t <= cur_t:
                if cur_t == prev_t:
                    return cur_y
                rel = (t - prev_t) / float(cur_t - prev_t)
                return prev_y + (cur_y - prev_y) * rel
            prev_t, prev_y = cur_t, cur_y
        return samples[-1][1]

    def build_step_rows(self) -> List[dict]:
        if self._step_cache is not None:
            return [dict(r) for r in self._step_cache]
        rows = []
        sample_ms = self.mechanics.sample_ms
        steps = self.mechanics.take_duration_ms // sample_ms
        accumulator = 0.0
        count = 0
        prev_sign = 0

        samples = self.sample_curve(800)
        sample_idx = 0
        prev_t, prev_y = samples[0]
        next_t, next_y = samples[1] if len(samples) > 1 else samples[0]

        for i in range(steps + 1):
            t = i * sample_ms
            while sample_idx < len(samples) - 2 and t > samples[sample_idx + 1][0]:
                sample_idx += 1
                prev_t, prev_y = samples[sample_idx]
                next_t, next_y = samples[sample_idx + 1]
            if next_t == prev_t:
                y = next_y
            else:
                rel = (t - prev_t) / float(next_t - prev_t)
                rel = max(0.0, min(1.0, rel))
                y = prev_y + (next_y - prev_y) * rel

            if y > 1e-9:
                sign = 1
            elif y < -1e-9:
                sign = -1
            else:
                sign = 0
            if sign != 0:
                prev_sign = sign
            dir_bit = 1 if prev_sign >= 0 else 0
            abs_y = abs(y)
            if abs_y <= 5.0:
                rate = 0.0
            else:
                normalized = max(0.0, min(1.0, (abs_y - 5.0) / 95.0))
                rate = (normalized ** 4) * self.mechanics.max_step_rate_per_s
            density = rate * (sample_ms / 1000.0)
            density = max(0.0, min(float(self.mechanics.max_step_per_sample), density))
            accumulator += density
            step = 0
            if accumulator >= 1.0:
                step = 1
                accumulator -= 1.0
                count += 1
            rows.append({
                "time_ms": t,
                "y": y,
                "dir": dir_bit,
                "step": step,
                "count": count,
                "rate": rate,
            })
        self._step_cache = tuple(dict(r) for r in rows)
        return [dict(r) for r in self._step_cache]

    def current_pulse_count(self) -> int:
        rows = self.build_step_rows()
        return int(rows[-1]["count"]) if rows else 0

    def pulse_budget_ratio(self) -> float:
        if self.mechanics.full_cycle_pulses <= 0:
            return 0.0
        return self.current_pulse_count() / float(self.mechanics.full_cycle_pulses)


class AxisSandboxWindow(tk.Tk):
    BG = "#16181C"
    PANEL = "#23272E"
    PANEL2 = "#2A3038"
    FG = "#F3F6F8"
    MUTED = "#AEB7C2"
    CURVE = "#D9E7F5"
    CURVE_GHOST = "#8B949E"
    NODE = "#FFD166"
    NODE_SEL = "#FF9F1C"
    STEP_ON = "#45C46B"
    STEP_OFF = "#48525E"
    SAFE = "#1E3A2F"
    WARN = "#5A4A1B"
    DANGER = "#4A2222"

    def __init__(self) -> None:
        super().__init__()
        self.title("TARZAN — Axis Sandbox")
        self.geometry("1700x980")
        self.configure(bg=self.BG)
        self.minsize(1400, 860)

        self.mechanics = AxisMechanics()
        self.model = AxisSandboxModel(self.mechanics)
        self.original_nodes = copy.deepcopy(self.model.nodes)

        self.display_y_scale = tk.DoubleVar(value=500.0)  # only view scale (operator range)
        self.mouse_y_precision = tk.DoubleVar(value=0.45)
        self.top_bottom_margin = tk.IntVar(value=24)

        self.selected_index: int | None = None
        self.drag_mode: str | None = None
        self.drag_anchor_x = 0
        self.drag_anchor_time = 0
        self.drag_anchor_y = 0
        self.drag_anchor_node_time = 0
        self.drag_anchor_node_y = 0.0
        self.live_preview_during_drag = False

        self.status_var = tk.StringVar(value="Gotowy.")
        self.metrics_var = tk.StringVar(value="")

        self._build_ui()
        self._refresh_all()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="TARZAN — SANDBOX JEDNEJ OSI", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 16)).pack(side="left")

        btns = tk.Frame(top, bg=self.BG)
        btns.pack(side="right")
        self._btn(btns, "SINUS TEST", self._sinus_test, "#2D6CDF").pack(side="left", padx=3)
        self._btn(btns, "NEG TEST", self._negative_test, "#6F42C1").pack(side="left", padx=3)
        self._btn(btns, "FLAT 0", self._flat_zero, "#C78B2A").pack(side="left", padx=3)
        self._btn(btns, "RESET", self._reset_nodes, "#BE185D").pack(side="left", padx=3)

        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.BG, width=290)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(left)

        self.curve_canvas = tk.Canvas(right, bg="#1B2028", height=430, highlightthickness=0)
        self.curve_canvas.pack(fill="x", pady=(0, 8))
        self.curve_canvas.bind("<Button-1>", self._on_curve_press)
        self.curve_canvas.bind("<B1-Motion>", self._on_curve_drag)
        self.curve_canvas.bind("<ButtonRelease-1>", self._on_curve_release)
        self.curve_canvas.bind("<Double-Button-1>", self._on_curve_double_click)
        self.curve_canvas.bind("<Button-3>", self._on_curve_right_click)

        self.step_canvas = tk.Canvas(right, bg="#1A1E24", height=260, highlightthickness=0)
        self.step_canvas.pack(fill="both", expand=True)

        status = tk.Label(outer, textvariable=self.status_var, bg=self.PANEL2, fg=self.FG, anchor="w", padx=10, pady=8, font=("Segoe UI", 9))
        status.pack(fill="x", pady=(8, 0))

    def _build_left_panel(self, parent: tk.Misc) -> None:
        tk.Label(parent, text=self.mechanics.axis_name.upper(), bg=self.BG, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 12)).pack(fill="x", pady=(0, 8))
        tk.Label(parent, textvariable=self.metrics_var, bg=self.BG, fg=self.MUTED, justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x", pady=(0, 12))

        box = tk.Frame(parent, bg=self.PANEL)
        box.pack(fill="x", pady=(0, 10))
        box.pack_propagate(False)

        self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0)
        self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05)
        self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1)

        info = tk.Text(parent, height=19, bg=self.PANEL2, fg=self.FG, relief="flat", wrap="word", font=("Segoe UI", 9))
        info.pack(fill="both", expand=True)
        info.insert(
            "1.0",
            "MODEL SANDBOX\n\n"
            "• amplituda logiczna: -100 .. +100\n"
            "• MODEL B+: soft low-end, dead zone ±5, rate = ((|Y|-5)/95)^4 * max_rate\n"
            "• STEP w próbce 10 ms: tylko 0 lub 1\n"
            "• START = 0, STOP = 0\n"
            "• przejście przez 0 = stop lub zmiana kierunku\n\n"
            "OBSŁUGA\n\n"
            "• drag punktu = edycja węzła\n"
            "• drag na pustym polu = PAN całej linii\n"
            "• double click = dodaj punkt\n"
            "• right click na punkcie = usuń punkt\n"
            "• suwaki stroją tylko widok operatora\n"
        )
        info.configure(state="disabled")

    def _scale_row(self, parent, label, var, from_, to, resolution):
        wrap = tk.Frame(parent, bg=self.PANEL)
        wrap.pack(fill="x", padx=10, pady=8)
        tk.Label(wrap, text=label, bg=self.PANEL, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        scale = tk.Scale(
            wrap,
            variable=var,
            from_=from_,
            to=to,
            resolution=resolution,
            orient="horizontal",
            command=lambda _v: self._refresh_all(),
            bg=self.PANEL,
            fg=self.FG,
            troughcolor="#39424E",
            highlightthickness=0,
            bd=0,
            length=240,
        )
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color, activeforeground="white", relief="flat", bd=0, padx=10, pady=6, font=("Segoe UI Semibold", 9), cursor="hand2")

    def _sinus_test(self) -> None:
        self.model.set_sinus_test()
        self.original_nodes = copy.deepcopy(self.model.nodes)
        self._refresh_all("Sinus test ustawiony.")

    def _negative_test(self) -> None:
        self.model.set_negative_test()
        self.original_nodes = copy.deepcopy(self.model.nodes)
        self._refresh_all("Negative test ustawiony.")

    def _flat_zero(self) -> None:
        self.model.set_flat_zero()
        self.original_nodes = copy.deepcopy(self.model.nodes)
        self._refresh_all("Linia wyzerowana.")

    def _reset_nodes(self) -> None:
        self.model.nodes = copy.deepcopy(self.original_nodes)
        self._refresh_all("Przywrócono ostatni stan bazowy.")

    def _curve_rect(self):
        w = max(300, int(self.curve_canvas.winfo_width() or 1200))
        h = max(220, int(self.curve_canvas.winfo_height() or 430))
        return 70, 14, w - 20, h - 20

    def _step_rect(self):
        w = max(300, int(self.step_canvas.winfo_width() or 1200))
        h = max(120, int(self.step_canvas.winfo_height() or 260))
        return 70, 16, w - 20, h - 24

    def _time_to_x(self, t_ms: int, left: int, right: int) -> float:
        span = max(1, self.mechanics.take_duration_ms)
        return left + (t_ms / span) * (right - left)

    def _x_to_time(self, x: float, left: int, right: int) -> int:
        rel = (x - left) / max(1.0, (right - left))
        rel = max(0.0, min(1.0, rel))
        return self.model.snap_time(rel * self.mechanics.take_duration_ms)

    def _logical_y_to_canvas(self, y: float, top: int, bottom: int) -> float:
        # tylko widok operatora; nie zmienia matematyki linii
        # amplituda logiczna nadal jest -100..+100, ale operator pracuje
        # w większej, przeskalowanej przestrzeni manipulacji np. 500.
        operator_range = max(200.0, float(self.display_y_scale.get()))
        logical_limit = max(1.0, float(self.model.Y_LIMIT))
        operator_y = float(y) * (operator_range / logical_limit)
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.top_bottom_margin.get())
        return mid - (operator_y / operator_range) * usable

    def _canvas_to_logical_y(self, py: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(self.display_y_scale.get()))
        logical_limit = max(1.0, float(self.model.Y_LIMIT))
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.top_bottom_margin.get())
        operator_y = ((mid - py) / max(1.0, usable)) * operator_range
        logical_y = operator_y * (logical_limit / operator_range)
        return self.model.clamp_y(logical_y)

    def _drag_delta_to_logical_y(self, delta_py: float, top: int, bottom: int) -> float:
        # Drag ma pozostać lekki dla ręki niezależnie od tego,
        # jak duży zakres operatora pokażemy w widoku.
        logical_limit = max(1.0, float(self.model.Y_LIMIT))
        usable = (bottom - top) / 2.0 - float(self.top_bottom_margin.get())
        precision = max(0.05, float(self.mouse_y_precision.get()))
        logical_per_px = logical_limit / max(1.0, usable)
        return float(delta_py) * logical_per_px * precision

    def _draw_curve(self) -> None:
        c = self.curve_canvas
        c.delete("all")
        left, top, right, bottom = self._curve_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="#303A45")

        # overlay mechaniki: bezpieczne strefy czasu rozruchu/hamowania
        settle = self.mechanics.start_settle_ms
        ramp = self.mechanics.start_ramp_ms
        start_total = settle + ramp
        stop_from = self.mechanics.take_duration_ms - start_total
        sx = self._time_to_x(start_total, left, right)
        ex = self._time_to_x(stop_from, left, right)
        c.create_rectangle(left, top, sx, bottom, fill=self.WARN, outline="")
        c.create_rectangle(ex, top, right, bottom, fill=self.WARN, outline="")
        c.create_rectangle(sx, top, ex, bottom, fill=self.SAFE, outline="")

        # strefy Y: odniesienie mechaniczne, nie blokada widoku
        for yv, color in [(100, self.DANGER), (50, self.WARN), (0, "#FF3030"), (-50, self.WARN), (-100, self.DANGER)]:
            py = self._logical_y_to_canvas(yv, top, bottom)
            width = 3 if yv == 0 else 1
            dash = None if yv == 0 else (5, 4)
            c.create_line(left, py, right, py, fill=color if yv != 0 else "#FF3030", width=width, dash=dash)
            c.create_text(left - 8, py, text=str(yv), fill=self.MUTED, anchor="e", font=("Consolas", 8))

        # time grid
        for minute in range(0, int(self.mechanics.min_full_cycle_time_s // 60) + 1):
            t_ms = minute * 60_000
            if t_ms > self.mechanics.take_duration_ms:
                continue
            px = self._time_to_x(t_ms, left, right)
            c.create_line(px, top, px, bottom, fill="#43505C", dash=(2, 6))
            c.create_text(px, bottom + 10, text=f"{minute}m", fill=self.MUTED, anchor="n", font=("Consolas", 8))

        # curve
        samples = self.model.sample_curve(1000)
        pts = []
        for t, y in samples:
            pts.extend([self._time_to_x(t, left, right), self._logical_y_to_canvas(y, top, bottom)])
        if len(pts) >= 4:
            c.create_line(*pts, fill=self.CURVE, width=3, smooth=True)

        # nodes
        for i, n in enumerate(self.model.nodes):
            px = self._time_to_x(n.time_ms, left, right)
            py = self._logical_y_to_canvas(n.y, top, bottom)
            r = 7
            fill = self.NODE_SEL if i == self.selected_index else self.NODE
            if i == 0 or i == len(self.model.nodes) - 1:
                fill = "#D6EAF8"
            c.create_oval(px - r, py - r, px + r, py + r, fill=fill, outline="black")

        # start/stop labels
        x0 = self._time_to_x(0, left, right)
        x1 = self._time_to_x(self.mechanics.take_duration_ms, left, right)
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

        visible_rows = rows  # całość; przy 3 min i 10 ms będzie dużo, więc agregujemy po px
        width = max(1, right - left)
        px_bucket = {}
        for row in visible_rows:
            x = int(round(self._time_to_x(row["time_ms"], left, right)))
            bucket = px_bucket.setdefault(x, {"step": 0, "count": 0})
            bucket["step"] = max(bucket["step"], int(row["step"]))
            bucket["count"] = int(row["count"])

        y_mid = (top + bottom) / 2.0
        c.create_line(left, y_mid, right, y_mid, fill="#55606D")
        for x in sorted(px_bucket.keys()):
            row = px_bucket[x]
            if row["step"] == 1:
                c.create_line(x, y_mid, x, top + 12, fill=self.STEP_ON, width=1)
            else:
                c.create_line(x, y_mid, x, y_mid + 8, fill=self.STEP_OFF, width=1)

        # labels
        c.create_text(left, top - 2, text="STEP 0/1 preview (zagregowany do px)", fill=self.FG, anchor="sw", font=("Segoe UI Semibold", 9))
        c.create_text(right, top - 2, text=f"rows={len(rows)}", fill=self.MUTED, anchor="se", font=("Consolas", 8))

    def _refresh_metrics(self) -> None:
        pulse_count = self.model.current_pulse_count()
        budget = self.mechanics.full_cycle_pulses
        ratio = (pulse_count / budget) if budget else 0.0
        rows = self.model.build_step_rows()
        peak_abs_y = max((abs(r["y"]) for r in rows), default=0.0)
        peak_rate = max((r["rate"] for r in rows), default=0.0)
        self.metrics_var.set(
            f"budżet impulsów : {pulse_count} / {budget}\n"
            f"wypełnienie      : {ratio * 100:6.2f} %\n"
            f"max |Y|          : {peak_abs_y:6.2f}\n"
            f"max rate         : {peak_rate:6.2f} step/s\n"
            f"sample           : {self.mechanics.sample_ms} ms\n"
            f"zakres operatora : ±{int(round(self.display_y_scale.get()))}\n"
            f"czas TAKE        : {self.mechanics.take_duration_ms / 1000.0:6.1f} s\n"
            f"pełny cykl min   : {self.mechanics.min_full_cycle_time_s:6.1f} s\n"
        )

    def _refresh_all(self, status: str | None = None, full: bool = True) -> None:
        self.model.sort_and_fix_nodes()
        self._draw_curve()
        if full:
            self._refresh_metrics()
            self._draw_step()
        if status is not None:
            self.status_var.set(status)
        else:
            self.status_var.set("Sandbox osi gotowy do strojenia.")

    def _hit_node(self, x: float, y: float) -> int | None:
        left, top, right, bottom = self._curve_rect()
        for i, n in enumerate(self.model.nodes):
            px = self._time_to_x(n.time_ms, left, right)
            py = self._logical_y_to_canvas(n.y, top, bottom)
            if abs(px - x) <= 14 and abs(py - y) <= 14:
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
        self.drag_anchor_time = 0
        self._refresh_all("PAN linii.")

    def _on_curve_drag(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        if self.drag_mode == "node" and self.selected_index is not None:
            delta_y = self.drag_anchor_y - event.y
            new_y = self.drag_anchor_node_y + self._drag_delta_to_logical_y(delta_y, top, bottom)

            delta_t = self._x_to_time(event.x, left, right) - self._x_to_time(self.drag_anchor_x, left, right)
            if abs(delta_t) < self.mechanics.sample_ms * 2:
                new_t = self.drag_anchor_node_time
            else:
                new_t = self.drag_anchor_node_time + delta_t

            self.model.move_node(self.selected_index, new_t, new_y)
            if self.live_preview_during_drag:
                self._refresh_all(f"Drag punktu {self.selected_index}.", full=False)
            else:
                self._draw_curve()
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(event.x, left, right)
            old_time = self._x_to_time(self.drag_anchor_x, left, right)
            delta = new_time - old_time
            self.drag_anchor_x = event.x
            self.model.shift_all(delta)
            if self.live_preview_during_drag:
                self._refresh_all("PAN linii.", full=False)
            else:
                self._draw_curve()

    def _on_curve_release(self, _event) -> None:
        self.drag_mode = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._refresh_all("Gotowy.", full=True)

    def _on_curve_double_click(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        t = self._x_to_time(event.x, left, right)
        y = self._canvas_to_logical_y(event.y, top, bottom)
        self.model.add_node(t, y)
        self._refresh_all("Dodano punkt.")

    def _on_curve_right_click(self, event) -> None:
        idx = self._hit_node(event.x, event.y)
        if idx is None:
            return
        self.model.remove_node(idx)
        self.selected_index = None
        self._refresh_all("Usunięto punkt.")


def main() -> None:
    app = AxisSandboxWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
