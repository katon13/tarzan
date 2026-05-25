# TARZAN HARDWARE RUNTIME — SPECYFIKACJA TESTÓW

## 1. Cel dokumentu

Ten dokument opisuje sposób prowadzenia testów sprzętu TARZAN na etapie:

```text
TARZAN MINI PC — konfiguracja hardware runtime
```

Celem nie jest jeszcze ruch osi ani pełne spięcie SignalBus/Snajper/TSP.  
Celem jest spokojne, kontrolowane sprawdzenie tego, co jest już fizycznie podłączone:

- PoKeys PLAY,
- PoKeys REC,
- wejścia cyfrowe,
- krańcówki,
- analogi,
- RRP,
- czujniki,
- LCD,
- Matrix LED,
- PoExtBus,
- PoSensors / I2C,
- czujnik odległości / laser po serialu,
- Nextion 5 i Nextion 7,
- PoStep / STEP / DIR / ENABLE tylko diagnostycznie, bez ruchu.

Każdy test ma być odnotowany w osobnym pliku checklisty:

```text
TARZAN_hardware_runtime_test_checklist.txt
```

---

## 2. Źródła prawdy

Obowiązują dwa poziomy źródeł prawdy.

### 2.1. Źródło prawdy TARZANA

```text
core/tarzanZmienneSygnalowe.py
```

Ten plik mówi:

- co jest podłączone,
- na której płytce,
- na którym pinie,
- jaki jest typ sygnału,
- jaki jest kierunek,
- jaka jest funkcja hardware,
- jaka jest nazwa kanoniczna,
- czy sygnał jest dozwolony, tylko do odczytu, czy zabroniony.

Nie wolno tworzyć równoległej ręcznej mapy pinów.

### 2.2. Źródło prawdy producenta

Dokumentacja producenta:

```text
PoKeys57 - user manual.pdf
PoKeys - protocol specification.pdf
PoSensors.pdf
PoStep25-32 UserManual.pdf
```

Ta dokumentacja mówi, jak technicznie wolno czytać, testować albo sterować urządzeniem.

---

## 3. Zasada główna testów

Nie testujemy abstrakcyjnych pinów `1–55`.

Testujemy to, co jest realnie nazwane i opisane w TARZANIE.

Czyli nie:

```text
pin 1
pin 2
pin 3
...
```

Tylko:

```text
PLAY / P01 / play_p01_arm_h_auto_limit / sensor_arm_h_auto_limit
REC  / P45 / rec_p45_sw_f1 / ui_f1_sw
PLAY / P45 / play_p45_rrp_pot_h / sensor_rrp_pot_h
REC  / P41 / rec_p41_free_aux_pot / sensor_level_x
```

Każdy test powinien być powiązany z wpisem z `tarzanZmienneSygnalowe.py`.

---

## 4. Statusy w checkliście

W pliku TXT stosujemy prosty format linuxowy:

```text
[ ]  nie testowane
[x]  przetestowane OK
[!]  problem / do sprawdzenia
[-]  pomijamy na tym etapie
```

Format wpisu:

```text
[ ] DATA | PŁYTKA | PIN/KANAŁ | SYGNAŁ | TEST | WYNIK | UWAGI
```

Przykład:

```text
[x] 2026-05-25 | PLAY | P45 | play_p45_rrp_pot_h / sensor_rrp_pot_h | odczyt analog RRP H | OK | płynna zmiana wartości
[!] 2026-05-25 | REC | P39 | rec_p39_shock_sensor / sensor_shock_state | odczyt czujnika wstrząsu | PROBLEM | brak zmiany po poruszeniu
[-] 2026-05-25 | PLAY | P46 | play_p46_step_ctr_arm_h / axis_arm_h_step | generowanie STEP | POMINIĘTE | bez ruchu na tym etapie
```

---

## 5. Klasy bezpieczeństwa testów

Każdy test musi należeć do jednej z klas.

### 5.1. READ_ONLY

Bezpieczny odczyt.

Obejmuje:

- krańcówki,
- wejścia cyfrowe,
- kopie sygnałów,
- analogi,
- potencjometry RRP,
- przyciski,
- statusy,
- czujniki,
- odczyt konfiguracji urządzenia,
- odczyt firmware,
- odczyt serialu,
- odczyt wejść i analogów.

To jest pierwszy etap.

### 5.2. SAFE_OUTPUT_MANUAL

Ręczne testowanie wyjść.

Obejmuje:

