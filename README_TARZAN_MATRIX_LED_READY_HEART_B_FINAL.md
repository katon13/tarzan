# TARZAN MATRIX LED READY HEART B FINAL

Poprawka końcowa dla Matrix LED po teście.

Założenia:
- nie wyłączamy sterownika Matrix LED,
- po teście zostaje znak gotowości,
- serce używa potwierdzonej orientacji B: kolumny przeliczone przez `_matrix_rows_from_columns`,
- nie rusza LCD, keypad, F-LED, ABC ani mapy pinów.

Zmieniony plik:
- `core/tarzanPoKeys.py`

Dodane:
- `matrix_led_ready_heart_once()`

Zmienione:
- `test_matrix_led_once()` po teście zostawia `matrix_ready`, a nie `matrix_off`.
