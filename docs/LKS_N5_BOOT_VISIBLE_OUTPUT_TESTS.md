# TARZAN LKS-N5 — widoczne testy wyjść w boot_test

Patch rozwiązuje problem: podczas `boot_test` operator widział opis testu na Nextionie, ale Matrix LED i LED F1-F4 nie pokazywały fizycznej reakcji.

## Zasada

Pełna diagnostyka startowa nadal jest bezpieczna dla osi:

- zero STEP,
- zero przełączania DIR dla ruchu,
- zero ENABLE,
- zero homingu,
- zero Pulse Engine.

Widoczne wzorce dostają tylko wyjścia operatorskie:

- `lcd_1602` — krótki napis testowy, potem `BEZ BLEDOW / GOTOWE`,
- `matrix_led` — krótki wzór `TEST/OK`, potem wygaszenie,
- `f_led` — krótkie mrugnięcie F1-F4, potem wygaszenie.

Przyciski, keypad i krańcówki nie czekają w boot na ręczne naciśnięcia.

## Zmienione pliki

- `core/TSP/tarzanTspLksDiagnostics.py`
- `core/TSP/tarzanTspLksBootProgress.py`

## Tryby

`run_all()` domyślnie zostaje cichy:

```bash
python3 -m core.TSP.tarzanTspLksDiagnostics --print-results --print-statuses
```

Boot LKS-N5 wywołuje teraz:

```python
diagnostics.run_all(operator_visible=True)
```

Widoczny tryb jest zawężony tylko do LCD/Matrix/LED, żeby nie blokować startu i nie dotykać ruchu.
