# -*- coding: utf-8 -*-
"""
TARZAN - KHR profiles

Ładowanie profili KHR z data/khr/khr_settings.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class KHRProfile:
    name: str
    description: str
    gain: float
    dead_zone_px: float
    smooth: float
    max_correction: float
    return_to_zero: float
    max_delta_per_tick: float
    prediction: float
    damping: float
    lost_target_decay: float
    object_speed: float
    step_angle_deg: float


def load_khr_settings(project_root: Path) -> dict:
    path = project_root / "data" / "khr" / "khr_settings.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def profile_from_settings(settings: dict, name: str | None = None) -> KHRProfile:
    profile_name = name or settings.get("active_profile", "CINEMA")
    data = settings["profiles"][profile_name]

    return KHRProfile(
        name=profile_name,
        description=data.get("description", ""),
        gain=float(data["gain"]),
        dead_zone_px=float(data["dead_zone_px"]),
        smooth=float(data["smooth"]),
        max_correction=float(data["max_correction"]),
        return_to_zero=float(data["return_to_zero"]),
        max_delta_per_tick=float(data["max_delta_per_tick"]),
        prediction=float(data["prediction"]),
        damping=float(data["damping"]),
        lost_target_decay=float(data["lost_target_decay"]),
        object_speed=float(data["object_speed"]),
        step_angle_deg=float(data["step_angle_deg"]),
    )


def profile_names(settings: dict) -> list[str]:
    return list(settings.get("profiles", {}).keys())
