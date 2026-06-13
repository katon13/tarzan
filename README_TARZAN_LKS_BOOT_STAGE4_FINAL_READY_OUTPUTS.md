# TARZAN LKS BOOT — ETAP 4: FINAL READY OUTPUTS

Etap 4 porządkuje końcówkę bootu bez zmiany ABC/POKSYG/map pinów.

Po pełnym teście LKS i safe-state wykonywany jest jeden ostatni stan fizyczny:
- F-LED OFF,
- LCD PLAY/REC = GOTOWE,
- Matrix LED = HEART READY, wariant B potwierdzony fizycznie.

Zmiany:
- `core/tarzanPoKeys.py` — dodaje `matrix_led_ready_heart_once()`, jeśli brak.
- `core/tarzanHardwareBridge.py` — dodaje `apply_lks_final_ready_outputs()`.
- `core/TSP/tarzanTspLksBootProgress.py` — wywołuje final-ready przed `ready_main`.

Nie rusza:
- ABC,
- PoKeys startup bytes,
- POKSYG,
- map pinów,
- osi / Pulse Engine,
- pełnego testu 30 komponentów z Etapu 3.
