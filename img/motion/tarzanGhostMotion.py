from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.tarzanUstawienia import GESTOSC_INTERPOLACJI
from motion.tarzanKrzyweRuchu import TarzanKrzyweRuchu
from motion.tarzanTakeModel import TarzanAxisTake


@dataclass
class TarzanGhostComparison:
    axis_name: str
    sample_count: int
    original_area: float
    edited_area: float
    area_delta: float
    area_delta_percent: float
    original_peak: float
    edited_peak: float
    peak_delta: float
    original_zero_crossings: int
    edited_zero_crossings: int
    original_times: np.ndarray
    original_amplitudes: np.ndarray
    edited_times: np.ndarray
    edited_amplitudes: np.ndarray


class TarzanGhostMotion:
    """
    Porównanie ghost ruchu:
    - oryginalna krzywa
    - edytowana krzywa
    """

    def __init__(self) -> None:
        self.krzywe = TarzanKrzyweRuchu()

    def compare_axes(
        self,
        original_axis: TarzanAxisTake,
        edited_axis: TarzanAxisTake,
        sample_count: int = GESTOSC_INTERPOLACJI,
    ) -> TarzanGhostComparison:
        original_times, original_amplitudes = self.krzywe.build_curve_samples(
            axis=original_axis,
            sample_count=sample_count,
        )
        edited_times, edited_amplitudes = self.krzywe.build_curve_samples(
            axis=edited_axis,
            sample_count=sample_count,
        )

        original_area = float(np.trapezoid(np.abs(original_amplitudes), original_times))
        edited_area = float(np.trapezoid(np.abs(edited_amplitudes), edited_times))

        area_delta = edited_area - original_area
        area_delta_percent = 0.0
        if abs(original_area) > 1e-9:
            area_delta_percent = (area_delta / original_area) * 100.0

        original_peak = float(np.max(np.abs(original_amplitudes)))
        edited_peak = float(np.max(np.abs(edited_amplitudes)))
        peak_delta = edited_peak - original_peak

        original_zero_crossings = self._count_zero_crossings(original_amplitudes)
        edited_zero_crossings = self._count_zero_crossings(edited_amplitudes)

        return TarzanGhostComparison(
            axis_name=original_axis.axis_name,
            sample_count=sample_count,
            original_area=original_area,
            edited_area=edited_area,
            area_delta=area_delta,
            area_delta_percent=area_delta_percent,
            original_peak=original_peak,
            edited_peak=edited_peak,
            peak_delta=peak_delta,
            original_zero_crossings=original_zero_crossings,
            edited_zero_crossings=edited_zero_crossings,
            original_times=original_times,
            original_amplitudes=original_amplitudes,
            edited_times=edited_times,
            edited_amplitudes=edited_amplitudes,
        )

    def _count_zero_crossings(self, amplitudes: np.ndarray) -> int:
        if len(amplitudes) < 2:
            return 0

        signs = np.sign(amplitudes)
        count = 0

        for index in range(1, len(signs)):
            left = signs[index - 1]
            right = signs[index]

            if left == 0 or right == 0:
                continue

            if left != right:
                count += 1

        return count