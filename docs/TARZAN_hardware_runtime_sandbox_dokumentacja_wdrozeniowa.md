# TARZAN — hardware runtime sandbox / dokumentacja wdrożeniowa

Data: 2026-05-25  
Zakres: `tarzanMiniPC`, PoKeys PLAY/REC, BUS/I2C, klawiatura, LCD, Matrix LED, F1–F4, CNC/RECK, wejścia/krańcówki/analogi.  
Plik roboczy sandboxa: `hardware/tarzanMiniPcSandbox.py`

---

## 1. Cel tej dokumentacji

Ten dokument opisuje, co zostało wykonane i potwierdzone w sandboxie hardware runtime, tak aby późniejsze spięcie z pełnym TARZANEM było łatwiejsze.

Najważniejsze: sandbox nie jest docelowym runtime TARZANA. Sandbox służy do bezpiecznego potwierdzenia:

- czy płytki są widoczne,
- czy `tarzanZmienneSygnalowe.py` pasuje do fizycznego hardware,
- czy PoKeysLib działa na `tarzanMiniPC`,
- czy wejścia są czytane,
- czy magistrale i peryferia działają,
- czy można bezpiecznie przygotować dalsze spięcie z SignalBus / Snajper / PAR / Nextion / TSP.

---

## 2. Podział ról sprzętowych

### 2.1 `tarzanMiniPC`

`tarzanMiniPC` jest lekkim node wykonawczym.

Rola:

```text
Debian / systemd / SSH
PoKeys runtime
BUS/I2C runtime
TSP server
SignalBus runtime
Nextion bridge
czujniki
diagnostyka/LKS
```

Nie jest to komputer UI.

Nie uruchamiamy tutaj ciężkich okien:

```text
EHR
PAR UI
TAKE UI
kamera / AI
duże preview
```

### 2.2 `tarzanStacja`

`tarzanStacja` jest komputerem operatorskim.

Rola:

```text
EHR
PAR
TAKE
KHR/AI/kamera
UI operatora
repo / PyCharm / Git
```

---

## 3. Adresy i nazwy

```text
tarzanMiniPC  = 192.168.1.26
tarzanStacja  = 192.168.1.12
```

Praca zdalna:

```text
SSH / PuTTY -> tarzanMiniPC
PowerShell / PyCharm -> tarzanStacja
```

---

## 4. PoKeys — aktualny komplet płytek

Potwierdzone płytki:

```text
PLAY / PLAYER = PoKeys57U serial 36102
REC  / RECK   = PoKeys57U serial 36084
```

W systemie USB widoczne jako:

```text
PoLabs PLAYER serial 2.36102
PoLabs RECK   serial 2.36084
```

PoKeysLib na mini PC:

```text
/usr/lib/libPoKeys.so
```

Podstawowy test:

```bash
cd /opt/tarzan
python3 -m hardware.tarzanMiniPcSandbox scan --lib-path /usr/lib/libPoKeys.so
```

Oczekiwany sens wyniku:

```text
PLAY serial=36102
REC  serial=36084
```

---

## 5. Źródło prawdy mapy sygnałów

Źródłem prawdy dla mapy pinów, nazw, kierunków, kanonicznych nazw i klasyfikacji jest:

```text
core/tarzanZmienneSygnalowe.py
```

Zasada:

```text
Nie robimy ręcznych równoległych map w sandboxie.
Sandbox czyta mapę TARZANA.
```

Dalsza implementacja w TARZANIE ma iść przez kanoniczne nazwy sygnałów, np.:

```text
sensor_light_lux
axis_arm_h_rec_step
axis_arm_h_rec_dir
ui_f1_sw
ui_f1_led
```

---

## 6. Sandbox — uruchamianie

Na mini PC:

```bash
cd /opt/tarzan
python3 -m hardware.tarzanMiniPcSandbox --help
```

Typowe komendy:

```bash
python3 -m hardware.tarzanMiniPcSandbox list --board PLAY --pins 24-27
python3 -m hardware.tarzanMiniPcSandbox read --board PLAY --pins 24-27 --lib-path /usr/lib/libPoKeys.so
python3 -m hardware.tarzanMiniPcSandbox monitor --board REC --pins 12-22,37 --interval 0.2 --lib-path /usr/lib/libPoKeys.so
```

