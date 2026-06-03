# TARZAN LKS-N5 — ETAP 13 HOTFIX: intro_status przed testowaniem elementów

## Cel

Poprawka przywraca stronę `intro_status` jako krótką stronę przejściową pomiędzy
sprawdzeniami hardware a wejściem w właściwe testowanie elementów.

Poprawny przebieg:

```text
boot_linux
boot_services
boot_hardware
intro_status
boot_test
status_main
```

## Dlaczego

`boot_test` nie ma pojawiać się nagle po `boot_hardware`. Operator powinien
najpierw zobaczyć jasny komunikat, że system przechodzi do testowania elementów.

## Zasada

- `intro_status` nie udaje testu.
- `intro_status` nie zapala kontrolek.
- `intro_status` nie rusza urządzeń.
- `intro_status` jest wyłącznie spokojnym komunikatem przejściowym.
- Pełne testy nadal uruchamiają się dopiero na `boot_test`.

## Komunikat na ekranie

```text
INTRO STATUS
WEJSCIE W TEST
ELEMENTY
ZA CHWILE TEST
90%
```

## Bezpieczeństwo

Poprawka nie dotyka ruchu osi i nie wysyła:

```text
STEP
DIR
ENABLE
```
