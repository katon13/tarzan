# TARZAN MAIN RUNTIME — plan pełnego zespolenia LKS/TSP/PAR/EHR/KHR

**Wersja:** v4 — pełna wersja v2 z naniesionymi uwagami JUNI, bez skracania dokumentu  
**Cel:** pełne zespolenie istniejących bloków TARZANA w jeden spójny organizm runtime.  
**Zasada nadrzędna 1:** NIE BUDUJEMY NICZEGO OD NOWA — ADAPTUJEMY TO, CO JUŻ JEST pamietamy o SNAJPERZE i stworzonych elementach systemu. Analizujem je przed implementacja.
**Zasada nadrzędna 2:** PROGRAMOWANIE SPINA SIĘ Z ELEKTRONIKĄ PRZEZ PROTOKÓŁ KOMUNIKACJI.

---

## 0. Decyzja architektoniczna

Przyjmujemy układ:

```text
Linux / miniPC
  ↓
LKS / TSP / core runtime
  ↓
SignalBus
  ↓
Snajper / Bridge / adaptery
  ↓
hardware / Nextion 5 / Nextion 7
  ↑
PAR przez TSP
  ↑
EHR / KHR przez PAR / TSP / SignalBus
```

To oznacza:

```text
miniPC = runtime, LKS, TSP, nadzorca core, testy, status, hardware
PAR    = zewnętrzna administracja TEST/LIVE
EHR    = przygotowanie TAKE / przebiegi / STEP stream
KHR    = korekta / wsparcie ruchu
SignalBus = tablica aktualnego stanu runtime
Snajper / Bridge / adaptery = rozprowadzanie sygnałów
Nextion 5 = lokalny panel LKS przy miniPC
Nextion 7 = obecny tor PAR / Bridge / Snajper
```

Nie zmieniamy nazw usług i nie tworzymy nowego świata obok obecnego kodu.

---

## 0A. Najważniejsza zasada wykonawcza

```text
PROGRAMOWANIE SPINA SIĘ Z ELEKTRONIKĄ PRZEZ PROTOKÓŁ KOMUNIKACJI.
```

To jest podstawa całej implementacji TARZANA. Kod nie ma sterować elektroniką prywatnymi skrótami, obejściami ani równoległymi ścieżkami. Programowanie i elektronika mają spotykać się przez wspólny język systemu:

```text
PAR / EHR / KHR / LKS
  ↓
TSP / SignalBus
  ↓
Snajper / Bridge / adaptery
  ↓
PoKeys / CNC / Nextion / czujniki / STEP-DIR / hardware
```

Znaczy to praktycznie:

```text
- PAR steruje elektroniką przez TSP i SignalBus, nie prywatnym skrótem do pinów.
- EHR przekazuje TAKE / przebieg / STEP stream przez ustalony tor komunikacji.
- KHR koryguje ruch przez sygnały i protokół, nie przez osobny układ wykonawczy.
- LKS/TSP/core testuje i nadzoruje elektronikę przez te same mapy i protokoły.
- Snajper / Bridge / adaptery są wykonawczym przełożeniem sygnałów na urządzenia.
```

Ta zasada łączy dwie poprzednie zasady:

```text
NIE BUDUJEMY OD NOWA.
ADAPTUJEMY ISTNIEJĄCE TORY.
PROGRAM ↔ ELEKTRONIKA ZAWSZE PRZEZ PROTOKÓŁ KOMUNIKACJI.
```

Niepoprawny kierunek:

```text
PAR → bezpośrednio pin
EHR → własny generator obok systemu
KHR → prywatny skrót do osi
TSP → własna symulacja zamiast realnego SignalBus
Bridge → własna prawda poza SignalBus
```

Poprawny kierunek:

```text
PAR / EHR / KHR / LKS
→ TSP / SignalBus
→ Snajper / Bridge / adaptery
→ elektronika
```

---

## 0B. Źródło prawdy dla sygnałów

Jasno przyjmujemy rozróżnienie:

```text
core/tarzanZmienneSygnalowe.py = źródło prawdy katalogu sygnałów
SignalBus                     = tablica aktualnego stanu runtime
```

`tarzanZmienneSygnalowe.py` mówi:

