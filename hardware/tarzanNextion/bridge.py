from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import json
import time
from typing import Any, Dict, List

from .config import load_ports
from .device import TarzanNextionDevice
from .protocol import cmd_page, cmd_text, cmd_visible, command_bytes
from .screen_model import ScreenDefinition, load_screen_definition
from .state_mapper import TarzanNextionStateMapper

try:
    from editor.TFD.tfd_state import tfd_state
except (ImportError, ModuleNotFoundError):
    tfd_state = None


# RRP: jedyne miejsce dekodowania numeru osi z fizycznego Nextiona.
# Dalej w SignalBus nie przenosimy indeksu jako źródła prawdy, tylko
# kanoniczne nazwy sygnałów zgodne z core/tarzanZmienneSygnalowe.py.
RRP_POT_SIGNAL_BY_PLAYER = {
    "p1": "sensor_rrp_pot_h",
    "p2": "sensor_rrp_pot_v",
}

def _rrp_binding(selected_axis: str, step_signal: str, dir_signal: str, en_signal: str) -> Dict[str, str]:
    return {
        "selected_axis": selected_axis,
        "step_signal": step_signal,
        "dir_signal": dir_signal,
        "en_signal": en_signal,
    }


# Korekta według rzeczywistego zachowania FIZYCZNEGO Nextiona.
# Indeks z Nextiona jest tylko wejściem; dalej do busa idą nazwy kanoniczne.
# P1 i P2 mają osobne wiersze przycisków, dlatego rozpoznanie indeksu jest osobne dla playera.
RRP_AXIS_BY_NEXTION_INDEX = {
    "p1": {
        0: _rrp_binding("cam_h", "axis_cam_h_step", "axis_cam_h_dir", "axis_cam_h_en"),
        1: _rrp_binding("cam_v", "axis_cam_v_step", "axis_cam_v_dir", "axis_cam_v_en"),
        2: _rrp_binding("cam_f", "axis_cam_f_step", "axis_cam_f_dir", "axis_cam_f_en"),
        3: _rrp_binding("arm_t", "axis_arm_t_step", "axis_arm_t_dir", "axis_arm_t_en"),
        4: _rrp_binding("arm_h", "axis_arm_h_step", "axis_arm_h_dir", "axis_arm_h_en"),
        5: _rrp_binding("arm_v", "axis_arm_v_step", "axis_arm_v_dir", "axis_arm_v_en"),
    },
    "p2": {
        0: _rrp_binding("cam_h", "axis_cam_h_step", "axis_cam_h_dir", "axis_cam_h_en"),
        1: _rrp_binding("cam_v", "axis_cam_v_step", "axis_cam_v_dir", "axis_cam_v_en"),
        2: _rrp_binding("cam_f", "axis_cam_f_step", "axis_cam_f_dir", "axis_cam_f_en"),
        3: _rrp_binding("arm_t", "axis_arm_t_step", "axis_arm_t_dir", "axis_arm_t_en"),
        4: _rrp_binding("arm_h", "axis_arm_h_step", "axis_arm_h_dir", "axis_arm_h_en"),
        5: _rrp_binding("arm_v", "axis_arm_v_step", "axis_arm_v_dir", "axis_arm_v_en"),
    },
}

RRP_ALL_EN_SIGNALS = tuple(
    sorted({axis["en_signal"] for player_map in RRP_AXIS_BY_NEXTION_INDEX.values() for axis in player_map.values()})
)
RRP_REC_AUTO_EN_SIGNALS = {"axis_cam_v_en", "axis_arm_t_en", "axis_cam_f_en", "axis_cam_h_en"}


def _rrp_axis_binding(player: str, nextion_axis_index: int) -> Dict[str, str]:
    try:
        idx = int(nextion_axis_index)
    except (TypeError, ValueError):
        idx = -1
    player_map = RRP_AXIS_BY_NEXTION_INDEX.get(player, {})
    if idx not in player_map:
        return {
            "selected_axis": "",
            "step_signal": "",
            "dir_signal": "",
            "en_signal": "",
        }
    return player_map[idx]

try:
    from audio.tarzanAudioPlayer import play as play_audio
except ImportError:
    play_audio = None


