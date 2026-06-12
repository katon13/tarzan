from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
POKEYS = ROOT / "core" / "tarzanPoKeys.py"
SIGNALS = ROOT / "core" / "tarzanZmienneSygnalowe.py"

LED_SPECS = [
    ("rec_p46_led_f1", 46, "F1"),
    ("rec_p48_led_f2", 48, "F2"),
    ("rec_p50_led_f3", 50, "F3"),
    ("rec_p52_led_f4", 52, "F4"),
]


def find_sygnal_block(text: str, name: str) -> tuple[int, int, str]:
    start = text.find(f"{name} = _sygnal(")
    if start < 0:
        raise SystemExit(f"Nie znaleziono bloku {name}")
    # Bloki w tym pliku kończą się pierwszą linią z samotnym ')' po starcie.
    m = re.search(r"^\)\s*$", text[start:], flags=re.MULTILINE)
    if not m:
        raise SystemExit(f"Nie znaleziono końca bloku {name}")
    end = start + m.end()
    return start, end, text[start:end]


def replace_or_fail(block: str, pattern: str, replacement: str, name: str) -> str:
    new, count = re.subn(pattern, replacement, block, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"Nie wykonano zamiany w {name}: {pattern}")
    return new


def patch_signals() -> None:
    text = SIGNALS.read_text(encoding="utf-8")
    for name, pin, label in LED_SPECS:
        start, end, block = find_sygnal_block(text, name)
        block = replace_or_fail(block, r'kierunek="[^"]+"', 'kierunek="OUT"', name)
        block = replace_or_fail(block, r'default="[^"]+"', 'default="1"', name)
        block = replace_or_fail(block, r'hardware_function=HW_[A-Z_]+', 'hardware_function=HW_GPIO', name)
        block = replace_or_fail(block, r'hardware_label="[^"]+"', f'hardware_label="GPIO output REC P{pin} LED {label}"', name)
        block = replace_or_fail(block, r'is_shared_pin=(True|False)', 'is_shared_pin=False', name)
        block = replace_or_fail(block, r'conflict_group=("[^"]+"|None)', 'conflict_group=None', name)
        text = text[:start] + block + text[end:]
    SIGNALS.write_text(text, encoding="utf-8")
    print("OK: REC F1-F4 LEDs mapped as GPIO OUT/off default=1")


def patch_pokeys() -> None:
    text = POKEYS.read_text(encoding="utf-8")

    marker = '    F_LED_PINS: Dict[str, int] = {"F1": 46, "F2": 48, "F3": 50, "F4": 52}\n'
    if marker not in text:
        raise SystemExit("Nie znaleziono F_LED_PINS")
    if "F_LED_ON_VALUE" not in text:
        text = text.replace(
            marker,
            marker
            + "    # REC F-LED są aktywne stanem 0. Po teście i w spoczynku OFF = 1.\n"
            + "    F_LED_ON_VALUE = 0\n"
            + "    F_LED_OFF_VALUE = 1\n",
            1,
        )

    start = text.find("    def blink_f_led_once(self, visible: bool = False) -> Dict[str, Any]:")
    if start < 0:
        if "def set_f_leds_off_once" in text:
            print("OK: F-LED methods already patched")
            POKEYS.write_text(text, encoding="utf-8")
            return
        raise SystemExit("Nie znaleziono blink_f_led_once")
    next_marker = "    def _clear_matrix_keyboard_hid_mapping"
    end = text.find(next_marker, start)
    if end < 0:
        raise SystemExit("Nie znaleziono końca bloku blink_f_led_once")

    new_block = '''    def set_f_leds_off_once(self) -> Dict[str, Any]:
        """Gasi fizyczne diody F1-F4 na REC.

        W okablowaniu TARZAN F-LED są aktywne stanem 0, więc OFF zapisujemy jako 1.
        """
        with self._lock:
            dev = self.get_device("REC")
            if dev is None:
                return {"ok": False, "error": "REC not connected"}
            errors: List[str] = []
            for name, pin in self.F_LED_PINS.items():
                try:
                    self.set_digital_output(dev, pin, self.F_LED_OFF_VALUE)
                except Exception as exc:
                    errors.append(f"{name}/P{pin}: {exc}")
            return {"ok": not errors, "pins": dict(self.F_LED_PINS), "off_value": self.F_LED_OFF_VALUE, "errors": errors}

    def blink_f_led_once(self, visible: bool = False) -> Dict[str, Any]:
        with self._lock:
            dev = self.get_device("REC")
            if dev is None:
                return {"ok": False, "error": "REC not connected"}
            errors: List[str] = []
            try:
                # Test zaczynamy od OFF i kończymy OFF. Diody nie mają świecić stale.
                off_res = self.set_f_leds_off_once()
                if not off_res.get("ok"):
                    errors.extend(off_res.get("errors", []))

                if visible:
                    for name, pin in self.F_LED_PINS.items():
                        try:
                            self.set_digital_output(dev, pin, self.F_LED_ON_VALUE)
                            time.sleep(0.08)
                            self.set_digital_output(dev, pin, self.F_LED_OFF_VALUE)
                        except Exception as exc:
                            errors.append(f"{name}/P{pin}: {exc}")

                final_off = self.set_f_leds_off_once()
                if not final_off.get("ok"):
                    errors.extend(final_off.get("errors", []))
                return {
                    "ok": not errors,
                    "pins": dict(self.F_LED_PINS),
                    "on_value": self.F_LED_ON_VALUE,
                    "off_value": self.F_LED_OFF_VALUE,
                    "errors": errors,
                }
            except Exception as exc:
                try:
                    self.set_f_leds_off_once()
                except Exception:
                    pass
                return {"ok": False, "error": str(exc), "pins": dict(self.F_LED_PINS)}

'''
    text = text[:start] + new_block + text[end:]
    POKEYS.write_text(text, encoding="utf-8")
    print("OK: blink_f_led_once leaves all F-LED OFF and set_f_leds_off_once added")


if __name__ == "__main__":
    patch_signals()
    patch_pokeys()
    print("OK: TARZAN F-LED GPIO/OFF patch applied")
