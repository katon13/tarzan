# TARZAN FRAME DATA — TFD

## 1. Nazwa

Przyjęta nazwa funkcji:

```text
TARZAN FRAME DATA
```

Skrót:

```text
TFD
```

TFD oznacza warstwę danych TARZANA przypisaną do obrazu z kamery filmowej.

---

## 2. Główna idea

**TARZAN FRAME DATA** to telemetryczna nakładka na oryginalny obraz z kamery filmowej umieszczonej na ramieniu TARZANA.

Nakładka ma być widoczna w OBS lub innym systemie nagrywania jako dodatkowa warstwa na obrazie.

Celem TFD jest zapisanie razem z obrazem informacji technicznych o ruchu, osi, czujnikach, świetle i czasie ujęcia.

Dzięki temu podczas montażu i przygotowywania efektów specjalnych można łatwiej odtworzyć, co dokładnie robił TARZAN w danej chwili filmu.

---

## 3. Definicja robocza

```text
TFD = telemetryczna warstwa danych TARZANA przypisana do klatki / ujęcia filmu.
```

TFD nie jest pulpitem sterowania.
TFD nie steruje ruchem.
TFD nie zmienia danych.
TFD tylko pokazuje kopię aktualnego stanu systemu.

---

## 4. Źródło prawdy

Źródłem prawdy pozostają istniejące moduły TARZANA:

```text
SignalBus
PAR
osie
TAKE
czujniki
```

TFD ma tylko odbierać i prezentować kopię tych danych.

Najważniejsza zasada:

```text
TFD niczego nie steruje.
TFD tylko pokazuje stan TARZANA.
```

---

## 5. Miejsce TFD w architekturze

Model logiczny:

```text
SignalBus / PAR / TAKE / osie / czujniki
        ↓
TFD Server / TFD Exporter
        ↓
protokół live, np. WebSocket
        ↓
TFD Overlay
        ↓
OBS / obraz z kamery filmowej
```

OBS nie musi być źródłem danych. OBS ma tylko wyświetlić i nagrać warstwę TFD razem z obrazem kamery.

---

## 6. Zakres danych TFD

TFD powinno docelowo pokazywać dane potrzebne do późniejszej analizy ujęcia, montażu i efektów specjalnych.

Podstawowy zakres:

```text
- numer TAKE
- TC / czas ujęcia
- impulsy dla 6 osi
- stany 6 osi
- wszystkie stany czujników z PAR
- natężenie światła
- krańcówki
- alarmy
- status ruchu, np. STOP / PLAY / REC / PAUSE
- stany komunikacji, np. COM OFF / SENSOR OFF
```

---

## 7. Osie TARZANA w TFD

TFD powinno używać pełnego nazewnictwa osi zgodnego z projektem TARZAN:

```text
- oś pozioma kamery
- oś pionowa kamery
- oś pochyłu kamery
- oś ostrości kamery
- oś pionowa ramienia
- oś pozioma ramienia
```

Dla każdej osi można pokazać na przykład:

```text
- liczba impulsów
- kierunek DIR
- aktywność STEP
- ENABLE
- stan krańcówki
- status osi
```

---

## 8. Relacja do PAR

PAR jest pulpitem diagnostyczno-operatorskim.

TFD jest filmową warstwą telemetryczną.

Dane mogą pochodzić z tych samych sygnałów, ale prezentacja ma być inna:

```text
PAR = pełny pulpit diagnostyczny
TFD = lekka nakładka na obraz kamery
```

TFD powinno pobierać wszystkie istotne stany czujników z PAR, ale nie powinno kopiować całego wyglądu PAR.

---

## 9. Relacja do OBS

TFD może być dodane do OBS jako osobna warstwa overlay.

Najlepszy kierunek techniczny:

```text
TFD Overlay działa jak overlay donatów:
- łączy się z lokalnym TFD Server
- odbiera dane live po protokole
- wyświetla je jako przezroczystą warstwę na obrazie
```