---

## 7. Zasady bezpieczeństwa sandboxa

Sandbox ma dwa tryby mentalne:

```text
READ ONLY
TEST PERYFERIUM
```

### 7.1 READ ONLY

Bezpieczne odczyty:

```text
list
read
monitor
scan
bus-scan
keypad-map
buttons-test
bh1750-bus-test
```

### 7.2 TEST PERYFERIUM

Kontrolowane testy urządzeń:

```text
lcd-test
lcd-scroll
matrix-test
led-test
```

### 7.3 Czego nie robimy w tym etapie

```text
STEP output
DIR output
ENABLE output
Pulse Engine Move
homing
ruch osi
zapis konfiguracji PoKeys do flash
```

---

## 8. LCD 1602 / HD44780

### 8.1 PLAY LCD

Podłączenie z mapy:

```text
PLAY P28 = play_p28_lcd_rw
PLAY P29 = play_p29_lcd_rs / ui_lcd_rs
PLAY P30 = play_p30_lcd_e  / ui_lcd_e
PLAY P31 = play_p31_lcd_db7 / ui_lcd_db7
PLAY P32 = play_p32_lcd_db6 / ui_lcd_db6
PLAY P33 = play_p33_lcd_db5 / ui_lcd_db5
PLAY P34 = play_p34_lcd_db4 / ui_lcd_db4
```

Test:

```bash
python3 -m hardware.tarzanMiniPcSandbox lcd-test --board PLAY --line1 "TARZAN PLAY" --line2 "LCD OK" --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LCD_TEST
```

Status:

```text
[x] PLAY LCD działa fizycznie
```

### 8.2 REC LCD

Podłączenie z mapy:

```text
REC P28 = rec_p28_lcd_rw
REC P29 = rec_p29_lcd_rs
REC P30 = rec_p30_lcd_e
REC P31 = rec_p31_lcd_db7
REC P32 = rec_p32_lcd_db6
REC P33 = rec_p33_lcd_db5
REC P34 = rec_p34_lcd_db4
```

Test:

```bash
python3 -m hardware.tarzanMiniPcSandbox lcd-test --board REC --line1 "TARZAN REC" --line2 "LCD OK" --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LCD_TEST
```

### 8.3 Uwaga do scrollowania LCD

LCD 1602 ma bezwładność wizualną. Przy szybkim scrollu mogą pojawiać się smużenia / migotanie.

Dalszy kierunek:

```text
dłuższy hold klatki
opcjonalne wygaszenie spacjami
wolniejszy scroll
```

---

## 9. Matrix LED

Matrix LED jest na REC / RECK.

Podłączenie:

```text
REC P09 = rec_p09_led_data
REC P10 = rec_p10_led_latch
REC P11 = rec_p11_led_clk
```

Test blink:

```bash
python3 -m hardware.tarzanMiniPcSandbox matrix-test --board REC --mode blink --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_MATRIX_TEST
```

Test wzoru:

```bash
python3 -m hardware.tarzanMiniPcSandbox matrix-test --board REC --mode checker --delay 0.25 --repeat 4 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_MATRIX_TEST
```

Test tekstu:

```bash
python3 -m hardware.tarzanMiniPcSandbox matrix-test --board REC --text "TARZAN" --mode scroll --delay 0.20 --repeat 2 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_MATRIX_TEST
```

Status:

```text
[x] Matrix LED REC widziany
[x] komenda PoKeysLib przechodzi
[x] peryferium działa jako test MatrixLED
```

---

## 10. Przyciski F1–F4

Przyciski są na REC / RECK.

Mapa:

```text
F1 = REC P45 = rec_p45_sw_f1 / ui_f1_sw
F2 = REC P47 = rec_p47_sw_f2 / ui_f2_sw
F3 = REC P49 = rec_p49_sw_f3 / ui_f3_sw
F4 = REC P51 = rec_p51_sw_f4 / ui_f4_sw
```

Test:

```bash
python3 -m hardware.tarzanMiniPcSandbox buttons-test --board REC --lib-path /usr/lib/libPoKeys.so
```

Potwierdzony wynik:

```text
F1: 1 -> 0 -> 1
F2: 1 -> 0 -> 1
F3: 1 -> 0 -> 1
F4: 1 -> 0 -> 1
```

