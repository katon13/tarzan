"""
Źródło sygnałów dla TSP.

Na tym etapie moduł generuje własne sygnały uruchomieniowe pod pełny protokół TSP.
Nie jest to osobna architektura — ta sama klasa zostanie później spięta z SignalBus.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Iterable, Optional

from .tarzanTspProtocol import (
    LANE_FAST,
    LANE_HEALTH,
    LANE_NORMAL,
    LANE_SLOW,
    PRIORITY_HIGH,
    PRIORITY_INFO,
    PRIORITY_MARKER,
    PRIORITY_SAFETY,
    monotonic_ms,
    urgent_event,
)

LOGIKA_DOZWOLONY = "DOZWOLONY"
LOGIKA_TYLKO_ODCZYT = "TYLKO_ODCZYT"
LOGIKA_ZABRONIONY = "ZABRONIONY"


@dataclass(frozen=True)
class TarzanTspSignalDef:
    name: str
    lane: str
    value_type: str
    default: Any
    logika_trybow: str = LOGIKA_DOZWOLONY
    rola_logiki: str = "STATUS"
    opis: str = ""

    def as_catalog_item(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "lane": self.lane,
            "type": self.value_type,
            "default": self.default,
            "logika_trybow": self.logika_trybow,
            "rola_logiki": self.rola_logiki,
            "opis": self.opis,
        }


class TarzanTspSignalProvider:
    """
    Provider sygnałów TSP.

    Obecnie generuje pełny zestaw sygnałów uruchomieniowych:
    - FAST: pulsy osi, RRP, TC,
    - NORMAL: tryby, transport, Nextion,
    - SLOW: sensory,
    - HEALTH: stan node.

    Późniejsza integracja: metody get_signal/set_signal/catalog zostają,
    a wnętrze zostanie spięte z SignalBus.
    """

    def __init__(self, node_name: str = "tarzanMiniPC") -> None:
        self.node_name = node_name
        self._lock = Lock()
        self._start_ms = monotonic_ms()
        self._last_ms = self._start_ms
        self._urgent_queue: list[Dict[str, Any]] = []
        self._signals: Dict[str, Any] = {}
        self._catalog: Dict[str, TarzanTspSignalDef] = {}
        self._build_catalog()
        self._reset_values()

    # ------------------------------------------------------------------
    # KATALOG
    # ------------------------------------------------------------------

    def _add(self, item: TarzanTspSignalDef) -> None:
        self._catalog[item.name] = item

    def _build_catalog(self) -> None:
        # TAKE / transport
        self._add(TarzanTspSignalDef("take_time_ms", LANE_FAST, "int", 0, LOGIKA_TYLKO_ODCZYT, "STATUS", "Czas TAKE w ms."))
        self._add(TarzanTspSignalDef("take_timecode", LANE_FAST, "str", "00:00:00:00", LOGIKA_TYLKO_ODCZYT, "STATUS", "Timecode TAKE."))
        self._add(TarzanTspSignalDef("active_mode", LANE_NORMAL, "str", "LIVE", LOGIKA_DOZWOLONY, "UI", "Aktywny tryb systemu."))
        self._add(TarzanTspSignalDef("transport_state", LANE_NORMAL, "str", "STOP", LOGIKA_DOZWOLONY, "UI", "Transport: STOP/PLAY/REC/PAUSE."))

        # RRP
        for name in ("rrp_p1_value", "rrp_p2_value"):
            self._add(TarzanTspSignalDef(name, LANE_FAST, "int", 0, LOGIKA_TYLKO_ODCZYT, "STATUS", "Wartość wskaźnika RRP."))
        self._add(TarzanTspSignalDef("rrp_p1_axis_index", LANE_NORMAL, "int", -1, LOGIKA_DOZWOLONY, "UI", "Wybrana oś P1."))
        self._add(TarzanTspSignalDef("rrp_p2_axis_index", LANE_NORMAL, "int", -1, LOGIKA_DOZWOLONY, "UI", "Wybrana oś P2."))
        self._add(TarzanTspSignalDef("rrp_p1_sensitivity", LANE_NORMAL, "int", 50, LOGIKA_DOZWOLONY, "UI", "Czułość P1 0-100."))
        self._add(TarzanTspSignalDef("rrp_p2_sensitivity", LANE_NORMAL, "int", 50, LOGIKA_DOZWOLONY, "UI", "Czułość P2 0-100."))

        # Osie TARZAN — pełne nazwy logiczne.
        axes = [
            "axis_cam_h",
            "axis_cam_v",
            "axis_cam_t",
            "axis_cam_f",
            "axis_arm_v",
            "axis_arm_h",
        ]
        for axis in axes:
            self._add(TarzanTspSignalDef(f"{axis}_pulses", LANE_FAST, "int", 0, LOGIKA_TYLKO_ODCZYT, "STATUS", f"Licznik impulsów {axis}."))
            self._add(TarzanTspSignalDef(f"{axis}_dir", LANE_FAST, "int", 0, LOGIKA_TYLKO_ODCZYT, "STATUS", f"DIR {axis}."))
            self._add(TarzanTspSignalDef(f"{axis}_step", LANE_FAST, "int", 0, LOGIKA_TYLKO_ODCZYT, "STATUS", f"STEP live {axis}."))

        # Nextion / Bridge
        self._add(TarzanTspSignalDef("nextion_page", LANE_NORMAL, "str", "take_main", LOGIKA_DOZWOLONY, "UI", "Aktywna strona Nextiona."))
        self._add(TarzanTspSignalDef("nextion_connected", LANE_NORMAL, "bool", True, LOGIKA_TYLKO_ODCZYT, "STATUS", "Status połączenia Nextion."))
        self._add(TarzanTspSignalDef("bridge_status", LANE_NORMAL, "str", "OK", LOGIKA_TYLKO_ODCZYT, "STATUS", "Status Bridge."))

        # Czujniki
        self._add(TarzanTspSignalDef("sensor_light_lux", LANE_SLOW, "float", 0.0, LOGIKA_TYLKO_ODCZYT, "SENSOR", "Światło BH1750."))
        self._add(TarzanTspSignalDef("sensor_level_x", LANE_SLOW, "float", 0.0, LOGIKA_TYLKO_ODCZYT, "SENSOR", "Poziomica X."))
        self._add(TarzanTspSignalDef("sensor_level_y", LANE_SLOW, "float", 0.0, LOGIKA_TYLKO_ODCZYT, "SENSOR", "Poziomica Y."))
        self._add(TarzanTspSignalDef("sensor_level_z", LANE_SLOW, "float", 1.0, LOGIKA_TYLKO_ODCZYT, "SENSOR", "Poziomica Z."))
        self._add(TarzanTspSignalDef("sensor_temp_c", LANE_SLOW, "float", 24.0, LOGIKA_TYLKO_ODCZYT, "SENSOR", "Temperatura."))
        self._add(TarzanTspSignalDef("sensor_shock_state", LANE_NORMAL, "int", 0, LOGIKA_TYLKO_ODCZYT, "SENSOR", "Czujnik wstrząsu."))

        # TFD / TAKE marker
        self._add(TarzanTspSignalDef("tfd_title", LANE_NORMAL, "str", "TARZAN TAKE", LOGIKA_DOZWOLONY, "UI", "Tytuł TFD."))
        self._add(TarzanTspSignalDef("tfd_director", LANE_NORMAL, "str", "DIRECTOR", LOGIKA_DOZWOLONY, "UI", "Reżyser TFD."))
        self._add(TarzanTspSignalDef("clap_event", LANE_NORMAL, "int", 0, LOGIKA_DOZWOLONY, "UI", "Zdarzenie klapsa."))
        self._add(TarzanTspSignalDef("take_marker", LANE_NORMAL, "str", "", LOGIKA_DOZWOLONY, "UI", "Marker TAKE."))

        # HEALTH
        self._add(TarzanTspSignalDef("node_name", LANE_HEALTH, "str", self.node_name, LOGIKA_TYLKO_ODCZYT, "STATUS", "Nazwa node."))
        self._add(TarzanTspSignalDef("node_uptime_ms", LANE_HEALTH, "int", 0, LOGIKA_TYLKO_ODCZYT, "STATUS", "Uptime TSP."))
        self._add(TarzanTspSignalDef("tsp_clients", LANE_HEALTH, "int", 0, LOGIKA_TYLKO_ODCZYT, "STATUS", "Liczba klientów TSP."))

    def _reset_values(self) -> None:
        for name, item in self._catalog.items():
            self._signals[name] = item.default

    def catalog(self) -> list[Dict[str, Any]]:
        with self._lock:
            return [item.as_catalog_item() for item in self._catalog.values()]

    def signal_count(self) -> int:
        with self._lock:
            return len(self._catalog)

    # ------------------------------------------------------------------
    # ODCZYT / ZAPIS
    # ------------------------------------------------------------------

    def get_signal(self, name: str) -> Any:
        with self._lock:
            if name not in self._signals:
                raise KeyError(name)
            return self._signals[name]

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._signals)

    def get_lane_values(self, lane: str, names: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        with self._lock:
            if names is None or "*" in set(names):
                wanted = [name for name, item in self._catalog.items() if item.lane == lane]
            else:
                wanted = [name for name in names if name in self._catalog and self._catalog[name].lane == lane]
            return {name: self._signals[name] for name in wanted if name in self._signals}

    def set_signal(self, name: str, value: Any, source: str = "tsp") -> Dict[str, Any]:
        with self._lock:
            item = self._catalog.get(name)
            if item is None:
                return {"ok": False, "error": "unknown_signal", "name": name}
            if item.logika_trybow == LOGIKA_TYLKO_ODCZYT:
                return {"ok": False, "error": "write_denied", "name": name, "reason": LOGIKA_TYLKO_ODCZYT}
            if item.logika_trybow == LOGIKA_ZABRONIONY:
                return {"ok": False, "error": "write_denied", "name": name, "reason": LOGIKA_ZABRONIONY}

            old = self._signals.get(name)
            self._signals[name] = self._coerce_value(value, item.value_type)
            new = self._signals[name]

            urgent = self._urgent_for_change(name, old, new, source)
            if urgent:
                self._urgent_queue.append(urgent)
            return {"ok": True, "name": name, "value": new}

    def _coerce_value(self, value: Any, value_type: str) -> Any:
        if value_type == "int":
            return int(value)
        if value_type == "float":
            return float(value)
        if value_type == "bool":
            return bool(value)
        if value_type == "str":
            return str(value)
        return value

    def _urgent_for_change(self, name: str, old: Any, new: Any, source: str) -> Optional[Dict[str, Any]]:
        if old == new:
            return None
        if name == "transport_state" and str(new).upper() in {"STOP", "PLAY", "REC", "PAUSE"}:
            priority = PRIORITY_SAFETY if str(new).upper() == "STOP" else PRIORITY_HIGH
            return urgent_event(name, new, f"transport_changed_by_{source}", priority)
        if name == "active_mode":
            return urgent_event(name, new, f"mode_changed_by_{source}", PRIORITY_HIGH)
        if name == "nextion_page":
            return urgent_event(name, new, "page_changed", PRIORITY_HIGH)
        if name in {"rrp_p1_axis_index", "rrp_p2_axis_index"}:
            return urgent_event(name, new, "rrp_axis_changed", PRIORITY_HIGH)
        if name in {"clap_event", "take_marker"}:
            return urgent_event(name, new, "take_marker", PRIORITY_MARKER)
        return None

    # ------------------------------------------------------------------
    # SYMULACJA RUCHU LIVE
    # ------------------------------------------------------------------

    def tick(self, client_count: int = 0) -> None:
        now = monotonic_ms()
        with self._lock:
            elapsed_ms = now - self._start_ms
            dt = max(1, now - self._last_ms)
            self._last_ms = now

            transport = str(self._signals.get("transport_state", "STOP")).upper()
            running = transport in {"PLAY", "REC"}

            self._signals["take_time_ms"] = elapsed_ms if running else self._signals.get("take_time_ms", 0)
            self._signals["take_timecode"] = self._format_timecode(int(self._signals.get("take_time_ms", 0)))

            t = elapsed_ms / 1000.0
            self._signals["rrp_p1_value"] = int(500 + 420 * math.sin(t * 1.7))
            self._signals["rrp_p2_value"] = int(500 + 390 * math.cos(t * 1.3))

            axes = ["axis_cam_h", "axis_cam_v", "axis_cam_t", "axis_cam_f", "axis_arm_v", "axis_arm_h"]
            for idx, axis in enumerate(axes):
                phase = t * (0.8 + idx * 0.13) + idx
                direction = 1 if math.sin(phase) >= 0 else -1
                step = 1 if int(elapsed_ms / 10 + idx) % (2 + (idx % 3)) == 0 else 0
                self._signals[f"{axis}_dir"] = direction
                self._signals[f"{axis}_step"] = step
                if running and step:
                    self._signals[f"{axis}_pulses"] = int(self._signals.get(f"{axis}_pulses", 0)) + direction

            self._signals["sensor_light_lux"] = round(430.0 + 70.0 * math.sin(t / 4.0), 2)
            self._signals["sensor_level_x"] = round(3.5 * math.sin(t / 2.5), 3)
            self._signals["sensor_level_y"] = round(2.8 * math.cos(t / 3.1), 3)
            self._signals["sensor_level_z"] = round(1.0 + 0.02 * math.sin(t / 2.0), 3)
            self._signals["sensor_temp_c"] = round(24.0 + 0.6 * math.sin(t / 12.0), 2)
            self._signals["node_uptime_ms"] = elapsed_ms
            self._signals["node_name"] = self.node_name
            self._signals["tsp_clients"] = client_count

            # Symulowany rzadki alarm wstrząsu tylko jako zdarzenie diagnostyczne.
            if random.random() < 0.0005:
                self._signals["sensor_shock_state"] = 1
                self._urgent_queue.append(
                    urgent_event("sensor_shock_state", 1, "shock_detected", PRIORITY_SAFETY)
                )
            elif self._signals.get("sensor_shock_state") == 1 and random.random() < 0.1:
                self._signals["sensor_shock_state"] = 0

    def pop_urgent_events(self) -> list[Dict[str, Any]]:
        with self._lock:
            items = list(self._urgent_queue)
            self._urgent_queue.clear()
            return items

    def call_action(self, name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        with self._lock:
            if name == "clap":
                count = int(self._signals.get("clap_event", 0)) + 1
                self._signals["clap_event"] = count
                self._signals["take_marker"] = f"CLAP_{count:03d}"
                self._urgent_queue.append(
                    urgent_event("clap_event", count, "operator_clap", PRIORITY_MARKER, marker=self._signals["take_marker"])
                )
                return {"ok": True, "action": name, "clap_event": count, "take_marker": self._signals["take_marker"]}
            if name == "nextion_refresh_page":
                page = str(self._signals.get("nextion_page", "take_main"))
                self._urgent_queue.append(urgent_event("nextion_page", page, "refresh_page", PRIORITY_HIGH))
                return {"ok": True, "action": name, "page": page}
            if name == "stop":
                self._signals["transport_state"] = "STOP"
                self._urgent_queue.append(urgent_event("transport_state", "STOP", "operator_stop", PRIORITY_SAFETY))
                return {"ok": True, "action": name, "transport_state": "STOP"}
            return {"ok": False, "error": "unknown_action", "action": name}

    def state_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "node": self.node_name,
                "signal_count": len(self._catalog),
                "active_mode": self._signals.get("active_mode"),
                "transport_state": self._signals.get("transport_state"),
                "nextion_page": self._signals.get("nextion_page"),
                "uptime_ms": self._signals.get("node_uptime_ms"),
            }

    @staticmethod
    def _format_timecode(ms: int, fps: int = 25) -> str:
        total_seconds = ms // 1000
        frame = int((ms % 1000) / (1000 / fps))
        seconds = total_seconds % 60
        minutes = (total_seconds // 60) % 60
        hours = total_seconds // 3600
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame:02d}"