```text
- jakie sygnały istnieją,
- jak się nazywają,
- jaka jest nazwa kanoniczna,
- do jakiej płytki / kanału / grupy należą,
- jaki mają typ, kierunek i rolę,
- czy są systemowe, wejściowe, wyjściowe, czujnikowe, UI albo sprzętowe,
- czy wolno nimi sterować, czy są tylko do odczytu.
```

SignalBus nie wymyśla sygnałów. SignalBus trzyma aktualne wartości sygnałów zdefiniowanych w katalogu.

To oznacza praktycznie:

```text
- nowych nazw sygnałów nie dopisujemy przypadkowo w kodzie lokalnym,
- najpierw sprawdzamy core/tarzanZmienneSygnalowe.py,
- jeśli sygnał systemowy jest potrzebny, dodajemy go do mapy jako sygnał systemowy,
- TSP, PAR, LKS, EHR i KHR mają używać nazw z tej mapy,
- SignalBus pokazuje aktualny stan tych sygnałów w runtime.
```

Dla tej integracji szczególnie ważne są sygnały systemowe, które muszą być potraktowane jako pełnoprawne sygnały katalogu, a nie luźne zmienne pomocnicze:

```text
system_state
runtime_state
tsp_state
lks_state
par_state
ehr_state
khr_state
nextion5_state
nextion7_state
hardware_state
control_owner
tarzan_ready
```

Te sygnały powinny być zdefiniowane w `tarzanZmienneSygnalowe.py` jako sygnały systemowe / runtime, najlepiej w klasie/roli typu `ROLA_SYSTEM` albo najbliższym istniejącym odpowiedniku w obecnej strukturze mapy, żeby cały system widział je tak samo.

---

## 0C. KROK ZERO — pierwszy wzorzec komunikacji

Przed pełnym spinaniem wszystkich bloków trzeba wykonać najmniejszy możliwy test wzorca komunikacji. Nie jako osobny system, tylko jako pierwsze użycie docelowego toru.

KROK ZERO:

```text
1. dodać / potwierdzić sygnał system_state w tarzanZmienneSygnalowe.py,
2. ustawić system_state = BOOTING po starcie TSP Servera,
3. wystawić ten stan przez istniejący TSP Server,
4. odebrać go w PAR przez istniejący TarzanParBridge i TarzanTspClient,
5. wpisać go do lokalnego SignalBus PAR,
6. sprawdzić, że PAR widzi system_state z miniPC,
7. sprawdzić prostą zmianę / potwierdzenie w drugą stronę przez TSP.
```

Dopiero gdy ten jeden sygnał działa w obie strony, rozciągamy wzorzec na kolejne stany i moduły. Dzięki temu nie budujemy dużej integracji na niepotwierdzonym połączeniu.

Ten krok nie skraca planu. To jest próba generalna dla całego wzorca:

```text
miniPC SignalBus
→ TSP Server
→ TarzanParBridge
→ SignalBus PAR

PAR
→ TarzanParBridge
→ TSP set_signal / call_action
→ SignalBus miniPC
```

---

## 1. Główne źródło startu

Nie zmieniamy nazwy:

```text
tarzan-tsp-lks-n5.service
```

Rozszerzamy jej znaczenie.

Obecna usługa ma stać się startem:

```text
TARZAN MAIN RUNTIME na miniPC
```

Najlepsze miejsce implementacji:

```text
core/TSP/tarzanTspServer.py
klasa TarzanTspServer
metoda start()
```

Powód:

```text
- usługa już uruchamia TSP,
- TSP Server już jest centrum kontaktu miniPC ↔ stacja,
- LKS-N5 jest już spięty z TSP,
- nie trzeba tworzyć nowego main.py,
- nie trzeba zmieniać nazwy systemd.
```

---

## 2. Cel końcowy runtime

Po starcie miniPC system ma dojść do stanu:

```text
TARZAN_READY
```

Ten stan oznacza:

```text
Linux działa
tarzan-tsp-lks-n5.service działa
TSP Server działa
SignalBus działa
Snajper działa
LKS-N5 / Nextion 5 działa
lokalne testy zostały wykonane
hardware ma status
PAR może się połączyć
EHR/KHR są wykrywalne jako bloki systemowe
system jest gotowy do MODE / RRP / osi / TAKE
```

Nie oznacza jeszcze uruchomienia programu ruchu.

---

## 3. Etapy pracy

