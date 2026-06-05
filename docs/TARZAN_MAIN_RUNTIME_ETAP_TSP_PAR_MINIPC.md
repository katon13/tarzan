# TARZAN MAIN RUNTIME — Zespolenie Pełne (Etap Wykonawczy)

**Status:** System ZESPOLONY. Etapy 6-16 (Wykonawcze) zamknięte.
**Wersja:** 3.0
**Data:** 2026-06-05

## 1. Stan Implementacji

### Mięśnie Systemu (ETAP 14 i 15) - ZAMKNIĘTE
- **Zrealizowano**: `TarzanHardwareBridge` jest teraz aktywnym mostkiem wykonawczym. Generuje impulsy STEP dla trybu manualnego (tM) i obsługuje statusy READY/ALARM/POS z PoKeys Pulse Engine v2.
- **Zrealizowano**: Blending ruchu (Etap 15). HardwareBridge w locie łączy impulsy STEP z TAKE z dynamicznymi offsetami KHR.
- **Zrealizowano**: EHR Playback (Etap 14). TSP Server odtwarza załadowane TAKE z częstotliwością 100Hz, strumieniując sygnały bezpośrednio do SignalBus i HardwareBridge.

### Logika Trybów (ETAP 12) - ZAMKNIĘTA
- **Zrealizowano**: `TarzanModeLogic` zarządza priorytetami sterowania (`control_owner`) i automatycznie reaguje na komendy systemowe (`cmd_ehr_start` itp.).

### Monitoring i Diagnostyka (ETAP 16) - ZAMKNIĘTE
- **Zrealizowano**: Publikacja `FAST_STATS` in czasie rzeczywistym. Pełna izolacja procesów diagnostycznych (Etap 3) chroni runtime przed crashami.

### Etap 6: PAR LIVE przez TarzanParBridge (ZAMKNIĘTY)
- **Status**: Stabilny, jedyny tor komunikacji PAR ↔ miniPC.
- **Zrealizowano**: Bridge zarządza cyklem życia `TarzanTspClient`. Handshake (HELLO, PING, GET_STATE, SUBSCRIBE) jest kompletny i zsynchronizowany.
- **Zrealizowano**: Wszystkie dane z miniPC trafiają do lokalnego SignalBus PAR przez `apply_snapshot`.

### Etap 7: Dwukierunkowa Synchronizacja (ZAMKNIĘTY)
- **Status**: Pełny przepływ informacji MiniPC ↔ PAR bez pętli zwrotnych.
- **Zrealizowano**: Filtrowanie identycznych wartości w `SignalBus.apply_snapshot` i `force_signal`.
- **Zrealizowano**: TSP Server zwraca czytelne statusy zapisu (`OK`, `UNKNOWN_SIGNAL`, `WRITE_DENIED`).

### Etap 8: PAR jako Pełna Administracja (ZAMKNIĘTY)
- **Status**: PAR w trybie LIVE w pełni kontroluje runtime przez TSP/SignalBus.
- **Zrealizowano**: Ujednolicone wywołania administracyjne przez `bridge.call_action(...)` i `bridge.write_output(...)`.
- **Zrealizowano**: Panel SYSTEM wyświetla stan hardware LKS, statystyki TSP i pozwala na akcje: `Diagnostyka`, `Take Control`, `Reboot`.
- **Zrealizowano**: Zdalne sterowanie modułami EHR/KHR (Start/Stop).

### Etap 13: RRP / SOK / Osie (ZAMKNIĘTY)
- **Status**: Pełne spięcie modułów manualnych i automatycznych przez tor wykonawczy.
- **Zrealizowano**: Dopisanie pełnej mapy statusów osi do katalogu centralnego.
- **Zrealizowano**: Logika `tarzanMode.py` (tM) mapuje rRP/SOK na sygnały wybranej osi.
- **Zrealizowano**: HardwareBridge generuje impulsy fizyczne i czyta statusy osi.

## 2. Zmienione kluczowe pliki
*   `core/tarzanZmienneSygnalowe.py`: Dodano 40+ sygnałów statusu osi i komend.
*   `core/TSP/tarzanTspServer.py` i `tarzanTspSignals.py`: Rozszerzony katalog akcji administracyjnych.
*   `core/tarzanMode.py`: Zabezpieczona logika trybów manualnych i automatycznych.
*   `editor/PAR/tarzanParBridge.py`: Ujednolicony klient TSP z pełnym logowaniem sesji.
*   `editor/PAR/tarzanParPanels.py`: Ujednolicone sterowanie administracyjne.

## 3. Jak uruchomić na MiniPC
1.  Pobrać najnowszy kod (`git pull`).
2.  Zrestartować usługę: `sudo systemctl restart tarzan-tsp-lks-n5.service`.
3.  Upewnić się, że `Tarzan Mode Logic: STARTED` widnieje w logach.

## 4. Jak testować (Próba Generalna)
1.  **Handshake**: Połącz PAR w trybie LIVE (Handshake OK).
2.  **Statusy**: Sprawdź, czy diody w panelu SYSTEM (Linux, TSP, Bus, PoKeys) świecą na zielono.
3.  **Akcje**: Kliknij "RUN DIAGNOSTICS" w PAR i sprawdź, czy w logach miniPC rusza diagnostyka.
4.  **Tryby**: Zmień tryb na `tM`. Ruszając rRP (jeśli fizycznie podpięte), sprawdź czy sygnały `axis_..._dir/speed` zmieniają się w SignalBus.
5.  **Owner**: Sprawdź, czy `control_owner` zmienia się poprawnie (np. na `PAR_LIVE` po połączeniu).

## 5. Co ma się pojawić w logach (Sukces)
*   `Handshake OK: tarzanMiniPC` — potwierdzenie dwukierunkowej komunikacji.
*   `apply_snapshot: applied X signals` — synchronizacja stanu początkowego.
*   `Isolated Spawn Process` — start bezpiecznej diagnostyki LKS na MiniPC.

## 6. Gotowość Wykonawcza (Aktywacja Mięśni)
System TARZAN jest obecnie w pełni zespolony. MiniPC samodzielnie nadzoruje hardware, odtwarza ruch i nakłada korekty w czasie rzeczywistym. PAR pełni rolę nadrzędnej konsoli administracyjnej.

**Kluczowe osiągnięcia:**
*   Tor EHR -> TSP -> HW Bridge -> PoKeys Pulse Engine jest aktywny.
*   Logika MODE (tM, tAA) jest zintegrowana i bezpieczna.
*   Statusy fizyczne osi są widoczne w czasie rzeczywistym.

## 7. Ważne przypomnienia
*   **Źródło Prawdy**: Katalog sygnałów (nazwy, typy, role) znajduje się WYŁĄCZNIE w `core/tarzanZmienneSygnalowe.py`.
*   **Aktualny Stan**: `SignalBus` to jedyna tablica aktualnych wartości runtime. Żaden moduł nie powinien trzymać prywatnych kopii stanu sygnałów.
*   **Protokół**: Programowanie spina się z elektroniką przez TSP/SignalBus. Zakaz stosowania bezpośrednich skrótów do sprzętu z poziomu UI PAR.

---
*Dokumentacja wygenerowana przez JUNI dla systemu TARZAN.*
