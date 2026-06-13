# TARZAN_LKS_BOOT_PROGRESS_VISUAL_CLEAN_PATCH

Zakres patcha: tylko warstwa boot/progress LKS-N5.

Zmieniony plik:

```text
core/TSP/tarzanTspLksBootProgress.py
```

Nie zmieniano:

```text
core/tarzanPoKeys.py
core/tarzanPokABC.py
core/tarzanZmienneSygnalowe.py
map pinów
ABC / POKSYG
startup bytes PLAY/REC
keypad zero-based
LCD low-level
F-LED low-level
Matrix LED low-level
osie / pulse engine
Nextion HMI / grafika / strony
```

## Co poprawia patch

1. Porządkuje zakres procentów bootu:
   - Linux / repo / czas: 0-20%
   - usługi: 20-35%
   - szybkie wykrycie hardware: 35-50%
   - pełna macierz 30 testów: 50-90%
   - safe-state: 90-96%
   - final-ready outputs: 96-99%
   - ready/status: 100%

2. Przenosi pełne testy urządzeń do `boot_test`, bez wykonywania pełnych testów I2C/BH1750/light_laser w `boot_hardware`.

3. Po teście `matrix_led` od razu przywraca serce READY, żeby nie zostawały kreski testowe.

4. Po safe-state ustawia finalny stan pokazowy:
   - LCD: `LKS GOTOWE` / `STATUS NA N5`
   - Matrix LED: serce READY
   - F-LED: OFF przez istniejącą metodę `set_f_leds_off_once()`

5. Nie uruchamia ponownego testu LCD jako finalnego refreshu. Finalny LCD to neutralny zapis gotowości, nie test.

## Testy wykonane lokalnie w sandboxie

```bash
python3 -m py_compile core/tarzanPoKeys.py core/tarzanPokABC.py core/tarzanZmienneSygnalowe.py core/tarzanHardwareBridge.py core/TSP/tarzanTspLks.py core/TSP/tarzanTspLksBootProgress.py core/TSP/tarzanTspLksHardwareTests.py core/TSP/tarzanTspServer.py main.py
```

Wykonano kontrolę kontraktu metod:

```bash
grep -R --exclude='*.pyc' "configure_play_keypad_4x3_api_only_once\|matrix_led_ready_heart_once\|set_f_leds_off_once\|test_matrix_led_once\|apply_lks_test_safe_state" -n core main.py
```

Metoda `configure_play_keypad_4x3_api_only_once()` nadal istnieje w `core/tarzanPoKeys.py`. Patch jej nie dotyka.

## Wdrożenie

PACZ:

```powershell
Expand-Archive -Path "X:\patch\TARZAN_LKS_BOOT_PROGRESS_VISUAL_CLEAN_PATCH.zip" -DestinationPath "X:\tarzan" -Force
```

GIT STACJA:

```powershell
cd X:\tarzan
git status
git add core\TSP\tarzanTspLksBootProgress.py README_TARZAN_LKS_BOOT_PROGRESS_VISUAL_CLEAN_PATCH.md
git commit -m "Clean LKS N5 boot progress visual order"
git push origin main
```

GIT miniPC:

```bash
cd /opt/tarzan && git checkout -- data/logi/tsp/tsp.log && git pull origin main && python3 -m py_compile core/tarzanPoKeys.py core/tarzanPokABC.py core/tarzanZmienneSygnalowe.py core/tarzanHardwareBridge.py core/TSP/tarzanTspLks.py core/TSP/tarzanTspLksBootProgress.py core/TSP/tarzanTspLksHardwareTests.py core/TSP/tarzanTspServer.py main.py && sudo systemctl restart tarzan-tsp-lks-n5.service && journalctl -u tarzan-tsp-lks-n5.service -n 180 --no-pager -l
```

Kontrola logu:

```bash
journalctl -u tarzan-tsp-lks-n5.service -b --no-pager -l | grep -Ei "Traceback|AttributeError|HardwareBridge|matrix_led|FINAL MATRIX|FINAL READY|TARZAN SYSTEM IS READY|ERROR"
```
