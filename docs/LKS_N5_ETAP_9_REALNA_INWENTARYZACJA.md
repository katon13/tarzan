# LKS-N5 — ETAP 9: realna inwentaryzacja sprzętu miniPC

## Cel

Ten etap nie domyka jeszcze pełnej diagnostyki. Jego celem jest ustalenie prawdy o realnym miniPC i sprzęcie, żeby ETAP 10 nie zgadywał.

Dotychczasowy tor LKS-N5 działał technicznie, ale część statusów była oparta na miękkich markerach repo albo ogólnej obecności magistrali. To nie wystarcza do `lks-n5-full-v1`.

## Nowy plik

```text
core/TSP/tarzanTspLksInventory.py
```

## Plik wynikowy na miniPC

```text
data/lks_n5/lks_n5_hardware_inventory.json
```

## Co zbiera ETAP 9

```text
Linux/Python/repo
systemd: ssh.service / sshd.service / tarzan-tsp-lks-n5.service
proces TSP
network links
system time
/dev/serial/by-id
/dev/ttyUSB* / /dev/ttyACM*
Nextion 5 CP2102 candidate
Nextion 7 serial candidates
lsusb
/dev/i2c-*
i2cdetect, jeśli dostępny
/dev/video*
v4l2-ctl, jeśli dostępny
markery repo: PAR/EHR/RRP/SOK/axis/PoKeys
konserwatywną tabelę komponentów status_main
```

## Czego ETAP 9 nie robi

```text
nie wysyła STEP
nie wysyła DIR
nie wysyła ENABLE
nie porusza osi
nie zapala wyjść
nie udaje zielonego statusu
nie wpisuje OK, jeśli jest tylko podejrzenie
```

## Zasada wyniku

Statusy inwentaryzacji:

```text
present — realnie znalezione
missing — realnie brak
unknown — kandydat / marker / wymaga mapowania
error   — błąd podczas odczytu
```

`unknown` jest poprawnym wynikiem ETAPU 9. To oznacza: wykryliśmy ślad, ale jeszcze nie wolno zapalić kontrolki na zielono.

## Komenda testowa

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksInventory --self-test --print
```

## Komenda zapisu inwentaryzacji

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksInventory --write data/lks_n5/lks_n5_hardware_inventory.json --print
```

## Następny etap

ETAP 10 ma użyć wyniku ETAPU 9 do prawdziwych testerów:

```text
check_pokeys_play()
check_pokeys_rec()
check_nextion7()
check_i2c_bus()
check_lcd_1602()
check_matrix_led()
check_keypad()
check_bh1750()
check_level_xyz()
check_shock_alarm()
check_cam_main()
check_cam_track()
check_par()
check_ehr()
```

W ETAPIE 10 zielone statusy mają wynikać z realnego testu albo jawnej konfiguracji, nie z samej obecności pliku w repo.
