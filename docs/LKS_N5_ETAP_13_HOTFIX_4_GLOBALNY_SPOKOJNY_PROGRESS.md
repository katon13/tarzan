# TARZAN LKS-N5 — ETAP 13 HOTFIX 4
## Globalny, spokojny pasek postępu dla operatora

## Cel

`j_progress` i `n_progress` nie mają pokazywać lokalnego testu pojedynczego elementu.
Dla operatora pasek ma oznaczać postęp całego startu systemu od chwili przejęcia ekranu przez Linux/systemd do wejścia na `status_main`.

## Problem

Poprzednia wersja pokazywała poprawne kroki, ale przy każdym kroku ponownie przełączała stronę Nextiona:

```text
page boot_linux
page boot_linux
page boot_linux
...
```

To powodowało wrażenie migania. Technicznie dane były prawdziwe, ale operatorsko pasek wyglądał nerwowo.

## Zmiana

W `core/TSP/tarzanTspLksBootProgress.py` dodano:

- cache aktualnej sceny,
- przełączanie `page` tylko wtedy, gdy realnie zmienia się strona,
- monotoniczny globalny progress,
- brak cofania paska,
- wynik pojedynczego kroku aktualizuje teksty, a nie resetuje strony.

## Zasada po zmianie

```text
boot_loading  — czeka spokojnie na Linux/systemd, bez zapętlania paska
boot_linux    — globalny progress 10–30%
boot_services — globalny progress 40–62%
boot_hardware — globalny progress 68–86%
boot_test     — globalny progress 94–100%
intro_status  — krótka plansza gotowości
status_main   — tablica prawdy urządzeń
```

## Ważne

`j_progress` nie oznacza, że wszystkie urządzenia są sprawne.
Oznacza, że zakończył się etap uruchamiania i diagnostyki.
Prawdziwy stan urządzeń pokazuje dopiero `status_main`.

## Nextion

W Nextion Editor strona `boot_loading` ma nie zapętlać paska. Ma być tylko ekranem oczekiwania na Linux:

```text
PostInitialize:
sendme
va_load.val=8
n_progress.val=va_load.val
j_progress.val=va_load.val
tm_load.tim=1000
tm_load.en=0
```

Timer `tm_load` ma być wyłączony albo ma nie zwiększać `j_progress` w pętli.
