# TARZAN LKS-N5 — ETAP 12: suwerenne testery sprzętu

## Cel

Ten etap zastępuje błędny kierunek „adapter do sandboxa”. LKS-N5 nie importuje i nie uruchamia `tarzanMiniPcSandbox.py` jako zależności runtime.

Sandbox był użyty tylko jako wzorzec sprawdzonych wywołań i nazw urządzeń. Produkcyjne testy są własne, czyste i znajdują się w:

```text
core/TSP/tarzanTspLksHardwareTests.py
```

## Zasada

```text
sandbox = nauczyciel / historia
LKS-N5 = własne suwerenne testery
```

## Co dodano

```text
core/TSP/tarzanTspLksHardwareTests.py
core/TSP/tarzanTspLksDiagnostics.py
core/TSP/tarzanTspLksNextion5.py
core/TSP/tarzanTspLksSandboxAdapter.py  # tylko blokada starej drogi
data/lks_n5/lks_n5_hardware_tests.example.json
```

## Testy suwerenne

Aktualnie moduł ma własne testy:

```text
pok_play       — real connect PoKeys PLAY
pok_rec        — real connect PoKeys REC/RECK
lcd_1602       — test sesji PoKeys, a po kliknięciu pisze na LCD: LKS-N5 TEST / LCD OK
matrix_led     — test sesji PoKeys, a po kliknięciu pokazuje wzór/OK na Matrix LED
f_button       — odczyt F1-F4, a po kliknięciu może czekać na naciśnięcie
f_led          — whitelist P46/P48/P50/P52, po kliknięciu mruga LED F1-F4
keypad         — odczyt MatrixKB, po kliknięciu może czekać na klawisz
light_bh1750   — odczyt BH1750 po BUS/I2C przez PoKeys
 i2c_bus        — skan BUS/I2C przez PoKeys
```

## Widoczność testu po kliknięciu

Po kliknięciu elementu `status_main`:

```text
1. Mruga tylko kliknięta kontrolka Nextion 5.
2. Testowany jest tylko wskazany komponent.
3. Jeżeli to urządzenie ma widoczny test, robi widoczny efekt:
   - LCD pokazuje tekst testowy,
   - Matrix LED pokazuje wzór,
   - LED F1-F4 mrugają,
   - przyciski/klawiatura czekają chwilę na naciśnięcie.
4. Wynik wraca na przycisk:
   OK   -> zielony
   FAIL -> szary
```

## Praca ciągła

Praca ciągła dalej jest lekka:

```text
bez pełnej diagnostyki w pętli
bez resetu status_main
bez page status_main co chwilę
bez obciążania miniPC
```

Pełniejszy widoczny test jest tylko:

```text
przy starcie — bezpieczny boot-check
po kliknięciu operatora — test punktowy
```

## Bezpieczeństwo

W module ETAPU 12 nie ma testów ruchu osi.

Zakaz pozostaje:

```text
zero STEP
zero DIR
zero ENABLE
zero ruchu osi
zero impulsów wykonawczych
zero nieznanych outputów
```

Jedyny zapis/wyjście runtime dotyczy whitelisty widocznych testów operatora:

```text
LCD PoKeys
Matrix LED PoKeys
LED F1-F4 na REC P46/P48/P50/P52
```

## Testy ręczne

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksHardwareTests --component pok_play
python3 -m core.TSP.tarzanTspLksHardwareTests --component pok_rec
python3 -m core.TSP.tarzanTspLksHardwareTests --component lcd_1602 --visible
python3 -m core.TSP.tarzanTspLksHardwareTests --component matrix_led --visible
python3 -m core.TSP.tarzanTspLksHardwareTests --component f_led --visible
python3 -m core.TSP.tarzanTspLksHardwareTests --component f_button --visible
python3 -m core.TSP.tarzanTspLksHardwareTests --component keypad --visible
python3 -m core.TSP.tarzanTspLksHardwareTests --component light_bh1750
python3 -m core.TSP.tarzanTspLksHardwareTests --component i2c_bus
```

Test przez LKS-N5 / kliknięcie:

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksDiagnostics --component lcd_1602 --print-results --print-statuses
python3 -m core.TSP.tarzanTspLksDiagnostics --component matrix_led --print-results --print-statuses
python3 -m core.TSP.tarzanTspLksDiagnostics --component f_led --print-results --print-statuses
```

## Wniosek

ETAP 12 nie podpina starego sandboxa. ETAP 12 przenosi wiedzę ze starego sandboxa do własnych testerów LKS-N5.
