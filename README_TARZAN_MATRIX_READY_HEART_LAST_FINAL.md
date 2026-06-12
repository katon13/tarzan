# TARZAN_MATRIX_READY_HEART_LAST_FINAL

Naprawa Matrix LED po testach LKS.

Problem:
- serce READY pojawiało się po teście matrix,
- późniejszy refresh/test nadpisywał matrycę i zostawały dwie kreski.

Zmiana:
- `test_matrix_led_once()` kończy się sercem READY w orientacji B,
- po pełnej sekwencji LKS boot, po finalnym LCD refresh, Matrix LED dostaje jeszcze raz serce jako ostatni fizyczny stan,
- nie wyłącza sterownika,
- nie rusza LCD, keypad, F-LED, ABC ani pinów.
