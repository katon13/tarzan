"""
tarzanMiniPcSandbox.py

TARZAN Mini PC Hardware Sandbox.

Rola:
- prosty, bezpieczny sandbox do testów hardware runtime na tarzanMiniPC,
- źródłem prawdy jest core/tarzanZmienneSygnalowe.py,
- nie ma ręcznej mapy pinów,
- domyślnie działa READ ONLY,
- v2: rozdziela w komunikatach seriale oczekiwane z mapy od wykrytych przez USB,
- v2: odczyt analogowy pokazuje tylko dla sygnałów typu ANALOG z mapy TARZANA,
- wyjścia są możliwe wyłącznie w trybie ręcznym z potwierdzeniem,
- nie generuje ruchu osi, nie uruchamia Pulse Engine Move, nie wykonuje homingu.

Przykłady:
    python -m hardware.tarzanMiniPcSandbox list --board PLAY
    python -m hardware.tarzanMiniPcSandbox scan
    python -m hardware.tarzanMiniPcSandbox read --board PLAY
    python -m hardware.tarzanMiniPcSandbox monitor --board REC --signals rec_p45_sw_f1,rec_p47_sw_f2
    python -m hardware.tarzanMiniPcSandbox report --board PLAY
    python -m hardware.tarzanMiniPcSandbox lcd-test --board PLAY --line1 "TARZAN PLAY" --line2 "LCD OK" --confirm YES_TARZAN_LCD_TEST
    python -m hardware.tarzanMiniPcSandbox lcd-scroll --board PLAY --text "TARZAN LCD SCROLL TEST" --confirm YES_TARZAN_LCD_SCROLL
    python -m hardware.tarzanMiniPcSandbox matrix-test --board REC --text "TARZAN" --confirm YES_TARZAN_MATRIX_TEST

UWAGA:
- Na Windows może działać z hardware/pokeys/PoKeyslib.dll.
- Na Debianie potrzebna jest biblioteka libPoKeys.so.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ======================================================================
# ŚCIEŻKI / IMPORTY ZGODNE Z REPO
# ======================================================================

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "hardware" / "pokeys") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "hardware" / "pokeys"))

try:
    from core.tarzanZmienneSygnalowe import (  # type: ignore
        POKEYS57U_PLAY_DEVICE_SERIAL,
        POKEYS57U_REC_DEVICE_SERIAL,
        SYGNALY_PLAY,
        SYGNALY_REC,
        SYGNALY_CNC,
        WSZYSTKIE_SYGNALY,
        TarzanSygnal,
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
        LOGIKA_ZABRONIONY,
        LOGIKA_TYLKO_ODCZYT,
        LOGIKA_DOZWOLONY,
    )
except Exception as exc:  # pragma: no cover - błąd środowiska
    raise SystemExit(
        "Nie mogę zaimportować core/tarzanZmienneSygnalowe.py. "
        "Uruchom z katalogu głównego repo TARZAN albo sprawdź strukturę projektu.\n"
        f"Szczegóły: {exc}"
    )


# PoKeys importujemy leniwie, dopiero przy komendach wymagających hardware.
def _import_pokeys():
    try:
        from hardware.pokeys.PoKeys import PoKeysDevice, ePK_PinCap  # type: ignore
        return PoKeysDevice, ePK_PinCap
    except Exception:
        try:
            from PoKeys import PoKeysDevice, ePK_PinCap  # type: ignore
            return PoKeysDevice, ePK_PinCap
        except Exception as exc:
            raise RuntimeError(
                "Nie mogę zaimportować biblioteki Python PoKeys. "
                "Sprawdź, czy hardware/pokeys/PoKeys.py istnieje."
            ) from exc


# ======================================================================
# MODELE
# ======================================================================

READ_ONLY = "READ_ONLY"
SAFE_OUTPUT_MANUAL = "SAFE_OUTPUT_MANUAL"
DISPLAY_TEST = "DISPLAY_TEST"
BUS_TEST = "BUS_TEST"
FORBIDDEN_MOTION = "FORBIDDEN_MOTION"
SYSTEM_SKIP = "SYSTEM_SKIP"


@dataclass(frozen=True)
class SandboxSignalRow:
    signal: TarzanSygnal
    test_class: str
    allowed_to_write: bool
    reason: str


@dataclass
class ReadValue:
    board: str
    pin: Optional[int]
    name: str
    canonical: str
    signal_type: str
    direction: str
    group: str
    hardware_function: str
    test_class: str
    digital_value: Optional[int] = None
    analog_raw: Optional[int] = None
    analog_v: Optional[float] = None
    pin_function: Optional[int] = None
    counter_value: Optional[int] = None
    note: str = ""


# ======================================================================
# MAPA Z TARZANA
# ======================================================================

def _signals_for_board(board: str) -> Dict[str, TarzanSygnal]:
    board_u = board.upper()
    if board_u == "PLAY":
        return SYGNALY_PLAY
    if board_u == "REC":
        return SYGNALY_REC
    if board_u == "CNC":
        return SYGNALY_CNC
    if board_u == "ALL":
        return WSZYSTKIE_SYGNALY
    raise ValueError(f"Nieznana płytka: {board}")


def _serial_for_board(board: str) -> int:
    board_u = board.upper()
    if board_u == "PLAY":
        return int(POKEYS57U_PLAY_DEVICE_SERIAL)
    if board_u == "REC":
        return int(POKEYS57U_REC_DEVICE_SERIAL)
    raise ValueError(f"Dla płytki {board} nie ma bezpośredniego serialu PoKeys")


def _classify_signal(signal: TarzanSygnal) -> SandboxSignalRow:
    hw = (signal.hardware_function or "").upper()
    typ = (signal.typ or "").upper()
    kierunek = (signal.kierunek or "").upper()
    grupa = (signal.grupa or "").upper()
    name = signal.nazwa

    if typ == "RESERVED" or kierunek == "RESERVED" or hw in {HW_RESERVED, HW_SYSTEM}:
        return SandboxSignalRow(signal, SYSTEM_SKIP, False, "pin/system/rezerwa - nie testować jako zwykły I/O")

    if name.endswith("reset_do_not_use") or "RESET" in name.upper():
        return SandboxSignalRow(signal, SYSTEM_SKIP, False, "pin reset/systemowy - nie testować")

    if hw == HW_PULSE or grupa in {"STEP_DIR", "STEP_CTR", "STEP_ENABLE", "CNC_CAMERA", "CNC_ARM", "CNC_CART"}:
        return SandboxSignalRow(signal, FORBIDDEN_MOTION, False, "warstwa STEP/DIR/ENABLE/Pulse - na tym etapie bez ruchu")

    if hw in {HW_LCD, HW_MATRIX_LED} or grupa == "UI" and typ == "F":
        return SandboxSignalRow(signal, DISPLAY_TEST, False, "wyświetlacz/klawiatura jako urządzenie, nie goły pin")

    if hw in {HW_I2C, HW_POEXTBUS, HW_KEYBOARD}:
        return SandboxSignalRow(signal, BUS_TEST, False, "magistrala/peryferium - osobny tryb testu")

    if typ == "ANALOG" or kierunek == "IN" or signal.logika_trybow == LOGIKA_TYLKO_ODCZYT:
        return SandboxSignalRow(signal, READ_ONLY, False, "odczyt bezpieczny")

    if kierunek == "OUT" and typ == "LH" and signal.logika_trybow != LOGIKA_ZABRONIONY:
        return SandboxSignalRow(signal, SAFE_OUTPUT_MANUAL, True, "wyjście tylko z ręcznym potwierdzeniem")

    return SandboxSignalRow(signal, READ_ONLY, False, "domyślnie tylko odczyt")


def _iter_rows(board: str) -> List[SandboxSignalRow]:
    rows = [_classify_signal(sig) for sig in _signals_for_board(board).values()]
    rows.sort(key=lambda r: (r.signal.plytka, 999 if r.signal.pin is None else r.signal.pin, r.signal.nazwa))
    return rows


def _filter_rows(
    rows: Iterable[SandboxSignalRow],
    *,
    pins: Optional[Sequence[int]] = None,
    signals: Optional[Sequence[str]] = None,
    include_skipped: bool = True,
) -> List[SandboxSignalRow]:
    pin_set = set(pins or [])
    sig_set = {s.strip() for s in (signals or []) if s.strip()}
    result: List[SandboxSignalRow] = []
    for row in rows:
        if pins is not None and row.signal.pin not in pin_set:
            continue
        if signals is not None and row.signal.nazwa not in sig_set and row.signal.kanoniczna_nazwa not in sig_set:
            continue
        if not include_skipped and row.test_class in {SYSTEM_SKIP, FORBIDDEN_MOTION}:
            continue
        result.append(row)
    return result


# ======================================================================
# POMOCNICZE
# ======================================================================

def _parse_pins(text: Optional[str]) -> Optional[List[int]]:
    if not text:
        return None
    pins: List[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            pins.extend(range(int(a), int(b) + 1))
        else:
            pins.append(int(part))
    return sorted(set(pins))


def _parse_signals(text: Optional[str]) -> Optional[List[str]]:
    if not text:
        return None
    return [x.strip() for x in text.split(",") if x.strip()]


def _find_pokeys_library(explicit_path: Optional[str]) -> Optional[str]:
    candidates: List[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    env_path = os.environ.get("TARZAN_POKEYS_LIB")
    if env_path:
        candidates.append(Path(env_path))

    # Automatycznie nie wybieramy DLL na Linuxie, bo skończy się błędem invalid ELF header.
    # DLL można nadal wskazać jawnie przez --lib-path albo TARZAN_POKEYS_LIB na Windows.
    if sys.platform.startswith("win"):
        candidates.extend(
            [
                REPO_ROOT / "hardware" / "pokeys" / "PoKeyslib.dll",
                Path("./PoKeyslib.dll"),
            ]
        )

    candidates.extend(
        [
            REPO_ROOT / "hardware" / "pokeys" / "libPoKeys.so",
            REPO_ROOT / "hardware" / "pokeys" / "libpokeys.so",
            Path("/usr/local/lib/libPoKeys.so"),
            Path("/usr/lib/libPoKeys.so"),
            Path("/usr/lib/x86_64-linux-gnu/libPoKeys.so"),
            Path("./libPoKeys.so"),
        ]
    )
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def _print_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))


def _ensure_reports_dir() -> Path:
    path = REPO_ROOT / "data" / "hardware" / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ======================================================================
# SESJA POKEYS READ-ONLY
# ======================================================================

class PoKeysReadOnlySession:
    def __init__(self, board: str, lib_path: str) -> None:
        self.board = board.upper()
        self.lib_path = lib_path
        self.serial = _serial_for_board(self.board)
        PoKeysDevice, _ = _import_pokeys()
        self.device = PoKeysDevice(self.lib_path)
        self.connected = False

    def __enter__(self) -> "PoKeysReadOnlySession":
        ok = self.device.PK_ConnectToDeviceWSerial(self.serial, 1, True)
        if not ok:
            raise RuntimeError(f"Nie udało się połączyć z {self.board} serial={self.serial}")
        actual_serial = int(self.device.device.contents.DeviceData.SerialNumber)
        if actual_serial != self.serial:
            raise RuntimeError(f"Zły serial dla {self.board}: oczekiwano {self.serial}, odczytano {actual_serial}")
        self.refresh()
        self.connected = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self.device.Disconnect()
        finally:
            self.connected = False

    def refresh(self) -> None:
        self.device.PK_PinConfigurationGet()
        self.device.PK_DigitalIOGet()
        self.device.PK_AnalogIOGet()
        try:
            self.device.PK_DigitalCounterGet()
        except Exception:
            pass

    def identity_text(self) -> str:
        dev = self.device.device.contents.DeviceData
        name = dev.DeviceName.decode("ascii", errors="ignore").strip("\x00")
        typ = dev.DeviceTypeName.decode("ascii", errors="ignore").strip("\x00")
        return (
            f"{self.board} serial={int(dev.SerialNumber)} "
            f"name='{name}' type='{typ}' fw_major={int(dev.FirmwareVersionMajor)} fw_minor={int(dev.FirmwareVersionMinor)}"
        )

    def read_signal(self, row: SandboxSignalRow) -> ReadValue:
        sig = row.signal
        result = ReadValue(
            board=self.board,
            pin=sig.pin,
            name=sig.nazwa,
            canonical=sig.kanoniczna_nazwa,
            signal_type=sig.typ,
            direction=sig.kierunek,
            group=sig.grupa,
            hardware_function=sig.hardware_function,
            test_class=row.test_class,
            note=row.reason,
        )
        if sig.pin is None:
            return result

        pin_index = sig.pin - 1
        try:
            pin_data = self.device.device.contents.Pins[pin_index]
            result.pin_function = int(pin_data.PinFunction)
            result.digital_value = int(pin_data.DigitalValueGet)
            # Analog pokazujemy tylko wtedy, gdy typ sygnału TARZANA jest ANALOG.
            # Nie wystarczy hardware_function == HW_ANALOG, bo część pinów analog-capable
            # może być świadomie użyta jako LH/IN w mapie TARZANA.
            if (sig.typ or "").upper() == "ANALOG":
                raw = int(pin_data.AnalogValue)
                result.analog_raw = raw
                result.analog_v = round(3.3 * raw / 4096.0, 4)
            try:
                if int(pin_data.DigitalCounterAvailable):
                    result.counter_value = int(pin_data.DigitalCounterValue)
            except Exception:
                pass
        except Exception as exc:
            result.note = f"BŁĄD ODCZYTU: {exc}"
        return result

    def safe_set_output(self, row: SandboxSignalRow, value: int) -> None:
        sig = row.signal
        if not row.allowed_to_write:
            raise RuntimeError(f"Sygnał {sig.nazwa} nie jest dopuszczony do ręcznego testu wyjścia: {row.reason}")
        if sig.pin is None:
            raise RuntimeError(f"Sygnał {sig.nazwa} nie ma pinu fizycznego")
        self.device.PK_DigitalIOSetSingle(sig.pin - 1, 1 if value else 0)
        self.device.PK_DigitalIOGet()


# ======================================================================
# KOMENDY
# ======================================================================

def cmd_list(args: argparse.Namespace) -> int:
    rows = _filter_rows(
        _iter_rows(args.board),
        pins=_parse_pins(args.pins),
        signals=_parse_signals(args.signals),
        include_skipped=args.include_skipped,
    )
    table = []
    for row in rows:
        s = row.signal
        table.append(
            [
                s.plytka,
                "" if s.pin is None else s.pin,
                s.nazwa,
                s.kanoniczna_nazwa,
                s.typ,
                s.kierunek,
                s.grupa,
                s.hardware_function,
                row.test_class,
                "TAK" if row.allowed_to_write else "NIE",
            ]
        )
    _print_table(
        ["PLYTKA", "PIN", "SYGNAŁ", "KANONICZNA", "TYP", "KIER.", "GRUPA", "HW", "TEST", "WRITE"],
        table,
    )
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    lib_path = _find_pokeys_library(args.lib_path)
    print("TARZAN Mini PC Sandbox — SCAN")
    print(f"repo={REPO_ROOT}")
    print("OCZEKIWANE Z MAPY TARZANA:")
    print(f"  PLAY serial={POKEYS57U_PLAY_DEVICE_SERIAL}")
    print(f"  REC  serial={POKEYS57U_REC_DEVICE_SERIAL}")
    print("WYKRYTE NA USB / PoKeysLib:")

    if not lib_path:
        print("[!] Nie znaleziono biblioteki PoKeysLib. Na Debianie dołóż libPoKeys.so.")
    else:
        print(f"PoKeysLib={lib_path}")
        try:
            PoKeysDevice, _ = _import_pokeys()
            dev = PoKeysDevice(lib_path)
            dev.ShowAllDevices(args.ethernet_timeout_ms)
            dev.Disconnect()
        except Exception as exc:
            print(f"[!] Błąd enumeracji PoKeys: {exc}")

    print("\nPorty serial w systemie:")
    for pattern in ["/dev/serial/by-id/*", "/dev/ttyUSB*", "/dev/ttyACM*"]:
        for item in sorted(Path("/").glob(pattern.lstrip("/"))):
            try:
                print(f"  /{item} -> {item.resolve()}")
            except Exception:
                print(f"  /{item}")
    return 0


def _read_values(args: argparse.Namespace) -> Tuple[str, List[ReadValue]]:
    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    rows = _filter_rows(
        _iter_rows(args.board),
        pins=_parse_pins(args.pins),
        signals=_parse_signals(args.signals),
        include_skipped=args.include_skipped,
    )
    rows = [row for row in rows if row.signal.plytka.upper() == args.board.upper()]
    values: List[ReadValue] = []
    with PoKeysReadOnlySession(args.board, lib_path) as session:
        identity = session.identity_text()
        for row in rows:
            values.append(session.read_signal(row))
    return identity, values


def _values_to_table(values: Sequence[ReadValue]) -> List[List[object]]:
    table = []
    for v in values:
        val = ""
        if v.analog_raw is not None:
            val = f"raw={v.analog_raw} / {v.analog_v}V"
        elif v.digital_value is not None:
            val = v.digital_value
        table.append(
            [
                v.board,
                "" if v.pin is None else v.pin,
                v.name,
                v.canonical,
                v.signal_type,
                v.direction,
                v.group,
                v.test_class,
                val,
                "" if v.pin_function is None else v.pin_function,
                "" if v.counter_value is None else v.counter_value,
                v.note,
            ]
        )
    return table


def cmd_read(args: argparse.Namespace) -> int:
    identity, values = _read_values(args)
    print(identity)
    _print_table(
        ["PLYTKA", "PIN", "SYGNAŁ", "KANONICZNA", "TYP", "KIER.", "GRUPA", "TEST", "WARTOŚĆ", "PIN_FUNC", "COUNTER", "UWAGA"],
        _values_to_table(values),
    )
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")
    rows = _filter_rows(
        _iter_rows(args.board),
        pins=_parse_pins(args.pins),
        signals=_parse_signals(args.signals),
        include_skipped=args.include_skipped,
    )
    rows = [row for row in rows if row.signal.plytka.upper() == args.board.upper()]
    if not rows:
        raise RuntimeError("Brak sygnałów do monitorowania dla podanych filtrów.")

    interval = max(0.05, float(args.interval))
    print(f"MONITOR {args.board} co {interval}s. Ctrl+C kończy.")
    if args.changes_only:
        print("Tryb: changes-only — wypisuję tylko po zmianie wartości, czyli po naciśnięciu/zwolnieniu przycisku.")
    if args.initial:
        print("Tryb: initial — pierwszy stan zostanie wypisany od razu.")

    previous: Dict[str, str] = {}

    with PoKeysReadOnlySession(args.board, lib_path) as session:
        print(session.identity_text())
        while True:
            session.refresh()
            stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            current: Dict[str, str] = {}
            for row in rows:
                value = session.read_signal(row)
                if value.analog_raw is not None:
                    current[row.signal.nazwa] = f"A{value.analog_raw}/{value.analog_v}V"
                else:
                    current[row.signal.nazwa] = f"D{value.digital_value}"

            if args.changes_only:
                changed = []
                for name, val in current.items():
                    old = previous.get(name)
                    if old is None:
                        if args.initial:
                            changed.append(f"{name}={val}")
                    elif old != val:
                        changed.append(f"{name}: {old} -> {val}")
                if changed:
                    print(f"{stamp} | " + " | ".join(changed), flush=True)
            else:
                parts = [f"{name}={val}" for name, val in current.items()]
                print(f"{stamp} | " + " | ".join(parts), flush=True)

            previous = current
            time.sleep(interval)


def cmd_output(args: argparse.Namespace) -> int:
    if not args.allow_write or args.confirm != "YES_TARZAN_OUTPUT_TEST":
        raise RuntimeError(
            "Brak potwierdzenia. Użyj: --allow-write --confirm YES_TARZAN_OUTPUT_TEST"
        )
    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    rows = _filter_rows(_iter_rows(args.board), signals=[args.signal], include_skipped=True)
    if not rows:
        raise RuntimeError(f"Nie znaleziono sygnału {args.signal} na {args.board}")
    row = rows[0]

    print(f"RĘCZNY TEST WYJŚCIA: {args.board} {row.signal.nazwa} pin={row.signal.pin} value={args.value}")
    print(f"Klasa={row.test_class}, powód={row.reason}")
    with PoKeysReadOnlySession(args.board, lib_path) as session:
        session.safe_set_output(row, args.value)
        value = session.read_signal(row)
        print(f"Po ustawieniu: digital={value.digital_value}, pin_function={value.pin_function}")
    return 0



def _lcd_text(value: str, width: int = 20) -> str:
    # HD44780 / PoKeys buffer accepts max 20 characters per row.
    # Polish characters are intentionally stripped/replaced here because many LCD 1602
    # modules do not have matching glyphs in ROM.
    table = str.maketrans({
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
        "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N", "Ó": "O", "Ś": "S", "Ź": "Z", "Ż": "Z",
    })
    return value.translate(table)[:width]


def cmd_lcd_test(args: argparse.Namespace) -> int:
    if args.confirm != "YES_TARZAN_LCD_TEST":
        raise RuntimeError("Brak potwierdzenia. Użyj: --confirm YES_TARZAN_LCD_TEST")

    board = args.board.upper()
    if board not in {"PLAY", "REC"}:
        raise RuntimeError("LCD test obsługuje tylko PLAY albo REC")

    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    # LCD w mapie TARZANA jest na pinach 28-34 i ma być testowany jako urządzenie,
    # nie przez ręczne ustawianie gołych pinów.
    lcd_rows = _filter_rows(_iter_rows(board), pins=list(range(28, 35)), include_skipped=True)
    if not lcd_rows or any((row.signal.hardware_function or "").upper() != HW_LCD for row in lcd_rows):
        raise RuntimeError(f"Mapa TARZANA nie potwierdza pełnego LCD na {board} P28-P34")

    line1 = _lcd_text(args.line1)
    line2 = _lcd_text(args.line2)

    print(f"LCD TEST {board}")
    print("Piny z mapy TARZANA: P28-P34")
    print(f"Line1: {line1!r}")
    print(f"Line2: {line2!r}")

    with PoKeysReadOnlySession(board, lib_path) as session:
        print(session.identity_text())

        lcd = session.device.device.contents.LCD

        # PoKeys LCD:
        # Configuration: 0 disabled, 1 primary pins, 2 secondary pins.
        # TARZAN ma LCD na P28-P34, czyli układ secondary z dokumentacji PoKeys.
        lcd.Configuration = 2
        lcd.Rows = int(args.rows)
        lcd.Columns = int(args.columns)

        rc = session.device.PK_LCDConfigurationSet()
        if rc != 0:
            raise RuntimeError(f"PK_LCDConfigurationSet zwróciło {rc}")

        rc = session.device.PK_LCDChangeMode(0)  # PK_LCD_MODE_DIRECT
        if rc != 0:
            raise RuntimeError(f"PK_LCDChangeMode(DIRECT) zwróciło {rc}")

        rc = session.device.PK_LCDInit()
        if rc != 0:
            raise RuntimeError(f"PK_LCDInit zwróciło {rc}")

        time.sleep(0.05)

        rc = session.device.PK_LCDClear()
        if rc != 0:
            raise RuntimeError(f"PK_LCDClear zwróciło {rc}")

        time.sleep(0.05)

        rc = session.device.PK_LCDMoveCursor(1, 1)
        if rc != 0:
            raise RuntimeError(f"PK_LCDMoveCursor(1,1) zwróciło {rc}")
        rc = session.device.PK_LCDPrint(line1)
        if rc != 0:
            raise RuntimeError(f"PK_LCDPrint(line1) zwróciło {rc}")

        rc = session.device.PK_LCDMoveCursor(2, 1)
        if rc != 0:
            raise RuntimeError(f"PK_LCDMoveCursor(2,1) zwróciło {rc}")
        rc = session.device.PK_LCDPrint(line2)
        if rc != 0:
            raise RuntimeError(f"PK_LCDPrint(line2) zwróciło {rc}")

    print("OK: komenda LCD wysłana przez funkcje LCD PoKeys.")
    return 0



def cmd_lcd_scroll(args: argparse.Namespace) -> int:
    if args.confirm != "YES_TARZAN_LCD_SCROLL":
        raise RuntimeError("Brak potwierdzenia. Użyj: --confirm YES_TARZAN_LCD_SCROLL")

    board = args.board.upper()
    if board not in {"PLAY", "REC"}:
        raise RuntimeError("LCD scroll obsługuje tylko PLAY albo REC")

    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    lcd_rows = _filter_rows(_iter_rows(board), pins=list(range(28, 35)), include_skipped=True)
    if not lcd_rows or any((row.signal.hardware_function or "").upper() != HW_LCD for row in lcd_rows):
        raise RuntimeError(f"Mapa TARZANA nie potwierdza pełnego LCD na {board} P28-P34")

    columns = max(8, int(args.columns))
    delay = max(0.03, float(args.delay))
    repeat = max(1, int(args.repeat))

    base = _lcd_text(args.text, width=120)
    if not base:
        base = "TARZAN LCD SCROLL TEST"

    # Puste pola z obu stron dają łagodne wejście i zejście tekstu.
    scroll_source = (" " * columns) + base + (" " * columns)

    print(f"LCD SCROLL {board}")
    print("Piny z mapy TARZANA: P28-P34")
    print(f"Text: {base!r}")
    print(f"Columns: {columns}, delay={delay}s, repeat={repeat}")

    with PoKeysReadOnlySession(board, lib_path) as session:
        print(session.identity_text())

        lcd = session.device.device.contents.LCD
        lcd.Configuration = 2
        lcd.Rows = int(args.rows)
        lcd.Columns = columns

        rc = session.device.PK_LCDConfigurationSet()
        if rc != 0:
            raise RuntimeError(f"PK_LCDConfigurationSet zwróciło {rc}")

        rc = session.device.PK_LCDChangeMode(0)  # PK_LCD_MODE_DIRECT
        if rc != 0:
            raise RuntimeError(f"PK_LCDChangeMode(DIRECT) zwróciło {rc}")

        rc = session.device.PK_LCDInit()
        if rc != 0:
            raise RuntimeError(f"PK_LCDInit zwróciło {rc}")

        time.sleep(0.05)
        session.device.PK_LCDClear()
        time.sleep(0.05)

        for _ in range(repeat):
            for pos in range(0, len(scroll_source) - columns + 1):
                window = scroll_source[pos:pos + columns]
                rc = session.device.PK_LCDMoveCursor(1, 1)
                if rc != 0:
                    raise RuntimeError(f"PK_LCDMoveCursor(1,1) zwróciło {rc}")
                rc = session.device.PK_LCDPrint(window)
                if rc != 0:
                    raise RuntimeError(f"PK_LCDPrint(scroll) zwróciło {rc}")

                if args.line2:
                    rc = session.device.PK_LCDMoveCursor(2, 1)
                    if rc != 0:
                        raise RuntimeError(f"PK_LCDMoveCursor(2,1) zwróciło {rc}")
                    rc = session.device.PK_LCDPrint(_lcd_text(args.line2, width=columns).ljust(columns))
                    if rc != 0:
                        raise RuntimeError(f"PK_LCDPrint(line2) zwróciło {rc}")

                time.sleep(delay)

        if args.clear_end:
            session.device.PK_LCDClear()

    print("OK: przewijanie tekstu LCD wysłane przez funkcje LCD PoKeys.")
    return 0



_MATRIX_FONT_5X7 = {
    "A": [0x1E, 0x05, 0x05, 0x1E, 0x00],
    "C": [0x0E, 0x11, 0x11, 0x11, 0x00],
    "E": [0x1F, 0x15, 0x15, 0x11, 0x00],
    "I": [0x11, 0x1F, 0x11, 0x00, 0x00],
    "K": [0x1F, 0x04, 0x0A, 0x11, 0x00],
    "L": [0x1F, 0x10, 0x10, 0x10, 0x00],
    "N": [0x1F, 0x02, 0x04, 0x1F, 0x00],
    "O": [0x0E, 0x11, 0x11, 0x0E, 0x00],
    "P": [0x1F, 0x05, 0x05, 0x02, 0x00],
    "R": [0x1F, 0x05, 0x0D, 0x12, 0x00],
    "S": [0x12, 0x15, 0x15, 0x09, 0x00],
    "T": [0x01, 0x01, 0x1F, 0x01, 0x01],
    "Y": [0x03, 0x04, 0x18, 0x04, 0x03],
    "Z": [0x19, 0x15, 0x13, 0x00, 0x00],
    "0": [0x0E, 0x11, 0x11, 0x0E, 0x00],
    "1": [0x12, 0x1F, 0x10, 0x00, 0x00],
    "2": [0x19, 0x15, 0x15, 0x12, 0x00],
    "3": [0x11, 0x15, 0x15, 0x0A, 0x00],
    "4": [0x07, 0x04, 0x1F, 0x04, 0x00],
    "5": [0x17, 0x15, 0x15, 0x09, 0x00],
    "6": [0x0E, 0x15, 0x15, 0x08, 0x00],
    "7": [0x01, 0x01, 0x1D, 0x03, 0x00],
    "8": [0x0A, 0x15, 0x15, 0x0A, 0x00],
    "9": [0x02, 0x15, 0x15, 0x0E, 0x00],
    " ": [0x00, 0x00, 0x00],
}


def _matrix_rows_from_columns(columns: Sequence[int], invert: bool = False) -> List[int]:
    rows = []
    for y in range(8):
        value = 0
        for x in range(8):
            if x < len(columns):
                bit = (int(columns[x]) >> y) & 0x01
                if bit:
                    value |= (1 << x)
        if invert:
            value ^= 0xFF
        rows.append(value & 0xFF)
    return rows


def _matrix_text_columns(text_value: str) -> List[int]:
    safe = _lcd_text(text_value.upper(), width=64)
    columns: List[int] = []
    for ch in safe:
        columns.extend(_MATRIX_FONT_5X7.get(ch, _MATRIX_FONT_5X7[" "]))
        columns.append(0x00)
    if not columns:
        columns = [0x00] * 8
    return columns


def _matrix_write_frame(session: PoKeysReadOnlySession, rows: Sequence[int], rows_count: int = 8, cols_count: int = 8) -> None:
    matrix_ptr = session.device.device.contents.MatrixLED
    if not matrix_ptr:
        raise RuntimeError("PoKeysLib nie udostępnił struktury MatrixLED")

    matrix = matrix_ptr[0]
    matrix.displayEnabled = 1
    matrix.rows = rows_count
    matrix.columns = cols_count
    matrix.RefreshFlag = 1

    for i in range(8):
        matrix.data[i] = int(rows[i]) & 0xFF if i < len(rows) else 0

    rc = session.device.PK_MatrixLEDConfigurationSet()
    if rc != 0:
        raise RuntimeError(f"PK_MatrixLEDConfigurationSet zwróciło {rc}")

    rc = session.device.PK_MatrixLEDUpdate()
    if rc != 0:
        raise RuntimeError(f"PK_MatrixLEDUpdate zwróciło {rc}")


def cmd_matrix_test(args: argparse.Namespace) -> int:
    if args.confirm != "YES_TARZAN_MATRIX_TEST":
        raise RuntimeError("Brak potwierdzenia. Użyj: --confirm YES_TARZAN_MATRIX_TEST")

    board = args.board.upper()
    if board != "REC":
        raise RuntimeError("Matrix LED w aktualnej mapie TARZANA jest tylko na REC / RECK")

    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    matrix_rows = _filter_rows(_iter_rows(board), pins=[9, 10, 11], include_skipped=True)
    if len(matrix_rows) != 3 or any((row.signal.hardware_function or "").upper() != HW_MATRIX_LED for row in matrix_rows):
        raise RuntimeError("Mapa TARZANA nie potwierdza Matrix LED na REC P09-P11")

    text_value = args.text or "TARZAN"
    delay = max(0.05, float(args.delay))
    repeat = max(1, int(args.repeat))
    mode = args.mode.lower()

    print("MATRIX LED TEST REC / RECK")
    print("Piny z mapy TARZANA: REC P09-P11")
    print(f"Mode: {mode}")
    print(f"Text: {text_value!r}")

    with PoKeysReadOnlySession(board, lib_path) as session:
        print(session.identity_text())

        # Najpierw pobieramy aktualną konfigurację; potem wysyłamy test jako peryferium Matrix LED.
        try:
            session.device.PK_MatrixLEDConfigurationGet()
        except Exception:
            pass

        frames: List[List[int]] = []

        if mode == "blink":
            frames = [[0xFF] * 8, [0x00] * 8] * repeat
        elif mode == "checker":
            frames = [[0xAA, 0x55] * 4, [0x55, 0xAA] * 4] * repeat
        elif mode == "box":
            frames = [[0xFF, 0x81, 0x81, 0x81, 0x81, 0x81, 0x81, 0xFF]] * repeat
        else:
            columns = ([0x00] * 8) + _matrix_text_columns(text_value) + ([0x00] * 8)
            for _ in range(repeat):
                for pos in range(0, len(columns) - 7):
                    window = columns[pos:pos + 8]
                    frames.append(_matrix_rows_from_columns(window, invert=args.invert))

        for rows in frames:
            if mode in {"blink", "checker", "box"}:
                out_rows = [(r ^ 0xFF) & 0xFF for r in rows] if args.invert else rows
            else:
                out_rows = rows
            _matrix_write_frame(session, out_rows, rows_count=8, cols_count=8)
            time.sleep(delay)

        if args.clear_end:
            _matrix_write_frame(session, [0x00] * 8, rows_count=8, cols_count=8)

    print("OK: Matrix LED wysłany przez funkcje MatrixLED PoKeys.")
    return 0



_BUTTON_TESTS_REC = [
    ("F1", 45, "rec_p45_sw_f1"),
    ("F2", 47, "rec_p47_sw_f2"),
    ("F3", 49, "rec_p49_sw_f3"),
    ("F4", 51, "rec_p51_sw_f4"),
]


def _find_row_by_pin(rows: Sequence[SandboxSignalRow], pin: int) -> Optional[SandboxSignalRow]:
    for row in rows:
        if row.signal.pin == pin:
            return row
    return None


def cmd_buttons_test(args: argparse.Namespace) -> int:
    board = args.board.upper()
    if board != "REC":
        raise RuntimeError("Test F1-F4 jest w aktualnej mapie TARZANA tylko na REC / RECK")

    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    selected = [x.strip().upper() for x in (args.buttons or "F1,F2,F3,F4").split(",") if x.strip()]
    wanted = [item for item in _BUTTON_TESTS_REC if item[0] in selected]
    if not wanted:
        raise RuntimeError("Brak przycisków do testu. Użyj np. --buttons F1,F2,F3,F4")

    rows_all = list(_iter_rows(board))
    print("TARZAN REC / RECK — test przycisków F1-F4")
    print("Tryb: skrypt czeka na naciśnięcie i sam potwierdza: 'nacisnąłeś F1 — działa'.")
    print("Ctrl+C kończy test.")
    print("")

    with PoKeysReadOnlySession(board, lib_path) as session:
        print(session.identity_text())
        print("")

        for label, pin, expected_signal in wanted:
            row = _find_row_by_pin(rows_all, pin)
            if row is None:
                print(f"[!] {label}: brak pinu P{pin} w mapie REC — pomijam.")
                continue

            print(f"Naciśnij {label}  ({row.signal.nazwa}, REC P{pin}) ...", flush=True)

            session.refresh()
            base_value = session.read_signal(row).digital_value
            if base_value is None:
                print(f"[!] {label}: brak odczytu digital — pomijam.")
                continue

            pressed_value = None
            started = time.time()

            while True:
                session.refresh()
                value = session.read_signal(row).digital_value
                if value != base_value:
                    pressed_value = value
                    print(f"[x] Nacisnąłeś {label} — działa  ({base_value} -> {pressed_value})", flush=True)
                    break

                if args.timeout > 0 and (time.time() - started) > args.timeout:
                    print(f"[!] {label}: timeout — nie wykryto naciśnięcia w {args.timeout}s", flush=True)
                    break

                time.sleep(max(0.03, float(args.interval)))

            if pressed_value is None:
                continue

            if args.wait_release:
                print(f"Puść {label} ...", flush=True)
                release_started = time.time()
                while True:
                    session.refresh()
                    value = session.read_signal(row).digital_value
                    if value == base_value:
                        print(f"[x] {label} puszczony — OK", flush=True)
                        break

                    if args.timeout > 0 and (time.time() - release_started) > args.timeout:
                        print(f"[!] {label}: nie wykryto puszczenia w {args.timeout}s", flush=True)
                        break

                    time.sleep(max(0.03, float(args.interval)))

            print("")

    print("Koniec testu przycisków.")
    return 0



_LED_TESTS_REC = {
    "F1": ("rec_p46_led_f1", "ui_f1_led", 46),
    "F2": ("rec_p48_led_f2", "ui_f2_led", 48),
    "F3": ("rec_p50_led_f3", "ui_f3_led", 50),
    "F4": ("rec_p52_led_f4", "ui_f4_led", 52),
}


def _find_led_row(board: str, led: str) -> SandboxSignalRow:
    board = board.upper()
    led = led.upper()
    if board != "REC":
        raise RuntimeError("LED F1-F4 są w aktualnej mapie TARZANA tylko na REC / RECK")
    if led not in _LED_TESTS_REC:
        raise RuntimeError("Nieznany LED. Użyj F1, F2, F3 albo F4.")

    signal_name, canonical_name, pin = _LED_TESTS_REC[led]
    rows = list(_iter_rows(board))
    for row in rows:
        sig = row.signal
        if sig.pin == pin and (sig.nazwa == signal_name or sig.kanoniczna_nazwa == canonical_name):
            return row

    raise RuntimeError(f"Nie znaleziono LED {led} w mapie REC jako {signal_name} / {canonical_name} na P{pin}")


def _set_led_pin_runtime(session: PoKeysReadOnlySession, pin: int, value: int) -> None:
    # LED test jest ręczny i chwilowy. Nie zapisujemy konfiguracji do flash.
    # Dla pinów LED ustawiamy tylko runtime PinFunction=digitalOutput i DigitalValueSet.
    _, ePK_PinCap = _import_pokeys()
    pin_index = pin - 1
    pin_data = session.device.device.contents.Pins[pin_index]

    try:
        pin_data.PinFunction = int(ePK_PinCap.PK_PinCap_digitalOutput)
        pin_data.DigitalValueSet = 1 if value else 0
        rc = session.device.PK_PinConfigurationSet()
        if rc != 0:
            raise RuntimeError(f"PK_PinConfigurationSet zwróciło {rc}")
    except Exception as exc:
        raise RuntimeError(f"Nie udało się ustawić P{pin} jako digital output runtime: {exc}") from exc

    rc = session.device.PK_DigitalIOSetSingle(pin_index, 1 if value else 0)
    if rc != 0:
        raise RuntimeError(f"PK_DigitalIOSetSingle(P{pin}, {value}) zwróciło {rc}")

    session.device.PK_DigitalIOGet()


def cmd_led_test(args: argparse.Namespace) -> int:
    if args.confirm != "YES_TARZAN_LED_TEST":
        raise RuntimeError("Brak potwierdzenia. Użyj: --confirm YES_TARZAN_LED_TEST")

    board = args.board.upper()
    if board != "REC":
        raise RuntimeError("LED F1-F4 są w aktualnej mapie TARZANA tylko na REC / RECK")

    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    leds = [x.strip().upper() for x in (args.led or "F1,F2,F3,F4").split(",") if x.strip()]
    if not leds:
        leds = ["F1", "F2", "F3", "F4"]

    rows = [(led, _find_led_row(board, led)) for led in leds]

    print("TARZAN REC / RECK — test LED F1-F4")
    print("Tryb: ręczny, tylko whitelist ui_f1_led..ui_f4_led.")
    print("Nie uruchamiam Pulse Engine, STEP, DIR ani ruchu osi.")
    print("Nie zapisuję konfiguracji PoKeys do flash.")
    print("")

    on_time = max(0.05, float(args.on_time))
    off_time = max(0.05, float(args.off_time))
    repeat = max(1, int(args.repeat))

    with PoKeysReadOnlySession(board, lib_path) as session:
        print(session.identity_text())
        print("")

        # Zgaś wszystkie znane LED na starcie testu.
        for _, row in rows:
            _set_led_pin_runtime(session, int(row.signal.pin), 0)
        time.sleep(off_time)

        for _ in range(repeat):
            for led, row in rows:
                pin = int(row.signal.pin)
                print(f"[TEST] {led} ON  ({row.signal.nazwa}, REC P{pin})", flush=True)
                _set_led_pin_runtime(session, pin, 1)
                time.sleep(on_time)

                print(f"[TEST] {led} OFF ({row.signal.nazwa}, REC P{pin})", flush=True)
                _set_led_pin_runtime(session, pin, 0)
                time.sleep(off_time)

        if args.leave_off:
            for _, row in rows:
                _set_led_pin_runtime(session, int(row.signal.pin), 0)

    print("OK: test LED zakończony.")
    return 0



_KEYBOARD_TESTS_PLAY = [
    ("KB1", 27, "play_p27_kb1"),
    ("KB2", 26, "play_p26_kb2"),
    ("KB3", 25, "play_p25_kb3"),
    ("KB4", 24, "play_p24_kb4"),
]


def cmd_keyboard_test(args: argparse.Namespace) -> int:
    board = args.board.upper()
    if board != "PLAY":
        raise RuntimeError("Klawiatura KB1-KB4 jest w aktualnej mapie TARZANA tylko na PLAY / PLAYER")

    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    selected = [x.strip().upper() for x in (args.keys or "KB1,KB2,KB3,KB4").split(",") if x.strip()]
    wanted = [item for item in _KEYBOARD_TESTS_PLAY if item[0] in selected]
    if not wanted:
        raise RuntimeError("Brak klawiszy do testu. Użyj np. --keys KB1,KB2,KB3,KB4")

    rows_all = list(_iter_rows(board))
    print("TARZAN PLAY / PLAYER — test klawiatury KB1-KB4")
    print("Tryb: skrypt czeka na naciśnięcie i sam potwierdza: 'nacisnąłeś KB1 — działa'.")
    print("Ctrl+C kończy test.")
    print("")

    with PoKeysReadOnlySession(board, lib_path) as session:
        print(session.identity_text())
        print("")

        for label, pin, expected_signal in wanted:
            row = _find_row_by_pin(rows_all, pin)
            if row is None:
                print(f"[!] {label}: brak pinu P{pin} w mapie PLAY — pomijam.")
                continue

            print(f"Naciśnij {label}  ({row.signal.nazwa}, PLAY P{pin}) ...", flush=True)

            session.refresh()
            base_value = session.read_signal(row).digital_value
            if base_value is None:
                print(f"[!] {label}: brak odczytu digital — pomijam.")
                continue

            pressed_value = None
            started = time.time()

            while True:
                session.refresh()
                value = session.read_signal(row).digital_value
                if value != base_value:
                    pressed_value = value
                    print(f"[x] Nacisnąłeś {label} — działa  ({base_value} -> {pressed_value})", flush=True)
                    break

                if args.timeout > 0 and (time.time() - started) > args.timeout:
                    print(f"[!] {label}: timeout — nie wykryto naciśnięcia w {args.timeout}s", flush=True)
                    break

                time.sleep(max(0.03, float(args.interval)))

            if pressed_value is None:
                continue

            if args.wait_release:
                print(f"Puść {label} ...", flush=True)
                release_started = time.time()
                while True:
                    session.refresh()
                    value = session.read_signal(row).digital_value
                    if value == base_value:
                        print(f"[x] {label} puszczony — OK", flush=True)
                        break

                    if args.timeout > 0 and (time.time() - release_started) > args.timeout:
                        print(f"[!] {label}: nie wykryto puszczenia w {args.timeout}s", flush=True)
                        break

                    time.sleep(max(0.03, float(args.interval)))

            print("")

    print("Koniec testu klawiatury.")
    return 0



_KEYPAD_4X3_SEQUENCE = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]


def _matrix_kb_values(session: PoKeysReadOnlySession) -> List[int]:
    rc = session.device.PK_MatrixKBStatusGet()
    if rc != 0:
        raise RuntimeError(f"PK_MatrixKBStatusGet zwróciło {rc}")
    kb = session.device.device.contents.matrixKB
    return [int(kb.matrixKBvalues[i]) for i in range(128)]


def _matrix_kb_config_text(session: PoKeysReadOnlySession) -> str:
    try:
        rc = session.device.PK_MatrixKBConfigurationGet()
    except Exception as exc:
        return f"[!] PK_MatrixKBConfigurationGet exception: {exc}"
    if rc != 0:
        return f"[!] PK_MatrixKBConfigurationGet zwróciło {rc}"

    kb = session.device.device.contents.matrixKB
    width = int(kb.matrixKBwidth)
    height = int(kb.matrixKBheight)
    enabled = int(kb.matrixKBconfiguration)
    dec = int(kb.matrixKBScanningDecimation)
    rows = [int(kb.matrixKBrowsPins[i]) for i in range(min(16, max(0, height or 4)))]
    cols = [int(kb.matrixKBcolumnsPins[i]) for i in range(min(8, max(0, width or 3)))]
    return (
        f"MatrixKB enabled={enabled} width={width} height={height} decimation={dec} "
        f"rowsPins={rows} columnsPins={cols}"
    )


def _first_matrix_change(base: Sequence[int], current: Sequence[int]) -> Optional[Tuple[int, int, int]]:
    for idx, (a, b) in enumerate(zip(base, current)):
        if int(a) != int(b):
            return idx, int(a), int(b)
    return None


def cmd_keypad_map(args: argparse.Namespace) -> int:
    board = args.board.upper()
    if board != "PLAY":
        raise RuntimeError("Klawiatura 4x3 jest w aktualnej mapie TARZANA na PLAY / PLAYER")

    lib_path = _find_pokeys_library(args.lib_path)
    if not lib_path:
        raise RuntimeError("Nie znaleziono biblioteki PoKeysLib. Ustaw --lib-path albo TARZAN_POKEYS_LIB.")

    sequence = [x.strip() for x in (args.sequence or ",".join(_KEYPAD_4X3_SEQUENCE)).split(",") if x.strip()]
    if not sequence:
        sequence = list(_KEYPAD_4X3_SEQUENCE)

    print("TARZAN PLAY / PLAYER — mapowanie klawiatury matrix 4x3")
    print("To nie jest test KB1-KB4. Ten test prosi o naciśnięcie realnych klawiszy: 1 2 3 ... * 0 #.")
    print("Skrypt czyta PoKeys Matrix Keyboard status i zapamiętuje wykryty indeks/wiersz/kolumnę.")
    print("Ctrl+C kończy test.")
    print("")

    results: List[Tuple[str, int, int, int, int, int]] = []

    with PoKeysReadOnlySession(board, lib_path) as session:
        print(session.identity_text())
        print(_matrix_kb_config_text(session))
        print("")

        for label in sequence:
            print(f"Naciśnij klawisz [{label}] ...", flush=True)
            base = _matrix_kb_values(session)
            started = time.time()
            detected: Optional[Tuple[int, int, int]] = None

            while True:
                current = _matrix_kb_values(session)
                detected = _first_matrix_change(base, current)
                if detected is not None:
                    idx, old, new = detected
                    row = idx // 8
                    col = idx % 8
                    print(f"[x] Klawisz [{label}] wykryty: index={idx}, row={row}, col={col}, {old}->{new}", flush=True)
                    results.append((label, idx, row, col, old, new))
                    break

                if args.timeout > 0 and (time.time() - started) > args.timeout:
                    print(f"[!] Klawisz [{label}]: timeout — nie wykryto naciśnięcia w {args.timeout}s", flush=True)
                    break

                time.sleep(max(0.03, float(args.interval)))

            if detected is None:
                print("")
                continue

            if args.wait_release:
                print(f"Puść klawisz [{label}] ...", flush=True)
                release_started = time.time()
                while True:
                    current = _matrix_kb_values(session)
                    idx, old, new = detected
                    if int(current[idx]) == int(base[idx]):
                        print(f"[x] Klawisz [{label}] puszczony — OK", flush=True)
                        break

                    if args.timeout > 0 and (time.time() - release_started) > args.timeout:
                        print(f"[!] Klawisz [{label}]: nie wykryto puszczenia w {args.timeout}s", flush=True)
                        break

                    time.sleep(max(0.03, float(args.interval)))

            print("")

    print("MAPA WYKRYTA:")
    for label, idx, row, col, old, new in results:
        print(f"  {label}: index={idx}, row={row}, col={col}, transition={old}->{new}")

    print("Koniec mapowania klawiatury.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    identity, values = _read_values(args)
    reports_dir = _ensure_reports_dir()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = reports_dir / f"tarzan_mini_pc_sandbox_{args.board.lower()}_{stamp}.txt"
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("# TARZAN Mini PC Sandbox Report\n")
        f.write(f"# date={datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"# repo={REPO_ROOT}\n")
        f.write(f"# {identity}\n")
        f.write("\n")
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["board", "pin", "name", "canonical", "type", "direction", "group", "hw", "test_class", "digital", "analog_raw", "analog_v", "pin_function", "counter", "note"])
        for v in values:
            writer.writerow([v.board, v.pin, v.name, v.canonical, v.signal_type, v.direction, v.group, v.hardware_function, v.test_class, v.digital_value, v.analog_raw, v.analog_v, v.pin_function, v.counter_value, v.note])
    print(f"Zapisano raport: {path}")
    return 0


# ======================================================================
# CLI
# ======================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tarzanMiniPcSandbox",
        description="TARZAN Mini PC Hardware Sandbox — testy PoKeys/hardware według core/tarzanZmienneSygnalowe.py",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common_board(p):
        p.add_argument("--board", choices=["PLAY", "REC", "CNC", "ALL"], default="PLAY")
        p.add_argument("--pins", help="Lista pinów, np. 1,2,5-8")
        p.add_argument("--signals", help="Lista nazw sygnałów lub kanonicznych nazw, rozdzielona przecinkami")
        p.add_argument("--include-skipped", action="store_true", default=False, help="Pokaż także SYSTEM_SKIP/FORBIDDEN_MOTION")

    p_list = sub.add_parser("list", help="Pokaż mapę sygnałów z tarzanZmienneSygnalowe.py")
    common_board(p_list)
    p_list.set_defaults(func=cmd_list)

    p_scan = sub.add_parser("scan", help="Skan środowiska: biblioteka, PoKeys, porty serial")
    p_scan.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_scan.add_argument("--ethernet-timeout-ms", type=int, default=1000)
    p_scan.set_defaults(func=cmd_scan)

    p_read = sub.add_parser("read", help="READ ONLY: odczyt sygnałów z płytki")
    common_board(p_read)
    p_read.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_read.set_defaults(func=cmd_read)

    p_monitor = sub.add_parser("monitor", help="READ ONLY: monitorowanie sygnałów w pętli")
    common_board(p_monitor)
    p_monitor.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_monitor.add_argument("--interval", type=float, default=0.8)
    p_monitor.add_argument("--changes-only", action="store_true", help="Wypisuj tylko zmianę wartości, np. po naciśnięciu przycisku")
    p_monitor.add_argument("--initial", action="store_true", help="W trybie --changes-only wypisz też pierwszy stan")
    p_monitor.set_defaults(func=cmd_monitor)


    p_buttons = sub.add_parser("buttons-test", help="Prowadzony test przycisków F1-F4 na REC / RECK")
    p_buttons.add_argument("--board", choices=["REC"], default="REC")
    p_buttons.add_argument("--buttons", default="F1,F2,F3,F4", help="Lista przycisków, np. F1,F2,F3,F4")
    p_buttons.add_argument("--interval", type=float, default=0.12)
    p_buttons.add_argument("--timeout", type=float, default=30.0)
    p_buttons.add_argument("--no-wait-release", dest="wait_release", action="store_false")
    p_buttons.set_defaults(wait_release=True)
    p_buttons.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_buttons.set_defaults(func=cmd_buttons_test)



    p_led = sub.add_parser("led-test", help="Ręczny test LED F1-F4 na REC / RECK")
    p_led.add_argument("--board", choices=["REC"], default="REC")
    p_led.add_argument("--led", default="F1,F2,F3,F4", help="F1,F2,F3,F4 albo pojedynczy LED, np. F1")
    p_led.add_argument("--on-time", type=float, default=0.7)
    p_led.add_argument("--off-time", type=float, default=0.25)
    p_led.add_argument("--repeat", type=int, default=1)
    p_led.add_argument("--leave-off", action="store_true", default=True)
    p_led.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_led.add_argument("--confirm", default="")
    p_led.set_defaults(func=cmd_led_test)



    p_keyboard = sub.add_parser("keyboard-test", help="Prowadzony test klawiatury KB1-KB4 na PLAY / PLAYER")
    p_keyboard.add_argument("--board", choices=["PLAY"], default="PLAY")
    p_keyboard.add_argument("--keys", default="KB1,KB2,KB3,KB4", help="Lista klawiszy, np. KB1,KB2,KB3,KB4")
    p_keyboard.add_argument("--interval", type=float, default=0.12)
    p_keyboard.add_argument("--timeout", type=float, default=30.0)
    p_keyboard.add_argument("--no-wait-release", dest="wait_release", action="store_false")
    p_keyboard.set_defaults(wait_release=True)
    p_keyboard.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_keyboard.set_defaults(func=cmd_keyboard_test)



    p_keypad_map = sub.add_parser("keypad-map", help="Prowadzone mapowanie klawiatury matrix 4x3 na PLAY / PLAYER")
    p_keypad_map.add_argument("--board", choices=["PLAY"], default="PLAY")
    p_keypad_map.add_argument("--sequence", default="1,2,3,4,5,6,7,8,9,*,0,#", help="Kolejność klawiszy do naciśnięcia")
    p_keypad_map.add_argument("--interval", type=float, default=0.08)
    p_keypad_map.add_argument("--timeout", type=float, default=30.0)
    p_keypad_map.add_argument("--no-wait-release", dest="wait_release", action="store_false")
    p_keypad_map.set_defaults(wait_release=True)
    p_keypad_map.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_keypad_map.set_defaults(func=cmd_keypad_map)


    p_report = sub.add_parser("report", help="READ ONLY: odczyt i zapis raportu do data/hardware/reports")
    common_board(p_report)
    p_report.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_report.set_defaults(func=cmd_report)


    p_lcd = sub.add_parser("lcd-test", help="Test LCD HD44780 przez funkcje LCD PoKeys")
    p_lcd.add_argument("--board", choices=["PLAY", "REC"], required=True)
    p_lcd.add_argument("--line1", default="TARZAN")
    p_lcd.add_argument("--line2", default="LCD OK")
    p_lcd.add_argument("--rows", type=int, default=2)
    p_lcd.add_argument("--columns", type=int, default=16)
    p_lcd.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_lcd.add_argument("--confirm", default="")
    p_lcd.set_defaults(func=cmd_lcd_test)



    p_lcd_scroll = sub.add_parser("lcd-scroll", help="Przewijanie tekstu na LCD HD44780 przez funkcje LCD PoKeys")
    p_lcd_scroll.add_argument("--board", choices=["PLAY", "REC"], required=True)
    p_lcd_scroll.add_argument("--text", default="TARZAN LCD SCROLL TEST")
    p_lcd_scroll.add_argument("--line2", default="")
    p_lcd_scroll.add_argument("--rows", type=int, default=2)
    p_lcd_scroll.add_argument("--columns", type=int, default=16)
    p_lcd_scroll.add_argument("--delay", type=float, default=0.18)
    p_lcd_scroll.add_argument("--repeat", type=int, default=2)
    p_lcd_scroll.add_argument("--clear-end", action="store_true")
    p_lcd_scroll.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_lcd_scroll.add_argument("--confirm", default="")
    p_lcd_scroll.set_defaults(func=cmd_lcd_scroll)



    p_matrix = sub.add_parser("matrix-test", help="Test Matrix LED na REC / RECK przez funkcje MatrixLED PoKeys")
    p_matrix.add_argument("--board", choices=["REC"], required=True)
    p_matrix.add_argument("--text", default="TARZAN")
    p_matrix.add_argument("--mode", choices=["scroll", "blink", "checker", "box"], default="scroll")
    p_matrix.add_argument("--delay", type=float, default=0.18)
    p_matrix.add_argument("--repeat", type=int, default=1)
    p_matrix.add_argument("--invert", action="store_true")
    p_matrix.add_argument("--clear-end", action="store_true")
    p_matrix.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_matrix.add_argument("--confirm", default="")
    p_matrix.set_defaults(func=cmd_matrix_test)


    p_out = sub.add_parser("output", help="Ręczny test bezpiecznego wyjścia")
    p_out.add_argument("--board", choices=["PLAY", "REC"], required=True)
    p_out.add_argument("--signal", required=True, help="Nazwa sygnału z tarzanZmienneSygnalowe.py")
    p_out.add_argument("--value", type=int, choices=[0, 1], required=True)
    p_out.add_argument("--lib-path", help="Ścieżka do libPoKeys.so albo PoKeyslib.dll")
    p_out.add_argument("--allow-write", action="store_true")
    p_out.add_argument("--confirm", default="")
    p_out.set_defaults(func=cmd_output)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\nPrzerwano.")
        return 130
    except Exception as exc:
        print(f"[BŁĄD] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
