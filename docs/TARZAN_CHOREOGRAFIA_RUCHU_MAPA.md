# MAPA EDYTORA CHOREOGRAFII RUCHU TARZANA

## ZASADA NADRZĘDNA GENEROWANIA IMPULSÓW STEP W TARZANIE

To jest zasada absolutnie nadrzędna dla całego edytora choreografii ruchu, generatora impulsów oraz protokołu wykonawczego TARZANA.

## Kluczowa zasada

W systemie TARZAN **nie wystarczy**, że zgadza się całkowita liczba impulsów STEP oraz całkowita droga ruchu osi.

To jest warunek konieczny, ale **niewystarczający**.

Równie ważna jest **płynność czasowego rozkładu kolejnych impulsów STEP**.

Oznacza to, że:

- kolejne impulsy STEP muszą następować w sposób płynny,
- odstępy czasu pomiędzy kolejnymi impulsami muszą zmieniać się łagodnie,
- gęstość impulsów nie może zmieniać się skokowo ani nerwowo,
- lokalny rytm impulsów musi odpowiadać płynnej zmianie natężenia ruchu osi.

## Co to oznacza fizycznie

Jeżeli amplituda krzywej ruchu zmienia się płynnie, to silnik nie może otrzymywać impulsów w sposób nerwowy, przypadkowy lub skokowy.

Nie wolno dopuszczać sytuacji, w której przebieg STEP przy gładkiej krzywej daje sekwencje typu:

```text
000001010000101011110000
```

albo inne lokalnie poszarpane układy impulsów.

Taki przebieg może dawać poprawną sumaryczną liczbę kroków, ale fizycznie powoduje, że:

- silnik pracuje nerwowo,
- ruch osi staje się szarpany,
- pojawiają się mikrodrgania,
- przebieg ruchu przestaje być filmowy,
- oś zachowuje się nienaturalnie mimo poprawnej całki ruchu.

## Wniosek wykonawczy

Generator STEP w TARZANIE musi pilnować jednocześnie trzech rzeczy:

1. zgodności całkowitej liczby impulsów z drogą ruchu osi,
2. zgodności kierunku ruchu z przebiegiem krzywej,
3. płynności lokalnego rozkładu impulsów w czasie.

To oznacza, że poprawny generator STEP nie może być oceniany wyłącznie po:

- całkowitej liczbie impulsów,
- zgodności COUNT,
- zgodności pola pod krzywą.

Musi być oceniany także po tym, czy **kolejne impulsy tworzą czasowo płynny rytm ruchu osi**.

## Zasada interpretacyjna

Im płynniej zmienia się funkcja natężenia ruchu, tym płynniej musi zmieniać się rytm impulsów STEP.

Czyli:

- płynny wzrost amplitudy -> płynne zagęszczanie impulsów,
- płynny spadek amplitudy -> płynne rozrzedzanie impulsów,
- brak ruchu -> brak impulsów,
- zmiana kierunku -> płynne przejście zgodne z logiką mechaniczną osi.

Nie wolno dopuścić do sytuacji, w której przy gładkiej krzywej rytm impulsów zmienia się gwałtownie i lokalnie chaotycznie.

## Status tej zasady

Ta zasada jest **jedną z najważniejszych zasad całego projektu TARZAN**.

Należy ją traktować jako zasadę nadrzędną przy:

- projektowaniu generatora impulsów,
- walidacji przebiegu osi,
- budowie preview protokołu,
- ocenie jakości ruchu,
- dalszym rozwijaniu edytora choreografii ruchu.

## Formuła skrócona

W TARZANIE ma być zachowana nie tylko:

```text
poprawna liczba impulsów
```

ale również:

```text
poprawna płynność kolejnych impulsów
```

Bo tylko wtedy ruch osi będzie jednocześnie:

- matematycznie poprawny,
- mechanicznie poprawny,
- fizycznie płynny,
- filmowo naturalny. 

## Kluczowa zasada działania edytora

W edytorze choreografii ruchu **myszka nie steruje bezpośrednio krzywą**.

Myszka steruje **parametrem ruchu**, natomiast krzywa jest **wynikiem funkcji matematycznej oraz ograniczeń mechanicznych osi**.

Schemat działania:

MYSZ → PARAMETR → FUNKCJA RUCHU → KRZYWA

Jest to fundamentalna zasada działania edytora ruchu w projekcie TARZAN.

Operator nie ustawia ręcznie wartości krzywej.  
Operator modyfikuje parametry ruchu, a system generuje krzywą zgodnie z algorytmem ruchu i ograniczeniami mechanicznymi.

---

# Co faktycznie edytuje użytkownik

Użytkownik **nie edytuje amplitudy punktu krzywej bezpośrednio**.

Użytkownik edytuje **parametry ruchu**, takie jak:

- intensywność ruchu – jak szybko oś przyspiesza
- kształt ruchu – charakter krzywej przyspieszenia
- timing – moment rozpoczęcia fragmentu ruchu
- energia ruchu – powierzchnia pod krzywą
- rozkład dynamiki – gdzie w czasie ruch jest najsilniejszy

W praktyce oznacza to:

ruch myszy → zmiana parametru ruchu

a system:

parametr → przeliczenie funkcji ruchu → aktualizacja krzywej

---

# Model krzywej ruchu

Krzywa ruchu nie jest definiowana jedynie przez kilka punktów amplitudy.

Zamiast modelu:

3 punkty → spline

stosowany jest model segmentowy:

```
segment ruchu  
↓  
model matematyczny  
↓  
gęsta krzywa wynikowa
```

Segment ruchu składa się z:

```
start  
control A  
control B  
stop
```

co odpowiada krzywej typu **cubic Bézier**.

---

# Model krzywej Béziera

Każdy segment ruchu definiowany jest przez cztery punkty:

```
P0 – start  
P1 – uchwyt kontrolny  
P2 – uchwyt kontrolny  
P3 – stop
```

Model ten jest stosowany w profesjonalnych narzędziach takich jak:

- Corel
- After Effects
- Blender
- DaVinci Resolve
- Fusion

---

# Zalety modelu Béziera w edytorze TARZAN

Ten model zapewnia:

- lokalną kontrolę nad fragmentem krzywej
- stabilność podczas edycji
- brak gwałtownych skoków wykresu
- przewidywalność zachowania krzywej
- możliwość zachowania zależności pomiędzy amplitudą i czasem ruchu

---

# Zależność amplituda – czas – impulsy

Model krzywej musi zachować fundamentalną zasadę systemu TARZAN:

większa amplituda  
→ większa chwilowa prędkość ruchu  
→ mniejszy czas trwania ruchu  
→ wcześniejszy punkt STOP

mniejsza amplituda  
→ mniejsza chwilowa prędkość ruchu  
→ dłuższy czas trwania ruchu  
→ przesunięty punkt STOP

Jednocześnie **całkowita liczba impulsów STEP pozostaje stała**, ponieważ droga ruchu osi nie zmienia się.

---

# Ograniczenia mechaniczne

Każda edycja krzywej musi być kontrolowana przez ograniczenia mechaniczne osi.

System musi respektować między innymi:

- maksymalną prędkość osi
- maksymalne przyspieszenie
- minimalny czas cyklu
- kompensację luzów
- zakres mechaniczny osi

Każda zmiana parametrów krzywej przechodzi przez procedurę:

enforce_axis_constraints()

Dzięki temu edytor nigdy nie generuje ruchu niemożliwego do wykonania przez mechanikę systemu.

## 1. Cel modułu

Edytor choreografii ruchu TARZANA jest operatorskim narzędziem służącym do:

- nagrywania ruchu wszystkich osi systemu TARZAN,
- wizualizacji ruchu w czasie,
- intuicyjnej edycji dynamiki ruchu,
- wygładzania przebiegów ruchu,
- synchronizacji osi,
- wersjonowania TAKE,
- przygotowania ruchu do trybu tAA — All-Auto.

Edytor nie służy do technicznej edycji sygnałów STEP/DIR, lecz do filmowej korekty dynamiki ruchu osi w czasie.
System automatycznie przelicza edytowany przebieg na protokół sygnałów sterujących zgodny z architekturą TARZAN.

## 2. Filozofia działania

Podstawą działania systemu TARZAN jest czasowy model ruchu, a nie model pozycyjny.
Ruch nie jest traktowany jako polecenie:

> „jedź do pozycji X”

lecz jako:

> „ciąg zdarzeń ruchowych rozłożonych w czasie”.

Dlatego:

- ruch jest nagrywany jako przebieg sygnałów w czasie
- następnie budowana jest warstwa operatorska
- operator edytuje dynamikę ruchu
- system ponownie generuje sygnały sterujące

Edytor jest więc czymś w rodzaju montażowni ruchu kamerowego.

## 3. Zakres osi objętych edycją

Edytor obsługuje wszystkie osie systemu.
Osie kamery:

- oś pozioma kamery
- oś pionowa kamery
- oś pochyłu kamery
- oś ostrości kamery

Osie ramienia:

- oś pionowa ramienia
- oś pozioma ramienia

Zdarzenie drona:
Dron nie posiada krzywej natężenia.
W edytorze reprezentowany jest jako punkt zdarzeniowy na osobnej osi pomocniczej.
Punkt ten oznacza moment zwolnienia elektromagnesu drona.

## 4. Model wizualizacji ruchu

Ruch każdej osi przedstawiany jest jako krzywa natężenia ruchu względem czasu.
Interpretacja krzywej:
wartość dodatnia – ruch w jednym kierunku
wartość ujemna – ruch w przeciwnym kierunku
wartość zero – brak ruchu
Operator widzi więc:

- kierunek ruchu
- intensywność ruchu
- tempo przyspieszania
- tempo wyhamowania
- moment zatrzymania
- zmianę kierunku
- relacje pomiędzy osiami

## 5. Zasada ciągłości ruchu

Krzywa edycyjna każdej osi jest jednym ciągłym przebiegiem.
Edycja nie polega na składaniu ruchu z segmentów.
Operator deformuje istniejący przebieg ruchu:

- ściska go
- rozciąga
- wygładza
- przesuwa w czasie

Można to porównać do sprężystego węża impulsów,
który może się kurczyć i wydłużać,
ale pozostaje jednym ciągłym elementem.

## 6. Stałość drogi ruchu

Podstawowa zasada matematyczna edytora:
Edycja krzywej nie zmienia drogi ruchu osi,
zmienia tylko rozkład ruchu w czasie.
Oznacza to że:

- liczba impulsów pozostaje taka sama

- zmienia się jedynie ich tempo

- Operator edytuje więc:

- rytm ruchu

- dynamikę

- płynność

ale nie zmienia:

- geometrii ruchu osi.

## 6.1 Zespolenie krzywej ruchu z czasem trwania ruchu

Krzywa ruchu osi w edytorze TARZANA nie jest jedynie wizualnym wykresem natężenia ruchu.
Stanowi ona matematyczny model rozkładu ruchu w czasie.

Dlatego zmiana kształtu krzywej nie może być traktowana wyłącznie jako zmiana amplitudy.

Obowiązuje zasada pełnej proporcji matematycznej pomiędzy:

- kształtem krzywej
- czasem trwania ruchu
- drogą ruchu osi

Oznacza to że:

- zmiana intensywności krzywej powoduje proporcjonalną zmianę czasu trwania ruchu
- zmniejszenie natężenia ruchu powoduje wydłużenie czasu ruchu
- zwiększenie natężenia ruchu powoduje skrócenie czasu ruchu

System zachowuje jednocześnie stałość drogi ruchu osi, wynikającą z liczby impulsów STEP.

Można to zapisać w uproszczonej formie jako zależność:

droga ruchu = całka z natężenia ruchu w czasie

Dlatego podczas edycji:

- zmiana kształtu krzywej powoduje automatyczne przeliczenie czasu jej przebiegu
- liczba impulsów ruchu pozostaje niezmienna
- zmienia się jedynie tempo generowania impulsów

Dzięki temu operator edytuje:

- dynamikę ruchu
- rytm ruchu
- płynność ruchu

ale nie zmienia:

- geometrii ruchu
- zakresu mechanicznego osi
- liczby impulsów ruchu wynikających z nagranego TAKE.

## 6.2 Zespolenie początku i końca ruchu z krzywą

Początek i koniec ruchu osi nie są w systemie TARZAN niezależnymi parametrami.

Granice ruchu wynikają bezpośrednio z krzywej ruchu:

- początek ruchu = pierwszy punkt krzywej
- koniec ruchu = ostatni punkt krzywej

Edytor może wizualizować te granice jako pionowe linie pomocnicze,
jednak nie stanowią one oddzielnych danych.

Zmiana początku lub końca ruchu jest w rzeczywistości zmianą:

- pierwszego punktu krzywej
- ostatniego punktu krzywej

Dzięki temu zachowana jest spójność modelu matematycznego:

- krzywa pozostaje jednym ciągłym przebiegiem
- nie powstają dwa niezależne ruchy
- zachowana jest pełna zgodność z protokołem ruchu.## 

# 6.3  Wniosek projektowy

To musi być jednoznaczne:

1. krzywa ruchu nie jest ozdobą, tylko matematycznym modelem ruchu osi
2. amplituda oznacza chwilową intensywność / tempo ruchu
3. jeśli amplituda maleje, czas ruchu musi rosnąć
4. jeśli amplituda rośnie, czas ruchu może maleć
5. całkowita liczba impulsów dla tego ruchu pozostaje taka sama
6. generator sygnałów potem rozkłada te impulsy na timeline zgodnie z nową dynamiką. 

## 7. Dane wejściowe jednej osi

Każda oś w edytorze posiada dwa zestawy danych.

## 7.1 Dane z protokołu ruchu

Z nagrania TAKE pobierane są:

- czas próbki
- STEP
- DIR
- ENABLE

Z tych danych system rekonstruuje:

- ruch dodatni
- ruch ujemny
- pauzy
- zmianę kierunku

## 7.2 Dane mechaniczne osi

Każda oś posiada parametry wynikające z mechaniki systemu:

- liczba impulsów pełnego cyklu
- maksymalna prędkość impulsów
- maksymalne przyspieszenie
- minimalny czas pełnego cyklu
- profil rozruchu
- profil hamowania
- kompensacja luzów
- zakres ruchu osi
- rozdzielczość próbkowania protokołu

## 7.3 Segmenty ruchu osi

Na podstawie protokołu sygnałów system buduje logiczne segmenty ruchu.
Segment ruchu jest podstawową jednostką analizy i zawiera:

- czas początku segmentu
- czas końca segmentu
- kierunek ruchu
- liczbę impulsów STEP
- informację czy segment jest pauzą
- informację o zmianie kierunku

Segmenty pozwalają zamienić surowy protokół sygnałów na czytelny model ruchu osi.
Dzięki temu edytor nie pracuje bezpośrednio na impulsach, lecz na uproszczonym modelu ruchu.
Na podstawie segmentów tworzona jest następnie krzywa natężenia ruchu, która stanowi warstwę operatorską edytora.

## 8. Silnik matematyczny edytora ruchu TARZANA

Silnik matematyczny edytora jest odpowiedzialny za przekształcenie nagranego protokołu ruchu w edytowalną krzywą operatorską oraz za ponowne przeliczenie tej krzywej na sygnały sterujące systemu.
Silnik ten pełni rolę warstwy pośredniej pomiędzy nagranym ruchem rzeczywistym, edycją operatorską oraz generowaniem sygnałów sterujących. Nie generuje ruchu od zera. Jego zadaniem jest deformacja dynamiki istniejącego ruchu przy zachowaniu ograniczeń mechanicznych systemu.

## 8.1 Model matematyczny ruchu osi

Ruch jednej osi opisany jest funkcją M(t), gdzie t oznacza czas, a M(t) natężenie ruchu osi.

- $M(t) >$ 0 ruch w kierunku dodatnim.
- $M(t) < 0  $ ruch w kierunku przeciwnym.
- $M(t) = 0 $ brak ruchu.

Wartość bezwzględna funkcji określa intensywność ruchu osi, czyli chwilową prędkość ruchu.

## 8.2 Zasada zachowania drogi ruchu

Jedną z podstawowych zasad działania edytora jest zachowanie drogi ruchu osi. Oznacza to, że edycja krzywej nie zmienia liczby impulsów generowanych przez oś, lecz jedynie ich rozkład w czasie.
Matematycznie oznacza to, że całka z wartości bezwzględnej funkcji M(t) musi odpowiadać tej samej liczbie impulsów STEP co w oryginalnym nagraniu. Dzięki temu operator może zmieniać dynamikę ruchu, moment przyspieszenia, moment wyhamowania oraz płynność ruchu, ale nie zmienia rzeczywistej drogi ruchu osi.

