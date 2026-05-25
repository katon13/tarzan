# TARZAN — LKS-N5: sprzętowa tablica komunikatów tarzanMiniPC

Data: 2026-05-25  
Status: ustalenie koncepcji / dokumentacja etapu  
Nazwa robocza: **LKS-N5**  
Pełna nazwa: **Lampka Kontrolna Systemu — Nextion 5**  
Rola opisowa: **sprzętowa tablica komunikatów TARZAN dla tarzanMiniPC**

---

## 1. Przydzielona nazwa

Dla małego ekranu Nextion 5 przyjmujemy nazwę:

```text
LKS-N5
```

Rozwinięcie:

```text
Lampka Kontrolna Systemu — Nextion 5
```

Opis funkcjonalny:

```text
sprzętowa tablica komunikatów tarzanMiniPC
```

Czyli:

```text
LKS-TTY = tekstowa Lampka Kontrolna Systemu na lokalnym TTY mini PC
LKS-N5  = wizualna Lampka Kontrolna Systemu na fizycznym Nextion 5
```

---

## 2. Główna decyzja projektowa

Nextion 5 **nie jest modułem PAR**.

Nextion 5 **nie jest drugim panelem operatorskim**.

Nextion 5 **nie jest drugim Nextionem 7**.

Nextion 5 ma być:

```text
wizualną, sprzętową tablicą komunikatów systemowych tarzanMiniPC
```

Czyli ma obrazować system pracy mini PC:

```text
boot Linuxa
ładowanie usług
status TSP
status hardware
status PoKeys
status Nextion 7
status połączenia PAR jako informacja, nie sterowanie
ostrzeżenia
błędy
potwierdzenia
TAKE / CLAP / marker jako główne komunikaty systemowe
```

---

## 3. Najważniejsze rozdzielenie ról

### Nextion 7

```text
główny ekran operatorski PAR / KHR / RRP / ustawienia / praca operatora
```

Nextion 7 należy do świata operatorskiego i PAR.

### Nextion 5 / LKS-N5

```text
sprzętowa tablica komunikatów mini PC
wizualizacja stanu pracy systemu
niezależna od PAR
```

Nextion 5 należy do świata mini PC, Linuxa, systemd, LKS, TSP i hardware runtime.

---

## 4. Czego nie robić

Nie podpinać LKS-N5 bezpośrednio pod PAR jako ekran HMI.

Nie robić z LKS-N5:

```text
drugiego PAR
drugiego Nextion 7
panelu ustawień
ciężkiego ekranu operatorskiego
monitora wszystkich logów
kopii layoutu PAR
```

PAR może być tylko jednym ze źródeł statusu:

```text
PAR: OFFLINE
PAR: CONNECTED
PAR: LOST
PAR: COMMAND RECEIVED
```

Ale PAR **nie steruje bezpośrednio LKS-N5**.

---

## 5. Docelowa architektura

Model docelowy:

```text
Linux / systemd / tarzanMiniPC
        ↓
TSP server / hardware runtime / LKS
        ↓
LKS-N5 Bridge
        ↓
Nextion 5
```

Nie:

```text
PAR → Nextion 5
```

PAR pozostaje na tarzanStacja.  
LKS-N5 jest po stronie tarzanMiniPC.

---

## 6. Zasada odciążenia mini PC

Mini PC **nie renderuje grafiki**.

Mini PC wysyła tylko krótkie znaczenie komunikatu:

```text
READY
BOOTING
TSP_OK
POKEYS_REC_OK
NEXTION7_LOST
TAKE_001
CLAP_MARKED
ERROR_POKEYS_LOST
```

Nextion 5 ma już wgrane własne:

```text
strony
tła
grafiki
ikony
kolory
ramki
plansze ostrzeżeń
plansze błędów
plansze TAKE / CLAP
```

Czyli:

```text
mini PC wysyła sens
Nextion 5 robi obraz
```

To jest kluczowa zasada LKS-N5.

---

## 7. Charakter urządzenia

LKS-N5 ma działać jak:

```text
sprzętowa tablica komunikatów / lampka życia systemu / mały billboard stanu tarzanMiniPC
```

Normalny stan:

```text
TARZAN NODE
READY
TSP: OK
PLAY: OK
REC: OK
PAR: WAITING / CONNECTED
N7: OK / WAITING
```

Komunikat TAKE:

```text
TAKE 001
TC 00:00:12:08
CLAP READY / CLAP MARKED
```

Ostrzeżenie:

```text
WARNING
NEXTION 7 LOST
CHECK USB
```

Błąd krytyczny:

```text
ERROR
POKEYS REC LOST
SYSTEM CHECK REQUIRED
```

---

## 8. Start systemu / intro

Dobrym kierunkiem jest rozpoczęcie od planszy intro oraz komunikatu ładowania systemu.

Sekwencja startowa:

```text
1. Zasilanie mini PC
2. Nextion 5 pokazuje własne intro TARZAN NODE
3. Linux startuje
4. LKS-N5 service uruchamia się możliwie wcześnie
5. Ekran pokazuje LOADING SYSTEM
6. Potem TSP STARTING / TSP OK
7. Potem PLAY BOARD OK / REC BOARD OK
8. Potem NEXTION 7 WAITING / CONNECTED
9. Potem PAR WAITING / CONNECTED
10. Normalnie READY
11. Przy problemie WARNING / ERROR
```

