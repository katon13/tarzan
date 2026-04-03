# TARZAN — PROJECT_CONTEXT.md

Ten plik jest krótkim kontekstem projektu, który pozwala natychmiast zrozumieć architekturę systemu TARZAN
bez czytania całej historii rozmów lub dokumentacji.

Pełny stan projektu znajduje się w:
docs/TARZAN_HANDOFF.md

Repozytorium projektu:
https://github.com/katon13/tarzan

------------------------------------------------------------

# 1. Czym jest TARZAN

TARZAN jest systemem sterowania ruchem ramienia kamery i osi optycznych.
Nie jest to system CNC.

Kluczowa różnica:

Ruch nie jest opisany przez pozycje.
Ruch jest opisany przez stany sygnałów sterujących w czasie.

System zapisuje:

STEP
DIR
ENABLE

dla każdej osi w każdej próbce czasu.

------------------------------------------------------------

# 2. Globalny czas systemu

Cały system pracuje w globalnej siatce czasu:

CZAS_PROBKOWANIA_MS = 10

czyli:

0 ms
10 ms
20 ms
30 ms
...

Każda ramka czasu zawiera stan wszystkich osi.

------------------------------------------------------------

# 3. Osie systemu TARZAN

System posiada 6 głównych osi:

oś pozioma kamery
oś pionowa kamery
oś pochyłu kamery
oś ostrości kamery

oś pionowa ramienia
oś pozioma ramienia

Nazewnictwo osi musi być zgodne z mapą projektu.

------------------------------------------------------------

# 4. Pipeline generacji ruchu

TAKE (JSON)
↓
krzywa ruchu
↓
analiza segmentów
↓
gęstość impulsów STEP
↓
generacja impulsów STEP
↓
timeline osi
↓
globalny timeline systemu
↓
protokół komunikacyjny

------------------------------------------------------------

# 5. Format choreografii ruchu

Choreografia jest zapisana jako pliki:

data/take/TAKE_XXX_vYY.json

np:

TAKE_001_v01.json

Plik zawiera:

metadata
timeline
axes
curve control points

------------------------------------------------------------

# 6. Wersjonowanie choreografii

Każda edycja krzywej tworzy nową wersję TAKE.

TAKE_001_v01
→ edycja
→ TAKE_001_v02

Mechanizm:

core/tarzanTakeVersioning.py

------------------------------------------------------------

# 7. Ghost Motion

System porównuje ruch oryginalny i edytowany.

Porównywane parametry:

pole pod krzywą
peak amplitudy
liczba przecięć z zerem

To pozwala ocenić czy edycja zmieniła drogę ruchu kamery.

------------------------------------------------------------

# 8. Generacja impulsów STEP

Krzywa ruchu jest przekształcana w:

gęstość impulsów STEP

następnie w:

czasy impulsów STEP

Moduły:

motion/tarzanSegmentAnalyzer.py
motion/tarzanStepGenerator.py

------------------------------------------------------------

# 9. Timeline osi

Każda oś posiada timeline:

STEP
DIR
ENABLE
STEP_COUNT

Timeline jest próbkowany co:

CZAS_PROBKOWANIA_MS

------------------------------------------------------------

# 10. Globalny timeline

Timeline wszystkich osi jest łączony w jeden globalny timeline systemu.

Moduł:

motion/tarzanTimeline.py

------------------------------------------------------------

# 11. Protokół ruchu

Globalny timeline jest eksportowany jako:

data/protokoly/TAKE_XXX_vYY_protocol.txt

Moduł eksportu:

core/tarzanProtokolRuchu.py

------------------------------------------------------------

# 12. Aktualny stan systemu

Obecnie działają:

✔ wczytywanie TAKE
✔ walidacja TAKE
✔ analiza segmentów
✔ generacja STEP
✔ timeline osi
✔ globalny timeline
✔ eksport protokołu
✔ edycja krzywej
✔ wersjonowanie TAKE
✔ ghost compare

------------------------------------------------------------

# 13. Aktualny problem matematyczny

Po edycji krzywej pole pod krzywą nie jest jeszcze idealnie zachowane.

Przykład:

Delta pola ≈ 2.8%

Docelowo:

≈ 0%

Plik wymagający poprawy:

motion/tarzanKrzyweRuchu.py

------------------------------------------------------------

# 14. Zasady projektu

Nie skracać istniejących plików.
Nie usuwać metod.
Nie upraszczać architektury.
Zachować strukturę projektu.

Nowe pliki dopisywać do mapy projektu.

------------------------------------------------------------

# 15. Jak zaczynać nową sesję pracy

Nową rozmowę należy rozpocząć:

Kontynuujemy projekt TARZAN.
Stan projektu:
docs/TARZAN_HANDOFF.md

Aktualny punkt pracy:
motion/tarzanKrzyweRuchu.py

Cel:
precyzyjna normalizacja krzywej ruchu.

------------------------------------------------------------

