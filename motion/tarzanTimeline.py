from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class TarzanTimelineFrame:
    """
    Jedna ramka roboczego timeline protokołu TARZANA.

    To jest warstwa pośrednia dla edytora i symulacji:
    - czas próbki
    - liczba impulsów STEP w danym przedziale
    - stan STEP uproszczony
    - stan DIR
    - stan ENABLE
    """
    time_ms: int
    step_count: int
    step_state: int
    dir_state: int
    enable_state: int


class TarzanTimeline:
    """
    Generator roboczego timeline protokołu TARZANA.

    Założenie:
    - pracujemy na siatce czasu, np. co 10 ms,
    - w każdej próbce zapisujemy stan roboczy osi,
    - impulsy STEP są agregowane do danego przedziału czasu.

    To NIE jest jeszcze finalny hardware timeline mikrosekundowy.
    To jest warstwa zgodna z filozofią TARZANA:
    czas + stan sygnałów w kolejnych próbkach.
    """

    def __init__(self, sample_step_ms: int = 10) -> None:
        self.sample_step_ms = sample_step_ms

    def build_frames(
        self,
        step_times: list[float],
        segment_start_ms: int,
        segment_end_ms: int,
        direction: int,
        enabled: bool = True,
    ) -> list[TarzanTimelineFrame]:
        if segment_end_ms < segment_start_ms:
            raise ValueError("segment_end_ms nie może być mniejsze od segment_start_ms")

        step_times_array = np.array(step_times, dtype=float)

        frames: list[TarzanTimelineFrame] = []

        frame_start = int(segment_start_ms)
        frame_end_limit = int(segment_end_ms)

        while frame_start <= frame_end_limit:
            frame_end = frame_start + self.sample_step_ms

            if step_times_array.size > 0:
                mask = (step_times_array >= frame_start) & (step_times_array < frame_end)
                step_count = int(np.count_nonzero(mask))
            else:
                step_count = 0

            frame = TarzanTimelineFrame(
                time_ms=frame_start,
                step_count=step_count,
                step_state=1 if step_count > 0 else 0,
                dir_state=self._map_direction(direction),
                enable_state=1 if enabled else 0,
            )

            frames.append(frame)
            frame_start += self.sample_step_ms

        return frames

    def _map_direction(self, direction: int) -> int:
        """
        Mapowanie kierunku do roboczego stanu DIR.
        """
        if direction > 0:
            return 1
        if direction < 0:
            return 0
        return 0