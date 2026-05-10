# KIJANKA — kompletna autorska koncepcja techniczna v2

## 1. Wizja produktu
KIJANKA to aktywny wózek kamerowy, który ma skrócić czas przygotowania ujęcia na planie filmowym.
Nie zastępuje całego TARZAN-a — jest jego bazą jezdną i stabilizującą.

## 2. Fundamentalna decyzja projektowa
Rozdzielam układ na 3 niezależne warstwy:
1. przejazd bazowy po planie,
2. aktywna kompensacja nierówności,
3. ruch właściwy kamery realizowany przez TARZAN.

To rozdzielenie jest kluczowe — dzięki temu układ nie miesza funkcji i jest łatwiejszy do sterowania.

## 3. Konstrukcja bazowa
Przyjmuję jedną sztywną płytę dolną z aluminium 20 mm jako główną bazę geometryczną i montażową.
Do niej mocowane są:
- 4 moduły kompensacyjne kół,
- napęd przejazdu po pasie referencyjnym,
- elektronika i zasilanie,
- centralny punkt IMU.

## 4. Przejazd
Ruch przód–tył realizuje silnik krokowy z przekładnią, współpracujący z pasem referencyjnym mocowanym do podłoża na odcinku około 10 m.
To daje:
- powtarzalność,
- prostą logistykę planową,
- szybszy setup niż klasyczne szyny.

## 5. Moduły kół
Każde koło ma osobny moduł:
- koło poliamidowe 160 mm,
- wahacz z punktem obrotu,
- serwo 750 W z enkoderem i hamulcem,
- przekładnia planetarna 5:1,
- śruba kulowa 1605,
- popychacz z przegubem kulowym,
- skok roboczy ~100 mm.

## 6. Dlaczego taki wybór
### 6.1 Serwo zamiast krokowca przy kompensacji
Bo kompensacja ma czasem działać energicznie, a nie tylko statycznie trzymać.
### 6.2 Brak ślimaka
Ślimak dawałby trzymanie, ale zabiera dynamikę i komplikuje układ.
To zastępuję hamulcem fail-safe.
### 6.3 Śruba kulowa
Daje wysoką sprawność i precyzyjny ruch liniowy.
### 6.4 Wahacz
Pozwala uprościć geometrię i nie wymaga pełnych szyn liniowych.

## 7. Sterowanie
Przyjmuję architekturę warstwową:
- lokalna pętla serwo/enkoder/hamulec,
- centralna pętla kompensacji z IMU,
- nadrzędna logika TARZAN / EHR / TAKE.

## 8. Założenia wymiarowe przyjęte autorsko
- gabaryt płyty nośnej: 1180 x 760 mm
- rozstaw osi modułów (centra stref S1–S4): 860 x 470 mm
- koło: ø160 mm
- długość wahacza P0–oś koła: 235 mm
- długość P0–P2: 145 mm
- skok śruby: 100 mm
- zakres kompensacji koła: ~70 mm efektywnie
- wysokość bazy nad podłożem: ok. 180–240 mm zależnie od położenia kół

## 9. Założenia eksploatacyjne
- praca na planach z umiarkowanymi nierównościami,
- szybki montaż pasa referencyjnego,
- możliwość powtarzalnego przejazdu,
- stabilizacja bazy przed dalszym ruchem kamery.

## 10. Kolejność budowy
1. wykonać bazę dolną,
2. wykonać 1 moduł koła,
3. uruchomić moduł na stanowisku,
4. dodać napęd przejazdu,
5. zbudować pełny wózek,
6. zintegrować z TARZAN.

## 11. Moja ocena koncepcji
To jest sensowny i wykonalny kierunek prototypu.
Największą wartością nie jest sama mechanika, lecz skrócenie czasu gotowości planu i powtarzalność ujęć.

## 12. Świadome ograniczenie
To nadal jest koncepcja techniczna, a nie finalny komplet produkcyjny CNC.
Ale jest wystarczająco konkretna, żeby na niej budować realny prototyp i później go skorygować.
