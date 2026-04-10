# TARZAN — PROTOKÓŁ → TAKE (WARSTWA REC / SYMULACJA / DOCELOWA IMPLEMENTACJA)

## CEL DOKUMENTU

Ten dokument precyzuje:

- jak w TARZANIE działa i ma działać ścieżka:
  **PROTOKÓŁ → TAKE**
- co już jest zaimplementowane jako architektura, symulacja i analiza
- czego jeszcze brakuje jako pełnego programu / recordera
- jakie pliki już dziś biorą udział w tworzeniu TAKE oraz protokołu
- jak to ma zostać wykorzystane przez **EHR**

To jest **kluczowy element systemu TARZAN**

---

# 1. FUNDAMENT TARZAN

## TAKE = timeline sygnałów

W TARZANIE TAKE nie jest klasycznym modelem pozycyjnym CNC.

TAKE to zapis ruchu jako przebiegu sygnałów w czasie:

- próbka co 10 ms
- STEP
- DIR
- ENABLE
- ewentualnie dalsze sygnały sterujące i zdarzenia

Najważniejsza zasada:

- osią nadrzędną jest **czas**
- nie zapisujemy „pozycji docelowej”
- zapisujemy **stan sterowania w czasie**

Czyli:

**TAKE = zapis rzeczywistego lub wygenerowanego ruchu jako funkcji czasu**

---

# 2. DWA KIERUNKI W SYSTEMIE

W TARZANIE istnieją dwa kierunki pracy:

## A. Aktualnie działający kierunek

**PROTOKÓŁ** → TAKE

To jest ścieżka już realnie używana:

- generator / edytor buduje TAKE
- z TAKE powstaje generated_protocol
- z generated_protocol można zbudować eksport i preview i do elektorniki przez protokół

To jest obecnie główny działający przepływ.

## B. Kluczowy kierunek docelowy

**PROTOKÓŁ → TAKE**

To jest ścieżka potrzebna dla:

- nagrywania REC
- odtwarzania rzeczywistego ruchu
- budowy TAKE z materiału źródłowego
- późniejszej edycji tego ruchu w EHR

Ta ścieżka jest już **opisana architektonicznie**
i **częściowo wsparta przez model oraz analizę segmentów**,
ale nie jest jeszcze zamknięta jako pełny recorder.

---

# 3. CO JUŻ ISTNIEJE

## 3.1. Dokumentacja architektury ruchu

Plik:

```text
docs/TARZAN_CHOREOGRAFIA_RUCHU_MAPA.md
docs/MAPA_PROJEKTU_TARZANA.md
```

Ten dokument opisuje kierunek:

```text
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

To oznacza, że w projekcie od początku istnieje założenie, że:

- TAKE jest jego logiczną reprezentacją,
- a edytor i generator pracują już na TAKE.

---

## 3.2. Model danych TAKE

Plik:

```text
motion/tarzanTakeModel.py
```

Ten plik zawiera model danych TAKE, czyli strukturę gotową do przechowania:

- metadata
- timeline
- axes
- events
- simulation
- source
- validation

oraz w obrębie osi:

- raw_signal
- segments
- curve
- generated_protocol

To znaczy, że **kontener danych TAKE już istnieje**
i jest przygotowany zarówno do:

- generatora,
- edytora,
- jak i przyszłej ścieżki REC → TAKE.

---

## 3.3. Analiza segmentów ruchu

Plik:

```text
motion/tarzanSegmentAnalyzer.py
```

To jest bardzo ważny element pośredni.

Ten moduł odpowiada za analizę ruchu na poziomie segmentów.
To właśnie tutaj znajduje się naturalny most między:

- surowym protokołem sterowania,
- a logicznym modelem ruchu.

To znaczy:

- z surowego przebiegu STEP / DIR / ENABLE można wykryć:
  - ruch dodatni,
  - ruch ujemny,
  - pauzy,
  - zmiany kierunku,
  - granice segmentów,
- a potem zbudować strukturę segmentów osi,
- która zasili model TAKE.

To jeszcze nie jest pełny recorder,
ale to już jest **realny fragment ścieżki PROTOKÓŁ → TAKE**.

---

## 3.4. Tworzenie TAKE w generatorze / edytorze cel

Metoda:

- tworzy obiekt `TarzanTake`
- buduje metadata
- buduje timeline
- tworzy osie
- ustawia eventy
- ustawia source jako `GENERATOR`

---

## 3.6. Budowa i eksport protokołu z TAKE

Plik:

```text
core/tarzanProtokolRuchu.py
```

To jest warstwa budowania protokołu z modelu TAKE.

Rola tego pliku:

- budowa wierszy protokołu z TAKE
- operacja na wspólnej osi czasu
- eksport do TXT / formatu plikowego

Czyli ten plik nie tworzy TAKE z protokołu,
tylko działa w kierunku:

**TAKE → PROTOKÓŁ**

Jest to jednak kluczowy element,
bo definiuje docelowy format danych,
który później recorder będzie musiał czytać w drugą stronę.

---

# Zapis TAKE do wersjonowanego pliku

```
Ten model do wykorzystania w czasie generowania i zapisywania z TAKE
```

Plik:

```text
core/tarzanTakeVersioning.py
```

To jest warstwa zapisu wersji TAKE.

W praktyce:

- EHR / generator / edytor przygotowuje dane TAKE,
- a ten moduł zapisuje nową wersję do pliku JSON.

Tu zamyka się obecna ścieżka tworzenia TAKE po stronie generatora.

---

### Kierunek PROTOKÓŁ → TAKE już istnieje:

- w architekturze,
- w dokumentacji,
- w modelu TAKE,
- w analizie segmentów,
- w logice przepływu systemu.

**brakuje finalnej implementacji programowej,
a nie samej idei ani podstaw architektury.**

---

## Model TAKE

```text
motion/
└── tarzanTakeModel.py
```

Rola:

- definicja struktury danych TAKE
- wspólny format dla generatora, edytora i przyszłego recordera
- kontener dla osi, segmentów, curve i generated_protocol

---

## Analiza ruchu / segmentów

```text
motion/
└── tarzanSegmentAnalyzer.py
```

Rola:

- analiza przebiegu ruchu
- rozbijanie ruchu na segmenty logiczne
- naturalny most pomiędzy sygnałem REC a modelem TAKE

To jest ważna warstwa dla przyszłego:
**PROTOKÓŁ → SEGMENTY → TAKE**

---

## Budowa protokołu i eksport

```text
core/
└── tarzanProtokolRuchu.py
```

Rola:

- budowa finalnego protokołu z TAKE
- składanie globalnej osi czasu
- eksport plikowy

To jest produkcyjna warstwa protokołu po stronie generatora.

---

## Zapis wersji TAKE

```text
core/
└── tarzanTakeVersioning.py
```

Rola:

- zapis nowego TAKE do pliku JSON
- wersjonowanie
- aktualizacja metadata

---

## 5.8. Docelowy recorder REC → TAKE

```text
motion/
└── tarzanTakeRecorder.py
```

Rola docelowa:

- wejście: surowy protokół REC
- analiza próbek czasowych
- budowa osi TAKE
- budowa raw_signal
- budowa segmentów
- wstępna budowa curve lub danych pod curve
- złożenie pełnego `TarzanTake`
- przekazanie do EHR / zapis JSON

To jest brakujące ogniwo.

---

# JAK TO POWINNO DZIAŁAĆ DOCELOWO

## Ścieżka GENERATOR / EDYTOR

```text
EHR / Generator
    ↓
TarzanTake
    ↓
TarzanStepGenerator
    ↓
generated_protocol
    ↓
tarzanProtokolRuchu
    ↓
