from __future__ import annotations

import time
from typing import Any, Dict, List

from .config import load_ports
from .device import TarzanNextionDevice
from .protocol import cmd_page, cmd_text, cmd_value, cmd_visible, command_bytes
from .screen_model import ScreenDefinition, load_screen_definition
from .state_mapper import TarzanNextionStateMapper

try:
    from editor.TFD.tfd_state import tfd_state
except ImportError:
    tfd_state = None

try:
    from audio.tarzanAudioPlayer import play as play_audio
except ImportError:
    play_audio = lambda msg: None


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
        self._snapshot_cache = {}
        self._snapshot_time = 0.0
        
        # Stan RRP (Physical Source of Truth)
        self.rrp_state = {
            "va_p1_axis": -1, "va_p1_dir": 0, "va_p1_val": 0, "h_p1_sens": 0,
            "va_p2_axis": -1, "va_p2_dir": 0, "va_p2_val": 0, "h_p2_sens": 0,
            "rrp_rev": 0
        }

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

    def _request_current_page(self, device: TarzanNextionDevice) -> None:
        if device.connected:
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
        if ok:
            page_id = self.active_pages.get(screen_key, "")
            if page_id:
                device.send_raw(cmd_page(page_id))
            self._request_current_page(device)
        return ok

    def disconnect_screen(self, screen_key: str) -> None:
        device = self.devices.get(screen_key)
        if device is not None:
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
            
            # Dodajemy stan RRP do sekcji ekranu (wymagane przez PAR)
            if key == "nextion_7":
                base[f"{key}.rrp_rev"] = self.rrp_state.get("rrp_rev", 0)
                for k, v in self.rrp_state.items():
                    base[f"{key}.rrp.{k}"] = v
                # DODANE: Uwzględniamy gęstość STEP w snapshotcie, aby sync() wykrywał zmiany
                base[f"{key}.rrp.p1_val"] = self.bus.get("par_rrp_p1_val", "0")
                base[f"{key}.rrp.p2_val"] = self.bus.get("par_rrp_p2_val", "0")
        
        # Kompatybilnoæ wsteczna
        for k, v in self.rrp_state.items():
            base[f"rrp.{k}"] = v
            
        self._snapshot_cache = base
        self._snapshot_time = now
        return base

    def set_page(self, screen_key: str, page_id: str) -> None:
        self.active_pages[screen_key] = page_id
        device = self.devices.get(screen_key)
        if device is not None and device.connected:
            device.send_raw(cmd_page(page_id))
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

    def _rrp_main_commands(self, screen_key: str, state: Dict[str, Any]) -> List[bytes]:
        if screen_key != "nextion_7":
            return []
        if self.active_pages.get(screen_key) != "rrp_main":
            return []
        
        cmds = []
        # Pobieramy wartosc obliczona przez generator w PAR
        p1_val = self.bus.get("par_rrp_p1_val", "0")
        p2_val = self.bus.get("par_rrp_p2_val", "0")
        
        # Wysylamy do pol tekstowych na fizycznym ekranie
        cmds.append(cmd_text("t_p1_val", str(p1_val)))
        cmds.append(cmd_text("t_p2_val", str(p2_val)))
        
        return cmds

    def sync(self, force: bool = False) -> None:
        snapshot = self.snapshot()
        now = time.time()
        
        # AKTUALIZACJA TFD (Telemetria)
        if tfd_state:
            # TFD pobiera dane z SignalBus
            tfd_state.update_from_bus(self.bus)

        interval = max(0.05, float(self.ports_cfg.get("sync_interval_ms", 50)) / 1000.0)
        if not force and snapshot == self.last_sent_snapshot and (now - self.last_sync) < interval:
            # Nawet jeśli snapshot busa się nie zmienił, metadane TFD mogły się zmienić (np. title)
            # ale obsłużymy to w pętli urządzeń poniżej jeśli potrzeba.
            return
            
        self.last_sync = now
        self.last_commands = []
        for key, device in self.devices.items():
            if not self._enabled(key) or not device.connected:
                continue
            commands = self.build_commands(key, snapshot)
            commands.extend(self._level_xyz_commands(key, snapshot))
            commands.extend(self._rrp_main_commands(key, snapshot))
            
            # DODANE: Wysyłka danych TFD do Nextiona (take_main lub settings_main)
            if key == "nextion_7":
                curr_page = self.active_pages.get(key)
                if curr_page == "take_main":
                    commands.extend(self._tfd_take_main_commands())
                elif curr_page == "settings_main":
                    commands.extend(self._tfd_settings_main_commands())

            for payload in commands:
                self.last_commands.append(f"{key}: {payload!r}")
                device.send_raw(payload)
        self.last_sent_snapshot = dict(snapshot)

    def _tfd_take_main_commands(self) -> List[bytes]:
        """
        Generuje komendy aktualizujące pola TFD na ekranie Nextion take_main.
        Wykorzystuje sent_cache w tfd_state do optymalizacji (wysyłka tylko zmian).
        """
        if not tfd_state:
            return []
            
        packet = tfd_state.get_packet()
        if not packet:
            return []
            
        cmds = []
        
        # 1. Metadane (Tytuł, Reżyser, Take, TC, Status, Clap)
        meta_data = {
            "t1": packet.get("title", ""),
            "t2": packet.get("director", ""),
            "t_take": f"TAKE: {packet.get('take', 1)}",
            "t_clap": "CLAP" if packet.get("clap") else "",
            "t_status": packet.get("status", "LIVE"),
            "t0": packet.get("t0", "00:00:0000"),
            "t_tc": packet.get("tc", "00:00:00:00")
        }
        
        for comp, val in meta_data.items():
            if tfd_state.should_update(f"nextion_7.{comp}", val):
                cmds.append(cmd_text(comp, val))
                
        # 2. Osie (t_axis0..5)
        axes = packet.get("axes", {})
        for i in range(6):
            comp = f"t_axis{i}"
            val = axes.get(f"axis{i}", "00000")
            if tfd_state.should_update(f"nextion_7.{comp}", val):
                cmds.append(cmd_text(comp, val))
                
        # 3. Czujniki
        sensors = packet.get("sensors", {})
        sensor_map = {
            "t_laser": sensors.get("laser"),
            "t_limits": sensors.get("limits"),
            "t_shock": sensors.get("shock"),
            "t_light": sensors.get("light"),
            "t_temp": sensors.get("temp"),
            "t_xyz": sensors.get("xyz")
        }
        
        for comp, val in sensor_map.items():
            if val is not None:
                if tfd_state.should_update(f"nextion_7.{comp}", val):
                    cmds.append(cmd_text(comp, val))
                    
        return cmds

    def _tfd_settings_main_commands(self) -> List[bytes]:
        """
        Aktualizuje pola tekstowe na stronie ustawień fizycznego Nextiona.
        """
        if not tfd_state:
            return []
            
        cmds = []
        # t_title i t_director na stronie settings_main
        if tfd_state.should_update("nextion_7.settings.title", tfd_state.title):
            cmds.append(cmd_text("t_title", tfd_state.title))
        if tfd_state.should_update("nextion_7.settings.director", tfd_state.director):
            cmds.append(cmd_text("t_director", tfd_state.director))
            
        return cmds

    def poll(self) -> List[str]:
        logs: List[str] = []
        for key, device in self.devices.items():
            for event in device.poll():
                raw = event.raw
                logs.append(f"{key} EVENT {raw!r}")

                # Obs³uga zdarzeñ tekstowych (np. rrp:, set:, take:)
                try:
                    msg = raw.decode("ascii", errors="replace")
                    
                    # 1. RRP EVENTS
                    if msg.startswith("rrp:"):
                        self._handle_rrp_event(msg)
                        logs.append(f"{key} RRP EVENT: {msg}")
                        continue
                        
                    # 2. TFD METADATA EVENTS (set:title=..., set:director=...)
                    if msg.startswith("set:") and tfd_state:
                        parts = msg.replace("set:", "").split("=", 1)
                        if len(parts) == 2:
                            k, v = parts[0], parts[1]
                            if k == "title": tfd_state.update_meta(title=v)
                            if k == "director": tfd_state.update_meta(director=v)
                            logs.append(f"{key} TFD SET: {k}={v}")
                        continue
                        
                    # 3. TFD CLAP EVENT (take:clap=1)
                    if msg.startswith("take:clap=1") and tfd_state:
                        tfd_state.set_clap(1)
                        play_audio("clap")
                        logs.append(f"{key} TFD CLAP!")
                        continue
                        
                except Exception as e:
                    logs.append(f"{key} DECODE ERROR: {e}")

                if len(raw) >= 2 and raw[0] == 0x66:
                    page_id = self._page_id_from_index(key, int(raw[1]))
                    self.active_pages[key] = page_id
                    logs.append(f"{key} PAGE {page_id}")
                    continue

                if len(raw) >= 4 and raw[0] == 0x65:
                    self._request_current_page(device)
                    logs.append(f"{key} TOUCH page={int(raw[1])} comp={int(raw[2])} event={int(raw[3])}")
        return logs

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
        """Aktualizuje magistrale sygnalowa na podstawie fizycznego stanu RRP."""
        for player in ("p1", "p2"):
            axis = self.rrp_state.get(f"va_{player}_axis", -1)
            direction = self.rrp_state.get(f"va_{player}_dir", 0)
            sensitivity = self.rrp_state.get(f"h_{player}_sens", 50)
            
            # Przekazujemy parametry sterowania do magistrali
            self.bus.set_input(f"par_rrp_{player}_axis", axis, source="NEXTION_PHYSICAL")
            self.bus.set_input(f"par_rrp_{player}_dir", direction, source="NEXTION_PHYSICAL")
            self.bus.set_input(f"par_rrp_{player}_sens", sensitivity, source="NEXTION_PHYSICAL")
            
            # Nie nadpisujemy juz sygnalow p45/p47 - one sa zarezerwowane dla fizycznych potencjometrow
            # ktore w PAR sa reprezentowane przez galki (knobs)

        # 2. Sterowanie sygnalami ENABLE osi ramienia
        active_axes = {self.rrp_state["va_p1_axis"], self.rrp_state["va_p2_axis"]}
        
        self.bus.set_input("play_p50_step_en_arm_h", 1 if 4 in active_axes else 0, source="NEXTION_PHYSICAL")
        self.bus.set_input("play_p51_step_en_arm_v", 1 if 5 in active_axes else 0, source="NEXTION_PHYSICAL")
        self.bus.set_input("play_p52_step_en_arm_tilt", 1 if 1 in active_axes else 0, source="NEXTION_PHYSICAL")

        # 3. Glowna lampa akcji
        any_active = any(ax != -1 for ax in active_axes)
        self.bus.set_input("play_p16_action_led", 1 if any_active else 0, source="NEXTION_PHYSICAL")

    def preview_rrp_tap(self, screen_key: str, key: str) -> None:
        """Przekazuje tapniêcie w Preview do fizycznego ekranu."""
        device = self.devices.get(screen_key)
        if not device or not device.connected:
            return
        
        # Mapowanie klucza z Preview na komponent w Nextion
        comp_map = {
            "p1_cam_v": "b_p1_cam_v", "p1_cam_t": "b_p1_cam_t", "p1_cam_f": "b_p1_cam_f",
            "p1_cam_h": "b_p1_cam_h", "p1_arm_h": "b_p1_arm_h", "p1_arm_v": "b_p1_arm_v",
            "p2_cam_v": "b_p2_cam_v", "p2_cam_t": "b_p2_cam_t", "p2_cam_f": "b_p2_cam_f",
            "p2_cam_h": "b_p2_cam_h", "p2_arm_h": "b_p2_arm_h", "p2_arm_v": "b_p2_arm_v",
            "p1_dir": "b_p1_dir", "p2_dir": "b_p2_dir",
            "stop": "b_stop", "home": "b_home"
        }
        
        comp = comp_map.get(key)
        if comp:
            # Wysy³amy click do fizycznego ekranu, co wywo³a Touch Release Event na Nextionie
            # i w efekcie fizyczny ekran wyle do nas rrp:komunikat.
            device.send_command(f"click {comp},1")

    def preview_rrp_set_value(self, screen_key: str, player: str, value: int) -> None:
        """Przekazuje zmianê suwaka w Preview do fizycznego ekranu."""
        device = self.devices.get(screen_key)
        if not device or not device.connected:
            return
        
        comp = f"h_{player}_sens"
        # Ustawiamy wartoæ na fizycznym ekranie i symulujemy puszczenie suwaka
        device.send_command(f"{comp}.val={value}")
        device.send_command(f"click {comp},1")
