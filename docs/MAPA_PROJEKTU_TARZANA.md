# MAPA PROJEKTU TARZAN

## 1. Cel projektu

TARZAN to inteligentne ramię kamerowe sterowane osiami napędzanymi silnikami krokowymi. System ma umożliwiać precyzyjne pozycjonowanie kamery i ramienia, płynny ruch, kontrolę balansu mechanicznego oraz dalszą rozbudowę o automatykę i logikę wysokiego poziomu.

Projekt łączy trzy warstwy: - mechanikę — ramię, głowica, przeciwwaga / regulator masy, - elektronikę — sterowniki silników, czujniki, krańcówki, zasilanie, płytki Play / Rec i urządzenia wykonawcze, - software — klasy sterujące osiami, logika ruchu, bezpieczeństwo, profile pracy, protokół rejestracji i odtwarzania sygnałów.

Dodatkową zasadą nadrzędną projektu jest: - prostota kodu, - prostota obsługi, - czytelna architektura, - bezpieczna logika sygnałowa.

System ma być lekki, modułowy, łatwy do testowania etapami i możliwy do uruchamiania częściami podczas integracji z elektroniką.

## Zasada synchronicznej pracy

System TARZAN realizuje logikę sterowania w sposób synchroniczny – wszystkie elementy systemu działają równolegle w tym samym cyklu sterowania, tworząc jedną spójną dynamikę ruchu odpowiadającą jednemu ujęciu.

```
Czas
↓
Stan wszystkich sygnałów
↓
Dynamika ruchu
↓
Ujęcię
```

## Zasada modułowej logiki sterowania

Logika systemu powinna być budowana z małych, czytelnych modułów o jasno określonych wejściach i wyjściach. Każdy moduł odpowiada za wąski fragment funkcjonalności, dzięki czemu tryby pracy mogą być składane z prostych elementów bez zwiększania złożoności całego systemu.

System powinien umożliwiać monitorowanie aktualnych stanów sygnałów oraz diagnostykę cyklu sterowania, tak aby możliwe było szybkie wykrycie przeciążeń, błędów logicznych lub konfliktów sygnałów.

## Centralna pętla serowania

Logika systemu TARZAN opiera się na centralnej pętli sterowania, w której w każdym cyklu analizowany jest pełny stan sygnałów systemu, a wszystkie decyzje sterujące wynikają z aktualnego kontekstu czasowego i trybu pracy.

### logika sprzętu logika ujęcia

Rozdzielenie logiki sprzętu i logiki ujęcia. Sprzęt robi tylko to co mu każesz. Logika ruchu obsługuje osie. Tryb pracy definiuje choreografię ujęcia.

```
sprzęt
↓
logika ruchu
↓
tryb pracy (ujęcie)
```

Należy przyjąć, że system Tarzan jest oparty MOTION CAPTURE. System sterowania ma być zbudowany jako synchronizowana w czasie choreografia sygnałów, a nie jako zestaw poleceń ruchu.

## 2. Główne założenia systemu

System ma obsługiwać następujące osie / moduły:

### Osie kamery

1. Oś pozioma kamery
2. Oś pionowa kamery
3. Oś pochyłu kamery
4. Oś ostrości kamery

### Osie ramienia

1. Oś pionowa ramienia
2. Oś pozioma ramienia

### Moduł balansu

1. Regulator masy — dodaj
2. Regulator masy — ujmij

W praktyce regulator masy jest osobnym mechanizmem wspomagającym balans ramienia, a nie zwykłą osią użytkową.

System ma być także przygotowany na dalszą rozbudowę o: 

- wózek, 

- drona, 

- tryby 3D, 

- FX / special effects, 

- tracking, 

- integrację z analizą obrazu i ruchem 3D.

## 3. Kluczowa idea mechaniczna: regulator masy

### Rola regulatora masy

Regulator masy to urządzenie wspomagające silniki krokowe w przełamywaniu grawitacji.

Jego zadaniem jest dynamiczna zmiana efektywnej masy na końcu ramienia, tak aby ograniczać moment grawitacyjny działający na układ.

### Zasada działania

- gdy głowica / ramię porusza się do góry, regulator masy odejmuje ok. 100 g na końcu ramienia,
- przez to dominanta równowagi ramienia staje się bardziej „ujemna” względem obciążenia, co odciąża napęd w ruchu w górę,
- gdy ramię porusza się w dół, regulator masy dodaje masę,
- gdy ramię wraca do pozycji neutralnej, regulator może przywrócić poprzednie warunki balansu.

### Warunek czasowy

Po przestawieniu regulatora masy należy odczekać około 3 sekund, dopiero potem wolno uruchomić ruch osi pionowej ramienia.

Jeżeli regulator masy nie potwierdzi stanu krańcowego, ruch osi pionowej ramienia nie może wystartować.

### Wniosek projektowy

Regulator masy powinien być modelowany jako osobna klasa logiczna, np.: - tarzanRegulatorMasy.py

To nie jest zwykły silnik osiowy — to moduł kompensacji grawitacyjnej.

## 4. Architektura logiczna projektu

Projekt warto podzielić na 6 głównych warstw systemowych oraz na warstwy funkcjonalne ruchu. System TARZAN korzysta z oficjalnej specyfikacji protokołu PoKeys jako źródła referencyjnego dla komunikacji z płytkami sterującymi. Konfiguracja pinów, odczyt sygnałów, sterowanie Pulse Engine oraz inne funkcje sprzętowe muszą być zgodne z dokumentem „PoKeys protocol specification”, dostarczone w dokumentacji.

### A. Warstwa rdzenia systemu

Obejmuje: - zmienne sygnałowe, - ustawienia, - logi, - protokół ruchu, - błędy, - stany pracy.

### B. Warstwa sprzętowa

Obejmuje fizyczne komponenty: 

- płytki **PoKeys57U**, 

- sterowniki **PoStep25**, 

- moduł **PoExtBusOC16-CNC**, 

- krańcówki / home switch, 

- czujniki pozycji, 

- czujniki TF-Luna i PoSensors, 

- Nextion, LCD, Matrix LED, 

- klawiaturę i przyciski funkcyjne, 

- kamerę i napęd ostrości, 

- sterowniki ręczne (SOK).

### C. Warstwa abstrakcji osi

Każda oś ma wspólny zestaw cech: 

- nazwa, 

- aktualna pozycja, 

- pozycja docelowa, 

- ograniczenia ruchu, 

- prędkość, 

- przyspieszenie, 

- stan homingu, 

- stan błędu, 

- możliwość ruchu ręcznego i automatycznego.

Tu powinna istnieć klasa bazowa, np.: 

```
TarzanAxis
```

### D. Warstwa wykonawcza ruchu

Odpowiada za: 

- generowanie ruchu, 

- kolejność startu osi, 

- synchronizację ruchów, 

- soft start / soft stop, 

- ochronę przed przeciążeniem, 

- bezpieczne zatrzymanie, 

- wykonanie sygnałów: STEP / DIR / ENABLE,

- wykonanie sygnałów regulatora masy.

### E. Warstwa balansu i kompensacji

Tu działa: 

- TarzanRegulatorMasy, 

- logika kompensacji grawitacyjnej, 

- profile odciążania zależne od kąta / kierunku ruchu, 

- blokada ruchu osi pionowej do czasu gotowości regulatora.

### F. Warstwa logiki wysokiego poziomu

Odpowiada za tryby pracy, np.: 

- manual, - preset, 

- ruch automatyczny,

- śledzenie trajektorii, 

- record motion, 

- play motion, 

- auto tracking, 

- pozycja transportowa, 

- pozycja startowa, 

- kalibracja.

### G. Warstwa bezpieczeństwa

Kontroluje: 

- zakresy osi, 

- kolizje, 

- ruch zabroniony, 

- brak homingu, 

- alarmy, 

- E-STOP, 

- timeouty, 

- błędy sterownika, 

- brak zgody modułu,

- konflikt sygnałów, 

- zgodność konfiguracji Play / Rec / PoStep / PoKeys.

## 5. Struktura modułów plików Pythona

Struktura projektu powinna łączyć wcześniejszy logiczny podział modułów z docelowym podziałem katalogów systemu:

```
STRUKTURA_PLIKOW_TARZAN.md
```

## 6. Klasy główne i ich odpowiedzialność

```
TarzanSystem
```

Najwyższy poziom systemu.

Odpowiada za: - inicjalizację wszystkich modułów, - ładowanie konfiguracji, - uruchamianie homingu, - spinanie osi, balansu i bezpieczeństwa, - sprawdzanie zgodności urządzeń, - przejście w tryb pracy.

```
TarzanController
```

Warstwa sterowania użytkowego / operatora.

Odpowiada za: - przyjmowanie poleceń, - wybór trybu pracy, - wywoływanie presetów, - sterowanie ręczne, - zatrzymanie awaryjne, - przełączanie między PLAY / REC / STOP / BAZA.

```
TarzanAxis
```

Klasa bazowa dla wszystkich osi.

Wspólne funkcje: - home() - move_to() - move_by() - stop() - enable() - disable() - get_position() - is_busy() - check_limits()

### Klasy osi dziedziczące

- TarzanCameraHorizontal

- TarzanCameraVertical

- TarzanCameraTilt

- TarzanCameraFocus

- TarzanArmVertical

- TarzanArmHorizontal

Każda z tych klas może mieć własne: 

- przełożenia, 

- limity, 

- profile prędkości, 

- kierunek domyślny, 

- logikę bezpieczeństwa, 

- mapowanie sygnałów DIR / STEP / ENABLE.

```
`TarzanRegulatorMasy`
```

Moduł kompensacji grawitacyjnej.

Powinien odpowiadać za: 

- określanie kiedy odjąć / dodać masę, 

- sterowanie mechanizmem regulatora, 

- profil odciążenia zależny od kierunku ruchu, 

- współpracę z osią pionową ramienia, 

- ochronę przed nagłą zmianą balansu, 

- blokadę startu osi do czasu gotowości regulatora, 

- potwierdzenie krańcówek regulatora, 

- timeout i opóźnienie 3 s.

Przykładowe metody: 

```
set_compensation_level() 

increase_compensation() 

decrease_compensation() 

prepare_for_upward_motion() 

prepare_for_downward_motion() 

sync_with_arm_position() 

is_ready_for_arm_vertical_motion()
```

