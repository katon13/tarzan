HARWARE — AUTOMATYKA

# TARZAN — AUTOMATYKA / PLAY P37 / BEZPIECZEŃSTWO RĘCZNEGO NAGRYWANIA RAMIENIA

## 1. Sygnał krytyczny

```text
nazwa: play_p37_step_disconnect_manual
płytka: PLAY
pin: 37
opis: Odłączenie przewodów/sygnałów silników krokowych osi poziomej i pionowej w trybie ręcznego nagrywania ramienia.
rola: sygnał bezpieczeństwa mechaniki ramienia
```

Ten sygnał nie jest zwykłym testem. To jest zabezpieczenie przed podaniem prądu / zwarciem / prądem zwrotnym na sterowniki silników podczas ręcznego ruszania ramieniem.

## 2. Zasada główna

```text
Jeżeli jest tryb ręcznego nagrywania ramienia:
PLAY P37 musi być WYSOKI.
```

Wysoki stan na PLAY P37 oznacza:

```text
sterowniki silników krokowych są odłączone,
ramię można prowadzić ręcznie,
automatyka nie steruje osiami ramienia.
```

## 3. Tryb AUTOMATYKA

```text
AUTOMATYKA aktywna
PLAY P37 = niski
sterowniki silników mogą być aktywne
nie wolno ręcznie ruszać ramieniem
LED z piorunem w PAR = czerwony
```

Znaczenie:

```text
system może pracować automatycznie,
ręczne poruszanie ramieniem jest zabronione,
bo sterowniki mogą trzymać prąd / pozycję.
```

## 4. Tryb NAGRYWANIE RAMIENIA / ręczne prowadzenie

```text
NAGRYWANIE RAMIENIA aktywne
PLAY P37 = wysoki
sterowniki silników krokowych są odłączone
automatyka = szara / nieaktywna
ramię można prowadzić ręcznie
```

Znaczenie:

```text
operator może fizycznie poruszać ramieniem,
bo sterowniki osi poziomej i pionowej są odcięte.
```

## 5. Zasada bezpieczeństwa

```text
Nigdy nie wolno ręcznie ruszać ramieniem, gdy automatyka jest aktywna i PLAY P37 nie odcina sterowników.
```

To jest krytyczna zasada mechaniczna TARZANA.

## 6. Test w PAR

Test ma być wykonywany przez panel / przycisk AUTOMATYKA w PAR.

Tor testu:

```text
PAR
→ TarzanParBridge
→ TSP miniPC
→ SignalBus miniPC
→ HardwareBridge / Snajper
→ PLAY P37
→ fizyczny stan odłączenia sterowników
```

Nie wolno robić obejścia lokalnego w PAR.

## 7. Zachowanie UI w PAR

### Automatyka aktywna

```text
LED z piorunem = czerwony
opis: NIE RUSZAĆ RĘCZNIE RAMIENIEM
PLAY P37 = niski
```

### Nagrywanie ręczne ramienia

```text
automatyka = szara / wyłączona
opis: SILNIKI ODŁĄCZONE — RUCH RĘCZNY DOZWOLONY
PLAY P37 = wysoki
```

## 8. Co ma być sprawdzane

Przycisk AUTOMATYKA w PAR ma sprawdzać i pokazywać:

```text
1. obecny stan PLAY P37,
2. czy automatyka jest aktywna,
3. czy ręczne nagrywanie ramienia jest dozwolone,
4. czy sterowniki silników są odłączone,
5. czy UI pokazuje właściwy stan bezpieczeństwa.
```

## 9. Model dla dalszych elementów TARZANA

Ta zasada ma być wzorem dla kolejnych elementów:

```text
każdy element ma mieć jasny sygnał,
każdy test ma mieć jasny stan bezpieczeństwa,
każde sterowanie ma iść przez PAR → Bridge → TSP → miniPC → HardwareBridge/Snajper,
każdy etap kończy się testem na fizycznym elemencie.
```

## 10. Status implementacyjny

```text
Do zrobienia:
ETAP 1U — AUTOMATYKA / PLAY P37 safety test

Zakres:
- sprawdzić obecny panel AUTOMATYKA w PAR,
- przepiąć test na play_p37_step_disconnect_manual,
- dodać jasne stany UI,
- dodać logi PAR,
- wykonać fizyczny test przez miniPC,
- nie mieszać tego ze STEP/DIR osi.
```
