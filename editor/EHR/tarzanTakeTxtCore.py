
from __future__ import annotations

from pathlib import Path
import re


def _parse_take_base_and_version(path: Path | None) -> tuple[str, int]:
    if path is None:
        return "TAKE_001", 0
    stem = Path(path).stem
    m = re.match(r"^(TAKE_\d+)(?:_v(\d+))?$", stem, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper(), int(m.group(2) or "0")
    m2 = re.search(r"(TAKE_\d+)", stem, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).upper(), 0
    return "TAKE_001", 0


def next_take_txt_path(current_path: Path | None, protocol_dir: Path, slot_index: int) -> Path:
    protocol_dir.mkdir(parents=True, exist_ok=True)
    if current_path is None:
        base = f"TAKE_{slot_index + 1:03d}"
        version = 1
    else:
        base, old_v = _parse_take_base_and_version(Path(current_path))
        version = old_v + 1 if old_v > 0 else 1
    return protocol_dir / f"{base}_v{version:02d}.txt"


def save_take_txt(axis_models, duration_ms: int, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("TARZAN_TAKE_TXT_V1")
    lines.append(f"DURATION_MS={int(duration_ms)}")
    lines.append("")

    for axis in axis_models:
        lines.append(f"[AXIS]{axis.axis_def.axis_id}|{axis.axis_def.axis_name}")
        if getattr(axis, "is_release_axis", False):
            release_time = getattr(axis, "release_time_ms", None)
            lines.append(f"RELEASE_MS={'' if release_time is None else int(release_time)}")
        for node in getattr(axis, "nodes", []):
            lines.append(f"NODE|{int(node.time_ms)}|{float(node.y):.6f}")
        lines.append("")

    lines.append("[PROTOCOL]")
    header = ["TIME_MS"]
    all_rows = []
    for axis in axis_models:
        rows = axis.protocol_rows(duration_ms=duration_ms)
        all_rows.append((axis, rows))
        header += [
            f"{axis.axis_def.axis_id.upper()}_DIR",
            f"{axis.axis_def.axis_id.upper()}_STEP",
            f"{axis.axis_def.axis_id.upper()}_EVENT",
        ]
    lines.append(";".join(header))

    steps = duration_ms // 10
    for i in range(steps + 1):
        row = [str(i * 10)]
        for axis, rows in all_rows:
            r = rows[i]
            row += [str(int(r["dir"])), str(int(r["step"])), str(r["event"])]
        lines.append(";".join(row))

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_take_txt(axis_models, path: str | Path) -> int:
    from editor.EHR.tarzanEhrMultiAxisModel import AxisNode

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    duration_ms: int | None = None
    axis_map = {axis.axis_def.axis_id: axis for axis in axis_models}
    parsed_nodes: dict[str, list[AxisNode]] = {axis.axis_def.axis_id: [] for axis in axis_models}
    current_axis_id: str | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("DURATION_MS="):
            try:
                duration_ms = int(line.split("=", 1)[1].strip())
            except Exception:
                duration_ms = None
            continue
        if line.startswith("[AXIS]"):
            payload = line[6:]
            current_axis_id = payload.split("|", 1)[0].strip()
            continue
        if line.startswith("[PROTOCOL]"):
            current_axis_id = None
            continue
        if current_axis_id is None:
            continue
        axis = axis_map.get(current_axis_id)
        if axis is None:
            continue
        if line.startswith("RELEASE_MS="):
            value = line.split("=", 1)[1].strip()
            if getattr(axis, "is_release_axis", False):
                axis.release_time_ms = int(value) if value else None
            continue
        if line.startswith("NODE|"):
            _, t, y = line.split("|", 2)
            parsed_nodes[current_axis_id].append(AxisNode(int(t), float(y)))

    loaded_duration = int(duration_ms or 0)
    for axis in axis_models:
        if loaded_duration:
            axis.set_axis_take_duration_ms(loaded_duration)
        nodes = parsed_nodes.get(axis.axis_def.axis_id, [])
        if nodes:
            axis.nodes = nodes
        axis.sort_and_fix_nodes()
        axis.clone_original_state()
        axis._invalidate_cache()

    return loaded_duration
