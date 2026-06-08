# TARZAN — MAPA WYNIKOWA / miniPC JAKO CENTRUM SYSTEMU

**Cel dokumentu:** podręczna mapa logiczna TARZANA po korekcie architektury: miniPC jest serwerem, runtime i źródłem prawdy. Stacja operatorska przenosi ciężar graficznego interfejsu, ale nie przejmuje prawdy systemu ani bezpośredniego sterowania POKSYG/PoKeys.

**Zakres:** to jest główna mapa prowadząca projekt. Nie zastępuje szczegółowych dokumentów modułów; pokazuje tylko główne bloki, relacje, źródła prawdy i kierunek wdrożenia.

**Zasada nadrzędna:**

```text
NIE BUDUJEMY OD NOWA.
ADAPTUJEMY ISTNIEJĄCE TORY.
PROGRAMOWANIE ↔ ELEKTRONIKA ZAWSZE PRZEZ PROTOKÓŁ / SIGNALBUS / TSP / BRIDGE / SNAJPER.
```

---

## 0. Co zmieniono względem poprzedniej mapy i co trzeba dopiąć w kodzie

```text
1. Nextion 7 przeniesiony logicznie na miniPC i docelowo fizycznie podłączony do miniPC po USB.
2. MODE, RRP, generatory i potencjometry są po stronie miniPC.
3. miniPC może działać samodzielnie bez stacji operatorskiej.
4. Stacja operatorska nie jest centrum wykonawczym, tylko ciężkim GUI / lustrem / panelem zdalnym.
5. PAR nie jest źródłem prawdy. Źródłem prawdy jest SignalBus na miniPC.
6. PAR-GUI na stacji i planowany PAR-TEXT/terminal na miniPC mają być klientami tego samego runtime.
7. Nextion 5 zostaje LKS, a Nextion 7 staje się lokalnym panelem operatorskim przy miniPC; wymaga to zmiany konfiguracji portu z Windows/COM na Linux/USB.
```

---

## 1. Diagram główny TARZANA — miniPC jako centrum

```text
┌──────────────────────────────────────────────────────────────┐
│                    miniPC / MAIN RUNTIME                     │
│   Linux + systemd + tarzan-tsp-lks-n5.service                │
│                                                              │
│  ┌───────────┐      ┌───────────┐      ┌──────────────┐      │
│  │ TSP       │ ───▶ │ SignalBus │ ───▶ │ MODE/Safety  │      │
│  │ brama     │      │ prawda    │      │ mode/owner   │      │
│  └─────┬─────┘      └─────┬─────┘      └──────┬───────┘      │
│        │                  │                   │              │
│        │                  │                   ▼              │
│        │                  │         ┌──────────────────┐     │
│        │                  └───────▶ │ RRP / generatory │     │
│        │                            │ rrp_* / sensor_* │     │
│        │                            └────────┬─────────┘     │
│        │                                     ▲               │
│        │                            ┌────────┴─────────┐     │
│        │                            │ Nextion 7        │     │
│        │                            │ panel operatora  │     │
│        │                            └────────┬─────────┘     │
│        │                                     ▼               │
│        │                            ┌──────────────────┐     │
│        └──────────────────────────▶ │ Snajper          │     │
│                                     │ targety/refresh  │     │
│                                     └────────┬─────────┘     │
│                                              ▼               │
│                                     ┌──────────────────┐     │
│                                     │ Bridge/adaptery  │     │
│                                     │ UI / wykonanie   │     │
│                                     └────────┬─────────┘     │
│                                              ▼               │
│                                     ┌──────────────────┐     │
│                                     │ POKSYG / PoKeys  │     │
│                                     │ STEP/DIR/czujniki│     │
│                                     └────────┬─────────┘     │
│                                              │               │
│                         potwierdzenie / odczyt / błąd        │
│                                              ▼               │
│                                     ┌──────────────────┐     │
│                                     │ SignalBus STATUS │     │
│                                     │ IN / STATUS      │     │
│                                     └────────┬─────────┘     │
│                                              │               │
│                    ┌──────────────────┐  ┌────────────────┐  │
│                    │ LKS / Nextion 5  │  │ PAR-TEXT       │  │
│                    │ status/diag.     │  │ terminal miniPC│  │
│                    └──────────────────┘  └────────────────┘  │
└──────────────────────────────┬───────────────────────────────┘
                               │ TCP / TSP / JSONL
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    STACJA OPERATORSKA / GUI                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                 │
│  │ PAR-GUI   │  │ EHR-GUI   │  │ KHR-GUI   │                 │
│  │ lustro    │  │ TAKE/ADRR │  │ korekta   │                 │
│  │ operator  │  │ edycja    │  │ tracking  │                 │
│  └───────────┘  └───────────┘  └───────────┘                 │
│                                                              │
│  Stacja nie jest źródłem prawdy.                             │
│  Pokazuje stan miniPC i wysyła intencje do TSP.              │
└──────────────────────────────────────────────────────────────┘
```

