# TARZAN LKS-N5 — ETAP 13 HOTFIX 2: `intro_status` przed `status_main`

## Cel

Poprawka ustawia `intro_status` we właściwym miejscu kolejności ekranów.

Poprawny przebieg po tej poprawce:

```text
boot_linux
boot_services
boot_hardware
boot_test
intro_status
status_main
```

## Zasada

`intro_status` nie jest wejściem w testowanie elementów. Testowanie elementów odbywa się na `boot_test`.

`intro_status` jest ostatnią spokojną planszą przejściową po zakończeniu diagnostyki i bezpośrednio przed tablicą `status_main`.

## Komunikat

```text
INTRO STATUS
TESTY ZAKONCZONE
GOTOWE X/30
BEZ BLEDOW
98%
```

`X/30` pochodzi z realnej liczby zielonych kontrolek po diagnostyce.

## Bezpieczeństwo

Poprawka nie dodaje nowych testów sprzętu i nie wysyła:

```text
STEP
DIR
ENABLE
```
