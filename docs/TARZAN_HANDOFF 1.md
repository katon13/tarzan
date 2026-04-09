# TARZAN_HANDOFF.md
## TARZAN — handoff do nowego wątku: nowy EHR oparty na SANDBOX

**Data:** 2026-04-08  
**Status:** handoff implementacyjny  
**Cel:** zamknąć bieżący wątek i otworzyć nowy z jasnym zadaniem: zbudować nowy środek EHR na bazie modelu SANDBOX, bez ruszania końca pipeline projektu.

---

# 1. Najkrótsze podsumowanie decyzji

W tym wątku została podjęta praktyczna decyzja projektowa:

> **SANDBOX ma wejść do EHR.**

Nie jako osobny eksperyment, nie jako pomocnicze demo, nie jako panel obok, tylko jako:

> **nowy rdzeń edycji osi w EHR.**

Jednocześnie:

- **SANDBOX nie ma zastępować całego projektu TARZAN**
- **SANDBOX nie ma zastępować timeline / protokołu / TAKE**
- **SANDBOX ma zastąpić wadliwy środek EHR**

czyli warstwę:

- edycji punktów,
- zachowania krzywej,
- strojenia impulsów,
- oraz przejścia:
  - **krzywa -> STEP 0/1 co 10 ms**

---

# 2. Co użytkownik powtarzał i co zostało doprecyzowane

W toku rozmowy użytkownik kilka razy doprecyzował to samo i warto to spisać jednoznacznie, bo właśnie tu najłatwiej gubił się kierunek.

## 2.1. SANDBOX jest lepszy od starego EHR

Użytkownik potwierdził, że:

- sposób dodawania punktów w SANDBOX jest lepszy,
- sposób przemieszczania punktów w SANDBOX jest lepszy,
- zachowanie linii / krzywej w SANDBOX jest lepsze,
- zasada strojenia krzywej do impulsów w SANDBOX jest bardzo dobra,
- cały model jednej osi w SANDBOX jest praktycznie tym, czego potrzeba dla każdej osi w EHR.

Kluczowy sens tej wypowiedzi:

> **SANDBOX nie jest już tylko testem.**
>
> **SANDBOX pokazał lepszy model osi niż obecny środek EHR.**

---

## 2.2. PAN nie ma być skopiowany 1:1 z SANDBOX

To było bardzo ważne doprecyzowanie.

Użytkownik zaznaczył, że:

- **PAN bardziej pasował z oryginalnego EHR**
- bo tam dotyczył integralnej całości
- i ta część ma zostać po staremu

Czyli:

### z SANDBOX bierzemy:
- model osi,
- model krzywej,
- dodawanie punktów,
- przesuwanie punktów,
- strojenie impulsów,
- model STEP preview / STEP generatora.

### z oryginalnego EHR zostaje:
- PAN całości / integralny charakter przesuwania całego przebiegu,
- wieloosiowy układ roboczy,
- istniejący kontekst pracy na całym TAKE.

To trzeba uszanować przy nowej implementacji.

---

## 2.3. TAKE ma zostać tak jak jest

Użytkownik wyraźnie zaznaczył, że:

- TAKE jest już skonstruowany w innych klasach,
- wynika z protokołu,
- nie należy go teraz przebudowywać.

Czyli:

- **nie zmieniamy modelu TAKE**
- **nie zmieniamy końca pipeline**
- **nie budujemy nowego formatu zapisu ruchu**

Zostaje obecny model:

- timeline,
- protokół ruchu,
- zapis do TAKE.

---

## 2.4. Presety osi mają być globalne, nie w TAKE

To też zostało ustalone jednoznacznie.

Użytkownik zgodził się, żeby parametry osi były trzymane:

- **bezpośrednio w `data/`**
- bez mnożenia dodatkowych katalogów
- jako globalne presety osi
- nie jako część TAKE

Ustalony model:

