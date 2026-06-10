from __future__ import annotations

import os
import platform
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from core.tarzanZmienneSygnalowe import (
    POKEYS57U_PLAY_DEVICE_SERIAL,
    POKEYS57U_REC_DEVICE_SERIAL,
    WSZYSTKIE_SYGNALY,
    HW_ANALOG,
    HW_GPIO,
    HW_I2C,
    HW_KEYBOARD,
    HW_LCD,
    HW_MATRIX_LED,
    HW_POEXTBUS,
    HW_PULSE,
    HW_PWM,
    HW_RESERVED,
    HW_SYSTEM,
    TarzanSygnal,
)

try:
    from core.tarzanPokABC import TarzanPokABC, TARZAN_POKEYS_BOARD_ARCHITECTURE
    TARZAN_POKABC_AVAILABLE = True
except Exception:  # pragma: no cover - boot must fail closed when ABC is unavailable
    TarzanPokABC = None  # type: ignore[assignment]
    TARZAN_POKEYS_BOARD_ARCHITECTURE = {}  # type: ignore[assignment]
    TARZAN_POKABC_AVAILABLE = False

# PoKeys binding for TARZAN miniPC/Linux.
# Runtime nie używa już starego toru Windows DLL ani hardware/pokeys/.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_POKEYS_PYTHON_DIR = _REPO_ROOT / "hardware" / "PoKeysLib" / "Python"
if _POKEYS_PYTHON_DIR.exists() and str(_POKEYS_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(_POKEYS_PYTHON_DIR))

try:
    from PoKeys import PoKeysDevice, ePK_PinCap
    LIB_POKEYS_AVAILABLE = True
except ImportError:
    PoKeysDevice = None  # type: ignore[assignment]
    ePK_PinCap = None  # type: ignore[assignment]
    LIB_POKEYS_AVAILABLE = False


class TarzanPoKeysSnajper:
    """Lekki strażnik próbkowania PoKeys.

    Zasada TARZAN:
    - w IDLE nic nie odpytuje PoKeys w pętli,
    - gdy hardware jest potrzebny, okno aktywne jest jawne,
    - szybkie sensory pracują z krokiem 10 ms, ale nie częściej,
    - ciężkie odczyty I2C są cache'owane i wykonywane tylko na żądanie.
    """

    def __init__(self, logger: Any, default_sample_ms: int = 10) -> None:
        self.logger = logger
        self.default_sample_s = max(0.001, float(default_sample_ms) / 1000.0)
        self.active_until = 0.0
        self._next_due: Dict[str, float] = {}
        self._lock = threading.RLock()

    def arm(self, source: str = "SNAJPER", duration_s: float = 1.5, sample_ms: int = 10) -> None:
        now = time.monotonic()
        with self._lock:
            self.default_sample_s = max(0.001, float(sample_ms) / 1000.0)
            self.active_until = max(self.active_until, now + max(0.0, float(duration_s)))

    def disarm(self) -> None:
        with self._lock:
            self.active_until = 0.0
            self._next_due.clear()

    def active(self) -> bool:
        return time.monotonic() <= self.active_until

    def due(self, key: str, sample_ms: Optional[int] = None, *, force: bool = False) -> bool:
        if force:
            return True
        now = time.monotonic()
        with self._lock:
            if now > self.active_until:
                return False
            interval = max(0.001, float(sample_ms) / 1000.0) if sample_ms is not None else self.default_sample_s
            due_at = self._next_due.get(key, 0.0)
            if now < due_at:
                return False
            self._next_due[key] = now + interval
            return True


