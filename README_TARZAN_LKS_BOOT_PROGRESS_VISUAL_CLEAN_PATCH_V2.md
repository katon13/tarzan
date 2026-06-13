# TARZAN LKS-N5 BOOT PROGRESS VISUAL CLEAN PATCH V2

Zakres: tylko `core/TSP/tarzanTspLksBootProgress.py`.

Nie rusza:
- `core/tarzanPoKeys.py`
- `core/tarzanPokABC.py`
- `core/tarzanZmienneSygnalowe.py`
- map pinów, ABC, POKSYG
- keypad zero-based
- LCD/F-LED/Matrix LED low-level
- osie / pulse engine
- Nextion HMI / grafika / strony

Zmiany V2:
1. Po `page(...)` pasek i liczba procentów są wysyłane natychmiast, przed dłuższą serią tekstów.
   Cel: ograniczyć widoczny domyślny `0` na stronach boot_linux/services/hardware/test.
2. `matrix_led` w macierzy 30 testów nie jest już testowany jako visible frame `OK`.
   Dla `matrix_led` używamy `visible=False`, czyli ACK + serce READY.
   Cel: usunąć dwie kreski widoczne na Matrix LED.
3. Po safe-state macierzy i po final safe-state serce READY jest potwierdzane ponownie.
   Cel: nie pozwolić, żeby safe-state lub późniejsze wyjście zostawiło testową ramkę.

Test lokalny:
```powershell
cd X:\tarzan
python -m py_compile core\TSP\tarzanTspLksBootProgress.py
```

Test miniPC:
```bash
cd /opt/tarzan && git checkout -- data/logi/tsp/tsp.log && git pull origin main && python3 -m py_compile core/tarzanPoKeys.py core/tarzanPokABC.py core/tarzanZmienneSygnalowe.py core/tarzanHardwareBridge.py core/TSP/tarzanTspLks.py core/TSP/tarzanTspLksBootProgress.py core/TSP/tarzanTspLksHardwareTests.py core/TSP/tarzanTspServer.py main.py && sudo systemctl restart tarzan-tsp-lks-n5.service && journalctl -u tarzan-tsp-lks-n5.service -n 180 --no-pager -l
```
