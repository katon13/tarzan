# TARZAN LKS-N5 — ETAP 13 HOTFIX 3

## boot_loading bez fałszywego paska postępu

Problem: po włączeniu miniPC strona `boot_loading` działała poprawnie jako ekran oczekiwania, ale jej lokalny timer Nextiona zwiększał `j_progress` od 20 do 90 i zapętlał pasek kilka razy zanim Linux/systemd uruchomił usługę LKS-N5.

To wyglądało jak postęp ładowania Linuxa, ale nie było realnym statusem.

## Zmiana

Na stronie `boot_loading`:

- `j_progress` startuje na małej wartości oczekiwania,
- `n_progress` pokazuje tę samą stałą wartość,
- `tm_load.en=0`,
- timer `tm_load` jest wyłączony,
- pasek nie zapętla się.

Realny postęp startu zaczyna się dopiero wtedy, gdy Python przejmie ekran i pokaże strony:

```text
boot_linux      10/20/30%
boot_services   40/50/58/62%
boot_hardware   68/74/78/82/86%
boot_test        94/100%
intro_status
status_main
```

## Ważne

Ten patch zmienia źródło HMI `hardware/Nextion_structure_5/boot_loading.txt`. Żeby zobaczyć zmianę na fizycznym ekranie, trzeba zaktualizować projekt Nextion/TFT i wgrać go do Nextion 5.

Kod Pythona ETAPU 13 zostaje bez zmian — on już pokazuje realny progress po starcie systemd.
