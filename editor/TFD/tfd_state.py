import time

class TFDState:
    def __init__(self):
        self.title = "TYTUŁ FILMU"
        self.director = "REŻYSER"
        self.take_number = 1
        self.clap = 0
        self.status = "LIVE"
        self.tc = "00:00:00:00"
        self.t0 = time.strftime("%d:%m:%Y") # Domyślnie data
        self.packet_id = 0
        
        # Cache dla paczki danych (Export Source of Truth)
        self.last_packet = {}
        
        # Cache dla optymalizacji wysyłki (sent_cache)
        self.sent_cache = {}
        
        self._last_update_time = 0.0
        self._update_interval = 0.04  # 40ms (ok. 25 FPS)

    def update_meta(self, title=None, director=None):
        """Aktualizuje metadane TFD."""
        if title is not None: 
            self.title = str(title).strip()[:100]
        if director is not None: 
            self.director = str(director).strip()[:100]

    def set_clap(self, value):
        """Ustawia marker CLAP i zapamiętuje czas dla auto-resetu."""
        if value:
            self.clap = 1
            self._clap_time = time.time()
        else:
            self.clap = 0
            self._clap_time = 0

    def update_from_bus(self, bus):
        """Aktualizuje stan TFD na podstawie danych systemowych."""
        now = time.time()
        
        # Auto-reset klapsa po 800ms
        if self.clap and (now - getattr(self, "_clap_time", 0)) > 0.8:
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

        axes = {}
        axis_map = {
            "axis0": "CAM_H", "axis1": "CAM_V", "axis2": "CAM_T", 
            "axis3": "CAM_F", "axis4": "ARM_H", "axis5": "ARM_V"
        }
        for i in range(6):
            key = f"axis{i}"
            func_name = axis_map.get(key)
            val = bus.get(f"par_{func_name.lower()}_pos", "00000")
            axes[key] = str(val).zfill(5)

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
            }
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