### ETAP 1 — centralne stany systemowe w SignalBus

Dodać lub uporządkować w istniejącym `SignalBus` i mapie sygnałów:

```text
system_state
runtime_state
tsp_state
lks_state
par_state
ehr_state
khr_state
nextion5_state
nextion7_state
hardware_state
control_owner
tarzan_ready
```

Przykładowe wartości:

```text
BOOTING
TESTING
READY_FOR_PAR
PAR_CONNECTED
PAR_LIVE
EHR_READY
KHR_READY
HARDWARE_READY
ERROR
```

Najważniejsze:

```text
runtime_state = READY_FOR_PAR
tarzan_ready = 1
control_owner = TSP_BOOT / TSP_SERVICE / PAR_LIVE / EHR_PLAYBACK / KHR_CORRECTION / LKS_DIAGNOSTIC / EMERGENCY_STOP
```

Uwagi implementacyjne JUNI do tego etapu:

```text
- te stany nie mogą być luźnymi zmiennymi w przypadkowych klasach,
- muszą być wpisane do core/tarzanZmienneSygnalowe.py jako sygnały systemowe, czyli `ROLA_SYSTEM` albo najbliższy istniejący odpowiednik w obecnej strukturze mapy,
- powinny być dostępne od początku runtime, zanim ruszą cięższe testy,
- SignalBus ma je obsługiwać tak samo jak inne sygnały,
- ich aktualna wartość jest stanem runtime, ale ich katalog i klasyfikacja pochodzą z tarzanZmienneSygnalowe.py.
```

Ważne rozróżnienie:

```text
tarzanZmienneSygnalowe.py = katalog i klasyfikacja sygnałów
SignalBus                  = aktualne wartości tych sygnałów
```

---

### ETAP 2 — rozszerzenie `TarzanTspServer.start()`

W `core/TSP/tarzanTspServer.py` metoda `start()` ma uruchamiać pełny runtime miniPC:

```text
1. utworzyć / przejąć centralny SignalBus miniPC
2. ustawić system_state = BOOTING
3. uruchomić TSP Server możliwie szybko, żeby PAR mógł zobaczyć BOOTING
4. uruchomić / podpiąć LKS-N5
5. podpiąć Snajpera / Bridge / adaptery istniejącym torem
6. wykonać lokalne testy LKS
7. zapisać wyniki testów do SignalBus
8. ustawić runtime_state = READY_FOR_PAR
9. wystawić stan do klientów TSP
```

Nie budować nowego startu. Rozszerzyć obecny.

Uwagi implementacyjne JUNI do tego etapu:

```text
- TSP Server nie może czekać z otwarciem komunikacji TCP aż skończą się wszystkie testy i nie może blokować akceptowania połączeń TCP od PAR,
- długie testy LKS / USB / I2C / PoKeys nie mogą blokować PAR przed zobaczeniem stanu BOOTING,
- najpierw ma być dostępny TSP z podstawowym stanem system_state=BOOTING,
- diagnostyka może iść dalej jako część runtime, aktualizując SignalBus,
- po zakończeniu testów runtime_state przechodzi na READY_FOR_PAR.
```

Czyli start logiczny ma wyglądać tak:

```text
TarzanTspServer.start()
  ↓
SignalBus + system_state=BOOTING
  ↓
TSP Server dostępny dla klienta
  ↓
LKS / diagnostyka / testy
  ↓
wyniki do SignalBus
  ↓
runtime_state=READY_FOR_PAR
```

---

### ETAP 3 — lokalne testy LKS jako część runtime

Wykorzystać istniejące moduły:

```text
core/TSP/tarzanTspLksBootProgress.py
core/TSP/tarzanTspLksDiagnostics.py
core/TSP/tarzanTspLksInventory.py
core/TSP/tarzanTspAxisInventory.py
```

Uwaga implementacyjna JUNI:

```text
- przed użyciem trzeba sprawdzić, które pliki realnie istnieją w aktualnym repo,
- nie zakładać nazwy tarzanTspLksAxisInventory.py, jeśli jej nie ma,
- jeśli inwentaryzacja osi jest już w tarzanTspAxisInventory.py, użyć jej,
- jeśli funkcja jest w tarzanTspLksInventory.py, scalić logikę w istniejącym miejscu,
- nie tworzyć dwóch inwentarzy osi o tej samej roli.
```

