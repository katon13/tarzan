# TARZAN LKS-N5 — ETAP 4: mapa kontrolek status_main

## Zakres

Etap 4 dodaje jeden plik prawdy dla nazw kontrolek strony `status_main`:

```text
core/TSP/tarzanTspLksStatusMap.py
```

## Kontrakt ON/OFF

```text
.val=0 = OFF / brak potwierdzenia / błąd / szary
.val=1 = ON / test OK / zielony
```

## Co zostało dodane

```text
LKS_STATUS_COMPONENTS
GROUP_SYSTEM
GROUP_POKEYS
GROUP_BUS
GROUP_IO
GROUP_CAMERA
GROUP_AXIS
GROUP_SOK
REQUIRED_BUS_DEVICES
all_components()
validate_component()
group_components()
validate_many()
empty_statuses()
bus_ok_from_statuses()
```

## Co zostało zmienione

`core/TSP/tarzanTspLksNextion5.py` nie używa już lokalnej, tymczasowej listy kontrolek.
`set_status()` i `reset_status_main()` idą przez centralną mapę.

## Czego nie ruszamy

```text
PAR
Nextion 7
EHR / KHR / KRO
Snajper
ruch osi
STEP / DIR / ENABLE
```

## Testy

```bash
python3 -m py_compile core/TSP/tarzanTspLksStatusMap.py core/TSP/tarzanTspLksNextion5.py
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --test-scenes
```

Na fizycznym Nextion 5 po `--test-scenes` końcowy stan `status_main`:

```text
ZIELONE:
linux_sys
pok_play
pok_rec
i2c_bus
take_sys

SZARE:
cała reszta
```

## Wynik

Nazwy kontrolek `status_main` są od teraz trzymane centralnie i gotowe pod ETAP 5/6:

```text
boot-check
diagnostyka podzespołów
agregacja i2c_bus
```
