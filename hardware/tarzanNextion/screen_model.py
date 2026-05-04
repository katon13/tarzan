from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .config import load_json


@dataclass
class ScreenDefinition:
    name: str
    width: int
    height: int
    pages: List[Dict[str, Any]]
    settings: Dict[str, Any]


def load_screen_definition(screen_key: str) -> ScreenDefinition:
    layout = load_json(f"{screen_key}_layout.json", {})
    settings = load_json(f"{screen_key}_settings.json", {})
    screen = layout.get("screen", {})
    return ScreenDefinition(
        name=screen.get("name", screen_key),
        width=int(screen.get("width", 800)),
        height=int(screen.get("height", 480)),
        pages=list(layout.get("pages", [])),
        settings=settings,
    )
