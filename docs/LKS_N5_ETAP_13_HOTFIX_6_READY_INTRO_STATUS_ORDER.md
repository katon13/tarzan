# TARZAN LKS-N5 — ETAP 13 HOTFIX 6

## Ready main przed intro_status i status_main

Poprawia końcówkę sekwencji startowej po realnych testach.

Poprawna kolejność operatorska:

```text
boot_loading
boot_linux
boot_services
boot_hardware
boot_test
ready_main
intro_status
status_main
```

`ready_main` jest spokojną planszą gotowości po testach. Nie wykonuje testów,
nie resetuje statusów i nie udaje paska procesu. Pokazuje wynik gotowości i
liczbę zielonych kontrolek.

`intro_status` zostaje ostatnią krótką planszą przejściową przed tablicą
`status_main`.

## Zasady

- `boot_test` wykonuje realną diagnostykę.
- `ready_main` pokazuje GOTOWE po diagnostyce.
- `intro_status` robi ostatnie przejście operatorskie.
- `status_main` pokazuje 30 realnych stanów.
- Brak ruchu osi, brak STEP/DIR/ENABLE.
- Brak resetowania statusów poza wejściem na tablicę końcową.

## Uwaga Nextion

Na `ready_main` używane są pola:

```text
t_title
t_subtitle
t_line1
t_line2
t_line3
t_status
t_code
n_test_idx
n_level
```

Nie wysyłamy na tej stronie `j_progress`, bo eksport `ready_main.txt` nie ma
tego komponentu. Dzięki temu nie generujemy błędów Invalid Variable.