Testy startowe mają publikować do SignalBus:

```text
linux_ok
tsp_ok
signalbus_ok
snajper_ok
lks_n5_ok
nextion5_ok
pokeys_ok
i2c_bus_ok
lcd_1602_ok
matrix_led_ok
f_led_ok
axis_inventory_ok
hardware_ready
```

Nextion 5 pokazuje lokalny status LKS/TSP/core.

---

### ETAP 4 — TSP Server jako brama całego systemu

TSP Server ma obsługiwać istniejące komendy:

```text
hello
ping
get_state
get_signal
set_signal
subscribe
unsubscribe
call_action
urgent_event
```

Dodatkowo ma utrzymywać stany klientów:

```text
par_state
par_last_seen
ehr_state
ehr_last_seen
khr_state
khr_last_seen
```

MiniPC po starcie:

```text
- sprawdza, czy klient/stacja jest dostępna, jeżeli obecny kod to umożliwia,
- jeżeli klient jest obecny, synchronizuje stan,
- jeżeli klienta nie ma, działa samodzielnie jako nadzorca i czeka.
```

---

### ETAP 5 — `tarzanTspSignals.py` z symulacji na realny SignalBus

Obecny `TarzanTspSignalProvider` nie może być głównym źródłem prawdy, jeżeli generuje dane testowe.

Docelowo:

```text
DEV / SMOKE / TEST  → może generować dane testowe
MAIN / LIVE         → czyta realny SignalBus miniPC
```

Zasada implementacyjna:

```text
nie pisać nowego providera obok
przerobić istniejącą klasę / istniejący tor
zostawić symulację tylko jako tryb testowy
```

`get_signal`, `get_state`, `subscribe` mają czytać realny stan.  
`set_signal`, `call_action` mają wpisywać do realnego SignalBus / istniejącego toru wykonawczego.

Uwagi implementacyjne JUNI do tego etapu:

```text
- jeżeli TarzanTspSignalProvider trzyma własny słownik _signals, nie może on być źródłem prawdy w MAIN/LIVE,
- w trybie MAIN/LIVE odczyt ma być delegowany do realnego SignalBus,
- własny słownik może zostać tylko dla DEV/SMOKE/TEST,
- get_signal ma czytać z bus,
- get_state ma budować stan z bus,
- set_signal ma pisać do bus przez istniejący mechanizm walidacji,
- TSP nie może dalej generować live świata testowego, jeżeli działa realny runtime.
```

Czyli praktycznie:

```text
DEV/SMOKE: TarzanTspSignalProvider może generować dane testowe.
MAIN/LIVE: TarzanTspSignalProvider ma być oknem na SignalBus miniPC.
```

---

### ETAP 6 — PAR LIVE przez istniejący `TarzanParBridge`

Miejsce integracji:

```text
editor/PAR/tarzanParBridge.py
```

Nie pakować logiki TSP do `tarzanParApp.py`.

`tarzanParApp.py` ma dalej robić:

```text
set_mode("LIVE")
self.bridge.set_mode("LIVE")
```

`TarzanParBridge` ma obsłużyć:

```text
TarzanTspClient
connect
hello
ping
get_state
subscribe
on_message
disconnect
logowanie do istniejącego logu PAR
```

Odebrane wartości trafiają do istniejącego lokalnego SignalBus PAR:

```text
bus.apply_snapshot(values, source="TSP_LIVE")
```

Jeżeli `apply_snapshot` nie istnieje, dodać ją do `core/tarzanSignalBus.py` jako hurtowe wejście używające istniejącego `set()` / powiadomień.

Uwagi implementacyjne JUNI do `apply_snapshot`:

```text
- apply_snapshot nie może bezmyślnie odświeżać całego UI,
- przy większej mapie sygnałów, nawet rzędu 3000+ pozycji, nie wolno wywołać tysięcy powiadomień, jeśli wartości się nie zmieniły,
- aktualizować tylko wartości różniące się od obecnych,
- używać istniejącego mechanizmu SignalBus.set, ale bez zapętlania odświeżania,
- source="TSP_LIVE" ma służyć do diagnostyki i filtrowania, nie do budowy drugiej tablicy stanu.
```

---

