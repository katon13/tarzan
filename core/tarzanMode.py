"""
TARZAN MODE — Logika trybów pracy (tM, tAA, tAT, itp.).
Spięcie sygnałów logicznych z torami wykonawczymi.
"""
import threading
import time
from typing import Optional, Any
from core.tarzanSignalBus import get_signal_bus
from core.tarzanSnajper import TarzanSnajperHardwarePolicy

class TarzanModeLogic:
    def __init__(self):
        self.bus = get_signal_bus()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._snajper_policy = TarzanSnajperHardwarePolicy()
        self._hardware_awake_until_ms = 0.0
        self._last_realtime_required: Optional[int] = None

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

            # ETAP 8 i 9: Obsługa komend systemowych
            self._handle_system_commands()

            cmd_awake = self.bus.read("cmd_hardware_awake", 0)
            if self._snajper_policy.truthy(cmd_awake):
                now = time.time() * 1000.0
                self._hardware_awake_until_ms = max(
                    self._hardware_awake_until_ms,
                    now + self._snajper_policy.grace_ms_for("default"),
                )
                self.bus.force_signal("cmd_hardware_awake", 0, source="MODE_AUTO_RESET")

            active_mode = self.bus.read("active_mode", "tM")
            transport = self.bus.read("transport_state", "STOP")
            owner = self.bus.read("control_owner", "TSP_BOOT")

            # Automatyczne zarządzanie control_owner na podstawie trybu
            self._manage_control_owner(active_mode, owner)

            # ETAP 12: Logika sterowania w zależności od trybu
            if active_mode == "tM":
                # Tryb MANUAL — rRP/SOK sterują bezpośrednio (Etap 13)
                if owner in {"PAR_LIVE", "TSP_SERVICE", "LKS_DIAGNOSTIC"}:
                    self._handle_manual_control()

            elif active_mode == "tAA":
                # Tryb ALL AUTO — EHR/TAKE steruje osiami (Etap 14)
                if owner == "EHR_PLAYBACK" and transport == "PLAY":
                    self._handle_auto_playback()

            # Przykład: Jeśli transport = REC, zapalamy LED nagrywania
            if transport == "REC":
                self.bus.write_output("rec_p09_led_data", 1, source="MODE_LOGIC")
            else:
                self.bus.write_output("rec_p09_led_data", 0, source="MODE_LOGIC")

            is_active = self._is_system_active(
                active_mode=active_mode,
                transport=transport,
                owner=owner,
            )
            realtime_required = 1 if is_active else 0
            if realtime_required != self._last_realtime_required:
                self.bus.set_input("hardware_realtime_required", realtime_required, source="MODE_LOGIC")
                self._last_realtime_required = realtime_required

            # Adaptacyjny sleep: aktywnie lekko, IDLE spokojnie. Bez SignalBus wait.
            time.sleep(0.05 if is_active else 1.0)

    def _is_system_active(self, active_mode: Any = None, transport: Any = None, owner: Any = None) -> bool:
        """Czy system wymaga realtime hardware.

        Sam PAR_CONNECTED/EHR_CONNECTED/Nextion status nie wystarcza. Wymagany
        jest strzał Snajpera, PLAY/REC, tryb wykonawczy albo realny ruch osi.
        """
        try:
            now = time.time() * 1000.0
            if now < float(self._hardware_awake_until_ms):
                return True

            active_mode = self.bus.read("active_mode", "tM") if active_mode is None else active_mode
            transport = self.bus.read("transport_state", "STOP") if transport is None else transport
            owner = self.bus.read("control_owner", "TSP_BOOT") if owner is None else owner
            if self._snajper_policy.runtime_requires_realtime(
                active_mode=active_mode,
                transport_state=transport,
                control_owner=owner,
                cmd_hardware_awake=0,
            ):
                return True

            from core.tarzanZmienneSygnalowe import LISTA_NAZW_OSI
            for ax in LISTA_NAZW_OSI:
                if self._snajper_policy.truthy(self.bus.read(f"axis_{ax}_dir", 0)):
                    return True
                if self._snajper_policy.truthy(self.bus.read(f"axis_{ax}_step", 0)):
                    return True

            for sig in ["cmd_unlock_axes", "cmd_clear_alarms", "cmd_ehr_start", "cmd_khr_start", "cmd_run_diagnostics"]:
                if self._snajper_policy.truthy(self.bus.read(sig, 0)):
                    return True

            if str(self.bus.read("ehr_state", "OFFLINE")).upper() == "ACTIVE":
                return True
            if str(self.bus.read("khr_state", "OFFLINE")).upper() == "ACTIVE":
                return True

        except Exception:
            # Błąd logiki trybu nie może wrzucać PoKeys w stałą pętlę.
            return False
        return False

    def _handle_system_commands(self):
        """Obsługuje komendy start/stop modułów EHR/KHR."""
        # EHR Start/Stop
        if self.bus.read("cmd_ehr_start", 0):
            self.bus.set_input("cmd_ehr_start", 0, source="MODE_LOGIC")
            self.bus.set_input("ehr_state", "ACTIVE", source="MODE_LOGIC")
            self.bus.set_input("transport_state", "PLAY", source="MODE_LOGIC")
            self.bus.log("MODE", "EHR Playback STARTED via command.")

        if self.bus.read("cmd_ehr_stop", 0):
            self.bus.set_input("cmd_ehr_stop", 0, source="MODE_LOGIC")
            self.bus.set_input("ehr_state", "READY", source="MODE_LOGIC")
            self.bus.set_input("transport_state", "STOP", source="MODE_LOGIC")
            self.bus.log("MODE", "EHR Playback STOPPED via command.")

        # KHR Start/Stop
        if self.bus.read("cmd_khr_start", 0):
            self.bus.set_input("cmd_khr_start", 0, source="MODE_LOGIC")
            self.bus.set_input("khr_state", "ACTIVE", source="MODE_LOGIC")
            self.bus.log("MODE", "KHR Correction ACTIVE.")

        if self.bus.read("cmd_khr_stop", 0):
            self.bus.set_input("cmd_khr_stop", 0, source="MODE_LOGIC")
            self.bus.set_input("khr_state", "READY", source="MODE_LOGIC")
            self.bus.log("MODE", "KHR Correction OFF.")

    def _manage_control_owner(self, mode: str, current_owner: str):
        """Automatycznie ustawia właściciela sterowania w zależności od trybu."""
        if mode == "tAA":
            if current_owner != "EHR_PLAYBACK":
                self.bus.set_input("control_owner", "EHR_PLAYBACK", source="MODE_AUTO")
                self.bus.log("MODE", "Control Owner changed to EHR_PLAYBACK for AUTO mode.")
        elif mode == "tM":
            if current_owner == "EHR_PLAYBACK":
                # Wracamy do PAR_LIVE jeśli EHR skończył
                self.bus.set_input("control_owner", "PAR_LIVE", source="MODE_AUTO")
                self.bus.log("MODE", "Control Owner restored to PAR_LIVE for MANUAL mode.")

    def _handle_manual_control(self):
        """Przekazywanie sterowania z rRP/SOK do osi (Etap 13)."""
        # 1. Sprawdzamy blokady bezpieczeństwa (SOK / EMERGENCY)
        if self.bus.read("sensor_shock_state", 0) or self.bus.read("emergency_stop", 0):
            return

        # 2. Gracz 1 (P1)
        axis_p1 = self.bus.read("rrp_p1_axis_index", 0)
        val_p1 = self.bus.read("sensor_rrp_pot_h", 512)
        self._apply_rrp_to_axis(axis_p1, val_p1, "p1")

        # 3. Gracz 2 (P2)
        axis_p2 = self.bus.read("rrp_p2_axis_index", 0)
        val_p2 = self.bus.read("sensor_rrp_pot_v", 512)
        self._apply_rrp_to_axis(axis_p2, val_p2, "p2")

    def _apply_rrp_to_axis(self, axis_index: int, value: int, player: str):
        """Mapowanie potencjometru na ruch osi (Etap 13)."""
        if axis_index == 0: return # Brak wybranej osi
        
        # Mapowanie indeksu na nazwę osi (zgodnie z katalogiem)
        axis_map = {
            1: "cam_h", 2: "cam_v", 3: "cam_t", 4: "cam_f",
            5: "arm_h", 6: "arm_v", 7: "tilt", 8: "cart"
        }
        axis_name = axis_map.get(axis_index)
        if not axis_name: return

        # 4. Sprawdzanie gotowości osi (Bezpieczeństwo Etap 13)
        prefix = f"axis_{axis_name}"
        if not self.bus.read(f"{prefix}_ready", 0):
            # Oś nie jest gotowa (brak inwentaryzacji lub błąd)
            return

        # 5. Wyznaczanie kierunku (deadzone)
        deadzone = 20
        diff = value - 512
        if abs(diff) < deadzone:
            dir_val = 0
        else:
            dir_val = 1 if diff > 0 else -1

        # 6. Zapis do SignalBus (Snajper/Adaptery to odbierają)
        if self.bus.exists(f"{prefix}_dir"):
            self.bus.write_output(f"{prefix}_dir", dir_val, source=f"MODE_RRP_{player.upper()}")
        
        # UWAGA BEZPIECZEŃSTWA: 
        # Nie generujemy impulsów STEP bezpośrednio w ModeLogic.
        # Hardware path (Snajper) zajmuje się generowaniem impulsów na podstawie 
        # kierunku i wartości potencjometru w trybie manualnym.

    def _handle_auto_playback(self):
        """Logika odtwarzania automatycznego z uwzględnieniem KHR (Etap 14-15)."""
        khr_active = self.bus.read("khr_state") == "ACTIVE"
        
        # EHR Playback wpisuje dane bezpośrednio do SignalBus (axis_ID_dir/step).
        # ModeLogic w trybie tAA nadzoruje czy KHR ma wprowadzić korekty.
        
        if khr_active:
            axes = ["cam_h", "cam_v", "arm_h", "arm_v"]
            for axis in axes:
                offset = self.bus.read(f"khr_{axis}_offset", 0)
                if offset != 0:
                    # Korekta KHR (Etap 15):
                    # W tym modelu KHR podaje gotowy offset do zaaplikowania.
                    # Realna implementacja w hardware path (Snajper) połączy
                    # puls podstawowy z pulsem korekcyjnym.
                    pass

def start_mode_logic():
    logic = TarzanModeLogic()
    logic.start()
    return logic
