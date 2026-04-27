# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class KHRStepPreview:
    accumulator: float = 0.0

    def sample(self, amplitude: float) -> tuple[int, int]:
        direction = 1 if amplitude >= 0.0 else 0
        self.accumulator += abs(amplitude)
        if self.accumulator >= 1.0:
            self.accumulator -= 1.0
            return direction, 1
        return direction, 0
