"""
Format pakietów TSP — TARZAN Signal Protocol.

Transport: TCP + JSON Lines / NDJSON.
Jedna wiadomość = jeden obiekt JSON zakończony znakiem \n.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from .tarzanTspConfig import TSP_PROTOCOL_NAME, TSP_PROTOCOL_VERSION


LANE_URGENT = "urgent"
LANE_FAST = "fast"
LANE_NORMAL = "normal"
LANE_SLOW = "slow"
LANE_HEALTH = "health"

PRIORITY_SAFETY = "SAFETY"
PRIORITY_HIGH = "HIGH"
PRIORITY_MARKER = "MARKER"
PRIORITY_INFO = "INFO"

CMD_HELLO = "hello"
CMD_PING = "ping"
CMD_GET_SIGNAL = "get_signal"
CMD_SET_SIGNAL = "set_signal"
CMD_GET_SIGNAL_CATALOG = "get_signal_catalog"
CMD_GET_ALL_SIGNALS = "get_all_signals"
CMD_SUBSCRIBE = "subscribe"
CMD_UNSUBSCRIBE = "unsubscribe"
CMD_GET_STATE = "get_state"
CMD_CALL_ACTION = "call_action"
CMD_TRACE_SIGNAL = "trace_signal"
CMD_DUMP_SNAPSHOT = "dump_snapshot"

ALL_LANES = {LANE_URGENT, LANE_FAST, LANE_NORMAL, LANE_SLOW, LANE_HEALTH}


class TspProtocolError(ValueError):
    """Błąd formatu wiadomości TSP."""


def now_ms() -> int:
    return int(time.time() * 1000)


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


def encode_jsonl(message: Dict[str, Any]) -> bytes:
    return (json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def decode_jsonl_line(raw_line: bytes | str) -> Dict[str, Any]:
    if isinstance(raw_line, bytes):
        text = raw_line.decode("utf-8", errors="replace").strip()
    else:
        text = raw_line.strip()

    if not text:
        raise TspProtocolError("empty_line")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TspProtocolError(f"invalid_json: {exc}") from exc

    if not isinstance(data, dict):
        raise TspProtocolError("message_must_be_object")

    return data


def ok_response(cmd: str, **fields: Any) -> Dict[str, Any]:
    data: Dict[str, Any] = {"ok": True, "cmd": cmd, "ts": now_ms()}
    data.update(fields)
    return data


def error_response(cmd: str, error: str, **fields: Any) -> Dict[str, Any]:
    data: Dict[str, Any] = {"ok": False, "cmd": cmd, "error": error, "ts": now_ms()}
    data.update(fields)
    return data


def hello_response(node: str, role: str, signal_count: int) -> Dict[str, Any]:
    return ok_response(
        CMD_HELLO,
        protocol=TSP_PROTOCOL_NAME,
        version=TSP_PROTOCOL_VERSION,
        node=node,
        role=role,
        signal_count=signal_count,
    )


def snajper_packet(lane: str, values: Dict[str, Any], dt_ms: Optional[int] = None) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "event": "snajper_packet",
        "lane": lane,
        "ts": now_ms(),
        "values": values,
    }
    if dt_ms is not None:
        data["dt_ms"] = dt_ms
    return data


def urgent_event(name: str, value: Any, reason: str, priority: str = PRIORITY_HIGH, **fields: Any) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "event": "urgent",
        "lane": LANE_URGENT,
        "priority": priority,
        "ts": now_ms(),
        "name": name,
        "value": value,
        "reason": reason,
    }
    data.update(fields)
    return data


def health_packet(**fields: Any) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "event": "health",
        "lane": LANE_HEALTH,
        "ts": now_ms(),
    }
    data.update(fields)
    return data


def normalize_signal_list(value: Any) -> list[str]:
    if value is None:
        return []
    if value == "*":
        return ["*"]
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(x) for x in value]
    return []


@dataclass(frozen=True)
class TspCommand:
    cmd: str
    payload: Dict[str, Any]

    @classmethod
    def from_message(cls, message: Dict[str, Any]) -> "TspCommand":
        cmd = message.get("cmd")
        if not isinstance(cmd, str) or not cmd:
            raise TspProtocolError("missing_cmd")
        return cls(cmd=cmd, payload=message)