---

**Uproszczenie mapy głównej:** końcówka toru wykonawczego to `POKSYG / PoKeys / STEP-DIR / czujniki`. Nie rozbijamy jej w tej mapie na osobny blok „realny hardware”; szczegóły sprzętowe zostają w dokumentach modułów.

## 1A. Relacje wewnętrzne miniPC — najważniejsze przebiegi

```text
Nextion 7 / operator
  ↓
RRP / potencjometry / generatory / czułość
  ↓
rrp_p1_axis_index / rrp_p2_axis_index
rrp_p1_speed_mul / rrp_p2_speed_mul
sensor_rrp_pot_h / sensor_rrp_pot_v
  ↓
SignalBus miniPC
  ↓
active_mode / transport_state / control_owner
  ↓
MODE / Safety
  ↓
Snajper
  ↓
Bridge / HardwareBridge
  ↓
POKSYG / PoKeys / STEP-DIR / czujniki
```

```text
POKSYG / PoKeys / czujniki
  ↓ potwierdzenie / odczyt / błąd
HardwareBridge
  ↓ set_input / STATUS
SignalBus miniPC
  ├─ LKS / Nextion 5
  ├─ Nextion 7
  ├─ PAR-TEXT / terminal
  └─ TSP Server
       ↓
     PAR-GUI / EHR-GUI / KHR-GUI na stacji
```

```text
PAR-GUI / EHR-GUI / KHR-GUI na stacji
  ↓ intencja / komenda / wybór TAKE
TSP Server miniPC
  ↓
SignalBus miniPC
  ↓
active_mode / transport_state / control_owner
  ↓
MODE / Safety
  ↓
Snajper / Bridge / HardwareBridge
  ↓
POKSYG / PoKeys / STEP-DIR / czujniki
```

Zasada:

```text
Nextion 7 może wywołać RRP / MODE lokalnie,
ale nadal nie omija SignalBus, MODE, Safety ani Bridge.
TSP jest bramą dla klientów zewnętrznych i lokalnych,
ale główna prawda nadal jest w SignalBus miniPC.
```

---

## 1B. Nazwy sygnałów, których nie wolno zgadywać

Te nazwy są punktem odniesienia dla patchy. Najpierw sprawdzić je w `core/tarzanZmienneSygnalowe.py`, potem używać przez SignalBus/TSP.

```text
SYSTEM / RUNTIME:
system_state
runtime_state
tarzan_ready
hardware_state

KLIENCI / PANELE:
par_state
ehr_state
khr_state
lks_state
nextion5_state
nextion7_state

MODE / TRANSPORT / WŁAŚCICIEL:
active_mode
transport_state
control_owner

RRP / POTENCJOMETRY:
rrp_p1_axis_index
rrp_p2_axis_index
rrp_p1_speed_mul
rrp_p2_speed_mul
sensor_rrp_pot_h
sensor_rrp_pot_v

POKSYG / P37 / POTWIERDZENIE:
play_p37_step_disconnect_manual
poksyg_play_p37_ack_ok
poksyg_play_p37_last_value
poksyg_play_p37_last_error
poksyg_last_forced_signal
poksyg_last_forced_value
poksyg_last_forced_ack_ok
poksyg_last_forced_message
```

Zasada:

```text
Nie dopisywać nowych nazw lokalnie w PAR, Nextionie ani Bridge.
Jeżeli sygnał ma być systemowy, najpierw musi być w katalogu sygnałów.
Potwierdzenia i statusy są IN/STATUS, nie OUT.
```

---

## 2. Sens TARZANA po korekcie

TARZAN ma działać także bez stacji operatorskiej.

```text
miniPC
  ↓
SignalBus / MODE / Snajper
  ↓
Bridge / adaptery
  ↓
POKSYG / PoKeys / STEP-DIR / czujniki / Nextion 5 / Nextion 7
  ↓
realny ruch i lokalny status
```

