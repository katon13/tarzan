from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class ParSignal:
    nazwa: str
    plytka: str
    pin: Optional[int]
    kanal: Optional[str]
    typ: str
    kierunek: str
    default: str
    opis: str
    grupa: str
    status: str
    panel_port: Optional[int]
    klasa_wykonawcza: str
    hardware_function: str
    hardware_label: str
    conflict_group: Optional[str]
    logika_trybow: str
    rola_logiki: str


def _from_tarzan_signal(obj: Any) -> ParSignal:
    return ParSignal(
        nazwa=getattr(obj, "nazwa", ""),
        plytka=getattr(obj, "plytka", ""),
        pin=getattr(obj, "pin", None),
        kanal=getattr(obj, "kanal", None),
        typ=getattr(obj, "typ", ""),
        kierunek=getattr(obj, "kierunek", ""),
        default=str(getattr(obj, "default", "")),
        opis=getattr(obj, "opis", ""),
        grupa=getattr(obj, "grupa", ""),
        status=getattr(obj, "status", ""),
        panel_port=getattr(obj, "panel_port", None),
        klasa_wykonawcza=getattr(obj, "klasa_wykonawcza", ""),
        hardware_function=getattr(obj, "hardware_function", ""),
        hardware_label=getattr(obj, "hardware_label", ""),
        conflict_group=getattr(obj, "conflict_group", None),
        logika_trybow=getattr(obj, "logika_trybow", ""),
        rola_logiki=getattr(obj, "rola_logiki", ""),
    )


def load_all_signals() -> List[ParSignal]:
    candidates = [
        "core.tarzanZmienneSygnalowe",
        "hardware.tarzanZmienneSygnalowe",
        "tarzanZmienneSygnalowe",
        "editor.PAR.tarzanZmienneSygnalowe",
    ]
    for module_name in candidates:
        try:
            mod = __import__(module_name, fromlist=["WSZYSTKIE_SYGNALY"])
            all_map = getattr(mod, "WSZYSTKIE_SYGNALY")
            return [_from_tarzan_signal(sig) for sig in all_map.values()]
        except Exception:
            pass

    return [
        ParSignal(
            nazwa="BRAK_MAPY_SYGNALOW",
            plytka="SYSTEM",
            pin=None,
            kanal=None,
            typ="LH",
            kierunek="IN",
            default="0",
            opis="Nie znaleziono tarzanZmienneSygnalowe.py w ścieżce importu.",
            grupa="SYSTEM",
            status="BŁĄD",
            panel_port=None,
            klasa_wykonawcza="tarzanParSignalsAdapter.py",
            hardware_function="SYSTEM",
            hardware_label="IMPORT ERROR",
            conflict_group=None,
            logika_trybow="ZABRONIONY",
            rola_logiki="SYSTEM",
        )
    ]


def by_group(signals: List[ParSignal], group: str) -> List[ParSignal]:
    gu = group.upper()
    return [s for s in signals if (s.grupa or "").upper() == gu]


def contains(signals: List[ParSignal], *needles: str) -> List[ParSignal]:
    ns = [n.lower() for n in needles]
    out = []
    for s in signals:
        blob = " ".join([s.nazwa, s.opis, s.grupa, s.klasa_wykonawcza, s.hardware_label]).lower()
        if any(n in blob for n in ns):
            out.append(s)
    return out
