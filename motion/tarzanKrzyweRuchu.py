from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline

from core.tarzanUstawienia import GESTOSC_INTERPOLACJI
from motion.tarzanTakeModel import TarzanAxisTake


class TarzanKrzyweRuchu:
    """
    Gładki silnik krzywych ruchu TARZANA.
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