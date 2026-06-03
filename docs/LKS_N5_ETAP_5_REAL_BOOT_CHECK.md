# TARZAN LKS-N5 — ETAP 5: realny boot-check miniPC

## Zakres

Dodano bezpieczną sekwencję startową LKS-N5:

```text
core/TSP/tarzanTspLksBootCheck.py
```

oraz wejście CLI w:

```text
core/TSP/tarzanTspLksNextion5.py --boot-check
```

## Kontrakt bezpieczeństwa

Ten etap nie rusza osi i nie steruje wyjściami wykonawczymi.

Zakazane i niewykonywane:

```text
STEP
DIR
ENABLE
ruch osi
CNC impulse
nieznane outputy
```

## Co robi ETAP 5

Sekwencja:

```text
bkcmd=3
boot_linux
boot_services
boot_hardware
boot_test
status_main
```

Sprawdzenia są tylko obecnościowe / read-only:

```text
Python runtime
TSP module
LKS-TTY module
SSH service — informacyjnie
katalog TAKE
katalog PAR
katalog EHR
/dev/serial/by-id
/dev/ttyUSB* /dev/ttyACM*
/dev/i2c-*
obecność plików/modułów PoKeys
```

Elementy wymagające pełnej diagnostyki sprzętowej pozostają `WAIT/OFF` do ETAPU 6.

## Test suchy

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --boot-check
```

albo bezpośrednio:

```bash
python3 -m core.TSP.tarzanTspLksBootCheck --dry-run
```

## Test fizyczny

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksNextion5 \
  --port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 \
  --baudrate 9600 \
  --boot-check
```

## Oczekiwany wynik

Nextion 5 przechodzi przez realne plansze:

```text
boot_linux
boot_services
boot_hardware
boot_test
status_main
```

Na `status_main` zapalają się tylko statusy potwierdzone przez bezpieczne testy.
Pełne zapalanie urządzeń magistrali i podzespołów będzie w ETAPIE 6.

## Tag

```text
lks-n5-etap-5-real-boot-check
```
