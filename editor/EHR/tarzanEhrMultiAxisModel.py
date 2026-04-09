from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass
class AxisNode:
    time_ms: int
    y: float


@dataclass
class AxisMechanics:
    axis_name: str = "oś wzorcowa"
    full_cycle_pulses: int = 9000
    min_full_cycle_time_s: float = 180.0
    start_settle_ms: int = 12000
    start_ramp_ms: int = 24000
    sample_ms: int = 10

    @property
    def take_duration_ms(self) -> int:
        return int(round(self.min_full_cycle_time_s * 1000.0))

    @property
    def max_step_per_sample(self) -> int:
        return 1

    @property
    def max_step_rate_per_s(self) -> float:
        return 1000.0 / float(self.sample_ms)


MECHANICS_PRESETS: Dict[str, AxisMechanics] = {
    "oś wzorcowa": AxisMechanics(),
    "oś pozioma kamery": AxisMechanics("oś pozioma kamery", 28800, 180.0, 12000, 24000, 10),
    "oś pionowa kamery": AxisMechanics("oś pionowa kamery", 12800, 120.0, 9000, 18000, 10),
    "oś pochyłu kamery": AxisMechanics("oś pochyłu kamery", 3200, 60.0, 5000, 9000, 10),
    "oś ostrości kamery": AxisMechanics("oś ostrości kamery", 30764, 60.0, 3000, 7000, 10),
    "oś pionowa ramienia": AxisMechanics("oś pionowa ramienia", 28485, 600.0, 20000, 40000, 10),
    "oś pozioma ramienia": AxisMechanics("oś pozioma ramienia", 92273, 900.0, 30000, 60000, 10),
    "DRON": AxisMechanics("DRON", 1, 60.0, 0, 0, 10),
}


@dataclass
class EhrAxisDefinition:
    axis_id: str
    axis_name: str
    color: str


@dataclass
class EhrEditorConfig:
    min_node_gap_ms: int = 500
    y_limit: float = 100.0


@dataclass
class AxisSandboxSettings:
    display_y_scale: float = 500.0
    mouse_y_precision: float = 0.45
    top_bottom_margin: int = 24


