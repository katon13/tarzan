# Raport ujednolicenia sygnałów TARZAN (Etap Końcowy)

## Podsumowanie zmian
Zrealizowano pełną unifikację systemu sygnałów, eliminując problem wielu nazw dla tego samego stanu logicznego. System operuje teraz na **nazwach kanonicznych**, zachowując jednocześnie pełną wsteczną kompatybilność z interfejsem PAR (alias `par_`) oraz diagnostyką sprzętową.

## Kluczowe zmiany techniczne

### 1. Centralna Magistrala (SignalBus)
- **Automatyczny Aliasing**: Metoda `_notify` została przebudowana tak, aby przy zmianie sygnału sprzętowego (np. `cnc_x_cam_h_dir`) automatycznie powiadamiać subskrybentów nazwy kanonicznej (`axis_cam_h_dir`) oraz legacy (`par_cam_h_dir`).
- **Mostek Legacy**: Wprowadzono metodę `_get_legacy_names`, która mapuje nowe nazwy na stare formaty oczekiwane przez UI, co ożywiło AxisCard i Timeline.
- **Synchronizacja Liczników**: Metoda `_set_internal_virtual` wywołuje teraz powiadomienia, co przywróciło działanie liczników impulsów (`pulses`) i pozycji (`pos`) we wszystkich modułach (PAR, TFD, Nextion).

### 2. Rejestr Sygnałów (tarzanZmienneSygnalowe.py)
- **Uzupełnienie Mapowań**: Dodano pole `kanoniczna_nazwa` do ponad 40 kluczowych sygnałów.
- **Ujednolicenie Osi**: Zmieniono `axis_arm_t_*` na `axis_cam_t_*` dla osi pochyłu, co przywróciło ikony w EHR i spójność z panelem CNC.
- **Standard Sensorów**: Wszystkie sensory i krańcówki używają teraz prefiksu `sensor_` (np. `sensor_temp_c`, `sensor_cam_h_limit_left`).
- **Poprawa Typów**: Zmieniono typ sensora światła na `ANALOG`, co wyeliminowało błędy konwersji `NoneType` przy starcie PAR.

### 3. Interfejs PAR i TFD
- **Refaktoryzacja Paneli**: Mapy `AXIS_SIGNAL_BINDINGS` i `_AXIS_TIMELINE_ROWS` korzystają wyłącznie z nazw kanonicznych.
- **SOK (System Odczytu Kierunku)**: Logika SOK została uproszczona i teraz nasłuchuje bezpośrednio nazw `axis_*_step`, co gwarantuje poprawny odczyt niezależnie od źródła ruchu (TAKE/CNC/RRP).
- **Spójność TFD**: Wszystkie dane przesyłane do overlayów (laser, shock, temp, xyz) są pobierane przez nazwy kanoniczne.

## Wyniki testów
- **Start Systemu**: `tarzanPAR.py` uruchamia się bez błędów.
- **Podgląd Osi**: Liczniki impulsów na kartach osi reagują na ruch i zliczają kroki poprawnie.
- **Sensory**: Panele temperatury, światła i XYZ wyświetlają poprawne wartości i reagują na zmiany.
- **Krańcówki**: Diody STOP na kartach osi poprawnie odzwierciedlają stan fizycznych pinów.
- **EHR**: Ikony osi są widoczne i poprawnie zmapowane.

## Lista nazw kanonicznych (wybrane)
- `axis_cam_h_step`, `axis_cam_v_step`, `axis_cam_t_step`, `axis_cam_f_step`
- `axis_arm_h_step`, `axis_arm_v_step`
- `sensor_temp_c`, `sensor_light_lux`, `sensor_laser_set`, `sensor_shock_state`
- `sensor_cam_h_limit_left`, `sensor_cam_h_limit_right`
- `ui_f1_sw` do `ui_f4_sw`, `ui_action_led`, `ui_lcd_rs` do `ui_lcd_db7`

System jest obecnie gotowy do dalszej rozbudowy w oparciu o czystą i spójną architekturę sygnałową.
