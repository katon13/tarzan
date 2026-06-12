# TARZAN — poprawka klawiatury PLAY 4x3 według schematu

Data: 2026-06-12

## Przyczyna

Po fizycznym sprawdzeniu schematu TARZAN-PCB-POKSYG-v2 ustalono, że klawiatura panelu PLAY nie jest czteroliniową klawiaturą P24-P27.
Jest to standardowa klawiatura matrycowa 4x3, czyli 7 linii:

- ROW1 = PLAY P27
- ROW2 = PLAY P26
- ROW3 = PLAY P25
- ROW4 = PLAY P24
- COL_A = PLAY P44
- COL_B = PLAY P43
- COL_C = PLAY P42

Poprzednio P42/P43/P44 były opisane jako rezerwa, więc część klawiatury zniknęła z mapy sygnałowej.

## Zasada bezpieczeństwa

PoKeys57U potrafi działać jako wirtualna klawiatura USB. Błędne ustawienie MatrixKB albo key mapping może powodować wpisywanie znaków do Windows/Linux, np. `142580369`.

Dlatego w TARZANIE:

- MatrixKB może być używany tylko jako odczyt statusu przez API PoKeys,
- USB HID keyboard mapping musi być wyzerowany,
- macro mapping musi być wyzerowany,
- triggered mapping musi być wyzerowany,
- TARZAN decyduje, co oznacza klawisz, a nie system operacyjny.

## Zmienione pliki

- `core/tarzanZmienneSygnalowe.py`
  - P24-P27 opisane jako ROW4-ROW1,
  - P42/P43/P44 zmienione z rezerwy na COL_C/COL_B/COL_A,
  - pełna klawiatura PLAY 4x3 jest widoczna w mapie sygnałów.

- `core/tarzanPokABC.py`
  - dodany twardy kontrakt PLAY_KEYPAD_4X3,
  - ABC wykrywa błąd, jeśli P42/P43/P44 wrócą jako rezerwa,
  - ABC ostrzega, że MatrixKB jest tylko API-only bez USB HID.

- `core/tarzanPoKeys.py`
  - dodane mapowanie PLAY 4x3,
  - konfiguracja MatrixKB: rows 27/26/25/24, columns 44/43/42,
  - keyMapping/macro/triggered mapping zerowane,
  - odczyt klawiatury przez `PK_MatrixKBStatusGet`, bez wysyłania znaków do OS.

## Nie wolno

Nie wolno programować tej klawiatury jako same P24-P27.
Nie wolno włączać direct key mapping / triggered key mapping / macro mapping dla tej klawiatury.
Nie wolno dopuszczać, aby PoKeys PLAY działał jako klawiatura systemowa Windows/Linux.
