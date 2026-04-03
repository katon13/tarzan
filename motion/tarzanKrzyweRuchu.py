
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import numpy as np
from scipy.interpolate import PchipInterpolator


@dataclass
class TarzanMechanicalProfile:
    start_settle_ms: int
    start_ramp_ms: int
    start_total_ms: int
    max_normalized_slope_per_ms: float


@dataclass
class TarzanNode:
    """
    Węzeł jednej ciągłej linii ruchu osi.
    """
    time_ms: int
    value: float


@dataclass
class TarzanMotionLine:
    """
    Jedna ciągła linia ruchu osi z wieloma punktami przełomu.
    """
    nodes: list[TarzanNode]


class TarzanKrzyweRuchu:
    """
    Model ruchu TARZAN:
    - jedna oś = jedna ciągła linia
    - linia może mieć wiele punktów przełomu
    - operator edytuje węzły tej jednej linii
    - wynik eksportowany jest do control_points osi TAKE
    """

    TIME_STEP_MS = 10
    MIN_NODE_GAP_MS = 20
    VALUE_LIMIT = 1.0
    SAMPLE_COUNT = 800
    AREA_TOLERANCE = 0.01

    def snap_time(self, value: float | int) -> int:
        return int(round(float(value) / self.TIME_STEP_MS) * self.TIME_STEP_MS)

    def clamp_value(self, value: float, limit: float | None = None) -> float:
        limit = self.VALUE_LIMIT if limit is None else abs(limit)
        return max(-limit, min(limit, float(value)))

    def get_axis_start_stop(self, axis) -> tuple[int, int]:
        points = axis.curve.control_points
        if len(points) < 2:
            raise ValueError(f"{axis.axis_name}: za mało punktów kontrolnych")
        return int(points[0].time), int(points[-1].time)

    def sanitize_start_stop(self, axis, start_ms: int, stop_ms: int) -> tuple[int, int]:
        start_ms = self.snap_time(start_ms)
        stop_ms = self.snap_time(stop_ms)
        if stop_ms <= start_ms:
            stop_ms = start_ms + self.TIME_STEP_MS
        return start_ms, stop_ms

    def _axis_value_limit(self, axis=None) -> float:
        return self.VALUE_LIMIT


    def _axis_name_key(self, axis=None) -> str:
        if axis is None:
            return ""
        return str(getattr(axis, "axis_name", "")).strip().lower()

    def _get_mechanical_profile(self, axis=None) -> TarzanMechanicalProfile:
        """
        Profil mechaniczny osi oparty na dokumentacji TARZAN:
        - START_SETTLE
        - START_RAMP
        - CRUISE

        Wartości czasów odpowiadają publicznej definicji mechaniki osi
        z pliku mechanics/tarzanMechanikaOsi.py.
        """
        axis_name = self._axis_name_key(axis)

        profile_map: dict[str, tuple[int, int]] = {
            "oś pozioma kamery": (300, 900),
            "oś pionowa kamery": (300, 900),
            "oś pochyłu kamery": (250, 750),
            "oś ostrości kamery": (200, 500),
            "oś pionowa ramienia": (500, 1000),
            "oś pozioma ramienia": (600, 1200),
        }

        settle_ms, ramp_ms = profile_map.get(axis_name, (400, 800))
        start_total_ms = max(self.TIME_STEP_MS, settle_ms + ramp_ms)

        # Znormalizowany limit nachylenia:
        # wartość 1.0 nie może zostać osiągnięta szybciej niż całkowity czas rozruchu.
        max_normalized_slope_per_ms = 1.0 / float(start_total_ms)

        return TarzanMechanicalProfile(
            start_settle_ms=settle_ms,
            start_ramp_ms=ramp_ms,
            start_total_ms=start_total_ms,
            max_normalized_slope_per_ms=max_normalized_slope_per_ms,
        )

    def _apply_mechanical_time_windows(self, line: TarzanMotionLine, axis=None) -> None:
        if len(line.nodes) < 3:
            return

        profile = self._get_mechanical_profile(axis)
        start_ms = line.nodes[0].time_ms
        stop_ms = line.nodes[-1].time_ms

        if stop_ms <= start_ms:
            return

        first_allowed = start_ms + profile.start_total_ms
        last_allowed = stop_ms - profile.start_total_ms

        if len(line.nodes) >= 3:
            line.nodes[1].time_ms = max(line.nodes[1].time_ms, first_allowed)

        if len(line.nodes) >= 4:
            line.nodes[-2].time_ms = min(line.nodes[-2].time_ms, last_allowed)

        # Jeżeli przebieg jest krótszy niż suma ramp, rozkładamy węzły proporcjonalnie
        if first_allowed >= last_allowed and len(line.nodes) > 2:
            usable = max(self.TIME_STEP_MS, stop_ms - start_ms)
            step = max(self.MIN_NODE_GAP_MS, usable // max(1, len(line.nodes) - 1))
            for index, node in enumerate(line.nodes[1:-1], start=1):
                node.time_ms = start_ms + index * step

    def _apply_mechanical_slope_limits(self, line: TarzanMotionLine, axis=None) -> None:
        if len(line.nodes) < 2:
            return

        profile = self._get_mechanical_profile(axis)
        slope = profile.max_normalized_slope_per_ms

        # Przód -> tył
        for index in range(1, len(line.nodes)):
            left = line.nodes[index - 1]
            right = line.nodes[index]
            dt = max(self.TIME_STEP_MS, right.time_ms - left.time_ms)
            max_dv = slope * dt
            lower = left.value - max_dv
            upper = left.value + max_dv
            right.value = max(lower, min(right.value, upper))

        # Tył -> przód
        for index in range(len(line.nodes) - 2, -1, -1):
            right = line.nodes[index + 1]
            left = line.nodes[index]
            dt = max(self.TIME_STEP_MS, right.time_ms - left.time_ms)
            max_dv = slope * dt
            lower = right.value - max_dv
            upper = right.value + max_dv
            left.value = max(lower, min(left.value, upper))

        line.nodes[0].value = 0.0
        line.nodes[-1].value = 0.0


    def build_from_axis(self, axis) -> TarzanMotionLine:
        points = getattr(axis.curve, "control_points", [])
        if len(points) < 2:
            raise ValueError(f"{axis.axis_name}: za mało punktów do budowy linii")

        nodes = []
        limit = self._axis_value_limit(axis)

        for index, point in enumerate(points):
            value = 0.0 if index == 0 or index == len(points) - 1 else float(point.amplitude)
            nodes.append(
                TarzanNode(
                    time_ms=self.snap_time(point.time),
                    value=self.clamp_value(value, limit),
                )
            )

        line = TarzanMotionLine(nodes=nodes)
        self.normalize_line(line, axis)
        return line

    def export_to_axis(self, axis, line: TarzanMotionLine):
        sampled = self.sample_line(line)

        new_axis = deepcopy(axis)
        cp_cls = type(axis.curve.control_points[0]) if axis.curve.control_points else None
        if cp_cls is None:
            raise ValueError(f"{axis.axis_name}: brak klasy control_point")

        new_axis.curve.control_points = [
            cp_cls(time=int(time_ms), amplitude=float(value))
            for time_ms, value in sampled
        ]
        self.enforce_axis_constraints(new_axis)
        return new_axis

    def sample_line(self, line: TarzanMotionLine, sample_count: int | None = None) -> list[tuple[int, float]]:
        sample_count = max(40, sample_count or self.SAMPLE_COUNT)

        times = np.array([node.time_ms for node in line.nodes], dtype=float)
        values = np.array([node.value for node in line.nodes], dtype=float)

        if len(times) < 2:
            return []

        dense_times = np.linspace(times[0], times[-1], sample_count)

        if len(times) == 2:
            dense_values = np.interp(dense_times, times, values)
        else:
            # Lokalny renderer shape-preserving:
            # spokojniejszy dla operatora niż globalny spline,
            # ale bez utraty logiki rozszerzania osi czasu.
            spline = PchipInterpolator(times, values, extrapolate=False)
            dense_values = spline(dense_times)

        dense_values = np.nan_to_num(
            dense_values,
            nan=0.0,
            posinf=self.VALUE_LIMIT,
            neginf=-self.VALUE_LIMIT,
        )
        dense_values = np.clip(dense_values, -self.VALUE_LIMIT, self.VALUE_LIMIT)

        dedup: dict[int, float] = {}
        for x, y in zip(dense_times, dense_values):
            dedup[self.snap_time(x)] = float(y)

        ordered = sorted(dedup.items(), key=lambda item: item[0])

        if ordered:
            ordered[0] = (line.nodes[0].time_ms, 0.0)
            ordered[-1] = (line.nodes[-1].time_ms, 0.0)

        return ordered

    def build_curve_samples(self, axis, sample_count: int = 600) -> tuple[np.ndarray, np.ndarray]:
        line = self.build_from_axis(axis)
        sampled = self.sample_line(line, sample_count=sample_count)
        xs = np.array([x for x, _ in sampled], dtype=float)
        ys = np.array([y for _, y in sampled], dtype=float)
        return xs, ys

    def compute_area(self, line: TarzanMotionLine, sample_count: int | None = None) -> float:
        sampled = self.sample_line(line, sample_count=sample_count)
        if len(sampled) < 2:
            return 0.0
        xs = np.array([x for x, _ in sampled], dtype=float)
        ys = np.array([abs(y) for _, y in sampled], dtype=float)
        return float(np.trapezoid(ys, xs))

    def compute_interval_area(self, axis, start_time_ms: int, end_time_ms: int, sample_count: int = 600) -> float:
        xs, ys = self.build_curve_samples(axis, sample_count=sample_count)
        mask = (xs >= start_time_ms) & (xs <= end_time_ms)
        if mask.sum() < 2:
            return 0.0
        return float(np.trapezoid(np.abs(ys[mask]), xs[mask]))

    def add_node(self, line: TarzanMotionLine, time_ms: int, value: float, axis=None) -> TarzanMotionLine:
        edited = deepcopy(line)
        time_ms = self.snap_time(time_ms)
        value = self.clamp_value(value, self._axis_value_limit(axis))

        insert_index = 0
        while insert_index < len(edited.nodes) and edited.nodes[insert_index].time_ms < time_ms:
            insert_index += 1

        if insert_index == 0:
            insert_index = 1
        if insert_index >= len(edited.nodes):
            insert_index = len(edited.nodes) - 1

        left = edited.nodes[insert_index - 1]
        right = edited.nodes[insert_index]

        time_ms = max(left.time_ms + self.MIN_NODE_GAP_MS, time_ms)
        time_ms = min(right.time_ms - self.MIN_NODE_GAP_MS, time_ms)

        edited.nodes.insert(insert_index, TarzanNode(time_ms=time_ms, value=value))
        self.normalize_line(edited, axis)
        return edited

    def remove_node(self, line: TarzanMotionLine, index: int, axis=None) -> TarzanMotionLine:
        edited = deepcopy(line)
        if index <= 0 or index >= len(edited.nodes) - 1:
            return edited
        if len(edited.nodes) <= 2:
            return edited
        del edited.nodes[index]
        self.normalize_line(edited, axis)
        return edited

    def move_node(
        self,
        line: TarzanMotionLine,
        index: int,
        new_time_ms: int | None = None,
        new_value: float | None = None,
        axis=None,
        preserve_area: bool = False,
    ) -> TarzanMotionLine:
        edited = deepcopy(line)
        if index < 0 or index >= len(edited.nodes):
            return edited

        target_area = self.compute_area(line) if preserve_area else None
        node = edited.nodes[index]

        if new_time_ms is not None:
            snapped = self.snap_time(new_time_ms)
            if index == 0:
                node.time_ms = snapped
            elif index == len(edited.nodes) - 1:
                node.time_ms = snapped
            else:
                left_limit = edited.nodes[index - 1].time_ms + self.MIN_NODE_GAP_MS
                right_limit = edited.nodes[index + 1].time_ms - self.MIN_NODE_GAP_MS
                node.time_ms = max(left_limit, min(snapped, right_limit))

        if new_value is not None:
            node.value = 0.0 if index == 0 or index == len(edited.nodes) - 1 else self.clamp_value(new_value, self._axis_value_limit(axis))

        self.normalize_line(edited, axis)

        if preserve_area and target_area is not None:
            edited = self._fit_duration_to_target_area(edited, target_area, axis)

        return edited

    def shift_line_in_time(self, line: TarzanMotionLine, delta_ms: int, axis=None) -> TarzanMotionLine:
        edited = deepcopy(line)
        delta_ms = self.snap_time(delta_ms)
        for node in edited.nodes:
            node.time_ms = self.snap_time(node.time_ms + delta_ms)
        self.normalize_line(edited, axis)
        return edited

    def set_line_start_stop(self, line: TarzanMotionLine, new_start_ms: int, new_stop_ms: int, axis=None, preserve_distance: bool = True) -> TarzanMotionLine:
        edited = deepcopy(line)

        old_start = edited.nodes[0].time_ms
        old_stop = edited.nodes[-1].time_ms
        old_duration = max(self.TIME_STEP_MS, old_stop - old_start)
        old_area = self.compute_area(edited)

        new_start_ms = self.snap_time(new_start_ms)
        new_stop_ms = self.snap_time(new_stop_ms)
        if new_stop_ms <= new_start_ms:
            new_stop_ms = new_start_ms + self.TIME_STEP_MS

        new_duration = max(self.TIME_STEP_MS, new_stop_ms - new_start_ms)
        time_scale = new_duration / old_duration
        value_scale = old_duration / new_duration if preserve_distance else 1.0
        limit = self._axis_value_limit(axis)

        for index, node in enumerate(edited.nodes):
            rel = node.time_ms - old_start
            node.time_ms = self.snap_time(new_start_ms + rel * time_scale)
            if index != 0 and index != len(edited.nodes) - 1:
                node.value = self.clamp_value(node.value * value_scale, limit)

        edited.nodes[0].time_ms = new_start_ms
        edited.nodes[-1].time_ms = new_stop_ms
        edited.nodes[0].value = 0.0
        edited.nodes[-1].value = 0.0

        self.normalize_line(edited, axis)

        if preserve_distance and old_area > 1e-9:
            edited = self.scale_line_to_area(edited, old_area, axis)

        return edited

    def set_axis_start_stop(self, axis, new_start_ms: int, new_stop_ms: int, preserve_distance: bool = True):
        line = self.build_from_axis(axis)
        edited = self.set_line_start_stop(line, new_start_ms, new_stop_ms, axis=axis, preserve_distance=preserve_distance)
        return self.export_to_axis(axis, edited)


    def _fit_duration_to_target_area(self, line: TarzanMotionLine, target_area: float, axis=None) -> TarzanMotionLine:
        """
        Zachowuje logikę TARZAN:
        zmiana wysokości punktów ma zmieniać długość całej osi czasu.
        START zostaje zakotwiczony, a STOP oraz węzły pośrednie skalują się w czasie.
        """
        edited = deepcopy(line)
        if len(edited.nodes) < 2:
            return edited

        start_ms = edited.nodes[0].time_ms
        best = deepcopy(edited)
        best_error = abs(self.compute_area(best) - target_area)

        for _ in range(14):
            current_area = self.compute_area(edited)
            error = abs(current_area - target_area)
            if error < best_error:
                best = deepcopy(edited)
                best_error = error

            if current_area <= 1e-9 or target_area <= 1e-9:
                break

            ratio = target_area / current_area
            if abs(1.0 - ratio) < self.AREA_TOLERANCE:
                return deepcopy(edited)

            current_stop = edited.nodes[-1].time_ms
            current_duration = max(self.TIME_STEP_MS, current_stop - start_ms)
            new_duration = max(self.TIME_STEP_MS, self.snap_time(current_duration * ratio))
            if new_duration == current_duration:
                break

            for index, node in enumerate(edited.nodes):
                if index == 0:
                    node.time_ms = start_ms
                    continue
                rel = (node.time_ms - start_ms) / current_duration
                node.time_ms = self.snap_time(start_ms + rel * new_duration)

            self.normalize_line(edited, axis)

        return best

    def scale_line_to_area(self, line: TarzanMotionLine, target_area: float, axis=None) -> TarzanMotionLine:
        edited = deepcopy(line)
        best = deepcopy(edited)
        best_error = abs(self.compute_area(best) - target_area)
        limit = self._axis_value_limit(axis)

        for _ in range(12):
            current_area = self.compute_area(edited)
            error = abs(current_area - target_area)
            if error < best_error:
                best = deepcopy(edited)
                best_error = error

            if current_area <= 1e-9 or target_area <= 1e-9:
                break

            ratio = target_area / current_area
            if abs(1.0 - ratio) < self.AREA_TOLERANCE:
                return deepcopy(edited)

            for node in edited.nodes[1:-1]:
                node.value = self.clamp_value(node.value * ratio, limit)

            self.normalize_line(edited, axis)

        return best

    def preserve_full_curve_distance_anchor_start(self, axis, target_area: float) -> None:
        line = self.build_from_axis(axis)
        line = self.scale_line_to_area(line, target_area, axis)
        updated = self.export_to_axis(axis, line)
        axis.curve.control_points = updated.curve.control_points

    def smooth_line(self, line: TarzanMotionLine, strength: float = 0.35, preserve_distance: bool = True, axis=None) -> TarzanMotionLine:
        edited = deepcopy(line)
        target_area = self.compute_area(edited)
        strength = max(0.0, min(1.0, float(strength)))

        original_values = [node.value for node in edited.nodes]

        for index in range(1, len(edited.nodes) - 1):
            left = original_values[index - 1]
            center = original_values[index]
            right = original_values[index + 1]
            average = (left + center + right) / 3.0
            edited.nodes[index].value = (1.0 - strength) * center + strength * average

        self.normalize_line(edited, axis)

        if preserve_distance:
            edited = self.scale_line_to_area(edited, target_area, axis)

        return edited

    def smooth_interval(self, axis, start_time_ms: int, end_time_ms: int, strength: float = 0.35, preserve_distance: bool = True):
        line = self.build_from_axis(axis)
        target_area = self.compute_area(line)
        strength = max(0.0, min(1.0, float(strength)))

        original_values = [node.value for node in line.nodes]

        for index in range(1, len(line.nodes) - 1):
            node = line.nodes[index]
            if not (start_time_ms <= node.time_ms <= end_time_ms):
                continue

            left = original_values[index - 1]
            center = original_values[index]
            right = original_values[index + 1]
            average = (left + center + right) / 3.0
            node.value = (1.0 - strength) * center + strength * average

        self.normalize_line(line, axis)

        if preserve_distance:
            line = self.scale_line_to_area(line, target_area, axis)

        return self.export_to_axis(axis, line)

    def shift_axis_in_time(self, axis, delta_ms: int):
        line = self.build_from_axis(axis)
        shifted = self.shift_line_in_time(line, delta_ms, axis)
        return self.export_to_axis(axis, shifted)

    def normalize_line(self, line: TarzanMotionLine, axis=None) -> None:
        if len(line.nodes) < 2:
            return

        line.nodes.sort(key=lambda node: node.time_ms)
        limit = self._axis_value_limit(axis)

        for index, node in enumerate(line.nodes):
            node.time_ms = self.snap_time(node.time_ms)
            if index == 0 or index == len(line.nodes) - 1:
                node.value = 0.0
            else:
                node.value = self.clamp_value(node.value, limit)

        for index in range(1, len(line.nodes)):
            if line.nodes[index].time_ms <= line.nodes[index - 1].time_ms:
                line.nodes[index].time_ms = line.nodes[index - 1].time_ms + self.MIN_NODE_GAP_MS

        # Mechanika osi musi działać PRZED rysowaniem.
        # Dzięki temu wykres nie może tworzyć pionowych ścian
        # sprzecznych z logiką START_SETTLE / START_RAMP / CRUISE.
        self._apply_mechanical_time_windows(line, axis)

        line.nodes.sort(key=lambda node: node.time_ms)
        for index in range(1, len(line.nodes)):
            min_allowed = line.nodes[index - 1].time_ms + self.MIN_NODE_GAP_MS
            if line.nodes[index].time_ms < min_allowed:
                line.nodes[index].time_ms = min_allowed

        for index, node in enumerate(line.nodes):
            node.time_ms = self.snap_time(node.time_ms)
            if index == 0 or index == len(line.nodes) - 1:
                node.value = 0.0
            else:
                node.value = self.clamp_value(node.value, limit)

        self._apply_mechanical_slope_limits(line, axis)

        for index, node in enumerate(line.nodes):
            node.time_ms = self.snap_time(node.time_ms)
            if index == 0 or index == len(line.nodes) - 1:
                node.value = 0.0
            else:
                node.value = self.clamp_value(node.value, limit)

    def enforce_axis_constraints(self, axis) -> None:
        points = axis.curve.control_points
        if not points:
            return

        if getattr(axis, "start_must_be_zero", False):
            points[0].amplitude = 0.0
        if getattr(axis, "end_must_be_zero", False):
            points[-1].amplitude = 0.0

        limit = self._axis_value_limit(axis)
        for point in points:
            point.time = self.snap_time(point.time)
            point.amplitude = self.clamp_value(point.amplitude, limit)

        points.sort(key=lambda p: p.time)
        for index in range(1, len(points)):
            if points[index].time <= points[index - 1].time:
                points[index].time = points[index - 1].time + self.TIME_STEP_MS
