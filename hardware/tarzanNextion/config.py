from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "nextion"


def load_json(filename: str, default: Any) -> Any:
    path = DATA_DIR / filename
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(filename: str, data: Any) -> Path:
    path = DATA_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_ports() -> Dict[str, Any]:
    return load_json(
        "nextion_ports.json",
        {
            "nextion_5": {"port": "COM5", "baudrate": 115200, "enabled": False},
            "nextion_7": {"port": "COM7", "baudrate": 115200, "enabled": False},
            "poll_interval_ms": 100,
            "sync_interval_ms": 300,
        },
    )
