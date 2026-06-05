# TARZAN — architektura źródła prawdy: Linux / LKS-TSP-core / SignalBus / PAR / Nextion

**Wersja:** v3  
**Cel:** utrwalić nadrzędny schemat architektury TARZANA, żeby nie mieszać ról LKS/TSP, PAR, EHR, KHR, Nextion 5 i Nextion 7.

---

## 1. Zasada nadrzędna

Przyjmujemy jako źródło prawdy następujący układ:

```text
1. Linux / miniPC
   uruchamia runtime TARZANA

2. LKS / TSP / core
   pilnuje systemu, testuje, monitoruje, obsługuje elektronikę
   + Nextion 5 jako lokalny wykonawca/status/operator-panel LKS

3. SignalBus
   tablica aktualnego stanu sygnałów

4. Snajper / Bridge / adaptery
   rozprowadzają sygnały do fizycznych i programowych celów
   + tutaj spięty jest Nextion 7 przez aktualny tor PAR/Bridge/Snajper

5. PAR
   zewnętrznie steruje i administruje przez TSP

6. EHR / KHR
   EHR przygotowuje ruch / TAKE / przebiegi
   KHR koryguje / wspiera ruch z obrazu, czujników i logiki korekt
   PAR może wpływać na EHR/KHR jako zewnętrzna administracja przez TSP / SignalBus

7. Nextion 5 / Nextion 7 — rozróżnienie roli
   Nextion 5 = lokalny panel LKS przy miniPC, status, boot, diagnostyka punktowa
   Nextion 7 = panel związany z PAR/Bridge/Snajper, dotychczasowy tor operatorski
```

---

## 2. Schemat blokowy

```text
┌──────────────────────────────────────────────────────────────┐
│ 1. Linux / miniPC                                            │
│    startuje system, usługi, runtime TARZANA                  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. LKS / TSP / core                                          │
│    integralny nadzorca miniPC                                │
│    testuje, monitoruje, pilnuje PoKeys, usługi, Nextion 5    │
│    obsługuje elektronikę przy systemie                       │
│                                                              │
│    Nextion 5 należy do tej warstwy jako lokalny panel LKS:   │
│    boot_intro / boot_loading / boot_* / ready_main /         │
│    intro_status / status_main                                │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. SignalBus                                                  │
│    tablica aktualnego stanu sygnałów                          │
│    tu widać prawdę runtime                                    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Snajper / Bridge / adaptery                                │
│    dystrybucja sygnałów do celów                              │
│    adaptery sprzętowe, Bridge, targety UI                     │
│                                                              │
│    Nextion 7 jest tutaj: tor PAR / Bridge / Snajper.           │
│    Nie przenosimy go do LKS-N5 i nie zmieniamy tej obsługi.    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. PAR                                                        │
│    zewnętrzna administracja i sterowanie operatorskie         │
│    TEST / LIVE                                                │
│    steruje przez TSP rozmieszczonymi sygnałami i elektroniką  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. EHR / KHR                                                  │
│    EHR przygotowuje TAKE, przebiegi, model ruchu, STEP stream │
│    KHR może korygować / wspierać ruch przez warstwę korekt     │
│    PAR może wpływać na EHR/KHR przez TSP / SignalBus           │
│    EHR/KHR nie zastępują runtime LKS/TSP/core                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Rola LKS / TSP / core

LKS/TSP/core to nie jest dodatek do PAR. To integralna, najbardziej zespolona część systemu miniPC przy elektronice.

Odpowiada za:

```text
- start runtime TARZANA,
- testy startowe,
- monitoring usług,
- monitoring PoKeys,
- monitoring Nextion 5,
- monitoring urządzeń i sygnałów,
- utrzymywanie SignalBus,
- wystawianie TSP dla PAR,
- raportowanie stanu do LKS-N5 / Nextion 5,
- wykonanie komend przychodzących z PAR przez TSP.
```

TSP może przygotować system aż do momentu, gdy PAR przejdzie w LIVE i przejmie administrację operatorską.

---

## 4. Rola PAR

PAR jest zewnętrznym systemem administracji, testowania i sterowania operatorskiego.

PAR ma prawo docelowo sterować elektroniką, ale przez właściwy tor:

```text
PAR
  ↓
TSP
  ↓
SignalBus
  ↓
Snajper / Bridge / adaptery
  ↓
hardware / UI / Nextion / PoKeys / osie
```

PAR nie jest tylko podglądem. PAR jest główną administracją TEST/LIVE, ale nie zastępuje wewnętrznego nadzorcy core na miniPC.

PAR może też wpływać na warstwy EHR i KHR, ponieważ są one częścią większego systemu sterowania ruchem:

```text
PAR
  ↓
TSP / SignalBus
  ↓
EHR / KHR / MODE / korekty
  ↓
Snajper / adaptery
  ↓
