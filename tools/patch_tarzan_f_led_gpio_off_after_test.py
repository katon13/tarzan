from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
POKEYS = ROOT / "core" / "tarzanPoKeys.py"
SIGNALS = ROOT / "core" / "tarzanZmienneSygnalowe.py"


def replace_block(text: str, name: str, replacements: dict[str, str]) -> str:
    pattern = rf"({name}\s*=\s*_sygnal\([\s\S]*?\n\))"
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"Nie znaleziono bloku {name}")
    block = m.group(1)
    new = block
    for old, new_value in replacements.items():
        new2 = re.sub(old, new_value, new, count=1)
        if new2 == new:
            raise SystemExit(f"Nie wykonano zamiany w {name}: {old}")
        new = new2
    return text[:m.start(1)] + new + text[m.end(1):]


def patch_signals() -> None:
    text = SIGNALS.read_text(encoding="utf-8")
    led_names = [
        ("rec_p46_led_f1", 46, "F1"),
        ("rec_p48_led_f2", 48, "F2"),
        ("rec_p50_led_f3", 50, "F3"),
        ("rec_p52_led_f4", 52, "F4"),
    ]
    for name, pin, label in led_names:
        text = replace_block(text, name, {
            r'kierunek="[^"]+"': 'kierunek="OUT"',
            r'hardware_function=HW_[A-Z_]+': 'hardware_function=HW_GPIO',
            r'hardware_label="[^"]+"': f'hardware_label="GPIO output REC P{pin} LED {label}"',
            r'conflict_group="[^"]+"|conflict_group=None': 'conflict_group=None',
        })
    SIGNALS.write_text(text, encoding="utf-8")
    print("OK: F1-F4 LED mapped as REC GPIO OUT in tarzanZmienneSygnalowe.py")


def patch_pokeys() -> None:
    text = POKEYS.read_text(encoding="utf-8")

    # Dodaj jawne wartości dla LED: ON=0, OFF=1 (w układzie TARZAN/PoKeys wyjście jest odwrócone).
    marker = '    F_LED_PINS: Dict[str, int] = {"F1": 46, "F2": 48, "F3": 50, "F4": 52}\n'
    if marker not in text:
        raise SystemExit("Nie znaleziono F_LED_PINS")
    insert = (
        marker +
        "    # F-LED na REC są aktywne stanem 0. OFF po teście/startupie = 1.\n"
        "    F_LED_ON_VALUE = 0\n"
        "    F_LED_OFF_VALUE = 1\n"
    )
    if "F_LED_OFF_VALUE" not in text:
        text = text.replace(marker, insert)

    old = '''    def blink_f_led_once(self, visible: bool = False) -> Dict[str, Any]:\n        with self._lock:\n            dev = self.get_device("REC")\n            if dev is None:\n                return {"ok": False, "error": "REC not connected"}\n            try:\n                if visible:\n                    for pin in self.F_LED_PINS.values():\n                        self.set_digital_output(dev, pin, 0)\n                    for pin in self.F_LED_PINS.values():\n                        self.set_digital_output(dev, pin, 1)\n                        time.sleep(0.08)\n                        self.set_digital_output(dev, pin, 0)\n                return {"ok": True, "pins": dict(self.F_LED_PINS)}\n            except Exception as exc:\n                return {"ok": False, "error": str(exc)}\n'''
    new = '''    def set_f_leds_off_once(self) -> Dict[str, Any]:\n        """Gasi wszystkie fizyczne diody F1-F4 na REC.\n\n        W układzie TARZAN F-LED są aktywne stanem 0, więc OFF zapisujemy jako 1.\n        """\n        with self._lock:\n            dev = self.get_device("REC")\n            if dev is None:\n                return {"ok": False, "error": "REC not connected"}\n            errors: List[str] = []\n            for name, pin in self.F_LED_PINS.items():\n                try:\n                    self.set_digital_output(dev, pin, self.F_LED_OFF_VALUE)\n                except Exception as exc:\n                    errors.append(f"{name}/P{pin}: {exc}")\n            return {"ok": not errors, "pins": dict(self.F_LED_PINS), "off_value": self.F_LED_OFF_VALUE, "errors": errors}\n\n    def blink_f_led_once(self, visible: bool = False) -> Dict[str, Any]:\n        with self._lock:\n            dev = self.get_device("REC")\n            if dev is None:\n                return {"ok": False, "error": "REC not connected"}\n            errors: List[str] = []\n            try:\n                # Najpierw zawsze gaś wszystkie diody, żeby test nie zostawiał stanu z poprzedniego startu.\n                off_res = self.set_f_leds_off_once()\n                if not off_res.get("ok"):\n                    errors.extend(off_res.get("errors", []))\n\n                if visible:\n                    for name, pin in self.F_LED_PINS.items():\n                        try:\n                            self.set_digital_output(dev, pin, self.F_LED_ON_VALUE)\n                            time.sleep(0.08)\n                            self.set_digital_output(dev, pin, self.F_LED_OFF_VALUE)\n                        except Exception as exc:\n                            errors.append(f"{name}/P{pin}: {exc}")\n\n                # Po teście zawsze gasimy wszystkie F-LED, także gdy jedna komenda po drodze zgłosi błąd.\n                final_off = self.set_f_leds_off_once()\n                if not final_off.get("ok"):\n                    errors.extend(final_off.get("errors", []))\n                return {"ok": not errors, "pins": dict(self.F_LED_PINS), "on_value": self.F_LED_ON_VALUE, "off_value": self.F_LED_OFF_VALUE, "errors": errors}\n            except Exception as exc:\n                try:\n                    self.set_f_leds_off_once()\n                except Exception:\n                    pass\n                return {"ok": False, "error": str(exc), "pins": dict(self.F_LED_PINS)}\n'''
    if old in text:
        text = text.replace(old, new)
    elif "def set_f_leds_off_once" not in text:
        raise SystemExit("Nie znaleziono starego blink_f_led_once do wymiany")

    POKEYS.write_text(text, encoding="utf-8")
    print("OK: F-LED blink now ends with all LEDs OFF in tarzanPoKeys.py")


if __name__ == "__main__":
    patch_signals()
    patch_pokeys()
    print("OK: patch TARZAN F-LED GPIO/OFF applied")
