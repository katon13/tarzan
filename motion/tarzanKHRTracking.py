# -*- coding: utf-8 -*-
"""
TARZAN - KHR Tracking plugin

Plugin śledzenia obiektu:
error_x → filtracja → korekta A(t).

Parametry inspirowane praktyką systemów śledzenia:
- dead zone: ignorowanie mikrodrgań
- gain: siła korekty
- smooth: filtr dolnoprzepustowy
- max_correction: limit wyjścia
- max_delta_per_tick: ograniczenie skoku korekty
- prediction: lekkie wyprzedzenie ruchu obiektu
- damping: tłumienie pochodnej, redukcja oscylacji
- lost_target_decay: łagodne wygaszenie korekty przy utracie obiektu
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KHRTracking:
    gain: float = 0.003
    dead_zone_px: float = 18.0
    smooth: float = 0.18
    max_correction: float = 0.50
    return_to_zero: float = 0.92
    max_delta_per_tick: float = 0.045
    prediction: float = 0.12
    damping: float = 0.10
    lost_target_decay: float = 0.86

    error_x: float = 0.0
    target_visible: bool = True

    _value: float = 0.0
    _prev_error_x: float = 0.0

    def set_error(self, error_x: float, visible: bool = True) -> None:
        self.error_x = float(error_x)
        self.target_visible = bool(visible)

    def apply_profile(self, profile) -> None:
        self.gain = profile.gain
        self.dead_zone_px = profile.dead_zone_px
        self.smooth = profile.smooth
        self.max_correction = profile.max_correction
        self.return_to_zero = profile.return_to_zero
        self.max_delta_per_tick = profile.max_delta_per_tick
        self.prediction = profile.prediction
        self.damping = profile.damping
        self.lost_target_decay = profile.lost_target_decay

    def update_manual_settings(
        self,
        gain: float,
        dead_zone_px: float,
        smooth: float,
        max_correction: float,
        max_delta_per_tick: float,
        prediction: float,
        damping: float,
        return_to_zero: float | None = None,
        lost_target_decay: float | None = None,
    ) -> None:
        self.gain = float(gain)
        self.dead_zone_px = float(dead_zone_px)
        self.smooth = float(smooth)
        self.max_correction = float(max_correction)
        self.max_delta_per_tick = float(max_delta_per_tick)
        self.prediction = float(prediction)
        self.damping = float(damping)
        if return_to_zero is not None:
            self.return_to_zero = float(return_to_zero)
        if lost_target_decay is not None:
            self.lost_target_decay = float(lost_target_decay)

    def update(self, axis_name: str, time_ms: int, base_value: float) -> float:
        if not self.target_visible:
            self._value *= self.lost_target_decay
            return self._value

        derivative = self.error_x - self._prev_error_x
        predicted_error = self.error_x + derivative * self.prediction

        raw = self._error_to_correction(predicted_error)

        # Tłumienie zmiany błędu redukuje oscylacje.
        raw -= derivative * self.gain * self.damping

        # Filtr smooth.
        wanted = self._value + (raw - self._value) * self.smooth

        # Ograniczenie maksymalnego skoku korekty na tick.
        delta = wanted - self._value
        if delta > self.max_delta_per_tick:
            wanted = self._value + self.max_delta_per_tick
        elif delta < -self.max_delta_per_tick:
            wanted = self._value - self.max_delta_per_tick

        self._value = wanted

        if abs(self.error_x) <= self.dead_zone_px:
            self._value *= self.return_to_zero

        self._value = max(-self.max_correction, min(self.max_correction, self._value))
        self._prev_error_x = self.error_x

        return self._value

    def _error_to_correction(self, error_x: float) -> float:
        if abs(error_x) <= self.dead_zone_px:
            return 0.0

        corrected_error = error_x
        if error_x > 0:
            corrected_error -= self.dead_zone_px
        else:
            corrected_error += self.dead_zone_px

        value = corrected_error * self.gain
        return max(-self.max_correction, min(self.max_correction, value))
