# TARZAN F-LED GPIO/OFF AFTER TEST

Naprawa F-LED na REC:

- REC P46/P48/P50/P52 są mapowane jako normalne `GPIO OUT`, nie jako funkcja specjalna.
- F-LED są aktywne stanem `0`, więc stan spoczynkowy/off to `1`.
- Test `blink_f_led_once()` po zakończeniu zawsze gasi wszystkie diody F1-F4.
- Dodano `set_f_leds_off_once()` jako jawne gaszenie wszystkich F-LED.

Nie rusza LCD PLAY/REC ani keypad 4x3.
