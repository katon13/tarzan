# LKS-N5 ETAP 13 HOTFIX 8 — intro_status bez artefaktów + PoKeys I2C BUS

## Cel

Poprawka po obserwacji operatora:

1. Na `intro_status` nie mogą pojawiać się żadne ikony ani kontrolki statusu.
2. Python nie wysyła wartości `status_main` w czasie trwania animacji intra.
3. `intro_status` pozostaje stroną sterowaną przez Nextion: `p_anim`, `va_anim`, `tm_anim`.
4. Status `i2c_bus` ma oznaczać realny PoKeys BUS/I2C używany w TARZANIE, a nie wyłącznie kernelowe `/dev/i2c-*`.

## Zasada stron

Kolejność pozostaje:

```text
boot_intro -> boot_loading -> boot_linux -> boot_services -> boot_hardware -> boot_test -> ready_main -> intro_status -> status_main
```

Python:

```text
page ready_main
page intro_status
czeka bezpiecznie na koniec animacji Nextiona
wysyła wartości 30 kontrolek dopiero po zakończeniu intra
```

Nie wysyłamy tekstów ani progressu na `intro_status`, bo ta strona ich nie ma.

## I2C / BUS

`i2c_bus` jest zielony, gdy realny PoKeys BUS/I2C odpowie w skanie albo gdy BH1750 potwierdzi komunikację po tej magistrali. Brak `/dev/i2c-*` nie wygasza już automatycznie protokołu PoKeys I2C, bo miniPC nie komunikuje się z tym BUS-em bezpośrednio przez kernelowy i2c-dev.