plik protokołu / preview / playback
```

To już w dużej części działa.**

## EHR pracuje na TAKE

nie na surowym protokole

## Dziś w systemie działa realnie:

```text
TAKE → PROTOKÓŁ
```

## W systemie istnieje już jako architektura i częściowa warstwa pośrednia:

```text
PROTOKÓŁ → TAKE
```

czyli pełnej implementacji recordera REC → TAKE.

To jest brakujące ogniwo,
ale cały system jest już przygotowany tak,
aby to ogniwo dopisać bez łamania architektury TARZAN.

# Struktura plików związana z protokołem

```
motion/tarzanTakeModel.py
motion/tarzanSegmentAnalyzer.py
core/tarzanProtokolRuchu.py
core/tarzanTakeVersioning.py
```



# TAKE - wybór z dokumentacji

Podstawową jednostką pracy edytora jest TAKE. TAKE oznacza pojedynczy zapis ruchu, który może być nagrywany, edytowany, poprawiany i zapisywany w kolejnych wersjach. System nie powinien nadpisywać bez potrzeby wcześniejszych wersji, lecz tworzyć ich kolejne odmiany. Dzięki temu operator może wracać do wcześniejszych wariantów ujęcia i porównywać efekty zmian.

Rejestr projektu pełni rolę modelu logicznego i organizacyjnego, natomiast rzeczywiste zapisy TAKE mogą być przechowywane w osobnych plikach tekstowych lub innych plikach roboczych zgodnych z przyjętym formatem projektu.

### Architektura logiczna modułu

Edytor choreografii ruchu TARZANA powinien być oparty na czterech głównych warstwach działania:

### Model TAKE

Z surowego zapisu system buduje uproszczoną, operatorską warstwę edycyjną zawierającą:

- czas,

- kierunek,

- natężenie,

- długość segmentów ruchu,

- zależności pomiędzy osiami,

- zdarzenia punktowe takie jak sygnał drona.

# Zasada zapisu sygnałów

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

### Przykład ramki protokołu z danymi osi, czujników i stanu trybu

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

### Związek protokołu z trybami pracy

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

19. Uzupełnienia zgodności z dokumentami źródłowymi

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

- 21. Zasada zgodności z dokumentacją PoKeys i bibliotekami
  
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
  
  ## Mechanika i proporcje przekładni
  
  Warstwa elektroniczne jest ściśle powiązana z mechaniką i pewne i bezawaryjne funkcjonowanie to główna zasada, która musi być uwzględniona. Tak jak i bezpieczeństwo i niwelowanie mechanicznych niedoskonałości.
  
  Jedno źródło prawdy dla TAKE i generatora
  
  ## TAKE jest źródłem danych ruchu
  
  Model TAKE przechowuje pełny zapis jednego ujęcia. Warstwa krzywych ruchu jest operatorską reprezentacją tego TAKE. Operator pracuje wyłącznie na tej warstwie, ale wynik ma wracać do TAKE jako nowa wersja.
  
  ## Generator działa na całym TAKE
  
  Generator STEP nie powinien działać tylko na jednej osi w izolacji.
  
  Choreografia ruchu jest globalna. Generator powinien działać na całym TAKE:
  
  - znać wszystkie osie,
  
  - iterować po wspólnej osi czasu,
  
  - dla każdej próbki czasu aktualizować akumulatory wszystkich osi,
  
  - generować STEP zgodnie z globalnym rytmem ujęcia.
  
  - 7. Warstwy odpowiedzialności EHR
    
    Żeby nie mieszać architektury, EHR musi mieć rozdzielone następujące warstwy:
    
    ## Warstwa danych źródłowych
    
    - surowe dane TAKE,
    - zapis wejściowy z pliku,
    - historia wersji,
    - segmenty i sygnały źródłowe.
    
    ## Warstwa modelu ruchu
    
    - krzywe ruchu,
    - punkty kontrolne,
    - parametry segmentów,
    - funkcje natężenia ruchu,
    - logika zachowania odległości / drogi.
    
    ## Warstwa walidacji mechanicznej
    
    - ograniczenia osi,
    - zakresy,
    - limity czasowe,
    - maksymalna liczba impulsów w czasie,
    - zgodność z mechaniką,
    - kompensacja luzów / backlash, jeśli dotyczy.
    
    ## Warstwa generatora protokołu
    
    - przeliczenie krzywej na STEP / DIR / ENABLE,
    - akumulator impulsów,
    - logika kierunku,
    - budowanie timeline’u sygnałów.
    
    ## Warstwa preview i UI
    
    - rysowanie krzywych,
    - rysowanie ghost motion,
    - zoom,
    - zaznaczenia,
    - narzędzia edycyjne,
    - play/stop/edit.
    
    ### Twarda zasada
    
    Warstwa UI i preview **nie może zmieniać modelu logiki generatora tylnymi drzwiami**.
    
    Warstwa wizualizacji ma pokazywać wynik, a nie stawać się źródłem prawdy dla protokołu.
    
    ## Format pliku
    
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
    
    ## Główna struktura
    
    ```
    Zawarta w impelemntacji plików
    ```
    
    ## Główne klasy logiczne modelu TAKE
    
    ```
    Zawarta w impelemntacji plików
    ```
    
    ---
    
    # Tryby pracy EHR
    
    Aby uniknąć konfliktów architektury, EHR powinien mieć jawne tryby pracy:
    
    ```text
    GENERATOR
    EDYTOR
    ```

## Architektura systemu TARZAN w kontekście edytora

Edytor choreografii ruchu jest jednym z kluczowych elementów systemu TARZAN, ale nie działa samodzielnie. Stanowi on element większego ekosystemu sterowania ruchem. Pełny przepływ danych w systemie wygląda następująco:

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

## Główna struktura pliku TAKE

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

## Sekcja metadata

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

## Sekcja timeline

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

## Sekcja axes

Najważniejsza część pliku.
Każda oś posiada własny blok.
Proponowane klucze osi:

- camera_horizontal

- camera_vertical

- camera_tilt

- camera_focus

- arm_vertical

- arm_horizontal

- dron

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

## Sekcja curve

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

## Sekcja generated_protocol

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

## Sekcja events

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

## Sekcja simulation

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

## Sekcja source

Powiązanie z materiałem źródłowym.

```
"source": {
  "record_mode": "tREC",
  "source_protocol_file": "REC_2026_03_21_01.txt",
  "source_notes": "Nagranie z próby 3"
}
```

## Sekcja validation

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

## Pełny przykład pliku TAKE

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

## Najważniejsze zasady tego formatu

Ten format spełnia wszystko, co ustaliliśmy:

- jeden plik = jeden TAKE,

- wersje są osobnymi plikami,

- osie są rozdzielone,

- dron jest zdarzeniem punktowym,

- krzywa operatorska jest oddzielona od sygnałów wykonawczych,

- mechanika osi jest jawnie powiązana z TAKE,

- walidacja jest częścią pliku.

To jest bardzo dobry fundament.

## Model klas Python dla pliku TAKE TARZANA

Poniższy model klas Python stanowi bezpośrednie odwzorowanie formatu pliku TAKE TARZANA. Jego zadaniem jest uporządkowanie danych ruchu w strukturze gotowej do zapisu, odczytu, walidacji oraz dalszego wykorzystania przez edytor, symulator i tryb tAA.

```
Zaimpelentowane w plikach
```

Uwagi, należy przeanalizowć zaimplementowan już metody do polików gotowe do użycia w innych systemach komunikacji w Tarzanie. 
NACZELNA UWAGA: ZAWSZE ANALIZUJ JUŻ CO JEST ZROBIONE:

# Struktura plików Tarazana

```
/tarzan
├── .gitignore
├── CHANGELOG.md
├── COMMIT_RULES.md
├── README.md
├── TarzanRejestr.json
├── VERSION
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── tarzan_export_signals_catalog.py
├── tarzan_signals_catalog.json
├── tarzan_tryb_form_v5.html
├── tmp.py
├── todo_list.txt
│
├── audio/
│   ├── __init__.py
│   ├── tarzanAudioCatalog.py
│   ├── tarzanAudioPlayer.py
│   ├── signals/
│   │   ├── beep_action.wav
│   │   ├── beep_emergency.wav
│   │   ├── beep_info.wav
│   │   └── beep_warning.wav
│   └── voice/
│       ├── All_set.wav
│       ├── Emergency_stop.wav
│       ├── Motion_starting.wav
│       ├── Motion_stopped.wav
│       ├── Playback_ready.wav
│       ├── Prepared_to_play.wav
│       ├── Ready.wav
│       ├── Ready_to_record.wav
│       ├── Recording_finished.wav
│       ├── Recording_started.wav
│       ├── Stay_clear.wav
│       ├── Step_away.wav
│       └── System_ready.wav
│
├── config/
│   ├── __init__.py
│   └── tarzanMotionConfig.py
│
├── core/
│   ├── __init__.py
│   ├── tarzanAssets.py
│   ├── tarzanBledy.py
│   ├── tarzanController.py
│   ├── tarzanLogger.py
│   ├── tarzanMetodyZezwolenie.py
│   ├── tarzanProtokolRuchu.py
│   ├── tarzanStanyPracy.py
│   ├── tarzanSystem.py
│   ├── tarzanTakeVersioning.py
│   ├── tarzanUstawienia.py
│   └── tarzanZmienneSygnalowe.py
│
├── data/
│   ├── ehr/
│   │   └── main_take_settings.json
│   ├── logi/
│   │   └── .gitkeep
│   ├── matrix_led_wzory/
│   │   └── .gitkeep
│   ├── presety/
│   │   └── .gitkeep
│   ├── protokoly/
│   │   ├── .gitkeep
│   │   ├── TAKE_001_v01_protocol.txt
│   │   └── TAKE_001_v02_protocol.txt
│   └── take/
│       ├── .gitkeep
│       ├── TAKE_001_v01.json
│       └── TAKE_001_v02.json
│
├── docs/
│   ├── INDEX.md
│   ├── MAPA_PROJEKTU_TARZANA.md
│   ├── STRUKTURA_PLIKOW_TARZAN.md
│   ├── TARZAN_CHOREOGRAFIA_RUCHU_MAPA.md
│   ├── TARZAN_CHOREOGRAFIA_RUCHU_MOEDEL_MATEMATYCZNY.md
│   ├── TARZAN_HANDOFF.md
│   ├── TARZAN_SYSTEM_ARCHITECTURE.md
│   └── external/
│       ├── CZUJNIK ODLEGLOSCI.pdf
│       ├── Dokumentacja techniczna czujnika.pdf
│       ├── G03-NP93-F.pdf
│       ├── PoKeys - protocol specification.pdf
│       ├── PoKeys57 - user manual.pdf
│       ├── PoSensors.pdf
│       ├── PoStep25-32 UserManual.pdf
│       ├── SOK2-21-0.pdf
│       ├── TSL25911_Datasheet_EN_v1.pdf
│       └── czujnik poziomu MMA.pdf
│
├── editor/
│   ├── __init__.py
│   ├── tarzanAxisSandbox.py
│   ├── tarzanEdycjaPunktow.py
│   ├── tarzanEdytorChoreografiiRuchu.py
│   ├── tarzanKontrolkiTransportu.py
│   ├── tarzanOknoTake.py
│   ├── tarzanPanelOsi.py
│   ├── tarzanPlayhead.py
│   ├── tarzanPresetyWygladzania.py
│   ├── tarzanProtocolPreview.py
│   ├── tarzanTakePreviewWindow.py
│   ├── tarzanWykresOsi.py
│   └── tarzanZoomTimeline.py
│
├── hardware/
│   ├── __init__.py
│   ├── tarzanKameryUSB.py
│   ├── tarzanKlawiatura4x3.py
│   ├── tarzanLCD1602.py
│   ├── tarzanMatrixLED8x8.py
│   ├── tarzanNextion50.py
│   ├── tarzanNextion70.py
│   ├── tarzanPoExtBus.py
│   ├── tarzanPoKeysLevels.py
│   ├── tarzanPoKeysPlay.py
│   ├── tarzanPoKeysRec.py
│   ├── tarzanPoKeysSetting.py
│   ├── tarzanPoKeysStart.py
│   ├── tarzanPoSensors.py
│   ├── tarzanPoStep25.py
│   ├── tarzanPrzyciskiFunkcyjne.py
│   ├── tarzanRRP.py
│   ├── tarzanSterownikSOK.py
│   ├── tarzanTFLuna.py
│   └── pokeys/
│       ├── Czujnik odleglosci Podlaczenie.py
│       ├── Czujnik odlegosci Przyklad.py
│       ├── PoKeys.py
│       ├── PoKeysUsage.py
│       └── PoKeyslib.dll
│
├── img/
│   ├── axes/
│   │   ├── axis_camera_horizontal.png
│   │   ├── axis_camera_vertical.png
│   │   ├── axis_camera_tilt.png
│   │   ├── axis_camera_focus.png
│   │   ├── axis_arm_horizontal.png
│   │   ├── axis_arm_vertical.png
│   │   └── (inne warianty ikon osi)
│   │
│   ├── take/
│   │   ├── take_icon_01.png
│   │   ├── take_icon_02.png
│   │   └── (inne ikony TAKE)
│   │
│   └── sorce_psd/
│       ├── axes_icons.psd
│       ├── take_icons.psd
│       └── (pliki źródłowe PSD)
│
├── mechanics/
│   ├── __init__.py
│   ├── tarzanArmHorizontal.py
│   ├── tarzanArmVertical.py
│   ├── tarzanAxis.py
│   ├── tarzanCameraFocus.py
│   ├── tarzanCameraHorizontal.py
│   ├── tarzanCameraTilt.py
│   ├── tarzanCameraVertical.py
│   ├── tarzanDronRelease.py
│   ├── tarzanMechanikaOsi.py
│   └── tarzanRegulatorMasy.py
│
├── modes/
│   ├── __init__.py
│   ├── tarzanTrybAllAuto.py
│   ├── tarzanTrybAllAuto3D.py
│   ├── tarzanTrybAllAutoDron.py
│   ├── tarzanTrybAllAutoSpecialEffects.py
│   ├── tarzanTrybAutoTracking.py
│   ├── tarzanTrybBazowy.py
│   ├── tarzanTrybManual.py
│   ├── tarzanTrybManualAutoSupport.py
│   ├── tarzanTrybPlayMotion.py
│   └── tarzanTrybRecordMotion.py
│
├── motion/
│   ├── __init__.py
│   ├── homingManager.py
│   ├── motionPlanner.py
│   ├── motionProfile.py
│   ├── tarzanGeneratorTAA.py
│   ├── tarzanGhostMotion.py
│   ├── tarzanKrzyweRuchu.py
│   ├── tarzanMechanicalValidator.py
│   ├── tarzanSegmentAnalyzer.py
│   ├── tarzanSmoothMotion.py
│   ├── tarzanStepGenerator.py
│   ├── tarzanSymulacjaRuchu.py
│   ├── tarzanTakeModel.py
│   ├── tarzanTakePlayer.py
│   ├── tarzanTakeRecorder.py
│   └── tarzanTimeline.py
│
├── presets/
│   ├── __init__.py
│   ├── presetManager.py
│   ├── smoothingProfiles.py
│   └── trajectories.py
│
└── safety/
    ├── __init__.py
    ├── faultManager.py
    ├── limitsManager.py
    └── safetyManager.py
```

# Uwagi implementacyjne

1. Pomijamy pliki, które mają wartość 0.

2. Mogą pojawić się powtórzenia i niektualne założenia zawsze wóczas pytaj.

3. Wszystko jest w fazie rozowuj i zmian, wynikających z implementacji, czyi zawsze ważne co już jest napisane a co w dokumentacji. 

4. Były próby starego EHR, któy działał  błędnie, mogą być jego echa, ale niektóre metody można analizować.
