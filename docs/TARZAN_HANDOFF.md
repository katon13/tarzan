# TARZAN_HANDOFF.md

## Cel tego handoffu

Ten dokument ma pozwolić rozpocząć nowy, czysty wątek pracy nad EHR bez gubienia ustaleń z obecnej rozmowy.

To nie jest krótkie streszczenie.
To jest pełny zapis diagnozy problemu, ustalonych zasad, błędów implementacyjnych, poprawnych założeń architektury oraz stanu faktycznego, który trzeba przyjąć jako punkt startowy kolejnej próby.

---

# 1. Status ogólny

Praca nad EHR (Edytor Choreografii Ruchu) trwała długo, ale nie doprowadziła jeszcze do skutecznej implementacji generatora STEP.

Powód nie jest koncepcyjny.
Powód nie jest dokumentacyjny.
Powód nie jest po stronie użytkownika.

## Prawdziwy powód

Problem jest implementacyjny i dotyczy tego, że:
- edytor,
- preview,
- generator STEP,
- walidacja mechaniki

nie pracują jeszcze na jednym spójnym modelu danych i jednym źródle prawdy dla protokołu STEP.

Wiele prób naprawy było:
- kosmetycznych,
- warstwowych,
- wykonywanych w preview,
- lub opartych o złe założenia na temat logiki STEP.

To doprowadziło do sytuacji, w której:
- UI zaczęło działać lepiej,
- linie zaczęły wyglądać lepiej,
- generator zaczął coś liczyć,
- ale końcowy protokół nadal nie odpowiada dokumentacji TARZANA.

---

# 2. Najważniejsze ustalenie całego wątku

## Kluczowa rzecz, którą trzeba zapamiętać

W EHR krzywa ruchu nie oznacza pozycji osi.

Krzywa nie oznacza też klasycznej prędkości w sensie CNC.

Krzywa oznacza:

**gęstość impulsów STEP w czasie**

czyli:
- wyższa krzywa -> więcej impulsów STEP w krótkim czasie -> szybszy ruch osi
- niższa krzywa -> mniej impulsów STEP w krótkim czasie -> wolniejszy ruch osi
- krzywa równa 0 -> brak impulsów STEP -> brak ruchu

Przykłady logiczne, które użytkownik wielokrotnie tłumaczył:
- `01` -> jeden krok osi
- `0101` -> dwa kroki osi
- `000010000` -> jeden krok osi, ale bardzo rozciągnięty w czasie

To jest fundament zrozumienia TARZANA.

Jeżeli implementacja tego nie rozumie, będzie stale produkować błędne wyniki.

---

# 3. Protokół 10 ms jest święty

To jest twarda zasada systemu.

## Obowiązuje bez wyjątków:

`CZAS_PROBKOWANIA_MS = 10`

Ta jednostka łączy:
- elektronikę,
- mechanikę,
- generator STEP,
- timeline TAKE,
- preview,
- player,
- recorder,
- walidację.

Nie wolno:
- wprowadzać lokalnych kroków czasu,
- interpolować preview w innym czasie,
- generować STEP w innym dt,
- traktować 10 ms jako opcjonalnego parametru.

Wszystko musi pracować dokładnie w siatce:
- 0 ms
- 10 ms
- 20 ms
- 30 ms
- ...

---

# 4. Mechanika jest nadrzędna

## Użytkownik doprecyzował to wielokrotnie

Silnik nie może obracać się za szybko, bo:
- mechanika może się uszkodzić,
- układ może stracić kontrolę,
- ramię może stanowić zagrożenie dla człowieka.

Czyli generator STEP musi zawsze respektować:
### a) limit prędkości osi
maksymalna ilość impulsów, jaką dana oś może przyjąć w danym przedziale czasu

### b) limit zakresu osi
maksymalna liczba impulsów wynikająca z mechaniki pełnego ruchu osi

## Najprostsza definicja użytkownika

`max_speed_axis` = maksymalna liczba impulsów STEP, którą dana oś może przyjąć w danym przedziale czasowym.

Czyli generator nie może po prostu „produkować impulsów zgodnie z krzywą”, tylko musi:
- najpierw policzyć teoretyczną gęstość impulsów z krzywej,
- potem przyciąć ją do mechaniki osi,
- dopiero potem budować protokół STEP.

