# TARZAN MAIN RUNTIME — Zespolenie Systemowe (Etapy 0-16)

**Status:** Logika zaimplementowana / Gotowy do testów integracyjnych na MiniPC
**Wersja:** 1.2  
**Data:** 2026-06-05

## 1. Co zostało wdrożone (Aktualizacja)
Ten etap stanowi pełne zespolenie "układu nerwowego" i "mózgu" systemu TARZAN.

*   **Zespolenie SignalBus (Etapy 0-7)**: Centralna magistrala synchronizuje się między MiniPC a Stacją w trybie LIVE.
*   **PAR jako Administracja (Etap 8)**: Nowy panel SYSTEM w PAR umożliwia:
    - Podgląd szczegółowego statusu LKS Hardware.
    - Wywoływanie akcji: Manualna Diagnostyka, Zmiana Właściciela (Take Control), Reboot MiniPC.
    - Monitorowanie statystyk sieciowych TSP (Etap 16).
*   **EHR/KHR jako Bloki Systemowe (Etap 9)**: 
    - EHR i KHR raportują swój stan (`ehr_state`, `khr_state`) do SignalBus.
    - Automatyczne połączenie z TSP po uruchomieniu w trybie LIVE.
*   **Logika MODE (Etap 12)**: Moduł `tarzanMode.py` zarządza priorytetami i przełącza źródła sterowania.
*   **Integracja rRP/SOK (Etap 13)**: Ruch manualny osiami przez rRP jest teraz częścią głównego toru (rRP -> PoKeys -> SignalBus -> ModeLogic -> Osie).
*   **Bezpieczeństwo**: Pełna izolacja diagnostyki PoKeys (multiprocessing spawn) zapobiegająca crashom całego systemu.

## 2. Zmienione kluczowe pliki
*   `core/tarzanZmienneSygnalowe.py`: Pełny katalog sygnałów systemowych i komend.
*   `core/TSP/tarzanTspServer.py`: Obsługa komend administracyjnych i statystyk.
*   `core/tarzanMode.py`: Logika trybów (tM, tAA).
*   `editor/PAR/tarzanParPanels.py`: Rozbudowa UI o panele statusu i akcji.
*   `editor/EHR/tarzanEhrUi.py` i `editor/tarzanKHR.py`: Raportowanie stanów modułów.

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
