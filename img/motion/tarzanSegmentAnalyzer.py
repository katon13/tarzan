from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion.tarzanKrzyweRuchu import TarzanKrzyweRuchu
from motion.tarzanTakeModel import TarzanAxisTake, TarzanSegment


@dataclass
class TarzanSegmentProfile:
    segment_id: str
    start_time: int
    end_time: int
    direction: int
    pulse_count: int
    is_pause: bool
    times_ms: np.ndarray
    amplitude_samples: np.ndarray
    pulse_density: np.ndarray
    reconstructed_pulses: float


class TarzanSegmentAnalyzer:
    """
    Analizator segmentów ruchu TARZANA.
    """

    def __init__(self) -> None:
        self.krzywe = TarzanKrzyweRuchu()

    def build_axis_segment_profiles(
        self,
        axis: TarzanAxisTake,
        sample_count: int = 800,
    ) -> list[TarzanSegmentProfile]:
        dense_times, dense_amplitudes = self.krzywe.build_curve_samples(
            axis=axis,
            sample_count=sample_count,
        )

        profiles: list[TarzanSegmentProfile] = []

        for segment in axis.segments:
            profile = self._build_single_segment_profile(
                segment=segment,
                dense_times=dense_times,
                dense_amplitudes=dense_amplitudes,
            )
            profiles.append(profile)

        return profiles

    def _build_single_segment_profile(
        self,
        segment: TarzanSegment,
        dense_times: np.ndarray,
        dense_amplitudes: np.ndarray,
    ) -> TarzanSegmentProfile:
        mask = (dense_times >= segment.start_time) & (dense_times <= segment.end_time)

        seg_times = dense_times[mask]
        seg_amplitudes = dense_amplitudes[mask]

        if len(seg_times) < 2:
            seg_times = np.array(
                [segment.start_time, segment.end_time],
                dtype=float,
            )
            seg_amplitudes = np.array([0.0, 0.0], dtype=float)

        if segment.is_pause or segment.pulse_count == 0:
            pulse_density = np.zeros_like(seg_amplitudes)
            reconstructed_pulses = 0.0

            return TarzanSegmentProfile(
                segment_id=segment.segment_id,
                start_time=segment.start_time,
                end_time=segment.end_time,
                direction=segment.direction,
                pulse_count=segment.pulse_count,
                is_pause=segment.is_pause,
                times_ms=seg_times,
                amplitude_samples=seg_amplitudes,
                pulse_density=pulse_density,
                reconstructed_pulses=reconstructed_pulses,
            )

        weights = np.abs(seg_amplitudes)
        area = np.trapezoid(weights, seg_times)

        if area <= 0.0:
            pulse_density = np.zeros_like(seg_amplitudes)
            reconstructed_pulses = 0.0
        else:
            scale = segment.pulse_count / area
            pulse_density = weights * scale
            reconstructed_pulses = float(np.trapezoid(pulse_density, seg_times))

        return TarzanSegmentProfile(
            segment_id=segment.segment_id,
            start_time=segment.start_time,
            end_time=segment.end_time,
            direction=segment.direction,
            pulse_count=segment.pulse_count,
            is_pause=segment.is_pause,
            times_ms=seg_times,
            amplitude_samples=seg_amplitudes,
            pulse_density=pulse_density,
            reconstructed_pulses=reconstructed_pulses,
        )