---

# 5. Dane mechaniczne osi – twarde wartości odniesienia

Z pliku `tarzanMechanikaOsi.py` wynikają pełne pojemności osi:
- oś pozioma kamery: **28800**
- oś pionowa kamery: **12800**
- oś pochyłu kamery: **3200**
- oś ostrości kamery: **30764**
- oś pionowa ramienia: **28485**
- oś pozioma ramienia: **92273**

To są wartości konstrukcyjne, nie kosmetyczne.

Muszą być wykorzystywane przez:
- generator,
- walidację,
- preview,
- stan początkowy osi,
- logikę ograniczania krzywych.

---

# 6. Zasada nadrzędna smooth STEP

W TARZANIE nie wystarczy, że zgadza się:
- całkowita liczba impulsów,
- całkowita droga ruchu,
- końcowy COUNT.

Równie ważne jest:

**czy rytm kolejnych impulsów STEP zmienia się płynnie w czasie**.

Nie wolno dopuszczać przebiegów typu:

`000001010000101011110000`

jeżeli krzywa ruchu jest gładka.

Takie przebiegi:
- dają poprawny wynik liczbowy,
- ale są mechanicznie złe,
- powodują szarpanie,
- niszczą filmową płynność ruchu.

## Generator STEP musi spełniać 3 warunki jednocześnie

1. poprawna liczba impulsów
2. poprawny kierunek
3. płynny lokalny rozkład impulsów w czasie

Jeżeli którykolwiek z tych trzech punktów nie jest spełniony, generator jest błędny.

---

# 7. Najważniejszy błąd popełniany w implementacji

## Błąd rozumienia sygnału STEP

W rozmowie wielokrotnie wychodziło, że implementacja traktowała STEP jako:
- stan próbki,
- znacznik „w tej próbce był ruch”,
- albo długi blok jedynek.

To jest błędne.

### Problem

Były generowane przebiegi, gdzie:
- COUNT rósł szybko,
- EV pokazywało impulsy w próbce,
- ale STEP pozostawał długo w stanie 1,
- albo po zakończeniu ruchu dalej utrzymywał się jako 1 przy `AMP = 0`.

To jest jednoznacznie niezgodne z logiką ustaloną przez użytkownika.

### Poprawna zasada

STEP musi odpowiadać logicznemu przebiegowi impulsów,
a nie pomocniczemu stanowi wewnętrznemu generatora.

Czyli:
- jeśli nie ma ruchu,
- jeśli `AMP = 0`,
- jeśli `EV = 0`,

to:
- STEP nie może pozostawać sztucznie w stanie 1.

---

# 8. Co zostało pomylone w generatorze

Obecne / wcześniejsze próby mieszały trzy różne warstwy:

1. teoretyczna liczba impulsów należnych w oknie 10 ms
2. licznik zbiorczy COUNT
3. rzeczywisty sygnał STEP

To są trzy różne rzeczy.

## Wniosek

Generator musi osobno utrzymywać:
### a) `EV`
liczbę impulsów przypadających na próbkę 10 ms

### b) `COUNT`
sumaryczną liczbę impulsów od początku TAKE

### c) `STEP`
rzeczywisty logiczny przebieg sterujący

I dopiero wtedy preview będzie miało sens.

---

# 9. Problem preview

Preview nie może być osobnym generatorem.

To był jeden z najważniejszych błędów architektury.

Były próby, w których:
- edytor zmieniał krzywą,
- preview budowało coś „po swojemu”,
- generator liczył jeszcze coś innego.

To musi zostać usunięte.

## Poprawna architektura

`edytor osi -> centralny generator STEP -> generated_protocol -> preview`

Nie:

`edytor osi -> preview -> generator`

Preview ma tylko pokazywać wynik generatora.

Nie może mieć:
- fallbacków,
- lokalnych obliczeń,
- pseudo-protokołu,
- zastępczego przeliczania.

---

# 10. Problem pełnego timeline TAKE

To była bardzo ważna uwaga użytkownika.

## Co musi być widoczne

W preview protokołu użytkownik musi widzieć:
- pełny timeline TAKE
- pełną długość osi czasu
- pełny zakres zapisu dla każdej osi