```text
data/
  axis_camera_horizontal.txt
  axis_camera_vertical.txt
  axis_camera_tilt.txt
  axis_camera_focus.txt
  axis_arm_vertical.txt
  axis_arm_horizontal.txt
```

To są:

- ustawienia linii,
- ustawienia strojenia impulsów,
- ustawienia danej osi jako modelu roboczego.

TAKE ma pozostać czysty i zawierać tylko wynik ruchu / protokołu.

---

## 2.5. Generator STEP ma działać według modelu SANDBOX

To jest klucz całej integracji.

Użytkownik bardzo wyraźnie ustalił, że:

- generator nie ma działać z segmentów jako źródła prawdy,
- generator ma działać **bezpośrednio z krzywej**,
- model ma być zgodny z SANDBOX,
- wynik ma być zgodny z tym, co widać podczas strojenia.

Ostateczne ustalenie było takie:

> **KRZYWA -> STEP**

a nie:

> **SEGMENTY -> STEP**

Segmenty mogą zostać pomocnicze / diagnostyczne, ale źródłem generacji ma być krzywa.

---

## 2.6. STEP ma być tylko 0 albo 1 co 10 ms

To też zostało wyjaśnione i potwierdzone.

Użytkownik zapytał o „ramkę”, a po wyjaśnieniu potwierdził model:

- czas systemowy: **10 ms**
- każda próbka czasu = jedna ramka czasu protokołu
- w tej próbce:
  - `STEP = 0`
  - albo `STEP = 1`

Nie więcej.

Czyli:

- **nie dopuszczamy wielu impulsów w jednej próbce**
- **nie dopuszczamy EV > 1 jako modelu docelowego**
- cały generator ma pracować w modelu zgodnym z SANDBOX.

---

## 2.7. Użytkownik chciał szerokiej implementacji, nie półśrodków

Bardzo ważny wniosek z końcówki wątku:

Użytkownik kilka razy zaznaczył, że:

- dzielenie tego na zbyt małe części powoduje zapychanie wątku,
- pół-implementacje nie pokazują realnego efektu,
- woli mieć szeroką implementację i potem korygować,
- ma tagi / kopię projektu i może ryzykować większą podmianę.

Potem doprecyzował jeszcze ważniej:

> **nie chodzi o cały projekt od nowa**
>
> **chodzi o nowy EHR od środka**

czyli:

- nie ruszać całego TARZAN,
- nie ruszać timeline / protokołu / TAKE,
- tylko zbudować nowy EHR, którego rdzeń jest oparty o SANDBOX.

To doprowadziło do ostatecznej decyzji:

> **lepiej rozpocząć nowy wątek i budować nowy EHR_v2 na bazie SANDBOX i istniejącego projektu, niż dalej łatać stary środek EHR.**

---

# 3. Architektura, która została ustalona

To jest najważniejsza część techniczna handoffu.

## 3.1. Warstwy logiczne TARZAN zostają

Użytkownik wielokrotnie pilnował, że nie wolno mieszać warstw.

Obowiązuje nadal:

```text
mechanika osi
    ↓
linia / krzywa
    ↓
STEP / protokół ruchu
    ↓
timeline
    ↓
TAKE
```

To znaczy:

- mechanika nie generuje bezpośrednio STEP,
- mechanika generuje ograniczenia i parametry,
- krzywa jest warstwą pośrednią,
- STEP powstaje z krzywej,
- timeline i protokół tylko to zapisują.

---

## 3.2. Docelowy model nowego EHR

Nowy EHR ma wyglądać tak:

```text
MECHANICS
    ↓
AXIS CURVE MODEL (SANDBOX)
    ↓
STEP TUNING (SANDBOX)
    ↓
STEP GENERATOR 0/1 co 10 ms
    ↓
TIMELINE
    ↓
PROTOCOL
    ↓
TAKE
```

Czyli:

- mechanika dostarcza ograniczenia,
- oś w EHR działa na modelu SANDBOX,
- strojenie impulsów jest częścią osi,
- generator STEP jest wspólny i zgodny z SANDBOX,
- dalej istniejący pipeline projektu robi timeline / protokół / TAKE.

