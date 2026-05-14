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

    def update_from_bus(self, bus):
        """Aktualizuje stan TFD na podstawie danych systemowych."""
        now = time.time()
        
        # Auto-reset klapsa po 800ms
        if self.clap and (now - self._clap_time) > 0.8:
            self.clap = 0
            
        if (now - self._last_update_time) < self._update_interval and self.last_packet:
            return self.last_packet
            
        self._last_update_time = now
        
        self.status = str(bus.get("par_status", "LIVE")).upper()
        self.tc = str(bus.get("take_tc", "00:00:00:00"))
        try:
            self.take_number = int(bus.get("take_num", 1))
        except:
            self.take_number = 1

        # Pełne dane osi - Mapowanie zgodne z AXIS_SIGNAL_BINDINGS
        axes = {}
        axis_map = {
            "axis0": {"name": "CAM_H", "steps": ["TAKE_CAM_H_STEP", "rec_p01_copy_ctr_cam_h", "cnc_x_cam_h_ctr"], "dirs": ["TAKE_CAM_H_DIR", "rec_p03_copy_dir_cam_h", "cnc_x_cam_h_dir"], "ens": []},
            "axis1": {"name": "CAM_V", "steps": ["TAKE_CAM_V_STEP", "rec_p02_copy_ctr_cam_v", "cnc_y_cam_v_ctr"], "dirs": ["TAKE_CAM_V_DIR", "rec_p04_copy_dir_cam_v", "cnc_y_cam_v_dir"], "ens": []},
            "axis2": {"name": "CAM_T", "steps": ["TAKE_CAM_T_STEP", "rec_p06_copy_ctr_tilt", "cnc_a_arm_tilt_ctr"], "dirs": ["TAKE_CAM_T_DIR", "rec_p08_copy_dir_tilt", "cnc_a_arm_tilt_dir"], "ens": []},
            "axis3": {"name": "CAM_F", "steps": ["TAKE_CAM_F_STEP", "rec_p05_copy_ctr_focus", "cnc_z_focus_ctr"], "dirs": ["TAKE_CAM_F_DIR", "rec_p07_copy_dir_focus", "cnc_z_focus_dir"], "ens": []},
            "axis4": {"name": "ARM_H", "steps": ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "cnc_b_arm_h_ctr"], "dirs": ["TAKE_ARM_H_DIR", "play_p38_step_dir_arm_h", "cnc_b_arm_h_dir"], "ens": ["play_p50_step_en_arm_h"]},
            "axis5": {"name": "ARM_V", "steps": ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "cnc_c_arm_v_ctr"], "dirs": ["TAKE_ARM_V_DIR", "play_p39_step_dir_arm_v", "cnc_c_arm_v_dir"], "ens": ["play_p51_step_en_arm_v"]}
        }
        
        for key, info in axis_map.items():
            name = info["name"]
            
            # Pobieramy pierwszą niezerową wartość z listy sygnałów
            step = 0
            for sig in info["steps"]:
                v = bus.get(sig, 0)
                if v: 
                    step = v
                    break
            
            dir_val = 0
            for sig in info["dirs"]:
                v = bus.get(sig, 0)
                if v:
                    dir_val = v
                    break
            
            en = 1
            if info["ens"]:
                for sig in info["ens"]:
                    v = bus.get(sig, 1)
                    if v == 0:
                        en = 0
                        break
            
            pos = bus.get(f"par_{name.lower()}_pos", "00000")
            
            axes[key] = {
                "name": name,
                "pos": str(pos).zfill(5),
                "step": step,
                "dir": dir_val,
                "en": en,
                "pulses": bus.get(f"par_{name.lower()}_pulses", 0)
            }

        # Czujniki
        laser_state = "OK" if not bus.get("par_laser_error", 0) else "ERR"
        limits_aktywne = any(bus.get(sig, 0) for sig in [
            "play_p03_arm_h_limit_left", "play_p01_arm_h_auto_limit", 
            "play_p04_arm_v_limit_up", "play_p09_arm_v_auto_limit",
            "cam_h_limit_left", "cam_h_limit_right", "cam_v_limit_up", "cam_v_limit_down"
        ])
        limits_state = "LIMIT!" if limits_aktywne else "OK"
        shock = "SHOCK!!" if bus.get("par_shock_sensor_state", 0) else "OK"
        light_val = bus.get("par_light_val", 0)
        light = f'{str(light_val).zfill(5)} LX'
        temp_val = bus.get("par_temperature_val", "22")
        temp = f"{temp_val}C"
        
        x = bus.get('par_level_x', 0)
        y = bus.get('par_level_y', 0)
        z = bus.get('par_level_z', 0)
        xyz = f'X{x:+} Y{y:+} Z{z:+}'

        packet = {
            "system": "TARZAN_FRAME_DATA",
            "short": "TFD",
            "packet_id": self.packet_id,
            "timestamp": time.time(),
            "take": self.take_number,
            "tc": self.tc,
            "t0": self.t0,
            "title": self.title,
            "director": self.director,
            "clap": self.clap,
            "status": self.status,
            "axes": axes,
            "sensors": {
                "laser": laser_state, "limits": limits_state,
                "shock": shock, "light": light,
                "temp": temp, "xyz": xyz,
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

tfd_state = TFDState()