## `MotionPlanner`

Planowanie ruchu wielu osi.

Odpowiada za: - kolejność ruchów, - ruch współbieżny, - synchronizację czasu, - rozkład trajektorii, - integrację z protokołem Record / Play.

### `SafetyManager`

Centralna logika bezpieczeństwa.

Odpowiada za: - walidację poleceń, - blokowanie niebezpiecznych ruchów, - monitorowanie alarmów, - reakcję na awarie, - wykrywanie konfliktów sygnałów, - wymuszanie warunków startu osi i trybów.

### `tarzanZmienneSygnalowe.py`

Centralny moduł definicji sygnałów.

Powinien zawierać: - wszystkie nazwy sygnałów, - aliasy programowe, - typ sygnału, - kierunek IN / OUT, - stan domyślny, - opis, - grupę logiczną, - powiązaną klasę, - status krytyczny / testowy / rezerwowy / sprzętowo zarezerwowany, - podział na domeny: Play, Rec, CNC / automatyka, UI, czujniki, rezerwa.

### `tarzanMetodyZezwolenie.py`

Moduł zgód na uruchamianie składowych systemu.

Powinien umożliwiać: - etapowe uruchamianie projektu, - testowanie tylko wybranych modułów, - blokowanie klas, które nie są jeszcze gotowe, - prostą logikę 0 / 1 dla zgody wykonania.

` tarzanPoKeysSetting.py``

Moduł stałej konfiguracji PoKeys.

Powinien odpowiadać za: - mapowanie konfiguracji pinów, - kontrolę zgodności z ustawieniem wzorcowym, - porównanie stanu urządzenia z konfiguracją referencyjną, - ostrzeganie przed zmianą parametrów sprzętowych, - odczyt konfiguracji tylko do odczytu z plików referencyjnych.

`tarzanPoKeysStart.py`

Moduł uruchamiania ramienia i relacji startowej ztarzanPoKeysSetting.py, traktowanym jako warstwa BIOS tarzan. Jego zadaniem jest przygotowanie systemu do pracy, uruchomienie testów startowych, potwierdzenie zgodności bezpieczeństwa oraz wydanie ostatecznej zgody na start ramienia.

Powinien odpowiadać za: - uruchomienie sekwencji startowej, - test połączeń PLAY i REC, - sprawdzenie zgodności raportu z tarzanPoKeysSetting.py, - test komponentów krytycznych, - potwierdzenie gotowości osi, - blokadę startu przy błędach bezpieczeństwa, - przekazanie systemu do poziomowania i pierwszego ruchu.

`tarzanPoKeysLevels.py`

Moduł poziomowania i kalibracji położenia ramienia oraz głowicy z wykorzystaniem czujnika poziomu. Moduł wchodzi do sekwencji po uzyskaniu zgody startowej z tarzanPoKeysStart.py.

Powinien odpowiadać za: - test ruchów osi potrzebnych do składania i ustawiania ramienia, - dostosowanie poziomów, - procedurę poziomowania głowicy kamery, - przygotowanie pozycji bazowej, - raport gotowości do pierwszego startu roboczego.

`tarzanAssemleChecklist.py`

Zewnętrzna aplikacja listy kontrolnej składania ramienia. Jej zadaniem jest krok po kroku zatwierdzać kompletację mechaniczną i elektryczną układu przed wydaniem zgody na start.

`tarzanKomunikaty.py`

Centralny moduł komunikatów operatorskich i ostrzegawczych. Ma spinać logikę komunikatów LCD, Matrix LED, przycisków funkcyjnych, sygnałów dźwiękowych i wibracyjnych, aby każdy tryb pracy korzystał z jednej spójnej warstwy komunikacji.

Powinien odpowiadać za: - komunikaty krańcówek głowicy kamery i ramienia, - komunikaty procedur startowych, - komunikaty błędów i blokad, - symbole na Matrix LED, - standardowe teksty na LCD Play i Rec, - wyzwalanie sygnałów dźwiękowych i wibracyjnych zależnie od typu zdarzenia.

## 7. Relacje między modułami

W silniku choreografii ruchu TARZANA obowiązuje zasada łagodności przebiegu. Wszystkie przejścia pomiędzy punktami kontrolnymi mają być możliwie płynne, bez ostrych załamań geometrycznych i bez gwałtownych zmian dynamiki, o ile nie wynika to bezpośrednio z logicznej potrzeby ujęcia.

### Główna zależność

TarzanSystem zarządza całością.

### Przepływ sterowania

1. Operator wydaje polecenie do TarzanController
2. TarzanController przekazuje ruch do MotionPlanner
3. MotionPlanner sprawdza ograniczenia w SafetyManager
4. Jeśli ruch dotyczy osi pionowej ramienia, konsultowany jest TarzanRegulatorMasy
5. Następnie wykonywana jest walidacja sygnałów i zgód w tarzanMetodyZezwolenie.py
6. Potem odpowiednie klasy osi wykonują ruch przez warstwę hardware
7. Jeżeli tryb to Record / Play, ruch przechodzi dodatkowo przez tarzanProtokolRuchu.py

### Zależności krytyczne

```
oś pionowa ramienia ↔ regulator masy
wszystkie osie ↔ safety manager
wszystkie osie ↔ homing manager
Play / Rec ↔ zgodność konfiguracji PoKeys
Record / Play ↔ spójność protokołu ruchu
```

## 8. Priorytety mechaniczne i sterownicze

### Najbardziej krytyczne elementy projektu

1. Oś pionowa ramienia

2. Regulator masy

3. Bezpieczeństwo zakresów ruchu

4. Homing i pozycja zerowa

5. Płynność ruchu kamery

6. Zgodność konfiguracji PoKeys i PoStep

7. Poprawność protokołu Record / Play

8. Dbanie o poziom kamery

9. Dbanie o liniowy układ kamery z pomocą czujnika laserowego

10. Czujnik wstrząsowy odłącza silniki gdy ramie zostanie uderzone mechanicznie.

To właśnie oś pionowa ramienia i regulator masy będą w największym stopniu decydować o stabilności, obciążeniu silników i bezpieczeństwie mechaniki.

## 9. Tryby pracy systemu

Tryby pracy systemu określają sposób interpretacji sygnałów sterujących oraz sposób generowania ruchu ramienia i głowicy kamery. Każdy tryb pracy wykorzystuje tę samą strukturę cyklu sterowania systemu, natomiast różni się logiką decyzji wykonywaną w etapie „Logika trybu pracy”. Nie wszystkie sygnały systemu TARZAN mogą uczestniczyć w logice trybów pracy. Sygnały przypisane do funkcji sprzętowych, magistral, wyświetlaczy, klawiatury, czujników lub funkcji bezpieczeństwa muszą być oznaczone jako ograniczone albo wyłączone z dowolnego użycia logicznego. To musi być w oparciu o dokumentacje sprzętową PoKeys57U i opis zdefiniowanych sygnałów w tarzanZmienneSygnalowe.py.

Dokumentacja PoBlocks, PoIL oraz przykładowe projekty XML mogą być wykorzystywane jako materiał referencyjny do nauki i projektowania nowych trybów pracy systemu TARZAN. Pokazują one sposoby budowy logiki sterowania, obsługi zdarzeń, sygnałów oraz współpracy z Pulse Engine.

### tM — Tryb prosty

Wejście do trybu: operator wciska przycisk nr 1 pod wyświetlaczem LCD „PROSTY”. Tryb ten służy do bezpośredniej, ręcznej pracy głowicą kamery i głowicą ramienia, bez aktywnej automatyki osi ramienia.

Sterowanie głowicą kamery odbywa się przez Regulator Obrotowy Ręczny SOK POZIOM / PION. Obrót gałką w prawo oznacza ruch kamery w prawo, a obrót gałką w lewo oznacza ruch w lewo. Wciśnięcie prawego przycisku SOK przełącza sterowaną oś na pion. W tej pozycji obrót w prawo powoduje ruch kamery do góry, a obrót w lewo powoduje ruch kamery w dół. Wciśnięcie obu klawiszy jednocześnie uruchamia ruch synchroniczny obu osi według tej samej zasady kierunkowej.

Sterowanie ostrością kamery odbywa się przez SOK OSTROŚĆ / POCHYŁ. Obrót w prawo oznacza ruch ostrości w prawo, a obrót w lewo oznacza ruch ostrości w lewo. Wciśnięcie prawego przycisku przełącza sterowanie z ostrości na pochył głowicy kamery. W tym stanie obrót w prawo realizuje pochył w prawą stronę, a obrót w lewo realizuje pochył w lewą stronę.

Głowica ramienia jest sterowana ręcznie. Sygnał z osi pionowej ramienia jest połączony bezpośrednio z SOK OSTROŚĆ / POCHYŁ w celu automatycznego poziomowania głowicy ramienia. Główną zasadą tego trybu jest utrzymanie logicznej prostoty sterowania: operator bezpośrednio steruje ruchem, a system jednocześnie pilnuje krańcówek, poziomu i komunikatów ostrzegawczych.

Warunki wejścia do trybu tM: 

- należy odłączyć napęd osi poziomej i pionowej ramienia, 

- kontrolka ostrzegawcza ma być zgaszona, 

- kluczyk w głównym zasilaniu ma znajdować się w pozycji wyłączonej. Warunki te muszą być sprawdzane przez logikę bezpieczeństwa oraz przez warstwę komunikatów operatora.

Komunikaty operatora w tM: 

LCD wyświetla komunikaty krańcowe dla głowicy kamery i głowicy ramienia, np. „Koniec! – obróć proszę gałkę w LEWĄ stronę” lub „OSTROŻNIE Koniec! – możliwy ruch tylko w GÓRĘ”, - Matrix LED wyświetla ♥ przy pracy bez uwag oraz symbole ▲ ► ▼ ◄ dla komunikatów krańcowych, 

- włączone są komunikaty dźwiękowe i wibracyjne: opór krańcowy głowicy kamery i ostrości daje wibrację obudowy SOK, a opór krańcowy głowicy ramienia daje dwa krótkie sygnały dźwiękowe. Hamulec kinetyczny pozostaje włączony.

Wniosek programistyczny dla tM: tryb musi spinać moduły 

```
tarzanTrybManual.py

tarzanSterownikSOK.py

tarzanKomunikaty.py

 tarzanLCD1602.py