Stacja operatorska jest potrzebna do wygodnej pracy graficznej, ale nie może być jedynym miejscem logiki.

---

## 3. Główne bloki systemu

```text
miniPC / Linux
  └─ tarzan-tsp-lks-n5.service
      ├─ MAIN Runtime
      ├─ TSP Server
      ├─ SignalBus
      ├─ MODE / Safety / control_owner
      ├─ Snajper
      ├─ Bridge / HardwareBridge / adaptery
      ├─ LKS / Nextion 5
      ├─ Nextion 7 lokalnie po USB
      ├─ RRP / potencjometry / generatory
      └─ PAR-TEXT / terminal lokalny

Stacja operatorska Windows
  ├─ PAR-GUI — ciężki panel operatorski / zdalne lustro
  ├─ EHR-GUI — ciężki edytor TAKE / krzywych / ADRR
  └─ KHR-GUI — ciężki podgląd korekty / tracking / wizja

Warstwa wspólna
  ├─ tarzanZmienneSygnalowe.py — katalog sygnałów
  ├─ SignalBus miniPC — aktualna prawda systemu
  ├─ TSP — komunikacja klientów ze źródłem prawdy
  ├─ Snajper — targety i odświeżanie
  └─ Bridge / adaptery — wykonanie na UI lub przez POKSYG/PoKeys
```

---

## 4. Źródła prawdy

```text
core/tarzanZmienneSygnalowe.py
= katalog sygnałów, nazwy, role, kierunek, sprzęt, klasyfikacja

SignalBus na miniPC
= główna aktualna prawda systemu

core/TSP/tarzanTspServer.py
= brama do prawdy miniPC

core/tarzanHardwareBridge.py
= wykonanie przez POKSYG/PoKeys i potwierdzenia ze sprzętu

core/tarzanSnajper.py
= mapa targetów i odświeżanie UI / Nextion / adapterów
```

Zasada:

```text
PAR-GUI nie jest źródłem prawdy.
PAR-TEXT nie jest źródłem prawdy.
Nextion 7 nie jest źródłem prawdy.
Źródłem prawdy runtime jest SignalBus na miniPC.
```

---

## 5. Przebieg STACJA/PAR-GUI → miniPC → Hardware

```text
PAR-GUI / operator na stacji
  ↓ intencja / komenda
editor/PAR/tarzanParBridge.py
  ↓ TCP JSONL / TSP
core/TSP/tarzanTspServer.py na miniPC
  ↓ walidacja
SignalBus miniPC
  ↓
active_mode / transport_state / control_owner
  ↓
MODE / Safety
  ↓
Snajper / Bridge / HardwareBridge
  ↓
POKSYG / PoKeys / STEP-DIR / czujniki
```

Zasada:

```text
PAR-GUI nie wykonuje ruchu.
PAR-GUI prosi miniPC o wykonanie.
miniPC wykonuje albo odrzuca.
```

---

## 6. Przebieg miniPC lokalnie bez stacji

```text
Nextion 7 / potencjometr / RRP / PAR-TEXT
  ↓ lokalna intencja operatora
rrp_p1_axis_index / rrp_p2_axis_index
sensor_rrp_pot_h / sensor_rrp_pot_v
  ↓
SignalBus miniPC
  ↓
active_mode / transport_state / control_owner
  ↓
MODE / Safety
  ↓
Snajper / Bridge / HardwareBridge
  ↓
POKSYG / PoKeys / STEP-DIR / czujniki
```

Zasada:

```text
TARZAN może działać bez Windows/stacji.
Stacja jest wygodnym GUI, nie warunkiem wykonania.
```

---

## 7. Przebieg Hardware → potwierdzenie → PAR/LKS/Nextion 7

```text
Hardware / PoKeys / POKSYG
  ↓ potwierdzenie / odczyt / błąd
HardwareBridge
  ↓ set_input / STATUS
SignalBus miniPC
  ↓
TSP Server
  ├─ PAR-GUI przez subscribe/get_state
  ├─ PAR-TEXT / terminal lokalny
  ├─ LKS / Nextion 5
  └─ Nextion 7 lokalny panel operatora
```

Przykład P37:

```text
play_p37_step_disconnect_manual wymuszone
  ↓
potwierdzenie OK / FAIL
  ↓
poksyg_play_p37_ack_ok
poksyg_play_p37_last_value
poksyg_last_forced_*
  ↓
PAR-GUI log + LKS status + Nextion 7 status
```

---

## 8. Rola LKS / Nextion 5

```text
LKS / Nextion 5
= lokalny panel statusu przy miniPC
= boot, diagnostyka punktowa, ważne potwierdzenia, stan core
```

Nie robi pełnego PAR, EHR ani KHR.

---

## 9. Rola Nextion 7 po korekcie

```text
Nextion 7
= lokalny panel operatora na miniPC
= docelowo podłączony fizycznie do miniPC po USB
= tryby MODE, RRP, potencjometry, operator, TAKE/sensory według dostępnych ekranów
= wymaga zmiany konfiguracji portu z Windows/COM na Linux/USB, np. /dev/ttyUSBx albo /dev/serial/by-id/...
```

Nextion 7 nie jest już traktowany jako ekran stacji.  
Jest częścią lokalnego runtime przy elektronice. Logika i przepływ informacji zostaje jak w obecnym PAR, ale bez przenoszenia ciężkiego GUI stacji na miniPC.

---

## 10. Rola PAR-GUI

```text
PAR-GUI
= ciężki graficzny panel operatora na stacji Windows
= pokazuje stan miniPC
= wysyła intencje do TSP
= nie trzyma głównego MODE
= nie jest źródłem prawdy
= nie steruje pinami bezpośrednio
```

PAR-GUI jest zdalnym lustrem i centrum wygodnej administracji.

---

## 11. Rola PAR-TEXT / terminal

```text
PAR-TEXT / terminal
= planowany lekki lokalny sposób obsługi miniPC bez grafiki
= komendy diagnostyczne i operatorskie
= klient tego samego runtime
= nie tworzy drugiej logiki PAR
```

To może działać na miniPC nawet bez stacji, ale nie jest osobnym źródłem prawdy.

Zasada:

```text
PAR-TEXT jest klientem terminalowym tego samego TSP/SignalBus.
Nie ma własnej logiki wykonawczej i nie tworzy drugiego runtime.
```

---

## 12. Rola MODE

MODE zostaje po stronie miniPC i współpracuje z PAR-TEXT / terminalem.

```text
active_mode
transport_state
control_owner
```

Tryby:

```text
tM   — Tryb Manualny
tMAS — Tryb Manual Assisted / manual wspomagany
tAA  — Tryb Auto Actor / automatyka aktora
tAT  — Tryb Auto Track / automatyczne śledzenie
t3D  — Tryb 3D / ruch przestrzenny
tAD  — Tryb Auto Dolly / automatyczny najazd/przejazd
tFX  — Tryb Efektowy / efekty specjalne ruchu
```

Transport:

```text
STOP  — zatrzymanie
REC   — nagrywanie
PLAY  — odtwarzanie
PAUSE — pauza
```

---

## 13. Rola EHR

```text
EHR-GUI na stacji
= ciężka edycja TAKE, krzywych, ADRR, STEP matrix

EHR-runtime / wykonanie
= docelowo po stronie miniPC / TSP / SignalBus / MODE
```

Zasada TAKE:

```text
EHR-GUI może przygotować TAKE na stacji.
Zatwierdzony TAKE musi trafić do miniPC jako dane/protokół.
Wykonanie ruchu odbywa się na miniPC przez SignalBus / MODE / Bridge.
```

EHR nie może mieć osobnego wykonania pinów poza miniPC.

---

## 14. Rola KHR

```text
KHR-GUI na stacji
= ciężki podgląd, analiza, tracking, wizja

KHR-runtime / korekta
= docelowo przez SignalBus / MODE / control_owner na miniPC
```

KHR nie steruje pinami prywatnie.

---

## 15. Rola Snajpera

Snajper to dyrygent targetów i odświeżania.

```text
SignalBus
  ↓
Snajper / Caliber / Bullet / Target
  ↓
PAR-GUI / Nextion 7 / LKS / TFD / adaptery
```

Zasada:

```text
nie robić refresh all
nie rozsyłać ręcznie tego samego sygnału w wielu miejscach
jeżeli target istnieje w Snajperze, użyć Snajpera
```

---

## 16. Nextion 5 vs Nextion 7

```text
Nextion 5
= LKS, status, boot, diagnostyka, lokalna kontrolka systemu

Nextion 7
= lokalny panel operatora miniPC, tryby, RRP, potencjometry, podglądy
```