Wniosek:

```text
[x] F1-F4 działają fizycznie
[x] logika active-low / pull-up
```

---

## 11. LED F1–F4

LED-y są na REC / RECK.

Mapa:

```text
LED F1 = REC P46 = rec_p46_led_f1 / ui_f1_led
LED F2 = REC P48 = rec_p48_led_f2 / ui_f2_led
LED F3 = REC P50 = rec_p50_led_f3 / ui_f3_led
LED F4 = REC P52 = rec_p52_led_f4 / ui_f4_led
```

Test:

```bash
python3 -m hardware.tarzanMiniPcSandbox led-test --board REC --led F1,F2,F3,F4 --on-time 0.12 --off-time 0.08 --repeat 5 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LED_TEST
```

Ważna zasada:

```text
led-test wolno uruchamiać tylko przez whitelistę:
ui_f1_led
ui_f2_led
ui_f3_led
ui_f4_led
```

Nie wolno robić ogólnego output-test na dowolnym pinie.

Dlaczego:

```text
niektóre piny mogą mieć zdolności specjalne / Pulse Engine
ale w tym teście używamy ich wyłącznie jako LED UI
bez ruchu i bez Pulse Engine
```

---

## 12. Klawiatura matrix 4x3

Fizyczna klawiatura:

```text
1  2  3
4  5  6
7  8  9
*  0  #
```

To nie są cztery przyciski `KB1-KB4` dla operatora. To jest matrix keyboard.

Linie w mapie:

```text
PLAY P24 = play_p24_kb4 / ui_kb4
PLAY P25 = play_p25_kb3 / ui_kb3
PLAY P26 = play_p26_kb2 / ui_kb2
PLAY P27 = play_p27_kb1 / ui_kb1
```

Test mapowania:

```bash
python3 -m hardware.tarzanMiniPcSandbox keypad-map --board PLAY --lib-path /usr/lib/libPoKeys.so
```

Potwierdzona mapa:

```text
1 = index 0,  row 0, col 0
2 = index 1,  row 0, col 1
3 = index 2,  row 0, col 2

4 = index 8,  row 1, col 0
5 = index 9,  row 1, col 1
6 = index 10, row 1, col 2

7 = index 16, row 2, col 0
8 = index 17, row 2, col 1
9 = index 18, row 2, col 2

* = index 24, row 3, col 0
0 = index 25, row 3, col 1
# = index 26, row 3, col 2
```

Status:

```text
[x] PLAY widzi klawiaturę matrix
[x] wszystkie 12 klawiszy wykryte
[x] mapa row/col kompletna
```

Dalszy krok implementacyjny:

```text
dodać w runtime parser:
index/row/col -> znak 1..#
```

Docelowo do SignalBus:

```text
ui_keypad_last_key
ui_keypad_pressed
ui_keypad_event
```

---

## 13. BUS / I2C

### 13.1 Zasada

BUS 5-pin / I2C nie jest COM i nie jest UART.

To idzie przez PoKeysLib:

```text
PoKeys PLAY -> BUS / I2C -> czujnik -> PoKeysLib -> TARZAN
```

Nie szukamy tego jako:

```text
/dev/ttyUSB0
```

### 13.2 Skan BUS

Komenda:

```bash
python3 -m hardware.tarzanMiniPcSandbox bus-scan --board PLAY --lib-path /usr/lib/libPoKeys.so
```

Potwierdzony wynik:

```text
WYKRYTE ADRESY BUS/I2C:
0x5C
```

Status:

```text
[x] BUS/I2C na PLAY działa
[x] czujnik odpowiada pod adresem 0x5C
```

---

## 14. Czujnik światła na BUS

Aktualnie podłączony jest jeden czujnik światła na BUS.

Ważne rozdzielenie:

```text
Są dwa możliwe czujniki światła w projekcie:
1. czujnik zgodny z dokumentacją PoKeys — na później
2. aktualnie podłączony czujnik światła na BUS — testowany teraz
```

Ten dokument opisuje czujnik aktualnie testowany.

Komenda:

```bash
python3 -m hardware.tarzanMiniPcSandbox bh1750-bus-test --board PLAY --address 0x5C --repeat 30 --interval 0.3 --lib-path /usr/lib/libPoKeys.so
```

