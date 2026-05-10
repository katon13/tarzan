# KIJANKA_naped_przejazdu_10m.md
# KIJANKA — napęd przejazdu po pasie referencyjnym 10 m
## Dokument techniczny roboczy

## 1. Cel dokumentu

Ten dokument opisuje założenia techniczne dla głównego napędu przejazdu systemu KIJANKA.

Napęd przejazdu ma realizować:
- ruch przód–tył,
- wysoką powtarzalność pozycji,
- możliwość odtwarzania przejazdów,
- współpracę z logiką TARZAN / EHR / TAKE.

To jest osobny podsystem względem aktywnej kompensacji kół.

---

## 2. Główna rola napędu przejazdu

Napęd przejazdu odpowiada za:
- precyzyjne przemieszczanie wózka po planie,
- utrzymanie zadanej trajektorii ruchu bazowego,
- możliwość wielokrotnego odtwarzania tego samego ujęcia.

Napęd przejazdu **nie odpowiada** za:
- kompensację lokalnych nierówności,
- korekcję przechyłu platformy,
- ruchy ramienia i kamery.

To oznacza ścisły podział:
- napęd przejazdu = ruch liniowy po planie,
- moduły kół = kompensacja,
- osie TARZAN = ruchy kamery i ramienia.

---

## 3. Założenie podstawowe

Przejazd ma być realizowany przez:

- silnik krokowy napędu głównego,
- przekładnię,
- element napędzający współpracujący z pasem zębatym,
- pas referencyjny mocowany do podłoża,
- długość roboczą około **10 m**.

Pas pełni rolę odniesienia liniowego dla przejazdu i ma zastąpić klasyczne ciężkie szyny w zakresie powtarzalności ruchu.

---

## 4. Dlaczego pas referencyjny

Pas referencyjny daje kilka przewag praktycznych:

- szybki montaż na planie,
- niższa masa i objętość niż klasyczne szyny,
- łatwiejszy transport,
- możliwość precyzyjnego przejazdu,
- prostsza integracja z napędem krokowym.

To jest rozwiązanie ukierunkowane na skrócenie czasu przygotowania zdjęć.

---

## 5. Architektura napędu przejazdu

## 5.1. Główne elementy
Układ powinien zawierać:

1. silnik krokowy  
2. przekładnię  
3. uchwyt silnika  
4. koło napędowe / element współpracy z pasem  
5. układ prowadzenia i napięcia pasa  
6. mocowanie pasa do podłoża  
7. czujnik referencyjny / pozycja startowa  
8. sterownik napędu  
9. integrację z systemem nadrzędnym

## 5.2. Zasada działania
- pas jest zamocowany do podłoża,
- napęd wózka współpracuje z tym pasem,
- obrót silnika przekłada się na przesuw całego wózka,
- układ jest sterowany pozycją i profilem ruchu,
- ruch może być zapisywany i odtwarzany.

---

## 6. Wymagania funkcjonalne napędu przejazdu

Napęd przejazdu powinien zapewnić:

### 6.1. Precyzję
- powtarzalny start i stop
- przewidywalną pozycję
- brak wyraźnego przeskoku i szarpania

### 6.2. Płynność
- płynny rozruch
- płynne hamowanie
- możliwość różnych profili prędkości

### 6.3. Bezpieczeństwo
- zatrzymanie awaryjne
- zatrzymanie kontrolowane
- zabezpieczenie przed utratą zazębienia
- zabezpieczenie przed nadmiernym luzem pasa

### 6.4. Praktyczność planowa
- szybki montaż pasa
- powtarzalne napięcie
- łatwa kontrola długości roboczej
- łatwe przeniesienie na inny plan

---

## 7. Silnik napędu przejazdu

## 7.1. Rola silnika
Silnik ma realizować precyzyjny ruch liniowy z dużą powtarzalnością.

## 7.2. Kierunek przyjęty roboczo
Na obecnym etapie sensowne jest:
- zastosowanie silnika krokowego,
- z przekładnią,
- do współpracy z pasem na długim dystansie.

## 7.3. Dlaczego krokowy
W tym podsystemie krokowiec nadal ma sens, ponieważ:
- ruch jest w dużej mierze przewidywalny,
- łatwo go zintegrować z profilami pozycyjnymi,
- dobrze współpracuje z odtwarzaniem choreografii,
- precyzja bazowa przejazdu jest ważniejsza niż bardzo agresywne korekty.

---

## 8. Przekładnia napędu przejazdu