- lampki,
- proste wyjścia UI,
- wyjścia mostka,
- enable tylko diagnostycznie,
- wyjścia, które nie uruchamiają ruchu.

Wymaga jawnego potwierdzenia operatora.

Nie może działać automatycznie po starcie programu.

### 5.3. DISPLAY_TEST

Testowanie wyświetlaczy jako urządzeń.

Obejmuje:

- LCD 1602,
- Matrix LED 8x8,
- później Nextion 5,
- później Nextion 7.

Wyświetlacza nie traktujemy jak zwykłego zestawu pinów.  
Testujemy go jako podłączony moduł.

### 5.4. BUS_TEST

Testowanie magistral i modułów po protokołach.

Obejmuje:

- I2C,
- 1-wire,
- PoSensors,
- PoNET,
- PoExtBus,
- serial dla czujnika odległości / lasera.

### 5.5. FORBIDDEN_MOTION

Na tym etapie zakazane.

Obejmuje:

- generowanie STEP,
- Pulse Engine Move,
- homing,
- jogging,
- automatyczny ruch osi,
- odpalanie silnika,
- testy pozycji,
- testy prędkości,
- praca PoStep jako napęd.

Te wpisy mogą być w checkliście, ale oznaczone jako:

```text
[-] pomijamy na tym etapie
```

---

## 6. Granice bezpieczeństwa

Na tym etapie nie wolno wykonywać bez osobnej decyzji:

```text
PK_PinConfigurationSet
PK_SaveConfiguration
PK_ClearConfiguration
PK_DigitalIOSet
PK_DigitalIOSetSingle
PK_PoExtBusSet
PK_PWMConfigurationSet
PK_PWMUpdate
PK_PEv2_PulseEngineSetup
PK_PEv2_AxisConfigurationSet
PK_PEv2_PositionSet
PK_PEv2_PulseEngineStateSet
PK_PEv2_PulseEngineMove
PK_PEv2_PulseEngineMovePV
PK_PEv2_HomingStart
PK_PEv2_ProbingStart
```

Dozwolone na starcie:

```text
PK_EnumerateUSBDevices
PK_ConnectToDevice
PK_ConnectToDeviceWSerial
PK_DeviceDataGet
PK_PinConfigurationGet
PK_DigitalIOGet
PK_DigitalIOGetSingle
PK_AnalogIOGet
PK_PEv2_StatusGet
PK_PEv2_Status2Get
PK_PoExtBusGet
PK_PWMConfigurationGet
PK_LCDConfigurationGet
PK_MatrixLEDConfigurationGet
PK_EasySensorsSetupGet
PK_EasySensorsValueGetAll
```

---

## 7. Kolejność testów

### Etap 0 — stan mini PC

Sprawdzić:

```text
Debian
hostname
IP
SSH
TSP
LKS
CPU
RAM
```

Ten etap jest już wstępnie zamknięty.

### Etap 1 — widoczność sprzętu w systemie

Na `tarzanMiniPC`:

```bash
lsusb
ls -l /dev/serial/by-id/ || true
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
dmesg | grep -iE "usb|tty|serial|pokeys|cp210|ch340|ftdi" | tail -80
```

Cel:

- widzieć urządzenia USB,
- ustalić porty serial,
- potwierdzić obecność PoKeys,
- potwierdzić porty Nextion/czujników.

### Etap 2 — biblioteka PoKeys

Sprawdzić:

```text
czy na Windows działa PoKeyslib.dll
czy na Debianie jest dostępne libPoKeys.so
czy Python ładuje bibliotekę
czy enumeracja urządzeń działa
```

Na mini PC prawdopodobnie będzie potrzebna linuxowa biblioteka:

```text
libPoKeys.so
```

DLL z Windows nie wystarczy dla Debiana.

### Etap 3 — PLAY

Oczekiwany serial:

```text
PLAY = 34238
```

Najpierw:

```text
wykrycie urządzenia
odczyt DeviceData
odczyt konfiguracji pinów
odczyt wejść
odczyt analogów
```

Potem:

```text
krańcówki
RRP analog
UI
bezpieczne wyjścia manualne
LCD
I2C / czujniki
```

### Etap 4 — REC

Oczekiwany serial:

```text
REC = 33410
```

Najpierw:

```text
wykrycie urządzenia
odczyt DeviceData
odczyt konfiguracji pinów
odczyt wejść
odczyt analogów
```

Potem:

```text
kopie sygnałów kamery
REC DIR/CTR
mostek PLAY-REC
F1-F4
XYZ
czujnik wstrząsu
LCD
Matrix LED
PoExtBus
```