## Moduły edycji choreografii ruchu

### Cel warstwy edycji

Edytor choreografii ruchu w projekcie TARZAN służy do graficznej edycji przebiegów sygnałów w funkcji czasu.  
Nie jest to edytor pozycji docelowych osi w stylu CNC.  
Podstawą jest zapis typu:

- czas
- stan sygnałów logicznych
- dane czujników
- synchronizacja wielu ścieżek sygnałowych

Oznacza to, że użytkownik edytuje przebiegi linii sygnałów, a nie współrzędne pozycji docelowych.

---

## Rozdział odpowiedzialności modułów

### `core/tarzanProtokolRuchu.py`

Moduł odpowiedzialny za definicję protokołu ruchu w dziedzinie czasu.

Zakres odpowiedzialności:

- definicja struktury próbki czasu,
- definicja ramek timeline,
- zasady zapisu stanów sygnałów,
- zasady synchronizacji sygnałów i czujników,
- eksport i import danych choreografii w postaci zgodnej z protokołem.

Ten plik jest warstwą protokołu i nie powinien zawierać logiki GUI edytora.

---

### `core/tarzanChoreografiaModel.py`

Moduł odpowiedzialny za roboczy model danych choreografii ruchu.

Zakres odpowiedzialności:

- struktura całego projektu choreografii,
- definicja ścieżek sygnałowych,
- definicja segmentów czasu i impulsów,
- definicja warstw roboczych potrzebnych do edycji,
- transformacja danych roboczych do formatu protokołu ruchu.

Ten plik jest warstwą modelu edycyjnego i pośredniczy między GUI a `tarzanProtokolRuchu.py`.

---

### `app/tarzanEdytorChoreografii.py`

Moduł odpowiedzialny za warstwę aplikacyjną edytora choreografii ruchu.

Zakres odpowiedzialności:

- obsługa projektu choreografii,
- ładowanie i zapisywanie choreografii,
- polecenia użytkownika,
- integracja GUI z modelem choreografii,
- operacje typu nowy projekt, otwórz, zapisz, eksportuj.

Ten plik nie powinien zawierać niskopoziomowej definicji protokołu.

---

### `gui/tarzanEdytorChoreografiiWidget.py`

Moduł odpowiedzialny za graficzny edytor linii sygnałów.

Zakres odpowiedzialności:

- rysowanie osi czasu,
- rysowanie ścieżek sygnałowych,
- zaznaczanie zakresów czasu,
- edycja odcinków 0/1,
- wstawianie impulsów,
- zoom, przewijanie, siatka czasu, kursor czasu,
- warstwa podglądu przebiegów.

Ten plik nie powinien przejmować logiki protokołu ani zapisu końcowego.

---

### `core/tarzanChoreografiaPlayer.py`

Moduł odpowiedzialny za odczyt i interpretację choreografii ruchu.

Zakres odpowiedzialności:

- odczyt timeline,
- iteracja po próbkach czasu,
- generowanie bieżącego stanu sygnałów dla danej chwili,
- przygotowanie danych do późniejszego wykonania lub symulacji.

Na obecnym etapie moduł dotyczy warstwy logicznej i testowej, bez wejścia w płytki PoKeys.

---

## Zasada architektoniczna

Na obecnym etapie projektu obowiązuje rozdział:

1. protokół ruchu,
2. model choreografii,
3. edytor GUI,
4. silnik odczytu choreografii,
5. dopiero później integracja z hardware.

Do czasu zakończenia warstwy edytora i protokołu nie należy przenosić odpowiedzialności za wykonanie sprzętowe do modułów edycji.

---

## Zasada nazewnictwa i unikania dublowania plików

Aby nie dublować ról modułów, przyjmuje się następujące zasady:

- `tarzanProtokolRuchu.py` pozostaje wyłącznie modułem protokołu czasu i sygnałów,
- wszystkie nowe pliki związane z edycją choreografii muszą być najpierw dopisane do mapy projektu,
- nie tworzyć równoległych plików o tej samej roli pod inną nazwą,
- GUI edytora musi być oddzielone od warstwy modelu i protokołu,
- eksport do formatu końcowego musi przechodzić przez `tarzanProtokolRuchu.py`.

---

## Zasada edycji choreografii

Edytor choreografii ma pracować jak edytor przebiegów logicznych:

- oś pozioma: czas,
- wiersze: sygnały,
- użytkownik edytuje stany 0/1 w segmentach czasu,
- możliwe są impulsy, odcinki aktywności, przerwy i przesunięcia,
- wynik zapisu musi być zgodny z głównym założeniem TARZAN:
  zapis ruchu jako funkcji czasu.

---

## Status etapu

Aktualny etap prac:

- skupienie na protokole ruchu,
- skupienie na modelu choreografii,
- skupienie na graficznej edycji sygnałów,
- bez integracji wykonawczej z płytkami.

Dopiero po domknięciu tej warstwy można przechodzić dalej do integracji sprzętowej.
