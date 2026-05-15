"""
TARZAN SignalBus — centralna magistrala sygnałów TEST / LIVE / MIX.

Cel:
- jedno API dla pełnej mapy WSZYSTKIE_SYGNALY,
- PAR w trybie TEST działa jako sprzęt zastępczy,
- TAKE może zasilać wyjścia STEP/DIR/EVENT w czasie 10 ms,
- późniejszy adapter PoKeys może podmienić warstwę LIVE bez zmiany PAR/EHR/KHR.

Ten plik NIE steruje mechaniką i NIE generuje STEP z krzywej.
Przenosi tylko stany sygnałów po nazwach z mapy systemu.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

try:
    from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
except Exception:
    CZAS_PROBKOWANIA_MS = 10


SignalCallback = Callable[[str, "TarzanSignalState"], None]


@dataclass(frozen=True)
class TarzanSignalMeta:
    nazwa: str
    plytka: str = ""
    pin: Optional[int] = None
    kanal: Optional[str] = None
    typ: str = "LH"
    kierunek: str = "IN"
    default: str = "0"
    opis: str = ""
    grupa: str = ""
    status: str = "AKTYWNY"
    hardware_function: str = ""
    hardware_label: str = ""
    panel_port: Optional[int] = None
    logika_trybow: str = ""
    rola_logiki: str = ""
    klasa_wykonawcza: str = ""
    conflict_group: Optional[str] = None

    @property
    def is_input(self) -> bool:
        return self.kierunek == "IN"

    @property
    def is_output(self) -> bool:
        return self.kierunek == "OUT"

    @property
    def is_analog(self) -> bool:
        return self.typ == "ANALOG"

    @property
    def is_forbidden(self) -> bool:
        return self.typ in {"F", "RESERVED"} or self.kierunek in {"F", "RESERVED"}


@dataclass
class TarzanSignalState:
    name: str
    value: Any = 0
    forced: bool = False
    source: str = "BOOT"       # BOOT / UI / TAKE / LIVE / API / SAFETY
    mode: str = "TEST"         # TEST / LIVE / MIX
    timestamp: float = field(default_factory=time.time)
    time_ms: Optional[int] = None
    previous_value: Any = None
    event: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "forced": self.forced,
            "source": self.source,
            "mode": self.mode,
            "timestamp": self.timestamp,
            "time_ms": self.time_ms,
            "previous_value": self.previous_value,
            "event": self.event,
        }


class TarzanSignalBus:
    """
    Centralny stan sygnałów TARZANA.

    Zasada kierunków:
    - IN: w TEST można ustawiać przez PAR, w LIVE docelowo przychodzą z PoKeys.
    - OUT: ustawiane przez program/TAKE; PAR pokazuje je i w DEBUG może wymusić.
    - F/RESERVED: tylko podgląd, domyślnie blokowane.
    """

    MODES = {"TEST", "LIVE", "MIX"}

    def __init__(self, mode: str = "TEST", sample_ms: int = CZAS_PROBKOWANIA_MS) -> None:
        self.sample_ms = int(sample_ms)
        self.mode = mode if mode in self.MODES else "TEST"
        self._lock = threading.RLock()
        self.meta: Dict[str, TarzanSignalMeta] = {}
        self.state: Dict[str, TarzanSignalState] = {}
        self.subscribers: List[SignalCallback] = []
        self.log_lines: List[str] = []
        self.history: List[Dict[str, Any]] = []
        self.max_history = 5000
        self.take_time_ms: int = 0
        self.loaded_take_path: Optional[str] = None
        self.debug_override_outputs: bool = False
        self.live_adapter: Any = None
        self._load_signal_map()
        self._ensure_par_sensor_virtual_signals()
        self.log("BUS", f"SignalBus start mode={self.mode} signals={len(self.meta)}")

    # ------------------------------------------------------------------
    # ŁADOWANIE MAPY SYGNAŁÓW
    # ------------------------------------------------------------------
    def _load_signal_map(self) -> None:
        loaded = False
        try:
            from core.tarzanZmienneSygnalowe import WSZYSTKIE_SYGNALY
            for name, signal in WSZYSTKIE_SYGNALY.items():
                meta = self._meta_from_object(signal)
                self.meta[name] = meta
                self.state[name] = TarzanSignalState(
                    name=name,
                    value=self._default_value(meta),
                    mode=self.mode,
                    source="BOOT",
                )
            loaded = True
        except Exception as exc:
            self.log("BUS", f"Nie udało się zaimportować WSZYSTKIE_SYGNALY: {exc}")

        if not loaded:
            self._load_from_catalog_json()

        if not self.meta:
            meta = TarzanSignalMeta(
                nazwa="BRAK_MAPY_SYGNALOW",
                plytka="SYSTEM",
                typ="LH",
                kierunek="IN",
                opis="Nie znaleziono core.tarzanZmienneSygnalowe ani tarzan_signals_catalog.json",
                grupa="SYSTEM",
                status="BŁĄD",
            )
            self.meta[meta.nazwa] = meta
            self.state[meta.nazwa] = TarzanSignalState(meta.nazwa, 0, source="ERROR", mode=self.mode)

    def _load_from_catalog_json(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "tarzan_signals_catalog.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                items = data.values() if all(isinstance(v, dict) for v in data.values()) else data.get("signals", [])
            else:
                items = data
            for item in items:
                name = item.get("nazwa") or item.get("name")
                if not name:
                    continue
                meta = TarzanSignalMeta(
                    nazwa=name,
                    plytka=item.get("plytka", ""),
                    pin=item.get("pin"),
                    kanal=item.get("kanal"),
                    typ=item.get("typ", "LH"),
                    kierunek=item.get("kierunek", "IN"),
                    default=str(item.get("default", "0")),
                    opis=item.get("opis", ""),
                    grupa=item.get("grupa", ""),
                    status=item.get("status", "AKTYWNY"),
                    hardware_function=item.get("hardware_function", ""),
                    hardware_label=item.get("hardware_label", ""),
                    panel_port=item.get("panel_port"),
                    logika_trybow=item.get("logika_trybow", ""),
                    rola_logiki=item.get("rola_logiki", ""),
                    klasa_wykonawcza=item.get("klasa_wykonawcza", ""),
                    conflict_group=item.get("conflict_group"),
                )
                self.meta[name] = meta
                self.state[name] = TarzanSignalState(name, self._default_value(meta), mode=self.mode, source="BOOT_JSON")
        except Exception as exc:
            self.log("BUS", f"Nie udało się wczytać tarzan_signals_catalog.json: {exc}")

    def _meta_from_object(self, signal: Any) -> TarzanSignalMeta:
        return TarzanSignalMeta(
            nazwa=getattr(signal, "nazwa", ""),
            plytka=getattr(signal, "plytka", ""),
            pin=getattr(signal, "pin", None),
            kanal=getattr(signal, "kanal", None),
            typ=getattr(signal, "typ", "LH"),
            kierunek=getattr(signal, "kierunek", "IN"),
            default=str(getattr(signal, "default", "0")),
            opis=getattr(signal, "opis", ""),
            grupa=getattr(signal, "grupa", ""),
            status=getattr(signal, "status", "AKTYWNY"),
            hardware_function=getattr(signal, "hardware_function", ""),
            hardware_label=getattr(signal, "hardware_label", ""),
            panel_port=getattr(signal, "panel_port", None),
            logika_trybow=getattr(signal, "logika_trybow", ""),
            rola_logiki=getattr(signal, "rola_logiki", ""),
            klasa_wykonawcza=getattr(signal, "klasa_wykonawcza", ""),
            conflict_group=getattr(signal, "conflict_group", None),
        )

    def _default_value(self, meta: TarzanSignalMeta) -> Any:
        if meta.typ == "ANALOG":
            try:
                return float(meta.default)
            except Exception:
                return 0.0
        if meta.typ == "CTR":
            # Domyślne CTR w mapie może mieć wzorzec typu "1010...".
            # Stan chwilowy magistrali trzymamy jako 0/1.
            return 0
        if meta.typ in {"F", "RESERVED"}:
            return None
        return 1 if str(meta.default).strip() == "1" else 0


    def _ensure_par_sensor_virtual_signals(self) -> None:
        """Wirtualne sygnały PAR dla nowych okien wskaźnikowych czujników."""
        virtuals = [
            ("par_lamp_auto_active", "PAR", "LH", "IN", "0", "Lampka pracy ramienia / automatyka włączona", "PAR_LAMP"),
            ("par_mass_reg_enable", "PAR", "LH", "IN", "0", "Regulator masy — sygnał włączający", "REGULATOR_MASY"),
            ("par_mass_reg_limit_add", "PAR", "LH", "IN", "0", "Regulator masy — masa dodana", "REGULATOR_MASY"),
            ("par_mass_reg_limit_remove", "PAR", "LH", "IN", "0", "Regulator masy — masa odjęta", "REGULATOR_MASY"),
            ("par_shock_sensor_state", "PAR", "LH", "IN", "0", "Czujnik wstrząsowy — stan wysoki/niski", "CZUJNIK_WSTRZASOWY"),
            ("par_bh1750_lux", "PAR", "ANALOG", "IN", "0", "BH1750 — odczyt światła lux", "CZUJNIK_SWIATLA"),
            ("par_level_x", "PAR", "ANALOG", "IN", "0", "Poziom XYZ — X", "CZUJNIK_POZIOMU_XYZ"),
            ("par_level_y", "PAR", "ANALOG", "IN", "0", "Poziom XYZ — Y", "CZUJNIK_POZIOMU_XYZ"),
            ("par_level_z", "PAR", "ANALOG", "IN", "0", "Poziom XYZ — Z", "CZUJNIK_POZIOMU_XYZ"),
            ("par_temperature_c", "PAR", "ANALOG", "IN", "0", "Temperatura — odczyt C", "CZUJNIK_TEMPERATURY"),
            ("par_laser_set", "PAR", "LH", "IN", "0", "Laser — SET", "CZUJNIK_LASEROWY"),
            ("par_laser_error", "PAR", "LH", "IN", "0", "Laser — ERROR", "CZUJNIK_LASEROWY"),
            ("par_laser_state_high", "PAR", "LH", "IN", "0", "Laser — stan wysoki", "CZUJNIK_LASEROWY"),
            ("par_laser_state_low", "PAR", "LH", "IN", "1", "Laser — stan niski", "CZUJNIK_LASEROWY"),
            ("par_lcd_line1", "PAR", "TEXT", "IN", "TARZAN PLAY", "LCD 1602 — linia 1", "LCD_1602"),
            ("par_lcd_line2", "PAR", "TEXT", "IN", "READY", "LCD 1602 — linia 2", "LCD_1602"),
            ("par_lcd_play_line1", "PAR", "TEXT", "IN", "TARZAN PLAY", "PLAY LCD 1602 — linia 1", "LCD_1602"),
            ("par_lcd_play_line2", "PAR", "TEXT", "IN", "READY", "PLAY LCD 1602 — linia 2", "LCD_1602"),
            ("par_lcd_rec_line1", "PAR", "TEXT", "IN", "TARZAN REC", "REC LCD 1602 — linia 1", "LCD_1602"),
            ("par_lcd_rec_line2", "PAR", "TEXT", "IN", "READY", "REC LCD 1602 — linia 2", "LCD_1602"),
            ("par_matrix_pattern", "PAR", "TEXT", "IN", "", "Matrix LED 8x8 — wzór", "MATRIX_LED"),
            ("par_mass_reg_value", "PAR", "ANALOG", "IN", "0", "Regulator masy — pozycja procentowa", "REGULATOR_MASY"),
            ("par_rrp_p1_axis", "PAR", "ANALOG", "IN", "-1", "RRP P1 — wybrana oś", "RRP"),
            ("par_rrp_p1_dir", "PAR", "LH", "IN", "0", "RRP P1 — kierunek", "RRP"),
            ("par_rrp_p1_sens", "PAR", "ANALOG", "IN", "50", "RRP P1 — czułość", "RRP"),
            ("par_rrp_p1_val", "PAR", "TEXT", "IN", "0", "RRP P1 — wartość/gęstość STEP", "RRP"),
            ("par_rrp_p2_axis", "PAR", "ANALOG", "IN", "-1", "RRP P2 — wybrana oś", "RRP"),
            ("par_rrp_p2_dir", "PAR", "LH", "IN", "0", "RRP P2 — kierunek", "RRP"),
            ("par_rrp_p2_sens", "PAR", "ANALOG", "IN", "50", "RRP P2 — czułość", "RRP"),
            ("par_rrp_p2_val", "PAR", "TEXT", "IN", "0", "RRP P2 — wartość/gęstość STEP", "RRP"),
            ("par_cam_h_pulses", "PAR", "ANALOG", "IN", "0", "Licznik impulsów CAM H", "PAR_COUNTERS"),
            ("par_cam_v_pulses", "PAR", "ANALOG", "IN", "0", "Licznik impulsów CAM V", "PAR_COUNTERS"),
            ("par_cam_t_pulses", "PAR", "ANALOG", "IN", "0", "Licznik impulsów CAM T", "PAR_COUNTERS"),
            ("par_cam_f_pulses", "PAR", "ANALOG", "IN", "0", "Licznik impulsów CAM F", "PAR_COUNTERS"),
            ("par_arm_h_pulses", "PAR", "ANALOG", "IN", "0", "Licznik impulsów ARM H", "PAR_COUNTERS"),
            ("par_arm_v_pulses", "PAR", "ANALOG", "IN", "0", "Licznik impulsów ARM V", "PAR_COUNTERS"),
            ("par_dron_pulses", "PAR", "ANALOG", "IN", "0", "Licznik impulsów DRON", "PAR_COUNTERS"),
            ("par_cam_h_pos", "PAR", "ANALOG", "IN", "0", "Pozycja CAM H", "PAR_POSITIONS"),
            ("par_cam_v_pos", "PAR", "ANALOG", "IN", "0", "Pozycja CAM V", "PAR_POSITIONS"),
            ("par_cam_t_pos", "PAR", "ANALOG", "IN", "0", "Pozycja CAM T", "PAR_POSITIONS"),
            ("par_cam_f_pos", "PAR", "ANALOG", "IN", "0", "Pozycja CAM F", "PAR_POSITIONS"),
            ("par_arm_h_pos", "PAR", "ANALOG", "IN", "0", "Pozycja ARM H", "PAR_POSITIONS"),
            ("par_arm_v_pos", "PAR", "ANALOG", "IN", "0", "Pozycja ARM V", "PAR_POSITIONS"),
            ("par_dron_pos", "PAR", "ANALOG", "IN", "0", "Pozycja DRON", "PAR_POSITIONS"),
        ]
        for name, board, typ, direction, default, opis, group in virtuals:
            if name in self.meta:
                continue
            meta = TarzanSignalMeta(
                nazwa=name,
                plytka=board,
                typ=typ,
                kierunek=direction,
                default=default,
                opis=opis,
                grupa=group,
                status="AKTYWNY",
                hardware_function="PAR_SENSOR_INDICATOR",
                hardware_label=opis,
                klasa_wykonawcza="core.tarzanSignalBus.py",
                logika_trybow="TEST/LIVE/MIX",
                rola_logiki="PAR_SENSOR_INDICATOR",
            )
            self.meta[name] = meta
            self.state[name] = TarzanSignalState(
                name=name,
                value=self._default_value(meta),
                mode=self.mode,
                source="PAR_VIRTUAL",
            )


    # ------------------------------------------------------------------
    # SUBSKRYPCJE / LOG
    # ------------------------------------------------------------------
    def subscribe(self, callback: SignalCallback) -> None:
        with self._lock:
            if callback not in self.subscribers:
                self.subscribers.append(callback)

    def unsubscribe(self, callback: SignalCallback) -> None:
        with self._lock:
            if callback in self.subscribers:
                self.subscribers.remove(callback)

    def _notify(self, name: str) -> None:
        st = self.state[name]
        for callback in list(self.subscribers):
            try:
                callback(name, st)
            except Exception as exc:
                self.log("BUS", f"subscriber error: {exc}")

    def log(self, source: str, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        line = f"{stamp} [{source}] {message}"
        self.log_lines.append(line)
        if len(self.log_lines) > 1000:
            self.log_lines = self.log_lines[-1000:]

    # ------------------------------------------------------------------
    # TRYB / ADAPTER LIVE
    # ------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        if mode not in self.MODES:
            raise ValueError(f"Nieznany tryb SignalBus: {mode}")
        with self._lock:
            self.mode = mode
            for st in self.state.values():
                st.mode = mode
            self.log("MODE", f"SignalBus mode={mode}")

    def set_live_adapter(self, adapter: Any) -> None:
        """Adapter LIVE ma docelowo implementować read(name), write(name, value), snapshot()."""
        with self._lock:
            self.live_adapter = adapter
            self.log("LIVE", f"Podpięto adapter LIVE: {adapter.__class__.__name__}")

    # ------------------------------------------------------------------
    # API GŁÓWNE
    # ------------------------------------------------------------------
    def exists(self, name: str) -> bool:
        return name in self.state

    def get_meta(self, name: str) -> Optional[TarzanSignalMeta]:
        return self.meta.get(name)

    def read(self, name: str, default: Any = 0) -> Any:
        with self._lock:
            if self.mode == "LIVE" and self.live_adapter is not None:
                try:
                    return self.live_adapter.read(name)
                except Exception as exc:
                    self.log("LIVE", f"read({name}) error: {exc}")
            return self.state.get(name, TarzanSignalState(name, default)).value

    def read_input(self, name: str, default: Any = 0) -> Any:
        return self.read(name, default)

    def get(self, name: str, default: Any = 0) -> Any:
        return self.read(name, default)

    def set_input(self, name: str, value: Any, *, source: str = "UI", forced: bool = True, time_ms: Optional[int] = None) -> bool:
        return self._set(name, value, source=source, forced=forced, time_ms=time_ms, allow_output=False, allow_reserved=False)

    def write_output(self, name: str, value: Any, *, source: str = "API", forced: bool = False, time_ms: Optional[int] = None) -> bool:
        if self.mode == "LIVE" and self.live_adapter is not None:
            try:
                self.live_adapter.write(name, value)
            except Exception as exc:
                self.log("LIVE", f"write({name}) error: {exc}")
        return self._set(name, value, source=source, forced=forced, time_ms=time_ms, allow_output=True, allow_reserved=False)

    def force_signal(self, name: str, value: Any, *, source: str = "FORCE", time_ms: Optional[int] = None) -> bool:
        return self._set(name, value, source=source, forced=True, time_ms=time_ms, allow_output=True, allow_reserved=True)

    def toggle_input(self, name: str, *, source: str = "UI") -> bool:
        return self.set_input(name, 0 if self.read(name) else 1, source=source, forced=True)

    def _set(
        self,
        name: str,
        value: Any,
        *,
        source: str,
        forced: bool,
        time_ms: Optional[int],
        allow_output: bool,
        allow_reserved: bool,
    ) -> bool:
        with self._lock:
            if name not in self.state:
                # Magistrala toleruje sygnały pośrednie z TAKE, ale oznacza je jako VIRTUAL.
                meta = TarzanSignalMeta(nazwa=name, plytka="VIRTUAL", typ="LH", kierunek="OUT", opis="Sygnał wirtualny SignalBus")
                self.meta[name] = meta
                self.state[name] = TarzanSignalState(name=name, value=0, mode=self.mode, source="VIRTUAL")
                self.log("BUS", f"Dodano sygnał wirtualny: {name}")

            meta = self.meta[name]
            if meta.is_forbidden and not allow_reserved:
                self.log("BLOCK", f"{name} zablokowany (F/RESERVED)")
                return False
            if meta.is_output and not allow_output and not self.debug_override_outputs:
                self.log("BLOCK", f"{name} jest OUT — użyj write_output albo DEBUG override")
                return False

            value = self._normalize_value(meta, value)
            st = self.state[name]
            if st.value == value and st.forced == forced and st.source == source and st.time_ms == time_ms:
                return True
            st.previous_value = st.value
            st.value = value
            st.forced = forced
            st.source = source
            st.mode = self.mode
            st.timestamp = time.time()
            st.time_ms = time_ms
            self._append_history(name, st)
            self._notify(name)
            return True

    def _normalize_value(self, meta: TarzanSignalMeta, value: Any) -> Any:
        if meta.typ == "TEXT":
            return str(value)
        if meta.typ == "ANALOG":
            try:
                return float(value)
            except Exception:
                return 0.0
        if meta.typ == "CTR":
            if isinstance(value, str) and "1" in value:
                return 1
            try:
                return 1 if int(value or 0) else 0
            except Exception:
                return 0
        if value in {True, "1", 1, "true", "TRUE", "on", "ON"}:
            return 1
        if value in {False, "0", 0, "false", "FALSE", "off", "OFF", None, ""}:
            return 0
        try:
            return 1 if int(value) else 0
        except Exception:
            return value

    def _append_history(self, name: str, st: TarzanSignalState) -> None:
        self.history.append(st.to_dict())
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    # ------------------------------------------------------------------
    # SNAPSHOT / RESET
    # ------------------------------------------------------------------
    def snapshot(self, *, include_meta: bool = False) -> Dict[str, Any]:
        with self._lock:
            data = {
                "mode": self.mode,
                "sample_ms": self.sample_ms,
                "take_time_ms": self.take_time_ms,
                "loaded_take_path": self.loaded_take_path,
                "signals": {name: st.to_dict() for name, st in self.state.items()},
            }
            if include_meta:
                data["meta"] = {name: asdict(meta) for name, meta in self.meta.items()}
            return data

    def values_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {name: st.value for name, st in self.state.items()}

    def apply_snapshot(self, snapshot: Dict[str, Any], *, source: str = "SNAPSHOT") -> None:
        signals = snapshot.get("signals", snapshot)
        for name, data in signals.items():
            value = data.get("value") if isinstance(data, dict) else data
            self.force_signal(name, value, source=source)

    def reset_to_defaults(self) -> None:
        with self._lock:
            for name, meta in self.meta.items():
                st = self.state[name]
                st.previous_value = st.value
                st.value = self._default_value(meta)
                st.forced = False
                st.source = "RESET"
                st.timestamp = time.time()
                st.time_ms = None
                self._notify(name)
            self.log("RESET", "Przywrócono domyślne stany sygnałów")

    # ------------------------------------------------------------------
    # FILTRY
    # ------------------------------------------------------------------
    def names(self) -> List[str]:
        return list(self.state.keys())

    def by_group(self, group: str) -> List[str]:
        group_u = group.upper()
        return [name for name, meta in self.meta.items() if (meta.grupa or "").upper() == group_u]

    def by_direction(self, direction: str) -> List[str]:
        direction_u = direction.upper()
        return [name for name, meta in self.meta.items() if (meta.kierunek or "").upper() == direction_u]

    def search(self, text: str) -> List[str]:
        q = (text or "").lower().strip()
        if not q:
            return self.names()
        out: List[str] = []
        for name, meta in self.meta.items():
            blob = " ".join([
                name,
                meta.opis or "",
                meta.grupa or "",
                meta.plytka or "",
                meta.hardware_label or "",
                meta.hardware_function or "",
            ]).lower()
            if q in blob:
                out.append(name)
        return out

    # ------------------------------------------------------------------
    # TAKE SUPPORT
    # ------------------------------------------------------------------
    def set_take_time(self, time_ms: int) -> None:
        self.take_time_ms = int(time_ms)

    def write_many_outputs(self, values: Dict[str, Any], *, source: str = "TAKE", time_ms: Optional[int] = None) -> None:
        for name, value in values.items():
            self.write_output(name, value, source=source, time_ms=time_ms)


_GLOBAL_BUS: Optional[TarzanSignalBus] = None
_GLOBAL_LOCK = threading.RLock()


def get_signal_bus(mode: str = "TEST") -> TarzanSignalBus:
    global _GLOBAL_BUS
    with _GLOBAL_LOCK:
        if _GLOBAL_BUS is None:
            _GLOBAL_BUS = TarzanSignalBus(mode=mode)
        return _GLOBAL_BUS


def reset_global_signal_bus(mode: str = "TEST") -> TarzanSignalBus:
    global _GLOBAL_BUS
    with _GLOBAL_LOCK:
        _GLOBAL_BUS = TarzanSignalBus(mode=mode)
        return _GLOBAL_BUS


# Wygodne funkcje dla przyszłych modułów KHR/EHR/skryptów.
def read_signal(name: str, default: Any = 0) -> Any:
    return get_signal_bus().read(name, default)


def set_input(name: str, value: Any, source: str = "API") -> bool:
    return get_signal_bus().set_input(name, value, source=source)


def write_output(name: str, value: Any, source: str = "API") -> bool:
    return get_signal_bus().write_output(name, value, source=source)
