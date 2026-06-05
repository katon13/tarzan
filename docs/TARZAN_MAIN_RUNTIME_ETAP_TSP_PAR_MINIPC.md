# TARZAN MAIN RUNTIME — Etapy 6, 7, 8, 13 (Zespolenie Logiczne)

**Status:** Fundament wdrożony. Etapy 6, 7, 8 i 13 (logiczne) zamknięte.
**Wersja:** 2.0
**Data:** 2026-06-05

## 1. Stan Implementacji

### Etap 6: PAR LIVE przez TarzanParBridge (ZAMKNIĘTY)
- **Status**: Stabilny, jedyny tor komunikacji PAR ↔ miniPC.
- **Zrealizowano**: Bridge zarządza cyklem życia `TarzanTspClient`. Handshake (HELLO, PING, GET_STATE, SUBSCRIBE) jest kompletny i zsynchronizowany.
- **Zrealizowano**: Wszystkie dane z miniPC trafiają do lokalnego SignalBus PAR przez `apply_snapshot`.

### Etap 7: Dwukierunkowa Synchronizacja (ZAMKNIĘTY)
- **Status**: Pełny przepływ informacji MiniPC ↔ PAR bez pętli zwrotnych.
- **Zrealizowano**: Filtrowanie identycznych wartości w `SignalBus.apply_snapshot` i `force_signal`.
- **Zrealizowano**: TSP Server zwraca czytelne statusy zapisu (`OK`, `UNKNOWN_SIGNAL`, `WRITE_DENIED`).

### Etap 8: PAR jako Pełna Administracja (ZAMKNIĘTY LOGICZNIE)
- **Status**: PAR w trybie LIVE kontroluje runtime przez TSP/SignalBus.
- **Zrealizowano**: Ujednolicone wywołania administracyjne przez `bridge.call_action(...)` i `bridge.write_output(...)`.
- **Zrealizowano**: Panel SYSTEM wyświetla stan hardware LKS, statystyki TSP i pozwala na akcje: `Diagnostyka`, `Take Control`, `Reboot`.
- **Zrealizowano**: Zdalne sterowanie modułami EHR/KHR (Start/Stop).

### Etap 13: RRP / SOK / Osie (ZAMKNIĘTY LOGICZNIE)
- **Status**: Logiczne spięcie modułów manualnych przez SignalBus/TSP/Snajper.
- **Zrealizowano**: Dopisanie pełnej mapy statusów osi (`axis_*_ready`, `alarm`, `enabled`, `owner`, `last_error`) do katalogu centralnego.
- **Zrealizowano**: Logika `tarzanMode.py` (tM) mapuje rRP/SOK na sygnały `dir` wybranej osi z uwzględnieniem blokad bezpieczeństwa i gotowości.
- **UWAGA BEZPIECZEŃSTWA**: Na tym etapie tor jest gotowy LOGICZNIE. Fizyczne impulsy STEP/DIR zostaną uruchomione po osobnym zatwierdzeniu operatora (Etap 13 Wykonawczy).

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

## 6. Co jeszcze nie jest pełne (Następne etapy)
Po potwierdzeniu stabilnego połączenia TSP i synchronizacji stanów (oraz weryfikacji odporności na crashe PoKeys), w kolejnych etapach wdrożone zostaną:

*   **Realne wykonanie hardware**: Podpięcie Snajpera do fizycznych wyjść PoKeys i sterowników CNC.
*   **Obsługa LCD i Matrix**: Wyświetlanie stanu systemowego na lokalnych peryferiach MiniPC.
*   **Ruch Osi**: Pełna kontrola nad STEP/DIR, ENABLE i inwentaryzacją osi (Etap 13).
*   **EHR Playback**: Odtwarzanie nagranych przebiegów i strumieniowanie punktów przez TSP.
*   **Logika MODE / RRP / SOK**: Pełne zespolenie trybów pracy na gotowym organizmie runtime.
*   **Pełny MODE**: Moduł `tarzanMode.py` jest obecnie w fazie wstępnej integracji sygnałowej.

## 7. Ważne przypomnienia
*   **Źródło Prawdy**: Katalog sygnałów (nazwy, typy, role) znajduje się WYŁĄCZNIE w `core/tarzanZmienneSygnalowe.py`.
*   **Aktualny Stan**: `SignalBus` to jedyna tablica aktualnych wartości runtime. Żaden moduł nie powinien trzymać prywatnych kopii stanu sygnałów.
*   **Protokół**: Programowanie spina się z elektroniką przez TSP/SignalBus. Zakaz stosowania bezpośrednich skrótów do sprzętu z poziomu UI PAR.

---
*Dokumentacja wygenerowana przez JUNI dla systemu TARZAN.*
