# TARZAN LKS-N5 — ETAP 2: serial device

## Zakres

Wykonano etap 2 z dokumentacji LKS-N5: niski poziom komunikacji `miniPC → Nextion 5`.

Dodany plik:

```text
hardware/tarzanNextion/lks_n5_device.py
```

## Co robi plik

```text
otwiera port serial
wysyła komendy Nextion z terminatorem FF FF FF
obsługuje page()
obsługuje txt()
obsługuje val()
obsługuje vis()
obsługuje bkcmd()
czyta eventy z Nextiona
trzyma last_tx / last_rx / last_error
ma tryb dry-run do testu bez sprzętu
```

## Czego nie robi

```text
nie diagnozuje sprzętu
nie steruje ruchem
nie wysyła STEP
nie wysyła DIR
nie wysyła ENABLE
nie rusza osi
nie zna PAR / EHR / Snajpera
```

## Test bez sprzętu

```bash
cd /opt/tarzan
python3 -m hardware.tarzanNextion.lks_n5_device --dry-run --test
```

## Test fizyczny na miniPC

```bash
cd /opt/tarzan
ls -l /dev/serial/by-id/
python3 -m hardware.tarzanNextion.lks_n5_device --port /dev/serial/by-id/TARZAN_NEXTION5 --baudrate 9600 --test
```

## Komendy wysyłane w teście

```text
bkcmd=3
page boot_linux
t_title.txt="LINUX OK"
t_line1.txt="TEST FROM MINI PC"
t_line2.txt="NEXTION 5 ONLINE"
t_status.txt="LKS-N5 SERIAL OK"
```

## Status

```text
ETAP 2 — Niski poziom komunikacji z Nextion 5: WYKONANY
```

## Tag roboczy

```text
lks-n5-etap-2-serial-device
```
