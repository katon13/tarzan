# TARZAN — podłączenie i testy: klawiatura 4x3, F1–F4, LED, LCD, Matrix LED

Data robocza: 2026-05-25  
Kontekst: testy hardware runtime na `tarzanMiniPC` przez `hardware/tarzanMiniPcSandbox.py` i `libPoKeys.so`.

## 1. Zasada bezpieczeństwa

Na tym etapie testujemy tylko elementy UI i diagnostykę:

- LCD jako peryferium LCD PoKeys,
- Matrix LED jako peryferium MatrixLED PoKeys,
- klawiaturę matrix jako Matrix Keyboard PoKeys,
- przyciski F1–F4 jako wejścia,
- LED F1–F4 jako ręczny test wyjść UI.

Nie testujemy tutaj:

- STEP,
- DIR,
- ENABLE,
- Pulse Engine Move,
- homingu,
- ruchu osi.

LED-y mogą być podłączone do różnych pinów cyfrowych PoKeys, także do pinów mających zdolności specjalne, ale test LED ma działać tylko przez whitelistę konkretnych sygnałów UI LED i nie może uruchamiać Pulse Engine.

---

## 2. Płytki PoKeys na aktualnym komplecie miniPC

Aktualnie używany komplet na `tarzanMiniPC`:

```text
PLAY / PLAYER = serial 36102
REC  / RECK   = serial 36084
```

Potwierdzone przez:

```text
lsusb / USB descriptor
PoKeysLib scan
sandbox read
```

---

## 3. LCD 1602 / HD44780

### 3.1 LCD PLAY

LCD na płytce PLAY / PLAYER:

```text
PLAY P28 = play_p28_lcd_rw
PLAY P29 = play_p29_lcd_rs / ui_lcd_rs
PLAY P30 = play_p30_lcd_e  / ui_lcd_e
PLAY P31 = play_p31_lcd_db7 / ui_lcd_db7
PLAY P32 = play_p32_lcd_db6 / ui_lcd_db6
PLAY P33 = play_p33_lcd_db5 / ui_lcd_db5
PLAY P34 = play_p34_lcd_db4 / ui_lcd_db4
```

Test wykonany:

```bash
python3 -m hardware.tarzanMiniPcSandbox lcd-test --board PLAY --line1 "TARZAN PLAY" --line2 "LCD OK" --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LCD_TEST
```

Wynik:

```text
[x] PLAY LCD działa fizycznie
```

### 3.2 LCD REC

LCD na płytce REC / RECK:

```text
REC P28 = rec_p28_lcd_rw
REC P29 = rec_p29_lcd_rs
REC P30 = rec_p30_lcd_e
REC P31 = rec_p31_lcd_db7
REC P32 = rec_p32_lcd_db6
REC P33 = rec_p33_lcd_db5
REC P34 = rec_p34_lcd_db4
```

Do testu:

```bash
python3 -m hardware.tarzanMiniPcSandbox lcd-test --board REC --line1 "TARZAN REC" --line2 "LCD OK" --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LCD_TEST
```

### 3.3 Uwaga do przewijania LCD

LCD 1602 / HD44780 nie jest szybkim ekranem graficznym. Przy szybkim scrollu znaki mogą wyglądać, jakby nachodziły na siebie lub mocno mrugały.

Kierunek dla dalszego `lcd-scroll`:

```text
tekst widoczny: 300–500 ms
opcjonalne wygaszenie spacjami: 60–120 ms
następna klatka dopiero po przerwie
```

LCD nadaje się do statusów i prostych komunikatów, nie do bardzo szybkich animacji.

---

## 4. Matrix LED

Matrix LED jest tylko na płytce REC / RECK.

```text
REC P09 = rec_p09_led_data
REC P10 = rec_p10_led_latch
REC P11 = rec_p11_led_clk
```

Potwierdzenie mapy:

```bash
python3 -m hardware.tarzanMiniPcSandbox list --board REC --pins 9-11
python3 -m hardware.tarzanMiniPcSandbox read --board REC --pins 9-11 --lib-path /usr/lib/libPoKeys.so
```

Test Matrix LED:

```bash
python3 -m hardware.tarzanMiniPcSandbox matrix-test --board REC --mode blink --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_MATRIX_TEST
```

Inne tryby:

```bash
python3 -m hardware.tarzanMiniPcSandbox matrix-test --board REC --mode checker --delay 0.25 --repeat 4 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_MATRIX_TEST

python3 -m hardware.tarzanMiniPcSandbox matrix-test --board REC --text "TARZAN" --mode scroll --delay 0.20 --repeat 2 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_MATRIX_TEST
```

Aktualny status:

```text
[x] Matrix LED REC P09-P11 widoczny w mapie
[x] Połączenie z RECK działa
[x] komenda MatrixLED PoKeys przechodzi
```

---

## 5. Przyciski F1–F4

Przyciski F1–F4 są na płytce REC / RECK.

