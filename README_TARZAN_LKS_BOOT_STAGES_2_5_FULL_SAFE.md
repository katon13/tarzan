# TARZAN LKS BOOT — FULL SAFE CLEANUP ETAPY 2–5

Ta paczka jest scalona: zawiera Etap 2, 3, 4, 5 oraz dodatkowy bezpiecznik F-LED/LCD.

## Zakres

- Etap 2: `boot_hardware` = szybkie wykrycie, `boot_test` = pełny test.
- Etap 3: jeden wspólny tor pełnego testu LKS_TEST_MATRIX.
- Etap 4: jeden końcowy stan fizyczny po testach.
- Etap 5: logiczne procenty paska postępu.
- Bezpiecznik: F-LED kończą test z OFF=1.
- Bezpiecznik: LCD nie pokazuje fałszywego `BEZ BLEDOW`; pokazuje neutralnie `LKS GOTOWE / STATUS NA N5`.

## Nie rusza

- ABC / POKSYG
- `core/tarzanPokABC.py`
- `core/tarzanZmienneSygnalowe.py`
- startup bytes PLAY/REC
- mapy pinów
- Nextion grafiki i nazwy stron
- osie / pulse engine / ruch fizyczny

## Główne pliki zmieniane

- `core/TSP/tarzanTspLksBootProgress.py`
- `core/TSP/tarzanTspLksHardwareTests.py`
- `core/TSP/tarzanTspServer.py`
- `core/tarzanHardwareBridge.py`
- `core/tarzanPoKeys.py`

## Uruchomienie

```powershell
python tools\patch_tarzan_lks_boot_stages_2_5_full_safe.py
```


## V2 CHECK
Skrypt scalony jest idempotentny: pomija etap, jeżeli jego znaczniki są już w repo. Nie rusza ABC, POKSYG ani mapy pinów.


## V4 dodatkowa kontrola

- Matrix LED po teście nie kończy pustą ramką `[0]*8`, tylko wraca do serca READY.
- To zabezpiecza przed powrotem do dwóch kresek/kropek po późniejszym teście punktowym.