Potwierdzony przykład odczytu:

```text
ciemno / zasłonięty:
lux około 4–17

światło / wiązka:
lux około 270–5500
```

Status:

```text
[x] adres 0x5C działa
[x] raw działa
[x] lux działa
[x] czujnik reaguje na światło
```

Roboczy zapis do dalszej implementacji:

```text
BUS_LIGHT_SENSOR_1
board: PLAY / PLAYER
bus: 5-pin BUS / I2C
address: 0x5C
value: lux
status: TEST OK
```

Docelowe sygnały SignalBus:

```text
sensor_light_lux
sensor_light_raw
sensor_light_bus_address
sensor_light_status
```

---

## 15. Wiele czujników na jednym BUS/I2C

Można równolegle podłączać wiele urządzeń I2C do tych samych linii:

```text
+V
GND
SDA
SCL
```

Schemat logiczny:

```text
BUS +V   -> czujnik 1 VCC -> czujnik 2 VCC -> czujnik 3 VCC
BUS GND  -> czujnik 1 GND -> czujnik 2 GND -> czujnik 3 GND
BUS SDA  -> czujnik 1 SDA -> czujnik 2 SDA -> czujnik 3 SDA
BUS SCL  -> czujnik 1 SCL -> czujnik 2 SCL -> czujnik 3 SCL
```

Warunek:

```text
Każdy czujnik musi mieć inny adres I2C.
```

Na teraz zajęty adres:

```text
0x5C = aktualny czujnik światła na BUS PLAY
```

Robocze ograniczenie dla TARZANA:

```text
bezpiecznie: 2–4 czujniki na BUS
po testach: 5–8 czujników
więcej tylko po sprawdzeniu długości przewodów, zasilania i adresów
```

---

## 16. CP2102 / UART

Na mini PC jest widoczny:

```text
CP2102 USB to UART Bridge Controller
/dev/ttyUSB0
```

Test nasłuchu:

```bash
python3 - <<'PY'
import serial, time

port = "/dev/ttyUSB0"
baud = 115200

print(f"OPEN {port} @ {baud}")
ser = serial.Serial(port, baudrate=baud, timeout=0.2)

print("Nasluch 5 sekund...")
end = time.time() + 5
while time.time() < end:
    data = ser.read(64)
    if data:
        print("RX:", data.hex(" "), " | ", repr(data))
ser.close()
print("KONIEC")
PY
```

Wynik:

```text
brak danych
```

Test komendą przykładową:

```text
42 57 02 00 00 00 01 06
```

Wynik:

```text
brak odpowiedzi
```

Wniosek:

```text
[x] CP2102 istnieje
[x] /dev/ttyUSB0 działa
[x] pyserial działa
[ ] nie zidentyfikowano aktywnego urządzenia UART
```

Na tym etapie nie mieszamy tego z czujnikiem światła BUS.

---

## 17. Osobna płytka CNC i RECK

Bardzo ważne rozdzielenie:

```text
RECK / REC = płytka PoKeys
CNC        = osobna płytka
CNC jest podłączona do RECK
RECK czyta sygnały z CNC / mostka
```

Nie mówimy, że „CNC jest w RECK”.

Mówimy:

```text
osobna płytka CNC jest czytana przez RECK
```

### 17.1 Linie diagnostyczne REC / CNC / mostek

Odczytywane linie:

```text
REC P12 = rec_p12_rec_dir_arm_h
REC P13 = rec_p13_rec_dir_arm_v
REC P15 = rec_p15_rec_ctr_arm_h
REC P16 = rec_p16_rec_ctr_arm_v

REC P17 = rec_p17_bridge_play_dir_x
REC P18 = rec_p18_bridge_play_dir_y
REC P19 = rec_p19_bridge_play_dir_z
REC P20 = rec_p20_bridge_play_ctr_x
REC P21 = rec_p21_bridge_play_ctr_y
REC P22 = rec_p22_bridge_play_ctr_z
REC P37 = rec_p37_bridge_play_rec_in
```

Test:

```bash
python3 -m hardware.tarzanMiniPcSandbox monitor --board REC --pins 12-22,37 --interval 0.2 --lib-path /usr/lib/libPoKeys.so
```

