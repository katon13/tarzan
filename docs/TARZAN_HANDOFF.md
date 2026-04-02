# TARZAN — HANDOFF / STAN PROJEKTU (EDYTOR CHOREOGRAFII RUCHU)

Ten dokument zawiera pełne podsumowanie stanu prac nad edytorem choreografii ruchu systemu TARZAN.
Jego celem jest umożliwienie natychmiastowego wznowienia pracy w nowej sesji lub w nowym wątku bez utraty wiedzy z dotychczasowego procesu projektowego.

Dokument nie skraca informacji — zbiera kluczowe zasady, architekturę, pipeline ruchu oraz aktualny stan implementacji.

------------------------------------------------------------

## 1. Główna idea systemu TARZAN

TARZAN jest systemem sterowania ruchem kamery i ramienia kamerowego, w którym ruch nie jest opisany przez pozycje docelowe (jak w systemach CNC), lecz przez zapis sygnałów sterujących w funkcji czasu.

Najważniejsza zasada projektu:

Ruch jest zapisywany jako timeline sygnałów:
STEP
DIR
ENABLE

w funkcji czasu.

System nie zapisuje pozycji osi.
System zapisuje stan sygnałów sterujących w każdej próbce czasu.

------------------------------------------------------------

## 2. Fundamentalna zasada czasowa systemu

Cały system odnosi się do globalnej stałej:

CZAS_PROBKOWANIA_MS = 10

Oznacza to że globalny timeline systemu ma strukturę:

0 ms
10 ms
20 ms
30 ms
...

Każda ramka czasu zawiera stan wszystkich osi.

------------------------------------------------------------

## 3. Architektura pipeline ruchu

Pełny pipeline generacji ruchu wygląda następująco:

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

## 4. Format choreografii — TAKE

Choreografia ruchu jest zapisana w plikach:

data/take/TAKE_XXX_vYY.json

Przykład:

TAKE_001_v01.json

Plik TAKE zawiera:

metadata
timeline
axes
curve control points

Krzywa opisuje profil ruchu osi.

------------------------------------------------------------

## 5. Edycja choreografii

System umożliwia:

1. wczytanie TAKE
2. modyfikację krzywej ruchu
3. zapis nowej wersji TAKE

Przykład pipeline:

TAKE_001_v01
↓
edycja krzywej
↓
TAKE_001_v02

Mechanizm wersjonowania realizuje:

core/tarzanTakeVersioning.py

------------------------------------------------------------

## 6. Ghost Motion (porównanie ruchu)

Dodano mechanizm porównania ruchu tzw. Ghost Compare.

Porównuje on:

krzywą oryginalną
krzywą po edycji

Analizowane są m.in.:

pole pod krzywą
peak amplitudy
liczba przecięć z zerem

Przykładowy wynik:

Pole oryginalne: 639.9242
Pole edytowane: 657.9136
Delta pola %: 2.81%

Ghost motion pozwala określić czy edycja zmieniła drogę ruchu kamery.

------------------------------------------------------------

## 7. Generacja impulsów STEP

Krzywa ruchu jest przekształcana w gęstość impulsów STEP.

Następnie generowane są konkretne czasy impulsów STEP.

Moduły:

motion/tarzanSegmentAnalyzer.py
motion/tarzanStepGenerator.py

------------------------------------------------------------

## 8. Timeline osi

Każda oś posiada własny timeline zawierający:

STEP
DIR
ENABLE
STEP_COUNT

Timeline jest próbkowany co:

CZAS_PROBKOWANIA_MS

------------------------------------------------------------

## 9. Globalny timeline systemu

Timeline wszystkich osi jest łączony w jeden globalny timeline systemu.

Przykład ramki:

t = 80 ms

camera_horizontal:
STEP_COUNT=1
STEP=1
DIR=1
ENABLE=1

Moduł:

motion/tarzanTimeline.py

------------------------------------------------------------

## 10. Protokół ruchu

Globalny timeline jest eksportowany jako:

data/protokoly/TAKE_XXX_vYY_protocol.txt

Przykład:

TAKE_001_v02_protocol.txt

Moduł eksportu:

core/tarzanProtokolRuchu.py

------------------------------------------------------------

## 11. Aktualny stan implementacji

Obecnie działają:

✔ wczytywanie TAKE  
✔ walidacja TAKE  
✔ analiza segmentów ruchu  
✔ generacja impulsów STEP  
✔ budowa timeline osi  
✔ budowa globalnego timeline  
✔ eksport protokołu ruchu  
✔ edycja krzywej ruchu  
✔ zapis nowej wersji TAKE  
✔ ghost compare ruchu  

------------------------------------------------------------

## 12. Aktualny pipeline działania

TAKE_001_v01.json
↓
edycja krzywej
↓
ghost compare
↓
TAKE_001_v02.json
↓
TAKE_001_v02_protocol.txt

System działa poprawnie.

------------------------------------------------------------

## 13. Aktualny problem matematyczny

Po edycji krzywej pole pod krzywą nie jest jeszcze idealnie zachowane.

Przykład:

Delta pola: 2.81%

Docelowo powinno być:

~0%

Do poprawy:

motion/tarzanKrzyweRuchu.py

Należy wprowadzić iteracyjną normalizację krzywej po edycji.

------------------------------------------------------------

## 14. Zasady projektowe

Podczas edycji kodu:

• nie skracać istniejących plików  
• nie usuwać metod  
• nie upraszczać architektury  
• zachowywać strukturę projektu  

Nowe pliki należy najpierw dopisać do mapy projektu.

------------------------------------------------------------

## 15. Zasady pracy

Podczas dalszego rozwoju:

• korzystać z istniejących modułów  
• korzystać z centralnych stałych  
• zachować strukturę katalogów  
• każdą zmianę zapisywać w Git  

------------------------------------------------------------

## 16. Repozytorium projektu

https://github.com/katon13/tarzan

Po każdym etapie pracy:

git add .  
git commit -m "opis etapu"  
git push  

------------------------------------------------------------

## 17. Następny krok rozwoju

Najbliższy etap:

poprawa matematyki edycji krzywej

należy wprowadzić:

iteracyjną normalizację pola pod krzywą

tak aby:

pole po edycji ≈ pole oryginalne

------------------------------------------------------------

## 18. Kolejne przyszłe etapy

• interaktywny edytor krzywej  
• operacje operatorskie na krzywej  
• ghost overlay ruchu  
• symulacja wielu osi  
• pełny protokół komunikacyjny  
• integracja z hardware  

------------------------------------------------------------

## 19. Punkt startowy do kolejnej sesji

Kontynuację należy rozpocząć od:

motion/tarzanKrzyweRuchu.py

Cel:

precyzyjna matematyczna normalizacja krzywej ruchu
po operacjach edycji

------------------------------------------------------------

KONIEC DOKUMENTU
