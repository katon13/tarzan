from __future__ import annotations

from typing import Any

TERMINATOR = b"\xff\xff\xff"


def _quote(value: Any) -> str:
    text = str(value).replace('"', r'\"')
    return f'"{text}"'


def command_bytes(command: str) -> bytes:
    return command.encode("ascii", errors="ignore") + TERMINATOR


def cmd_page(page_id: str) -> bytes:
    return command_bytes(f"page {page_id}")


def cmd_text(component: str, value: Any) -> bytes:
    return command_bytes(f"{component}.txt={_quote(value)}")


def cmd_value(component: str, value: Any) -> bytes:
    try:
        ivalue = int(float(value))
    except Exception:
        ivalue = 0
    return command_bytes(f"{component}.val={ivalue}")


def cmd_visible(component: str, visible: bool) -> bytes:
    return command_bytes(f"vis {component},{1 if visible else 0}")


def cmd_color(component: str, color_565: int) -> bytes:
    return command_bytes(f"{component}.pco={int(color_565)}")


def rgb_to_565(hex_color: str) -> int:
    color = (hex_color or "#ffffff").lstrip("#")
    if len(color) != 6:
        return 65535
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
