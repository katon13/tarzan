# TARZAN POKEYS/LKS STABLE FULL PATCH V2

Cel:
- zatrzymać crashe HW_Bridge_Loop po zmianach ABC override,
- utrzymać testy osi w trybie NO_MOTION,
- wyłączyć lokalny tekstowy LKS na monitorze miniPC,
- zachować Nextion 5 jako właściwy panel LKS-N5,
- rozdzielić light_laser / light_bh1750 / i2c_bus.

Najważniejsze zabezpieczenia:
1. core/tarzanPoKeys.py
   - ABC_STARTUP_SAFE_VALUE_OVERRIDES istnieje jako pole klasy.
   - ABC_STARTUP_SAFE_VALUE_OVERRIDES istnieje też jako pole instancji w __init__.
   - _abc_safe_output_value(board, sig) ma fallback i nie może wywrócić HardwareBridge.
   - configure_and_verify_project_once() łapie wyjątek z ensure_project_startup_bios_once().
   - Nie ma błędnego wywołania self._abc_safe_output_value(sig).
   - Nie uruchamia ruchu osi.

2. core/TSP/tarzanTspLks.py
   - twarda blokada pisania na /dev/tty7 bez TARZAN_ENABLE_TTY_LKS=1.

3. main.py / tarzanTspServer.py
   - LKS-TTY domyślnie wyłączony.
   - Nextion 5 zostaje aktywnym LKS-N5.

4. core/TSP/tarzanTspLksStatusMap.py / tarzanTspServer.py
   - light_laser i light_bh1750 są osobnymi statusami.
   - i2c_bus może agregować z testów bus/device, ale light_laser ma własny test.

UWAGA:
Override dla 4 fizycznie świecących diod jest mechanicznie gotowy, ale mapa jest pusta,
bo nie wolno zgadywać pinów. Po teście trzeba wpisać konkretne ("PLAY"/"REC", pin).
