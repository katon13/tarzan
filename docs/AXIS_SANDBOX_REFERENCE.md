# AXIS_SANDBOX_REFERENCE

## Status dokumentu
**Status:** punkt odniesienia / reference  
**Zakres:** sandbox jednej osi TARZAN  
**Cel:** zamrożenie modelu strojenia linii i STEP preview przed integracją z EHR

---

## Rola sandboxu

`editor/tarzanAxisSandbox.py` jest **sandboxem odniesienia** dla pracy nad osią w projekcie TARZAN.

Ten plik nie jest docelowym edytorem choreografii ruchu.  
Jego rolą jest:

- strojenie ergonomii pracy operatora,
- strojenie zachowania linii jednej osi,
- strojenie modelu przejścia:
  - **linia / krzywa**
  - → **preview STEP**
- strojenie czułości myszy, skali widoku i parametrów zagęszczenia impulsów,
- testowanie zachowania osi bez ryzyka rozwalenia głównego edytora EHR.

Sandbox należy traktować jako:

> **wzorzec odniesienia dla modelu strojenia osi**

a nie jako miejsce do mieszania warstw projektu.

---

## Dlaczego ten sandbox jest ważny

W toku pracy został wypracowany model, który dał bardzo dobre rezultaty:

- ergonomia operatora została zestrojona,
- wizualizacja STEP działa poprawnie,
- jedna oś daje się stroić precyzyjnie,
- model jest czytelny i stabilny,
- sandbox pozwala świadomie szukać parametrów zamiast zgadywać poprawki „na ślepo”.

Ten model należy traktować jako **idealny model odniesienia** dla dalszej pracy nad osiami.

---

## Zasada architektoniczna

W projekcie TARZAN obowiązuje rozdzielenie warstw:

1. **mechanika osi generuje linię / krzywą**
2. **linia / krzywa generuje protokół ruchu**
3. **edytor tylko wizualizuje i pozwala stroić zachowanie**

Sandbox działa wyłącznie w tej logice.

Nie wolno upraszczać architektury do:

- bezpośredniego STEP z mechaniki,
- mieszania mechaniki i wizualizacji,
- mieszania generatora protokołu z UI sandboxu.

---

## Czego sandbox dotyczy

Sandbox dotyczy wyłącznie:

- pojedynczej osi,
- modelu linii,
- modelu preview STEP,
- ergonomii operatora,
- strojenia parametrów.

W szczególności sandbox jest miejscem do strojenia takich rzeczy jak:

- zakres widoku osi,
- czułość drag / pan,
- minimalny odstęp węzłów,
- dead zone,
- krzywa wejścia Y → gęstość impulsów,
- strefowe zagęszczenie dolnego wykresu,
- smoothing preview,
- parametry akumulatora STEP,
- sposób czytania parametrów osi z mechaniki.

---

## Czego sandbox nie może naruszać

Sandbox **nie może**:

- zmieniać architektury EHR,
- zmieniać generatora protokołu ruchu,
- zmieniać kontraktu TAKE,
- zmieniać centralnych stałych projektu,
- zastępować docelowej mechaniki osi,
- stać się „drugim edytorem głównym”.

Jeżeli proponowana zmiana wymaga wyjścia poza tę warstwę, należy się zatrzymać i opisać to wprost zamiast dopisywać kod.

---

## Zasada dalszego rozwoju

Sandbox ma być rozwijany jako:

> **laboratorium strojenia modelu osi**

To oznacza, że można i warto rozwijać:

- kolejne suwaki strojenia,
- profile i presety,
- eksport / import TXT,
- odczyt parametrów z mechaniki osi,
- testy zachowania dla różnych osi,
- porównania różnych modeli zagęszczania STEP.

Ale wszystkie te zmiany mają pozostać w warstwie sandboxu.

---

## Kluczowy wniosek projektowy

Wypracowany tutaj model nie jest jednorazowym eksperymentem.

Docelowo:

- **każda oś TARZAN** powinna mieć możliwość strojenia
  w oparciu o ten model,
- model sandboxu ma stać się **odniesieniem** dla integracji
  z właściwym edytorem EHR,
- integracja ma polegać na przeniesieniu logiki strojenia,
  a nie na psuciu architektury projektu.

Innymi słowy:

> sandbox jednej osi jest wzorcem zachowania,  
> który później ma być zastosowany dla wszystkich osi.

---

## Co przenosimy z sandboxu do EHR

Do dalszej integracji kwalifikują się przede wszystkim:

- zasady edycji węzłów,
- ergonomia drag / pan,
- rozdzielenie logiki od widoku,
- model strojenia linii,
- model strojenia preview STEP,
- odczyt parametrów osi z mechaniki,
- możliwość strojenia każdej osi w podobnym standardzie.

---

## Czego nie przenosimy bezpośrednio

Nie przenosimy bezpośrednio:

- przypadkowych uproszczeń sandboxu,
- lokalnych skrótów matematycznych użytych wyłącznie do testu,
- kodu tylko tymczasowego lub pomocniczego,
- elementów, które łamałyby rozdział:
  - mechanika osi
  - linia / krzywa
  - protokół
  - edytor / wizualizacja

Przenosimy tylko to, co zostało potwierdzone jako stabilny model odniesienia.

---

## Status repozytoryjny

Ten sandbox powinien być oznaczony w repozytorium jako:

- **reference implementation**
- punkt odniesienia przed integracją z EHR

Tag repozytoryjny powinien jasno wskazywać, że jest to wersja referencyjna, a nie przypadkowa iteracja robocza.

Przykład:

```bash
git tag axis-sandbox-reference
```

---

## Zasada pracy przy kolejnych zmianach

Przy każdej kolejnej zmianie dotyczącej sandboxu należy zaczynać od krótkiego bloku:

- **WARSTWA**
- **NIE RUSZAM**
- **KONTRAKT ZOSTAJE**
- **ZMIENIAM TYLKO**

Tak, aby sandbox nie zaczął po cichu naruszać innych warstw projektu.

---

## Decyzja projektowa

Na obecnym etapie projektowym obowiązuje decyzja:

> model wypracowany w `tarzanAxisSandbox.py`  
> jest modelem odniesienia dla dalszej pracy nad osiami TARZANA.

To oznacza, że:

- należy go chronić,
- należy go rozwijać ostrożnie,
- należy go traktować jako wzorzec,
- należy przygotować grunt pod to,
  aby **każda oś** mogła być strojona w analogiczny sposób.

---

## Następny logiczny krok

Następny logiczny krok po zamrożeniu sandboxu jako reference to:

1. dalej stroić model sandboxu,
2. potwierdzić zestawy parametrów dla różnych osi,
3. przygotować bezpieczną integrację z EHR,
4. zachować rozdział warstw projektu.

