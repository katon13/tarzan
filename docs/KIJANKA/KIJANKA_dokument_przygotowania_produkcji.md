# KIJANKA — aktywny wózek kamerowy TARZAN  
## Dokument przygotowania do produkcji  
### Nazwa robocza rozszerzona: **KIJANKA — aktywny wózek kamerowy z pasem referencyjnym i kompensacją kół**

## 1. Cel dokumentu

Ten dokument porządkuje założenia produkcyjne nowego modułu jezdnego systemu TARZAN, nazwanego roboczo **KIJANKA**.

Nazwa „KIJANKA” wynika z charakteru konstrukcji:
- układ jest niski,
- porusza się po powierzchni płaskiej,
- ma aktywnie kompensować nierówności przez regulację wysokości kół,
- wizualnie i funkcjonalnie przypomina organizm o niskim, szerokim rozstawie i aktywnej pracy kończyn.

Dodatkowa nazwa opisowa:
**aktywny wózek kamerowy z pasem referencyjnym i kompensacją kół**.

To jest dokument **przygotowania produkcji**, a nie tylko notatka koncepcyjna.  
Ma służyć jako punkt startowy do:
- budowy pierwszego egzemplarza,
- zamawiania elementów,
- przygotowania mechaniki,
- określenia architektury napędów,
- powiązania mechaniki z logiką TARZAN / EHR / TAKE.

---

## 2. Główna idea systemu KIJANKA

KIJANKA nie jest klasycznym wózkiem filmowym opartym o ciężkie szyny.

Założenie jest inne:

- główny ruch przejazdu realizowany jest przez **precyzyjny napęd po pasie zębatym** mocowanym do podłoża na długości około **10 metrów**,
- sam wózek ma własne koła i porusza się po powierzchni planu,
- nierówności podłoża nie są niwelowane przez idealne szyny, tylko przez **aktywną kompensację wysokości kół**,
- korekty wysokości mają być realizowane automatycznie, na podstawie czujników położenia / przechyłu XYZ,
- cały układ ma współpracować z systemem TARZAN, aby skracać czas ustawiania ujęcia i przyspieszać pracę na planie filmowym.

Najważniejsza idea praktyczna:

**najdroższy na planie jest czas oczekiwania ludzi na gotowe ujęcie**  
— dlatego KIJANKA ma ograniczać:
- czas poziomowania,
- czas ustawiania wózka,
- czas ręcznego strojenia ruchu,
- czas powtórek technicznych.

---

## 3. Rola KIJANKA w całym systemie TARZAN

KIJANKA ma być elementem większego systemu, a nie niezależnym pojazdem.

Podział funkcji powinien być następujący:

### 3.1. KIJANKA
Odpowiada za:
- fizyczny przejazd po planie,
- aktywną kompensację nierówności,
- utrzymywanie stabilniejszej platformy bazowej.

### 3.2. TARZAN / osie ramienia i kamery
Odpowiadają za:
- ruch kamery,
- ruch ramienia,
- pochył, poziom, ostrość i pozostałe osie systemu.

### 3.3. EHR / TAKE / choreografia ruchu
Odpowiadają za:
- zapis ruchów,
- odtwarzanie przejazdów,
- szybkie powtarzanie ujęć,
- skrócenie czasu przygotowania sceny,
- integrację mechaniki z logiką ruchu.

Najważniejsze:
**KIJANKA nie zastępuje osi TARZAN-a.**
KIJANKA jest bazą ruchową i stabilizacyjną.

---

## 4. Główne założenie mechaniczne

## 4.1. Napęd przejazdu po planie

Przejazd przód–tył ma być realizowany przez:
- silnik krokowy z przekładnią,
- koło zębate / układ współpracujący z **pasem zębatym mocowanym do podłoża**,
- długość pasa referencyjnego około **10 m**.

Cel:
- bardzo precyzyjny ruch liniowy,
- powtarzalne przejazdy,
- możliwość programowania i odtwarzania pozycji.

To jest odpowiednik toru odniesienia, ale bez konieczności rozstawiania klasycznych ciężkich szyn filmowych.

## 4.2. Układ kompensacji nierówności

