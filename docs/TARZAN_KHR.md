# TARZAN – KHR / Korektor Choreografii Ruchu

## Definicja

KHR steruje gęstością impulsów STEP przez korektę natężenia ruchu A(t), co w protokole objawia się zagęszczaniem lub rozrzedzaniem sekwencji 0/1.

## Warstwy

```text
EHR / TAKE / manual
↓
A_base(t)
↓
KHR + pluginy
↓
A_final(t)
↓
generator STEP/DIR
↓
protokół 10 ms
```

## Profile KHR

Profile zapisane są w:

```text
data/khr/khr_settings.json
```

Dostępne profile:

```text
CINEMA      miękki ruch filmowy
STABLE      bardzo stabilny kadr
FOLLOW      zrównoważone podążanie
FAST        szybka reakcja
AGGRESSIVE  mocne testowe śledzenie
```

## Parametry

- dead_zone_px — martwa strefa, ignoruje mikrodrgania
- gain — siła korekty
- smooth — szybkość dochodzenia do korekty
- max_correction — maksymalna korekta A(t)
- max_delta_per_tick — maksymalna zmiana korekty w jednym ticku 10 ms
- prediction — lekkie wyprzedzenie ruchu obiektu
- damping — tłumienie oscylacji
- lost_target_decay — wygaszanie korekty po utracie celu

## Zasada krytyczna

Plugin nie steruje osią.
Plugin daje tylko korektę A(t).
Generator STEP/DIR pozostaje osobną warstwą.
