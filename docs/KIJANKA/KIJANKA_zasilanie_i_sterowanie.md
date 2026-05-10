# KIJANKA_zasilanie_i_sterowanie.md
# KIJANKA — zasilanie i sterowanie
## Dokument techniczny roboczy

## 1. Cel dokumentu

Ten dokument opisuje wstępną architekturę zasilania, sterowania i bezpieczeństwa dla systemu KIJANKA.

Celem jest uporządkowanie:
- źródeł zasilania,
- rozdziału mocy,
- sterowania napędami,
- roli hamulców,
- roli enkoderów i czujników,
- relacji między KIJANKA a systemem TARZAN.

---

## 2. Główne założenie architektury

System KIJANKA ma zawierać dwa główne obszary wykonawcze:

1. **napęd przejazdu po pasie referencyjnym**
2. **4 aktywne moduły kompensacyjne kół**

Te dwa obszary muszą być wspólne systemowo, ale rozdzielone funkcjonalnie.

---

## 3. Główne grupy elektryczne

W architekturze należy rozdzielić co najmniej:

### 3.1. Zasilanie mocy napędów
- serwonapędy modułów kół
- napęd przejazdu
- ewentualne przetwornice pomocnicze

### 3.2. Zasilanie sterowania
- sterownik centralny
- logika I/O
- komunikacja
- czujniki

### 3.3. Zasilanie hamulców
- obwody hamulców bezpieczeństwa
- kontrola stanu hamulca
- reakcja na zanik zasilania

### 3.4. Obwody bezpieczeństwa
- E-STOP
- odcięcie mocy
- kontrola błędów
- reakcje awaryjne

---

## 4. Zasilanie napędów kompensacji

## 4.1. Założenie
Każdy moduł koła posiada:
- serwonapęd,
- enkoder,
- hamulec,
- driver.

## 4.2. Wymagania
Układ zasilania napędów kompensacji powinien zapewnić:
- wystarczającą moc chwilową,
- stabilne napięcie,
- odporność na spadki przy równoczesnej pracy osi,
- odpowiednie zabezpieczenie każdego modułu.

## 4.3. Zalecenie architektoniczne
Należy przewidzieć:
- wspólną magistralę mocy,
- oddzielne zabezpieczenie dla każdego napędu,
- centralny punkt odcięcia mocy,
- czytelny podział przewodów mocy i sygnałów.

---

## 5. Zasilanie napędu przejazdu

Napęd przejazdu powinien mieć:
- własny sterownik,
- własne zabezpieczenie,
- wydzieloną logikę ruchu,
- wspólną integrację z systemem głównym.

Nie należy mieszać sterowania przejazdem z lokalnymi pętlami kompensacji.

---

## 6. Hamulce bezpieczeństwa

## 6.1. Rola hamulców
Hamulec w każdym module ma:
- trzymać pozycję po zaniku zasilania,
- zwiększać bezpieczeństwo,
- ograniczać ryzyko niekontrolowanego opadania modułu.

## 6.2. Zasada działania
Hamulec powinien być traktowany jako element bezpieczeństwa, a nie normalnego sterowania ruchem.

Czyli:
- w normalnej pracy hamulec jest zwolniony,
- w stanie awaryjnym hamulec ma zadziałać,
- system musi wykrywać stan hamulca.

## 6.3. Stany awaryjne
Hamulec powinien być sprzęgnięty z:
- zanikiem zasilania,
- E-STOP,
- wykryciem krytycznego błędu osi,
- ewentualnie przekroczeniem warunków bezpieczeństwa.

---

## 7. Enkodery

## 7.1. Rola enkoderów
Enkodery w modułach koła mają zapewnić:
- rzeczywistą informację o położeniu,
- sprzężenie zwrotne dla sterowania,
- możliwość diagnozowania błędu pozycji,
- większą powtarzalność ruchu.

## 7.2. Wymagania systemowe
System sterowania powinien wykorzystywać informację z enkoderów do:
- zamknięcia pętli pozycjonowania,
- diagnostyki,
- kontroli błędów,
- ewentualnego logowania przebiegu ruchu.

