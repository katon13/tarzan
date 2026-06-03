# TARZAN LKS-N5 — ETAP 10: realne testery urządzeń

## Cel

ETAP 10 domyka lukę po ETAPIE 9: diagnostyka nie może już zapalać kontrolek na podstawie samego markera repo, eksportu HMI albo przypuszczenia.

Źródłem wejściowym jest:

```text
data/lks_n5/lks_n5_hardware_inventory.json
```

Opcjonalnie można dodać:

```text
data/lks_n5/lks_n5_hardware_requirements.json
```

na podstawie przykładu:

```text
data/lks_n5/lks_n5_hardware_requirements.example.json
```

## Zasada ETAPU 10

```text
PRESENT + realny test OK      -> zielony
MISSING                       -> szary
UNKNOWN                       -> szary
repo marker only              -> szary
brak adresu/ścieżki testowej  -> szary
```

## Co zmieniono

```text
core/TSP/tarzanTspLksDiagnostics.py
core/TSP/tarzanTspLksBootCheck.py
data/lks_n5/lks_n5_hardware_requirements.example.json
```

## Diagnostyka PoKeys

PoKeys nie jest już zapalany tylko przez obecność biblioteki.

Wymagane jest realne wykrycie USB z `lsusb`:

```text
PoLabs PLAYER -> pok_play
PoLabs RECK / REC -> pok_rec
```

## Diagnostyka I2C / magistrali

Jeżeli nie ma `/dev/i2c-*`, wszystkie elementy magistrali są szare:

```text
lcd_1602
matrix_led
keypad
light_bh1750
level_xyz
shock_alarm
light_laser
i2c_bus
```

Jeżeli `/dev/i2c-*` istnieje, zielone pojawi się dopiero po wpisaniu realnych adresów w `lks_n5_hardware_requirements.json` i potwierdzeniu ich w skanie.

## PAR / EHR / RRP / osie / SOK

Repo marker nie wystarcza.

```text
PAR/EHR/RRP -> wymagany runtime/heartbeat
osie/SOK    -> wymagany read-only driver status path albo późniejsze API statusu
```

Bez tego kontrolka zostaje szara.

## Boot-check

`tarzanTspLksBootCheck.py` używa teraz realnej diagnostyki ETAPU 10 do końcowego `status_main`.

Plansza `boot_test` pokazuje wynik realnych testerów, a nie wcześniejsze `WAIT` / `ETAP 5 no outputs`.

## Bezpieczeństwo

Nadal obowiązuje:

```text
zero STEP
zero DIR
zero ENABLE
zero ruchu osi
zero nieznanych outputów
```

## Testy

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksDiagnostics --print-results --print-statuses
python3 -m core.TSP.tarzanTspLksDiagnostics --component pok_play --print-results --print-statuses
python3 -m core.TSP.tarzanTspLksDiagnostics --component i2c_bus --print-results --print-statuses
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --boot-check
```

Test fizyczny:

```bash
python3 -m core.TSP.tarzanTspLksNextion5 --port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 --baudrate 9600 --boot-check
```

## Oczekiwanie po obecnej inwentaryzacji miniPC

Po obecnym ETAPIE 9 spodziewany wynik jest konserwatywny:

```text
zielone: linux_sys, snajper_sys, pok_play, pok_rec, take_sys
szare: i2c_bus, next_7, kamery, PAR/EHR runtime, RRP, osie, SOK, I/O bez mapowania
```

Jeżeli później podłączysz I2C, kamery albo Nextion 7 do miniPC, najpierw ponownie uruchamiasz ETAP 9, a potem ETAP 10 pokaże nowe zielone statusy tylko wtedy, gdy są realnie potwierdzone.