class TarzanNextionBridge:
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
        self._transport_log: List[str] = []
        self._transport_log_limit = 500
        self._nextion_ui_cut = bool(getattr(tfd_state, "nextion_ui_cut", False)) if tfd_state is not None else False
        self._snapshot_cache = {}
        self._snapshot_time = 0.0
        self.last_version = -1
        self._snajper_pending = OrderedDict()
        self._tfd_save_status_until = 0.0
        self._tfd_save_status_visible = False
        # Teksty settings_main są edytowalne na fizycznym Nextionie.
        # Dlatego odtwarzamy je z JSON/stanu tylko raz po starcie bridge,
        # a potem nie nadpisujemy ich przy każdym powrocie na stronę.
        self._settings_main_text_loaded = False
        self._tarzan_snajper = None
        self._reverse_signal_map: Dict[str, List[str]] = {}

        # TC sterowany fizycznym b_clap.
        # To nie jest osobny bridge ani nowy refresh: b_clap tylko otwiera/zamyka
        # istniejący tor Snajpera dla take_timecode, a flush zostaje w flush_snajper_commands().
        self._clap_tc_running = False
        self._clap_tc_start_monotonic = 0.0
        self._clap_tc_start_elapsed_ms = 0
        self._clap_tc_elapsed_ms = 0
        self._clap_tc_last_sent_ms = -1
        self._clap_tc_last_toggle_monotonic = 0.0

        # Stan RRP (Physical Source of Truth)
        self.rrp_state = {
            "va_p1_axis": -1, "va_p1_dir": 0, "va_p1_val": 0, "h_p1_sens": 0,
            "va_p2_axis": -1, "va_p2_dir": 0, "va_p2_val": 0, "h_p2_sens": 0,
            "rrp_rev": 0
        }

        # TFD metadata bootstrap: na starcie odtwarzamy stan zapisany w JSON,
        # żeby settings_main po sendme dostał aktualny TITLE/DIRECTOR/UI CUT.
        self._bootstrap_tfd_metadata_from_json()

    def _candidate_tfd_metadata_paths(self) -> List[Path]:
        """Możliwe lokalizacje zapisu metadanych TFD w projekcie."""
        root = Path(__file__).resolve().parents[2]
        paths: List[Path] = []

        # Jeśli singleton tfd_state zna własną ścieżkę, traktujemy ją jako pierwszą.
        if tfd_state is not None:
            for attr in ("metadata_path", "meta_path", "json_path", "path", "META_PATH"):
                raw = getattr(tfd_state, attr, None)
                if raw:
                    try:
                        paths.append(Path(raw))
                    except Exception:
                        pass

        paths.extend([
            root / "data" / "tfd_metadata.json",
            root / "data" / "tfd" / "tfd_metadata.json",
            root / "data" / "TFD" / "tfd_metadata.json",
            root / "editor" / "TFD" / "tfd_metadata.json",
            root / "tfd_metadata.json",
        ])

        unique: List[Path] = []
        seen = set()
        for path in paths:
            try:
                resolved = path.resolve()
            except Exception:
                resolved = path
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            unique.append(path)
        return unique

    def _read_tfd_metadata_json(self) -> Dict[str, Any]:
        """Czyta zapisane TITLE/DIRECTOR/UI CUT z JSON bez tworzenia nowego źródła prawdy."""
        for path in self._candidate_tfd_metadata_paths():
            try:
                if not path.exists():
                    continue
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    self._append_transport_log(f"EV nextion_7: TFD META JSON LOAD {path}")
                    return data
            except Exception as exc:
                self._append_transport_log(f"EV nextion_7: TFD META JSON READ ERROR {path}: {exc}")
        return {}

    @staticmethod
    def _json_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(int(value))
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off", ""}:
            return False
        return default

    def _bootstrap_tfd_metadata_from_json(self) -> None:
        """Na starcie ładuje metadane TFD z JSON do tfd_state/busa/bridge."""
        data = self._read_tfd_metadata_json()
        if not data:
            return

        title = data.get("title")
        director = data.get("director")
        has_ui_cut = "nextion_ui_cut" in data
        ui_cut = self._json_bool(data.get("nextion_ui_cut"), default=self._nextion_ui_cut) if has_ui_cut else self._nextion_ui_cut

        if tfd_state is not None:
            try:
                kwargs: Dict[str, Any] = {}
                if title is not None:
                    kwargs["title"] = str(title)
                if director is not None:
                    kwargs["director"] = str(director)
                if has_ui_cut:
                    kwargs["nextion_ui_cut"] = bool(ui_cut)
                if kwargs and hasattr(tfd_state, "update_meta"):
                    tfd_state.update_meta(**kwargs)
                else:
                    if title is not None:
                        setattr(tfd_state, "title", str(title))
                    if director is not None:
                        setattr(tfd_state, "director", str(director))
                    if has_ui_cut:
                        setattr(tfd_state, "nextion_ui_cut", bool(ui_cut))
            except Exception as exc:
                self._append_transport_log(f"EV nextion_7: TFD META STATE BOOT ERROR {exc}")

        if title is not None:
            try:
                self.bus.force_signal("tfd_title", str(title), source="TFD_JSON_BOOT")
            except Exception:
                pass
        if director is not None:
            try:
                self.bus.force_signal("tfd_director", str(director), source="TFD_JSON_BOOT")
            except Exception:
                pass
        if has_ui_cut:
            self._nextion_ui_cut = bool(ui_cut)
            try:
                self.bus.force_signal("nextion_ui_cut", 1 if ui_cut else 0, source="TFD_JSON_BOOT")
            except Exception:
                pass

    @property
    def tarzan_snajper(self):
        return self._tarzan_snajper

    @tarzan_snajper.setter
    def tarzan_snajper(self, value):
        self._tarzan_snajper = value
        if value:
            self._rebuild_reverse_signal_map()

    def _rebuild_reverse_signal_map(self):
        """Buduje mapę logical -> List[raw_signals] dla potrzeb refreshu."""
        self._reverse_signal_map = {}
        snajper = self._tarzan_snajper
        if not snajper:
            return
        
        # 1. Mapowanie z signal_map
        if hasattr(snajper, "signal_map"):
            for raw, logical in snajper.signal_map.items():
                self._reverse_signal_map.setdefault(logical, []).append(raw)
        
        # 2. Mapowanie tożsamościowe i prefiksy dla wszystkich nazw logicznych
        if hasattr(snajper, "targets"):
            for logical in snajper.targets.keys():
                # Kandydaci na nazwy w busie
                candidates = [logical, f"par_{logical}", f"sensor_{logical}", f"par_sensor_{logical}"]
                
                # Dodatkowe specyficzne mapowania dla osi
                if logical.startswith("axis_") and logical.endswith("_value"):
                    # np. axis_0_value -> par_axis_0_pos, axis_0_pos
                    try:
                        axis_id = logical.split("_")[1]
                        candidates.extend([f"par_axis_{axis_id}_pos", f"axis_{axis_id}_pos"])
                    except (IndexError, ValueError):
                        pass
                elif logical.startswith("axis_") and logical.endswith("_dir"):
                    try:
                        axis_id = logical.split("_")[1]
                        candidates.extend([f"par_axis_{axis_id}_dir", f"axis_{axis_id}_dir"])
                    except (IndexError, ValueError):
                        pass
                
                for cand in candidates:
                    if logical not in self._reverse_signal_map:
                        self._reverse_signal_map[logical] = [cand]
                    elif cand not in self._reverse_signal_map[logical]:
                        self._reverse_signal_map[logical].append(cand)

    def get_rrp_state(self, screen_key: str = "nextion_7") -> Dict[str, Any]:
        return dict(self.rrp_state)

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

    def _request_current_page(self, screen_key: str, device: TarzanNextionDevice) -> None:
        if device.connected:
            self._append_transport_log(f"TX {screen_key}: sendme")
            device.send_raw(command_bytes("sendme"))

    def connect_enabled(self) -> None:
        for key in self.devices:
            if self._enabled(key):
                self.connect_screen(key)

    def connect_screen(self, screen_key: str) -> bool:
        device = self.devices.get(screen_key)
        if device is None:
            return False
        ok = device.handshake(wait_ms=100)
        self._append_transport_log(f"EV {screen_key}: CONNECT {'OK' if ok else 'FAIL'} port={device.port} baud={device.baudrate}")
        if ok:
            page_id = self.active_pages.get(screen_key, "")
            if page_id:
                self._append_transport_log(f"TX {screen_key}: page {page_id}")
                device.send_raw(cmd_page(page_id))
                self._refresh_physical_nextion_page_from_state(screen_key, page_id)
            self._request_current_page(screen_key, device)
        return ok

    def disconnect_screen(self, screen_key: str) -> None:
        device = self.devices.get(screen_key)
        if device is not None:
            self._append_transport_log(f"EV {screen_key}: DISCONNECT")
            device.close()

    def disconnect_all(self) -> None:
        for device in self.devices.values():
            device.close()

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        if (now - self._snapshot_time) < 0.02:
            return self._snapshot_cache
        base = self.state_mapper.snapshot()
        for key, device in self.devices.items():
            base[f"{key}.connected"] = bool(device.connected)
            base[f"{key}.port"] = device.port
            base[f"{key}.baudrate"] = int(device.baudrate)
            base[f"{key}.last_error"] = device.last_error or ""
            base[f"{key}.page"] = self.active_pages.get(key, "")
            base[f"{key}.ui_cut"] = int(bool(self._nextion_ui_cut))
            base[f"{key}.snajper_pending"] = len(self._snajper_pending)
            base[f"{key}.transport_log_count"] = len(self._transport_log)
            
            # Dodajemy stan RRP do sekcji ekranu (wymagane przez PAR)
            if key == "nextion_7":
                base[f"{key}.rrp_rev"] = self.rrp_state.get("rrp_rev", 0)
                for k, v in self.rrp_state.items():
                    base[f"{key}.rrp.{k}"] = v
                # DODANE: Uwzględniamy gęstość STEP w snapshotcie, aby sync() wykrywał zmiany
                base[f"{key}.rrp.p1_val"] = self.bus.get("par_rrp_p1_val", "0")
                base[f"{key}.rrp.p2_val"] = self.bus.get("par_rrp_p2_val", "0")
        
        # Kompatybilność wsteczna
        for k, v in self.rrp_state.items():
            base[f"rrp.{k}"] = v
            
        if tfd_state:
            base["tfd.packet_id"] = tfd_state.packet_id

        self._snapshot_cache = base
        self._snapshot_time = now
        return base

    def set_page(self, screen_key: str, page_id: str) -> None:
        self.active_pages[screen_key] = page_id
        device = self.devices.get(screen_key)
        if device is not None and device.connected:
            self._append_transport_log(f"TX {screen_key}: page {page_id}")
            device.send_raw(cmd_page(page_id))
            self._refresh_physical_nextion_page_from_state(screen_key, page_id)
            self._request_current_page(screen_key, device)

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

    def _append_transport_log(self, line: str) -> None:
        """Lekki log transportu dla panelu diagnostycznego Nextiona."""
        try:
            stamp = time.strftime("%H:%M:%S")
        except Exception:
            stamp = "--:--:--"
        text = f"{stamp} {line}"
        self._transport_log.append(text)
        if len(self._transport_log) > self._transport_log_limit:
            del self._transport_log[:len(self._transport_log) - self._transport_log_limit]

    def get_recent_transport_log(self, screen_key: str = "nextion_7", limit: int = 120) -> List[str]:
        """Zwraca ostatnie logi TX/RX/PAGE/SET/SYS/ERR dla monitora PAR."""
        try:
            limit = max(1, int(limit))
        except Exception:
            limit = 120
        prefix_a = f"TX {screen_key}:"
        prefix_b = f"RX {screen_key}:"
        prefix_c = f"EV {screen_key}:"
        prefix_d = f"{screen_key} "
        filtered = [
            line for line in self._transport_log
            if prefix_a in line or prefix_b in line or prefix_c in line or prefix_d in line
        ]
        return filtered[-limit:]

    def clear_transport_log(self, screen_key: str | None = None) -> None:
        """Czyści log transportu. Jeśli podano screen_key, czyści tylko wpisy tego ekranu."""
        if not screen_key:
            self._transport_log.clear()
            return
        prefix_a = f"TX {screen_key}:"
        prefix_b = f"RX {screen_key}:"
        prefix_c = f"EV {screen_key}:"
        prefix_d = f"{screen_key} "
        self._transport_log = [
            line for line in self._transport_log
            if not (prefix_a in line or prefix_b in line or prefix_c in line or prefix_d in line)
        ]

    def get_nextion_monitor_state(self, screen_key: str = "nextion_7") -> Dict[str, Any]:
        """Jedno miejsce odczytu stanu dla uproszczonego panelu Nextiona."""
        device = self.devices.get(screen_key)
        return {
            "screen_key": screen_key,
            "connected": bool(getattr(device, "connected", False)) if device is not None else False,
            "port": getattr(device, "port", ""),
            "baudrate": int(getattr(device, "baudrate", 0) or 0),
            "last_error": getattr(device, "last_error", "") or "",
            "page": self.active_pages.get(screen_key, ""),
            "ui_cut": int(bool(self._nextion_ui_cut)),
            "pending": len(self._snajper_pending),
            "log_count": len(self._transport_log),
        }

    def queue_snajper_command(self, scope: str, component: str, prop: str, value) -> None:
        # TARZAN_SNAJPER_V8: Bridge jest tylko wykonawcą.
        # Cache i decyzja o wysyłce leży wyłącznie w core/tarzanSnajper.py.
        # Nextion .val nie przyjmuje True/False jako wartości; musi dostać 0/1.
        if isinstance(value, bool):
            value = "1" if value else "0"
        else:
            value = str(value)
        # Ochrona TC: po PAUZA/STOP nie przyjmujemy technicznego 00:00:00:000/001
        # z opóźnionego toru TFD/bus. T0 ma zostać na ostatnim realnym czasie.
        if (
            scope == "take_main"
            and component == "t0"
            and prop in {"txt", "text"}
            and not self._clap_tc_running
            and int(getattr(self, "_clap_tc_elapsed_ms", 0) or 0) > 100
            and str(value).strip() in {"00:00:00:000", "00:00:00:001", "0", "1"}
        ):
            return

        key = f"{scope}.{component}.{prop}"
        self._snajper_pending[key] = (scope, component, prop, value)

    def flush_snajper_commands(self) -> None:
        # TARZAN_SNAJPER: dynamiczne zmiany Nextiona.
        # Nieaktywne strony zostają w pending, żeby nie gubić wartości.
        self._update_clap_tc_for_snajper()
        self._update_tfd_save_status_for_snajper()
        pending = list(self._snajper_pending.items())
        for key, (scope, component, prop, value) in pending:
            if not self._is_scope_active(scope):
                continue

            command_texts: List[str] = []
            if prop in {"txt", "text"}:
                command_texts = [f'{component}.txt="{value}"']
                payloads = [cmd_text(component, value)]
            elif prop == "val":
                command_texts = [f"{component}.val={value}"]
                payloads = [command_bytes(command_texts[0])]
            elif prop == "pic":
                command_texts = [f"{component}.pic={value}"]
                payloads = [command_bytes(command_texts[0])]
            elif prop == "pco":
                command_texts = [f"{component}.pco={value}"]
                payloads = [command_bytes(command_texts[0])]
            elif prop == "visible":
                visible = str(value).strip().lower() not in {"0", "false", "off", "hidden", "hide", ""}
                command_texts = [f"vis {component},{1 if visible else 0}"]
                payloads = [cmd_visible(component, visible)]
            elif prop == "play":
                # Komenda play dla audio na Nextionie
                command_texts = [f"play {value}"]
                payloads = [command_bytes(command_texts[0])]
            else:
                continue

            sent = False
            for screen_key, device in self.devices.items():
                if self._enabled(screen_key) and device.connected and self.active_pages.get(screen_key) == scope:
                    self.last_commands.append(f"{screen_key}: SNAJPER {scope}.{component}.{prop}={value}")
                    for command_text, payload in zip(command_texts, payloads):
                        self._append_transport_log(f"TX {screen_key}: SNAJPER {scope}.{component}.{prop}={value} | {command_text}")
                        device.send_raw(payload)
                    sent = True

            if sent:
                self._snajper_pending.pop(key, None)

    def _is_scope_active(self, scope: str) -> bool:
        if not hasattr(self, "active_pages"):
            return True
        return scope in set(self.active_pages.values())

    def sync(self, force: bool = False) -> None:
        return self.flush_snajper_commands()

    def poll(self) -> List[str]:
        logs: List[str] = []
        for key, device in self.devices.items():
            for event in device.poll():
                raw = event.raw
                logs.append(f"{key} EVENT {raw!r}")
                self._append_transport_log(f"RX {key}: {raw!r}")

                # Obsługa zdarzeń tekstowych (np. rrp:, set:, take:)
                try:
                    # Nextion kończy tekst przez FF FF FF. Nie wolno usuwać FF i potem
                    # łapać regexem, bo sklejone set:title=...set:director=... ucina tekst.
                    messages = []
                    for part in raw.split(b'\xff\xff\xff'):
                        if not part:
                            continue

                        # b_clap w fizycznym HMI wysyła: print "take:clap=" + prints b_clap.val,0.
                        # Dla wartości 0 payload ma postać b"take:clap=\x00...". Nie wolno robić
                        # strip("\x00"), bo z explicit STOP robi się pusty payload i bridge traktuje go
                        # jako TOGGLE. Dlatego stan 1/0 dekodujemy z surowych bajtów przed stripem.
                        clap_prefix = b"take:clap="
                        clap_pos = part.find(clap_prefix)
                        if clap_pos >= 0:
                            payload = part[clap_pos + len(clap_prefix):]
                            value = 1 if payload and payload[0] == 1 else 0
                            messages.append(f"take:clap={value}")
                            continue

                        msg = part.decode("cp1250", errors="replace").strip("\x00\x1a\r\n ")
                        if msg:
                            messages.append(msg)

                    if not messages:
                        clean_raw = raw.replace(b'\xff', b'')
                        clap_prefix = b"take:clap="
                        clap_pos = clean_raw.find(clap_prefix)
                        if clap_pos >= 0:
                            payload = clean_raw[clap_pos + len(clap_prefix):]
                            value = 1 if payload and payload[0] == 1 else 0
                            messages.append(f"take:clap={value}")
                        else:
                            msg = clean_raw.decode("cp1250", errors="replace").strip("\x00\x1a\r\n ")
                            if msg:
                                messages.append(msg)

                    handled_text = False
                    for msg in messages:
                        if self._handle_snajper_text_message(msg, logs, key):
                            handled_text = True
                            continue
                        if msg.startswith("sys:ui_cut="):
                            self.active_pages[key] = "settings_main"
                            enabled = 1 if msg.split("=", 1)[1].strip() == "1" else 0
                            # SYS z przycisku b_ui_cut jest zmianą roboczą stanu ekranu.
                            # Nie zapisuje JSON i nie pokazuje SAVED. Zapis robi dopiero set:ui_cut z b_save_meta.
                            self._nextion_ui_cut = bool(enabled)
                            if tfd_state is not None:
                                try:
                                    setattr(tfd_state, "nextion_ui_cut", bool(enabled))
                                except Exception:
                                    pass
                            try:
                                self.bus.force_signal("nextion_ui_cut", enabled, source="NEXTION_SYS")
                            except Exception:
                                pass
                            self._fire_snajper_signal("nextion_ui_cut", enabled, source="NEXTION_SYS", force_physical=True)
                            self.flush_snajper_commands()
                            logs.append(f"{key} TFD SYS UI_CUT: {enabled}")
                            handled_text = True
                            continue
                        # 1. RRP EVENTS
                        if msg.startswith("rrp:"):
                            self._handle_rrp_event(msg)
                            logs.append(f"{key} RRP EVENT: {msg}")
                            handled_text = True
                            continue

                        # 2. TFD METADATA EVENTS (set:title=..., set:director=..., set:ui_cut=...)
                        if self._handle_tfd_meta_event(msg, logs, key):
                            handled_text = True
                            continue

                        # 3. TAKE CLAP / TC steruje _handle_snajper_text_message().

                    if handled_text:
                        continue
                        
                except Exception as e:
                    logs.append(f"{key} DECODE ERROR: {e}")

                if len(raw) >= 2 and raw[0] == 0x66:
                    page_index = int(raw[1])
                    page_id = self._page_id_from_index(key, page_index)
                    self.active_pages[key] = page_id
                    self._refresh_physical_nextion_page_from_state(key, page_id)
                    logs.append(f"{key} PAGE {page_id}")
                    continue

                if len(raw) >= 4 and raw[0] == 0x65:
                    # TOUCH 0x65 zawiera już indeks strony w raw[1].
                    # Nie wolno tu wysyłać sendme, bo na settings_main naciśnięcie SAVE
                    # generuje touch press przed print set:title/set:director. Dodatkowy sendme
                    # wywoływał PAGE settings_main i page refresh nadpisywał tekst wpisany
                    # z fizycznej klawiatury wartością z JSON przed właściwym zapisem.
                    page_index = int(raw[1])
                    component_id = int(raw[2])
                    event_type = int(raw[3])
                    if self._handle_touch_event(key, page_index, component_id, event_type, logs):
                        continue
                    logs.append(f"{key} TOUCH page={page_index} comp={component_id} event={event_type}")

        # Jeżeli PAR ma lekki poll Nextiona, ten sam poll przepycha kolejkę Snajpera.
        # To nie jest refresh_all ani PAR_APP.tick: wysyła tylko pending po konkretnych strzałach.
        self.flush_snajper_commands()
        for line in logs:
            self._append_transport_log(f"EV {line}")
        return logs


    def _handle_snajper_text_message(self, msg: str, logs: List[str] | None = None, screen_key: str = "nextion_7") -> bool:
        """
        Lekki dekoder tekstowych zdarzeń z fizycznego Nextiona.
        Nie tworzy drugiego toru: przycisk b_clap tylko uruchamia istniejące
        bus.set_take_time(...) -> Snajper -> physical_nextion -> queue/flush.
        """
        text = str(msg or "").strip()
        if not text:
            return False

        compact = text.replace(" ", "")
        # Jeżeli zdarzenie przyszło jako odpowiedź stringowa Nextiona (0x70),
        # usuwamy prefiks i dalej obsługujemy ten sam tekst z HMI.
        if compact and compact[0] == "\x70":
            compact = compact[1:]
        lower = compact.lower()
        if logs is None:
            logs = []

        # Dual-state b_clap jest teraz traktowany jako STAN, nie jako ślepy toggle:
        #   take:clap=1 -> START TC
        #   take:clap=0 -> STOP TC
        # Jeśli HMI wyśle samo "take:clap=" bez wartości, używamy fallbacku TOGGLE.
        # Obsługujemy też warianty z bajtem 0x01/0x00, gdy Nextion wyśle wartość numeryczną.
        if lower.startswith("take:clap=") or lower.startswith("clap="):
            value = compact.split("=", 1)[1] if "=" in compact else ""
            value = str(value).strip()
            value_lower = value.lower()
            if value_lower in {"1", "true", "on", "run", "start"} or (value and ord(value[0]) == 1):
                self._set_clap_tc(True, logs, screen_key)
                logs.append(f"{screen_key} TAKE CLAP TEXT {compact!r} -> TC START")
                return True
            if value_lower in {"0", "false", "off", "stop"} or (value and ord(value[0]) == 0):
                self._set_clap_tc(False, logs, screen_key)
                logs.append(f"{screen_key} TAKE CLAP TEXT {compact!r} -> TC STOP")
                return True
            self._toggle_clap_tc(logs, screen_key)
            logs.append(f"{screen_key} TAKE CLAP TEXT {compact!r} -> TC TOGGLE")
            return True

        # Jawne wartości snajperowe zostają wartościami, bo mogą pochodzić z PAR/testów.
        if lower in {
            "b_clap=1",
            "b_clap.val=1",
            "take_main.b_clap=1",
            "take_main.b_clap.val=1",
        }:
            self._set_clap_tc(True, logs, screen_key)
            return True

        if lower in {
            "b_clap=0",
            "b_clap.val=0",
            "take_main.b_clap=0",
            "take_main.b_clap.val=0",
        }:
            self._set_clap_tc(False, logs, screen_key)
            return True

        # Format uniwersalny dla Snajpera: snajper:scope.component.prop=value
        # np. snajper:take_main.b_clap.val=1
        if lower.startswith("snajper:"):
            payload = compact.split(":", 1)[1]
            if "=" not in payload:
                return False
            left, value = payload.split("=", 1)
            parts = left.split(".")
            if len(parts) >= 3:
                scope, component, prop = parts[0], parts[1], parts[2]
                if scope == "take_main" and component == "b_clap" and prop == "val":
                    self._set_clap_tc(str(value).strip() == "1", logs, screen_key)
                    return True
                self.queue_snajper_command(scope, component, prop, value)
                self.flush_snajper_commands()
                return True

        return False

    def _component_name_from_touch(self, screen_key: str, page_index: int, component_id: int) -> str:
        """Zwraca nazwę komponentu z definicji ekranu dla zdarzenia 0x65."""
        try:
            screen = self.screen_defs[screen_key]
            if not (0 <= int(page_index) < len(screen.pages)):
                return ""
            page = screen.pages[int(page_index)]
            for comp in page.get("components", []):
                nxt = comp.get("nextion") or {}
                name = str(nxt.get("component") or comp.get("component") or comp.get("id") or "")
                raw_ids = [
                    nxt.get("id"), nxt.get("component_id"), nxt.get("cmp_id"), nxt.get("cid"),
                    comp.get("nextion_id"), comp.get("component_id"), comp.get("cmp_id"), comp.get("cid"),
                ]
                for raw_id in raw_ids:
                    if raw_id is None:
                        continue
                    try:
                        if int(raw_id) == int(component_id):
                            return name
                    except Exception:
                        continue
        except Exception:
            return ""
        return ""

    def _handle_touch_event(self, screen_key: str, page_index: int, component_id: int, event_type: int, logs: List[str]) -> bool:
        """Obsługuje realny touch Nextiona, gdy HMI nie wysyła tekstu take:clap=1."""
        page_id = self._page_id_from_index(screen_key, int(page_index))
        self.active_pages[screen_key] = page_id
        component = self._component_name_from_touch(screen_key, int(page_index), int(component_id))

        # b_clap w aktualnym HMI wysyła tekst take:clap=... w Touch Press Event.
        # Send Component ID jest włączone tylko pomocniczo, więc touch 0x65 ignorujemy,
        # żeby jeden klik nie wykonał dwóch przełączeń TC.
        if page_id == "take_main" and component == "b_clap":
            logs.append(f"{screen_key} TOUCH b_clap ignored; text take:clap is authoritative")
            return True

        return False


    def _toggle_clap_tc(self, logs: List[str], screen_key: str) -> None:
        """Fallback dla starego touch eventu: przełącza TC."""
        self._set_clap_tc(not self._clap_tc_running, logs, screen_key)

    def _set_clap_tc(self, running: bool, logs: List[str], screen_key: str) -> None:
        """Dual-state b_clap: val=1 START TC, val=0 STOP TC."""
        self.active_pages[screen_key] = "take_main"
        self._clap_tc_last_toggle_monotonic = time.monotonic()

        if running:
            if not self._clap_tc_running:
                # b_clap jest pauzą/wznowieniem czasu, nie resetem.
                # Pierwszy START rusza od aktualnej wartości (zwykle 0),
                # kolejny START po STOP kontynuuje od zatrzymanego TC.
                self._clap_tc_running = True
                self._clap_tc_start_elapsed_ms = int(self._clap_tc_elapsed_ms)
                self._clap_tc_start_monotonic = time.monotonic()
                self._clap_tc_last_sent_ms = -1
                self._publish_clap_tc_state(True, elapsed_ms=self._clap_tc_elapsed_ms, source="NEXTION_CLAP_START")
                self._fire_audio_event("clap_start", logs=logs, screen_key=screen_key)
                logs.append(f"{screen_key} TAKE CLAP TC START {self._clap_tc_elapsed_ms} ms")
            else:
                self._update_clap_tc_for_snajper(force=True)
                self._publish_clap_tc_state(True, elapsed_ms=self._clap_tc_elapsed_ms, source="NEXTION_CLAP_RUN")
                logs.append(f"{screen_key} TAKE CLAP TC RUN")

            self.queue_snajper_command("take_main", "t_clap", "txt", "TC RUN")
        else:
            if self._clap_tc_running:
                self._update_clap_tc_for_snajper(force=True)
                self._clap_tc_running = False
                self._publish_clap_tc_state(False, elapsed_ms=self._clap_tc_elapsed_ms, source="NEXTION_CLAP_STOP")
                self._fire_audio_event("clap_stop", logs=logs, screen_key=screen_key)
                logs.append(f"{screen_key} TAKE CLAP TC STOP {self._clap_tc_elapsed_ms} ms")
            else:
                self._publish_clap_tc_state(False, elapsed_ms=self._clap_tc_elapsed_ms, source="NEXTION_CLAP_STOP")
                logs.append(f"{screen_key} TAKE CLAP TC STOP")

            # Nie zmieniamy take_status/t_status. Pole LIVE zostaje od statusu trybu.
            self.queue_snajper_command("take_main", "t_clap", "txt", "TC STOP")

        self.flush_snajper_commands()

    def _publish_clap_tc_state(self, running: bool, elapsed_ms: int | None = None, source: str = "NEXTION_CLAP") -> None:
        """Publikuje stan b_clap do SignalBus, Snajpera i TFD bez tworzenia nowej pętli."""
        if elapsed_ms is None:
            elapsed_ms = int(self._clap_tc_elapsed_ms)
        else:
            try:
                elapsed_ms = max(0, int(elapsed_ms))
            except Exception:
                elapsed_ms = int(self._clap_tc_elapsed_ms)

        value = 1 if running else 0
        for name in ("take_tc_running", "par_take_tc_running", "take_clap", "par_take_clap"):
            try:
                self.bus.force_signal(name, value, source=source)
            except Exception:
                pass
        tc_text = self._format_tc_from_ms(elapsed_ms)
        for name in ("take_time_ms", "TAKE_TIME_MS"):
            try:
                self.bus.force_signal(name, elapsed_ms, source=source)
            except Exception:
                pass
        for name in ("take_timecode", "par_take_timecode", "take_tc", "tfd_tc"):
            try:
                self.bus.force_signal(name, tc_text, source=source)
            except Exception:
                pass

        if tfd_state:
            try:
                if hasattr(tfd_state, "set_clap_tc_state"):
                    tfd_state.set_clap_tc_state(running, elapsed_ms=elapsed_ms, source=source)
                else:
                    tfd_state.clap = value
                    tfd_state.add_event("CLAP_START" if running else "CLAP_STOP", source, {"elapsed_ms": elapsed_ms})
            except Exception:
                pass

        snajper = getattr(self, "tarzan_snajper", None)
        if snajper is not None:
            try:
                # Nie strzelamy już take_clap jako tekst do t_clap, bo to wpisywało "1/0"
                # w pole pomocnicze. CLAP jest stanem; tekst RUN/STOP ustawia _set_clap_tc.
                snajper.fire("take_timecode", tc_text)
                snajper.fire("take_tc_running", value)
            except Exception:
                pass

    @staticmethod
    def _format_tc_from_ms(ms: int) -> str:
        try:
            ms = max(0, int(ms))
        except Exception:
            ms = 0
        h = ms // 3_600_000
        ms %= 3_600_000
        m = ms // 60_000
        ms %= 60_000
        sec = ms // 1000
        milli = ms % 1000
        return f"{h:02d}:{m:02d}:{sec:02d}:{milli:03d}"

    def _fire_audio_event(self, event_name: str, logs: List[str] | None = None, screen_key: str = "nextion_7") -> None:
        """Jeden tor audio dla fizycznego Nextiona: SignalBus/Snajper + lokalny fallback WAV."""
        if logs is None:
            logs = []

        event_name = str(event_name or "").strip().lower()
        if event_name == "clap_start":
            logical = "take_clap_start"
            audio_key = "signals/clap"
            wav_candidates = ("audio/signals/clap.wav", "audio/signals/cllap.wav", "audio/clap.wav")
        elif event_name == "clap_stop":
            logical = "take_clap_stop"
            audio_key = "voice/motin_coplete"
            wav_candidates = ("audio/voice/motin_coplete.wav", "audio/voice/motion_complete.wav", "audio/voice/Motion_complete.wav")
        else:
            logical = "nextion_audio_event"
            audio_key = event_name
            wav_candidates = ()

        try:
            self.bus.force_signal("nextion_audio_event", logical, source="NEXTION_AUDIO")
            self.bus.force_signal("nextion_audio_key", audio_key, source="NEXTION_AUDIO")
            self.bus.force_signal("nextion_audio_rev", int(time.time() * 1000), source="NEXTION_AUDIO")
        except Exception:
            pass

        snajper = getattr(self, "tarzan_snajper", None)
        if snajper is not None:
            try:
                snajper.fire(logical, audio_key)
                snajper.fire("nextion_audio_event", audio_key)
            except Exception:
                pass

        # Natychmiastowy fallback PC, bo Snajper może nie mieć jeszcze zarejestrowanego audio_adaptera.
        if self._play_audio_key(audio_key, wav_candidates):
            logs.append(f"{screen_key} AUDIO {audio_key}")
        else:
            logs.append(f"{screen_key} AUDIO MISS {audio_key}")

    def _play_audio_key(self, audio_key: str, wav_candidates=()) -> bool:
        """Odtwarza realny WAV. Najpierw bezpośredni plik, potem opcjonalny audio player."""
        try:
            import winsound
            root = Path(__file__).resolve().parents[2]
            for rel in wav_candidates:
                wav_path = root / rel
                if wav_path.exists():
                    winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return True
        except Exception:
            pass

        if play_audio is not None:
            key_variants = [audio_key, audio_key.replace("/", "_"), Path(audio_key).name]
            for key_name in key_variants:
                try:
                    result = play_audio(key_name)
                    # Nie zakładamy wyjątku jako jedynego sygnału błędu, ale jeśli player istnieje,
                    # traktujemy go jako drugi tor dopiero po nieudanym bezpośrednim WAV.
                    return True if result is None else bool(result)
                except Exception:
                    pass
        return False

    def _play_clap_audio(self) -> None:
        """Kompatybilność: stare wywołanie traktujemy jako start CLAP."""
        self._fire_audio_event("clap_start", logs=[], screen_key="nextion_7")

    def _update_clap_tc_for_snajper(self, force: bool = False) -> None:
        """Lekki 10 ms strzał TC przez istniejący Snajper, tylko gdy b_clap uruchomił TC."""
        if not self._clap_tc_running and not force:
            return

        sample_ms = max(1, int(getattr(self.bus, "sample_ms", 10) or 10))
        if self._clap_tc_running:
            raw_delta_ms = int(round((time.monotonic() - self._clap_tc_start_monotonic) * 1000.0))
            raw_ms = int(self._clap_tc_start_elapsed_ms) + max(0, raw_delta_ms)
            elapsed_ms = max(0, (raw_ms // sample_ms) * sample_ms)
            self._clap_tc_elapsed_ms = elapsed_ms
        else:
            elapsed_ms = int(self._clap_tc_elapsed_ms)

        if not force and elapsed_ms == self._clap_tc_last_sent_ms:
            return

        self._clap_tc_last_sent_ms = elapsed_ms
        # Jedno źródło TC: bridge publikuje gotowy take_timecode.
        # Nie wywołujemy bus.set_take_time(), bo w obecnym torze potrafi ono
        # wstrzyknąć techniczne 00:00:00:001 po STOP i cofać overlay/fizyczny t0.
        self._publish_clap_tc_state(self._clap_tc_running, elapsed_ms=elapsed_ms, source="NEXTION_CLAP_TC")


    def _fire_snajper_signal(self, name: str, value: Any, source: str = "NEXTION", force_physical: bool = False) -> None:
        """Aktualizuje BUS i natychmiast odpala istniejącego Snajpera.

        force_physical: jeśli True, wymusza ponowną wysyłkę do physical_nextion
        poprzez wyczyszczenie cache Snajpera dla tego celu.
        """
        try:
            self.bus.force_signal(name, value, source=source)
        except Exception:
            pass
        snajper = getattr(self, "tarzan_snajper", None)
        if snajper is not None:
            try:
                logical = snajper.signal_map.get(name, name) if hasattr(snajper, "signal_map") else name
                if force_physical:
                    # Czyścimy cache Snajpera tylko dla physical_nextion
                    for target in snajper.targets.get(logical, []):
                        if target.adapter == "physical_nextion":
                            cache_key = snajper._cache_key(target)
                            snajper.last_values.pop(cache_key, None)
                
                if hasattr(snajper, "fire"):
                    snajper.fire(logical, value)
                elif hasattr(snajper, "fire_from_signal"):
                    snajper.fire_from_signal(name, value)
            except Exception:
                pass


    def _write_tfd_meta_value(self, key: str, value: Any) -> None:
        """Przekazuje metadane TFD do tfd_state. TFDState odpowiada za zapis JSON."""
        if tfd_state is not None:
            try:
                if key == "title":
                    tfd_state.update_meta(title=str(value))
                elif key == "director":
                    tfd_state.update_meta(director=str(value))
                elif key == "nextion_ui_cut":
                    cut_val = False
                    if str(value).isdigit():
                        cut_val = bool(int(value))
                    else:
                        cut_val = bool(value)
                    self._nextion_ui_cut = bool(cut_val)
                    tfd_state.update_meta(nextion_ui_cut=cut_val)
            except Exception:
                pass

    def _show_tfd_save_status(self) -> None:
        """Pokazuje SAVED na settings_main przez 1 sekundę, bez cache Snajpera.

        t_save_status jest lokalnym komunikatem ekranu settings_main. Nextion sam
        ustawia WAIT w HMI, a PC ma po zapisie zawsze fizycznie nadpisać go na
        SAVED. Dlatego ten mały komunikat idzie bezpośrednio do kolejki Bridge,
        a nie przez normalny cache Snajpera.
        """
        self._tfd_save_status_until = time.time() + 1.0
        self._tfd_save_status_visible = True

        if tfd_state:
            tfd_state.save_status_visible = True
            tfd_state.save_status_text = "SAVED"

        self.queue_snajper_command("settings_main", "t_save_status", "txt", "SAVED")
        self.queue_snajper_command("settings_main", "sound", "play", 1)
        self.queue_snajper_command("settings_main", "t_save_status", "visible", 1)

    def _update_tfd_save_status_for_snajper(self) -> None:
        """Lekko chowa SAVED po 1 sekundzie; bez refresh_all i bez pełnego sync."""
        if not self._tfd_save_status_visible:
            return
        if time.time() < self._tfd_save_status_until:
            return
        self._tfd_save_status_visible = False
        self._tfd_save_status_until = 0.0
        
        if tfd_state:
            tfd_state.save_status_visible = False
            tfd_state.save_status_text = ""

        self.queue_snajper_command("settings_main", "t_save_status", "visible", 0)

    def _refresh_physical_nextion_page_from_state(self, screen_key: str, page_id: str) -> None:
        """Jednorazowy page-start refresh aktywnej strony po sendme / PAGE 0x66.

        Zasada:
        1. Bierze aktualny stan z PAR / SignalBus / TFDState.
        2. Wysyła tylko targety Snajpera 'physical_nextion' należące do aktywnej strony (scope == page_id).
        3. settings_main: t_title/t_director tylko raz (INIT/SKIP), b_ui_cut zawsze.
        4. Na koniec flush.
        """
        if screen_key != "nextion_7":
            return
            
        self.active_pages[screen_key] = page_id
        snajper = getattr(self, "tarzan_snajper", None)
        if snajper is None:
            self._append_transport_log(f"EV {screen_key}: PAGE START REFRESH SKIP {page_id} reason=NO_SNAJPER")
            self.flush_snajper_commands()
            return

        fired = 0

        # Specjalna obsługa settings_main (ekran edycyjny)
        if page_id == "settings_main":
            if not self._settings_main_text_loaded:
                fired += self._force_page_target_from_logical(snajper, page_id, "tfd_title", only_targets={"t_title"})
                fired += self._force_page_target_from_logical(snajper, page_id, "tfd_director", only_targets={"t_director"})
                self._settings_main_text_loaded = True
                self._append_transport_log(f"EV {screen_key}: SETTINGS PAGE TEXT INIT")
            else:
                self._append_transport_log(f"EV {screen_key}: SETTINGS PAGE TEXT SKIP")

            fired += self._force_page_target_from_logical(
                snajper,
                page_id,
                "nextion_ui_cut",
                only_targets={"b_ui_cut"},
                explicit_value=1 if bool(self._nextion_ui_cut) else 0,
            )
        else:
            # Dla wszystkich pozostałych stron (take_main, rrp_main, mode_main, page1, boot, itp.)
            # odtwarzamy wszystkie fizyczne targety strony, dla których aktualna wartość 
            # jest dostępna w TFDState/SignalBus/PAR.
            logicals = []
            for logical, targets in getattr(snajper, "targets", {}).items():
                if any(
                    target.adapter == "physical_nextion" and target.scope == page_id
                    for target in targets
                ):
                    logicals.append(logical)

            for logical in set(logicals):
                fired += self._force_page_target_from_logical(snajper, page_id, logical)

        self._append_transport_log(f"EV {screen_key}: PAGE START REFRESH {page_id} targets={fired}")
        self.flush_snajper_commands()

    def _force_page_target_from_logical(
        self,
        snajper,
        page_id: str,
        logical: str,
        only_targets: set[str] | None = None,
        explicit_value: Any | None = None,
    ) -> int:
        """Wysyła aktualną wartość logicznego sygnału na fizyczne targety aktywnej strony."""
        value = explicit_value if explicit_value is not None else self._read_page_refresh_value(snajper, logical)
        if value is None:
            return 0

        adapter = getattr(snajper, "adapters", {}).get("physical_nextion")
        if adapter is None:
            return 0

        fired = 0
        normalized = snajper.normalize_value(value) if hasattr(snajper, "normalize_value") else str(value)
        
        # Pobieramy listę targetów dla danego sygnału logicznego
        targets_list = getattr(snajper, "targets", {}).get(logical, [])
        for target in targets_list:
            if target.adapter != "physical_nextion":
                continue
            if target.scope != page_id:
                continue
            if only_targets is not None and target.target not in only_targets:
                continue

            # Czyścimy cache Snajpera, aby wymusić wysyłkę nawet jeśli wartość się nie zmieniła w busie
            try:
                # W TARZAN_SNAJPER_V8 cache_key to np. "physical_nextion.take_main.t1.txt"
                cache_key = snajper._cache_key(target)
                snajper.last_values.pop(cache_key, None)
            except Exception:
                cache_key = None

            try:
                adapter.update_target(target, value)
                # Po udanej aktualizacji wpisujemy do cache znormalizowaną wartość
                if cache_key is not None:
                    snajper.last_values[cache_key] = normalized
                fired += 1
            except Exception:
                pass

        return fired

    def _read_page_refresh_value(self, snajper, logical: str) -> Any | None:
        """Odczytuje wartość sygnału z hierarchii: TFDState > SignalBus > Fallback."""
        # 1. TFDState (np. title, director, nextion_ui_cut)
        if tfd_state is not None:
            if logical == "tfd_title":
                return getattr(tfd_state, "title", None)
            if logical == "tfd_director":
                return getattr(tfd_state, "director", None)
            if logical == "nextion_ui_cut":
                return 1 if bool(self._nextion_ui_cut) else 0
            if logical == "take_number":
                return getattr(tfd_state, "take_number", None)
            if logical == "take_status":
                return getattr(tfd_state, "status", None)

        # 2. SignalBus
        if self.bus:
            # 2a. Agregacja dla specyficznych sygnałów logicznych
            if logical == "sensor_xyz":
                # Próbujemy zebrać X, Y, Z z osobnych kanałów busa (MMA7660)
                lx = self.bus.read("sensor_level_x", self.bus.read("par_level_x", 0))
                ly = self.bus.read("sensor_level_y", self.bus.read("par_level_y", 0))
                lz = self.bus.read("sensor_level_z", self.bus.read("par_level_z", 0))
                return f"{lx},{ly},{lz}"
            
            if logical == "nextion_level_xyz_va0_val":
                return self.bus.read("sensor_level_x", self.bus.read("par_level_x", 0))
            if logical == "nextion_level_xyz_va1_val":
                return self.bus.read("sensor_level_y", self.bus.read("par_level_y", 0))
            if logical == "nextion_level_xyz_va2_val":
                return self.bus.read("sensor_level_z", self.bus.read("par_level_z", 0))

            # 2b. Próbujemy po nazwie logicznej bezpośrednio
            val = self.bus.read(logical, default=None)
            if val is not None:
                return val
            
            # 2c. Próbujemy sygnały źródłowe z mapy odwrotnej (wzbogaconej o prefiksy)
            raw_signals = self._reverse_signal_map.get(logical, [])
            for sig in raw_signals:
                val = self.bus.read(sig, default=None)
                if val is not None:
                    return val

            # 2d. Fallbacki dla metadanych TFD/TAKE oraz sensorów
            tfd_fallbacks = {
                "tfd_title": ("par_tfd_title", "tfd_title", "take_title", "movie_title", "title"),
                "tfd_director": ("par_tfd_director", "tfd_director", "take_director", "movie_director", "director"),
                "take_number": ("par_take_number", "take_number", "take_label", "loaded_take_path"),
                "take_status": ("par_take_status", "take_status", "par_mode", "system_status"),
                "level_x": ("sensor_level_x", "par_level_x", "level_x", "axis_x_pos", "par_xyz_x"),
                "level_y": ("sensor_level_y", "par_level_y", "level_y", "axis_y_pos", "par_xyz_y"),
                "level_z": ("sensor_level_z", "par_level_z", "level_z", "axis_z_pos", "par_xyz_z"),
                "sensor_temp": ("par_temp", "sensor_temp", "temp", "par_sensors_temp"),
                "sensor_light": ("par_light", "sensor_light", "light", "par_sensors_light"),
                "sensor_xyz": ("par_xyz", "sensor_xyz", "par_sensors_xyz"),
            }
            if logical in tfd_fallbacks:
                for fallback_key in tfd_fallbacks[logical]:
                    val = self.bus.read(fallback_key, default=None)
                    if val is not None:
                        return val

        return None

    def _handle_tfd_meta_event(self, msg: str, logs: List[str], key: str) -> bool:
        """Przetwarza tekst z settings_main: set:title=... albo set:director=..."""
        if not msg.startswith("set:"):
            return False

        # set:* przychodzi wyłącznie z fizycznego okna settings_main.
        # Ustawiamy aktywny scope zanim Snajper zrobi flush; inaczej poprawny
        # target może zostać w pending, bo bridge myśli, że aktywna jest inna strona.
        self.active_pages[key] = "settings_main"
        
        # TARZAN_SNAJPER_V8: Logika cache i resyncu leży wyłącznie w core/tarzanSnajper.py.
        # Bridge nie czyści już cache'u samowolnie.
        
        payload = msg[4:]
        if payload.startswith("title="):
            val = payload[len("title="):].strip()
            self._write_tfd_meta_value("title", val)
            self._fire_snajper_signal("tfd_title", val, source="NEXTION_PHYSICAL", force_physical=True)
            logs.append(f"{key} TFD SET TITLE: {val}")
            
            # Status SAVED idzie celowo przez istniejącą kolejkę Snajpera na 1 sekundę.
            self._show_tfd_save_status()
            self.flush_snajper_commands()
            return True

        if payload.startswith("director="):
            val = payload[len("director="):].strip()
            self._write_tfd_meta_value("director", val)
            self._fire_snajper_signal("tfd_director", val, source="NEXTION_PHYSICAL", force_physical=True)
            logs.append(f"{key} TFD SET DIRECTOR: {val}")
            
            # Status SAVED idzie celowo przez istniejącą kolejkę Snajpera na 1 sekundę.
            self._show_tfd_save_status()
            self.flush_snajper_commands()
            return True

        if payload.startswith("ui_cut="):
            raw_val = payload[len("ui_cut="):].strip()
            enabled = 1 if raw_val == "1" else 0
            self._nextion_ui_cut = bool(enabled)
            self._write_tfd_meta_value("nextion_ui_cut", enabled)
            self._fire_snajper_signal("nextion_ui_cut", enabled, source="NEXTION_PHYSICAL", force_physical=True)
            logs.append(f"{key} TFD SET UI_CUT: {enabled}")
            self._show_tfd_save_status()
            self.flush_snajper_commands()
            return True

        return False

    def _handle_rrp_event(self, msg: str) -> None:
        """Przetwarza komunikaty tekstowe rrp: z fizycznego ekranu Nextion."""
        if hasattr(self.bus, "log"):
            self.bus.log("NEXTION_RRP", msg)
        # Przyk³ady: "rrp:p1_ax=0", "rrp:p1_dr=1", "rrp:p1_se=50", "rrp:stop=1"
        parts = msg.replace("rrp:", "").split("=")
        if len(parts) != 2:
            return
        
        cmd_key, val = parts[0], parts[1]
        try:
            val_int = int(val)
        except ValueError:
            return

        if cmd_key == "stop" and val_int == 1:
            self.rrp_state["va_p1_axis"] = -1
            self.rrp_state["va_p2_axis"] = -1
        else:
            # Mapowanie nazw z rrp_main.txt na klucze w rrp_state
            # h_p1_sens -> h_p1_sens
            # p1_ax -> va_p1_axis
            # p1_dr -> va_p1_dir
            # p1_se -> h_p1_sens
            
            mapping = {
                "p1_ax": "va_p1_axis",
                "p2_ax": "va_p2_axis",
                "p1_dr": "va_p1_dir",
                "p2_dr": "va_p2_dir",
                "p1_se": "h_p1_sens",
                "p2_se": "h_p2_sens",
            }
            
            target_key = mapping.get(cmd_key, cmd_key)
            self.rrp_state[target_key] = val_int
        
            self.rrp_state["rrp_rev"] += 1
        self._update_bus_from_rrp()

    def _update_bus_from_rrp(self) -> None:
        """Aktualizuje SignalBus po zdarzeniu RRP z Nextiona.

        Indeks osi z Nextiona jest rozpoznawany wyłącznie tutaj. Do dalszych
        warstw trafiają już gotowe kanoniczne nazwy osi i sygnałów.
        """
        active_en_signals = set()

        for player in ("p1", "p2"):
            axis_index = self.rrp_state.get(f"va_{player}_axis", -1)
            direction = self.rrp_state.get(f"va_{player}_dir", 0)
            sensitivity = self.rrp_state.get(f"h_{player}_sens", 50)
            binding = _rrp_axis_binding(player, axis_index)
            pot_signal = RRP_POT_SIGNAL_BY_PLAYER[player]
            active = 1 if binding["selected_axis"] else 0

            if binding["en_signal"]:
                active_en_signals.add(binding["en_signal"])

            canonical_state = {
                "active": active,
                "selected_axis": binding["selected_axis"],
                "pot_signal": pot_signal,
                "step_signal": binding["step_signal"],
                "dir_signal": binding["dir_signal"],
                "en_signal": binding["en_signal"],
                "dir": direction,
                "sens": sensitivity,
            }

            for key, value in canonical_state.items():
                self.bus.force_signal(f"rrp_{player}_{key}", value, source="NEXTION_PHYSICAL")
                self.bus.force_signal(f"par_rrp_{player}_{key}", value, source="NEXTION_PHYSICAL")

            # Kompatybilność dla starego preview: nie jest to już źródło prawdy.
            self.bus.force_signal(f"par_rrp_{player}_axis", binding["selected_axis"], source="NEXTION_PHYSICAL")
            self.bus.force_signal(f"par_rrp_{player}_dir", direction, source="NEXTION_PHYSICAL")
            self.bus.force_signal(f"par_rrp_{player}_sens", sensitivity, source="NEXTION_PHYSICAL")

        rec_auto_active = any(en_sig in RRP_REC_AUTO_EN_SIGNALS for en_sig in active_en_signals)
        self.bus.write_output("ui_rec_auto_enable", 1 if rec_auto_active else 0, source="NEXTION_PHYSICAL")

        for en_sig in RRP_ALL_EN_SIGNALS:
            self.bus.write_output(en_sig, 1 if en_sig in active_en_signals else 0, source="NEXTION_PHYSICAL")

        self.bus.write_output("ui_action_led", 1 if active_en_signals else 0, source="NEXTION_PHYSICAL")

    def preview_rrp_tap(self, screen_key: str, key: str) -> None:
        """Przekazuje tapnięcie w Preview do fizycznego ekranu oraz aktualizuje stan lokalnie."""
        device = self.devices.get(screen_key)
        
        # Mapowanie klucza z Preview na komponent w Nextion
        comp_map = {
            "p1_cam_v": "b_p1_cam_v", "p1_arm_t": "b_p1_arm_t", "p1_cam_f": "b_p1_cam_f",
            "p1_cam_h": "b_p1_cam_h", "p1_arm_h": "b_p1_arm_h", "p1_arm_v": "b_p1_arm_v",
            "p2_cam_v": "b_p2_cam_v", "p2_arm_t": "b_p2_arm_t", "p2_cam_f": "b_p2_cam_f",
            "p2_cam_h": "b_p2_cam_h", "p2_arm_h": "b_p2_arm_h", "p2_arm_v": "b_p2_arm_v",
            "p1_dir": "b_p1_dir", "p2_dir": "b_p2_dir",
            "stop": "b_stop", "home": "b_home"
        }
        
        comp = comp_map.get(key)
        if comp:
            # 1. Jeśli urządzenie jest podłączone, wysyłamy click (fizyczny ekran odpowie rrp:)
            if device and device.connected:
                device.send_command(f"click {comp},1")
            
            # 2. DODANE: Symulujemy zmianę stanu lokalnie dla płynności Preview bez sprzętu
            self._simulate_rrp_click(key)

    def _simulate_rrp_click(self, key: str) -> None:
        """Symuluje logikę przycisków RRP dla trybu bez sprzętu."""
        # Mapowanie kluczy Preview na osie (indeksy 0-5)
        axis_map = {
            "p1_cam_v": (1, 0), "p1_arm_t": (1, 1), "p1_cam_f": (1, 2), "p1_cam_h": (1, 3), "p1_arm_h": (1, 4), "p1_arm_v": (1, 5),
            "p2_cam_v": (2, 0), "p2_arm_t": (2, 1), "p2_cam_f": (2, 2), "p2_cam_h": (2, 3), "p2_arm_h": (2, 4), "p2_arm_v": (2, 5),
        }
        
        if key in axis_map:
            p_idx, ax_idx = axis_map[key]
            current = self.rrp_state.get(f"va_p{p_idx}_axis", -1)
            # Toggle osi
            self.rrp_state[f"va_p{p_idx}_axis"] = ax_idx if current != ax_idx else -1
            self.rrp_state["rrp_rev"] += 1
            self._update_bus_from_rrp()
        
        elif key == "stop":
            self.rrp_state["va_p1_axis"] = -1
            self.rrp_state["va_p2_axis"] = -1
            self.rrp_state["rrp_rev"] += 1
            self._update_bus_from_rrp()
            
        elif key in ("p1_dir", "p2_dir"):
            p_idx = 1 if "p1" in key else 2
            curr_dir = self.rrp_state.get(f"va_p{p_idx}_dir", 0)
            self.rrp_state[f"va_p{p_idx}_dir"] = 1 - curr_dir
            self.rrp_state["rrp_rev"] += 1
            self._update_bus_from_rrp()

    def preview_rrp_set_value(self, screen_key: str, player: str, value: int) -> None:
        """Przekazuje zmianę suwaka w Preview do fizycznego ekranu oraz aktualizuje stan lokalnie."""
        device = self.devices.get(screen_key)
        
        comp = f"h_{player}_sens"
        # 1. Jeśli urządzenie jest podłączone, aktualizujemy i klikamy
        if device and device.connected:
            device.send_command(f"{comp}.val={value}")
            device.send_command(f"click {comp},1")
        
        # 2. DODANE: Aktualizujemy stan lokalny
        self.rrp_state[comp] = value
        self.rrp_state["rrp_rev"] += 1
        self._update_bus_from_rrp()

    def nextion_sync(self, force: bool = False) -> None:
        return self.flush_snajper_commands()
