# TARZAN MATRIX LED OFF AFTER TEST

Poprawka usuwa mały punkt/ghost pixel na Matrix LED po testach.

Przyczyna: `test_matrix_led_once()` czyścił dane `[0]*8`, ale zostawiał `displayEnabled=1`.
Na fizycznym module po multipleksowaniu mógł zostać pojedynczy świecący punkt.

Zmiana:
- dodaje `matrix_led_off_once()`;
- po teście Matrix LED zeruje dane i ustawia `displayEnabled=0`;
- test niewidoczny też kończy stanem OFF.
