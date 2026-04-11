# # TARZAN TAKE PROTOCOL Z SANDBOX

## Cel tej wersji

Ta wersja sandboxa służy wyłącznie do dopracowania układu, grafiki i logiki operatora dla modułu TAKE PROTOCOL przed integracją z właściwym EHR.

Na tym etapie:

- nie ma realnego ładowania danych do osi,
- nie ma integracji z MAIN TAKE,
- są tylko komunikaty statusu typu „dane wczytane” i „zapisany”.

---

## Główne zasady UI v2

### 1. Osobne okno testowe, ale w proporcjach pasa TAKE PROTOCOL

Sandbox ma działać jako osobne okno testowe, ale jego układ ma być przygotowany dokładnie pod przyszłe osadzenie w obszarze TAKE PROTOCOL w MAIN TAKE WINDOW.

### 2. Dark mode

Całość ma być utrzymana w dark mode zgodnym z EHR.
Nie używamy jasnych kafli ani białych teł wokół ikon.

### 3. 10 ikon w jednym rzędzie

- dokładnie 10 ikon,
- bez scrolla,
- bez przewijania poziomego,
- ikony możliwie blisko siebie,
- wszystko ma zmieścić się w jednym rzędzie w pasie TAKE PROTOCOL.

### 4. Prawdziwe ikony TAKE

Używamy gotowych ikon dla stanów:

- open,
- closed,
- active.

Stany:

- EMPTY → open,
- LOADED → closed,
- ACTIVE → active.

### 5. Numer TAKE

- tylko numer, np. `001`,
- bez nazwy pliku pod ikoną,
- numer ma być duży,
- numer ma trafiać centralnie w tabliczkę ikony,
- numer ma być wpisany tak, jakby był napisany na klapsie,
- kolor biały, w stylu kredy,
- używamy dostarczonej czcionki z katalogu `font`.

### 6. EDIT

- tylko dla wybranego i edytowanego TAKE,
- bardzo mały napis,
- pozycja: dolny lewy róg tabliczki,
- traktowany jako mini etykieta.

### 7. SAVE

- tylko dla aktywnego TAKE,
- pozycja: dolny prawy róg tabliczki,
- ma być wkomponowany w ikonę,
- ma mieć zielone tło,
- kolor zieleni stonowany, nie agresywny,
- ma być większy niż poprzednio, ale nadal ma wyglądać jak część tabliczki.

### 8. Hover i akcja

Zamiast double click:

- po najechaniu myszką na ikonę pojawia się małe czerwone kółko akcji,
- klik w czerwone kółko działa jak dawne „aktywuj / wczytaj”,
- czerwone kółko jest widoczne tylko na hover,
- nie jest stale wyświetlane na wszystkich TAKE.

### 9. Kliknięcia

- zwykły klik na slot → wybór / podmiana pliku TAKE,
- klik w czerwone kółko → aktywacja TAKE,
- klik w SAVE → zapis aktywnego TAKE,
- aktywny może być tylko jeden TAKE.

### 10. Status i komunikaty

Komunikaty mają trafiać do dolnego paska statusu, tak jak w głównym EHR.

Przykłady:

- TAKE 001 podpięty,
- TAKE 001 aktywowany,
- dane wczytane,
- TAKE 001 zapisany.

---

## Zasady techniczne

### 1. Zakaz `_refresh_all`

To jest zasada krytyczna.

W sandboxie NIE używamy:

- `_refresh_all`,
- globalnego przerysowania całego układu po jednej akcji,
- masowego odświeżania wszystkiego przy hover lub kliknięciu.

### 2. Tylko lokalne aktualizacje

Odświeżamy tylko to, czego dotyczy akcja:

- tylko aktywny slot,
- tylko slot pod myszką,
- tylko slot zmieniony po wyborze pliku,
- status bar osobno.

### 3. Cache ikon

