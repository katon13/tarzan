# TARZAN — EHR (Edytor Choreografii Ruchu)
## Dokumentacja scalona

Wersja: scalona na podstawie dokumentacji repozytorium `/docs` i handoffów projektu  
Cel: jeden dokument referencyjny dla dalszej pracy nad **Edytorem Choreografii Ruchu (EHR)** bez rozbijania logiki pomiędzy wiele plików opisowych.

---

# 1. Cel dokumentu

Ten dokument scala w jednym miejscu założenia architektoniczne, matematyczne, operatorskie i implementacyjne dotyczące EHR w projekcie TARZAN.

Ma być używany jako główne odniesienie przy:
- analizie architektury EHR,
- dalszej implementacji generatora STEP,
- pracy nad edytorem osi,
- walidacji mechanicznej,
- odtwarzaniu i zapisie TAKE,
- porządkowaniu granic między warstwami systemu.

Dokument nie zastępuje całej dokumentacji repozytorium, ale stanowi **jedną scaloną konstytucję EHR**.

---

# 2. Miejsce EHR w projekcie TARZAN

Projekt TARZAN jest systemem inteligentnego ramienia kamerowego sterowanego osiami napędzanymi silnikami krokowymi. Główna mapa projektu opisuje system jako połączenie mechaniki, elektroniki i software’u, z naciskiem na prostotę kodu, prostotę obsługi i bezpieczną logikę sygnałową.

EHR jest częścią warstwy ruchu i przygotowania ujęcia. Nie jest samodzielnym „rysownikiem krzywych”, tylko narzędziem operatorskim, które:
- pracuje na modelu TAKE,
- pokazuje operatorską reprezentację ruchu osi,
- pozwala operatorowi kształtować dynamikę ruchu,
- przekazuje wynik do generatora STEP,
- zapisuje nową wersję TAKE.

EHR musi pozostawać zgodny z nadrzędną architekturą TARZANA:

```text
mechanika osi
    ↓
linia / krzywa ruchu
    ↓
generator protokołu STEP/DIR/ENABLE
    ↓
preview / player / zapis TAKE
```

Nie wolno odwracać tego przepływu i nie wolno skracać go do bezpośredniego „mechanika → STEP”.

---

# 3. Zasada nadrzędna EHR

## 3.1. EHR nie edytuje pozycji osi

W EHR krzywa ruchu **nie oznacza pozycji osi**.

Krzywa nie oznacza też klasycznej prędkości w rozumieniu CNC. W systemie TARZAN krzywa oznacza:

- **natężenie ruchu w czasie**,
- praktycznie: **gęstość impulsów STEP w czasie**,
- a więc rytm, z jakim mechanika dostaje kolejne kroki.

Interpretacja:
- wyższa krzywa → więcej impulsów STEP w krótkim czasie → szybszy ruch osi,
- niższa krzywa → mniej impulsów STEP w krótkim czasie → wolniejszy ruch osi,
- krzywa równa 0 → brak impulsów STEP → brak ruchu.

Przykład logiczny:
- `01` → jeden krok osi,
- `0101` → dwa kroki osi,
- `000010000` → jeden krok osi, ale rozciągnięty w czasie.

To jest fundament zrozumienia EHR.

## 3.2. Operator nie steruje bezpośrednio krzywą

W EHR mysz nie steruje bezpośrednio przebiegiem krzywej jako swobodnie rysowaną linią.

Prawidłowy model pracy to:

```text
MYSZ → PARAMETR → FUNKCJA RUCHU → KRZYWA
```

Czyli operator modyfikuje parametry ruchu, a system generuje wynikową krzywą zgodnie z:
- modelem matematycznym,
- ograniczeniami mechanicznymi,
- budżetem impulsów osi,
- zasadami TAKE.

## 3.3. Kluczowe rozróżnienie

Operator w EHR edytuje:
- dynamikę ruchu,
- rytm ruchu,
- płynność ruchu,
- rozkład natężenia ruchu w czasie.

Operator **nie powinien** bezpośrednio zmieniać:
- geometrii mechanicznej osi,
- pełnego zakresu osi,
- całkowitej drogi osi zapisanej w TAKE,
- budżetu impulsów wynikającego z nagrania.

---

# 4. Zasada matematyczna ruchu

## 4.1. Oś czasu

Cały system EHR działa na świętej siatce czasu TARZANA:

```text
CZAS_PROBKOWANIA_MS = 10
```

Czyli wszystkie próbki czasu muszą być zgodne z siatką:

```text
0 ms, 10 ms, 20 ms, 30 ms, ...
```

