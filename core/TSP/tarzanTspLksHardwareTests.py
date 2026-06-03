from __future__ import annotations

"""TARZAN LKS-N5 — ETAP 12: suwerenne testery sprzętu.

Ten moduł NIE importuje ``hardware.tarzanMiniPcSandbox`` w runtime.
Sandbox był tylko wzorcem nazw, pinów i sprawdzonych wywołań PoKeys.
Tutaj są czyste testery LKS-N5:

* read-only w pracy automatycznej,
* widoczne testy tylko po kliknięciu operatora,
* zero STEP, zero DIR, zero ENABLE, zero ruchu osi.
"""

import argparse
import os
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
POKEYS_DIR = REPO_ROOT / "hardware" / "pokeys"
if str(POKEYS_DIR) not in sys.path:
    sys.path.insert(0, str(POKEYS_DIR))

try:
    from core.tarzanZmienneSygnalowe import (  # type: ignore
        POKEYS57U_PLAY_DEVICE_SERIAL,
        POKEYS57U_REC_DEVICE_SERIAL,
    )
except Exception:  # pragma: no cover
    POKEYS57U_PLAY_DEVICE_SERIAL = 36102
    POKEYS57U_REC_DEVICE_SERIAL = 36084


@dataclass
class LksHardwareTestResult:
    component: str
    ok: bool
    supported: bool
    label: str
    detail: str = ""
    error: str = ""
    visible_action: str = ""


class _PoKeysSession:
    """Mała sesja PoKeys dla LKS-N5.

    Kopiuje tylko sprawdzony schemat połączenia ze starego sandboxa, bez
    importowania sandboxa. Testy osi i pulse engine nie istnieją w tym module.
    """

    def __init__(self, board: str, lib_path: str) -> None:
        self.board = board.upper()
        self.lib_path = str(lib_path)
        self.serial = int(POKEYS57U_PLAY_DEVICE_SERIAL if self.board == "PLAY" else POKEYS57U_REC_DEVICE_SERIAL)
        PoKeysDevice, _ = _import_pokeys()
        self.device = PoKeysDevice(self.lib_path)

    def __enter__(self) -> "_PoKeysSession":
        ok = self.device.PK_ConnectToDeviceWSerial(self.serial, 1, True)
        if not ok:
            raise RuntimeError(f"Nie udało się połączyć z {self.board} serial={self.serial}")
        actual = int(self.device.device.contents.DeviceData.SerialNumber)
        if actual != self.serial:
            raise RuntimeError(f"Zły serial {self.board}: oczekiwano {self.serial}, odczytano {actual}")
        self.refresh()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self.device.Disconnect()
        except Exception:
            pass

    def refresh(self) -> None:
        self.device.PK_PinConfigurationGet()
        self.device.PK_DigitalIOGet()
        try:
            self.device.PK_AnalogIOGet()
        except Exception:
            pass

    def identity_text(self) -> str:
        dev = self.device.device.contents.DeviceData
        name = dev.DeviceName.decode("ascii", errors="ignore").strip("\x00")
        typ = dev.DeviceTypeName.decode("ascii", errors="ignore").strip("\x00")
        return f"{self.board} serial={int(dev.SerialNumber)} name='{name}' type='{typ}'"


def _import_pokeys():
    try:
        from hardware.pokeys.PoKeys import PoKeysDevice, ePK_PinCap  # type: ignore
        return PoKeysDevice, ePK_PinCap
    except Exception:
        try:
            from PoKeys import PoKeysDevice, ePK_PinCap  # type: ignore
            return PoKeysDevice, ePK_PinCap
        except Exception as exc:
            raise RuntimeError("Nie mogę zaimportować Python wrappera PoKeys.py") from exc


def _lcd_text(value: str, width: int = 20) -> str:
    repl = str(value).replace("ł", "l").replace("Ł", "L").replace("ó", "o").replace("Ó", "O")
    repl = repl.replace("ą", "a").replace("ę", "e").replace("ś", "s").replace("ż", "z").replace("ź", "z")
    repl = repl.replace("ń", "n").replace("ć", "c")
    return repl[:width]


