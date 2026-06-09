"""
TARZAN PARcore — wykonawczy rdzeń PAR bez UI.

ZASADA:
- to nie jest nowy PAR i nie jest drugi model logiki,
- rdzeń zachowuje wykonawcze tory obecnego PAR: SignalBus, TSP, TAKE, RRP,
  SOK, sensory, automatyka/P37, akcje osi,
- GUI toolkit, layout, canvas, widgety i menu zostają poza tym plikiem,
- PAR-GUI, PARtext, Nextion 7, EHR i KHR mają wołać te same metody tej klasy.

Źródła transplantacji:
- editor/PAR/tarzanParBridge.py       → TSP / SignalBus / TAKE / snapshot / command bridge
- editor/PAR/tarzanParPanels.py       → akcje osi / RRP / SOK / sensory / automatyka / P37
- editor/PAR/tarzanParTakePlayer.py   → odtwarzacz TAKE
- editor/PAR/tarzanParProtocolMapper.py → TAKE → SignalBus
"""
from __future__ import annotations

import csv
import json
import re
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    from core.tarzanSignalBus import TarzanSignalBus, get_signal_bus
except Exception:  # pragma: no cover
    TarzanSignalBus = Any  # type: ignore
    def get_signal_bus(mode: str = "TEST") -> Any:  # type: ignore
        raise

try:
    from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
except Exception:  # pragma: no cover
    CZAS_PROBKOWANIA_MS = 10

try:
    from core.TSP.tarzanTspClient import TarzanTspClient
    from core.TSP.tarzanTspConfig import TSP_MINI_PC_HOST
except Exception:  # pragma: no cover
    TarzanTspClient = None  # type: ignore
    TSP_MINI_PC_HOST = "127.0.0.1"

try:
    from hardware.tarzanNextion.bridge import TarzanNextionBridge
except Exception:  # pragma: no cover
    TarzanNextionBridge = None  # type: ignore

try:
    from core.tarzanMode import TarzanModeLogic
except Exception:  # pragma: no cover
    TarzanModeLogic = None  # type: ignore

try:
    from core.tarzanSnajper import TarzanSnajper, NextionPhysicalSnajperAdapter
except Exception:  # pragma: no cover
    TarzanSnajper = None  # type: ignore
    NextionPhysicalSnajperAdapter = None  # type: ignore


# ============================================================================
# 1:1 z obecnego PAR: mapa osi i kanałów wykonawczych paneli.
# ============================================================================

AXIS_ALIASES: Dict[str, str] = {
    "0": "CAM_H", "CAM_H": "CAM_H", "CAMERA_H": "CAM_H", "POZIOM_KAMERY": "CAM_H",
    "1": "CAM_V", "CAM_V": "CAM_V", "CAMERA_V": "CAM_V", "PION_KAMERY": "CAM_V",
    "2": "CAM_F", "CAM_F": "CAM_F", "FOCUS": "CAM_F", "FOKUS": "CAM_F",
    "3": "ARM_T", "ARM_T": "ARM_T", "CAM_T": "ARM_T", "TILT": "ARM_T", "POCHYL": "ARM_T", "POCHYŁ": "ARM_T",
    "4": "ARM_H", "ARM_H": "ARM_H", "RAMIE_H": "ARM_H", "POZIOM": "ARM_H",
    "5": "ARM_V", "ARM_V": "ARM_V", "RAMIE_V": "ARM_V", "PION": "ARM_V",
    "6": "DRON", "DRON": "DRON",
}

AXIS_INDEX: Dict[str, int] = {
    "CAM_H": 0,
    "CAM_V": 1,
    "CAM_F": 2,
    "ARM_T": 3,
    "ARM_H": 4,
    "ARM_V": 5,
    "DRON": 6,
}

AXIS_SIGNAL_BINDINGS: Dict[str, Dict[str, List[str]]] = {
    "CAM_H": {"step": ["axis_cam_h_step", "axis_cam_h_auto_step", "axis_cam_h_rec_step"], "dir": ["axis_cam_h_dir", "axis_cam_h_auto_dir", "axis_cam_h_rec_dir"], "en": ["axis_cam_h_en"], "pulses": ["axis_cam_h_pulses"], "pos": ["axis_cam_h_pos"], "left": ["sensor_cam_h_limit_left"], "right": ["sensor_cam_h_limit_right"]},
    "CAM_V": {"step": ["axis_cam_v_step", "axis_cam_v_auto_step", "axis_cam_v_rec_step"], "dir": ["axis_cam_v_dir", "axis_cam_v_auto_dir", "axis_cam_v_rec_dir"], "en": ["axis_cam_v_en"], "pulses": ["axis_cam_v_pulses"], "pos": ["axis_cam_v_pos"], "left": ["sensor_cam_v_limit_down"], "right": ["sensor_cam_v_limit_up"]},
    "ARM_T": {"step": ["axis_arm_t_step", "axis_arm_t_auto_step", "axis_arm_t_rec_step"], "dir": ["axis_arm_t_dir", "axis_arm_t_auto_dir", "axis_arm_t_rec_dir"], "en": ["axis_arm_t_en"], "pulses": ["axis_arm_t_pulses"], "pos": ["axis_arm_t_pos"], "left": ["sensor_cam_t_limit"], "right": ["sensor_cam_t_limit"]},
    "CAM_F": {"step": ["axis_cam_f_step", "axis_cam_f_auto_step", "axis_cam_f_rec_step"], "dir": ["axis_cam_f_dir", "axis_cam_f_auto_dir", "axis_cam_f_rec_dir"], "en": ["axis_cam_f_en"], "pulses": ["axis_cam_f_pulses"], "pos": ["axis_cam_f_pos"], "left": [], "right": []},
    "ARM_H": {"step": ["axis_arm_h_step", "axis_arm_h_auto_step", "axis_arm_h_rec_step"], "dir": ["axis_arm_h_dir", "axis_arm_h_auto_dir", "axis_arm_h_rec_dir"], "en": ["axis_arm_h_en"], "pulses": ["axis_arm_h_pulses"], "pos": ["axis_arm_h_pos"], "left": ["sensor_arm_h_limit_left"], "right": ["sensor_arm_h_limit_right"]},
    "ARM_V": {"step": ["axis_arm_v_step", "axis_arm_v_auto_step", "axis_arm_v_rec_step"], "dir": ["axis_arm_v_dir", "axis_arm_v_auto_dir", "axis_arm_v_rec_dir"], "en": ["axis_arm_v_en"], "pulses": ["axis_arm_v_pulses"], "pos": ["axis_arm_v_pos"], "left": ["sensor_arm_v_limit_down"], "right": ["sensor_arm_v_limit_up"]},
    "DRON": {"step": ["axis_dron_step"], "dir": ["axis_dron_dir"], "en": ["axis_dron_en"], "pulses": ["axis_dron_pulses"], "pos": ["axis_dron_pos"], "left": [], "right": []},
}

SOK_MODE_MAP: Dict[str, Tuple[List[str], List[str]]] = {
    "PAN":    (["axis_cam_h_dir"], ["axis_cam_h_step"]),
    "TILT":   (["axis_cam_v_dir"], ["axis_cam_v_step"]),
    "FOKUS":  (["axis_cam_f_dir"], ["axis_cam_f_step"]),
    "FOCUS":  (["axis_cam_f_dir"], ["axis_cam_f_step"]),
    "POCHYŁ": (["axis_arm_t_dir"], ["axis_arm_t_step"]),
    "POCHYL": (["axis_arm_t_dir"], ["axis_arm_t_step"]),
    "POZIOM": (["axis_arm_h_dir"], ["axis_arm_h_step"]),
    "PION":   (["axis_arm_v_dir"], ["axis_arm_v_step"]),
}

SENSOR_GROUPS: Dict[str, List[str]] = {
    "xyz": ["sensor_xyz", "sensor_level_x", "sensor_level_y", "sensor_level_z", "level_x", "level_y", "level_z"],
    "level": ["sensor_xyz", "sensor_level_x", "sensor_level_y", "sensor_level_z", "level_x", "level_y", "level_z"],
    "temperature": ["sensor_temp_c", "temperature_c", "par_temp_c", "temp_c", "rec_p44_free_keyboard_old"],
    "temp": ["sensor_temp_c", "temperature_c", "par_temp_c", "temp_c", "rec_p44_free_keyboard_old"],
    "light": ["sensor_light_lux", "light_lux", "par_light_lux", "play_p45_rrp_pot_h"],
    "bh1750": ["sensor_light_lux", "light_lux", "par_light_lux"],
    "limits": ["sensor_limits_status", "limit_state", "sensor_arm_h_limit_left", "sensor_arm_h_limit_right", "sensor_arm_v_limit_down", "sensor_arm_v_limit_up"],
    "shock": ["sensor_shock_state", "shock_state"],
    "laser": ["sensor_laser_set", "laser_state"],
    "rrp": ["sensor_rrp_pot_h", "sensor_rrp_pot_v", "play_p45_rrp_pot_h", "play_p47_rrp_pot_v"],
}


# ============================================================================
# Snajper headless — transplant zasad z tarzanParPanels.py bez widgetów/UI.
# ============================================================================

TARZAN_SNAJPER_PAR_SECTIONS: Dict[str, set[str]] = {
    "rrp": {"par_rrp_p1_val", "par_rrp_p2_val", "par_rrp_p1_dir", "par_rrp_p2_dir", "par_rrp_p1_sens", "par_rrp_p2_sens", "par_rrp_p1_axis", "par_rrp_p2_axis"},
    "motor_cards": {"axis_0_value", "axis_1_value", "axis_2_value", "axis_3_value", "axis_4_value", "axis_5_value", "axis_cam_v_pulses", "axis_cam_t_pulses", "axis_cam_f_pulses", "axis_cam_h_pulses", "axis_arm_h_pulses", "axis_arm_v_pulses"},
    "step_dir_preview": {"axis_0_step", "axis_1_step", "axis_2_step", "axis_3_step", "axis_4_step", "axis_5_step", "axis_0_dir", "axis_1_dir", "axis_2_dir", "axis_3_dir", "axis_4_dir", "axis_5_dir", "step_dir_stream", "protocol_tick", "take_timecode"},
    "temperature": {"sensor_temp_c", "temperature_c", "par_temp_c"},
    "light": {"sensor_light_lux", "light_lux", "par_light_lux"},
    "xyz": {"sensor_xyz", "sensor_level_x", "sensor_level_y", "sensor_level_z", "level_x", "level_y", "level_z"},
    "limits": {"sensor_limits_status", "limit_state", "krańcówki", "krancowki"},
    "shock_laser": {"sensor_shock_state", "sensor_laser_set", "shock_state", "laser_state"},
    "sok": {"sok_pan", "sok_tilt", "sok_focus", "sok_cam"},
    "cnc": {"cnc_status", "cnc_signal", "cnc_step", "cnc_dir"},
    "logs": {"system_status", "log_event", "par_log"},
}

