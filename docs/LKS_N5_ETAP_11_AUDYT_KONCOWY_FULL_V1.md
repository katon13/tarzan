# TARZAN LKS-N5 — ETAP 11: audyt końcowy i tag `lks-n5-full-v1`

## Cel

ETAP 11 nie dodaje nowej diagnostyki sprzętu. Domyka v1 formalnie:

```text
1. sprawdza, czy wszystkie moduły LKS-N5 istnieją i importują się poprawnie,
2. sprawdza, czy inwentaryzacja ETAPU 9 jest zapisana,
3. uruchamia realną konserwatywną diagnostykę ETAPU 10,
4. sprawdza obecność systemd unit,
5. sprawdza usługę systemd na miniPC,
6. usuwa ostrzeżenie RuntimeWarning przy `python -m core.TSP.tarzanTspLksNextion5`,
7. potwierdza API punktowej diagnostyki z przycisków `status_main`,
8. zapisuje raport audytu.
```

## Co zmieniono

```text
core/TSP/__init__.py
core/TSP/tarzanTspLksAudit.py
docs/LKS_N5_ETAP_11_AUDYT_KONCOWY_FULL_V1.md
```

## Dlaczego zmieniono `core/TSP/__init__.py`

Pakiet `core.TSP` importował serwer TSP już na etapie importu pakietu. Serwer importował LKS-N5, więc uruchomienie:

```bash
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --boot-check
```

mogło pokazać ostrzeżenie `RuntimeWarning`, że moduł został znaleziony w `sys.modules` przed właściwym wykonaniem. Po zmianie importy klas TSP są leniwe przez `__getattr__`.

## Test audytu

```bash
cd /opt/tarzan
python3 -m py_compile core/TSP/__init__.py core/TSP/tarzanTspLksAudit.py
python3 -m core.TSP.tarzanTspLksAudit --print --write data/lks_n5/lks_n5_v1_audit_report.json
```

Jeżeli audyt przejdzie:

```text
OK LKS-N5 AUDIT
```

można zrobić tag końcowy:

```bash
git tag lks-n5-full-v1
git push origin lks-n5-full-v1
```

## Ważna interpretacja v1

`lks-n5-full-v1` nie oznacza „wszystkie kontrolki zielone”. Oznacza:

```text
LKS-N5 pokazuje prawdę.
```

Jeżeli miniPC nie widzi `/dev/i2c-*`, kamer albo Nextion 7, kontrolki pozostają szare. To jest poprawne zachowanie v1.

## Kontrakt końcowy

```text
miniPC diagnozuje
Nextion 5 pokazuje wynik
LKS-TTY zostaje
LKS-N5 działa równolegle
pełna diagnostyka przy starcie albo na klik operatora
praca ciągła spokojna, bez mrugania i bez ciężkiej pętli
kliknięty element może mrugać tylko podczas testu punktowego
OK wraca na zielono
FAIL/OFF wraca na szaro
zero STEP
zero DIR
zero ENABLE
zero ruchu osi
```

## Po ETAPIE 11

Dalszy rozwój nie powinien już być „etapami LKS-N5 v1”, tylko dopinaniem konkretnych realnych wejść:

```text
- podpięcie I2C na miniPC,
- jawne mapowanie Nextion 7,
- kamery /dev/video*,
- heartbeat PAR/EHR,
- read-only status osi i SOK,
- konfiguracja realnych adresów w data/lks_n5/lks_n5_hardware_requirements.json.
```