Nawet jeśli:
- ruch jest tylko na fragmencie,
- oś stoi przez większość czasu,
- generator jest w stanie STOP.

## Nie wolno

Nie wolno pokazywać tylko „małego fragmentu aktywności”.

To utrudnia:
- ocenę mechaniki,
- synchronizację osi,
- ocenę logiki generatora,
- debugowanie STEP.

## Stan początkowy w GENERATORZE

Użytkownik ustalił:
- pełny timeline TAKE ma istnieć zawsze
- domyślnie:
  - `STEP = 0`
  - `DIR = 0`
  - `COUNT = 0`

czyli pełna oś czasu, ale bez ruchu.

---

# 11. Tryby EHR – ustalone i wdrożone częściowo

Użytkownik ustalił konieczne tryby pracy EHR:
- GENERATOR
- EDYTOR
- PLAYER
- RECORDER
- LIVE

To było bardzo słuszne założenie.

## Dlaczego

Bo wcześniej mieszały się funkcje:
- generowania ruchu od zera,
- edycji już istniejącego TAKE,
- preview,
- ładowania pliku.

To powodowało chaos architektury.

## Poprawna zasada

### GENERATOR
- start bez przykładowego JSON
- pełny timeline TAKE
- osie gotowe do generowania ruchu
- zapis wyniku do TAKE

### EDYTOR
- wczytanie TAKE
- rekonstrukcja krzywej z protokołu
- ponowna edycja
- nowy generator STEP

### PLAYER
- tylko odtwarzanie

### RECORDER
- zapis rzeczywistego ruchu

### LIVE
- bezpośrednie sterowanie

Tryby zostały częściowo dodane do UI i to należy zachować.

---

# 12. Co działa lepiej niż na początku

Mimo że rdzeń STEP nadal nie działa poprawnie, pewne rzeczy poszły w dobrym kierunku i trzeba je zachować:

1. okno działa szybciej niż wcześniej
2. osie mieszczą się lepiej w obszarze
3. generator startuje w trybie GENERATOR
4. duże przyciski trybów zostały dodane
5. niektóre wersje lepiej rozciągały linie na pełny obszar TAKE
6. podgląd zaczął w ogóle coś liczyć
7. został dopisany istotny materiał do dokumentacji

Tego nie wolno rozwalić w nowym podejściu.

---

# 13. Co nadal nie działa

## Lista problemów aktualnych

1. osie / parametry nadal świecą na czerwono bez logicznej zgodności
2. `STEP` nadal nie odpowiada poprawnie wykresowi
3. `COUNT` bywa liczbowo „jakiś”, ale nie jest logicznie sprzężony z realnym przebiegiem STEP
4. `EV` i `STEP` nie reprezentują tej samej rzeczy
5. po zejściu amplitudy do zera STEP potrafi pozostawać w stanie 1
6. preview nie daje jeszcze pełnej, jednoznacznej informacji o protokole
7. generator nadal nie respektuje ustaleń w sposób spójny od początku do końca

## Najkrótsza diagnoza

To co jest generowane, jest:
- częściowo liczbowo sensowne,
- ale logicznie niespójne.

Czyli:
**generator produkuje coś, ale nie to, co opisuje dokumentacja TARZANA.**

---

# 14. Błąd metodologiczny asystenta

W tym wątku popełniono błąd metodologiczny:
- próbowano łatać generator bez pełnego trzymania się aktualnych plików użytkownika,
- tworzono uproszczone implementacje,
- zgadywano interfejsy API,
- dawano ZIP-y, które łamały zgodność z kodem edytora,
- poprawki były robione zbyt często „na skróty”.

To doprowadziło do pętli:
- nowy ZIP
- nowy crash
- naprawa importu
- naprawa sygnatury
- naprawa iteracji timeline
- ale bez domknięcia sedna.

W nowym wątku nie wolno tak pracować.

---

# 15. Na jakiej bazie trzeba teraz pracować

Użytkownik na końcu przekazał bazową wersję projektu:

`tarzan-0.6.0.zip`

To jest wersja odniesienia.
Kolejna próba musi być robiona bezpośrednio na tej paczce i tylko na niej.

Nie wolno:
- tworzyć izolowanych generatorów obok projektu,
- zgadywać klas,
- zgadywać API,
- pisać „uniwersalnych” modułów bez wpasowania w istniejący kod.

