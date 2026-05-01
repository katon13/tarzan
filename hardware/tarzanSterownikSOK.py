"""
TARZAN — SOK (Sterownik Obrotowy Kurkowy)

Warstwa hardware/symulator sygnałów dla PAR.
Ten moduł nie generuje choreografii, nie liczy krzywych i nie dotyka mechaniki osi.
Publikuje wyłącznie sygnały DIR/CTR oraz przyciski pomocnicze SOK do SignalBus.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, MutableMapping, Optional


@dataclass(frozen=True)
class SokSectionConfig:
    name: str
    ctr_signals: List[str] = field(default_factory=list)
    dir_signals: List[str] = field(default_factory=list)
    button_signals: List[str] = field(default_factory=list)


SOK_SECTIONS: Dict[str, SokSectionConfig] = {
    "SOKPan": SokSectionConfig(
        name="SOKPan",
        ctr_signals=["rec_p20_bridge_play_ctr_x"],
        dir_signals=["rec_p17_bridge_play_dir_x"],
    ),
    "SOKTilt": SokSectionConfig(
        name="SOKTilt",
        ctr_signals=["rec_p21_bridge_play_ctr_y"],
        dir_signals=["rec_p18_bridge_play_dir_y"],
    ),
    "SOKFokus": SokSectionConfig(
        name="SOKFokus",
        ctr_signals=["rec_p05_copy_ctr_focus", "rec_p06_copy_ctr_tilt"],
        dir_signals=["rec_p07_copy_dir_focus", "rec_p08_copy_dir_tilt"],
        button_signals=["par_sok_fokus_button_right"],
    ),
    "SOKCam": SokSectionConfig(
        name="SOKCam",
        ctr_signals=["rec_p01_copy_ctr_cam_h", "rec_p02_copy_ctr_cam_v"],
        dir_signals=["rec_p03_copy_dir_cam_h", "rec_p04_copy_dir_cam_v"],
        button_signals=["par_sok_cam_button_left", "par_sok_cam_button_right"],
    ),
}


class TarzanSterownikSOK:
    """Mały adapter logiczny SOK -> SignalBus.

    `bus` ma implementować `force_signal(name, value, source=...)`.
    """

    def __init__(self, bus, sections: Optional[Mapping[str, SokSectionConfig]] = None) -> None:
        self.bus = bus
        self.sections: Mapping[str, SokSectionConfig] = sections or SOK_SECTIONS
        self.position: MutableMapping[str, int] = {key: 0 for key in self.sections}

    def step(self, section: str, direction: int) -> int:
        cfg = self.sections[section]
        direction = 1 if direction else 0
        delta = 1 if direction else -1
        self.position[section] = self.position.get(section, 0) + delta
        for name in cfg.dir_signals:
            self.bus.force_signal(name, direction, source="SOK")
        for name in cfg.ctr_signals:
            self.bus.force_signal(name, 1, source="SOK")
        return self.position[section]

    def reset_ctr(self, section: str) -> None:
        cfg = self.sections[section]
        for name in cfg.ctr_signals:
            self.bus.force_signal(name, 0, source="SOK_RESET")

    def press_button(self, signal_name: str, value: int = 1) -> None:
        self.bus.force_signal(signal_name, 1 if value else 0, source="SOK_BUTTON")