Nie wolno:
- wprowadzać lokalnego kroku czasu dla preview,
- generować STEP w innym dt,
- traktować 10 ms jako opcji zależnej od modułu.

## 4.2. Funkcja natężenia ruchu

Ruch osi opisuje funkcja:

```text
A(t)
```

Jest to funkcja natężenia ruchu budowana z punktów kontrolnych i interpolowana gładko.

## 4.3. Gęstość impulsów

Natężenie ruchu zamieniane jest na gęstość impulsów STEP:

```text
ρ(t) = k · |A(t)|
```

gdzie:
- `ρ(t)` — gęstość impulsów,
- `A(t)` — funkcja natężenia ruchu,
- `k` — współczynnik skalowania dla osi.

Interpretacja: `ρ(t)` mówi, ile impulsów STEP przypada na jednostkę czasu.

## 4.4. Droga ruchu i całka

Jedna z najważniejszych zasad EHR:

```text
droga ruchu = całka z natężenia ruchu w czasie
```

Stąd wynika:
- zmiana kształtu krzywej zmienia tempo ruchu,
- ale budżet impulsów ruchu musi pozostać zgodny z TAKE,
- przy niższym natężeniu ruchu czas trwania rośnie,
- przy wyższym natężeniu ruchu czas trwania maleje,
- liczba impulsów pozostaje zgodna z zapisaną drogą osi.

## 4.5. Generator jako akumulator impulsów

Generator STEP działa jako integrator / akumulator:

```text
sumuj ρ(t)·dt
jeżeli akumulator >= 1 → wygeneruj impuls STEP
```

To jest centralny mechanizm przejścia z krzywej do protokołu dyskretnego.

---

# 5. Zasada nadrzędna generatora STEP

Poprawny generator STEP w TARZANIE **nie może być oceniany tylko po całkowitej liczbie impulsów**.

Musi spełniać jednocześnie trzy warunki:

1. zgodność całkowitej liczby impulsów z drogą ruchu osi,
2. zgodność kierunku ruchu z przebiegiem krzywej,
3. płynność lokalnego rozkładu impulsów w czasie.

## 5.1. Płynność impulsów jest obowiązkowa

Jeżeli amplituda krzywej zmienia się płynnie, to rytm kolejnych impulsów STEP też musi zmieniać się płynnie.

Niedopuszczalne są lokalnie poszarpane przebiegi impulsów przy gładkiej krzywej, nawet jeśli suma impulsów końcowo się zgadza.

Czyli:
- płynny wzrost amplitudy → płynne zagęszczanie impulsów,
- płynny spadek amplitudy → płynne rozrzedzanie impulsów,
- brak ruchu → brak impulsów,
- zmiana kierunku → płynne przejście zgodne z logiką mechaniczną osi.

To jest warunek jednocześnie:
- matematyczny,
- mechaniczny,
- fizyczny,
- filmowy.

## 5.2. Generator nie może działać poza mechaniką

Generator nie może „produkować impulsów zgodnie z samą krzywą”, ignorując mechanikę.

Musi zawsze respektować:
- limit prędkości osi,
- limit liczby impulsów w danym czasie,
- limit zakresu osi,
- ograniczenia przyspieszeń i zmian rytmu,
- warunki bezpieczeństwa wynikające z mechaniki.

Czyli poprawna kolejność jest taka:

```text
krzywa → teoretyczna gęstość impulsów → ograniczenie mechaniczne → generator STEP
```

---

# 6. Jedno źródło prawdy dla TAKE i generatora

## 6.1. TAKE jest źródłem danych ruchu

Model TAKE przechowuje pełny zapis jednego ujęcia. Warstwa krzywych ruchu jest operatorską reprezentacją tego TAKE. Operator pracuje wyłącznie na tej warstwie, ale wynik ma wracać do TAKE jako nowa wersja.

## 6.2. Błąd architektury, którego trzeba unikać

W dotychczasowej pracy wykryto konflikt pomiędzy:
- danymi TAKE,
- parametrami mechaniki (`full_cycle_pulses`),
- lokalnymi obliczeniami preview,
- krzywą edytora.

To prowadziło do złego pipeline’u:

```text
edytor osi → preview → generator STEP
```

A prawidłowy pipeline powinien być taki:

```text
edytor osi → generator STEP → preview
```

## 6.3. Budżet impulsów osi

Budżet impulsów TAKE nie może być liczony z parametrów mechanicznych.

Prawidłowa kolejność źródeł prawdy:
1. `generated_protocol.step_count_total`
2. suma `segments[].pulse_count`
3. `raw_signal.step_count_total`

