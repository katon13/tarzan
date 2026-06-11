# TARZAN LKS-TTY + LKS-N5 + PoKeys ABC — FINAL PATCH

Cel patcha:
- przywraca prawidłowy LKS-TTY na HDMI/TTY miniPC (`/dev/tty7`),
- zostawia Nextion 5 jako osobne równoległe wyjście LKS-N5 po UART,
- nie miesza HDMI z Nextionem,
- usuwa błędny wymóg `TARZAN_ENABLE_TTY_LKS=1`,
- zostawia poprawki PoKeys ABC:
  - brak `ABC_STARTUP_SAFE_VALUE_OVERRIDES` nie może wywalić `HW_Bridge_Loop`,
  - `auto=255` jest akceptowane,
  - startup BIOS PLAY/REC jest potwierdzany,
  - test osi pozostaje NO_MOTION,
  - `light_laser` jest oddzielony od `light_bh1750`.

Zasada:
- HDMI / monitor miniPC = lokalny LKS-TTY na `/dev/tty7`.
- Nextion 5 = LKS-N5 po UART.
- Oba wyjścia LKS działają równolegle.
- LKS nie jest PAR i nie wykonuje ruchu osi.
