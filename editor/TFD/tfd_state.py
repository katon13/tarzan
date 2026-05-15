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
        self.tc = "00:00:00:00"
        self.t0 = time.strftime("%d.%m.%Y")
        self.packet_id = 0
        
        self.events = []
        self.last_packet = {}
        self.sent_cache = {}
        
        self._last_update_time = 0.0
        self._update_interval = 0.04  # 40ms
        self._clap_time = 0
        
        self.load_metadata()

    def load_metadata(self):
        if self.meta_path.exists():
            try:
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.title = data.get("title", self.title)
                    self.director = data.get("director", self.director)
            except:
                pass

    def save_metadata(self):
        try:
            self.meta_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.meta_path, 'w', encoding='utf-8') as f:
                json.dump({"title": self.title, "director": self.director}, f, ensure_ascii=False, indent=2)
        except:
            pass

    def update_meta(self, title=None, director=None):
        changed = False
        if title is not None: 
            new_title = str(title).strip()[:100]
            if new_title != self.title:
                self.title = new_title
                changed = True
        if director is not None: 
            new_director = str(director).strip()[:100]
            if new_director != self.director:
                self.director = new_director
                changed = True
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
        # Zachowujemy tylko ostatnie 100 zdarzeń w pamięci
        if len(self.events) > 100:
            self.events.pop(0)
            
        if event_type == "CLAP":
            self.clap = 1
            self._clap_time = time.time()
        return event

    def format_tfd_axis_value(self, pulses, dir_val):
        """Format: +00000 / -00000 na podstawie licznika impulsów i kierunku DIR."""
        try:
            val = abs(int(float(pulses)))
            sign = "+" if dir_val else "-"
        except:
            val = 0
            sign = "+" if dir_val else "-"
        return f"{sign}{str(val).zfill(5)}"

    def format_tfd_xyz(self, x, y, z):
        """Format: +00 +00 +00 (zaokrąglone do liczb całkowitych)."""
        try:
            ix, iy, iz = int(round(float(x))), int(round(float(y))), int(round(float(z)))
        except:
            ix, iy, iz = 0, 0, 0
        return f"{ix:+03d} {iy:+03d} {iz:+03d}"

    def format_tfd_tc(self, bus_tc=None):
        """Format: HH:MM:SS:mmmm (pełny) i wersja skrócona dla Nextiona (10 znaków)."""
        if bus_tc and ":" in str(bus_tc) and str(bus_tc) != "00:00:00:00":
            val = str(bus_tc)
            # Upewnij się, że ostatni człon ma 4 cyfry, jeśli to HH:MM:SS:FF
            parts = val.split(":")
            if len(parts) == 4 and len(parts[3]) == 2:
                val = f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}0"
        else:
            # Fallback do czasu systemowego
            t = time.time()
            milli = int((t - int(t)) * 1000)
            # Format 00:00:00:000 (wymagane 3 cyfry na końcu)
            val = time.strftime("%H:%M:%S", time.localtime(t)) + f":{milli:03d}"
        
        # Zwracamy słownik z obiema wersjami, aby bridge mógł wybrać
        return {
            "full": val,
            "short": val[:10] # Ucinamy do 10 znaków dla Nextiona (limit pola t0)
        }

    def format_tfd_take_number(self, take_num):
        """Format: 001, 002... lub 001-12 jeśli wersja podana"""
        s_num = str(take_num)
        if "-" in s_num:
            parts = s_num.split("-")
            try:
                return f"{str(int(float(parts[0]))).zfill(3)}-{parts[1]}"
            except:
                return s_num
        
        try:
            return str(int(float(take_num))).zfill(3)
        except:
            import re
            match = re.search(r'(\d+)', s_num)
            if match:
                return str(int(match.group(1))).zfill(3)
            return "001"

    def format_tfd_sensor_value(self, sensor_type, value):
        """Formaty dla czujników: OK/SHOCK, OFF/ON itp."""
        if sensor_type == "shock":
            return "SHOCK" if value else "OK"
        if sensor_type == "laser":
            return "ON" if value else "OFF"
        return "OK" if not value else "ERR"

    def update_from_bus(self, bus):
        """Aktualizuje stan TFD na podstawie danych systemowych."""
        now = time.time()
        
        # Auto-reset klapsa po 800ms
        if self.clap and (now - self._clap_time) > 0.8:
            self.clap = 0
            
        if (now - self._last_update_time) < self._update_interval and self.last_packet:
            return self.last_packet
            
        self._last_update_time = now
        
        # Status PAR: TEST / LIVE / MIX
        # SignalBus mode
        mode = "LIVE"
        if hasattr(bus, "mode"):
            mode = str(bus.mode).upper()
        
        # Fallback na par_mode jeśli istnieje w bus.get
        par_mode = bus.get("par_mode")
        if par_mode == 0: mode = "TEST"
        elif par_mode == 1: mode = "LIVE"
        elif par_mode == 2: mode = "MIX"
        
        self.status = "MIZ" if mode == "MIX" else mode # Użytkownik preferuje MIZ
        
        # TC i Czas bieżący
        self.tc = str(bus.get("take_tc", "00:00:00:00"))
        tc_data = self.format_tfd_tc(self.tc)
        self.t0 = tc_data["full"]
        self.tc_short = tc_data["short"]
        
        # Numer ujęcia z ścieżki TAKE lub numeru
        take_path = getattr(bus, "loaded_take_path", None)
        if take_path:
            import re
            filename = os.path.basename(take_path)
            # Szukamy numeru ujęcia i opcjonalnej wersji (np. TAKE_001_v12, TAKE_001-12)
            # Grupa 1: numer, Grupa 2: wersja (po separatorze - lub _ lub v)
            match = re.search(r'(?:TAKE_)?(\d+)(?:[-_vV]+(\d+))?', filename, re.IGNORECASE)
            if match:
                num = match.group(1).zfill(3)
                ver = match.group(2)
                if ver:
                    self.take_number = f"{num}-{ver}"
                else:
                    self.take_number = num
            else:
                self.take_number = "001"
        else:
            raw_take = bus.get("take_num") or bus.get("par_take_num", 1)
            self.take_number = self.format_tfd_take_number(raw_take)

        # Pełne dane osi - Mapowanie zgodne z AXIS_SIGNAL_BINDINGS
        axes = {}
        axis_names = ["CAM_H", "CAM_V", "CAM_T", "CAM_F", "ARM_H", "ARM_V"]
        
        for i, name in enumerate(axis_names):
            key = f"axis{i}"
            
            # Pobieramy DIR dla formatowania znaku
            # Szukamy w SignalBus sygnału DIR powiązanego z tą osią
            dir_val = 0
            dir_keys = [f"par_{name.lower()}_dir", f"TAKE_{name}_DIR"]
            for dk in dir_keys:
                if bus.exists(dk):
                    dir_val = 1 if bus.get(dk) else 0
                    break
            
            # LICZNIK KROKÓW - kluczowy parametr dla TFD
            # Pobieramy z par_{axis}_pulses, który jest aktualizowany przez TarzanParPanels z AxisCard.counter
            pulses = bus.get(f"par_{name.lower()}_pulses", 0)
            
            # Formatujemy wartość osi dla TFD: +00000 / -00000
            formatted_pos = self.format_tfd_axis_value(pulses, dir_val)
            
            axes[key] = {
                "name": name,
                "pos": formatted_pos,
                "dir": dir_val,
                "pulses": pulses
            }

        # Czujniki
        laser_active = bus.get("par_laser_set", 0) or bus.get("par_laser_active", 0)
        laser_error = bus.get("par_laser_error", 0)
        # Czujnik laserowy - dwa stany 0 i 1
        if laser_error:
            laser_state = "0"
        else:
            laser_state = "1" if laser_active else "0"
        
        limits_state = bus.get("par_limits_status", "0")
        
        shock_val = bus.get("par_shock_sensor_state", 0) or bus.get("par_shock_active", 0)
        shock = "1" if shock_val else "0"
        
        light_val = bus.get("par_bh1750_lux", 0)
        light = f'{str(int(light_val)).zfill(5)}'
        
        temp_val = bus.get("par_temperature_c", 22.0)
        try:
            temp = f"{float(temp_val):.1f}"
        except:
            temp = f"{temp_val}"
        
        lx = bus.get('par_level_x', 0)
        ly = bus.get('par_level_y', 0)
        lz = bus.get('par_level_z', 0)
        xyz_formatted = self.format_tfd_xyz(lx, ly, lz)

        packet = {
            "system": "TARZAN_FRAME_DATA",
            "short": "TFD",
            "packet_id": self.packet_id,
            "timestamp": time.time(),
            "take": self.format_tfd_take_number(self.take_number),
            "tc": self.tc,
            "tc_short": getattr(self, "tc_short", self.tc[:10]),
            "t0": self.t0,
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
            "last_event": self.events[-1] if self.events else None
        }

        self.last_packet = packet
        self.packet_id += 1
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
        if not self.last_packet:
            return {
                "title": self.title, "director": self.director,
                "take": self.take_number, "clap": self.clap,
                "status": self.status, "tc": self.tc
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
