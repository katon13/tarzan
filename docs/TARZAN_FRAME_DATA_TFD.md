# TARZAN FRAME DATA — TFD

## 1. Nazwa i skrót

Przyjęta nazwa funkcji:

```text
TARZAN FRAME DATA
```

Przyjęty skrót:

```text
TFD
```

TFD oznacza telemetryczną warstwę danych TARZANA przypisaną do obrazu z kamery filmowej.

---

## 2. Główna idea

**TARZAN FRAME DATA** to nakładka danych technicznych nakładana na oryginalny obraz z kamery filmowej umieszczonej na ramieniu TARZANA.

TFD ma być widoczne jako dodatkowa warstwa w OBS lub innym systemie nagrywania. Celem nie jest sterowanie TARZANEM, tylko zapisanie razem z obrazem informacji o tym, co dokładnie robił system podczas ujęcia.

TFD ma pomagać później w:

```text
- montażu,
- analizie ujęcia,
- efektach specjalnych,
- synchronizacji obrazu, dźwięku i ruchu,
- odtworzeniu stanu osi, czujników i światła dla konkretnego TAKE.
```

---

## 3. Definicja robocza

```text
TFD = telemetryczna warstwa danych TARZANA przypisana do klatki / ujęcia filmu.
```

TFD:

```text
- nie jest pulpitem sterowania,
- nie steruje ruchem,
- nie zmienia danych,
- nie zastępuje PAR,
- nie zastępuje Nextiona,
- pokazuje kopię aktualnego stanu systemu.
```

---

## 4. Źródło prawdy

Podstawowym źródłem prawdy dla TFD są istniejące moduły TARZANA:

```text
SignalBus
PAR
TAKE
osie
czujniki
```

TFD ma odbierać i prezentować kopię tych danych.

Najważniejsza zasada:

```text
TFD niczego nie steruje.
TFD tylko pokazuje stan TARZANA.
Źródłem prawdy pozostaje TARZAN.
```

---

## 5. Jedyny wyjątek: CLAP

Jedynym dodatkowym sygnałem, który może być traktowany jako osobne źródło prawdy dla TFD, jest:

```text
CLAP
```

CLAP to świadomy marker synchronizacyjny początku TAKE, wywołany z ekranu Nextion `take_main`.

CLAP nie steruje ruchem. CLAP oznacza moment synchronizacji:

```text
- wizualnie na ekranie Nextion,
- dźwiękowo jako dźwięk klapsa filmowego,
- cyfrowo jako marker w TFD / TAKE.
```

Zasada:

```text
Dla wszystkich stanów systemu źródłem prawdy jest PAR / SignalBus / TAKE / osie / czujniki.
Jedynym dodatkowym markerem spoza tych danych jest CLAP.
```

CLAP powinien być zapisany z:

```text
- numerem TAKE,
- TC / czasem,
- źródłem zdarzenia,
- identyfikatorem lub numerem zdarzenia, jeśli będzie potrzebny.
```

---

## 6. Miejsce TFD w architekturze

Model logiczny:

```text
SignalBus / PAR / TAKE / osie / czujniki
        ↓
TFD Collector / TFD Exporter
        ↓
TFD Packet
        ├─ OBS Overlay
        └─ Nextion take_main
```

TFD ma mieć dwóch głównych odbiorców:

```text
1. OBS — jako nakładka na obraz z kamery filmowej.
2. Nextion take_main — jako fizyczny podgląd TAKE / TFD.
```

OBS i Nextion nie są głównym źródłem danych TFD. One wyświetlają kopię stanu.

Wyjątkiem jest przycisk CLAP w Nextion `take_main`, który generuje marker początku TAKE.

---

## 7. Relacja do PAR

PAR jest pulpitem diagnostyczno-operatorskim.

TFD jest filmową warstwą telemetryczną.

Dane mogą pochodzić z tych samych sygnałów, ale prezentacja ma być inna:

```text
PAR = pełny pulpit diagnostyczny i operatorski.
TFD = lekka nakładka telemetryczna na obraz kamery.
```

TFD powinno pobierać wszystkie istotne stany czujników z PAR, ale nie powinno kopiować całego wyglądu PAR.

---

## 8. Relacja do OBS

TFD ma być dodane do OBS jako osobna warstwa overlay.

