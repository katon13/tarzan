import time
import json
import os
from pathlib import Path


class TFDState:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parents[2]
        self.meta_path = self.root_dir / "data" / "tfd_metadata.json"

        self.title = "TYTUŁ FILMU"
        self.director = "REŻYSER"
        self.take_number = 1
        self.clap = 0
        self.status = "LIVE"
        self.tc = "00:00:00:000"
        self.t0 = "00:00:00:000"
        self.tc_short = "00:00:00"
        self.packet_id = 0
        self.nextion_ui_cut = False
        self.save_status_visible = False
        self.save_status_text = ""
        self.snajper = None

        self.events = []
        self.last_packet = {}
        self.sent_cache = {}

        self._last_update_time = 0.0
        self._update_interval = 0.01  # 10ms (100Hz)
        self._clap_time = 0.0
        self._tc_running = False
        self._tc_elapsed_ms = 0
        self._last_audio_event = ""

        self.load_metadata()

    def load_metadata(self):
        if self.meta_path.exists():
            try:
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.title = data.get("title", self.title)
                    self.director = data.get("director", self.director)
                    self.nextion_ui_cut = bool(data.get("nextion_ui_cut", self.nextion_ui_cut))
            except Exception:
                pass

    def save_metadata(self):
        try:
            self.meta_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.meta_path, 'w', encoding='utf-8') as f:
                json.dump({"title": self.title, "director": self.director, "nextion_ui_cut": bool(self.nextion_ui_cut)}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_snajper(self, snajper):
        self.snajper = snajper

    def update_meta(self, title=None, director=None, nextion_ui_cut=None):
        changed = False
        if title is not None:
            new_title = str(title).strip()[:100]
            if new_title != self.title:
                self.title = new_title
                changed = True
                if self.snajper:
                    self.snajper.fire("tfd_title", self.title)
        if director is not None:
            new_director = str(director).strip()[:100]
            if new_director != self.director:
                self.director = new_director
                changed = True
                if self.snajper:
                    self.snajper.fire("tfd_director", self.director)
        if nextion_ui_cut is not None:
            new_ui_cut = bool(nextion_ui_cut)
            if new_ui_cut != self.nextion_ui_cut:
                self.nextion_ui_cut = new_ui_cut
                changed = True
                if self.snajper:
                    self.snajper.fire("nextion_ui_cut", self.nextion_ui_cut)
        if changed:
            self.save_metadata()

    def add_event(self, event_type, source, data=None):
        """Dodaje pełne zdarzenie do logu TFD."""
        event = {
            "timestamp": time.time(),
            "time_ms": int(time.time() * 1000),
            "type": event_type,
            "source": source,
            "take": self.take_number,
            "tc": self.tc,
            "event_id": len(self.events),
            "data": data or {}
        }
        self.events.append(event)
        if len(self.events) > 100:
            self.events.pop(0)

        if event_type in {"CLAP", "CLAP_START"}:
            self.set_clap_tc_state(True, data=(data or {}), source=source)
        elif event_type in {"CLAP_STOP", "TC_STOP"}:
            self.set_clap_tc_state(False, data=(data or {}), source=source)
        return event

    def set_clap_tc_state(self, running, elapsed_ms=None, source="NEXTION", data=None):
        """Stan dual-state b_clap: 1 uruchamia TC, 0 zatrzymuje TC."""
        if isinstance(data, dict) and elapsed_ms is None:
            elapsed_ms = data.get("elapsed_ms")

        self._tc_running = bool(running)
        self.clap = 1 if self._tc_running else 0
        self._clap_time = time.time()

        if elapsed_ms is not None:
            try:
                self._tc_elapsed_ms = max(0, int(float(elapsed_ms)))
            except Exception:
                pass

        # Overlay TFD nie może zależeć od ciągłych pakietów z bridge.
        # START/STOP ustawia bazę czasu, a TFDState może sam policzyć bieżący TC.
        if self._tc_running:
            self._tc_start_elapsed_ms = int(self._tc_elapsed_ms)
            self._tc_start_monotonic = time.monotonic()
        else:
            self._tc_elapsed_ms = self._current_tc_elapsed_ms()
            self._tc_start_elapsed_ms = int(self._tc_elapsed_ms)
            self._tc_start_monotonic = time.monotonic()

        self._last_bus_running = self._tc_running

        tc_data = self.format_tfd_tc(self._current_tc_elapsed_ms(), numeric_is_elapsed_ms=True)
        self.tc = tc_data["full"]
        self.t0 = tc_data["full"]
        self.tc_short = tc_data["short"]

        # Jeżeli serwer TFD działa w tym samym procesie, aktualizujemy ostatni pakiet od razu.
        # Dzięki temu SSE dostaje START/STOP natychmiast, a overlay może liczyć TC lokalnie
        # między pakietami bez specjalnej synchronizacji co 10 ms.
        if self.last_packet:
            self.packet_id += 1
            self.last_packet.update({
                "packet_id": self.packet_id,
                "timestamp": time.time(),
                "tc": self.tc,
                "t0": self.t0,
                "tc_short": self.tc_short,
                "tc_running": 1 if self._tc_running else 0,
                "clap": self.clap,
            })

        # TFD jest kopią podglądową. Nie wysyła take_timecode z powrotem do Snajpera,
        # bo wtedy overlay/server może nadpisać fizyczny Nextion technicznym 00:00:00:001.
        return self.t0

    def _current_tc_elapsed_ms(self):
        """Zwraca bieżący TC w ms liczony lokalnie między START i STOP."""
        if self._tc_running:
            delta = int(max(0.0, time.monotonic() - float(self._tc_start_monotonic or time.monotonic())) * 1000.0)
            return max(0, int(self._tc_start_elapsed_ms) + delta)
        return max(0, int(self._tc_elapsed_ms))

    @staticmethod
    def _format_ms(ms):
        try:
            ms = max(0, int(float(ms)))
        except Exception:
            ms = 0
        h = ms // 3_600_000
        ms %= 3_600_000
        m = ms // 60_000
        ms %= 60_000
        sec = ms // 1000
        milli = ms % 1000
        return f"{h:02d}:{m:02d}:{sec:02d}:{milli:03d}"

    def format_tfd_axis_value(self, pulses, dir_val=None):
        """Tekst licznika bez +/-; kierunek idzie osobno jako kolor."""
        try:
            val = abs(int(float(pulses)))
        except Exception:
            val = 0
        return str(val).zfill(5)

    def format_tfd_xyz(self, x, y, z):
        """Format: +00 +00 +00 (zaokrąglone do liczb całkowitych)."""
        try:
            ix, iy, iz = int(round(float(x))), int(round(float(y))), int(round(float(z)))
        except Exception:
            ix, iy, iz = 0, 0, 0
        return f"{ix:+03d} {iy:+03d} {iz:+03d}"

    def format_tfd_tc(self, bus_tc=None, *, numeric_is_elapsed_ms=False):
        """TC pochodzi z TAKE/CLAP.

        Tekst TC ma format HH:MM:SS:MS. Surowe 0/1 z b_clap nie jest TC.
        Liczbę traktujemy jako elapsed_ms tylko wtedy, gdy wywołanie jawnie to zaznaczy
        albo gdy wartość jest typem liczbowym przekazanym z lokalnego licznika TFD.
        """
        val = None
        if bus_tc is not None:
            if isinstance(bus_tc, (int, float)) and not isinstance(bus_tc, bool):
                val = self._format_ms(bus_tc)
            else:
                text = str(bus_tc).strip()
                if text and ":" in text:
                    parts = text.split(":")
                    if len(parts) == 4 and len(parts[3]) == 2:
                        val = f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}0"
                    else:
                        val = text
                elif numeric_is_elapsed_ms and text not in {"", "0", "1"}:
                    try:
                        val = self._format_ms(int(float(text)))
                    except Exception:
                        val = None

        if val is None:
            val = self._format_ms(self._current_tc_elapsed_ms() if self._tc_running else self._tc_elapsed_ms)
        return {"full": val, "short": val[:10]}

    def format_tfd_take_number(self, take_num):
        """Format: 001, 002... lub 001-12 jeśli wersja podana"""
        s_num = str(take_num)
        if "-" in s_num:
            parts = s_num.split("-")
            try:
                return f"{str(int(float(parts[0]))).zfill(3)}-{parts[1]}"
            except Exception:
                return s_num

        try:
            return str(int(float(take_num))).zfill(3)
        except Exception:
            import re
            match = re.search(r'(\d+)', s_num)
            if match:
                return str(int(match.group(1))).zfill(3)
            return "001"

    def format_tfd_sensor_value(self, sensor_type, value):
        """Formaty dla czujników: 0/1/OK/LIMIT."""
        b_val = bool(value)
        if isinstance(value, str):
            if value.lower() in ("0", "false", "off", "ok", "none", ""):
                b_val = False
            else:
                b_val = True

        if sensor_type == "shock":
            return "1" if b_val else "0"
        if sensor_type == "laser":
            return "1" if b_val else "0"
        if sensor_type == "limits":
            return value if (isinstance(value, str) and value != "0") else ("OK" if not b_val else "LIMIT")
        return "OK" if not b_val else "ERR"

    @staticmethod
    def _bus_get(bus, key, default=None):
        try:
            return bus.get(key, default)
        except TypeError:
            try:
                value = bus.get(key)
                return default if value is None else value
            except Exception:
                return default
        except Exception:
            try:
                return bus.read(key, default=default)
            except Exception:
                return default

    @staticmethod
    def _bool_like(value):
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on", "run", "start"}
        return bool(value)

    def update_from_bus(self, bus):
        """Aktualizuje stan TFD na podstawie danych systemowych."""
        now = time.time()

        # Stary impuls CLAP może się wygasić, ale tylko gdy dual-state TC nie pracuje.
        if self.clap and not self._tc_running and (now - self._clap_time) > 0.8:
            self.clap = 0
            if self.snajper:
                self.snajper.fire("take_clap", 0)

        if (now - self._last_update_time) < self._update_interval and self.last_packet:
            return self.last_packet

        self._last_update_time = now

        mode = "LIVE"
        if hasattr(bus, "mode"):
            mode = str(bus.mode).upper()
        par_mode = self._bus_get(bus, "par_mode")
        if par_mode == 0:
            mode = "TEST"
        elif par_mode == 1:
            mode = "LIVE"
        elif par_mode == 2:
            mode = "MIX"

        old_status = self.status
        self.status = "MIZ" if mode == "MIX" else mode
        if self.snajper and self.status != old_status:
            self.snajper.fire("take_status", self.status)

        running_from_bus = self._bus_get(bus, "take_tc_running", None)
        if running_from_bus is not None:
            new_running = self._bool_like(running_from_bus)
            if new_running != self._tc_running:
                # Zmiana 0->1 lub 1->0 z busa jest jedynym sygnałem sterującym dla TFD.
                # Po START overlay/TFD liczy czas lokalnie; po STOP zostaje ostatnia wartość.
                if new_running:
                    self._tc_start_elapsed_ms = int(self._tc_elapsed_ms)
                    self._tc_start_monotonic = time.monotonic()
                else:
                    self._tc_elapsed_ms = self._current_tc_elapsed_ms()
                    self._tc_start_elapsed_ms = int(self._tc_elapsed_ms)
                    self._tc_start_monotonic = time.monotonic()
            self._tc_running = new_running
            self._last_bus_running = new_running
            self.clap = 1 if self._tc_running else 0

        elapsed_ms = self._bus_get(bus, "take_time_ms", None)
        if elapsed_ms is None:
            elapsed_ms = self._bus_get(bus, "TAKE_TIME_MS", None)
        bus_tc = self._bus_get(bus, "take_timecode", None)
        if bus_tc is None:
            bus_tc = self._bus_get(bus, "par_take_timecode", None)
        if bus_tc is None:
            bus_tc = self._bus_get(bus, "take_tc", None)

        if elapsed_ms is not None:
            try:
                bus_elapsed = max(0, int(float(elapsed_ms)))
            except Exception:
                bus_elapsed = None
            if bus_elapsed is not None:
                if self._tc_running:
                    # Bridge/Nextion może wysyłać rzadziej; TFD nie utyka na ostatnim pakiecie.
                    current_local = self._current_tc_elapsed_ms()
                    if abs(current_local - bus_elapsed) > 500:
                        self._tc_elapsed_ms = bus_elapsed
                        self._tc_start_elapsed_ms = bus_elapsed
                        self._tc_start_monotonic = time.monotonic()
                    else:
                        self._tc_elapsed_ms = current_local
                else:
                    self._tc_elapsed_ms = bus_elapsed

        if self._tc_running:
            tc_data = self.format_tfd_tc(self._current_tc_elapsed_ms(), numeric_is_elapsed_ms=True)
        elif elapsed_ms is not None:
            tc_data = self.format_tfd_tc(self._tc_elapsed_ms, numeric_is_elapsed_ms=True)
        else:
            tc_data = self.format_tfd_tc(bus_tc)

        old_tc = self.tc
        self.tc = tc_data["full"]
        self.t0 = tc_data["full"]
        self.tc_short = tc_data["short"]
        # TFD nie jest źródłem TC dla fizycznego Nextiona.
        # TC do Nextiona publikuje bridge; TFD tylko pokazuje kopię w overlay.

        old_take = self.take_number
        take_path = getattr(bus, "loaded_take_path", None)
        if take_path:
            import re
            filename = os.path.basename(take_path)
            match = re.search(r'(?:TAKE_)?(\d+)(?:[-_vV]+(\d+))?', filename, re.IGNORECASE)
            if match:
                num = match.group(1).zfill(3)
                ver = match.group(2)
                self.take_number = f"{num} {ver}" if ver else num
            else:
                self.take_number = "001"
        else:
            raw_take = self._bus_get(bus, "take_num") or self._bus_get(bus, "par_take_num", 1)
            self.take_number = self.format_tfd_take_number(raw_take)

        if self.snajper and self.take_number != old_take:
            self.snajper.fire("take_number", self.take_number)

        axes = {}
        axis_names = ["CAM_V", "ARM_T", "CAM_F", "CAM_H", "ARM_H", "ARM_V"]
        for i, name in enumerate(axis_names):
            key = f"axis{i}"
            axis_id = name.lower()
            dir_val = 1 if self._bus_get(bus, f"axis_{axis_id}_dir") else 0
            pulses = self._bus_get(bus, f"axis_{axis_id}_pulses", 0)
            moving = bool(self._bus_get(bus, f"axis_{axis_id}_moving", False))
            formatted_pos = self.format_tfd_axis_value(pulses, dir_val)
            axes[key] = {
                "name": name,
                "pos": formatted_pos,
                "dir": dir_val,
                "dir_class": "dir-positive" if dir_val else "dir-negative",
                "dir_color": "green" if dir_val else "red",
                "pulses": pulses,
                "moving": moving
            }

        laser_active = bool(self._bus_get(bus, "sensor_laser_set", 0))
        laser_error = bool(self._bus_get(bus, "sensor_laser_error", 0))
        laser_state = "ERR" if laser_error else self.format_tfd_sensor_value("laser", laser_active)

        raw_limits = self._bus_get(bus, "sensor_limits_status", "0")
        limits_state = self.format_tfd_sensor_value("limits", raw_limits)
        shock_val = self._bus_get(bus, "sensor_shock_state", 0)
        shock = self.format_tfd_sensor_value("shock", shock_val)

        light_val = self._bus_get(bus, "sensor_light_lux", 0)
        try:
            light = f'{str(int(light_val)).zfill(5)} '
        except Exception:
            light = "00000"

        temp_val = self._bus_get(bus, "sensor_temp_c", 22.0)
        try:
            fv = float(temp_val)
            temp = f"{int(fv)}" if abs(fv) >= 100 else f"{fv:.1f}"
        except Exception:
            temp = str(temp_val)

        lx = self._bus_get(bus, 'sensor_level_x', 0)
        ly = self._bus_get(bus, 'sensor_level_y', 0)
        lz = self._bus_get(bus, 'sensor_level_z', 0)
        xyz_formatted = self.format_tfd_xyz(lx, ly, lz)

        packet = {
            "system": "TARZAN_FRAME_DATA",
            "short": "TFD",
            "packet_id": self.packet_id,
            "timestamp": time.time(),
            "take": self.format_tfd_take_number(self.take_number),
            "tc": self.tc,
            "tc_short": self.tc_short,
            "t0": self.t0,
            "tc_running": 1 if self._tc_running else 0,
            "title": self.title,
            "director": self.director,
            "clap": self.clap,
            "status": self.status,
            "axes": axes,
            "sensors": {
                "laser": laser_state, "limits": limits_state,
                "shock": shock, "light": light,
                "temp": temp, "xyz": xyz_formatted,
                "status": "OK"
            },
            "last_audio_event": self._last_audio_event,
            "last_event": self.events[-1] if self.events else None
        }

        self.last_packet = packet
        self.packet_id += 1

        if self.snajper:
            for i in range(6):
                ax = axes.get(f"axis{i}", {})
                self.snajper.fire(f"tfd_axis_{i}_active", ax.get("moving", False))
            self.snajper.fire("tfd_laser_active", laser_active)
            self.snajper.fire("tfd_laser_error", laser_error)
            self.snajper.fire("tfd_limits_active", raw_limits != "0")
            self.snajper.fire("tfd_shock_active", bool(shock_val))

        return packet

    def get_packet(self):
        return self.last_packet

    def should_update(self, recipient_id, data_to_send):
        last_sent = self.sent_cache.get(recipient_id)
        if data_to_send != last_sent:
            self.sent_cache[recipient_id] = data_to_send
            return True
        return False

    def to_dict(self):
        """Zwraca słownik z danymi. Jeśli last_packet nie istnieje, tworzy pakiet startowy."""
        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        if bus:
            self.update_from_bus(bus)

        if not self.last_packet:
            return {
                "packet_id": self.packet_id,
                "title": self.title,
                "director": self.director,
                "take": self.format_tfd_take_number(self.take_number),
                "clap": self.clap,
                "tc_running": 1 if self._tc_running else 0,
                "status": self.status,
                "tc": self.tc,
                "t0": self.t0,
                "axes": {},
                "sensors": {
                    "laser": "OFF", "limits": "OK", "shock": "OK",
                    "light": "00000", "temp": "22.0", "xyz": "+00 +00 +00"
                }
            }
        return self.last_packet


import sys
# Singleton gwarantujący jedną instancję w całym procesie (unikamy duplikacji przy różnych importach)
tfd_state = None
for _mod in list(sys.modules.values()):
    if hasattr(_mod, "tfd_state") and isinstance(getattr(_mod, "tfd_state"), TFDState):
        tfd_state = getattr(_mod, "tfd_state")
        break
if tfd_state is None:
    tfd_state = TFDState()
