# KIJANKA_geometria.md
# KIJANKA — geometria i punkty montażowe
## Dokument roboczy do przygotowania konstrukcji

## 1. Cel dokumentu

Ten dokument opisuje założenia geometryczne i montażowe dla systemu KIJANKA.

Nie jest to jeszcze rysunek warsztatowy.  
To jest dokument, który ma uporządkować:
- relacje geometryczne,
- główne osie ruchu,
- punkty podparcia,
- punkty napędowe,
- obszary wymagające szczególnej dokładności.

---

## 2. Główne założenie geometryczne systemu

System KIJANKA składa się z dwóch warstw geometrii:

### Warstwa A — geometria przejazdu
- rama bazowa
- rozstaw kół
- pozycja napędu jazdy
- pozycja koła współpracującego z pasem referencyjnym
- baza całego wózka

### Warstwa B — geometria kompensacji
- pozycja każdego ramienia koła
- punkt obrotu ramienia
- pozycja serwa
- pozycja przekładni
- oś śruby kulowej
- pozycja punktu pchania dźwigni

Obie warstwy muszą być spójne, ale nie wolno ich mieszać funkcjonalnie.

---

## 3. Główne punkty odniesienia geometrii

Dla dalszej dokumentacji warto wprowadzić nazwy punktów:

### Dla jednego modułu koła
- **P0** — punkt obrotu ramienia koła
- **P1** — środek osi koła
- **P2** — punkt przyłożenia popychacza do ramienia
- **P3** — oś śruby kulowej
- **P4** — punkt mocowania śruby do ramy
- **P5** — punkt mocowania serwa / przekładni
- **P6** — ogranicznik dolny
- **P7** — ogranicznik górny

### Dla całego wózka
- **W0** — środek geometryczny ramy
- **W1–W4** — punkty położenia czterech modułów kół
- **W5** — punkt centralny czujnika IMU / XYZ
- **W6** — punkt napędu przejazdu
- **W7** — linia pracy pasa referencyjnego

---

## 4. Geometria jednego modułu koła

## 4.1. Założenie podstawowe
Ramię koła obraca się wokół punktu **P0**.  
Koło znajduje się w punkcie **P1**.  
Popychacz działa na ramię w punkcie **P2**.

To daje układ:
- punkt obrotu,
- ramię nośne,
- punkt wymuszenia ruchu.

## 4.2. Rola punktu P2
Punkt **P2** jest jednym z najważniejszych punktów projektu.

To właśnie jego położenie decyduje o:
- przełożeniu geometrycznym,
- wymaganej sile popychacza,
- zakresie ruchu śruby,
- liniowości działania modułu,
- kątach pracy końcówki przegubowej.

## 4.3. Zasada doboru P2
Punkt P2 nie powinien:
- być zbyt blisko punktu P0, bo wtedy siły będą zbyt duże,
- być zbyt blisko koła, bo wtedy wzrosną zakresy ruchu popychacza i problem kinematyczny.

Trzeba znaleźć kompromis między:
- siłą,
- zakresem,
- szybkością,
- geometrią.

---

## 5. Oś śruby kulowej

## 5.1. Założenie
Oś śruby kulowej **P3** powinna być ustawiona tak, aby:
- ruch popychacza był możliwie osiowy,
- śruba nie przenosiła dużych sił poprzecznych,
- zmiana kąta między popychaczem a ramieniem była kontrolowana.

## 5.2. Konsekwencje złej geometrii
Jeżeli śruba będzie ustawiona źle, pojawią się:
- siły boczne,
- większe tarcie,
- szybsze zużycie nakrętki,
- ugięcia i luzy,
- pogorszenie jakości kompensacji.

## 5.3. Zalecenie
Połączenie popychacza z ramieniem musi mieć element przegubowy.  
Nie wolno prowadzić tego jako sztywnego połączenia wymuszającego skręcanie śruby.

---

## 6. Geometria serwa i przekładni

## 6.1. Punkt mocowania napędu
Napęd modułu powinien być mocowany do ramy w okolicy punktu **P5**.

Układ mocowania musi:
- zapewnić sztywność,
- zachować osiowość,
- ułatwić serwis,
- umożliwić ustawienie współosiowości z przekładnią i śrubą.

## 6.2. Strefa serwisowa
Wokół zespołu napędu należy przewidzieć:
- miejsce na przewody,
- miejsce na wtyczki,
- miejsce na dostęp do śrub montażowych,
- miejsce na obsługę hamulca i enkodera.

---

## 7. Ograniczniki mechaniczne

Każdy moduł powinien mieć dwa niezależne ograniczenia:
- ogranicznik dolny
- ogranicznik górny