## 8.3 Punkty kontrolne krzywej

Krzywa ruchu reprezentowana jest przez zestaw punktów kontrolnych. Każdy punkt kontrolny zawiera czas punktu, wartość natężenia ruchu oraz typ interpolacji do następnego punktu.
Między punktami stosowana jest interpolacja płynna, umożliwiająca tworzenie naturalnych przebiegów ruchu.
Operator może:

- przesuwać punkt w górę lub w dół

- przesuwać punkt w czasie

- usuwać punkt

- dodawać nowy punkt

- zmiana położenia punktu powoduje natychmiastową deformację lokalnego przebiegu funkcji M(t).

## 8.4 Edycja amplitudy krzywej

Podniesienie punktu kontrolnego powoduje zwiększenie chwilowej prędkości ruchu osi. Obniżenie punktu powoduje zmniejszenie chwilowej prędkości ruchu osi.
Ponieważ całkowita droga ruchu musi pozostać stała, silnik automatycznie przelicza czas trwania segmentu ruchu.

- większa amplituda krzywej -> krótszy czas ruchu,
- mniejsza amplituda krzywej -> dłuższy czas ruchu.

## 8.5 Edycja czasu

Przesunięcie punktu w osi czasu powoduje zmianę momentu przyspieszenia lub wyhamowania ruchu. Silnik przelicza wówczas lokalny rozkład prędkości tak, aby zachowana została całkowita droga ruchu.

## 8.6 Wygładzanie przebiegu

Nagrania ruchu wykonywane ręcznie mogą zawierać mikrodrgania, nierówne tempo oraz drobne szarpnięcia. Edytor umożliwia wygładzanie wybranego fragmentu krzywej.

- Algorytm wygładzania redukuje gwałtowne zmiany wartości funkcji,
- Zachowuje znak kierunku ruchu,
- Zachowuje całkowitą drogę ruchu,
- Zachowuje początek i koniec segmentu.

Celem wygładzania jest uzyskanie bardziej filmowej płynności ruchu.

## 8.7 Ograniczenia mechaniczne

Każda oś posiada zestaw ograniczeń wynikających z mechaniki systemu. Silnik matematyczny musi kontrolować:

- maksymalną prędkość osi,
- maksymalne przyspieszenie,
- minimalny czas pełnego cyklu,
- profil rozruchu osi,
- profil hamowania osi,
- kompensację luzów przekładni.

Edycja krzywej nie może generować ruchu przekraczającego te ograniczenia. W przypadku naruszenia ograniczeń edytor blokuje dalszą edycję lub automatycznie ogranicza amplitudę krzywej.

## 8.8 Zmiana kierunku ruchu

Zmiana kierunku ruchu osi występuje w momencie przejścia krzywej przez wartość zero. Silnik wykrywa taki moment i automatycznie:

- wprowadza kompensację luzów mechanicznych,
- wstawia impulsy kompensacyjne,
- zachowuje płynność przejścia przez zero.

Mechanizm ten jest całkowicie niewidoczny dla operatora.

## 8.9 Pauzy w ruchu

Jeżeli funkcja M(t) przyjmuje wartość zero przez pewien czas, oznacza to pauzę ruchu.

- W tym czasie nie generowane są impulsy STEP,
- Kierunek dir pozostaje w ostatnim stanie,
- Oś pozostaje nieruchoma.

Pauzy są naturalną częścią TAKE i mogą być dowolnie wydłużane lub skracane.

## 8.10 Generowanie sygnałów sterujących

Po zakończeniu edycji krzywej system przelicza przebieg ruchu na sygnały sterujące. Proces ten obejmuje:

- wyznaczenie chwilowej prędkości osi,
- wyznaczenie kierunku ruchu,
- generowanie impulsów STEP,
- ustawienie sygnału DIR,
- ustawienie sygnału ENABLE.

Wynikiem jest ponownie wygenerowany protokół ruchu TARZANA, zgodny z architekturą systemu.

## 8.11 Weryfikacja końcowa

Przed zapisaniem TAKE system wykonuje automatyczną kontrolę:

- czy liczba impulsów jest zgodna z drogą ruchu,
- czy nie przekroczono maksymalnej prędkości osi,
- czy nie przekroczono maksymalnego przyspieszenia,
- czy start i koniec TAKE mają wartość zero,
- czy zmiany kierunku są poprawne,
- czy zdarzenie drona zachowało swój czas.

Dopiero po pozytywnej weryfikacji nowa wersja TAKE może zostać zapisana.

## 9. Diagram architektury silnika edytora

Poniższy schemat pokazuje pełny przepływ danych przez edytor choreografii ruchu TARZANA.

```
PROTOKÓŁ RUCHU
       ↓
ANALIZATOR SYGNAŁÓW
       ↓
MODEL TAKE
       ↓
KRZYWE RUCHU
       ↓
EDYTOR OPERATORA
       ↓
WALIDATOR MECHANICZNY
       ↓
GENERATOR IMPULSÓW
       ↓
NOWY TAKE
```

## 9.1 Znaczenie diagramu

Przepływ rozpoczyna się od protokołu ruchu, czyli rzeczywistego zapisu sygnałów STEP, DIR i ENABLE w czasie. Następnie analizator sygnałów buduje logiczne odcinki ruchu, pauzy i zmiany kierunku.
Model TAKE przechowuje pełny zapis jednego ujęcia, a warstwa krzywych ruchu tworzy jego operatorską reprezentację w postaci ciągłych linii natężenia ruchu. Operator pracuje wyłącznie na tej warstwie.
Po zakończeniu edycji walidator mechaniczny sprawdza zgodność przebiegu z parametrami osi, a generator impulsów przelicza finalną krzywą z powrotem na sygnały wykonawcze. Wynik zapisywany jest jako nowa wersja TAKE.

## 10. Struktura modułów oprogramowania edytora

Aby zachować przejrzystość architektury systemu TARZAN, edytor choreografii ruchu powinien być podzielony na niezależne moduły programowe.
Podział ten oddziela:

- interfejs operatorski

- model danych TAKE

- logikę matematyczną ruchu

- walidację mechaniczną

- generowanie sygnałów sterujących

Dzięki temu system pozostaje czytelny i łatwy do rozwijania.

## 10.1 Główne moduły edytora

Zalecana struktura plików:

```
tarzanEdytorChoreografiiRuchu.py
tarzanTakeModel.py
tarzanKrzyweRuchu.py
tarzanSegmentAnalyzer.py
tarzanMechanicalValidator.py
tarzanGeneratorImpulsow.py
tarzanGhostMotion.py
tarzanMotionConfig.py
```

## 10.2 tarzanEdytorChoreografiiRuchu.py

Główny moduł interfejsu operatorskiego.
Odpowiada za:

- wyświetlanie osi czasu

- rysowanie krzywych ruchu

- obsługę punktów kontrolnych

- obsługę PLAY / STOP / EDIT

- sterowanie zoomem czasu

- obsługę ghost ruchu

- zapis nowych wersji TAKE

Moduł ten nie zawiera logiki matematycznej ruchu, a jedynie korzysta z innych modułów systemu.

## 10.3 tarzanTakeModel.py

Moduł przechowujący pełną strukturę danych jednego TAKE.
Zawiera:

- listę osi

- dane krzywych ruchu

- dane segmentów ruchu

- zdarzenia punktowe (np. dron)

- informacje o wersji TAKE

- metadane nagrania

Model TAKE jest centralnym obiektem danych edytora.

## 10.4 tarzanSegmentAnalyzer.py

Moduł analizujący surowy protokół ruchu.
Jego zadaniem jest:

- analiza sygnałów STEP / DIR

- wykrywanie ruchów dodatnich

- wykrywanie ruchów ujemnych

- wykrywanie pauz

- wykrywanie zmian kierunku

- budowanie segmentów ruchu

Segmenty te stanowią podstawę budowy krzywych ruchu.

## 10.5 tarzanKrzyweRuchu.py

Moduł odpowiedzialny za budowę i edycję krzywych ruchu.
Odpowiada za:

- tworzenie krzywych M(t)

- interpolację między punktami kontrolnymi

- deformację krzywej

- wygładzanie fragmentów ruchu

- normalizację drogi ruchu

- aktualizację segmentów

