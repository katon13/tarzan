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

            # Logika sterowania w zależności od trybu
            if active_mode == "tM":
                # Tryb MANUAL — rRP/SOK sterują bezpośrednio
                pass
            elif active_mode == "tAA":
                # Tryb ALL AUTO — EHR/TAKE steruje osiami
                pass
            
            # Przykład: Jeśli transport = REC, zapalamy LED nagrywania
            if transport == "REC":
                self.bus.write_output("rec_p09_led_data", 1, source="MODE_LOGIC")
            else:
                self.bus.write_output("rec_p09_led_data", 0, source="MODE_LOGIC")

            time.sleep(0.05) # 20Hz wystarczy dla logiki trybów

def start_mode_logic():
    logic = TarzanModeLogic()
    logic.start()
    return logic
