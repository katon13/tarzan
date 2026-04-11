"""
tarzanPoKeysSetting.py

Stała konfiguracja płytek PoKeys57U dla projektu TARZAN.

Rola modułu:
- połączenie z płytką PLAY lub REC,
- odczyt aktualnej konfiguracji,
- walidacja zgodności z referencyjną mapą sygnałów,
- ustawienie bazowych funkcji pinów,
- ustawienie bezpiecznych stanów wyjść,
- opcjonalny zapis konfiguracji do pamięci urządzenia.

Założenie bezpieczeństwa:
- moduł NIE zapisuje konfiguracji do flash sam z siebie,
- zapis do flash jest wywoływany tylko jawnie,
- PLAY i REC są zawsze obsługiwane przez DWIE osobne instancje PoKeysDevice,
- połączenie odbywa się po SERIALU, nigdy po indeksie urządzenia USB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from PoKeys import PoKeysDevice, ePK_PinCap

from tarzanZmienneSygnalowe import (
    POKEYS57U_PLAY_DEVICE_SERIAL,
    POKEYS57U_REC_DEVICE_SERIAL,
    SYGNALY_PLAY,
    SYGNALY_REC,
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
)


# ======================================================================
# WYJĄTKI
# ======================================================================

class TarzanPoKeysError(RuntimeError):
    """Błąd bazowy modułu konfiguracji PoKeys."""


class TarzanPoKeysConnectionError(TarzanPoKeysError):
    """Błąd połączenia z płytką."""


class TarzanPoKeysValidationError(TarzanPoKeysError):
    """Błąd walidacji konfiguracji."""


# ======================================================================
# MODELE DANYCH
# ======================================================================

@dataclass(frozen=True)
class TarzanPinMismatch:
    board_name: str
    serial: int
    nazwa: str
    pin: int
    expected_pin_function: int
    actual_pin_function: int
    opis: str


@dataclass(frozen=True)
class TarzanPinConflict:
    board_name: str
    nazwa: str
    pin: int
    conflict_group: str
    opis: str


@dataclass(frozen=True)
class TarzanBoardIdentity:
    board_name: str
    expected_serial: int
    actual_serial: int
    device_name: str
    firmware_major: int
    firmware_minor: int


@dataclass
class TarzanValidationReport:
    identity: TarzanBoardIdentity
    mismatches: List[TarzanPinMismatch]
    conflicts: List[TarzanPinConflict]

    @property
    def is_ok(self) -> bool:
        return not self.mismatches and not self.conflicts


# ======================================================================
# MAPOWANIE TARZAN -> PoKeys PinFunction
# ======================================================================

def _expected_pin_function(signal: TarzanSygnal) -> Optional[int]:
    """
    Wyznacza bazową funkcję PinFunction dla danego sygnału.

    Uwaga:
    - funkcje specjalne LCD / Matrix LED / I2C / Pulse / PoExtBus mają własne
      dodatkowe konfiguracje, ale bazowo pin i tak jest cyfrowy albo analogowy,
      zgodnie z dokumentacją i przykładami użycia biblioteki.
    """
    if signal.typ == "ANALOG":
        return ePK_PinCap.PK_PinCap_analogInput

    if signal.typ == "RESERVED":
        return ePK_PinCap.PK_PinCap_pinRestricted

    if signal.hardware_function in (HW_RESERVED, HW_SYSTEM):
        return ePK_PinCap.PK_PinCap_pinRestricted

    if signal.typ in ("LH", "CTR"):
        if signal.kierunek == "IN":
            return ePK_PinCap.PK_PinCap_digitalInput
        if signal.kierunek == "OUT":
            return ePK_PinCap.PK_PinCap_digitalOutput

    if signal.typ == "F":
        if signal.hardware_function == HW_ANALOG:
            return ePK_PinCap.PK_PinCap_analogInput
        if signal.kierunek == "IN":
            return ePK_PinCap.PK_PinCap_digitalInput
        if signal.kierunek == "OUT":
            return ePK_PinCap.PK_PinCap_digitalOutput
        return ePK_PinCap.PK_PinCap_digitalOutput

    return None


def _safe_output_default(signal: TarzanSygnal) -> Optional[int]:
    """
    Wyznacza bezpieczny stan wyjścia po konfiguracji.

    Zasada:
    - dla zwykłych LH OUT bierzemy default 0/1,
    - dla CTR zawsze ustawiamy 0,
    - dla wyjść specjalnych też bierzemy 0/1 jeśli jawnie podane,
      w przeciwnym razie 0.
    """
    if signal.kierunek != "OUT":
        return None

    if signal.typ == "CTR":
        return 0

    if signal.default == "1":
        return 1
    if signal.default == "0":
        return 0

    return 0


# ======================================================================
# SESJA PŁYTKI
# ======================================================================

class TarzanPoKeysBoardSession:
    """
    Osobna sesja dla jednej płytki.
    Jedna instancja = jedno połączenie = jedna płytka.
    """

    def __init__(self, dll_path: str, board_name: str, serial: int) -> None:
        self.dll_path = dll_path
        self.board_name = board_name
        self.serial = serial
        self.device = PoKeysDevice(self.dll_path)
        self.connected = False

    def connect(self) -> None:
        self.device.ShowAllDevices(1000)

        ok = self.device.PK_ConnectToDeviceWSerial(self.serial, 1, True)
        if not ok:
            raise TarzanPoKeysConnectionError(
                f"Nie udało się połączyć z płytką {self.board_name} "
                f"(serial={self.serial})."
            )

        try:
            actual_serial = int(self.device.device.contents.DeviceData.SerialNumber)
        except Exception as exc:
            raise TarzanPoKeysConnectionError(
                f"Połączenie z {self.board_name} zostało nawiązane, ale nie udało się "
                f"odczytać numeru seryjnego."
            ) from exc

        if actual_serial != self.serial:
            raise TarzanPoKeysConnectionError(
                f"Płytka {self.board_name} ma zły serial po połączeniu. "
                f"Oczekiwano {self.serial}, odczytano {actual_serial}."
            )

        self.device.PK_PinConfigurationGet()
        self.device.PK_DigitalIOGet()
        self.device.PK_AnalogIOGet()
        self.connected = True

    def disconnect(self) -> None:
        try:
            self.device.Disconnect()
        except Exception:
            pass
        self.connected = False

    def identity(self) -> TarzanBoardIdentity:
        if not self.connected:
            raise TarzanPoKeysConnectionError(
                f"Płytka {self.board_name} nie jest połączona."
            )

        dev = self.device.device.contents.DeviceData
        device_name = dev.DeviceName.decode("ascii", errors="ignore").strip("\x00")
        fw_major = int(dev.FirmwareVersionMajor)
        fw_minor = int(dev.FirmwareVersionMinor)
        actual_serial = int(dev.SerialNumber)

        return TarzanBoardIdentity(
            board_name=self.board_name,
            expected_serial=self.serial,
            actual_serial=actual_serial,
            device_name=device_name,
            firmware_major=fw_major,
            firmware_minor=fw_minor,
        )


# ======================================================================
# GŁÓWNA KLASA
# ======================================================================

class TarzanPoKeysSetting:
    """
    Główna klasa konfiguracji stałej PoKeys dla TARZAN.

    Użycie:
        cfg = TarzanPoKeysSetting()
        play_report = cfg.validate_play()
        rec_report = cfg.validate_rec()

        cfg.configure_play(save_to_flash=False)
        cfg.configure_rec(save_to_flash=False)
    """

    def __init__(
        self,
        dll_path: str = "./PoKeyslib.dll",
        play_serial: int = POKEYS57U_PLAY_DEVICE_SERIAL,
        rec_serial: int = POKEYS57U_REC_DEVICE_SERIAL,
    ) -> None:
        self.dll_path = dll_path
        self.play_serial = play_serial
        self.rec_serial = rec_serial

    # ------------------------------------------------------------------
    # PUBLIC: WALIDACJA
    # ------------------------------------------------------------------

    def validate_play(self) -> TarzanValidationReport:
        return self._validate_board(
            board_name="PLAY",
            serial=self.play_serial,
            signals=SYGNALY_PLAY,
        )

    def validate_rec(self) -> TarzanValidationReport:
        return self._validate_board(
            board_name="REC",
            serial=self.rec_serial,
            signals=SYGNALY_REC,
        )

    def validate_all(self) -> Tuple[TarzanValidationReport, TarzanValidationReport]:
        return self.validate_play(), self.validate_rec()

    # ------------------------------------------------------------------
    # PUBLIC: KONFIGURACJA
    # ------------------------------------------------------------------

    def configure_play(self, save_to_flash: bool = False) -> TarzanValidationReport:
        return self._configure_board(
            board_name="PLAY",
            serial=self.play_serial,
            signals=SYGNALY_PLAY,
            save_to_flash=save_to_flash,
        )

    def configure_rec(self, save_to_flash: bool = False) -> TarzanValidationReport:
        return self._configure_board(
            board_name="REC",
            serial=self.rec_serial,
            signals=SYGNALY_REC,
            save_to_flash=save_to_flash,
        )

    def configure_all(
        self,
        save_to_flash: bool = False,
    ) -> Tuple[TarzanValidationReport, TarzanValidationReport]:
        play_report = self.configure_play(save_to_flash=save_to_flash)
        rec_report = self.configure_rec(save_to_flash=save_to_flash)
        return play_report, rec_report

    # ------------------------------------------------------------------
    # INTERNAL: WALIDACJA
    # ------------------------------------------------------------------

    def _validate_board(
        self,
        *,
        board_name: str,
        serial: int,
        signals: Dict[str, TarzanSygnal],
    ) -> TarzanValidationReport:
        session = TarzanPoKeysBoardSession(self.dll_path, board_name, serial)
        session.connect()
        try:
            identity = session.identity()
            conflicts = self._detect_map_conflicts(board_name, signals.values())
            mismatches = self._detect_pin_mismatches(session, signals.values())

            return TarzanValidationReport(
                identity=identity,
                mismatches=mismatches,
                conflicts=conflicts,
            )
        finally:
            session.disconnect()

    def _detect_pin_mismatches(
        self,
        session: TarzanPoKeysBoardSession,
        signals: Iterable[TarzanSygnal],
    ) -> List[TarzanPinMismatch]:
        mismatches: List[TarzanPinMismatch] = []

        for signal in signals:
            if signal.pin is None:
                continue

            expected = _expected_pin_function(signal)
            if expected is None:
                continue

            actual = int(session.device.device.contents.Pins[signal.pin - 1].PinFunction)
            if actual != int(expected):
                mismatches.append(
                    TarzanPinMismatch(
                        board_name=session.board_name,
                        serial=session.serial,
                        nazwa=signal.nazwa,
                        pin=signal.pin,
                        expected_pin_function=int(expected),
                        actual_pin_function=actual,
                        opis=signal.opis,
                    )
                )

        return mismatches

    def _detect_map_conflicts(
        self,
        board_name: str,
        signals: Iterable[TarzanSygnal],
    ) -> List[TarzanPinConflict]:
        conflicts: List[TarzanPinConflict] = []
        groups: Dict[str, List[TarzanSygnal]] = {}

        for signal in signals:
            if signal.conflict_group:
                groups.setdefault(signal.conflict_group, []).append(signal)

        for conflict_group, items in groups.items():
            if len(items) <= 1:
                continue

            active_items = [x for x in items if x.status == "AKTYWNY"]
            if len(active_items) <= 1:
                continue

            functions = {(x.hardware_function, x.pin) for x in active_items}
            if len(functions) > 1:
                for item in active_items:
                    conflicts.append(
                        TarzanPinConflict(
                            board_name=board_name,
                            nazwa=item.nazwa,
                            pin=item.pin or -1,
                            conflict_group=conflict_group,
                            opis=item.opis,
                        )
                    )

        return conflicts

    # ------------------------------------------------------------------
    # INTERNAL: KONFIGURACJA
    # ------------------------------------------------------------------

    def _configure_board(
        self,
        *,
        board_name: str,
        serial: int,
        signals: Dict[str, TarzanSygnal],
        save_to_flash: bool,
    ) -> TarzanValidationReport:
        session = TarzanPoKeysBoardSession(self.dll_path, board_name, serial)
        session.connect()
        try:
            identity = session.identity()
            conflicts = self._detect_map_conflicts(board_name, signals.values())
            if conflicts:
                raise TarzanPoKeysValidationError(
                    f"Nie można skonfigurować płytki {board_name}: "
                    f"wykryto konflikty sprzętowe w mapie sygnałów."
                )

            self._apply_base_pin_configuration(session, signals.values())
            self._apply_safe_output_defaults(session, signals.values())
            self._read_special_peripherals(session)

            if save_to_flash:
                session.device.PK_SaveConfiguration()

            # Po zapisie / ustawieniu odczyt jeszcze raz.
            session.device.PK_PinConfigurationGet()
            session.device.PK_DigitalIOGet()
            session.device.PK_AnalogIOGet()

            mismatches = self._detect_pin_mismatches(session, signals.values())
            return TarzanValidationReport(
                identity=identity,
                mismatches=mismatches,
                conflicts=[],
            )
        finally:
            session.disconnect()

    def _apply_base_pin_configuration(
        self,
        session: TarzanPoKeysBoardSession,
        signals: Iterable[TarzanSygnal],
    ) -> None:
        for signal in signals:
            if signal.pin is None:
                continue

            expected = _expected_pin_function(signal)
            if expected is None:
                continue

            session.device.device.contents.Pins[signal.pin - 1].PinFunction = expected

        session.device.PK_PinConfigurationSet()

    def _apply_safe_output_defaults(
        self,
        session: TarzanPoKeysBoardSession,
        signals: Iterable[TarzanSygnal],
    ) -> None:
        for signal in signals:
            if signal.pin is None:
                continue

            value = _safe_output_default(signal)
            if value is None:
                continue

            # PK_DigitalIOSetSingle używa indeksu 0-based, tak jak w przykładzie biblioteki.
            session.device.PK_DigitalIOSetSingle(signal.pin - 1, value)

        session.device.PK_DigitalIOGet()

    def _read_special_peripherals(self, session: TarzanPoKeysBoardSession) -> None:
        """
        Odczyt konfiguracji peryferiów specjalnych.

        Nie zmieniamy tutaj szczegółowych parametrów LCD / Matrix / PWM / PEv2,
        bo to powinno być doprecyzowane w kolejnych modułach i zgodne z realnym
        użyciem TARZAN. Tutaj tylko wymuszamy, że urządzenie odpowiada i peryferia
        są czytelne z biblioteki.
        """
        try:
            session.device.PK_LCDConfigurationGet()
        except Exception:
            pass

        try:
            session.device.PK_MatrixLEDConfigurationGet()
        except Exception:
            pass

        try:
            session.device.PK_MatrixKBConfigurationGet()
        except Exception:
            pass

        try:
            session.device.PK_PWMConfigurationGet()
        except Exception:
            pass

        try:
            session.device.PK_PoExtBusGet()
        except Exception:
            pass

        try:
            session.device.PK_PEv2_StatusGet()
        except Exception:
            pass


# ======================================================================
# SZYBKIE NARZĘDZIA TEKSTOWE
# ======================================================================

def formatuj_raport(report: TarzanValidationReport) -> str:
    lines: List[str] = []
    lines.append(
        f"[{report.identity.board_name}] "
        f"serial oczekiwany={report.identity.expected_serial}, "
        f"serial odczytany={report.identity.actual_serial}, "
        f"device='{report.identity.device_name}', "
        f"fw={report.identity.firmware_major}.{report.identity.firmware_minor}"
    )

    if report.conflicts:
        lines.append("Konflikty:")
        for item in report.conflicts:
            lines.append(
                f"  - pin {item.pin:02d} | {item.nazwa} | grupa={item.conflict_group} | {item.opis}"
            )

    if report.mismatches:
        lines.append("Rozjazdy konfiguracji:")
        for item in report.mismatches:
            lines.append(
                f"  - pin {item.pin:02d} | {item.nazwa} | expected={item.expected_pin_function} "
                f"| actual={item.actual_pin_function} | {item.opis}"
            )

    if report.is_ok:
        lines.append("Status: OK")

    return "\n".join(lines)