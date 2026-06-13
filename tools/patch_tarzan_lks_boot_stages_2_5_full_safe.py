from pathlib import Path
import runpy

ROOT = Path.cwd()

STAGE_SCRIPTS = [
    "tools/patch_tarzan_lks_boot_detect_vs_test_stage2.py",
    "tools/patch_tarzan_lks_boot_stage3_one_full_matrix_path.py",
    "tools/patch_tarzan_lks_boot_stage4_final_ready_outputs.py",
    "tools/patch_tarzan_lks_boot_stage5_progress_final_cleanup.py",
]


def _read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _stage_done(stage: int) -> bool:
    """Pozwala bezpiecznie uruchomić paczkę także wtedy, gdy część etapów już jest w repo."""
    boot = _read("core/TSP/tarzanTspLksBootProgress.py")
    hwtests = _read("core/TSP/tarzanTspLksHardwareTests.py")
    server = _read("core/TSP/tarzanTspServer.py")
    bridge = _read("core/tarzanHardwareBridge.py")

    if stage == 2:
        return (
            "boot_hardware = szybkie wykrycie" in boot
            and "PoKeys USB detect" in boot
            and "Full device tests" in boot
        )
    if stage == 3:
        return (
            "def run_lks_full_matrix_via_bridge" in hwtests
            and "run_lks_full_matrix_via_bridge" in boot
            and "run_lks_full_matrix_via_bridge" in server
        )
    if stage == 4:
        return (
            "def apply_lks_final_ready_outputs" in bridge
            and "apply_lks_final_ready_outputs" in boot
        )
    if stage == 5:
        return (
            "ETAP 5: procenty odpowiadaja fazom pracy" in boot
            and "SCENE_BOOT_TEST, 60" in boot
            and "98%" in boot
            and "progress_start=60" in server
        )
    return False


def run_stage_scripts() -> None:
    for idx, script in enumerate(STAGE_SCRIPTS, start=2):
        path = ROOT / script
        if not path.exists():
            raise SystemExit(f"Brak skryptu etapu: {script}")
        if _stage_done(idx):
            print(f"SKIP ETAP {idx}: already applied")
            continue
        print(f"RUN {script}")
        runpy.run_path(str(path), run_name="__main__")


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> tuple[str, bool]:
    start = text.find(start_marker)
    if start < 0:
        return text, False
    end = text.find(end_marker, start)
    if end < 0:
        return text, False
    return text[:start] + replacement + text[end:], True


def ensure_f_led_safe_off(root: Path) -> bool:
    """Gwarantuje ustalone zachowanie F-LED: OFF=1, ON=0, test konczy OFF."""
    path = root / "core" / "tarzanPoKeys.py"
    text = path.read_text(encoding="utf-8")
    original = text

    block = """    def read_f_buttons_once(self) -> Dict[str, Any]:
        with self._lock:
            dev = self.get_device("REC")
            if dev is None:
                return {"ok": False, "values": {}, "error": "REC not connected"}
            try:
                values = {name: self.read_pin(dev, pin) for name, pin in self.F_BUTTON_PINS.items()}
                return {"ok": True, "values": values}
            except Exception as exc:
                return {"ok": False, "values": {}, "error": str(exc)}

    def set_f_leds_off_once(self) -> Dict[str, Any]:
        \"\"\"Naturalny stan F1-F4 LED po testach: zgaszone.

        F-LED sa aktywne stanem niskim: ON=0, OFF=1.
        \"\"\"
        with self._lock:
            dev = self.get_device("REC")
            if dev is None:
                return {"ok": False, "error": "REC not connected", "pins": dict(self.F_LED_PINS)}
            try:
                for pin in self.F_LED_PINS.values():
                    self.set_digital_output(dev, int(pin), 1)
                return {"ok": True, "pins": dict(self.F_LED_PINS), "off_value": 1}
            except Exception as exc:
                return {"ok": False, "error": str(exc), "pins": dict(self.F_LED_PINS)}

    def blink_f_led_once(self, visible: bool = False) -> Dict[str, Any]:
        \"\"\"Test F1-F4 LED: krotkie migniecie i zawsze powrot do OFF.\"\"\"
        with self._lock:
            dev = self.get_device("REC")
            if dev is None:
                return {"ok": False, "error": "REC not connected", "pins": dict(self.F_LED_PINS)}
            try:
                for pin in self.F_LED_PINS.values():
                    self.set_digital_output(dev, int(pin), 1)
                if visible:
                    for pin in self.F_LED_PINS.values():
                        self.set_digital_output(dev, int(pin), 0)
                        time.sleep(0.08)
                        self.set_digital_output(dev, int(pin), 1)
                for pin in self.F_LED_PINS.values():
                    self.set_digital_output(dev, int(pin), 1)
                return {"ok": True, "pins": dict(self.F_LED_PINS), "off_value": 1}
            except Exception as exc:
                try:
                    for pin in self.F_LED_PINS.values():
                        self.set_digital_output(dev, int(pin), 1)
                except Exception:
                    pass
                return {"ok": False, "error": str(exc), "pins": dict(self.F_LED_PINS)}

"""
    text, ok = replace_between(text, "    def read_f_buttons_once", "    def read_keypad_once", block)
    if not ok:
        raise SystemExit("PATCH FAILED: no F-button/F-LED block in core/tarzanPoKeys.py")
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def ensure_lcd_ready_text_not_fake(root: Path) -> bool:
    """Nie piszemy na LCD 'BEZ BLEDOW', bo czesc testow moze byc PARTIAL."""
    path = root / "core" / "tarzanHardwareBridge.py"
    text = path.read_text(encoding="utf-8")
    old = 'self.pokeys.lcd_write_lines(board, "BEZ BLEDOW", "GOTOWE")'
    new = 'self.pokeys.lcd_write_lines(board, "LKS GOTOWE", "STATUS NA N5")'
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return True
    return False