_MATRIX_FONT_5X7: Dict[str, List[int]] = {
    " ": [0, 0, 0, 0, 0],
    "A": [0x7E, 0x11, 0x11, 0x11, 0x7E],
    "B": [0x7F, 0x49, 0x49, 0x49, 0x36],
    "C": [0x3E, 0x41, 0x41, 0x41, 0x22],
    "D": [0x7F, 0x41, 0x41, 0x22, 0x1C],
    "E": [0x7F, 0x49, 0x49, 0x49, 0x41],
    "F": [0x7F, 0x09, 0x09, 0x09, 0x01],
    "G": [0x3E, 0x41, 0x49, 0x49, 0x7A],
    "H": [0x7F, 0x08, 0x08, 0x08, 0x7F],
    "I": [0x00, 0x41, 0x7F, 0x41, 0x00],
    "K": [0x7F, 0x08, 0x14, 0x22, 0x41],
    "L": [0x7F, 0x40, 0x40, 0x40, 0x40],
    "M": [0x7F, 0x02, 0x0C, 0x02, 0x7F],
    "N": [0x7F, 0x04, 0x08, 0x10, 0x7F],
    "O": [0x3E, 0x41, 0x41, 0x41, 0x3E],
    "P": [0x7F, 0x09, 0x09, 0x09, 0x06],
    "R": [0x7F, 0x09, 0x19, 0x29, 0x46],
    "S": [0x46, 0x49, 0x49, 0x49, 0x31],
    "T": [0x01, 0x01, 0x7F, 0x01, 0x01],
    "U": [0x3F, 0x40, 0x40, 0x40, 0x3F],
    "V": [0x1F, 0x20, 0x40, 0x20, 0x1F],
    "X": [0x63, 0x14, 0x08, 0x14, 0x63],
    "Y": [0x07, 0x08, 0x70, 0x08, 0x07],
    "Z": [0x61, 0x51, 0x49, 0x45, 0x43],
    "0": [0x3E, 0x45, 0x49, 0x51, 0x3E],
    "1": [0x00, 0x42, 0x7F, 0x40, 0x00],
    "2": [0x62, 0x51, 0x49, 0x49, 0x46],
    "3": [0x22, 0x41, 0x49, 0x49, 0x36],
    "4": [0x18, 0x14, 0x12, 0x7F, 0x10],
    "5": [0x27, 0x45, 0x45, 0x45, 0x39],
    "6": [0x3C, 0x4A, 0x49, 0x49, 0x30],
    "7": [0x01, 0x71, 0x09, 0x05, 0x03],
    "8": [0x36, 0x49, 0x49, 0x49, 0x36],
    "9": [0x06, 0x49, 0x49, 0x29, 0x1E],
}


def _matrix_text_columns(text_value: str) -> List[int]:
    cols: List[int] = []
    for ch in _lcd_text(text_value.upper(), 32):
        cols.extend(_MATRIX_FONT_5X7.get(ch, _MATRIX_FONT_5X7[" "]))
        cols.append(0x00)
    return cols or [0] * 8


def _matrix_rows_from_columns(columns: Sequence[int]) -> List[int]:
    rows: List[int] = []
    for row in range(8):
        value = 0
        for col in range(min(8, len(columns))):
            if int(columns[col]) & (1 << row):
                value |= 1 << col
        rows.append(value & 0xFF)
    return rows


