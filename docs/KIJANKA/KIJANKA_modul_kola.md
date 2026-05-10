# KIJANKA_modul_kola.md
# KIJANKA — moduł jednego koła
## Dokument techniczny roboczy

## 1. Cel dokumentu

Ten dokument opisuje jeden aktywny moduł koła systemu KIJANKA.

Moduł jednego koła ma:
- przenosić obciążenie,
- toczyć się po podłożu,
- kompensować nierówności,
- współpracować z logiką stabilizacji,
- nie pełnić funkcji głównego napędu przejazdu.

To jest dokument roboczy do przygotowania pierwszego prototypu modułu.

---

## 2. Funkcja modułu koła

Każdy moduł koła ma odpowiadać za lokalną regulację wysokości punktu podparcia wózka.

Najważniejsze rozróżnienie:
- moduł koła **nie odpowiada za precyzyjny ruch przejazdu po planie**,
- moduł koła **odpowiada za kompensację nierówności i stabilizację platformy bazowej**.

Moduł jest elementem wykonawczym sterowanym na podstawie:
- czujników orientacji,
- logiki stabilizacji,
- sygnałów systemu nadrzędnego TARZAN.

---

## 3. Proponowana architektura modułu

## 3.1. Struktura funkcjonalna

Jeden moduł koła powinien składać się z następujących części:

1. koło nośne  
2. ramię / wahacz koła  
3. punkt obrotu ramienia  
4. serwonapęd z enkoderem  
5. hamulec bezpieczeństwa  
6. przekładnia  
7. śruba kulowa  
8. nakrętka / tuleja pchająca  
9. połączenie przegubowe z ramieniem  
10. mocowanie do ramy wózka

## 3.2. Zasada działania

- koło podtrzymuje wózek,
- koło jest osadzone na wahaczu,
- wahacz obraca się wokół swojego punktu obrotu,
- serwo napędza przez przekładnię śrubę kulową,
- śruba przesuwa nakrętkę / popychacz,
- popychacz naciska na odpowiedni punkt ramienia,
- przez to wysokość koła względem ramy zmienia się,
- układ kompensuje lokalną nierówność.

---

## 4. Wymagania funkcjonalne modułu

Moduł powinien spełnić następujące wymagania:

### 4.1. Wymagania nośne
- przeniesienie średniego obciążenia przypadającego na jedno koło
- zachowanie zapasu na obciążenia nierównomierne
- zachowanie zapasu na chwilowe przeciążenia dynamiczne

### 4.2. Wymagania ruchowe
- możliwość płynnej korekty wysokości
- możliwość korekt spokojnych i energicznych
- brak zacięć w pełnym zakresie pracy
- powtarzalność położenia

### 4.3. Wymagania bezpieczeństwa
- brak niekontrolowanego opadania po zaniku zasilania
- zatrzymanie przez hamulec
- ograniczenie mechaniczne skrajnych położeń
- kontrola błędu położenia

### 4.4. Wymagania serwisowe
- dostęp do śruby
- dostęp do koła
- dostęp do napędu
- łatwa wymiana łożysk / osi / końcówki popychającej

---

## 5. Koło nośne

## 5.1. Rola koła
Koło ma:
- przenosić obciążenie na podłoże,
- zapewniać toczenie,
- współpracować z ramieniem koła.

## 5.2. Wymagania dla koła
- odpowiednia nośność
- odporność na ścieranie
- łożyskowanie
- umiarkowany opór toczenia
- przewidywalne zachowanie na typowych powierzchniach planu

## 5.3. Kierunek roboczy
Na obecnym etapie sensowne są:
- koła poliamidowe łożyskowane
- walcowe
- o konstrukcji przemysłowej

---

## 6. Ramię / wahacz koła

## 6.1. Rola ramienia
Ramię:
- utrzymuje koło,
- przenosi siły między kołem a ramą,
- odbiera ruch od popychacza śruby,
- obraca się wokół ustalonego punktu.

## 6.2. Wymagania dla ramienia
- wysoka sztywność
- odporność zmęczeniowa
- przewidywalna geometria
- niewielkie luzy na punkcie obrotu
- prosty montaż i serwis

## 6.3. Punkt obrotu ramienia
Punkt obrotu musi:
- być sztywny,
- mieć ograniczony luz,
- mieć dobrane łożyskowanie lub ślizg,
- mieć zabezpieczenie osi.

---

## 7. Napęd kompensacyjny

## 7.1. Serwonapęd
Serwo zostało przyjęte jako podstawowy kierunek, ponieważ:
- daje szybszą reakcję niż klasyczny krokowiec,
- ma sprzężenie zwrotne,
- nadaje się do korekt dynamicznych,
- pozwala sterować pozycją i prędkością.

## 7.2. Enkoder
Enkoder ma zapewnić:
- informację o położeniu,
- informację o prędkości,
- możliwość detekcji błędu,
- możliwość dokładniejszej regulacji.