### Etap 5 — czujnik odległości / laser

Najpierw tylko port i odczyt.

Parametry z dostarczonych przykładów:

```text
serial 115200
ramka YY
dystans = Dist_H * 256 + Dist_L
```

Nie zakładać portu na sztywno.  
Najpierw mapowanie `/dev/serial/by-id/`.

### Etap 6 — wyświetlacze

Testy osobne:

```text
LCD PLAY
LCD REC
Matrix LED PLAY/REC
Nextion 5
Nextion 7
```

Nextiony będą testowane później, według osobnej specyfikacji i oficjalnego Nextion Instruction Set.

### Etap 7 — PoSensors / I2C

Testy:

```text
I2C scan
BH1750 światło
temperatura
wilgotność
XYZ / akcelerometr
ADC
```

Testujemy tylko odczyt.

### Etap 8 — PoStep / CNC / STEP-DIR

Na tym etapie tylko:

```text
czy mapa sygnałów istnieje
czy statusy są czytelne
czy nie ma błędów drivera
czy ENABLE/DIR/STEP są opisane poprawnie
```

Bez ruchu.

---

## 8. Struktura przyszłego sandboxa

Docelowy sandbox powinien mieć tryby:

```text
1. SCAN
2. PLAY READ
3. REC READ
4. PLAY MONITOR
5. REC MONITOR
6. ANALOG / RRP
7. DISPLAY TEST
8. BUS TEST
9. SAFE OUTPUT MANUAL
10. REPORT
```

Nie powinien mieć własnej mapy pinów.  
Powinien importować:

```python
from core.tarzanZmienneSygnalowe import (
    POKEYS57U_PLAY_DEVICE_SERIAL,
    POKEYS57U_REC_DEVICE_SERIAL,
    SYGNALY_PLAY,
    SYGNALY_REC,
    SYGNALY_CNC,
    WSZYSTKIE_SYGNALY,
)
```

---

## 9. Raport po testach

Każdy większy test powinien dawać raport:

```text
data/hardware/reports/tarzan_hardware_test_YYYY-MM-DD_HHMMSS.txt
```

Raport powinien zawierać:

```text
data
host
operator
urządzenie
serial
lista testów
wynik OK / problem
piny testowane
sygnały testowane
wartości odczytane
ostrzeżenia
następne kroki
```

---

## 10. Zasada pracy z użytkownikiem

Użytkownik decyduje kolejność:

```text
co testujemy
co odpalamy
co pomijamy
co oznaczamy jako OK
co oznaczamy jako problem
```

Po każdym teście aktualizujemy checklistę.

Najpierw testujemy to, co jest już fizycznie podłączone.  
Nie budujemy teorii obok dokumentacji i mapy sygnałów.

---

## 11. Najbliższy praktyczny krok

Pierwszy realny test powinien być:

```text
SCAN hardware mini PC
```

Czyli:

```text
lsusb
/dev/serial/by-id
ładowanie PoKeysLib
enumeracja PoKeys
wykrycie PLAY 34238
wykrycie REC 33410
raport
```

Dopiero po tym przechodzimy do:

```text
PLAY read-only
REC read-only
analogi
czujniki
wyświetlacze
wyjścia manualne
```

---

## 12. Skrót do nowego wątku

```text
Budujemy TARZAN HARDWARE RUNTIME TEST SANDBOX.

Źródło prawdy:
- core/tarzanZmienneSygnalowe.py
- PoKeys57 user manual
- PoKeys protocol specification
- PoSensors manual
- PoStep25-32 manual

Nie tworzymy ręcznej mapy pinów.
Testujemy tylko to, co jest opisane jako realnie podłączone w TARZANIE.

Najpierw READ ONLY:
- wykrycie PLAY 34238
- wykrycie REC 33410
- odczyt konfiguracji
- odczyt wejść
- odczyt analogów
- raport

Potem ręcznie:
- LCD
- Matrix LED
- PoExtBus
- PoSensors/I2C
- czujnik odległości
- Nextion 5/7

Na tym etapie zakaz:
- generowania STEP
- Pulse Engine Move
- homing
- jogging
- ruchu osi
- zapisu konfiguracji PoKeys bez osobnej decyzji

Prowadzimy plik:
TARZAN_hardware_runtime_test_checklist.txt

Statusy:
[ ] nie testowane
[x] OK
[!] problem
[-] pomijamy
```
