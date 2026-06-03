# TARZAN LKS-N5 — ETAP 6: Diagnostyka podzespołów

Zakres etapu: dodanie bezpiecznej diagnostyki podzespołów dla `status_main`.

## Pliki

```text
core/TSP/tarzanTspLksDiagnostics.py
core/TSP/tarzanTspLksNextion5.py
```

## Kontrakt bezpieczeństwa

Automatyczna diagnostyka jest tylko read-only / presence-check.

Zakaz nadal obowiązuje:

```text
zero STEP
zero DIR
zero ENABLE
zero ruchu osi
zero impulsów wykonawczych
zero nieznanych outputów
```

## Co sprawdza etap 6

```text
linux_sys       — Python, TSP, LKS-TTY
snajper_sys     — warstwa sygnałów/Snajper import
pok_play        — obecność PoKeys lib/module
pok_rec         — obecność PoKeys lib/module
lcd_1602        — ścieżka komunikacji I2C
matrix_led      — ścieżka komunikacji I2C
keypad          — ścieżka komunikacji I2C
light_bh1750    — ścieżka komunikacji I2C
level_xyz       — ścieżka komunikacji I2C
shock_alarm     — ścieżka komunikacji I2C
light_laser     — ścieżka magistrali
f_button        — ścieżka odczytu GPIO/sysfs
f_led           — tylko whitelist/presence, bez przełączania wyjść
kranc           — ścieżka odczytu krańcówek
cam_main        — /dev/video*
cam_track       — drugie /dev/video*
take_sys        — katalog TAKE
par_sys         — katalog PAR
ehr_sys         — katalog EHR
osie/SOK/RRP/N7 — tylko ślady konfiguracji/modułów, bez sterowania
```

`i2c_bus` jest agregatem wymaganych urządzeń magistrali. Dostaje `1` dopiero wtedy,
gdy wymagane elementy z mapy mają `OK`.

## Test suchy

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --diagnostics --print-results
```

## Test fizyczny

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksNextion5 --port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 --baudrate 9600 --diagnostics --print-results
```

## Wynik etapu

Nextion 5 przechodzi na `status_main`, resetuje kontrolki i zapala te, które przeszły bezpieczną diagnostykę.
