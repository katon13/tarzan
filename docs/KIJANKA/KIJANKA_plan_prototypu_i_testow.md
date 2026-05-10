# KIJANKA_plan_prototypu_i_testow.md
# KIJANKA — plan prototypu i testów
## Dokument przygotowania wdrożenia

## 1. Cel dokumentu

Ten dokument definiuje plan budowy pierwszego prototypu KIJANKA oraz kolejność testów potrzebnych do zweryfikowania koncepcji.

Celem nie jest od razu budowa wersji finalnej estetycznie dopracowanej.  
Celem jest jak najszybsze dojście do:
- działającego modułu,
- potwierdzenia założeń mechanicznych,
- potwierdzenia sterowalności,
- potwierdzenia sensu całej architektury.

---

## 2. Główna zasada prototypowania

Pierwszy prototyp ma odpowiedzieć na pytanie:

**czy koncepcja KIJANKA realnie przyspieszy pracę na planie i czy jest wykonalna mechanicznie oraz sterowniczo?**

Dlatego prototypowanie musi iść od najważniejszych ryzyk, a nie od pełnego dopracowania obudów i detali wizualnych.

---

## 3. Etapy prototypu

## 3.1. Etap A — moduł jednego koła
Na początku należy zbudować tylko jeden pełny aktywny moduł koła.

Cel:
- sprawdzenie geometrii,
- sprawdzenie śruby,
- sprawdzenie działania serwa,
- sprawdzenie hamulca,
- sprawdzenie sił i zakresu ruchu.

To jest najważniejszy etap.

## 3.2. Etap B — rama testowa
Drugi etap to budowa uproszczonej bazy:
- rama testowa,
- 4 punkty montażowe,
- możliwość zamocowania 1–2 modułów,
- możliwość podania obciążenia.

Cel:
- sprawdzić zachowanie modułów w układzie zbliżonym do rzeczywistego.

## 3.3. Etap C — napęd przejazdu
Osobno należy przygotować:
- odcinek testowy pasa,
- napęd jazdy,
- bazowanie i powtarzalny ruch przejazdu.

Cel:
- potwierdzenie, że precyzyjny ruch po pasie działa niezależnie od kompensacji.

## 3.4. Etap D — integracja
Dopiero po wcześniejszych testach:
- integracja przejazdu,
- integracja modułów,
- czujniki,
- logika sterowania,
- integracja z TARZAN.

---

## 4. Najważniejsze ryzyka do sprawdzenia

### Ryzyko 1 — geometria popychacza
Czy śruba pracuje osiowo i nie dostaje dużych sił bocznych?

### Ryzyko 2 — sztywność ramienia
Czy ramię koła nie ugina się nadmiernie?

### Ryzyko 3 — luz mechaniczny
Czy sumaryczny luz napędu nie będzie za duży dla stabilizacji?

### Ryzyko 4 — reakcja napędu
Czy serwo reaguje wystarczająco szybko?

### Ryzyko 5 — bezpieczeństwo
Czy hamulec skutecznie utrzyma układ po awarii?

### Ryzyko 6 — napęd przejazdu
Czy pas referencyjny daje wymaganą powtarzalność?

---

## 5. Testy modułu jednego koła

## 5.1. Test mechaniczny bez napędu
Cel:
- sprawdzić zakres ruchu,
- sprawdzić kolizje,
- sprawdzić płynność pracy wahacza.

## 5.2. Test mechaniczny z napędem bez obciążenia
Cel:
- sprawdzić ruch śruby,
- sprawdzić popychacz,
- sprawdzić ograniczniki.

## 5.3. Test statyczny pod obciążeniem
Cel:
- sprawdzić utrzymanie pozycji,
- sprawdzić ugięcia,
- sprawdzić zachowanie hamulca.

## 5.4. Test dynamiczny
Cel:
- sprawdzić szybkość korekty,
- sprawdzić oscylacje,
- sprawdzić stabilność działania.

## 5.5. Test awaryjny
Cel:
- sprawdzić zachowanie po odcięciu zasilania,
- sprawdzić pracę hamulca,
- sprawdzić bezpieczeństwo po zatrzymaniu.

---

## 6. Testy napędu przejazdu

## 6.1. Test odcinka pasa
- montaż
- napinanie
- stabilność linii

## 6.2. Test jazdy bez obciążenia
- rozruch
- zatrzymanie
- powtarzalność

## 6.3. Test jazdy z obciążeniem
- płynność
- pozycjonowanie
- wpływ obciążenia na precyzję

## 6.4. Test odtworzenia przejazdu
- zapis przejazdu
- powtórzenie
- porównanie końca i czasu ruchu

---

## 7. Testy integracyjne

Po połączeniu podsystemów należy sprawdzić:

### 7.1. Integrację przejazdu z kompensacją
- czy kompensacja nie psuje płynności przejazdu
- czy przejazd nie destabilizuje kompensacji

### 7.2. Integrację z IMU
- czy korekty wynikają z rzeczywistego przechyłu
- czy nie pojawiają się niepożądane oscylacje

### 7.3. Integrację z TARZAN
- czy ruch można rejestrować
- czy można odtwarzać konfiguracje
- czy system wspiera szybsze przygotowanie ujęcia

---

## 8. Minimalne kryteria zaliczenia prototypu

Prototyp można uznać za obiecujący, jeśli potwierdzi:

1. poprawną geometrię jednego modułu koła  
2. skuteczne działanie śruby i popychacza  
3. skuteczne działanie hamulca  
4. sensowną dynamikę korekt  
5. powtarzalny przejazd po pasie  
6. możliwość dalszej integracji z EHR / TAKE

---

## 9. Plan budowy prototypu — kolejność prac

### Krok 1
Doprecyzować geometrię jednego modułu.

### Krok 2
Zamówić i zbudować jeden moduł koła.

### Krok 3
Uruchomić testy modułu bez pełnego wózka.

### Krok 4
Przygotować odcinek testowy pasa i napęd przejazdu.

### Krok 5
Zbudować prostą ramę testową.

### Krok 6
Zintegrować minimum 1 moduł + przejazd.

### Krok 7
Dopiero potem budować pełny 4-kołowy prototyp.

---

## 10. Dokumentacja testów

Każdy test powinien kończyć się zapisem:
- konfiguracji mechanicznej,
- ustawień sterowania,
- obserwacji,
- błędów,
- decyzji: zostaje / poprawić / odrzucić.

To ważne, bo KIJANKA ma być rozwijana produkcyjnie, a nie tylko koncepcyjnie.

---

## 11. Co powinno powstać po etapie prototypu

Po pierwszym cyklu testów powinny powstać:
- poprawiona geometria,
- poprawiony BOM,
- lista zmian mechanicznych,
- lista zmian sterowania,
- decyzja o wersji V2,
- dokument z wnioskami produkcyjnymi.

---

## 12. Wniosek

Najkrótsza droga do skutecznego prototypu KIJANKA to:
- najpierw moduł jednego koła,
- potem przejazd,
- potem integracja.

To ogranicza ryzyko i pozwala szybko sprawdzić, czy system realnie spełni swój najważniejszy cel:
**przyspieszanie przygotowania ujęcia na planie filmowym.**