class TarzanPoKeys:
    """Własna biblioteka metod PoKeys dla TARZANA.

    Zasada projektu:
    - hardware/PoKeysLib/Python/PoKeys.py jest tylko bindingiem niskiego poziomu,
    - core/tarzanPoKeys.py jest naszą biblioteką metod i mapą użycia,
    - testy LKS, HardwareBridge i PARcore mają wołać metody TARZANA,
      a nie grzebać bezpośrednio w przykładach/wrapperze,
    - IDLE nie oznacza odłączania libusb; IDLE oznacza brak pollingu/testów.

    Ten plik zbiera metody potrzebne dla obecnego projektu:
    PLAY/REC, GPIO, wejścia analogowe/potencjometry RRP, sensory, I2C,
    LCD/Matrix/FLED przez pinowe metody pomocnicze, PoExtBus/CNC/Pulse Engine
    jako kontrolowane metody, nie jako pętla runtime.
    """

    BOARDS: Dict[str, int] = {
        "PLAY": int(POKEYS57U_PLAY_DEVICE_SERIAL),
        "REC": int(POKEYS57U_REC_DEVICE_SERIAL),
    }

    # RRP / potencjometry z mapy sygnałowej projektu.
    RRP_POTS: Dict[str, Tuple[str, str, int, Tuple[str, ...]]] = {
        "P1": ("PLAY", "play_p45_rrp_pot_h", 45, ("sensor_rrp_pot_h", "par_rrp_p1_val", "rrp_p1_val")),
        "P2": ("PLAY", "play_p47_rrp_pot_v", 47, ("sensor_rrp_pot_v", "par_rrp_p2_val", "rrp_p2_val")),
    }

    # LED F1-F4 i przyciski F1-F4 wg mapy REC.
    F_LED_PINS: Dict[str, int] = {"F1": 46, "F2": 48, "F3": 50, "F4": 52}
    F_BUTTON_PINS: Dict[str, int] = {"F1": 45, "F2": 47, "F3": 49, "F4": 51}

    # XYZ w projekcie TARZAN to analogowe wejścia REC/Poksyg, nie osie CNC X/Y/Z.
    POKSYG_XYZ_ANALOG: Dict[str, Tuple[str, int, str]] = {
        "x": ("REC", 41, "sensor_level_x"),
        "y": ("REC", 42, "sensor_level_y"),
        "z": ("REC", 43, "sensor_level_z"),
    }

    # Typowe adresy 7-bit I2C dla PoSensors; do wrappera PoKeys wysyłamy adres 8-bit (addr7 << 1),
    # bo przykład PoKeys dla LM75 używa 0x90 zamiast 0x48.
    I2C_ADDR7 = {
        "bh1750": (0x23, 0x5C),
        "lm75": tuple(range(0x48, 0x50)),
        "sht21": (0x40,),
        "mma7660": (0x4C,),
        "mcp3425": (0x68,),
    }

    def __init__(self, logger: Any) -> None:
        self.logger = logger
        self._lock = threading.RLock()
        self.devices: Dict[str, Any] = {"PLAY": None, "REC": None}
        self.state = "IDLE"  # Dostępne: IDLE, FAST_SAMPLE, POINT_TEST, FULL_DIAGNOSTICS
        self.call_counters: Dict[str, int] = {}
        self.logical_sleep = False
        self.last_lib_path = ""
        self._last_error: Dict[str, str] = {}
        self._signal_groups = self.build_signal_groups(WSZYSTKIE_SYGNALY)
        self.pokabc = TarzanPokABC(logger, WSZYSTKIE_SYGNALY) if TARZAN_POKABC_AVAILABLE and TarzanPokABC is not None else None
        self._abc_boot_confirmed = False
        self._abc_last_result: Dict[str, Any] = {"ok": False, "error": "ABC_NOT_CONFIRMED"}
        self.snajper = TarzanPoKeysSnajper(logger, default_sample_ms=10)
        self._i2c_scan_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._i2c_scan_cache_ttl_s = 30.0
        self._i2c_force_min_gap_s = 2.0
        self._slow_i2c_reads_enabled = os.environ.get("TARZAN_ENABLE_SLOW_I2C_SENSOR_READS") == "1"
        self._runtime_i2c_scan_enabled = os.environ.get("TARZAN_ALLOW_RUNTIME_I2C_SCAN") == "1"
        # libPoKeys/libusb na Linuxie uruchamia własny read_thread.
        # Przy stop usługi agresywne PK_DisconnectDevice potrafi zrobić core dump,
        # jeżeli read_thread nadal siedzi w libusb_handle_events.
        self._shutting_down = False
        self._disconnect_on_stop = os.environ.get("TARZAN_POKEYS_DISCONNECT_ON_STOP") == "1"

    # ------------------------------------------------------------------
    # Biblioteka / połączenia
    # ------------------------------------------------------------------
    def lib_available(self) -> bool:
        return bool(LIB_POKEYS_AVAILABLE and PoKeysDevice is not None)

    def get_lib_path(self) -> str:
        repo_root = Path(__file__).resolve().parents[1]
        candidates = [
            repo_root / "hardware" / "PoKeysLib" / "libPoKeys.so",
            Path("/opt/PoKeysLib/libPoKeys.so"),
            Path("/usr/lib/libPoKeys.so"),
            Path("/usr/local/lib/libPoKeys.so"),
            Path("/usr/lib/x86_64-linux-gnu/libPoKeys.so"),
        ]
        for candidate in candidates:
            try:
                if candidate.exists():
                    return str(candidate)
            except Exception:
                continue
        return str(repo_root / "hardware" / "PoKeysLib" / "libPoKeys.so")

    def connect_all(self, lib_path: Optional[str] = None) -> int:
        with self._lock:
            self._shutting_down = False
            old_state = self.state
            self.state = "POINT_TEST"
            try:
                path = str(lib_path or self.get_lib_path())
                self.last_lib_path = path
                for board, serial in self.BOARDS.items():
                    if self.devices.get(board) is None:
                        self.devices[board] = self.connect_board(board, serial, path)
                self.logical_sleep = False
                # ABC nie tylko sprawdza. Jeżeli płytka ma stary setup, robimy
                # JEDEN restore konfiguracji z tarzanPokABC.py, zapis do PoKeys,
                # odczyt kontrolny i ponowny verify. Bez pętli.
                abc = self.configure_and_verify_project_once(force_i2c=False, restore_if_needed=True)
                if not abc.get("ok"):
                    self._abc_boot_confirmed = False
                    self._abc_last_result = abc
                    self.logger.error("POKEYS ABC BOOT BLOCK: PLAY/REC not confirmed after ABC restore-once")
                    return 0
                self._abc_boot_confirmed = True
                self._abc_last_result = abc
                # Samo połączenie PLAY/REC nie oznacza aktywnego próbkowania.
                # Próbkowanie uruchamia jawnie HardwareBridge/Snajper/KHR albo test punktowy.
                return self.connected_count()
            finally:
                self.state = old_state

    def connect_board(self, board: str, serial: int, lib_path: Optional[str] = None) -> Any:
        board = str(board).upper()
        if not self.lib_available():
            self.logger.error("PoKeys binding not available")
            return None
        path = str(lib_path or self.get_lib_path())
        try:
            device = PoKeysDevice(path)  # type: ignore[misc]
            ok = device.PK_ConnectToDeviceWSerial(int(serial), 1, False)
            if not ok:
                self.logger.warning("Failed to connect to %s board (serial=%s)", board, serial)
                return None
            self.refresh_device(device, analog=False, digital=False, config=False)
            self.logger.info("Connected to %s board (serial=%s).", board, serial)
            return device
        except Exception as exc:
            self._last_error[board] = str(exc)
            self.logger.warning("PoKeys connect %s failed: %s", board, exc)
            return None

    def connected_count(self) -> int:
        return sum(1 for dev in self.devices.values() if dev is not None)

    def is_any_connected(self) -> bool:
        return self.connected_count() > 0

    def is_all_connected(self) -> bool:
        return self.connected_count() == len(self.devices)

    def get_device(self, board: str) -> Any:
        return self.devices.get(str(board).upper())

    def logical_idle(self) -> bool:
        with self._lock:
            if self.logical_sleep:
                return False
            self.logical_sleep = True
            self.state = "IDLE"
            self.snajper.disarm()
            self.logger.info("USB SLEEP: logical sleep; PoKeys handles kept open (no PK_DisconnectDevice in IDLE). STATE=IDLE")
            return True

    def logical_wake(self) -> bool:
        with self._lock:
            if not self.logical_sleep:
                return False
            self.logical_sleep = False
            # logical_wake nie wymusza już FAST_SAMPLE. 
            # Pozwala na PK_*, o ile stan zostanie jawnie zmieniony 
            # (np. przez begin_fast_sample lub begin_point_test).
            self.logger.info("USB WAKE: logical wake; PoKeys handles already open. STATE=%s", self.state)
            return True

    def safe_stop(self) -> None:
        """Bezpieczne zamknięcie PoKeys przy STOP usługi.

        Na Linuxie libPoKeys/libusb ma własny read_thread. Logi z miniPC pokazały,
        że równoległe PK_DisconnectDevice podczas stop/restart potrafi wejść w
        libusb_close, gdy read_thread nadal jest w libusb_handle_events, i kończy
        proces core dumpem. Dlatego domyślnie nie wołamy fizycznego Disconnect
        przy stop usługi. Zostawiamy zamknięcie uchwytów procesowi systemd/kernel.

        Wymuszenie starego zachowania tylko diagnostycznie:
            TARZAN_POKEYS_DISCONNECT_ON_STOP=1
        """
        with self._lock:
            self._shutting_down = True
            self.logical_sleep = True
            self.state = "IDLE"
            self.snajper.disarm()

            if not self._disconnect_on_stop:
                connected = [board for board, device in self.devices.items() if device is not None]
                for board in connected:
                    self.devices[board] = None
                self.logger.info(
                    "POKEYS SAFE SHUTDOWN: skipped PK_DisconnectDevice for boards=%s "
                    "to avoid libusb read_thread crash.",
                    ",".join(connected) if connected else "none",
                )
                return

            for board, device in list(self.devices.items()):
                if device is None:
                    continue
                try:
                    device.Disconnect()
                    self.logger.info("Disconnected %s board.", board)
                except BaseException as exc:
                    self.logger.warning("PoKeys safe_stop disconnect %s ignored: %s", board, exc)
                finally:
                    self.devices[board] = None
            self.logger.warning("POKEYS SAFE SHUTDOWN: forced PK_DisconnectDevice was enabled by env.")

    def set_state(self, state: str) -> None:
        """Ustawia stan bramki (IDLE, FAST_SAMPLE, POINT_TEST, FULL_DIAGNOSTICS)."""
        with self._lock:
            state = str(state).upper()
            if state in ["IDLE", "FAST_SAMPLE", "POINT_TEST", "FULL_DIAGNOSTICS"]:
                self.state = state
                if state != "IDLE":
                    self.logical_sleep = False
                self.logger.info("POKEYS STATE: %s", state)
            else:
                self.logger.warning("Invalid PoKeys state: %s", state)

    def begin_fast_sample(self, source: str = "SNAJPER", duration_s: float = 1.5, sample_ms: int = 10) -> None:
        """Przełącza bramkę w tryb szybkiego próbkowania (KHR/Snajper)."""
        with self._lock:
            self.logical_sleep = False
            self.state = "FAST_SAMPLE"
            self.snajper.arm(source, duration_s=duration_s, sample_ms=sample_ms)
            self.logger.debug("POKEYS STATE: FAST_SAMPLE (source=%s, dur=%s, smp=%s)", source, duration_s, sample_ms)

    def begin_point_test(self, component: str) -> None:
        """Przełącza bramkę w tryb testu punktowego (np. klik ikonki LKS)."""
        with self._lock:
            self.logical_sleep = False
            self.state = "POINT_TEST"
            self.logger.info("POKEYS STATE: POINT_TEST (component=%s)", component)

    def begin_full_diagnostics(self, reason: str = "manual") -> None:
        """Przełącza bramkę w tryb pełnej diagnostyki (np. boot test)."""
        with self._lock:
            self.logical_sleep = False
            self.state = "FULL_DIAGNOSTICS"
            self.logger.info("POKEYS STATE: FULL_DIAGNOSTICS (reason=%s)", reason)

    def begin_exec(self, source: str = "") -> None:
        """Przełącza bramkę w tryb realnego wykonania (ruchu/akcji)."""
        with self._lock:
            self.logical_sleep = False
            self.state = "EXEC"
            self.logger.info("POKEYS STATE: EXEC (source=%s)", source)

    def end_active_state(self) -> None:
        """Powrót do trybu IDLE."""
        with self._lock:
            self.state = "IDLE"
            self.logical_sleep = True
            self.snajper.disarm()
            self.logger.debug("POKEYS STATE: IDLE (returned from active state)")

    def snajper_arm(self, source: str = "SNAJPER", duration_s: float = 1.5, sample_ms: int = 10) -> None:
        """Jawne okno aktywnego próbkowania PoKeys; używać z HardwareBridge/Snajper/KHR."""
        with self._lock:
            self.logical_sleep = False
            self.state = "FAST_SAMPLE"
            self.snajper.arm(source, duration_s=duration_s, sample_ms=sample_ms)

    def snajper_disarm(self) -> None:
        """Zamknięcie okna aktywnego próbkowania bez zamykania USB."""
        with self._lock:
            self.state = "IDLE"
            self.snajper.disarm()

    def _snajper_due(self, key: str, sample_ms: int = 10, *, force: bool = False) -> bool:
        if force:
            return True
        if self.logical_sleep:
            return False
        return self.snajper.due(key, sample_ms=sample_ms, force=False)

    @staticmethod
    def _skipped(name: str, reason: str = "logical_sleep") -> Dict[str, Any]:
        return {"ok": False, "skipped": True, "name": name, "reason": reason}

    # ------------------------------------------------------------------
    # Inwentaryzacja wg core/tarzanZmienneSygnalowe.py
    # ------------------------------------------------------------------
    def build_signal_groups(self, signals: Dict[str, TarzanSygnal]) -> Dict[str, List[TarzanSygnal]]:
        groups: Dict[str, List[TarzanSygnal]] = {
            "gpio_in": [], "gpio_out": [], "analog_in": [], "pulse": [], "cnc": [],
            "poextbus": [], "i2c": [], "lcd": [], "matrix": [], "keyboard": [],
            "f_led": [], "f_button": [], "sensors": [], "limits": [], "rrp_pots": [],
        }
        for sig in signals.values():
            board = str(sig.plytka or "").upper()
            hf = str(sig.hardware_function or "").upper()
            name = str(sig.nazwa or "")
            grupa = str(sig.grupa or "").upper()
            if hf == HW_PULSE:
                groups["pulse"].append(sig)
            # CNC to tylko projektowa płytka/grupa osi CNC, nie każdy pin z funkcją PULSE.
            # REC F-LED, shock, free_limit itp. mają hardware_function=PULSE, ale nie są osiami.
            if board == "CNC" or str(sig.grupa or "").upper().startswith("CNC_"):
                groups["cnc"].append(sig)
            if hf == HW_GPIO:
                if str(sig.kierunek).upper() == "IN":
                    groups["gpio_in"].append(sig)
                elif str(sig.kierunek).upper() == "OUT":
                    groups["gpio_out"].append(sig)
            if hf == HW_ANALOG or str(sig.typ).upper() == "ANALOG":
                groups["analog_in"].append(sig)
            if hf == HW_POEXTBUS:
                groups["poextbus"].append(sig)
            if hf == HW_I2C:
                groups["i2c"].append(sig)
            if hf == HW_LCD:
                groups["lcd"].append(sig)
            if hf == HW_MATRIX_LED:
                groups["matrix"].append(sig)
            if "KEY" in hf or "KEYPAD" in name:
                groups["keyboard"].append(sig)
            if name in {"rec_p46_led_f1", "rec_p48_led_f2", "rec_p50_led_f3", "rec_p52_led_f4"}:
                groups["f_led"].append(sig)
            if name in {"rec_p45_sw_f1", "rec_p47_sw_f2", "rec_p49_sw_f3", "rec_p51_sw_f4"}:
                groups["f_button"].append(sig)
            if "CZUJN" in grupa or "SENSOR" in name or "LIGHT" in name or "TEMP" in name or "SHOCK" in name:
                groups["sensors"].append(sig)
            if "KRA" in grupa or "LIMIT" in name:
                groups["limits"].append(sig)
            if name in {"play_p45_rrp_pot_h", "play_p47_rrp_pot_v", "sensor_rrp_pot_h", "sensor_rrp_pot_v"}:
                groups["rrp_pots"].append(sig)
        return groups

    def inventory(self) -> Dict[str, int]:
        return {k: len(v) for k, v in self._signal_groups.items()}

    def signals(self, group: str) -> List[TarzanSygnal]:
        return list(self._signal_groups.get(group, []))

    def begin_active_sampling(self, source: str = "SNAJPER", duration_s: float = 1.5, sample_ms: int = 10) -> None:
        """Jawne okno próbkowania PoKeys dla Snajpera/KHR/testu punktowego.

        IDLE nie odpytuje sprzętu. Ten przełącznik jest wejściem dla warstwy,
        która naprawdę potrzebuje szybkich próbek. Minimalny krok to 10 ms.
        """
        with self._lock:
            self.state = "FAST_SAMPLE"
            self.snajper.arm(source=source, duration_s=duration_s, sample_ms=max(10, int(sample_ms)))

    def end_active_sampling(self) -> None:
        with self._lock:
            self.state = "IDLE"
            self.snajper.disarm()

    def enable_slow_i2c_reads(self, enabled: bool = True) -> None:
        """Włącza ciężkie odczyty I2C sensorów tylko dla jawnego testu/serwisu."""
        self._slow_i2c_reads_enabled = bool(enabled)
        if enabled:
            self._runtime_i2c_scan_enabled = True

    def enable_i2c_diagnostics(self, enabled: bool = True) -> None:
        """Pozwala na diagnostyczny scan I2C; domyślnie runtime/startup nie skanuje I2C."""
        self._runtime_i2c_scan_enabled = bool(enabled)

    def _i2c_allowed(self, *, force: bool = False) -> bool:
        return bool(force or self._slow_i2c_reads_enabled or self._runtime_i2c_scan_enabled)

    # ------------------------------------------------------------------
    # Odczyty niskiego poziomu: tylko na żądanie / aktywne okno
    # ------------------------------------------------------------------
    def identity_text(self, board: str, device: Any) -> str:
        try:
            data = device.device.contents.DeviceData
            serial = int(getattr(data, "SerialNumber", 0))
            name = data.DeviceName.decode("ascii", errors="ignore").strip("\x00")
            typ = data.DeviceTypeName.decode("ascii", errors="ignore").strip("\x00")
            return f"{board} serial={serial} name='{name}' type='{typ}'"
        except Exception:
            return f"{board} connected"

    def refresh_device(self, device: Any, *, analog: bool = True, digital: bool = True, config: bool = False) -> None:
        if config:
            for call_name in ("PK_DeviceDataGet", "PK_PinConfigurationGet"):
                self._call_device(device, call_name)
        if digital:
            self._call_device(device, "PK_DigitalIOGet")
        if analog:
            self._call_device(device, "PK_AnalogIOGet")

    def read_pin(self, device: Any, pin: int) -> int:
        self.refresh_device(device, analog=False, digital=True)
        return int(device.device.contents.Pins[int(pin) - 1].DigitalValueGet)

    def read_analog_pin(self, device: Any, pin: int) -> int:
        self.refresh_device(device, analog=True, digital=False)
        try:
            return int(device.device.contents.Pins[int(pin) - 1].AnalogValue)
        except Exception:
            return 0

    def set_digital_output(self, device: Any, pin: int, value: int) -> None:
        if ePK_PinCap is None:
            raise RuntimeError("ePK_PinCap unavailable")
        pin_index = int(pin) - 1
        pin_data = device.device.contents.Pins[pin_index]
        pin_data.PinFunction = int(ePK_PinCap.PK_PinCap_digitalOutput)
        pin_data.DigitalValueSet = 1 if value else 0
        res = self._call_device(device, "PK_PinConfigurationSet")
        if not res.get("ok"):
            raise RuntimeError(f"PK_PinConfigurationSet P{pin} failed: {res.get('error') or res.get('rc')}")
        res = self._call_device(device, "PK_DigitalIOSetSingle", pin_index, 1 if value else 0)
        if not res.get("ok"):
            raise RuntimeError(f"PK_DigitalIOSetSingle P{pin} failed: {res.get('error') or res.get('rc')}")

    def _device_for_signal(self, sig: TarzanSygnal) -> Any:
        board = str(sig.plytka or "").upper()
        if board in {"PLAY", "REC"}:
            return self.get_device(board)
        # CNC/PoExtBus w obecnej mapie jest funkcją PoKeys, nie osobną płytką USB.
        # Bezpiecznie preferujemy PLAY dla pulse/CNC, REC dla FLED/PoExtBus REC.
        if board == "CNC":
            return self.get_device("PLAY") or self.get_device("REC")
        return None

    def set_output_by_signal(self, sig: TarzanSygnal, value: Any) -> bool:
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            device = self._device_for_signal(sig)
            if device is None:
                return False
            try:
                hf = str(sig.hardware_function or "").upper()
                if hf == HW_GPIO and sig.pin is not None:
                    self.set_digital_output(device, int(sig.pin), 1 if value else 0)
                    return True
                if hf == HW_POEXTBUS:
                    return self.set_poextbus_signal(sig, value)
                if hf == HW_PULSE:
                    # Ruch osi zostaje kontrolowany przez wyższą warstwę, ale sygnał jest rozpoznany.
                    return self.write_pulse_signal(sig, value)
                if hf == HW_PWM and sig.pin is not None:
                    return self.set_digital_output(device, int(sig.pin), 1 if value else 0) is None
            except Exception as exc:
                self._last_error[sig.nazwa] = str(exc)
                self.logger.debug("tarzanPoKeys set_output_by_signal %s failed: %s", sig.nazwa, exc)
        return False

    # ------------------------------------------------------------------
    # Poll jednorazowy, tylko gdy aktywnie testujemy / wykonujemy
    # ------------------------------------------------------------------
    def poll_gpio_inputs_once(self, gpio_inputs: Iterable[TarzanSygnal], update: Callable[[str, Any, str], None], *, force: bool = False) -> None:
        with self._lock:
            if not self._snajper_due("gpio_inputs", sample_ms=10, force=force):
                return
            for board_name, device in self.devices.items():
                if device is None:
                    continue
                try:
                    res = self._call_device(board_name, "PK_DigitalIOGet")
                    if not res.get("ok"):
                        continue
                    pins_ptr = device.device.contents.Pins
                    for sig in gpio_inputs:
                        if str(sig.plytka).upper() == board_name and sig.pin is not None:
                            val = 1 if pins_ptr[int(sig.pin) - 1].DigitalValueGet else 0
                            update(str(sig.nazwa), val, f"HW.{board_name}")
                            if sig.kanoniczna_nazwa:
                                update(str(sig.kanoniczna_nazwa), val, f"HW.{board_name}")
                except Exception as exc:
                    self.logger.debug("PoKeys GPIO poll %s error: %s", board_name, exc)

    def poll_analog_inputs_once(self, analog_inputs: Iterable[TarzanSygnal], update: Callable[[str, Any, str], None], *, force: bool = False) -> None:
        with self._lock:
            if not self._snajper_due("analog_inputs", sample_ms=10, force=force):
                return
            grouped: Dict[str, List[TarzanSygnal]] = {"PLAY": [], "REC": []}
            for sig in analog_inputs:
                board = str(sig.plytka).upper()
                if board in grouped and sig.pin is not None:
                    grouped[board].append(sig)
            for board, items in grouped.items():
                device = self.get_device(board)
                if device is None or not items:
                    continue
                try:
                    res = self._call_device(board, "PK_AnalogIOGet")
                    if not res.get("ok"):
                        continue
                    pins = device.device.contents.Pins
                    for sig in items:
                        val = int(pins[int(sig.pin) - 1].AnalogValue)
                        update(sig.nazwa, val, f"HW.{board}.ANALOG")
                        if sig.kanoniczna_nazwa:
                            update(sig.kanoniczna_nazwa, val, f"HW.{board}.ANALOG")
                except Exception as exc:
                    self.logger.debug("PoKeys analog poll %s error: %s", board, exc)

    # ------------------------------------------------------------------
    # Potencjometry RRP / CNC / sensory — testy na żądanie
    # ------------------------------------------------------------------
    def sample_fast_once(
        self,
        update: Optional[Callable[[str, Any, str], None]] = None,
        *,
        include_counters: bool = False,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Szybka próbka dla KHR/Snajpera: analog + digital, maksymalnie co 10 ms.

        Nie dotyka I2C, LCD, Matrix, PoExtBus ani Pulse Engine. Liczniki/CTR
        tylko gdy caller jawnie poda include_counters=True.
        """
        if self.state not in ["FAST_SAMPLE", "POINT_TEST", "FULL_DIAGNOSTICS"]:
            if not force:
                return self._skipped("fast_sample", reason=f"NOT_ALLOWED_IN_STATE_{self.state}")

        if self.logical_sleep and not force:
            return self._skipped("fast_sample")
        if not self.snajper.due("fast_sample", sample_ms=10, force=force):
            return {"ok": False, "skipped": True, "reason": "snajper_not_due"}

        result: Dict[str, Any] = {"ok": False, "analog": {}, "digital": {}, "counters": {}, "errors": []}

        def _upd(name: str, val: Any, source: str) -> None:
            if update:
                update(name, val, source)

        try:
            self.poll_analog_inputs_once(self.signals("analog_in"), lambda n, v, src: (result["analog"].__setitem__(n, v), _upd(n, v, src)), force=False)
        except Exception as exc:
            result["errors"].append(f"analog: {exc}")
        try:
            gpio = [s for s in (self.signals("gpio_in") + self.signals("sensors") + self.signals("limits")) if s.pin is not None]
            self.poll_gpio_inputs_once(gpio, lambda n, v, src: (result["digital"].__setitem__(n, v), _upd(n, v, src)), force=False)
        except Exception as exc:
            result["errors"].append(f"digital: {exc}")
        if include_counters:
            for board in ("PLAY", "REC"):
                try:
                    result["counters"][board] = self.digital_counter_get_once(board)
                except Exception as exc:
                    result["errors"].append(f"counters.{board}: {exc}")
        result["ok"] = not result["errors"]
        return result

    def test_potentiometers_once(self, update: Optional[Callable[[str, Any, str], None]] = None) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ok": False, "values": {}, "errors": []}
        with self._lock:
            device = self.get_device("PLAY")
            if device is None:
                out["errors"].append("PLAY not connected")
                return out
            try:
                res = self._call_device("PLAY", "PK_AnalogIOGet")
                if not res.get("ok"):
                    out["errors"].append(res.get("error") or "PK_AnalogIOGet failed")
                    return out
                pins = device.device.contents.Pins
                for label, (_board, sig_name, pin, aliases) in self.RRP_POTS.items():
                    val = int(pins[int(pin) - 1].AnalogValue)
                    out["values"][sig_name] = val
                    out["values"][label] = val
                    if update:
                        update(sig_name, val, "HW.PLAY.RRP")
                        for alias in aliases:
                            update(alias, val, "HW.PLAY.RRP")
                out["ok"] = True
            except Exception as exc:
                out["errors"].append(str(exc))
        return out

    def test_cnc_once(self) -> Dict[str, Any]:
        """Konserwatywny test CNC: mapa sygnałów + status Pulse Engine, bez ruchu osi."""
        out: Dict[str, Any] = {
            "ok": False,
            "signals": [s.nazwa for s in self.signals("cnc")],
            "pulse_status": {},
            "errors": [],
        }
        dev = self.get_device("PLAY") or self.get_device("REC")
        if dev is None:
            out["errors"].append("no PoKeys board connected")
            return out
        try:
            out["pulse_status"] = self.get_pulse_engine_status(dev)
            out["ok"] = True
        except Exception as exc:
            out["errors"].append(str(exc))
        return out

    def test_sensors_once(self, update: Optional[Callable[[str, Any, str], None]] = None) -> Dict[str, Any]:
        """Pełny jednorazowy test sensorów TARZANA bez pętli IDLE.

        Obejmuje:
        - analogowe XYZ z Poksyg/REC: rec_p41..43,
        - analogowe RRP P45/P47,
        - krańcówki i wejścia GPIO z mapy,
        - PoSensors po I2C: BH1750, LM75, SHT21, MMA7660, MCP3425,
        - EasySensors, jeśli są skonfigurowane w PoKeys.
        """
        result: Dict[str, Any] = {
            "ok": False,
            "analog": {},
            "digital": {},
            "xyz": {},
            "posensors": {},
            "easy_sensors": {},
            "i2c_scan": {},
            "errors": [],
        }

        def _upd(name: str, val: Any, source: str) -> None:
            if update:
                update(name, val, source)

        try:
            self.poll_analog_inputs_once(self.signals("analog_in"), lambda n, v, s: (result["analog"].__setitem__(n, v), _upd(n, v, s)))
        except Exception as exc:
            result["errors"].append(f"analog: {exc}")
        try:
            result["xyz"] = self.read_xyz_poksyg_once(update=update)
        except Exception as exc:
            result["errors"].append(f"xyz: {exc}")
        try:
            sensor_gpio = [s for s in (self.signals("sensors") + self.signals("limits")) if s.hardware_function == HW_GPIO and s.pin is not None]
            self.poll_gpio_inputs_once(sensor_gpio, lambda n, v, s: (result["digital"].__setitem__(n, v), _upd(n, v, s)))
        except Exception as exc:
            result["errors"].append(f"digital: {exc}")
        # I2C/PoSensors to wolny tor diagnostyczny. Nie uruchamiamy go w runtime/startup.
        result["i2c_scan"] = {"ok": False, "skipped": True, "reason": "i2c_runtime_disabled"}
        result["posensors"] = {"ok": False, "skipped": True, "reason": "slow_i2c_reads_disabled_in_runtime"}
        result["easy_sensors"] = {"ok": False, "skipped": True, "reason": "slow_i2c_reads_disabled_in_runtime"}
        result["ok"] = len(result["errors"]) == 0
        return result

    # ------------------------------------------------------------------
    # I2C / EasySensors / PoExtBus / Pulse Engine
    # ------------------------------------------------------------------
    def scan_i2c_once(self, board: str = "PLAY", *, force: bool = False, cache_ttl_s: Optional[float] = None) -> Dict[str, Any]:
        """Jednorazowy skan I2C przez PoKeys, z cache i bez młócenia w IDLE."""
        board = str(board or "PLAY").upper()
        now = time.monotonic()
        ttl = self._i2c_scan_cache_ttl_s if cache_ttl_s is None else max(0.0, float(cache_ttl_s))
        cached = self._i2c_scan_cache.get(board)
        if cached and ttl > 0 and (now - cached[0]) <= ttl:
            out = dict(cached[1])
            out["cached"] = True
            return out
        # Nawet force nie ma prawa młócić magistrali kilka razy pod rząd.
        # Do twardego debugowania użyć cache_ttl_s=0.
        if cached and ttl > 0 and (now - cached[0]) <= self._i2c_force_min_gap_s:
            out = dict(cached[1])
            out["cached"] = True
            out["force_throttled"] = True
            return out
        if self.logical_sleep and not force:
            return {"ok": False, "addresses": [], "found": [], "skipped": True, "reason": "logical_sleep", "board": board}
        if not self._i2c_allowed(force=force):
            return {"ok": False, "addresses": [], "found": [], "skipped": True, "reason": "i2c_runtime_disabled", "board": board}
        device = self.get_device(board)
        if device is None:
            result = {"ok": False, "addresses": [], "found": [], "error": f"{board} not connected", "board": board}
            self.logger.info("I2C_SCAN board=%s ok=False error=%s", board, result["error"])
            return result
        try:
            res = self._call_device(board, "PK_I2CBusScanStart")
            if not res.get("ok"):
                return {"ok": False, "addresses": [], "found": [], "error": f"PK_I2CBusScanStart failed: {res.get('error')}", "board": board}
            time.sleep(0.35)
            data = self._call_device(board, "PK_I2CBusScanGetResults").get("rc")
            if not data:
                return {"ok": False, "addresses": [], "found": [], "error": "PK_I2CBusScanGetResults returned no data", "board": board}
            addrs = [addr for addr in range(0, min(128, len(data))) if int(data[addr]) == 1]
            result = {"ok": True, "addresses": addrs, "found": addrs, "board": board}
            self._i2c_scan_cache[board] = (time.monotonic(), dict(result))
            self.logger.info("I2C_SCAN board=%s ok=True addresses=%s", board, ",".join(f"0x{x:02X}" for x in addrs) or "none")
            return result
        except Exception as exc:
            result = {"ok": False, "addresses": [], "found": [], "error": str(exc), "board": board}
            self.logger.info("I2C_SCAN board=%s ok=False error=%s", board, exc)
            return result

    def _i2c_addr8(self, addr7: int) -> int:
        """PoKeys wrapper pracuje jak przykłady z dokumentacji: adres 7-bit przesunięty w lewo."""
        return (int(addr7) & 0x7F) << 1

    def i2c_write(self, board: str, addr7: int, data: Iterable[int]) -> bool:
        if not self._i2c_allowed():
            return False
        device = self.get_device(board)
        if device is None:
            return False
        try:
            res = self._call_device(board, "PK_I2CWrite", self._i2c_addr8(addr7), list(data))
            return res.get("ok", False)
        except Exception as exc:
            self.logger.debug("I2C write board=%s addr=0x%02X failed: %s", board, addr7, exc)
            return False

    def i2c_read(self, board: str, addr7: int, n: int) -> Optional[List[int]]:
        if not self._i2c_allowed():
            return None
        device = self.get_device(board)
        if device is None:
            return None
        try:
            res = self._call_device(board, "PK_I2CRead", self._i2c_addr8(addr7), int(n))
            data = res.get("rc")
            if data is None:
                return None
            return [int(x) & 0xFF for x in data]
        except Exception as exc:
            self.logger.debug("I2C read board=%s addr=0x%02X failed: %s", board, addr7, exc)
            return None

    def i2c_write_read(self, board: str, addr7: int, write: Iterable[int], n: int) -> Optional[List[int]]:
        if not self._i2c_allowed():
            return None
        device = self.get_device(board)
        if device is None:
            return None
        try:
            res = self._call_device(board, "PK_I2CWriteAndRead", self._i2c_addr8(addr7), list(write), int(n))
            data = res.get("rc")
            if data is None:
                return None
            return [int(x) & 0xFF for x in data]
        except Exception as exc:
            self.logger.debug("I2C write/read board=%s addr=0x%02X failed: %s", board, addr7, exc)
            return None

    def _addr_from_scan(self, scan: Optional[Dict[str, Any]], names: Iterable[str]) -> Optional[int]:
        if not scan:
            return None
        addrs = set(scan.get("addresses") or scan.get("found") or [])
        for name in names:
            for addr in self.I2C_ADDR7.get(name, ()):  # type: ignore[arg-type]
                if addr in addrs:
                    return int(addr)
        return None

    def _first_present_addr(self, board: str, names: Iterable[str], scan: Optional[Dict[str, Any]] = None) -> Optional[int]:
        scan = scan if scan is not None else self.scan_i2c_once(board)
        return self._addr_from_scan(scan, names)

    @staticmethod
    def _missing_sensor(sensor: str, board: str, names: Iterable[str]) -> Dict[str, Any]:
        return {"ok": False, "sensor": sensor, "board": board, "skipped": True, "reason": "address_not_present", "names": list(names)}

    def read_bh1750_lux_once(self, board: str = "PLAY", addr7: Optional[int] = None, scan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        present = self._first_present_addr(board, ["bh1750"], scan) if addr7 is None else int(addr7)
        if present is None:
            return self._missing_sensor("BH1750", board, ["bh1750"])
        addr = int(present)
        try:
            # Power on + continuous high resolution mode; pomiar około 120-180 ms.
            self.i2c_write(board, addr, [0x01])
            self.i2c_write(board, addr, [0x10])
            time.sleep(0.18)
            data = self.i2c_read(board, addr, 2)
            if not data or len(data) < 2:
                return {"ok": False, "sensor": "BH1750", "addr7": addr, "error": "no data"}
            raw = (data[0] << 8) | data[1]
            lux = raw / 1.2
            return {"ok": True, "sensor": "BH1750", "addr7": addr, "raw": raw, "lux": lux}
        except Exception as exc:
            return {"ok": False, "sensor": "BH1750", "addr7": addr, "error": str(exc)}

    def read_lm75_temp_once(self, board: str = "PLAY", addr7: Optional[int] = None, scan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        present = self._first_present_addr(board, ["lm75"], scan) if addr7 is None else int(addr7)
        if present is None:
            return self._missing_sensor("LM75", board, ["lm75"])
        addr = int(present)
        data = self.i2c_write_read(board, addr, [0x00], 2)
        if not data or len(data) < 2:
            return {"ok": False, "sensor": "LM75", "addr7": addr, "error": "no data"}
        raw = ((data[0] << 8) | data[1]) >> 5
        if raw & 0x400:
            raw -= 0x800
        temp_c = raw * 0.125
        return {"ok": True, "sensor": "LM75", "addr7": addr, "raw": raw, "temp_c": temp_c}

    def read_sht21_once(self, board: str = "PLAY", addr7: int = 0x40, scan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # No-hold measurement commands: temp 0xF3, humidity 0xF5.
        if scan is not None and int(addr7) not in set(scan.get("addresses") or scan.get("found") or []):
            return self._missing_sensor("SHT21", board, ["sht21"])
        out: Dict[str, Any] = {"ok": False, "sensor": "SHT21", "addr7": addr7}
        try:
            self.i2c_write(board, addr7, [0xF3])
            time.sleep(0.09)
            t = self.i2c_read(board, addr7, 3)
            self.i2c_write(board, addr7, [0xF5])
            time.sleep(0.035)
            h = self.i2c_read(board, addr7, 3)
            if not t or len(t) < 2 or not h or len(h) < 2:
                out["error"] = "no data"
                return out
            t_raw = ((t[0] << 8) | t[1]) & 0xFFFC
            h_raw = ((h[0] << 8) | h[1]) & 0xFFFC
            out.update({
                "ok": True,
                "temp_c": -46.85 + 175.72 * (t_raw / 65536.0),
                "humidity_pct": -6.0 + 125.0 * (h_raw / 65536.0),
                "raw_temp": t_raw,
                "raw_humidity": h_raw,
            })
            return out
        except Exception as exc:
            out["error"] = str(exc)
            return out

    def _mma7660_value(self, b: int) -> int:
        b &= 0x3F
        if b & 0x20:
            b -= 0x40
        return b

    def read_mma7660_level_once(self, board: str = "PLAY", addr7: int = 0x4C, scan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if scan is not None and int(addr7) not in set(scan.get("addresses") or scan.get("found") or []):
            return self._missing_sensor("MMA7660", board, ["mma7660"])
        try:
            # Standby, konfiguracja, active. Jeżeli sensor już aktywny, komendy są nieszkodliwe.
            self.i2c_write(board, addr7, [0x07, 0x00])
            self.i2c_write(board, addr7, [0x08, 0x00])
            self.i2c_write(board, addr7, [0x07, 0x01])
            time.sleep(0.02)
            data = self.i2c_write_read(board, addr7, [0x00], 3)
            if not data or len(data) < 3:
                return {"ok": False, "sensor": "MMA7660", "addr7": addr7, "error": "no data"}
            x, y, z = [self._mma7660_value(v) for v in data[:3]]
            # MMA7660 typowo ~21 counts/g.
            return {"ok": True, "sensor": "MMA7660", "addr7": addr7, "x_raw": x, "y_raw": y, "z_raw": z, "x_g": x/21.0, "y_g": y/21.0, "z_g": z/21.0}
        except Exception as exc:
            return {"ok": False, "sensor": "MMA7660", "addr7": addr7, "error": str(exc)}

    def read_mcp3425_adc_once(self, board: str = "PLAY", addr7: int = 0x68, scan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if scan is not None and int(addr7) not in set(scan.get("addresses") or scan.get("found") or []):
            return self._missing_sensor("MCP3425", board, ["mcp3425"])
        try:
            # One-shot 16-bit, gain x1.
            self.i2c_write(board, addr7, [0x80])
            time.sleep(0.08)
            data = self.i2c_read(board, addr7, 3)
            if not data or len(data) < 2:
                return {"ok": False, "sensor": "MCP3425", "addr7": addr7, "error": "no data"}
            raw = (data[0] << 8) | data[1]
            if raw & 0x8000:
                raw -= 0x10000
            # LSB dla trybu 16-bit przy PGA=1 w MCP3425 to około 62.5 uV.
            volts = raw * 0.0000625
            return {"ok": True, "sensor": "MCP3425", "addr7": addr7, "raw": raw, "volts": volts}
        except Exception as exc:
            return {"ok": False, "sensor": "MCP3425", "addr7": addr7, "error": str(exc)}

    def read_posensors_once(self, board: str = "PLAY", update: Optional[Callable[[str, Any, str], None]] = None, *, force: bool = False) -> Dict[str, Any]:
        """Odczyt PoSensors bez kaskady skanów I2C.

        Jeden scan na wejściu, potem tylko sensory obecne pod znalezionymi adresami.
        Brakujące adresy są SKIPPED, nie bombardujemy magistrali błędnymi odczytami.
        """
        if self.logical_sleep and not force:
            return self._skipped("posensors")
        if not self._slow_i2c_reads_enabled:
            # PoSensors po I2C są wolne i nie są to próbki 10 ms dla KHR.
            # Domyślnie nie robimy nawet scan_i2c_once, żeby startup/runtime nie młócił magistrali.
            return {"ok": False, "skipped": True, "reason": "slow_i2c_reads_disabled", "board": str(board).upper()}
        scan = self.scan_i2c_once(board, force=True)
        out: Dict[str, Any] = {
            "scan": scan,
            "bh1750": self.read_bh1750_lux_once(board, scan=scan),
            "lm75": self.read_lm75_temp_once(board, scan=scan),
            "sht21": self.read_sht21_once(board, scan=scan),
            "mma7660": self.read_mma7660_level_once(board, scan=scan),
            "mcp3425": self.read_mcp3425_adc_once(board, scan=scan),
        }
        ok = any(isinstance(v, dict) and v.get("ok") for v in out.values())
        out["ok"] = ok
        if update:
            try:
                if out["bh1750"].get("ok"):
                    update("sensor_light_lux", out["bh1750"]["lux"], "HW.POSENSORS.BH1750")
                if out["lm75"].get("ok"):
                    update("sensor_temp_c", out["lm75"]["temp_c"], "HW.POSENSORS.LM75")
                if out["sht21"].get("ok"):
                    update("sensor_sht21_temp_c", out["sht21"]["temp_c"], "HW.POSENSORS.SHT21")
                    update("sensor_humidity_pct", out["sht21"]["humidity_pct"], "HW.POSENSORS.SHT21")
                if out["mma7660"].get("ok"):
                    update("sensor_level_x", out["mma7660"].get("x_g"), "HW.POSENSORS.MMA7660")
                    update("sensor_level_y", out["mma7660"].get("y_g"), "HW.POSENSORS.MMA7660")
                    update("sensor_level_z", out["mma7660"].get("z_g"), "HW.POSENSORS.MMA7660")
                if out["mcp3425"].get("ok"):
                    update("sensor_adc_mcp3425_v", out["mcp3425"].get("volts"), "HW.POSENSORS.MCP3425")
            except Exception:
                pass
        return out

    def read_xyz_poksyg_once(self, update: Optional[Callable[[str, Any, str], None]] = None) -> Dict[str, Any]:
        """XYZ z Poksyg/REC: rec_p41, rec_p42, rec_p43 jako sensor_level_x/y/z."""
        out: Dict[str, Any] = {"ok": False, "values": {}, "errors": []}
        try:
            dev = self.get_device("REC")
            if dev is None:
                out["errors"].append("REC not connected")
                return out
            res = self._call_device("REC", "PK_AnalogIOGet")
            if not res.get("ok"):
                out["errors"].append(res.get("error") or "PK_AnalogIOGet failed")
                return out
            pins = dev.device.contents.Pins
            for axis, (_board, pin, signal_name) in self.POKSYG_XYZ_ANALOG.items():
                raw = int(pins[int(pin) - 1].AnalogValue)
                volts = 3.3 * raw / 4095.0
                out["values"][axis] = {"pin": pin, "signal": signal_name, "raw": raw, "volts": volts}
                if update:
                    update(signal_name, raw, "HW.REC.XYZ")
                    update(f"{signal_name}_v", volts, "HW.REC.XYZ")
            out["ok"] = True
        except Exception as exc:
            out["errors"].append(str(exc))
        return out

    def read_tfluna_uart_once(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 0.15) -> Dict[str, Any]:
        """TF-Luna jest UART/USB, nie PoKeys I2C. Metoda jest w core, ale wymaga podanego portu."""
        if not port:
            return {"ok": False, "sensor": "TF-Luna", "kind": "UART", "error": "UART port not configured"}
        try:
            import serial  # type: ignore
            with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
                data = ser.read(9)
            if len(data) < 9 or data[0] != 0x59 or data[1] != 0x59:
                return {"ok": False, "sensor": "TF-Luna", "kind": "UART", "error": "bad frame", "raw": list(data)}
            dist_cm = data[2] | (data[3] << 8)
            strength = data[4] | (data[5] << 8)
            temp_c = ((data[6] | (data[7] << 8)) / 8.0) - 256.0
            return {"ok": True, "sensor": "TF-Luna", "kind": "UART", "distance_cm": dist_cm, "strength": strength, "temp_c": temp_c}
        except Exception as exc:
            return {"ok": False, "sensor": "TF-Luna", "kind": "UART", "error": str(exc)}

    def read_easy_sensors_once(self, board: str = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_EasySensorsValueGetAll")
        if not res.get("ok"):
            return res
        try:
            device = self.get_device(board)
            values = {}
            count = int(device.device.contents.info.iEasySensors)
            for idx in range(max(0, min(count, 16))):
                sensor = device.device.contents.EasySensors[idx]
                values[str(idx)] = int(getattr(sensor, "sensorValue", 0))
            return {"ok": True, "values": values}
        except Exception as exc:
            return {"ok": False, "values": {}, "error": str(exc)}

    def set_poextbus_signal(self, sig: TarzanSygnal, value: Any) -> bool:
        # Na razie bezpieczna metoda: rozpoznaje PoExtBus i zapisuje tylko gdy sygnał ma pin/kanal.
        board = "REC" if str(sig.nazwa).startswith("rec_") else "PLAY"
        device = self.get_device(board)
        if device is None:
            return False
        try:
            if not self._call_device(board, "PK_PoExtBusGet").get("ok"):
                return False
            idx = None
            if sig.pin is not None:
                idx = int(sig.pin)
            elif sig.kanal and str(sig.kanal).isdigit():
                idx = int(sig.kanal)
            if idx is None:
                return False
            idx = max(0, min(79, idx))
            byte_i, bit_i = divmod(idx, 8)
            if value:
                device.device.contents.PoExtBusData[byte_i] |= (1 << bit_i)
            else:
                device.device.contents.PoExtBusData[byte_i] &= ~(1 << bit_i)
            return self._call_device(board, "PK_PoExtBusSet").get("ok")
        except Exception as exc:
            self.logger.debug("PoExtBus write %s failed: %s", sig.nazwa, exc)
            return False

    def get_pulse_engine_status(self, device: Any) -> Dict[str, Any]:
        status: Dict[str, Any] = {}
        try:
            board = "PLAY"
            # Szukamy boardu dla danego device, by poprawnie wołać _call_device
            for b, d in self.devices.items():
                if d == device:
                    board = b
                    break
            res = self._call_device(board, "PK_PEv2_StatusGet")
            if not res.get("ok"):
                return res
            pe = device.device.contents.PEv2
            status["state"] = int(getattr(pe, "PulseEngineState", 0))
            axes = {}
            for idx in range(8):
                try:
                    axes[str(idx)] = {
                        "state": int(pe.AxesState[idx]),
                        "pos": int(pe.CurrentPosition[idx]),
                    }
                except Exception:
                    break
            status["axes"] = axes
            status["ok"] = True
        except Exception as exc:
            status["error"] = str(exc)
            status["ok"] = False
        return status

    def set_pulse_axis_enable(self, device: Any, axis_idx: int, enabled: bool) -> bool:
        try:
            axis_idx = int(axis_idx)
            if not self._call_device(device, "PK_PEv2_AxisConfigurationGet", axis_idx).get("ok"):
                return False
            if enabled:
                device.device.contents.PEv2.AxesConfig[axis_idx] |= 0x01
            else:
                device.device.contents.PEv2.AxesConfig[axis_idx] &= ~0x01
            return self._call_device(device, "PK_PEv2_AxisConfigurationSet", axis_idx).get("ok")
        except Exception as exc:
            self.logger.debug("PE axis enable failed axis=%s: %s", axis_idx, exc)
            return False

    def set_pulse_axis_position(self, device: Any, axis_idx: int, target_pos: int) -> bool:
        """Ustawia pozycję osi Pulse Engine przez jeden wspólny tor TARZAN PoKeys."""
        try:
            axis_idx = int(axis_idx)
            target_pos = int(target_pos)
            if not self._call_device(device, "PK_PEv2_StatusGet").get("ok"):
                return False
            device.device.contents.PEv2.Axes[axis_idx].Position = target_pos
            return self._call_device(device, "PK_PEv2_PositionSet").get("ok")
        except Exception as exc:
            self.logger.debug("PE position set failed axis=%s target=%s: %s", axis_idx, target_pos, exc)
            return False

    def write_pulse_signal(self, sig: TarzanSygnal, value: Any) -> bool:
        # Ruch właściwy zostaje w Snajper/PARcore/HardwareBridge. Tu jest punkt wejścia biblioteki.
        # Nie generujemy ruchu w ciemno, jeśli sygnał nie ma jawnego kanału osi.
        device = self._device_for_signal(sig)
        if device is None:
            return False
        if sig.nazwa.endswith("_en"):
            axis_idx = self.axis_index_from_signal(sig)
            if axis_idx is not None:
                return self.set_pulse_axis_enable(device, axis_idx, bool(value))
        return True

    def axis_index_from_signal(self, sig: TarzanSygnal) -> Optional[int]:
        if sig.kanal:
            text = str(sig.kanal).upper()
            for idx, key in enumerate(["X", "Y", "Z", "A", "B", "C", "D", "E"]):
                if text.startswith(key) or f"ID{idx+1}" in text:
                    return idx
            if text.isdigit():
                return int(text)
        name = sig.nazwa.lower()
        mapping = ["cam_h", "cam_v", "focus", "arm_tilt", "arm_h", "arm_v", "cart"]
        for idx, part in enumerate(mapping):
            if part in name:
                return idx
        return None

    # ------------------------------------------------------------------
    # LKS-N5 widoczne testy sprzętu — jedyny tor przez tarzanPoKeys
    # ------------------------------------------------------------------
    @staticmethod
    def _lcd_text(value: str, width: int = 20) -> str:
        repl = str(value).replace("ł", "l").replace("Ł", "L").replace("ó", "o").replace("Ó", "O")
        repl = repl.replace("ą", "a").replace("ę", "e").replace("ś", "s").replace("ż", "z").replace("ź", "z")
        repl = repl.replace("ń", "n").replace("ć", "c")
        return repl[:width]

    def _resolve_device_target(self, target: Any, default_board: str = "PLAY") -> Tuple[str, Any]:
        """Przyjmuje nazwę płytki PLAY/REC albo już otwarty uchwyt PoKeys."""
        if isinstance(target, str):
            board = target.upper()
            return board, self.get_device(board)
        for board, dev in self.devices.items():
            if dev is target:
                return board, dev
        return default_board.upper(), target

    def lcd_init(self, board: Any = "PLAY") -> Dict[str, Any]:
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            board, device = self._resolve_device_target(board, "PLAY")
            if device is None:
                return {"ok": False, "board": board, "error": f"{board} not connected"}
            try:
                lcd = device.device.contents.LCD
                lcd.Configuration = 2
                lcd.Rows = 2
                lcd.Columns = 16
                for name, args in (
                    ("PK_LCDConfigurationSet", []),
                    ("PK_LCDChangeMode", [0]),
                    ("PK_LCDInit", []),
                    ("PK_LCDClear", []),
                ):
                    res = self._call_device(board, name, *args)
                    if not res.get("ok"):
                        raise RuntimeError(f"{name} failed: {res.get('error') or res.get('rc')}")
                return {"ok": True, "board": board}
            except Exception as exc:
                return {"ok": False, "board": board, "error": str(exc)}

    def lcd_write_lines(self, board: Any, line1: str, line2: str) -> Dict[str, Any]:
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            board, device = self._resolve_device_target(board, "PLAY")
            if device is None:
                return {"ok": False, "board": board, "error": f"{board} not connected"}
            try:
                if not self._call_device(board, "PK_LCDMoveCursor", 1, 1).get("ok"):
                    raise RuntimeError("PK_LCDMoveCursor(1,1) failed")
                if not self._call_device(board, "PK_LCDPrint", self._lcd_text(line1, 16).ljust(16)).get("ok"):
                    raise RuntimeError("PK_LCDPrint line1 failed")
                if not self._call_device(board, "PK_LCDMoveCursor", 2, 1).get("ok"):
                    raise RuntimeError("PK_LCDMoveCursor(2,1) failed")
                if not self._call_device(board, "PK_LCDPrint", self._lcd_text(line2, 16).ljust(16)).get("ok"):
                    raise RuntimeError("PK_LCDPrint line2 failed")
                return {"ok": True, "board": board, "line1": line1, "line2": line2}
            except Exception as exc:
                return {"ok": False, "board": board, "error": str(exc)}

    def test_lcd_1602_once(self, visible: bool = False, boards: Iterable[str] = ("PLAY", "REC")) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ok": False, "boards": {}, "errors": []}
        for board in [str(b).upper() for b in boards]:
            if visible:
                init = self.lcd_init(board)
                if not init.get("ok"):
                    out["boards"][board] = init
                    out["errors"].append(f"{board}: {init.get('error')}")
                    continue
                self.lcd_write_lines(board, f"LKS-N5 {board}", "TEST LCD")
                time.sleep(0.25)
                final = self.lcd_write_lines(board, "BEZ BLEDOW", "GOTOWE")
                out["boards"][board] = final
                if not final.get("ok"):
                    out["errors"].append(f"{board}: {final.get('error')}")
            else:
                ok = self.test_board_once(board)
                out["boards"][board] = {"ok": ok, "board": board}
                if not ok:
                    out["errors"].append(f"{board}: board test failed")
        out["ok"] = not out["errors"]
        return out

    _MATRIX_FONT_5X7: Dict[str, List[int]] = {
        " ": [0, 0, 0, 0, 0], "O": [0x3E, 0x41, 0x41, 0x41, 0x3E], "K": [0x7F, 0x08, 0x14, 0x22, 0x41],
        "T": [0x01, 0x01, 0x7F, 0x01, 0x01], "E": [0x7F, 0x49, 0x49, 0x49, 0x41], "S": [0x46, 0x49, 0x49, 0x49, 0x31],
    }

    def _matrix_text_columns(self, text_value: str) -> List[int]:
        cols: List[int] = []
        for ch in self._lcd_text(text_value.upper(), 16):
            cols.extend(self._MATRIX_FONT_5X7.get(ch, self._MATRIX_FONT_5X7[" "]))
            cols.append(0)
        return cols or [0] * 8

    @staticmethod
    def _matrix_rows_from_columns(columns: Iterable[int]) -> List[int]:
        col_list = list(columns)
        rows: List[int] = []
        for row in range(8):
            value = 0
            for col in range(min(8, len(col_list))):
                if int(col_list[col]) & (1 << row):
                    value |= 1 << col
            rows.append(value & 0xFF)
        return rows

    def matrix_write_frame(self, board: Any = "REC", rows: Iterable[int] = ()) -> Dict[str, Any]:
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            board, device = self._resolve_device_target(board, "REC")
            if device is None:
                return {"ok": False, "board": board, "error": f"{board} not connected"}
            try:
                matrix_ptr = device.device.contents.MatrixLED
                matrix = matrix_ptr[0]
                matrix.displayEnabled = 1
                matrix.rows = 8
                matrix.columns = 8
                matrix.RefreshFlag = 1
                row_list = list(rows)
                for i in range(8):
                    matrix.data[i] = int(row_list[i]) & 0xFF if i < len(row_list) else 0
                res = self._call_device(board, "PK_MatrixLEDConfigurationSet")
                if not res.get("ok"):
                    raise RuntimeError(f"PK_MatrixLEDConfigurationSet failed: {res.get('error')}")
                res = self._call_device(board, "PK_MatrixLEDUpdate")
                if not res.get("ok"):
                    raise RuntimeError(f"PK_MatrixLEDUpdate failed: {res.get('error')}")
                return {"ok": True, "board": board}
            except Exception as exc:
                return {"ok": False, "board": board, "error": str(exc)}

    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:
        if not visible:
            return {"ok": self.test_board_once(board), "board": board}
        cols = self._matrix_text_columns("OK")
        res = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))
        time.sleep(0.20)
        self.matrix_write_frame(board, [0] * 8)
        return res

    def read_f_buttons_once(self) -> Dict[str, Any]:
        with self._lock:
            dev = self.get_device("REC")
            if dev is None:
                return {"ok": False, "values": {}, "error": "REC not connected"}
            try:
                values = {name: self.read_pin(dev, pin) for name, pin in self.F_BUTTON_PINS.items()}
                return {"ok": True, "values": values}
            except Exception as exc:
                return {"ok": False, "values": {}, "error": str(exc)}

    def blink_f_led_once(self, visible: bool = False) -> Dict[str, Any]:
        with self._lock:
            dev = self.get_device("REC")
            if dev is None:
                return {"ok": False, "error": "REC not connected"}
            try:
                if visible:
                    for pin in self.F_LED_PINS.values():
                        self.set_digital_output(dev, pin, 0)
                    for pin in self.F_LED_PINS.values():
                        self.set_digital_output(dev, pin, 1)
                        time.sleep(0.08)
                        self.set_digital_output(dev, pin, 0)
                return {"ok": True, "pins": dict(self.F_LED_PINS)}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

    def read_keypad_once(self) -> Dict[str, Any]:
        with self._lock:
            dev = self.get_device("PLAY")
            if dev is None:
                return {"ok": False, "error": "PLAY not connected"}
            try:
                res = self._call_device("PLAY", "PK_MatrixKBConfigurationGet")
                if not res.get("ok"):
                    raise RuntimeError(f"PK_MatrixKBConfigurationGet failed: {res.get('error')}")
                res = self._call_device("PLAY", "PK_MatrixKBStatusGet")
                if not res.get("ok"):
                    raise RuntimeError(f"PK_MatrixKBStatusGet failed: {res.get('error')}")
                values = [int(dev.device.contents.matrixKB.matrixKBvalues[i]) for i in range(128)]
                return {"ok": True, "values": values}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Pełniejsza warstwa wykonawcza PoKeys wg dokumentacji / bindingu
    # ------------------------------------------------------------------
    def _call_device(self, board: Any, method_name: str, *args: Any, default_board: str = "PLAY") -> Dict[str, Any]:
        """Jedno bezpieczne wejście do funkcji PK_*.

        Runtime TARZANA nie powinien wołać PK_* poza tym plikiem. Ta metoda
        daje wspólny lock, bramkę stanów, logical_wake, obsługę braku urządzenia
        i jednolity format wyniku dla metod wykonawczych.
        """
        with self._lock:
            if self._shutting_down:
                return {"ok": False, "skipped": True, "method": method_name, "reason": "shutting_down"}

            # 1. Inkrementacja liczników dla monitoringu - liczymy każde PK_
            if method_name.startswith("PK_"):
                self.call_counters[method_name] = self.call_counters.get(method_name, 0) + 1

            # 2. Bramka logiczna IDLE - kategoryczny zakaz fizycznego pollingu PK_*
            if self.state == "IDLE":
                # W IDLE pozwalamy TYLKO na całkowicie bezkosztowe sprawdzenie statusu połączenia
                if method_name not in ["PK_IsConnected", "PK_GetCurrentDeviceConnectionType"]:
                    return {"ok": False, "skipped": True, "method": method_name, "reason": "system_idle"}

            # 3. Bramka FAST_SAMPLE (Tryb KHR/Snajper 10ms - TYLKO SZYBKIE ODCZYTY)
            if self.state == "FAST_SAMPLE":
                allowed_fast = [
                    "PK_DigitalIOGet", "PK_AnalogIOGet", "PK_PEv2_StatusGet",
                    "PK_IsConnected", "PK_GetCurrentDeviceConnectionType",
                    "PK_DigitalCounterGet"
                ]
                # W FAST_SAMPLE kategorycznie zabraniamy zapisu, konfiguracji, LCD, Matrix, I2C
                if method_name not in allowed_fast:
                    return {"ok": False, "skipped": True, "method": method_name, "reason": "NOT_ALLOWED_IN_FAST_SAMPLE"}

            # 4. Bramka EXEC (Realne wykonanie ruchu/akcji)
            if self.state == "EXEC":
                allowed_exec = [
                    "PK_DigitalIOGet", "PK_AnalogIOGet", "PK_PEv2_StatusGet",
                    "PK_IsConnected", "PK_GetCurrentDeviceConnectionType",
                    "PK_DigitalCounterGet", "PK_DigitalIOSetSingle",
                    "PK_PinConfigurationGet", "PK_PinConfigurationSet",
                    "PK_PoExtBusSet", "PK_PoExtBusGet", "PK_PEv2_PositionSet",
                    "PK_SaveConfiguration", "PK_ClearConfiguration",
                    # EXEC obejmuje realny zapis akcesoriów z PAR (LCD/Matrix/FLED),
                    # ale nie jest używany do stałego pollingu ani I2C scanów.
                    "PK_LCDInit", "PK_LCDUpdate", "PK_LCDConfigurationGet", "PK_LCDConfigurationSet",
                    "PK_LCDClear", "PK_LCDPrint", "PK_LCDMoveCursor", "PK_LCDChangeMode",
                    "PK_MatrixLEDConfigurationGet", "PK_MatrixLEDConfigurationSet", "PK_MatrixLEDUpdate"
                ]
                if method_name not in allowed_exec:
                    return {"ok": False, "skipped": True, "method": method_name, "reason": "NOT_ALLOWED_IN_EXEC"}

            # 5. Bramka POINT_TEST / FULL_DIAGNOSTICS (Testy widoczne LKS / boot)
            if self.state in ["POINT_TEST", "FULL_DIAGNOSTICS"]:
                # Tu pozwalamy na wszystko co potrzebne do testów akcesoriów
                allowed_test = [
                    "PK_DigitalIOGet", "PK_AnalogIOGet", "PK_PEv2_StatusGet",
                    "PK_IsConnected", "PK_GetCurrentDeviceConnectionType",
                    "PK_DigitalCounterGet", "PK_DigitalIOSetSingle",
                    "PK_PoExtBusSet", "PK_PoExtBusGet", "PK_PEv2_PositionSet",
                    "PK_SaveConfiguration", "PK_ClearConfiguration",
                    "PK_DeviceDataGet", "PK_PinConfigurationGet", "PK_PinConfigurationSet",
                    "PK_LCDInit", "PK_LCDUpdate", "PK_LCDConfigurationGet", "PK_LCDConfigurationSet",
                    "PK_LCDClear", "PK_LCDPrint", "PK_LCDMoveCursor", "PK_LCDChangeMode",
                    "PK_MatrixLEDConfigurationGet", "PK_MatrixLEDConfigurationSet", "PK_MatrixLEDUpdate",
                    "PK_MatrixKBConfigurationGet", "PK_MatrixKBConfigurationSet", "PK_MatrixKBStatusGet",
                    "PK_I2CBusScanStart", "PK_I2CBusScanGetResults", "PK_I2CBusRead", "PK_I2CBusWrite", 
                    "PK_I2CBusWriteAndRead", "PK_PulseEngineSetup", "PK_PEv2_PulseEngineSetup",
                    "PK_PoStepDriverConfigurationGet", "PK_PoStepDriverConfigurationSet",
                    "PK_PoStep_ConfigurationGet", "PK_PoStep_StatusGet"
                ]
                if method_name not in allowed_test:
                    return {"ok": False, "skipped": True, "method": method_name, "reason": f"NOT_ALLOWED_IN_{self.state}"}

            resolved_board, device = self._resolve_device_target(board, default_board)
            if device is None:
                return {"ok": False, "board": resolved_board, "method": method_name, "error": f"{resolved_board} not connected"}
            try:
                fn = getattr(device, method_name, None)
                if fn is None:
                    return {"ok": False, "board": resolved_board, "method": method_name, "error": "method unavailable"}
                rc = fn(*args)
                # Dla większości metod PoKeys 0 to sukces, None/True też.
                # Metody typu GetResults zwracają listy - wtedy ok=True jeśli rc nie jest None.
                ok = (rc == 0 or rc is True or rc is None)
                if not ok and isinstance(rc, (list, bytes, str)):
                    ok = True
                return {"ok": ok, "board": resolved_board, "method": method_name, "rc": rc}
            except Exception as exc:
                return {"ok": False, "board": resolved_board, "method": method_name, "error": str(exc)}

    @staticmethod
    def _plain_value(value: Any, max_items: int = 32) -> Any:
        """Mały konwerter ctypes/list do prostego dict/list bez ciężkiego chodzenia po pamięci."""
        try:
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            if isinstance(value, bytes):
                return value[:max_items].hex()
            if hasattr(value, "value") and not hasattr(value, "_fields_"):
                return value.value
            if hasattr(value, "_fields_"):
                out: Dict[str, Any] = {}
                for name, _typ in list(value._fields_)[:max_items]:
                    try:
                        out[name] = TarzanPoKeys._plain_value(getattr(value, name), max_items=8)
                    except Exception:
                        out[name] = "<unreadable>"
                return out
            if hasattr(value, "__len__") and not isinstance(value, dict):
                return [TarzanPoKeys._plain_value(value[i], max_items=8) for i in range(min(len(value), max_items))]
            return str(value)
        except Exception:
            return str(value)

    def _device_snapshot(self, board: Any, section: Optional[str] = None, default_board: str = "PLAY") -> Dict[str, Any]:
        with self._lock:
            resolved_board, device = self._resolve_device_target(board, default_board)
            if device is None:
                return {"ok": False, "board": resolved_board, "error": f"{resolved_board} not connected"}
            try:
                root = device.device.contents
                if section:
                    return {"ok": True, "board": resolved_board, "section": section, "data": self._plain_value(getattr(root, section))}
                return {"ok": True, "board": resolved_board, "data": self._plain_value(root)}
            except Exception as exc:
                return {"ok": False, "board": resolved_board, "section": section, "error": str(exc)}

    # --- konfiguracja urządzenia / podstawy ---------------------------------
    def save_configuration(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_SaveConfiguration")

    def clear_configuration(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_ClearConfiguration")

    def get_connection_type(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_GetCurrentDeviceConnectionType")

    def get_device_data_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_DeviceDataGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "DeviceData")
            res["data"] = snap.get("data")
        return res

    def get_pin_configuration_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_PinConfigurationGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "Pins")
            res["pins"] = snap.get("data")
        return res

    def set_pin_configuration_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PinConfigurationSet")

    # --- GPIO / liczniki / analog --------------------------------------------
    def digital_io_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_DigitalIOGet")
        if res.get("ok"):
            values: Dict[str, Any] = {}
            b = str(board).upper()
            device = self.get_device(b)
            if device is not None:
                pins_ptr = device.device.contents.Pins
                for sig in self.signals("gpio_in"):
                    if str(sig.plytka).upper() == b and sig.pin is not None:
                        values[sig.nazwa] = 1 if pins_ptr[int(sig.pin) - 1].DigitalValueGet else 0
            res["values"] = values
        return res

    def digital_io_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_DigitalIOSet")

    def digital_io_set_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_DigitalIOSetGet")

    def digital_io_get_single_once(self, board: Any = "PLAY", pin: int = 1) -> Dict[str, Any]:
        res = self._call_device(board, "PK_DigitalIOGetSingle", int(pin) - 1)
        if res.get("ok"):
            res["pin"] = int(pin)
            res["value"] = int(res.get("rc", 0))
        return res

    def digital_counter_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_DigitalCounterGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "Pins")
            res["pins"] = snap.get("data")
        return res

    def is_counter_available_once(self, board: Any = "PLAY", pin: int = 1) -> Dict[str, Any]:
        return self._call_device(board, "PK_IsCounterAvailable", int(pin) - 1)

    def analog_io_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_AnalogIOGet")
        if res.get("ok"):
            values: Dict[str, Any] = {}
            b = str(board).upper()
            device = self.get_device(b)
            if device is not None:
                pins = device.device.contents.Pins
                for sig in self.signals("analog_in"):
                    if str(sig.plytka).upper() == b and sig.pin is not None:
                        values[sig.nazwa] = int(pins[int(sig.pin) - 1].AnalogValue)
            res["values"] = values
        return res

    def analog_filter_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_AnalogRCFilterGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "DeviceData")
            res["data"] = snap.get("data")
        return res

    def analog_filter_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_AnalogRCFilterSet")

    # --- PWM ------------------------------------------------------------------
    def pwm_configuration_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_PWMConfigurationGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "PWM")
            res["pwm"] = snap.get("data")
        return res

    def pwm_configuration_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PWMConfigurationSet")

    def pwm_update_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PWMUpdate")

    def pwm_set_direct_once(self, board: Any = "PLAY", period: int = 0, duty_cycles: Optional[Iterable[int]] = None) -> Dict[str, Any]:
        duty = list(duty_cycles or [])
        return self._call_device(board, "PK_PWMConfigurationSetDirectly", int(period), duty)

    def pwm_update_direct_once(self, board: Any = "PLAY", duty_cycles: Optional[Iterable[int]] = None) -> Dict[str, Any]:
        duty = list(duty_cycles or [])
        return self._call_device(board, "PK_PWMUpdateDirectly", duty)

    # --- enkodery -------------------------------------------------------------
    def encoder_configuration_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_EncoderConfigurationGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "Encoders")
            res["encoders"] = snap.get("data")
        return res

    def encoder_configuration_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_EncoderConfigurationSet")

    def encoder_values_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_EncoderValuesGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "Encoders")
            res["encoders"] = snap.get("data")
        return res

    def encoder_values_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_EncoderValuesSet")

    # --- LCD / Matrix config niskiego poziomu przez tarzanPoKeys -------------
    def lcd_configuration_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_LCDConfigurationGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "LCD")
            res["lcd"] = snap.get("data")
        return res

    def lcd_configuration_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_LCDConfigurationSet")

    def lcd_update_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_LCDUpdate")

    def matrix_led_configuration_get_once(self, board: Any = "REC") -> Dict[str, Any]:
        res = self._call_device(board, "PK_MatrixLEDConfigurationGet", default_board="REC")
        if res.get("ok"):
            snap = self._device_snapshot(board, "MatrixLED", default_board="REC")
            res["matrix"] = snap.get("data")
        return res

    def matrix_led_configuration_set_once(self, board: Any = "REC") -> Dict[str, Any]:
        return self._call_device(board, "PK_MatrixLEDConfigurationSet", default_board="REC")

    def matrix_led_update_once(self, board: Any = "REC") -> Dict[str, Any]:
        return self._call_device(board, "PK_MatrixLEDUpdate", default_board="REC")

    def matrix_keyboard_configuration_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        res = self._call_device(board, "PK_MatrixKBConfigurationGet")
        if res.get("ok"):
            snap = self._device_snapshot(board, "matrixKB")
            res["keyboard"] = snap.get("data")
        return res

    def matrix_keyboard_configuration_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_MatrixKBConfigurationSet")

    def matrix_keyboard_status_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self.read_keypad_once()

    # --- Pulse Engine / CNC / PoStep -----------------------------------------
    def pulse_engine_setup_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_PulseEngineSetup")

    def pulse_engine_state_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_PulseEngineStateSet")

    def pulse_engine_move_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_PulseEngineMove")

    def pulse_engine_move_pv_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_PulseEngineMovePV")

    def pulse_engine_status2_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_Status2Get")

    def pulse_engine_external_outputs_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_ExternalOutputsGet")

    def pulse_engine_external_outputs_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_ExternalOutputsSet")

    def pulse_engine_buffer_clear_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_BufferClear")

    def pulse_engine_reboot_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_PulseEngineReboot")

    def pulse_engine_homing_start_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_HomingStart")

    def pulse_engine_homing_finish_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_HomingFinish")

    def pulse_engine_probing_start_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_ProbingStart")

    def pulse_engine_probing_finish_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_ProbingFinish")

    def pulse_engine_threading_status_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_ThreadingStatusGet")

    def pulse_engine_threading_cancel_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_ThreadingCancel")

    def postep_configuration_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoStep_ConfigurationGet")

    def postep_configuration_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoStep_ConfigurationSet")

    def postep_status_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoStep_StatusGet")

    def postep_driver_configuration_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoStep_DriverConfigurationGet")

    def postep_driver_configuration_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoStep_DriverConfigurationSet")

    def internal_drivers_configuration_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_InternalDriversConfigurationGet")

    def internal_drivers_configuration_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PEv2_InternalDriversConfigurationSet")

    # --- EasySensors / 1-Wire -------------------------------------------------
    def easy_sensors_setup_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_EasySensorsSetupGet")

    def easy_sensors_setup_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_EasySensorsSetupSet")

    def one_wire_status_set_once(self, board: Any = "PLAY", activated: bool = True) -> Dict[str, Any]:
        return self._call_device(board, "PK_1WireStatusSet", 1 if activated else 0)

    def one_wire_status_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_1WireStatusGet")

    def one_wire_read_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_1WireRead")

    def one_wire_scan_once(self, board: Any = "PLAY", pin: int = 1, retries: int = 5) -> Dict[str, Any]:
        return self._call_device(board, "PK_1WireScan", int(pin) - 1, int(retries))

    def easy_sensor_configure_1wire_once(
        self,
        board: Any = "PLAY",
        slot: int = 0,
        pin: int = 1,
        rom: Optional[Iterable[int]] = None,
        reading_id: int = 0,
        period: int = 10,
        failsafe: int = 0,
    ) -> Dict[str, Any]:
        return self._call_device(board, "PK_EasySensorConfigure_1wire", int(slot), int(pin) - 1, list(rom or []), int(reading_id), int(period), int(failsafe))

    # --- PoExtBus / PoNET -----------------------------------------------------
    def poextbus_get_once(self, board: Any = "REC") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoExtBusGet", default_board="REC")

    def poextbus_set_once(self, board: Any = "REC") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoExtBusSet", default_board="REC")

    def ponet_status_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETGetPoNETStatus")

    def ponet_module_settings_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETGetModuleSettings")

    def ponet_module_status_request_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETGetModuleStatusRequest")

    def ponet_module_status_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETGetModuleStatus")

    def ponet_module_status_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETSetModuleStatus")

    def ponet_module_pwm_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETSetModulePWM")

    def ponet_module_light_request_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETGetModuleLightRequest")

    def ponet_module_light_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoNETGetModuleLight")

    # --- CAN / SPI / RTC ------------------------------------------------------
    def can_configure_once(self, board: Any = "PLAY", bitrate: int = 125000) -> Dict[str, Any]:
        return self._call_device(board, "PK_CANConfigure", int(bitrate))

    def can_register_filter_once(self, board: Any = "PLAY", frame_format: int = 0, can_id: int = 0) -> Dict[str, Any]:
        return self._call_device(board, "PK_CANRegisterFilter", int(frame_format), int(can_id))

    def can_flush_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_CANFlush")

    def spi_configure_once(self, board: Any = "PLAY", prescaler: int = 250, frame_format: int = 0) -> Dict[str, Any]:
        return self._call_device(board, "PK_SPIConfigure", int(prescaler), int(frame_format))

    def spi_write_once(self, board: Any = "PLAY", data: Optional[Iterable[int]] = None, pin_cs: int = 8) -> Dict[str, Any]:
        return self._call_device(board, "PK_SPIWrite", list(data or []), int(pin_cs))

    def spi_read_once(self, board: Any = "PLAY", read_len: int = 1) -> Dict[str, Any]:
        return self._call_device(board, "PK_SPIRead", int(read_len))

    def spi_transfer_once(self, board: Any = "PLAY", data: Optional[Iterable[int]] = None, pin_cs: int = 8) -> Dict[str, Any]:
        return self._call_device(board, "PK_SPI", list(data or []), int(pin_cs))

    def rtc_get_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_RTCGet")

    def rtc_set_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_RTCSet")

    # --- PoIL -----------------------------------------------------------------
    def poil_get_state_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoILGetState")

    def poil_set_core_state_once(self, board: Any = "PLAY", state: int = 0) -> Dict[str, Any]:
        return self._call_device(board, "PK_PoILSetCoreState", int(state))

    def poil_set_master_enable_once(self, board: Any = "PLAY", enabled: bool = False) -> Dict[str, Any]:
        return self._call_device(board, "PK_PoILSetMasterEnable", 1 if enabled else 0)

    def poil_reset_core_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoILResetCore")

    def poil_task_status_once(self, board: Any = "PLAY") -> Dict[str, Any]:
        return self._call_device(board, "PK_PoILTaskStatus")


    # ------------------------------------------------------------------
    # ŚWIĘTA KONFIGURACJA PLAY/REC wg core/tarzanZmienneSygnalowe.py
    # ------------------------------------------------------------------
    def project_board_contract(self, board: str) -> Dict[str, Any]:
        """Statyczny kontrakt PLAY/REC z core/tarzanPokABC.py.

        Brak ABC oznacza FAIL. tarzanPoKeys.py nie ma prawa samodzielnie
        udawać, że konfiguracja PLAY/REC jest poprawna.
        """
        board = str(board or "").upper()
        if self.pokabc is None:
            return {"ok": False, "board": board, "error": "ABC_NOT_AVAILABLE", "errors": ["ABC_NOT_AVAILABLE"]}
        return self.pokabc.board_contract(board)

    def project_configuration_contract(self) -> Dict[str, Any]:
        """Kontrakt całego zestawu PLAY+REC z core/tarzanPokABC.py."""
        if self.pokabc is None:
            return {"ok": False, "error": "ABC_NOT_AVAILABLE", "errors": ["ABC_NOT_AVAILABLE"], "boards": {}}
        return self.pokabc.configuration_contract()

    def _project_expected_role(self, sig: TarzanSygnal) -> str:
        typ = str(sig.typ or "").upper()
        direction = str(sig.kierunek or "").upper()
        hf = str(sig.hardware_function or "").upper()
        if typ == "RESERVED" or direction == "RESERVED":
            return "RESERVED"
        if hf == HW_ANALOG or typ == "ANALOG":
            return "ANALOG_IN"
        if hf == HW_LCD:
            return "LCD_SPECIAL"
        if hf == HW_MATRIX_LED:
            return "MATRIX_LED_SPECIAL"
        if hf == HW_KEYBOARD:
            return "KEYBOARD_SPECIAL"
        if hf == HW_I2C:
            return "I2C_SPECIAL"
        if hf == HW_POEXTBUS:
            return "POEXTBUS_SPECIAL"
        if hf == HW_PWM:
            return "PWM_SPECIAL" if direction == "OUT" else "PWM_CAPABLE_INPUT"
        if hf == HW_PULSE:
            if typ == "CTR" and direction == "OUT":
                return "PULSE_STEP_OUT"
            if direction == "OUT":
                return "PULSE_GPIO_OUT"
            if typ == "CTR":
                return "COUNTER_INPUT"
            return "PULSE_CAPABLE_INPUT"
        if typ == "CTR":
            return "COUNTER_INPUT" if direction == "IN" else "COUNTER_OUTPUT"
        if direction == "OUT":
            return "DIGITAL_OUT"
        if direction == "IN":
            return "DIGITAL_IN"
        if direction == "F" or typ == "F":
            return "SPECIAL"
        return "UNKNOWN"

    def _project_expected_cap_names(self, sig: TarzanSygnal) -> List[str]:
        """Nazwy enumów PoKeys dopuszczalne dla danego pinu.

        Dajemy kilka wariantów nazw, bo wrappery PoKeys różnie nazywają ePK_PinCap.
        Jeżeli dany enum nie istnieje w bindingu, walidacja nie zgaduje — zgłasza
        PIN_CAP_ENUM_UNAVAILABLE zamiast udawać OK.
        """
        typ = str(sig.typ or "").upper()
        direction = str(sig.kierunek or "").upper()
        hf = str(sig.hardware_function or "").upper()
        if typ == "RESERVED" or direction == "RESERVED":
            return []
        if hf == HW_ANALOG or typ == "ANALOG":
            return ["PK_PinCap_analogInput", "PK_PinCap_analog", "PK_PinCap_digitalInput"]
        if hf == HW_GPIO:
            if direction == "OUT":
                return ["PK_PinCap_digitalOutput", "PK_PinCap_digitalIO"]
            return ["PK_PinCap_digitalInput", "PK_PinCap_digitalIO"]
        if hf == HW_LCD:
            return ["PK_PinCap_LCD", "PK_PinCap_lcd", "PK_PinCap_digitalOutput"]
        if hf == HW_MATRIX_LED:
            return ["PK_PinCap_matrixLED", "PK_PinCap_MatrixLED", "PK_PinCap_digitalOutput"]
        if hf == HW_KEYBOARD:
            return ["PK_PinCap_matrixKeyboard", "PK_PinCap_Keyboard", "PK_PinCap_digitalInput"]
        if hf == HW_I2C:
            return ["PK_PinCap_I2C", "PK_PinCap_i2c"]
        if hf == HW_POEXTBUS:
            return ["PK_PinCap_PoExtBus", "PK_PinCap_poExtBus", "PK_PinCap_digitalOutput", "PK_PinCap_digitalInput"]
        if hf == HW_PWM:
            return ["PK_PinCap_PWM", "PK_PinCap_pwm", "PK_PinCap_digitalOutput", "PK_PinCap_digitalInput"]
        if hf == HW_PULSE:
            if direction == "OUT":
                return ["PK_PinCap_pulseEngine", "PK_PinCap_PulseEngine", "PK_PinCap_digitalOutput"]
            return ["PK_PinCap_digitalInput", "PK_PinCap_digitalIO"]
        if typ == "CTR":
            return ["PK_PinCap_digitalInput", "PK_PinCap_counter", "PK_PinCap_digitalIO"]
        if direction == "OUT":
            return ["PK_PinCap_digitalOutput", "PK_PinCap_digitalIO"]
        if direction == "IN":
            return ["PK_PinCap_digitalInput", "PK_PinCap_digitalIO"]
        return []

    def _pin_cap_values(self, cap_names: Iterable[str]) -> Dict[str, int]:
        values: Dict[str, int] = {}
        if ePK_PinCap is None:
            return values
        for name in cap_names:
            try:
                value = getattr(ePK_PinCap, str(name), None)
                if value is not None:
                    values[str(name)] = int(value)
            except Exception:
                continue
        return values

    def _read_pin_config_value(self, pin_obj: Any) -> Optional[int]:
        for attr in ("PinFunction", "pinFunction", "PinCap", "PinCapability"):
            try:
                if hasattr(pin_obj, attr):
                    return int(getattr(pin_obj, attr))
            except Exception:
                continue
        return None

    def _verify_signal_pin_against_device(self, board: str, sig: TarzanSygnal, pin_obj: Any, *, strict_pin_function: bool = True) -> Dict[str, Any]:
        expected_caps = self._project_expected_cap_names(sig)
        cap_values = self._pin_cap_values(expected_caps)
        actual_cap = self._read_pin_config_value(pin_obj)
        item: Dict[str, Any] = {
            "signal": sig.nazwa,
            "board": board,
            "pin": int(sig.pin or 0),
            "type": sig.typ,
            "direction": sig.kierunek,
            "hardware_function": sig.hardware_function,
            "hardware_label": sig.hardware_label,
            "role": self._project_expected_role(sig),
            "expected_pin_caps": expected_caps,
            "expected_pin_cap_values": cap_values,
            "actual_pin_function": actual_cap,
            "ok": True,
            "errors": [],
            "warnings": [],
        }
        if not sig.pin_is_fixed:
            item["errors"].append("PIN_NOT_FIXED_IN_SIGNAL_MAP")
        if str(sig.typ).upper() == "RESERVED" or str(sig.kierunek).upper() == "RESERVED":
            item["warnings"].append("RESERVED_PIN_NOT_ACTIVE_TESTED")
            return item
        if strict_pin_function and expected_caps and not cap_values:
            item["warnings"].append("PIN_CAP_ENUM_UNAVAILABLE")
        if strict_pin_function and cap_values and actual_cap is not None and actual_cap not in set(cap_values.values()):
            # Nie każdy pin PoKeys przechowuje funkcję specjalną tak samo, dlatego shared pins
            # traktujemy jako błąd tylko dla czystych GPIO/ANALOG; dla funkcji specjalnych jest FAIL_WARN
            # plus test specjalny niżej (LCD/Matrix/I2C/PoExtBus/Pulse).
            if str(sig.hardware_function).upper() in {HW_GPIO, HW_ANALOG} and not bool(sig.is_shared_pin):
                item["errors"].append("BAD_PIN_CONFIG")
            else:
                item["warnings"].append("PIN_FUNCTION_DIFFERS_FROM_EXPECTED_SPECIAL_OR_SHARED")
        item["ok"] = not item["errors"]
        return item


    def _abc_expected_pin_function(self, sig: TarzanSygnal) -> Optional[int]:
        """Bazowa funkcja pinu wg TARZAN ABC.

        Oparta o dokumentację PoKeys: pin ma bazową funkcję digital input,
        digital output albo analog input; funkcje specjalne LCD/Matrix/I2C/
        PoExtBus/Pulse mają osobne ACK, ale pin musi mieć bezpieczny bazowy
        kierunek. Nie generuje ruchu osi.
        """
        if ePK_PinCap is None:
            return None
        typ = str(sig.typ or "").upper()
        direction = str(sig.kierunek or "").upper()
        hf = str(sig.hardware_function or "").upper()
        try:
            if typ == "ANALOG" or hf == HW_ANALOG:
                return int(ePK_PinCap.PK_PinCap_analogInput)
            if typ == "RESERVED" or direction == "RESERVED" or hf in {HW_RESERVED, HW_SYSTEM}:
                restricted = getattr(ePK_PinCap, "PK_PinCap_pinRestricted", None)
                if restricted is not None:
                    return int(restricted)
                return int(ePK_PinCap.PK_PinCap_digitalInput)
            if direction == "OUT":
                return int(ePK_PinCap.PK_PinCap_digitalOutput)
            if direction == "IN":
                return int(ePK_PinCap.PK_PinCap_digitalInput)
            if typ == "F":
                return int(ePK_PinCap.PK_PinCap_digitalOutput)
        except Exception:
            return None
        return None

    def _abc_safe_output_value(self, sig: TarzanSygnal) -> Optional[int]:
        """Domyślny stan bezpieczny TARZAN po konfiguracji ABC.

        WAŻNE PoKeys: dla zwykłego nieodwróconego wyjścia cyfrowego zapis
        wartości 0 daje fizycznie stan wysoki ok. 3.3 V, a zapis 1 daje
        fizycznie stan niski 0 V. Dlatego bezpieczne OFF/LOW dla TARZAN to
        tutaj wartość zapisywana do PoKeys = 1.

        Cel: LED off, ENABLE off, STEP low, bridge/mass/auto off.
        Nie odpalamy PulseEngineMove, MovePV ani żadnego ruchu osi.
        """
        if str(sig.kierunek or "").upper() != "OUT":
            return None

        # Fizyczny LOW/OFF na PoKeys digital output. Nie zmieniać na 0:
        # 0 w API PoKeys daje fizycznie HIGH na nieodwróconym wyjściu.
        return 1

    def apply_project_board_configuration_once(self, board: str = "PLAY", *, save_to_flash: bool = True) -> Dict[str, Any]:
        """Ustawia JEDNĄ płytkę PLAY/REC według ABC i zapisuje do PoKeys.

        To jest restore-once dla starego setupu płytki. Nie działa w pętli,
        nie generuje STEP, nie uruchamia Pulse Engine move.
        """
        board = str(board or "").upper()
        out: Dict[str, Any] = {"ok": False, "board": board, "applied": 0, "safe_outputs": 0, "saved": False, "errors": [], "warnings": []}
        if self.pokabc is None:
            out["errors"].append("ABC_NOT_AVAILABLE")
            return out
        contract = self.project_board_contract(board)
        if not contract.get("ok"):
            out["errors"].append("ABC_CONTRACT_FAIL")
            out["contract_errors"] = contract.get("errors", [])
            return out
        with self._lock:
            old_state = self.state
            self.set_state("POINT_TEST")
            try:
                dev = self.get_device(board)
                if dev is None:
                    out["errors"].append("NO_DEVICE")
                    return out
                data_res = self._call_device(board, "PK_DeviceDataGet")
                if not data_res.get("ok"):
                    out["errors"].append(f"PK_DeviceDataGet:{data_res.get('error') or data_res.get('rc')}")
                    return out
                try:
                    actual_serial = int(getattr(dev.device.contents.DeviceData, "SerialNumber", 0))
                    ident = self.pokabc.verify_board_identity_from_serial(board, actual_serial)
                    out["identity"] = ident
                    if not ident.get("ok"):
                        out["errors"].append("BAD_SERIAL")
                        return out
                except Exception as exc:
                    out["errors"].append(f"SERIAL_READ_ERROR:{exc}")
                    return out

                cfg_get = self._call_device(board, "PK_PinConfigurationGet")
                if not cfg_get.get("ok"):
                    out["errors"].append(f"PK_PinConfigurationGet:{cfg_get.get('error') or cfg_get.get('rc')}")
                    return out

                pins_ptr = dev.device.contents.Pins
                board_signals = [s for s in WSZYSTKIE_SYGNALY.values() if str(s.plytka or "").upper() == board and s.pin is not None]
                for sig in sorted(board_signals, key=lambda s: int(s.pin or 999)):
                    expected = self._abc_expected_pin_function(sig)
                    if expected is None:
                        out["warnings"].append(f"P{sig.pin}:{sig.nazwa}:NO_EXPECTED_PIN_FUNCTION")
                        continue
                    try:
                        pins_ptr[int(sig.pin) - 1].PinFunction = int(expected)
                        out["applied"] += 1
                    except Exception as exc:
                        out["errors"].append(f"P{sig.pin}:{sig.nazwa}:PIN_APPLY_ERROR:{exc}")

                if out["errors"]:
                    return out
                cfg_set = self._call_device(board, "PK_PinConfigurationSet")
                out["pin_configuration_set"] = cfg_set
                if not cfg_set.get("ok"):
                    out["errors"].append(f"PK_PinConfigurationSet:{cfg_set.get('error') or cfg_set.get('rc')}")
                    return out

                # Default safe state: wszystkie OUT ustawiamy w fizyczne LOW/OFF.
                # W PoKeys zapis 1 oznacza fizycznie 0 V na nieodwróconym wyjściu.
                for sig in sorted(board_signals, key=lambda s: int(s.pin or 999)):
                    value = self._abc_safe_output_value(sig)
                    if value is None:
                        continue
                    try:
                        pin_idx = int(sig.pin) - 1
                        pins_ptr[pin_idx].DigitalValueSet = int(value)
                        res = self._call_device(board, "PK_DigitalIOSetSingle", pin_idx, int(value))
                        if not res.get("ok"):
                            out["warnings"].append(f"P{sig.pin}:{sig.nazwa}:SAFE_OUTPUT_SET_WARN:{res.get('error') or res.get('rc')}")
                        else:
                            out["safe_outputs"] += 1
                    except Exception as exc:
                        out["warnings"].append(f"P{sig.pin}:{sig.nazwa}:SAFE_OUTPUT_ERROR:{exc}")

                # Odczyt po ustawieniu, potem zapis do pamięci PoKeys.
                self._call_device(board, "PK_DigitalIOGet")
                self._call_device(board, "PK_PinConfigurationGet")
                if save_to_flash:
                    save_res = self.save_configuration(board)
                    out["save"] = save_res
                    out["saved"] = bool(save_res.get("ok"))
                    if not save_res.get("ok"):
                        out["errors"].append(f"PK_SaveConfiguration:{save_res.get('error') or save_res.get('rc')}")
                        return out
                out["ok"] = not out["errors"]
                return out
            finally:
                self.set_state(old_state)

    def apply_project_configuration_once(self, *, save_to_flash: bool = True) -> Dict[str, Any]:
        """Ustawia PLAY i REC według ABC dokładnie raz."""
        play = self.apply_project_board_configuration_once("PLAY", save_to_flash=save_to_flash)
        rec = self.apply_project_board_configuration_once("REC", save_to_flash=save_to_flash)
        errors: List[str] = []
        warnings: List[str] = []
        for res in (play, rec):
            errors.extend([f"{res.get('board')}:{e}" for e in res.get("errors", [])])
            warnings.extend([f"{res.get('board')}:{w}" for w in res.get("warnings", [])])
        return {"ok": not errors, "boards": {"PLAY": play, "REC": rec}, "errors": errors, "warnings": warnings, "restore_once": True}

    def apply_default_safe_state_once(self) -> Dict[str, Any]:
        """Zeruje bezpieczne wyjścia PLAY/REC po poprawnym ABC, bez zapisu pętlowego."""
        out: Dict[str, Any] = {"ok": True, "boards": {}, "errors": [], "warnings": []}
        for board in ("PLAY", "REC"):
            board_res: Dict[str, Any] = {"ok": True, "board": board, "safe_outputs": 0, "warnings": [], "errors": []}
            with self._lock:
                old_state = self.state
                self.set_state("POINT_TEST")
                try:
                    dev = self.get_device(board)
                    if dev is None:
                        board_res["errors"].append("NO_DEVICE")
                        board_res["ok"] = False
                    else:
                        for sig in sorted(WSZYSTKIE_SYGNALY.values(), key=lambda s: int(s.pin or 999)):
                            if str(sig.plytka or "").upper() != board or sig.pin is None:
                                continue
                            value = self._abc_safe_output_value(sig)
                            if value is None:
                                continue
                            pin_idx = int(sig.pin) - 1
                            res = self._call_device(board, "PK_DigitalIOSetSingle", pin_idx, int(value))
                            if res.get("ok"):
                                board_res["safe_outputs"] += 1
                            else:
                                board_res["warnings"].append(f"P{sig.pin}:{sig.nazwa}:{res.get('error') or res.get('rc')}")
                finally:
                    self.set_state(old_state)
            out["boards"][board] = board_res
            out["errors"].extend([f"{board}:{e}" for e in board_res.get("errors", [])])
            out["warnings"].extend([f"{board}:{w}" for w in board_res.get("warnings", [])])
        out["ok"] = not out["errors"]
        return out

    def configure_and_verify_project_once(self, *, force_i2c: bool = False, restore_if_needed: bool = True) -> Dict[str, Any]:
        """Verify ABC; gdy wykryje stary setup, restore ABC RAZ, save, readback, verify.

        Brak pętli. Jedno podejście restore na start albo po wykrytym rozjeździe.
        """
        first = self.verify_project_configuration_once(force_i2c=force_i2c)
        if first.get("ok"):
            safe = self.apply_default_safe_state_once()
            first["abc_confirmed"] = True
            first["restored"] = False
            first["safe_state"] = safe
            self._abc_boot_confirmed = True
            self._abc_last_result = first
            self.logger.info("POKEYS ABC OK: PLAY/REC already confirmed; default safe state applied once")
            return first
        if not restore_if_needed:
            first["abc_confirmed"] = False
            self._abc_boot_confirmed = False
            self._abc_last_result = first
            return first

        self.logger.warning("POKEYS ABC RESTORE_ONCE: config mismatch detected, applying TARZAN ABC to PLAY/REC once")
        apply_res = self.apply_project_configuration_once(save_to_flash=True)
        second = self.verify_project_configuration_once(force_i2c=force_i2c)
        safe = self.apply_default_safe_state_once() if second.get("ok") else {"ok": False, "skipped": True, "reason": "ABC_VERIFY_AFTER_RESTORE_FAILED"}
        result = {
            "ok": bool(second.get("ok")),
            "abc_confirmed": bool(second.get("ok")),
            "restored": True,
            "first_verify": first,
            "apply": apply_res,
            "second_verify": second,
            "safe_state": safe,
            "errors": [] if second.get("ok") else list(second.get("errors", [])),
            "warnings": list(first.get("warnings", [])) + list(apply_res.get("warnings", [])) + list(second.get("warnings", [])),
        }
        self._abc_boot_confirmed = bool(result.get("ok"))
        self._abc_last_result = result
        if result.get("ok"):
            self.logger.info("POKEYS ABC RESTORE_ONCE OK: PLAY/REC saved, read back and confirmed")
        else:
            self.logger.error("POKEYS ABC RESTORE_ONCE FAIL: %s", "; ".join(str(x) for x in result.get("errors", [])[:20]))
        return result

    def verify_project_board_configuration_once(
        self,
        board: str = "PLAY",
        *,
        strict_pin_function: bool = True,
        check_special: bool = True,
        force_i2c: bool = False,
    ) -> Dict[str, Any]:
        """Twardy audyt jednej płyty PoKeys względem mapy TARZANA.

        Sprawdza:
        - czy podłączona jest właściwa płytka PLAY/REC po serialu,
        - czy konfiguracja pinów z PoKeys jest czytelna,
        - czy każdy fizyczny pin z tarzanZmienneSygnalowe.py pasuje do projektu,
        - czy funkcje specjalne odpowiadają swojej grupie: LCD/Matrix/Keyboard/I2C/PoExtBus/Pulse,
        - bez ruchu osi i bez stałego pollingu.
        """
        board = str(board or "").upper()
        if self.pokabc is None:
            return {"ok": False, "board": board, "error": "ABC_NOT_AVAILABLE", "errors": ["ABC_NOT_AVAILABLE"], "abc_confirmed": False}
        abc_static = self.pokabc.confirm_signal_map_abc()
        if not abc_static.get("ok"):
            return {"ok": False, "board": board, "error": "ABC_SIGNAL_MAP_FAIL", "errors": abc_static.get("errors", []), "abc_confirmed": False, "abc": abc_static}
        contract = self.project_board_contract(board)
        if not contract.get("ok"):
            return {**contract, "abc_confirmed": False}
        out: Dict[str, Any] = {
            "ok": False,
            "abc_confirmed": False,
            "abc_source": "core/tarzanPokABC.py",
            "board": board,
            "expected_serial": self.BOARDS.get(board),
            "serial_ok": False,
            "pin_config_ok": False,
            "pins_checked": 0,
            "pins": {},
            "special": {},
            "errors": [],
            "warnings": [],
        }
        with self._lock:
            old_state = self.state
            self.set_state("POINT_TEST")
            try:
                dev = self.get_device(board)
                if dev is None:
                    out["errors"].append("NO_DEVICE")
                    return out
                data_res = self._call_device(board, "PK_DeviceDataGet")
                if not data_res.get("ok"):
                    out["errors"].append(f"PK_DeviceDataGet:{data_res.get('error') or data_res.get('rc')}")
                    return out
                try:
                    serial = int(getattr(dev.device.contents.DeviceData, "SerialNumber", 0))
                    ident = self.pokabc.verify_board_identity_from_serial(board, serial) if self.pokabc is not None else {"ok": False, "error": "ABC_NOT_AVAILABLE"}
                    out["actual_serial"] = serial
                    out["serial_ok"] = bool(ident.get("ok"))
                    out["identity"] = ident
                    if not out["serial_ok"]:
                        out["errors"].append(ident.get("error") or "BAD_BOARD_SERIAL")
                except Exception as exc:
                    out["errors"].append(f"SERIAL_READ_ERROR:{exc}")

                cfg_res = self._call_device(board, "PK_PinConfigurationGet")
                if not cfg_res.get("ok"):
                    out["errors"].append(f"PK_PinConfigurationGet:{cfg_res.get('error') or cfg_res.get('rc')}")
                    return out
                out["pin_config_ok"] = True
                pins_ptr = dev.device.contents.Pins
                for sig in sorted(WSZYSTKIE_SYGNALY.values(), key=lambda s: int(s.pin or 999)):
                    if str(sig.plytka or "").upper() != board or sig.pin is None:
                        continue
                    pin = int(sig.pin)
                    item = self.pokabc.verify_signal_pin_against_device(board, sig, pins_ptr[pin - 1], cap_enum=ePK_PinCap, strict_pin_function=strict_pin_function) if self.pokabc is not None else self._verify_signal_pin_against_device(board, sig, pins_ptr[pin - 1], strict_pin_function=strict_pin_function)
                    out["pins"][str(pin)] = item
                    out["pins_checked"] += 1
                    for err in item.get("errors", []):
                        out["errors"].append(f"P{pin}:{sig.nazwa}:{err}")
                    for warn in item.get("warnings", []):
                        out["warnings"].append(f"P{pin}:{sig.nazwa}:{warn}")

                if check_special:
                    out["special"] = self.verify_project_special_functions_once(board, force_i2c=force_i2c)
                    for err in out["special"].get("errors", []):
                        out["errors"].append(f"SPECIAL:{err}")
                    for warn in out["special"].get("warnings", []):
                        out["warnings"].append(f"SPECIAL:{warn}")
                out["ok"] = bool(out["serial_ok"] and out["pin_config_ok"] and not out["errors"])
                out["abc_confirmed"] = bool(out["ok"])
                return out
            finally:
                self.set_state(old_state)

    def verify_project_special_functions_once(self, board: str = "PLAY", *, force_i2c: bool = False) -> Dict[str, Any]:
        """Sprawdza funkcje specjalne przypisane w mapie sygnałów dla PLAY/REC."""
        board = str(board or "").upper()
        out: Dict[str, Any] = {"ok": False, "board": board, "checks": {}, "errors": [], "warnings": []}
        board_signals = [s for s in WSZYSTKIE_SYGNALY.values() if str(s.plytka or "").upper() == board]
        hfs = {str(s.hardware_function or "").upper() for s in board_signals}
        if HW_LCD in hfs:
            res = self._call_device(board, "PK_LCDConfigurationGet")
            out["checks"]["LCD"] = res
            if not res.get("ok"):
                out["errors"].append(f"LCD_CONFIG_NO_ACK:{res.get('error') or res.get('rc')}")
        if HW_MATRIX_LED in hfs:
            res = self._call_device(board, "PK_MatrixLEDConfigurationGet")
            out["checks"]["MATRIX_LED"] = res
            if not res.get("ok"):
                out["errors"].append(f"MATRIX_CONFIG_NO_ACK:{res.get('error') or res.get('rc')}")
        if HW_KEYBOARD in hfs:
            res = self._call_device(board, "PK_MatrixKBConfigurationGet")
            out["checks"]["KEYBOARD"] = res
            if not res.get("ok"):
                out["errors"].append(f"KEYBOARD_CONFIG_NO_ACK:{res.get('error') or res.get('rc')}")
        if HW_POEXTBUS in hfs:
            res = self._call_device(board, "PK_PoExtBusGet")
            out["checks"]["POEXTBUS"] = res
            if not res.get("ok"):
                out["errors"].append(f"POEXTBUS_NO_ACK:{res.get('error') or res.get('rc')}")
        if HW_PULSE in hfs:
            dev = self.get_device(board)
            res = self.get_pulse_engine_status(dev) if dev is not None else {"ok": False, "error": "NO_DEVICE"}
            out["checks"]["PULSE_ENGINE"] = res
            if not res.get("ok"):
                out["errors"].append(f"PULSE_ENGINE_NO_ACK:{res.get('error') or res.get('rc')}")
        if HW_I2C in hfs:
            if force_i2c:
                old_scan = self._runtime_i2c_scan_enabled
                self._runtime_i2c_scan_enabled = True
                try:
                    res = self.scan_i2c_once(board, force=True, cache_ttl_s=0)
                finally:
                    self._runtime_i2c_scan_enabled = old_scan
                out["checks"]["I2C"] = res
                if not res.get("ok"):
                    out["errors"].append(f"I2C_SCAN_NO_ACK:{res.get('error') or res.get('reason')}")
            else:
                out["checks"]["I2C"] = {"ok": False, "skipped": True, "reason": "force_i2c_false"}
                out["warnings"].append("I2C_SCAN_SKIPPED_SET_force_i2c_TRUE_FOR_PHYSICAL_SCAN")
        out["ok"] = not out["errors"]
        return out

    def verify_project_configuration_once(self, *, force_i2c: bool = False) -> Dict[str, Any]:
        """Audyt obu płytek PLAY+REC względem świętej mapy sygnałów."""
        play = self.verify_project_board_configuration_once("PLAY", force_i2c=force_i2c)
        rec = self.verify_project_board_configuration_once("REC", force_i2c=force_i2c)
        errors = []
        warnings = []
        for board_res in (play, rec):
            errors.extend([f"{board_res.get('board')}:{e}" for e in board_res.get("errors", [])])
            warnings.extend([f"{board_res.get('board')}:{w}" for w in board_res.get("warnings", [])])
        return {"ok": not errors, "boards": {"PLAY": play, "REC": rec}, "errors": errors, "warnings": warnings}

    def assert_project_configuration_once(self, *, force_i2c: bool = False) -> Dict[str, Any]:
        """Jednoznaczny test świętości konfiguracji PLAY/REC dla boot/LKS.

        Brak potwierdzenia z core/tarzanPokABC.py = błąd krytyczny.
        """
        if self.pokabc is None:
            res = {"ok": False, "error": "ABC_NOT_AVAILABLE", "errors": ["ABC_NOT_AVAILABLE"], "abc_confirmed": False}
            self._abc_boot_confirmed = False
            self._abc_last_result = res
            self.logger.error("POKEYS ABC FAIL: core/tarzanPokABC.py unavailable")
            return res
        res = self.configure_and_verify_project_once(force_i2c=force_i2c, restore_if_needed=True)
        res["abc_confirmed"] = bool(res.get("ok"))
        self._abc_boot_confirmed = bool(res.get("ok"))
        self._abc_last_result = res
        if res.get("ok"):
            if res.get("restored"):
                self.logger.info("POKEYS ABC OK: restored once, saved and confirmed by core/tarzanPokABC.py")
            else:
                self.logger.info("POKEYS ABC OK: PLAY/REC confirmed by core/tarzanPokABC.py")
        else:
            self.logger.error("POKEYS ABC FAIL: %s", "; ".join(str(x) for x in res.get("errors", [])[:20]))
        return res


    def test_cnc_axis_link_once(self, axis_signals: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        """Twardy test toru osi do płytki CNC/PoExtBus bez ruchu mechanicznego.

        Ten test jest dla LKS point-test osi. Sprawdza fundament ABC oraz realne ACK
        z PoKeys dla toru CNC: Pulse Engine + PoExtBusOC16-CNC. Nie wykonuje
        PK_PEv2_Move, nie generuje STEP, nie zmienia pozycji.
        """
        signals = [str(x) for x in (axis_signals or []) if str(x or "")]
        out: Dict[str, Any] = {
            "ok": False,
            "source": "tarzanPoKeys.test_cnc_axis_link_once",
            "signals": signals,
            "checks": {},
            "errors": [],
            "warnings": [],
        }

        # ABC jest warunkiem wejścia. Bez tego nie ma sensu testować CNC.
        abc = self.abc_last_result()
        if not abc.get("ok"):
            abc = self.assert_project_configuration_once(force_i2c=False)
        out["checks"]["ABC"] = abc
        if not abc.get("ok"):
            out["errors"].append("ABC_NOT_CONFIRMED")
            out["ok"] = False
            return out

        play = self.get_device("PLAY")
        rec = self.get_device("REC")
        if play is None:
            out["errors"].append("PLAY_NOT_CONNECTED")
        if rec is None:
            out["errors"].append("REC_NOT_CONNECTED")

        # Oś/Pulse Engine: ACK z PLAY. To potwierdza tor PoKeys dla osi bez ruchu.
        if play is not None:
            pulse = self.get_pulse_engine_status(play)
            out["checks"]["PULSE_ENGINE_PLAY"] = pulse
            if not pulse.get("ok"):
                out["errors"].append(f"PULSE_ENGINE_NO_ACK:{pulse.get('error') or pulse.get('rc')}")

        # Płytka CNC jest po torze PoExtBus/REC w projekcie. Tu wymagamy ACK.
        if rec is not None:
            poext = self.poextbus_get_once("REC")
            out["checks"]["POEXTBUS_CNC_REC"] = poext
            if not poext.get("ok"):
                out["errors"].append(f"CNC_POEXTBUS_NO_ACK:{poext.get('error') or poext.get('rc')}")

        # PoStep status jeżeli binding/firmware udostępnia metodę. Błąd metody nie blokuje,
        # bo podstawowym potwierdzeniem CNC w tym projekcie jest PoExtBus + Pulse Engine.
        postep = self.postep_status_get_once("PLAY") if play is not None else {"ok": False, "error": "PLAY_NOT_CONNECTED"}
        out["checks"]["POSTEP_STATUS_PLAY"] = postep
        if not postep.get("ok"):
            out["warnings"].append(f"POSTEP_STATUS_NO_ACK:{postep.get('error') or postep.get('rc')}")

        # Sprawdzenie, czy sygnały osi naprawdę dotyczą CNC/PULSE/STEP/REC copy.
        for name in signals:
            sig = WSZYSTKIE_SYGNALY.get(name)
            if sig is None:
                out["errors"].append(f"{name}:BAD_SIGNAL_MAP")
                continue
            board = str(sig.plytka or "").upper()
            hw = str(sig.hardware_function or "").upper()
            group = str(sig.grupa or "").upper()
            if board == "CNC" and hw != HW_PULSE:
                out["errors"].append(f"{name}:CNC_SIGNAL_NOT_PULSE:{hw}")
            if board == "PLAY" and group.startswith("STEP") and hw not in {HW_PULSE, HW_GPIO}:
                out["errors"].append(f"{name}:PLAY_AXIS_BAD_HW:{hw}")
            if board == "REC" and group not in {"COPY_CAMERA", "RECORD", "MOSTEK_PLAY_REC"} and "COPY" not in group:
                out["warnings"].append(f"{name}:REC_AXIS_GROUP_CHECK:{group}")

        out["ok"] = not out["errors"]
        return out

    def abc_boot_confirmed(self) -> bool:
        return bool(self._abc_boot_confirmed)

    def abc_last_result(self) -> Dict[str, Any]:
        return dict(self._abc_last_result or {"ok": False, "error": "ABC_NOT_CONFIRMED"})

    def diagnostic_capability_report_once(self) -> Dict[str, Any]:
        """Raport pokrycia metod wykonawczych. Bez ciężkich testów i bez pętli."""
        groups = self.inventory()
        return {
            "ok": True,
            "connected": self.connected_count(),
            "all_connected": self.is_all_connected(),
            "inventory": groups,
            "runtime_rule": "PK_* only inside core/tarzanPoKeys.py",
            "method_groups": {
                "boards": ["connect_all", "connect_board", "logical_idle", "logical_wake", "safe_stop", "verify_project_configuration_once", "assert_project_configuration_once"],
                "gpio_analog": ["digital_io_get_once", "digital_io_get_single_once", "analog_io_get_once", "poll_gpio_inputs_once", "poll_analog_inputs_once"],
                "i2c_sensors": ["scan_i2c_once", "read_bh1750_lux_once", "read_lm75_temp_once", "read_sht21_once", "read_mma7660_level_once", "read_mcp3425_adc_once", "read_posensors_once"],
                "ui_hardware": ["lcd_write_lines", "matrix_write_frame", "read_f_buttons_once", "blink_f_led_once", "read_keypad_once"],
                "cnc_postep": ["get_pulse_engine_status", "set_pulse_axis_enable", "set_pulse_axis_position", "postep_status_get_once"],
                "extended": ["pwm_configuration_get_once", "encoder_values_get_once", "one_wire_scan_once", "ponet_status_get_once", "spi_transfer_once", "rtc_get_once"],
            },
        }


    # ------------------------------------------------------------------
    # Testy punktowe używane przez LKS / PARcore
    # ------------------------------------------------------------------
    def test_board_once(self, board: str) -> bool:
        # Twardy test płyty TARZAN: samo PK_DeviceDataGet nie wystarcza.
        # PLAY/REC musi zgadzać się z core/tarzanZmienneSygnalowe.py.
        res = self.verify_project_board_configuration_once(board, force_i2c=False)
        return bool(res.get("ok"))

    def test_all_once(self, update: Optional[Callable[[str, Any, str], None]] = None) -> Dict[str, Any]:
        """Pełny test na żądanie, bez dublowania ciężkich odczytów.

        Nie jest to pętla runtime. PoSensors czytamy raz; reszta korzysta z lekkich testów.
        """
        with self._lock:
            old_state = self.state
            self.set_state("FULL_DIAGNOSTICS")
            try:
                return {
                    "capabilities": self.diagnostic_capability_report_once(),
                    "inventory": self.inventory(),
                    "project_config": self.assert_project_configuration_once(force_i2c=True),
                    "boards": {"PLAY": self.test_board_once("PLAY"), "REC": self.test_board_once("REC")},
                    "potentiometers": self.test_potentiometers_once(update),
                    "xyz_poksyg": self.read_xyz_poksyg_once(update),
                    "i2c_scan": self.scan_i2c_once(force=True),
                    "posensors": self.read_posensors_once(update=update, force=True),
                    "easy_sensors": self.read_easy_sensors_once(),
                    "cnc": self.test_cnc_once(),
                    "poextbus": self.poextbus_get_once("REC"),
                    "tfluna_uart": self.read_tfluna_uart_once(),
                }
            finally:
                self.set_state(old_state)
