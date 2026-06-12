# TARZAN F-LED GPIO/OFF AFTER TEST V2

Poprawka dla fizycznych diod F1-F4 na REC:

- REC P46 F1 LED = GPIO OUT, default OFF=1
- REC P48 F2 LED = GPIO OUT, default OFF=1
- REC P50 F3 LED = GPIO OUT, default OFF=1
- REC P52 F4 LED = GPIO OUT, default OFF=1
- test `blink_f_led_once(visible=True)` zaczyna od OFF i kończy OFF
- dodaje `set_f_leds_off_once()` do jawnego gaszenia wszystkich F-LED

Nie rusza LCD PLAY/REC ani keypad 4x3.
