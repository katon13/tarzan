"""
tarzan_export_signals_catalog_v2.py

Eksport katalogu sygnałów TARZAN do JSON dla formularza HTML V3.
Wersja respektuje nowe pola klasyfikacji:
- logika_trybow
- rola_logiki
- uwaga_logiki

Jeżeli sygnał ich nie posiada, skrypt stosuje bezpieczne wartości domyślne.
"""

import json
from pathlib import Path
from tarzanZmienneSygnalowe import WSZYSTKIE_SYGNALY

OUTPUT_JSON = "tarzan_signals_catalog.json"


def get_attr(obj, name, default=None):
    return getattr(obj, name, default)


def signal_to_dict(sig):
    return {
        "nazwa": get_attr(sig, "nazwa"),
        "plytka": get_attr(sig, "plytka"),
        "pin": get_attr(sig, "pin"),
        "kanal": get_attr(sig, "kanal"),
        "typ": get_attr(sig, "typ"),
        "kierunek": get_attr(sig, "kierunek"),
        "default": get_attr(sig, "default"),
        "opis": get_attr(sig, "opis"),
        "zrodlo": get_attr(sig, "zrodlo"),
        "hardware_function": get_attr(sig, "hardware_function"),
        "hardware_label": get_attr(sig, "hardware_label"),
        "pin_is_fixed": get_attr(sig, "pin_is_fixed"),
        "is_shared_pin": get_attr(sig, "is_shared_pin"),
        "conflict_group": get_attr(sig, "conflict_group"),
        "panel_port": get_attr(sig, "panel_port"),
        "grupa": get_attr(sig, "grupa"),
        "klasa_wykonawcza": get_attr(sig, "klasa_wykonawcza"),
        "status": get_attr(sig, "status"),
        "logika_trybow": get_attr(sig, "logika_trybow", "DOZWOLONY"),
        "rola_logiki": get_attr(sig, "rola_logiki", ""),
        "uwaga_logiki": get_attr(sig, "uwaga_logiki", ""),
    }


def main():
    data = [signal_to_dict(sig) for sig in WSZYSTKIE_SYGNALY.values()]
    data.sort(key=lambda x: (
        x["plytka"] or "",
        x["grupa"] or "",
        x["logika_trybow"] or "",
        x["nazwa"] or ""
    ))
    Path(OUTPUT_JSON).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Zapisano {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
