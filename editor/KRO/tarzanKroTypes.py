from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class KroPluginType(str, Enum):
    KONTRA = "KONTRA"
    FOLLOW = "FOLLOW"
    COMP = "COMP"
    SYNC = "SYNC"


@dataclass
class KroRelationSpec:
    relation_id: str
    source_axis_id: str
    target_axis_id: str
    plugin_type: KroPluginType | str = KroPluginType.KONTRA
    enabled: bool = True

    def normalized_plugin_type(self) -> KroPluginType:
        try:
            if isinstance(self.plugin_type, KroPluginType):
                return self.plugin_type
            return KroPluginType(str(self.plugin_type).strip().upper())
        except Exception:
            return KroPluginType.KONTRA

    def clamp(self) -> None:
        self.relation_id = str(self.relation_id or "").strip()
        self.source_axis_id = str(self.source_axis_id or "").strip()
        self.target_axis_id = str(self.target_axis_id or "").strip()
        self.enabled = bool(self.enabled)
        self.plugin_type = self.normalized_plugin_type()


@dataclass
class KroAxisLine:
    axis_id: str
    points: list[tuple[int, float]]
    y_limit: float = 100.0


@dataclass
class KroAxisMechanicalProfile:
    axis_id: str
    pulses_per_cycle: float = 0.0
    cruise_max_pulses_per_second: float = 0.0
    start_settle_pulses: float = 0.0
    start_settle_time: float = 0.0
    start_ramp_pulses: float = 0.0
    start_ramp_time: float = 0.0
    backlash_compensation_pulses: float = 0.0


@dataclass
class KroTuningProfile:
    # Bazowe mnożniki wyliczane z mechaniki i pluginów
    axis_multiplier: float = 1.0
    plugin_multiplier: float = 1.0

    # Parametry strojenia empirycznego
    empirical_gain: float = 1.0
    damping: float = 1.0
    max_effect_limit: float = 100.0
    backlash_weight: float = 0.0
    start_settle_weight: float = 0.0
    start_ramp_weight: float = 0.0
    inertia_weight: float = 0.0
    cruise_limit_weight: float = 0.0
    direction_correction: float = 1.0  # 1.0 lub -1.0
    comment: str = ""

    extra_params: dict = field(default_factory=dict)


@dataclass
class KroBuildResult:
    target_axis_id: str
    plugin_type: KroPluginType
    new_points: list[tuple[int, float]]
    status: str
