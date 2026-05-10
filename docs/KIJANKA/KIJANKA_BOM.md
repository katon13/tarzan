# KIJANKA_BOM.md
# KIJANKA — BOM / lista części
## Dokument roboczy do przygotowania produkcji prototypu

## 1. Cel dokumentu

Ten dokument porządkuje listę głównych zespołów, podzespołów i materiałów dla pierwszego prototypu systemu **KIJANKA**.

To nie jest jeszcze finalna lista zakupowa pod zamówienie seryjne.  
To jest **BOM roboczy prototypu**, którego celem jest:
- podział konstrukcji na zespoły,
- wskazanie elementów krytycznych,
- przygotowanie zakupów i wyceny,
- przygotowanie dalszej dokumentacji technicznej.

---

## 2. Struktura BOM

BOM podzielono na 8 głównych grup:

1. Rama bazowa wózka  
2. Moduły kół kompensacyjnych  
3. Napęd przejazdu po pasie referencyjnym  
4. Zasilanie i dystrybucja energii  
5. Sterowanie i napędy  
6. Czujniki i bezpieczeństwo  
7. Okablowanie i połączenia  
8. Obróbka, wykończenie i montaż

---

## 3. BOM główny

## 3.1. Rama bazowa wózka

### Zespół RB-01 — rama główna
- płyta / płyty nośne z aluminium
- elementy boczne nośne
- belki usztywniające
- punkty montażowe modułów kół
- punkty montażowe napędu przejazdu
- punkty montażowe elektroniki
- punkty montażowe osłon

### Zespół RB-02 — detale montażowe ramy
- dystanse
- kątowniki montażowe
- płytki mocujące
- obejmy
- wsporniki pod zasilacze i sterowniki
- śruby, podkładki, nakrętki samokontrujące

### Zespół RB-03 — obróbka ramy
- wycięcie detali aluminiowych 20 mm
- frezowanie otworów i gniazd
- gwintowanie
- toczenia wybranych osi i tulei
- anodowanie / wykończenie powierzchni

---

## 3.2. Moduły kół kompensacyjnych

### Zespół MK-01 — koło nośne
Na 1 moduł:
- 1x koło poliamidowe łożyskowane walcowe
- 1x oś koła
- 2x łożyska lub gotowy zespół łożyskowany
- 1x komplet tulei dystansowych
- 1x zabezpieczenie osi

Na cały wózek:
- 4x koło poliamidowe łożyskowane
- 4x oś koła
- 4 komplety łożysk / dystansów / zabezpieczeń

### Zespół MK-02 — ramię / wahacz koła
Na 1 moduł:
- 1x ramię koła
- 1x punkt obrotu ramienia
- 1x oś obrotu ramienia
- 2x elementy łożyskowania lub ślizgu
- 1x ogranicznik mechaniczny zakresu pracy

Na cały wózek:
- 4 komplety ramion i punktów obrotu

### Zespół MK-03 — mechanizm pchający
Na 1 moduł:
- 1x śruba kulowa
- 1x nakrętka śruby kulowej
- 1x tuleja / wózek pchający
- 1x końcówka przegubowa / widełki / ucho
- 1x wspornik mocowania śruby
- 1x wspornik mocowania nakrętki / popychacza

Na cały wózek:
- 4 komplety mechanizmu liniowego

### Zespół MK-04 — napęd modułu koła
Na 1 moduł:
- 1x serwonapęd z enkoderem
- 1x hamulec bezpieczeństwa
- 1x przekładnia
- 1x sprzęgło
- 1x uchwyt silnika
- 1x uchwyt przekładni
- 1x element połączenia z mechanizmem śruby

Na cały wózek:
- 4 kompletne zespoły napędowe

---

## 3.3. Napęd przejazdu po pasie referencyjnym

### Zespół NP-01 — napęd jazdy
- 1x silnik krokowy napędu głównego
- 1x przekładnia do napędu przejazdu
- 1x sterownik silnika krokowego
- 1x koło zębate napędowe
- 1x koło prowadzące / napinające
- 1x mocowanie silnika

### Zespół NP-02 — pas referencyjny
- 1x pas zębaty o długości około 10 m
- 2x końcówki mocujące do podłoża
- 1x układ naciągu
- 1x zestaw punktów mocowania pośredniego
- 1x osłona / organizacja strefy pasa

### Zespół NP-03 — układ toczenia po podłożu
- 4x koła nośne
- geometria rozstawu kół
- elementy stabilizacji jazdy
- opcjonalne rolki pomocnicze / odbojowe

---

## 3.4. Zasilanie i dystrybucja energii

### Zespół ZE-01 — zasilanie główne
- zasilacz główny do napędów kompensacji
- zasilacz pomocniczy sterowania
- zasilanie hamulców
- bezpieczniki główne
- rozłącznik serwisowy
- awaryjne odcięcie zasilania