tarzanMatrixLED8x8.py

tarzanPrzyciskiFunkcyjne.py

tarzanPoKeysLevels.py 
```

oraz sygnały krańcówek zdefiniowane w 

```
tarzanZmienneSygnalowe.py
```

### tMAS — Tryb półautomatyczny

Wejście do trybu: operator wciska przycisk nr 2 pod wyświetlaczem LCD „1/2 AUTO”, podłącza Sterownik Ręcznej Regulacji Pozycji (RRP) i włącza przełącznik RRP w pozycję „ON”. Przed włączeniem automatyki należy podać komendę bezpieczeństwa: 

> „Proszę odsunąć się od ramienia, włączam automatykę!”. 

Dioda sygnalizacyjna sterownika zaczyna świecić po poprawnym przejściu procedury.

W trybie tMAS głowica ramienia jest sterowana zdalnie przez RRP. Ruch w prawo i lewo odbywa się przełącznikiem kierunku oraz potencjometrem osi poziomej, a ruch do góry i w dół przełącznikiem kierunku oraz potencjometrem osi pionowej. Szybkość ruchu zależy od wychylenia potencjometrów. Po zakończeniu sesji potencjometry muszą wrócić do pozycji zero. Ta zasada ma być wprost kontrolowana przez logikę trybu i komunikaty ostrzegawcze.

Głowica kamery w tMAS nadal jest sterowana przez SOK POZIOM / PION, a ostrość i pochył przez SOK OSTROŚĆ / POCHYŁ, dokładnie według tych samych zasad kierunkowych co w tM. Sygnał z osi pionowej ramienia pozostaje połączony bezpośrednio z SOK OSTROŚĆ / POCHYŁ w celu automatycznego poziomowania głowicy ramienia.

Warunki wejścia do trybu tMAS: 

- należy włączyć napęd osi poziomej i pionowej ramienia, 

- kontrolka ostrzegawcza „AKCJA” ma być włączona, 

- należy włączyć kluczykiem główne zasilanie osi. Logika trybu ma wymuszać pełną procedurę zgód przed uzyskaniem aktywnego sterowania.

Komunikaty operatora w tMAS: 

- LCD wyświetla komunikaty krańcowe dla głowicy kamery i głowicy ramienia oraz komunikaty procedury uruchomienia, 

- po wciśnięciu przycisku wyboru trybu dioda w przycisku mruga i pojawia się komunikat o oczyszczeniu przestrzeni pracy oraz podaniu losowego kodu trzycyfrowego zakończonego #, 

- następnie pojawia się komunikat o sprawdzeniu głównego zasilania i potwierdzeniu #, 

- końcowo pojawia się komunikat o gotowości urządzenia i o włączeniu „1/2 auto”, po czym dioda LED przestaje migać i świeci ciągłym światłem. Matrix LED wyświetla ♥ przy pracy bez uwag, ▲ ► ▼ ◄ dla komunikatów krańcowych oraz X dla błędu. Komunikaty dźwiękowe i wibracyjne pozostają aktywne, a hamulec kinetyczny pozostaje załączony.

Wniosek programistyczny dla tMAS: tryb musi spinać moduły 

```
tarzanTrybManualAutoSupport.py

tarzanRRP.py

tarzanSterownikSOK.py

tarzanKomunikaty.py 

tarzanPrzyciskiFunkcyjne.py

tarzanLCD1602.py 

tarzanMatrixLED8x8.py 

tarzanPoKeysStart.py 

tarzanPoKeysLevels.py 
```

oraz sygnały zgody AUTO i sygnały bezpieczeństwa z

```
 tarzanZmienneSygnalowe.py.
```

### tAA — All-Auto

Pełny tryb automatyczny.

### tAT — Auto Tracking

Automatyczne śledzenie obiektu.

### t3D — All-Auto 3D

Tryb integracji z ruchem 3D / trajektorią 3D.

### tAD — All-Auto Dron

Tryb integracji z dronem.

### tFX — All-Auto Special Effects

Tryb efektów specjalnych.

### tREC — Record Motion

Tryb tREC służy do nagrywania ruchu ramienia oraz głowicy kamery w czasie rzeczywistym. System nie zapisuje pozycji osi w postaci docelowych punktów ruchu, lecz rejestruje stan sygnałów sterujących w kolejnych chwilach czasu.

Oznacza to zapis:

- sygnałów STEP,
- sygnałów DIR,
- sygnałów ENABLE,
- stanów wejść operatora,
- stanów czujników systemowych.
  Dzięki temu możliwe jest późniejsze dokładne odtworzenie zarejestrowanego ruchu.

Źródła sterowania

W trybie tREC ruch systemu pochodzi z:

- sterowników SOK (głowica kamery),
- sterownika RRP (ramię),
- ewentualnych innych wejść operatora.
  System zachowuje się więc identycznie jak w trybie manualnym, z tą różnicą, że wszystkie sygnały są zapisywane w protokole ruchu.

Zakres działania

W trybie tREC aktywne są wszystkie osie systemu:

- oś pozioma kamery

- oś pionowa kamery

- oś pochyłu kamery

- oś ostrości kamery

- oś pionowa ramienia

- oś pozioma ramienia

System może również zapisywać:

- stan regulatora masy,

- komunikaty operatora,

- stany czujników.

Warunki wejścia w tryb

Aby uruchomić tryb tREC muszą zostać spełnione warunki:

- system znajduje się w stanie READY,

- mechanika została zainicjalizowana,

- poziomowanie zostało wykonane,

- brak aktywnych błędów bezpieczeństwa.

Zapis danych

Zapis ruchu odbywa się w postaci próbek czasowych.

Każda próbka zawiera:

- stan wejść,
- stan czujników,
- stan wyjść,
- znacznik czasu.
  Schemat zapisu:

```
czas | wejścia | czujniki | wyjścia
```

Dane te są zapisywane w plikach protokołu ruchu.

Zastosowanie

Tryb tREC umożliwia:

- nagrywanie trajektorii ruchu,
- powtarzalne ujęcia filmowe,
- analizę ruchu ramienia,
- przygotowanie sekwencji automatycznych.
  Wniosek programistyczny

Logika trybu tREC powinna być implementowana w module:

```
modes/tarzanTrybRecordMotion.py
```

Moduł ten musi:

- przechwytywać sygnały sterujące,

- zapisywać stan systemu w każdej iteracji cyklu,

- przekazywać ruch do systemu sterowania osi.

**tREC dostarcza materiał źródłowy dla Edytora Choreografii Ruchu, a tAA wykorzystuje materiał zatwierdzony po edycji.**

### tPLAY — Play Motion

Tryb służy do odtwarzania wcześniej zarejestrowanego ruchu zapisanego w protokole systemu. System odczytuje kolejne próbki zapisanych sygnałów i odtwarza je w czasie rzeczywistym. Odtwarzanie polega na generowaniu tych samych sygnałów sterujących, które zostały zapisane podczas nagrywania.

Źródło ruchu

W trybie tPLAY ruch nie pochodzi od operatora, lecz z zapisanych danych protokołu ruchu.

System odczytuje kolejno:

- sygnały STEP,

- sygnały DIR,

- sygnały ENABLE,

- inne zapisane sygnały wyjściowe.

Zakres działania

W trybie tPLAY system steruje wszystkimi osiami, które zostały zapisane w nagraniu:

- oś pozioma kamery

- oś pionowa kamery

- oś pochyłu kamery

- oś ostrości kamery

- oś pionowa ramienia

- oś pozioma ramienia

System odtwarza także inne zapisane elementy:

- regulator masy,

- komunikaty,

- sygnały pomocnicze.

Warunki wejścia w tryb

Wejście w tryb tPLAY jest możliwe, gdy:

- system znajduje się w stanie READY,
- dostępny jest poprawny plik nagrania,
- mechanika układu została zainicjalizowana,
- brak aktywnych alarmów bezpieczeństwa.
  Zasada działania

Odtwarzanie polega na:

1. odczycie kolejnej próbki protokołu,
2. analizie czasu jej wykonania,
3. wygenerowaniu odpowiednich sygnałów wyjściowych.
   Schemat:

```
protokół ruchu
      ↓
odczyt próbki
      ↓
generowanie sygnałów
      ↓
sterowanie osiami
```

Zastosowanie

Tryb tPLAY umożliwia:

- powtarzalne ruchy kamerowe,
- odtwarzanie zaprogramowanych ujęć,
- synchronizację ruchu z nagraniem,
- automatyczne sekwencje ruchu.
  Wniosek programistyczny

Logika trybu tPLAY powinna być implementowana w module:

```
modes/tarzanTrybPlayMotion.py
```

Moduł ten musi:

- odczytywać dane z protokołu ruchu,
- synchronizować czas próbek,
- generować sygnały sterujące dla osi systemu.

### 9A. Zasada uruchamiania ramienia

Uruchamianie tarzan ma przebiegać etapami i w logice zgód. Najpierw zewnętrzna aplikacja tarzanAssemleChecklist.py potwierdza poprawne złożenie mechaniczne i elektryczne ramienia. Następnie 

```
tarzanPoKeysStart.py 
```

uruchamia testy startowe, odczytuje relację z 

```
tarzanPoKeysSetting.py
```

i dopiero po pełnej walidacji przekazuje system do poziomowania przez 

```
tarzanPoKeysLevels.py.
```

Sekwencja startowa 

1. zatwierdzenie listy składania, 

2. identyfikacja i walidacja Play / Rec, 

3. test komponentów krytycznych, 

4. weryfikacja zgód bezpieczeństwa, 

5. poziomowanie ramienia i głowicy, 

6. zgoda na pierwszy start roboczy. 

Każdy etap może zablokować przejście dalej.

### 9B. Zasada poziomu kamery

Oś poziomu kamery ma utrzymywać poziom obrazu za wszelką cenę, analogicznie do stabilizacji stosowanej w dronach. Oznacza to, że podstawowym celem tej osi nie jest efekt specjalny, tylko kompensacja odczytu z czujnika poziomu i utrzymanie horyzontu kamery.

Tryb efektowy z pochyłą głowicą pozostaje metodą drugorzędną. Domyślnie tarzan powinien traktować utrzymanie poziomu jako priorytet, a odchył kontrolowany jako funkcję świadomie wywoływaną przez operatora lub tryb specjalny.

Wniosek projektowy: logika poziomu kamery musi być powiązana z tarzanPoKeysLevels.py, warstwą czujników poziomu oraz klasą osi odpowiedzialnej za kompensację pochyłu głowicy.

## 10. Stan maszyny / logika pracy

Warto zbudować system jako maszynę stanów:

- OFF
- INIT
- HOMING
- IDLE
- MANUAL
- AUTO
- CALIBRATION
- ERROR
- EMERGENCY_STOP

### Przykładowa logika

- po starcie system przechodzi do INIT

- następnie wykonuje HOMING

- po poprawnym homingu przechodzi do IDLE

- z IDLE może wejść w MANUAL lub AUTO

- wykrycie błędu przenosi do ERROR

- E-STOP przenosi do EMERGENCY_STOP

Dodatkowo logika użytkowa powinna uwzględniać wybór domyślnego trybu z listy, z domyślnym startem w trybie: **- tM**

## 10.1. Cykliczna metoda pracy systemu TARZAN (główna pętla sterowania)

Sterowanie systemem TARZAN oparte jest na cyklicznej metodzie analizy sygnałów, która stanowi podstawę działania wszystkich trybów pracy. System pracuje w sposób ciągły w pętli sterującej, w której w każdej iteracji wykonywane są następujące kroki:

• Odczyt wejść sterujących
• Odczyt czujników systemowych
• Analiza bezpieczeństwa
• Analiza logiki aktualnego trybu pracy
• Wyznaczenie decyzji sterowania
• Wysterowanie wyjść systemowych
• Zapis stanu systemu do protokołu komunikacyjnego
• Aktualizacja komunikatów dla operatora

Każdy tryb pracy systemu korzysta z tej samej struktury cyklu sterowania.

## 10.2 Schemat cyklu sterowania

```
1. Zbieranie wejść
   ├─ sterowniki operatora (SOK)
   ├─ sterownik RRP
   ├─ przyciski funkcyjne
   ├─ przełączniki trybów
   └─ sygnały systemowe