### ETAP 7 — dwukierunkowe spięcie PAR ↔ TSP ↔ SignalBus

Kierunek miniPC → PAR:

```text
SignalBus miniPC
  ↓
TSP packets / get_state / subscribe
  ↓
TarzanParBridge
  ↓
SignalBus PAR
  ↓
istniejące panele PAR
```

Kierunek PAR → miniPC:

```text
PAR UI
  ↓
TarzanParBridge
  ↓
TSP set_signal / call_action
  ↓
SignalBus miniPC
  ↓
Snajper / Bridge / adaptery
  ↓
hardware
```

Panele PAR nie mają wiedzieć, czy sygnał jest lokalny, czy z TSP.  
Czytają i zapisują przez istniejący tor PAR/Bridge/SignalBus.

Uwaga implementacyjna JUNI — pętla zwrotna:

```text
PAR ustawia sygnał
→ wysyła do TSP
→ TSP ustawia go w SignalBus miniPC
→ TSP publikuje aktualizację
→ PAR odbiera tę samą wartość
→ SignalBus PAR nie może odpalić kolejnej identycznej zmiany
```

Dlatego `SignalBus.set()` / `apply_snapshot()` muszą ignorować aktualizację, jeżeli wartość jest identyczna z obecną. To nie jest obejście, tylko konieczna ochrona przy dwukierunkowej synchronizacji.

---

### ETAP 8 — PAR jako pełna administracja, nie podgląd

W trybie LIVE PAR ma sterować systemem przez TSP:

```text
active_mode
transport_state
testy modułów
statusy hardware
RRP
SOK
osie
EHR
KHR
Nextion 7
logi
diagnostyka
```

Zakaz:

```text
PAR → bezpośrednio pin
PAR → osobny generator
PAR → osobny bridge
PAR → prywatny skrót do hardware
```

Poprawnie:

```text
PAR → TSP → SignalBus miniPC → Snajper / Bridge / adaptery → hardware
```

---

### ETAP 9 — EHR i KHR jako bloki systemowe

PAR ma widzieć i kontrolować EHR/KHR przez stany:

```text
EHR_OFF
EHR_READY
EHR_ACTIVE
EHR_ERROR

KHR_OFF
KHR_READY
KHR_ACTIVE
KHR_ERROR
```

PAR powinien móc:

```text
sprawdzić EHR
uruchomić EHR
sprawdzić KHR
uruchomić KHR
wybrać TAKE
uzbroić korekty
zatrzymać korekty
widzieć błędy
```

Nie wymaga to bezpośredniego importowania klas EHR/KHR do PAR, jeśli można operować przez sygnały i procesy.

Docelowy tor:

```text
PAR → TSP → SignalBus → EHR/KHR/MODE/korekta → Snajper/adaptery → hardware
```

---

### ETAP 10 — Nextion 5 i Nextion 7 bez mieszania

Zasada zostaje:

```text
Nextion 5 = LKS/TSP/core, boot/status/diagnostyka przy miniPC
Nextion 7 = PAR/Bridge/Snajper, obecny tor operatorski
```

Nie przenosić Nextion 7 do LKS.  
Nie przenosić Nextion 5 do PAR.

Po zespoleniu oba mają widzieć ten sam stan systemu przez SignalBus/TSP, ale w różnych rolach.

Uwaga implementacyjna JUNI:

```text
- Nextion 5 jest lokalnie podpięty do miniPC / LKS,
- jest ostatnią linią obrony statusu przy urządzeniu,
- musi działać także wtedy, gdy zerwie się połączenie Ethernet/WiFi ze stacją PAR,
- dlatego nie wolno mieszać jego roli z Nextionem 7 ani uzależniać lokalnego statusu LKS od PAR.
```

---

### ETAP 11 — `control_owner` i priorytety

Wprowadzić jawnego właściciela sterowania:

```text
TSP_BOOT
TSP_SERVICE
PAR_LIVE
EHR_PLAYBACK
KHR_CORRECTION
LKS_DIAGNOSTIC
EMERGENCY_STOP
```

Znaczenie:

```text
TSP_BOOT       — start i testy miniPC
TSP_SERVICE    — miniPC nadzoruje bez aktywnego PAR
PAR_LIVE       — PAR administruje i steruje
EHR_PLAYBACK   — wykonywanie TAKE / przebiegu
KHR_CORRECTION — korekta ruchu
LKS_DIAGNOSTIC — diagnostyka punktowa z Nextion 5
EMERGENCY_STOP — najwyższy priorytet
```

