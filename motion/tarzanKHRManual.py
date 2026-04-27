# -*- coding: utf-8 -*-
"""
TARZAN - KHR Manual plugin

Placeholder pod ręczną korektę operatora.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KHRManual:
    value: float = 0.0

    def set_value(self, value: float) -> None:
        self.value = float(value)

    def update(self, axis_name: str, time_ms: int, base_value: float) -> float:
        return self.value