W OBS należy użyć źródła:

```text
Źródła → + → Przeglądarka
```

Czyli polskie źródło **Przeglądarka** odpowiada angielskiemu **Browser Source**.

Docelowo TFD powinno działać podobnie jak overlay donatów:

```text
- łączy się z lokalnym TFD Server,
- odbiera dane live po protokole,
- wyświetla je jako przezroczystą warstwę na obrazie.
```

Rekomendowany kierunek techniczny:

```text
OBS Browser Source
        ↓
TFD HTML Overlay
        ↓
WebSocket / lokalny protokół live
        ↓
TFD Server / TFD Exporter
```

Przykład adresu lokalnego:

```text
ws://127.0.0.1:8765/tfd
```

Albo dla samego źródła przeglądarkowego:

```text
http://127.0.0.1:8765/tfd
```

OBS ma tylko nagrać obraz kamery razem z warstwą TFD.

---

## 9. Wygląd overlayu: HTML / CSS / JS

Wygląd TFD overlay powinien być robiony jako normalna warstwa webowa.

Podział odpowiedzialności:

```text
HTML = układ pól i struktura overlayu.
CSS  = wygląd, pozycje, kolory, ramki, przezroczystość, fonty.
JS   = odbiór danych live i wpisywanie wartości do pól.
```

Przykładowe pliki:

```text
tarzan_tfd_overlay.html
tarzan_tfd_overlay.css
tarzan_tfd_overlay.js
```

CSS powinien odpowiadać za:

```text
- przezroczyste tło,
- pozycję paneli,
- kolory statusów,
- wygląd pól osi,
- wygląd pól czujników,
- styl TC,
- styl TAKE,
- styl CLAP,
- sygnalizację alarmów,
- czytelność na obrazie filmowym.
```

Zasada:

```text
CSS robi wygląd.
JS robi dane.
TARZAN robi prawdę.
OBS tylko wyświetla.
```

---

## 10. Relacja do Nextion take_main

Te same dane TFD, które idą do OBS, mają iść jako kopia podglądowa na fizyczny Nextion do okna:

```text
take_main
```

Nextion `take_main` ma być fizycznym ekranem referencyjnym dla TAKE / TFD.

Ekran Nextion może być filmowany przez kamerę głównego ujęcia. Dzięki temu początek TAKE może być oznaczony jednocześnie:

```text
- na obrazie z kamery,
- w dźwięku,
- w danych TFD,
- w logice TAKE.
```

Nextion `take_main` powinien pokazywać uproszczoną kopię danych TFD, np.:

```text
- numer TAKE,
- TC,
- status REC / PLAY / STOP,
- CLAP status,
- wybrane stany osi,
- wybrane stany czujników,
- światło,
- alarmy / krańcówki.
```

Nextion nie powinien być źródłem prawdy dla danych osi, czujników ani TAKE. Ma pokazywać kopię tych danych.

Wyjątkiem jest przycisk CLAP.

---

## 11. Przycisk CLAP na Nextion take_main

W oknie `take_main` ma powstać przycisk:

```text
CLAP
```

Zadanie przycisku CLAP:

```text
- oznaczyć początek TAKE,
- wysłać komendę do systemu,
- uruchomić odtworzenie dźwięku klapsa filmowego,
- wygenerować marker CLAP w TFD / TAKE,
- dać synchronizację obrazu, dźwięku i danych.
```

CLAP jest cyfrowo-fizycznym klapsem filmowym TARZANA.

Przykładowa komenda z Nextiona:

```text
print "take:clap=1"
printh FF FF FF
```

Dopuszczalna alternatywa, jeśli warstwa będzie nazwana bezpośrednio TFD:

```text
print "tfd:clap=1"
printh FF FF FF
```

Preferowana roboczo komenda:

```text
take:clap=1
```

Uzasadnienie: przycisk oznacza początek TAKE, a TFD zapisuje i pokazuje ten marker.

## KONIECZE DO PRECYZYJNEJ PRACY Z NEXTION i PAR

W budowie komunikacji nalezy uzywac tylko gotowych zasad opisanych i w przyladach dokumentacji i instukcji komend

```
https://nextion.tech/instruction-set/?utm_source=chatgpt.com
```

---

## 12. Zakres danych TFD