To jest rdzeń matematyczny edytora.

## 10.6 tarzanMechanicalValidator.py

Moduł kontrolujący zgodność ruchu z ograniczeniami mechanicznymi osi.
Sprawdza:

- maksymalną prędkość osi

- maksymalne przyspieszenie

- minimalny czas pełnego cyklu

- profil rozruchu

- profil hamowania

- kompensację luzów

- poprawność zmiany kierunku

Walidacja wykonywana jest po każdej większej zmianie krzywej.

## 10.7 tarzanGeneratorImpulsow.py

Moduł generujący finalny protokół ruchu TARZANA.
Odpowiada za:

- przeliczenie funkcji M(t) na impulsy STEP

- generowanie sygnału DIR

- generowanie sygnału ENABLE

- rekonstrukcję pełnego zapisu czasowego

Wynikiem działania modułu jest nowa wersja TAKE.

## 10.8 tarzanGhostMotion.py

Moduł obsługujący tryb ghost ruchu.
Przechowuje:
oryginalny przebieg ruchu
aktualnie edytowaną wersję
różnice pomiędzy nimi
Dzięki temu operator może porównywać zmiany ruchu w czasie rzeczywistym.

## 10.9 tarzanMotionConfig.py

Moduł konfiguracji ruchu.
Zawiera:

- parametry mechaniczne osi

- ograniczenia ruchu

- profile rozruchu i hamowania

- ustawienia algorytmów wygładzania

- parametry generowania impulsów

## 11. Architektura systemu TARZAN w kontekście edytora

Edytor choreografii ruchu jest jednym z kluczowych elementów systemu TARZAN, ale nie działa samodzielnie.
Stanowi on element większego ekosystemu sterowania ruchem.
Pełny przepływ danych w systemie wygląda następująco:

```
OPERATOR
   ↓
EDYTOR CHOREOGRAFII RUCHU
   ↓
MODEL TAKE
   ↓
SILNIK MATEMATYCZNY RUCHU
   ↓
WALIDATOR MECHANICZNY
   ↓
GENERATOR PROTOKOŁU
   ↓
TRYB tAA (All-Auto)
   ↓
PROTOKÓŁ CZASOWY TARZAN
   ↓
STEROWNIKI PoKeys
   ↓
STEROWNIKI SILNIKÓW
   ↓
OSIE RAMIENIA I KAMERY
```

## 11.1 Znaczenie architektury

Architektura ta rozdziela system na dwie główne warstwy:

#### warstwę operatorską

gdzie odbywa się:

- nagrywanie ruchu

- edycja choreografii

- przygotowanie TAKE

#### warstwę wykonawczą

gdzie odbywa się:

- generowanie sygnałów sterujących

- sterowanie osiami

- fizyczne wykonanie ruchu

Takie rozdzielenie pozwala rozwijać system niezależnie:

- interfejs operatorski może ewoluować

- mechanika osi może się zmieniać

- algorytmy ruchu mogą być ulepszane

bez naruszania całej architektury systemu.

## 12. Struktura danych TAKE

TAKE jest podstawową jednostką pracy systemu TARZAN.

Oznacza pojedynczy zapis ruchu wszystkich osi w czasie, który może być:

- nagrywany,

- analizowany,

- edytowany,

- wersjonowany,

- odtwarzany w trybie tAA.

TAKE zawiera kompletny opis ruchu osi oraz zdarzeń powiązanych z danym ujęciem.

## 12.1 Struktura logiczna TAKE

TAKE składa się z następujących elementów:

```
TAKE
 ├ metadata
 ├ osie
 │   ├ oś pozioma kamery
 │   ├ oś pionowa kamery
 │   ├ oś pochyłu kamery
 │   ├ oś ostrości kamery
 │   ├ oś pionowa ramienia
 │   └ oś pozioma ramienia
 │
 ├ segmenty ruchu
 ├ krzywe ruchu
 ├ zdarzenia
 │   └ dron
 │
 ├ parametry TAKE
 └ historia wersji
```

## 12.2 Metadane TAKE

Metadane zawierają informacje opisujące nagranie.

```
metadata
 ├ id_take
 ├ nazwa_take
 ├ data_utworzenia
 ├ autor
 ├ opis
 ├ czas_trwania
 └ wersja
```

Metadane umożliwiają identyfikację i organizację ujęć.

## 12.3 Struktura osi w TAKE

Każda oś przechowuje pełen zapis swojego ruchu.

```
axis
 ├ axis_id
 ├ axis_name
 ├ segments
 ├ editable_curve
 ├ mechanical_limits
 └ raw_signal_reference
```

## 12.4 Segmenty ruchu

Segmenty ruchu są logiczną interpretacją protokołu sygnałów.
Segment opisuje fragment ruchu o jednolitym charakterze.

```
segment
 ├ segment_id
 ├ start_time
 ├ end_time
 ├ direction
 ├ pulse_count
 ├ is_pause
 └ is_direction_change
```

Segment może oznaczać:

- ruch dodatni

- ruch ujemny

- pauzę

Segmenty są podstawą budowy krzywej ruchu.

## 12.5 Krzywe ruchu

Krzywa ruchu jest operatorską reprezentacją dynamiki ruchu osi.
Każda oś posiada jedną krzywą:

```
curve
 ├ control_points
 ├ interpolation_type
 ├ amplitude_limits
 └ normalization_reference
```

## 12.6 Punkty kontrolne

Krzywa składa się z punktów kontrolnych.

```
control_point
 ├ time
 ├ amplitude
 ├ interpolation
```

Zmiana położenia punktu powoduje lokalną deformację funkcji M(t).

## 12.7 Zdarzenia

Zdarzenia są dodatkowymi elementami synchronizacji.
W pierwszej wersji systemu występuje jedno zdarzenie:

```
event
 ├ event_type = drone_release
 └ event_time
```

Zdarzenie nie jest częścią krzywej ruchu.
Jest to punkt synchronizacji.

## 12.8 Parametry TAKE

Parametry TAKE opisują globalne właściwości ruchu.

```
take_parameters
 ├ take_start_time
 ├ take_end_time
 ├ take_duration
 ├ total_axes
 └ simulation_mode
```

## 12.9 Historia wersji

Każdy TAKE może mieć wiele wersji.
System nie nadpisuje wcześniejszych wersji.

```
versions
 ├ TAKE_01
 ├ TAKE_02
 ├ TAKE_03
 └ ...
```

Każda wersja przechowuje:

- własne krzywe ruchu

- własny protokół impulsów

- referencję do wersji poprzedniej

## 12.10 Relacja między TAKE a protokołem ruchu

TAKE nie jest bezpośrednim zapisem sygnałów STEP/DIR.
Jest modelem ruchu, który może być przeliczony na protokół sterujący.
Relacja wygląda następująco:

```
TAKE
   ↓
krzywe ruchu
   ↓
funkcja M(t)
   ↓
generator impulsów
   ↓
protokół STEP/DIR
```

## 12.11 Zasady poprawności TAKE

Każdy TAKE musi spełniać następujące warunki:

1. wszystkie osie zaczynają ruch od wartości zero

2. wszystkie osie kończą ruch na wartości zero

3. liczba impulsów odpowiada drodze ruchu

4. prędkość osi nie przekracza limitów mechanicznych

5. przyspieszenie nie przekracza limitów mechanicznych

6. zmiany kierunku uwzględniają kompensację luzów

7. zdarzenia pozostają w obrębie czasu TAKE

## 13. Model klas Python dla edytora

Poniższy model klas Python stanowi bezpośredni most pomiędzy dokumentacją edytora a implementacją kodu. Model ten nie opisuje jeszcze detali bibliotek GUI ani sposobu połączenia z hardware, lecz definiuje podstawowe obiekty, które powinny istnieć w architekturze edytora TARZANA.

## 13.1 TarzanTake

Klasa reprezentująca jeden pełny TAKE.
Powinna zawierać:

- metadata
- axes
- events
- take_parameters
- versions

## 13.2 TarzanAxisTake

Klasa reprezentująca jedną oś w ramach TAKE.
Powinna zawierać:

- axis_id
- axis_name
- segments
- editable_curve
- mechanical_limits
- raw_signal_reference

## 13.3 TarzanSegment

Klasa opisująca pojedynczy logiczny segment ruchu.
Powinna zawierać:

- segment_id
- start_time
- end_time
- direction
- pulse_count
- is_pause
- is_direction_change