@dataclass
class StepTuning:
    dead_zone_y: float = 5.0
    input_max_y: float = 100.0
    input_gamma: float = 4.0
    step_rate_gain: float = 1.0
    step_rate_max_percent: float = 100.0
    preview_rate_smoothing: float = 0.0
    bucket_width_px: int = 1
    off_bar_height: int = 8
    low_zone_gain: float = 0.25
    mid_zone_gain: float = 0.55
    high_zone_gain: float = 1.0
    accumulator_bias: float = 0.0
    emit_threshold: float = 1.0
    node_hit_radius_px: int = 14
    time_drag_threshold_samples: int = 2

    def clamp(self) -> None:
        self.dead_zone_y = max(0.0, min(95.0, float(self.dead_zone_y)))
        self.input_max_y = max(self.dead_zone_y + 1.0, min(100.0, float(self.input_max_y)))
        self.input_gamma = max(0.10, min(12.0, float(self.input_gamma)))
        self.step_rate_gain = max(0.01, min(5.0, float(self.step_rate_gain)))
        self.step_rate_max_percent = max(1.0, min(100.0, float(self.step_rate_max_percent)))
        self.preview_rate_smoothing = max(0.0, min(0.95, float(self.preview_rate_smoothing)))
        self.bucket_width_px = max(1, min(16, int(round(self.bucket_width_px))))
        self.off_bar_height = max(1, min(40, int(round(self.off_bar_height))))
        self.low_zone_gain = max(0.0, min(2.0, float(self.low_zone_gain)))
        self.mid_zone_gain = max(0.0, min(2.0, float(self.mid_zone_gain)))
        self.high_zone_gain = max(0.0, min(2.0, float(self.high_zone_gain)))
        self.accumulator_bias = max(0.0, min(0.99, float(self.accumulator_bias)))
        self.emit_threshold = max(0.20, min(2.0, float(self.emit_threshold)))
        self.node_hit_radius_px = max(6, min(30, int(round(self.node_hit_radius_px))))
        self.time_drag_threshold_samples = max(0, min(10, int(round(self.time_drag_threshold_samples))))

    def to_text(self, mechanics: AxisMechanics) -> str:
        self.clamp()
        payload = {
            **asdict(self),
            "axis_name": mechanics.axis_name,
            "full_cycle_pulses": mechanics.full_cycle_pulses,
            "min_full_cycle_time_s": mechanics.min_full_cycle_time_s,
            "start_settle_ms": mechanics.start_settle_ms,
            "start_ramp_ms": mechanics.start_ramp_ms,
            "sample_ms": mechanics.sample_ms,
        }
        lines = ["AXIS_SANDBOX_STEP_PRESET"]
        for key, value in payload.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines) + "\n"

    @classmethod
    def from_text(cls, text: str) -> tuple["StepTuning", AxisMechanics | None]:
        tuning = cls()
        mechanics = None
        raw: Dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("AXIS_SANDBOX_STEP_PRESET") or "=" not in line:
                continue
            key, value = [part.strip() for part in line.split("=", 1)]
            raw[key] = value
        for key, value in raw.items():
            if hasattr(tuning, key):
                current = getattr(tuning, key)
                try:
                    setattr(tuning, key, int(float(value)) if isinstance(current, int) else float(value))
                except ValueError:
                    pass
        tuning.clamp()
        mechanic_keys = {"axis_name", "full_cycle_pulses", "min_full_cycle_time_s", "start_settle_ms", "start_ramp_ms", "sample_ms"}
        if mechanic_keys.intersection(raw.keys()):
            try:
                mechanics = AxisMechanics(
                    axis_name=raw.get("axis_name", "oś z TXT"),
                    full_cycle_pulses=int(float(raw.get("full_cycle_pulses", "9000"))),
                    min_full_cycle_time_s=float(raw.get("min_full_cycle_time_s", "180.0")),
                    start_settle_ms=int(float(raw.get("start_settle_ms", "12000"))),
                    start_ramp_ms=int(float(raw.get("start_ramp_ms", "24000"))),
                    sample_ms=int(float(raw.get("sample_ms", "10"))),
                )
            except ValueError:
                mechanics = None
        return tuning, mechanics


