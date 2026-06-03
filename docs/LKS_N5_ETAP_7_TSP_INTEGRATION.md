# TARZAN LKS-N5 — ETAP 7 — integracja z TSP/LKS

## Zakres

Podpięto LKS-N5 jako opcjonalne, równoległe wyjście istniejącego `TarzanTspServer`.

LKS-TTY zostaje bez zmian. LKS-N5 nie zastępuje `TarzanTspLks`.

## Zmienione pliki

```text
core/TSP/tarzanTspServer.py
core/TSP/tarzanTsp.py
docs/LKS_N5_ETAP_7_TSP_INTEGRATION.md
```

## Nowe argumenty serwera

```bash
--lks-n5
--lks-n5-port /dev/serial/by-id/...
--lks-n5-baudrate 9600
--lks-n5-dry-run
--lks-n5-refresh 2.0
```

## Zasady bezpieczeństwa

- błąd Nextiona 5 nie zatrzymuje TSP,
- LKS-TTY nadal działa,
- FAST/Snajper nie odświeża Nextiona przy każdym pakiecie,
- cykliczny refresh LKS-N5 jest lekki,
- URGENT/ERROR/connect/disconnect mogą odświeżyć natychmiast,
- brak STEP, DIR, ENABLE i ruchu osi.

## Test suchy

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTsp server --host 127.0.0.1 --port 17777 --no-lks --lks-n5 --lks-n5-dry-run --lks-n5-refresh 1
```

W drugim terminalu można sprawdzić klienta:

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTsp client --host 127.0.0.1 --port 17777 --smoke
```

## Test fizyczny

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTsp server \
  --host 0.0.0.0 \
  --port 7777 \
  --lks \
  --lks-n5 \
  --lks-n5-port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 \
  --lks-n5-baudrate 9600 \
  --lks-n5-refresh 2
```

## Status

ETAP 7 jest gotowy do testu na miniPC.
