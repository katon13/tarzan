# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol


class KHRPlugin(Protocol):
    def update(self, axis_name: str, time_ms: int, base_value: float) -> float:
        """Zwraca korektę A(t), nie STEP/DIR."""


@dataclass
class TarzanKHR:
    plugins: list[KHRPlugin] = field(default_factory=list)
    max_output: float = 1.0

    def add_plugin(self, plugin: KHRPlugin) -> None:
        self.plugins.append(plugin)

    def clear_plugins(self) -> None:
        self.plugins.clear()

    def update(self, axis_name: str, time_ms: int, base_value: float) -> float:
        correction = 0.0
        for plugin in self.plugins:
            correction += plugin.update(axis_name, time_ms, base_value)
        return max(-self.max_output, min(self.max_output, base_value + correction))