class AxisCurveModel:
    def __init__(self, axis_def: EhrAxisDefinition, config: EhrEditorConfig) -> None:
        self.axis_def = axis_def
        self.config = config
        self.mechanics = copy.deepcopy(MECHANICS_PRESETS.get(axis_def.axis_name, MECHANICS_PRESETS["oś wzorcowa"]))
        self.sandbox = AxisSandboxSettings()
        self.step_tuning = StepTuning()
        self.is_release_axis = axis_def.axis_id == "dron"
        self.release_time_ms: int | None = None
        self.axis_take_duration_ms: int | None = None
        self.nodes: List[AxisNode] = self._build_default_nodes()
        if self.is_release_axis:
            self.release_time_ms = self.snap_time(self.take_duration_ms * 0.5)
        self.original_nodes: List[AxisNode] = copy.deepcopy(self.nodes)
        self._curve_cache: dict[tuple[int, int], tuple[tuple[int, float], ...]] = {}
        self._step_cache: dict[int, tuple[dict, ...]] = {}

    @property
    def take_duration_ms(self) -> int:
        return self.axis_take_duration_ms if self.axis_take_duration_ms is not None else self.mechanics.take_duration_ms

    @property
    def sample_ms(self) -> int:
        return self.mechanics.sample_ms

    def clone_original_state(self) -> None:
        self.original_nodes = copy.deepcopy(self.nodes)

    def reset_to_original_state(self) -> None:
        self.nodes = copy.deepcopy(self.original_nodes)
        self._invalidate_cache()

    def _invalidate_cache(self) -> None:
        self._curve_cache.clear()
        self._step_cache.clear()

    def set_mechanics(self, mechanics: AxisMechanics) -> None:
        self.mechanics = copy.deepcopy(mechanics)
        self.nodes = self._build_default_nodes()
        if self.is_release_axis:
            self.release_time_ms = self.snap_time(self.take_duration_ms * 0.5)
        self.clone_original_state()
        self._invalidate_cache()

    def set_axis_take_duration_ms(self, take_duration_ms: int | None) -> None:
        old_duration = max(self.sample_ms, self.take_duration_ms)
        self.axis_take_duration_ms = None if take_duration_ms is None else self.snap_time(max(self.sample_ms, int(take_duration_ms)))
        new_duration = max(self.sample_ms, self.take_duration_ms)

        if self.is_release_axis:
            if self.release_time_ms is None:
                self.release_time_ms = self.snap_time(new_duration * 0.5)
            else:
                scaled_release = int(round(self.release_time_ms * new_duration / old_duration))
                self.release_time_ms = self.snap_time(max(0, min(new_duration, scaled_release)))
            self.nodes = [AxisNode(0, 0.0), AxisNode(new_duration, 0.0)]
            self.clone_original_state()
            self._invalidate_cache()
            return

        scaled_nodes: List[AxisNode] = []
        for index, node in enumerate(self.nodes):
            if index == 0:
                scaled_nodes.append(AxisNode(0, 0.0))
            elif index == len(self.nodes) - 1:
                scaled_nodes.append(AxisNode(new_duration, 0.0))
            else:
                scaled_time = int(round(node.time_ms * new_duration / old_duration))
                scaled_nodes.append(AxisNode(self.snap_time(scaled_time), node.y))
        self.nodes = scaled_nodes
        self.sort_and_fix_nodes()
        self.clone_original_state()
        self._invalidate_cache()

    def set_step_tuning(self, tuning: StepTuning) -> None:
        tuning.clamp()
        self.step_tuning = copy.deepcopy(tuning)
        self._invalidate_cache()

    def apply_zero_snap(self, main_take_settings, value: float) -> float:
        value = self.clamp_y(value)
        if not getattr(main_take_settings, "snap_to_zero_enabled", False):
            return value
        threshold = float(getattr(main_take_settings, "snap_to_zero_threshold", 0.0))
        effective_threshold = max(0.0, threshold * 0.35)
        return 0.0 if abs(value) <= effective_threshold else value

    def _build_default_nodes(self) -> List[AxisNode]:
        d = self.take_duration_ms
        if self.is_release_axis:
            return [AxisNode(0, 0.0), AxisNode(d, 0.0)]
        return [AxisNode(0, 0.0), AxisNode(int(d * 0.18), 18.0), AxisNode(int(d * 0.40), 42.0), AxisNode(int(d * 0.68), 16.0), AxisNode(d, 0.0)]

    def set_flat_zero(self) -> None:
        d = self.take_duration_ms
        self.nodes = [AxisNode(0, 0.0), AxisNode(d, 0.0)]
        self._invalidate_cache()

    def set_sinus_test(self) -> None:
        d = self.take_duration_ms
        self.nodes = [AxisNode(0, 0.0), AxisNode(int(d * 0.16), 22.0), AxisNode(int(d * 0.30), 52.0), AxisNode(int(d * 0.50), 78.0), AxisNode(int(d * 0.72), 34.0), AxisNode(d, 0.0)]
        self._invalidate_cache()

    def set_negative_test(self) -> None:
        d = self.take_duration_ms
        self.nodes = [AxisNode(0, 0.0), AxisNode(int(d * 0.15), -18.0), AxisNode(int(d * 0.38), -48.0), AxisNode(int(d * 0.62), -22.0), AxisNode(d, 0.0)]
        self._invalidate_cache()

    def set_zero_cross_test(self) -> None:
        d = self.take_duration_ms
        self.nodes = [AxisNode(0, 0.0), AxisNode(int(d * 0.18), 38.0), AxisNode(int(d * 0.42), -24.0), AxisNode(int(d * 0.70), 46.0), AxisNode(d, 0.0)]
        self._invalidate_cache()

    def clamp_y(self, value: float) -> float:
        limit = self.config.y_limit
        return max(-limit, min(limit, float(value)))

    def snap_time(self, value_ms: float) -> int:
        step = self.sample_ms
        return int(round(float(value_ms) / step) * step)

    def sort_and_fix_nodes(self) -> None:
        self.nodes.sort(key=lambda n: n.time_ms)
        if not self.nodes:
            self.nodes = [AxisNode(0, 0.0), AxisNode(self.take_duration_ms, 0.0)]
            return
        self.nodes[0].time_ms = 0
        self.nodes[0].y = 0.0
        self.nodes[-1].time_ms = self.take_duration_ms
        self.nodes[-1].y = 0.0
        min_gap = self.config.min_node_gap_ms
        for i in range(1, len(self.nodes) - 1):
            left = self.nodes[i - 1].time_ms + min_gap
            right = self.nodes[i + 1].time_ms - min_gap if i + 1 < len(self.nodes) else self.take_duration_ms
            self.nodes[i].time_ms = self.snap_time(self.nodes[i].time_ms)
            self.nodes[i].time_ms = max(left, min(right, self.nodes[i].time_ms))
            self.nodes[i].y = self.clamp_y(self.nodes[i].y)

    def add_node(self, time_ms: int, y: float) -> None:
        self.nodes.append(AxisNode(self.snap_time(time_ms), self.clamp_y(y)))
        self.sort_and_fix_nodes()
        self._invalidate_cache()

    def remove_node(self, index: int) -> None:
        if index <= 0 or index >= len(self.nodes) - 1:
            return
        del self.nodes[index]
        self.sort_and_fix_nodes()
        self._invalidate_cache()

    def move_node(self, index: int, time_ms: int | None = None, y: float | None = None) -> bool:
        if index < 0 or index >= len(self.nodes):
            return False
        node = self.nodes[index]
        old_time = int(node.time_ms)
        old_y = float(node.y)
        if time_ms is not None:
            node.time_ms = self.snap_time(time_ms)
        if y is not None:
            node.y = self.clamp_y(y)
        if index == 0 or index == len(self.nodes) - 1:
            node.y = 0.0
        changed = (node.time_ms != old_time) or (abs(node.y - old_y) > 1e-9)
        if not changed:
            return False
        self.sort_and_fix_nodes()
        changed_after = (self.nodes[index].time_ms != old_time) or (abs(self.nodes[index].y - old_y) > 1e-9)
        if not changed_after:
            return False
        self._invalidate_cache()
        return True

    def shift_all(self, delta_ms: int) -> bool:
        if len(self.nodes) <= 2:
            return False
        delta_ms = self.snap_time(delta_ms)
        if delta_ms == 0:
            return False
        inner = copy.deepcopy(self.nodes[1:-1])
        for n in inner:
            n.time_ms += delta_ms
        left_limit = self.config.min_node_gap_ms
        right_limit = self.take_duration_ms - self.config.min_node_gap_ms
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
        old_state = tuple((n.time_ms, n.y) for n in self.nodes)
        self.nodes = [self.nodes[0]] + inner + [self.nodes[-1]]
        self.sort_and_fix_nodes()
        new_state = tuple((n.time_ms, n.y) for n in self.nodes)
        if new_state == old_state:
            return False
        self._invalidate_cache()
        return True

    def smooth_all(self, strength: float = 0.45, passes: int = 1) -> None:
        if len(self.nodes) <= 2:
            return
        strength = max(0.0, min(1.0, float(strength)))
        passes = max(1, int(passes))
        ys = [node.y for node in self.nodes]
        for _ in range(passes):
            new_ys = ys[:]
            for i in range(1, len(ys) - 1):
                neighbor_avg = (ys[i - 1] + ys[i + 1]) * 0.5
                new_ys[i] = ys[i] * (1.0 - strength) + neighbor_avg * strength
            ys = new_ys
        for i in range(1, len(self.nodes) - 1):
            self.nodes[i].y = self.clamp_y(ys[i])
        self.sort_and_fix_nodes()
        self._invalidate_cache()

    def set_release_time(self, time_ms: int) -> bool:
        if not self.is_release_axis:
            return False
        new_time = self.snap_time(max(0, min(self.take_duration_ms, int(time_ms))))
        if self.release_time_ms == new_time:
            return False
        self.release_time_ms = new_time
        return True

    def protocol_rows(self, duration_ms: int | None = None) -> List[dict]:
        rows = self.build_step_rows(duration_ms=duration_ms)
        release_time = self.release_time_ms if self.is_release_axis else None
        return [{
            "time_ms": int(row["time_ms"]),
            "dir": int(row["dir"]),
            "step": int(row["step"]),
            "event": "RELEASE" if release_time is not None and int(row["time_ms"]) == int(release_time) else "",
        } for row in rows]

    def _edge_slope(self, h0: float, h1: float, d0: float, d1: float) -> float:
        m = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1) if (h0 + h1) != 0 else 0.0
        if (m > 0) != (d0 > 0):
            return 0.0
        if (d0 > 0) != (d1 > 0) and abs(m) > abs(3 * d0):
            return 3 * d0
        return m

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

    def sample_curve(self, steps: int = 800, duration_ms: int | None = None) -> List[tuple[int, float]]:
        self.sort_and_fix_nodes()
        duration = max(self.sample_ms, int(duration_ms or self.take_duration_ms))
        cache_key = (steps, duration)
        if cache_key in self._curve_cache:
            return list(self._curve_cache[cache_key])

        xs = [float(node.time_ms) for node in self.nodes]
        ys = [float(node.y) for node in self.nodes]
        if len(xs) < 2:
            return []
        if duration != self.take_duration_ms and self.take_duration_ms > 0:
            scale = duration / float(self.take_duration_ms)
            xs = [x * scale for x in xs]
        m = self._pchip_slopes(xs, ys)
        dense = max(steps, 120)
        result: List[tuple[int, float]] = []
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
        self._curve_cache[cache_key] = tuple(result)
        return list(self._curve_cache[cache_key])

    def _zone_gain(self, normalized: float, tuning: StepTuning) -> float:
        if normalized <= 1 / 3:
            return tuning.low_zone_gain
        if normalized <= 2 / 3:
            return tuning.mid_zone_gain
        return tuning.high_zone_gain

    def build_step_rows(self, duration_ms: int | None = None) -> List[dict]:
        duration = max(self.sample_ms, int(duration_ms or self.take_duration_ms))
        if duration in self._step_cache:
            return [dict(r) for r in self._step_cache[duration]]
        rows: List[dict] = []
        sample_ms = self.sample_ms
        steps = duration // sample_ms
        if self.is_release_axis:
            for i in range(steps + 1):
                rows.append({"time_ms": i * sample_ms, "y": 0.0, "dir": 1, "step": 0, "count": 0, "rate": 0.0, "acc": 0.0})
            self._step_cache[duration] = tuple(dict(r) for r in rows)
            return [dict(r) for r in self._step_cache[duration]]

        tuning = copy.deepcopy(self.step_tuning)
        tuning.clamp()
        accumulator = tuning.accumulator_bias
        count = 0
        prev_sign = 0
        prev_rate = 0.0
        samples = self.sample_curve(800, duration_ms=duration)
        if not samples:
            return []
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
            sign = 1 if y > 1e-9 else -1 if y < -1e-9 else 0
            if sign != 0:
                prev_sign = sign
            dir_bit = 1 if prev_sign >= 0 else 0
            abs_y = abs(y)
            if abs_y <= tuning.dead_zone_y:
                rate = 0.0
            else:
                span = max(1e-6, tuning.input_max_y - tuning.dead_zone_y)
                normalized = (min(abs_y, tuning.input_max_y) - tuning.dead_zone_y) / span
                normalized = max(0.0, min(1.0, normalized))
                curve = (normalized ** tuning.input_gamma) * self._zone_gain(normalized, tuning)
                rate = curve * self.mechanics.max_step_rate_per_s
                rate *= tuning.step_rate_gain
                rate *= tuning.step_rate_max_percent / 100.0
            if tuning.preview_rate_smoothing > 0.0:
                alpha = max(0.0, min(0.95, tuning.preview_rate_smoothing))
                rate = prev_rate * alpha + rate * (1.0 - alpha)
            prev_rate = rate
            density = max(0.0, min(float(self.mechanics.max_step_per_sample), rate * (sample_ms / 1000.0)))
            accumulator += density
            step = 0
            if accumulator >= tuning.emit_threshold:
                step = 1
                accumulator -= tuning.emit_threshold
                count += 1
            rows.append({"time_ms": t, "y": y, "dir": dir_bit, "step": step, "count": count, "rate": rate, "acc": accumulator})
        self._step_cache[duration] = tuple(dict(r) for r in rows)
        return [dict(r) for r in self._step_cache[duration]]

    def current_pulse_count(self, duration_ms: int | None = None) -> int:
        rows = self.build_step_rows(duration_ms=duration_ms)
        return int(rows[-1]["count"]) if rows else 0

    def metrics_summary(self, duration_ms: int | None = None) -> str:
        rows = self.build_step_rows(duration_ms=duration_ms)
        pulse_count = int(rows[-1]["count"]) if rows else 0
        budget = self.mechanics.full_cycle_pulses
        ratio = (pulse_count / budget) if budget else 0.0
        peak_abs_y = max((abs(r["y"]) for r in rows), default=0.0)
        peak_rate = max((r["rate"] for r in rows), default=0.0)
        release_text = f"{self.release_time_ms} ms" if self.is_release_axis and self.release_time_ms is not None else "-"
        summary_duration = max(self.sample_ms, int(duration_ms or self.take_duration_ms))
        return (
            f"oś               : {self.axis_def.axis_name}\n"
            f"węzły             : {len(self.nodes)}\n"
            f"release          : {release_text}\n"
            f"budżet impulsów   : {pulse_count} / {budget}\n"
            f"wypełnienie       : {ratio * 100:6.2f} %\n"
            f"max |Y|           : {peak_abs_y:6.2f}\n"
            f"max rate          : {peak_rate:6.2f} step/s\n"
            f"sample            : {self.sample_ms} ms\n"
            f"zakres operatora  : ±{int(round(self.sandbox.display_y_scale))}\n"
            f"czas MAIN TAKE    : {summary_duration / 1000.0:6.1f} s\n"
            f"pełny cykl min    : {self.mechanics.min_full_cycle_time_s:6.1f} s\n"
            f"settle+ramp       : {(self.mechanics.start_settle_ms + self.mechanics.start_ramp_ms) / 1000.0:6.1f} s\n"
        )


DEFAULT_AXIS_DEFINITIONS: list[EhrAxisDefinition] = [
    EhrAxisDefinition("cam_h", "oś pozioma kamery", "#78DCE8"),
    EhrAxisDefinition("cam_v", "oś pionowa kamery", "#FFD866"),
    EhrAxisDefinition("cam_t", "oś pochyłu kamery", "#FF6188"),
    EhrAxisDefinition("cam_f", "oś ostrości kamery", "#A9DC76"),
    EhrAxisDefinition("arm_v", "oś pionowa ramienia", "#AB9DF2"),
    EhrAxisDefinition("arm_h", "oś pozioma ramienia", "#FC9867"),
    EhrAxisDefinition("dron", "DRON", "#F472B6"),
]