class TarzanTspLksHardwareTests:
    """Suwerenne testery sprzętu LKS-N5.

    ``visible=False`` oznacza test bez efektów operatorskich, do bootu.
    ``visible=True`` oznacza test po kliknięciu operatora: LCD pisze TEST,
    Matrix pokazuje wzór, LED F1-F4 mrugają, przyciski/klawiatura mogą chwilę
    czekać na zmianę. Nadal nie ma STEP/DIR/ENABLE.
    """

    def __init__(self, repo_root: Optional[str] = None, lib_path: Optional[str] = None) -> None:
        self.repo_root = Path(repo_root or REPO_ROOT).resolve()
        self.lib_path = lib_path or self.find_pokeys_library()

    def _res(self, component: str, ok: bool, supported: bool, label: str, detail: str = "", error: str = "", visible_action: str = "") -> LksHardwareTestResult:
        return LksHardwareTestResult(component=component, ok=bool(ok), supported=bool(supported), label=label, detail=detail, error=error, visible_action=visible_action)

    def find_pokeys_library(self) -> Optional[str]:
        env = os.environ.get("TARZAN_POKEYS_LIB")
        candidates = []
        if env:
            candidates.append(Path(env))
        candidates.extend([
            self.repo_root / "hardware" / "pokeys" / "libPoKeys.so",
            self.repo_root / "hardware" / "pokeys" / "libpokeys.so",
            Path("/usr/local/lib/libPoKeys.so"),
            Path("/usr/lib/libPoKeys.so"),
            Path("/usr/lib/x86_64-linux-gnu/libPoKeys.so"),
        ])
        # DLL tylko na Windows albo gdy użytkownik poda ją jawnie przez TARZAN_POKEYS_LIB/--lib-path.
        if platform.system().lower().startswith("win"):
            candidates.append(self.repo_root / "hardware" / "pokeys" / "PoKeyslib.dll")
        for path in candidates:
            if path and Path(path).exists():
                return str(path)
        return None

    def _session(self, board: str) -> _PoKeysSession:
        if not self.lib_path:
            raise RuntimeError("Nie znaleziono libPoKeys.so / PoKeyslib.dll")
        return _PoKeysSession(board, self.lib_path)

    # ------------------------------------------------------------------
    # PoKeys / USB identity
    # ------------------------------------------------------------------
    def check_pokeys(self, board: str) -> LksHardwareTestResult:
        board = board.upper()
        component = "pok_play" if board == "PLAY" else "pok_rec"
        try:
            with self._session(board) as session:
                return self._res(component, True, True, f"PoKeys {board} real connect", detail=session.identity_text())
        except Exception as exc:
            return self._res(component, False, True, f"PoKeys {board} real connect", error=str(exc))

    # ------------------------------------------------------------------
    # LCD 1602 — widoczny test po kliknięciu, konfiguracja bez ruchu osi
    # ------------------------------------------------------------------
    def test_lcd_1602(self, visible: bool = False, board: str = "PLAY") -> LksHardwareTestResult:
        try:
            with self._session(board) as session:
                if visible:
                    lcd = session.device.device.contents.LCD
                    lcd.Configuration = 2
                    lcd.Rows = 2
                    lcd.Columns = 16
                    for call, name in (
                        (session.device.PK_LCDConfigurationSet, "PK_LCDConfigurationSet"),
                        (lambda: session.device.PK_LCDChangeMode(0), "PK_LCDChangeMode"),
                        (session.device.PK_LCDInit, "PK_LCDInit"),
                        (session.device.PK_LCDClear, "PK_LCDClear"),
                    ):
                        rc = call()
                        if rc != 0:
                            raise RuntimeError(f"{name} zwróciło {rc}")
                    if session.device.PK_LCDMoveCursor(1, 1) != 0:
                        raise RuntimeError("PK_LCDMoveCursor(1,1) failed")
                    if session.device.PK_LCDPrint(_lcd_text("LKS-N5 TEST", 16)) != 0:
                        raise RuntimeError("PK_LCDPrint line1 failed")
                    if session.device.PK_LCDMoveCursor(2, 1) != 0:
                        raise RuntimeError("PK_LCDMoveCursor(2,1) failed")
                    if session.device.PK_LCDPrint(_lcd_text("LCD OK", 16)) != 0:
                        raise RuntimeError("PK_LCDPrint line2 failed")
                    return self._res("lcd_1602", True, True, "LCD 1602 PoKeys visible test", detail=session.identity_text(), visible_action="LCD pokazuje LKS-N5 TEST / LCD OK")
                return self._res("lcd_1602", True, True, "LCD 1602 PoKeys session", detail=session.identity_text())
        except Exception as exc:
            return self._res("lcd_1602", False, True, "LCD 1602 PoKeys test", error=str(exc))

    # ------------------------------------------------------------------
    # Matrix LED 8x8 — widoczny wzór/test po kliknięciu
    # ------------------------------------------------------------------
    def _matrix_write_frame(self, session: _PoKeysSession, rows: Sequence[int]) -> None:
        matrix_ptr = session.device.device.contents.MatrixLED
        if not matrix_ptr:
            raise RuntimeError("PoKeysLib nie udostępnił struktury MatrixLED")
        matrix = matrix_ptr[0]
        matrix.displayEnabled = 1
        matrix.rows = 8
        matrix.columns = 8
        matrix.RefreshFlag = 1
        for i in range(8):
            matrix.data[i] = int(rows[i]) & 0xFF if i < len(rows) else 0
        rc = session.device.PK_MatrixLEDConfigurationSet()
        if rc != 0:
            raise RuntimeError(f"PK_MatrixLEDConfigurationSet zwróciło {rc}")
        rc = session.device.PK_MatrixLEDUpdate()
        if rc != 0:
            raise RuntimeError(f"PK_MatrixLEDUpdate zwróciło {rc}")

    def test_matrix_led(self, visible: bool = False, board: str = "REC") -> LksHardwareTestResult:
        try:
            with self._session(board) as session:
                if visible:
                    try:
                        session.device.PK_MatrixLEDConfigurationGet()
                    except Exception:
                        pass
                    columns = _matrix_text_columns("OK")
                    rows = _matrix_rows_from_columns(columns[:8])
                    self._matrix_write_frame(session, rows)
                    time.sleep(0.25)
                    self._matrix_write_frame(session, [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55])
                    time.sleep(0.25)
                    self._matrix_write_frame(session, [0] * 8)
                    return self._res("matrix_led", True, True, "Matrix LED visible test", detail=session.identity_text(), visible_action="Matrix pokazuje OK/wzór i gaśnie")
                return self._res("matrix_led", True, True, "Matrix LED PoKeys session", detail=session.identity_text())
        except Exception as exc:
            return self._res("matrix_led", False, True, "Matrix LED PoKeys test", error=str(exc))

    # ------------------------------------------------------------------
    # F1-F4 buttons / LEDs — REC P45/P47/P49/P51 i P46/P48/P50/P52
    # ------------------------------------------------------------------
    def _read_pin(self, session: _PoKeysSession, pin: int) -> int:
        session.refresh()
        return int(session.device.device.contents.Pins[int(pin) - 1].DigitalValueGet)

    def test_f_buttons(self, visible: bool = False, timeout: float = 0.0) -> LksHardwareTestResult:
        pins = [45, 47, 49, 51]
        try:
            with self._session("REC") as session:
                base = {pin: self._read_pin(session, pin) for pin in pins}
                if visible and timeout > 0:
                    end = time.time() + max(0.5, timeout)
                    while time.time() < end:
                        for pin in pins:
                            if self._read_pin(session, pin) != base[pin]:
                                return self._res("f_button", True, True, "F1-F4 button visible test", detail=f"REC P{pin} changed", visible_action="operator nacisnął F1-F4")
                        time.sleep(0.05)
                    return self._res("f_button", False, True, "F1-F4 button visible test", detail=str(base), error="nie wykryto naciśnięcia w czasie testu")
                return self._res("f_button", True, True, "F1-F4 buttons read-only", detail=str(base))
        except Exception as exc:
            return self._res("f_button", False, True, "F1-F4 buttons read-only", error=str(exc))

    def _set_led_pin_runtime(self, session: _PoKeysSession, pin: int, value: int) -> None:
        _, ePK_PinCap = _import_pokeys()
        pin_index = int(pin) - 1
        pin_data = session.device.device.contents.Pins[pin_index]
        pin_data.PinFunction = int(ePK_PinCap.PK_PinCap_digitalOutput)
        pin_data.DigitalValueSet = 1 if value else 0
        rc = session.device.PK_PinConfigurationSet()
        if rc != 0:
            raise RuntimeError(f"PK_PinConfigurationSet P{pin} zwróciło {rc}")
        rc = session.device.PK_DigitalIOSetSingle(pin_index, 1 if value else 0)
        if rc != 0:
            raise RuntimeError(f"PK_DigitalIOSetSingle P{pin} zwróciło {rc}")
        session.device.PK_DigitalIOGet()

    def test_f_led(self, visible: bool = False) -> LksHardwareTestResult:
        pins = [46, 48, 50, 52]
        try:
            with self._session("REC") as session:
                if visible:
                    for pin in pins:
                        self._set_led_pin_runtime(session, pin, 0)
                    for pin in pins:
                        self._set_led_pin_runtime(session, pin, 1)
                        time.sleep(0.12)
                        self._set_led_pin_runtime(session, pin, 0)
                        time.sleep(0.08)
                    return self._res("f_led", True, True, "F1-F4 LED whitelist visible test", detail=session.identity_text(), visible_action="LED F1-F4 mrugają po kolei")
                return self._res("f_led", True, True, "F1-F4 LED whitelist available", detail="REC P46/P48/P50/P52")
        except Exception as exc:
            return self._res("f_led", False, True, "F1-F4 LED whitelist test", error=str(exc))

    # ------------------------------------------------------------------
    # Keypad / keyboard / BUS / BH1750
    # ------------------------------------------------------------------
    def test_keypad(self, visible: bool = False, timeout: float = 0.0) -> LksHardwareTestResult:
        try:
            with self._session("PLAY") as session:
                rc = session.device.PK_MatrixKBConfigurationGet()
                if rc != 0:
                    raise RuntimeError(f"PK_MatrixKBConfigurationGet zwróciło {rc}")
                rc = session.device.PK_MatrixKBStatusGet()
                if rc != 0:
                    raise RuntimeError(f"PK_MatrixKBStatusGet zwróciło {rc}")
                base = [int(session.device.device.contents.matrixKB.matrixKBvalues[i]) for i in range(128)]
                if visible and timeout > 0:
                    end = time.time() + max(0.5, timeout)
                    while time.time() < end:
                        session.device.PK_MatrixKBStatusGet()
                        cur = [int(session.device.device.contents.matrixKB.matrixKBvalues[i]) for i in range(128)]
                        if cur != base:
                            return self._res("keypad", True, True, "Keypad 4x3 visible matrix test", detail="matrix value changed", visible_action="operator nacisnął keypad")
                        time.sleep(0.05)
                    return self._res("keypad", False, True, "Keypad 4x3 visible matrix test", error="nie wykryto klawisza")
                return self._res("keypad", True, True, "Keypad matrix status read", detail="PK_MatrixKBStatusGet OK")
        except Exception as exc:
            return self._res("keypad", False, True, "Keypad matrix status read", error=str(exc))

    def scan_i2c_bus(self, board: str = "PLAY") -> Tuple[List[int], str]:
        with self._session(board) as session:
            session.device.PK_I2CBusScanStart()
            time.sleep(0.4)
            devices = session.device.PK_I2CBusScanGetResults()
            found = [addr for addr in range(0, min(128, len(devices))) if int(devices[addr]) == 1]
            return found, session.identity_text()

    def test_i2c_bus(self, visible: bool = False) -> LksHardwareTestResult:
        try:
            found, ident = self.scan_i2c_bus("PLAY")
            if not found:
                return self._res("i2c_bus", False, True, "PoKeys BUS/I2C scan", detail=ident, error="brak adresów BUS/I2C")
            return self._res("i2c_bus", True, True, "PoKeys BUS/I2C scan", detail=ident + " addresses=" + ",".join(f"0x{x:02X}" for x in found))
        except Exception as exc:
            return self._res("i2c_bus", False, True, "PoKeys BUS/I2C scan", error=str(exc))

    def test_bh1750(self, visible: bool = False, address: int = 0x5C) -> LksHardwareTestResult:
        try:
            with self._session("PLAY") as session:
                session.device.PK_I2CWrite(int(address), [0x01])
                time.sleep(0.02)
                session.device.PK_I2CWrite(int(address), [0x07])
                time.sleep(0.02)
                session.device.PK_I2CWrite(int(address), [0x20])
                time.sleep(0.18)
                data = session.device.PK_I2CRead(int(address), 2)
                if data is None or len(data) < 2:
                    raise RuntimeError(f"brak 2 bajtów z 0x{address:02X}")
                raw = (int(data[0]) << 8) | int(data[1])
                lux = raw / 1.2
                return self._res("light_bh1750", True, True, "BH1750 BUS read", detail=f"0x{address:02X} raw={raw} lux={lux:.2f}")
        except Exception as exc:
            return self._res("light_bh1750", False, True, "BH1750 BUS read", error=str(exc))

    def unsupported(self, component: str, label: str = "No sovereign tester yet") -> LksHardwareTestResult:
        return self._res(component, False, False, label, error="brak suwerennego testera LKS-N5 dla tego komponentu")

    def test_component(self, component: str, visible: bool = False) -> LksHardwareTestResult:
        name = str(component)
        if name == "pok_play":
            return self.check_pokeys("PLAY")
        if name == "pok_rec":
            return self.check_pokeys("REC")
        if name == "lcd_1602":
            return self.test_lcd_1602(visible=visible)
        if name == "matrix_led":
            return self.test_matrix_led(visible=visible)
        if name == "f_button":
            return self.test_f_buttons(visible=visible, timeout=6.0 if visible else 0.0)
        if name == "f_led":
            return self.test_f_led(visible=visible)
        if name == "keypad":
            return self.test_keypad(visible=visible, timeout=6.0 if visible else 0.0)
        if name == "i2c_bus":
            return self.test_i2c_bus(visible=visible)
        if name == "light_bh1750":
            return self.test_bh1750(visible=visible)
        if name in {"lcd", "display"}:
            return self.test_lcd_1602(visible=visible)
        return self.unsupported(name)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 ETAP 12 sovereign hardware tests")
    parser.add_argument("--component", default="", help="status_main component, e.g. lcd_1602, matrix_led, f_led")
    parser.add_argument("--visible", action="store_true", help="operator visible test: display writes / LED blink / key wait")
    parser.add_argument("--lib-path", default="")
    parser.add_argument("--repo-root", default="")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    tests = TarzanTspLksHardwareTests(repo_root=args.repo_root or None, lib_path=args.lib_path or None)
    component = args.component or "i2c_bus"
    result = tests.test_component(component, visible=bool(args.visible))
    mark = "OK" if result.ok else "OFF"
    print(f"{mark} {result.component} supported={1 if result.supported else 0} {result.label}")
    if result.detail:
        print(result.detail)
    if result.visible_action:
        print("VISIBLE:", result.visible_action)
    if result.error:
        print("ERROR:", result.error)
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