2. Zbieranie czujników
   ├─ krańcówki osi
   ├─ czujnik poziomu
   ├─ czujnik laserowy geometrii ramienia
   ├─ czujnik wstrząsowy
   ├─ czujnik odległości TF-Luna
   └─ inne czujniki systemowe

3. Analiza bezpieczeństwa
   ├─ wykrycie uderzenia
   ├─ utrata geometrii ramienia
   ├─ nagła zmiana poziomu
   ├─ przekroczenie krańcówek
   └─ inne warunki alarmowe

4. Logika trybu pracy
   ├─ interpretacja wejść operatora
   ├─ wybór aktywnych osi
   ├─ decyzja o kierunku ruchu
   ├─ decyzja o prędkości
   └─ decyzje automatyki wspomagającej

5. Generowanie sygnałów sterujących
   ├─ STEP
   ├─ DIR
   ├─ ENABLE
   ├─ sterowanie regulatora masy
   └─ inne wyjścia sprzętowe

6. Komunikaty systemowe
   ├─ LCD
   ├─ LED Matrix
   ├─ sygnały dźwiękowe
   └─ wibracje sterowników

7. Zapis do protokołu ruchu
   ├─ stan wejść
   ├─ stan czujników
   ├─ stan wyjść
   └─ znacznik czasu
8. Edytor choreografii ruchu
   ├─ take model
   ├─ krzywa ruchu
   ├─ generator
   └─ motion config