To nie ma być bootlog Debiana.

Nie pokazujemy:

```text
systemd raw log
mount details
pełne logi kernela
surowy terminal
```

Pokazujemy estetyczną wizualizację etapów:

```text
BOOTING
LOADING TARZAN NODE
STARTING SERVICES
CHECKING HARDWARE
READY
```

---

## 9. Proponowane strony Nextion 5

Minimalny zestaw stron HMI dla LKS-N5:

```text
boot_intro      — logo / start TARZAN NODE
boot_loading    — ładowanie Linuxa / systemu
boot_check      — sprawdzanie usług i hardware
ready_main      — system gotowy
status_main     — skrócony status node
message_main    — neutralny komunikat
confirm_main    — potwierdzenie akcji
warning_main    — ostrzeżenie
error_main      — błąd krytyczny
take_main       — TAKE / TC / marker
clap_main       — CLAP / marker wysłany
```

---

## 10. Proponowany model danych

Najprostszy model:

```text
lks_scene
```

Możliwe wartości:

```text
boot
loading
checking
ready
status
take
clap
warning
error
confirm
```

Pola pomocnicze:

```text
lks_title
lks_line1
lks_line2
lks_line3
lks_level
lks_timeout_ms
lks_take_number
lks_take_tc
lks_marker
lks_error_code
lks_warning_code
```

Przykład TAKE:

```text
lks_scene=take
lks_take_number=001
lks_take_tc=00:00:12:08
lks_marker=CLAP_READY
```

Przykład ostrzeżenia:

```text
lks_scene=warning
lks_title=WARNING
lks_line1=NEXTION 7 LOST
lks_line2=CHECK USB
lks_warning_code=N7_LOST
```

Przykład gotowości:

```text
lks_scene=ready
lks_title=TARZAN NODE
lks_line1=TSP OK
lks_line2=PLAY OK / REC OK
lks_line3=PAR WAITING
```

---

## 11. Co trafia na LKS-N5

Na LKS-N5 powinny trafiać tylko główne informacje:

```text
BOOT / LOADING
LINUX OK
TSP STARTING / OK / ERROR
PLAY PoKeys OK / LOST
REC PoKeys OK / LOST
BUS/I2C OK / ERROR
Nextion 7 WAITING / CONNECTED / LOST
PAR WAITING / CONNECTED / LOST
TAKE number
CLAP / marker
WARNING
ERROR
STOP / safety alert
```

Nie trafiają tam:

```text
pełne logi PAR
pełne logi Python UI
każde kliknięcie operatora
każda komenda Nextion 7
pełny spam FAST
surowe dane debugowe
```

---

## 12. Relacja z TSP

TSP może być źródłem statusu, ale LKS-N5 nie jest klientem PAR.

TSP dostarcza stan:

```text
czy serwer żyje
czy tarzanStacja jest połączona
czy są błędy
czy hardware jest wykryty
czy Nextion 7 jest dostępny
czy pojawił się komunikat TAKE / CLAP / WARNING / ERROR
```

LKS-N5 wizualizuje te stany w formie sprzętowej tablicy komunikatów.

---

## 13. Możliwy serwis systemd

Docelowo można utworzyć usługę:

```text
tarzan-lks-n5.service
```

Rola usługi:

```text
uruchamia się po starcie Linuxa
otwiera port Nextion 5
wysyła planszę loading
monitoruje TSP / hardware runtime / status mini PC
wysyła krótkie komendy do Nextion 5
nie steruje PAR
nie renderuje grafiki
```

Możliwy moduł:

```text
core/TSP/tarzanTspLksNextion5.py
```

albo osobna warstwa hardware:

```text
hardware/tarzanNextionLksN5.py
```

Decyzję o lokalizacji zostawić na etap implementacji.

---

## 14. Zakres implementacji przyszłego etapu

Przyszły etap powinien mieć zakres:

```text
WARSTWA:
LKS / Linux / mini PC / Nextion 5

CEL:
uruchomić LKS-N5 jako sprzętową tablicę komunikatów

NIE RUSZAM:
PAR layout
Nextion 7
Snajper głównego HMI
EHR
TAKE generator
KHR
PoKeys runtime poza odczytem statusu

ZMIENIAM:
warstwę statusów LKS-N5
komendy do Nextion 5
mapowanie stanów systemu na strony/grafiki Nextiona 5
```

---

## 15. Konkluzja

Przyjęta decyzja:

```text
Nextion 5 = LKS-N5 = Lampka Kontrolna Systemu — Nextion 5
```

Rola:

```text
sprzętowa tablica komunikatów tarzanMiniPC
```

Zasada:

```text
mini PC wysyła znaczenie
Nextion 5 pokazuje gotową grafikę
```

Nie jest to PAR.  
Nie jest to ekran operatorski.  
Nie jest to ciężkie UI.  
To jest wizualna lampka życia i komunikatów systemu pracy tarzanMiniPC.
