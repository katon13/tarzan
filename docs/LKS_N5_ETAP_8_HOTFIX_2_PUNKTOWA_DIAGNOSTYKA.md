# TARZAN LKS-N5 — ETAP 8 HOTFIX 2: spokojna praca i diagnostyka punktowa

## Cel

LKS-N5 nie może mrugać ani wykonywać pełnej diagnostyki w krótkiej pętli.
Pełny test jest potrzebny przy starcie systemu oraz na żądanie operatora.

## Nowa zasada pracy

1. Przy starcie: boot-check i bezpieczna diagnostyka startowa.
2. W pracy ciągłej: spokojny status, bez resetowania `status_main` i bez pełnego skanowania podzespołów.
3. Kliknięcie kontrolki `status_main`: test tylko wskazanego ogniwa.
4. Podczas testu punktowego mruga tylko kliknięty element.
5. Wynik testu:
   - OK: `.val=1`, czyli zielony,
   - FAIL/OFF/brak potwierdzenia: `.val=0`, czyli szary.

## Ważne wymaganie HMI

Przyciski `status_main` muszą wysyłać ID komponentu do miniPC.
W Nextion Editor dla 30 przycisków Dual-state Button na `status_main` ustaw:

```text
Send Component ID = enabled
```

Alternatywnie można w Touch Release Event wysłać event `0x65`, ale najprościej
włączyć `Send Component ID`. Eksport tekstowy `hardware/Nextion_structure_5/status_main.txt`
został ustawiony na `enabled`, ale fizyczny panel wymaga ponownego wgrania HMI/TFT,
jeżeli obecnie ma `disabled`.

## Obsługiwany event

Kod obsługuje standardowy event Nextion:

```text
0x65 page_id component_id touch_event FF FF FF
```

Test uruchamia się tylko na `touch_event=1` — release.

## Pliki

- `core/TSP/tarzanTspServer.py`
- `core/TSP/tarzanTspLksNextion5.py`
- `core/TSP/tarzanTspLksDiagnostics.py`
- `core/TSP/tarzanTspLksStatusMap.py`
- `hardware/Nextion_structure_5/status_main.txt`

## Zakazy

Nadal obowiązuje:

```text
zero STEP
zero DIR
zero ENABLE
zero ruchu osi
zero pełnej diagnostyki w pętli
zero resetowania całego status_main co cykl
```
