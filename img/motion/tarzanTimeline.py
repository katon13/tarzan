from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np

from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS


@dataclass
class TarzanTimelineFrame:
    """
    Jedna ramka czasu dla jednej osi.
    """
    time_ms: int
    step_count: int
    step_state: int
    dir_state: int
    enable_state: int


@dataclass
class TarzanAxisTimeline:
    """
    Timeline jednej osi.
    """
    axis_key: str
    axis_name: str
    frames: List[TarzanTimelineFrame] = field(default_factory=list)


class TarzanTimeline:
    """
    Generator timeline protokołu TARZANA.

    Wariant B:
    - przechowuje globalny timeline jako słownik:
      timeline[time_ms][axis_key] = {signals}

    To jest najwygodniejsze dla:
    - wielu osi,
    - symulacji,
    - eksportu do protokołu,
    - późniejszego tAA.
    """

    def __init__(self, sample_step_ms: int = CZAS_PROBKOWANIA_MS) -> None:
        self.sample_step_ms = sample_step_ms

    def build_axis_frames(
        self,
        step_times: List[float],
        segment_start_ms: int,
        segment_end_ms: int,
        direction: int,
        enabled: bool = True,
    ) -> List[TarzanTimelineFrame]:
        if segment_end_ms < segment_start_ms:
            raise ValueError("segment_end_ms nie może być mniejsze od segment_start_ms")

        step_times_array = np.array(step_times, dtype=float)
        frames: List[TarzanTimelineFrame] = []

        frame_start = int(segment_start_ms)
        frame_end_limit = int(segment_end_ms)

        while frame_start <= frame_end_limit:
            frame_end = frame_start + self.sample_step_ms

            if step_times_array.size > 0:
                mask = (step_times_array >= frame_start) & (step_times_array < frame_end)
                step_count = int(np.count_nonzero(mask))
            else:
                step_count = 0

            frames.append(
                TarzanTimelineFrame(
                    time_ms=frame_start,
                    step_count=step_count,
                    step_state=1 if step_count > 0 else 0,
                    dir_state=self._map_direction(direction),
                    enable_state=1 if enabled else 0,
                )
            )

            frame_start += self.sample_step_ms

        return frames

    def build_global_timeline(
        self,
        axis_timelines: List[TarzanAxisTimeline],
    ) -> Dict[int, Dict[str, Dict[str, int | str]]]:
        """
        Buduje wspólny timeline dla wszystkich osi.

        Wynik:
            {
                0: {
                    "camera_horizontal": {
                        "axis_name": "...",
                        "STEP_COUNT": 0,
                        "STEP": 0,
                        "DIR": 1,
                        "ENABLE": 1,
                    },
                    ...
                },
                10: {...},
                20: {...},
            }
        """
        global_timeline: Dict[int, Dict[str, Dict[str, int | str]]] = {}

        for axis_timeline in axis_timelines:
            for frame in axis_timeline.frames:
                if frame.time_ms not in global_timeline:
                    global_timeline[frame.time_ms] = {}

                global_timeline[frame.time_ms][axis_timeline.axis_key] = {
                    "axis_name": axis_timeline.axis_name,
                    "STEP_COUNT": frame.step_count,
                    "STEP": frame.step_state,
                    "DIR": frame.dir_state,
                    "ENABLE": frame.enable_state,
                }

        return dict(sorted(global_timeline.items(), key=lambda item: item[0]))

    def build_empty_axis_frames(
        self,
        take_start_ms: int,
        take_end_ms: int,
        enabled: bool = True,
    ) -> List[TarzanTimelineFrame]:
        """
        Pomocniczo buduje pusty timeline osi, gdy brak aktywnych segmentów.
        """
        if take_end_ms < take_start_ms:
            raise ValueError("take_end_ms nie może być mniejsze od take_start_ms")

        frames: List[TarzanTimelineFrame] = []
        current_time = int(take_start_ms)

        while current_time <= int(take_end_ms):
            frames.append(
                TarzanTimelineFrame(
                    time_ms=current_time,
                    step_count=0,
                    step_state=0,
                    dir_state=0,
                    enable_state=1 if enabled else 0,
                )
            )
            current_time += self.sample_step_ms

        return frames

    def _map_direction(self, direction: int) -> int:
        if direction > 0:
            return 1
        if direction < 0:
            return 0
        return 0