from __future__ import annotations

import time
import threading
import os
import platform
import glob
import json
from pathlib import Path
from typing import Any, Dict, Optional, List, Sequence

from core.tarzanZmienneSygnalowe import (
    WSZYSTKIE_SYGNALY,
    POKEYS57U_PLAY_DEVICE_SERIAL,
    POKEYS57U_REC_DEVICE_SERIAL,
    TarzanSygnal
)
from core.TSP.tarzanTspLog import setup_tsp_logger

# Próba importu biblioteki PoKeys
try:
    from hardware.pokeys.PoKeys import PoKeysDevice, ePK_PinCap
    LIB_POKEYS_AVAILABLE = True
except ImportError:
    LIB_POKEYS_AVAILABLE = False
    PoKeysDevice = None
    ePK_PinCap = None

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
        self._lock = threading.Lock()
        
        self.devices: Dict[str, Any] = {
            "PLAY": None,
            "REC": None
        }
        self._lcd_lines: Dict[str, List[str]] = {
            "PLAY": ["", ""],
            "REC": ["", ""],
        }
        
        # Liczniki absolutne pozycji (Etap 14/15)
        # Kluczem jest nazwa bazowa osi, np. "axis_cam_h"
        self._abs_positions: Dict[str, int] = {}
        
        self._last_poll_ms = 0
        self._poll_interval_ms = 50  # 20Hz dla wejść
        
        # FLAGA BEZPIECZEŃSTWA - musi być True, aby generować impulsy na fizycznym sprzęcie
        # ETAP 13: Aktywacja mięśni (odblokowanie osi po weryfikacji logicznej i komunikacyjnej)
        # Zmiana na True oznacza przejście w tryb pełnego zespolenia wykonawczego.
        self.safety_axis_unlock = False
        
        # Mapa sygnałów dla szybkiego dostępu w metodzie write/read
        self._signal_map = WSZYSTKIE_SYGNALY
        
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
            self._init_devices(lib_path)
            self.running = True
            self.bus.set_live_adapter(self)
            
            # Subskrypcja offsetów KHR (Etap 15) - reagujemy na zmiany offsetu nawet bez impulsów STEP
            self.bus.subscribe(self._on_signal_change)
            
            self._thread = threading.Thread(target=self._run, daemon=True, name="HW_Bridge_Loop")
            self._thread.start()
            
            self.bus.force_signal("hardware_state", "READY", source="HW_BRIDGE")
            self.logger.info("Hardware Bridge STARTED and linked to SignalBus.")
            return True
        except Exception as exc:
            self.logger.error(f"Hardware Bridge failed to start: {exc}")
            self.bus.force_signal("hardware_state", "ERROR", source="HW_BRIDGE")
            return False

    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        
        with self._lock:
            for board, device in self.devices.items():
                if device:
                    try:
                        device.Disconnect()
                        self.logger.info(f"Disconnected {board} board.")
                    except:
                        pass
                    self.devices[board] = None
        
        self.bus.set_live_adapter(None)
        self.logger.info("Hardware Bridge STOPPED.")

    def _get_lib_path(self) -> str:
        # Taka sama logika jak w tarzanTspLksHardwareTests
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[1]
        if platform.system() == "Windows":
            return str(repo_root / "hardware" / "pokeys" / "PoKeysDevice_x64.dll")
        else:
            return str(repo_root / "hardware" / "pokeys" / "libPoKeys.so")

    def _init_devices(self, lib_path: str) -> None:
        # PLAY Board
        self.devices["PLAY"] = self._connect_board("PLAY", POKEYS57U_PLAY_DEVICE_SERIAL, lib_path)
        # REC Board
        self.devices["REC"] = self._connect_board("REC", POKEYS57U_REC_DEVICE_SERIAL, lib_path)

    def _connect_board(self, name: str, serial: int, lib_path: str) -> Any:
        device = PoKeysDevice(lib_path)
        ok = device.PK_ConnectToDeviceWSerial(serial, 1, True)
        if not ok:
            self.logger.warning(f"Failed to connect to {name} board (serial={serial})")
            return None
        
        # Pobieramy dane początkowe
        device.PK_DeviceDataGet()
        device.PK_PinConfigurationGet()
        self.logger.info(f"Connected to {name} board (serial={serial}).")
        return device

    def _run(self) -> None:
        while self.running:
            now = time.time() * 1000
            
            # 1. Polling wejść (20Hz)
            if now - self._last_poll_ms >= self._poll_interval_ms:
                self._poll_hardware()
                self._last_poll_ms = now
                
            # 2. Generator trybu manualnego (tM) - ETAP 13
            self._handle_manual_generator()
            
            time.sleep(0.005)

    def _handle_manual_generator(self) -> None:
        """Generuje impulsy STEP w trybie manualnym na podstawie kierunków w SignalBus."""
        if self.bus.read("active_mode", "tM") != "tM":
            return
            
        # Tylko jeśli PAR lub LKS ma kontrolę
        owner = self.bus.read("control_owner", "TSP_BOOT")
        if owner not in {"PAR_LIVE", "TSP_SERVICE", "LKS_DIAGNOSTIC"}:
            return

        from core.tarzanZmienneSygnalowe import LISTA_NAZW_OSI
        for ax_name in LISTA_NAZW_OSI:
            prefix = f"axis_{ax_name}"
            dir_val = int(self.bus.read(f"{prefix}_dir", 0))
            
            if dir_val != 0:
                # Generujemy impuls co N obiegów pętli (uproszczona prędkość)
                # W realnym systemie częstotliwość byłaby sterowana rrp_speed_mul
                step_signal = f"{prefix}_step"
                # Wpisujemy do SignalBus - to wywoła write() w tym samym bridge'u
                self.bus.write_output(step_signal, 1, source="HW_MANUAL_GEN")
                self.bus.write_output(step_signal, 0, source="HW_MANUAL_GEN")

    def _poll_hardware(self) -> None:
        """Odczytuje stany wejść z hardware i wpisuje do SignalBus."""
        with self._lock:
            for board_name, device in self.devices.items():
                if not device:
                    continue
                
                try:
                    # 1. Odczyt wejść cyfrowych GPIO
                    device.PK_DigitalIOGet()
                    for syg in self._signal_map.values():
                        if syg.plytka == board_name and syg.kierunek == "IN":
                            if syg.hardware_function == "GPIO" and syg.pin is not None:
                                val = device.PK_DigitalIOGetSingle(syg.pin)
                                self.bus.set_input(syg.nazwa, 1 if val else 0, source=f"HW.{board_name}", forced=True)

                    # 2. Odczyt statusu Pulse Engine (Etap 13 - Statusy osi)
                    if board_name == "PLAY": # Zakładamy, że PE działa na płycie PLAY
                        self._poll_pulse_engine_status(device)

                except Exception as exc:
                    self.logger.debug(f"Poll hardware error ({board_name}): {exc}")

    def _poll_pulse_engine_status(self, device: Any) -> None:
        """Czyta READY, ALARM i pozycję z Pulse Engine v2."""
        try:
            device.PK_PEv2_StatusGet()
            
            # Mapowanie osi TARZAN na kanały PE
            from core.tarzanZmienneSygnalowe import LISTA_NAZW_OSI
            
            for idx, ax_name in enumerate(LISTA_NAZW_OSI):
                if idx >= 8: break # PoKeys obsługuje do 8 osi
                
                axis_state = device.PEv2.AxesState[idx]
                axis_pos = device.PEv2.CurrentPosition[idx]
                
                # Bity statusu PE v2:
                # Bit 0: Axis enabled
                # Bit 1: Axis running
                # Bit 2: Axis error/alarm
                # Bit 3: Home sensor status
                
                is_enabled = (axis_state & 0x01) == 0x01
                is_running = (axis_state & 0x02) == 0x02
                has_alarm = (axis_state & 0x04) == 0x04
                
                # axis_ready w TARZAN oznacza: włączona, brak błędu, gotowa do pracy
                axis_ready = 1 if (is_enabled and not has_alarm) else 0
                
                # Sygnały statusowe
                self.bus.set_input(f"axis_{ax_name}_ready", axis_ready, source="HW.PE")
                self.bus.set_input(f"axis_{ax_name}_alarm", 1 if has_alarm else 0, source="HW.PE")
                self.bus.set_input(f"axis_{ax_name}_running", 1 if is_running else 0, source="HW.PE")
                
                # Aktualizacja pozycji w SignalBus
                self.bus.force_signal(f"axis_{ax_name}_pos", axis_pos, source="HW.PE")
                
        except Exception as e:
            self.logger.debug(f"Pulse Engine poll error: {e}")


    # ------------------------------------------------------------------
    # LKS-N5 point tests przez aktywny HardwareBridge
    # ------------------------------------------------------------------

    def _device_ready(self, board: str) -> Optional[Any]:
        board = str(board).upper()
        device = self.devices.get(board)
        return device if self.running and device is not None else None

    def _device_identity_text(self, board: str, device: Any) -> str:
        try:
            data = device.device.contents.DeviceData
            serial = int(getattr(data, "SerialNumber", 0))
            name = data.DeviceName.decode("ascii", errors="ignore").strip("\x00")
            typ = data.DeviceTypeName.decode("ascii", errors="ignore").strip("\x00")
            return f"{board} serial={serial} name='{name}' type='{typ}'"
        except Exception:
            return f"{board} connected"

    def _lks_test_result(self, component: str, ok: bool, detail: str = "", error: str = "") -> Dict[str, Any]:
        return {"component": str(component), "ok": bool(ok), "detail": str(detail or ""), "error": str(error or "")}

    def _lks_refresh_device(self, device: Any) -> None:
        try:
            device.PK_PinConfigurationGet()
        except Exception:
            pass
        try:
            device.PK_DigitalIOGet()
        except Exception:
            pass
        try:
            device.PK_AnalogIOGet()
        except Exception:
            pass

    def _lcd_text(self, value: str, width: int = 16) -> str:
        repl = str(value)
        for src, dst in (("ł", "l"), ("Ł", "L"), ("ó", "o"), ("Ó", "O"), ("ą", "a"), ("ę", "e"), ("ś", "s"), ("ż", "z"), ("ź", "z"), ("ń", "n"), ("ć", "c")):
            repl = repl.replace(src, dst)
        return repl[:width].ljust(width)

    def _lks_lcd_init(self, device: Any) -> None:
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

    def _lks_lcd_write_lines(self, device: Any, line1: str, line2: str) -> None:
        if device.PK_LCDMoveCursor(1, 1) != 0:
            raise RuntimeError("PK_LCDMoveCursor(1,1) failed")
        if device.PK_LCDPrint(self._lcd_text(line1, 16)) != 0:
            raise RuntimeError("PK_LCDPrint line1 failed")
        if device.PK_LCDMoveCursor(2, 1) != 0:
            raise RuntimeError("PK_LCDMoveCursor(2,1) failed")
        if device.PK_LCDPrint(self._lcd_text(line2, 16)) != 0:
            raise RuntimeError("PK_LCDPrint line2 failed")

    def _lks_test_lcd_1602(self, visible: bool = True) -> Dict[str, Any]:
        details: List[str] = []
        errors: List[str] = []
        for board in ("PLAY", "REC"):
            device = self._device_ready(board)
            if device is None:
                errors.append(f"{board}: not connected")
                continue
            try:
                if visible:
                    self._lks_lcd_init(device)
                    self._lks_lcd_write_lines(device, f"LKS-N5 {board}", "TEST LCD")
                    time.sleep(0.35)
                    try:
                        device.PK_LCDClear()
                    except Exception:
                        pass
                    self._lks_lcd_write_lines(device, "BEZ BLEDOW", "GOTOWE")
                details.append(self._device_identity_text(board, device))
            except Exception as exc:
                errors.append(f"{board}: {exc}")
        return self._lks_test_result("lcd_1602", not errors, detail="; ".join(details), error="; ".join(errors))

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
        matrix_ptr = device.device.contents.MatrixLED
        if not matrix_ptr:
            raise RuntimeError("PoKeysLib nie udostępnił struktury MatrixLED")
        matrix = matrix_ptr[0]
        matrix.displayEnabled = 1
        matrix.rows = 8
        matrix.columns = 8
        matrix.RefreshFlag = 1
        for i in range(8):
            matrix.data[i] = int(rows[i]) & 0xFF if i < len(rows) else 0
        rc = device.PK_MatrixLEDConfigurationSet()
        if rc != 0:
            raise RuntimeError(f"PK_MatrixLEDConfigurationSet zwróciło {rc}")
        rc = device.PK_MatrixLEDUpdate()
        if rc != 0:
            raise RuntimeError(f"PK_MatrixLEDUpdate zwróciło {rc}")

    def _lks_test_matrix_led(self, visible: bool = True) -> Dict[str, Any]:
        device = self._device_ready("REC")
        if device is None:
            return self._lks_test_result("matrix_led", False, error="REC not connected")
        try:
            if visible:
                try:
                    try:
                        device.PK_MatrixLEDConfigurationGet()
                    except Exception:
                        pass
                    self._lks_matrix_write_frame(device, self._matrix_rows_from_text("OK"))
                    time.sleep(0.25)
                    self._lks_matrix_write_frame(device, [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55])
                    time.sleep(0.20)
                finally:
                    try:
                        self._lks_matrix_write_frame(device, [0] * 8)
                    except Exception:
                        pass
            return self._lks_test_result("matrix_led", True, detail=self._device_identity_text("REC", device))
        except Exception as exc:
            return self._lks_test_result("matrix_led", False, error=str(exc))

    def _lks_read_pin(self, device: Any, pin: int) -> int:
        self._lks_refresh_device(device)
        return int(device.device.contents.Pins[int(pin) - 1].DigitalValueGet)

    def _lks_set_led_pin(self, device: Any, pin: int, value: int) -> None:
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
        try:
            device.PK_DigitalIOGet()
        except Exception:
            pass

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
                        time.sleep(0.10)
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

    def _lks_test_keypad(self, visible: bool = True) -> Dict[str, Any]:
        device = self._device_ready("PLAY")
        if device is None:
            return self._lks_test_result("keypad", False, error="PLAY not connected")
        try:
            rc = device.PK_MatrixKBConfigurationGet()
            if rc != 0:
                raise RuntimeError(f"PK_MatrixKBConfigurationGet zwróciło {rc}")
            rc = device.PK_MatrixKBStatusGet()
            if rc != 0:
                raise RuntimeError(f"PK_MatrixKBStatusGet zwróciło {rc}")
            base = [int(device.device.contents.matrixKB.matrixKBvalues[i]) for i in range(128)]
            if visible:
                end = time.time() + 2.5
                while time.time() < end:
                    device.PK_MatrixKBStatusGet()
                    cur = [int(device.device.contents.matrixKB.matrixKBvalues[i]) for i in range(128)]
                    if cur != base:
                        return self._lks_test_result("keypad", True, detail="matrix value changed")
                    time.sleep(0.05)
                return self._lks_test_result("keypad", False, error="nie wykryto klawisza")
            return self._lks_test_result("keypad", True, detail="PK_MatrixKBStatusGet OK")
        except Exception as exc:
            return self._lks_test_result("keypad", False, error=str(exc))

    def _lks_test_i2c_bus(self) -> Dict[str, Any]:
        device = self._device_ready("PLAY")
        serial_links = sorted(glob.glob("/dev/serial/by-id/*"))
        tty_links = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
        usb_detail = "USB=" + (",".join(serial_links[:3] or tty_links[:3]) or "no-tty")
        if device is None:
            return self._lks_test_result("i2c_bus", False, detail=usb_detail, error="PLAY not connected")
        try:
            device.PK_I2CBusScanStart()
            time.sleep(0.35)
            devices = device.PK_I2CBusScanGetResults()
            found = [addr for addr in range(0, min(128, len(devices))) if int(devices[addr]) == 1]
            if not found:
                return self._lks_test_result("i2c_bus", False, detail=usb_detail, error="brak adresów BUS/I2C")
            bus_detail = "addresses=" + ",".join(f"0x{x:02X}" for x in found)
            return self._lks_test_result("i2c_bus", True, detail=f"{bus_detail}; {usb_detail}")
        except Exception as exc:
            return self._lks_test_result("i2c_bus", False, detail=usb_detail, error=str(exc))

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

    def _lks_test_bh1750(self, address: int = 0x5C) -> Dict[str, Any]:
        device = self._device_ready("PLAY")
        if device is None:
            return self._lks_test_result("light_bh1750", False, error="PLAY not connected")
        try:
            device.PK_I2CWrite(int(address), [0x01])
            time.sleep(0.02)
            device.PK_I2CWrite(int(address), [0x07])
            time.sleep(0.02)
            device.PK_I2CWrite(int(address), [0x20])
            time.sleep(0.18)
            data = device.PK_I2CRead(int(address), 2)
            if data is None or len(data) < 2:
                raise RuntimeError(f"brak 2 bajtów z 0x{address:02X}")
            raw = (int(data[0]) << 8) | int(data[1])
            lux = raw / 1.2
            return self._lks_test_result("light_bh1750", True, detail=f"0x{address:02X} raw={raw} lux={lux:.2f}")
        except Exception as exc:
            return self._lks_test_result("light_bh1750", False, error=str(exc))

    def test_lks_component(self, component: str, visible: bool = True) -> Dict[str, Any]:
        """Punktowy test LKS-N5 bez otwierania drugiej sesji PoKeys.

        Używa urządzeń PLAY/REC już trzymanych przez aktywny HardwareBridge,
        więc kliknięcie status_main nie dubluje połączeń USB i nie generuje
        fałszywego "Requested device not found!".
        """
        name = str(component)
        with self._lock:
            if name == "pok_play":
                dev = self._device_ready("PLAY")
                return self._lks_test_result(name, dev is not None, detail=self._device_identity_text("PLAY", dev) if dev else "", error="PLAY not connected" if dev is None else "")
            if name == "pok_rec":
                dev = self._device_ready("REC")
                return self._lks_test_result(name, dev is not None, detail=self._device_identity_text("REC", dev) if dev else "", error="REC not connected" if dev is None else "")
            if name == "lcd_1602":
                return self._lks_test_lcd_1602(visible=visible)
            if name == "matrix_led":
                return self._lks_test_matrix_led(visible=visible)
            if name == "f_led":
                return self._lks_test_f_led(visible=visible)
            if name == "f_button":
                return self._lks_test_f_buttons(visible=visible)
            if name == "keypad":
                return self._lks_test_keypad(visible=visible)
            if name == "i2c_bus":
                return self._lks_test_i2c_bus()
            if name == "light_bh1750":
                return self._lks_test_bh1750()
            if name == "next_7":
                return self._lks_test_nextion7()
            return self._lks_test_result(name, False, error="component not handled by active HardwareBridge point test")

    # ------------------------------------------------------------------
    # SignalBus LIVE Adapter Interface
    # ------------------------------------------------------------------

    def read(self, name: str) -> Any:
        """Odczyt sygnału bezpośrednio z hardware (jeśli to możliwe)."""
        # Dla optymalizacji większość odczytów i tak idzie z cache SignalBus,
        # który jest aktualizowany w _poll_hardware.
        return None

    def _write_par_lcd_signal(self, name: str, value: Any) -> bool:
        """Wykonuje centralny zapis PAR -> miniPC -> LCD 1602 przez aktywny HardwareBridge."""
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
        board, idx = target
        text = self._lcd_text(str(value), 16)
        with self._lock:
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

    def _write_par_matrix_signal(self, name: str, value: Any) -> bool:
        """Wykonuje PAR -> miniPC -> Matrix LED przez aktywny HardwareBridge."""
        if name != "par_matrix_pattern":
            return False
        rows = self._parse_matrix_pattern_rows(value)
        with self._lock:
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

    def _write_par_f_led_signal(self, name: str, value: Any) -> bool:
        """Wykonuje PAR -> miniPC -> diody F1-F4 REC przez aktywny HardwareBridge."""
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
        state = 1 if str(value).strip().lower() not in {"", "0", "false", "off", "none"} else 0
        with self._lock:
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

    def _write_automation_safety_signal(self, name: str, value: Any) -> bool:
        """AUTOMATYKA: PLAY P37 odłącza STEP osi ramienia w trybie nagrywania ręcznego."""
        if name != "play_p37_step_disconnect_manual":
            return False
        state = 1 if str(value).strip().lower() not in {"", "0", "false", "off", "none"} else 0

        def _ack(ok: bool, message: str) -> None:
            try:
                self.bus.set_input("poksyg_play_p37_ack_ok", 1 if ok else 0, source="POKSYG")
                self.bus.set_input("poksyg_play_p37_last_value", state, source="POKSYG")
                self.bus.log("POKSYG", message)
            except Exception:
                pass

        with self._lock:
            device = self.devices.get("PLAY")
            if not device:
                self.logger.warning("HW AUTOMATYKA PLAY P37 skipped: PLAY board not connected")
                _ack(False, f"ACK ERROR PLAY P37={state} PLAY board not connected")
                return True
            try:
                self._lks_set_led_pin(device, 37, state)
                if state:
                    self.logger.info("HW AUTOMATYKA PLAY P37=1 manual_record_step_disconnect_active")
                    _ack(True, "ACK OK PLAY P37=1 STEP odłączone / nagrywanie ręczne")
                else:
                    self.logger.info("HW AUTOMATYKA PLAY P37=0 automation_active_manual_move_forbidden")
                    _ack(True, "ACK OK PLAY P37=0 automatyka aktywna / zakaz ręcznego ruchu")
            except Exception as exc:
                self.logger.warning("HW AUTOMATYKA PLAY P37 failed: %s", exc)
                _ack(False, f"ACK ERROR PLAY P37={state} {exc}")
        return True

    def write(self, name: str, value: Any) -> None:
        """Zapis sygnału bezpośrednio do hardware."""
        if self._write_par_lcd_signal(name, value):
            return
        if self._write_par_matrix_signal(name, value):
            return
        if self._write_par_f_led_signal(name, value):
            return
        if self._write_automation_safety_signal(name, value):
            return

        syg = self._signal_map.get(name)
        if not syg:
            return
            
        if syg.kierunek != "OUT" and syg.kierunek != "F":
            return

        with self._lock:
            device = self.devices.get(syg.plytka)
            if not device:
                return

            try:
                # Obsługa wyjść cyfrowych
                if syg.hardware_function == "GPIO" and syg.pin is not None:
                    device.PK_DigitalIOSetSingle(syg.pin, 1 if value else 0)
                
                # Obsługa sygnału ENABLE dla osi (Etap 13)
                elif syg.nazwa.startswith("axis_") and syg.nazwa.endswith("_en"):
                    self._handle_pulse_engine_enable(syg, value, device)

                # Obsługa Pulse Engine (STEP/DIR) - ETAP 14
                elif syg.hardware_function == "PULSE_ENGINE":
                    self._handle_pulse_engine_write(syg, value, device)
                    
            except Exception as exc:
                self.logger.debug(f"Write hardware error ({name}={value}): {exc}")

    def _handle_pulse_engine_enable(self, syg: TarzanSygnal, value: Any, device: Any) -> None:
        """Włącza/wyłącza oś w Pulse Engine (Etap 13)."""
        try:
            axis_idx = int(syg.kanal) if syg.kanal and syg.kanal.isdigit() else 0
            # Konfiguracja osi
            device.PK_PEv2_AxisConfigurationGet(axis_idx)
            if value == 1:
                device.PEv2.AxesConfig[axis_idx] |= 0x01 # PK_AC_ENABLED
            else:
                device.PEv2.AxesConfig[axis_idx] &= ~0x01
            device.PK_PEv2_AxisConfigurationSet(axis_idx)
            
            # Aktualizujemy status w SignalBus
            ax_base = syg.nazwa.replace("_en", "")
            self.bus.set_input(f"{ax_base}_enabled", 1 if value else 0, source="HW.PE")
        except Exception as e:
            self.logger.debug(f"Pulse Engine EN error: {e}")

    def _handle_pulse_engine_write(self, syg: TarzanSygnal, value: Any, device: Any) -> None:
        """
        Implementacja Pulse Engine v2 dla PoKeys (Etap 14 + 15).
        Obsługuje narastające zbocza impulsów STEP i nakłada korekty KHR.
        """
        if not self.safety_axis_unlock:
            # Blokada bezpieczeństwa - logujemy tylko raz na jakiś czas
            if time.time() % 10 < 0.1:
                self.logger.warning("PHYSICAL MOTION BLOCKED by safety_axis_unlock=False (Etap 13 Safety)")
            return

        try:
            # Zakładamy, że 'kanal' sygnału to indeks osi (np. "0", "1", ...)
            axis_idx = int(syg.kanal) if syg.kanal and syg.kanal.isdigit() else 0
            
            # Pobieramy nazwę bazową osi, np. axis_cam_h
            # Nazwa sygnału to np. axis_cam_h_step
            axis_base = syg.nazwa.replace("_step", "")
            
            if axis_base not in self._abs_positions:
                self._abs_positions[axis_base] = 0

            # Reagujemy tylko na impuls (zbocze narastające)
            if value == 1:
                # Sprawdzamy kierunek w SignalBus
                dir_signal = axis_base + "_dir"
                dir_val = self.bus.read(dir_signal, 1)
                
                # Aktualizujemy licznik lokalny (Etap 14 - Playback stream)
                step_inc = 1 if dir_val == 1 else -1
                self._abs_positions[axis_base] += step_inc

            # PROTOKOŁ KOREKTY KHR (Etap 15 - Szkielet / Blending)
            # Obecnie implementujemy prosty offset pozycji.
            # Docelowo: wygładzanie (lerp) i blending z krzywą bazową.
            khr_signal = f"khr_{axis_base[5:]}_offset"
            khr_offset = int(float(self.bus.read(khr_signal, 0.0)))
            
            # Pozycja docelowa = TAKE (local counter) + KHR offset
            target_pos = self._abs_positions[axis_base] + khr_offset
            
            # Aktualizujemy PoKeys Pulse Engine
            device.PK_PEv2_StatusGet()
            device.PEv2.Axes[axis_idx].Position = target_pos
            device.PK_PEv2_PositionSet()
            
        except Exception as exc:
            self.logger.debug(f"Pulse Engine robust write error: {exc}")

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