Wynik:

```text
wszystkie linie stabilnie D1
```

Wniosek:

```text
[x] RECK ma kontakt odczytowy z osobną płytką CNC / mostkiem
[x] linie są czytane
[x] stan spoczynkowy = D1
[ ] impulsy niepotwierdzone
[ ] ruch nietestowany
```

---

## 18. STEP / DIR / ENABLE — co wiemy na dziś

Według logiki projektu:

```text
STEP / DIR / ENABLE do sterownika = sygnały wykonawcze
CTR / DIR czytane przez RECK     = sygnały diagnostyczne / wejściowe
```

Na dziś przetestowano tylko odczyt wejściowy.

Monitor CTR:

```bash
python3 -m hardware.tarzanMiniPcSandbox monitor --board REC --pins 15,16,20,21,22 --interval 0.05 --lib-path /usr/lib/libPoKeys.so
```

Wynik:

```text
rec_p15_rec_ctr_arm_h = D1
rec_p16_rec_ctr_arm_v = D1
rec_p20_bridge_play_ctr_x = D1
rec_p21_bridge_play_ctr_y = D1
rec_p22_bridge_play_ctr_z = D1
```

Wniosek:

```text
[x] linie są widoczne
[x] stan spoczynkowy jest czytany
[ ] nie było impulsu
[ ] counter STEP/CTR jeszcze niepotwierdzony impulsem
[ ] ENABLE wykonawczo nietestowany
[ ] ruch osi nietestowany
```

Do pełnego potwierdzenia potrzebny będzie bezpieczny impuls testowy z CNC/generatora, bez ruchu osi.

---

## 19. Wejścia, krańcówki, analogi — PLAY

Test:

```bash
python3 -m hardware.tarzanMiniPcSandbox read --board PLAY --pins 11-16,23,45,47,53 --lib-path /usr/lib/libPoKeys.so
```

Potwierdzone odczyty:

```text
PLAY P11 = play_p11_cart_limit_end         = 1
PLAY P12 = play_p12_arm_v_limit_down       = 1
PLAY P13 = play_p13_mass_reg_limit_add     = 1
PLAY P14 = play_p14_drone_release          = 1
PLAY P15 = play_p15_rrp_dir_h_res          = 1
PLAY P16 = play_p16_action_led             = 0
PLAY P23 = play_p23_mass_reg_limit_remove  = 1
PLAY P45 = play_p45_rrp_pot_h              = raw=0 / 0.0V
PLAY P47 = play_p47_rrp_pot_v              = raw=0 / 0.0V
```

Wniosek:

```text
[x] PLAY czyta kanały krańcówek / regulatora / RRP
[x] analogi są widoczne
[ ] brak fizycznych krańcówek
[ ] brak fizycznych potencjometrów / sygnałów analogowych
```

---

## 20. Wejścia, czujniki, analogi — REC

Test:

```bash
python3 -m hardware.tarzanMiniPcSandbox read --board REC --pins 27,39-44 --lib-path /usr/lib/libPoKeys.so
```

Potwierdzone odczyty:

```text
REC P27 = sensor_laser_set = D1
REC P41 = sensor_level_x   = raw=0 / 0.0V
REC P42 = sensor_level_y   = raw=0 / 0.0V
REC P43 = sensor_level_z   = raw=0 / 0.0V
REC P44 = sensor_temp_c    = raw=0 / 0.0V
```

Wniosek:

```text
[x] REC widzi wejście sensor_laser_set
[x] REC widzi analogi level/temp
[ ] brak fizycznych czujników / napięć
```

---

## 21. Aktualny status pełnej diagnostyki bazowej

```text
[x] PLAY / PLAYER wykryty i czytany
[x] REC / RECK wykryty i czytany
[x] PoKeysLib działa na mini PC
[x] mapa TARZANA pasuje do seriali PLAY/REC
[x] LCD PLAY działa fizycznie
[x] Matrix LED REC działa przez PoKeysLib
[x] F1-F4 przyciski działają fizycznie
[x] LED F1-F4 mają przygotowany bezpieczny test whitelistą
[x] klawiatura matrix 4x3 działa i jest zmapowana
[x] BUS/I2C PLAY działa
[x] czujnik światła BUS działa na 0x5C
[x] osobna płytka CNC jest czytana przez RECK w stanie spoczynku
[x] wejścia/krańcówki/analogi są widoczne diagnostycznie
```