Każde koło ma posiadać własny układ kompensacyjny.

Założony mechanizm:
- koło osadzone w układzie dźwigni / ramienia,
- regulacja wysokości koła realizowana przez osobny napęd,
- ruch kompensacyjny ograniczony do tego, co potrzebne do niwelowania nierówności.

Ważne doprecyzowanie z rozmów:
- ten mechanizm **nie prowadzi wózka po planie**,
- ten mechanizm **tylko kompensuje** nierówności,
- reszta ruchów i geometrii jest realizowana w innych osiach systemu.

---

## 5. Rezygnacja z klasycznych szyn filmowych

To jest kluczowa decyzja projektowa.

Szyny w filmie są używane dlatego, że:
- dają powtarzalny ruch,
- dobrze trzymają poziom,
- są znanym standardem.

Ale mają też istotne wady:
- są ciężkie,
- zajmują czas w transporcie i rozstawieniu,
- wymagają poziomowania,
- wydłużają przygotowanie planu,
- zwiększają zależność od warunków podłoża.

KIJANKA ma rozwiązać to inaczej:
- precyzję przejazdu bierze z **pasa zębatego mocowanego do podłoża**,
- kompensację nierówności bierze z **aktywnej regulacji wysokości kół**,
- przez to można szybciej wejść w gotowość do zdjęć.

Wniosek:
**KIJANKA nie jest zamiennikiem klasycznych szyn 1:1, tylko nowym sposobem osiągania powtarzalnego ruchu przy krótszym czasie przygotowania.**

---

## 6. Założona architektura aktywnej kompensacji koła

Dla każdego koła rozważono kilka wariantów.  
Po analizie najbardziej sensowny kierunek produkcyjny wygląda tak:

### 6.1. Architektura napędu kompensacji
- **serwo z enkoderem**,
- **hamulec bezpieczeństwa**,
- **przekładnia**,
- **śruba kulowa**,
- **tuleja / nakrętka pchająca dźwignię**,
- **ramię koła**.

### 6.2. Dlaczego serwo
Serwo zostało ocenione jako lepsze niż krokowiec dla kompensacji, ponieważ:
- ma lepszą reakcję dynamiczną,
- nadaje się do energicznych korekt,
- daje sprzężenie zwrotne,
- łatwiej je kontrolować przy szybkich zmianach obciążenia.

### 6.3. Dlaczego enkoder
Enkoder jest potrzebny, bo:
- daje rzeczywistą informację o położeniu,
- pozwala sterownikowi kontrolować faktyczny ruch,
- ogranicza ryzyko pracy „na ślepo”.

### 6.4. Dlaczego hamulec
Hamulec ma zwiększyć bezpieczeństwo układu:
- przy zaniku zasilania,
- przy awarii,
- przy niekontrolowanym opadaniu,
- jako dodatkowe zabezpieczenie trzymania pozycji.

### 6.5. Dlaczego śruba kulowa
Śruba kulowa:
- daje precyzyjny ruch liniowy,
- dobrze nadaje się do pchania dźwigni,
- pozwala uzyskać sztywny, przewidywalny ruch.

Wadą śruby kulowej jest brak samohamowności, dlatego wcześniej rozważano ślimak.  
Ostatecznie przyjęto, że:
- zamiast ślimaka można dać **mocniejszy serwonapęd i hamulec**,
- co uprości układ i zachowa lepszą dynamikę.

---

## 7. Ruch kompensacyjny i geometria

Z przyjętej rozmowami logiki wynika:

- cały skok mechanizmu liniowego potrzebny do pracy to około **100 mm**,
- regulacja działa przez dźwignię,
- w przybliżeniu rozważano układ **1:4**,
- przy wcześniejszych założeniach operacyjnych pojawiała się także wartość ramienia / promienia około **40 mm** w uproszczonych obliczeniach.

Najważniejsze jednak:
- śruba kulowa ma być **napędem pchającym**,
- nie ma pełnić roli klasycznej prowadnicy szynowej,
- ruch ma być przekazywany przez odpowiednio dobrany punkt pchania dźwigni,
- końcówka pchająca powinna mieć przegub / widełki / ucho, aby ograniczyć siły boczne na śrubie.