Parametr `full_cycle_pulses` wolno używać tylko do walidacji ograniczeń mechanicznych.

## 6.4. Generator działa na całym TAKE

Generator STEP nie powinien działać tylko na jednej osi w izolacji.

Choreografia ruchu jest globalna. Generator powinien działać na całym TAKE:
- znać wszystkie osie,
- iterować po wspólnej osi czasu,
- dla każdej próbki czasu aktualizować akumulatory wszystkich osi,
- generować STEP zgodnie z globalnym rytmem ujęcia.

---

# 7. Warstwy odpowiedzialności EHR

Żeby nie mieszać architektury, EHR musi mieć rozdzielone następujące warstwy:

## 7.1. Warstwa danych źródłowych
- surowe dane TAKE,
- zapis wejściowy z pliku,
- historia wersji,
- segmenty i sygnały źródłowe.

## 7.2. Warstwa modelu ruchu
- krzywe ruchu,
- punkty kontrolne,
- parametry segmentów,
- funkcje natężenia ruchu,
- logika zachowania odległości / drogi.

## 7.3. Warstwa walidacji mechanicznej
- ograniczenia osi,
- zakresy,
- limity czasowe,
- maksymalna liczba impulsów w czasie,
- zgodność z mechaniką,
- kompensacja luzów / backlash, jeśli dotyczy.

## 7.4. Warstwa generatora protokołu
- przeliczenie krzywej na STEP / DIR / ENABLE,
- akumulator impulsów,
- logika kierunku,
- budowanie timeline’u sygnałów.

## 7.5. Warstwa preview i UI
- rysowanie krzywych,
- rysowanie ghost motion,
- zoom,
- zaznaczenia,
- narzędzia edycyjne,
- play/stop/edit.

### Twarda zasada

Warstwa UI i preview **nie może zmieniać modelu logiki generatora tylnymi drzwiami**.

Warstwa wizualizacji ma pokazywać wynik, a nie stawać się źródłem prawdy dla protokołu.

---

# 8. Zalecany podział modułów EHR

Dokumentacja choreografii ruchu zaleca następujący podział:

```text
tarzanEdytorChoreografiiRuchu.py
tarzanTakeModel.py
tarzanKrzyweRuchu.py
tarzanSegmentAnalyzer.py
tarzanMechanicalValidator.py
tarzanGeneratorImpulsow.py
tarzanGhostMotion.py
tarzanMotionConfig.py
```

## 8.1. `tarzanEdytorChoreografiiRuchu.py`
Odpowiada za:
- wyświetlanie osi czasu,
- rysowanie krzywych ruchu,
- obsługę punktów kontrolnych,
- PLAY / STOP / EDIT,
- zoom czasu,
- obsługę ghost motion,
- zapis nowych wersji TAKE.

Nie powinien zawierać zasadniczej matematyki ruchu.

## 8.2. `tarzanTakeModel.py`
Odpowiada za pełną strukturę jednego TAKE.

## 8.3. `tarzanKrzyweRuchu.py`
Odpowiada za:
- reprezentację krzywych,
- interpolację,
- przeliczenia parametrów ruchu,
- zachowanie budżetu drogi / impulsów.

## 8.4. `tarzanSegmentAnalyzer.py`
Odpowiada za:
- analizę segmentów ruchu,
- rozpoznanie kierunków,
- liczenie impulsów segmentów,
- odtwarzanie segmentowej logiki TAKE.

## 8.5. `tarzanMechanicalValidator.py`
Odpowiada za:
- kontrolę zgodności z osią,
- limity mechaniczne,
- dopuszczalną dynamikę,
- odrzucanie przebiegów niebezpiecznych.

## 8.6. `tarzanGeneratorImpulsow.py`
Centralny moduł generatora STEP. To on ma być sercem pipeline’u.

## 8.7. `tarzanGhostMotion.py`
Warstwa pomocniczej wizualizacji ruchu.

## 8.8. `tarzanMotionConfig.py`
Centralna konfiguracja parametrów ruchu, konwersji i pracy EHR.

---

# 9. Model danych TAKE dla EHR

## 9.1. Format pliku

Zalecany format TAKE:

```text
JSON
```

Przykładowe nazwy:

```text
TAKE_001_v01.json
TAKE_001_v02.json
TAKE_002_v01.json
```

## 9.2. Główna struktura

Plik TAKE powinien zawierać:

```text
TAKE
├── metadata
├── timeline
├── axes
├── events
├── simulation
├── source
└── validation
```

## 9.3. Główne klasy logiczne modelu TAKE

