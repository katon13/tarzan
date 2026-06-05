"""
TARZAN MODE — Logika trybów pracy (tM, tAA, tAT, itp.).
Spięcie sygnałów logicznych z torami wykonawczymi.
"""
import threading
import time
from typing import Optional
from core.tarzanSignalBus import get_signal_bus

class TarzanModeLogic:
    def __init__(self):
        self.bus = get_signal_bus()
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, name="TarzanModeLogic", daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _loop(self):
        while self.running:
            # Czekamy na gotowość systemu
            if not self.bus.read("tarzan_ready", 0):
                time.sleep(0.5)
                continue

            active_mode = self.bus.read("active_mode", "tM")
            transport = self.bus.read("transport_state", "STOP")
            owner = self.bus.read("control_owner", "TSP_BOOT")

            # ETAP 12: Logika sterowania w zależności od trybu
            if active_mode == "tM":
                # Tryb MANUAL — rRP/SOK sterują bezpośrednio (Etap 13)
                # TYLKO jeśli właściciel pozwala na sterowanie ręczne
                if owner in {"PAR_LIVE", "TSP_SERVICE", "LKS_DIAGNOSTIC"}:
                    self._handle_manual_control()
            
            elif active_mode == "tAA":
                # Tryb ALL AUTO — EHR/TAKE steruje osiami (Etap 14)
                # control_owner powinien być ustawiony na EHR_PLAYBACK
                if owner == "EHR_PLAYBACK" and transport == "PLAY":
                    self._handle_auto_playback()
            
            # Przykład: Jeśli transport = REC, zapalamy LED nagrywania
            if transport == "REC":
                self.bus.write_output("rec_p09_led_data", 1, source="MODE_LOGIC")
            else:
                self.bus.write_output("rec_p09_led_data", 0, source="MODE_LOGIC")

            time.sleep(0.05) # 20Hz wystarczy dla logiki trybów

    def _handle_manual_control(self):
        """Przekazywanie sterowania z rRP/SOK do osi (Etap 13)."""
        # Gracz 1 (P1)
        axis_p1 = self.bus.read("rrp_p1_axis_index", 0)
        val_p1 = self.bus.read("sensor_rrp_pot_h", 512)
        self._apply_rrp_to_axis(axis_p1, val_p1, "p1")

        # Gracz 2 (P2)
        axis_p2 = self.bus.read("rrp_p2_axis_index", 0)
        val_p2 = self.bus.read("sensor_rrp_pot_v", 512)
        self._apply_rrp_to_axis(axis_p2, val_p2, "p2")

    def _apply_rrp_to_axis(self, axis_index: int, value: int, player: str):
        """Mapowanie potencjometru na ruch osi."""
        if axis_index == 0: return # Brak wybranej osi
        
        # Mapowanie indeksu na nazwę osi (zgodnie z katalogiem)
        axis_map = {
            1: "cam_h", 2: "cam_v", 3: "cam_t", 4: "cam_f",
            5: "arm_h", 6: "arm_v", 7: "tilt", 8: "cart"
        }
        axis_name = axis_map.get(axis_index)
        if not axis_name: return

        # Wyznaczanie kierunku i prędkości (deadzone)
        # Zakładamy pot 0..1023, center 512
        deadzone = 20
        diff = value - 512
        if abs(diff) < deadzone:
            speed = 0
            dir_val = 0
        else:
            speed = abs(diff) # Uproszczone: prędkość = wychylenie
            dir_val = 1 if diff > 0 else -1

        # Zapis do SignalBus (Snajper/Adaptery to odbierają)
        prefix = f"axis_{axis_name}"
        if self.bus.exists(f"{prefix}_dir"):
            self.bus.write_output(f"{prefix}_dir", dir_val, source=f"MODE_RRP_{player.upper()}")
        # Prędkość / kroki mogą być generowane przez Snajper/PulseEngine na podstawie speed
        if self.bus.exists(f"{prefix}_speed"):
            self.bus.write_output(f"{prefix}_speed", speed, source=f"MODE_RRP_{player.upper()}")

    def _handle_auto_playback(self):
        """Logika odtwarzania automatycznego (EHR)."""
        # Tu MODE_LOGIC może nadzorować czy EHR podaje dane i czy nie ma limitów
        pass

def start_mode_logic():
    logic = TarzanModeLogic()
    logic.start()
    return logic
