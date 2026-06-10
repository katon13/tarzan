from __future__ import annotations

"""
tarzanPokABC.py

PoKeys Architecture / Board / Configuration dla TARZANA.

To jest betonowy kontrakt PLAY/REC:
- architektura płytek PoKeys57U,
- role płytek PLAY/REC i ich seriale,
- piny 1..55 dla każdej płytki,
- funkcje specjalne: LCD, Matrix LED, Keyboard, I2C, PoExtBus, Pulse Engine,
- porównanie z core/tarzanZmienneSygnalowe.py,
- wynik OK/FAIL dla startu systemu.

Ten plik NIE wykonuje sprzętu. Wykonanie PK_* zostaje w core/tarzanPoKeys.py.
Jeżeli tarzanPoKeys.py nie dostanie potwierdzenia z tego pliku, konfiguracja PoKeys
ma być traktowana jako FAIL, a nie jako miękkie ostrzeżenie.
"""

from typing import Any, Dict, Iterable, List, Optional, Set

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

POKEYS57_PIN_MIN = 1
POKEYS57_PIN_MAX = 55

TARZAN_POKEYS_BOARD_ROLES: Dict[str, Dict[str, Any]] = {
    "PLAY": {
        "serial": int(POKEYS57U_PLAY_DEVICE_SERIAL),
        "device": "PoKeys57U",
        "role": "PLAY",
        "required": True,
    },
    "REC": {
        "serial": int(POKEYS57U_REC_DEVICE_SERIAL),
        "device": "PoKeys57U",
        "role": "REC",
        "required": True,
    },
}


def _signal_reserved(sig: TarzanSygnal) -> bool:
    return str(sig.typ or "").upper() == "RESERVED" or str(sig.kierunek or "").upper() == "RESERVED"


def _signal_special(sig: TarzanSygnal) -> bool:
    return str(sig.typ or "").upper() == "F" or str(sig.kierunek or "").upper() == "F"


def expected_role(sig: TarzanSygnal) -> str:
    typ = str(sig.typ or "").upper()
    direction = str(sig.kierunek or "").upper()
    hf = str(sig.hardware_function or "").upper()
    if typ == "RESERVED" or direction == "RESERVED" or hf == HW_RESERVED:
        return "RESERVED"
    if hf == HW_SYSTEM:
        return "SYSTEM"
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


def expected_pin_cap_names(sig: TarzanSygnal) -> List[str]:
    typ = str(sig.typ or "").upper()
    direction = str(sig.kierunek or "").upper()
    hf = str(sig.hardware_function or "").upper()
    if typ == "RESERVED" or direction == "RESERVED" or hf == HW_RESERVED:
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


def _pin_cap_values(cap_enum: Any, cap_names: Iterable[str]) -> Dict[str, int]:
    values: Dict[str, int] = {}
    if cap_enum is None:
        return values
    for name in cap_names:
        try:
            value = getattr(cap_enum, str(name), None)
            if value is not None:
                values[str(name)] = int(value)
        except Exception:
            continue
    return values


def _read_pin_config_value(pin_obj: Any) -> Optional[int]:
    for attr in ("PinFunction", "pinFunction", "PinCap", "PinCapability"):
        try:
            if hasattr(pin_obj, attr):
                return int(getattr(pin_obj, attr))
        except Exception:
            continue
    return None


def _build_static_architecture() -> Dict[str, Any]:
    boards: Dict[str, Any] = {}
    for board, meta in TARZAN_POKEYS_BOARD_ROLES.items():
        pins: Dict[int, Dict[str, Any]] = {}
        for sig in sorted(WSZYSTKIE_SYGNALY.values(), key=lambda s: (str(s.plytka), int(s.pin or 999), str(s.nazwa))):
            if str(sig.plytka or "").upper() != board or sig.pin is None:
                continue
            pin = int(sig.pin)
            pins[pin] = {
                "signal": sig.nazwa,
                "pin": pin,
                "type": sig.typ,
                "direction": sig.kierunek,
                "hardware_function": sig.hardware_function,
                "hardware_label": sig.hardware_label,
                "pin_is_fixed": bool(sig.pin_is_fixed),
                "is_shared_pin": bool(sig.is_shared_pin),
                "conflict_group": sig.conflict_group,
                "panel_port": sig.panel_port,
                "group": sig.grupa,
                "class": sig.klasa_wykonawcza,
                "status": sig.status,
                "canonical": sig.kanoniczna_nazwa,
                "role": expected_role(sig),
                "reserved": _signal_reserved(sig),
                "special": _signal_special(sig),
                "expected_pin_caps": expected_pin_cap_names(sig),
            }
        boards[board] = {**meta, "pins": pins}
    return {
        "name": "TARZAN_POKEYS_ABC",
        "description": "PoKeys Architecture / Board / Configuration for TARZAN PLAY/REC",
        "pin_range": [POKEYS57_PIN_MIN, POKEYS57_PIN_MAX],
        "boards": boards,
    }


