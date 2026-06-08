import json
import sys
import os
from pathlib import Path

# Dodaj ścieżkę do projektu
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from core.tarzanZmienneSygnalowe import WSZYSTKIE_SYGNALY

def update_json():
    catalog_path = ROOT_DIR / "tarzan_signals_catalog.json"
    print(f"Updating catalog: {catalog_path}")
    
    signals_list = []
    for name, sig in WSZYSTKIE_SYGNALY.items():
        # Konwersja obiektu TarzanSygnal na słownik
        d = {
            "nazwa": sig.nazwa,
            "plytka": sig.plytka,
            "pin": sig.pin,
            "kanal": sig.kanal,
            "typ": sig.typ,
            "kierunek": sig.kierunek,
            "default": sig.default,
            "opis": sig.opis,
            "zrodlo": sig.zrodlo,
            "hardware_function": sig.hardware_function,
            "hardware_label": sig.hardware_label,
            "pin_is_fixed": sig.pin_is_fixed,
            "is_shared_pin": sig.is_shared_pin,
            "conflict_group": sig.conflict_group,
            "panel_port": sig.panel_port,
            "grupa": sig.grupa,
            "klasa_wykonawcza": sig.klasa_wykonawcza,
            "status": "AKTYWNY"
        }
        # Dodanie pól opcjonalnych z SignalBus meta jeśli istnieją
        if hasattr(sig, 'kanoniczna_nazwa'):
            d["kanoniczna_nazwa"] = sig.kanoniczna_nazwa
            
        signals_list.append(d)
        
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(signals_list, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully exported {len(signals_list)} signals to JSON.")

if __name__ == "__main__":
    update_json()
