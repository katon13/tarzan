# TARZAN — uwaga do testów LCD 1602 / HD44780

## Problem obserwowany

Przy szybkim przewijaniu tekstu na małym LCD 1602 znaki mogą wyglądać tak, jakby **nachodziły na siebie**, migały albo zostawiały chwilowy ślad.

To nie musi oznaczać błędu PoKeys ani złego podłączenia. Może wynikać z fizycznych ograniczeń tego typu wyświetlacza.

## Przyczyna

LCD 1602 / HD44780 nie zachowuje się jak szybki ekran graficzny:

- znak nie gaśnie natychmiast,
- matryca ma widoczną bezwładność,
- szybkie nadpisywanie kolejnych ramek powoduje miganie,
- agresywne `clear` całego ekranu też może pogorszyć efekt.

## Wniosek dla TARZANA

Do LCD 1602 nie należy robić bardzo szybkich animacji tekstu.

Lepszy tryb testowy:

```text
1. pokaż krótką klatkę tekstu
2. zostaw ją stabilnie przez chwilę
3. opcjonalnie wygaś linię spacjami
4. daj krótki czas na wygaszenie
5. dopiero pokaż następną klatkę
```

## Zalecenie do sandboxa

Przy dalszym rozwoju `lcd-scroll` warto dodać tryb wolniejszy:

```text
--hold-ms
--blank-between
--blank-ms
```

Przykładowy kierunek:

```text
tekst widoczny: 300–500 ms
wygaszenie spacjami: 60–120 ms
następna klatka dopiero po przerwie
```

## Ważne

Ten LCD nadaje się dobrze do statusów, komunikatów i prostych testów, ale nie do szybkiego płynnego scrolla jak na ekranie graficznym.