Przekładnia ma:
- dopasować moment silnika,
- poprawić kulturę pracy,
- odciążyć silnik,
- poprawić zakres użytecznej prędkości.

Przy doborze przekładni trzeba znaleźć kompromis między:
- momentem,
- rozdzielczością ruchu,
- prędkością maksymalną przejazdu,
- płynnością.

---

## 9. Pas referencyjny 10 m

## 9.1. Rola pasa
Pas jest liniowym odniesieniem mechanicznym dla ruchu wózka.

## 9.2. Wymagania dla pasa
- odpowiednia sztywność
- odpowiednia długość
- odporność na uszkodzenia planowe
- stabilność geometryczna
- łatwy montaż do podłoża

## 9.3. Punkty mocowania pasa
Pas powinien mieć:
- punkt początkowy,
- punkt końcowy,
- możliwość naciągu,
- możliwość szybkiego mocowania do podłoża,
- możliwość pośredniego zabezpieczenia przed falowaniem.

## 9.4. Uwaga praktyczna
Największym ryzykiem nie jest sam napęd, tylko:
- niewłaściwe napięcie pasa,
- złe mocowanie do podłoża,
- utrata prostoliniowości odniesienia.

To trzeba uwzględnić już w projekcie planowym.

---

## 10. Mocowanie pasa do podłoża

To jest jeden z najważniejszych tematów wdrożeniowych.

System mocowania pasa powinien być:
- szybki,
- powtarzalny,
- prosty w obsłudze,
- możliwy do zastosowania w różnych warunkach planu.

Przykładowe kierunki:
- kotwy tymczasowe,
- płyty bazowe,
- listwy dociskowe,
- szybkozłącza montażowe,
- odcinkowe punkty stabilizujące.

To wymaga później osobnego dokumentu wykonawczego.

---

## 11. Pozycja referencyjna i bazowanie

Napęd przejazdu musi mieć przewidziany sposób bazowania.

System powinien mieć:
- punkt referencyjny,
- procedurę startową,
- możliwość ustawienia pozycji zero,
- powtarzalny sposób kalibracji odcinka roboczego.

To jest niezbędne do współpracy z EHR / TAKE.

---

## 12. Profil ruchu

Napęd przejazdu powinien obsługiwać:
- ruch bardzo wolny,
- ruch roboczy standardowy,
- łagodne wejście i wyjście z ruchu,
- profile przyspieszenia i hamowania,
- odtwarzanie zapisanych przejazdów.

To jest ważne, bo w praktyce zdjęciowej liczy się nie tylko pozycja, ale też charakter ruchu.

---

## 13. Integracja z EHR / TAKE

Napęd przejazdu powinien być traktowany jak pełnoprawna oś ruchu w logice systemu.

Powinien umożliwiać:
- zapis przejazdu,
- przypisanie przejazdu do ujęcia,
- odtworzenie przejazdu,
- synchronizację z pozostałymi osiami,
- ręczną i automatyczną korektę parametrów.

To jest jeden z głównych powodów, dla których napęd musi być projektowany od razu jako element systemowy.

---

## 14. Minimalny zakres testów napędu przejazdu

### Test 1 — test pasa
- montaż i napięcie
- utrzymanie linii
- powtarzalność mocowania

### Test 2 — test napędu bez obciążenia
- płynność rozruchu
- płynność hamowania
- zachowanie przy różnych prędkościach

### Test 3 — test przejazdu z wózkiem
- pozycjonowanie
- powtarzalność przejazdu
- wpływ kompensacji kół na ruch bazowy

### Test 4 — test odtworzenia
- zapis przejazdu
- powtórzenie tego samego ruchu
- porównanie błędu końcowego

---

## 15. Otwarte decyzje techniczne

Do doprecyzowania:
- dokładny model silnika,
- dokładny typ przekładni,
- dokładny typ pasa,
- geometria mocowania pasa do podłoża,
- system napinania,
- system bazowania i referencji,
- osłony i bezpieczeństwo pracy na planie.

---

## 16. Wniosek

Napęd przejazdu po pasie 10 m jest jednym z kluczowych elementów wyróżniających KIJANKA.

To on ma zapewnić:
- precyzję przejazdu,
- powtarzalność ujęć,
- szybsze przygotowanie planu niż klasyczne szyny.

Dalsze prace powinny iść w stronę:
- doprecyzowania mocowania pasa,
- doboru napędu,
- integracji z systemem choreografii ruchu.
