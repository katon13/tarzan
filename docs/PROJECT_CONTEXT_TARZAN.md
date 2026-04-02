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

KONIEC DOKUMENTU