Ikony i zasoby graficzne mają być ładowane do cache.
Nie wczytujemy assetów od nowa przy każdym ruchu myszy.

### 4. Obsługa pojedynczego kliknięcia

Ponieważ single click i double click w Tkinter potrafią się gryźć, stosujemy bezpieczny model:

- single click z krótkim opóźnieniem,
- hover action zamiast double click.

---

## Logika slotów

### Single click

- EMPTY → wybór pliku → zapis do slotu,
- LOADED → wybór nowego pliku → nadpisanie przypięcia.

### Action click (czerwone kółko)

- EMPTY → najpierw wybór pliku, potem aktywacja,
- LOADED → aktywacja,
- wynik: komunikat „dane wczytane”.

### SAVE

- działa tylko dla aktywnego TAKE,
- na tym etapie symulacja,
- docelowo zapis do pliku TAKE.

---

## Import plików TAKE

- dialog startuje domyślnie w `data/take/`,
- można wskazać plik spoza tego katalogu,
- po wyborze plik trafia do `data/take/`,
- jeśli istnieje plik o tej samej nazwie, tworzymy nową nazwę:
  - `_import_01`,
  - `_import_02`,
  - itd.

---

## Storage slotów

Plik pamięci slotów:

```text
data/ehr/take_protocol_slots.json
```

Przykład:

```json
{
  "slots": [
    {"path": "data/take/TAKE_001_v01.json"},
    {"path": null}
  ],
  "active_slot": 0
}
```

---

## Docelowy kierunek

Po dopracowaniu sandboxa UI v2:

- moduł ma zostać osadzony w obszarze TAKE PROTOCOL w MAIN TAKE WINDOW,
- dopiero wtedy dojdzie prawdziwa integracja z EHR i `load_take(...)`.

# TAKE - wybór z dokumentacji

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
18. Zasada zapisu sygnałów

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

### Protokół komunikacji — rozwinięcie implementacyjne

Powyższa zasada źródłowa pozostaje podstawą. Poniższe rozwinięcie ma już charakter programistyczny i wiąże protokół komunikacji z pakietem danych, czujnikami, trybami pracy oraz strukturą modułów tarzan.

W implementacji tarzan protokół komunikacji ma być budowany jako pakiet danych uporządkowany w osi czasu. Każda próbka protokołu musi odnosić się do ustalonego czasu próbkowania 10 ms i zawierać pełny stan sygnałów potrzebnych do wiernego odtworzenia ruchu, odczytu czujników i kontroli bezpieczeństwa.

Minimalne grupy danych w jednej próbce protokołu: - identyfikacja próbki: numer próbki, czas, aktywny tryb, znaczniki zdarzeń, - domena Play: stany wejść i wyjść związanych z wykonaniem ruchu, - domena Rec: stany rejestrowanego sterowania i mostka sygnałów, - domena CNC / automatyka: sygnały generowane przez warstwę automatyki, - grupa osi: STEP / DIR / ENABLE dla osi kamery i ramienia, - grupa regulatora masy: dodaj / ujmij / stan krańcówek / gotowość, - grupa czujników: TF-Luna, czujnik poziomu, PoSensors i krańcówki, - grupa interfejsu: wybór trybu, przyciski funkcyjne, potwierdzenia operatora i komunikaty zdarzeń.

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

14. ## Format pliku TAKE TARZANA

CAŁOŚĆ NALEŻY POBRAĆ Z IMPELENTACJI PLIKÓW:

```
Protokuł komunikacji zaimpementowany,
Take zaimpementowany.
```

> UWAGA: W impelmentacji zastosowano projekt już wdrożony do systemu.

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

2. Bazuemy na protokołach, które już są zaimpeentowane i foramty zapisów jonson. To już jest.

3. Przytowoujemy tak implementacje aby można było ją łatwo połączyć z EHR w wyznaczonym miejscu: TAKE PROTOCOL

![Main_take_windows_area.png](X:\tarzan\docs\Main_take_windows_area.png)
