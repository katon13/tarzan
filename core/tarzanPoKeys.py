from __future__ import annotations

import platform
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
    HW_LCD,
    HW_MATRIX_LED,
    HW_POEXTBUS,
    HW_PULSE,
    HW_PWM,
    TarzanSygnal,
)

try:
    from hardware.pokeys.PoKeys import PoKeysDevice, ePK_PinCap
    LIB_POKEYS_AVAILABLE = True
except ImportError:
    PoKeysDevice = None  # type: ignore[assignment]
    ePK_PinCap = None  # type: ignore[assignment]
    LIB_POKEYS_AVAILABLE = False


class TarzanPoKeys:
    """Własna biblioteka metod PoKeys dla TARZANA.

    Zasada projektu:
    - hardware/pokeys/PoKeys.py jest tylko bindingiem niskiego poziomu,
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
        self.logical_sleep = False
        self.last_lib_path = ""
        self._last_error: Dict[str, str] = {}
        self._signal_groups = self.build_signal_groups(WSZYSTKIE_SYGNALY)

    # ------------------------------------------------------------------
    # Biblioteka / połączenia
    # ------------------------------------------------------------------
    def lib_available(self) -> bool:
        return bool(LIB_POKEYS_AVAILABLE and PoKeysDevice is not None)

    def get_lib_path(self) -> str:
        repo_root = Path(__file__).resolve().parents[1]
        if platform.system() == "Windows":
            candidates = [repo_root / "hardware" / "pokeys" / "PoKeysDevice_x64.dll"]
        else:
            candidates = [
                repo_root / "hardware" / "pokeys" / "libPoKeys.so",
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
        if platform.system() == "Windows":
            return str(repo_root / "hardware" / "pokeys" / "PoKeysDevice_x64.dll")
        return str(repo_root / "hardware" / "pokeys" / "libPoKeys.so")

    def connect_all(self, lib_path: Optional[str] = None) -> int:
        with self._lock:
            path = str(lib_path or self.get_lib_path())
            self.last_lib_path = path
            for board, serial in self.BOARDS.items():
                if self.devices.get(board) is None:
                    self.devices[board] = self.connect_board(board, serial, path)
            self.logical_sleep = False
            return self.connected_count()

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
            self.refresh_device(device, analog=False, digital=False, config=True)
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
            self.logger.info("USB SLEEP: logical sleep; PoKeys handles kept open (no PK_DisconnectDevice in IDLE).")
            return True

    def logical_wake(self) -> bool:
        with self._lock:
            if not self.logical_sleep:
                return False
            self.logical_sleep = False
            self.logger.info("USB WAKE: logical wake; PoKeys handles already open.")
            return True

    def safe_stop(self) -> None:
        """Zamknięcie uchwytów tylko przy STOP usługi, raz i pod lockiem."""
        with self._lock:
            for board, device in list(self.devices.items()):
                if device is None:
                    continue
                try:
                    device.Disconnect()
                    self.logger.info("Disconnected %s board.", board)
                except Exception as exc:
                    self.logger.warning("PoKeys safe_stop disconnect %s ignored: %s", board, exc)
                finally:
                    self.devices[board] = None
            self.logical_sleep = False

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
                try:
                    getattr(device, call_name)()
                except Exception:
                    pass
        if digital:
            try:
                device.PK_DigitalIOGet()
            except Exception:
                pass
        if analog:
            try:
                device.PK_AnalogIOGet()
            except Exception:
                pass

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
        rc = device.PK_PinConfigurationSet()
        if rc != 0:
            raise RuntimeError(f"PK_PinConfigurationSet P{pin} zwróciło {rc}")
        rc = device.PK_DigitalIOSetSingle(pin_index, 1 if value else 0)
        if rc != 0:
            raise RuntimeError(f"PK_DigitalIOSetSingle P{pin} zwróciło {rc}")

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
    def poll_gpio_inputs_once(self, gpio_inputs: Iterable[TarzanSygnal], update: Callable[[str, Any, str], None]) -> None:
        with self._lock:
            if self.logical_sleep:
                return
            for board_name, device in self.devices.items():
                if device is None:
                    continue
                try:
                    device.PK_DigitalIOGet()
                    pins_ptr = device.device.contents.Pins
                    for sig in gpio_inputs:
                        if str(sig.plytka).upper() == board_name and sig.pin is not None:
                            val = 1 if pins_ptr[int(sig.pin) - 1].DigitalValueGet else 0
                            update(str(sig.nazwa), val, f"HW.{board_name}")
                            if sig.kanoniczna_nazwa:
                                update(str(sig.kanoniczna_nazwa), val, f"HW.{board_name}")
                except Exception as exc:
                    self.logger.debug("PoKeys GPIO poll %s error: %s", board_name, exc)

    def poll_analog_inputs_once(self, analog_inputs: Iterable[TarzanSygnal], update: Callable[[str, Any, str], None]) -> None:
        with self._lock:
            if self.logical_sleep:
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
                    device.PK_AnalogIOGet()
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
    def test_potentiometers_once(self, update: Optional[Callable[[str, Any, str], None]] = None) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ok": False, "values": {}, "errors": []}
        with self._lock:
            device = self.get_device("PLAY")
            if device is None:
                out["errors"].append("PLAY not connected")
                return out
            try:
                device.PK_AnalogIOGet()
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
        try:
            result["i2c_scan"] = self.scan_i2c_once("PLAY")
        except Exception as exc:
            result["errors"].append(f"i2c_scan: {exc}")
        try:
            result["posensors"] = self.read_posensors_once("PLAY", update=update)
        except Exception as exc:
            result["errors"].append(f"posensors: {exc}")
        try:
            result["easy_sensors"] = self.read_easy_sensors_once("PLAY")
        except Exception as exc:
            result["errors"].append(f"easy_sensors: {exc}")
        result["ok"] = len(result["errors"]) == 0
        return result

    # ------------------------------------------------------------------
    # I2C / EasySensors / PoExtBus / Pulse Engine
    # ------------------------------------------------------------------
    def scan_i2c_once(self, board: str = "PLAY") -> Dict[str, Any]:
        device = self.get_device(board)
        if device is None:
            return {"ok": False, "addresses": [], "error": f"{board} not connected"}
        try:
            device.PK_I2CBusScanStart()
            time.sleep(0.35)
            data = device.PK_I2CBusScanGetResults()
            addrs = [addr for addr in range(0, min(128, len(data))) if int(data[addr]) == 1]
            return {"ok": True, "addresses": addrs}
        except Exception as exc:
            return {"ok": False, "addresses": [], "error": str(exc)}

    def _i2c_addr8(self, addr7: int) -> int:
        """PoKeys wrapper pracuje jak przykłady z dokumentacji: adres 7-bit przesunięty w lewo."""
        return (int(addr7) & 0x7F) << 1

    def i2c_write(self, board: str, addr7: int, data: Iterable[int]) -> bool:
        device = self.get_device(board)
        if device is None:
            return False
        try:
            rc = device.PK_I2CWrite(self._i2c_addr8(addr7), list(data))
            return bool(rc)
        except Exception as exc:
            self.logger.debug("I2C write board=%s addr=0x%02X failed: %s", board, addr7, exc)
            return False

    def i2c_read(self, board: str, addr7: int, n: int) -> Optional[List[int]]:
        device = self.get_device(board)
        if device is None:
            return None
        try:
            data = device.PK_I2CRead(self._i2c_addr8(addr7), int(n))
            if data is None:
                return None
            return [int(x) & 0xFF for x in data]
        except Exception as exc:
            self.logger.debug("I2C read board=%s addr=0x%02X failed: %s", board, addr7, exc)
            return None

    def i2c_write_read(self, board: str, addr7: int, write: Iterable[int], n: int) -> Optional[List[int]]:
        device = self.get_device(board)
        if device is None:
            return None
        try:
            data = device.PK_I2CWriteAndRead(self._i2c_addr8(addr7), list(write), int(n))
            if data is None:
                return None
            return [int(x) & 0xFF for x in data]
        except Exception as exc:
            self.logger.debug("I2C write/read board=%s addr=0x%02X failed: %s", board, addr7, exc)
            return None

    def _first_present_addr(self, board: str, names: Iterable[str]) -> Optional[int]:
        scan = self.scan_i2c_once(board)
        addrs = set(scan.get("addresses") or [])
        for name in names:
            for addr in self.I2C_ADDR7.get(name, ()):  # type: ignore[arg-type]
                if addr in addrs:
                    return int(addr)
        return None

    def read_bh1750_lux_once(self, board: str = "PLAY", addr7: Optional[int] = None) -> Dict[str, Any]:
        addr = int(addr7 if addr7 is not None else (self._first_present_addr(board, ["bh1750"]) or 0x23))
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

    def read_lm75_temp_once(self, board: str = "PLAY", addr7: Optional[int] = None) -> Dict[str, Any]:
        addr = int(addr7 if addr7 is not None else (self._first_present_addr(board, ["lm75"]) or 0x48))
        data = self.i2c_write_read(board, addr, [0x00], 2)
        if not data or len(data) < 2:
            return {"ok": False, "sensor": "LM75", "addr7": addr, "error": "no data"}
        raw = ((data[0] << 8) | data[1]) >> 5
        if raw & 0x400:
            raw -= 0x800
        temp_c = raw * 0.125
        return {"ok": True, "sensor": "LM75", "addr7": addr, "raw": raw, "temp_c": temp_c}

    def read_sht21_once(self, board: str = "PLAY", addr7: int = 0x40) -> Dict[str, Any]:
        # No-hold measurement commands: temp 0xF3, humidity 0xF5.
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

    def read_mma7660_level_once(self, board: str = "PLAY", addr7: int = 0x4C) -> Dict[str, Any]:
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

    def read_mcp3425_adc_once(self, board: str = "PLAY", addr7: int = 0x68) -> Dict[str, Any]:
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

    def read_posensors_once(self, board: str = "PLAY", update: Optional[Callable[[str, Any, str], None]] = None) -> Dict[str, Any]:
        """Odczyt całego modułu PoSensors: BH1750, LM75, SHT21, MMA7660, MCP3425."""
        out: Dict[str, Any] = {
            "bh1750": self.read_bh1750_lux_once(board),
            "lm75": self.read_lm75_temp_once(board),
            "sht21": self.read_sht21_once(board),
            "mma7660": self.read_mma7660_level_once(board),
            "mcp3425": self.read_mcp3425_adc_once(board),
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
            dev.PK_AnalogIOGet()
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
        device = self.get_device(board)
        if device is None:
            return {"ok": False, "values": {}, "error": f"{board} not connected"}
        try:
            rc = device.PK_EasySensorsValueGetAll()
            if rc != 0:
                return {"ok": False, "values": {}, "error": f"PK_EasySensorsValueGetAll={rc}"}
            values = {}
            try:
                count = int(device.device.contents.info.iEasySensors)
                for idx in range(max(0, min(count, 16))):
                    sensor = device.device.contents.EasySensors[idx]
                    values[str(idx)] = int(getattr(sensor, "sensorValue", 0))
            except Exception:
                pass
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
            if not hasattr(device, "PK_PoExtBusGet") or not hasattr(device, "PK_PoExtBusSet"):
                return False
            device.PK_PoExtBusGet()
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
            return device.PK_PoExtBusSet() == 0
        except Exception as exc:
            self.logger.debug("PoExtBus write %s failed: %s", sig.nazwa, exc)
            return False

    def get_pulse_engine_status(self, device: Any) -> Dict[str, Any]:
        status: Dict[str, Any] = {}
        try:
            device.PK_PEv2_StatusGet()
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
        except Exception as exc:
            status["error"] = str(exc)
        return status

    def set_pulse_axis_enable(self, device: Any, axis_idx: int, enabled: bool) -> bool:
        try:
            axis_idx = int(axis_idx)
            device.PK_PEv2_AxisConfigurationGet(axis_idx)
            if enabled:
                device.device.contents.PEv2.AxesConfig[axis_idx] |= 0x01
            else:
                device.device.contents.PEv2.AxesConfig[axis_idx] &= ~0x01
            return device.PK_PEv2_AxisConfigurationSet(axis_idx) == 0
        except Exception as exc:
            self.logger.debug("PE axis enable failed axis=%s: %s", axis_idx, exc)
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

    def lcd_init(self, board: str = "PLAY") -> Dict[str, Any]:
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            device = self.get_device(board)
            if device is None:
                return {"ok": False, "board": board, "error": f"{board} not connected"}
            try:
                lcd = device.device.contents.LCD
                lcd.Configuration = 2
                lcd.Rows = 2
                lcd.Columns = 16
                for call, name in (
                    (device.PK_LCDConfigurationSet, "PK_LCDConfigurationSet"),
                    (lambda: device.PK_LCDChangeMode(0), "PK_LCDChangeMode"),
                    (device.PK_LCDInit, "PK_LCDInit"),
                    (device.PK_LCDClear, "PK_LCDClear"),
                ):
                    rc = call()
                    if rc != 0:
                        raise RuntimeError(f"{name} zwróciło {rc}")
                return {"ok": True, "board": board}
            except Exception as exc:
                return {"ok": False, "board": board, "error": str(exc)}

    def lcd_write_lines(self, board: str, line1: str, line2: str) -> Dict[str, Any]:
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            device = self.get_device(board)
            if device is None:
                return {"ok": False, "board": board, "error": f"{board} not connected"}
            try:
                if device.PK_LCDMoveCursor(1, 1) != 0:
                    raise RuntimeError("PK_LCDMoveCursor(1,1) failed")
                if device.PK_LCDPrint(self._lcd_text(line1, 16).ljust(16)) != 0:
                    raise RuntimeError("PK_LCDPrint line1 failed")
                if device.PK_LCDMoveCursor(2, 1) != 0:
                    raise RuntimeError("PK_LCDMoveCursor(2,1) failed")
                if device.PK_LCDPrint(self._lcd_text(line2, 16).ljust(16)) != 0:
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

    def matrix_write_frame(self, board: str = "REC", rows: Iterable[int] = ()) -> Dict[str, Any]:
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            device = self.get_device(board)
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
                rc = device.PK_MatrixLEDConfigurationSet()
                if rc != 0:
                    raise RuntimeError(f"PK_MatrixLEDConfigurationSet zwróciło {rc}")
                rc = device.PK_MatrixLEDUpdate()
                if rc != 0:
                    raise RuntimeError(f"PK_MatrixLEDUpdate zwróciło {rc}")
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
                rc = dev.PK_MatrixKBConfigurationGet()
                if rc != 0:
                    raise RuntimeError(f"PK_MatrixKBConfigurationGet zwróciło {rc}")
                rc = dev.PK_MatrixKBStatusGet()
                if rc != 0:
                    raise RuntimeError(f"PK_MatrixKBStatusGet zwróciło {rc}")
                values = [int(dev.device.contents.matrixKB.matrixKBvalues[i]) for i in range(128)]
                return {"ok": True, "values": values}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Testy punktowe używane przez LKS / PARcore
    # ------------------------------------------------------------------
    def test_board_once(self, board: str) -> bool:
        device = self.get_device(board)
        if device is None:
            return False
        try:
            device.PK_DeviceDataGet()
            device.PK_PinConfigurationGet()
            return True
        except Exception as exc:
            self.logger.warning("PoKeys test %s failed: %s", board, exc)
            return False

    def test_all_once(self, update: Optional[Callable[[str, Any, str], None]] = None) -> Dict[str, Any]:
        return {
            "inventory": self.inventory(),
            "boards": {"PLAY": self.test_board_once("PLAY"), "REC": self.test_board_once("REC")},
            "potentiometers": self.test_potentiometers_once(update),
            "xyz_poksyg": self.read_xyz_poksyg_once(update),
            "posensors": self.read_posensors_once("PLAY", update),
            "sensors": self.test_sensors_once(update),
            "cnc": self.test_cnc_once(),
            "tfluna_uart": self.read_tfluna_uart_once(),
        }
