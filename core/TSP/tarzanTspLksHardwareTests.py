from __future__ import annotations

"""TARZAN LKS-N5 — sprzętowe testy punktowe przez core/tarzanPoKeys.

Zasada po poprawce:
- ten moduł NIE importuje hardware.pokeys.PoKeys,
- ten moduł NIE tworzy PoKeysDevice,
- ten moduł NIE ma własnej sesji libusb,
- wszystko idzie przez nasz core: core/tarzanPoKeys.py,
- IDLE nie robi pollingu; testy są jednorazowe i tylko na żądanie.
"""

import argparse
import logging
import os
import glob
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

from core.tarzanPoKeys import TarzanPoKeys

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class LksHardwareTestResult:
    component: str
    ok: bool
    supported: bool
    label: str
    detail: str = ""
    error: str = ""
    visible_action: str = ""


class TarzanTspLksHardwareTests:
    """Suwerenne testery LKS-N5 oparte wyłącznie o TarzanPoKeys.

    Ten moduł może być użyty ręcznie/offline przez CLI albo przez diagnostykę,
    ale nie otwiera już starego toru ``hardware/pokeys/PoKeys.py``. Binding
    PoKeys istnieje tylko pod spodem w ``core/tarzanPoKeys.py``.
    """

    def __init__(
        self,
        repo_root: Optional[str] = None,
        lib_path: Optional[str] = None,
        pokeys: Optional[TarzanPoKeys] = None,
        allow_own_pokeys: bool = False,
    ) -> None:
        self.repo_root = Path(repo_root or REPO_ROOT).resolve()
        self.logger = logging.getLogger("TARZAN.LKS_HW_TESTS")
        self._own_pokeys_allowed = bool(allow_own_pokeys)
        self.pokeys: Optional[TarzanPoKeys]
        if pokeys is not None:
            self.pokeys = pokeys
        elif self._own_pokeys_allowed:
            self.pokeys = TarzanPoKeys(self.logger)
        else:
            # Runtime nie może tworzyć drugiej instancji TarzanPoKeys. Jedynym
            # właścicielem PoKeys/libusb ma być aktywny TarzanHardwareBridge.
            # Własna sesja jest dopuszczona tylko dla jawnego CLI/offline.
            self.pokeys = None
        self.lib_path = lib_path or (self.pokeys.get_lib_path() if self.pokeys is not None else "")
        self._connected = False

    def _ensure_connected(self) -> None:
        if self.pokeys is None:
            raise RuntimeError(
                "TarzanTspLksHardwareTests nie ma aktywnego TarzanPoKeys. "
                "W runtime użyj HardwareBridge.test_lks_component(); własny PoKeys "
                "wolno otworzyć tylko jawnie przez CLI/offline."
            )
        if self._connected and self.pokeys.is_any_connected():
            return
        self.pokeys.connect_all(self.lib_path)
        # Dla trybu offline/CLI ustawiamy domyślnie stan POINT_TEST,
        # aby operacje PK_* nie były blokowane przez Bramkę Stanów IDLE.
        self.pokeys.set_state("POINT_TEST")
        self._connected = True

    def _res(self, component: str, ok: bool, supported: bool, label: str, detail: str = "", error: str = "", visible_action: str = "") -> LksHardwareTestResult:
        return LksHardwareTestResult(component=component, ok=bool(ok), supported=bool(supported), label=label, detail=detail, error=error, visible_action=visible_action)

    def find_pokeys_library(self) -> Optional[str]:
        return self.pokeys.get_lib_path() if self.pokeys is not None else None

    def check_pokeys(self, board: str) -> LksHardwareTestResult:
        board = board.upper()
        component = "pok_play" if board == "PLAY" else "pok_rec"
        try:
            self._ensure_connected()
            dev = self.pokeys.get_device(board)
            ok = bool(dev is not None and self.pokeys.test_board_once(board))
            detail = self.pokeys.identity_text(board, dev) if dev is not None else f"{board} not connected"
            return self._res(component, ok, True, f"PoKeys {board} TarzanPoKeys test", detail=detail, error="" if ok else detail)
        except Exception as exc:
            return self._res(component, False, True, f"PoKeys {board} TarzanPoKeys test", error=str(exc))

    def test_lcd_1602(self, visible: bool = False, board: str = "BOTH") -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            boards = ("PLAY", "REC") if board.upper() in {"BOTH", "ALL"} else (board.upper(),)
            data = self.pokeys.test_lcd_1602_once(visible=visible, boards=boards)
            summary = str(data.get("summary") or "").strip()
            if not summary:
                summary = "; ".join(
                    f"LCD {b} {'OK' if d.get('ok') else 'FAIL'}"
                    for b, d in (data.get("boards") or {}).items()
                )
            detail = summary or str(data.get("boards", {}))[:240]
            error = "; ".join(str(x) for x in data.get("errors", []))
            return self._res(
                "lcd_1602",
                bool(data.get("ok")),
                True,
                "LCD 1602 PLAY+REC TarzanPoKeys test",
                detail=detail[:240],
                error=error,
                visible_action="LCD PLAY+REC: TEST -> BEZ BLEDOW / GOTOWE" if visible and data.get("ok") else "",
            )
        except Exception as exc:
            return self._res("lcd_1602", False, True, "LCD 1602 TarzanPoKeys test", error=str(exc))

    def test_matrix_led(self, visible: bool = False, board: str = "REC") -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            data = self.pokeys.test_matrix_led_once(visible=visible, board=board.upper())
            return self._res(
                "matrix_led",
                bool(data.get("ok")),
                True,
                "Matrix LED TarzanPoKeys test",
                detail=str(data)[:220],
                error=str(data.get("error", "") or ""),
                visible_action="Matrix pokazuje OK i gasnie" if visible and data.get("ok") else "",
            )
        except Exception as exc:
            return self._res("matrix_led", False, True, "Matrix LED TarzanPoKeys test", error=str(exc))

    def test_f_buttons(self, visible: bool = False, timeout: float = 0.0) -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            data = self.pokeys.read_f_buttons_once()
            return self._res("f_button", bool(data.get("ok")), True, "F1-F4 buttons TarzanPoKeys read", detail=str(data.get("values", {})), error=str(data.get("error", "") or ""))
        except Exception as exc:
            return self._res("f_button", False, True, "F1-F4 buttons TarzanPoKeys read", error=str(exc))

    def test_f_led(self, visible: bool = False) -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            data = self.pokeys.blink_f_led_once(visible=visible)
            return self._res(
                "f_led",
                bool(data.get("ok")),
                True,
                "F1-F4 LED TarzanPoKeys test",
                detail=str(data.get("pins", {})),
                error=str(data.get("error", "") or ""),
                visible_action="LED F1-F4 mrugaja i gasna" if visible and data.get("ok") else "",
            )
        except Exception as exc:
            return self._res("f_led", False, True, "F1-F4 LED TarzanPoKeys test", error=str(exc))

    def test_keypad(self, visible: bool = False, timeout: float = 0.0) -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            data = self.pokeys.read_keypad_once()
            return self._res("keypad", bool(data.get("ok")), True, "Keypad TarzanPoKeys status", detail="matrix status read" if data.get("ok") else "", error=str(data.get("error", "") or ""))
        except Exception as exc:
            return self._res("keypad", False, True, "Keypad TarzanPoKeys status", error=str(exc))

    def scan_i2c_bus(self, board: str = "PLAY"):
        self._ensure_connected()
        data = self.pokeys.scan_i2c_once(board.upper())
        return list(data.get("addresses") or data.get("found") or []), str(data)

    def test_i2c_bus(self, visible: bool = False) -> LksHardwareTestResult:
        """Realny agregat BUS/I2C dla LKS-N5.

        Nie uznajemy samej obecności CP2102/USB-UART za sukces.
        OK wymaga realnego ACK: adresy PoKeys BUS/I2C albo PoSensors.
        W runtime test light_laser jest dodatkowo wykonywany przez HardwareBridge,
        bo tam mamy dostęp do matrix sygnałów i aktywnego SignalBus.
        """
        try:
            self._ensure_connected()
            play = self.pokeys.scan_i2c_once("PLAY")
            rec = self.pokeys.scan_i2c_once("REC")
            play_found = list(play.get("addresses") or play.get("found") or [])
            rec_found = list(rec.get("addresses") or rec.get("found") or [])
            bus_scan_ok = bool((play.get("ok") or rec.get("ok")) and (play_found or rec_found))

            try:
                posensors = self.pokeys.read_posensors_once("PLAY")
                if not isinstance(posensors, dict):
                    posensors = {"ok": False, "raw": posensors}
            except Exception as exc:
                posensors = {"ok": False, "error": str(exc)}
            posensors_ok = bool(posensors.get("ok"))

            serial_links = sorted(glob.glob("/dev/serial/by-id/*"))
            tty_links = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
            usb_detail = "USB=" + (",".join(serial_links[:3] or tty_links[:3]) or "no-tty")
            play_txt = ",".join(f"0x{int(x):02X}" for x in play_found) or "none"
            rec_txt = ",".join(f"0x{int(x):02X}" for x in rec_found) or "none"
            ok = bool(bus_scan_ok or posensors_ok)
            detail = f"PLAY={play_txt} REC={rec_txt}; PoSensors={posensors_ok}; {usb_detail}"
            error = "" if ok else f"BUS_SCAN_NO_ADDR PLAY={play} REC={rec}; PoSensors={str(posensors)[:160]}"
            return self._res("i2c_bus", ok, True, "PoKeys BUS/I2C/PoSensors real ACK", detail=detail, error=error)
        except Exception as exc:
            return self._res("i2c_bus", False, True, "PoKeys BUS/I2C/PoSensors real ACK", error=str(exc))

    def test_bh1750(self, visible: bool = False, address: int = 0x5C) -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            data = self.pokeys.read_bh1750_lux_once("PLAY", None)
            return self._res("light_bh1750", bool(data.get("ok")), True, "BH1750 TarzanPoKeys read", detail=str(data)[:220], error=str(data.get("error", "") or ""))
        except Exception as exc:
            return self._res("light_bh1750", False, True, "BH1750 TarzanPoKeys read", error=str(exc))

    def test_posensors(self, visible: bool = False) -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            data = self.pokeys.read_posensors_once("PLAY")
            return self._res("posensors", bool(data.get("ok")), True, "PoSensors TarzanPoKeys read", detail=str(data)[:260], error="" if data.get("ok") else str(data)[:180])
        except Exception as exc:
            return self._res("posensors", False, True, "PoSensors TarzanPoKeys read", error=str(exc))

    def test_xyz_poksyg(self, visible: bool = False) -> LksHardwareTestResult:
        try:
            self._ensure_connected()
            data = self.pokeys.read_xyz_poksyg_once()
            return self._res("level_xyz", bool(data.get("ok")), True, "XYZ Poksyg TarzanPoKeys read", detail=str(data.get("values", {}))[:220], error="; ".join(str(x) for x in data.get("errors", [])))
        except Exception as exc:
            return self._res("level_xyz", False, True, "XYZ Poksyg TarzanPoKeys read", error=str(exc))

    def unsupported(self, component: str, label: str = "No sovereign tester yet") -> LksHardwareTestResult:
        return self._res(component, False, False, label, error="brak suwerennego testera LKS-N5 dla tego komponentu")

    def test_component(self, component: str, visible: bool = False) -> LksHardwareTestResult:
        name = str(component)
        
        # Otwieramy bramkę stanów dla testów CLI/punktowych
        if self.pokeys:
            self.pokeys.begin_point_test(name)
            
        try:
            if name == "pok_play":
                return self.check_pokeys("PLAY")
            if name == "pok_rec":
                return self.check_pokeys("REC")
            if name == "lcd_1602" or name in {"lcd", "display"}:
                return self.test_lcd_1602(visible=visible)
            if name == "matrix_led":
                return self.test_matrix_led(visible=visible)
            if name == "f_button":
                return self.test_f_buttons(visible=visible)
            if name == "f_led":
                return self.test_f_led(visible=visible)
            if name == "keypad":
                return self.test_keypad(visible=visible)
            if name == "i2c_bus":
                return self.test_i2c_bus(visible=visible)
            if name == "light_bh1750":
                return self.test_bh1750(visible=visible)
            if name in {"posensors", "sensors"}:
                return self.test_posensors(visible=visible)
            if name in {"level_xyz", "xyz", "mma7660"}:
                return self.test_xyz_poksyg(visible=visible)
            return self.unsupported(name)
        finally:
            if self.pokeys:
                self.pokeys.end_active_state()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 hardware tests through core/tarzanPoKeys")
    parser.add_argument("--component", default="", help="status_main component, e.g. lcd_1602, matrix_led, f_led")
    parser.add_argument("--visible", action="store_true", help="operator visible test: display writes / LED blink / key wait")
    parser.add_argument("--lib-path", default="")
    parser.add_argument("--repo-root", default="")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    tests = TarzanTspLksHardwareTests(
        repo_root=args.repo_root or None,
        lib_path=args.lib_path or None,
        allow_own_pokeys=True,
    )
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
