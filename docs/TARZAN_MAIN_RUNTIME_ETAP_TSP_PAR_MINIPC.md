# TARZAN MAIN RUNTIME — Etap: Fundament MAIN RUNTIME / etap TSP-PAR (Wdrożenie MiniPC)

**Status:** Gotowy do wdrożenia fundamentu / Próba generalna połączenia
**Wersja:** 1.0  
**Data:** 2026-06-05

## 1. Co zostało wdrożone
Ten etap stanowi fundament "układu nerwowego" systemu TARZAN, łącząc MiniPC (Runtime) ze Stacją (Administracja PAR).

*   **Zespolenie SignalBus**: Centralna magistrala sygnałów w trybie LIVE synchronizuje się między urządzeniami.
*   **TSP Server (MiniPC)**: Rozszerzony start w `TarzanTspServer.start()` inicjalizuje `SignalBus`, ustawia stan `BOOTING` i uruchamia diagnostykę LKS przygotowaną do testu na miniPC.
*   **PAR Bridge (Stacja)**: Zintegrowany klient TSP, który automatycznie łączy się z MiniPC po przełączeniu PAR w tryb LIVE.
*   **Protokół Komunikacji**: Pełny handshake (HELLO, PING, GET_STATE, SUBSCRIBE) zapewniający spójność danych zaraz po połączeniu.
*   **Bezpieczeństwo**: Mechanizm `control_owner` przygotowany do blokowania konfliktów sterowania (np. blokada osi podczas pracy EHR).

## 2. Zmienione kluczowe pliki
*   `core/tarzanZmienneSygnalowe.py`: Dodanie sygnałów systemowych (`system_state`, `runtime_state`, `control_owner` itd.).
*   `core/tarzanSignalBus.py`: Implementacja `apply_snapshot` z filtrowaniem zmian (brak pętli zwrotnych).
*   `core/TSP/tarzanTspServer.py`: Nowa logika startu Main Runtime i asynchroniczna diagnostyka.
*   `core/TSP/tarzanTspSignals.py`: Przepięcie providera TSP na realny `SignalBus`.
*   `editor/PAR/tarzanParBridge.py`: Implementacja asynchronicznego konektora TSP Client.

## 3. Jak uruchomić na MiniPC
1.  Pobrać najnowszy kod na MiniPC (`git pull`).
2.  Zrestartować usługę nadzorczą:
    ```bash
    sudo systemctl restart tarzan-tsp-lks-n5.service
    ```
3.  Sprawdzić logi serwera:
    ```bash
    tail -f data/logi/tsp/tsp.log
    ```
    Powinien pojawić się wpis: `TSP Server running on 0.0.0.0:7777` oraz `system_state -> BOOTING`.

## 4. Jak testować PAR LIVE (Stacja)
1.  Uruchomić PAR na Stacji.
2.  W nagłówku kliknąć przycisk **LIVE**.
3.  Obserwować panel logów w PAR:
    - Powinno pojawić się: `TSP: Starting TSP connector thread (LIVE)...`
    - Następnie: `TSP: Connected. Sending HELLO...`
    - Na końcu: `TSP: Handshake OK: tarzanMiniPC`.
4.  Sprawdzić, czy stan `system_state` w PAR odzwierciedla stan z MiniPC.

## 5. Co ma się pojawić w logach (Sukces)
*   `Handshake OK: tarzanMiniPC` — potwierdzenie dwukierunkowej komunikacji.
*   `apply_snapshot: applied X signals` — synchronizacja stanu początkowego.
*   `Diagnostics started` / `Diagnostics finished` — na MiniPC.

## 6. Co jeszcze nie jest pełne (Następne etapy)
Po potwierdzeniu stabilnego połączenia TSP i synchronizacji stanów, w kolejnych etapach wdrożone zostaną:

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