TFD powinno docelowo pokazywać dane potrzebne do późniejszej analizy ujęcia, montażu i efektów specjalnych.

Podstawowy zakres:

```text
- numer TAKE,
- TC / czas ujęcia,
- impulsy dla 6 osi,
- stany 6 osi,
- wszystkie istotne stany czujników z PAR,
- natężenie światła,
- krańcówki,
- alarmy,
- status ruchu, np. STOP / PLAY / REC / PAUSE,
- stany komunikacji, np. COM OFF / SENSOR OFF,
- marker CLAP.
```

---

## 13. Osie TARZANA w TFD

TFD powinno używać pełnego nazewnictwa osi zgodnego z projektem TARZAN:

```text
- oś pozioma kamery,
- oś pionowa kamery,
- oś pochyłu kamery,
- oś ostrości kamery,
- oś pionowa ramienia,
- oś pozioma ramienia.
```

Dla każdej osi można pokazać na przykład:

```text
- liczba impulsów,
- kierunek DIR,
- aktywność STEP,
- ENABLE,
- stan krańcówki,
- status osi.
```

---

## 14. Próbkowanie, pakiety i odświeżanie

Protokół ruchu TARZANA i TAKE może nadal pracować z krokiem:

```text
10 ms
```

Ale TFD overlay nie powinien być bezpośrednio odświeżany co 10 ms.

Lepszy model:

```text
SignalBus / PAR / TAKE / osie / czujniki
        ↓
TFD Collector zbiera lub czyta stan
        ↓
TFD Packet Builder buduje paczki
        ↓
OBS / Nextion dostają paczki okresowo
```

Rekomendacja:

```text
Warstwa ruchu / TAKE / analiza: 10 ms.
Warstwa TFD / OBS / Nextion: paczki, np. 40–50 ms na start.
```

Możliwe rytmy:

```text
33 ms  ≈ 30 FPS
40 ms  = 25 FPS
50 ms  = 20 FPS
100 ms = spokojny panel diagnostyczny
```

Dla startu TFD rekomendowane jest:

```text
40–50 ms
```

Dla bardzo spokojnego podglądu można użyć:

```text
100 ms
```

Zasada:

```text
TFD nie pompuje każdej próbki 10 ms do overlayu.
TFD pakuje stan i wysyła czytelne paczki do odbiorników.
```

---

## 15. Przykładowy pakiet danych TFD

Przykładowa ramka danych:

```json
{
  "system": "TARZAN_FRAME_DATA",
  "short": "TFD",
  "packet_id": 18421,
  "take": "TAKE_003",
  "tc": "00:01:24:120",
  "time_ms": 84210,
  "sample_range_ms": [84180, 84210],
  "light": 72,
  "motion_status": "REC",
  "axes": {
    "os_pozioma_kamery": {
      "label": "oś pozioma kamery",
      "impulses_total": 1240,
      "step_count_in_packet": 3,
      "dir": 1,
      "step": 0,
      "enable": 1,
      "status": "OK"
    },
    "os_pionowa_kamery": {
      "label": "oś pionowa kamery",
      "impulses_total": 830,
      "step_count_in_packet": 2,
      "dir": -1,
      "step": 1,
      "enable": 1,
      "status": "OK"
    },
    "os_pochylu_kamery": {
      "label": "oś pochyłu kamery",
      "impulses_total": 210,
      "step_count_in_packet": 0,
      "dir": 0,
      "step": 0,
      "enable": 1,
      "status": "OK"
    },
    "os_ostrosci_kamery": {
      "label": "oś ostrości kamery",
      "impulses_total": 455,
      "step_count_in_packet": 1,
      "dir": 1,
      "step": 0,
      "enable": 1,
      "status": "OK"
    },
    "os_pionowa_ramienia": {
      "label": "oś pionowa ramienia",
      "impulses_total": 3010,
      "step_count_in_packet": 5,
      "dir": 1,
      "step": 1,
      "enable": 1,
      "status": "OK"
    },
    "os_pozioma_ramienia": {
      "label": "oś pozioma ramienia",
      "impulses_total": 2875,
      "step_count_in_packet": 4,
      "dir": -1,
      "step": 0,
      "enable": 1,
      "status": "OK"
    }
  },
  "sensors": {
    "limit_camera_horizontal_left": 0,
    "limit_camera_horizontal_right": 0,
    "light_sensor": 72,
    "emergency_stop": 0
  },
  "events": []
}
```