Rekomendowany protokół startowy:

```text
WebSocket lokalny
```

Przykład:

```text
ws://127.0.0.1:8765/tfd
```

OBS może wyświetlać TFD jako Browser Source, ale dane nie powinny pochodzić ze statycznego pliku. Docelowo overlay powinien działać live po protokole.

---

## 10. Przykładowy pakiet danych TFD

Przykładowa ramka danych:

```json
{
  "system": "TARZAN_FRAME_DATA",
  "short": "TFD",
  "take": "TAKE_003",
  "tc": "00:01:24:120",
  "light": 72,
  "motion_status": "REC",
  "axes": {
    "os_pozioma_kamery": {
      "label": "oś pozioma kamery",
      "impulses": 1240,
      "dir": 1,
      "step": 0,
      "enable": 1
    },
    "os_pionowa_kamery": {
      "label": "oś pionowa kamery",
      "impulses": 830,
      "dir": -1,
      "step": 1,
      "enable": 1
    },
    "os_pochylu_kamery": {
      "label": "oś pochyłu kamery",
      "impulses": 210,
      "dir": 0,
      "step": 0,
      "enable": 1
    },
    "os_ostrosci_kamery": {
      "label": "oś ostrości kamery",
      "impulses": 455,
      "dir": 1,
      "step": 0,
      "enable": 1
    },
    "os_pionowa_ramienia": {
      "label": "oś pionowa ramienia",
      "impulses": 3010,
      "dir": 1,
      "step": 1,
      "enable": 1
    },
    "os_pozioma_ramienia": {
      "label": "oś pozioma ramienia",
      "impulses": 2875,
      "dir": -1,
      "step": 0,
      "enable": 1
    }
  },
  "sensors": {
    "limit_camera_horizontal_left": 0,
    "limit_camera_horizontal_right": 0,
    "light_sensor": 72,
    "emergency_stop": 0
  }
}
```

---

## 11. Zasady projektowe

Przy implementacji TFD obowiązują następujące zasady:

```text
1. TFD jest tylko odbiornikiem danych.
2. TFD nie steruje osiami ani TAKE.
3. TFD nie zmienia SignalBus.
4. TFD nie zastępuje PAR.
5. TFD nie zastępuje Nextiona.
6. TFD ma być lekkie i odświeżane okresowo.
7. TFD ma działać jako kopia stanu do obrazu filmowego.
8. TFD ma być przydatne w montażu i efektach specjalnych.
```

---

## 12. Rekomendowany rytm odświeżania

Na start wystarczy:

```text
100 ms
```

To pasuje do lekkiego modelu odświeżania znanego z kierunku Nextiona.

Jeśli później będzie potrzebna większa precyzja dla TC albo synchronizacji klatek, można rozważyć szybsze próbkowanie lub osobną synchronizację z klatkami obrazu.

---

## 13. Granice pierwszej implementacji

Pierwsza implementacja TFD powinna być mała i bezpieczna.

Zakres:

```text
WARSTWA:
TFD / overlay / prezentacja danych

NIE RUSZAM:
mechaniki osi
generatora protokołu
EHR
TAKE save/load
Nextiona
logiki sterowania ruchem

KONTRAKT ZOSTAJE:
SignalBus / PAR / TAKE są źródłem prawdy
TFD pokazuje tylko kopię danych

ZMIENIAM TYLKO:
dodanie eksportera TFD
dodanie lokalnego kanału danych live
dodanie overlayu do OBS
```

---

## 14. Podsumowanie

**TARZAN FRAME DATA** to techniczna warstwa danych nakładana na obraz filmowy z kamery zamontowanej na ramieniu TARZANA.

TFD ma pomóc w analizie ujęcia, montażu i efektach specjalnych, ponieważ razem z obrazem pokazuje stan osi, czujników, światła, TAKE i TC.

Najważniejsza zasada:

```text
TFD jest kopią danych przypisaną do obrazu.
Źródłem prawdy pozostaje TARZAN.
```