```text
F1 = REC P45 = rec_p45_sw_f1 / ui_f1_sw
F2 = REC P47 = rec_p47_sw_f2 / ui_f2_sw
F3 = REC P49 = rec_p49_sw_f3 / ui_f3_sw
F4 = REC P51 = rec_p51_sw_f4 / ui_f4_sw
```

Test operatorski:

```bash
python3 -m hardware.tarzanMiniPcSandbox buttons-test --board REC --lib-path /usr/lib/libPoKeys.so
```

Wynik z testu:

```text
[x] F1 działa: 1 -> 0 -> 1
[x] F2 działa: 1 -> 0 -> 1
[x] F3 działa: 1 -> 0 -> 1
[x] F4 działa: 1 -> 0 -> 1
```

To znaczy: wejścia są aktywne w logice pull-up / active-low, czyli naciśnięcie daje przejście `1 -> 0`, a puszczenie wraca `0 -> 1`.

---

## 6. LED F1–F4

LED-y F1–F4 są na płytce REC / RECK.

```text
LED F1 = REC P46 = rec_p46_led_f1 / ui_f1_led
LED F2 = REC P48 = rec_p48_led_f2 / ui_f2_led
LED F3 = REC P50 = rec_p50_led_f3 / ui_f3_led
LED F4 = REC P52 = rec_p52_led_f4 / ui_f4_led
```

Ważne: część tych pinów w mapie/sandboxie może mieć sprzętowe zdolności specjalne, np. Pulse Engine. To nie oznacza, że LED nie może być tam podłączony. Oznacza tylko, że test LED musi być zabezpieczony whitelistą po nazwach UI LED i nie może aktywować żadnego ruchu.

Do testu LED używać tylko:

```bash
python3 -m hardware.tarzanMiniPcSandbox led-test --board REC --led F1,F2,F3,F4 --on-time 0.12 --off-time 0.08 --repeat 5 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LED_TEST
```

Szybsze mruganie po kolei:

```bash
python3 -m hardware.tarzanMiniPcSandbox led-test --board REC --led F1,F2,F3,F4 --on-time 0.07 --off-time 0.05 --repeat 8 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LED_TEST
```

Test pojedynczy:

```bash
python3 -m hardware.tarzanMiniPcSandbox led-test --board REC --led F1 --lib-path /usr/lib/libPoKeys.so --confirm YES_TARZAN_LED_TEST
```

Założenie kodowe:

```text
led-test pozwala tylko na:
ui_f1_led
ui_f2_led
ui_f3_led
ui_f4_led
```

Nie wolno robić ogólnego testu output na dowolnym pinie bez tej whitelisty.

---

## 7. Klawiatura matrix 4x3

Fizyczna klawiatura ma układ:

```text
1  2  3
4  5  6
7  8  9
*  0  #
```

Nie należy jej traktować jako prostych `KB1-KB4` do naciskania przez operatora. `PLAY P24-P27` są liniami klawiatury matrix / wejściami funkcji keyboard PoKeys.

Linie w mapie:

```text
PLAY P24 = play_p24_kb4 / ui_kb4
PLAY P25 = play_p25_kb3 / ui_kb3
PLAY P26 = play_p26_kb2 / ui_kb2
PLAY P27 = play_p27_kb1 / ui_kb1
```

Mapowanie wykonane komendą:

```bash
python3 -m hardware.tarzanMiniPcSandbox keypad-map --board PLAY --lib-path /usr/lib/libPoKeys.so
```

Wykryta mapa:

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
[x] PLAY / PLAYER widzi klawiaturę matrix
[x] Matrix Keyboard status działa
[x] wszystkie 12 klawiszy wykryte
[x] mapa row/col kompletna
```

Następny dobry krok kodowy:

```text
dodać keypad-read, który wypisuje już gotowy znak:
Nacisnąłeś: 1
Nacisnąłeś: 2
Nacisnąłeś: #
```

a nie techniczne `index/row/col`.

---

## 8. Podsumowanie aktualnego stanu

```text
[x] PLAY / PLAYER serial 36102 działa przez PoKeysLib
[x] REC / RECK serial 36084 działa przez PoKeysLib

[x] PLAY LCD działa
[ ] REC LCD do osobnego potwierdzenia fizycznego, jeśli nie było jeszcze wykonane

[x] REC Matrix LED: komenda działa po PoKeysLib
[x] REC F1-F4 przyciski działają fizycznie
[x] REC LED F1-F4: przygotowany bezpieczny test whitelistą UI LED

[x] PLAY klawiatura matrix 4x3 działa i jest zmapowana
```

## 9. Ważne zasady dalszej pracy

1. Nie testować UI przez losowe ręczne ustawianie pinów.
2. LCD, Matrix LED i Keyboard traktować jako peryferia PoKeys.
3. LED-y testować tylko przez whitelistę `ui_f1_led..ui_f4_led`.
4. STEP / DIR / ENABLE / Pulse Engine nadal poza tym etapem.
5. Nie zapisywać konfiguracji PoKeys do flash bez osobnej decyzji.