## 13.4 TarzanCurve

Klasa opisująca operatorską krzywą ruchu osi.
Powinna zawierać:

- control_points
- interpolation_type
- amplitude_limits
- normalization_reference

## 13.5 TarzanControlPoint

Klasa reprezentująca punkt kontrolny krzywej.
Powinna zawierać:

- time
- amplitude
- interpolation

## 13.6 TarzanEvent

Klasa reprezentująca zdarzenie punktowe.
Powinna zawierać:

- event_type
- event_time

## 13.7 TarzanVersion

Klasa reprezentująca pojedynczą wersję TAKE.
Powinna zawierać:

- version_id
- created_at
- author
- curve_snapshot
- protocol_snapshot
- previous_version_reference

## 13.8 Zależności pomiędzy klasami

Najwyższym obiektem jest TarzanTake. Zawiera on listę obiektów TarzanAxisTake, listę zdarzeń TarzanEvent oraz metadane i historię wersji. Każda oś zawiera listę obiektów TarzanSegment oraz jedną krzywą TarzanCurve. Krzywa składa się z listy obiektów TarzanControlPoint. Każda zapisana wersja TAKE przechowywana jest jako obiekt TarzanVersion.

## 14. Format pliku TAKE TARZANA

Każdy TAKE powinien być zapisywany jako osobny plik projektu.
Zalecany format:

```
JSON
```

Przykładowa nazwa pliku:

```
TAKE_001_v01.json
TAKE_001_v02.json
TAKE_002_v01.json
```

Taki model zapewnia:

- prostą archiwizację,

- czytelne wersjonowanie,

- łatwe porównywanie wersji,

- prosty import i eksport.

## 14.1 Główna struktura pliku TAKE

Plik TAKE powinien zawierać następujące sekcje:

```
TAKE
├── metadata
├── timeline
├── axes
├── events
├── simulation
├── source
└── validation
```

## 14.2 Sekcja metadata

Sekcja opisująca tożsamość TAKE.

```
"metadata": {
  "take_id": "TAKE_001",
  "version": "v01",
  "title": "Ujęcie wejścia aktora",
  "author": "Jacek Joniec",
  "created_at": "2026-03-21T18:30:00",
  "edited_at": "2026-03-21T19:12:00",
  "description": "Pierwsza wersja ruchu kamery i ramienia",
  "notes": "Wersja surowa po nagraniu"
}
```

## 14.3 Sekcja timeline

Sekcja globalna dla całego TAKE.

```
"timeline": {
  "time_unit": "ms",
  "sample_step": 10,
  "take_start": 0,
  "take_end": 12840,
  "take_duration": 12840
}
```

Znaczenie:

```
time_unit — jednostka czasu
sample_step — rozdzielczość próbki
take_start — początek TAKE
take_end — koniec TAKE
take_duration — całkowity czas trwania
```

## 14.4 Sekcja axes

Najważniejsza część pliku.
Każda oś posiada własny blok.
Proponowane klucze osi:

- camera_horizontal

- camera_vertical

- camera_tilt

- camera_focus

- arm_vertical

- arm_horizontal

Przykład struktury jednej osi:

```
"camera_horizontal": {
  "axis_name": "oś pozioma kamery",
  "axis_enabled": true,
  "mechanics_ref": "tarzanCameraHorizontal",
  "full_cycle_pulses": 28800,
  "min_full_cycle_time_s": 4.0,
  "max_pulse_rate": 7200,
  "max_acceleration": 1800,
  "backlash_compensation": 24,
  "start_must_be_zero": true,
  "end_must_be_zero": true,

  "raw_signal": {
    "source_take": "REC_2026_03_21_01",
    "step_count_total": 8420
  },

  "segments": [],
  "curve": {},
  "generated_protocol": {}
}
```

## 14.5 Sekcja segments

Segmenty logiczne osi.
Przykład:

```
"segments": [
  {
    "segment_id": "SEG_001",
    "start_time": 0,
    "end_time": 1850,
    "direction": 1,
    "pulse_count": 1240,
    "is_pause": false,
    "is_direction_change": false
  },
  {
    "segment_id": "SEG_002",
    "start_time": 1850,
    "end_time": 2600,
    "direction": 0,
    "pulse_count": 0,
    "is_pause": true,
    "is_direction_change": false
  },
  {
    "segment_id": "SEG_003",
    "start_time": 2600,
    "end_time": 4180,
    "direction": -1,
    "pulse_count": 980,
    "is_pause": false,
    "is_direction_change": true
  }
]
```

Znaczenie:

- direction = 1 — kierunek dodatni

- direction = -1 — kierunek przeciwny

- direction = 0 — pauza 

## 14.6 Sekcja curve

To jest operatorska warstwa edycyjna.

```
"curve": {
  "curve_type": "motion_intensity",
  "interpolation": "spline",
  "preserve_distance": true,
  "ghost_enabled": true,
  "control_points": [
    { "time": 0, "amplitude": 0.0 },
    { "time": 420, "amplitude": 0.35 },
    { "time": 900, "amplitude": 0.72 },
    { "time": 1450, "amplitude": 0.20 },
    { "time": 1850, "amplitude": 0.0 },
    { "time": 2600, "amplitude": 0.0 },
    { "time": 3100, "amplitude": -0.25 },
    { "time": 3700, "amplitude": -0.66 },
    { "time": 4180, "amplitude": 0.0 }
  ]
}
```

Znaczenie:

- amplituda dodatnia = ruch w jedną stronę

- amplituda ujemna = ruch w drugą stronę

- zero = postój

- preserve_distance = true — droga pozostaje stała

## 14.7 Sekcja generated_protocol

To jest wynik syntezy po edycji.
Na początku może być pusta albo generowana dopiero po zapisie wersji.

```
"generated_protocol": {
  "step_samples": [],
  "dir_samples": [],
  "enable_samples": [],
  "step_count_total": 8420,
  "validated": true
}
```

W wersji oszczędnej lepiej nie trzymać tu pełnych próbek zawsze, tylko:

- generować je na potrzeby symulacji i eksportu,

- a w pliku przechowywać uproszczoną wersję.

Czyli docelowo lepiej:

```
"generated_protocol": {
  "export_file": "TAKE_001_v01_protocol.txt",
  "step_count_total": 8420,
  "validated": true
}
```

To będzie lżejsze.

## 14.8 Sekcja events

Na razie tylko dron.

```
"events": [
  {
    "event_id": "EV_001",
    "event_type": "drone_release",
    "event_time": 6240,
    "enabled": true,
    "note": "Zwolnienie elektromagnesu"
  }
]
```

## 14.9 Sekcja simulation

Ustawienia pomocnicze dla symulacji.

```
"simulation": {
  "playhead_start": 0,
  "playhead_last_position": 4120,
  "zoom_level": 1.5,
  "ghost_visible": true,
  "show_all_axes": true
}
```

To nie jest krytyczne dla ruchu, ale wygodne dla GUI.

## 14.10 Sekcja source

Powiązanie z materiałem źródłowym.

```
"source": {
  "record_mode": "tREC",
  "source_protocol_file": "REC_2026_03_21_01.txt",
  "source_notes": "Nagranie z próby 3"
}
```

## 14.11 Sekcja validation

Wynik ostatniej walidacji mechanicznej.

```
"validation": {
  "status": "ok",
  "checked_at": "2026-03-21T19:10:00",
  "max_speed_ok": true,
  "max_acceleration_ok": true,
  "start_zero_ok": true,
  "end_zero_ok": true,
  "direction_change_ok": true,
  "events_ok": true,
  "messages": []
}
```

Jeśli coś jest nie tak:

```
"messages": [
  "Przekroczona maksymalna prędkość osi arm_vertical w czasie 3420 ms"
]
```

## 14.12 Pełny przykład pliku TAKE

Poniżej skrócony przykład całości:

```
{
  "metadata": {
    "take_id": "TAKE_001",
    "version": "v01",
    "title": "Wejście aktora",
    "author": "Jacek Joniec",
    "created_at": "2026-03-21T18:30:00",
    "edited_at": "2026-03-21T19:12:00",
    "description": "Pierwsza wersja ruchu",
    "notes": "Wersja surowa"
  },
  "timeline": {
    "time_unit": "ms",
    "sample_step": 10,
    "take_start": 0,
    "take_end": 12840,
    "take_duration": 12840
  },
  "axes": {
    "camera_horizontal": {
      "axis_name": "oś pozioma kamery",
      "axis_enabled": true,
      "mechanics_ref": "tarzanCameraHorizontal",
      "full_cycle_pulses": 28800,
      "min_full_cycle_time_s": 4.0,
      "max_pulse_rate": 7200,
      "max_acceleration": 1800,
      "backlash_compensation": 24,
      "start_must_be_zero": true,
      "end_must_be_zero": true,
      "raw_signal": {
        "source_take": "REC_2026_03_21_01",
        "step_count_total": 8420
      },
      "segments": [
        {
          "segment_id": "SEG_001",
          "start_time": 0,
          "end_time": 1850,
          "direction": 1,
          "pulse_count": 1240,
          "is_pause": false,
          "is_direction_change": false
        }
      ],
      "curve": {
        "curve_type": "motion_intensity",
        "interpolation": "spline",
        "preserve_distance": true,
        "ghost_enabled": true,
        "control_points": [
          { "time": 0, "amplitude": 0.0 },
          { "time": 420, "amplitude": 0.35 },
          { "time": 900, "amplitude": 0.72 },
          { "time": 1450, "amplitude": 0.20 },
          { "time": 1850, "amplitude": 0.0 }
        ]
      },
      "generated_protocol": {
        "export_file": "TAKE_001_v01_protocol.txt",
        "step_count_total": 8420,
        "validated": true
      }
    }
  },
  "events": [
    {
      "event_id": "EV_001",
      "event_type": "drone_release",
      "event_time": 6240,
      "enabled": true,
      "note": "Zwolnienie elektromagnesu"
    }
  ],
  "simulation": {
    "playhead_start": 0,
    "playhead_last_position": 4120,
    "zoom_level": 1.5,
    "ghost_visible": true,
    "show_all_axes": true
  },
  "source": {
    "record_mode": "tREC",
    "source_protocol_file": "REC_2026_03_21_01.txt",
    "source_notes": "Nagranie z próby 3"
  },
  "validation": {
    "status": "ok",
    "checked_at": "2026-03-21T19:10:00",
    "max_speed_ok": true,
    "max_acceleration_ok": true,
    "start_zero_ok": true,
    "end_zero_ok": true,
    "direction_change_ok": true,
    "events_ok": true,
    "messages": []
  }
}
```

## 14.13 Najważniejsze zasady tego formatu

Ten format spełnia wszystko, co ustaliliśmy:

- jeden plik = jeden TAKE,

- wersje są osobnymi plikami,

- osie są rozdzielone,

- dron jest zdarzeniem punktowym,

- krzywa operatorska jest oddzielona od sygnałów wykonawczych,

- mechanika osi jest jawnie powiązana z TAKE,

- walidacja jest częścią pliku.

To jest bardzo dobry fundament.

## 15. Diagram przepływu danych całego silnika ruchu

Pełny przepływ danych w systemie TARZAN powinien być rozumiany jako ciąg logicznych etapów przejścia od nagrania ruchu do jego ponownego wykonania przez układ automatyczny.

```
REC (protokół czasu)
        ↓
TAKE (model ruchu)
        ↓
krzywe edytora
        ↓
silnik matematyczny
        ↓
generator impulsów
        ↓
tAA
        ↓
PoKeys / sterowanie osiami
```

## 15.1 Znaczenie poszczególnych etapów

REC (protokół czasu)
To warstwa źródłowa, w której zapisane są rzeczywiste sygnały STEP, DIR, ENABLE oraz inne stany systemu w kolejnych próbkach czasu.

#### TAKE (model ruchu)

To logiczna reprezentacja nagranego ujęcia. TAKE porządkuje dane osi, segmentów ruchu, krzywych oraz zdarzeń punktowych takich jak zwolnienie drona.

#### Krzywe edytora

To operatorska warstwa robocza. Operator nie pracuje na impulsach, lecz na ciągłych krzywych natężenia ruchu w czasie.

#### Silnik matematyczny

To warstwa deformacji przebiegu ruchu. Silnik zachowuje stałą drogę ruchu osi, przelicza czas, pilnuje limitów mechanicznych i przygotowuje finalny przebieg wykonawczy.

#### Generator impulsów

To warstwa syntezy sygnałów sterujących STEP, DIR i ENABLE na podstawie krzywych zatwierdzonych po edycji.

#### tAA

To tryb wykonawczy All-Auto, który wykorzystuje zatwierdzony TAKE jako źródło sterowania ruchem automatycznym.

#### PoKeys / sterowanie osiami

To warstwa sprzętowa wykonująca finalnie sygnały wygenerowane przez system i sterująca rzeczywistym ruchem osi ramienia i kamery.

## 15.2 Główna zasada architektoniczna

Najważniejszą zasadą całego przepływu jest rozdzielenie warstwy operatorskiej od warstwy wykonawczej.
Oznacza to, że:

- operator pracuje na modelu ruchu,

- edytor deformuje dynamikę ruchu,

- silnik matematyczny waliduje przebieg,

- generator zamienia wynik na impulsy,

- sprzęt wykonuje wyłącznie zatwierdzony ruch.

- Dzięki temu system TARZAN zachowuje jednocześnie:

- prostotę pracy operatora,

- zgodność z mechaniką osi,

- bezpieczeństwo wykonania,

- możliwość dalszego rozwoju systemu.

## 16. Model klas Python dla pliku TAKE TARZANA

Poniższy model klas Python stanowi bezpośrednie odwzorowanie formatu pliku TAKE TARZANA. Jego zadaniem jest uporządkowanie danych ruchu w strukturze gotowej do zapisu, odczytu, walidacji oraz dalszego wykorzystania przez edytor, symulator i tryb tAA.

## 16.1 Główne klasy systemu

```
TarzanTake
TarzanTakeMetadata
TarzanTimeline
TarzanAxisTake
TarzanSegment
TarzanCurve
TarzanControlPoint
TarzanEvent
TarzanSourceInfo
TarzanValidation
```

## 16.2 TarzanTake

Główna klasa reprezentująca jeden pełny TAKE.
Powinna zawierać:

```
metadata
timeline
axes
events
simulation
source
validation
```

Przykładowa logika klasy:

```
class TarzanTake:
    metadata: TarzanTakeMetadata
    timeline: TarzanTimeline
    axes: dict[str, TarzanAxisTake]
    events: list[TarzanEvent]
    source: TarzanSourceInfo
    validation: TarzanValidation
```

## 16.3 TarzanTakeMetadata

Klasa przechowująca metadane TAKE.

```
class TarzanTakeMetadata:
    take_id: str
    version: str
    title: str
    author: str
    created_at: str
    edited_at: str
    description: str
    notes: str
```

## 16.4 TarzanTimeline

Klasa opisująca globalną oś czasu TAKE.

```
class TarzanTimeline:
    time_unit: str
    sample_step: int
    take_start: int
    take_end: int
    take_duration: int
```

## 16.5 TarzanAxisTake

Klasa reprezentująca jedną oś w ramach TAKE.

```
class TarzanAxisTake:
    axis_name: str
    axis_enabled: bool
    mechanics_ref: str
    full_cycle_pulses: int
    min_full_cycle_time_s: float
    max_pulse_rate: int
    max_acceleration: int
    backlash_compensation: int
    start_must_be_zero: bool
    end_must_be_zero: bool
    raw_signal: dict
    segments: list[TarzanSegment]
    curve: TarzanCurve
    generated_protocol: dict
```

## 16.6 TarzanSegment

Klasa logicznego segmentu ruchu osi.

```
class TarzanSegment:
    segment_id: str
    start_time: int
    end_time: int
    direction: int
    pulse_count: int
    is_pause: bool
    is_direction_change: bool
```

## 16.7 TarzanCurve

Klasa operatorskiej krzywej ruchu.

```
class TarzanCurve:
    curve_type: str
    interpolation: str
    preserve_distance: bool
    ghost_enabled: bool
    control_points: list[TarzanControlPoint]
```

## 16.8 TarzanControlPoint

Klasa pojedynczego punktu kontrolnego krzywej.

```
class TarzanControlPoint:
    time: int
    amplitude: float
```

## 16.9 TarzanEvent

Klasa zdarzenia punktowego.

```
class TarzanEvent:
    event_id: str
    event_type: str
    event_time: int
    enabled: bool
    note: str
```

## 16.10 TarzanSourceInfo