---

## 16. Przykładowy marker CLAP w TFD

W momencie naciśnięcia przycisku CLAP można wysłać osobny pakiet zdarzenia:

```json
{
  "system": "TARZAN_FRAME_DATA",
  "short": "TFD",
  "take": "TAKE_003",
  "tc": "00:00:00:000",
  "time_ms": 0,
  "event": {
    "type": "CLAP",
    "source": "NEXTION_TAKE_MAIN",
    "label": "TAKE_START_MARKER"
  }
}
```

Albo dodać marker CLAP do bieżącej paczki:

```json
{
  "take": "TAKE_003",
  "tc": "00:00:00:000",
  "clap": 1,
  "clap_source": "NEXTION_TAKE_MAIN"
}
```

Preferowany model docelowy:

```text
CLAP jako event / marker w TFD i TAKE.
```

---

## 17. Zasady projektowe

Przy implementacji TFD obowiązują następujące zasady:

```text
1. TFD jest odbiornikiem i prezentacją danych.
2. TFD nie steruje osiami.
3. TFD nie zmienia SignalBus.
4. TFD nie zastępuje PAR.
5. TFD nie zastępuje Nextiona.
6. TFD nie zmienia mechaniki osi.
7. TFD nie zmienia generatora protokołu ruchu.
8. TFD ma być lekkie i odświeżane okresowo.
9. TFD ma działać jako kopia stanu do obrazu filmowego.
10. TFD ma być przydatne w montażu i efektach specjalnych.
11. CLAP jest jedynym dodatkowym markerem TFD spoza danych PAR / SignalBus / TAKE / osi / czujników.
12. CLAP nie steruje ruchem — tylko oznacza synchronizację początku TAKE.
```

---

## 18. Granice pierwszej implementacji

Pierwsza implementacja TFD powinna być mała i bezpieczna.

Zakres:

```text
WARSTWA:
TFD / overlay / prezentacja danych / kopia danych do OBS i Nextion take_main

NIE RUSZAM:
mechaniki osi
generatora protokołu
EHR
TAKE save/load
logiki sterowania ruchem
istniejącego działania PAR
istniejącego działania RRP

KONTRAKT ZOSTAJE:
SignalBus / PAR / TAKE / osie / czujniki są źródłem prawdy
TFD pokazuje tylko kopię danych
CLAP jest jedynym dodatkowym markerem synchronizacji

ZMIENIAM TYLKO:
dodanie eksportera TFD
dodanie lokalnego kanału danych live
dodanie overlayu do OBS
dodanie kopii podglądowej do Nextion take_main
dodanie przycisku CLAP w take_main
dodanie obsługi markera CLAP
```

---

## 19. Proponowane nazwy elementów implementacji

Robocze nazwy plików / modułów:

```text
tarzan_tfd_exporter.py
tarzan_tfd_server.py
tarzan_tfd_packet.py
tarzan_tfd_overlay.html
tarzan_tfd_overlay.css
tarzan_tfd_overlay.js
```

Robocza nazwa kanału:

```text
/tfd
```

Robocza nazwa zdarzenia:

```text
CLAP
```

Robocza komenda z Nextiona:

```text
take:clap=1
```

---

## 20. Podsumowanie

**TARZAN FRAME DATA** to techniczna warstwa danych nakładana na obraz filmowy z kamery zamontowanej na ramieniu TARZANA.

TFD ma pomóc w analizie ujęcia, montażu i efektach specjalnych, ponieważ razem z obrazem pokazuje stan osi, czujników, światła, TAKE i TC.

Te same dane TFD mają iść do:

```text
- OBS jako overlay,
- Nextion take_main jako fizyczny podgląd TAKE / TFD.
```

Dodatkowo w Nextion `take_main` ma powstać przycisk:

```text
CLAP
```

CLAP oznacza początek TAKE i daje synchronizację:

```text
obraz + dźwięk + dane TFD + TAKE.
```

Najważniejsza zasada:

```text
TFD jest kopią danych przypisaną do obrazu.
Źródłem prawdy pozostaje TARZAN: SignalBus / PAR / TAKE / osie / czujniki.
Jedyny dodatkowy marker TFD to CLAP.
```