```

## 11. Dane konfiguracyjne

W tarzanUstawienia.py, TarzanRejestr.json oraz plikach referencyjnych warto przechowywać: 

- limity osi, 

- prędkości maksymalne, 

- przyspieszenia, 

- kierunki domyślne, 

- parametry homingu, 

- mapowanie pinów, 

- przełożenia mechaniczne, 

- kroki na jednostkę, 

- mikrokrok, 

- progi bezpieczeństwa, 

- profile regulatora masy, 

- numery seryjne urządzeń, 

- ustawienia UI, 

- timeouty, 

- ustawienia protokołu, 

- ustawienia czujników, 

- ustawienia testów.

Dane należy rozdzielić na: 

- konfigurację stałą sprzętową 

- tylko do odczytu,

- konfigurację użytkową 

- zmienianą z poziomu panelu ustawień.

Podstawowe znane parametry startowe:

- czas próbkowania protokołu: 10 ms,
- PoKeys57UPlayDeviceSerial = 34238
- PoKeys57URecDeviceSerial = 33410,
- startowy mikrokrok: 32.

### 11.1 Edytor choreografii ruchu TARZANA

Edytor choreografii ruchu TARZANA jest operatorskim narzędziem do nagrywania, wizualizacji, edycji, wygładzania i wersjonowania ruchu wszystkich osi systemu TARZAN w ujęciu filmowym. Jego zadaniem nie jest techniczna edycja pojedynczych sygnałów STEP/DIR, lecz intuicyjna korekta przebiegu ruchu w czasie w taki sposób, aby operator mógł dopracować płynność, rytm, moment startu, zakończenie oraz zależności pomiędzy osiami bez ingerowania w techniczne szczegóły sterowania.

Edytor pracuje na komputerze jako główna platforma operatorska. W dalszym etapie logika tego modułu może zostać częściowo uproszczona i zaimplementowana na urządzeniach NEXTION jako interfejs pomocniczy, jednak pełna wersja edycyjna ma być realizowana w środowisku Python GUI.

Edytor choreografii ruchu TARZANA jest narzędziem do filmowej deformacji nagranego przebiegu ruchu osi w czasie, przy zachowaniu stałej drogi ruchu i ograniczeń mechanicznych każdej osi.

### Główna zasada działania

Podstawą pracy edytora jest filozofia projektu TARZAN, w której nadrzędnym parametrem ruchu jest czas, a nie pozycja docelowa. Oznacza to, że ruch nie jest traktowany jak komenda CNC prowadząca oś do konkretnego punktu, lecz jako ciąg zdarzeń i stanów ruchowych rozłożonych w czasie. Dzięki temu nagrany ruch może być później analizowany, edytowany i przeliczany ponownie na sygnały sterujące w sposób zgodny z charakterem pracy filmowej.

Edytor przedstawia ruch jako ciągłe krzywe natężenia względem czasu. Wartości dodatnie oznaczają ruch w jednym kierunku, a wartości ujemne ruch w kierunku przeciwnym. Taka prezentacja pozwala operatorowi intuicyjnie rozumieć:

- kierunek ruchu,

- intensywność ruchu,

- tempo narastania i wygaszania ruchu,

- momenty zatrzymania,

- zmianę kierunku,

- wzajemne relacje pomiędzy osiami.

Krzywa edycyjna nie zastępuje protokołu czasowego TARZANA, lecz stanowi jego roboczą warstwę operatorską. Po zakończeniu edycji system automatycznie przelicza dane z powrotem na protokół sygnałów sterujących zgodny z architekturą systemu.

### Zakres osi objętych edycją

Edytor obejmuje wszystkie osie ruchowe wykorzystywane w pracy systemu:

- oś pozioma kamery,

- oś pionowa kamery,

- oś pochyłu kamery,

- oś ostrości kamery,

- oś pionowa ramienia,

- oś pozioma ramienia.

Dodatkowo edytor obejmuje także sygnał drona, jednak nie w postaci pełnej krzywej natężenia. Dron w edytorze ma być prezentowany jako punktowy sygnał zdarzeniowy na osobnej małej osi. Punkt ten oznacza moment aktywacji sygnału zwolnienia elektromagnesu. Dzięki temu operator może synchronizować zdarzenie zwolnienia z ruchem pozostałych osi w ramach jednego TAKE.

### Przeznaczenie operatorskie

Edytor choreografii ruchu TARZANA ma być narzędziem filmowca, a nie interfejsem technicznym dla programisty lub automatyka. Z tego względu interfejs ma być maksymalnie prosty, czytelny i skoncentrowany na pracy operatorskiej. Operator ma widzieć wyłącznie to, co jest potrzebne do świadomej korekty ujęcia.

Na ekranie powinny być widoczne jednocześnie wszystkie osie, każda jako osobna krzywa na własnym poziomie wysokości. Całość ma być rozłożona na wspólnej osi czasu, tak aby operator od razu widział zależności pomiędzy wszystkimi elementami ruchu. Ekran roboczy zakłada wykorzystanie pełnej przestrzeni monitora HD.

Interfejs powinien zawierać jedynie podstawowe, proste elementy sterujące:

- PLAY,

- STOP,

- EDIT,

- SAVE TAKE.

Dodatkowo obowiązkowym elementem interfejsu jest playhead, czyli pionowa linia czasu wskazująca aktualny moment ujęcia, podobnie jak w systemach montażowych typu Avid. Ma ona umożliwiać szybkie zrozumienie, w którym miejscu czasowym znajduje się bieżąca analiza lub symulacja ruchu.

### Funkcje podstawowe edytora

Edytor musi umożliwiać:

- nagrywanie ruchu do TAKE,

- odczyt i wizualizację nagranego TAKE,

- prostą ręczną edycję krzywych ruchu,

- przesuwanie ruchu w czasie,

- opóźnianie początku ruchu,

- wcześniejsze lub późniejsze zakończenie ruchu,

- skracanie lub wydłużanie fragmentów ruchu,

- korektę intensywności ruchu w wybranych przedziałach czasu,

- wygładzanie niedoskonałości ruchu nagranego przez człowieka,

- poprawianie płynności całego ujęcia,

- zachowanie zależności pomiędzy osiami,

- zapis kolejnych wersji TAKE,

- eksport ruchu do trybu tAA — All-Auto,

- odtwarzanie testowe w formie symulacji.

W pierwszej wersji PLAY ma służyć wyłącznie do symulacji przebiegu ruchu, bez wysyłania rzeczywistego sterowania do układu wykonawczego.

### Wygładzanie i korekta filmowa

Jedną z najważniejszych funkcji edytora jest możliwość niwelowania niedociągnięć ruchu wykonanego przez człowieka. W praktyce oznacza to, że nagrany ruch może zawierać:

- drobne szarpnięcia,

- nierówności tempa,

- niepożądane mikrodrgania,

- zbyt gwałtowne wejścia i wyjścia z ruchu,

- błędy wynikające z reakcji operatora na akcję aktora.

Edytor musi umożliwiać zarówno ręczną korektę takich niedoskonałości, jak i ich półautomatyczne wygładzanie przez algorytm. Celem tej funkcji nie jest techniczne filtrowanie danych dla samej poprawności matematycznej, lecz dopracowanie jakości ujęcia filmowego i osiągnięcie lepszej płynności ruchu.

### Ghost ruchu

Obowiązkową funkcją edytora jest tryb **ghost ruchu**, czyli jednoczesne pokazanie:

- oryginalnego nagranego przebiegu,

- aktualnie edytowanej wersji przebiegu.

Dzięki temu operator może widzieć, jak bardzo zmienił charakter ruchu i czy poprawki prowadzą w pożądanym kierunku. Jest to szczególnie istotne przy subtelnej pracy nad płynnością ujęcia.

### Zoom osi czasu

Edytor musi posiadać funkcję zoom czasu, pozwalającą przybliżać i oddalać skalę osi czasu. Funkcja ta jest konieczna zarówno do ogólnej oceny całego ujęcia, jak i do precyzyjnej korekty krótkich fragmentów ruchu.

### TAKE i wersjonowanie

Podstawową jednostką pracy edytora jest TAKE. TAKE oznacza pojedynczy zapis ruchu, który może być nagrywany, edytowany, poprawiany i zapisywany w kolejnych wersjach. System nie powinien nadpisywać bez potrzeby wcześniejszych wersji, lecz tworzyć ich kolejne odmiany. Dzięki temu operator może wracać do wcześniejszych wariantów ujęcia i porównywać efekty zmian.

Rejestr projektu pełni rolę modelu logicznego i organizacyjnego, natomiast rzeczywiste zapisy TAKE mogą być przechowywane w osobnych plikach tekstowych lub innych plikach roboczych zgodnych z przyjętym formatem projektu.

### Architektura logiczna modułu

Edytor choreografii ruchu TARZANA powinien być oparty na czterech głównych warstwach działania:

### Nagrywanie ruchu

Z protokołu ruchu powstaje zapis TAKE obejmujący przebieg wszystkich osi oraz zdarzeń dodatkowych.

### Model TAKE

Z surowego zapisu system buduje uproszczoną, operatorską warstwę edycyjną zawierającą:

- czas,
- kierunek,
- natężenie,
- długość segmentów ruchu,
- zależności pomiędzy osiami,
- zdarzenia punktowe takie jak sygnał drona.

### Edytor krzywych

Operator edytuje wyłącznie prosty, wizualny przebieg ruchu bez konieczności pracy na technicznych sygnałach wykonawczych.

### Silnik syntezy

Po zakończeniu edycji system przelicza krzywe ruchu z powrotem na sygnały sterujące zgodne z architekturą TARZAN i przygotowuje dane do wykorzystania w trybie tAA.

### Założenia implementacyjne

W projekcie należy utrzymać rozdzielenie pomiędzy warstwą operatorską a warstwą techniczną. Główna klasa edytora powinna stanowić moduł interfejsu użytkownika, natomiast logika TAKE, krzywych ruchu, syntezy oraz konfiguracji powinna być rozdzielona na osobne moduły pomocnicze.

Docelowo zaleca się wykorzystanie następujących plików:

- tarzanEdytorChoreografiiRuchu.py

- tarzanTakeModel.py

- tarzanKrzyweRuchu.py

- tarzanGeneratorTAA.py

- tarzanMotionConfig.py

Takie rozdzielenie pozwoli zachować porządek architektury i uniknąć mieszania interfejsu operatorskiego z logiką wewnętrzną systemu.

### Znaczenie modułu w projekcie

Edytor choreografii ruchu TARZANA jest jednym z kluczowych modułów całego systemu, ponieważ tworzy pomost pomiędzy:

- rzeczywistym nagraniem ruchu,

- świadomą korektą operatorską,

- ponowną syntezą sterowania automatycznego.

W praktyce oznacza to, że TARZAN nie tylko rejestruje ruch, ale także umożliwia jego późniejsze filmowe opracowanie. Moduł ten stanowi więc swoistą montażownię ruchu kamerowego, która pozwala dopracować ujęcie nie tylko pod względem zgodności z ruchem aktora, ale przede wszystkim pod względem jakości, rytmu i płynności ruchu.

### Ciągłość i „zespawanie” przebiegu ruchu

Profil ruchu każdej osi w ramach TAKE ma charakter ciągły i nierozłączny. Edycja nie polega na składaniu ruchu z osobnych segmentów ani na kopiowaniu fragmentów, lecz na deformowaniu już nagranego przebiegu w czasie. Oznacza to, że linia ruchu pozostaje jednym spójnym przebiegiem, który może być lokalnie ściskany, rozciągany, wygładzany i przesuwany w czasie bez rozrywania jego ciągłości.

## Stała droga ruchu osi

Edycja krzywej nie zmienia całkowitej drogi ruchu zapisanej dla danej osi w obrębie danego fragmentu TAKE, lecz zmienia jedynie rozkład tego ruchu w czasie. Oznacza to, że operator koryguje dynamikę, tempo i płynność przebiegu, przy zachowaniu tej samej drogi mechanicznej wynikającej z liczby impulsów oraz parametrów osi.

### Ograniczenia mechaniczne jako warunek bezwzględny

Każda edycja krzywej musi pozostawać zgodna z parametrami mechanicznymi danej osi, w szczególności z maksymalną prędkością, dopuszczalnym przyspieszeniem, minimalnym czasem pełnego cyklu, strefą łagodnego rozruchu oraz kompensacją luzów. Edytor nie może dopuścić do wygenerowania przebiegu, który naruszałby ograniczenia wynikające z mechaniki układu.

## Pełna mapa choreografii ruchu

Pełna mapa znajduje się w pliku

```
TARZAN_CHOREOGRAFIA_RUCHU_MOEDEL_MATEMATYCZNY.md
```

## 12. Diagnostyka i logowanie

System powinien mieć logi dla: 

- startu systemu, 

- homingu, 

- błędów krańcówek, 

- prób wyjścia poza zakres, 

- aktywacji regulatora masy, 

- przeciążenia napędów, 

- zatrzymania awaryjnego, 

- wykonanych presetów, 

- nagrywania i odtwarzania protokołu, 

- niezgodności konfiguracji sprzętowej, 

- konfliktu sygnałów, 

- błędów komunikacji z płytkami.

Dobrze przewidzieć klasy: 

- eventLogger 

- diagnosticSnapshot

W oknach operatorskich komunikaty robocze powinny trafiać do terminala logu na dole ekranu, bez popupów.

## 13. Roadmapa rozwoju

### V1 — fundament

- klasa bazowa osi,
- 6 osi podstawowych,
- prosty homing,
- proste sterowanie ręczne,
- podstawowe limity,
- szkic regulatora masy,
- podstawowa definicja sygnałów,
- podstawowe połączenie z Play i Rec.

### V2 — integracja balansu i protokołu

- pełna klasa TarzanRegulatorMasy,
- powiązanie z osią pionową ramienia,
- profile odciążania przy ruchu w górę / w dół,
- bezpieczne przejścia balansu,
- protokół próbkowany co 10 ms,
- rozdział sygnałów LH / CTR / Analog,
- podział sygnałów na Play / Rec / CNC.

### V3 — planowanie ruchu

- MotionPlanner,
- płynne profile ruchu,
- ruch wieloosiowy,
- presety pozycji,
- integracja z record / play.

### V4 — bezpieczeństwo i diagnostyka

- pełny SafetyManager,
- lepsze logi,
- obsługa błędów,
- watchdog,
- tryb serwisowy,
- weryfikacja konfiguracji PoKeys / PoStep.

### V5 — inteligencja systemu

- automatyczne trajektorie,
- profile pracy zależne od obciążenia,
- półautonomiczne pozycjonowanie,
- możliwa integracja z wizją komputerową,
- tracking,
- integracja z 3D,
- integracja z dronem.

## 14. Najważniejsze decyzje architektoniczne

### Decyzja 1

Regulator masy nie jest zwykłą osią. Powinien być osobnym modułem kompensacyjnym.

### Decyzja 2

Wszystkie osie muszą dziedziczyć po wspólnej klasie bazowej. To uprości rozwój i testowanie.

### Decyzja 3

Bezpieczeństwo musi być centralne, nie rozproszone. Jedna warstwa powinna zatwierdzać ruchy.

### Decyzja 4

Oś pionowa ramienia i balans to jeden logiczny układ. Nie wolno ich projektować niezależnie.

### Decyzja 5

Projekt powinien być gotowy pod dalszą rozbudowę. Już teraz trzeba zostawić miejsce na presety, trajektorie, automatykę i sensory.

### Decyzja 6

Protokół ruchu ma być oparty o czas, a nie o samą pozycję docelową. To jest zapis przebiegów sterujących, nie klasyczny model CNC.

### Decyzja 7

Konfiguracja sprzętowa PoKeys i urządzeń fabrycznych musi być traktowana jako referencyjna i chroniona przed przypadkową zmianą.

### Decyzja 8

Projekt musi być uruchamiany etapami. Do tego służy tarzanMetodyZezwolenie.py i środowisko testowe tarzanTesty.py.

## 15. Minimalny rdzeń do implementacji jako pierwszy

Jeżeli mamy przejść do kodu, pierwszy sensowny rdzeń to:

```
tarzanZmienneSygnalowe.py

tarzanUstawienia.py

tarzanMetodyZezwolenie.py

TarzanAxis

TarzanArmVertical

TarzanArmHorizontal

TarzanRegulatorMasy

SafetyManager

HomingManager

TarzanSystem

tarzanPoKeysSetting.py

