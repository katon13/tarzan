from __future__ import annotations

"""
TARZAN SNAJPER BULLET

Bullet przygotowuje wartość/payload dla celu Snajpera.

Nie wskazuje targetu.
Nie obsługuje COM.
Nie wykonuje strzału.
"""

from typing import Any, Callable, Dict
import re


RED_565 = 63488
GREEN_565 = 2016
WHITE_565 = 65535


def clamp_int(value: Any, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(round(float(value)))))
    except Exception:
        return minimum


def axis_counter(value: Any, direction: int = 0) -> str:
    # Licznik impulsów jest wartością stałą/narastającą.
    # Kierunek pokazuje kolor .pco, więc tekst nie ma znaku +/-.
    try:
        mag = abs(int(round(float(value))))
        return f"{mag:06d}"
    except Exception:
        text = str(value).strip()
        if text.startswith(("+", "-")):
            text = text[1:]
        return text


def one_decimal(value: Any, suffix: str = "") -> str:
    try:
        return f"{float(value):.1f}{suffix}"
    except Exception:
        return str(value)


def integer_value(value: Any, suffix: str = "") -> str:
    try:
        return f"{int(round(float(value)))}{suffix}"
    except Exception:
        return str(value)


def binary(value: Any) -> str:
    try:
        return "1" if int(float(value or 0)) else "0"
    except Exception:
        text = str(value).strip().upper()
        return "1" if text in {"1", "ON", "TRUE", "YES", "HIGH"} else "0"


def dir_int(value: Any) -> int:
    try:
        return 1 if int(float(value or 0)) == 1 else 0
    except Exception:
        return 1 if str(value).strip() in {"1", "+", "PLUS", "RIGHT", "UP"} else 0


def xyz_components(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return {
            "tx": value.get("x", value.get("tx", 0)),
            "ty": value.get("y", value.get("ty", 0)),
            "tz": value.get("z", value.get("tz", 0)),
        }
    if isinstance(value, (list, tuple)):
        vals = list(value)[:3]
    else:
        text = str(value).strip()
        if "," in text or ";" in text or " " in text:
            vals = [p for p in re.split(r"[;,\s]+", text) if p][:3]
        else:
            vals = [value]
    while len(vals) < 3:
        vals.append(0)
    return {"tx": vals[0], "ty": vals[1], "tz": vals[2]}


def xyz_axis_number(axis_target: str, value: Any) -> int:
    # Jeżeli Snajper odpala osobny sygnał level_x/level_y/level_z,
    # do targetu tx/ty/tz trafia pojedyncza liczba i trzeba ją traktować
    # jako wartość tej konkretnej osi, nie jako pierwszy element pakietu XYZ.
    if not isinstance(value, (dict, list, tuple)):
        text = str(value).strip()
        if not ("," in text or ";" in text or " " in text):
            raw = value
        else:
            raw = xyz_components(value).get(axis_target, 0)
    else:
        raw = xyz_components(value).get(axis_target, 0)
    try:
        return max(-100, min(100, int(round(float(raw)))))
    except Exception:
        return 0


def xyz_axis_text(axis_target: str, value: Any) -> str:
    # Tekst nie ma znaku +/-; znak pokazuje kolor .pco danego pola.
    number = xyz_axis_number(axis_target, value)
    return f"{abs(number):03d}"


def xyz_axis_sign(axis_target: str, value: Any) -> int:
    number = xyz_axis_number(axis_target, value)
    if number > 0:
        return 1
    if number < 0:
        return -1
    return 0


def take_label(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return text

    m = re.search(r"TAKE[_\s-]*(\d+).*?[vV](\d+)", text)
    if m:
        return f"{int(m.group(1)):03d} {int(m.group(2)):02d}"

    m = re.search(r"(\d{1,3})[_\s-]*[vV](\d+)", text)
    if m:
        return f"{int(m.group(1)):03d} {int(m.group(2)):02d}"

    m = re.search(r"(\d{1,3})-(\d{1,3})", text)
    if m:
        return f"{int(m.group(1)):03d} {int(m.group(2)):02d}"

    try:
        return f"{int(float(text)):03d}"
    except Exception:
        return text


def tc_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return "00:00:00:000"
    if ":" in text:
        return text
    try:
        ms = max(0, int(round(float(text))))
        h = ms // 3_600_000
        ms %= 3_600_000
        m = ms // 60_000
        ms %= 60_000
        sec = ms // 1000
        milli = ms % 1000
        return f"{h:02d}:{m:02d}:{sec:02d}:{milli:03d}"
    except Exception:
        return text


def mode_text(value: Any) -> str:
    try:
        iv = int(float(value))
        if iv == 0:
            return "TEST"
        if iv == 1:
            return "LIVE"
        if iv == 2:
            return "MIX"
    except Exception:
        pass
    return str(value).upper()


def format_nextion_bullet(
    target: Any,
    value: Any,
    axis_dir_get: Callable[[str, int], int] | None = None,
) -> Any:
    """
    Przygotowuje gotowy pocisk dla physical_nextion.
    Snajper przekazuje wynik do Bridge.
    """
    if axis_dir_get is None:
        axis_dir_get = lambda _target, default=0: default

    if target.scope == "rrp_main" and target.target in {"t_p1_val", "t_p2_val"} and target.prop in {"txt", "text"}:
        return axis_counter(value, axis_dir_get(target.target, 0))
    if target.scope == "rrp_main" and target.target in {"t_p1_val", "t_p2_val"} and target.prop == "pco":
        return GREEN_565 if dir_int(value) == 1 else RED_565

    if target.scope == "level_xyz" and target.target in {"va0", "va1", "va2", "va3"} and target.prop == "val":
        return clamp_int(value, -100, 100)
    if target.scope == "take_main" and target.target == "t0" and target.prop in {"txt", "text"}:
        return tc_text(value)
    if target.scope == "take_main" and target.target in {"tx", "ty", "tz"} and target.prop in {"txt", "text"}:
        return xyz_axis_text(target.target, value)
    if target.scope == "take_main" and target.target in {"tx", "ty", "tz"} and target.prop == "pco":
        sign = xyz_axis_sign(target.target, value)
        if sign == 1:
            return GREEN_565
        if sign == -1:
            return RED_565
        return WHITE_565
    if target.scope == "take_main" and target.target.startswith("t_axis") and target.prop in {"txt", "text"}:
        return axis_counter(value, axis_dir_get(target.target, 0))
    if target.scope == "take_main" and target.target.startswith("t_axis") and target.prop == "pco":
        return GREEN_565 if dir_int(value) == 1 else RED_565
    if target.scope == "take_main" and target.target == "t_light" and target.prop in {"txt", "text"}:
        return integer_value(value)
    if target.scope == "take_main" and target.target == "t_temp" and target.prop in {"txt", "text"}:
        return one_decimal(value, suffix="")
    if target.scope == "take_main" and target.target in {"t_laser", "t_shock"} and target.prop in {"txt", "text"}:
        return binary(value)
    if target.scope == "take_main" and target.target == "t_status" and target.prop in {"txt", "text"}:
        return mode_text(value)
    if target.scope == "take_main" and target.target == "t_take" and target.prop in {"txt", "text"}:
        return take_label(value)
    if target.scope == "take_main" and target.target == "p5" and target.prop == "pic":
        # Ikona CLAP: 51 = aktywny (czerwony), 50 = standard
        return 51 if bool(value) else 50

    return value