_LINKED_SIGNAL_GROUPS: Dict[str, List[str]] = {
    "limit_mass_reg_add": ["limit_mass_reg_add", "par_mass_reg_limit_add"],
    "limit_mass_reg_remove": ["limit_mass_reg_remove", "par_mass_reg_limit_remove"],
    "axis_arm_h_en": ["axis_arm_h_en", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "ui_action_led": ["ui_action_led", "par_lamp_auto_active"],
    "sensor_shock_state": ["sensor_shock_state", "par_shock_sensor_state"],
}

_RRP_NEXTION_AXIS_ORDER: Tuple[str, ...] = ("cam_v", "arm_t", "cam_f", "cam_h", "arm_h", "arm_v")
_RRP_CANON_AXIS_TO_PAR: Dict[str, str] = {
    "cam_v": "CAM_V", "arm_t": "ARM_T", "cam_f": "CAM_F", "cam_h": "CAM_H", "arm_h": "ARM_H", "arm_v": "ARM_V"
}
_RRP_REC_AUTO_EN_SIGNALS = {"axis_cam_v_rec_step", "axis_arm_t_rec_step", "axis_cam_f_rec_step", "axis_cam_h_rec_step", "axis_arm_h_rec_step", "axis_arm_v_rec_step"}
_RRP_ALL_EN_SIGNALS = {name for bind in AXIS_SIGNAL_BINDINGS.values() for name in bind.get("en", [])}

class TarzanStepDirMultiSnajperHeadless:
    """Headless odpowiednik TarzanStepDirMultiSnajper z PAR Panels."""
    AXIS_ORDER = ("cam_h", "cam_v", "cam_t", "cam_f", "arm_h", "arm_v", "arm_t", "global")

    def __init__(self, core: Any) -> None:
        self.core = core
        self.last_values: Dict[str, str] = {}
        self.axis_state: Dict[str, Dict[str, Any]] = {}
        self._in_fire = False

    def is_step_dir_signal(self, name: str) -> bool:
        s = str(name).lower()
        return (
            "step" in s or "_stp" in s or "dir" in s or "ctr" in s or
            "pulse" in s or "puls" in s or s.endswith("_pos") or "_pos" in s or
            s.startswith("axis_") or s.startswith("par_") or s.startswith("cnc_") or
            s.startswith("play_") or s.startswith("rec_")
        )

    def fire(self, name: str, value: Any) -> Optional[Dict[str, Any]]:
        if self._in_fire or not self.is_step_dir_signal(name):
            return None
        key = str(name)
        normalized = str(value)
        if self.last_values.get(key) == normalized:
            return None
        self.last_values[key] = normalized
        axis = self._axis_from_signal(key)
        kind = self._kind_from_signal(key)
        state = self.axis_state.setdefault(axis, {})
        state[kind] = value
        state["last_signal"] = key
        state["last_value"] = value
        packet = {"axis": axis, "kind": kind, "signal": key, "value": value, "state": dict(state)}
        self._in_fire = True
        try:
            self.core.force_signal("snajper_step_dir_last", json.dumps(packet, ensure_ascii=False), source="PARCORE_STEPDIR_SNAJPER")
            self.core.snajper_fire_log_take_nextion("step_dir_preview", packet)
        finally:
            self._in_fire = False
        return packet

    def _axis_from_signal(self, name: str) -> str:
        s = str(name).lower()
        aliases = (
            ("cam_h", ("cam_h", "camera_h", "pozioma_kamery")),
            ("cam_v", ("cam_v", "camera_v", "pionowa_kamery")),
            ("cam_t", ("cam_t", "tilt", "pochyl")),
            ("cam_f", ("cam_f", "focus", "ostrosc", "ostrość")),
            ("arm_h", ("arm_h", "ramie_h", "pozioma_ramienia")),
            ("arm_v", ("arm_v", "ramie_v", "pionowa_ramienia")),
            ("arm_t", ("arm_t", "arm_tilt", "ramie_tilt")),
        )
        for axis, keys in aliases:
            if any(k in s for k in keys):
                return axis
        m = re.search(r"axis[_-]?(\d+)", s)
        if m:
            idx = int(m.group(1))
            if 0 <= idx < len(self.AXIS_ORDER):
                return self.AXIS_ORDER[idx]
            return f"axis_{idx}"
        return "global"

    def _kind_from_signal(self, name: str) -> str:
        s = str(name).lower()
        if "dir" in s:
            return "dir"
        if "ctr" in s:
            return "ctr"
        if "rec_step" in s:
            return "rec_step"
        if "auto_step" in s:
            return "auto_step"
        if "step" in s or "_stp" in s:
            return "step"
        if "pulse" in s or "puls" in s:
            return "pulses"
        if "_pos" in s or s.endswith("pos"):
            return "pos"
        return "value"

class TarzanParSectionSnajperHeadless:
    """Headless odpowiednik TarzanParSectionSnajper z PAR Panels."""
    def __init__(self, core: Any) -> None:
        self.core = core
        self.last_values: Dict[str, str] = {}
        self.signal_to_sections: Dict[str, set[str]] = {}
        self._in_fire = False
        for section, signals in TARZAN_SNAJPER_PAR_SECTIONS.items():
            for signal in signals:
                self.signal_to_sections.setdefault(signal, set()).add(section)

    def fire(self, signal_name: str, value: Any) -> set[str]:
        if self._in_fire:
            return set()
        key = str(signal_name)
        normalized = str(value)
        if self.last_values.get(key) == normalized:
            return set()
        self.last_values[key] = normalized
        sections = set(self.signal_to_sections.get(key, set()))
        sections.update(self._infer_sections(key))
        self._in_fire = True
        try:
            for section in sorted(sections):
                self.update_section(section, key, value)
        finally:
            self._in_fire = False
        return sections

    def _infer_sections(self, signal_name: str) -> set[str]:
        s = str(signal_name).lower()
        sections: set[str] = set()
        if "rrp" in s or "p1" in s or "p2" in s:
            sections.add("rrp")
        if ("axis" in s or "os_" in s or "step" in s or "_stp" in s or "dir" in s or "_ctr" in s or "ctr" in s or "pulse" in s or "puls" in s or "cnc_" in s or "play_" in s):
            sections.add("motor_cards")
            sections.add("step_dir_preview")
        if "timecode" in s or "take_time" in s or "protocol_tick" in s:
            sections.add("step_dir_preview")
        if "temp" in s:
            sections.add("temperature")
        if "light" in s or "lux" in s or "bh1750" in s:
            sections.add("light")
        if "xyz" in s or "level" in s or "mma" in s:
            sections.add("xyz")
        if "limit" in s or "kranc" in s or "krańc" in s:
            sections.add("limits")
        if "shock" in s or "shok" in s or "laser" in s:
            sections.add("shock_laser")
        if "sok" in s:
            sections.add("sok")
        if "cnc" in s:
            sections.add("cnc")
            sections.add("step_dir_preview")
        if "status" in s or "log" in s:
            sections.add("logs")
        return sections

    def update_section(self, section: str, signal_name: str, value: Any) -> Dict[str, Any]:
        method = getattr(self.core, f"_snajper_update_section_{section}", None)
        if callable(method):
            try:
                return method(signal_name, value)  # type: ignore[misc]
            except TypeError:
                return method()  # type: ignore[misc]
        return self.core._snajper_update_section_generic(section, signal_name, value)


# ============================================================================
# publiczny kontrakt prostych wejść PARcore.
# To jest lista metod, które wolno wołać z PAR-GUI / PARtext / Nextion 7 / EHR / KHR.
# Nie zawiera GUI toolkita, layoutu, canvasów, widgetów ani menu PAR.
# ============================================================================

PARCORE_PUBLIC_ENTRYPOINTS: Tuple[str, ...] = (
    "set_mode",
    "rrp_set_axis",
    "rrp_set_dir",
    "rrp_set_speed",
    "rrp_set_sens",
    "take_load",
    "take_play",
    "take_pause",
    "take_stop",
    "test_axis",
    "sok_set",
    "sensor_read",
    "sensor_test",
    "manual_record_arm",
    "set_signal",
    "snapshot",
)

PARCORE_FORBIDDEN_UI_MARKERS: Tuple[str, ...] = (
    "gui_toolkit", "gui_widgets", "rysowanie_UI", "przycisk_UI", "ramka_UI", "menu_UI", "layout_pack(", "layout_grid(", "layout_place(",
)


# ============================================================================
# wszyscy klienci trafiają do tych samych metod PARcore.
# PAR-GUI i EHR/KHR zdalnie idą przez TSP/JSON, PARtext i Nextion 7 lokalnie.
# To nadal jeden plik wykonawczy, bez UI i bez drugiego modelu logiki.
# ============================================================================

PARCORE_CLIENT_ROUTES: Dict[str, str] = {
    "PAR-GUI": "TSP -> PARcore.route_client_command('PAR-GUI', ...) -> call_action(...) / public method",
    "PARtext": "local text -> PARcore.route_client_command('PARtext', ...) -> call_action(...) / public method",
    "Nextion7": "local UART/event -> PARcore.route_client_command('Nextion7', ...) -> dispatch_nextion7(...)",
    "EHR-GUI": "TSP TAKE/payload -> PARcore.route_client_command('EHR-GUI', ...) -> take_load/take_play/TAKE mapper",
    "KHR-GUI": "TSP correction/payload -> PARcore.route_client_command('KHR-GUI', ...) -> set_signal/call_action",
}

PARCORE_CLIENT_ALIASES: Dict[str, str] = {
    "par": "PAR-GUI",
    "par-gui": "PAR-GUI",
    "par_gui": "PAR-GUI",
    "gui": "PAR-GUI",
    "partext": "PARtext",
    "par-text": "PARtext",
    "text": "PARtext",
    "cli": "PARtext",
    "nextion7": "Nextion7",
    "nextion_7": "Nextion7",
    "n7": "Nextion7",
    "ehr": "EHR-GUI",
    "ehr-gui": "EHR-GUI",
    "ehr_gui": "EHR-GUI",
    "khr": "KHR-GUI",
    "khr-gui": "KHR-GUI",
    "khr_gui": "KHR-GUI",
}


# ============================================================================
# TAKE mapper — transplant z tarzanParProtocolMapper.py
# ============================================================================

@dataclass(frozen=True)
class AxisProtocolMap:
    prefix: str
    axis_key: str
    label: str
    step_signals: List[str] = field(default_factory=list)
    dir_signals: List[str] = field(default_factory=list)
    enable_signals: List[str] = field(default_factory=list)
    event_signals: List[str] = field(default_factory=list)


class TarzanParProtocolMapper:
    """Tłumaczy wiersz TAKE/EHR na paczkę sygnałów SignalBus."""

    def __init__(self, known_signal_names: Iterable[str]) -> None:
        self.known = set(known_signal_names)
        self.axis_maps: Dict[str, AxisProtocolMap] = self._build_maps()

    def _build_maps(self) -> Dict[str, AxisProtocolMap]:
        maps = [
            AxisProtocolMap("CAM_H", "cam_h", "oś pozioma kamery", ["axis_cam_h_step"], ["axis_cam_h_dir"]),
            AxisProtocolMap("CAM_V", "cam_v", "oś pionowa kamery", ["axis_cam_v_step"], ["axis_cam_v_dir"]),
            AxisProtocolMap("CAM_T", "cam_t", "oś pochyłu kamery", ["axis_cam_t_step", "axis_arm_t_step"], ["axis_cam_t_dir", "axis_arm_t_dir"]),
            AxisProtocolMap("CAM_F", "cam_f", "oś ostrości kamery", ["axis_cam_f_step"], ["axis_cam_f_dir"]),
            AxisProtocolMap("ARM_H", "arm_h", "oś pozioma ramienia", ["axis_arm_h_step"], ["axis_arm_h_dir"], ["axis_arm_h_en"]),
            AxisProtocolMap("ARM_V", "arm_v", "oś pionowa ramienia", ["axis_arm_v_step"], ["axis_arm_v_dir"], ["axis_arm_v_en"]),
            AxisProtocolMap("DRON", "dron", "DRON", ["axis_dron_step"], ["axis_dron_dir"], [], ["ui_drone_release"]),
        ]
        return {m.prefix: m for m in maps}

    def map_row(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        time_ms = self._int(row.get("TIME_MS", 0))
        out["TAKE_TIME_MS"] = time_ms
        out["take_time_ms"] = time_ms
        out["take_timecode"] = time_ms

        for prefix, axis in self.axis_maps.items():
            step_col = f"{prefix}_STEP"
            dir_col = f"{prefix}_DIR"
            event_col = f"{prefix}_EVENT"

            if step_col in row:
                step_value = self._bit(row.get(step_col))
                out[f"TAKE_{step_col}"] = step_value
                for name in axis.step_signals:
                    out[name] = step_value

            if dir_col in row:
                dir_value = self._bit(row.get(dir_col))
                out[f"TAKE_{dir_col}"] = dir_value
                for name in axis.dir_signals:
                    out[name] = dir_value

            if event_col in row:
                event_raw = row.get(event_col, "")
                event_value = 1 if str(event_raw).strip() else 0
                out[f"TAKE_{event_col}"] = event_value
                for name in axis.event_signals:
                    out[name] = event_value

            if (step_col in row or dir_col in row) and axis.enable_signals:
                for name in axis.enable_signals:
                    out[name] = 1
        return out

    def map_take_columns(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for prefix, axis in self.axis_maps.items():
            result[f"{prefix}_STEP"] = [f"TAKE_{prefix}_STEP"] + axis.step_signals
            result[f"{prefix}_DIR"] = [f"TAKE_{prefix}_DIR"] + axis.dir_signals
            result[f"{prefix}_EVENT"] = [f"TAKE_{prefix}_EVENT"] + axis.event_signals
        return result


    def _pick(self, names: Sequence[str], fallback: str = "") -> str:
        """Transplant helper z mappera PAR: wybiera pierwszy znany sygnał z listy.

        Mapper nie wymyśla nowego sygnału, tylko preferuje nazwę istniejącą w SignalBus.
        Gdy mapa historyczna zawiera aliasy, ta metoda zachowuje zasadę wyboru
        oryginalnego tarzanParProtocolMapper.py.
        """
        for name in names:
            if name in self.known:
                return name
        if names:
            return str(names[0])
        return str(fallback or "")

    def _bit(self, value: Any) -> int:
        return 1 if value in {1, True, "1", "true", "TRUE", "on", "ON"} else 0

    def _int(self, value: Any) -> int:
        try:
            return int(float(value))
        except Exception:
            return 0


# ============================================================================
# TAKE player — headless transplant z tarzanParTakePlayer.py
# ============================================================================

@dataclass
class TarzanTakeData:
    path: Path
    header: Dict[str, str] = field(default_factory=dict)
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, str]] = field(default_factory=list)

    @property
    def duration_ms(self) -> int:
        if not self.rows:
            return 0
        try:
            return int(float(self.rows[-1].get("TIME_MS", 0)))
        except Exception:
            return 0

    @property
    def metadata(self) -> Dict[str, str]:
        # Zgodność 1:1 z tarzanParBridge.load_take(), gdzie payload używa data.metadata.
        return self.header

    def duration_ms_value(self) -> int:
        # Alias bezpieczny dla kodu, który traktował duration_ms jak metodę.
        return self.duration_ms


class _TimerScheduler:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._timers: Dict[int, threading.Timer] = {}
        self._counter = 0

    def after(self, delay_ms: int, callback: Callable[[], Any]) -> int:
        with self._lock:
            self._counter += 1
            ident = self._counter
            timer = threading.Timer(max(0.0, delay_ms / 1000.0), self._run, args=(ident, callback))
            timer.daemon = True
            self._timers[ident] = timer
            timer.start()
            return ident

    def _run(self, ident: int, callback: Callable[[], Any]) -> None:
        with self._lock:
            self._timers.pop(ident, None)
        callback()

    def after_cancel(self, ident: Any) -> None:
        with self._lock:
            timer = self._timers.pop(int(ident), None) if ident is not None else None
        if timer:
            timer.cancel()


class TarzanParTakePlayer:
    def __init__(self, bus: TarzanSignalBus, mapper: TarzanParProtocolMapper) -> None:
        self.bus = bus
        self.mapper = mapper
        self.take: Optional[TarzanTakeData] = None
        self.index = 0
        self.playing = False
        self.loop = False
        self.speed = 1.0
        self._after: Optional[Callable[[int, Callable[[], Any]], Any]] = None
        self._after_cancel: Optional[Callable[[Any], Any]] = None
        self._after_id: Any = None
        self.on_row: Optional[Callable[[Dict[str, str]], None]] = None

    def set_scheduler(self, after: Callable[[int, Callable[[], Any]], Any], after_cancel: Callable[[Any], Any]) -> None:
        self._after = after
        self._after_cancel = after_cancel

    def load(self, path: str | Path) -> TarzanTakeData:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        take = TarzanTakeData(path=path)
        raw = path.read_text(encoding="utf-8", errors="replace")
        header_lines: List[str] = []
        protocol_lines: List[str] = []
        in_protocol = False
        for line in raw.splitlines():
            stripped = line.strip("\ufeff")
            if not stripped:
                continue
            if stripped.startswith("#"):
                header_lines.append(stripped.lstrip("#").strip())
                continue
            if "TIME_MS" in stripped and ";" in stripped:
                in_protocol = True
            if in_protocol:
                protocol_lines.append(stripped)
        for line in header_lines:
            if "=" in line:
                k, v = line.split("=", 1)
                take.header[k.strip()] = v.strip()
        if protocol_lines:
            reader = csv.DictReader(protocol_lines, delimiter=";")
            take.columns = list(reader.fieldnames or [])
            take.rows = [dict(row) for row in reader]

        self.stop(reset_to_zero=False, log_stop=False)
        self.take = take
        self.index = 0
        self.bus.loaded_take_path = str(path)
        self.bus.force_signal("take_number", path.name, source="TAKE_LOAD")
        self.bus.force_signal("loaded_take_path", str(path), source="TAKE_LOAD")
        self.bus.force_signal("take_status", "LOADED", source="TAKE_LOAD")
        self.bus.set_take_time(0)
        self.bus.log("TAKE", f"Załadowano TAKE: {path.name}, rows={len(take.rows)}, duration={take.duration_ms} ms")
        return take

    def unload(self) -> None:
        self.stop(reset_to_zero=False)
        self.take = None
        self.index = 0
        self.bus.loaded_take_path = None
        self.bus.force_signal("take_number", "BRAK", source="TAKE_UNLOAD")
        self.bus.force_signal("loaded_take_path", "", source="TAKE_UNLOAD")
        self.bus.force_signal("take_status", "EMPTY", source="TAKE_UNLOAD")
        self.bus.set_take_time(0)
        self.bus.log("TAKE", "Odłączono TAKE")

    def step_to_index(self, index: int) -> Optional[Dict[str, str]]:
        if not self.take or not self.take.rows:
            return None
        self.index = max(0, min(int(index), len(self.take.rows) - 1))
        row = self.take.rows[self.index]
        self.apply_row(row)
        return row

    def step_time(self, time_ms: int) -> Optional[Dict[str, str]]:
        if not self.take or not self.take.rows:
            return None
        idx = int(round(int(time_ms) / max(1, CZAS_PROBKOWANIA_MS)))
        return self.step_to_index(idx)

    def apply_row(self, row: Dict[str, str]) -> None:
        time_ms = self._row_time(row)
        self.bus.set_take_time(time_ms)
        mapped = self.mapper.map_row(row)
        self.bus.write_many_outputs(mapped, source="TAKE", time_ms=time_ms)
        if self.on_row:
            self.on_row(row)

    def play(self) -> None:
        if not self.take or not self.take.rows or self.playing:
            return
        if self._after is None:
            self.bus.log("TAKE", "PLAY zablokowany: brak schedulera")
            return
        self.playing = True
        self.bus.force_signal("take_status", "PLAY", source="TAKE_PLAY")
        self.bus.log("TAKE", "PLAY")
        self._schedule_next(delay_ms=0)

    def pause(self) -> None:
        if not self.playing:
            return
        self.playing = False
        self._cancel_after()
        self.bus.force_signal("take_status", "PAUSE", source="TAKE_PAUSE")
        self.bus.log("TAKE", "PAUSE")

    def stop(self, *, reset_to_zero: bool = True, log_stop: bool = True) -> None:
        self.playing = False
        self._cancel_after()
        self.index = 0
        if reset_to_zero and self.take and self.take.rows:
            self.apply_row(self.take.rows[0])
        self.bus.force_signal("take_status", "STOP" if self.take else "EMPTY", source="TAKE_STOP")
        if log_stop:
            self.bus.log("TAKE", "STOP")

    def _schedule_next(self, delay_ms: Optional[int] = None) -> None:
        if not self.playing or self._after is None:
            return
        delay = self._sample_delay_ms() if delay_ms is None else max(0, int(delay_ms))
        self._after_id = self._after(delay, self._tick)

    def _cancel_after(self) -> None:
        if self._after_id is not None and self._after_cancel is not None:
            try:
                self._after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def _tick(self) -> None:
        self._after_id = None
        if not self.playing or not self.take or not self.take.rows:
            return
        if self.index >= len(self.take.rows):
            if self.loop:
                self.index = 0
            else:
                self.playing = False
                self.bus.force_signal("take_status", "END", source="TAKE_END")
                self.bus.log("TAKE", "KONIEC")
                return
        row = self.take.rows[self.index]
        self.apply_row(row)
        self.index += 1
        self._schedule_next()

    def _sample_delay_ms(self) -> int:
        try:
            speed = max(0.01, float(self.speed))
        except Exception:
            speed = 1.0
        return max(1, int(round(CZAS_PROBKOWANIA_MS / speed)))

    def _row_time(self, row: Dict[str, str]) -> int:
        try:
            return int(float(row.get("TIME_MS", 0)))
        except Exception:
            return 0




# ============================================================================
# PAR compatibility adapters — lekkie zgodności z tarzanParState.py i
# tarzanParSignalsAdapter.py. To nie jest nowa prawda: stan nadal siedzi w
# SignalBus, a adaptery tylko utrzymują stare nazwy/metody dla Snajpera/PAR.
# ============================================================================

class TarzanParStateCompat:
    """Headless adapter zgodności z editor/PAR/tarzanParState.py."""
    def __init__(self, core: Any) -> None:
        self.core = core
        self._subscribers: Dict[str, List[Callable[[str, Any], Any]]] = {}
        self._logs: List[str] = []
        self._log_limit = 300

    def _default(self, name: str = "", default: Any = None) -> Any:
        if default is not None:
            return default
        key = str(name or "").lower()
        if key.endswith("_state") or key.endswith("_status"):
            return ""
        if key.endswith("_text") or key.endswith("_preview") or key.endswith("_log"):
            return ""
        return 0

    def subscribe(self, name: str, callback: Callable[[str, Any], Any]) -> bool:
        if not callable(callback):
            return False
        self._subscribers.setdefault(str(name), []).append(callback)
        return True

    def notify(self, name: str, value: Any = None) -> int:
        key = str(name)
        if value is None:
            value = self.get(key)
        callbacks = list(self._subscribers.get(key, [])) + list(self._subscribers.get("*", []))
        count = 0
        for callback in callbacks:
            try:
                callback(key, value)
                count += 1
            except TypeError:
                try:
                    callback(value)
                    count += 1
                except Exception:
                    pass
            except Exception:
                pass
        return count

    def get(self, name: str, default: Any = None) -> Any:
        return self.core._bus_read(str(name), self._default(str(name), default))

    def log(self, source: str, message: Any = "") -> str:
        if message == "":
            line = str(source)
        else:
            line = f"{source}: {message}"
        self._logs.append(line)
        if len(self._logs) > self._log_limit:
            self._logs = self._logs[-self._log_limit:]
        try:
            self.core.log_par_event(line, source=str(source))
        except Exception:
            pass
        return line


class TarzanParSignalsAdapterCompat:
    """Headless adapter zgodności z editor/PAR/tarzanParSignalsAdapter.py."""
    def __init__(self, core: Any) -> None:
        self.core = core
        self._signals: Dict[str, Dict[str, Any]] = {}

    def _from_tarzan_signal(self, signal: Any) -> Dict[str, Any]:
        if isinstance(signal, dict):
            name = str(signal.get("name") or signal.get("signal") or "")
            data = dict(signal)
        else:
            name = str(getattr(signal, "name", "") or getattr(signal, "nazwa", "") or signal)
            data = {}
            for attr in ("name", "label", "group", "typ", "direction", "is_input", "default"):
                if hasattr(signal, attr):
                    try:
                        data[attr] = getattr(signal, attr)
                    except Exception:
                        pass
        data.setdefault("name", name)
        data.setdefault("label", data.get("opis") or name)
        data.setdefault("group", data.get("grupa") or data.get("section") or "signals")
        data.setdefault("value", self.core._bus_read(name, data.get("default", 0)))
        return data

    def load_all_signals(self) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        names: List[str] = []
        try:
            names = list(self.core.bus.names())
        except Exception:
            try:
                names = list(getattr(self.core.bus, "signals", {}).keys())
            except Exception:
                names = []
        meta = getattr(self.core.bus, "meta", {}) or {}
        for name in names:
            sig_meta = meta.get(name) if isinstance(meta, dict) else None
            data = self._from_tarzan_signal(sig_meta if sig_meta is not None else name)
            data["name"] = str(name)
            data["value"] = self.core._bus_read(str(name), data.get("default", 0))
            out[str(name)] = data
        self._signals = out
        return out

    def by_group(self, group: str) -> Dict[str, Dict[str, Any]]:
        if not self._signals:
            self.load_all_signals()
        wanted = str(group or "").lower()
        return {
            name: data for name, data in self._signals.items()
            if str(data.get("group", "")).lower() == wanted
            or str(data.get("section", "")).lower() == wanted
            or name.lower().startswith(wanted + "_")
        }

    def contains(self, name: str) -> bool:
        key = str(name)
        try:
            return bool(self.core.bus.exists(key))
        except Exception:
            if not self._signals:
                self.load_all_signals()
            return key in self._signals

# ============================================================================
# PARcore — jeden wykonawczy punkt wejścia dla PAR-GUI / PARtext / Nextion 7.
# ============================================================================

class TarzanParCore:
    def __init__(
        self,
        bus: Optional[TarzanSignalBus] = None,
        hardware_bridge: Any = None,
        mode: str = "TEST",
        tsp_host: Optional[str] = None,
        enable_tsp_client: bool = False,
        enable_headless_take_scheduler: bool = True,
        nextion_bridge: Any = None,
        enable_nextion_bridge: bool = False,
        snajper: Optional[Any] = None,
    ) -> None:
        self.bus = bus or get_signal_bus(mode)
        # Adaptery zgodności dla starego PAR i Snajpera; nie tworzą drugiej prawdy.
        self.state = TarzanParStateCompat(self)
        self.signals_adapter = TarzanParSignalsAdapterCompat(self)
        self.hardware_bridge = hardware_bridge
        self.tsp_host = tsp_host or TSP_MINI_PC_HOST
        self.enable_tsp_client = bool(enable_tsp_client)
        self.mapper = TarzanParProtocolMapper(self.bus.names())
        self.take_player = TarzanParTakePlayer(self.bus, self.mapper)
        self.scheduler = _TimerScheduler() if enable_headless_take_scheduler else None
        if self.scheduler is not None:
            self.take_player.set_scheduler(self.scheduler.after, self.scheduler.after_cancel)

        # Transplant z tarzanParBridge.py: fizyczny most Nextiona zostaje komponentem
        # wykonawczym, ale bez preview, bez canvasów i bez GUI toolkita.
        self.nextion = nextion_bridge
        if self.nextion is None and enable_nextion_bridge and TarzanNextionBridge is not None:
            try:
                self.nextion = TarzanNextionBridge(self.bus)
            except Exception as exc:
                self.nextion = None
                self._bus_log("NEXTION_ERROR", f"Bridge init failed: {exc}")

        self.tsp_client: Optional[Any] = None
        self._tsp_thread: Optional[threading.Thread] = None
        self._tsp_active = False
        self._tsp_subscribed: bool = False
        self._tsp_last_state_sync_ts = 0.0
        # 1:1 z tarzanParBridge.py — lekki start TSP, bez zalewania FAST/* na boot.
        self._tsp_boot_signals = [
            "system_state", "runtime_state", "tsp_state", "lks_state", "par_state",
            "ehr_state", "khr_state", "hardware_state", "control_owner",
            "tarzan_ready", "safety_axis_unlock", "par_last_error", "ehr_last_error",
            "tsp_fast_stats",
        ]
        self._rrp_runtime: Dict[str, Dict[str, Any]] = {
            "p1": {"selected_axis": "", "pulse_accumulator": 0.0, "last_tick_ts": time.monotonic()},
            "p2": {"selected_axis": "", "pulse_accumulator": 0.0, "last_tick_ts": time.monotonic()},
        }
        self._rrp_thread: Optional[threading.Thread] = None
        self._rrp_active = False
        # MAIN Runtime binduje tu realne komponenty miniPC.
        self.tsp_server: Optional[Any] = None
        self._nextion7_bridge: Optional[Any] = None
        self._nextion7_thread: Optional[threading.Thread] = None
        self._nextion7_active = False
        self._nextion7_event_lock = threading.RLock()
        self._nextion7_event_queue: List[Any] = []
        # Pełne headless transplanty Snajpera z PAR Panels: STEP/DIR i sekcje.
        self.step_dir_multi_snajper = TarzanStepDirMultiSnajperHeadless(self)
        self.section_snajper = TarzanParSectionSnajperHeadless(self)
        self._last_log_values: Dict[str, Any] = {}
        self._last_log_times: Dict[str, float] = {}
        self._rrp_nextion_state: Dict[str, Any] = {
            "va_p1_axis": -1, "va_p2_axis": -1, "va_p1_dir": 0, "va_p2_dir": 0,
            "va_p1_val": 0, "va_p2_val": 0, "h_p1_sens": 50, "h_p2_sens": 50,
            "rrp_rev": 0,
        }
        self._rrp_player_initialized: Dict[str, bool] = {"p1": False, "p2": False}
        # pełny headless transplant brakujących silników: MODE, Snajper systemowy,
        # NextionBridge/TDF/CLAP/TC/transport log. Nie jest to UI; to wykonawcze tory.
        self.mode_logic: Optional[Any] = None
        self._mode_running: bool = False
        self._mode_thread: Optional[threading.Thread] = None
        self.snajper: Optional[Any] = snajper
        self._snajper_adapters_registered: bool = False
        self._transport_log: List[str] = []
        self._transport_log_limit: int = 500
        self._clap_tc_running: bool = False
        self._clap_tc_start_monotonic: float = 0.0
        self._clap_tc_start_elapsed_ms: int = 0
        self._clap_tc_elapsed_ms: int = 0
        self._clap_tc_last_sent_ms: int = -1
        self._clap_tc_last_toggle_monotonic: float = 0.0
        self._tfd_metadata_cache: Dict[str, Any] = {}
        self._tfd_save_status_until: float = 0.0
        self._tfd_save_status_visible: bool = False
        self._ensure_parcore_signal_types()
        self.set_mode(mode)
        self.bus.force_signal("parcore_state", "READY", source="PARCORE_BOOT")
        self.bus.force_signal("par_state", self._par_runtime_state(), source="PARCORE_BOOT")
        self.assert_public_contract()


    # ------------------------------------------------------------------
    # publiczne proste wejścia PARcore.
    # Te metody są stabilnym kontraktem dla PAR-GUI / PARtext / Nextion 7 / EHR / KHR.
    # ------------------------------------------------------------------
    @classmethod
    def public_entrypoints(cls) -> Tuple[str, ...]:
        return PARCORE_PUBLIC_ENTRYPOINTS

    def public_api(self) -> Dict[str, Any]:
        return {
            "entrypoints": list(PARCORE_PUBLIC_ENTRYPOINTS),
            "headless": True,
            "forbidden_ui": list(PARCORE_FORBIDDEN_UI_MARKERS),
            "routes": dict(PARCORE_CLIENT_ROUTES),
            "stage5": {
                "single_dispatcher": "route_client_command(...) / handle_client_payload(...) / command_text(...)",
                "same_methods": list(PARCORE_PUBLIC_ENTRYPOINTS),
                "no_second_logic": True,
            },
        }

    def assert_public_contract(self) -> bool:
        missing = [name for name in PARCORE_PUBLIC_ENTRYPOINTS if not callable(getattr(self, name, None))]
        if missing:
            raise RuntimeError(f"PARcore public contract missing methods: {', '.join(missing)}")
        return True

    def command(self, name: str, **kwargs: Any) -> Any:
        """Najprostsze wejście tekstowe/JSON: PARtext, TSP i testy mogą wołać command(...)."""
        return self.call_action(name, kwargs)

    # ------------------------------------------------------------------
    # jeden dispatcher dla klientów.
    # PAR-GUI -> TSP -> PARcore
    # PARtext -> lokalnie -> PARcore
    # Nextion 7 -> lokalnie -> PARcore
    # EHR-GUI -> TSP -> PARcore/TAKE
    # KHR-GUI -> TSP -> PARcore/korekta
    # ------------------------------------------------------------------
    @classmethod
    def client_routes(cls) -> Dict[str, str]:
        return dict(PARCORE_CLIENT_ROUTES)

    def _normalize_client_name(self, client: Any) -> str:
        raw = str(client or "PARtext").strip()
        key = raw.lower().replace(" ", "_")
        return PARCORE_CLIENT_ALIASES.get(key, raw if raw in PARCORE_CLIENT_ROUTES else "PARtext")

    def route_client_command(self, client: str, action: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """Jeden punkt dla wszystkich klientów, bez kopiowania logiki.

        Każdy klient jest tylko źródłem komendy. Wykonanie zawsze przechodzi
        przez istniejące metody PARcore: call_action(...), dispatch_nextion7(...),
        take_load/play/stop albo set_signal(...).
        """
        client_name = self._normalize_client_name(client)
        payload = dict(args or {})
        self.force_signal("parcore_last_client", client_name, source="PARCORE_CLIENT")
        self.force_signal("parcore_last_action", str(action), source="PARCORE_CLIENT")

        if client_name == "Nextion7":
            event = payload.get("event") or payload.get("raw") or payload.get("command") or action
            value = payload.get("value") if "value" in payload else payload.get("val")
            return self.dispatch_nextion7(str(event), value)

        if client_name == "EHR-GUI":
            return self.route_ehr_gui(action, payload)

        if client_name == "KHR-GUI":
            return self.route_khr_gui(action, payload)

        # PAR-GUI przez TSP i PARtext lokalnie schodzą do tego samego call_action.
        return self.call_action(action, payload)

    def handle_client_payload(self, payload: Mapping[str, Any], default_client: str = "PARtext") -> Any:
        """Obsługa JSON/dict z TSP, PARtext albo testów lokalnych."""
        if not isinstance(payload, Mapping):
            return self.command_text(str(payload), client=default_client)
        client = payload.get("client") or payload.get("source") or payload.get("from") or default_client
        action = payload.get("action") or payload.get("cmd") or payload.get("command") or payload.get("name")
        args = payload.get("args") or payload.get("payload") or payload.get("data") or {}
        if not isinstance(args, dict):
            args = {"value": args}
        # Gdy argumenty są płasko w payloadzie, dokładamy je do args.
        for key, value in payload.items():
            if key not in {"client", "source", "from", "action", "cmd", "command", "name", "args", "payload", "data", "type"}:
                args.setdefault(str(key), value)
        if action is None:
            if self._normalize_client_name(client) == "Nextion7":
                action = args.get("event") or args.get("raw") or args.get("value")
            else:
                raise ValueError(f"Brak akcji w payloadzie klienta PARcore: {payload}")
        return self.route_client_command(str(client), str(action), args)

    def command_text(self, line: str, client: str = "PARtext") -> Any:
        """PARtext: proste tekstowe wejście do tych samych metod PARcore.

        Przykłady:
          test axis arm_h
          rrp p1 axis arm_h
          rrp p1 dir 1
          rrp p1 speed 2
          rrp p1 sens 70
          take play
          mode LIVE
          set_signal name value
          manual_record_arm on
          snapshot
        """
        text = str(line or "").strip()
        if not text:
            return None
        if text.startswith("{"):
            return self.handle_client_payload(json.loads(text), default_client=client)
        parts = text.split()
        head = parts[0].lower()

        if head == "snapshot":
            return self.route_client_command(client, "snapshot", {})
        if head == "mode" and len(parts) >= 2:
            return self.route_client_command(client, "set_mode", {"mode": parts[1]})
        if head == "set_signal" and len(parts) >= 3:
            return self.route_client_command(client, "set_signal", {"name": parts[1], "value": self._parse_cli_value(" ".join(parts[2:]))})
        if head == "force_signal" and len(parts) >= 3:
            return self.route_client_command(client, "force_signal", {"name": parts[1], "value": self._parse_cli_value(" ".join(parts[2:]))})
        if head == "manual_record_arm":
            return self.route_client_command(client, "manual_record_arm", {"enabled": self._parse_cli_value(parts[1] if len(parts) > 1 else "on")})
        if head == "take" and len(parts) >= 2:
            sub = parts[1].lower()
            if sub == "load" and len(parts) >= 3:
                return self.route_client_command(client, "take_load", {"path": " ".join(parts[2:])})
            if sub in {"play", "pause", "stop"}:
                return self.route_client_command(client, f"take_{sub}", {})
        if head == "test" and len(parts) >= 3 and parts[1].lower() == "axis":
            return self.route_client_command(client, "test_axis", {"axis": parts[2], "direction": parts[3] if len(parts) > 3 else 1})
        if head == "sensor" and len(parts) >= 3:
            action = "sensor_test" if parts[1].lower() == "test" else "sensor_read"
            return self.route_client_command(client, action, {"name": parts[2]})
        if head == "sok" and len(parts) >= 2:
            return self.route_client_command(client, "sok_set", {"mode": parts[1], "direction": parts[2] if len(parts) > 2 else 1})
        if head == "rrp" and len(parts) >= 4:
            player = parts[1]
            sub = parts[2].lower()
            value = parts[3]
            mapping = {
                "axis": "rrp_set_axis", "ax": "rrp_set_axis",
                "dir": "rrp_set_dir", "direction": "rrp_set_dir",
                "speed": "rrp_set_speed", "mul": "rrp_set_speed",
                "sens": "rrp_set_sens", "sensitivity": "rrp_set_sens",
                "pot": "rrp_set_pot", "val": "rrp_set_pot",
            }
            if sub in mapping:
                return self.route_client_command(client, mapping[sub], {"player": player, "value": value, sub: value})
        raise ValueError(f"Nieznana komenda PARtext/PARcore: {line}")

    def _parse_cli_value(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        v = value.strip()
        low = v.lower()
        if low in {"on", "true", "tak", "yes"}:
            return True
        if low in {"off", "false", "nie", "no"}:
            return False
        try:
            if "." in v:
                return float(v)
            return int(v)
        except Exception:
            return v

    def route_par_gui_tsp(self, payload: Mapping[str, Any]) -> Any:
        """PAR-GUI przez TSP: payload jest tylko komendą, wykonuje PARcore."""
        return self.handle_client_payload(payload, default_client="PAR-GUI")

    def route_partext(self, line_or_payload: Any) -> Any:
        """PARtext lokalnie: tekst albo dict schodzi do tych samych metod."""
        if isinstance(line_or_payload, Mapping):
            return self.handle_client_payload(line_or_payload, default_client="PARtext")
        return self.command_text(str(line_or_payload), client="PARtext")

    def route_nextion7_local(self, event: str, value: Any = None) -> Any:
        """Nextion 7 lokalnie na miniPC: event UART -> dispatch_nextion7."""
        return self.route_client_command("Nextion7", str(event), {"event": event, "value": value})

    def route_ehr_gui(self, action: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """EHR-GUI przez TSP: TAKE i transport bez drugiego odtwarzacza."""
        payload = dict(args or {})
        action_norm = str(action or "").strip().lower()
        self.force_signal("ehr_state", "COMMAND", source="PARCORE_EHR")
        if action_norm in {"take_load", "load_take", "load", "ehr_take_load"}:
            if payload.get("path") or payload.get("file"):
                result = self.take_load(payload.get("path") or payload.get("file"))
            else:
                result = self.take_load_payload(payload)
            self.force_signal("ehr_state", "TAKE_LOADED", source="PARCORE_EHR")
            return result
        if action_norm in {"take_play", "play", "ehr_play"}:
            self.take_play(); self.force_signal("ehr_state", "PLAY", source="PARCORE_EHR"); return self.take_playback_status()
        if action_norm in {"take_pause", "pause", "ehr_pause"}:
            self.take_pause(); self.force_signal("ehr_state", "PAUSE", source="PARCORE_EHR"); return self.take_playback_status()
        if action_norm in {"take_stop", "stop", "ehr_stop"}:
            self.take_stop(); self.force_signal("ehr_state", "STOP", source="PARCORE_EHR"); return self.take_playback_status()
        if action_norm in {"set_signal", "force_signal"}:
            return self.force_signal(payload.get("name", payload.get("signal", "")), payload.get("value"), source="PARCORE_EHR")
        return self.call_action(action_norm, payload)

    def route_khr_gui(self, action: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """KHR-GUI przez TSP: korekty zapisują się w SignalBus i dalej idą normalnym torem."""
        payload = dict(args or {})
        action_norm = str(action or "").strip().lower()
        self.force_signal("khr_state", "COMMAND", source="PARCORE_KHR")
        if action_norm in {"correction", "korekta", "set_correction", "offset"}:
            axis = self._normalize_axis(payload.get("axis", payload.get("name", "")))
            value = payload.get("value", payload.get("offset", 0))
            signal = payload.get("signal") or f"khr_{axis.lower()}_offset"
            self.force_signal(str(signal), value, source="PARCORE_KHR")
            self.force_signal("khr_state", "CORRECTION_SET", source="PARCORE_KHR")
            return {"axis": axis, "signal": signal, "value": value}
        if action_norm in {"set_signal", "force_signal"}:
            return self.force_signal(payload.get("name", payload.get("signal", "")), payload.get("value"), source="PARCORE_KHR")
        return self.call_action(action_norm, payload)

    def take_playback_status(self) -> Dict[str, Any]:
        take = self.take_player.take
        return {
            "loaded": bool(take),
            "path": str(take.path) if take else "",
            "rows": len(take.rows) if take else 0,
            "index": self.take_player.index,
            "playing": bool(self.take_player.playing),
            "status": self.bus.get("take_status", "EMPTY"),
            "time_ms": self.bus.get("take_time_ms", self.bus.get("TAKE_TIME_MS", 0)),
        }

    def _ensure_parcore_signal_types(self) -> None:
        """PARcore musi zachować indeksy RRP jako liczby, nie jako LH 0/1 z mapy."""
        for name in ("rrp_p1_axis_index", "rrp_p2_axis_index", "rrp_p1_speed_mul", "rrp_p2_speed_mul"):
            try:
                meta = self.bus.meta.get(name)
                if meta is not None and getattr(meta, "typ", "") != "ANALOG":
                    self.bus.meta[name] = replace(meta, typ="ANALOG")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Niski poziom: SignalBus / TSP / hardware bridge
    # ------------------------------------------------------------------
    def _normalize_axis(self, axis: Any) -> str:
        key = str(axis).strip().upper().replace("-", "_").replace(" ", "_")
        return AXIS_ALIASES.get(key, key)

    def _bus_log(self, source: str, message: str) -> None:
        try:
            self.bus.log(source, message)
        except Exception:
            pass

    def _par_runtime_state(self) -> str:
        mode = str(getattr(self.bus, "mode", "TEST") or "TEST").upper()
        return "PAR_LIVE" if mode == "LIVE" else "PAR_TEST"

    def set_mode(self, mode: str) -> None:
        mode = str(mode or "TEST").upper()
        if mode not in {"TEST", "LIVE", "MIX"}:
            mode = "TEST"
        self.bus.set_mode(mode)
        self.bus.force_signal("par_mode", mode, source="PARCORE_MODE")
        self.bus.force_signal("par_state", self._par_runtime_state(), source="PARCORE_MODE")
        if self.enable_tsp_client and mode in {"TEST", "LIVE", "MIX"}:
            self._tsp_active = True
            self._start_tsp()
        elif not self.enable_tsp_client:
            self._tsp_active = False

    def _start_tsp(self) -> None:
        if TarzanTspClient is None:
            self._bus_log("TSP_ERROR", "TarzanTspClient niedostępny")
            return
        if self._tsp_thread and self._tsp_thread.is_alive():
            return
        self._tsp_thread = threading.Thread(target=self._tsp_connector_loop, name="PARCORE-TSP", daemon=True)
        self._tsp_thread.start()

    def _client_is_connected(self) -> bool:
        client = self.tsp_client
        if client is None:
            return False
        state = getattr(client, "is_connected", False)
        try:
            return bool(state() if callable(state) else state)
        except Exception:
            return False

    def _drop_tsp_client(self, reason: str = "connection_lost") -> None:
        client = self.tsp_client
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        self.tsp_client = None
        self._tsp_subscribed = False
        self._bus_log("TSP", f"Client dropped: {reason}. Reconnect pending...")

    def _queue_tsp_message(self, message: Dict[str, Any]) -> None:
        self._handle_tsp_message(message)

    def _tsp_connector_loop(self) -> None:
        """Transplant z tarzanParBridge.py: stabilne połączenie TSP + heartbeat.

        To nie jest UI. To jest wykonawczy most PARcore ↔ TSP.
        TEST/LIVE/MIX używają tego samego toru, jeżeli klient TSP jest włączony.
        """
        while self._tsp_active:
            try:
                if self.tsp_client is None or not self._client_is_connected():
                    if self.tsp_client is not None:
                        self._bus_log("TSP_ERROR", "CONNECTION LOST: MiniPC offline or client closed. Reconnecting...")
                        try:
                            self.tsp_client.close()
                        except Exception:
                            pass
                        self.tsp_client = None
                        self._tsp_subscribed = False

                    self.bus.set_input("par_state", "CONNECTING", source="PARCORE_TSP")
                    client = TarzanTspClient(host=self.tsp_host, name="tarzanPARcore")  # type: ignore
                    client.on_message = self._queue_tsp_message
                    client.connect()
                    self.tsp_client = client
                    self._tsp_subscribed = False
                    self._tsp_last_state_sync_ts = 0.0

                    self._bus_log("TSP", f"Connected to {self.tsp_host}. Sending HELLO...")
                    self.bus.set_input("par_state", "CONNECTED", source="PARCORE_TSP")
                    client.hello()
                else:
                    assert self.tsp_client is not None
                    self.tsp_client.ping()
                    self._sync_zero_state_with_tsp()
            except Exception as exc:
                self.bus.set_input("par_state", "OFFLINE", source="PARCORE_TSP")
                self._bus_log("TSP_ERROR", f"Connector loop error: {exc}")
                self._drop_tsp_client("connector_exception")
            time.sleep(1.0)
        self._bus_log("TSP", "TSP connector thread stopped.")

    def _announce_par_live_to_tsp(self) -> None:
        client = self.tsp_client
        if client is None or not self._client_is_connected():
            return
        try:
            client.set_signal("par_state", self._par_runtime_state())
            self._tsp_last_state_sync_ts = time.monotonic()
        except Exception as exc:
            self._bus_log("TSP_ERROR", f"PAR state announce failed: {exc}")
            self._drop_tsp_client(reason="par_state_announce_failed")

    def _sync_zero_state_with_tsp(self) -> None:
        client = self.tsp_client
        if client is None or not self._client_is_connected():
            return
        now = time.monotonic()
        if now - self._tsp_last_state_sync_ts < 5.0:
            return
        try:
            client.get_state()
            client.set_signal("par_state", self._par_runtime_state())
            self._tsp_last_state_sync_ts = now
        except Exception as exc:
            self._bus_log("TSP_ERROR", f"KROK ZERO state sync failed: {exc}")
            self._drop_tsp_client(reason="krok_zero_state_sync_failed")

    def _stop_tsp(self) -> None:
        self._tsp_active = False
        if self.tsp_client:
            self._bus_log("TSP", "Disconnecting from MiniPC...")
            try:
                if self._client_is_connected():
                    self.tsp_client.set_signal("par_state", "DISCONNECTED")
            except Exception:
                pass
            try:
                self.tsp_client.close()
            except Exception:
                pass
            self.tsp_client = None
        self._tsp_subscribed = False
        self._tsp_thread = None

    def _handle_tsp_message(self, message: Dict[str, Any]) -> None:
        """Obsługa wiadomości TSP przepisana z tarzanParBridge.py, bez UI.

        Zachowane tory: snajper_packet, get_state, hello/subscribe, error/write_denied,
        disconnect, log_event i trace. Dodatkowo przyjmujemy prostsze komunikaty
        STATE/SIGNAL/COMMAND używane przez klientów tekstowych lub lokalne adaptery.
        """
        if not isinstance(message, dict):
            return

        event = message.get("event")
        cmd = message.get("cmd")
        ok = message.get("ok", True)
        typ = str(message.get("type") or cmd or "").upper()

        if event == "snajper_packet":
            values = message.get("values", {})
            if isinstance(values, dict):
                try:
                    self.bus.apply_snapshot(values, source="TSP_LIVE")
                except Exception:
                    for name, value in values.items():
                        self.bus.force_signal(str(name), value, source="TSP_LIVE")
            return

        if (cmd == "get_state" and ok) or typ in {"STATE", "SNAPSHOT"}:
            state = message.get("state") or message.get("signals") or {}
            if isinstance(state, dict):
                self._bus_log("TSP", f"GET_STATE OK: signals={len(state.get('signals', state) if isinstance(state, dict) else state)}")
                try:
                    self.bus.apply_snapshot(state, source="TSP_INITIAL" if cmd == "get_state" else "TSP_LIVE")
                except Exception:
                    data = state.get("signals", state) if isinstance(state, dict) else {}
                    if isinstance(data, dict):
                        for name, value in data.items():
                            if isinstance(value, dict) and "value" in value:
                                value = value.get("value")
                            self.bus.force_signal(str(name), value, source="TSP_LIVE")
            return

        if (event == "hello") or (cmd == "hello" and ok):
            node = message.get("node") or message.get("node_name") or message.get("node_id", "unknown")
            self._bus_log("TSP", f"Handshake OK: {node}")
            if self.tsp_client and not self._tsp_subscribed:
                self._tsp_subscribed = True
                try:
                    self.tsp_client.ping()
                    self.tsp_client.get_state()
                    if hasattr(self.tsp_client, "subscribe"):
                        self.tsp_client.subscribe(
                            lanes=["normal", "slow", "health", "urgent"],
                            signals=self._tsp_boot_signals,
                        )
                    else:
                        self._announce_par_live_to_tsp()
                except Exception as exc:
                    self._bus_log("TSP_ERROR", f"HELLO follow-up failed: {exc}")
                    self._drop_tsp_client("hello_followup_failed")
            return

        if cmd == "subscribe" and ok:
            self._bus_log("TSP", "SUBSCRIBE OK: receiving live updates.")
            self._announce_par_live_to_tsp()
            try:
                if self.tsp_client and self._client_is_connected():
                    self.tsp_client.get_state()
            except Exception as exc:
                self._bus_log("TSP_ERROR", f"GET_STATE after subscribe failed: {exc}")
            return

        if typ in {"SIGNAL", "SET_SIGNAL", "UPDATE"}:
            name = message.get("name") or message.get("signal")
            if name:
                self.bus.force_signal(str(name), message.get("value"), source="TSP_LIVE")
            return

        if typ in {"COMMAND", "CALL_ACTION", "ACTION", "PARCORE", "PAR_GUI", "EHR", "KHR"}:
            payload = dict(message)
            if typ == "PAR_GUI":
                payload.setdefault("client", "PAR-GUI")
            elif typ == "EHR":
                payload.setdefault("client", "EHR-GUI")
            elif typ == "KHR":
                payload.setdefault("client", "KHR-GUI")
            else:
                payload.setdefault("client", message.get("client") or message.get("source") or "PAR-GUI")
            self.handle_client_payload(payload, default_client=str(payload.get("client") or "PAR-GUI"))
            return

        if event == "error" or (not ok and (message.get("error") or message.get("message"))):
            err_code = message.get("error", "unknown_error")
            err_msg = message.get("message") or message.get("reason") or err_code
            self._bus_log("TSP_ERROR", f"TSP Error ({err_code}): {err_msg}")
            self.bus.set_input("par_last_error", f"{err_code}: {err_msg}", source="TSP_LIVE")
            if err_code == "write_denied":
                self._bus_log("TSP_ERROR", f"Access Denied: {message.get('reason', 'control_owner_conflict')}")
                self.bus.set_input("par_write_denied_event", 1, source="TSP_LIVE")
                threading.Timer(1.0, lambda: self.bus.set_input("par_write_denied_event", 0, source="TSP_LIVE")).start()
            return

        if event == "disconnect":
            self._bus_log("TSP", "Server disconnected.")
            self._drop_tsp_client(reason="server_disconnect_event")
            return

        if event == "log_event":
            src = message.get("source", "REMOTE")
            msg = message.get("message", "")
            self._bus_log(f"MINI:{src}", str(msg))
            return

        if event == "trace":
            name = message.get("signal", "unknown")
            val = message.get("value", 0)
            self.bus.force_signal(f"trace_{name}", val, source="TSP_TRACE")
            return

    def _send_to_tsp_if_ready(self, send_fn: Callable[[Any], Any], action_name: str) -> bool:
        if not self._tsp_active or not self._client_is_connected():
            return False
        try:
            assert self.tsp_client is not None
            send_fn(self.tsp_client)
            return True
        except Exception as exc:
            self._bus_log("TSP_ERROR", f"{action_name} failed: {exc}")
            self._drop_tsp_client(reason=f"send_failed:{action_name}")
            return False

    def set_signal(self, name: str, value: Any, source: str = "PARCORE") -> bool:
        return self._set_signal(name, value, source=source)

    def set_input(self, name: str, value: Any, source: str = "PARCORE_INPUT") -> bool:
        ok = bool(self.bus.set_input(name, value, source=source))
        self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"set_input:{name}")
        return ok

    def write_output(self, name: str, value: Any, source: str = "PARCORE_OUTPUT") -> bool:
        ok = bool(self.bus.write_output(name, value, source=source))
        if self.hardware_bridge is not None:
            self._write_hardware(name, value)
        self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"write_output:{name}")
        return ok

    def force_signal(self, name: str, value: Any, source: str = "PARCORE_FORCE") -> bool:
        ok = bool(self.bus.force_signal(name, value, source=source))
        if self.hardware_bridge is not None:
            self._write_hardware(name, value)
        self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"force_signal:{name}")
        return ok

    def _set_signal(self, name: str, value: Any, source: str = "PARCORE") -> bool:
        try:
            signal_name = str(name or "")
            meta = self.bus.get_meta(signal_name)
            par_exec_prefixes = ("par_lcd_", "par_matrix_", "par_f_led_")
            par_exec_names = {
                "rec_p46_led_f1", "rec_p48_led_f2", "rec_p50_led_f3", "rec_p52_led_f4",
                "play_p37_step_disconnect_manual",
            }
            is_par_exec = signal_name.startswith(par_exec_prefixes) or signal_name in par_exec_names
            is_output = bool(
                is_par_exec
                or getattr(meta, "is_output", False)
                or getattr(meta, "kierunek", "") == "OUT"
            )
            if is_output:
                ok = self.write_output(signal_name, value, source=source)
            else:
                ok = self.set_input(signal_name, value, source=source)
        except Exception:
            ok = self.force_signal(name, value, source=source)
        try:
            self.on_state_change(name, value, source=source)
        except Exception:
            pass
        return bool(ok)


    # ------------------------------------------------------------------
    # Bridge compatibility — transplant zasad z tarzanParBridge.py bez UI.
    # ------------------------------------------------------------------
    def _requires_minipc_connection(self) -> bool:
        """Czy bieżący tryb wymaga aktywnego miniPC/TSP.

        W TEST można działać lokalnie na SignalBus. W LIVE/MIX komendy
        operatorskie powinny mieć tor do miniPC/TSP, ale PARcore nadal nie
        tworzy drugiej prawdy — zapis stanu przechodzi przez SignalBus.
        """
        mode = str(getattr(self.bus, "mode", "TEST") or "TEST").upper()
        return mode in {"LIVE", "MIX"}

    def _bus_set_input(self, name: str, value: Any, source: str = "PARCORE_BRIDGE") -> bool:
        """Zgodność z bridge: wpis wejściowy do SignalBus + opcjonalny TSP sync."""
        try:
            ok = bool(self.bus.set_input(name, value, source=source))
        except Exception:
            ok = bool(self.bus.force_signal(name, value, source=source))
        self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"_bus_set_input:{name}")
        return ok

    def read_input(self, name: str, default: Any = None) -> Any:
        """Zgodność z bridge: odczyt wejścia/stanu z SignalBus bez lokalnej prawdy."""
        try:
            if hasattr(self.bus, "read_input"):
                return self.bus.read_input(name, default)  # type: ignore[attr-defined]
        except TypeError:
            try:
                return self.bus.read_input(name)  # type: ignore[attr-defined]
            except Exception:
                pass
        except Exception:
            pass
        try:
            return self.bus.get(name, default)
        except Exception:
            return default

    def poll(self) -> Dict[str, Any]:
        """Bridge poll: lekki odczyt runtime/TSP/Nextion/TAKE bez ciężkiej diagnostyki."""
        if self._tsp_active and self._client_is_connected():
            self._send_to_tsp_if_ready(lambda c: c.get_state(), "poll:get_state")
        try:
            self.nextion_poll()
        except Exception as exc:
            self._bus_log("NEXTION7_ERROR", f"poll nextion failed: {exc}")
        return {
            "mode": str(getattr(self.bus, "mode", "TEST") or "TEST"),
            "requires_minipc": self._requires_minipc_connection(),
            "tsp_connected": self._client_is_connected(),
            "par_state": self.bus.get("par_state", ""),
            "parcore_state": self.bus.get("parcore_state", ""),
            "take_status": self.bus.get("take_status", ""),
            "nextion7_state": self.bus.get("nextion7_state", ""),
        }

    # ------------------------------------------------------------------
    # Headless transplant zasad paneli PAR — bez Tkintera, bez layoutu.
    # ------------------------------------------------------------------
    def _is_signal_input(self, name: str) -> bool:
        try:
            meta = self.bus.get_meta(name)
            return bool(getattr(meta, "is_input", False))
        except Exception:
            return False

    def _signal_blocked(self, name: str) -> bool:
        """Czy sygnał jest zablokowany dla ręcznego wymuszenia PAR.

        Zachowuje zasadę paneli: nie klikamy bokiem w wejścia sprzętowe,
        blokady safety i aktywne tory TAKE/automatyki.
        """
        n = str(name or "")
        if not n:
            return True
        lowered = n.lower()
        if lowered.startswith(("sensor_", "input_", "ack_", "status_")):
            return True
        if self._is_signal_input(n) and not lowered.startswith("par_"):
            return True
        if lowered in {"safety_axis_unlock", "axis_safety_unlock"}:
            return False
        try:
            if int(self.bus.get("safety_axis_unlock", 0) or 0) == 0 and lowered.endswith(("_step", "_dir", "_en")):
                return True
        except Exception:
            pass
        return False

    def _signal_clickable_input(self, name: str) -> bool:
        """Czy panel PAR mógł traktować sygnał jako wejście klikalne/testowe."""
        n = str(name or "")
        if not n:
            return False
        lowered = n.lower()
        return lowered.startswith(("par_", "ui_", "rrp_", "take_", "sok_", "manual_", "camera_", "khr_", "ehr_"))

    def _all_signals_clickable(self) -> List[str]:
        """Lista sygnałów, które można wystawić do PARtext/diagnostyki jako akcje."""
        names = list(self.bus.names()) if hasattr(self.bus, "names") else []
        return [n for n in names if not self._signal_blocked(n) or self._signal_clickable_input(n)]

    def _final_force_or_toggle(self, name: str, value: Any = None, source: str = "PARCORE_PANEL") -> Any:
        """Oryginalna zasada paneli: klik bez wartości przełącza, z wartością wymusza."""
        if self._signal_blocked(name) and not self._signal_clickable_input(name):
            self.force_signal("par_last_error", f"WRITE_DENIED:{name}", source=source)
            self._bus_log("WRITE_DENIED", f"{name} blocked")
            return {"ok": False, "error": "WRITE_DENIED", "signal": name}
        if value is None:
            current = self.read_input(name, 0)
            if isinstance(current, str):
                value = 0 if current.strip().lower() in {"1", "true", "on", "yes", "tak"} else 1
            else:
                value = 0 if bool(current) else 1
        ok = self._set_signal(name, value, source=source)
        self.on_state_change(name, value, source=source)
        return {"ok": bool(ok), "signal": name, "value": value}

    def reset_signals(self, names: Optional[Iterable[str]] = None, value: Any = 0) -> Dict[str, Any]:
        """Reset wykonawczy sygnałów PAR bez ruszania wejść i sensorów."""
        if names is None:
            names = self._all_signals_clickable()
        changed: Dict[str, Any] = {}
        for name in names:
            if self._signal_blocked(str(name)) and not self._signal_clickable_input(str(name)):
                continue
            try:
                self._set_signal(str(name), value, source="PARCORE_RESET")
                changed[str(name)] = value
                self.on_state_change(str(name), value, source="PARCORE_RESET")
            except Exception as exc:
                changed[str(name)] = f"ERROR:{exc}"
        self.force_signal("par_last_error", "", source="PARCORE_RESET")
        return changed

    def _increment_axis_counter(self, axis: Any, pulses: int = 1, direction: Any = 1) -> int:
        axis_name = self._normalize_axis(axis)
        sign = 1 if str(direction).strip().lower() in {"1", "true", "on", "right", "prawo", "+", "cw"} or direction is True else -1
        pos_names = AXIS_SIGNAL_BINDINGS.get(axis_name, {}).get("pos", [f"axis_{axis_name.lower()}_pos"])
        pos_name = self._first_existing(pos_names) or pos_names[0]
        try:
            current = int(float(self.bus.get(pos_name, 0) or 0))
        except Exception:
            current = 0
        new_value = current + sign * int(pulses)
        self.force_signal(pos_name, new_value, source="PARCORE_AXIS_COUNTER")
        self.force_signal(f"axis_{axis_name.lower()}_pulses_total", abs(new_value), source="PARCORE_AXIS_COUNTER")
        return new_value

    def _first_value(self, names: Iterable[str], default: Any = None) -> Any:
        for name in names:
            try:
                if self.bus.exists(str(name)):
                    value = self.bus.get(str(name), None)
                    if value is not None and value != "":
                        return value
            except Exception:
                continue
        return default

    def sensor_label(self, name: str) -> str:
        labels = {
            "xyz": "LEVEL XYZ",
            "level": "LEVEL XYZ",
            "temperature": "TEMP",
            "temp": "TEMP",
            "light": "LIGHT/BH1750",
            "bh1750": "LIGHT/BH1750",
            "limits": "LIMITS",
            "shock": "SHOCK/ALARM",
            "laser": "LASER",
            "rrp": "RRP POT",
        }
        return labels.get(str(name).lower(), str(name).upper())

    def register_step_dir_snajper_target(self, axis: Any, section: str = "PARCORE") -> Dict[str, Any]:
        axis_name = self._normalize_axis(axis)
        bind = AXIS_SIGNAL_BINDINGS.get(axis_name, {})
        targets = {
            "axis": axis_name,
            "section": section,
            "step": list(bind.get("step", [])),
            "dir": list(bind.get("dir", [])),
            "en": list(bind.get("en", [])),
            "pos": list(bind.get("pos", [])),
        }
        self.force_signal(f"snajper_target_{axis_name.lower()}", json.dumps(targets, ensure_ascii=False), source="PARCORE_SNAJPER")
        return targets

    def _ensure_step_dir_multi_snajper(self) -> TarzanStepDirMultiSnajperHeadless:
        if not isinstance(getattr(self, "step_dir_multi_snajper", None), TarzanStepDirMultiSnajperHeadless):
            self.step_dir_multi_snajper = TarzanStepDirMultiSnajperHeadless(self)
        for axis in AXIS_SIGNAL_BINDINGS.keys():
            self.register_step_dir_snajper_target(axis, section="STEP_DIR")
        self.force_signal("snajper_step_dir_ready", 1, source="PARCORE_SNAJPER")
        return self.step_dir_multi_snajper

    def _ensure_section_snajper(self, section: str = "", signals: Optional[Iterable[str]] = None) -> TarzanParSectionSnajperHeadless | Dict[str, Any]:
        if not isinstance(getattr(self, "section_snajper", None), TarzanParSectionSnajperHeadless):
            self.section_snajper = TarzanParSectionSnajperHeadless(self)
        if not section:
            return self.section_snajper
        sigs = list(signals or [])
        if not sigs:
            section_l = str(section).lower()
            sigs = list(TARZAN_SNAJPER_PAR_SECTIONS.get(section_l, set()))
            if not sigs:
                sigs = [n for n in (self.bus.names() if hasattr(self.bus, "names") else []) if section_l in str(n).lower()]
        payload = {"section": section, "signals": sigs, "count": len(sigs)}
        self.force_signal(f"snajper_section_{str(section).lower()}", json.dumps(payload, ensure_ascii=False), source="PARCORE_SNAJPER")
        return payload

    def _ensure_log_take_nextion_snajper_targets(self) -> Dict[str, Any]:
        payload = {
            "log": self._ensure_section_snajper("log", ["par_last_error", "ehr_last_error", "khr_last_error"]),
            "take": self._ensure_section_snajper("take", ["take_status", "take_time_ms", "loaded_take_path"]),
            "nextion": self._ensure_section_snajper("nextion7", ["nextion7_state", "nextion7_last_event"]),
        }
        self.force_signal("snajper_log_take_nextion_ready", 1, source="PARCORE_SNAJPER")
        return payload

    def snajper_fire_log_take_nextion(self, section: str = "take", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        packet = {
            "section": section,
            "payload": dict(payload or {}),
            "ts": time.time(),
        }
        # Jeżeli istnieje realny Snajper/bridge, użyj go. Inaczej tylko SignalBus.
        bridge = self.hardware_bridge
        fired = False
        for attr in ("snajper_fire", "fire_snajper", "queue_snajper_command"):
            fn = getattr(bridge, attr, None) if bridge is not None else None
            if callable(fn):
                try:
                    fn(packet)
                    fired = True
                    break
                except TypeError:
                    try:
                        fn(section, packet)
                        fired = True
                        break
                    except Exception:
                        pass
                except Exception:
                    pass
        self.queue_snajper_command(section, packet)
        self.force_signal("snajper_last_packet", json.dumps(packet, ensure_ascii=False), source="PARCORE_SNAJPER")
        return {"queued": True, "fired": fired, "packet": packet}

    def on_state_change(self, name: str, value: Any, source: str = "PARCORE_STATE_CHANGE", previous_value: Any = None) -> None:
        """Headless odpowiednik reakcji panelu na zmianę SignalBus.

        Transplant zasad z tarzanParPanels.py:
        - Snajper log/take/nextion,
        - StepDirMultiSnajper,
        - SectionSnajper,
        - linkowane sygnały,
        - logi zdarzeń i sensorów z deadband.
        """
        n = str(name or "")
        if not n:
            return
        lowered = n.lower()
        prev = previous_value
        if prev is None:
            try:
                prev = getattr(self.bus.get_state(n), "previous_value", None)  # type: ignore[attr-defined]
            except Exception:
                prev = self._last_log_values.get(f"__prev__:{n}")
        changed = str(prev) != str(value)
        self._last_log_values[f"__prev__:{n}"] = value

        # Linki sygnałów z PAR Panels: jedna prawda, wiele nazw technicznych.
        try:
            linked = list(_LINKED_SIGNAL_GROUPS.get(n, []))
            explicit_groups = (
                {"play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"},
                {"play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"},
                {"play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"},
                {"play_p16_action_led", "par_lamp_auto_active", "ui_action_led"},
                {"rec_p39_shock_sensor", "par_shock_sensor_state", "sensor_shock_state"},
            )
            for group in explicit_groups:
                if n in group:
                    linked.extend(sorted(group))
            for extra in dict.fromkeys(linked):
                if extra != n and self.bus.exists(extra) and self.bus.get(extra) != value:
                    self.force_signal(extra, value, source="PAR_LINK_SYNC")
        except Exception as exc:
            self._bus_log("PAR_LINK_ERROR", f"{n}: {exc}")

        # Status krańcówek.
        try:
            meta = self.bus.get_meta(n)
            is_limit = "limit" in lowered or str(getattr(meta, "grupa", "")).upper() in {"KRAŃCÓWKI", "KRANCOWKI"}
        except Exception:
            is_limit = "limit" in lowered
        if is_limit:
            try:
                self.update_limits_status()
                if n != "sensor_limits_status" and changed:
                    lbl = self.limit_label(n)
                    status = "AKTYWACJA" if value == 1 else "OK"
                    self.bus.log("LIMIT", f"{status}: {lbl} SRC={source}")
            except Exception:
                pass

        # Snajper headless.
        try:
            if lowered.startswith("take_") or lowered in {"loaded_take_path", "take_status"}:
                self.snajper_fire_log_take_nextion("take", {"signal": n, "value": value, "source": source})
            elif "nextion7" in lowered:
                self.snajper_fire_log_take_nextion("nextion7", {"signal": n, "value": value, "source": source})
            elif lowered.startswith(("par_", "ehr_", "khr_")):
                self.snajper_fire_log_take_nextion("log", {"signal": n, "value": value, "source": source})
            self._ensure_step_dir_multi_snajper().fire(n, value)
            section = self._ensure_section_snajper()
            if isinstance(section, TarzanParSectionSnajperHeadless):
                section.fire(n, value)
        except Exception as exc:
            self._bus_log("SNAJPER_ERROR", f"on_state_change({n}) failed: {exc}")

        # RRP pamięć osi i wartość z impulsów dla fizycznego Nextiona.
        try:
            self._remember_rrp_selected_axis(n, n, value)
            self._fire_rrp_value_from_axis_pulses(n, value)
        except Exception:
            pass

        # Logi zdarzeń PAR bez UI.
        try:
            if changed:
                if n == "sensor_laser_set":
                    self.bus.log("LASER", ("ON" if value else "OFF") + f" SRC={source}")
                elif n == "sensor_shock_state":
                    self.bus.log("SHOCK", ("AKTYWACJA" if value else "OK") + f" SRC={source}")
                elif n == "ui_action_led":
                    self.bus.log("PRACA", ("START" if value else "STOP") + f" SRC={source}")
                elif n in {"ui_f1_sw", "ui_f2_sw", "ui_f3_sw", "ui_f4_sw"} and value == 1:
                    self.bus.log("PRZYCISK", f"{n.split('_')[-2].upper()} AKTYWACJA SRC={source}")

            def _float(v: Any, default: float = 0.0) -> float:
                try:
                    return float(v)
                except Exception:
                    return default
            if n == "sensor_temp_c":
                val = _float(value)
                last = _float(self._last_log_values.get(n, -999.0), -999.0)
                if abs(val - last) >= 0.5:
                    self._last_log_values[n] = val
                    self.bus.log("SENSOR", f"TEMPERATURA {val:.1f}C SRC={source}")
            elif n == "sensor_light_lux":
                val = _float(value)
                last = _float(self._last_log_values.get(n, -999.0), -999.0)
                diff = abs(val - last)
                if diff >= 500 or (last > 0 and diff >= 0.2 * last):
                    self._last_log_values[n] = val
                    self.bus.log("SENSOR", f"ŚWIATŁO {int(val)}lx SRC={source}")
            elif n in {"sensor_level_x", "sensor_level_y", "sensor_level_z"}:
                val = _float(value)
                last = _float(self._last_log_values.get(n, -999.0), -999.0)
                if abs(val - last) >= 10:
                    self._last_log_values[n] = val
                    self.bus.log("SENSOR", f"POZIOM {n.split('_')[-1].upper()}: {int(val)} SRC={source}")
        except Exception:
            pass

        # SOK log po zboczu STEP.
        try:
            if value == 1 and prev == 0:
                sok_map = {
                    "axis_cam_h_step": ("PAN", "axis_cam_h_dir"),
                    "axis_cam_v_step": ("TILT", "axis_cam_v_dir"),
                    "axis_cam_f_step": ("FOKUS", "axis_cam_f_dir"),
                    "axis_arm_t_step": ("POCHYŁ", "axis_arm_t_dir"),
                    "axis_arm_h_step": ("RAMIĘ H", "axis_arm_h_dir"),
                    "axis_arm_v_step": ("RAMIĘ V", "axis_arm_v_dir"),
                }
                if n in sok_map:
                    sec, d_sig = sok_map[n]
                    now = time.time()
                    if now - self._last_log_times.get(n, 0.0) >= 0.5:
                        self._last_log_times[n] = now
                        kier = "PRAWO" if self.bus.get(d_sig, 0) else "LEWO"
                        self.bus.log("SOK", f"{sec} RUCH {kier} SRC={source}")
        except Exception:
            pass

        # Tekstowe preview/logi są wyjściem stanu, nie źródłem komend.
        try:
            if not lowered.endswith("_preview") and "preview" not in lowered:
                if lowered.startswith(("par_", "ehr_", "khr_", "take_", "axis_", "sensor_", "rrp_")):
                    self.log_par_event(f"{n}={self._short_preview_value(value)}", source=source)
                if "nextion7" in lowered:
                    self.log_nextion7_event(f"{n}={self._short_preview_value(value)}", source=source)
                self.publish_text_previews("all")
        except Exception:
            pass

    def _snajper_update_section(self, section: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.snajper_fire_log_take_nextion(section, payload or {})

    def _snajper_update_section_generic(self, section: str, signal_name: str, value: Any) -> Dict[str, Any]:
        return self._snajper_update_section(section, {"signal": signal_name, "value": value})

    def _snajper_update_section_take(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        payload = self.take_playback_status()
        if signal_name:
            payload.update({"signal": signal_name, "value": value})
        return self._snajper_update_section("take", payload)

    def _snajper_update_section_nextion(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        payload = {"state": self.bus.get("nextion7_state", "")}
        if signal_name:
            payload.update({"signal": signal_name, "value": value})
        return self._snajper_update_section("nextion7", payload)

    def _snajper_update_section_log(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        payload = {"last_error": self.bus.get("par_last_error", "")}
        if signal_name:
            payload.update({"signal": signal_name, "value": value})
        return self._snajper_update_section("log", payload)

    def _snajper_update_section_rrp(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("rrp", {"signal": signal_name, "value": value, "rrp": self.build_rrp_preview()})

    def _snajper_update_section_motor_cards(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("motor_cards", {"signal": signal_name, "value": value, "axes": self.build_axis_preview()})

    def _snajper_update_section_step_dir_preview(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("step_dir_preview", {"signal": signal_name, "value": value})

    def _snajper_update_section_temperature(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("temperature", {"signal": signal_name, "value": value, "preview": self.build_sensors_preview()})

    def _snajper_update_section_light(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("light", {"signal": signal_name, "value": value, "preview": self.build_sensors_preview()})

    def _snajper_update_section_xyz(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("xyz", {"signal": signal_name, "value": value, "preview": self.build_sensors_preview()})

    def _snajper_update_section_limits(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("limits", {"signal": signal_name, "value": value, "status": self.bus.get("sensor_limits_status", "")})

    def _snajper_update_section_shock_laser(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("shock_laser", {"signal": signal_name, "value": value})

    def _snajper_update_section_sok(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("sok", {"signal": signal_name, "value": value})

    def _snajper_update_section_cnc(self, signal_name: str = "", value: Any = None) -> Dict[str, Any]:
        return self._snajper_update_section("cnc", {"signal": signal_name, "value": value})

    def _write_hardware(self, name: str, value: Any) -> None:
        bridge = self.hardware_bridge
        if bridge is None:
            return
        for method in ("write", "write_output", "set_signal", "force_signal"):
            fn = getattr(bridge, method, None)
            if callable(fn):
                try:
                    fn(name, value)
                    return
                except TypeError:
                    try:
                        fn(name, value, source="PARCORE")
                        return
                    except Exception:
                        pass
                except Exception as exc:
                    self._bus_log("HW_ERROR", f"{method}({name}) failed: {exc}")
                    return

    # ------------------------------------------------------------------
    # Snajper fizyczny / RRP / MODE — domknięcie transplantu zasad.
    # ------------------------------------------------------------------
    def _remember_rrp_selected_axis(self, raw_signal: str, logical_signal: Optional[str], value: Any) -> None:
        names = {str(raw_signal or "").strip(), str(logical_signal or "").strip()}
        if names.intersection({"rrp_p1_selected_axis", "par_rrp_p1_selected_axis", "par_rrp_p1_axis", "par_rrp_p1_axis"}):
            self._rrp_runtime.setdefault("p1", {})["selected_axis"] = str(value or "").strip().lower()
        if names.intersection({"rrp_p2_selected_axis", "par_rrp_p2_selected_axis", "par_rrp_p2_axis", "par_rrp_p2_axis"}):
            self._rrp_runtime.setdefault("p2", {})["selected_axis"] = str(value or "").strip().lower()

    def _fire_rrp_value_from_axis_pulses(self, raw_signal: str, value: Any) -> None:
        raw = str(raw_signal or "").strip()
        if not raw.startswith("axis_") or not raw.endswith("_pulses"):
            return
        selected_axis = raw[len("axis_"):-len("_pulses")]
        for player in ("p1", "p2"):
            if str(self._rrp_runtime.get(player, {}).get("selected_axis", "")).lower() == selected_axis:
                self.force_signal(f"rrp_{player}_value", value, source="PARCORE_RRP_SNAJPER")
                self.force_signal(f"par_rrp_{player}_val", value, source="PARCORE_RRP_SNAJPER")
                self.snajper_fire_log_take_nextion("rrp", {"signal": raw, "player": player, "value": value})

    def fire_nextion_physical_resync(self, fast: bool = False) -> Dict[str, Any]:
        """Headless delegacja do realnego Snajpera/Nextion adaptera, bez UI."""
        fired = False
        snajper = getattr(self.hardware_bridge, "tarzan_snajper", None) if self.hardware_bridge is not None else None
        if snajper is None:
            snajper = getattr(self, "tarzan_snajper", None)
        fn = getattr(snajper, "fire_nextion_physical_resync", None)
        if callable(fn):
            try:
                fn(self.bus, fast=fast)
                fired = True
            except TypeError:
                try:
                    fn(self.bus)
                    fired = True
                except Exception:
                    pass
        if not fired:
            self.snajper_fire_log_take_nextion("nextion7", {"resync": "physical", "fast": fast})
        self.force_signal("nextion7_physical_resync_last", time.time(), source="PARCORE_NEXTION7_RESYNC")
        return {"fired": fired, "fast": fast}

    def fire_nextion_page_loaded_resync(self, page_id: str) -> Dict[str, Any]:
        fired = 0
        snajper = getattr(self.hardware_bridge, "tarzan_snajper", None) if self.hardware_bridge is not None else None
        if snajper is None:
            snajper = getattr(self, "tarzan_snajper", None)
        fn = getattr(snajper, "fire_nextion_page_loaded_resync", None)
        if callable(fn):
            try:
                fired = int(fn(self.bus, page_id) or 0)
            except Exception:
                fired = 0
        if not fired:
            self.snajper_fire_log_take_nextion("nextion7", {"resync": "page_loaded", "page": page_id})
        self.force_signal("nextion7_page_loaded_resync_last", str(page_id), source="PARCORE_NEXTION7_RESYNC")
        return {"fired": fired, "page_id": str(page_id)}

    def _apply_rrp_to_axis(self, axis_index: int, value: int, player: str) -> Dict[str, Any]:
        """Transplant zasady TarzanModeLogic._apply_rrp_to_axis bez omijania SignalBus."""
        try:
            idx = int(axis_index)
            val = int(value)
        except Exception:
            return {"active": False, "reason": "bad_value"}
        # MODE używał 1..8, Nextion RRP używa 0..5. Obsługujemy oba bez nowej prawdy.
        mode_axis_map = {1: "cam_h", 2: "cam_v", 3: "cam_t", 4: "cam_f", 5: "arm_h", 6: "arm_v", 7: "tilt", 8: "cart"}
        nextion_axis_map = {0: "cam_v", 1: "arm_t", 2: "cam_f", 3: "cam_h", 4: "arm_h", 5: "arm_v"}
        axis_name = nextion_axis_map.get(idx) if idx in nextion_axis_map else mode_axis_map.get(idx)
        if not axis_name:
            return {"active": False, "reason": "no_axis"}
        prefix = f"axis_{axis_name}"
        ready = self.bus.get(f"{prefix}_ready", 1)
        if ready in {0, "0", False, "False", "false"}:
            return {"active": False, "axis": axis_name, "reason": "not_ready"}
        diff = val - 512
        if abs(diff) < 20:
            dir_val = 0
        else:
            dir_val = 1 if diff > 0 else -1
        if self.bus.exists(f"{prefix}_dir"):
            self.write_output(f"{prefix}_dir", dir_val, source=f"MODE_RRP_{str(player).upper()}")
        self.force_signal(f"rrp_{player}_axis_index", idx, source="PARCORE_MODE_RRP")
        self.force_signal(f"rrp_{player}_value", val, source="PARCORE_MODE_RRP")
        self.force_signal(f"rrp_{player}_dir", dir_val, source="PARCORE_MODE_RRP")
        self.snajper_fire_log_take_nextion("rrp", {"player": player, "axis": axis_name, "value": val, "dir": dir_val})
        return {"active": True, "axis": axis_name, "dir": dir_val, "value": val}

    def get_rrp_state(self) -> Dict[str, Any]:
        return dict(self._rrp_nextion_state)

    def get_nextion_monitor_state(self, screen_key: str = "nextion_7", **kwargs: Any) -> Dict[str, Any]:
        bridge = self._nextion7_bridge or self.nextion
        for method in ("get_nextion_monitor_state", "snapshot"):
            fn = getattr(bridge, method, None) if bridge is not None else None
            if callable(fn):
                try:
                    try:
                        state = fn(screen_key)
                    except TypeError:
                        state = fn()
                    if isinstance(state, dict):
                        return state
                except Exception:
                    pass
        return {"nextion7_state": self.bus.get("nextion7_state", ""), "last_event": self.bus.get("nextion7_last_event", ""), "rrp": self.get_rrp_state()}

    def _rrp_axis_binding(self, player: str, axis_index: Any) -> Dict[str, Any]:
        try:
            idx = int(axis_index)
        except Exception:
            idx = -1
        axis_key = _RRP_NEXTION_AXIS_ORDER[idx] if 0 <= idx < len(_RRP_NEXTION_AXIS_ORDER) else ""
        par_axis = _RRP_CANON_AXIS_TO_PAR.get(axis_key, "")
        bind = AXIS_SIGNAL_BINDINGS.get(par_axis, {}) if par_axis else {}
        return {
            "selected_axis": axis_key,
            "step_signal": (bind.get("step") or [""])[0],
            "dir_signal": (bind.get("dir") or [""])[0],
            "en_signal": (bind.get("en") or [""])[0],
        }

    def _handle_rrp_event(self, msg: str) -> Dict[str, Any]:
        raw = str(msg or "").strip().replace("\xff", "")
        if raw.startswith("rrp:"):
            raw = raw[4:]
        if "=" not in raw:
            return {"ok": False, "raw": msg}
        cmd_key, val = raw.split("=", 1)
        try:
            val_int = int(float(val))
        except Exception:
            return {"ok": False, "raw": msg}
        if cmd_key == "stop" and val_int == 1:
            self._rrp_nextion_state.update({"va_p1_axis": -1, "va_p2_axis": -1, "va_p1_dir": 0, "va_p2_dir": 0, "va_p1_val": 0, "va_p2_val": 0})
            self._rrp_player_initialized.update({"p1": False, "p2": False})
        else:
            mapping = {"p1_ax": "va_p1_axis", "p2_ax": "va_p2_axis", "p1_dr": "va_p1_dir", "p2_dr": "va_p2_dir", "p1_dir": "va_p1_dir", "p2_dir": "va_p2_dir", "p1_se": "h_p1_sens", "p2_se": "h_p2_sens", "p1_sens": "h_p1_sens", "p2_sens": "h_p2_sens"}
            target_key = mapping.get(cmd_key, cmd_key)
            self._rrp_nextion_state[target_key] = val_int
            if cmd_key in {"p1_ax", "p1_axis"}:
                self._rrp_player_initialized["p1"] = val_int >= 0
            elif cmd_key in {"p2_ax", "p2_axis"}:
                self._rrp_player_initialized["p2"] = val_int >= 0
        self._rrp_nextion_state["rrp_rev"] = int(self._rrp_nextion_state.get("rrp_rev", 0)) + 1
        self._update_bus_from_rrp()
        return {"ok": True, "cmd": cmd_key, "value": val_int, "state": self.get_rrp_state()}

    def _update_bus_from_rrp(self) -> Dict[str, Any]:
        active_en_signals: set[str] = set()
        for idx, axis_name in enumerate(_RRP_NEXTION_AXIS_ORDER):
            current = self._rrp_nextion_state.get(f"axis_{axis_name}_pulses", 0)
            value = current
            for key in (f"axis_{axis_name}_pulses", f"axis_{axis_name}_pos", f"axis_{idx}_value", f"par_axis_{idx}_val", f"par_axis_{idx}_pos"):
                try:
                    candidate = self.bus.get(key, None)
                except Exception:
                    candidate = None
                if candidate is not None:
                    value = candidate
                    break
            self._rrp_nextion_state[f"axis_{axis_name}_pulses"] = value
        for player in ("p1", "p2"):
            axis_index = self._rrp_nextion_state.get(f"va_{player}_axis", -1)
            direction = self._rrp_nextion_state.get(f"va_{player}_dir", 0)
            sensitivity = self._rrp_nextion_state.get(f"h_{player}_sens", 50)
            binding = self._rrp_axis_binding(player, axis_index)
            pot_signal = "sensor_rrp_pot_h" if player == "p1" else "sensor_rrp_pot_v"
            active = 1 if binding["selected_axis"] else 0
            if binding["en_signal"]:
                active_en_signals.add(binding["en_signal"])
            canonical = {"active": active, "axis_index": axis_index, "selected_axis": binding["selected_axis"], "pot_signal": pot_signal, "step_signal": binding["step_signal"], "dir_signal": binding["dir_signal"], "en_signal": binding["en_signal"], "dir": direction, "sens": sensitivity}
            for key, val in canonical.items():
                if key == "sens" and not self._rrp_player_initialized.get(player, False):
                    continue
                self.force_signal(f"rrp_{player}_{key}", val, source="NEXTION_PHYSICAL")
                self.force_signal(f"par_rrp_{player}_{key}", val, source="NEXTION_PHYSICAL")
            self.force_signal(f"par_rrp_{player}_axis", binding["selected_axis"], source="NEXTION_PHYSICAL")
            self.force_signal(f"par_rrp_{player}_dir", direction, source="NEXTION_PHYSICAL")
            for axis_name in _RRP_NEXTION_AXIS_ORDER:
                btn_value = 0 if binding["selected_axis"] == axis_name else 1
                self.force_signal(f"rrp_{player}_btn_{axis_name}", btn_value, source="NEXTION_PHYSICAL")
                self.force_signal(f"par_rrp_{player}_btn_{axis_name}", btn_value, source="NEXTION_PHYSICAL")
            counter = self._rrp_nextion_state.get(f"axis_{binding['selected_axis']}_pulses", 0) if binding["selected_axis"] else 0
            self._rrp_nextion_state[f"va_{player}_val"] = counter
            self.force_signal(f"rrp_{player}_value", counter, source="NEXTION_PHYSICAL")
            self.force_signal(f"par_rrp_{player}_val", counter, source="NEXTION_PHYSICAL")
        rec_auto_active = any(en in _RRP_REC_AUTO_EN_SIGNALS for en in active_en_signals)
        if self.bus.exists("ui_rec_auto_enable"):
            self.write_output("ui_rec_auto_enable", 1 if rec_auto_active else 0, source="NEXTION_PHYSICAL")
        for en_sig in _RRP_ALL_EN_SIGNALS:
            if self.bus.exists(en_sig):
                self.write_output(en_sig, 1 if en_sig in active_en_signals else 0, source="NEXTION_PHYSICAL")
        if self.bus.exists("ui_action_led"):
            self.write_output("ui_action_led", 1 if active_en_signals else 0, source="NEXTION_PHYSICAL")
        return self.get_rrp_state()

    def preview_rrp_tap(self, screen_key: str, key: str) -> Dict[str, Any]:
        bridge = self._nextion7_bridge or self.nextion
        comp_map = {"p1_cam_v":"b_p1_cam_v", "p1_arm_t":"b_p1_arm_t", "p1_cam_f":"b_p1_cam_f", "p1_cam_h":"b_p1_cam_h", "p1_arm_h":"b_p1_arm_h", "p1_arm_v":"b_p1_arm_v", "p2_cam_v":"b_p2_cam_v", "p2_arm_t":"b_p2_arm_t", "p2_cam_f":"b_p2_cam_f", "p2_cam_h":"b_p2_cam_h", "p2_arm_h":"b_p2_arm_h", "p2_arm_v":"b_p2_arm_v", "p1_dir":"b_p1_dir", "p2_dir":"b_p2_dir", "stop":"b_stop", "home":"b_home"}
        comp = comp_map.get(str(key))
        if comp and bridge is not None:
            dev = getattr(bridge, "devices", {}).get(screen_key) if hasattr(bridge, "devices") else None
            if dev is not None and getattr(dev, "connected", False):
                try:
                    dev.send_command(f"click {comp},1")
                except Exception:
                    pass
        return self._simulate_rrp_click(key)

    def _simulate_rrp_click(self, key: str) -> Dict[str, Any]:
        axis_map = {"p1_cam_v":("p1",0), "p1_arm_t":("p1",1), "p1_cam_f":("p1",2), "p1_cam_h":("p1",3), "p1_arm_h":("p1",4), "p1_arm_v":("p1",5), "p2_cam_v":("p2",0), "p2_arm_t":("p2",1), "p2_cam_f":("p2",2), "p2_cam_h":("p2",3), "p2_arm_h":("p2",4), "p2_arm_v":("p2",5)}
        if key in axis_map:
            player, idx = axis_map[key]
            field = f"va_{player}_axis"
            self._rrp_nextion_state[field] = idx if self._rrp_nextion_state.get(field, -1) != idx else -1
            self._rrp_player_initialized[player] = self._rrp_nextion_state[field] >= 0
        elif key == "stop":
            self._rrp_nextion_state.update({"va_p1_axis": -1, "va_p2_axis": -1})
            self._rrp_player_initialized.update({"p1": False, "p2": False})
        elif key in {"p1_dir", "p2_dir"}:
            player = "p1" if "p1" in key else "p2"
            field = f"va_{player}_dir"
            self._rrp_nextion_state[field] = 1 - int(self._rrp_nextion_state.get(field, 0) or 0)
        self._rrp_nextion_state["rrp_rev"] = int(self._rrp_nextion_state.get("rrp_rev", 0)) + 1
        return self._update_bus_from_rrp()

    def preview_rrp_set_value(self, screen_key: str, player: str, value: int) -> Dict[str, Any]:
        bridge = self._nextion7_bridge or self.nextion
        comp = f"h_{player}_sens"
        if bridge is not None:
            dev = getattr(bridge, "devices", {}).get(screen_key) if hasattr(bridge, "devices") else None
            if dev is not None and getattr(dev, "connected", False):
                try:
                    dev.send_command(f"{comp}.val={int(value)}")
                    dev.send_command(f"click {comp},1")
                except Exception:
                    pass
        self._rrp_nextion_state[comp] = int(value)
        self._rrp_player_initialized[self._normalize_player(player)] = True
        self._rrp_nextion_state["rrp_rev"] = int(self._rrp_nextion_state.get("rrp_rev", 0)) + 1
        return self._update_bus_from_rrp()

    # ------------------------------------------------------------------
    # RRP — logika wykonawcza operatora bez widgetów.
    # ------------------------------------------------------------------
    def rrp_set_axis(self, player: str, axis: Any) -> Dict[str, Any]:
        player = self._normalize_player(player)
        axis_name = self._normalize_axis(axis)
        if axis_name not in AXIS_SIGNAL_BINDINGS:
            raise ValueError(f"Nieznana oś RRP: {axis}")
        bind = AXIS_SIGNAL_BINDINGS[axis_name]
        step_signal = self._first_existing(bind.get("step", [])) or (bind.get("step", [""])[0])
        dir_signal = self._first_existing(bind.get("dir", [])) or (bind.get("dir", [""])[0])
        pot_signal = "sensor_rrp_pot_h" if player == "p1" else "sensor_rrp_pot_v"
        if not self.bus.exists(pot_signal):
            pot_signal = "play_p45_rrp_pot_h" if player == "p1" else "play_p47_rrp_pot_v"

        self.force_signal(f"rrp_{player}_axis_index", AXIS_INDEX[axis_name], source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_selected_axis", axis_name, source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_axis", axis_name, source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_step_signal", step_signal, source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_dir_signal", dir_signal, source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_pot_signal", pot_signal, source="PARCORE_RRP")
        self._rrp_runtime[player]["selected_axis"] = axis_name
        self._ensure_rrp_loop()
        return {"player": player, "axis": axis_name, "index": AXIS_INDEX[axis_name], "step_signal": step_signal, "dir_signal": dir_signal, "pot_signal": pot_signal}

    def rrp_clear_axis(self, player: str) -> None:
        player = self._normalize_player(player)
        self.force_signal(f"rrp_{player}_axis_index", -1, source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_selected_axis", "", source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_axis", "", source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_step_signal", "", source="PARCORE_RRP")
        self.force_signal(f"par_rrp_{player}_dir_signal", "", source="PARCORE_RRP")
        self._rrp_runtime[player]["selected_axis"] = ""

    def rrp_set_dir(self, player: str, direction: Any) -> int:
        player = self._normalize_player(player)
        val = 1 if str(direction).strip().lower() in {"1", "true", "on", "right", "prawo", "+", "cw"} or direction is True else 0
        self.force_signal(f"par_rrp_{player}_dir", val, source="PARCORE_RRP_DIR")
        return val

    def rrp_set_speed(self, player: str, mul: Any) -> int:
        player = self._normalize_player(player)
        try:
            value = int(float(mul or 1))
        except Exception:
            value = 1
        if value not in {1, 2, 3, 4}:
            value = max(1, min(4, value))
        self.force_signal(f"rrp_{player}_speed_mul", value, source="PARCORE_RRP_SPEED")
        return value

    def rrp_set_sens(self, player: str, sens: Any) -> float:
        player = self._normalize_player(player)
        try:
            value = max(0.0, min(100.0, float(sens)))
        except Exception:
            value = 50.0
        self.force_signal(f"par_rrp_{player}_sens", value, source="PARCORE_RRP_SENS")
        return value

    # aliasy zgodne z planem użytkownika: rrp_set_speed/sens(...)
    def rrp_set_speed_sens(self, player: str, sens: Any) -> float:
        return self.rrp_set_sens(player, sens)

    def rrp_sens(self, player: str, sens: Any) -> float:
        return self.rrp_set_sens(player, sens)

    def rrp_speed(self, player: str, mul: Any) -> int:
        return self.rrp_set_speed(player, mul)

    def rrp_set_pot(self, player: str, value: Any) -> int:
        player = self._normalize_player(player)
        try:
            pot = max(0, min(4095, int(float(value))))
        except Exception:
            pot = 0
        sig = "sensor_rrp_pot_h" if player == "p1" else "sensor_rrp_pot_v"
        if not self.bus.exists(sig):
            sig = "play_p45_rrp_pot_h" if player == "p1" else "play_p47_rrp_pot_v"
        self.force_signal(sig, pot, source="PARCORE_RRP_POT")
        self.force_signal(f"par_rrp_{player}_val", pot, source="PARCORE_RRP_POT")
        return pot

    def _normalize_player(self, player: Any) -> str:
        p = str(player or "p1").strip().lower()
        if p in {"1", "p1", "left", "l", "h"}:
            return "p1"
        if p in {"2", "p2", "right", "r", "v"}:
            return "p2"
        raise ValueError(f"Nieznany kanał RRP: {player}")

    def _first_existing(self, names: Sequence[str]) -> Optional[str]:
        for name in names:
            if self.bus.exists(name):
                return name
        return names[0] if names else None

    def _ensure_rrp_loop(self) -> None:
        if self._rrp_thread and self._rrp_thread.is_alive():
            return
        self._rrp_active = True
        self._rrp_thread = threading.Thread(target=self._rrp_loop, name="PARCORE-RRP", daemon=True)
        self._rrp_thread.start()

    def _rrp_loop(self) -> None:
        sample_ms = max(1, int(CZAS_PROBKOWANIA_MS))
        while self._rrp_active:
            start = time.monotonic()
            try:
                self._rrp_tick_all()
            except Exception as exc:
                self._bus_log("RRP_ERROR", str(exc))
            elapsed_ms = int((time.monotonic() - start) * 1000)
            time.sleep(max(0.001, (sample_ms - elapsed_ms) / 1000.0))

    def _rrp_tick_all(self) -> None:
        for player in ("p1", "p2"):
            axis = str(self.bus.get(f"par_rrp_{player}_selected_axis", "") or "").upper()
            if not axis:
                continue
            step_signal = str(self.bus.get(f"par_rrp_{player}_step_signal", "") or "")
            dir_signal = str(self.bus.get(f"par_rrp_{player}_dir_signal", "") or "")
            pot_signal = str(self.bus.get(f"par_rrp_{player}_pot_signal", "") or "")
            if not step_signal or not dir_signal or not pot_signal:
                continue
            try:
                pot_val = max(0.0, min(4095.0, float(self.bus.get(pot_signal, 0) or 0)))
                sens = max(0.0, min(100.0, float(self.bus.get(f"par_rrp_{player}_sens", 50) or 50)))
                speed_mul = int(float(self.bus.get(f"rrp_{player}_speed_mul", 1) or 1))
            except Exception:
                continue
            speed_mul = speed_mul if speed_mul in {1, 2, 3, 4} else 1
            pot_norm = pot_val / 4095.0
            sens_norm = sens / 100.0
            rate_hz = max(0.0, min(1000.0, 1000.0 * sens_norm * float(speed_mul) * pot_norm))
            rt = self._rrp_runtime[player]
            now = time.monotonic()
            elapsed_s = max(0.0, min(0.1, now - float(rt.get("last_tick_ts", now))))
            rt["last_tick_ts"] = now
            rt["pulse_accumulator"] = min(30.0, float(rt.get("pulse_accumulator", 0.0)) + rate_hz * elapsed_s)
            pulse_count = int(rt["pulse_accumulator"])
            if pulse_count <= 0:
                continue
            rt["pulse_accumulator"] = float(rt["pulse_accumulator"]) - pulse_count
            direction = int(self.bus.get(f"par_rrp_{player}_dir", 0) or 0)
            try:
                axis_index = int(self.bus.get(f"rrp_{player}_axis_index", -1) or -1)
                self._apply_rrp_to_axis(axis_index, int(round(pot_val * 1023.0 / 4095.0)), player)
            except Exception:
                pass
            self.force_signal(dir_signal, direction, source="PARCORE_RRP_GEN")
            for _ in range(pulse_count):
                self.force_signal(step_signal, 1, source="PARCORE_RRP_GEN")
                self.force_signal(step_signal, 0, source="PARCORE_RRP_GEN")
            self.force_signal(f"par_rrp_{player}_val", int(pot_val), source="PARCORE_RRP_GEN")
            self.force_signal(f"rrp_{player}_val", int(pot_val), source="PARCORE_RRP_GEN")

    # ------------------------------------------------------------------
    # TAKE / EHR transport
    # ------------------------------------------------------------------
    def take_load(self, path: str | Path) -> TarzanTakeData:
        data = self.take_player.load(path)
        # Transplant z tarzanParBridge.load_take(): jeśli PARcore działa jako klient TSP,
        # przesyła TAKE do miniPC tym samym kontraktem payloadu.
        if self._client_is_connected() and self.tsp_client is not None:
            payload = {
                "name": Path(path).name,
                "columns": data.columns,
                "rows": data.rows,
                "metadata": data.metadata,
                "duration_ms": data.duration_ms,
            }
            try:
                if hasattr(self.tsp_client, "load_take"):
                    self.tsp_client.load_take(payload)
                else:
                    self.tsp_client.call_action("load_take", payload)
            except Exception as exc:
                self._bus_log("TSP_ERROR", f"LOAD_TAKE payload failed: {exc}")
                self._drop_tsp_client("load_take_failed")
        return data

    def take_load_payload(self, payload: Mapping[str, Any]) -> TarzanTakeData:
        """Przyjmuje TAKE z TSP/EHR bez tworzenia dodatkowego pliku logiki.

        Payload zgodny z tarzanParBridge.load_take(): name, columns, rows, metadata, duration_ms.
        Dla lokalnego playera budujemy TarzanTakeData w pamięci.
        """
        name = str(payload.get("name") or "TAKE_REMOTE.txt")
        data = TarzanTakeData(path=Path(name))
        meta = payload.get("metadata") or payload.get("header") or {}
        if isinstance(meta, dict):
            data.header.update({str(k): str(v) for k, v in meta.items()})
        columns = payload.get("columns") or []
        rows = payload.get("rows") or []
        data.columns = [str(c) for c in columns] if isinstance(columns, (list, tuple)) else []
        if isinstance(rows, list):
            data.rows = [dict(r) for r in rows if isinstance(r, Mapping)]
        self.take_player.stop(reset_to_zero=False, log_stop=False)
        self.take_player.take = data
        self.take_player.index = 0
        self.bus.loaded_take_path = name
        self.bus.force_signal("take_number", name, source="TAKE_LOAD_REMOTE")
        self.bus.force_signal("loaded_take_path", name, source="TAKE_LOAD_REMOTE")
        self.bus.force_signal("take_status", "LOADED", source="TAKE_LOAD_REMOTE")
        self.bus.set_take_time(0)
        self._bus_log("TAKE", f"Załadowano TAKE payload: {name}, rows={len(data.rows)}, duration={data.duration_ms} ms")
        return data

    def load_take(self, path: str | Path) -> TarzanTakeData:
        return self.take_load(path)

    def take_play(self) -> None:
        self.take_player.play()

    def play_take(self) -> None:
        self.take_play()

    def take_pause(self) -> None:
        self.take_player.pause()

    def pause_take(self) -> None:
        self.take_pause()

    def take_stop(self) -> None:
        self.take_player.stop()

    def take(self, action: str, value: Any = None) -> Any:
        action_norm = str(action or "").strip().lower()
        if action_norm in {"load", "open"}:
            return self.take_load(value)
        if action_norm == "play":
            return self.take_play()
        if action_norm == "pause":
            return self.take_pause()
        if action_norm == "stop":
            return self.take_stop()
        if action_norm in {"status", "snapshot"}:
            return self.take_playback_status()
        raise ValueError(f"Nieznana akcja TAKE: {action}")

    def stop_take(self) -> None:
        self.take_stop()

    def step_take_index(self, index: int) -> Optional[Dict[str, str]]:
        return self.take_player.step_to_index(index)

    def step_take_time(self, time_ms: int) -> Optional[Dict[str, str]]:
        return self.take_player.step_time(time_ms)

    def take_column_map(self) -> Dict[str, List[str]]:
        return self.mapper.map_take_columns()

    # ------------------------------------------------------------------
    # Nextion bridge — transplant z tarzanParBridge.py bez preview/canvas/GUI toolkit.
    # ------------------------------------------------------------------
    def nextion_connect(self) -> Any:
        if self.nextion is None:
            self._bus_log("NEXTION", "Nextion bridge not configured")
            return False
        if hasattr(self.nextion, "connect_enabled"):
            return self.nextion.connect_enabled()
        if hasattr(self.nextion, "connect"):
            return self.nextion.connect()
        return False

    def nextion_sync(self, force: bool = False, screen_key: str = "nextion_7", **kwargs: Any) -> Any:
        if self.nextion is None:
            return False
        if hasattr(self.nextion, "sync"):
            try:
                return self.nextion.sync(force=force, screen_key=screen_key)
            except TypeError:
                return self.nextion.sync(force=force)
        return False

    def nextion_poll(self, screen_key: str = "nextion_7", **kwargs: Any) -> Any:
        # Publiczne wywołanie z PAR STACJA/PARtext: jednorazowy, nieblokujący
        # odbiór zdarzeń Nextion. Nie tworzy własnego refreshu UI i nie omija Snajpera.
        return self.poll_nextion7_once(block=False)

    # UWAGA: nie robimy aliasu poll = nextion_poll.
    # PARcore ma pełny poll runtime wyżej; Nextion 7 ma osobne nextion_poll().

    # ------------------------------------------------------------------
    # Oś / SOK / sensory / P37
    # ------------------------------------------------------------------
    def test_axis(self, axis: Any, direction: Any = 1, pulses: int = 10, delay_ms: int = 7, enable: bool = True) -> Dict[str, Any]:
        axis_name = self._normalize_axis(axis)
        if axis_name not in AXIS_SIGNAL_BINDINGS:
            raise ValueError(f"Nieznana oś: {axis}")
        bind = AXIS_SIGNAL_BINDINGS[axis_name]
        dir_val = 1 if str(direction).strip().lower() in {"1", "true", "on", "right", "prawo", "+", "cw"} or direction is True else 0
        if enable:
            for n in bind.get("en", []):
                self.force_signal(n, 1, source="PARCORE_AXIS_TEST")
        for n in bind.get("dir", []):
            self.force_signal(n, dir_val, source="PARCORE_AXIS_TEST")
        pulses = max(1, int(pulses))
        for _ in range(pulses):
            for n in bind.get("step", []):
                self.force_signal(n, 1, source="PARCORE_AXIS_TEST")
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            for n in bind.get("step", []):
                self.force_signal(n, 0, source="PARCORE_AXIS_TEST")
        self._increment_axis_counter(axis_name, pulses=pulses, direction=dir_val)
        self.force_signal(f"axis_{axis_name.lower()}_last_error", "", source="PARCORE_AXIS_TEST")
        self.force_signal(f"axis_{axis_name.lower()}_ready", 1, source="PARCORE_AXIS_TEST")
        return {"axis": axis_name, "direction": dir_val, "pulses": pulses}

    def manual_axis_step(self, axis: Any, direction: Any = 1, pulses: int = 10, delay_ms: int = 7) -> Dict[str, Any]:
        """Headless odpowiednik TarzanParPanels._manual_axis_step()."""
        return self.test_axis(axis, direction=direction, pulses=pulses, delay_ms=delay_ms, enable=False)

    def axis_enable(self, axis: Any, enabled: Any = True) -> Dict[str, Any]:
        axis_name = self._normalize_axis(axis)
        if axis_name not in AXIS_SIGNAL_BINDINGS:
            raise ValueError(f"Nieznana oś: {axis}")
        val = 1 if str(enabled).strip().lower() in {"1", "true", "on", "enable", "enabled", "tak", "yes"} or enabled is True else 0
        for n in AXIS_SIGNAL_BINDINGS[axis_name].get("en", []):
            self.force_signal(n, val, source="PARCORE_AXIS_ENABLE")
        self.force_signal(f"axis_{axis_name.lower()}_enabled", val, source="PARCORE_AXIS_ENABLE")
        return {"axis": axis_name, "enabled": val}

    def axis_status(self, axis: Any) -> Dict[str, Any]:
        axis_name = self._normalize_axis(axis)
        if axis_name not in AXIS_SIGNAL_BINDINGS:
            raise ValueError(f"Nieznana oś: {axis}")
        bind = AXIS_SIGNAL_BINDINGS[axis_name]
        return {
            "axis": axis_name,
            "step": {n: self.bus.get(n, 0) for n in bind.get("step", [])},
            "dir": {n: self.bus.get(n, 0) for n in bind.get("dir", [])},
            "en": {n: self.bus.get(n, 0) for n in bind.get("en", [])},
            "pos": {n: self.bus.get(n, 0) for n in bind.get("pos", [])},
            "ready": self.bus.get(f"axis_{axis_name.lower()}_ready", None),
            "last_error": self.bus.get(f"axis_{axis_name.lower()}_last_error", ""),
        }

    def update_limits_status(self) -> str:
        """Headless odpowiednik _update_limits_status z paneli."""
        names = self._get_clean_limit_names()
        active = [str(i + 1) for i, n in enumerate(names) if self.bus.get(n)]
        res = "0" if not active else ",".join(active)
        self.force_signal("sensor_limits_status", res, source="PARCORE_LIMIT_MONITOR")
        return res

    def _group_or_search(self, group: str, needles: List[str]) -> List[str]:
        res: List[str] = []
        for name in self.bus.names():
            try:
                m = self.bus.get_meta(name)
            except Exception:
                m = None
            if (m and getattr(m, "grupa", "") == group) or any(k in name.lower() for k in needles):
                res.append(name)
        return sorted(list(set(res)))

    def _get_clean_limit_names(self) -> List[str]:
        raw = self._group_or_search("KRAŃCÓWKI", ["limit"])
        names: List[str] = []
        seen: set[str] = set()
        for n in raw:
            lbl = self.limit_label(n)
            if any(k in f"{n} {lbl}".upper() for k in ("WOLNY", "FREE", "STATUS")):
                continue
            if lbl.upper() in seen:
                continue
            seen.add(lbl.upper())
            names.append(n)
        return names

    def limit_label(self, name: str) -> str:
        try:
            meta = self.bus.get_meta(name)
            opis = " ".join(str(getattr(meta, "opis", "") or "").split()) if meta else ""
            return opis or name
        except Exception:
            return name

    def sok_set(self, mode: str, direction: Any = 1, pulses: int = 1, delay_ms: int = 70) -> Dict[str, Any]:
        m = str(mode or "PAN").strip().upper()
        if m not in SOK_MODE_MAP:
            raise ValueError(f"Nieznany tryb SOK: {mode}")
        dirs, ctrs = SOK_MODE_MAP[m]
        dir_val = 1 if str(direction).strip().lower() in {"1", "true", "on", "right", "prawo", "+", "cw"} or direction is True else 0
        for n in dirs:
            self.force_signal(n, dir_val, source="PARCORE_SOK")
        for _ in range(max(1, int(pulses))):
            self._pulse_many_signals(ctrs, delay_ms=delay_ms, src="PARCORE_SOK")
        self.force_signal(f"sok_{m.lower()}_last", dir_val, source="PARCORE_SOK")
        return {"mode": m, "direction": dir_val, "pulses": pulses, "dir_signals": dirs, "step_signals": ctrs}

    def sensor_read(self, name: str, default: Any = None) -> Any:
        key = str(name or "").strip()
        if key.lower() in SENSOR_GROUPS:
            return {n: self.bus.get(n, default) for n in SENSOR_GROUPS[key.lower()] if self.bus.exists(n)}
        return self.bus.get(key, default)

    def sensor_test(self, name: str) -> Dict[str, Any]:
        data = self.sensor_read(name, default=None)
        ok = bool(data) if isinstance(data, dict) else data is not None
        self.force_signal(f"sensor_{str(name).lower()}_test_status", "OK" if ok else "NO_DATA", source="PARCORE_SENSOR_TEST")
        return {"sensor": name, "ok": ok, "value": data}

    def test_sensor(self, name: str) -> Dict[str, Any]:
        return self.sensor_test(name)

    def manual_record_arm(self, enabled: Any = True) -> int:
        val = 1 if str(enabled).strip().lower() in {"1", "true", "on", "enable", "enabled", "tak", "yes"} or enabled is True else 0
        sig = "play_p37_step_disconnect_manual"
        self._set_signal(sig, val, source="PARCORE_AUTOMATYKA")
        self.force_signal("poksyg_play_p37_last_value", val, source="PARCORE_AUTOMATYKA")
        self.force_signal("poksyg_play_p37_ack_ok", 1, source="PARCORE_AUTOMATYKA")
        if val:
            self._bus_log("AUTOMATYKA", "PLAY P37=1: aktywny sygnał odłączenia STEP, silniki odłączone")
        else:
            self._bus_log("AUTOMATYKA", "PLAY P37=0: automatyka aktywna, zakaz ręcznego ruchu ramieniem")
        return val

    def _pulse_many_signals(self, names: Sequence[str], delay_ms: int = 10, src: str = "PARCORE_PULSE") -> None:
        for n in names:
            self.force_signal(n, 1, source=src)
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        for n in names:
            self.force_signal(n, 0, source=src)

    # ------------------------------------------------------------------
    # Administracja wykonawcza z paneli PAR: system, EHR/KHR, safety, trace.
    # ------------------------------------------------------------------
    def run_diagnostics(self) -> bool:
        return self.remote_action("run_diagnostics")

    def take_control(self, owner: str = "PAR_LIVE") -> bool:
        self.force_signal("control_owner", owner, source="PARCORE_OWNER")
        return self.remote_action("set_owner", {"owner": owner})

    def clear_axis_errors(self) -> bool:
        self.force_signal("par_last_error", "", source="PARCORE_CLEAR_ERRORS")
        return self.remote_action("axis_status", {"cmd": "clear_alarms"})

    def trace_signal(self, name: str, seconds: int = 30) -> bool:
        if not name:
            return False
        if self._client_is_connected() and self.tsp_client is not None and hasattr(self.tsp_client, "trace_signal"):
            try:
                self.tsp_client.trace_signal(name, seconds=seconds)
                return True
            except Exception as exc:
                self._bus_log("TSP_ERROR", f"trace_signal failed: {exc}")
                self._drop_tsp_client("trace_signal_failed")
        self.force_signal(f"trace_{name}", self.bus.get(name, 0), source="PARCORE_TRACE_LOCAL")
        return True

    def safety_axis_unlock(self, enabled: Any) -> int:
        val = 1 if str(enabled).strip().lower() in {"1", "true", "on", "unlock", "unlocked", "tak", "yes"} or enabled is True else 0
        self.set_signal("cmd_unlock_axes", val, source="PARCORE_SAFETY")
        self.force_signal("safety_axis_unlock", val, source="PARCORE_SAFETY")
        self._bus_log("PAR", f"Requesting physical axis {'UNLOCK' if val else 'LOCK'}.")
        return val

    def ehr_cmd(self, action: str) -> bool:
        sig = f"cmd_ehr_{str(action).strip().lower()}"
        return self.write_output(sig, 1, source="PARCORE_EHR")

    def khr_cmd(self, action: str) -> bool:
        sig = f"cmd_khr_{str(action).strip().lower()}"
        return self.write_output(sig, 1, source="PARCORE_KHR")

    def camera_mode(self, mode: str) -> str:
        value = str(mode or "").strip().upper()
        self.set_signal("khr_active_mode", value, source="PARCORE_CAMERA")
        return value

    def remote_action(self, name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        payload = dict(payload or {})
        if name == "trace_signal" and payload:
            sig = payload.get("name")
            sec = int(payload.get("seconds", 30) or 30)
            if sig:
                return self.trace_signal(str(sig), seconds=sec)
        if self._send_to_tsp_if_ready(lambda c: c.call_action(name, payload), f"call_action {name}"):
            return True
        self._bus_log("PAR", f"Action {name} handled locally/ignored (TSP not connected)")
        return False

    # ------------------------------------------------------------------
    # Komendy wspólne dla TSP / PARtext / Nextion7.
    # ------------------------------------------------------------------
    def call_action(self, action: str, args: Optional[Dict[str, Any]] = None) -> Any:
        args = dict(args or {})
        action_norm = str(action or "").strip().lower()
        aliases = {
            "set_mode": self.set_mode,
            "mode": self.set_mode,
            "rrp_set_axis": self.rrp_set_axis,
            "rrp_axis": self.rrp_set_axis,
            "rrp_set_dir": self.rrp_set_dir,
            "rrp_dir": self.rrp_set_dir,
            "rrp_set_speed": self.rrp_set_speed,
            "rrp_speed": self.rrp_set_speed,
            "rrp_set_sens": self.rrp_set_sens,
            "rrp_sens": self.rrp_set_sens,
            "rrp_set_pot": self.rrp_set_pot,
            "take_load": self.take_load,
            "load_take": self.take_load,
            "take_play": self.take_play,
            "play_take": self.take_play,
            "take_pause": self.take_pause,
            "pause_take": self.take_pause,
            "take_stop": self.take_stop,
            "stop_take": self.take_stop,
            "test_axis": self.test_axis,
            "axis_test": self.test_axis,
            "sok_set": self.sok_set,
            "sensor_read": self.sensor_read,
            "sensor_test": self.sensor_test,
            "manual_record_arm": self.manual_record_arm,
            "manual_axis_step": self.manual_axis_step,
            "axis_enable": self.axis_enable,
            "axis_status": self.axis_status,
            "update_limits_status": self.update_limits_status,
            "run_diagnostics": self.run_diagnostics,
            "take_control": self.take_control,
            "clear_axis_errors": self.clear_axis_errors,
            "trace_signal": self.trace_signal,
            "safety_axis_unlock": self.safety_axis_unlock,
            "ehr_cmd": self.ehr_cmd,
            "khr_cmd": self.khr_cmd,
            "camera_mode": self.camera_mode,
            "nextion_connect": self.nextion_connect,
            "nextion_sync": self.nextion_sync,
            "nextion_poll": self.nextion_poll,
            "connect_screen": self.connect_screen,
            "disconnect_screen": self.disconnect_screen,
            "sync": self.sync,
            "get_page": self.get_page,
            "set_page": self.set_page,
            "next_page": self.next_page,
            "prev_page": self.prev_page,
            "clear_transport_log": self.clear_transport_log,
            "connect_enabled": self.connect_enabled,
            "poll": self.poll,
            "read_input": self.read_input,
            "reset_signals": self.reset_signals,
            "force_or_toggle": self._final_force_or_toggle,
            "signal_toggle": self._final_force_or_toggle,
            "all_signals_clickable": self._all_signals_clickable,
            "register_step_dir_snajper_target": self.register_step_dir_snajper_target,
            "ensure_step_dir_multi_snajper": self._ensure_step_dir_multi_snajper,
            "ensure_section_snajper": self._ensure_section_snajper,
            "ensure_log_take_nextion_snajper_targets": self._ensure_log_take_nextion_snajper_targets,
            "snajper_fire_log_take_nextion": self.snajper_fire_log_take_nextion,
            "fire_nextion_physical_resync": self.fire_nextion_physical_resync,
            "fire_nextion_page_loaded_resync": self.fire_nextion_page_loaded_resync,
            "preview_rrp_tap": self.preview_rrp_tap,
            "preview_rrp_set_value": self.preview_rrp_set_value,
            "get_rrp_state": self.get_rrp_state,
            "get_nextion_monitor_state": self.get_nextion_monitor_state,
            "apply_rrp_to_axis": self._apply_rrp_to_axis,
            "build_text_preview": self.build_text_preview,
            "publish_text_previews": self.publish_text_previews,
            "build_par_preview": self.build_par_preview,
            "build_nextion7_preview": self.build_nextion7_preview,
            "build_take_preview": self.build_take_preview,
            "build_rrp_preview": self.build_rrp_preview,
            "build_sensors_preview": self.build_sensors_preview,
            "build_axis_preview": self.build_axis_preview,
            "build_snajper_preview": self.build_snajper_preview,
            "log_par_event": self.log_par_event,
            "log_nextion7_event": self.log_nextion7_event,
            "build_par_log_preview": self.build_par_log_preview,
            "build_nextion7_log_preview": self.build_nextion7_log_preview,
            "set_signal": self.set_signal,
            "force_signal": self.force_signal,
            "_force_signal": self._force_signal,
            "_manual_axis_step": self._manual_axis_step,
            "_update_limits_status": self._update_limits_status,
            "_on_bus_signal_change": self._on_bus_signal_change,
            "register_log_snajper_widget": self.register_log_snajper_widget,
            "snajper_log_fire": self.snajper_log_fire,
            "snajper_take_fire": self.snajper_take_fire,
            "snajper_step_dir_fire": self.snajper_step_dir_fire,
            "public_api": self.public_api,
            "public_entrypoints": self.public_entrypoints,
            "assert_public_contract": self.assert_public_contract,
            "take_status": self.take_playback_status,
            "take_playback_status": self.take_playback_status,
            # MODE / Snajper systemowy / NextionBridge / TFD/CLAP/TC.
            "start_mode_logic": self.start_mode_logic,
            "stop_mode_logic": self.stop_mode_logic,
            "handle_system_commands": self._handle_system_commands,
            "manage_control_owner": self._manage_control_owner,
            "handle_manual_control": self._handle_manual_control,
            "handle_auto_playback": self._handle_auto_playback,
            "ensure_system_snajper": self.ensure_system_snajper,
            "register_adapter": self.register_adapter,
            "register_signal": self.register_signal,
            "register_signals": self.register_signals,
            "register_target": self.register_target,
            "register_targets": self.register_targets,
            "fire_from_signal": self.fire_from_signal,
            "fire_many": self.fire_many,
            "fire_with_policy": self.fire_with_policy,
            "clear_scope": self.clear_scope,
            "clear_all": self.clear_all,
            "set_refresh_policy": self.set_refresh_policy,
            "cancel_refresh_policy": self.cancel_refresh_policy,
            "update_target": self.update_target,
            "unregister_adapter": self.unregister_adapter,
            "clear_adapter": self.clear_adapter,
            "refresh_policy_interval_ms": self.refresh_policy_interval_ms,
            "flush_policy": self._flush_policy,
            "rebuild_reverse_signal_map": self._rebuild_reverse_signal_map,
            "enabled": self._enabled,
            "page_ids": self._page_ids,
            "page_id_from_index": self._page_id_from_index,
            "connect_enabled": self.connect_enabled,
            "connect_screen": self.connect_screen,
            "disconnect_screen": self.disconnect_screen,
            "disconnect_all": self.disconnect_all,
            "sync": self.sync,
            "get_page": self.get_page,
            "set_page": self.set_page,
            "next_page": self.next_page,
            "prev_page": self.prev_page,
            "request_current_page": self._request_current_page,
            "handle_touch_event": self._handle_touch_event,
            "queue_snajper_command": self.queue_snajper_command,
            "flush_snajper_commands": self.flush_snajper_commands,
            "refresh_physical_nextion_page_from_state": self._refresh_physical_nextion_page_from_state,
            "append_transport_log": self._append_transport_log,
            "get_recent_transport_log": self.get_recent_transport_log,
            "clear_transport_log": self.clear_transport_log,
            "toggle_clap_tc": self._toggle_clap_tc,
            "set_clap_tc": self._set_clap_tc,
            "publish_clap_tc_state": self._publish_clap_tc_state,
            "update_clap_tc_for_snajper": self._update_clap_tc_for_snajper,
            "play_clap_audio": self._play_clap_audio,
            "bootstrap_tfd_metadata_from_json": self._bootstrap_tfd_metadata_from_json,
            "read_tfd_metadata_json": self._read_tfd_metadata_json,
            "write_tfd_meta_value": self._write_tfd_meta_value,
            "read_tfd_meta_value": self._read_tfd_meta_value,
            "handle_tfd_meta_event": self._handle_tfd_meta_event,
            "show_tfd_save_status": self._show_tfd_save_status,
            "update_tfd_save_status_for_snajper": self._update_tfd_save_status_for_snajper,
            "snapshot": self.snapshot,
        }
        if action_norm not in aliases:
            raise ValueError(f"Nieznana akcja PARcore: {action}")
        fn = aliases[action_norm]
        if action_norm in {"take_play", "play_take", "take_pause", "pause_take", "take_stop", "stop_take", "snapshot", "update_limits_status", "run_diagnostics", "take_control", "clear_axis_errors", "nextion_connect", "nextion_poll", "poll", "all_signals_clickable", "ensure_step_dir_multi_snajper", "ensure_log_take_nextion_snajper_targets", "get_rrp_state", "get_nextion_monitor_state", "public_api", "public_entrypoints", "assert_public_contract", "take_status", "take_playback_status", "build_par_preview", "build_nextion7_preview", "build_take_preview", "build_rrp_preview", "build_sensors_preview", "build_axis_preview", "build_snajper_preview", "build_par_log_preview", "build_nextion7_log_preview", "start_mode_logic", "stop_mode_logic", "handle_system_commands", "handle_manual_control", "handle_auto_playback", "ensure_system_snajper", "disconnect_all", "sync", "next_page", "prev_page", "flush_snajper_commands", "clear_transport_log", "toggle_clap_tc", "publish_clap_tc_state", "update_clap_tc_for_snajper", "play_clap_audio", "bootstrap_tfd_metadata_from_json", "read_tfd_metadata_json"}:
            return fn()  # type: ignore[misc]
        if action_norm == "nextion_sync":
            return fn(bool(args.get("force", False)))  # type: ignore[misc]
        if action_norm == "fire_nextion_physical_resync":
            return fn(bool(args.get("fast", False)))  # type: ignore[misc]
        if action_norm == "fire_nextion_page_loaded_resync":
            return fn(args.get("page_id", args.get("page", "")))  # type: ignore[misc]
        if action_norm == "preview_rrp_tap":
            return fn(args.get("screen_key", "nextion_7"), args.get("key", args.get("value", "")))  # type: ignore[misc]
        if action_norm == "preview_rrp_set_value":
            return fn(args.get("screen_key", "nextion_7"), args.get("player", "p1"), args.get("value", args.get("sens", 50)))  # type: ignore[misc]
        if action_norm == "apply_rrp_to_axis":
            return fn(args.get("axis_index", args.get("axis", 0)), args.get("value", 512), args.get("player", "p1"))  # type: ignore[misc]
        if action_norm == "ensure_section_snajper":
            return fn(args.get("section", ""), args.get("signals"))  # type: ignore[misc]
        if action_norm == "manage_control_owner":
            return fn(args.get("mode", args.get("active_mode", "tM")), args.get("owner", args.get("control_owner", "PAR_LIVE")))  # type: ignore[misc]
        if action_norm in {"register_signal"}:
            return fn(args.get("raw_signal", args.get("name", "")), args.get("logical_signal", args.get("value", args.get("name", ""))))  # type: ignore[misc]
        if action_norm in {"fire_from_signal"}:
            return fn(args.get("signal", args.get("name", "")), args.get("value", None))  # type: ignore[misc]
        if action_norm in {"fire_many", "register_signals", "register_targets"}:
            return fn(args.get("values", args.get("mapping", args)))  # type: ignore[misc]
        if action_norm in {"clear_scope", "cancel_refresh_policy"}:
            return fn(args.get("scope", args.get("name", args.get("value", ""))))  # type: ignore[misc]
        if action_norm == "set_refresh_policy":
            return fn(args.get("name", args.get("policy", "LIVE_FAST")), args.get("interval_ms", args.get("value", 50)))  # type: ignore[misc]
        if action_norm in {"connect_enabled", "connect_screen", "disconnect_screen", "get_page", "request_current_page", "refresh_physical_nextion_page_from_state"}:
            return fn(args.get("screen_key", args.get("screen", "nextion_7")))  # type: ignore[misc]
        if action_norm == "set_page":
            return fn(args.get("screen_key", args.get("screen", "nextion_7")), args.get("page", args.get("page_id", args.get("value", ""))))  # type: ignore[misc]
        if action_norm == "handle_touch_event":
            return fn(args.get("screen_key", args.get("screen", "nextion_7")), args.get("page", args.get("page_id", "")), args.get("component_id", args.get("component", args.get("id", ""))), args.get("event_type", args.get("value", None)))  # type: ignore[misc]
        if action_norm == "queue_snajper_command":
            return fn(args.get("command", args.get("value", args)))  # type: ignore[misc]
        if action_norm == "append_transport_log":
            return fn(args.get("line", args.get("text", args.get("value", ""))))  # type: ignore[misc]
        if action_norm == "get_recent_transport_log":
            return fn(args.get("limit", 50))  # type: ignore[misc]
        if action_norm == "set_clap_tc":
            return fn(args.get("running", args.get("enabled", args.get("value", True))))  # type: ignore[misc]
        if action_norm == "write_tfd_meta_value":
            return fn(args.get("key", args.get("name", "")), args.get("value", ""))  # type: ignore[misc]
        if action_norm == "read_tfd_meta_value":
            return fn(args.get("key", args.get("name", "")), args.get("default", ""))  # type: ignore[misc]
        if action_norm == "handle_tfd_meta_event":
            return fn(args.get("key", args.get("name", "")), args.get("value", ""))  # type: ignore[misc]
        if action_norm == "show_tfd_save_status":
            return fn(args.get("ok", True), args.get("seconds", 2.0))  # type: ignore[misc]
        if action_norm == "update_tfd_save_status_for_snajper":
            return fn(args.get("ok", True))  # type: ignore[misc]
        if action_norm in {"set_mode", "mode"}:
            return fn(args.get("mode", args.get("value", "TEST")))  # type: ignore[misc]
        if action_norm in {"rrp_set_axis", "rrp_axis"}:
            return fn(args.get("player", "p1"), args.get("axis", args.get("value", "")))  # type: ignore[misc]
        if action_norm in {"rrp_set_dir", "rrp_dir"}:
            return fn(args.get("player", "p1"), args.get("direction", args.get("dir", args.get("value", 0))))  # type: ignore[misc]
        if action_norm in {"rrp_set_speed", "rrp_speed"}:
            return fn(args.get("player", "p1"), args.get("mul", args.get("speed", args.get("value", 1))))  # type: ignore[misc]
        if action_norm in {"rrp_set_sens", "rrp_sens"}:
            return fn(args.get("player", "p1"), args.get("sens", args.get("value", 50)))  # type: ignore[misc]
        if action_norm == "rrp_set_pot":
            return fn(args.get("player", "p1"), args.get("pot", args.get("value", 0)))  # type: ignore[misc]
        if action_norm in {"take_load", "load_take"}:
            return fn(args.get("path") or args.get("file") or args.get("value"))  # type: ignore[misc]
        if action_norm in {"test_axis", "axis_test"}:
            return fn(args.get("axis", args.get("value", "")), args.get("direction", 1), args.get("pulses", 10), args.get("delay_ms", 7))  # type: ignore[misc]
        if action_norm == "sok_set":
            return fn(args.get("mode", args.get("value", "PAN")), args.get("direction", 1), args.get("pulses", 1), args.get("delay_ms", 70))  # type: ignore[misc]
        if action_norm in {"sensor_read", "sensor_test"}:
            return fn(args.get("name", args.get("sensor", args.get("value", ""))))  # type: ignore[misc]
        if action_norm == "manual_record_arm":
            return fn(args.get("enabled", args.get("value", True)))  # type: ignore[misc]
        if action_norm == "manual_axis_step":
            return fn(args.get("axis", args.get("value", "")), args.get("direction", 1), args.get("pulses", 10), args.get("delay_ms", 7))  # type: ignore[misc]
        if action_norm == "axis_enable":
            return fn(args.get("axis", args.get("value", "")), args.get("enabled", True))  # type: ignore[misc]
        if action_norm == "axis_status":
            return fn(args.get("axis", args.get("value", "")))  # type: ignore[misc]
        if action_norm == "trace_signal":
            return fn(args.get("name", args.get("signal", args.get("value", ""))), int(args.get("seconds", 30) or 30))  # type: ignore[misc]
        if action_norm == "safety_axis_unlock":
            return fn(args.get("enabled", args.get("value", True)))  # type: ignore[misc]
        if action_norm in {"ehr_cmd", "khr_cmd", "camera_mode"}:
            return fn(args.get("action", args.get("mode", args.get("value", ""))))  # type: ignore[misc]
        if action_norm == "read_input":
            return fn(args.get("name", args.get("signal", args.get("value", ""))), args.get("default", None))  # type: ignore[misc]
        if action_norm == "reset_signals":
            return fn(args.get("names"), args.get("value", 0))  # type: ignore[misc]
        if action_norm in {"force_or_toggle", "signal_toggle"}:
            return fn(args.get("name", args.get("signal", "")), args.get("value", None))  # type: ignore[misc]
        if action_norm == "register_step_dir_snajper_target":
            return fn(args.get("axis", args.get("value", "")), args.get("section", "PARCORE"))  # type: ignore[misc]
        if action_norm == "snajper_fire_log_take_nextion":
            return fn(args.get("section", "take"), args.get("payload", {}))  # type: ignore[misc]
        if action_norm == "build_text_preview":
            return fn(args.get("target", "all"))  # type: ignore[misc]
        if action_norm == "publish_text_previews":
            return fn(args.get("target", "all"))  # type: ignore[misc]
        if action_norm == "log_par_event":
            return fn(args.get("message", args.get("value", "")), args.get("source", "PAR"))  # type: ignore[misc]
        if action_norm == "log_nextion7_event":
            return fn(args.get("message", args.get("value", "")), args.get("source", "NEXTION7"))  # type: ignore[misc]
        if action_norm in {"set_signal", "force_signal"}:
            return fn(args.get("name", args.get("signal", "")), args.get("value"))  # type: ignore[misc]
        return fn(**args)  # type: ignore[misc]

    def dispatch_nextion7(self, event: str, value: Any = None) -> Any:
        """Lokalny adapter Nextion 7 → PARcore, bez UI.

        Obsługuje formaty z Nextiona i proste komendy tekstowe:
        rrp:p1_ax=4, rrp:p1_dir=1, rrp:p1_pot=2048, mode:live, take:play,
        sensor:light, safety:unlock, manual_record_arm=1.
        """
        raw = str(event or "").strip()
        if "=" in raw:
            raw, value = raw.split("=", 1)
        key = raw.lower().strip()
        key = key.replace("rrp:", "")

        if key in {"stop"} and str(value) in {"1", "true", "True", "ON", "on"}:
            return self._handle_rrp_event("rrp:stop=1")
        if key in {"p1_ax", "p1_axis"}:
            self._handle_rrp_event(f"rrp:p1_ax={value}")
            return self.rrp_set_axis("p1", value)
        if key in {"p2_ax", "p2_axis"}:
            self._handle_rrp_event(f"rrp:p2_ax={value}")
            return self.rrp_set_axis("p2", value)
        if key in {"p1_dir", "p1_dr"}:
            self._handle_rrp_event(f"rrp:p1_dr={value}")
            return self.rrp_set_dir("p1", value)
        if key in {"p2_dir", "p2_dr"}:
            self._handle_rrp_event(f"rrp:p2_dr={value}")
            return self.rrp_set_dir("p2", value)
        if key in {"p1_pot", "p1_val"}:
            return self.rrp_set_pot("p1", value)
        if key in {"p2_pot", "p2_val"}:
            return self.rrp_set_pot("p2", value)
        if key in {"p1_speed", "p1_mul"}:
            return self.rrp_set_speed("p1", value)
        if key in {"p2_speed", "p2_mul"}:
            return self.rrp_set_speed("p2", value)
        if key in {"p1_sens", "p1_sensitivity", "p1_se"}:
            self._handle_rrp_event(f"rrp:p1_se={value}")
            return self.rrp_set_sens("p1", value)
        if key in {"p2_sens", "p2_sensitivity", "p2_se"}:
            self._handle_rrp_event(f"rrp:p2_se={value}")
            return self.rrp_set_sens("p2", value)

        if key.startswith("mode:"):
            return self.set_mode(key.split(":", 1)[1].upper())
        if key in {"mode", "set_mode"}:
            return self.set_mode(str(value or "TEST").upper())

        if key in {"take:play", "take_play", "play"}:
            return self.take_play()
        if key in {"take:pause", "take_pause", "pause"}:
            return self.take_pause()
        if key in {"take:stop", "take_stop", "stop"}:
            return self.take_stop()

        if key.startswith("sensor:"):
            return self.sensor_test(key.split(":", 1)[1])
        if key.startswith("sok:"):
            return self.sok_set(key.split(":", 1)[1], value if value is not None else 1)
        if key.startswith("axis:test:"):
            return self.test_axis(key.split(":", 2)[2], value if value is not None else 1)
        if key in {"safety:unlock", "axis_unlock", "unlock_axes"}:
            return self.safety_axis_unlock(1 if value is None else value)
        if key in {"safety:lock", "axis_lock", "lock_axes"}:
            return self.safety_axis_unlock(0)
        if key in {"manual_record_arm", "arm_manual", "p37"}:
            return self.manual_record_arm(1 if value is None else value)

        raise ValueError(f"Nieznany event Nextion7 dla PARcore: {event}")

    def snapshot(self, include_meta: bool = False) -> Dict[str, Any]:
        snap = self.bus.snapshot(include_meta=include_meta)
        snap["parcore"] = {
            "state": self.bus.get("parcore_state", "READY"),
            "mode": getattr(self.bus, "mode", "TEST"),
            "take_loaded": str(getattr(self.bus, "loaded_take_path", "") or ""),
            "take_playing": bool(self.take_player.playing),
            "rrp": {
                "p1_axis": self.bus.get("par_rrp_p1_selected_axis", ""),
                "p2_axis": self.bus.get("par_rrp_p2_selected_axis", ""),
                "p1_index": self.bus.get("rrp_p1_axis_index", -1),
                "p2_index": self.bus.get("rrp_p2_axis_index", -1),
            },
            "take": self.take_playback_status(),
            "public_entrypoints": list(PARCORE_PUBLIC_ENTRYPOINTS),
            "client_routes": dict(PARCORE_CLIENT_ROUTES),
            "last_client": self.bus.get("parcore_last_client", ""),
            "last_action": self.bus.get("parcore_last_action", ""),
        }
        return snap


    # ------------------------------------------------------------------
    # tekstowe preview i logi PAR / Nextion 7.
    # To jest WYJŚCIE informacyjne z SignalBus/PARcore, nie parser komend.
    # Komendy Nextion 7 nadal idą przez event bridge -> dispatch_nextion7(...).
    # ------------------------------------------------------------------
    def build_text_preview(self, target: str = "all") -> Dict[str, str]:
        """Buduje wspólny tekstowy podgląd stanu dla PAR-GUI i Nextion 7.

        Preview wolno pokazywać w PAR i Nextion 7. Nie wolno z niego wykonywać
        komend ani zgadywać eventów. Źródłem prawdy pozostaje SignalBus.
        """
        target_norm = str(target or "all").strip().lower()
        sections = {
            "par": self.build_par_preview(),
            "nextion7": self.build_nextion7_preview(),
            "take": self.build_take_preview(),
            "rrp": self.build_rrp_preview(),
            "sensors": self.build_sensors_preview(),
            "axis": self.build_axis_preview(),
            "snajper": self.build_snajper_preview(),
            "par_log": self.build_par_log_preview(),
            "nextion7_log": self.build_nextion7_log_preview(),
        }
        if target_norm not in {"all", "*", ""}:
            return {target_norm: sections.get(target_norm, "")}
        return sections

    def publish_text_previews(self, target: str = "all") -> Dict[str, str]:
        """Publikuje tekstowe preview do SignalBus dla PAR-GUI i Nextion 7."""
        previews = self.build_text_preview(target)
        signal_map = {
            "par": "par_text_preview",
            "nextion7": "nextion7_text_preview",
            "take": "take_text_preview",
            "rrp": "rrp_text_preview",
            "sensors": "sensor_text_preview",
            "axis": "axis_text_preview",
            "snajper": "snajper_text_preview",
            "par_log": "par_log_preview",
            "nextion7_log": "nextion7_log_preview",
        }
        for key, text in previews.items():
            signal = signal_map.get(key)
            if signal:
                self.force_signal(signal, text, source="PARCORE_TEXT_PREVIEW")
        # Główne widoki, tak jak dawniej w PAR/Nextion, tylko wywołane z rdzenia.
        if "par" in previews:
            self.force_signal("par_preview_text", previews["par"], source="PARCORE_TEXT_PREVIEW")
        if "nextion7" in previews:
            self.force_signal("nextion7_preview_text", previews["nextion7"], source="PARCORE_TEXT_PREVIEW")
        return previews

    def build_par_preview(self) -> str:
        lines = [
            "PARcore",
            f"mode={getattr(self.bus, 'mode', 'TEST')}",
            f"state={self._preview_get('parcore_state', 'READY')}",
            f"par={self._preview_get('par_state', '')}",
            f"tsp={self._preview_get('tsp_state', '')}",
            f"hardware={self._preview_get('hardware_state', '')}",
            f"owner={self._preview_get('control_owner', '')}",
            f"last_client={self._preview_get('parcore_last_client', '')}",
            f"last_action={self._preview_get('parcore_last_action', '')}",
            f"last_error={self._preview_get('par_last_error', '')}",
        ]
        return self._join_preview(lines)

    def build_nextion7_preview(self) -> str:
        lines = [
            "NEXTION 7",
            f"state={self._preview_get('nextion7_state', 'UNKNOWN')}",
            f"event_source={self._preview_get('nextion7_event_source', '')}",
            f"last_event={self._preview_get('nextion7_last_event', '')}",
            f"last_result={self._preview_get('nextion7_last_result', '')}",
            self.build_rrp_preview(),
            self.build_take_preview(),
        ]
        return self._join_preview(lines)

    def build_take_preview(self) -> str:
        status = self.take_playback_status()
        lines = [
            "TAKE",
            f"status={status.get('status', self._preview_get('take_status', 'EMPTY'))}",
            f"loaded={status.get('loaded', bool(self.take_player.take))}",
            f"path={status.get('path', self._preview_get('loaded_take_path', ''))}",
            f"time_ms={status.get('time_ms', self._preview_get('take_time_ms', 0))}",
            f"index={status.get('index', getattr(self.take_player, 'index', 0))}",
            f"duration_ms={status.get('duration_ms', 0)}",
        ]
        return self._join_preview(lines)

    def build_rrp_preview(self) -> str:
        lines = [
            "RRP",
            f"p1_axis={self._preview_get('par_rrp_p1_selected_axis', '')} idx={self._preview_get('rrp_p1_axis_index', -1)} dir={self._preview_get('par_rrp_p1_dir', 0)} speed={self._preview_get('rrp_p1_speed_mul', 1)} sens={self._preview_get('par_rrp_p1_sens', '')} val={self._preview_get('par_rrp_p1_val', self._preview_get('rrp_p1_val', ''))}",
            f"p2_axis={self._preview_get('par_rrp_p2_selected_axis', '')} idx={self._preview_get('rrp_p2_axis_index', -1)} dir={self._preview_get('par_rrp_p2_dir', 0)} speed={self._preview_get('rrp_p2_speed_mul', 1)} sens={self._preview_get('par_rrp_p2_sens', '')} val={self._preview_get('par_rrp_p2_val', self._preview_get('rrp_p2_val', ''))}",
            f"pot_h={self._preview_first(['sensor_rrp_pot_h', 'play_p45_rrp_pot_h'], '')}",
            f"pot_v={self._preview_first(['sensor_rrp_pot_v', 'play_p47_rrp_pot_v'], '')}",
        ]
        return self._join_preview(lines)

    def build_sensors_preview(self) -> str:
        groups = ("rrp", "limits", "light", "temperature", "xyz", "shock")
        lines = ["SENSORY"]
        for group in groups:
            data = self.sensor_read(group, default="")
            if isinstance(data, dict):
                compact = ", ".join(f"{k}={self._short_preview_value(v)}" for k, v in list(data.items())[:8])
            else:
                compact = self._short_preview_value(data)
            lines.append(f"{group}: {compact}")
        return self._join_preview(lines)

    def build_axis_preview(self) -> str:
        lines = ["OSIE"]
        for axis in ("CAM_H", "CAM_V", "CAM_F", "ARM_T", "ARM_H", "ARM_V", "DRON"):
            try:
                st = self.axis_status(axis)
            except Exception:
                st = {"axis": axis}
            pos = self._short_preview_value(st.get("pos", ""))
            ready = self._short_preview_value(st.get("ready", ""))
            enabled = self._short_preview_value(st.get("enabled", ""))
            err = self._short_preview_value(st.get("last_error", ""))
            lines.append(f"{axis}: pos={pos} ready={ready} en={enabled} err={err}")
        return self._join_preview(lines)

    def build_snajper_preview(self) -> str:
        lines = [
            "SNAJPER",
            f"section={self._preview_get('snajper_last_section', '')}",
            f"packet={self._short_preview_value(self._preview_get('snajper_last_packet', ''))}",
            f"state={self._preview_get('snajper_state', '')}",
        ]
        return self._join_preview(lines)

    def log_par_event(self, message: Any, source: str = "PAR") -> str:
        entry = self._format_log_entry(source, message)
        buf = self._append_preview_buffer("_par_text_log_buffer", entry)
        text = "\n".join(buf)
        self.force_signal("par_log_preview", text, source="PARCORE_PAR_LOG")
        self.force_signal("par_last_log", entry, source="PARCORE_PAR_LOG")
        return entry

    def log_nextion7_event(self, message: Any, source: str = "NEXTION7") -> str:
        entry = self._format_log_entry(source, message)
        buf = self._append_preview_buffer("_nextion7_text_log_buffer", entry)
        text = "\n".join(buf)
        self.force_signal("nextion7_log_preview", text, source="PARCORE_N7_LOG")
        self.force_signal("nextion7_last_log", entry, source="PARCORE_N7_LOG")
        return entry

    def build_par_log_preview(self, limit: int = 20) -> str:
        buf = list(getattr(self, "_par_text_log_buffer", []))[-max(1, int(limit)):]
        return "\n".join(buf)

    def build_nextion7_log_preview(self, limit: int = 20, screen_key: str = "nextion_7", **kwargs: Any) -> List[str]:
        buf = list(getattr(self, "_nextion7_text_log_buffer", []))[-max(1, int(limit)):]
        return buf

    def _append_preview_buffer(self, attr: str, entry: str, limit: int = 80) -> List[str]:
        buf = list(getattr(self, attr, []))
        buf.append(str(entry))
        buf = buf[-max(1, int(limit)):]
        setattr(self, attr, buf)
        return buf

    def _format_log_entry(self, source: str, message: Any) -> str:
        ts = time.strftime("%H:%M:%S")
        msg = self._short_preview_value(message, limit=220)
        return f"{ts} [{source}] {msg}"

    def _preview_get(self, name: str, default: Any = "") -> Any:
        try:
            return self.bus.get(name, default)
        except Exception:
            return default

    def _preview_first(self, names: Sequence[str], default: Any = "") -> Any:
        for name in names:
            try:
                if self.bus.exists(name):
                    value = self.bus.get(name, default)
                    if value not in (None, ""):
                        return value
            except Exception:
                continue
        return default

    def _short_preview_value(self, value: Any, limit: int = 120) -> str:
        try:
            if isinstance(value, (dict, list, tuple)):
                text = json.dumps(value, ensure_ascii=False, default=str)
            else:
                text = str(value)
        except Exception:
            text = repr(value)
        text = text.replace("\r", " ").strip()
        if len(text) > limit:
            return text[: max(0, limit - 3)] + "..."
        return text

    def _join_preview(self, lines: Sequence[Any]) -> str:
        return "\n".join(str(line) for line in lines if str(line) != "")


    # ------------------------------------------------------------------
    # MAIN Runtime miniPC uruchamia i spina komponenty.
    # SignalBus / TSP Server / PARcore / HardwareBridge / Nextion 5 / Nextion 7.
    # To nadal nie jest UI: to runtime bind i kierowanie zdarzeń do tych samych metod PARcore.
    # ------------------------------------------------------------------
    def attach_main_runtime(
        self,
        tsp_server: Any = None,
        hardware_bridge: Any = None,
        nextion7_bridge: Any = None,
        enable_nextion7: bool = True,
    ) -> Dict[str, Any]:
        """Spina PARcore z MAIN Runtime miniPC bez tworzenia drugiego modelu.

        MAIN tworzy jedną instancję PARcore i przekazuje tu istniejący TSP Server
        oraz HardwareBridge. TSP provider deleguje CALL_ACTION do PARcore, a lokalny
        Nextion 7 jest odpytywany jako HMI/event source i schodzi do dispatch_nextion7(...).
        """
        status: Dict[str, Any] = {"ok": True, "components": {}}
        if hardware_bridge is not None:
            status["components"]["hardware_bridge"] = self.bind_hardware_bridge(hardware_bridge)
        if tsp_server is not None:
            status["components"]["tsp_server"] = self.bind_tsp_server(tsp_server)
            hw = getattr(tsp_server, "hw_bridge", None)
            if hw is not None and self.hardware_bridge is None:
                status["components"]["hardware_bridge"] = self.bind_hardware_bridge(hw)
        if enable_nextion7:
            status["components"]["nextion7"] = self.start_nextion7_runtime(nextion7_bridge)
        try:
            status["components"]["snajper"] = bool(self.ensure_system_snajper())
        except Exception as exc:
            status["components"]["snajper"] = f"ERROR:{exc}"
        try:
            self.start_mode_logic(prefer_existing=True)
            status["components"]["mode_logic"] = True
        except Exception as exc:
            status["components"]["mode_logic"] = f"ERROR:{exc}"
            self._bus_log("MODE_ERROR", f"start_mode_logic failed: {exc}")
        try:
            self._bootstrap_tfd_metadata_from_json()
            status["components"]["tfd_metadata"] = True
        except Exception as exc:
            status["components"]["tfd_metadata"] = f"ERROR:{exc}"
        self.force_signal("parcore_runtime_attached", 1, source="PARCORE_MAIN")
        self.force_signal("parcore_state", "RUNTIME_ATTACHED", source="PARCORE_MAIN")
        return status

    def bind_hardware_bridge(self, hardware_bridge: Any) -> bool:
        self.hardware_bridge = hardware_bridge
        self.force_signal("hardware_state", "CONNECTED", source="PARCORE_MAIN")
        self._bus_log("PARCORE_MAIN", "HardwareBridge bound to PARcore")
        return True

    def bind_tsp_server(self, tsp_server: Any) -> bool:
        self.tsp_server = tsp_server
        provider = getattr(tsp_server, "provider", None)
        if provider is not None:
            # Preferujemy oficjalną metodę, ale zostawiamy fallback przez atrybut,
            # żeby nie rozbijać starszego providera.
            bound = False
            for method in ("bind_parcore", "set_parcore_delegate", "set_runtime_delegate"):
                fn = getattr(provider, method, None)
                if callable(fn):
                    fn(self)
                    bound = True
                    break
            if not bound:
                setattr(provider, "parcore", self)
        setattr(tsp_server, "parcore", self)
        self.force_signal("tsp_state", "PARCORE_BOUND", source="PARCORE_MAIN")
        self._bus_log("PARCORE_MAIN", "TSP Server bound to PARcore")
        return True

    def start_nextion7_runtime(self, nextion7_bridge: Any = None) -> Dict[str, Any]:
        """Start lokalnego toru Nextion 7 przez realny adapter/bridge eventów.

        Ten kod nie czyta eventów z logów. Bridge ma przekazać zdarzenie przez
        callback albo jedną ze zwykłych metod eventowych: read_events/get_events/
        poll_events/read_event/recv_event. PARcore tylko routuje taki event do
        dispatch_nextion7(...).
        """
        if nextion7_bridge is not None:
            self._nextion7_bridge = nextion7_bridge
        elif self._nextion7_bridge is None:
            if self.nextion is not None:
                self._nextion7_bridge = self.nextion
            elif TarzanNextionBridge is not None:
                try:
                    self._nextion7_bridge = TarzanNextionBridge(self.bus)
                    self.nextion = self._nextion7_bridge
                except Exception as exc:
                    self.force_signal("nextion7_state", "ERROR", source="PARCORE_N7")
                    self.force_signal("par_last_error", f"Nextion 7 bridge init failed: {exc}", source="PARCORE_N7")
                    return {"ok": False, "error": str(exc)}
        bridge = self._nextion7_bridge
        if bridge is None:
            self.force_signal("nextion7_state", "DISABLED", source="PARCORE_N7")
            return {"ok": False, "error": "no_nextion7_bridge"}
        self._bind_nextion7_event_source(bridge)
        connected = False
        try:
            if hasattr(bridge, "connect_screen"):
                connected = bool(bridge.connect_screen("nextion_7"))
            elif hasattr(bridge, "connect_nextion7"):
                connected = bool(bridge.connect_nextion7())
            elif hasattr(bridge, "connect_enabled"):
                bridge.connect_enabled()
                connected = True
            elif hasattr(bridge, "connect"):
                connected = bool(bridge.connect())
            self.force_signal("nextion7_state", "CONNECTED" if connected else "NOT_CONNECTED", source="PARCORE_N7")
        except Exception as exc:
            self.force_signal("nextion7_state", "ERROR", source="PARCORE_N7")
            self.force_signal("par_last_error", f"Nextion 7 connect failed: {exc}", source="PARCORE_N7")
            return {"ok": False, "connected": False, "error": str(exc)}
        if not self._nextion7_thread or not self._nextion7_thread.is_alive():
            self._nextion7_active = True
            self._nextion7_thread = threading.Thread(target=self._nextion7_poll_loop, name="PARCORE-NEXTION7", daemon=True)
            self._nextion7_thread.start()
        self._bus_log("PARCORE_MAIN", f"Nextion 7 event bridge started connected={connected}")
        return {"ok": True, "connected": connected, "event_bridge": True}

    def _bind_nextion7_event_source(self, bridge: Any) -> None:
        """Podepnij PARcore jako callback realnego adaptera Nextion 7, bez log scraping."""
        callback = self.handle_nextion7_event
        bindings = (
            "set_nextion7_event_handler",
            "set_event_handler",
            "register_nextion7_handler",
            "register_event_handler",
            "on_nextion7_event",
            "on_event",
        )
        for name in bindings:
            fn = getattr(bridge, name, None)
            if callable(fn):
                try:
                    fn(callback)
                    self.force_signal("nextion7_event_source", name, source="PARCORE_N7")
                    return
                except TypeError:
                    try:
                        fn("nextion_7", callback)
                        self.force_signal("nextion7_event_source", name, source="PARCORE_N7")
                        return
                    except Exception:
                        pass
                except Exception as exc:
                    self._bus_log("NEXTION7_BIND_ERROR", f"{name}: {exc}")
        for attr in ("nextion7_event_handler", "event_handler", "on_nextion7_event", "on_event"):
            try:
                setattr(bridge, attr, callback)
                self.force_signal("nextion7_event_source", attr, source="PARCORE_N7")
                return
            except Exception:
                pass
        self.force_signal("nextion7_event_source", "poll_events", source="PARCORE_N7")

    def stop_nextion7_runtime(self) -> None:
        self._nextion7_active = False
        bridge = self._nextion7_bridge
        if bridge is not None:
            try:
                if hasattr(bridge, "disconnect_screen"):
                    bridge.disconnect_screen("nextion_7")
                elif hasattr(bridge, "disconnect_nextion7"):
                    bridge.disconnect_nextion7()
                elif hasattr(bridge, "disconnect_all"):
                    bridge.disconnect_all()
            except Exception:
                pass
        self.force_signal("nextion7_state", "STOPPED", source="PARCORE_N7")

    def _nextion7_poll_loop(self) -> None:
        while self._nextion7_active:
            try:
                # Blokujący odczyt RX jednego ekranu. To nie jest cykliczne
                # odświeżanie UI i nie zastępuje Snajpera. Wątek śpi w UART.
                self.poll_nextion7_once(block=True)
                # Po odebraniu (lub timeout) wypychamy zaległe komendy Snajpera
                # na fizyczny ekran, żeby odświeżanie było płynne.
                self.flush_snajper_commands()
            except Exception as exc:
                self.force_signal("nextion7_state", "ERROR", source="PARCORE_N7")
                self.force_signal("par_last_error", f"Nextion7 event poll failed: {exc}", source="PARCORE_N7")
                time.sleep(0.5)

    def handle_nextion7_event(self, event: Any = None, value: Any = None, **kwargs: Any) -> Any:
        """Realny callback adaptera Nextion 7 -> PARcore.

        Adapter może przekazać str, bytes albo dict typu:
        {"screen":"nextion_7", "event":"rrp:p1_ax", "value":4}.
        """
        if kwargs:
            payload: Any = dict(kwargs)
            if event is not None:
                payload.setdefault("event", event)
            if value is not None:
                payload.setdefault("value", value)
        else:
            payload = event
            if value is not None and not isinstance(event, Mapping):
                payload = {"event": event, "value": value}
        with self._nextion7_event_lock:
            self._nextion7_event_queue.append(payload)
        try:
            self.log_nextion7_event({"event": payload}, source="NEXTION7_EVENT")
            self.publish_text_previews("nextion7")
        except Exception:
            pass
        return True

    def poll_nextion7_once(self, block: bool = False) -> List[str]:
        bridge = self._nextion7_bridge
        raw_events: List[Any] = []
        with self._nextion7_event_lock:
            if self._nextion7_event_queue:
                raw_events.extend(self._nextion7_event_queue)
                self._nextion7_event_queue.clear()
        if bridge is not None:
            raw_events.extend(self._read_nextion7_bridge_events(bridge, block=block))
        routed: List[str] = []
        for raw_event in raw_events:
            event, value = self._coerce_nextion7_event(raw_event)
            if not event:
                continue
            if self._is_nextion7_transport_event(event):
                continue
            try:
                self.route_nextion7_local(event, value)
                routed.append(str(event) if value is None else f"{event}={value}")
            except Exception as exc:
                self._bus_log("NEXTION7_ROUTE_ERROR", f"{event}: {exc}")
        if routed:
            self.force_signal("nextion7_state", "ACTIVE", source="PARCORE_N7")
            self.force_signal("nextion7_last_event", routed[-1], source="PARCORE_N7")
            try:
                self.log_nextion7_event(" | ".join(routed), source="NEXTION7_ROUTE")
                self.publish_text_previews("nextion7")
            except Exception:
                pass
        return routed

    def _read_nextion7_bridge_events(self, bridge: Any, block: bool = False) -> List[Any]:
        """Odczyt realnych eventów z adaptera; bez parsowania logów tekstowych.

        W trybie wątku lokalnego używamy blokującego odczytu UART jednego ekranu
        Nextion 7. To nie jest refresh UI; Snajper nadal decyduje o tym, co ma
        zostać wysłane na fizyczny ekran.
        """
        events: List[Any] = []
        if block:
            for name in ("poll_nextion7_events", "poll_screen"):
                fn = getattr(bridge, name, None)
                if not callable(fn):
                    continue
                try:
                    if name == "poll_screen":
                        logs = fn("nextion_7", block=True, timeout_s=0.25)
                        # ETAP 14: poll_screen zwraca logi tekstowe (TX/RX/ERR).
                        # Musimy je zapisać, zanim nadpiszemy result eventami strukturalnymi.
                        if logs and isinstance(logs, list):
                            for line in logs:
                                self._append_transport_log(line)
                        
                        pull = getattr(bridge, "read_events", None)
                        result = pull("nextion_7") if callable(pull) else logs
                    else:
                        result = fn("nextion_7", block=True, timeout_s=0.25)
                    
                    events.extend(self._normalize_nextion7_event_result(result))
                    if events:
                        return events
                except TypeError:
                    try:
                        result = fn("nextion_7")
                        events.extend(self._normalize_nextion7_event_result(result))
                        if events:
                            return events
                    except Exception as exc:
                        self._bus_log("NEXTION7_EVENT_READ_ERROR", f"{name}: {exc}")
                except Exception as exc:
                    self._bus_log("NEXTION7_EVENT_READ_ERROR", f"{name}: {exc}")
        for name in (
            "read_nextion7_events",
            "get_nextion7_events",
            "read_events",
            "get_events",
        ):
            fn = getattr(bridge, name, None)
            if not callable(fn):
                continue
            try:
                try:
                    result = fn("nextion_7")
                except TypeError:
                    result = fn()
                events.extend(self._normalize_nextion7_event_result(result))
                if events:
                    return events
            except Exception as exc:
                self._bus_log("NEXTION7_EVENT_READ_ERROR", f"{name}: {exc}")
        for name in ("read_nextion7_event", "recv_nextion7_event", "read_event", "recv_event"):
            fn = getattr(bridge, name, None)
            if not callable(fn):
                continue
            try:
                try:
                    result = fn("nextion_7")
                except TypeError:
                    result = fn()
                events.extend(self._normalize_nextion7_event_result(result))
                if events:
                    return events
            except Exception as exc:
                self._bus_log("NEXTION7_EVENT_READ_ERROR", f"{name}: {exc}")
        poll_screen = getattr(bridge, "poll_screen", None)
        if callable(poll_screen):
            try:
                logs = poll_screen("nextion_7", block=False, timeout_s=0.0)
                if logs and isinstance(logs, list):
                    for line in logs:
                        self._append_transport_log(line)
                
                pull = getattr(bridge, "read_events", None)
                if callable(pull):
                    events.extend(self._normalize_nextion7_event_result(pull("nextion_7")))
            except Exception as exc:
                self._bus_log("NEXTION7_EVENT_READ_ERROR", f"poll_screen: {exc}")
        return events

    def _normalize_nextion7_event_result(self, result: Any, accept_plain_text: bool = True) -> List[Any]:
        if result is None or result is False:
            return []
        if isinstance(result, (list, tuple, set)):
            out: List[Any] = []
            for item in result:
                out.extend(self._normalize_nextion7_event_result(item, accept_plain_text=accept_plain_text))
            return out
        if isinstance(result, Mapping):
            screen = str(result.get("screen") or result.get("device") or result.get("target") or "").lower()
            if screen and screen not in {"nextion7", "nextion_7", "n7", "7"}:
                return []
            return [result]
        if isinstance(result, (bytes, bytearray)):
            return [result]
        if isinstance(result, str):
            text = result.strip()
            if not text:
                return []
            if accept_plain_text and self._looks_like_nextion7_command(text):
                return [text]
            return []
        return [result]

    def _coerce_nextion7_event(self, raw_event: Any) -> Tuple[str, Any]:
        if isinstance(raw_event, Mapping):
            event = raw_event.get("event") or raw_event.get("cmd") or raw_event.get("command") or raw_event.get("name") or raw_event.get("component")
            value = raw_event.get("value")
            if value is None:
                value = raw_event.get("val") or raw_event.get("data")
            if event is None and "raw" in raw_event:
                return self._coerce_nextion7_event(raw_event.get("raw"))
            return str(event or "").strip(), value
        if isinstance(raw_event, (bytes, bytearray)):
            parts = bytes(raw_event).split(b"\xff\xff\xff")
            for part in parts:
                msg = part.decode("cp1250", errors="replace").strip("\x00\x1a\r\n ")
                if msg:
                    return self._coerce_nextion7_event(msg)
            return "", None
        text = str(raw_event or "").strip()
        if not text:
            return "", None
        if "=" in text:
            event, value = text.split("=", 1)
            return event.strip(), value.strip()
        return text, None

    def _looks_like_nextion7_command(self, text: str) -> bool:
        low = text.lower().strip()
        return low.startswith(("rrp:", "take:", "mode:", "sensor:", "sok:", "axis:", "safety:", "manual_record_arm"))

    def _is_nextion7_transport_event(self, event: Any) -> bool:
        low = str(event or "").strip().lower()
        return low in {"raw", "port_open", "connect", "connected", "disconnect", "page", "touch"}

    def main_runtime_status(self) -> Dict[str, Any]:
        return {
            "signalbus": True,
            "tsp_server": self.tsp_server is not None,
            "parcore": self.bus.get("parcore_state", "READY"),
            "hardware_bridge": self.hardware_bridge is not None,
            "nextion5": bool(getattr(self.tsp_server, "lks_n5", None)) if self.tsp_server is not None else False,
            "nextion7": self.bus.get("nextion7_state", "UNKNOWN"),
        }


    # ------------------------------------------------------------------
    # pełny transplant brakujących silników wykonawczych bez UI:
    # MODE/RRP, Snajper systemowy, NextionBridge, TFD/CLAP/TC/transport log.
    # ------------------------------------------------------------------
    def start_mode_logic(self, prefer_existing: bool = True) -> Any:
        """Uruchamia istniejący TarzanModeLogic albo headless odpowiednik w PARcore.

        Zasada: nie tworzymy drugiego modelu. Jeżeli w repo istnieje TarzanModeLogic,
        delegujemy do niego. Jeżeli nie da się go uruchomić, PARcore uruchamia tę samą
        pętlę wykonawczą na własnym busie.
        """
        if self.mode_logic is not None:
            try:
                if hasattr(self.mode_logic, "start"):
                    self.mode_logic.start()
                return self.mode_logic
            except Exception:
                pass
        if prefer_existing and TarzanModeLogic is not None:
            try:
                logic = TarzanModeLogic()  # type: ignore[operator]
                # Wyrównanie busa, żeby singleton z tarzanMode nie zrobił drugiej prawdy.
                try:
                    logic.bus = self.bus
                except Exception:
                    pass
                logic.start()
                self.mode_logic = logic
                self.force_signal("mode_logic_state", "RUNNING_EXISTING", source="PARCORE_MODELOGIC")
                return logic
            except Exception as exc:
                self._bus_log("MODE_ERROR", f"Existing TarzanModeLogic start failed, fallback headless: {exc}")
        self._mode_running = True
        if self._mode_thread is None or not self._mode_thread.is_alive():
            self._mode_thread = threading.Thread(target=self._mode_loop, name="PARCORE-MODE", daemon=True)
            self._mode_thread.start()
        self.force_signal("mode_logic_state", "RUNNING_HEADLESS", source="PARCORE_MODELOGIC")
        return self

    def stop_mode_logic(self) -> None:
        self._mode_running = False
        if self.mode_logic is not None and hasattr(self.mode_logic, "stop"):
            try:
                self.mode_logic.stop()
            except Exception:
                pass
        self.force_signal("mode_logic_state", "STOPPED", source="PARCORE_MODELOGIC")

    def _mode_loop(self) -> None:
        while self._mode_running:
            try:
                if not self._bus_read("tarzan_ready", 1):
                    time.sleep(0.5)
                    continue
                self._handle_system_commands()
                active_mode = str(self._bus_read("active_mode", "tM") or "tM")
                transport = str(self._bus_read("transport_state", "STOP") or "STOP")
                owner = str(self._bus_read("control_owner", "TSP_BOOT") or "TSP_BOOT")
                self._manage_control_owner(active_mode, owner)
                if active_mode == "tM":
                    if owner in {"PAR_LIVE", "TSP_SERVICE", "LKS_DIAGNOSTIC", "PARCORE", "TSP_BOOT"}:
                        self._handle_manual_control()
                elif active_mode == "tAA":
                    if owner == "EHR_PLAYBACK" and transport == "PLAY":
                        self._handle_auto_playback()
                self.write_output("rec_p09_led_data", 1 if transport == "REC" else 0, source="MODE_LOGIC")
                self._update_clap_tc_for_snajper()
            except Exception as exc:
                self._bus_log("MODE_ERROR", str(exc))
            time.sleep(0.05)

    def _bus_read(self, name: str, default: Any = 0) -> Any:
        for method in ("read", "get"):
            fn = getattr(self.bus, method, None)
            if callable(fn):
                try:
                    return fn(name, default)
                except TypeError:
                    try:
                        return fn(name)
                    except Exception:
                        pass
                except Exception:
                    pass
        return default

    def _handle_system_commands(self) -> None:
        if self._bus_read("cmd_ehr_start", 0):
            self.set_input("cmd_ehr_start", 0, source="MODE_LOGIC")
            self.set_input("ehr_state", "ACTIVE", source="MODE_LOGIC")
            self.set_input("transport_state", "PLAY", source="MODE_LOGIC")
            self.log_par_event("MODE", "EHR Playback STARTED via command")
        if self._bus_read("cmd_ehr_stop", 0):
            self.set_input("cmd_ehr_stop", 0, source="MODE_LOGIC")
            self.set_input("ehr_state", "READY", source="MODE_LOGIC")
            self.set_input("transport_state", "STOP", source="MODE_LOGIC")
            self.log_par_event("MODE", "EHR Playback STOPPED via command")
        if self._bus_read("cmd_khr_start", 0):
            self.set_input("cmd_khr_start", 0, source="MODE_LOGIC")
            self.set_input("khr_state", "ACTIVE", source="MODE_LOGIC")
            self.log_par_event("MODE", "KHR Correction ACTIVE")
        if self._bus_read("cmd_khr_stop", 0):
            self.set_input("cmd_khr_stop", 0, source="MODE_LOGIC")
            self.set_input("khr_state", "READY", source="MODE_LOGIC")
            self.log_par_event("MODE", "KHR Correction OFF")

    def _manage_control_owner(self, mode: str, current_owner: str) -> None:
        if mode == "tAA" and current_owner != "EHR_PLAYBACK":
            self.set_input("control_owner", "EHR_PLAYBACK", source="MODE_AUTO")
            self.log_par_event("MODE", "Control Owner changed to EHR_PLAYBACK for AUTO mode")
        elif mode == "tM" and current_owner == "EHR_PLAYBACK":
            self.set_input("control_owner", "PAR_LIVE", source="MODE_AUTO")
            self.log_par_event("MODE", "Control Owner restored to PAR_LIVE for MANUAL mode")

    def _handle_manual_control(self) -> None:
        if self._bus_read("sensor_shock_state", 0) or self._bus_read("emergency_stop", 0):
            return
        axis_p1 = self._bus_read("rrp_p1_axis_index", 0)
        val_p1 = self._bus_read("sensor_rrp_pot_h", self._bus_read("play_p45_rrp_pot_h", 512))
        self._apply_rrp_to_axis(axis_p1, val_p1, "p1")
        axis_p2 = self._bus_read("rrp_p2_axis_index", 0)
        val_p2 = self._bus_read("sensor_rrp_pot_v", self._bus_read("play_p47_rrp_pot_v", 512))
        self._apply_rrp_to_axis(axis_p2, val_p2, "p2")

    def _handle_auto_playback(self) -> None:
        if str(self._bus_read("khr_state", "")) == "ACTIVE":
            for axis in ("cam_h", "cam_v", "arm_h", "arm_v"):
                offset = self._bus_read(f"khr_{axis}_offset", 0)
                if offset:
                    self.force_signal(f"khr_{axis}_offset_active", offset, source="MODE_KHR")
                    self.snajper_fire_log_take_nextion("khr", {"axis": axis, "offset": offset})

    def ensure_system_snajper(self) -> Any:
        """Zapewnia realny Snajper z core/tarzanSnajper.py albo headless fallback."""
        if self.snajper is not None:
            self.register_system_snajper_defaults()
            return self.snajper
        candidate = None
        for src in (self.tsp_server, self.hardware_bridge):
            if src is None:
                continue
            for attr in ("snajper", "tarzan_snajper", "_tarzan_snajper"):
                obj = getattr(src, attr, None)
                if obj is not None:
                    candidate = obj
                    break
            if candidate is not None:
                break
        if candidate is None and self.nextion is not None:
            try:
                candidate = self.nextion.tarzan_snajper
            except Exception:
                candidate = getattr(self.nextion, "_tarzan_snajper", None)
        if candidate is None and TarzanSnajper is not None:
            try:
                candidate = TarzanSnajper()  # type: ignore[operator]
            except Exception as exc:
                self._bus_log("SNAJPER_ERROR", f"TarzanSnajper init failed: {exc}")
        self.snajper = candidate
        if self.snajper is not None:
            self.register_system_snajper_defaults()
            self.force_signal("snajper_state", "CONNECTED", source="PARCORE_SNAJPER")
        return self.snajper

    def register_system_snajper_defaults(self) -> bool:
        sn = self.snajper
        if sn is None or self._snajper_adapters_registered:
            return bool(sn)
        try:
            if hasattr(sn, "register_signals"):
                mapping = {name: name for name in self.bus.names()} if hasattr(self.bus, "names") else {}
                if mapping:
                    sn.register_signals(mapping)
            if self.nextion is not None and NextionPhysicalSnajperAdapter is not None and hasattr(sn, "register_adapter"):
                try:
                    adapter = NextionPhysicalSnajperAdapter(self.nextion)  # type: ignore[operator]
                    sn.register_adapter("nextion_physical", adapter)
                except Exception:
                    pass
            self._snajper_adapters_registered = True
        except Exception as exc:
            self._bus_log("SNAJPER_ERROR", f"register defaults failed: {exc}")
        return True

    def register_adapter(self, name: str, adapter: Any) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "register_adapter"):
            sn.register_adapter(name, adapter)
            return True
        return False

    def register_signal(self, raw_signal: str, logical_signal: str) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "register_signal"):
            sn.register_signal(raw_signal, logical_signal)
            return True
        self.force_signal(f"snajper_signal_map_{raw_signal}", logical_signal, source="PARCORE_SNAJPER")
        return False

    def register_signals(self, mapping: Mapping[str, str]) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "register_signals"):
            sn.register_signals(dict(mapping))
            return True
        for k, v in dict(mapping).items():
            self.register_signal(str(k), str(v))
        return False

    def register_target(self, logical_signal: str, target: Any) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "register_target"):
            sn.register_target(logical_signal, target)
            return True
        self.snajper_fire_log_take_nextion("target", {"signal": logical_signal, "target": str(target)})
        return False

    def register_targets(self, mapping: Mapping[str, Any]) -> bool:
        ok = True
        for k, v in dict(mapping).items():
            ok = self.register_target(str(k), v) and ok
        return ok

    def fire_from_signal(self, signal_name: str, value: Any = None) -> bool:
        if value is None:
            value = self._bus_read(signal_name, None)
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "fire_from_signal"):
            sn.fire_from_signal(signal_name, value)
            return True
        self.step_dir_multi_snajper.fire(signal_name, value)
        self.section_snajper.fire(signal_name, value)
        return False

    def fire_many(self, values: Mapping[str, Any]) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "fire_many"):
            sn.fire_many(dict(values))
            return True
        for k, v in dict(values).items():
            self.fire_from_signal(str(k), v)
        return False

    def fire_with_policy(self, signal_name: str, value: Any, policy: str = "IMMEDIATE", scheduler: Optional[Callable[[int, Callable[[], None]], Any]] = None) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "fire_with_policy"):
            try:
                sn.fire_with_policy(signal_name, value, policy=policy, scheduler=scheduler or (self.scheduler.after if self.scheduler else None))
            except TypeError:
                try:
                    sn.fire_with_policy(signal_name, value, policy=policy)
                except TypeError:
                    sn.fire_with_policy(signal_name, value)
            return True
        return self.fire_from_signal(signal_name, value)

    def clear_scope(self, scope: str) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "clear_scope"):
            sn.clear_scope(scope)
            return True
        return False

    def clear_all(self) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "clear_all"):
            sn.clear_all()
            return True
        return False

    def set_refresh_policy(self, name: str, interval_ms: int) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "set_refresh_policy"):
            sn.set_refresh_policy(name, interval_ms)
            return True
        self.force_signal(f"snajper_policy_{name}", int(interval_ms), source="PARCORE_SNAJPER")
        return False

    def cancel_refresh_policy(self, name: str) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "cancel_refresh_policy"):
            sn.cancel_refresh_policy(name)
            return True
        return False

    def update_target(self, target: Any, value: Any) -> bool:
        adapter = None
        if self.nextion is not None and NextionPhysicalSnajperAdapter is not None:
            try:
                adapter = NextionPhysicalSnajperAdapter(self.nextion)  # type: ignore[operator]
            except Exception:
                adapter = None
        if adapter is not None and hasattr(adapter, "update_target"):
            adapter.update_target(target, value)
            return True
        for method in ("update_target", "set_target"):
            fn = getattr(self.nextion, method, None) if self.nextion is not None else None
            if callable(fn):
                try:
                    fn(target, value)
                    return True
                except Exception:
                    pass
        return False

    # NextionBridge — pełniejszy runtime/preview/monitor/transport/TFD bez UI.
    def connect_enabled(self, screen_key: str = "nextion_7") -> bool:
        if self.nextion is not None and hasattr(self.nextion, "connect_enabled"):
            try:
                return bool(self.nextion.connect_enabled(screen_key))
            except Exception:
                pass
        cfg = getattr(self.nextion, "ports_cfg", {}).get(screen_key, {}) if self.nextion is not None else {}
        return bool(cfg.get("enabled", True))

    def connect_screen(self, screen_key: str = "nextion_7") -> bool:
        if self.nextion is not None and hasattr(self.nextion, "connect_screen"):
            try:
                return bool(self.nextion.connect_screen(screen_key))
            except Exception as exc:
                self.log_nextion7_event("connect_screen", f"ERROR {exc}")
                return False
        self.force_signal(f"{screen_key}_state", "CONNECTED_DRY", source="PARCORE_NEXTION")
        return True

    def disconnect_screen(self, screen_key: str = "nextion_7") -> bool:
        if self.nextion is not None and hasattr(self.nextion, "disconnect_screen"):
            try:
                return bool(self.nextion.disconnect_screen(screen_key))
            except Exception:
                return False
        self.force_signal(f"{screen_key}_state", "DISCONNECTED", source="PARCORE_NEXTION")
        return True

    def disconnect_all(self) -> bool:
        if self.nextion is not None and hasattr(self.nextion, "disconnect_all"):
            try:
                self.nextion.disconnect_all()
                return True
            except Exception:
                pass
        self.disconnect_screen("nextion_5")
        self.disconnect_screen("nextion_7")
        return True

    def sync(self, force: bool = False, screen_key: str = "nextion_7", **kwargs: Any) -> bool:
        return self.nextion_sync(force=force, screen_key=screen_key)

    def get_page(self, screen_key: str = "nextion_7") -> str:
        if self.nextion is not None and hasattr(self.nextion, "get_page"):
            try:
                return str(self.nextion.get_page(screen_key))
            except Exception:
                pass
        return str(self._bus_read(f"{screen_key}_page", self._bus_read("nextion7_page", "")) or "")

    def set_page(self, screen_key: str, page_id: str) -> bool:
        if self.nextion is not None and hasattr(self.nextion, "set_page"):
            try:
                return bool(self.nextion.set_page(screen_key, page_id))
            except Exception:
                pass
        self.force_signal(f"{screen_key}_page", page_id, source="PARCORE_NEXTION_PAGE")
        if screen_key in {"nextion7", "nextion_7"}:
            self.force_signal("nextion7_page", page_id, source="PARCORE_NEXTION_PAGE")
            self.fire_nextion_page_loaded_resync(page_id)
        return True

    def next_page(self, screen_key: str = "nextion_7") -> str:
        if self.nextion is not None and hasattr(self.nextion, "next_page"):
            try:
                return str(self.nextion.next_page(screen_key))
            except Exception:
                pass
        self.set_page(screen_key, "next")
        return self.get_page(screen_key)

    def prev_page(self, screen_key: str = "nextion_7") -> str:
        if self.nextion is not None and hasattr(self.nextion, "prev_page"):
            try:
                return str(self.nextion.prev_page(screen_key))
            except Exception:
                pass
        self.set_page(screen_key, "prev")
        return self.get_page(screen_key)

    def _request_current_page(self, screen_key: str = "nextion_7") -> Optional[str]:
        if self.nextion is not None and hasattr(self.nextion, "_request_current_page"):
            try:
                return self.nextion._request_current_page(screen_key)
            except Exception:
                pass
        return self.get_page(screen_key)

    def _component_name_from_touch(self, screen_key: str, page_id: str, component_id: Any) -> str:
        if self.nextion is not None and hasattr(self.nextion, "_component_name_from_touch"):
            try:
                return str(self.nextion._component_name_from_touch(screen_key, page_id, component_id))
            except Exception:
                pass
        return f"{page_id}.{component_id}"

    def _handle_touch_event(self, screen_key: str, page_id: str, component_id: Any, event_type: Any = None) -> Any:
        if self.nextion is not None and hasattr(self.nextion, "_handle_touch_event"):
            try:
                return self.nextion._handle_touch_event(screen_key, page_id, component_id, event_type)
            except Exception as exc:
                self.log_nextion7_event("touch", f"bridge error {exc}")
        component = self._component_name_from_touch(screen_key, page_id, component_id)
        self.log_nextion7_event("touch", f"{screen_key}:{page_id}:{component}:{event_type}")
        if page_id and str(page_id).lower() in {"rrp_main", "rrp"}:
            return self._handle_rrp_event(screen_key, component, event_type)
        if str(component).lower() in {"b_clap", "clap", "tc"}:
            return self._toggle_clap_tc()
        return self.handle_nextion7_event({"screen": screen_key, "event": component, "value": event_type, "page": page_id})

    def _handle_snajper_text_message(self, screen_key: str, message: str) -> bool:
        if self.nextion is not None and hasattr(self.nextion, "_handle_snajper_text_message"):
            try:
                return bool(self.nextion._handle_snajper_text_message(screen_key, message))
            except Exception:
                pass
        self.log_nextion7_event("snajper_text", f"{screen_key}: {message}")
        return True

    def _fire_snajper_signal(self, signal_name: str, value: Any, policy: str = "IMMEDIATE") -> bool:
        return self.fire_with_policy(signal_name, value, policy)

    def queue_snajper_command(self, *args: Any, **kwargs: Any) -> bool:
        """Jedna wersja kolejki Snajpera/Nextion po scaleniu kodu.

        Obsługuje stare wywołanie z bridge:
            queue_snajper_command(scope, component, prop, value)
        oraz nowsze wywołania PARcore:
            queue_snajper_command(command)
            queue_snajper_command(section, payload)
        """
        if kwargs:
            command: Any = dict(kwargs)
        elif len(args) == 1:
            command = args[0]
        elif len(args) == 2:
            command = {"scope": args[0], "payload": args[1]}
        elif len(args) >= 4:
            command = {"scope": args[0], "component": args[1], "prop": args[2], "value": args[3]}
        else:
            command = {"args": list(args)}

        if self.nextion is not None and hasattr(self.nextion, "queue_snajper_command"):
            try:
                # Najpierw nowszy kontrakt: pojedynczy dict/string.
                self.nextion.queue_snajper_command(command)
                return True
            except TypeError:
                try:
                    # Potem stary kontrakt NextionBridge: scope, component, prop, value.
                    if isinstance(command, Mapping) and {"scope", "component", "prop", "value"}.issubset(command.keys()):
                        self.nextion.queue_snajper_command(command["scope"], command["component"], command["prop"], command["value"])
                        return True
                except Exception:
                    pass
            except Exception:
                pass

        # Fallback bez rekurencji: snajper_fire_log_take_nextion(...) samo woła
        # queue_snajper_command(...), więc tutaj zapisujemy pakiet bezpośrednio.
        try:
            payload = command if isinstance(command, Mapping) else {"command": command}
            self.bus.force_signal("nextion7_snajper_command_last", json.dumps(payload, ensure_ascii=False, default=str), source="PARCORE_NEXTION_QUEUE")
        except Exception:
            pass
        return True

    def flush_snajper_commands(self) -> int:
        if self.nextion is not None and hasattr(self.nextion, "flush_snajper_commands"):
            try:
                return int(self.nextion.flush_snajper_commands())
            except Exception:
                pass
        return 0

    def _is_scope_active(self, screen_key: str, scope: str) -> bool:
        if self.nextion is not None and hasattr(self.nextion, "_is_scope_active"):
            try:
                return bool(self.nextion._is_scope_active(screen_key, scope))
            except Exception:
                pass
        return True

    def _refresh_physical_nextion_page_from_state(self, screen_key: str = "nextion_7", force: bool = False) -> bool:
        if self.nextion is not None and hasattr(self.nextion, "_refresh_physical_nextion_page_from_state"):
            try:
                return bool(self.nextion._refresh_physical_nextion_page_from_state(screen_key, force=force))
            except TypeError:
                try:
                    return bool(self.nextion._refresh_physical_nextion_page_from_state(screen_key))
                except Exception:
                    pass
            except Exception:
                pass
        self.publish_text_previews()
        self.fire_nextion_physical_resync(fast=not force)
        return True

    def _force_page_target_from_logical(self, logical_signal: str, value: Any) -> bool:
        self.force_signal(f"nextion_target_{logical_signal}", value, source="PARCORE_NEXTION_TARGET")
        return self._fire_snajper_signal(logical_signal, value)

    def _read_page_refresh_value(self, logical_signal: str, default: Any = None) -> Any:
        return self._bus_read(logical_signal, default)

    def _append_transport_log(self, line: str) -> None:
        text = str(line)
        ts = time.strftime("%H:%M:%S")
        entry = text if text.startswith("EV ") else f"EV nextion_7: {ts} {text}"
        self._transport_log.append(entry)
        if len(self._transport_log) > self._transport_log_limit:
            self._transport_log = self._transport_log[-self._transport_log_limit:]
        
        # ETAP 14: Logi transportu do podglądu tekstowego (dla PAR STACJA / TSP)
        self.log_nextion7_event(text, source="TRANS")
        
        self.force_signal("nextion7_transport_log_last", entry, source="PARCORE_NEXTION_LOG")
        self.force_signal("nextion7_transport_log", "\n".join(self._transport_log[-20:]), source="PARCORE_NEXTION_LOG")

    def get_recent_transport_log(self, limit: int = 50) -> List[str]:
        if self.nextion is not None and hasattr(self.nextion, "get_recent_transport_log"):
            try:
                return list(self.nextion.get_recent_transport_log(limit))
            except Exception:
                pass
        return list(self._transport_log[-max(1, int(limit)):])

    def clear_transport_log(self, screen_key: str = "nextion_7", **kwargs: Any) -> None:
        if self.nextion is not None and hasattr(self.nextion, "clear_transport_log"):
            try:
                self.nextion.clear_transport_log()
            except Exception:
                pass
        self._transport_log.clear()
        self.force_signal("nextion7_transport_log", "", source="PARCORE_NEXTION_LOG")

    def _toggle_clap_tc(self) -> bool:
        return self._set_clap_tc(not self._clap_tc_running)

    def _set_clap_tc(self, running: bool) -> bool:
        now = time.monotonic()
        if now - self._clap_tc_last_toggle_monotonic < 0.08:
            return self._clap_tc_running
        self._clap_tc_last_toggle_monotonic = now
        if running and not self._clap_tc_running:
            self._clap_tc_start_monotonic = now
            self._clap_tc_start_elapsed_ms = int(self._clap_tc_elapsed_ms)
            self._clap_tc_running = True
            self._play_clap_audio()
            self._append_transport_log("CLAP TC START")
        elif not running and self._clap_tc_running:
            self._update_clap_tc_for_snajper(force=True)
            self._clap_tc_running = False
            self._append_transport_log("CLAP TC STOP")
        self._publish_clap_tc_state()
        return self._clap_tc_running

    def _publish_clap_tc_state(self) -> Dict[str, Any]:
        state = {
            "running": self._clap_tc_running,
            "elapsed_ms": int(self._clap_tc_elapsed_ms),
            "timecode": self._format_tc_from_ms(int(self._clap_tc_elapsed_ms)),
        }
        self.force_signal("clap_tc_running", 1 if self._clap_tc_running else 0, source="PARCORE_CLAP_TC")
        self.force_signal("clap_tc_elapsed_ms", state["elapsed_ms"], source="PARCORE_CLAP_TC")
        self.force_signal("take_timecode", state["timecode"], source="PARCORE_CLAP_TC")
        return state

    def _format_tc_from_ms(self, ms: int) -> str:
        ms = max(0, int(ms))
        s, msec = divmod(ms, 1000)
        m, sec = divmod(s, 60)
        h, minute = divmod(m, 60)
        return f"{h:02d}:{minute:02d}:{sec:02d}.{msec:03d}"

    def _update_clap_tc_for_snajper(self, force: bool = False) -> bool:
        if self._clap_tc_running:
            self._clap_tc_elapsed_ms = self._clap_tc_start_elapsed_ms + int((time.monotonic() - self._clap_tc_start_monotonic) * 1000)
        elapsed = int(self._clap_tc_elapsed_ms)
        if not force and abs(elapsed - self._clap_tc_last_sent_ms) < 100:
            return False
        self._clap_tc_last_sent_ms = elapsed
        self._publish_clap_tc_state()
        return self._fire_snajper_signal("take_timecode", self._format_tc_from_ms(elapsed), policy="LIVE_FAST")

    def _fire_audio_event(self, key: str, payload: Any = None) -> bool:
        self.force_signal("audio_last_event", key, source="PARCORE_AUDIO")
        self.force_signal("audio_last_payload", json.dumps(payload, ensure_ascii=False) if payload is not None else "", source="PARCORE_AUDIO")
        return True

    def _play_audio_key(self, key: str) -> bool:
        self._fire_audio_event(key)
        try:
            from audio.tarzanAudioPlayer import play as play_audio  # type: ignore
            play_audio(key)
            return True
        except Exception:
            return False

    def _play_clap_audio(self) -> bool:
        return self._play_audio_key("clap")

    def _candidate_tfd_metadata_paths(self) -> List[Path]:
        root = Path(__file__).resolve().parents[2]
        paths = [
            root / "data" / "tfd_metadata.json",
            root / "data" / "tfd" / "tfd_metadata.json",
            root / "data" / "TFD" / "tfd_metadata.json",
            root / "editor" / "TFD" / "tfd_metadata.json",
            root / "tfd_metadata.json",
        ]
        unique: List[Path] = []
        seen = set()
        for path in paths:
            key = str(path)
            if key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    def _read_tfd_metadata_json(self) -> Dict[str, Any]:
        for path in self._candidate_tfd_metadata_paths():
            try:
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        self._tfd_metadata_cache.update(data)
                        self._append_transport_log(f"TFD META JSON LOAD {path}")
                        return data
            except Exception as exc:
                self._append_transport_log(f"TFD META JSON READ ERROR {path}: {exc}")
        return dict(self._tfd_metadata_cache)

    def _write_tfd_metadata_json(self, data: Mapping[str, Any]) -> bool:
        path = self._candidate_tfd_metadata_paths()[0]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            current = self._read_tfd_metadata_json()
            current.update(dict(data))
            path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            self._tfd_metadata_cache.update(current)
            return True
        except Exception as exc:
            self._append_transport_log(f"TFD META JSON WRITE ERROR {path}: {exc}")
            return False

    def _bootstrap_tfd_metadata_from_json(self) -> Dict[str, Any]:
        data = self._read_tfd_metadata_json()
        if not data:
            return {}
        if "title" in data:
            self.force_signal("tfd_title", str(data.get("title") or ""), source="PARCORE_TFD")
        if "director" in data:
            self.force_signal("tfd_director", str(data.get("director") or ""), source="PARCORE_TFD")
        if "nextion_ui_cut" in data:
            self.force_signal("nextion_ui_cut", 1 if self._json_bool(data.get("nextion_ui_cut")) else 0, source="PARCORE_TFD")
        self._refresh_physical_nextion_page_from_state("nextion_7", force=True)
        return data

    def _json_bool(self, value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(int(value))
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "tak"}:
            return True
        if text in {"0", "false", "no", "off", "nie", ""}:
            return False
        return default

    def _write_tfd_meta_value(self, key: str, value: Any) -> bool:
        self.force_signal(f"tfd_{key}", value, source="PARCORE_TFD")
        return self._write_tfd_metadata_json({key: value})

    def _read_tfd_meta_value(self, key: str, default: Any = "") -> Any:
        signal_name = f"tfd_{key}"
        value = self._bus_read(signal_name, None)
        if value is not None:
            return value
        return self._read_tfd_metadata_json().get(key, default)

    def _handle_tfd_meta_event(self, key: str, value: Any) -> bool:
        ok = self._write_tfd_meta_value(str(key), value)
        self._show_tfd_save_status(ok)
        self._update_tfd_save_status_for_snajper(ok)
        return ok

    def _show_tfd_save_status(self, ok: bool = True, seconds: float = 2.0) -> None:
        self._tfd_save_status_until = time.monotonic() + float(seconds)
        self._tfd_save_status_visible = bool(ok)
        self.force_signal("tfd_save_status", "OK" if ok else "ERROR", source="PARCORE_TFD")

    def _update_tfd_save_status_for_snajper(self, ok: bool = True) -> bool:
        return self._fire_snajper_signal("tfd_save_status", "OK" if ok else "ERROR", policy="LIVE_FAST")

    # ------------------------------------------------------------------
    # zgodność brakujących nazw/metod po końcowej inwentaryzacji.
    # To są aliasy i headless odpowiedniki starego PAR/Nextion/Snajper bez UI.
    # ------------------------------------------------------------------
    def _on_bus_signal_change(self, name: str, value: Any, source: str = "PARCORE_BUS", previous_value: Any = None) -> None:
        """Zgodność z TarzanParPanels._on_bus_signal_change bez widgetów."""
        return self.on_state_change(name, value, source=source, previous_value=previous_value)

    def _force_signal(self, name: str, value: Any, source: str = "PARCORE_FORCE_ALIAS") -> bool:
        """Zgodność ze starą nazwą z paneli; wykonanie dalej idzie przez SignalBus."""
        return self.force_signal(name, value, source=source)

    def _manual_axis_step(self, axis: Any, direction: Any = 1, pulses: int = 10, delay_ms: int = 7) -> Dict[str, Any]:
        """Zgodność ze starą nazwą z paneli; bez lokalnego UI."""
        return self.manual_axis_step(axis, direction=direction, pulses=pulses, delay_ms=delay_ms)

    def _update_limits_status(self) -> str:
        """Zgodność ze starą nazwą z paneli."""
        return self.update_limits_status()

    def register_log_snajper_widget(self, widget: Any = None, name: str = "par_log") -> bool:
        """Stary PAR rejestrował widget; PARcore rejestruje target logiczny bez UI."""
        try:
            return self.register_target(str(name or "par_log"), widget if widget is not None else str(name or "par_log"))
        except Exception:
            self.force_signal(f"snajper_target_{name}", str(widget), source="PARCORE_SNAJPER")
            return False

    def snajper_log_fire(self, line: Any = "", source: str = "PAR") -> Dict[str, Any]:
        payload = {"line": str(line), "source": str(source), "ts": time.time()}
        return self.snajper_fire_log_take_nextion("log", payload)

    def snajper_take_fire(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = dict(payload or {})
        if not data:
            data = {
                "take_status": self._bus_read("take_status", ""),
                "take_time_ms": self._bus_read("take_time_ms", 0),
                "loaded_take_path": self._bus_read("loaded_take_path", ""),
            }
        return self.snajper_fire_log_take_nextion("take", data)

    def snajper_step_dir_fire(self, signal_name: str, value: Any = None) -> bool:
        if value is None:
            value = self._bus_read(signal_name, 0)
        try:
            return bool(self.step_dir_multi_snajper.fire(signal_name, value))
        except Exception:
            return self.fire_from_signal(signal_name, value)

    def unregister_adapter(self, name: str) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "unregister_adapter"):
            try:
                sn.unregister_adapter(name)
                return True
            except Exception as exc:
                self._bus_log("SNAJPER_ERROR", f"unregister_adapter({name}) failed: {exc}")
                return False
        try:
            adapters = getattr(self, "_snajper_local_adapters", {})
            if isinstance(adapters, dict):
                adapters.pop(str(name), None)
                self._snajper_local_adapters = adapters
        except Exception:
            pass
        self.force_signal(f"snajper_adapter_{name}_state", "UNREGISTERED", source="PARCORE_SNAJPER")
        return False

    def clear_adapter(self, name: str) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "clear_adapter"):
            try:
                sn.clear_adapter(name)
                return True
            except Exception as exc:
                self._bus_log("SNAJPER_ERROR", f"clear_adapter({name}) failed: {exc}")
                return False
        return self.unregister_adapter(name)

    def refresh_policy_interval_ms(self, name: str, default: int = 0) -> int:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "refresh_policy_interval_ms"):
            try:
                return int(sn.refresh_policy_interval_ms(name, default))
            except TypeError:
                try:
                    return int(sn.refresh_policy_interval_ms(name))
                except Exception:
                    pass
            except Exception:
                pass
        return int(self._bus_read(f"snajper_policy_{name}", default) or default)

    def _policy_key(self, scope: str, target: Any = None) -> str:
        if target is None or str(target) == "":
            return str(scope)
        return f"{scope}:{target}"

    def _flush_policy(self, name: str = "", value: Any = None) -> bool:
        sn = self.ensure_system_snajper()
        if sn is not None and hasattr(sn, "_flush_policy"):
            try:
                sn._flush_policy(name, value)
                return True
            except TypeError:
                try:
                    sn._flush_policy(name)
                    return True
                except Exception:
                    pass
            except Exception:
                pass
        if name:
            return self.fire_from_signal(name, value)
        return self.flush_snajper_commands()

    def _rebuild_reverse_signal_map(self) -> Dict[str, str]:
        """Headless odpowiednik mapy odwrotnej Nextion bridge."""
        mapping: Dict[str, str] = {}
        if self.nextion is not None and hasattr(self.nextion, "_rebuild_reverse_signal_map"):
            try:
                res = self.nextion._rebuild_reverse_signal_map()
                if isinstance(res, dict):
                    return {str(k): str(v) for k, v in res.items()}
            except Exception:
                pass
        for name in self.bus.names() if hasattr(self.bus, "names") else []:
            mapping[str(name).lower()] = str(name)
        self._nextion_reverse_signal_map = mapping
        return mapping

    def _enabled(self, screen_key: str = "nextion_7") -> bool:
        return self.connect_enabled(screen_key)

    def _page_ids(self, screen_key: str = "nextion_7") -> Dict[str, int]:
        if self.nextion is not None and hasattr(self.nextion, "_page_ids"):
            try:
                res = self.nextion._page_ids(screen_key)
                if isinstance(res, dict):
                    return {str(k): int(v) for k, v in res.items()}
            except TypeError:
                try:
                    res = self.nextion._page_ids
                    if isinstance(res, dict):
                        return {str(k): int(v) for k, v in res.items()}
                except Exception:
                    pass
            except Exception:
                pass
        # Znane strony Nextion 7 z dotychczasowego bridge; nie jest to UI, tylko mapa techniczna.
        return {
            "boot": 0,
            "page1": 1,
            "level_xyz": 2,
            "face_rec": 3,
            "rrp_main": 4,
            "sensors_main": 5,
            "settings_main": 6,
            "take_main": 7,
        }

    def _page_id_from_index(self, screen_key: str, index: Any) -> str:
        ids = self._page_ids(screen_key)
        try:
            wanted = int(index)
        except Exception:
            wanted = -1
        for name, idx in ids.items():
            if int(idx) == wanted:
                return name
        return str(index)


    # ------------------------------------------------------------------
    # zgodność końcowa z tarzanParState / tarzanParSignalsAdapter,
    # alias MODE _loop oraz brakujący binding RRP NextionBridge.
    # ------------------------------------------------------------------
    def _default(self, name: str = "", default: Any = None) -> Any:
        return self.state._default(name, default)

    def subscribe(self, name: str, callback: Callable[[str, Any], Any]) -> bool:
        return self.state.subscribe(name, callback)

    def notify(self, name: str, value: Any = None) -> int:
        return self.state.notify(name, value)

    def get(self, name: str, default: Any = None) -> Any:
        return self.state.get(name, default)

    def log(self, source: str, message: Any = "") -> str:
        return self.state.log(source, message)

    def _from_tarzan_signal(self, signal: Any) -> Dict[str, Any]:
        return self.signals_adapter._from_tarzan_signal(signal)

    def load_all_signals(self) -> Dict[str, Dict[str, Any]]:
        return self.signals_adapter.load_all_signals()

    def by_group(self, group: str) -> Dict[str, Dict[str, Any]]:
        return self.signals_adapter.by_group(group)

    def contains(self, name: str) -> bool:
        return self.signals_adapter.contains(name)

    def _loop(self) -> None:
        """Alias zgodności z TarzanModeLogic._loop — używa tego samego MODE/RRP."""
        return self._mode_loop()

    def _rrp_binding(self, player: str = "p1", axis: Any = None) -> Dict[str, Any]:
        """Headless odpowiednik NextionBridge._rrp_binding.

        Zwraca techniczne powiązanie P1/P2: wybrana oś, sygnały STEP/DIR,
        potencjometr i indeks dla Nextion 7/RRP. Nie generuje UI.
        """
        player = self._normalize_player(player)
        selected = axis if axis is not None else self._bus_read(f"par_rrp_{player}_selected_axis", "")
        axis_name = self._normalize_axis(selected) if selected not in (None, "", -1) else ""
        if not axis_name or axis_name not in AXIS_SIGNAL_BINDINGS:
            idx = self._bus_read(f"rrp_{player}_axis_index", -1)
            try:
                idx_int = int(idx)
                for cand, cand_idx in AXIS_INDEX.items():
                    if cand_idx == idx_int:
                        axis_name = cand
                        break
            except Exception:
                axis_name = ""
        bind = AXIS_SIGNAL_BINDINGS.get(axis_name, {}) if axis_name else {}
        step_signal = str(self._bus_read(f"par_rrp_{player}_step_signal", "") or "")
        dir_signal = str(self._bus_read(f"par_rrp_{player}_dir_signal", "") or "")
        pot_signal = str(self._bus_read(f"par_rrp_{player}_pot_signal", "") or "")
        if not step_signal:
            step_signal = self._first_existing(bind.get("step", [])) or ""
        if not dir_signal:
            dir_signal = self._first_existing(bind.get("dir", [])) or ""
        if not pot_signal:
            pot_signal = "sensor_rrp_pot_h" if player == "p1" else "sensor_rrp_pot_v"
            try:
                if not self.bus.exists(pot_signal):
                    pot_signal = "play_p45_rrp_pot_h" if player == "p1" else "play_p47_rrp_pot_v"
            except Exception:
                pass
        return {
            "player": player,
            "axis": axis_name,
            "axis_index": AXIS_INDEX.get(axis_name, -1),
            "step_signal": step_signal,
            "dir_signal": dir_signal,
            "pot_signal": pot_signal,
            "dir": self._bus_read(f"par_rrp_{player}_dir", 0),
            "speed_mul": self._bus_read(f"rrp_{player}_speed_mul", 1),
            "sens": self._bus_read(f"par_rrp_{player}_sens", 50),
            "value": self._bus_read(pot_signal, 0) if pot_signal else 0,
        }

    def close(self) -> None:
        self._rrp_active = False
        self._tsp_active = False
        self._nextion7_active = False
        try:
            self.stop_mode_logic()
        except Exception:
            pass
        try:
            self.take_player.stop(reset_to_zero=False, log_stop=False)
        except Exception:
            pass
        if self.tsp_client is not None:
            try:
                self.tsp_client.close()
            except Exception:
                pass
            self.tsp_client = None
        try:
            self.stop_nextion7_runtime()
        except Exception:
            pass
        if self.nextion is not None and hasattr(self.nextion, "close"):
            try:
                self.nextion.close()
            except Exception:
                pass
        self.bus.force_signal("parcore_state", "STOPPED", source="PARCORE_CLOSE")


# Zgodność z różnymi stylami importu.
PARcore = TarzanParCore
TarzanPARcore = TarzanParCore


def create_parcore(*args: Any, **kwargs: Any) -> TarzanParCore:
    return TarzanParCore(*args, **kwargs)