## 7.3. Hamulec
Hamulec ma pełnić funkcję:
- zabezpieczenia po zaniku zasilania,
- podtrzymania pozycji,
- wsparcia bezpieczeństwa mechanicznego.

---

## 8. Przekładnia

## 8.1. Rola przekładni
Przekładnia ma:
- zwiększyć dostępny moment,
- dopasować charakterystykę serwa do śruby,
- poprawić warunki pracy napędu.

## 8.2. Wymagania dla przekładni
- mały luz
- odpowiednia sztywność
- dobra sprawność
- zgodność z dynamiką kompensacji
- łatwy montaż do serwa

## 8.3. Uwaga projektowa
Przekładnia nie powinna nadmiernie spowalniać reakcji układu.  
Moduł ma kompensować, a nie tylko statycznie trzymać.

---

## 9. Śruba kulowa

## 9.1. Rola śruby
Śruba kulowa zamienia ruch obrotowy na ruch liniowy popychacza.

## 9.2. Założenia robocze
- roboczy zakres ruchu około 100 mm
- śruba pracuje osiowo
- śruba nie jest prowadnicą główną
- śruba ma pchać / ciągnąć punkt ramienia

## 9.3. Wymagania
- odpowiednia nośność osiowa
- płynna praca
- mały luz
- możliwość łatwego mocowania
- możliwość osłony przed zabrudzeniem

## 9.4. Bardzo ważna zasada
Śruba powinna pracować głównie **na osi ruchu**, a nie przenosić dużych sił bocznych.  
To oznacza konieczność:
- prawidłowego doboru punktu pchania,
- zastosowania przegubu,
- poprawnej geometrii całego modułu.

---

## 10. Popychacz i połączenie z ramieniem

## 10.1. Rola popychacza
Popychacz:
- odbiera ruch z nakrętki śruby,
- przekazuje siłę na ramię,
- pozwala zmieniać położenie koła.

## 10.2. Zalecane połączenie
Na końcu popychacza powinno znaleźć się:
- ucho,
- widełki,
- albo przegub kulowy.

Celem jest:
- ograniczenie skręcania śruby,
- kompensacja drobnych zmian kąta,
- poprawa trwałości układu.

---

## 11. Zakres ruchu i ograniczniki

Moduł powinien mieć:
- zakres roboczy wynikający z geometrii ramienia,
- ogranicznik dolny,
- ogranicznik górny,
- rezerwę bezpieczeństwa względem krańcówek,
- detekcję położeń skrajnych.

Nie wolno opierać bezpieczeństwa tylko na software.

---

## 12. Siły działające w module

Na moduł działają równocześnie:
- siła pionowa od masy wózka,
- siły od nierówności podłoża,
- siły dynamiczne od przejazdu,
- siły od aktywnej korekty wysokości,
- siły wewnętrzne od popychacza.

To oznacza, że projekt modułu musi rozdzielać:
- przenoszenie obciążeń nośnych,
- realizację ruchu regulacyjnego,
- bezpieczeństwo i ograniczniki.

---

## 13. Co trzeba sprawdzić w pierwszym prototypie modułu

Pierwszy prototyp jednego modułu powinien odpowiedzieć na pytania:

1. Czy geometria punktu pchania jest poprawna?  
2. Czy śruba pracuje osiowo?  
3. Czy ramię ma wystarczającą sztywność?  
4. Czy układ nie ma za dużych luzów?  
5. Czy serwo reaguje wystarczająco szybko?  
6. Czy hamulec skutecznie trzyma moduł?  
7. Czy przy pełnym zakresie pracy nic nie koliduje?  
8. Czy dostęp serwisowy jest akceptowalny?

---

## 14. Minimalny zestaw testów modułu

### Test 1 — test bez obciążenia
- pełen zakres ruchu
- płynność pracy
- brak kolizji
- sprawdzenie krańcówek

### Test 2 — test pod obciążeniem statycznym
- utrzymanie pozycji
- zachowanie hamulca
- pomiar ugięć

### Test 3 — test korekty dynamicznej
- szybka korekta małej zmiany położenia
- obserwacja oscylacji
- obserwacja błędu położenia

### Test 4 — test awaryjny
- zanik zasilania
- zadziałanie hamulca
- zachowanie modułu po zatrzymaniu

---

## 15. Wniosek

Moduł jednego koła KIJANKA należy traktować jako:
**aktywny moduł kompensacyjny**, a nie jako moduł głównego napędu wózka.

Najważniejsze cechy modułu:
- sztywność,
- przewidywalna geometria,
- dobra reakcja napędu,
- bezpieczeństwo przez hamulec,
- poprawna praca śruby kulowej bez nadmiernych sił bocznych.

Ten dokument stanowi bazę do kolejnego kroku:
**doprecyzowania geometrii i punktów montażowych.**