TARZAN_POKEYS_BOARD_ARCHITECTURE: Dict[str, Any] = _build_static_architecture()


class TarzanPokABC:
    """Twardy walidator ABC PLAY/REC.

    Nie dotyka sprzętu samodzielnie. Przyjmuje snapshoty/obiekty zwrócone przez
    tarzanPoKeys.py i mówi OK/FAIL. Brak potwierdzenia ABC = FAIL.
    """

    def __init__(self, logger: Any = None, signals: Optional[Dict[str, TarzanSygnal]] = None) -> None:
        self.logger = logger
        self.signals = signals or WSZYSTKIE_SYGNALY
        self.architecture = TARZAN_POKEYS_BOARD_ARCHITECTURE

    def board_meta(self, board: str) -> Dict[str, Any]:
        board = str(board or "").upper()
        return dict(TARZAN_POKEYS_BOARD_ROLES.get(board, {}))

    def board_contract(self, board: str) -> Dict[str, Any]:
        board = str(board or "").upper()
        errors: List[Any] = []
        if board not in TARZAN_POKEYS_BOARD_ROLES:
            return {"ok": False, "board": board, "errors": ["UNKNOWN_BOARD_ROLE"], "pins": {}, "pin_count": 0}
        pins: Dict[int, Dict[str, Any]] = {}
        seen_names: Set[str] = set()
        duplicates: List[Any] = []
        for sig in sorted(self.signals.values(), key=lambda s: (str(s.plytka), int(s.pin or 999), str(s.nazwa))):
            if str(sig.plytka or "").upper() != board or sig.pin is None:
                continue
            pin = int(sig.pin)
            if sig.nazwa in seen_names:
                duplicates.append({"signal": sig.nazwa, "error": "DUPLICATE_SIGNAL_NAME"})
            seen_names.add(sig.nazwa)
            if pin in pins:
                duplicates.append({"pin": pin, "signal": sig.nazwa, "previous": pins[pin].get("signal"), "error": "DUPLICATE_PIN"})
            pins[pin] = {
                "signal": sig.nazwa,
                "pin": pin,
                "type": sig.typ,
                "direction": sig.kierunek,
                "hardware_function": sig.hardware_function,
                "hardware_label": sig.hardware_label,
                "fixed": bool(sig.pin_is_fixed),
                "shared": bool(sig.is_shared_pin),
                "conflict_group": sig.conflict_group,
                "panel_port": sig.panel_port,
                "group": sig.grupa,
                "role": expected_role(sig),
                "reserved": _signal_reserved(sig),
                "special": _signal_special(sig),
                "expected_pin_caps": expected_pin_cap_names(sig),
            }
            if pin < POKEYS57_PIN_MIN or pin > POKEYS57_PIN_MAX:
                errors.append({"signal": sig.nazwa, "pin": pin, "error": "PIN_OUT_OF_POKEYS57_RANGE"})
            if not bool(sig.pin_is_fixed):
                errors.append({"signal": sig.nazwa, "pin": pin, "error": "PIN_NOT_FIXED"})
            if not sig.hardware_function:
                errors.append({"signal": sig.nazwa, "pin": pin, "error": "MISSING_HW_FUNCTION"})
            if not sig.typ or not sig.kierunek:
                errors.append({"signal": sig.nazwa, "pin": pin, "error": "MISSING_TYPE_OR_DIRECTION"})
        missing = [pin for pin in range(POKEYS57_PIN_MIN, POKEYS57_PIN_MAX + 1) if pin not in pins]
        for pin in missing:
            errors.append({"pin": pin, "error": "BAD_PIN_MISSING"})
        errors.extend(duplicates)
        return {
            "ok": not errors,
            "board": board,
            "serial": int(TARZAN_POKEYS_BOARD_ROLES[board]["serial"]),
            "pins": pins,
            "pin_count": len(pins),
            "missing_pins": missing,
            "errors": errors,
        }

    def configuration_contract(self) -> Dict[str, Any]:
        boards = {board: self.board_contract(board) for board in TARZAN_POKEYS_BOARD_ROLES}
        errors: List[Any] = []
        for board, res in boards.items():
            for err in res.get("errors", []):
                errors.append({"board": board, **err} if isinstance(err, dict) else {"board": board, "error": err})
        return {"ok": not errors, "boards": boards, "errors": errors, "architecture": self.architecture}

    def confirm_signal_map_abc(self) -> Dict[str, Any]:
        """Twarda kontrola statycznej mapy: PLAY i REC muszą mieć 1..55."""
        contract = self.configuration_contract()
        if contract.get("ok"):
            return {"ok": True, "source": "tarzanPokABC.py", "message": "ABC_SIGNAL_MAP_OK", "contract": contract}
        return {"ok": False, "source": "tarzanPokABC.py", "error": "ABC_SIGNAL_MAP_FAIL", "contract": contract, "errors": contract.get("errors", [])}

    def verify_board_identity_from_serial(self, board: str, actual_serial: Optional[int]) -> Dict[str, Any]:
        board = str(board or "").upper()
        meta = self.board_meta(board)
        if not meta:
            return {"ok": False, "board": board, "error": "UNKNOWN_BOARD_ROLE"}
        expected = int(meta["serial"])
        try:
            actual = int(actual_serial) if actual_serial is not None else None
        except Exception:
            actual = None
        ok = actual == expected
        return {
            "ok": ok,
            "board": board,
            "expected_serial": expected,
            "actual_serial": actual,
            "error": None if ok else "BAD_SERIAL",
        }

    def verify_signal_pin_against_device(self, board: str, sig: TarzanSygnal, pin_obj: Any, *, cap_enum: Any = None, strict_pin_function: bool = True) -> Dict[str, Any]:
        board = str(board or "").upper()
        expected_caps = expected_pin_cap_names(sig)
        cap_values = _pin_cap_values(cap_enum, expected_caps)
        actual_cap = _read_pin_config_value(pin_obj)
        item: Dict[str, Any] = {
            "source": "tarzanPokABC.py",
            "signal": sig.nazwa,
            "board": board,
            "pin": int(sig.pin or 0),
            "type": sig.typ,
            "direction": sig.kierunek,
            "hardware_function": sig.hardware_function,
            "hardware_label": sig.hardware_label,
            "role": expected_role(sig),
            "expected_pin_caps": expected_caps,
            "expected_pin_cap_values": cap_values,
            "actual_pin_function": actual_cap,
            "ok": True,
            "errors": [],
            "warnings": [],
        }
        if str(sig.plytka or "").upper() != board:
            item["errors"].append("BAD_BOARD_ROLE")
        if not sig.pin_is_fixed:
            item["errors"].append("PIN_NOT_FIXED")
        if sig.pin is None or int(sig.pin) < POKEYS57_PIN_MIN or int(sig.pin) > POKEYS57_PIN_MAX:
            item["errors"].append("BAD_PIN_CONFIG")
        if _signal_reserved(sig):
            # Pin rezerwowy ma istnieć w ABC, ale nie jest aktywnie wykonywany.
            item["warnings"].append("RESERVED_PIN_NOT_ACTIVE_TESTED")
            item["ok"] = not item["errors"]
            return item
        if strict_pin_function and expected_caps and not cap_values:
            item["warnings"].append("PIN_CAP_ENUM_UNAVAILABLE")
        if strict_pin_function and cap_values and actual_cap is not None and actual_cap not in set(cap_values.values()):
            hf = str(sig.hardware_function or "").upper()
            if hf in {HW_GPIO, HW_ANALOG} and not bool(sig.is_shared_pin):
                item["errors"].append("BAD_PIN_CONFIG")
            else:
                item["warnings"].append("PIN_FUNCTION_DIFFERS_FROM_EXPECTED_SPECIAL_OR_SHARED")
        item["ok"] = not item["errors"]
        return item

    def required_special_functions(self, board: str) -> List[str]:
        board = str(board or "").upper()
        board_signals = [s for s in self.signals.values() if str(s.plytka or "").upper() == board]
        hfs = {str(s.hardware_function or "").upper() for s in board_signals}
        out: List[str] = []
        for hf, name in (
            (HW_LCD, "LCD"),
            (HW_MATRIX_LED, "MATRIX_LED"),
            (HW_KEYBOARD, "KEYBOARD"),
            (HW_I2C, "I2C"),
            (HW_POEXTBUS, "POEXTBUS"),
            (HW_PULSE, "PULSE_ENGINE"),
            (HW_PWM, "PWM"),
        ):
            if hf in hfs:
                out.append(name)
        return out


__all__ = [
    "TARZAN_POKEYS_BOARD_ARCHITECTURE",
    "TARZAN_POKEYS_BOARD_ROLES",
    "TarzanPokABC",
    "expected_role",
    "expected_pin_cap_names",
]