Jeszcze niepotwierdzone, bo nie było urządzeń / impulsów:

```text
[ ] realne krańcówki
[ ] realne czujniki analogowe level/temp
[ ] realne potencjometry RRP
[ ] realne wyjścia wykonawcze
[ ] impulsy STEP/CTR z CNC
[ ] ENABLE wykonawczo
[ ] ruch osi
```

---

## 22. Jak to przenieść później do pełnego TARZANA

### 22.1 Nie przenosić sandboxa jako runtime 1:1

Sandbox ma zostać jako narzędzie diagnostyczne.

Do pełnego TARZANA przenosimy:

```text
sprawdzone mapowanie
sprawdzone adresy
sprawdzone nazwy kanoniczne
sprawdzone sposoby odczytu
sprawdzone urządzenia peryferyjne
```

### 22.2 Docelowy model runtime

Docelowo:

```text
PoKeys runtime / hardware layer
        ↓
SignalBus
        ↓
Snajper / PAR / Nextion / TSP / LKS
```

Nie budować równoległego toru odświeżania.

### 22.3 Sygnały do SignalBus

Proponowane sygnały:

```text
pokeys_play_online
pokeys_rec_online

sensor_light_lux
sensor_light_raw
sensor_light_status
sensor_light_bus_address

ui_keypad_last_key
ui_keypad_pressed
ui_keypad_event

ui_f1_sw
ui_f2_sw
ui_f3_sw
ui_f4_sw

ui_f1_led
ui_f2_led
ui_f3_led
ui_f4_led

cnc_bridge_dir_x
cnc_bridge_dir_y
cnc_bridge_dir_z
cnc_bridge_ctr_x
cnc_bridge_ctr_y
cnc_bridge_ctr_z
cnc_bridge_rec_in

axis_arm_h_rec_step
axis_arm_v_rec_step
axis_arm_h_rec_dir
axis_arm_v_rec_dir

sensor_cart_limit_end
sensor_arm_v_limit_down
sensor_mass_reg_limit_add
sensor_mass_reg_limit_remove
sensor_rrp_pot_h
sensor_rrp_pot_v
sensor_level_x
sensor_level_y
sensor_level_z
sensor_temp_c
sensor_laser_set
```

### 22.4 Częstotliwości odczytu robocze

Roboczo:

```text
F1-F4 / keypad events: 20–50 ms
BUS light sensor: 100–250 ms
CNC/CTR monitor diagnostyczny: 10–50 ms zależnie od testu
analog level/temp: 100–500 ms
LKS status: około 1 s
```

STEP/CTR impulsowe docelowo wymaga osobnej polityki, liczników lub szybszego toru niż zwykły UI polling.

---

## 23. Git / wdrażanie zmian sandboxa

Na stacji:

```powershell
cd X:\tarzan; git add hardware\tarzanMiniPcSandbox.py; git status; git commit -m "Update mini PC hardware sandbox diagnostics"; git push
```

Na mini PC:

```bash
cd /opt/tarzan
git pull
```

Ważne:

```text
ZIP wygenerowany w rozmowie nie oznacza, że plik jest już na mini PC.
Przed testem zawsze git pull albo ręczne wgranie pliku.
```

---

## 24. Wnioski końcowe

Obecny etap można uznać za zakończony jako:

```text
TARZAN hardware runtime — diagnostyka bazowa bez urządzeń wykonawczych
```

Potwierdzono:

```text
komunikację z PoKeys
zgodność seriali PLAY/REC
odczyt mapy sygnałów
działanie peryferiów UI
działanie BUS/I2C
działanie czujnika światła
odczyt osobnej płytki CNC przez RECK w stanie spoczynku
widoczność przyszłych wejść/krańcówek/analogów
```

Dalszy etap:

```text
1. spięcie wyników sandboxa z hardware runtime TARZANA
2. SignalBus jako źródło prawdy dla stanu live
3. LKS na mini PC
4. TSP server jako kanał do stacji
5. etapowe podłączanie urządzeń końcowych
6. dopiero później impulsy STEP/CTR i ruch osi
```
