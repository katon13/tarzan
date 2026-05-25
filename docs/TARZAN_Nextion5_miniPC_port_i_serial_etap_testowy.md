# TARZAN — etap testowy Nextion 5 na tarzanMiniPC

Data: 2026-05-25  
Zakres: tylko aktualnie podłączony **Nextion 5** na `tarzanMiniPC`.

---

## 1. Zakres tego etapu

Ten etap dotyczy wyłącznie jednego urządzenia:

```text
Nextion 5
podłączony do tarzanMiniPC
przez konwerter USB-UART Silicon Labs CP2102
```

Nie dotyczy:

```text
Nextion 7
Snajpera
Bridge runtime
PAR UI
TSP
PoKeys
czujników
pełnej konfiguracji systemu
```

Na tym etapie jesteśmy jeszcze w fazie testów i podłączania urządzeń. Nie wychodzimy przed szereg.

---

## 2. Co zostało ustalone

Na `tarzanMiniPC` wykonano skan portów:

```bash
ls -l /dev/serial/by-id/ || true
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
dmesg | grep -iE "ttyUSB|ttyACM|cp210|ch340|ftdi|converter" | tail -60
```

Wynik:

```text
/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 -> ../../ttyUSB0
/dev/ttyUSB0
```

Wniosek:

```text
Nextion 5 jest widoczny jako:
PORT = /dev/ttyUSB0
ADAPTER = Silicon Labs CP2102 USB-UART
```

---

## 3. Parametry serial dla Nextion 5

Ustalenia robocze:

```text
NEXTION5_PORT = /dev/ttyUSB0
NEXTION5_BAUD = 9600
TRYB = 8N1
FLOW CONTROL = OFF
```

Pełny zapis parametrów:

```text
port: /dev/ttyUSB0
baudrate: 9600
bytesize: 8
parity: none / N
stopbits: 1
xonxoff: false
rtscts: false
dsrdtr: false
```

Roboczy wpis konfiguracyjny:

```json
{
  "enabled": true,
  "port": "/dev/ttyUSB0",
  "baudrate": 9600,
  "bytesize": 8,
  "parity": "N",
  "stopbits": 1,
  "xonxoff": false,
  "rtscts": false,
  "dsrdtr": false
}
```

---

## 4. Status techniczny portu

Port był widoczny jako CP2102, ale pojawił się błąd drivera:

```text
cp210x ttyUSB0: failed set request 0x0 status: -32
cp210x_open - Unable to enable UART
```

Po odłączeniu i ponownym podłączeniu konwertera system ponownie wykrył urządzenie:

```text
USB disconnect
cp210x converter now disconnected from ttyUSB0
device disconnected
CP2102 USB to UART Bridge Controller
cp210x converter detected
cp210x converter now attached to ttyUSB0
```

Wniosek:

```text
[x] Nextion 5 / CP2102 jest widoczny w Linuxie
[x] port systemowy jest ustalony
[x] baud roboczy jest ustalony
[ ] komunikacja ekranowa nie była jeszcze potwierdzana jako etap runtime
```

---

## 5. Poprawna kolejność dalszej pracy

Nie zaczynamy od mieszania komunikacji z całym systemem.

Kolejność:

```text
1. Ustalić port fizyczny Nextion 5.
2. Ustalić baudrate i tryb serial.
3. Wpisać to do konfiguracji Nextion 5 w TARZANIE.
4. Dopiero potem wykonać test komunikacji z ekranem.
5. Dopiero potem podpinać bridge / Snajpera / odświeżanie.
```

Na tym etapie wykonano kroki 1–2.

Do wykonania następnie:

```text
ustawienie konfiguracji Nextion 5:
PORT=/dev/ttyUSB0
BAUD=9600
8N1
flow control off
```

---

## 6. Czego nie robić teraz

Na tym etapie nie robimy:

```text
testów Nextion 7
szukania drugiego ekranu
przebudowy bridge.py
przebudowy Snajpera
zmian w PAR UI
zmian w TSP
automatycznego odświeżania stron
testów page/sendme
```

Najpierw konfiguracja portu dla **Nextion 5**.

---

## 7. Minimalny test portu, gdy będzie potrzebny

Dopiero po ustawieniu konfiguracji można wykonać minimalny test samego portu:

```bash
python3 - <<'PY'
import serial

port="/dev/ttyUSB0"

ser = serial.Serial(
    port=port,
    baudrate=9600,
    bytesize=8,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=0.5,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False,
)

print("OPEN OK", port)
ser.close()
PY
```

Jeżeli port otwiera się poprawnie:

```text
OPEN OK /dev/ttyUSB0
```

to dopiero potem można robić test komendy Nextion `connect`.

---

## 8. Minimalny test Nextion connect, później

Test komunikacji ekranowej, ale dopiero po wpisaniu portu do konfiguracji:

```bash
python3 - <<'PY'
import serial, time

port="/dev/ttyUSB0"
baud=9600
END=b"\xff\xff\xff"

ser = serial.Serial(
    port=port,
    baudrate=baud,
    bytesize=8,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=0.7,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False,
)

ser.reset_input_buffer()
ser.reset_output_buffer()

ser.write(b"connect" + END)
ser.flush()
time.sleep(0.7)

data = ser.read(512)
print("RX HEX:", data.hex(" ") if data else "brak")
print("RX RAW:", repr(data))

ser.close()
PY
```

Pozytywny wynik to odpowiedź typu:

```text
comok ...
```

albo ramka zakończona:

```text
ff ff ff
```

---

## 9. Wpis roboczy do dokumentacji projektu

```text
NEXTION 5 / tarzanMiniPC

Port:
  /dev/ttyUSB0

Adapter:
  Silicon Labs CP2102 USB-UART

Baudrate:
  9600

Serial:
  8N1

Flow control:
  off

Status:
  urządzenie widoczne w Linuxie
  port ustalony
  baudrate ustalony
  komunikacja ekranowa do osobnego testu po wpisaniu konfiguracji
```

---

## 10. Stan końcowy etapu

Etap można zamknąć jako:

```text
Nextion 5 — port i parametry serial ustalone na tarzanMiniPC
```

Potwierdzone:

```text
[x] Nextion 5 jest podłączony do mini PC
[x] widoczny jako Silicon Labs CP2102
[x] port: /dev/ttyUSB0
[x] baudrate roboczy: 9600
[x] tryb serial: 8N1, flow off
```

Niepotwierdzone jeszcze:

```text
[ ] odpowiedź ekranowa `connect`
[ ] page/sendme
[ ] bridge runtime
[ ] Snajper refresh
[ ] integracja z PAR/TSP
```

Następny etap:

```text
wpisać konfigurację Nextion 5 do plików TARZANA i dopiero potem testować komunikację ekranową
```
