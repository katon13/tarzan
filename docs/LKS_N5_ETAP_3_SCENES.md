# TARZAN LKS-N5 — ETAP 3: warstwa scen Nextion 5

## Zakres

Wykonano etap 3 z dokumentacji LKS-N5: warstwa scen, czyli mapowanie znaczeń LKS na strony i pola Nextion 5.

Dodane pliki:

```text
core/TSP/tarzanTspLksMessages.py
core/TSP/tarzanTspLksNextion5.py
```

## Co robi `tarzanTspLksMessages.py`

```text
trzyma nazwy scen / stron HMI
trzyma poziomy OK / INFO / WARN / ERROR
trzyma kody błędów i ostrzeżeń
trzyma stałe postępu bootu
```

## Co robi `tarzanTspLksNextion5.py`

```text
show_boot_linux()
show_services()
show_hardware()
show_test()
show_ready()
show_status()
show_warn()
show_error()
show_take()
set_status(component, bool)
set_many_statuses(dict)
reset_status_main()
```

## Czego nie robi

```text
nie diagnozuje sprzętu
nie uruchamia osi
nie wysyła STEP
nie wysyła DIR
nie wysyła ENABLE
nie zastępuje PAR
nie odświeża po każdym pakiecie FAST/Snajper
```

## Test suchy

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --test-scenes
```

## Test fizyczny na miniPC

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksNextion5 --port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 --baudrate 9600 --test-scenes
```

## Test pojedynczej sceny

```bash
python3 -m core.TSP.tarzanTspLksNextion5 --port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 --baudrate 9600 --scene status --reset-status
python3 -m core.TSP.tarzanTspLksNextion5 --port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 --baudrate 9600 --scene status --set linux_sys=1 --set pok_play=1 --set pok_rec=1
```

## Status

```text
ETAP 3 — Warstwa scen LKS-N5: WYKONANY
```

## Tag roboczy

```text
lks-n5-etap-3-scenes
```