tarzanTesty.py
```

To pozwoli najpierw opanować najbardziej krytyczny fragment mechaniki: ruch ramienia + balans + bezpieczeństwo + zgodność sygnałów + testowanie elektroniki.

## 16. Jednozdaniowa definicja projektu

TARZAN to modułowy system sterowania inteligentnym ramieniem kamerowym, w którym osie ruchu kamery i ramienia współpracują z aktywnym regulatorem masy oraz z prostym protokołem czasowego zapisu sygnałów, aby zapewnić precyzję, płynność ruchu, powtarzalność ujęć i bezpieczne pokonywanie wpływu grawitacji. Cały ruch odbywa się bardzo wolo w oparciu o mechanikę układu.

## 17. Diagram przepływu sterowania

`                                        OPERATOR
                                                │
                                                │ sterowanie ręczne
                                               ▼
                                         UI SYSTEMU
                     (Nextion / LCD / przyciski / SOK / RRP)
                                                │
                                               ▼
                                       CONTROLLER
                                core/tarzanController.py
                                                │
                                               ▼
                                             MODES
                          (logika aktualnego trybu pracy)
                    │
        ┌──────────────┼──────────────┐
        │                                       │                                      │
       ▼                                      ▼                                    ▼
  tM (manual)           tMAS (manual+auto)           tREC / tPLAY / AUTO / INNE...
                                                  │
                                                 ▼
                                            SAFETY
                              safety/safetyManager.py
                                     ├─ krańcówki
                                     ├─ czujnik wstrząsowy
                                     ├─ czujnik laserowy geometrii
                                     ├─ czujnik poziomu
                                     └─ inne zabezpieczenia
                                      │
                      (jeżeli OK → ruch)
                                      │
                                     ▼
                                MOTION
                       motionPlanner.py
                        motionProfile.py
                                      │
                                     ▼
                                  AXIS
                  mechanics/tarzanAxis.py
                                     ├─ oś pozioma kamery
                                     ├─ oś pionowa kamery
                                     ├─ oś pochyłu kamery
                                     ├─ oś ostrości kamery
                                     ├─ oś pionowa ramienia
                                     └─ oś pozioma ramienia
                                    │
                                   ▼
                           HARDWARE
            hardware/tarzanPoKeys*.py
                                    ├─ STEP
                                    ├─ DIR
                                    ├─ ENABLE
                                    ├─ regulator masy
                                    └─ inne wyjścia
                                    │
                                   ▼
                               SILNIKI
                       + urządzenia
                                   │
                                  ▼
                             SENSORS
                                   ├─ krańcówki osi
                                   ├─ czujnik poziomu
                                   ├─ czujnik laserowy
                                   ├─ czujnik wstrząsowy
                                   ├─ TF-Luna
                                   │  └─ inne czujniki
                                   │
                                   │ dane pomiarowe
                                  ▼
                          CONTROLLER
                   (kolejna iteracja pętli)

## 18. Zasada zapisu sygnałów

Poniższy opis jest włączony do dokumentacji jako źródłowa zasada zapisu sygnałów sterujących TARZAN i pozostaje bez modyfikacji treści:

- w każdej próbce czasu

- dla każdej osi i sygnału

- zapisujemy stan sygnału dokładnie w tej chwili

- np. 1 / 0, ewentualnie komplet stanów logicznych i pomocniczych

tak, aby dało się odtworzyć rzeczywisty ruch jako sekwencję zmian w czasie
Czyli to ma być de facto:

- „timeline ruchu” / „zapis przebiegów sterujących”,
  a nie „lista komend pozycjonujących”.

- osią nadrzędną nie jest „pozycja”, tylko czas

- każda mikrosekunda albo każdy ustalony tick czasu ma swój rekord

### 18.1. Protokół komunikacji — rozwinięcie implementacyjne

Powyższa zasada źródłowa pozostaje podstawą. Poniższe rozwinięcie ma już charakter programistyczny i wiąże protokół komunikacji z pakietem danych, czujnikami, trybami pracy oraz strukturą modułów tarzan.

W implementacji tarzan protokół komunikacji ma być budowany jako pakiet danych uporządkowany w osi czasu. Każda próbka protokołu musi odnosić się do ustalonego czasu próbkowania 10 ms i zawierać pełny stan sygnałów potrzebnych do wiernego odtworzenia ruchu, odczytu czujników i kontroli bezpieczeństwa.

Minimalne grupy danych w jednej próbce protokołu: - identyfikacja próbki: numer próbki, czas, aktywny tryb, znaczniki zdarzeń, - domena Play: stany wejść i wyjść związanych z wykonaniem ruchu, - domena Rec: stany rejestrowanego sterowania i mostka sygnałów, - domena CNC / automatyka: sygnały generowane przez warstwę automatyki, - grupa osi: STEP / DIR / ENABLE dla osi kamery i ramienia, - grupa regulatora masy: dodaj / ujmij / stan krańcówek / gotowość, - grupa czujników: TF-Luna, czujnik poziomu, PoSensors i krańcówki, - grupa interfejsu: wybór trybu, przyciski funkcyjne, potwierdzenia operatora i komunikaty zdarzeń.

### 18.2. Przykład ramki protokołu z danymi osi, czujników i stanu trybu

Przykład czytelnej ramki tekstowej:

```
t=001250 ms | TRYB=tMAS | CAM_PAN_STEP=1 | CAM_PAN_DIR=0 | 
CAM_TILT_STEP=0 | CAM_TILT_DIR=1 | ARM_VERT_STEP=1 | ARM_VERT_DIR=1 | 
MASS_ADD=0 | MASS_SUB=1 | LIMIT_ARM_UP=0 | LIMIT_CAM_LEFT=0 | 
LEVEL_X=+0.2 | LEVEL_Y=-0.1 | TF_LUNA=1450 |F1=0 | F2=1 | AUTO_EN=1
```

Przykład zwartej ramki kolumnowej do zapisu plikowego:

```
`1250;tMAS``;1;0;0;1;1;1;0;1;0;0``;+0.2;-0.1;1450;0;1;1`
```

W obu przykładach pierwsze pola opisują czas i tryb, kolejne pola opisują sygnały CTR i kierunki, następne pola opisują krańcówki i regulator masy, a końcowe pola opisują czujniki i stan logiki operatorskiej. Dokładna kolejność kolumn ma być jedną stałą definicją systemową.

### 18.3. Związek protokołu z trybami pracy

Protokół musi umieć zapisać ręczne sterowanie SOK, stany krańcówek, poziomowanie głowicy i komunikaty wynikające ze zdarzeń granicznych. W tMAS protokół musi dodatkowo zapisać sterowanie z RRP, stan zgody AUTO, procedurę uruchomienia, potwierdzenia operatora oraz sygnały bezpieczeństwa związane z aktywną automatyką osi ramienia.

To oznacza, że dwa pierwsze tryby nie są jedynie trybami interfejsu. One definiują realny zakres danych, które muszą zostać obsłużone przez protokół komunikacji i później przez wizualizację oraz edycję sygnałów.

rekord zawiera stany wszystkich istotnych linii/sygnałów

np. dla osi krokowej nie zapisujemy „pozycja = 1250”, tylko raczej:

- STEP = 0/1
- DIR = 0/1
- ENABLE = 0/1
- ewentualnie dodatkowe sygnały sterujące

dla regulatora masy i innych elementów analogicznie zapisujemy ich stan w tej samej osi czasu

całość ma pozwolić na:

- analizę ruchu

- wierne odtworzenie

- synchronizację wszystkich osi i urządzeń

Czyli dokumentacyjnie protokół powinien być opisany bardziej tak:`

`w chwili T - CAM_PAN_STEP = 1 - CAM_PAN_DIR = 0 - CAM_TILT_STEP = 0 - ARM_VERTICAL_STEP = 1 - MASS_REG_ADD = 0 - MASS_REG_SUB = 1 - itd.`

a potem w następnej mikrosekundzie kolejny pełny stan.

Przykładowo idea rekordu byłaby bliżej temu:

`t=000000125 us | ``CAM_PAN_STEP``=1 | ``CAM_PAN_DIR``=0 | ``CAM_TILT_STEP``=0 | ``CAM_TILT_DIR``=1 | ``ARM_VERT_STEP``=1 | ``ARM_VERT_DIR``=1 | ``MASS_ADD``=0 | ``MASS_SUB``=1`

albo w wersji bardziej zwartej:

```
`125;1;0;0;1;1;1;0;1`
```

z dokładnie zdefiniowaną kolejnością kolumn. To ma być zapis ruchu jako funkcji czasu, próbka po próbce, a nie model pozycyjny.

I druga ważna rzecz: taki zapis jest bliższy:

- rejestracji przebiegów logicznych,

- taśmie sterującej,

- motion capture dla sygnałów sterowania,

Inne niż klasycznemu G-code lub komendom CNC.

## 19. Uzupełnienia zgodności z dokumentami źródłowymi

Poniższe elementy zostały dopisane, aby mapa była zgodna z pełnymi założeniami projektu:

- core/
- hardware/
- mechanics/
- modes/
- ui/
- data/

### Typy sygnałów

- LH — sygnały logiczne wysokie / niskie,
- CTR — sygnały impulsowe sterujące ruchem,
- Analogowe — potencjometry / wejścia analogowe.

### Domeny sygnałów

- Play
- Rec
- CNC / automatyka

### Główne urządzenia operatorskie i wykonawcze

- PoKeys57U Play,
- PoKeys57U Rec,
- PoExtBusOC16-CNC,
- PoStep25,
- Nextion 7”,
- Nextion 5”,
- LCD wc1602a x2,
- Matrix LED 8x8,
- klawiatura 4x3,
- F1–F4,
- TF-Luna,
- PoSensors,
- Czujnik światła TSL25911,
- SOK,
- RRP,
- Czujnik laserowy,
- Czujnik wstrząsowy,
- kamera usb HD
- kamera USB do analizy

### Jednostka czasu systemu

- podstawowa jednostka czasu protokołu: 10 ms

### Wymaganie wydajnościowe

System ma działać na lekkim mini PC Jetway NP93 i dlatego: - kod ma być oszczędny pamięciowo, - logika ma być prosta, - należy unikać ciężkich bibliotek, - preferowany system operacyjny: Windows 10 64-bit.

### Testowanie i interfejs

tarzanTesty.py ma być pełnoekranowym panelem testowym w dark mode, z dużymi przyciskami i terminalem logów na dole, bez popupów roboczych.

### Bezpieczeństwo sprzętowe

Ruch nie startuje, jeśli: - brak połączenia z wymaganą płytką, - brak zgodności konfiguracji PoKeys, - brak zgody modułu tarzanMetodyZezwolenie.py, - brak gotowości osi, - brak gotowości regulatora masy, - aktywna krańcówka blokująca ruch, - wykryto konflikt sygnałów.

### Dodatkowa walidacja dla Record / Play

Record i Play wymagają walidacji protokołu przed odtworzeniem: - format pliku, - zgodność czasu próbkowania, - integralność sygnałów CTR, - zgodność nazw osi, - brak konfliktu kierunków i enable.

## 20. Fizyczne złącza systemu (panel połączeń)

System TARZAN posiada panel złączy zewnętrznych opisany tabliczką „PODŁĄCZENIA”. Złącza te definiują fizyczne interfejsy komunikacyjne i zasilające całego systemu.

Układ złączy jest następujący:

```
1 — STEROWANIE GŁÓWNE
2 — SOK RAMIĘ PION
3 — SOK RAMIĘ POZIOM
4 — TABLET
5 — SOK KAM OSTROŚĆ
6 — GŁOWICA STEROWANIE
7 — GŁOWICA CZUJNIKI
8 — REG. MASY
```

### 20.1. Podział funkcjonalny złączy

#### Sterowanie i komunikacja

- sterowanie główne systemu TARZAN

- komunikacja z tabletem operatorskim Nextion

- sterowanie głowicy kamerowej

- sygnały czujników głowicy

#### Sterowniki osi (SOK)

- sterownik osi ramię pion

- sterownik osi ramię poziom

- sterownik osi kamera ostrość

#### Mechanizm kompensacji

- sterowanie regulatorem masy

### 20.2. Znaczenie architektoniczne

Panel złączy stanowi fizyczny odpowiednik warstwy hardware systemu opisanej w architekturze projektu bezpośrednio połączony z dokumentacją:

```
PoKeys - protocol specification.pdf