def check_no_dangerous_changes(root: Path) -> None:
    pok = (root / "core" / "tarzanPoKeys.py").read_text(encoding="utf-8")
    if 'F_LED_PINS: Dict[str, int] = {"F1": 46, "F2": 48, "F3": 50, "F4": 52}' not in pok:
        raise SystemExit("SAFETY FAIL: F_LED_PINS changed or missing")
    if "def set_f_leds_off_once" not in pok:
        raise SystemExit("SAFETY FAIL: set_f_leds_off_once missing")
    if "def matrix_led_ready_heart_once" not in pok:
        raise SystemExit("SAFETY FAIL: matrix_led_ready_heart_once missing")
    if "[0x00, 0x66, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00]" not in pok:
        raise SystemExit("SAFETY FAIL: confirmed Matrix heart B pattern missing")

    boot = (root / "core" / "TSP" / "tarzanTspLksBootProgress.py").read_text(encoding="utf-8")
    if "time.sleep(max(self.pause_s, 2.4))" not in boot:
        raise SystemExit("SAFETY FAIL: intro_status wait contract missing")
    if "self.n5.set_many_statuses(self.statuses)" not in boot:
        raise SystemExit("SAFETY FAIL: final Nextion status cache missing")
    if "SCENE_BOOT_TEST, 60" not in boot:
        raise SystemExit("SAFETY FAIL: full test progress range missing")

    hb = (root / "core" / "tarzanHardwareBridge.py").read_text(encoding="utf-8")
    if "def apply_lks_final_ready_outputs" not in hb:
        raise SystemExit("SAFETY FAIL: final ready outputs missing")
    if 'lcd_write_lines(board, "LKS GOTOWE", "STATUS NA N5")' not in hb:
        raise SystemExit("SAFETY FAIL: neutral LCD ready text missing")


def ensure_matrix_test_finishes_ready(root: Path) -> bool:
    """Nie zostawia matrix po tescie w pustej/losowej ramce.

    Ustalenie z watku: wariant B serca jest poprawny fizycznie. Test moze
    mignac OK, ale po tescie i w stanie READY Matrix LED ma pokazywac serce,
    nie puste dane ani kreski.
    """
    path = root / "core" / "tarzanPoKeys.py"
    text = path.read_text(encoding="utf-8")
    original = text

    if "def matrix_led_ready_heart_once" not in text:
        old = '''    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:
        if not visible:
            return {"ok": self.test_board_once(board), "board": board}
        cols = self._matrix_text_columns("OK")
        res = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))
        time.sleep(0.20)
        self.matrix_write_frame(board, [0] * 8)
        return res
'''
        new = old + '''
    def matrix_led_ready_heart_once(self, board: Any = "REC") -> Dict[str, Any]:
        # Koncowy stan READY dla Matrix LED; wariant B potwierdzony fizycznie.
        heart_columns = [0x00, 0x66, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00]
        return self.matrix_write_frame(board, self._matrix_rows_from_columns(heart_columns))
'''
        if old in text:
            text = text.replace(old, new, 1)

    old_tail = '''        time.sleep(0.20)
        self.matrix_write_frame(board, [0] * 8)
        return res
'''
    new_tail = '''        time.sleep(0.20)
        ready = self.matrix_led_ready_heart_once(board) if hasattr(self, "matrix_led_ready_heart_once") else {"ok": True}
        if isinstance(ready, dict) and not ready.get("ok", True):
            return {"ok": False, "board": board, "write": res, "matrix_ready": ready}
        return {"ok": bool(res.get("ok")), "board": board, "write": res, "matrix_ready": ready}
'''
    if old_tail in text:
        text = text.replace(old_tail, new_tail, 1)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    run_stage_scripts()
    changed = []
    if ensure_f_led_safe_off(ROOT):
        changed.append("core/tarzanPoKeys.py:F_LED_SAFE_OFF")
    if ensure_lcd_ready_text_not_fake(ROOT):
        changed.append("core/tarzanHardwareBridge.py:LCD_READY_TEXT")
    if ensure_matrix_test_finishes_ready(ROOT):
        changed.append("core/tarzanPoKeys.py:MATRIX_TEST_FINISHES_READY")
    check_no_dangerous_changes(ROOT)
    print("OK: FULL SAFE LKS BOOT CLEANUP applied; extra=" + (", ".join(changed) if changed else "none"))


if __name__ == "__main__":
    main()