---

# 16. Zakres plików, które realnie trzeba ruszyć

Minimalny sensowny zakres:
- `motion/tarzanStepGenerator.py`
- `editor/tarzanTakePreviewWindow.py`

Bardzo możliwe, że dodatkowo:
- `editor/tarzanEdytorChoreografiiRuchu.py`
- `editor/tarzanWykresOsi.py`

Ale nie więcej niż trzeba.

Zasada użytkownika jest jasna:
- pracować na istniejących plikach,
- nie mnożyć nowych bytów,
- nie rozwalać tego, co działa.

---

# 17. Poprawny model generatora STEP – do wdrożenia

To jest rdzeń, który trzeba zaimplementować w nowym wątku.

## Wejście
- pełny timeline TAKE
- krzywa ruchu osi
- mechaniczne ograniczenia osi:
  - `full_cycle_pulses`
  - `max_speed_axis`
  - rozruch / rampa
  - backlash
- stan startowy:
  - `STEP = 0`
  - `DIR = 0`
  - `COUNT = 0`

## Proces
1. próbkuj krzywą w siatce 10 ms
2. z krzywej wyznacz teoretyczną gęstość impulsów
3. przytnij ją do mechaniki osi
4. policz ile impulsów przypada na okno 10 ms (`EV`)
5. zsumuj do `COUNT`
6. z `EV` zbuduj poprawny logiczny przebieg `STEP`
7. przy `AMP = 0` nie generuj impulsów
8. przy końcu ruchu `STEP` ma wrócić do 0
9. preview ma czytać wynik generatora, nie budować własnej wersji

## Wyjście

`generated_protocol` zawierający spójnie:
- `TIME`
- `DIR`
- `STEP`
- `EV`
- `ENABLE`
- `AMP`
- `COUNT`

---

# 18. Kluczowa zasada interpretacyjna dla nowego wątku

Nie pytać już więcej, czy krzywa oznacza pozycję albo prędkość w sensie klasycznym.

To zostało rozstrzygnięte.

Krzywa oznacza:
**gęstość impulsów STEP w czasie**.

Mechanika oznacza:
**ile impulsów wolno wygenerować w danym czasie i w całym ruchu osi**.

To jest zespolone.

---

# 19. Czego nie robić w nowym wątku

1. nie robić kolejnych kosmetycznych poprawek tylko w preview
2. nie tworzyć nowych plików bez konieczności
3. nie zmieniać nazw plików w ZIP
4. nie dawać pojedynczych plików niezgodnych z API projektu
5. nie zgadywać interfejsów
6. nie wracać do rozważań „co oznacza krzywa”, bo to już ustalone
7. nie produkować generatora, który daje dobry COUNT, ale zły STEP

---

# 20. Co powiedzieć na starcie nowego wątku

Najlepszy start kolejnego wątku:

> Wracamy do TARZANA na bazie `tarzan-0.6.0.zip`. Problem nie jest już koncepcyjny ani dokumentacyjny. Problem jest implementacyjny: `motion/tarzanStepGenerator.py` nadal nie buduje poprawnego logicznie przebiegu STEP zgodnego z krzywą, mechaniką osi i protokołem 10 ms. Preview ma czytać wyłącznie `generated_protocol`. Nie chcę kosmetycznych łatek ani nowych plików. Pracujemy tylko na istniejących plikach i dajesz jeden ZIP z właściwymi ścieżkami.

---

# 21. Uczciwa ocena końcowa

W tym wątku:
- dokumentacja została bardzo dobrze doprecyzowana,
- architektura EHR została mocno wyjaśniona,
- tryby pracy zostały sensownie rozdzielone,
- użytkownik przekazał jasne i wystarczające reguły działania systemu.

Ale:
- skuteczna implementacja generatora STEP nie została domknięta,
- asystent nie poradził sobie z przełożeniem jasnych ustaleń na poprawny kod,
- ZIP-y nie doprowadziły do końca problemu.

To trzeba przyjąć bez pudrowania.

---

# 22. Najważniejsze zdanie z całego handoffu

**W TARZANIE problem nie polega już na tym, że czegoś nie wiadomo.
Problem polega na tym, że jasne zasady nie zostały jeszcze poprawnie zaimplementowane w kodzie.**
