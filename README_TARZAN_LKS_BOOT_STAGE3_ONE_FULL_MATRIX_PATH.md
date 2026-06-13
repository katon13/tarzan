# TARZAN LKS BOOT — ETAP 3: jeden tor pełnego testu LKS

## Etap 1 — inwentaryzacja
Ustalono, że start LKS ma kilka torów testów: BootProgress, TspServer, HardwareBridge i TarzanPoKeys. Sprzęt działa, ale boot jest dublowany.

## Etap 2 — szybkie wykrycie vs pełny test
`boot_hardware` ma robić tylko szybki detect. Pełny test 30 komponentów zostaje w `boot_test`.

## Etap 3 — ten patch
Tworzy jeden wspólny helper pełnego testu:

`run_lks_full_matrix_via_bridge()` w `core/TSP/tarzanTspLksHardwareTests.py`

Następnie:
- `tarzanTspLksBootProgress.py` używa tego helpera w `boot_test`,
- `tarzanTspServer.py` używa tego samego helpera w diagnostyce ręcznej,
- kolejność komponentów, agregat `i2c_bus` i `safe-state` są wspólne.

Nie rusza:
- ABC,
- POKSYG,
- map pinów,
- LCD,
- keypad,
- F-LED,
- Matrix LED wzoru,
- startup bytes PoKeys.
