# TARZAN LCD visible final refresh

Patch naprawia sytuację, w której test LCD 1602 zwracał `ok=True`, ale fizycznie na wyświetlaczach nie było widać tekstu.

## Zasada

- LCD PLAY i LCD REC są testowane osobno.
- Test widoczny robi dłuższy HOLD na ekranie.
- Po zakończeniu pełnej macierzy LKS-N5 wykonywany jest finalny refresh LCD jako ostatni test fizyczny.
- To jest tylko LCD/raportowanie. Patch nie rusza osi, STEP, DIR ani ENABLE.

## Oczekiwane logi

```text
LCD PLAY VISIBLE OK: init/write/hold confirmed
LCD REC VISIBLE OK: init/write/hold confirmed
LCD 1602 BOTH VISIBLE OK: LCD PLAY OK; LCD REC OK
LKS-N5 FINAL LCD VISIBLE REFRESH component=lcd_1602 ok=True
```
