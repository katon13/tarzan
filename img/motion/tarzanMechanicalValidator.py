from __future__ import annotations

from motion.tarzanTakeModel import TarzanTake


class TarzanMechanicalValidator:
    """
    Pierwsza wersja walidatora mechanicznego.
    Sprawdza podstawowe warunki logiczne osi i segmentów.
    """

    def validate_take(self, take: TarzanTake) -> list[str]:
        errors: list[str] = []

        for axis_key, axis in take.axes.items():
            errors.extend(self._validate_axis(axis_key, axis))

        return errors

    def _validate_axis(self, axis_key: str, axis) -> list[str]:
        errors: list[str] = []

        if axis.full_cycle_pulses <= 0:
            errors.append(f"{axis_key}: full_cycle_pulses musi być > 0")

        if axis.min_full_cycle_time_s <= 0:
            errors.append(f"{axis_key}: min_full_cycle_time_s musi być > 0")

        if axis.max_pulse_rate <= 0:
            errors.append(f"{axis_key}: max_pulse_rate musi być > 0")

        if axis.max_acceleration <= 0:
            errors.append(f"{axis_key}: max_acceleration musi być > 0")

        previous_end = None
        for segment in axis.segments:
            if segment.end_time < segment.start_time:
                errors.append(
                    f"{axis_key}: segment {segment.segment_id} ma end_time < start_time"
                )

            if segment.direction not in (-1, 0, 1):
                errors.append(
                    f"{axis_key}: segment {segment.segment_id} ma nieprawidłowy direction"
                )

            if segment.is_pause and segment.pulse_count != 0:
                errors.append(
                    f"{axis_key}: segment {segment.segment_id} jest pauzą, ale pulse_count != 0"
                )

            if previous_end is not None and segment.start_time < previous_end:
                errors.append(
                    f"{axis_key}: segment {segment.segment_id} nachodzi na poprzedni segment"
                )

            previous_end = segment.end_time

        if axis.start_must_be_zero and axis.curve.control_points:
            if axis.curve.control_points[0].amplitude != 0.0:
                errors.append(f"{axis_key}: pierwszy punkt krzywej musi mieć amplitudę 0.0")

        if axis.end_must_be_zero and axis.curve.control_points:
            if axis.curve.control_points[-1].amplitude != 0.0:
                errors.append(f"{axis_key}: ostatni punkt krzywej musi mieć amplitudę 0.0")

        return errors