Oba są po stronie miniPC, ale mają różne role.

---

## 17. Logi i statusy

```text
journalctl
= systemowy log Linuxa usługi tarzan-tsp-lks-n5.service

PAR-GUI log
= log operatorski na stacji, odbity z TSP i działań operatora

trace
= podgląd jednego wybranego sygnału na żywo

LKS status
= skrócony trwały status na Nextion 5

Nextion 7 status
= lokalny status operatorski na miniPC
```

---

## 18. Czego nie wolno robić

```text
1. Nie przenosić źródła prawdy do PAR-GUI.
2. Nie robić osobnej logiki PAR-TEXT obok TSP/SignalBus.
3. Nie traktować Nextion 7 jako ekranu stacji.
4. Nie sterować pinami bezpośrednio z PAR-GUI.
5. Nie omijać MODE/Safety/control_owner.
6. Nie tworzyć drugiego runtime na stacji.
7. Nie zostawiać TSP w MAIN/LIVE jako symulacji.
8. Nie mieszać roli LKS i lokalnego operatora Nextion 7.
9. Nie logować FAST 10 ms ramka po ramce.
10. Nie budować nowego toru, jeśli istnieje SignalBus / TSP / Bridge / Snajper.
```

---

## 18A. Uwagi zgodności z obecnym repo

Ta mapa jest nadrzędnym drogowskazem. Szczegóły wykonania zostają w dokumentach i plikach konkretnych modułów.

```text
1. Nextion 7 jest docelowo lokalny na miniPC, ale obecna konfiguracja portu może jeszcze wskazywać port Windows/COM.
2. PAR-TEXT / terminal jest nazwą kierunku i lekkiego klienta; nie tworzyć osobnego drugiego PAR.
3. RRP i potencjometry muszą iść przez istniejące sygnały rrp_* oraz sensor_rrp_*.
4. MODE musi czytać i ustawiać active_mode, transport_state oraz control_owner.
5. POKSYG/P37 musi używać istniejących sygnałów play_p37_step_disconnect_manual i poksyg_*_ack/status.
6. W MAIN/LIVE TSP nie może udawać stanu testowego, tylko czytać SignalBus miniPC.
```

---

## 19. Kolejność aktualizacji po tej korekcie

```text
1. Zatwierdzić tę mapę jako nową wersję główną.
2. Dopisać Nextion 7 jako lokalny panel miniPC.
3. Dopisać MODE / RRP / generatory / potencjometry po stronie miniPC.
4. Dopisać PAR-GUI jako zdalne lustro, nie źródło prawdy.
5. Sprawdzić porty Nextion 7 na miniPC.
6. Potem wrócić do ETAP 1ZA / POKSYG status LKS.
7. Potem system_state / runtime_state.
8. Dopiero potem MODE / RRP / osie / EHR / KHR.
```

---

## 20. Hasło kontrolne

```text
JEŻELI COŚ MA WYKONAĆ RUCH ALBO ZMIENIĆ STAN SPRZĘTU:
MUSI PRZEJŚĆ PRZEZ miniPC / SignalBus / MODE / Bridge.

JEŻELI COŚ JEST NA STACJI:
JEST GUI, LUSTREM ALBO EDYTOREM,
NIE ŹRÓDŁEM PRAWDY.
```

---

# Słownik bloków i skrótów

### GŁÓWNE BLOKI

```text
TARZAN
= cały system inteligentnego ramienia kamerowego: mechanika + elektronika + software.

PAR — PANEL ADMINISTRACJI RUCHU
= główny panel operatora na stacji Windows; administracja TEST/LIVE i sterowanie przez TSP.

TSP — TARZAN SYSTEM PROTOCOL
= protokół i serwer/proces komunikacji miniPC ze stacją; brama do SignalBus i hardware.

LKS — LAMPKA KONTROLNA SYSTEMU
= lokalny status/panel przy miniPC; Nextion 5, boot, diagnostyka, ważne stany.

EHR — EDYTOR HARMONOGRAMU RUCHU
= przygotowanie TAKE, krzywych, ADRR, STEP matrix i przebiegu ruchu.

KHR — KOREKTOR HARMONOGRAMU RUCHU
= korekta ruchu przez tracking, obraz, czujniki, LEVEL/FACE; nie steruje pinami bokiem.

ADRR — ACCELERATION / DECELERATION / RHYTHM / RAMP
= model łagodnego prowadzenia ruchu osi: przyspieszanie, hamowanie, rytm i rampa.

KRO — KOREKTOR RELACJI OSI
= relacje między osiami i korekta geometrii ruchu.

TFD — TARZAN FRAME DATA
= ramka danych na podgląd.

Nextion 5
= ekran LKS przy miniPC; lokalny status systemu.

Nextion 7
= lokalny panel operatora przy miniPC; MODE, RRP, TAKE, sensory i podglądy.

SOK — STEROWNIK OPERATORA KAMERY
= blok sterowania operatorskiego kamerą.

SNAJPER
= dyrygent targetów i odświeżania; prowadzi, gdzie ma trafić zmiana sygnału.
```

