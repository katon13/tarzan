
from __future__ import annotations

import math
import random
import time
from collections import deque
from itertools import cycle
from typing import Any, Deque, Dict, List, Optional

from .config import load_ports
from .device import TarzanNextionDevice
from .protocol import cmd_page, cmd_text, cmd_value, cmd_visible, command_bytes
from .screen_model import ScreenDefinition, load_screen_definition
from .state_mapper import TarzanNextionStateMapper


class TarzanNextionBridge:
    """
    Bridge łączący fizyczny Nextion i wspólny model stanu TARZAN.

    WARSTWA:
    - transport i parser eventów z urządzenia,
    - jawny stan ekranu per screen,
    - małe mapowanie dla nextion_7 / rrp_main bez ruszania reszty PAR.

    NIE robi tu mechaniki osi ani logiki TAKE.
    """

    _RRP_AXIS_BY_COMPONENT: Dict[int, tuple[str, int]] = {
        6: ("p1", 0),   # b_p1_cam_v
        7: ("p2", 0),   # b_p2_cam_v
        10: ("p1", 1),  # b_p1_cam_t
        15: ("p2", 1),  # b_p2_cam_t
        11: ("p1", 2),  # b_p1_cam_f
        16: ("p2", 2),  # b_p2_cam_f
        12: ("p1", 3),  # b_p1_cam_h
        17: ("p2", 3),  # b_p2_cam_h
        13: ("p1", 4),  # b_p1_arm_h
        18: ("p2", 4),  # b_p2_arm_h
        14: ("p1", 5),  # b_p1_arm_v
        19: ("p2", 5),  # b_p2_arm_v
    }
    _RRP_AXIS_LABELS = {
        0: "CAM_V",
        1: "CAM_T",
        2: "CAM_F",
        3: "CAM_H",
        4: "ARM_H",
        5: "ARM_V",
        -1: "STOP",
    }
    _RRP_AXIS_DIR_SIGNALS: Dict[int, List[str]] = {
        0: ["rec_p04_copy_dir_cam_v", "cnc_y_cam_v_dir", "TAKE_CAM_V_DIR"],
        1: ["rec_p08_copy_dir_tilt", "cnc_a_arm_tilt_dir", "play_p40_step_dir_arm_tilt", "TAKE_CAM_T_DIR"],
        2: ["rec_p07_copy_dir_focus", "cnc_z_focus_dir", "TAKE_CAM_F_DIR"],
        3: ["rec_p03_copy_dir_cam_h", "cnc_x_cam_h_dir", "TAKE_CAM_H_DIR"],
        4: ["play_p38_step_dir_arm_h", "rec_p12_rec_dir_arm_h", "cnc_b_arm_h_dir", "TAKE_ARM_H_DIR"],
        5: ["play_p39_step_dir_arm_v", "rec_p13_rec_dir_arm_v", "cnc_c_arm_v_dir", "TAKE_ARM_V_DIR"],
    }
    # Mapowanie osi na sygnały szyny (zgodnie z rrp_main.txt i Panels)
    _RRP_AXIS_MAP = {
        0: "CAM_V",
        1: "CAM_T",
        2: "CAM_F",
        3: "CAM_H",
        4: "ARM_H",
        5: "ARM_V"
    }

    _AXIS_SIGNAL_BINDINGS = {
        "CAM_V": {"step": ["TAKE_CAM_V_STEP", "rec_p02_copy_ctr_cam_v", "cnc_y_cam_v_ctr"], "dir": ["TAKE_CAM_V_DIR", "rec_p04_copy_dir_cam_v", "cnc_y_cam_v_dir"]},
        "CAM_T": {"step": ["TAKE_CAM_T_STEP", "rec_p06_copy_ctr_tilt", "cnc_a_arm_tilt_ctr", "play_p49_step_ctr_arm_tilt"], "dir": ["TAKE_CAM_T_DIR", "rec_p08_copy_dir_tilt", "cnc_a_arm_tilt_dir", "play_p40_step_dir_arm_tilt"]},
        "CAM_F": {"step": ["TAKE_CAM_F_STEP", "rec_p05_copy_ctr_focus", "cnc_z_focus_ctr"], "dir": ["TAKE_CAM_F_DIR", "rec_p07_copy_dir_focus", "cnc_z_focus_dir"]},
        "CAM_H": {"step": ["TAKE_CAM_H_STEP", "rec_p01_copy_ctr_cam_h", "cnc_x_cam_h_ctr"], "dir": ["TAKE_CAM_H_DIR", "rec_p03_copy_dir_cam_h", "cnc_x_cam_h_dir"]},
        "ARM_H": {"step": ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "rec_p15_rec_ctr_arm_h", "cnc_b_arm_h_ctr"], "dir": ["TAKE_ARM_H_DIR", "play_p38_step_dir_arm_h", "rec_p12_rec_dir_arm_h", "cnc_b_arm_h_dir"]},
        "ARM_V": {"step": ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "rec_p16_rec_ctr_arm_v", "cnc_c_arm_v_ctr"], "dir": ["TAKE_ARM_V_DIR", "play_p39_step_dir_arm_v", "rec_p13_rec_dir_arm_v", "cnc_c_arm_v_dir"]},
    }

    _PAGE_COMPONENT_TO_PAGE = {
        "page1": {
            1: "face_rec",
            2: "level_xyz",
            3: "rrp_main",
            4: "sensors_main",
            5: "settings_main",
            6: "take_main",
        },
        "face_rec": {2: "page1"},
        "level_xyz": {7: "page1"},
        "rrp_main": {1: "page1"},
        "sensors_main": {2: "page1"},
        "settings_main": {2: "page1"},
        "take_main": {2: "page1"},
    }

    _RRP_POLL_INTERVAL = 0.1  # Szybszy tick pollingu, ale pytamy o mniej rzeczy naraz

    def __init__(self, bus) -> None:
        self.bus = bus
        self.state_mapper = TarzanNextionStateMapper(bus)
        self.ports_cfg = load_ports()
        self.screen_defs: Dict[str, ScreenDefinition] = {
            "nextion_5": load_screen_definition("nextion_5"),
            "nextion_7": load_screen_definition("nextion_7"),
        }
        self.active_pages: Dict[str, str] = {
            key: (screen.settings.get("startup_page") or (screen.pages[0]["id"] if screen.pages else "main"))
            for key, screen in self.screen_defs.items()
        }
        self.devices: Dict[str, TarzanNextionDevice] = {}
        for key in ("nextion_5", "nextion_7"):
            cfg = self.ports_cfg.get(key, {})
            self.devices[key] = TarzanNextionDevice(key, cfg.get("port", "COM1"), int(cfg.get("baudrate", 115200)))

        self.last_sync = 0.0
        self.last_sent_snapshot: Dict[str, Any] = {}
        self.last_commands: List[str] = []
        self.transport_log: Dict[str, Deque[str]] = {key: deque(maxlen=200) for key in self.devices}
        self._pending_numeric_query: Dict[str, Deque[str]] = {key: deque() for key in self.devices}
        self._last_payload_by_screen: Dict[str, Dict[str, bytes]] = {key: {} for key in self.devices}
        self._rrp_hold_until: Dict[str, Dict[str, float]] = {
            "nextion_7": {},
            "nextion_5": {},
        }
        self._rrp_revision: Dict[str, int] = {"nextion_7": 0, "nextion_5": 0}
        self._last_rrp_poll_ts: Dict[str, float] = {"nextion_7": 0.0, "nextion_5": 0.0}
        self._last_pot_poll_ts: Dict[str, float] = {"nextion_7": 0.0, "nextion_5": 0.0}
        self._last_pot_player: Dict[str, str] = {"nextion_7": "p2", "nextion_5": "p2"}
        self._last_received_rrp: Dict[str, Dict[str, Any]] = {
            "nextion_7": {}, "nextion_5": {}
        }
        self._rrp_poll_cycle: Dict[str, int] = {"nextion_7": 0, "nextion_5": 0}
        self._last_sent_rrp_device: Dict[str, Dict[str, Any]] = {"nextion_7": {}, "nextion_5": {}}

    # ------------------------------------------------------------------
    # BASIC HELPERS
    # ------------------------------------------------------------------
    def _default_rrp_state(self) -> Dict[str, Any]:
        return {
            "va_p1_axis": -1,
            "va_p2_axis": -1,
            "va_p1_dir": 0,
            "va_p2_dir": 0,
            "va_p1_val": 0,
            "va_p2_val": 0,
            "h_p1_sens": 50,
            "h_p2_sens": 50,
        }

    def _enabled(self, screen_key: str) -> bool:
        return bool(self.ports_cfg.get(screen_key, {}).get("enabled", False))

    def _page_ids(self, screen_key: str) -> List[str]:
        screen = self.screen_defs[screen_key]
        return [str(p.get("id", "")) for p in screen.pages if p.get("id")]

    def _page_id_from_index(self, screen_key: str, page_index: int) -> str:
        page_ids = self._page_ids(screen_key)
        if 0 <= page_index < len(page_ids):
            return page_ids[page_index]
        return self.active_pages.get(screen_key, page_ids[0] if page_ids else "main")

    def _page_index_from_id(self, screen_key: str, page_id: str) -> int:
        page_ids = self._page_ids(screen_key)
        try:
            return page_ids.index(page_id)
        except ValueError:
            return 0

    def _log_transport(self, screen_key: str, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        line = f"{stamp} [{screen_key}] {message}"
        self.transport_log.setdefault(screen_key, deque(maxlen=200)).append(line)

    def _request_current_page(self, device: TarzanNextionDevice) -> None:
        if device.connected:
            self._send_payload(device.name, command_bytes("sendme"), tag="sendme")

    def get_recent_transport_log(self, screen_key: str, limit: int = 30) -> List[str]:
        return list(self.transport_log.get(screen_key, []))[-max(1, int(limit)):]

    def _bump_rrp_revision(self, screen_key: str) -> None:
        self._rrp_revision[screen_key] = int(self._rrp_revision.get(screen_key, 0)) + 1

    def _maybe_poll_rrp_state(self, screen_key: str) -> None:
        device = self.devices.get(screen_key)
        if device is None or not device.connected or self.active_pages.get(screen_key) != "rrp_main":
            return

        pending = self._pending_numeric_query.get(screen_key, [])
        if len(pending) > 6:
            return

        now = time.time()
        if now - float(self._last_rrp_poll_ts.get(screen_key, 0.0)) < self._RRP_POLL_INTERVAL:
            return
        self._last_rrp_poll_ts[screen_key] = now

        cycle_idx = int(self._rrp_poll_cycle.get(screen_key, 0)) % 4
        self._rrp_poll_cycle[screen_key] = cycle_idx + 1

        poll_sets = [
            [("va_p1_val.val", "rrp:va_p1_val")],
            [("va_p2_val.val", "rrp:va_p2_val")],
            [("h_p1_sens.val", "rrp:h_p1_sens"), ("va_p1_axis.val", "rrp:va_p1_axis"), ("va_p1_dir.val", "rrp:va_p1_dir")],
            [("h_p2_sens.val", "rrp:h_p2_sens"), ("va_p2_axis.val", "rrp:va_p2_axis"), ("va_p2_dir.val", "rrp:va_p2_dir")],
        ]
        for expr, token in poll_sets[cycle_idx]:
            self._queue_numeric_get(screen_key, expr, token)

        if random.random() < 0.02:
            self._request_current_page(device)

    def _mark_rrp_hold(self, screen_key: str, field: str, seconds: float = 0.35) -> None:
        hold = self._rrp_hold_until.setdefault(screen_key, {})
        hold[field] = time.time() + max(0.05, float(seconds))

    def _mark_rrp_hold_many(self, screen_key: str, fields: List[str], seconds: float = 0.35) -> None:
        for field in fields:
            self._mark_rrp_hold(screen_key, field, seconds)

    def _rrp_hold_active(self, screen_key: str, field: str) -> bool:
        hold = self._rrp_hold_until.setdefault(screen_key, {})
        return time.time() < float(hold.get(field, 0.0) or 0.0)

    def get_rrp_state(self, screen_key: str = "nextion_7") -> Dict[str, Any]:
        """Zwraca stan RRP oparty na szynie sygnałowej."""
        state = self._default_rrp_state()
        
        for player in ("p1", "p2"):
            # Oś
            raw_axis = self.bus.get(f"par_rrp_{player}_axis", -1)
            state[f"va_{player}_axis"] = int(raw_axis) if raw_axis is not None else -1
            
            # Kierunek
            raw_dir = self.bus.get(f"par_rrp_{player}_dir", 0)
            state[f"va_{player}_dir"] = int(raw_dir) if raw_dir is not None else 0
            
            # Czułość
            raw_sens = self.bus.get(f"par_rrp_{player}_sens", 50)
            state[f"h_{player}_sens"] = int(raw_sens) if raw_sens is not None else 50
            
            # Potencjometr
            sig_pot = "play_p45_rrp_pot_h" if player == "p1" else "play_p47_rrp_pot_v"
            raw_pot = self.bus.get(sig_pot, 0)
            state[f"va_{player}_val"] = int(raw_pot) if raw_pot is not None else 0

        state["p1_axis_label"] = self._RRP_AXIS_LABELS.get(int(state.get("va_p1_axis", -1)), "STOP")
        state["p2_axis_label"] = self._RRP_AXIS_LABELS.get(int(state.get("va_p2_axis", -1)), "STOP")
        return state

    def _send_payload(self, screen_key: str, payload: bytes, *, tag: str = "") -> None:
        device = self.devices.get(screen_key)
        if device is None or not device.connected:
            return
        try:
            device.send_raw(payload)
            text = payload[:-3].decode("utf-8", errors="ignore") if payload.endswith(b"\xff\xff\xff") else repr(payload)
            label = f"TX {tag}: {text}" if tag else f"TX: {text}"
            self._log_transport(screen_key, label)
            self.last_commands.append(f"{screen_key}: {text}")
        except Exception as exc:
            self._log_transport(screen_key, f"TX_ERR {exc}")

    def _queue_numeric_get(self, screen_key: str, expression: str, token: str) -> None:
        self._pending_numeric_query[screen_key].append(token)
        self._send_payload(screen_key, command_bytes(f"get {expression}"), tag=f"get {expression}")

    # ------------------------------------------------------------------
    # CONNECTION
    # ------------------------------------------------------------------
    def connect_enabled(self) -> None:
        for key in self.devices:
            if self._enabled(key):
                self.connect_screen(key)

    def connect_screen(self, screen_key: str) -> bool:
        device = self.devices.get(screen_key)
        if device is None:
            return False
        self._log_transport(screen_key, f"OPEN port={device.port} baud={device.baudrate}")
        ok = device.handshake(wait_ms=100)
        if ok:
            self._log_transport(screen_key, "HANDSHAKE OK")
            page_id = self.active_pages.get(screen_key, "")
            if page_id:
                self._send_payload(screen_key, cmd_page(page_id), tag="page")
            self._request_current_page(device)
        else:
            self._log_transport(screen_key, f"HANDSHAKE FAIL err={getattr(device, 'last_error', '')}")
        return ok

    def disconnect_screen(self, screen_key: str) -> None:
        device = self.devices.get(screen_key)
        if device is not None:
            self._log_transport(screen_key, "CLOSE")
            device.close()

    def disconnect_all(self) -> None:
        for key, device in self.devices.items():
            self._log_transport(key, "CLOSE")
            device.close()

    # ------------------------------------------------------------------
    # SNAPSHOT / PAGE
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        base = self.state_mapper.snapshot()
        for key, device in self.devices.items():
            base[f"{key}.connected"] = bool(device.connected)
            base[f"{key}.port"] = device.port
            base[f"{key}.baudrate"] = int(device.baudrate)
            base[f"{key}.last_error"] = device.last_error or ""
            base[f"{key}.page"] = self.active_pages.get(key, "")
            rrp = self.get_rrp_state(key)
            for rrp_key, value in rrp.items():
                base[f"{key}.rrp.{rrp_key}"] = value
            base[f"{key}.rrp_rev"] = int(self._rrp_revision.get(key, 0))
            recent = self.get_recent_transport_log(key, limit=2)
            base[f"{key}.log_last"] = recent[-1] if recent else ""
        return base

    def set_page(self, screen_key: str, page_id: str) -> None:
        self.active_pages[screen_key] = page_id
        device = self.devices.get(screen_key)
        if device is not None and device.connected:
            self._send_payload(screen_key, cmd_page(page_id), tag="page")
            self._request_current_page(device)

    def next_page(self, screen_key: str) -> None:
        screen = self.screen_defs[screen_key]
        pages = [p.get("id") for p in screen.pages]
        if not pages:
            return
        cur = self.active_pages.get(screen_key, pages[0])
        idx = pages.index(cur) if cur in pages else 0
        self.set_page(screen_key, pages[(idx + 1) % len(pages)])

    def prev_page(self, screen_key: str) -> None:
        screen = self.screen_defs[screen_key]
        pages = [p.get("id") for p in screen.pages]
        if not pages:
            return
        cur = self.active_pages.get(screen_key, pages[0])
        idx = pages.index(cur) if cur in pages else 0
        self.set_page(screen_key, pages[(idx - 1) % len(pages)])

    def get_page(self, screen_key: str) -> Dict[str, Any]:
        screen = self.screen_defs[screen_key]
        page_id = self.active_pages.get(screen_key)
        for page in screen.pages:
            if page.get("id") == page_id:
                return page
        return screen.pages[0] if screen.pages else {"id": "empty", "components": []}

    # ------------------------------------------------------------------
    # OUTBOUND STATE -> NEXTION
    # ------------------------------------------------------------------
    def build_commands(self, screen_key: str, state: Dict[str, Any]) -> List[bytes]:
        page = self.get_page(screen_key)
        commands: List[bytes] = []
        for comp in page.get("components", []):
            nxt = comp.get("nextion") or {}
            component = nxt.get("component")
            prop = nxt.get("property", "txt")
            if not component:
                continue
            visible_if = comp.get("visible_if")
            if visible_if:
                commands.append(cmd_visible(component, bool(state.get(visible_if))))
            bind = comp.get("bind")
            if bind:
                value = state.get(bind, comp.get("text", ""))
            else:
                value = comp.get("text", "")
            if prop == "val":
                commands.append(cmd_value(component, value))
            else:
                commands.append(cmd_text(component, value))
        return commands

    def _level_xyz_commands(self, screen_key: str, state: Dict[str, Any]) -> List[bytes]:
        if screen_key != "nextion_7":
            return []
        if self.active_pages.get(screen_key) != "level_xyz":
            return []

        try:
            x = int(float(self.bus.get("par_level_x", 0) or 0))
        except Exception:
            x = 0
        try:
            y = int(float(self.bus.get("par_level_y", 0) or 0))
        except Exception:
            y = 0

        x = max(-30, min(30, x))
        y = max(-30, min(30, y))
        return [
            command_bytes(f"va0.val={x}"),
            command_bytes(f"va1.val={y}"),
        ]

    def _sync_rrp_from_bus(self, screen_key: str) -> None:
        """Uproszczona synchronizacja szyny do mostka. Wywoływane przed sync()."""
        state = self.get_rrp_state(screen_key)
        last_sent = self._last_sent_rrp_device.setdefault(screen_key, {})
        
        changed = False
        for k, v in state.items():
            if k.endswith("_label"): continue
            if last_sent.get(k) != v:
                # Deadband 50 dla ADC tekstowego
                if "val" in k and abs(int(last_sent.get(k, 0)) - int(v)) <= 50:
                    continue
                changed = True
                break
        
        if changed:
            self._bump_rrp_revision(screen_key)

    def _rrp_button_value_commands(self, state: Dict[str, Any]) -> List[bytes]:
        """Uproszczone podświetlanie przycisków osi."""
        mapping = {
            "b_p1_cam_v": 0, "b_p1_cam_t": 1, "b_p1_cam_f": 2, "b_p1_cam_h": 3, "b_p1_arm_h": 4, "b_p1_arm_v": 5,
            "b_p2_cam_v": 0, "b_p2_cam_t": 1, "b_p2_cam_f": 2, "b_p2_cam_h": 3, "b_p2_arm_h": 4, "b_p2_arm_v": 5,
        }
        commands: List[bytes] = []
        p1_axis = int(state.get("va_p1_axis", -1))
        p2_axis = int(state.get("va_p2_axis", -1))
        
        for component, axis_idx in mapping.items():
            player_axis = p1_axis if component.startswith("b_p1_") else p2_axis
            # W Nextion Dual-state: 0=active/pressed(red), 1=inactive/normal(gray)
            val = 0 if player_axis == axis_idx else 1
            commands.append(command_bytes(f"{component}.val={val}"))
            
        commands.append(command_bytes(f"b_p1_dir.val={int(state.get('va_p1_dir', 0))}"))
        commands.append(command_bytes(f"b_p2_dir.val={int(state.get('va_p2_dir', 0))}"))
        return commands

    def _nextion7_rrp_commands(self) -> List[bytes]:
        """Generuje komendy RRP (Zadajnik parametrów + Wskaźniki)."""
        screen_key = "nextion_7"
        state = self.get_rrp_state(screen_key)
        commands = []
        last_sent = self._last_sent_rrp_device.setdefault(screen_key, {})

        for p in ("p1", "p2"):
            val_key = f"va_{p}_val"
            val_adc = int(state.get(val_key, 0))
            if not self._rrp_hold_active(screen_key, val_key):
                if abs(val_adc - int(last_sent.get(val_key, -999))) > 50:
                    commands.append(command_bytes(f"{val_key}.val={val_adc}"))
                    commands.append(command_bytes(f't_{p}_val.txt="{val_adc}"'))
                    last_sent[val_key] = val_adc

            for suffix in ("axis", "dir", "sens"):
                key = f"va_{p}_{suffix}" if suffix != "sens" else f"h_{p}_sens"
                if self._rrp_hold_active(screen_key, key):
                    continue
                val = int(state.get(key, -1 if "axis" in key else (50 if "sens" in key else 0)))
                if last_sent.get(key) != val:
                    commands.append(command_bytes(f"{key}.val={val}"))
                    last_sent[key] = val

        if not any(self._rrp_hold_active(screen_key, field) for field in (
            "va_p1_axis", "va_p2_axis", "va_p1_dir", "va_p2_dir"
        )):
            commands.extend(self._rrp_button_value_commands(state))
        return commands

    def _page_specific_commands(self, screen_key: str) -> List[bytes]:
        page_id = self.active_pages.get(screen_key, "")
        if screen_key == "nextion_7" and page_id == "rrp_main":
            return self._nextion7_rrp_commands()
        return []

    def sync(self, force: bool = False) -> None:
        # Zanim zrobimy snapshot, synchronizujemy RRP z szyny
        for key in self.devices:
            if self._enabled(key):
                self._sync_rrp_from_bus(key)

        snapshot = self.snapshot()
        now = time.time()
        interval = max(0.1, float(self.ports_cfg.get("sync_interval_ms", 100)) / 1000.0)
        if not force and snapshot == self.last_sent_snapshot and (now - self.last_sync) < interval:
            return

        self.last_sync = now
        self.last_commands = []

        for key, device in self.devices.items():
            if not self._enabled(key) or not device.connected:
                continue

            commands = self.build_commands(key, snapshot)
            commands.extend(self._level_xyz_commands(key, snapshot))
            commands.extend(self._page_specific_commands(key))

            cache = self._last_payload_by_screen.setdefault(key, {})
            for payload in commands:
                payload_text = payload[:-3].decode("utf-8", errors="ignore") if payload.endswith(b"\xff\xff\xff") else repr(payload)
                if not force and cache.get(payload_text) == payload:
                    continue
                cache[payload_text] = payload
                self._send_payload(key, payload)

        self.last_sent_snapshot = dict(snapshot)

    # ------------------------------------------------------------------
    # INBOUND NEXTION -> STATE
    # ------------------------------------------------------------------
    def _apply_axis_dir(self, axis_idx: int, value: int) -> None:
        for signal in self._RRP_AXIS_DIR_SIGNALS.get(axis_idx, []):
            if hasattr(self.bus, "exists") and self.bus.exists(signal):
                self.bus.force_signal(signal, int(value), source="NEXTION_RRP_DIR")

    def _apply_slider_to_bus(self, player: str, slider_value: int) -> None:
        sig_sens = f"par_rrp_{player}_sens"
        if hasattr(self.bus, "force_signal"):
            self.bus.force_signal(sig_sens, int(slider_value), source="NEXTION_RRP")
        return

    def _apply_rrp_value_to_bus(self, player: str, value: int) -> None:
        signal = "play_p45_rrp_pot_h" if player == "p1" else "play_p47_rrp_pot_v"
        raw_value = max(0, min(4095, int(value)))
        try:
            # Używamy force_signal, ponieważ play_* to zazwyczaj sygnały typu OUT,
            # a my chcemy je nadpisać z fizycznego kontrolera RRP.
            if hasattr(self.bus, "force_signal"):
                self.bus.force_signal(signal, raw_value, source="NEXTION_RRP")
            elif hasattr(self.bus, "set_input"):
                self.bus.set_input(signal, raw_value, source="NEXTION_RRP")
            
            # Podbijamy rewizję, aby wskaźniki cyfrowe w podglądzie odświeżały się płynnie
            self._bump_rrp_revision("nextion_7")
        except Exception:
            pass

    def _handle_rrp_stop(self, screen_key: str) -> None:
        """Zatrzymuje obie osie RRP (ustawia axis na -1 i dir na 0)."""
        for player in ("p1", "p2"):
            self.bus.force_signal(f"par_rrp_{player}_axis", -1, source="NEXTION_RRP_STOP")
            self.bus.force_signal(f"par_rrp_{player}_dir", 0, source="NEXTION_RRP_STOP")
            
        self._bump_rrp_revision(screen_key)
        self._log_transport(screen_key, "RRP STOP (Axis/Dir reset only)")

    def _handle_page_navigation_touch(self, screen_key: str, page_id: str, component_id: int) -> bool:
        page_map = self._PAGE_COMPONENT_TO_PAGE.get(page_id, {})
        target = page_map.get(component_id)
        if target:
            self.active_pages[screen_key] = target
            self._log_transport(screen_key, f"NAV {page_id}:{component_id} -> {target}")
            return True
        return False

    def _handle_touch_release(self, screen_key: str, page_index: int, component_id: int) -> None:
        page_id = self._page_id_from_index(screen_key, page_index)
        if self._handle_page_navigation_touch(screen_key, page_id, component_id):
            return

        if screen_key != "nextion_7" or page_id != "rrp_main":
            return

        self._mark_rrp_hold_many(screen_key, [
            "va_p1_axis", "va_p2_axis", "va_p1_dir", "va_p2_dir",
            "h_p1_sens", "h_p2_sens", "va_p1_val", "va_p2_val",
        ], 0.40)

        if component_id in self._RRP_AXIS_BY_COMPONENT:
            player, _ = self._RRP_AXIS_BY_COMPONENT[component_id]
            self._mark_rrp_hold(screen_key, f"va_{player}_axis", 0.40)
            self._queue_numeric_get(screen_key, f"va_{player}_axis.val", f"rrp:va_{player}_axis")
        elif component_id == 8: # b_p1_dir
            self._mark_rrp_hold(screen_key, "va_p1_dir", 0.40)
            self._queue_numeric_get(screen_key, "va_p1_dir.val", "rrp:va_p1_dir")
        elif component_id == 9: # b_p2_dir
            self._mark_rrp_hold(screen_key, "va_p2_dir", 0.40)
            self._queue_numeric_get(screen_key, "va_p2_dir.val", "rrp:va_p2_dir")
        elif component_id == 2: # h_p1_sens
            self._mark_rrp_hold(screen_key, "h_p1_sens", 0.50)
            self._queue_numeric_get(screen_key, "h_p1_sens.val", "rrp:h_p1_sens")
        elif component_id == 4: # h_p2_sens
            self._mark_rrp_hold(screen_key, "h_p2_sens", 0.50)
            self._queue_numeric_get(screen_key, "h_p2_sens.val", "rrp:h_p2_sens")
        elif component_id == 25: # b_stop
            self._handle_rrp_stop(screen_key)
        else:
            for expr, token in [
                ("va_p1_val.val", "rrp:va_p1_val"), ("va_p2_val.val", "rrp:va_p2_val"),
                ("h_p1_sens.val", "rrp:h_p1_sens"), ("h_p2_sens.val", "rrp:h_p2_sens"),
                ("va_p1_axis.val", "rrp:va_p1_axis"), ("va_p2_axis.val", "rrp:va_p2_axis"),
                ("va_p1_dir.val", "rrp:va_p1_dir"), ("va_p2_dir.val", "rrp:va_p2_dir"),
            ]:
                self._queue_numeric_get(screen_key, expr, token)

    def _handle_numeric_response(self, screen_key: str, value: int) -> None:
        pending = self._pending_numeric_query.get(screen_key) or deque()
        token = pending.popleft() if pending else None
        if not token:
            return

        # Podbijamy rewizję stanu dla preview przy każdej odpowiedzi z urządzenia
        self._bump_rrp_revision(screen_key)
        
        mapping = {
            "rrp:va_p1_axis": "par_rrp_p1_axis", "rrp:va_p2_axis": "par_rrp_p2_axis",
            "rrp:va_p1_dir":  "par_rrp_p1_dir",  "rrp:va_p2_dir":  "par_rrp_p2_dir",
            "rrp:h_p1_sens":  "par_rrp_p1_sens", "rrp:h_p2_sens":  "par_rrp_p2_sens",
        }
        
        if token in mapping:
            sig = mapping[token]
            self.bus.force_signal(sig, value, source="device")
            field = token.split(":")[-1]
            self._last_sent_rrp_device.setdefault(screen_key, {})[field] = value

        elif token == "rrp:va_p1_val":
            self.bus.force_signal("play_p45_rrp_pot_h", value, source="device")
            self._last_sent_rrp_device.setdefault(screen_key, {})["va_p1_val"] = value
        elif token == "rrp:va_p2_val":
            self.bus.force_signal("play_p47_rrp_pot_v", value, source="device")
            self._last_sent_rrp_device.setdefault(screen_key, {})["va_p2_val"] = value

    def _rrp_generate_steps(self) -> None:
        """Lekki generator STEP dla RRP (Model XYZ). Wywoływany z poll()."""
        now = time.time()
        # Bezpiecznik startowy: 3s spokoju
        boot_ts = getattr(self, "_rrp_boot_ts", 0.0)
        if boot_ts == 0.0:
            self._rrp_boot_ts = now
            return
        if now - boot_ts < 3.0:
            return

        for p in ("p1", "p2"):
            axis_idx = int(self.bus.get(f"par_rrp_{p}_axis", -1))
            if axis_idx == -1: continue
            
            sig_pot = "play_p45_rrp_pot_h" if p == "p1" else "play_p47_rrp_pot_v"
            val = float(self.bus.get(sig_pot, 0))
            if val < 30.0: continue # Martwa strefa
            
            sens = int(self.bus.get(f"par_rrp_{p}_sens", 50))
            direction = int(self.bus.get(f"par_rrp_{p}_dir", 0))
            
            intensity = val / 4095.0
            speed_factor = 0.5 + (sens / 10.0)
            
            # Obliczenie opóźnienia między impulsami (0.01s - 2.0s)
            delay = 0.1 / max(0.05, intensity * speed_factor)
            
            last_ts_attr = f"_rrp_last_step_ts_{p}"
            last_ts = getattr(self, last_ts_attr, 0.0)
            
            if now - last_ts >= delay:
                setattr(self, last_ts_attr, now)
                axis_name = self._RRP_AXIS_MAP.get(axis_idx)
                if not axis_name: continue
                
                bnd = self._AXIS_SIGNAL_BINDINGS.get(axis_name, {})
                # DIR
                for ds in bnd.get("dir", []):
                    self.bus.force_signal(ds, direction, source="RRP_GEN")
                # STEP (impuls binarny)
                for ss in bnd.get("step", []):
                    self.bus.force_signal(ss, 1, source="RRP_GEN")
                    # Ponieważ nie mamy .after(), impuls '0' wyślemy w następnym cyklu lub zaraz po
                    self.bus.force_signal(ss, 0, source="RRP_GEN")

    def poll(self) -> List[str]:
        logs: List[str] = []
        # Wywołujemy generator kroków RRP w każdym cyklu poll
        self._rrp_generate_steps()
        
        for key, device in self.devices.items():
            self._maybe_poll_rrp_state(key)
            
            # Fallback: jeśli kolejka pytań jest zbyt długa, czyścimy ją (zapobieganie zatorom)
            if len(self._pending_numeric_query.get(key, [])) > 20:
                self._pending_numeric_query[key].clear()
                self._log_transport(key, "CLEARED pending numeric query queue (overflow)")

            for event in device.poll():
                raw = bytes(getattr(event, "raw", b""))
                self._log_transport(key, f"RX {raw!r}")
                logs.append(f"{key} EVENT {raw!r}")

                if len(raw) >= 2 and raw[0] == 0x66:
                    page_id = self._page_id_from_index(key, int(raw[1]))
                    old_page = self.active_pages.get(key)
                    self.active_pages[key] = page_id
                    logs.append(f"{key} PAGE {page_id}")
                    self._log_transport(key, f"PAGE {page_id}")
                    # Jeśli weszliśmy na rrp_main, wymuszamy odświeżenie całego stanu
                    if page_id == "rrp_main" and old_page != "rrp_main":
                        self._log_transport(key, "RRP_MAIN enter -> forcing full state poll")
                        # Lista wszystkich zmiennych do odpytania przy wejściu na stronę
                        vars_to_poll = [
                            ("va_p1_val.val", "rrp:va_p1_val"), ("va_p2_val.val", "rrp:va_p2_val"),
                            ("h_p1_sens.val", "rrp:h_p1_sens"), ("h_p2_sens.val", "rrp:h_p2_sens"),
                            ("va_p1_axis.val", "rrp:va_p1_axis"), ("va_p2_axis.val", "rrp:va_p2_axis"),
                            ("va_p1_dir.val", "rrp:va_p1_dir"), ("va_p2_dir.val", "rrp:va_p2_dir"),
                        ]
                        for expr, token in vars_to_poll:
                            self._queue_numeric_get(key, expr, token)
                    continue

                if len(raw) >= 5 and raw[0] == 0x71:
                    value = int.from_bytes(raw[1:5], byteorder="little", signed=True)
                    self._handle_numeric_response(key, value)
                    continue

                if len(raw) >= 4 and raw[0] == 0x65:
                    page_index = int(raw[1])
                    component_id = int(raw[2])
                    event_type = int(raw[3])
                    logs.append(f"{key} TOUCH page={page_index} comp={component_id} event={event_type}")
                    self._log_transport(key, f"TOUCH page={page_index} comp={component_id} event={event_type}")
                    if event_type == 1:
                        self._handle_touch_release(key, page_index, component_id)
                    
                    self._request_current_page(device)
                    continue
                
                # Ignorujemy błędy "Invalid Variable" 0x1A jeśli pollujemy stare zmienne
                if len(raw) >= 1 and raw[0] == 0x1A:
                    continue

    # ------------------------------------------------------------------
    # PREVIEW HELPERS
    # ------------------------------------------------------------------
    def preview_rrp_tap(self, screen_key: str, target: str) -> None:
        """Pomocnik dla podglądu PAR: pisze bezpośrednio na szynę sygnałową."""
        if screen_key != "nextion_7":
            return

        elif target == "home":
            self.set_page(screen_key, "page1")
            return
        
        # Podbijamy rewizję, żeby podgląd w PAR wiedział o konieczności odświeżenia grafiki
        self._bump_rrp_revision(screen_key)

        tap_map = {
            "p1_cam_v": ("axis", "p1", 0),
            "p1_cam_t": ("axis", "p1", 1),
            "p1_cam_f": ("axis", "p1", 2),
            "p1_cam_h": ("axis", "p1", 3),
            "p1_arm_h": ("axis", "p1", 4),
            "p1_arm_v": ("axis", "p1", 5),
            "p2_cam_v": ("axis", "p2", 0),
            "p2_cam_t": ("axis", "p2", 1),
            "p2_cam_f": ("axis", "p2", 2),
            "p2_cam_h": ("axis", "p2", 3),
            "p2_arm_h": ("axis", "p2", 4),
            "p2_arm_v": ("axis", "p2", 5),
            "p1_dir": ("dir", "p1", None),
            "p2_dir": ("dir", "p2", None),
            "stop": ("stop", None, None),
        }
        item = tap_map.get(target)
        if not item: return

        kind, player, axis_idx = item
        if kind == "axis":
            cur = int(self.bus.get(f"par_rrp_{player}_axis", -1))
            new_val = -1 if cur == int(axis_idx) else int(axis_idx)
            self._mark_rrp_hold(screen_key, f"va_{player}_axis", 0.3)
            self.bus.force_signal(f"par_rrp_{player}_axis", new_val, source="PREVIEW")
        elif kind == "dir":
            self._mark_rrp_hold(screen_key, f"va_{player}_dir", 0.3)
            cur = int(self.bus.get(f"par_rrp_{player}_dir", 0))
            self.bus.force_signal(f"par_rrp_{player}_dir", 0 if cur else 1, source="PREVIEW")
        elif kind == "stop":
            self._handle_rrp_stop(screen_key)

    def preview_rrp_set_value(self, screen_key: str, player: str, value: int) -> None:
        if screen_key != "nextion_7": return
        self._mark_rrp_hold(screen_key, f"h_{player}_sens", 0.5)
        self._bump_rrp_revision(screen_key)
        self.bus.force_signal(f"par_rrp_{player}_sens", int(value), source="PREVIEW")

    def preview_rrp_set_pot(self, screen_key: str, player: str, value: int) -> None:
        if screen_key != "nextion_7": return
        self._mark_rrp_hold(screen_key, f"va_{player}_val", 0.5)
        self._bump_rrp_revision(screen_key)
        signal = "play_p45_rrp_pot_h" if player == "p1" else "play_p47_rrp_pot_v"
        self.bus.force_signal(signal, int(value), source="PREVIEW")