PoKeys57 - user manual.pdf

PoSensors.pdf

PoStep25-32 UserManual.pdf

STERWONIKI silinkow krokowych POKSYG.pdf
```

### 20.3. Wpływ na model sygnałów

Złącza panelu stanowią podstawę do budowy mapy sygnałów w module `tarzanZmienneSygnalowe.py.`

Każdy port panelu może być traktowany jako: 

- grupa sygnałów LH, 

- sygnały sterujące CTR, 

- ewentualne sygnały analogowe.

To oznacza, że panel połączeń nie jest jedynie opisem mechanicznym urządzenia, ale również punktem odniesienia dla logicznej organizacji sygnałów, testów, diagnostyki i przyszłego mapowania I/O w kodzie.

### 20.4. Wniosek projektowy i PoKeys

Panel połączeń powinien być traktowany jako oficjalna warstwa referencyjna fizycznych interfejsów TARZAN i PoKeys.

W praktyce oznacza to, że: 

- nazwy portów z tabliczki powinny być zachowane w dokumentacji, 

- nazwy uproszczone mogą być używane w kodzie jako aliasy, 

- każde złącze powinno mieć później własną tabelę sygnałów, 

- mapa połączeń panelu powinna zostać powiązana z konfiguracją sprzętową Play / Rec / CNC oraz z dokumentacją testową 
  
  ```
  tarzanTesty.py
  ```

## 21. Zasada zgodności z dokumentacją PoKeys i bibliotekami

Każda nowa wersja mapy, modułu lub klasy tarzan musi być sprawdzana względem dokumentacji PoKeys, biblioteki PoKeys dla Python oraz aktualnych plików referencyjnych projektu. W szczególności dotyczy to konfiguracji pinów, funkcji specjalnych, pulse engine, LCD, Matrix LED, PoExtBus oraz logiki odczytu i zapisu stanów.

Przed oddaniem nowej wersji należy zawsze wykonać kontrolę kompletności: czy nic nie zostało pominięte, czy mapa zgadza się z dokumentacją sprzętową oraz czy nowe moduły nie naruszają wcześniej przyjętych założeń projektu. Ta zasada jest stałą regułą pracy nad tarzan.

Mapa została uzupełniona z uwzględnieniem aktualnych plików referencyjnych 

```
tarzanPoKeysSetting.py 
```

oraz tarzan

```
ZmienneSygnalowe.py 
```

które definiują odpowiednio warstwę stałej konfiguracji PoKeys i centralną mapę sygnałów systemu.

## 22. Mechanika i proporcje przekładni

Warstwa elektroniczne jest ściśle powiązana z mechaniką i pewne i bezawaryjne funkcjonowanie to główna zasada, która musi być uwzględniona. Tak jak i bezpieczeństwo i niwelowanie mechanicznych niedoskonałości.

### 22.1 Parametr bezpieczeństwa czasu pełnego cyklu osi

Każda ruchoma oś systemu TARZAN musi posiadać zdefiniowany stały parametr minimalnego czasu wykonania jednego pełnego cyklu roboczego. Parametr ten jest parametrem ochronnym i wynika z wymagań bezpieczeństwa mechaniki, przekładni oraz silników krokowych.

Pełny cykl osi oznacza wykonanie całego dopuszczalnego zakresu ruchu tej osi, wynikającego z jej maksymalnego kąta roboczego ograniczonego konstrukcją mechaniczną i ogranicznikami krańcowymi.

- Minimalny czas pełnego cyklu:

- ma być definiowany osobno dla każdej osi,

- ma być zapisywany w minutach,

- jest wartością stałą i nie może być dowolnie skracany przez logikę programu,

- służy do wyliczenia maksymalnej dopuszczalnej prędkości impulsów STEP dla danej osi.

Celem tego ograniczenia jest ochrona układu przed:

- gwałtownym startem osi,

- przeciążeniem mechanicznym,

- gubieniem kroków,

- przegrzaniem lub spaleniem silników,

- uszkodzeniem przekładni i elementów konstrukcyjnych.

System nie może dopuścić do wykonania pełnego cyklu osi w czasie krótszym niż zapisany minimalny czas pełnego cyklu. Oznacza to, że maksymalna częstotliwość impulsów sterujących dla osi musi być wyliczana na podstawie:

- liczby impulsów potrzebnych do wykonania pełnego cyklu osi,

- minimalnego czasu wykonania tego cyklu.
  Parametr ten ma charakter nadrzędnego zabezpieczenia mechaniczno-czasowego i musi być respektowany przez wszystkie tryby pracy systemu.

### 22.2 Główne parametry ustawień mechaniki

Pełen opis w pliku tarzanMechanics.py tu zestawienie, który wynika z metod:

- oś pozioma kamery – jeden pełny cykl to: 28800 impulsów.
- oś pionowa kamery – jeden pełny cykl to: 12800 impulsów.
- oś pochyłu kamery – jeden pełny cykl to: 3200 impulsów.
- oś ostrości kamery – jeden pełny cykl to: 30764 impulsów.
- oś pionowa ramienia – jeden pełny cykl to: 28485 impulsów.
- oś pozioma ramienia – jeden pełny cykl to: 92272 impulsów.

### 22.3 Strefa łagodnego rozruchu osi

W systemie TARZAN początkowa faza ruchu osi musi być traktowana jako strefa podwyższonego obciążenia mechanicznego. Najbardziej krytyczny jest moment wyprowadzenia ramienia z równowagi oraz pierwsze milimetry lub pierwsze stopnie ruchu osi.

W tej fazie układ pokonuje jednocześnie:

- bezwładność początkową,

- zmianę równowagi,

- obciążenie grawitacyjne,

- napięcia i luzy mechaniczne układu.

Z tego powodu pierwsze impulsy sterujące nie mogą być podawane z pełną prędkością roboczą. Początkowa część ruchu musi być realizowana wolniej, aby:

- nie powodować szarpnięcia osi,

- nie gubić kroków,

- nie tracić precyzji,

- nie wyprowadzać ramienia z płynnej pracy.

Dla każdej osi należy zdefiniować strefę łagodnego rozruchu, określoną jako:

- początkowy zakres ruchu,

- oraz maksymalna dopuszczalna prędkość impulsów w tej strefie.

Strefa ta jest parametrem wynikającym z mechaniki układu i powinna być traktowana jako stały warunek bezpiecznego sterowania osią.

### 22.4 Kompensacja luzów przekładni zębatych

W mechanice osi TARZAN należy uwzględnić luz przekładni zębatych jako stały parametr konstrukcyjny wpływający na precyzję ruchu, szczególnie przy zmianie kierunku.

W osiach kamery oraz osi ostrości występuje jedna para zazębienia, dlatego uwzględniany jest jeden luz przekładni.

W osiach ramienia występują dwa stopnie zazębienia:

- pierwszy stopień: zębatka silnika → zębatka pośrednia,
- drugi stopień: zębatka pośrednia → zębatka osi głównej,
  przy czym druga i trzecia zębatka leżą na tej samej osi pośredniej. Oznacza to, że całkowity luz osi ramienia jest sumą luzów dwóch zazębień.

Dla zębatek o skoku M1 luz pomiędzy stykami zębów może wynosić około 0,5 mm dla jednego kierunku pracy. Przy zmianie kierunku ruchu układ musi najpierw skasować luz mechaniczny, dlatego efektywny martwy skok wzrasta około dwukrotnie dla danego zazębienia.

W praktyce oznacza to:

- dla osi kamery i ostrości kompensacja zmiany kierunku obejmuje jeden luz,

- dla osi ramienia kompensacja zmiany kierunku obejmuje dwa luzy i musi być liczona jako suma obu stopni przekładni.

Kompensacja luzów powinna być zapisana w klasie mechaniki jako stały parametr osi i później uwzględniana przez logikę generowania impulsów przy zmianie kierunku ruchu.

Jeżeli chcesz, w następnym kroku dam Ci już dokładny blok kodu do wklejenia do obecnego tarzanMechanics.py, bez ruszania reszty pliku.

## 23. Zabezpieczenie integralności mechanicznej układu

System tarzan musi wykrywać nie tylko bezpośrednie uderzenie mechaniki, ale również utratę prawidłowej geometrii ramienia oraz nagłą zmianę poziomu układu.

Stanem prawidłowym dla systemu tarzan jest ruch:

- cichy,
- płynny,
- geometrycznie stabilny.
  Każde silne uderzenie, utrata osiowości wykryta przez laser lub nagła nienaturalna zmiana poziomu muszą być traktowane jako zdarzenie awaryjne.

Do tego celu należy wykorzystać trzy niezależne źródła kontroli:

- czujnik wstrząsowy,
- czujnik laserowy,
- czujnik poziomu.

### 23.1. Czujnik wstrząsowy

Czujnik wstrząsowy zabezpiecza układ przed uszkodzeniem mechanicznym wynikającym z:

- uderzenia w przeszkodę,
- kolizji,
- gwałtownego szarpnięcia mechaniki.
  W systemie tarzan należy przyjąć zasadę, że:

jeden silny impuls wstrząsowy przekraczający ustalony próg alarmowy oznacza stan nieprawidłowy i musi spowodować natychmiastowe zatrzymanie układu.

Czujnik ten ma wykrywać:

- uderzenie,
- kolizję,
- gwałtowne szarpnięcie,
- nienaturalną zmianę dynamiki mechaniki.

### 23.2. Czujnik laserowy

Czujnik laserowy pełni funkcję kontroli geometrii ramienia.

Jeżeli światło lasera pada idealnie centrycznie, oznacza to, że wzajemne ustawienie elementów ramienia nie zostało zmienione i układ zachowuje poprawną geometrię.

Jeżeli po uderzeniu, skręceniu lub przestawieniu któregoś elementu wiązka przestanie być zgodna z pozycją referencyjną, należy uznać to za utratę integralności mechanicznej układu.

Czujnik laserowy wykrywa więc:

- zmianę wzajemnego ustawienia elementów ramienia,

- skręcenie któregoś segmentu,

- utratę osiowości konstrukcji,

- rozstrojenie geometrii układu.

Laser nie pełni wyłącznie funkcji pomiarowej, lecz działa jako:
strażnik geometrii ramienia.

### 23.3. Czujnik poziomu

Czujnik poziomu pełni funkcję kontroli stabilności przestrzennej układu.

Jeżeli poziom zmieni się nagle i w sposób niezgodny z aktualnie wykonywanym ruchem, oznacza to stan nieprawidłowy, który może świadczyć o:

- przesunięciu konstrukcji,

- skręceniu któregoś elementu,

- rozkalibrowaniu mechaniki,

- utracie stabilności układu.

Czujnik poziomu ma więc wykrywać:

- nagłą nienaturalną zmianę poziomu,

- utratę stabilności układu,

- przesunięcie konstrukcji,

- zmianę ustawienia ramienia względem stanu referencyjnego.

### 23.4. Zasada wspólnej oceny integralności mechanicznej

Czujnik wstrząsowy, czujnik laserowy i czujnik poziomu tworzą razem jedną grupę bezpieczeństwa:

zabezpieczenie integralności mechanicznej układu

Oznacza to, że tarzan ma pilnować nie tylko:

- zakresów osi,

- krańcówek,

- prędkości ruchu,

- sygnałów bezpieczeństwa,

ale również:

- czy konstrukcja nadal ma prawidłową geometrię,

- czy układ nie został rozkalibrowany mechanicznie,

- czy dalsza praca nie grozi uszkodzeniem mechaniki albo utratą powtarzalności ruchu.

### 23.5. Reakcja systemu na alarm integralności mechanicznej

Jeżeli wystąpi którykolwiek z poniższych warunków:

- silny impuls z czujnika wstrząsowego,

- utrata centrycznego trafienia lasera,

- nagła nienaturalna zmiana poziomu,

to system ma:

- zatrzymać wszystkie osie,

- odłączyć sygnały ENABLE wszystkich napędów,

- przerwać aktywny ruch,

- zapisać błąd integralności mechaniki,

- wyświetlić jednoznaczny komunikat operatorowi,

- przejść do stanu ERROR albo EMERGENCY_STOP,

- zablokować automatyczne wznowienie pracy.

Wznowienie pracy może nastąpić dopiero po:

- świadomym potwierdzeniu operatora,

- kontroli stanu mechaniki,

- ponownej ocenie gotowości układu.

### 23.6. Zapis programistyczny

W implementacji programowej logika ta powinna zostać skupiona w jednym bloku bezpieczeństwa, np. w module:

```
safetyManager.py
```

Moduł ten powinien zbierać trzy sygnały alarmowe:

- alarm czujnika wstrząsowego,
- alarm czujnika laserowego,
- alarm nagłej zmiany poziomu,
  a następnie wykonywać wspólną ocenę integralności mechanicznej.

Schemat logiczny:

```
czujnik wstrząsowy
czujnik laserowy
czujnik poziomu
        ↓
