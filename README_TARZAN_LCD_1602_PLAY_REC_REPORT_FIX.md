# TARZAN — LCD 1602 PLAY/REC raportowany osobno

Data: 2026-06-12

## Przyczyna

Po ręcznym teście potwierdzono, że oba wyświetlacze LCD 1602 działają fizycznie:

- `LCD PLAY INIT ok=True`
- `LCD PLAY WRITE ok=True`
- `LCD REC INIT ok=True`
- `LCD REC WRITE ok=True`

W LKS był jednak jeden komponent `lcd_1602`, przez co wyglądało, jakby sprawdzony był tylko jeden LCD.

## Zmiana

- `core/tarzanPoKeys.py`
  - `test_lcd_1602_once()` raportuje jawnie per-board: `LCD PLAY OK` i `LCD REC OK`,
  - zwraca `tested_boards`, `boards` oraz `summary`,
  - w logu pojawia się `LCD 1602 BOTH OK: LCD PLAY OK; LCD REC OK`.

- `core/TSP/tarzanTspLksHardwareTests.py`
  - wynik LKS dla `lcd_1602` pokazuje teraz skrót `LCD PLAY OK; LCD REC OK`,
  - opis testu zmieniony na `LCD 1602 PLAY+REC TarzanPoKeys test`.

## Zasada

Jedna ikona LKS `lcd_1602` może zostać na ekranie, ale test pod spodem musi potwierdzić oba fizyczne LCD: PLAY i REC.
