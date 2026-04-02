from __future__ import annotations

from copy import deepcopy

import numpy as np
from scipy.interpolate import CubicSpline

from core.tarzanUstawienia import GESTOSC_INTERPOLACJI
from motion.tarzanTakeModel import TarzanAxisTake


class TarzanKrzyweRuchu:
    """
    Silnik krzywych ruchu TARZANA.

    Ta wersja obsługuje:
    - budowę gładkiej krzywej ruchu,
    - gradient,
    - przyspieszenie,
    - edycję amplitudy fragmentu,
    - przesunięcie fragmentu w czasie,
    - wygładzanie fragmentu,
    - zachowanie drogi ruchu w obrębie edytowanego przedziału.
    """

    def build_curve_samples(
        self,
        axis: TarzanAxisTake,
        sample_count: int = GESTOSC_INTERPOLACJI,
    ) -> tuple[np.ndarray, np.ndarray]:
        spline, dense_times = self._build_spline(axis, sample_count)
        dense_amplitudes = spline(dense_times)
        return dense_times, dense_amplitudes

    def build_gradient_samples(
        self,
        axis: TarzanAxisTake,
        sample_count: int = GESTOSC_INTERPOLACJI,
    ) -> tuple[np.ndarray, np.ndarray]:
        spline, dense_times = self._build_spline(axis, sample_count)
        gradients = spline.derivative(1)(dense_times)
        return dense_times, gradients

    def build_acceleration_samples(
        self,
        axis: TarzanAxisTake,
        sample_count: int = GESTOSC_INTERPOLACJI,
    ) -> tuple[np.ndarray, np.ndarray]:
        spline, dense_times = self._build_spline(axis, sample_count)
        accelerations = spline.derivative(2)(dense_times)
        return dense_times, accelerations

    def get_control_points(
        self,
        axis: TarzanAxisTake,
    ) -> tuple[np.ndarray, np.ndarray]:
        return self._extract_control_points(axis)

    def clone_axis(self, axis: TarzanAxisTake) -> TarzanAxisTake:
        """
        Tworzy kopię osi do bezpiecznej edycji.
        """
        return deepcopy(axis)

    def apply_amplitude_scale_on_interval(
        self,
        axis: TarzanAxisTake,
        start_time_ms: int,
        end_time_ms: int,
        scale: float,
        normalize_distance: bool = True,
    ) -> TarzanAxisTake:
        """
        Skaluje amplitudę punktów kontrolnych w zadanym przedziale czasu.

        scale > 1.0  -> większa intensywność ruchu
        scale < 1.0  -> mniejsza intensywność ruchu
        """
        edited_axis = self.clone_axis(axis)

        original_area = self.compute_interval_area(
            edited_axis,
            start_time_ms,
            end_time_ms,
        )

        for point in edited_axis.curve.control_points:
            if start_time_ms <= point.time <= end_time_ms:
                point.amplitude *= scale

        if normalize_distance:
            self.normalize_interval_area(
                edited_axis,
                start_time_ms,
                end_time_ms,
                target_area=original_area,
            )

        return edited_axis

    def shift_interval_in_time(
        self,
        axis: TarzanAxisTake,
        start_time_ms: int,
        end_time_ms: int,
        shift_ms: int,
    ) -> TarzanAxisTake:
        """
        Przesuwa punkty kontrolne w zadanym przedziale czasu.

        shift_ms > 0  -> później
        shift_ms < 0  -> wcześniej
        """
        edited_axis = self.clone_axis(axis)

        if not edited_axis.curve.control_points:
            return edited_axis

        min_time = min(point.time for point in edited_axis.curve.control_points)
        max_time = max(point.time for point in edited_axis.curve.control_points)

        for point in edited_axis.curve.control_points:
            if start_time_ms <= point.time <= end_time_ms:
                point.time += shift_ms
                point.time = max(min_time, min(point.time, max_time))

        self._sort_and_fix_duplicate_times(edited_axis)

        if edited_axis.start_must_be_zero and edited_axis.curve.control_points:
            edited_axis.curve.control_points[0].time = min_time

        if edited_axis.end_must_be_zero and edited_axis.curve.control_points:
            edited_axis.curve.control_points[-1].time = max_time

        return edited_axis

    def smooth_interval(
        self,
        axis: TarzanAxisTake,
        start_time_ms: int,
        end_time_ms: int,
        strength: float = 0.35,
        normalize_distance: bool = True,
    ) -> TarzanAxisTake:
        """
        Wygładza amplitudy punktów kontrolnych w zadanym przedziale.

        strength:
        0.0 -> brak wpływu
        1.0 -> bardzo mocne wygładzenie
        """
        edited_axis = self.clone_axis(axis)

        original_area = self.compute_interval_area(
            edited_axis,
            start_time_ms,
            end_time_ms,
        )

        points = edited_axis.curve.control_points
        if len(points) < 3:
            return edited_axis

        original_amplitudes = [point.amplitude for point in points]

        for index in range(1, len(points) - 1):
            point = points[index]
            if not (start_time_ms <= point.time <= end_time_ms):
                continue

            left = original_amplitudes[index - 1]
            center = original_amplitudes[index]
            right = original_amplitudes[index + 1]

            average = (left + center + right) / 3.0
            point.amplitude = (1.0 - strength) * center + strength * average

        if normalize_distance:
            self.normalize_interval_area(
                edited_axis,
                start_time_ms,
                end_time_ms,
                target_area=original_area,
            )

        return edited_axis

    def normalize_interval_area(
        self,
        axis: TarzanAxisTake,
        start_time_ms: int,
        end_time_ms: int,
        target_area: float,
        sample_count: int = GESTOSC_INTERPOLACJI,
    ) -> TarzanAxisTake:
        """
        Zachowuje drogę ruchu przez wyrównanie pola pod |A(t)|
        w zadanym przedziale czasu.
        """
        current_area = self.compute_interval_area(
            axis,
            start_time_ms,
            end_time_ms,
            sample_count=sample_count,
        )

        if current_area <= 1e-9:
            return axis

        if target_area <= 1e-9:
            return axis

        scale = target_area / current_area

        for point in axis.curve.control_points:
            if start_time_ms <= point.time <= end_time_ms:
                point.amplitude *= scale

        return axis

    def compute_interval_area(
        self,
        axis: TarzanAxisTake,
        start_time_ms: int,
        end_time_ms: int,
        sample_count: int = GESTOSC_INTERPOLACJI,
    ) -> float:
        """
        Liczy pole pod |A(t)| w zadanym przedziale czasu.
        """
        dense_times, dense_amplitudes = self.build_curve_samples(
            axis=axis,
            sample_count=sample_count,
        )

        mask = (dense_times >= start_time_ms) & (dense_times <= end_time_ms)
        interval_times = dense_times[mask]
        interval_amplitudes = dense_amplitudes[mask]

        if len(interval_times) < 2:
            return 0.0

        return float(np.trapezoid(np.abs(interval_amplitudes), interval_times))

    def _build_spline(
        self,
        axis: TarzanAxisTake,
        sample_count: int,
    ) -> tuple[CubicSpline, np.ndarray]:
        times, amplitudes = self._extract_control_points(axis)

        if len(times) < 2:
            raise ValueError(
                f"{axis.axis_name}: za mało punktów kontrolnych do interpolacji"
            )

        spline = CubicSpline(
            times,
            amplitudes,
            bc_type=((1, 0.0), (1, 0.0)),
        )

        dense_times = np.linspace(times.min(), times.max(), sample_count)
        return spline, dense_times

    def _extract_control_points(
        self,
        axis: TarzanAxisTake,
    ) -> tuple[np.ndarray, np.ndarray]:
        if not axis.curve.control_points:
            raise ValueError(f"{axis.axis_name}: brak punktów kontrolnych")

        times = np.array(
            [point.time for point in axis.curve.control_points],
            dtype=float,
        )
        amplitudes = np.array(
            [point.amplitude for point in axis.curve.control_points],
            dtype=float,
        )

        self._validate_points(axis.axis_name, times)

        return times, amplitudes

    def _validate_points(
        self,
        axis_name: str,
        times: np.ndarray,
    ) -> None:
        if len(times) == 0:
            raise ValueError(f"{axis_name}: brak punktów czasu")

        if len(times) != len(np.unique(times)):
            raise ValueError(
                f"{axis_name}: punkty kontrolne mają powtarzające się wartości czasu"
            )

        if np.any(np.diff(times) <= 0):
            raise ValueError(
                f"{axis_name}: czasy punktów kontrolnych muszą być rosnące"
            )

    def _sort_and_fix_duplicate_times(
        self,
        axis: TarzanAxisTake,
    ) -> None:
        """
        Sortuje punkty po czasie i delikatnie rozsuwa ewentualne duplikaty.
        """
        points = axis.curve.control_points
        points.sort(key=lambda point: point.time)

        for index in range(1, len(points)):
            if points[index].time <= points[index - 1].time:
                points[index].time = points[index - 1].time + 1