hardware / osie / elektronika
```

Znaczy to:

```text
- PAR może wybierać TAKE / tryb / aktywną konfigurację ruchu,
- PAR może uruchamiać albo zatrzymywać przygotowany przebieg,
- PAR może zmieniać parametry pracy i testów,
- PAR może aktywować lub dezaktywować korekty KHR, jeśli dany etap na to pozwala,
- PAR może być administracją dla EHR/KHR, ale nie powinien omijać TSP/SignalBus.
```

---

## 5. Rola Nextion 5

Nextion 5 należy do warstwy LKS/TSP/core.

Jest lokalnym panelem przy miniPC:

```text
boot_intro
boot_loading
boot_linux
boot_services
boot_hardware
boot_test
ready_main
intro_status
status_main
```

Zasady Nextion 5:

```text
- pokazuje start systemu,
- pokazuje status LKS,
- pokazuje diagnostykę punktową,
- status_main ma 30 dual-state buttonów,
- kliknięcie komponentu robi diagnostykę punktową,
- intro_status ma własny timer i sam przechodzi do status_main,
- Python nie przerywa intro_status,
- LKS-N5 nie wykonuje automatycznego ruchu osi bez świadomego etapu/testu.
```

Nextion 5 obrazuje i obsługuje lokalny nadzór LKS. Jest przy warstwie 2, nie przy PAR.

---

## 6. Rola Nextion 7

Nextion 7 jest związany z aktualnym torem PAR / Bridge / Snajper.

To oznacza:

```text
- Nextion 7 jest spięty z warstwą 4: Snajper / Bridge / adaptery,
- jego obecnej obsługi teraz nie zmieniamy,
- nie przenosimy Nextion 7 do LKS-N5,
- nie mieszamy go z boot/status Nextion 5,
- Nextion 7 pozostaje częścią istniejącego operatorskiego toru PAR.
```

Korekta ważna:

```text
Nextion 5 ≠ Nextion 7
```

```text
Nextion 5 = lokalny LKS / boot / status / diagnostyka przy miniPC
Nextion 7 = aktualny tor PAR / Bridge / Snajper / operatorski panel
```

---

## 7. Rola EHR / KHR

EHR i KHR są warstwami ruchu i korekt, ale nie są głównym runtime nadzorczym miniPC.

```text
EHR = przygotowanie TAKE, przebiegów, modelu ruchu i STEP streamu
KHR = warstwa korekty / wspomagania ruchu z obrazu, czujników i logiki korekt
```

PAR może wpływać na EHR/KHR, bo PAR jest zewnętrzną administracją i panelem LIVE. Nie oznacza to jednak obejścia core.

Poprawny tor:

```text
PAR → TSP → SignalBus → EHR/KHR/MODE/korekta → Snajper/adaptery → hardware
```

Niepoprawny tor:

```text
PAR → prywatny skrót do EHR/KHR → prywatny skrót do pinów
```

Zasada:

```text
PAR administruje i steruje.
EHR komponuje ruch.
KHR koryguje / wspiera ruch.
TSP/LKS/core nadzoruje runtime.
SignalBus pokazuje aktualny stan.
Snajper/adaptery rozprowadzają wykonanie.
```

---

## 8. Rola SignalBus

SignalBus jest tablicą aktualnego stanu sygnałów.

Nie oznacza to, że SignalBus jest samodzielnym procesem decyzyjnym. Praktycznie:

```text
LKS/TSP/core utrzymuje i nadzoruje stan,
SignalBus pokazuje aktualną prawdę runtime,
Snajper/Bridge/adaptery rozprowadzają stan,
PAR wydaje komendy przez TSP,
EHR przygotowuje przebiegi ruchu.
```

---

## 9. Właściciel sterowania

Żeby nie pogubić kontroli, system powinien rozróżniać właściciela sterowania:

```text
TSP_BOOT       — system startuje i testuje urządzenia
TSP_SERVICE    — miniPC utrzymuje system bez aktywnego PAR
PAR_LIVE       — PAR przejął administrację operatorską
EHR_PLAYBACK   — odtwarzanie przygotowanego TAKE / przebiegu
LKS_DIAGNOSTIC — diagnostyka punktowa z Nextion 5 / LKS
```

To nie ogranicza PAR. To tylko porządkuje, kto w danej chwili wydaje komendy.

---

## 10. Ograniczenia tej zasady

Ta zasada jest słuszna, ale ma ograniczenia, których trzeba pilnować:

### 10.1. Nie budować równoległych torów

Nie wolno robić osobnych ścieżek typu:

```text
PAR bezpośrednio do pinów,
TSP osobno,
Bridge osobno,
LKS osobno,
SignalBus osobno.
```

Poprawnie:

```text
PAR → TSP → SignalBus → Snajper / Bridge / adaptery → hardware
```

### 10.2. Nie mieszać Nextion 5 i Nextion 7

```text
Nextion 5 = lokalny LKS / status / boot
Nextion 7 = tor PAR / Bridge / Snajper
```

Tego teraz nie zmieniamy.

### 10.3. LKS/TSP ma nadzorować stale

PAR może przejąć administrację, ale LKS/TSP/core na miniPC nadal pilnuje systemu, usług, sprzętu i komunikacji.

### 10.4. EHR/KHR nie są runtime nadzorczym

EHR przygotowuje ruch, przebiegi i TAKE, a KHR koryguje lub wspiera ruch, ale EHR/KHR nie zastępują LKS/TSP/core.

### 10.5. PAR ma sterować przez TSP

PAR ma prawo sterować elektroniką, ale jako zewnętrzny administrator przez TSP i ustalone sygnały.

---

## 11. Najkrótsza formuła

```text
Linux uruchamia.
LKS/TSP/core nadzoruje.
SignalBus pokazuje stan.
Snajper/Bridge/adaptery rozprowadzają.
PAR administruje i steruje z zewnątrz przez TSP.
EHR przygotowuje ruch.
KHR koryguje / wspiera ruch.
PAR może wpływać na EHR/KHR przez TSP/SignalBus.
Nextion 5 pokazuje lokalny status LKS.
Nextion 7 zostaje w torze PAR/Bridge/Snajper.
```