---

## 3.3. Preview ma być tym samym co generator

Użytkownik bardzo jednoznacznie ustalił:

> **to co widać w EHR ma być tym samym, co pojedzie do protokołu**

Czyli:

- nie dwa algorytmy,
- nie osobny preview i osobny generator,
- nie „prawie podobne” działanie.

Ma być:

```text
preview STEP = generator STEP
```

To jest fundamentalne założenie nowej implementacji.

---

# 4. Co już istnieje w projekcie i czego nie trzeba budować od zera

W tym wątku została zrobiona analiza istniejących plików i architektury.

## 4.1. Pliki, które już są poprawnym końcem pipeline

Te pliki nie są głównym problemem i nie powinny być przebudowywane na początku nowego wątku:

### `motion/tarzanTakeModel.py`
Już trzyma:
- metadata,
- timeline,
- osie,
- krzywe,
- segments,
- generated_protocol.

### `motion/tarzanTimeline.py`
Już buduje:
- globalny timeline po czasie,
- `STEP_COUNT`,
- `STEP`,
- `DIR`,
- `ENABLE`.

### `core/tarzanProtokolRuchu.py`
Już zapisuje:
- timeline osi,
- stan sygnałów,
- dane do protokołu ruchu,
- eksport TXT.

Wniosek:

> **koniec pipeline jest już zbudowany i nie jest miejscem startowym nowej implementacji EHR.**

---

## 4.2. Gdzie siedzi problem

Główne problemy są w środku EHR:

- model edycji osi,
- zachowanie punktów,
- zachowanie krzywej,
- przejście z krzywej do STEP,
- spójność pomiędzy tym co widzi użytkownik a tym co zapisze protokół.

Szczególnie ważne jest to, że obecny `tarzanStepGenerator.py` był robiony pod model bardziej ogólny (`EV`, wielokrotne impulsy w próbce), a nie pod sztywny model SANDBOX:

- `10 ms`
- `STEP tylko 0 albo 1`

To wymaga przepisania generatora pod model sandboxowy.

---

# 5. Co ma być zrobione w nowym wątku

To jest właściwy plan startowy.

## 5.1. Nie naprawiać starego EHR kawałkami

W nowym wątku **nie wracać** do podejścia:

- jedna drobna poprawka,
- jedna kosmetyka,
- jedna drobna integracja,
- jedna łatka na stary środek.

To już zostało uznane za zły kierunek.

---

## 5.2. Zbudować nowy EHR od środka

Cel nowego wątku:

> **zbudować nową implementację EHR opartą na SANDBOX, ale spiętą z istniejącym TAKE / timeline / protokołem.**

Czyli praktycznie:

- nowy środek EHR,
- nowe pliki EHR,
- nowe nazwy po angielsku,
- bazowanie na tym co już istnieje,
- ale bez dalszego łatania starej logiki osi.

---

## 5.3. Nazwy i pliki mają być po angielsku

Użytkownik poprosił, żeby w nowym wątku:

- tworzyć nowe pliki oznaczone jako EHR,
- dawać nazwy po angielsku.

To oznacza, że nowy zestaw plików powinien iść raczej w stronę np.:

```text
editor/ehrAxisModel.py
editor/ehrAxisTrack.py
editor/ehrAxisSettings.py
editor/ehrCurveEditor.py
motion/ehrStepGenerator.py
```

To są tylko przykładowe nazwy kierunkowe — ważne jest, żeby nowa implementacja była:
- czytelna,
- odróżniona od starego EHR,
- po angielsku,
- jednoznacznie związana z EHR.

---

# 6. Co ma wejść z SANDBOX do nowego EHR

To jest najważniejsza lista funkcjonalna.

## 6.1. Ma wejść bezpośrednio

Z SANDBOX należy przenieść / odtworzyć jako rdzeń:

- model jednej osi,
- model węzłów,
- dodawanie punktów,
- łapanie punktów,
- przeciąganie punktów,
- ograniczenia ruchu punktów,
- snap czasu,
- zachowanie krzywej,
- strojenie STEP,
- podgląd STEP,
- generator STEP zgodny z preview,
- preset osi.

---

## 6.2. Szczególnie ważne parametry z SANDBOX

Każda oś ma mieć własne ustawienia, jak w SANDBOX.

Przynajmniej te grupy parametrów mają być wspierane:

- dead zone,
- input max,
- gamma,
- zone gains,
- smoothing,
- accumulator bias,
- emit threshold,
- hit radius,
- time drag threshold,
- ewentualnie inne parametry osi / preview, jeśli są potrzebne do ergonomii.

To ma być trzymane jako preset osi.

---

## 6.3. Preset osi

Preset osi ma być:

- globalny,
- trzymany w `data/`,
- osobny dla każdej osi,
- nie w TAKE,
- zgodny z logiką TXT z SANDBOX.

Ustalony kierunek:

```text
data/
  axis_camera_horizontal.txt
  axis_camera_vertical.txt
  axis_camera_tilt.txt
  axis_camera_focus.txt
  axis_arm_vertical.txt
  axis_arm_horizontal.txt
```

---

# 7. Co ma zostać z istniejącego EHR

To też jest ważne, bo nowy EHR nie ma być kopią SANDBOX 1:1.

## Z istniejącego EHR ma zostać:
- PAN całej choreografii,
- układ wieloosiowy,
- ogólny kontekst TAKE,
- podpięcie do istniejącego pipeline po stronie timeline / protokołu / TAKE.

Czyli nowy EHR nie ma być „sandboxem rozciągniętym na wiele osi”, tylko:

> **wieloosiowym edytorem EHR z sandboxowym środkiem osi.**

---

# 8. Czego nie robić w nowym wątku

Żeby nie powtórzyć błędów z tego wątku, w nowym wątku nie robić:

- pół-integracji starego `tarzanWykresOsi.py`,
- kosmetycznych zmian bez efektu,
- osobnego preview i osobnego generatora,
- segmentów jako źródła STEP,
- modelu `EV > 1`,
- zmian całego projektu TARZAN,
- ruszania timeline / protokołu / TAKE na starcie.

---

# 9. Docelowe pytanie startowe do nowego wątku

Najlepiej zacząć nowy wątek mniej więcej tak:

> Budujemy nowy EHR_v2 dla TARZAN.
> Nie ruszamy końca pipeline: TAKE / timeline / protokół zostają.
> Chcemy zbudować nowy środek EHR na bazie SANDBOX.
> Każda oś ma mieć sandboxowy model:
> - edycji punktów,
> - krzywej,
> - strojenia impulsów,
> - generatora STEP 0/1 co 10 ms.
> Zostaje PAN całości z EHR.
> Nowe pliki mają być po angielsku i oznaczone jako EHR.
> Zaczynamy od architektury plików i potem od razu przechodzimy do pełnej implementacji nowego EHR.

To powinno natychmiast ustawić prawidłowy kierunek.

---

# 10. Ostateczny wniosek z tego wątku

Ten wątek doprowadził do bardzo ważnej konkluzji:

> **nie ma sensu dalej łatać starego środka EHR**
>
> **trzeba zbudować nowy EHR na bazie modelu SANDBOX**

Jednocześnie:

> **nie trzeba budować całego projektu TARZAN od nowa**
>
> **trzeba wymienić tylko środek EHR i spiąć go z istniejącym pipeline**

To jest właściwy punkt startowy na kolejny etap prac.

---

# 11. Jednozdaniowa definicja zadania na nowy wątek

> **Zbudować nowy EHR_v2 dla TARZAN, w którym każda oś działa na modelu SANDBOX, a wyjście pozostaje zgodne z obecnym TAKE / timeline / protokołem.**
