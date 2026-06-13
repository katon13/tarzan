# TARZAN LKS BOOT — ETAP 5: PROGRESS + FINAL CLEANUP

Etap 5 kończy porządkowanie bootu LKS po Etapach 1–4.

## Co było wcześniej

- Etap 1: inwentaryzacja bez zmian w kodzie.
- Etap 2: boot_hardware = szybkie wykrycie, boot_test = pełny test.
- Etap 3: jeden wspólny tor pełnego testu LKS_TEST_MATRIX.
- Etap 4: jeden finalny stan fizyczny po testach: F-LED OFF, LCD READY, Matrix HEART.

## Co robi Etap 5

- Porządkuje procenty paska postępu.
- boot_linux/services/hardware idą stopniowo, bez skoku na jednym procencie.
- pełny test 30 komponentów ma własny zakres 60–90%.
- final-ready outputs mają zakres 94–98%.
- READY zostaje na 100%.

## Nie rusza

- ABC / POKSYG
- pin map
- startup bytes PLAY/REC
- LCD/keypad/F-LED/Matrix funkcje niskiego poziomu
- Nextion grafiki/stron
- logiki osi i pulse engine

## Pliki

- `core/TSP/tarzanTspLksBootProgress.py`
- `core/TSP/tarzanTspServer.py` tylko spójne domyślne procenty testu ręcznego.
