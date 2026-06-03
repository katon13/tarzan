# TARZAN LKS-N5 — ETAP 13 — realny boot progress Linux/systemd

## Cel

`boot_loading` na Nextion 5 nie może udawać prawdziwego ładowania Linuxa. Nextion startuje wcześniej niż miniPC i do chwili uruchomienia usługi systemd może tylko czekać.

Od momentu startu usługi `tarzan-tsp-lks-n5.service` ekran przejmuje Linux i pokazuje realne kroki:

```text
10%  Linux alive
20%  repo OK
30%  czas systemowy
40%  sieć
50%  SSH
58%  TSP module
62%  LKS-TTY
68%  LKS-N5 serial
74%  PoKeys USB
78%  Nextion 7 mapping
82%  I2C nodes
86%  video nodes
94%  real diagnostics
100% status_main
```

## Zasada

Nie ma już paska „na oko” po starcie usługi. Każdy procent jest wynikiem realnego kroku.

Przed startem usługi:

```text
Nextion sam pokazuje boot_intro / boot_loading
Linux jeszcze nie mówi do ekranu
```

Po starcie usługi:

```text
Linux przejmuje ekran
miniPC sprawdza kroki
Nextion pokazuje realny postęp
na końcu status_main pokazuje realne stany
```

## Pliki

```text
core/TSP/tarzanTspLksBootProgress.py
core/TSP/tarzanTspLksBootCheck.py
core/TSP/tarzanTspServer.py
```

## Bezpieczeństwo

ETAP 13 nie rusza osi i nie wysyła:

```text
STEP
DIR
ENABLE
Pulse Engine
homing
ruchu ramienia
ruchu kamery
```

## Praca ciągła

Po starcie systemu pełna diagnostyka nie działa w pętli. LKS-N5 pozostaje spokojny:

```text
brak mrugania całej tablicy
brak resetu status_main co cykl
zmieniają się tylko elementy, których stan realnie się zmienił
pełniejszy test pojedynczego elementu działa po kliknięciu przycisku status_main
```

## Test

```bash
cd /opt/tarzan
python3 -m py_compile core/TSP/tarzanTspLksBootProgress.py core/TSP/tarzanTspLksBootCheck.py core/TSP/tarzanTspServer.py
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --boot-check
python3 -m core.TSP.tarzanTspLksNextion5 --port /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 --baudrate 9600 --boot-check
sudo systemctl restart tarzan-tsp-lks-n5.service
journalctl -u tarzan-tsp-lks-n5.service -n 80 --no-pager -l
```

## Wynik akceptacyjny

Na Nextion 5 po restarcie usługi ma być widoczne przejście:

```text
boot_linux / SERVICES / HARDWARE / DEVICE TEST / status_main
```

Pasek `j_progress` i `n_progress` zmieniają się po kolejnych realnych krokach. Jeżeli coś nie istnieje, status pozostaje OFF/szary. Nie zgadujemy.