---

## 8. Ocena koncepcji bez klasycznych szyn

Ta koncepcja została oceniona jako dobra z powodów praktycznych:

- krótszy czas budowy,
- mniej precyzyjnej obróbki montażowej,
- szybszy pierwszy prototyp,
- mniejsza liczba elementów niż przy pełnym prowadzeniu szynowym,
- lepsze dopasowanie do funkcji kompensacyjnej.

Kluczowe rozróżnienie:
- szyny są potrzebne tam, gdzie prowadzenie musi samo zapewniać idealną geometrię,
- tutaj geometrię prowadzi ogólny układ wózka i pozostałe osie,
- a mechanizm koła ma tylko **kompensować**.

To oznacza, że brak szyn w module koła **nie jest wadą**, tylko świadomym uproszczeniem zgodnym z funkcją.

---

## 9. Główne obliczeniowe wnioski robocze z rozmów

W rozmowach przyjęto uproszczony model:
- całkowita masa układu na kołach około **60 kg**,
- czyli średnio około **15 kg na jedno koło**,
- rozważano momenty rzędu **8.7 Nm**, **13 Nm** i układy dźwigniowe **1:4**.

Wnioski z tych uproszczeń:
- wymagane momenty nie wyglądają ekstremalnie duże dla samego statycznego utrzymania,
- ale problemem nie jest tylko statyka,
- ważniejsze są:
  - dynamika korekty,
  - bezpieczeństwo,
  - odporność na chwilowe szarpnięcia,
  - zachowanie po zaniku zasilania,
  - szybkość reakcji w stylu aktywnej stabilizacji.

Dlatego kierunek produkcyjny został przesunięty z:
- krokowiec + ślimak

na:
- **serwo + enkoder + hamulec + przekładnia + śruba kulowa**

---

## 10. Rola czujników i logiki stabilizacji

Układ ma działać podobnie do stabilizacji:
- nie przez idealne podłoże,
- tylko przez aktywną korektę.

Założenie:
- nierówności są wykrywane przez czujnik orientacji / przechyłu / XYZ,
- wysokość kół korygowana jest przez mechanizm kompensacyjny,
- stabilizacja bazowa ma odciążać dalsze osie TARZAN-a.

Ważne:
- kompensacja kół nie zastępuje pełnej stabilizacji kamerowej,
- ale ma ograniczyć ilość zaburzeń przenoszonych wyżej w układ.

---

## 11. Rola EHR / TAKE / automatyzacji pracy

To jest klucz biznesowy i produkcyjny.

KIJANKA nie ma być tylko „wózkiem z silnikami”.

Ma być częścią systemu, który:
- przyspiesza ustawianie scen,
- skraca czas przygotowania przejazdu,
- pozwala łatwo powtarzać ruch,
- redukuje techniczne opóźnienia na planie.

Najważniejszy sens:
**oszczędność czasu całej ekipy zdjęciowej.**

To oznacza, że w projekcie produkcyjnym trzeba od razu uwzględnić:
- integrację z choreografią ruchu,
- integrację z zapisami TAKE,
- możliwość odtwarzania ustawień,
- szybkie przejście od pomysłu do gotowego ujęcia.

---

## 12. Proponowany moduł jednego koła

Jeden moduł koła powinien zawierać:

- koło nośne,
- wahacz / ramię koła,
- punkt obrotu ramienia,
- serwonapęd z enkoderem,
- hamulec bezpieczeństwa,
- przekładnię mechaniczną,
- śrubę kulową około 100 mm skoku roboczego,
- nakrętkę / tuleję pchającą,
- przegubowe połączenie z dźwignią,
- lokalne okablowanie zasilania i sygnałów.

Do sprawdzenia produkcyjnego:
- rzeczywisty zakres pracy ramienia,
- geometria punktu pchania,
- kąt pracy dźwigni,
- siły boczne,
- dostęp serwisowy,
- osłony mechaniczne.

---

## 13. Minimalny zakres pierwszego prototypu

Pierwszy prototyp nie musi od razu mieć pełnej finalnej estetyki.  
Powinien udowodnić:

1. że przejazd po pasie zębatym daje wymaganą precyzję,
2. że jeden moduł koła potrafi kompensować nierówność,
3. że sterowanie serwem jest wystarczająco szybkie,
4. że hamulec zabezpiecza układ,
5. że EHR / TAKE mogą później realnie przyspieszać pracę.

Dlatego pierwszy etap produkcyjny można podzielić na:

### Etap A — moduł jednego koła
- budowa jednego aktywnego modułu,
- test siły i zakresu ruchu,
- test sterowania,
- test pracy pod obciążeniem.

### Etap B — wózek bazowy
- rama,
- 4 koła,
- napęd przejazdu,
- pas referencyjny,
- zasilanie.

### Etap C — integracja z logiką TARZAN
- odczyt czujników,
- sterowanie kompensacją,
- integracja z EHR / TAKE,
- zapis i odtwarzanie ruchów.

---

## 14. Otwarta lista tematów do rozstrzygnięcia przed produkcją

Przed właściwym wykonaniem trzeba jeszcze doprecyzować:

### Mechanika
- dokładny model serwa,
- dokładny model przekładni,
- dokładny model śruby kulowej,
- sposób montażu końcówki pchającej,
- średnice osi,
- długości ramion,
- materiały konstrukcyjne,
- sposób osłony elementów ruchomych.

### Elektryka
- napięcia zasilania,
- moc całkowita,
- zasilanie hamulców,
- przewody do pracy ruchomej,
- zabezpieczenia awaryjne.

### Sterowanie
- częstotliwość odczytu czujników,
- algorytm kompensacji,
- warunki awaryjnego hamowania,
- współpraca z resztą systemu TARZAN.

### Produkcja
- technologia wykonania ramy,
- sposób wycinania elementów,
- toczenia i detale,
- anodowanie,
- montaż końcowy,
- serwis i wymienność podzespołów.

---

## 15. Wstępna filozofia bezpieczeństwa

Układ powinien mieć:
- hamulec bezpieczeństwa,
- tryb awaryjny,
- kontrolę błędów położenia,
- ograniczniki mechaniczne,
- możliwość szybkiego zatrzymania.

Ważna zasada:
**aktywny system ma pomagać, ale nie może tworzyć nowego niebezpieczeństwa.**

Dlatego w produkcji trzeba przewidzieć:
- awarię zasilania,
- błąd sterowania,
- zatrzymanie awaryjne,
- utratę pozycji,
- przeciążenie mechaniki.

---

## 16. Wniosek końcowy

Projekt **KIJANKA** ma sens jako:
**aktywny wózek kamerowy z pasem referencyjnym i kompensacją kół**.

Najważniejsze zalety tego kierunku:
- brak konieczności budowy klasycznych ciężkich szyn,
- krótszy czas przygotowania planu,
- szybsze wejście w gotowość do zdjęć,
- precyzyjny przejazd po pasie zębatym,
- aktywna kompensacja nierówności,
- dobra integracja z filozofią TARZAN / EHR / TAKE.

Na obecnym etapie najbardziej sensowny kierunek wykonawczy to:
- **wózek bazowy z napędem po pasie zębatym**,
- **4 aktywne moduły kompensacyjne kół**,
- **serwo z enkoderem i hamulcem**,
- **przekładnia**,
- **śruba kulowa**,
- **dźwignia koła**.

To nie jest jeszcze finalna dokumentacja wykonawcza warsztatowa, ale jest to **dobry dokument startowy do przygotowania produkcji**.

---

## 17. Proponowane następne dokumenty po tym pliku

Po tym dokumencie warto przygotować osobno:

1. **KIJANKA — BOM / lista części**
2. **KIJANKA — geometria jednego modułu koła**
3. **KIJANKA — architektura zasilania i sterowania**
4. **KIJANKA — logika kompensacji i integracja z TARZAN**
5. **KIJANKA — plan prototypu i testów**

---

## 18. Status dokumentu

Status: **roboczy produkcyjny / start przygotowania projektu**  
Przeznaczenie: **budowa pierwszego egzemplarza KIJANKA**