Ich funkcja:
- ochrona przed wyjściem poza zakres,
- ochrona śruby i nakrętki,
- ograniczenie przeciążeń mechaniki,
- bezpieczeństwo w razie błędu sterowania.

Ograniczniki mechaniczne powinny działać niezależnie od software.

---

## 8. Geometria całego wózka

## 8.1. Rozstaw kół
Rozstaw kół musi zostać dobrany tak, aby:
- zachować stabilność wózka,
- zapewnić miejsce dla mechanizmów kompensacji,
- umożliwić montaż napędu przejazdu,
- nie ograniczać pozostałych osi systemu.

## 8.2. Środek układu
Środek masy oraz punkt montażu IMU powinny być możliwie blisko środka geometrycznego bazy.  
Pozwoli to uprościć logikę kompensacji.

## 8.3. Rama bazowa
Rama powinna być traktowana jako odniesienie dla:
- mocowań modułów,
- zasilania,
- napędu przejazdu,
- elektroniki centralnej.

---

## 9. Pas referencyjny i geometria przejazdu

## 9.1. Linia pasa
Pas referencyjny powinien tworzyć możliwie prostą linię odniesienia dla ruchu przejazdu.

## 9.2. Pozycja napędu
Napęd przejazdu musi być osadzony tak, aby:
- zapewnić prawidłowe zazębienie,
- nie tracić precyzji,
- nie powodować przekoszeń wózka.

## 9.3. Punkty mocowania pasa
Mocowanie pasa do podłoża musi być:
- powtarzalne,
- szybkie,
- stabilne,
- łatwe do naciągu.

To jest kluczowe dla praktycznego zastosowania na planie.

---

## 10. Obszary wymagające największej dokładności

W projekcie KIJANKA nie wszystkie wymiary są równie krytyczne.

Największej dokładności wymagają:

### Krytyczne geometrycznie
- położenie punktu P0
- położenie punktu P2
- oś śruby P3
- współosiowość napędu i przekładni
- osie mocowania modułów do ramy
- linia napędu przejazdu

### Mniej krytyczne
- część osłon
- część powierzchni zewnętrznych
- elementy wizualne

To ważne produkcyjnie, bo pozwala oszczędzać czas tam, gdzie nadmierna dokładność nie daje wartości.

---

## 11. Geometria pod kątem produkcji

W projekcie prototypowym geometria powinna być projektowana tak, aby:
- unikać zbyt skomplikowanych kształtów,
- ograniczyć liczbę trudnych baz obróbczych,
- ograniczyć liczbę elementów specjalnych,
- pozwalać na montaż etapami,
- umożliwiać poprawki po pierwszych testach.

Dlatego zaleca się:
- prostą ramę bazową,
- łatwo wymienne wsporniki,
- otwory fasolkowe w miejscach regulacyjnych,
- modułowość napędu i śruby.

---

## 12. Minimalny zestaw rysunków, które powinny powstać po tym dokumencie

Na podstawie tego dokumentu powinny powstać minimum:

1. rysunek ramy bazowej
2. rysunek jednego wahacza koła
3. rysunek punktu obrotu ramienia
4. rysunek wspornika serwa
5. rysunek wspornika śruby kulowej
6. rysunek popychacza i końcówki przegubowej
7. rysunek mocowania koła
8. schemat rozmieszczenia 4 modułów na ramie
9. schemat linii pasa referencyjnego

---

## 13. Lista pytań kontrolnych do geometrii

Przed zatwierdzeniem konstrukcji trzeba odpowiedzieć na pytania:

- Czy śruba pracuje osiowo?
- Czy ramię ma wystarczający zakres ruchu?
- Czy punkt pchania nie generuje nadmiernych kątów?
- Czy dostęp do serwisu jest możliwy?
- Czy hamulec ma miejsce montażowe i chłodzenie?
- Czy przewody nie wchodzą w strefę ruchu?
- Czy moduł koła można zdemontować bez rozbierania całego wózka?
- Czy napęd przejazdu ma czystą linię pracy względem pasa?

---

## 14. Wniosek

Geometria KIJANKA powinna być podporządkowana jednej zasadzie:

**prostota mechaniczna tam, gdzie to możliwe, i dokładność tylko tam, gdzie naprawdę wpływa na działanie.**

Najważniejsze relacje geometryczne to:
- punkt obrotu ramienia,
- punkt pchania,
- oś śruby,
- mocowanie napędu,
- linia pasa referencyjnego.

Ten dokument stanowi podstawę do przejścia do rysunków konstrukcyjnych i modelu CAD prototypu.
