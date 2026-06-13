# TARZAN_LKS_F_LED_FINAL_OFF_FIX

Patch punktowy do LKS-N5 boot/final-ready.

## Cel
Naprawia komunikat:

```text
LKS-N5 FINAL F-LED OFF ok=False
```

Przyczyna była podwójna:

1. Test `f_led` w `core/tarzanHardwareBridge.py` kończył pinami na `0`, a dla F-LED w TARZAN `ON=0`, `OFF=1`.
2. Finalne `set_f_leds_off_once()` w `core/TSP/tarzanTspLksBootProgress.py` było wołane po safe-state, gdy PoKeys mógł być już w `IDLE`; wtedy `_call_device()` blokował `PK_PinConfigurationSet` jako `system_idle`.

## Zmienione pliki

- `core/tarzanHardwareBridge.py`
- `core/TSP/tarzanTspLksBootProgress.py`

## Nie ruszane

- `core/tarzanPoKeys.py`
- ABC / POKSYG
- mapy pinów
- Nextion HMI
- Matrix LED low-level
- LCD low-level
- osie / pulse engine

## Zmiany

- `_lks_test_f_led()` używa jawnie `ON=0`, `OFF=1` z `TarzanPoKeys`.
- Test F-LED zaczyna OFF, miga ON i kończy OFF.
- Finalne `set_f_leds_off_once()` wchodzi przez `begin_point_test("f_led_final_off")`, żeby zapis PoKeys był dozwolony poza IDLE.
- Po finalnym OFF stan aktywny jest zamykany przez `end_active_state()`.

## Test

```bash
python3 -m py_compile core/tarzanHardwareBridge.py core/TSP/tarzanTspLksBootProgress.py
```
