# TARZAN_KEYPAD_ZERO_BASED_PINS_FIX

Poprawka krytyczna PoKeys MatrixKB:

- fizyczne piny w schemacie TARZAN pozostają:
  - ROW1=P27, ROW2=P26, ROW3=P25, ROW4=P24
  - COL_A=P44, COL_B=P43, COL_C=P42
- PoKeysLib MatrixKB oczekuje w tablicach `matrixKBrowsPins[]` i `matrixKBcolumnsPins[]` indeksów zero-based:
  - fizyczne P27 zapisuje się jako `26`
  - fizyczne P44 zapisuje się jako `43`
- poprzednio wpisywaliśmy 27/26/25/24 oraz 44/43/42 bez `-1`, przez co konfiguracja przesuwała klawiaturę o jeden pin i mogła wejść na LCD P28.

Patch naprawia konfigurację keypad i dodaje readback `expected_*_api` / `actual_*_api`.
