# Raport ujednolicenia sygnałów TARZAN - Przed zmianą (Baseline)

## Informacje ogólne
Data: 2026-05-16
Status: Analiza bazowa przed wdrożeniem zmian.

## Stan aktualny (Analiza)
W projekcie zidentyfikowano 3 systemy nazewnictwa dla tych samych stanów logicznych:
1. Hardware/Pinowe: np. 'play_p38_step_dir_arm_h', 'rec_p03_copy_dir_cam_h'.
2. Protokół TAKE: np. 'TAKE_CAM_H_DIR', 'TAKE_ARM_H_STEP'.
3. Wirtualne/Widokowe: np. 'par_cam_h_pulses', 'axis0', 'io.arm_h_enable'.

### Główne problemy:
- 'editor/TFD/tfd_state.py' używa niepełnej listy kluczy do pobierania kierunku osi, co powoduje, że stany sprzętowe nie są widoczne w TFD/Overlay.
- 'editor/PAR/tarzanParPanels.py' posiada rozproszone mapy, które dublują logikę.
- 'hardware/tarzanNextion/state_mapper.py' mapuje ręcznie nazwy na stare nazwy sprzętowe.

## Wyniki testów bazowych
Uruchomiono 'python editor/tarzanPAR.py'. System uruchamia się poprawnie.
- PAR: Działa, panele się wyświetlają.
- TFD Server: Uruchomiony.
- SignalBus: Inicjalizuje wirtualne sygnały.
- DIR Osi: Niezgodność między SOK a TFD potwierdzona.
- Sensory/Limits: Używają nazw 'par_*'.

## Planowane zmiany
1. Ujednolicenie nazw w 'core/tarzanSignalBus.py'.
2. Aktualizacja map w 'editor/PAR/tarzanParPanels.py' i 'editor/PAR/tarzanParProtocolMapper.py'.
3. Aktualizacja odwołań w 'editor/TFD/tfd_state.py' i 'hardware/tarzanNextion'.
4. Usunięcie zbędnych aliasów.

---
Podpisano: Junie