### `TarzanTakeMetadata`
- `take_id`
- `version`
- `title`
- `author`
- `created_at`
- `edited_at`
- `description`
- `notes`

### `TarzanTimeline`
- `time_unit`
- `sample_step`
- `take_start`
- `take_end`
- `take_duration`

### `TarzanAxisTake`
- `axis_name`
- `axis_enabled`
- `mechanics_ref`
- `full_cycle_pulses`
- `min_full_cycle_time_s`
- `max_pulse_rate`
- `max_acceleration`
- `backlash_compensation`
- `start_must_be_zero`
- `end_must_be_zero`
- `raw_signal`
- `segments`
- `curve`
- `generated_protocol`

### `TarzanSegment`
- `segment_id`
- `start_time`
- `end_time`
- `direction`
- `pulse_count`
- `is_pause`
- `is_direction_change`

### `TarzanCurve`
- `curve_type`
- `interpolation`
- `preserve_distance`
- `ghost_enabled`
- `control_points`

### `TarzanControlPoint`
- `time`
- `amplitude`

### `TarzanEvent`
- `event_id`
- `event_type`
- `event_time`
- `enabled`
- `note`

### `TarzanVersion`
Powinna zawierać:
- `version_id`
- `created_at`
- `author`
- `curve_snapshot`
- `protocol_snapshot`
- `previous_version_reference`

## 9.4. Relacje między obiektami

Najwyższym obiektem jest `TarzanTake`.

Zawiera on:
- listę osi (`TarzanAxisTake`),
- listę zdarzeń (`TarzanEvent`),
- metadane,
- historię wersji.

Każda oś zawiera:
- listę segmentów (`TarzanSegment`),
- jedną krzywą (`TarzanCurve`),
- wygenerowany protokół.

Krzywa zawiera listę punktów kontrolnych (`TarzanControlPoint`).

---

# 10. Tryby pracy EHR

Aby uniknąć konfliktów architektury, EHR powinien mieć jawne tryby pracy:

```text
GENERATOR
EDYTOR
PLAYER
RECORDER
LIVE
```

Tryby te powinny być czytelne w interfejsie i reprezentowane przez duże przyciski.

## Znaczenie trybów

### GENERATOR
- analiza TAKE,
- przeliczenie krzywych,
- generacja protokołu,
- preview wyników generatora.

### EDYTOR
- praca operatorska na parametrach ruchu,
- korekta przebiegów,
- narzędzia węzłów / punktów.

### PLAYER
- odtwarzanie wygenerowanego TAKE,
- test spójności protokołu.

### RECORDER
- import / zapis przebiegów z warstwy nagrania,
- przygotowanie materiału wejściowego do EHR.

### LIVE
- podgląd aktualnej pracy lub przyszły tryb pracy bieżącej.

---

# 11. Wymagania operatorskie i UX

EHR nie jest narzędziem dla programisty, tylko dla operatora filmowego.

Interfejs powinien być:
- czytelny,
- prosty,
- bez modalnego chaosu,
- z dużymi przyciskami,
- z naciskiem na płynność pracy.

W szczególności:
- wszystkie osie powinny być widoczne na wspólnej osi czasu,
- edycja ma być płynna i przewidywalna,
- ghost motion jest warstwą pomocniczą,
- zoom i pan muszą służyć pracy operatorskiej,
- preview nie może przekłamywać generatora,
- terminal / log jest lepszy niż wyskakujące okna dla diagnostyki.

---

# 12. Mechanika i bezpieczeństwo w EHR

Mechanika jest nadrzędna wobec edycji wizualnej.

Generator i edytor muszą respektować:
- maksymalną prędkość osi,
- maksymalną liczbę impulsów na próbkę / odcinek czasu,
- ograniczenia pełnego cyklu osi,
- zakresy osi,
- warunki bezpieczeństwa wynikające z ruchu ramienia.

Wniosek:
- nie wolno oceniać krzywej tylko „na oko”,
- nie wolno uznawać za poprawny przebiegu, który jest ładny graficznie, ale mechanicznie niewykonalny,
- walidacja mechaniczna musi być obowiązkowym etapem pipeline’u.

---

# 13. Najważniejsze błędy architektury, których nie wolno powtarzać

## 13.1. Preview przed generatorem
Błędny porządek:

```text
edytor → preview → generator
```

Prawidłowy porządek:

```text
edytor → generator → preview
```

## 13.2. Liczenie budżetu impulsów z mechaniki
`full_cycle_pulses` służy do walidacji ograniczeń, nie do wyznaczania budżetu impulsów TAKE.

## 13.3. Mieszanie warstw
Nie wolno mieszać warstw:
- mechanika osi,
- linia / krzywa,
- generator protokołu,
- edytor / wizualizacja.

