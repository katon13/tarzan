# -*- coding: utf-8 -*-
"""
TARZAN - Vision Config

Jedno miejsce ładowania ustawień kamery i trackingu.

Ustawienia są w:
data/khr/vision_settings.json
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HsvRange:
    h_min: int
    s_min: int
    v_min: int
    h_max: int
    s_max: int
    v_max: int


@dataclass
class TargetProfile:
    name: str
    description: str
    hsv_ranges: list[HsvRange]
    min_area: float
    max_area: float
    min_solidity: float
    min_extent: float
    morph_open_kernel: int
    morph_close_kernel: int
    blur_kernel: int
    prefer_largest_contour: bool


def load_vision_settings(project_root: Path) -> dict:
    path = project_root / "data" / "khr" / "vision_settings.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def target_profile_from_settings(settings: dict, name: str | None = None) -> TargetProfile:
    tracking = settings["tracking"]
    target_name = name or tracking.get("active_target", "RED_OBJECT")
    data = tracking["target_profiles"][target_name]

    return TargetProfile(
        name=target_name,
        description=data.get("description", ""),
        hsv_ranges=[HsvRange(**item) for item in data["hsv_ranges"]],
        min_area=float(data["min_area"]),
        max_area=float(data["max_area"]),
        min_solidity=float(data["min_solidity"]),
        min_extent=float(data["min_extent"]),
        morph_open_kernel=int(data["morph_open_kernel"]),
        morph_close_kernel=int(data["morph_close_kernel"]),
        blur_kernel=int(data["blur_kernel"]),
        prefer_largest_contour=bool(data["prefer_largest_contour"]),
    )


def target_profile_names(settings: dict) -> list[str]:
    return list(settings.get("tracking", {}).get("target_profiles", {}).keys())


def odd_kernel(value: int) -> int:
    value = int(value)
    if value <= 1:
        return 1
    if value % 2 == 0:
        value += 1
    return value