Klasa opisująca źródło TAKE.

```
class TarzanSourceInfo:
    record_mode: str
    source_protocol_file: str
    source_notes: str
```

## 16.11 TarzanValidation

Klasa przechowująca wynik walidacji mechanicznej i logicznej.

```
class TarzanValidation:
    status: str
    checked_at: str
    max_speed_ok: bool
    max_acceleration_ok: bool
    start_zero_ok: bool
    end_zero_ok: bool
    direction_change_ok: bool
    events_ok: bool
    messages: list[str]
```

## 16.12 Główna zasada projektowa

Model klas ma być prosty, czytelny i bezpośrednio zgodny z plikiem TAKE. Dzięki temu jedna struktura może służyć jednocześnie do:

- zapisu pliku

- odczytu pliku

- pracy edytora

- symulacji ruchu

- walidacji mechanicznej

- przekazania danych do generatora impulsów.

## Wniosek projektowy

Edytor choreografii ruchu nie jest dodatkiem do systemu, lecz centralnym ogniwem pomiędzy nagraniem ruchu a jego automatycznym odtworzeniem. To właśnie ten moduł przekształca surowy zapis sygnałów w świadomie opracowane ujęcie filmowe gotowe do wykonania przez TARZAN.

# DODATEK: Zasady mechanicznego ograniczania krzywej

To są uwagi związane z pracą nad logiką układu. Dlatego znajduą się na końcu, wynkiły z pracy i założeń.

## Uwaga projektowa – logika maszyny musi być na wejściu

W edytorze choreografii ruchu TARZAN linia nie może być traktowana jak swobodny rysunek geometryczny.  
Linia jest wizualizacją ruchu wynikającego z protokołu sygnałów i ograniczeń mechaniki osi.

Dlatego kolejność działania musi być następująca:

```text
mechanika
→ protokół
→ dozwolony model ruchu
→ wizualizacja
```

a nie:

```text
mysz rysuje dowolny kształt
→ system próbuje go później naprawić
```

To oznacza, że logika maszyny musi być zastosowana **na wejściu**, jeszcze przed rysowaniem finalnej krzywej.

---

## Kluczowa zasada

Użytkownik nie może edytować krzywej w sposób całkowicie swobodny.  
Użytkownik wskazuje kierunek zmiany, ale edytor może przyjąć tylko taki ruch, który jest zgodny z:

- protokołem ruchu,
- sygnałami sterującymi,
- ograniczeniami mechanicznymi osi,
- centralnymi zmiennymi projektu,
- dokumentacją TARZAN.

Czyli:

```text
mysz wskazuje kierunek
→ mechanika ogranicza
→ powstaje dozwolony ruch
→ rysowany jest wynik
```

---

## Konsekwencje dla edytora

Jeżeli ograniczenia zostaną wprowadzone na początku, wykres nie będzie mógł wykonywać chaotycznych skoków.

W szczególności edytor nie może dopuszczać:

- pionowych ścian krzywej,
- natychmiastowego startu z wysoką wartością,
- nielogicznych skoków przy przejściu pod osią,
- swobodnego „dodawania lub odejmowania pięter w budynku”, czyli lokalnych zmian sprzecznych z mechaniką.

Takie kształty są niezgodne z rzeczywistą pracą maszyny i nie mogą być akceptowane nawet chwilowo w preview operatorskim.

---

## Ograniczenia, które muszą być stosowane przed rysowaniem krzywej

### 1. Minimalny czas między węzłami

Węzły nie mogą być ustawiane tak gęsto, aby tworzyły pionowe uskoki.  
Muszą respektować krok czasu projektu:

```text
CZAS_PROBKOWANIA_MS = 10
```

oraz dodatkowe minimalne odstępy wynikające z modelu mechaniki.

### 2. Maksymalne lokalne nachylenie krzywej

Zmiana wartości w czasie musi mieć limit wynikający z dopuszczalnej dynamiki osi.

Czyli:

```text
d(wartość)/dt ≤ limit mechaniki osi
```

### 3. Wymuszona rampa startowa

Maszyna nie może wystartować pionowo.  
Początek ruchu musi być zrealizowany jako dozwolone narastanie.

### 4. Wymuszona rampa końcowa

Zatrzymanie ruchu także nie może być pionowym załamaniem.  
Końcowy odcinek musi być zgodny z dopuszczalnym wygaszaniem ruchu.

### 5. Ograniczenie lokalne względem sąsiadów

Przesunięcie jednego węzła nie może tworzyć lokalnego kształtu sprzecznego z sąsiednimi fragmentami przebiegu.

### 6. Ograniczenie przejścia przez zero

Przejścia przez oś i praca pod osią muszą być zgodne z realnym zachowaniem mechaniki i protokołu.  
Edytor nie może dopuszczać nienaturalnych skoków tylko dlatego, że są matematycznie możliwe.

### 7. Zależność amplituda ↔ czas

Zmiana wysokości przebiegu musi pozostać sprzężona z czasem trwania ruchu.  
Jeżeli zmienia się intensywność ruchu, system musi przeliczać skutek czasowy zgodnie z ustaloną logiką projektu.

---

## Wniosek projektowy

Edytor nie może działać jak narzędzie do swobodnego rysowania krzywej.  
Musi działać jak narzędzie do modelowania ruchu wynikającego z mechaniki maszyny.

Krzywa ma być:

- płynna dla operatora,
- czytelna wizualnie,
- ale zawsze zespolona z mechaniką, zmiennymi projektu i dokumentacją TARZAN.

To jest zasada obowiązująca przy dalszym rozwijaniu modułu choreografii ruchu.

# Dodatki z pracy, logika generowania impulsów STEP

## Zasada sterowania prędkością osi

W systemie TARZAN sterowanie prędkością silnika krokowego **nie polega na stałym rytmie sygnału STEP**. 
Próbkowanie protokołu odbywa się w stałym kroku czasu:

CZAS_PROBKOWANIA_MS = 10 ms

Każda próbka reprezentuje okno czasu, w którym **może wystąpić lub nie wystąpić zmiana stanu sygnału STEP**.

Silnik krokowy wykonuje krok tylko w momencie **zmiany stanu sygnału STEP (0 → 1 lub 1 → 0)**. 
Dlatego prędkość osi wynika z **gęstości impulsów w czasie**, a nie z samego faktu generowania sygnału.

## Błędny model (nie stosować)

Stały rytm przełączeń:

0 1 0 1 0 1 0 1

oznacza zawsze tę samą częstotliwość kroków i w efekcie **stałą prędkość silnika**. 
W takim modelu krzywa choreografii nie wpływa na prędkość ruchu osi.

## Poprawny model TARZAN

Krzywa ruchu określa **gęstość impulsów STEP w czasie**.

Przykłady:

Szybki ruch (duża gęstość impulsów):
0 1 0 1 0 1 0 1

Wolniejszy ruch:
1 0 0 0 1 0 0 0 1

Bardzo wolny ruch:
0 0 0 0 1 0 0 0 0

Zmienne tempo ruchu:
0 0 0 1 0 1 1 0 0 0 1 1 1

Im **większa amplituda krzywej ruchu**, tym **więcej impulsów STEP w jednostce czasu**.

## Wniosek dla edytora choreografii

Edytor nie generuje stałego sygnału STEP. Zamiast tego:

1. krzywa ruchu definiuje intensywność ruchu,
2. intensywność przeliczana jest na liczbę kroków w czasie,
3. kroki są rozkładane w próbkach 10 ms,
4. zmiana kierunku realizowana jest przez sygnał DIR:
   - DIR = 1 → ruch w prawo
   - DIR = 0 → ruch w lewo

Oznacza to, że **odstępy czasowe pomiędzy impulsami STEP muszą być zmienne**, 
ponieważ to one definiują rzeczywistą prędkość obrotu silnika.

# Wnioski implementacyjne z pracy nad EHR (Edytor Choreografii Ruchu) wynikające z procesu pracy

Dokument zbiera wnioski wynikające z analizy implementacji generatora STEP, działania edytora oraz modelu matematycznego TARZANA. 
Celem jest doprecyzowanie zasad architektury systemu, aby uniknąć rozbieżności pomiędzy dokumentacją a implementacją.

---

# 1. Fundamentalna zasada czasu systemowego

W całym systemie TARZAN obowiązuje jedna globalna jednostka czasu:

CZAS_PROBKOWANIA_MS = 10

Jednostka ta jest wspólnym mianownikiem dla:

- elektroniki sterującej
- mechaniki układu
- generatora STEP
- symulacji
- protokołu ruchu
- edytora choreografii
- preview i playera

Nie wolno wprowadzać lokalnych kroków czasu w poszczególnych modułach.

Każdy moduł musi korzystać z tej wartości z centralnego pliku:

core/tarzanUstawienia.py

Model czasu:

t_n = n * Δt
Δt = 10 ms

---

# 2. Model matematyczny generatora STEP

Dokumentacja definiuje model ruchu osi jako funkcję czasu.

A(t) – natężenie ruchu osi

Gęstość impulsów:

ρ(t) = k * |A(t)|

Liczba impulsów:

N = ∫ ρ(t) dt

Generator STEP działa jako akumulator:

accumulator += ρ(t) * dt

jeśli accumulator ≥ 1:
 emit STEP
 accumulator -= 1

Kierunek:

DIR = sign(A(t))

---

# 3. Pipeline generowania ruchu

Poprawny przepływ danych:

punkty kontrolne
↓
interpolacja spline
↓
funkcja ruchu A(t)
↓
gęstość impulsów ρ(t)
↓
integracja
↓
STEP / DIR
↓
generated_protocol

Generator STEP musi być jedynym źródłem prawdy dla protokołu ruchu.

---

# 4. Błąd architektury wykryty podczas implementacji

W aktualnej implementacji występuje konflikt pomiędzy:

- danymi TAKE
- parametrami mechaniki (full_cycle_pulses)
- lokalnymi obliczeniami preview
- krzywą edytora

Powoduje to sytuację, w której:

edytor osi
↓
preview
↓
generator STEP

zamiast:

edytor osi
↓
generator STEP
↓
preview

Generator STEP musi być centralnym elementem pipeline.

---

# 5. Budżet impulsów osi

Budżet impulsów TAKE nie może być liczony z parametrów mechanicznych.

Prawidłowa kolejność źródeł:

1. generated_protocol.step_count_total
2. suma segments[].pulse_count
3. raw_signal.step_count_total

Parametr full_cycle_pulses wolno używać tylko do walidacji ograniczeń mechanicznych.

---

# 6. Generator musi działać na całym TAKE

Choreografia ruchu jest globalna.

Generator STEP musi znać wszystkie osie.

TAKE
├─ axis_1
├─ axis_2
├─ axis_3
└─ ...

Generator działa w pętli czasu:

dla każdej próbki czasu:
 dla każdej osi:
 aktualizuj akumulator
 generuj STEP

Nie wolno generować STEP dla jednej osi w izolacji.

---

# 7. Rozdzielenie funkcji EHR

Edytor Choreografii Ruchu (EHR) pełni kilka funkcji systemowych.
Aby uniknąć konfliktów architektury należy wprowadzić jawne tryby pracy.

Proponowane tryby systemu:

GENERATOR
EDYTOR
PLAYER
RECORDER
LIVE

Tryby te powinny być reprezentowane przez duże przyciski w interfejsie.

---

# 8. Tryb GENERATOR

W trybie GENERATOR:

- wszystkie osie są generowane syntetycznie
- STEP powstaje bezpośrednio z krzywych
- wynik zapisywany jest jako protokół TAKE

Pipeline:

krzywe
↓
generator STEP
↓
protokół
↓
zapis TAKE

W tym trybie nie występuje konflikt między edycją a rekonstrukcją sygnału.

---

# 9. Tryb EDYTOR

W trybie EDYTOR:

START:
protokół STEP

↓

analiza segmentów

↓

rekonstrukcja krzywej ruchu

↓

edycja parametrów

↓

nowy generator STEP

Pipeline:

STEP → analiza → krzywa → STEP

---

# 10. Tryb PLAYER

PLAYER odpowiada wyłącznie za odtwarzanie TAKE.
Nie wykonuje żadnej syntezy STEP.

---

# 11. Tryb RECORDER

RECORDER zapisuje rzeczywisty ruch osi do protokołu STEP.

Pipeline:

sprzęt → STEP → zapis TAKE

---

# 12. Tryb LIVE

LIVE umożliwia bezpośrednie sterowanie układem bez zapisu TAKE.

---

# 13. Struktura danych osi

Każda oś powinna być reprezentowana przez jeden obiekt logiczny:

AxisTakeState

axis_key
raw_protocol
segments
editable_curve
mechanics_limits
generated_protocol
validation

UI nigdy nie powinno korzystać bezpośrednio z:

raw_signal
segments
mechanics

Tylko z obiektu AxisTakeState.

---

# 14. Ograniczenia mechaniczne osi

Ograniczenia mechaniczne nie mogą być traktowane symetrycznie.

Oś może mieć różne warunki ruchu dla:

- kierunku dodatniego
- kierunku ujemnego

Dlatego ograniczenia powinny być przypisane osobno dla:

- kierunku

- kierunku

W interfejsie należy je prezentować jako:

limity nad osią
lub
limity pod osią

---

# 15. Wnioski końcowe

Dokumentacja matematyczna TARZANA jest spójna.

Główne problemy implementacyjne wynikają z:

- braku jednego źródła prawdy dla STEP
- mieszania danych mechanicznych z danymi choreografii
- braku jawnych trybów pracy EHR
- lokalnych obliczeń preview

Po wprowadzeniu:

- centralnego generatora STEP
- globalnego czasu 10 ms
- jawnych trybów EHR
- jednego obiektu AxisTakeState

system powinien odzyskać spójność architektury.

# WNIOSKI KOŃCOWE WYNIKAJĄCE Z PRACY: Zasada generowania impulsów STEP w systemie TARZAN (EHR)

## Interpretacja krzywej ruchu

W edytorze choreografii ruchu TARZANA krzywa nie oznacza pozycji osi ani bezpośrednio prędkości fizycznej.
Krzywa oznacza **gęstość impulsów STEP w czasie**.

Interpretacja:

- wyższa krzywa → większa gęstość impulsów STEP → szybszy ruch osi
- niższa krzywa → mniejsza gęstość impulsów STEP → wolniejszy ruch osi
- krzywa równa 0 → brak impulsów STEP → brak ruchu

Przykładowe przebiegi:

01 → jeden krok silnika  
0101 → dwa kroki silnika w krótkim czasie  
000010000 → jeden krok, ale rozciągnięty w czasie (wolny ruch)

## Powiązanie z mechaniką osi

Każda oś posiada parametry mechaniczne określone w module mechaniki:

- `max_speed_axis` – maksymalna liczba impulsów STEP na sekundę
- `max_steps_axis` – maksymalna liczba kroków wynikająca z zakresu ruchu osi

Parametry te wynikają z:

- przełożenia mechanicznego
- ustawienia mikrokroku sterownika
- dopuszczalnej prędkości pracy mechaniki

## Ograniczenie krzywej

Krzywa w edytorze **zawsze jest automatycznie ograniczana przez mechanikę osi**.

Oznacza to:

curve_amplitude → skalowanie do `max_speed_axis`

Jeżeli amplituda krzywej przekracza dopuszczalną prędkość osi, generator STEP automatycznie przycina ją do wartości:

`max_speed_axis`

Dzięki temu:

- oś nigdy nie przekroczy bezpiecznej prędkości
- ruch pozostaje zgodny z możliwościami mechaniki
- krzywa w edytorze może być rysowana swobodnie, ale wykonanie zawsze pozostaje ograniczone fizycznie

## Generator STEP

Generator STEP przelicza krzywą na sygnał binarny STEP/DIR.

Dla każdego kroku czasu (np. 10 ms):

1. obliczana jest gęstość impulsów z krzywej
2. gęstość jest ograniczana do `max_speed_axis`
3. akumulator impulsów generuje sygnał STEP

Kierunek ruchu określany jest znakiem krzywej:

- krzywa dodatnia → DIR = +1
- krzywa ujemna → DIR = −1

## Zasada bezpieczeństwa

Mechanika osi jest zawsze nadrzędna wobec krzywej choreografii.

Krzywa definiuje **profil ruchu**, ale:

- prędkość jest ograniczana przez `max_speed_axis`
- zakres ruchu przez `max_steps_axis`

Dzięki temu system TARZAN może generować płynne choreografie ruchu przy jednoczesnym zachowaniu bezpieczeństwa mechaniki.