## 13.4. Osobna logika czasu dla preview
Całość musi pracować na `CZAS_PROBKOWANIA_MS = 10`.

## 13.5. Ocena generatora tylko po COUNT
Zgodność sumarycznej liczby impulsów nie wystarcza. Musi zgadzać się także lokalna płynność rytmu STEP.

## 13.6. Jedna wartość pełniąca kilka ról
Nie należy mieszać:
- danych źródłowych TAKE,
- danych logicznych generatora,
- danych mechanicznych,
- danych wyłącznie wizualnych.

---

# 14. Reguły implementacyjne dla dalszej pracy nad kodem

To są praktyczne zasady wynikające z architektury EHR i ustaleń projektu.

## 14.1. Zmiana w jednej warstwie
Każda zmiana kodu powinna dotyczyć jednej warstwy naraz.

Jeśli zmiana wymaga naruszenia więcej niż jednej z warstw:
- mechanika osi,
- linia / krzywa,
- protokół,
- edytor / wizualizacja,

należy się zatrzymać i najpierw to zgłosić, zamiast od razu pisać kod.

## 14.2. Obowiązkowy blok zakresu przed kodem
Przed każdą propozycją zmian kodu należy zdefiniować:

```text
WARSTWA
NIE RUSZAM
KONTRAKT ZOSTAJE
ZMIENIAM TYLKO
```

## 14.3. Kontrakt, który ma pozostać nienaruszony

```text
mechanika osi → linia/krzywa → protokół
```

Nie wolno mieszać tych warstw ani upraszczać ich do bezpośredniego STEP z mechaniki.

## 14.4. Kod ma wynikać z aktualnych plików projektu
Zmian nie należy tworzyć przez rekonstrukcję z pamięci. Kod powinien być proponowany na podstawie aktualnych plików i aktualnej dokumentacji repozytorium.

---

# 15. Aktualny stan problemu EHR

Na podstawie handoffu projektowego stan problemu wygląda tak:

- praca nad EHR była długa i częściowo skuteczna w warstwie UI,
- generator STEP nie został jeszcze wdrożony w pełni poprawnie,
- główny problem nie jest koncepcyjny ani dokumentacyjny,
- główny problem jest implementacyjny,
- edytor, preview, generator STEP i walidacja mechaniki nie pracują jeszcze na jednym spójnym modelu danych i jednym źródle prawdy dla protokołu.

To oznacza, że dalsza praca powinna iść przede wszystkim w kierunku:
1. uszczelnienia modelu danych TAKE,
2. uszczelnienia generatora jako centralnego modułu,
3. dopiero potem dopinania preview i wygładzania UI.

---

# 16. Minimalna definicja gotowości EHR

EHR można uznać za architektonicznie gotowy dopiero wtedy, gdy spełnia jednocześnie następujące warunki:

1. operator pracuje na krzywej jako modelu natężenia ruchu, a nie pozycji,
2. cały pipeline pracuje w siatce 10 ms,
3. generator STEP jest centralnym elementem przeliczenia,
4. preview pokazuje wynik generatora, a nie własną lokalną interpretację,
5. budżet impulsów jest brany z TAKE, nie z mechaniki,
6. walidacja mechaniczna jest obowiązkowa,
7. generator utrzymuje zarówno poprawną liczbę impulsów, jak i płynność ich lokalnego rytmu,
8. nowa wersja TAKE zapisuje spójny snapshot krzywej i protokołu.

---

# 17. Dokumenty źródłowe użyte do scalenia

Dokument scalony opiera się głównie na następujących plikach repozytorium TARZAN:

- `docs/INDEX.md`
- `docs/MAPA_PROJEKTU_TARZANA.md`
- `docs/TARZAN_CHOREOGRAFIA_RUCHU_MAPA.md`
- `docs/TARZAN_CHOREOGRAFIA_RUCHU_MOEDEL_MATEMATYCZNY.md`
- `docs/TARZAN_HANDOFF.md`

Pomocniczo uwzględniono także istniejącą strukturę katalogu `/docs` jako nadrzędne źródło odniesienia dla projektu.

---

# 18. Status tego dokumentu

Ten plik ma pełnić rolę:
- jednego wejścia do EHR,
- dokumentu startowego do nowych wątków,
- punktu odniesienia przy analizie kodu,
- dokumentu kontrolnego przy każdej większej zmianie edytora choreografii ruchu.

Najbezpieczniej traktować go jako dokument nadrzędny dla EHR, a pozostałe pliki z `/docs` jako źródła szczegółowe.
