# TARZAN LKS BOOT — ETAP 2: szybkie wykrycie vs pełny test

Zakres:
- zmienia tylko `core/TSP/tarzanTspLksBootProgress.py`,
- `boot_hardware` robi szybkie wykrycie, bez głębokich testów komponentów,
- `boot_test` zostaje jedynym miejscem pełnego testu 30 komponentów,
- nie rusza ABC, POKSYG, map pinów, LCD, keypad, F-LED, Matrix LED ani PoKeys startup bytes.

Najważniejsze:
- `boot_hardware` nie woła już `HardwareBridge.test_lks_component()` dla PoKeys/I2C/BH1750/light_laser,
- szybkie detekcje w `boot_hardware` nie ustawiają statusów ikon `status_main`,
- statusy ikon ustawia dopiero pełna macierz testów w `boot_test`.