ocena integralności mechanicznej
        ↓
STOP / ERROR / EMERGENCY_STOP
```

Wniosek programistyczny:

- logika alarmowa musi być wspólna,
- reakcja systemu musi być natychmiastowa,
- sygnał alarmowy nie może być ignorowany przez tryb pracy,
- bezpieczeństwo integralności mechanicznej ma pierwszeństwo przed logiką ruchu.
  Zabezpieczenia integralności mechanicznej są sprawdzane w każdej iteracji głównej pętli sterowania systemu TARZAN. Analiza wykonywana jest w module:

```
safety/safetyManager.py
```

Jeżeli którykolwiek z czujników zgłosi alarm, system przechodzi do stanu:

```
EMERGENCY_STOP
```

## 24. Moduł drona / elektromagnes zwalniający

Dron nie jest osią systemu tarzan. Dron jest mocowany elektromagnesem na końcu głowicy ramienia i porusza się razem z ramieniem w pełnej synchronizacji dynamicznej ujęcia.

W logice programu dron nie posiada:

- sterowania kierunkiem,

- sterowania prędkością,

- sterowania pozycją.

Moduł drona posiada tylko jeden stan wykonawczy:

```
ZWOLNIJ
```

Oznacza to, że w odpowiednim momencie ruchu, zgodnym z dynamiką ujęcia, tryb pracy może wydać zezwolenie na zwolnienie elektromagnesu, a dron odlatuje.

Wniosek programistyczny:

- dron nie może być modelowany jako oś,

- dron musi być modelowany jako oddzielny moduł specjalny,

- moduł drona posiada jedno wyjście logiczne typu „release / zwolnij”,

- warunek zwolnienia może zależeć od:

- czasu,

- próbki protokołu,

- pozycji fazowej ruchu,

- warunku bezpieczeństwa,

- zgody operatora.

Proponowany plik modułu:

```
mechanics/tarzanDronRelease.py
```

W formularzu logiki trybów dron powinien być osobną sekcją:

- aktywny / nieaktywny w trybie,

- sygnał ZWOLNIJ,

- warunek zwolnienia,

- komentarz po ludzku.

## 25. Sygnalizacja LED osi i modułów

Każda oś oraz każdy moduł wykonawczy systemu tarzan może posiadać własną logikę sygnalizacji LED. Dla każdej osi lub modułu należy móc zdefiniować:

- który sygnał LED jest z nim powiązany,

- jaki jest tryb pracy diody,

- w jakim warunku dioda ma działać,

- komentarz opisujący znaczenie sygnalizacji.

Obsługiwane zachowania LED:

- off

- on

- blink_slow

- blink_fast

- pulse

- toggle

- alternating

LED jest warstwą informacji stanu i musi być zapisywany razem z definicją trybu pracy.

## 26. Biblioteka dźwięków TARZAN

System posiada bibliotekę komunikatów głosowych i sygnałów ostrzegawczych używanych do informowania operatora o stanie pracy urządzenia, rozpoczęciu nagrywania, odtwarzaniu ruchu oraz zdarzeniach bezpieczeństwa. Komunikaty są mapowane z nazw logicznych systemu na pliki WAV przechowywane w katalogu audio/voice, a ich odtwarzanie realizuje moduł tarzanAudioPlayer.

## 27. Uwagi końcowe

Mapa projektu stanowi nadrzędne odniesienie dla wszystkich zmian i edycji kodu systemu TARZAN. Każda modyfikacja skryptów programu musi być wykonywana z zachowaniem pełnej zgodności z zasadami i strukturą opisanymi w tej mapie.

Podczas edycji kodu nie wolno upraszczać ani zmieniać jego struktury w sposób, który mógłby naruszyć logikę działania systemu lub pominąć istniejące elementy. W szczególności należy zachować spójność metod, klas oraz plików systemowych zgodnie z ich pierwotnym układem.

Jeżeli kod jest modyfikowany, należy zawsze odnosić się do wersji oryginalnej i zachować wszystkie istniejące elementy strukturalne, chyba że ich zmiana wynika bezpośrednio z logicznej potrzeby wynikającej z projektu. Niedopuszczalne jest skracanie lub usuwanie fragmentów kodu tylko dlatego, że nie są bezpośrednio objęte aktualną zmianą.

Przed wprowadzeniem zmian należy sprawdzić, jakie pliki, metody i klasy już istnieją w systemie i czy nie pełnią one funkcji powiązanych z innymi elementami programu. Każda zmiana musi być wykonana z pełną świadomością wpływu na całą architekturę systemu.

Nowe elementy kodu należy dodawać w sposób spójny z istniejącą logiką, stylem programowania i formatowaniem projektu. Nie należy ich wyróżniać ani opisywać w sposób odbiegający od reszty kodu – dokumentacja i komentarze powinny być jednolite dla całego systemu.

Zawsze należy korzystać z najbardziej aktualnej wersji Mapy Projektu, która stanowi podstawowe odniesienie dla struktury programu, protokołów oraz zasad działania systemu.

Zachowanie poprawności logiki programu, jego struktury oraz zgodności z Mapą Projektu jest nadrzędną zasadą przy wszystkich zmianach w kodzie.

#Assety graficzne (ikony osi)

## Lokalizacja

Ikony osi systemu TARZAN są przechowywane w katalogu:

```
img/axes/
```

## Zakres

Katalog zawiera:

- Ikony osi kamery:
  
  - oś pozioma kamery
  - oś pionowa kamery
  - oś pochyłu kamery
  - oś ostrości kamery

- Ikony osi ramienia:
  
  - oś pionowa ramienia
  - oś pozioma ramienia

- Ikona drona

## Format plików

Dostępne formaty:

- PNG (do UI aplikacji)
- ICO (do systemu / buildów aplikacji)

## Wersje

Każda ikona występuje w wariantach:

- active (aktywny stan)
- inactive (nieaktywny stan)

## Rozmiary

Dostępne rozdzielczości:

- 64 px
- 96 px
- 128 px
- 320 px

## Dostęp w kodzie

Dostęp do ikon realizowany jest przez:

```
core/tarzanAssets.py
```

Przykład:

```
axis_icon("oś pozioma kamery", 64, "active")
```

## Uwagi

- Nie używać bezpośrednich ścieżek w kodzie
- Zawsze korzystać z warstwy `tarzanAssets`
- Ikony są wspólne dla całego systemu (EHR, PLAY, przyszłe UI)