---

## 8. Czujnik IMU / XYZ

## 8.1. Rola czujnika
Czujnik IMU / XYZ ma stanowić główne źródło informacji o:
- przechyle platformy,
- zmianach orientacji,
- dynamice ruchu bazowego.

## 8.2. Miejsce montażu
Najlepiej przewidzieć montaż:
- w pobliżu środka geometrycznego bazy,
- na możliwie sztywnej części konstrukcji,
- z uwzględnieniem ograniczenia lokalnych zakłóceń mechanicznych.

## 8.3. Rola w sterowaniu
IMU nie zastępuje enkoderów.  
IMU daje informację globalną o stanie platformy.  
Enkodery dają informację lokalną o wykonaniu ruchu przez napędy.

---

## 9. Sterownik centralny

Sterownik centralny powinien odpowiadać za:
- koordynację napędu przejazdu,
- koordynację modułów kompensacji,
- zbieranie danych z czujników,
- wymianę danych z TARZAN,
- realizację logiki bezpieczeństwa wyższego poziomu,
- logowanie i diagnostykę.

---

## 10. Warstwowanie logiki sterowania

Dla KIJANKA warto zachować trzy warstwy sterowania:

### Warstwa 1 — sterowanie lokalne napędu
- driver serwa
- pętla lokalna położenia / prędkości
- reakcje bezpośrednie

### Warstwa 2 — logika modułu i stabilizacji
- korekty wynikające z geometrii
- kompensacja z IMU
- nadzór nad zakresem pracy

### Warstwa 3 — system nadrzędny
- choreografia przejazdu
- integracja z TAKE
- synchronizacja z osiami TARZAN
- zarządzanie sceną / ujęciem

To pozwala nie mieszać szybkiej automatyki lokalnej z logiką scenariusza ruchu.

---

## 11. Komunikacja

System powinien przewidywać:
- komunikację sterownika centralnego z driverami,
- komunikację z systemem TARZAN,
- możliwość odczytu statusu napędów,
- możliwość logowania alarmów i błędów.

Do doprecyzowania pozostaje konkretny standard komunikacji.

---

## 12. E-STOP i bezpieczeństwo

System bezpieczeństwa powinien przewidywać:
- łatwo dostępny E-STOP,
- odcięcie mocy napędów,
- przejście osi do stanu bezpiecznego,
- automatyczne załączenie hamulców,
- sygnalizację błędu,
- wymuszenie procedury powrotu do pracy po alarmie.

---

## 13. Okablowanie

## 13.1. Podział przewodów
Przewody należy rozdzielić na:
- moc
- sygnały enkoderów
- sygnały czujników
- komunikację
- sterowanie hamulcem

## 13.2. Wymagania montażowe
- przewody nie mogą wchodzić w strefy ruchu,
- trzeba przewidzieć zapasy długości,
- trzeba przewidzieć możliwość serwisu,
- należy ograniczać ryzyko zakłóceń między mocą a sygnałami.

---

## 14. Procedury startowe

System powinien mieć przewidzianą procedurę:
1. uruchomienia zasilania
2. sprawdzenia stanu napędów
3. sprawdzenia stanu hamulców
4. sprawdzenia czujników
5. bazowania napędu przejazdu
6. ustawienia pozycji gotowości modułów

To ma być możliwie szybkie, bo cały sens KIJANKA to skracanie czasu wejścia do pracy.

---

## 15. Tematy do doprecyzowania

Przed finalizacją trzeba ustalić:
- dokładne napięcia systemu,
- rezerwy mocy,
- sposób sterowania hamulcem,
- topologię sterownika centralnego,
- standard komunikacji,
- sposób awaryjnego podtrzymania logiki,
- logikę restartu po błędzie.

---

## 16. Wniosek

Architektura zasilania i sterowania KIJANKA musi być:
- modularna,
- bezpieczna,
- szybka w uruchomieniu,
- czytelnie rozdzielona między przejazd i kompensację.

Najważniejsza zasada:
**lokalne napędy mają wykonywać ruch, ale system nadrzędny ma zarządzać gotowością do pracy na planie.**
