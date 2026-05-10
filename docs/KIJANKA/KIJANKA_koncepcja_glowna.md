# KIJANKA — kompletna koncepcja i pakiet rysunków technicznych roboczych
## Wersja: robocza produkcyjna v1
## Tryb opracowania: jak do realnego wykonania prototypu

## 1. Cel
Ten pakiet jest przygotowany tak, jakbym miał sam prowadzić wykonanie pierwszego prototypu KIJANKA.

Założenie praktyczne:
- nie budujemy teraz dokumentacji idealnej pod seryjną produkcję,
- budujemy **pakiet do wykonania pierwszego prototypu produkcyjnego**,
- priorytetem jest: **szybkość dojścia do działającej mechaniki**, a nie formalna kompletność.

## 2. Czym jest KIJANKA
KIJANKA to:
**aktywny wózek kamerowy z pasem referencyjnym i kompensacją wysokości kół**

Podział funkcji:
- przejazd przód–tył: osobny napęd po pasie zębatym mocowanym do podłoża
- kompensacja nierówności: osobne moduły przy kołach
- osie TARZAN: dalsza stabilizacja i choreografia ruchu kamery

Najważniejszy sens:
**oszczędność czasu na planie zdjęciowym**
przez:
- szybsze ustawienie przejazdu
- mniejszą potrzebę klasycznych szyn
- lepszą powtarzalność
- integrację z EHR / TAKE

## 3. Fundament mechaniczny
Bazą konstrukcji jest wycinana z aluminium 20 mm płyta dolna.
Aktualny materiał wejściowy wskazuje:
- wykorzystanie około 1/2 arkusza 1250 x 2500 mm
- centralny korpus nośny
- 4 strefy narożne pod moduły kół
- komplet dodatkowych detali wycinanych z tej samej płyty

Ta płyta powinna być traktowana jako:
**KB-01 — baza nośna dolna KIJANKA**

## 4. Założona architektura mechaniczna
### 4.1. Napęd przejazdu
- silnik krokowy z przekładnią
- pas zębaty mocowany do podłoża, długość robocza około 10 m
- pozycjonowanie i powtarzalny przejazd

### 4.2. Moduły kompensacji koła
Dla każdego koła:
- serwo z enkoderem
- hamulec bezpieczeństwa
- przekładnia
- śruba kulowa
- popychacz z przegubem
- ramię / wahacz koła

### 4.3. Logika układu
- przejazd ma być powtarzalny
- kompensacja ma wyrównywać nierówności
- kompensacja nie zastępuje osi TARZAN
- kompensacja odciąża dalszą stabilizację

## 5. Dlaczego tak
Nie buduję tego jak klasyczny wózek na ciężkich szynach, bo:
- szyny zabierają czas
- poziomowanie zabiera czas
- transport zabiera czas
- rozstawienie zabiera czas

Tutaj precyzja ma pochodzić z:
- pasa referencyjnego
- kontroli napędu
- aktywnej kompensacji

## 6. Główne zespoły do wykonania
1. baza nośna dolna
2. komplet detali z tej samej płyty
3. 4 moduły kół
4. napęd przejazdu
5. zasilanie i sterowanie
6. czujniki i bezpieczeństwo
7. integracja z TARZAN

## 7. Jak bym to robił
### Etap 1
Zamrożenie geometrii bazy dolnej i stref montażowych.

### Etap 2
Zrobienie jednego modułu koła na stanowisku testowym.

### Etap 3
Sprawdzenie:
- siły
- zakresu
- hamulca
- reakcji serwa
- pracy śruby kulowej

### Etap 4
Dopiero potem pełna rama 4-kołowa.

### Etap 5
Napęd przejazdu z pasem referencyjnym.

### Etap 6
Integracja sterowania i testy EHR / TAKE.

## 8. Co jest krytyczne
- geometria punktu pchania dźwigni
- osiowość śruby
- luz w przekładni i popychaczu
- działanie hamulca po zaniku zasilania
- mocowanie pasa do podłoża
- dostęp serwisowy

## 9. Co celowo zostawiam jako robocze
Na tym etapie nie zamykam jeszcze:
- finalnych średnic osi
- finalnej długości śruby
- finalnego modelu przekładni
- finalnych tolerancji warsztatowych
- finalnych uchwytów przewodów

To ma zostać dopięte po prototypie jednego koła.

## 10. Wniosek
To jest pakiet opracowany tak, żeby dało się przejść do realnego prototypu.
Nie jest to jeszcze komplet finalnych rysunków warsztatowych 1:1,
ale jest to **prawdziwa baza wykonawcza** do rozpoczęcia pracy.