### BLOKI WYKONAWCZE

```text
MAIN Runtime
= główny runtime miniPC uruchamiany przez usługę tarzan-tsp-lks-n5.service.

tarzan-tsp-lks-n5.service
= usługa Linux/systemd na miniPC; automatycznie startuje TARZAN runtime po uruchomieniu miniPC.

SignalBus
= aktualna tablica wartości sygnałów w czasie pracy systemu.

tarzanZmienneSygnalowe.py
= katalog sygnałów; źródło nazw, ról, kierunków i klasyfikacji.

MODE
= tryby pracy i transport: active_mode, transport_state, STOP, REC, PLAY, PAUSE.

Bridge
= most między SignalBus a wykonaniem w UI albo sprzęcie.

Adapter
= dopasowanie jednego urządzenia/panelu do wspólnego toru sygnałów.

HardwareBridge
= most miniPC do POKSYG/PoKeys, czujników i wyjść.
```

### SPRZĘT I SYGNAŁY

```text
PoKeys
= karta wejść/wyjść USB do elektroniki.

POKSYG
= tor/sygnały PoKeys używane do wymuszeń i potwierdzeń sprzętu.

P37
= pin PLAY 37; bezpieczeństwo odłączenia STEP dla ręcznego ruchu ramienia.

STEP
= impuls kroku dla sterownika silnika krokowego.

DIR — DIRECTION
= kierunek ruchu silnika krokowego.

ENABLE
= włączenie/aktywacja sterownika osi.

ACK — ACKNOWLEDGEMENT
= potwierdzenie odbioru albo wykonania komendy.

ACK OK — ACKNOWLEDGEMENT OK
= sprzęt potwierdził wykonanie komendy.

ACK ERROR — ACKNOWLEDGEMENT ERROR
= sprzęt zgłosił błąd albo brak wykonania.

OUT — OUTPUT
= sygnał wyjściowy; rozkaz do sprzętu.

IN — INPUT
= sygnał wejściowy; odczyt ze sprzętu albo czujnika.

STATUS
= stan systemu albo ostatni wynik; nie steruje sprzętem.

FAST
= szybki tor ruchu, np. 10 ms; nie logować każdej ramki.

SYSTEM
= sygnały stanu całego systemu: system_state, runtime_state, tarzan_ready.

RRP SIGNALS
= rrp_p1_axis_index, rrp_p2_axis_index, rrp_p1_speed_mul, rrp_p2_speed_mul.

RRP POT
= sensor_rrp_pot_h, sensor_rrp_pot_v.

TAKE
= zapis/przebieg ruchu do odtworzenia.

CLAP
= znacznik/zdarzenie synchronizacji w TAKE.
```

### STANY I LOGI

```text
control_owner
= informacja, kto aktualnie ma prawo prowadzić sterowanie.

system_state
= główny stan systemu, np. BOOTING, READY, ERROR.

runtime_state
= stan runtime miniPC, np. READY_FOR_PAR.

tarzan_ready
= sygnał, że system jest gotowy do dalszej pracy.

WRITE_DENIED
= odmowa zapisu sygnału, np. konflikt właściciela sterowania.

journalctl
= systemowy podgląd logów usługi TARZAN na Linux miniPC.

PAR log
= log operatorski w PAR: co wysłano i co wróciło.

trace
= podgląd jednego wybranego sygnału na żywo.

snapshot
= jednorazowy zrzut aktualnego stanu sygnałów.

payload
= paczka danych wysyłana przez TSP do PAR/LKS.

JSONL
= format komunikacji: jedna wiadomość JSON w jednej linii.
```
