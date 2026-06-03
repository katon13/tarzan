# LKS-N5 — ETAP 13 HOTFIX 5 — intro_status w globalnym progressie

Cel: zachować poprawną kolejność ekranów dla operatora po wprowadzeniu spokojnego globalnego paska postępu.

Poprawna kolejność:

```text
boot_loading   — lokalne oczekiwanie Nextiona na Linuxa, bez udawanego postępu
boot_linux     — realne kroki Linuxa
boot_services  — realne kroki usług
boot_hardware  — realne kroki sprzętowe
boot_test      — realna diagnostyka urządzeń
intro_status   — ostatnia plansza przejściowa: TESTY ZAKONCZONE / GOTOWE / SPRAWDZ STATUS
status_main    — tablica stałych statusów
```

Zmiana:

- `intro_status` nie jest pomijany po HOTFIX 4.
- `intro_status` jest bezpośrednio przed `status_main`.
- Nie ma już dodatkowej planszy `BOOT COMPLETE` na `boot_test`, bo dublowała rolę `intro_status`.
- `j_progress` i `n_progress` na `intro_status` zostają na 100%.
- Pasek nie cofa się z 100% do 98%.

Zasada operatora:

```text
Pasek = globalny postęp startu systemu.
Intro = ostatni oddech / informacja przed tablicą status_main.
Status_main = prawda o urządzeniach.
```