To nie ogranicza PAR. To porządkuje, kto w danej chwili prowadzi system.

Uwagi implementacyjne JUNI do `control_owner`:

```text
- control_owner musi być realnie sprawdzany przy zapisie sygnałów wykonawczych,
- jeśli control_owner = EHR_PLAYBACK, ręczne komendy PAR dla osi mogą zostać odrzucone,
- jeśli control_owner = KHR_CORRECTION, system musi wiedzieć, że korekta wpływa na ruch,
- jeśli control_owner = LKS_DIAGNOSTIC, diagnostyka punktowa nie może ścierać się z PAR LIVE,
- EMERGENCY_STOP ma najwyższy priorytet.
```

Przykładowe zachowanie TSP przy konflikcie:

```text
PAR wysyła set_signal dla osi
control_owner = EHR_PLAYBACK
TSP Server odrzuca zapis
zwraca WRITE_DENIED z powodem control_owner_conflict
```

To nie jest ograniczanie PAR z góry. To jest zapisanie zasad bezpiecznego prowadzenia systemu, gdy kilka warstw może wpływać na ruch.

---

### ETAP 12 — MODE na gotowy organizm

MODE nie startuje przed `TARZAN_READY`.

Najpierw:

```text
TARZAN_READY
```

Potem:

```text
active_mode = tM / tMAS / tAA / tAT / t3D / tAD / tFX
transport_state = STOP / REC / PLAY / PAUSE
```

MODE ma korzystać z istniejących sygnałów i istniejącej mapy.

Tor:

```text
Nextion 7 / PAR
  ↓
Bridge
  ↓
SignalBus
  ↓
MODE rules
  ↓
Snajper / adaptery
  ↓
hardware
```

---

### ETAP 13 — RRP / SOK / osie jako moduły LIVE

Po spięciu MAIN/PAR/TSP/SignalBus wchodzą realne moduły:

```text
RRP
SOK
ramię CNC
pochył
osie kamery
krańcówki
READY/ALARM
STEP/DIR/ENABLE
```

Tor:

```text
PAR / Nextion 7 / MODE
  ↓
SignalBus
  ↓
TSP/core
  ↓
Snajper / Bridge / adaptery
  ↓
PoKeys / CNC
```

Testy osi i sterowników mają być częścią tego toru, a nie osobnym światem.

---

### ETAP 14 — EHR playback

EHR przygotowuje:

```text
TAKE
krzywe
STEP stream
czas
zdarzenia
```

PAR wybiera i uruchamia.  
TSP/core wykonuje.  
SignalBus pokazuje stan.  
MODE/Safety/KHR mogą korygować.

Tor:

```text
EHR TAKE
  ↓
PAR wybiera / uzbraja
  ↓
TSP/core przyjmuje
  ↓
SignalBus
  ↓
MODE / Safety / KHR
  ↓
Snajper / adaptery
  ↓
STEP/DIR
```

---

### ETAP 15 — KHR correction

KHR działa jako korektor, nie osobny sterownik pinów.

Tor:

```text
bazowy ruch z EHR / MODE
  ↓
KHR / LEVEL / FACE / AI korekta
  ↓
zagęszcza / rozrzedza / blokuje / koryguje
  ↓
wyjście STEP/DIR przez SignalBus/Snajper/adaptery
```

PAR widzi:

```text
KHR OFF/READY/ACTIVE/ERROR
aktywne korekty
wpływ korekty
blokady
alarmy
```

---

### ETAP 16 — logi, trace, snapshot

Spójne logowanie:

```text
LKS log
TSP log
PAR log
EHR log
KHR log
SignalBus events
urgent events
```

Logować:

```text
CONNECT
DISCONNECT
HELLO
SUBSCRIBE
UNKNOWN_SIGNAL
WRITE_DENIED
CALL_ACTION
URGENT
ERROR
READY
```

Nie logować każdej ramki FAST 10 ms.  
Dla FAST używać statystyk.

Uwagi implementacyjne JUNI do logowania FAST:

```text
- nie zapisywać każdej ramki 10 ms do pliku,
- nie zalewać panelu logów PAR pakietami FAST,
- logować FAST_STATS, np. raz na sekundę,
- mierzyć liczbę pakietów, jitter, dropped, kolejkę, ostatni czas odebrania,
- trace uruchamiać tylko dla wybranego sygnału i przez ograniczony czas.
```

Docelowo:

```text
trace signal
snapshot debug
last packets
FAST_STATS
```

---

### ETAP 17 — sprzątanie i likwidacja równoległych torów

Po każdym większym fragmencie:

```text
usunąć obejścia
usunąć martwą symulację, jeśli realny tor ją zastąpił
nie zostawiać duplikatów metod
nie trzymać dwóch ścieżek dla jednego sygnału
nie dodawać nowych plików bez konieczności
aktualizować dokumentację
```

Najważniejsze:

```text
jeżeli obecny kod da się rozszerzyć, rozszerzamy go
jeżeli coś jest stare i zastąpione, usuwamy
jeżeli coś jest testowe, oznaczamy jako DEV/SMOKE
```

---

## 4. Planowane cele końcowe

Po wykonaniu planu system ma działać tak:

```text
1. Włączasz miniPC.
2. Linux startuje.
3. tarzan-tsp-lks-n5.service uruchamia MAIN RUNTIME.
4. LKS/TSP/core testuje lokalny system.
5. Nextion 5 pokazuje boot/status.
6. TSP Server wystawia runtime.
7. System ustawia READY_FOR_PAR.
8. PAR na stacji łączy LIVE przez TSP.
9. PAR dostaje stan miniPC do swojego SignalBus.
10. Panele PAR pokazują realny system.
11. PAR może sterować elektroniką przez TSP.
12. EHR/KHR są widoczne jako bloki gotowe/aktywne.
13. Nextion 7 zostaje w torze PAR/Bridge/Snajper.
14. MODE wchodzi na gotowy organizm.
15. RRP/SOK/osie/TAKE/KHR działają przez wspólny tor.
```

---

## 5. Najważniejsze ograniczenia

```text
Nie zmieniamy nazw usług bez potrzeby.
Nie budujemy nowego main obok istniejącego TSP.
Nie tworzymy równoległego klienta TSP dla PAR.
Nie przepisujemy paneli PAR.
Nie mieszamy Nextion 5 i Nextion 7.
Nie zostawiamy symulacji jako domyślnego LIVE.
Nie sterujemy hardware prywatnym skrótem.
Nie mnożymy kodu.
```

---

## 5A. Uwagi JUNI naniesione na plan bez skracania

Do planu zostały naniesione następujące korekty, bez skracania pierwotnej dokumentacji:

```text
1. tarzanZmienneSygnalowe.py jest źródłem prawdy katalogu i klasyfikacji sygnałów.
2. SignalBus jest tablicą aktualnego stanu runtime, nie katalogiem nazw.
3. Stany systemowe muszą być sygnałami systemowymi w mapie, nie luźnymi zmiennymi.
4. Przed pełną integracją robimy KROK ZERO na jednym sygnale system_state.
5. TSP Server ma startować szybko i pokazywać BOOTING, a diagnostyka nie może blokować komunikacji TCP.
6. Inwentaryzację osi trzeba oprzeć na istniejącym pliku/funkcji, bez tworzenia drugiego inwentarza.
7. tarzanTspSignals.py w MAIN/LIVE ma czytać realny SignalBus, a symulacja zostaje tylko dla DEV/SMOKE/TEST.
8. apply_snapshot ma aktualizować tylko zmienione wartości, bez masowego odświeżania UI.
9. Dwukierunkowe PAR ↔ TSP wymaga ochrony przed pętlą zwrotną.
10. control_owner musi realnie blokować konflikty zapisów wykonawczych i zwracać WRITE_DENIED.
11. FAST nie logujemy ramka po ramce; używamy FAST_STATS, trace i snapshotów.
```

---

## 6. Najkrótsze hasło wdrożenia

```text
TARZAN MAIN RUNTIME =
obecny TSP/LKS/core rozszerzony do pełnego startu,
PAR spięty przez istniejący Bridge,
SignalBus jako wspólna tablica stanu,
Snajper/Bridge/adaptery jako wykonanie,
EHR/KHR/MODE jako warstwy ruchu na gotowym organizmie.
```