### Zespół ZE-02 — rozdział mocy
- listwy rozdzielcze
- moduły bezpiecznikowe
- przewody zasilające
- końcówki oczkowe / tulejkowe
- kanały / uchwyty przewodów

---

## 3.5. Sterowanie i napędy

### Zespół ST-01 — sterowniki osi kompensacyjnych
- 4x driver serwo
- 4x interfejs enkodera
- 4x sterowanie hamulcem
- mocowania driverów

### Zespół ST-02 — sterowanie napędem przejazdu
- 1x driver napędu głównego
- logika pozycjonowania przejazdu
- integracja z systemem TARZAN

### Zespół ST-03 — komputer / elektronika nadrzędna
- sterownik centralny
- interfejs komunikacyjny
- moduły I/O
- obwody awaryjne
- sygnalizacja stanu

---

## 3.6. Czujniki i bezpieczeństwo

### Zespół CZ-01 — czujniki orientacji
- 1x moduł IMU / XYZ
- mocowanie centralne czujnika
- ekranowanie / odsprzężenie mechaniczne

### Zespół CZ-02 — czujniki pozycji
- enkodery w napędach
- krańcówki mechaniczne / elektryczne
- czujniki referencyjne
- czujniki stanu hamulca

### Zespół CZ-03 — bezpieczeństwo
- E-STOP
- kontrola błędu położenia
- kontrola przeciążenia
- kontrola awarii napędu
- logika zatrzymania awaryjnego

---

## 3.7. Okablowanie i połączenia

### Zespół OK-01 — przewody mocy
- przewody zasilające napędy
- przewody zasilające hamulce
- przewody zasilania sterowania

### Zespół OK-02 — przewody sygnałowe
- przewody enkoderów
- przewody czujników
- przewody komunikacyjne

### Zespół OK-03 — osprzęt kablowy
- peszle
- opaski
- uchwyty
- przepusty
- dławnice
- oznaczniki przewodów

---

## 3.8. Obróbka, wykończenie i montaż

### Zespół OB-01 — usługi produkcyjne
- cięcie aluminium
- frezowanie
- wiercenie
- gwintowanie
- toczenie
- montaż próbny
- anodowanie

### Zespół OB-02 — montaż końcowy
- składanie ramy
- montaż mechaniki
- montaż napędów
- montaż elektroniki
- prowadzenie przewodów
- uruchomienie bazowe

---

## 4. BOM ilościowy — poziom uproszczony

### Na 1 wózek KIJANKA
- 1x rama bazowa
- 4x moduł koła kompensacyjnego
- 1x napęd przejazdu po pasie
- 1x pas referencyjny około 10 m
- 1x system zasilania
- 1x system sterowania
- 1x zestaw czujników
- 1x zestaw bezpieczeństwa
- 1x komplet okablowania
- 1x komplet usług obróbczych

### Na 1 moduł koła
- 1x koło
- 1x ramię / wahacz
- 1x serwo z enkoderem
- 1x hamulec
- 1x przekładnia
- 1x śruba kulowa
- 1x nakrętka / popychacz
- 1x komplet wsporników
- 1x komplet osi / tulei / śrub

---

## 5. Elementy krytyczne BOM

Najbardziej krytyczne dla powodzenia prototypu:

### Krytyczne mechanicznie
- geometria modułu koła
- sztywność ramienia
- jakość punktu obrotu
- ochrona śruby kulowej przed siłami bocznymi
- dobór przekładni i sprzęgła

### Krytyczne dynamicznie
- dobór serwonapędu
- dobór przełożenia
- szybkość reakcji układu
- stabilność sterowania kompensacją

### Krytyczne produkcyjnie
- dokładność osi i punktów montażowych
- równoległość i osiowość elementów napędowych
- łatwość serwisu
- czas wykonania pierwszego prototypu

---

## 6. Co musi zostać doprecyzowane przed finalnym BOM zakupowym

Przed przejściem do finalnego arkusza zakupowego trzeba doprecyzować:

- dokładne modele serw
- dokładny typ hamulca
- dokładny typ przekładni
- typ śruby kulowej i jej skok
- średnice osi i wałów
- dokładny model koła
- sposób montażu pasa referencyjnego
- konstrukcję napędu jazdy
- rzeczywiste moce zasilania
- dokładny sterownik centralny

---

## 7. Wniosek

BOM KIJANKA pokazuje, że projekt należy traktować jako złożenie dwóch głównych podsystemów:

1. **precyzyjny przejazd po planie**
2. **aktywna kompensacja wysokości kół**

To rozdzielenie jest kluczowe i powinno zostać utrzymane w całej dalszej dokumentacji technicznej.
