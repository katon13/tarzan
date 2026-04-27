# -*- coding: utf-8 -*-
"""
TARZAN - Tracking State Filter

Filtr stanu celu:
- wygładzanie środka obiektu
- histereza widoczności
- ochrona przed skokiem celu
"""

from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass
class FilteredTarget:
    visible: bool = False
    x: float = 0.0
    y: float = 0.0
    area: float = 0.0


class TrackingStateFilter:
    def __init__(
        self,
        center_smoothing: float = 0.35,
        area_smoothing: float = 0.25,
        visible_hysteresis_on: int = 2,
        visible_hysteresis_off: int = 5,
        hold_last_target_ms: int = 250,
        max_jump_px: float = 220.0,
    ) -> None:
        self.center_smoothing = float(center_smoothing)
        self.area_smoothing = float(area_smoothing)
        self.visible_hysteresis_on = int(visible_hysteresis_on)
        self.visible_hysteresis_off = int(visible_hysteresis_off)
        self.hold_last_target_ms = int(hold_last_target_ms)
        self.max_jump_px = float(max_jump_px)

        self.target = FilteredTarget()
        self._on_count = 0
        self._off_count = 0
        self._last_seen_ms = 0

    def update(self, visible: bool, x: float, y: float, area: float) -> FilteredTarget:
        now_ms = int(time.time() * 1000)

        if visible:
            if self.target.visible:
                dx = x - self.target.x
                dy = y - self.target.y
                if (dx * dx + dy * dy) ** 0.5 > self.max_jump_px:
                    visible = False

        if visible:
            self._on_count += 1
            self._off_count = 0
            self._last_seen_ms = now_ms

            if not self.target.visible and self._on_count >= self.visible_hysteresis_on:
                self.target.visible = True
                self.target.x = x
                self.target.y = y
                self.target.area = area
            elif self.target.visible:
                s = self.center_smoothing
                a = self.area_smoothing
                self.target.x = self.target.x + (x - self.target.x) * s
                self.target.y = self.target.y + (y - self.target.y) * s
                self.target.area = self.target.area + (area - self.target.area) * a

        else:
            self._off_count += 1
            self._on_count = 0

            hold = (now_ms - self._last_seen_ms) <= self.hold_last_target_ms
            if self._off_count >= self.visible_hysteresis_off and not hold:
                self.target.visible = False

        return self.target
