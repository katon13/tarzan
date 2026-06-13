from __future__ import annotations

import time
import threading
import os
import platform
import glob
import json
from pathlib import Path
from typing import Any, Dict, Optional, List, Sequence, Mapping

from core.tarzanZmienneSygnalowe import (
    WSZYSTKIE_SYGNALY,
    POKEYS57U_PLAY_DEVICE_SERIAL,
    POKEYS57U_REC_DEVICE_SERIAL,
    TarzanSygnal
)
from core.TSP.tarzanTspLog import setup_tsp_logger
from core.tarzanSnajper import TarzanSnajperHardwarePolicy

from core.tarzanPoKeys import TarzanPoKeys, LIB_POKEYS_AVAILABLE

class TarzanHardwareBridge:
    """
    Bridge łączący SignalBus z fizycznym sprzętem (PoKeys, I2C, LCD).
    Działa jako LIVE_ADAPTER dla SignalBus na miniPC.
    
    ARCHITEKTURA:
    PAR / EHR / KHR / LKS (Intencja)
    -> SignalBus (Tablica stanu)
    -> Snajper (Rozprowadzanie)
    -> TarzanHardwareBridge (Ten moduł - Wykonanie)
    -> PoKeys / Hardware (Fizyka)
    
    ETAP 13 (Wykonawczy) + ETAP 14 (EHR Playback).
    """

    def __init__(self, bus: Any) -> None:
        self.bus = bus
        self.logger = setup_tsp_logger("HW.BRIDGE")
        self.running = False
        self._lock = threading.RLock()
        self.pokeys = TarzanPoKeys(self.logger)
        # Własny adapter core/tarzanPoKeys.py trzyma uchwyty PLAY/REC.
        # hardware/pokeys/PoKeys.py jest tylko bindingiem niskiego poziomu.
        self.devices: Dict[str, Any] = self.pokeys.devices
        self._lcd_lines: Dict[str, List[str]] = {
            "PLAY": ["", ""],
            "REC": ["", ""],
        }
        
        # Liczniki absolutne pozycji (Etap 14/15)
        # Kluczem jest nazwa bazowa osi, np. "axis_cam_h"
        self._abs_positions: Dict[str, int] = {}
        
        self._last_poll_ms = 0
        self._poll_interval_ms = 10  # 100Hz dla wejść (tryb realtime 10ms)
        
        # ZASADA SNAJPERA (ETAP 17): Dynamiczne połączenie
        self._last_activity_ms = 0 # Startujemy w IDLE
        self._reconnect_cooldown_ms = 0
        self._idle_timeout_ms = 2000  # Krótki, ale nie zrywa połączenia w środku serii testów LKS.
        self._hardware_awake_until_ms = 0.0
        self._hardware_batch_depth = 0
        self._hardware_batch_source = ""
        self._snajper_policy = TarzanSnajperHardwarePolicy()
        self._last_connect_failed = False # Flaga dla selektywnego cooldownu
        self._hardware_logical_sleep = False  # IDLE: pauza logiczna bez PK_DisconnectDevice.
        self._startup_i2c_test_done = False
        self._startup_i2c_test_error = ""
        
        # Optymalizacja (Etap 17): cache wejść hardware'owych
        # ZASADA SNAJPERA: nie brudzimy SignalBus jeśli na pinach cisza.
        self._gpio_inputs: List[Any] = []
        self._analog_inputs: List[Any] = []
        self._cnc_signals: List[Any] = []
        self._input_cache: Dict[str, Any] = {}
        
        # FLAGA BEZPIECZEŃSTWA - musi być True, aby generować impulsy na fizycznym sprzęcie
        # ETAP 13: Aktywacja mięśni (odblokowanie osi po weryfikacji logicznej i komunikacyjnej)
        # Zmiana na True oznacza przejście w tryb pełnego zespolenia wykonawczego.
        self.safety_axis_unlock = False
        
        # Mapa sygnałów dla szybkiego dostępu w metodzie write/read
        self._signal_map = WSZYSTKIE_SYGNALY
        for syg in self._signal_map.values():
            if syg.kierunek == "IN" and syg.hardware_function == "GPIO" and syg.pin is not None:
                self._gpio_inputs.append(syg)
            if (syg.hardware_function == "ANALOG" or syg.typ == "ANALOG") and syg.pin is not None:
                self._analog_inputs.append(syg)
            if syg.plytka == "CNC" or syg.hardware_function == "PULSE_ENGINE":
                self._cnc_signals.append(syg)

        self.logger.info("tarzanPoKeys inventory: %s", self.pokeys.inventory())
        
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        if self.running:
            return True
            
        self.logger.info("Starting Hardware Bridge...")
        
        if not LIB_POKEYS_AVAILABLE:
            self.logger.error("PoKeys library not available!")
            self.bus.force_signal("hardware_state", "ERROR", source="HW_BRIDGE")
            return False

        # Ścieżka do biblioteki PoKeys (zależna od platformy)
        lib_path = self._get_lib_path()
        if not lib_path or not os.path.exists(lib_path):
            self.logger.error(f"PoKeys library file not found at: {lib_path}")
            self.bus.force_signal("hardware_state", "ERROR", source="HW_BRIDGE")
            return False

        try:
            # ZASADA SNAJPERA: Nie łączymy od razu, pętla _run zajmie się tym
            # gdy wykryje aktywność lub wymusi startowy test.
            self.running = True
            self.bus.set_input("hardware_connected", 0, source="HW_BRIDGE")
            self.bus.set_live_adapter(self)
            # Start systemu ma wykonać jednorazowe sprawdzenie PoKeys/I2C,
            # potem HardwareBridge wraca do IDLE bez pollingu.
            self.request_hardware_awake(source="HW_STARTUP_I2C", grace_ms=15000, ensure=False, action_type="FULL_DIAGNOSTICS")
            
            # Subskrypcja offsetów KHR (Etap 15)
            self.bus.subscribe(self._on_signal_change)
            
            self._thread = threading.Thread(target=self._run, daemon=True, name="HW_Bridge_Loop")
            self._thread.start()
            
            self.bus.force_signal("hardware_state", "READY", source="HW_BRIDGE")
            self.logger.info("Hardware Bridge STARTED (Pending Connection).")
            return True
        except Exception as exc:
            self.logger.error(f"Hardware Bridge failed to start: {exc}")
            self.bus.force_signal("hardware_state", "ERROR", source="HW_BRIDGE")
            return False

    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        
        # Fizyczny disconnect tylko przy STOP usługi, przez własną warstwę PoKeys.
        self.pokeys.safe_stop()
        
        self.bus.set_live_adapter(None)
        self.logger.info("Hardware Bridge STOPPED.")

    def _get_lib_path(self) -> str:
        """Zwraca realną ścieżkę do biblioteki PoKeys przez core/tarzanPoKeys.py."""
        return self.pokeys.get_lib_path()

    def _init_devices(self, lib_path: str) -> None:
        self.pokeys.connect_all(lib_path)

    def _connect_board(self, name: str, serial: int, lib_path: str) -> Any:
        return self.pokeys.connect_board(name, serial, lib_path)

    def _run(self) -> None:
        while self.running:
            now = time.time() * 1000

            # 1. ZASADA SNAJPERA (ETAP 17): Zarządzanie aktywnością i połączeniem
            is_active = self._is_system_active()
            
            if is_active:
                self._last_activity_ms = now
                self._ensure_connected()
            else:
                # Grace period przed snem logicznym.
                # Nie zamykamy uchwytow PoKeys w IDLE: PK_DisconnectDevice/libusb
                # potrafi zrobic ABRT przy concurrent close. Cel CPU osiagamy przez
                # zatrzymanie pollingu, nie przez agresywne USB disconnect.
                if now - self._last_activity_ms > self._idle_timeout_ms:
                    self._ensure_disconnected()

            # 2. Adaptacyjny polling wejść
            is_connected = self._is_any_connected()
            
            if is_connected and is_active:
                # PoKeys GPIO/PE tylko w aktywnym oknie. W IDLE brak pollingu.
                if now - self._last_poll_ms >= self._poll_interval_ms:
                    self._poll_hardware(is_active=True)
                    self._last_poll_ms = now
            
            # 3. Generator trybu manualnego (tM) - ETAP 13
            has_motion = False
            if is_connected:
                has_motion = self._handle_manual_generator()

            # Adaptacyjny sleep zgodny z Zasadą Snajpera.
            if has_motion:
                time.sleep(0.005) # 200Hz przy ruchu
            elif is_active:
                time.sleep(0.01)  # 100Hz realtime (10ms)
            else:
                # W głębokim IDLE nie ma SignalBus wait zależnego od wersji SignalBus.
                # Brak akcji = spokój, bez libusb/PoKeys i bez kręcenia CPU.
                time.sleep(1.0)

    def _is_any_connected(self) -> bool:
        return self.pokeys.is_any_connected()


    def begin_hardware_batch(self, source: str = "SNAJPER_BATCH", grace_ms: int = 12000, ensure: bool = False, action_type: str = "FULL_DIAGNOSTICS") -> None:
        """Sesja wielu strzałów Snajpera bez reconnect-spinu.
        
        Używane dla boot diagnostyki, pełnej diagnostyki LKS lub serii szybkich ruchów (RRP).
        Utrzymuje wybrany stan aktywności hardware przez czas trwania batcha.
        """
        try:
            now = time.time() * 1000.0
            grace = max(2000, int(grace_ms or 12000))
            action_type = str(action_type or "FULL_DIAGNOSTICS").upper()
            with self._lock:
                self._hardware_batch_depth += 1
                self._hardware_batch_source = str(source or "SNAJPER_BATCH")
                self._hardware_awake_until_ms = max(self._hardware_awake_until_ms, now + grace)
                self._last_activity_ms = now
                
                if action_type == "POINT_TEST":
                    self.pokeys.begin_point_test(source)
                elif action_type == "FULL_DIAGNOSTICS":
                    self.pokeys.begin_full_diagnostics(source)
                elif action_type == "EXEC":
                    self.pokeys.begin_exec(source)
                elif action_type == "FAST_SAMPLE":
                    self.pokeys.begin_fast_sample(source=f"BATCH_{source}")

            if ensure:
                self._ensure_connected()
        except Exception as exc:
            self.logger.debug("begin_hardware_batch failed source=%s error=%s", source, exc)

    def end_hardware_batch(self, source: str = "SNAJPER_BATCH", grace_ms: int = 2000) -> None:
        """Kończy serię testów i pozwala hardware wrócić do IDLE po krótkim grace."""
        try:
            now = time.time() * 1000.0
            grace = max(500, int(grace_ms or 2000))
            with self._lock:
                self._hardware_batch_depth = max(0, self._hardware_batch_depth - 1)
                self._hardware_awake_until_ms = max(self._hardware_awake_until_ms, now + grace)
                self._last_activity_ms = now
                if self._hardware_batch_depth == 0:
                    self._hardware_batch_source = ""
                    self.pokeys.end_active_state()
        except Exception as exc:
            self.logger.debug("end_hardware_batch failed source=%s error=%s", source, exc)

    def apply_lks_test_safe_state(self, source: str = "LKS_TEST") -> Dict[str, Any]:
        """Przywraca bezpieczny stan wyjść po testach LKS/ABC, bez ruchu osi.

        Testy LKS mogą chwilowo mignąć LED/wyjściami. Po zakończeniu serii
        wracamy do naturalnego stanu OFF/LOW zapisanego w tarzanPoKeys.
        Nie zapisujemy konfiguracji i nie uruchamiamy STEP/DIR/ENABLE.
        """
        try:
            if hasattr(self.pokeys, "apply_default_safe_state_once"):
                result = self.pokeys.apply_default_safe_state_once()
                self.logger.info(
                    "POKEYS ABC SAFE STATE AFTER %s ok=%s",
                    source,
                    bool(isinstance(result, dict) and result.get("ok")),
                )
                return result if isinstance(result, dict) else {"ok": False, "raw": result}
        except Exception as exc:
            self.logger.warning("POKEYS ABC SAFE STATE AFTER %s failed: %s", source, exc)
            return {"ok": False, "error": str(exc)}
        return {"ok": False, "error": "NO_SAFE_STATE_METHOD"}

    def request_hardware_awake(self, source: str = "SNAJPER", grace_ms: int = 1500, ensure: bool = False, action_type: str = "CONNECT_ONLY") -> None:
        """Krótki strzał Snajpera w hardware: akcja -> reakcja.

        Nie jest to stały tryb pracy. Metoda daje okno aktywności, opcjonalnie
        łączy PoKeys natychmiast na czas testu/akcji i po grace wraca do IDLE.
        """
        try:
            now = time.time() * 1000.0
            grace = max(500, int(grace_ms or self._snajper_policy.grace_ms_for("default")))
            
            with self._lock:
                self._hardware_awake_until_ms = max(self._hardware_awake_until_ms, now + grace)
                self._last_activity_ms = now
                
                # Rozdzielamy wybudzanie na jawne tory wg MAPY TARZANA.
                # Brak jawnego typu NIE oznacza FAST_SAMPLE.
                action_type = str(action_type or "CONNECT_ONLY").upper()
                self.logger.info("HW AWAKE source=%s action_type=%s grace_ms=%s", source, action_type, grace)
                if action_type == "POINT_TEST":
                    self.pokeys.begin_point_test(source)
                elif action_type == "FULL_DIAGNOSTICS":
                    self.pokeys.begin_full_diagnostics(source)
                elif action_type == "EXEC":
                    self.pokeys.begin_exec(source)
                elif action_type == "FAST_SAMPLE":
                    # FAST_SAMPLE tylko jeśli nie trwa ważniejsza akcja
                    if self.pokeys.state in ["IDLE", "FAST_SAMPLE"]:
                        self.pokeys.begin_fast_sample(source=f"AWAKE_{source}")
                elif action_type == "CONNECT_ONLY":
                    # Tylko zapewnienie połączenia, bez zmiany stanu logicznego bramki
                    pass

            try:
                self.bus.set_input("hardware_realtime_required", 1, source=f"HW_AWAKE_{source}")
            except Exception:
                pass
            try:
                self.bus.set_input("cmd_hardware_awake", 0, source=f"HW_AWAKE_{source}_ACK")
            except Exception:
                pass
            if ensure:
                self._ensure_connected()
        except Exception as exc:
            self.logger.debug("request_hardware_awake failed source=%s error=%s", source, exc)

    def _ensure_connected(self) -> None:
        """Nawiązuje połączenie z PoKeys jeśli system jest aktywny a hardware uśpiony."""
        with self._lock:
            if self.pokeys.is_all_connected():
                if self._hardware_logical_sleep:
                    self._hardware_logical_sleep = False
                    self.pokeys.logical_wake()
                    try:
                        self.bus.set_input("hardware_sleep", 0, source="HW_BRIDGE")
                    except Exception:
                        pass
                    # Jeśli budzimy przez ensure_connected, to znaczy że system jest aktywny.
                    # Ale nie ustawiamy FAST_SAMPLE automatycznie w logical_wake.
                    # Pętla _run lub jawne metody ustawią stan.
                return
            
            # Cooldown 5s stosować wyłącznie po błędzie connect,
            # nie po normalnym IDLE disconnect.
            now = time.time() * 1000
            if self._last_connect_failed:
                if now - self._reconnect_cooldown_ms < 5000:
                    return
            
            self._reconnect_cooldown_ms = now
            
            lib_path = self._get_lib_path()
            self.logger.info("ZASADA SNAJPERA: Wybudzanie hardware (realtime required)...")
            self._hardware_logical_sleep = False
            self._init_devices(lib_path)
            
            connected_count = self.pokeys.connected_count()
            
            # Sprawdzamy czy wszystkie się połączyły
            if connected_count < len(self.devices):
                self._last_connect_failed = True
            else:
                self._last_connect_failed = False
                
            self.bus.set_input("hardware_connected", connected_count, source="HW_BRIDGE")
            if connected_count > 0 and not self._startup_i2c_test_done:
                self._run_startup_i2c_test_once()

    def _run_startup_i2c_test_once(self) -> None:
        """Jednorazowy test PoKeys BUS/I2C przy starcie runtime.

        To jest test startowy, nie pętla. Ma dać jasny ślad w logu, że
        I2C/PoSensors są realnie sprawdzane przez core/tarzanPoKeys.py.
        """
        self._startup_i2c_test_done = True
        try:
            self.logger.info("STARTUP_I2C_TEST begin")
            self.pokeys.begin_full_diagnostics("startup")
            play_scan = self.pokeys.scan_i2c_once("PLAY")
            rec_scan = self.pokeys.scan_i2c_once("REC")
            try:
                posensors = self.pokeys.read_posensors_once("PLAY")
            except Exception as exc:
                posensors = {"ok": False, "error": str(exc)}
            
            # Koniec testu startowego
            self.pokeys.end_active_state()

            play_addrs = play_scan.get("addresses") or play_scan.get("found") or []
            rec_addrs = rec_scan.get("addresses") or rec_scan.get("found") or []
            ok = bool(play_scan.get("ok") or rec_scan.get("ok"))
            if play_addrs or rec_addrs:
                ok = True

            try:
                self.bus.set_input("i2c_bus", 1 if ok else 0, source="HW.STARTUP_I2C")
                if play_addrs:
                    self.bus.set_input("i2c_play_addresses", ",".join(f"0x{int(x):02X}" for x in play_addrs), source="HW.STARTUP_I2C")
                if rec_addrs:
                    self.bus.set_input("i2c_rec_addresses", ",".join(f"0x{int(x):02X}" for x in rec_addrs), source="HW.STARTUP_I2C")
            except Exception:
                pass

            self.logger.info(
                "STARTUP_I2C_TEST result ok=%s PLAY=%s REC=%s PoSensors=%s",
                ok,
                ",".join(f"0x{int(x):02X}" for x in play_addrs) or "none",
                ",".join(f"0x{int(x):02X}" for x in rec_addrs) or "none",
                bool(isinstance(posensors, dict) and posensors.get("ok")),
            )
        except Exception as exc:
            self._startup_i2c_test_error = str(exc)
            self.logger.warning("STARTUP_I2C_TEST failed: %s", exc)

    def _ensure_disconnected(self) -> None:
        """Przełącza hardware w IDLE bez fizycznego zamykania PoKeys.

        Poprzednia wersja wykonywała PK_DisconnectDevice po grace period.
        Runtime pokazał core-dump w libusb/hid_close podczas USB SLEEP.
        Dlatego IDLE oznacza teraz sen logiczny: brak pollingu, brak testów
        w pętli, uchwyty PoKeys zostają stabilne do STOP usługi.
        """
        with self._lock:
            if all(dev is None for dev in self.devices.values()):
                return
            if self._hardware_logical_sleep:
                return

            self._hardware_logical_sleep = True
            self._last_connect_failed = False
            self.logger.info("ZASADA SNAJPERA: Hardware przechodzi w tryb uśpienia logicznego (grace period end)...")
            self.pokeys.logical_idle()
            try:
                self.bus.set_input("hardware_sleep", 1, source="HW_BRIDGE")
            except Exception:
                pass

    def _is_system_active(self) -> bool:
        """Szybki test aktywności systemu dla adaptacyjnego pollingu.

        Zasada: sama obecność PAR/EHR/Nextiona nie budzi PoKeys. Budzi tylko
        jawny strzał Snajpera, PLAY/REC, tryb wykonawczy albo realny ruch osi.
        """
        try:
            now = time.time() * 1000.0
            if int(getattr(self, "_hardware_batch_depth", 0) or 0) > 0:
                return True
            if now < float(self._hardware_awake_until_ms):
                return True

            cmd = self.bus.read("cmd_hardware_awake", 0)
            active_mode = self.bus.read("active_mode", "tM")
            transport = self.bus.read("transport_state", "STOP")
            owner = self.bus.read("control_owner", "TSP_BOOT")
            if self._snajper_policy.runtime_requires_realtime(
                active_mode=active_mode,
                transport_state=transport,
                control_owner=owner,
                cmd_hardware_awake=cmd,
            ):
                if self._snajper_policy.truthy(cmd):
                    self.request_hardware_awake(source="SIGNALBUS_CMD", grace_ms=self._snajper_policy.grace_ms_for("default"), ensure=False, action_type="CONNECT_ONLY")
                return True

            # Realtime z ModeLogic jest pomocniczy. Nie może zostać wiecznie
            # przyklejony po krótkim teście LKS/PAR.
            if int(self.bus.read("hardware_realtime_required", 0) or 0) == 1:
                # Jeżeli nie ma już transportu/trybu/impulsu i lokalne okno wygasło,
                # gasimy stan, żeby PoKeys mógł zasnąć.
                try:
                    self.bus.set_input("hardware_realtime_required", 0, source="HW_IDLE_EXPIRE")
                except Exception:
                    pass
                return False

            return False
        except Exception:
            # Błąd odczytu nie może wybudzać PoKeys w IDLE.
            return False

    def _handle_manual_generator(self) -> bool:
        """Generuje impulsy STEP w trybie manualnym na podstawie kierunków w SignalBus."""
        if self.bus.read("active_mode", "tM") != "tM":
            return False
            
        # Tylko jeśli PAR lub LKS ma kontrolę
        owner = self.bus.read("control_owner", "TSP_BOOT")
        if owner not in {"PAR_LIVE", "TSP_SERVICE", "LKS_DIAGNOSTIC"}:
            return False

        has_any_motion = False
        from core.tarzanZmienneSygnalowe import LISTA_NAZW_OSI
        for ax_name in LISTA_NAZW_OSI:
            prefix = f"axis_{ax_name}"
            dir_val = int(self.bus.read(f"{prefix}_dir", 0))
            
            if dir_val != 0:
                has_any_motion = True
                # Generujemy impuls co N obiegów pętli (uproszczona prędkość)
                # W realnym systemie częstotliwość byłaby sterowana rrp_speed_mul
                step_signal = f"{prefix}_step"
                # Wpisujemy do SignalBus - to wywoła write() w tym samym bridge'u
                self.bus.write_output(step_signal, 1, source="HW_MANUAL_GEN")
                self.bus.write_output(step_signal, 0, source="HW_MANUAL_GEN")
        
        return has_any_motion

    def _poll_hardware(self, is_active: bool = True) -> None:
        """Jednorazowy odczyt wejść. W IDLE nie dotykamy PoKeys."""
        if not is_active or self._hardware_logical_sleep:
            return

        with self._lock:
            # ZASADA SNAJPERA: pętla pollingu NIE MOŻE sama wybudzać hardware.
            # Jeśli stan to IDLE, po prostu skipujemy polling do czasu jawnej akcji.
            if self.pokeys.state == "IDLE":
                return

            # W stanach diagnostycznych polling GPIO/Analog może być potrzebny,
            # ale tylko jeśli jawnie to dopuszczamy.
            if self.pokeys.state not in ["FAST_SAMPLE", "EXEC", "POINT_TEST", "FULL_DIAGNOSTICS"]:
                return

            def _update(name: str, val: Any, source: str) -> None:
                if self._input_cache.get(name) != val:
                    self._input_cache[name] = val
                    self.bus.set_input(name, val, source=source, forced=True)

            self.pokeys.poll_gpio_inputs_once(self._gpio_inputs, _update)
            self.pokeys.poll_analog_inputs_once(self._analog_inputs, _update)

            # Potencjometry RRP są wejściami analogowymi; czytamy je tylko w aktywnym oknie,
            # nigdy w bezczynnej pętli IDLE.
            try:
                self.pokeys.test_potentiometers_once(_update)
            except Exception as exc:
                self.logger.debug("RRP pots one-shot read skipped: %s", exc)

            # Pulse Engine tylko w aktywnym oknie ruchu/testu.
            play = self.devices.get("PLAY")
            if play is not None:
                self._poll_pulse_engine_status(play)


    def _poll_pulse_engine_status(self, device: Any) -> None:
        """Czyta READY, ALARM i pozycję przez core/tarzanPoKeys.py."""
        try:
            status = self.pokeys.get_pulse_engine_status(device)
            if not status.get("ok"):
                err = status.get("error")
                if err:
                    self.logger.debug("Pulse Engine poll error: %s", err)
                return

            from core.tarzanZmienneSygnalowe import LISTA_NAZW_OSI

            axes = status.get("axes", {}) or {}
            for idx, ax_name in enumerate(LISTA_NAZW_OSI):
                if idx >= 8:
                    break
                axis = axes.get(str(idx), {}) if isinstance(axes, dict) else {}
                axis_state = int(axis.get("state", 0) or 0)
                axis_pos = int(axis.get("pos", 0) or 0)
                is_enabled = (axis_state & 0x01) == 0x01
                is_running = (axis_state & 0x02) == 0x02
                has_alarm = (axis_state & 0x04) == 0x04
                axis_ready = 1 if (is_enabled and not has_alarm) else 0
                self._update_if_changed(f"axis_{ax_name}_ready", axis_ready, source="HW.PE", is_input=True)
                self._update_if_changed(f"axis_{ax_name}_alarm", 1 if has_alarm else 0, source="HW.PE", is_input=True)
                self._update_if_changed(f"axis_{ax_name}_running", 1 if is_running else 0, source="HW.PE", is_input=True)
                self._update_if_changed(f"axis_{ax_name}_pos", axis_pos, source="HW.PE", force_signal=True)
        except Exception as e:
            self.logger.debug("Pulse Engine poll error: %s", e)

    def _update_if_changed(self, name: str, value: Any, source: str, is_input: bool = False, force_signal: bool = False) -> None:
        """Pomocnik aktualizujący sygnał tylko przy realnej zmianie hardware."""
        if self._input_cache.get(name) != value:
            self._input_cache[name] = value
            if is_input:
                self.bus.set_input(name, value, source=source)
            elif force_signal:
                self.bus.force_signal(name, value, source=source)
            else:
                self.bus.write_output(name, value, source=source)


    # ------------------------------------------------------------------
    # LKS-N5 point tests przez aktywny HardwareBridge
    # ------------------------------------------------------------------

    def _device_ready(self, board: str) -> Optional[Any]:
        board = str(board).upper()
        device = self.pokeys.get_device(board)
        return device if self.running and device is not None else None

    def _device_identity_text(self, board: str, device: Any) -> str:
        return self.pokeys.identity_text(board, device)

    def _lks_test_result(self, component: str, ok: bool, detail: str = "", error: str = "", supported: bool = True) -> Dict[str, Any]:
        return {"component": str(component), "ok": bool(ok), "detail": str(detail or ""), "error": str(error or ""), "supported": bool(supported)}

    def _lks_refresh_device(self, device: Any) -> None:
        self.pokeys.refresh_device(device)

    def _lcd_text(self, value: str, width: int = 16) -> str:
        repl = str(value)
        for src, dst in (("ł", "l"), ("Ł", "L"), ("ó", "o"), ("Ó", "O"), ("ą", "a"), ("ę", "e"), ("ś", "s"), ("ż", "z"), ("ź", "z"), ("ń", "n"), ("ć", "c")):
            repl = repl.replace(src, dst)
        return repl[:width].ljust(width)


    def _lks_lcd_init(self, device: Any) -> None:
        # Stary bezpośredni tor LCD został przeniesiony do core/tarzanPoKeys.py.
        self.pokeys.lcd_init(device)


    def _lks_lcd_write_lines(self, device: Any, line1: str, line2: str) -> None:
        # Stary bezpośredni tor LCD został przeniesiony do core/tarzanPoKeys.py.
        self.pokeys.lcd_write_lines(device, line1, line2)


    def _lks_test_lcd_1602(self, visible: bool = True) -> Dict[str, Any]:
        return self.pokeys.test_lcd_1602_once(visible=visible)

    _MATRIX_FONT_5X7: Dict[str, List[int]] = {
        " ": [0, 0, 0, 0, 0],
        "A": [0x7E, 0x11, 0x11, 0x11, 0x7E], "B": [0x7F, 0x49, 0x49, 0x49, 0x36],
        "E": [0x7F, 0x49, 0x49, 0x49, 0x41], "K": [0x7F, 0x08, 0x14, 0x22, 0x41],
        "L": [0x7F, 0x40, 0x40, 0x40, 0x40], "O": [0x3E, 0x41, 0x41, 0x41, 0x3E],
        "S": [0x46, 0x49, 0x49, 0x49, 0x31], "T": [0x01, 0x01, 0x7F, 0x01, 0x01],
        "Z": [0x61, 0x51, 0x49, 0x45, 0x43], "0": [0x3E, 0x45, 0x49, 0x51, 0x3E],
        "1": [0x00, 0x42, 0x7F, 0x40, 0x00], "2": [0x62, 0x51, 0x49, 0x49, 0x46],
        "3": [0x22, 0x41, 0x49, 0x49, 0x36], "4": [0x18, 0x14, 0x12, 0x7F, 0x10],
        "5": [0x27, 0x45, 0x45, 0x45, 0x39], "6": [0x3C, 0x4A, 0x49, 0x49, 0x30],
        "7": [0x01, 0x71, 0x09, 0x05, 0x03], "8": [0x36, 0x49, 0x49, 0x49, 0x36],
        "9": [0x06, 0x49, 0x49, 0x29, 0x1E],
    }

    def _matrix_rows_from_text(self, text_value: str) -> List[int]:
        cols: List[int] = []
        for ch in str(text_value).upper():
            cols.extend(self._MATRIX_FONT_5X7.get(ch, self._MATRIX_FONT_5X7[" "]))
            cols.append(0)
        cols = (cols + [0] * 8)[:8]
        rows: List[int] = []
        for row in range(8):
            value = 0
            for col, col_value in enumerate(cols):
                if int(col_value) & (1 << row):
                    value |= 1 << col
            rows.append(value & 0xFF)
        return rows


    def _lks_matrix_write_frame(self, device: Any, rows: Sequence[int]) -> None:
        # Stary bezpośredni tor MatrixLED został przeniesiony do core/tarzanPoKeys.py.
        self.pokeys.matrix_write_frame(device, rows)


    def _lks_test_matrix_led(self, visible: bool = True) -> Dict[str, Any]:
        return self.pokeys.test_matrix_led_once(visible=visible)

    def _lks_read_pin(self, device: Any, pin: int) -> int:
        return self.pokeys.read_pin(device, pin)

    def _lks_set_led_pin(self, device: Any, pin: int, value: int) -> None:
        self.pokeys.set_digital_output(device, pin, value)

    def _lks_test_f_led(self, visible: bool = True) -> Dict[str, Any]:
        device = self._device_ready("REC")
        pins = [46, 48, 50, 52]
        if device is None:
            return self._lks_test_result("f_led", False, error="REC not connected")
        try:
            if visible:
                try:
                    for pin in pins:
                        self._lks_set_led_pin(device, pin, 0)
                    for pin in pins:
                        self._lks_set_led_pin(device, pin, 1)
                        time.sleep(0.18)
                        self._lks_set_led_pin(device, pin, 0)
                finally:
                    for pin in pins:
                        try:
                            self._lks_set_led_pin(device, pin, 0)
                        except Exception:
                            pass
            return self._lks_test_result("f_led", True, detail="REC P46/P48/P50/P52")
        except Exception as exc:
            return self._lks_test_result("f_led", False, error=str(exc))

    def _lks_test_f_buttons(self, visible: bool = True) -> Dict[str, Any]:
        device = self._device_ready("REC")
        pins = [45, 47, 49, 51]
        if device is None:
            return self._lks_test_result("f_button", False, error="REC not connected")
        try:
            base = {pin: self._lks_read_pin(device, pin) for pin in pins}
            if visible:
                end = time.time() + 2.5
                while time.time() < end:
                    for pin in pins:
                        if self._lks_read_pin(device, pin) != base[pin]:
                            return self._lks_test_result("f_button", True, detail=f"REC P{pin} changed")
                    time.sleep(0.05)
                return self._lks_test_result("f_button", False, detail=str(base), error="nie wykryto naciśnięcia F1-F4")
            return self._lks_test_result("f_button", True, detail=str(base))
        except Exception as exc:
            return self._lks_test_result("f_button", False, error=str(exc))


    def _lks_test_keypad(self, visible: bool = False) -> Dict[str, Any]:
        return self.pokeys.read_keypad_once()


    def _lks_i2c_scan_summary(self) -> Dict[str, Any]:
        """Jednorazowy, bezpieczny odczyt stanu PoKeys BUS/I2C.

        Wynik OK nie może opierać się na samym CP2102/USB-UART.
        Zielone dla i2c_bus wolno dać tylko po realnym potwierdzeniu:
        - adresów PoKeys BUS/I2C,
        - albo poprawnego odczytu PoSensors,
        - albo poprawnego realnego testu czujnika laser/light_laser.
        """
        serial_links = sorted(glob.glob("/dev/serial/by-id/*"))
        tty_links = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
        usb_detail = "USB=" + (",".join(serial_links[:3] or tty_links[:3]) or "no-tty")

        def _scan(board: str) -> Dict[str, Any]:
            try:
                data = self.pokeys.scan_i2c_once(board)
                return data if isinstance(data, dict) else {"ok": False, "raw": data}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

        play = _scan("PLAY")
        rec = _scan("REC")
        play_found = list(play.get("addresses") or play.get("found") or [])
        rec_found = list(rec.get("addresses") or rec.get("found") or [])
        bus_scan_ok = bool((play.get("ok") or rec.get("ok")) and (play_found or rec_found))

        posensors: Dict[str, Any]
        try:
            posensors = self.pokeys.read_posensors_once("PLAY")
            if not isinstance(posensors, dict):
                posensors = {"ok": False, "raw": posensors}
        except Exception as exc:
            posensors = {"ok": False, "error": str(exc)}
        posensors_ok = bool(posensors.get("ok"))

        laser_ok = False
        laser_detail = ""
        try:
            # ETAP 1R: Realny test I2C czujnika TSL25911 (Light Laser)
            laser = self._lks_test_tsl25911("REC", 0x29)
            laser_ok = bool(laser.get("ok"))
            laser_detail = str(laser.get("detail") or laser.get("error") or "")[:180]
        except Exception as exc:
            laser_detail = f"laser_test_error={exc}"

        play_txt = ",".join(f"0x{int(x):02X}" for x in play_found) or "none"
        rec_txt = ",".join(f"0x{int(x):02X}" for x in rec_found) or "none"
        ok = bool(bus_scan_ok or posensors_ok or laser_ok)
        detail = (
            f"PLAY={play_txt} REC={rec_txt}; "
            f"PoSensors={posensors_ok}; light_laser={laser_ok}; {usb_detail}"
        )
        errors = []
        if not bus_scan_ok:
            errors.append(f"BUS_SCAN_NO_ADDR PLAY={play} REC={rec}")
        if not posensors_ok:
            errors.append(f"PoSensors={str(posensors)[:160]}")
        if not laser_ok:
            errors.append(f"light_laser={laser_detail or 'NO_ACK'}")
        return {
            "ok": ok,
            "detail": detail,
            "error": " | ".join(errors),
            "play": play,
            "rec": rec,
            "posensors": posensors,
            "light_laser_ok": laser_ok,
            "usb_detail": usb_detail,
        }

    def _lks_test_i2c_bus(self) -> Dict[str, Any]:
        summary = self._lks_i2c_scan_summary()
        if summary.get("ok"):
            return self._lks_test_result("i2c_bus", True, detail="BUS_REAL_ACK; " + str(summary.get("detail", "")))
        return self._lks_test_result("i2c_bus", False, detail=str(summary.get("detail", "")), error=str(summary.get("error", "I2C_BUS_FAIL")))

    def _lks_test_nextion7(self) -> Dict[str, Any]:
        """Bezpieczny test obecności portu Nextion 7 / USB-UART bez otwierania HMI."""
        candidates: List[str] = []
        try:
            cfg_path = Path(__file__).resolve().parents[1] / "data" / "nextion" / "nextion_ports.json"
            if cfg_path.exists():
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                n7 = cfg.get("nextion_7", {}) if isinstance(cfg, dict) else {}
                port = str(n7.get("port", "") or "")
                if port and not port.upper().startswith("COM"):
                    candidates.append(port)
        except Exception:
            pass
        candidates.extend(sorted(glob.glob("/dev/serial/by-id/*Nextion*7*") + glob.glob("/dev/serial/by-id/*NX8048*")))
        candidates.extend(sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")))
        existing = []
        seen = set()
        for item in candidates:
            if item in seen:
                continue
            seen.add(item)
            if Path(item).exists():
                existing.append(item)
        if existing:
            return self._lks_test_result("next_7", True, detail=", ".join(existing[:3]))
        return self._lks_test_result("next_7", False, detail=", ".join(candidates[:3]), error="brak portu Nextion 7 na miniPC")


    def _lks_test_tsl25911(self, board: str = "REC", addr7: int = 0x29) -> Dict[str, Any]:
        """Realny test czujnika Light Laser (TSL25911) zgodnie z dokumentacją.
        Sprawdza rejestr ID (0x12) -> oczekiwane 0x50.
        """
        try:
            # Rejestr ID dla TSL25911 to 0x12 (0x92 z command bit 10100000 | 0x12)
            # W PoKeys i2c_write_read: board, addr7, write_bytes, read_len
            # Command bit (0xA0) + register (0x12) = 0xB2
            result = self.pokeys.i2c_write_read(board, addr7, [0xB2], 1)
            if not result or not isinstance(result, list) or len(result) < 1:
                return self._lks_test_result("light_laser", False, error="I2C_READ_FAIL")
            
            device_id = result[0]
            # TSL2591 0x50, TSL25911 0x50
            if device_id == 0x50:
                return self._lks_test_result("light_laser", True, detail=f"TSL25911_ACK ID=0x{device_id:02X}")
            else:
                return self._lks_test_result("light_laser", False, detail=f"ID=0x{device_id:02X}", error="WRONG_DEVICE_ID")
        except Exception as exc:
            return self._lks_test_result("light_laser", False, error=str(exc))

    def _lks_test_bh1750(self, address: int = 0x5C) -> Dict[str, Any]:
        result = self.pokeys.read_bh1750_lux_once(board="PLAY", addr7=address)
        if not result.get("ok"):
            return self._lks_test_result("light_bh1750", False, error=str(result.get("error", "BH1750 failed")))
        return self._lks_test_result("light_bh1750", True, detail=f"0x{int(result.get('addr', address)):02X} raw={result.get('raw')} lux={float(result.get('lux', 0.0)):.2f}")

    def _normalize_lks_component(self, component: str) -> str:
        raw = str(component or "").strip()
        aliases = {
            "nextion7": "next_7",
            "nextion_7": "next_7",
            "n7": "next_7",
            "pokeys_play": "pok_play",
            "pokeys_rec": "pok_rec",
            "play": "pok_play",
            "rec": "pok_rec",
            "lcd": "lcd_1602",
            "matrix": "matrix_led",
            "f_buttons": "f_button",
            "f_leds": "f_led",
            "bh1750": "light_bh1750",
            "laser": "light_laser",
            "i2c": "i2c_bus",
        }
        return aliases.get(raw, raw)

    def _lks_status_from_bus(self, name: str) -> Optional[Dict[str, Any]]:
        """Lekki status logiczny bez budzenia PoKeys."""
        try:
            if name == "linux_sys":
                return self._lks_test_result(name, True, detail="Linux/runtime active")
            if name == "snajper_sys":
                return self._lks_test_result(name, True, detail="SignalBus/Snajper active")
            if name == "take_sys":
                return self._lks_test_result(name, True, detail=str(self.bus.read("transport_state", "STOP")))
            if name == "par_sys":
                state = str(self.bus.read("par_state", self.bus.read("par_status", "NOT_CONNECTED")))
                ok = state.upper() in {"CONNECTED", "PAR_CONNECTED", "ACTIVE", "LIVE"}
                return self._lks_test_result(name, ok, detail=state, error="PAR not connected" if not ok else "")
            if name == "ehr_sys":
                state = str(self.bus.read("ehr_state", self.bus.read("ehr_status", "NOT_CONNECTED")))
                ok = state.upper() in {"CONNECTED", "EHR_CONNECTED", "ACTIVE", "LIVE"}
                return self._lks_test_result(name, ok, detail=state, error="EHR not connected" if not ok else "")
            if name in {"cam_main", "cam_track"}:
                nodes = sorted(glob.glob("/dev/video*"))
                need = 1 if name == "cam_main" else 2
                ok = len(nodes) >= need
                return self._lks_test_result(name, ok, detail=", ".join(nodes[:4]), error="no camera node" if not ok else "")
            if name in {"rrp", "sok_poz", "sok_pion", "kam_poz", "kam_pion", "kam_ostr", "kam_poch", "ram_poziom", "ram_pion", "kranc", "level_xyz", "shock_alarm", "light_laser"}:
                # Te elementy sprawdza konserwatywna diagnostyka read-only poniżej.
                return None
        except Exception as exc:
            return self._lks_test_result(name, False, error=str(exc))
        return None

    def _lks_matrix_error(self, component: str, code: str, detail: str = "", supported: bool = True) -> Dict[str, Any]:
        return self._lks_test_result(component, False, detail=str(detail or ""), error=str(code or "FAIL"), supported=supported)

    def _lks_matrix_signals(self, entry: Mapping[str, Any]) -> List[TarzanSygnal]:
        component = str(entry.get("component") or "")
        result: List[TarzanSygnal] = []
        missing: List[str] = []
        for name in entry.get("signals", ()) or ():
            if not name:
                continue
            sig = WSZYSTKIE_SYGNALY.get(str(name))
            if sig is None:
                missing.append(str(name))
            else:
                result.append(sig)
        if missing:
            raise RuntimeError("BAD_SIGNAL_MAP missing=" + ",".join(missing))
        return result

    def _lks_board_ready(self, board: str) -> tuple[Optional[Any], str]:
        name = str(board or "").upper()
        if name == "CNC":
            dev = self._device_ready("PLAY") or self._device_ready("REC")
            return dev, "CNC/PULSE via " + ("PLAY/REC" if dev is not None else "NO_DEVICE")
        dev = self._device_ready(name)
        return dev, name

    def _lks_test_pokeys_device_matrix(self, component: str, entry: Mapping[str, Any]) -> Dict[str, Any]:
        board = str(entry.get("board") or "").upper()
        dev = self._device_ready(board)
        if dev is None:
            return self._lks_matrix_error(component, f"NO_DEVICE {board}")
        return self._lks_test_result(component, True, detail=self._device_identity_text(board, dev))

    def _lks_test_signal_reads_matrix(self, component: str, entry: Mapping[str, Any]) -> Dict[str, Any]:
        signals = self._lks_matrix_signals({**dict(entry), "component": component})
        if not signals:
            return self._lks_matrix_error(component, "BAD_SIGNAL_MAP no signals")
        values: Dict[str, Any] = {}
        ack_boards: Dict[str, bool] = {}
        errors: List[str] = []
        for sig in signals:
            board = str(sig.plytka or "").upper()
            dev, board_label = self._lks_board_ready(board)
            if dev is None:
                errors.append(f"{sig.nazwa}:NO_DEVICE:{board_label}")
                continue
            ack_boards[board_label] = True
            try:
                typ = str(sig.typ or "").upper()
                direction = str(sig.kierunek or "").upper()
                hw = str(sig.hardware_function or "").upper()
                if sig.pin is None:
                    # Funkcja specjalna/CNC bez numeru pinu: potwierdzamy mapę i obecność PoKeys.
                    values[sig.nazwa] = f"ACK:{board_label}:{hw}:{typ}:{direction}"
                elif typ == "ANALOG" or hw == "ANALOG":
                    values[sig.nazwa] = self.pokeys.read_analog_pin(dev, int(sig.pin))
                elif direction == "IN" or typ in {"LH", "CTR"}:
                    values[sig.nazwa] = self.pokeys.read_pin(dev, int(sig.pin))
                else:
                    # OUT w point-test osi: bez zapisu i bez ruchu. ACK = urządzenie + konfiguracja/mapa.
                    values[sig.nazwa] = f"ACK:NO_WRITE:P{int(sig.pin)}:{hw}:{typ}:{direction}"
            except Exception as exc:
                errors.append(f"{sig.nazwa}:{exc}")
        ok = bool(values) and not errors
        detail = "; ".join(f"{k}={v}" for k, v in list(values.items())[:10])
        if len(values) > 10:
            detail += f"; +{len(values)-10} signals"
        return self._lks_test_result(component, ok, detail=detail, error="; ".join(errors))

    def _lks_axis_expected_config_errors(self, component: str, entry: Mapping[str, Any], signals: List[TarzanSygnal]) -> List[str]:
        by_name = {sig.nazwa: sig for sig in signals}
        expected_config = entry.get("expected_config") or {}
        errors: List[str] = []
        for name, expected in expected_config.items():
            sig = by_name.get(str(name))
            if sig is None:
                errors.append(f"{name}:BAD_SIGNAL_MAP")
                continue
            checks = (
                ("plytka", "BAD_BOARD"),
                ("pin", "BAD_PIN_CONFIG"),
                ("kanal", "BAD_CHANNEL"),
                ("typ", "BAD_SIGNAL_TYPE"),
                ("kierunek", "BAD_DIRECTION"),
                ("hardware_function", "BAD_HW_FUNCTION"),
                ("pin_is_fixed", "BAD_FIXED_PIN"),
            )
            for field, code in checks:
                if field not in expected:
                    continue
                actual_value = getattr(sig, field, None)
                expected_value = expected.get(field)
                if actual_value != expected_value:
                    errors.append(f"{name}:{code}:{field}={actual_value!r}:expected={expected_value!r}")
        if not expected_config:
            errors.append(f"{component}:NO_EXPECTED_AXIS_CONFIG")
        return errors

    def _lks_test_axis_matrix_no_motion(self, component: str, entry: Mapping[str, Any]) -> Dict[str, Any]:
        signals = self._lks_matrix_signals({**dict(entry), "component": component})
        if not signals:
            return self._lks_matrix_error(component, "BAD_SIGNAL_MAP no axis signals")
        errors: List[str] = []
        ack: List[str] = []

        # Najpierw twarda kontrola mapy osi: pin/kanał/kierunek/typ/funkcja muszą zgadzać się
        # z oczekiwaną konfiguracją matrix. Jeżeli sygnały osi rozjadą się w mapie, test ma FAIL.
        errors.extend(self._lks_axis_expected_config_errors(component, entry, signals))

        # Drugi obowiązkowy próg dla osi: ABC + realne ACK toru CNC/PoExtBus/Pulse Engine.
        # Bez tego sama zgodność pinów w mapie nie wystarcza.
        try:
            if hasattr(self.pokeys, "test_cnc_axis_link_once"):
                cnc = self.pokeys.test_cnc_axis_link_once(entry.get("signals", ()))
                if cnc.get("ok"):
                    ack.append("CNC_LINK_OK:ABC+PULSE_ENGINE+POEXTBUS")
                else:
                    for err in cnc.get("errors", []) or ["CNC_LINK_FAIL"]:
                        errors.append(f"CNC:{err}")
                    for warn in cnc.get("warnings", []) or []:
                        ack.append(f"CNC_WARN:{warn}")
            else:
                errors.append("CNC:POKEYS_CNC_LINK_TEST_MISSING")
        except Exception as exc:
            errors.append(f"CNC_LINK_ERROR:{exc}")

        for sig in signals:
            board = str(sig.plytka or "").upper()
            dev, board_label = self._lks_board_ready(board)
            if dev is None:
                errors.append(f"{sig.nazwa}:NO_DEVICE:{board_label}")
                continue
            hw = str(sig.hardware_function or "").upper()
            typ = str(sig.typ or "").upper()
            direction = str(sig.kierunek or "").upper()
            if direction == "OUT" and hw in {"PULSE_ENGINE", "GPIO", "PWM"}:
                # Świadomie bez DigitalIOSet/PulseStart. To test toru/mapy/ACK, nie ruch.
                pin_text = "PIN_NONE" if sig.pin is None else f"P{int(sig.pin)}"
                channel_text = str(sig.kanal or "")
                ack.append(f"{sig.nazwa}:PINCFG_OK:{board_label}:{pin_text}:{channel_text}:{hw}:{typ}:{direction}:NO_MOTION")
            elif direction == "IN" and sig.pin is not None:
                try:
                    value = self.pokeys.read_pin(dev, int(sig.pin))
                    ack.append(f"{sig.nazwa}:PINCFG_OK:P{int(sig.pin)}:{value}")
                except Exception as exc:
                    errors.append(f"{sig.nazwa}:{exc}")
            else:
                pin_text = "PIN_NONE" if sig.pin is None else f"P{int(sig.pin)}"
                ack.append(f"{sig.nazwa}:PINCFG_OK:{board_label}:{pin_text}:{hw}:{typ}:{direction}")
        ok = bool(ack) and not errors
        return self._lks_test_result(component, ok, detail="; ".join(ack[:8]), error="; ".join(errors))

    def _lks_test_runtime_matrix(self, component: str, entry: Mapping[str, Any]) -> Dict[str, Any]:
        method = str(entry.get("method") or "")
        try:
            if method == "linux_runtime_alive":
                return self._lks_test_result(component, bool(self.running), detail=f"pid={os.getpid()} running={self.running}", error="RUNTIME_NOT_RUNNING" if not self.running else "")
            if method == "snajper_alive":
                return self._lks_test_result(component, self._snajper_policy is not None, detail="Snajper policy active")
            if method == "take_state":
                state = str(self.bus.read("transport_state", "STOP"))
                return self._lks_test_result(component, True, detail=state)
            if method == "par_tsp_client":
                state = str(self.bus.read("par_state", self.bus.read("par_status", "NOT_CONNECTED")))
                ok = state.upper() in {"CONNECTED", "PAR_CONNECTED", "ACTIVE", "LIVE", "AVAILABLE"}
                return self._lks_test_result(component, ok, detail=state, error="RUNTIME_NOT_CONNECTED" if not ok else "")
            if method == "ehr_tsp_client":
                state = str(self.bus.read("ehr_state", self.bus.read("ehr_status", "NOT_CONNECTED")))
                ok = state.upper() in {"CONNECTED", "EHR_CONNECTED", "ACTIVE", "LIVE", "AVAILABLE"}
                return self._lks_test_result(component, ok, detail=state, error="RUNTIME_NOT_CONNECTED" if not ok else "")
        except Exception as exc:
            return self._lks_matrix_error(component, "RUNTIME_ERROR", str(exc))
        return self._lks_matrix_error(component, "BAD_TEST_METHOD " + method)

    def _lks_test_usb_camera_matrix(self, component: str, entry: Mapping[str, Any]) -> Dict[str, Any]:
        nodes = sorted(glob.glob("/dev/video*"))
        index = int(entry.get("camera_index", 0) or 0)
        if len(nodes) <= index:
            return self._lks_matrix_error(component, "NO_DEVICE", ", ".join(nodes[:4]) or "no /dev/video*")
        node = nodes[index]
        try:
            flags = os.O_RDONLY
            if hasattr(os, "O_NONBLOCK"):
                flags |= os.O_NONBLOCK
            fd = os.open(node, flags)
            os.close(fd)
            return self._lks_test_result(component, True, detail=f"open {node} ACK")
        except Exception as exc:
            return self._lks_matrix_error(component, "USB_ERROR", f"{node}: {exc}")

    def _lks_test_xyz_matrix(self, component: str) -> Dict[str, Any]:
        try:
            data = self.pokeys.read_xyz_poksyg_once()
            return self._lks_test_result(component, bool(data.get("ok")), detail=str(data.get("values", data))[:240], error="; ".join(str(x) for x in data.get("errors", [])))
        except Exception as exc:
            return self._lks_matrix_error(component, "I2C_ERROR", str(exc))

    def _lks_execute_matrix_entry(self, component: str, entry: Mapping[str, Any], visible: bool = True) -> Dict[str, Any]:
        tester = str(entry.get("tester") or "")
        method = str(entry.get("method") or "")
        if tester == "runtime_state":
            return self._lks_test_runtime_matrix(component, entry)
        if tester == "usb_camera":
            return self._lks_test_usb_camera_matrix(component, entry)
        if tester == "nextion_serial" or method == "nextion7_port_exists":
            return self._lks_test_nextion7()
        if tester == "poksyg_device":
            return self._lks_test_pokeys_device_matrix(component, entry)
        if method == "lcd_1602_ack":
            return self._lks_test_lcd_1602(visible=visible)
        if method == "matrix_led_ack":
            return self._lks_test_matrix_led(visible=visible)
        if method == "f_led_ack":
            return self._lks_test_f_led(visible=visible)
        if method == "keypad_read_ack":
            data = self._lks_test_keypad(visible=visible)
            if isinstance(data, dict) and "component" not in data:
                return self._lks_test_result(component, bool(data.get("ok")), detail=str(data)[:220], error=str(data.get("error", "") or ""))
            return data
        if method == "scan_i2c":
            return self._lks_test_i2c_bus()
        if method == "bh1750_read":
            return self._lks_test_bh1750()
        if method == "tsl25911_read_id":
            return self._lks_test_tsl25911("REC", 0x29)
        if method == "xyz_read":
            return self._lks_test_xyz_matrix(component)
        if tester == "poksyg_axis" or method == "axis_wiring_ack_no_motion":
            return self._lks_test_axis_matrix_no_motion(component, entry)
        if tester == "poksyg_signals" or method in {"read_input_signals", "read_analog_signals"}:
            return self._lks_test_signal_reads_matrix(component, entry)
        return self._lks_matrix_error(component, "BAD_TEST_METHOD " + method)

    def test_lks_component(self, component: str, visible: bool = True) -> Dict[str, Any]:
        """Punktowy test LKS-N5 wyłącznie przez LKS_TEST_MATRIX.

        Nie ma fallbacku do TarzanTspLksDiagnostics ani ręcznej whitelisty ikon.
        Brak wpisu w matrix = NO_TEST_MATRIX.
        """
        from core.TSP.tarzanTspLksTestMatrix import MATRIX_ERRORS, LKS_TEST_MATRIX

        name = self._normalize_lks_component(component)
        if MATRIX_ERRORS:
            return self._lks_matrix_error(name, "BAD_TEST_MATRIX", "; ".join(MATRIX_ERRORS[:6]))
        entry = LKS_TEST_MATRIX.get(name)
        if entry is None:
            return self._lks_matrix_error(name, "NO_TEST_MATRIX", supported=False)

        needs_pokeys = str(entry.get("tester") or "").startswith("poksyg") or str(entry.get("method") or "") in {
            "lcd_1602_ack", "matrix_led_ack", "f_led_ack", "keypad_read_ack", "scan_i2c", "bh1750_read", "xyz_read",
            "tsl25911_read_id"
        }
        if needs_pokeys:
            self.request_hardware_awake(
                source=f"LKS_TEST_MATRIX_{name}",
                grace_ms=self._snajper_policy.grace_ms_for("lks"),
                ensure=True,
                action_type="POINT_TEST",
            )

        with self._lock:
            if needs_pokeys:
                self.pokeys.begin_point_test(name)
            try:
                result = self._lks_execute_matrix_entry(name, entry, visible=visible)
                result.setdefault("component", name)
                result["matrix"] = True
                result["tester"] = str(entry.get("tester") or "")
                result["method"] = str(entry.get("method") or "")
                result["expect"] = str(entry.get("expect") or "")
                
                # Wymagany log DONE dla kliku/testu punktowego
                ok = bool(result.get("ok", False))
                detail = str(result.get("detail", "") or result.get("error", "") or "")
                self.logger.info("LKS-N5 POINT TEST DONE component=%s ok=%s %s", name, ok, detail[:220])
                
                return result
            finally:
                if needs_pokeys:
                    if self._hardware_batch_depth == 0:
                        self.pokeys.end_active_state()
                    else:
                        self.pokeys.begin_full_diagnostics(self._hardware_batch_source or "batch")


    # ------------------------------------------------------------------
    # SignalBus LIVE Adapter Interface
    # ------------------------------------------------------------------

    def read(self, name: str) -> Any:
        """Odczyt sygnału bezpośrednio z hardware (jeśli to możliwe)."""
        # Dla optymalizacji większość odczytów i tak idzie z cache SignalBus,
        # który jest aktualizowany w _poll_hardware.
        return None

    def _write_par_lcd_signal_no_lock(self, name: str, value: Any, action_type: str = "EXEC", request_awake: bool = True) -> bool:
        """Wykonuje centralny zapis PAR -> miniPC -> LCD 1602 przez aktywny HardwareBridge (bez locka)."""
        mapping = {
            "par_lcd_play_line1": ("PLAY", 0),
            "par_lcd_play_line2": ("PLAY", 1),
            "par_lcd_rec_line1": ("REC", 0),
            "par_lcd_rec_line2": ("REC", 1),
            "par_lcd_line1": ("PLAY", 0),
            "par_lcd_line2": ("PLAY", 1),
        }
        target = mapping.get(name)
        if not target:
            return False
        
        if request_awake:
            # Wybudzamy hardware dla realnego zapisu PAR w trybie EXEC.
            self.request_hardware_awake(source=f"LCD_WRITE_{name}", action_type=action_type)
        
        board, idx = target
        text = self._lcd_text(str(value), 16)
        device = self.devices.get(board)
        if not device:
            self.logger.warning("HW LCD WRITE %s skipped: board not connected", board)
            return True
        try:
            self._lcd_lines.setdefault(board, ["", ""])[idx] = text
            line1, line2 = self._lcd_lines[board]
            self._lks_lcd_init(device)
            self._lks_lcd_write_lines(device, line1, line2)
            self.logger.info("HW LCD WRITE %s line%d='%s'", board, idx + 1, text)
        except Exception as exc:
            self.logger.warning("HW LCD WRITE %s line%d failed: %s", board, idx + 1, exc)
        return True

    def _parse_matrix_pattern_rows(self, value: Any) -> list[int]:
        """Parsuje pattern z PAR: 8 wierszy binarnych rozdzielonych '/' albo ';'."""
        text = str(value or "").strip()
        if not text:
            return [0] * 8
        text = text.replace(";", "/").replace(",", "/")
        parts = [p.strip() for p in text.split("/") if p.strip()]
        rows: list[int] = []
        for part in parts[:8]:
            bits = "".join(ch for ch in part if ch in "01")[:8].ljust(8, "0")
            rows.append(int(bits, 2))
        while len(rows) < 8:
            rows.append(0)
        return rows

    def _write_par_matrix_signal_no_lock(self, name: str, value: Any, action_type: str = "EXEC", request_awake: bool = True) -> bool:
        """Wykonuje PAR -> miniPC -> Matrix LED przez aktywny HardwareBridge (bez locka)."""
        if name != "par_matrix_pattern":
            return False
            
        if request_awake:
            # Wybudzamy hardware dla realnego zapisu PAR w trybie EXEC.
            self.request_hardware_awake(source="MATRIX_WRITE", action_type=action_type)
        
        rows = self._parse_matrix_pattern_rows(value)
        device = self.devices.get("REC")
        if not device:
            self.logger.warning("HW MATRIX WRITE skipped: REC board not connected")
            return True
        try:
            self._lks_matrix_write_frame(device, rows)
            self.logger.info("HW MATRIX WRITE pattern='%s'", value)
        except Exception as exc:
            self.logger.warning("HW MATRIX WRITE failed: %s", exc)
        return True

    def _write_par_f_led_signal_no_lock(self, name: str, value: Any, action_type: str = "EXEC", request_awake: bool = True) -> bool:
        """Wykonuje PAR -> miniPC -> diody F1-F4 REC przez aktywny HardwareBridge (bez locka)."""
        mapping = {
            "par_f_led_f1": 46,
            "par_f_led_f2": 48,
            "par_f_led_f3": 50,
            "par_f_led_f4": 52,
            "rec_p46_led_f1": 46,
            "rec_p48_led_f2": 48,
            "rec_p50_led_f3": 50,
            "rec_p52_led_f4": 52,
        }
        pin = mapping.get(name)
        if pin is None:
            return False
            
        if request_awake:
            # Wybudzamy hardware dla realnego zapisu PAR w trybie EXEC.
            self.request_hardware_awake(source=f"FLED_WRITE_{name}", action_type=action_type)
        
        state = 1 if str(value).strip().lower() not in {"", "0", "false", "off", "none"} else 0
        device = self.devices.get("REC")
        if not device:
            self.logger.warning("HW F_LED WRITE P%s skipped: REC board not connected", pin)
            return True
        try:
            self._lks_set_led_pin(device, pin, state)
            self.logger.info("HW F_LED WRITE P%s=%s", pin, state)
        except Exception as exc:
            self.logger.warning("HW F_LED WRITE P%s failed: %s", pin, exc)
        return True

    def _write_automation_safety_signal_no_lock(self, name: str, value: Any, action_type: str = "EXEC", request_awake: bool = True) -> bool:
        """AUTOMATYKA: PLAY P37 to aktywny systemowy sygnał odłączenia STEP osi ramienia (bez locka)."""
        if name != "play_p37_step_disconnect_manual":
            return False
        state = 1 if str(value).strip().lower() not in {"", "0", "false", "off", "none"} else 0

        def _ack(ok: bool, message: str, error: str = "") -> None:
            try:
                self.bus.set_input("poksyg_play_p37_ack_ok", 1 if ok else 0, source="POKSYG")
                self.bus.set_input("poksyg_play_p37_last_value", state, source="POKSYG")
                self.bus.set_input("poksyg_play_p37_last_error", "" if ok else str(error or message), source="POKSYG")
                self.bus.set_input("poksyg_last_forced_signal", "play_p37_step_disconnect_manual", source="POKSYG")
                self.bus.set_input("poksyg_last_forced_value", state, source="POKSYG")
                self.bus.set_input("poksyg_last_forced_ack_ok", 1 if ok else 0, source="POKSYG")
                self.bus.set_input("poksyg_last_forced_message", message if ok else str(error or message), source="POKSYG")
                self.bus.log("POKSYG", message)
            except Exception as exc:
                self.logger.warning("HW AUTOMATYKA PLAY P37 ACK status update failed: %s", exc)

        if request_awake:
            self.request_hardware_awake(source="P37_SAFETY", action_type=action_type)

        device = self.devices.get("PLAY")
        if not device:
            self.logger.warning("HW AUTOMATYKA PLAY P37 skipped: PLAY board not connected")
            _ack(False, f"ACK ERROR PLAY P37={state} PLAY board not connected", "PLAY board not connected")
            return True
        try:
            self._lks_set_led_pin(device, 37, state)
            if state:
                self.logger.info("HW AUTOMATYKA PLAY P37=1 step_disconnect_active")
                _ack(True, "ACK OK PLAY P37=1 STEP odłączone / sygnał aktywny")
            else:
                self.logger.info("HW AUTOMATYKA PLAY P37=0 automation_active_manual_move_forbidden")
                _ack(True, "ACK OK PLAY P37=0 automatyka aktywna / zakaz ręcznego ruchu")
        except Exception as exc:
            self.logger.warning("HW AUTOMATYKA PLAY P37 failed: %s", exc)
            _ack(False, f"ACK ERROR PLAY P37={state} {exc}", str(exc))
        return True

    def write(self, name: str, value: Any, action_type: str = "EXEC") -> None:
        """Zapis sygnału bezpośrednio do hardware."""
        with self._lock:
            self._write_to_hardware_no_lock(name, value, action_type=action_type)

    def write_batch(self, mapping: Dict[str, Any], action_type: str = "EXEC") -> None:
        """Szybki zapis wielu sygnałów do hardware w jednym locku."""
        if not mapping:
            return
        with self._lock:
            self.request_hardware_awake(source="BATCH_WRITE", action_type=action_type)
            for name, value in mapping.items():
                self._write_to_hardware_no_lock(name, value, action_type=action_type, request_awake=False)

    def _write_to_hardware_no_lock(self, name: str, value: Any, action_type: str = "EXEC", request_awake: bool = True) -> None:
        """Wewnętrzna metoda zapisu bez locka, używana przez write() i write_batch()."""
        if self._write_par_lcd_signal_no_lock(name, value, action_type=action_type, request_awake=request_awake):
            return
        if self._write_par_matrix_signal_no_lock(name, value, action_type=action_type, request_awake=request_awake):
            return
        if self._write_par_f_led_signal_no_lock(name, value, action_type=action_type, request_awake=request_awake):
            return
        if self._write_automation_safety_signal_no_lock(name, value, action_type=action_type, request_awake=request_awake):
            return

        syg = self._signal_map.get(name)
        if not syg:
            return
            
        if syg.kierunek != "OUT" and syg.kierunek != "F":
            return

        if request_awake:
            # Każdy zapis do hardware (GPIO/PWM/PE) musi wybudzić system w wybranym trybie (domyślnie EXEC)
            self.request_hardware_awake(source=f"WRITE_{name}", action_type=action_type)
        
        device = self.devices.get(syg.plytka)
        if not device:
            return

        try:
            # Obsługa wyjść cyfrowych
            if syg.hardware_function == "GPIO" and syg.pin is not None:
                self.pokeys.set_output_by_signal(syg, value)
            
            # Obsługa sygnału ENABLE dla osi (Etap 13)
            elif syg.nazwa.startswith("axis_") and syg.nazwa.endswith("_en"):
                self._handle_pulse_engine_enable(syg, value, device)

            # Obsługa Pulse Engine (STEP/DIR) - ETAP 14
            elif syg.hardware_function == "PULSE_ENGINE":
                self._handle_pulse_engine_write(syg, value, device)
                
        except Exception as exc:
            self.logger.debug(f"Write hardware error ({name}={value}): {exc}")


    def _handle_pulse_engine_enable(self, syg: TarzanSygnal, value: Any, device: Any) -> None:
        """Włącza/wyłącza oś przez core/tarzanPoKeys.py."""
        try:
            axis_idx = self.pokeys.axis_index_from_signal(syg)
            if axis_idx is None:
                axis_idx = int(syg.kanal) if syg.kanal and str(syg.kanal).isdigit() else 0
            ok = self.pokeys.set_pulse_axis_enable(device, int(axis_idx), bool(value))
            if ok:
                ax_base = syg.nazwa.replace("_en", "")
                self.bus.set_input(f"{ax_base}_enabled", 1 if value else 0, source="HW.PE")
        except Exception as e:
            self.logger.debug("Pulse Engine EN error: %s", e)


    def _handle_pulse_engine_write(self, syg: TarzanSygnal, value: Any, device: Any) -> None:
        """STEP/DIR/pozycja osi przez core/tarzanPoKeys.py, bez bezpośredniego toru PoKeys w Bridge."""
        if not self.safety_axis_unlock:
            if time.time() % 10 < 0.1:
                self.logger.warning("PHYSICAL MOTION PREVENTED by safety_axis_unlock=False (Etap 13 Safety)")
            return
        try:
            axis_idx = self.pokeys.axis_index_from_signal(syg)
            if axis_idx is None:
                axis_idx = int(syg.kanal) if syg.kanal and str(syg.kanal).isdigit() else 0
            axis_base = syg.nazwa.replace("_step", "")
            if axis_base not in self._abs_positions:
                self._abs_positions[axis_base] = 0
            if value == 1:
                dir_signal = axis_base + "_dir"
                dir_val = self.bus.read(dir_signal, 1)
                self._abs_positions[axis_base] += 1 if dir_val == 1 else -1
            khr_signal = f"khr_{axis_base[5:]}_offset"
            khr_offset = int(float(self.bus.read(khr_signal, 0.0)))
            target_pos = self._abs_positions[axis_base] + khr_offset
            self.pokeys.set_pulse_axis_position(device, int(axis_idx), int(target_pos))
        except Exception as exc:
            self.logger.debug("Pulse Engine robust write error: %s", exc)

    def snapshot(self) -> Dict[str, Any]:
        """Zwraca aktualny stan hardware (jeśli adapter ma własną tablicę)."""
        return {}

    def _on_signal_change(self, name: str, state: Any) -> None:
        """Reaguje na zmiany sygnałów w SignalBus (np. offsety KHR, komendy)."""
        if name.startswith("khr_") and name.endswith("_offset"):
            # Znajdujemy odpowiadającą oś
            # khr_cam_h_offset -> axis_cam_h
            axis_base = "axis_" + name[4:-7]
            
            # Pobieramy sygnał STEP dla tej osi, aby znać płytkę i kanał PE
            step_signal = axis_base + "_step"
            syg = self._signal_map.get(step_signal)
            if not syg or syg.hardware_function != "PULSE_ENGINE":
                return

            with self._lock:
                device = self.devices.get(syg.plytka)
                if not device:
                    return
                # Ponownie przeliczamy i wysyłamy pozycję PE
                self._handle_pulse_engine_write(syg, 0, device) # value 0 because it's offset change, not step

        elif name == "cmd_unlock_axes":
            val = int(state)
            self.logger.info(f"ACTION: Safety axis unlock changed to {val}")
            self.safety_axis_unlock = (val == 1)
            # Synchronizacja statusu zwrotnego
            self.bus.set_input("safety_axis_unlock", val, source="HW_BRIDGE_SYNC")

        elif name == "cmd_clear_alarms" and state == 1:
            # ETAP 13: Resetowanie alarmów osi
            self.logger.info("ACTION: Clearing axis alarms on miniPC.")
            from core.tarzanZmienneSygnalowe import LISTA_NAZW_OSI
            for ax in LISTA_NAZW_OSI:
                self.bus.set_input(f"axis_{ax}_alarm", 0, source="HW_BRIDGE_CLEAR")
            
            # Resetujemy stan komendy
            self.bus.set_input("cmd_clear_alarms", 0, source="HW_BRIDGE_FINISH")
