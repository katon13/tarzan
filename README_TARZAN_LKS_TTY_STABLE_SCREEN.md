# TARZAN LKS-TTY stable HDMI screen

Naprawa efektu „pojeżdżania” obrazu LKS na monitorze HDMI / /dev/tty7.

Zmiana:
- LKS-TTY nadal działa na /dev/tty7.
- Nextion 5 nadal działa osobno po UART.
- Stała szerokość renderu TTY = 78 kolumn.
- Brak linii 100/120 znaków, które zawijały się na konsoli HDMI.
- Stała ramka 24 linie, bez przewijania i bez czyszczenia całego ekranu w cyklu.

Nie rusza PoKeys, ABC, Nextion 5 ani HardwareBridge.
