# Dokumentacja Implementacji: TARZAN MAIN RUNTIME (Etap TSP/PAR)

**Wersja:** 1.0  
**Data:** 2026-06-05  
**Autor:** JUNI

## 1. Podsumowanie zmian
Zrealizowano fundamenty **TARZAN MAIN RUNTIME**, łącząc MiniPC (Runtime/LKS/TSP) ze Stacją PAR w jeden spójny organizm komunikacyjny. Głównym celem tego etapu było ustanowienie niezawodnego "układu nerwowego" systemu opartego na protokole TSP.

### Co dodano:
- **Centralny Katalog Sygnałów**: Rozszerzono `core/tarzanZmienneSygnalowe.py` o sygnały systemowe (`system_state`, `runtime_state`, `control_owner`) oraz stany modułów.
- **Zoptymalizowany SignalBus**: Wprowadzono metodę `apply_snapshot` w `core/tarzanSignalBus.py` z filtrowaniem zmian, co zapobiega pętlom zwrotnym i nadmiarowemu odświeżaniu UI.
- **Fundament MAIN RUNTIME / etap TSP-PAR**: Rozszerzono `TarzanTspServer` o automatyczny start, diagnostykę LKS przygotowaną do testu na miniPC oraz nadzór nad stanem `BOOTING`.
- **Integracja PAR LIVE**: `TarzanParBridge` posiada teraz wbudowanego klienta TSP, który automatycznie synchronizuje stan z MiniPC po przełączeniu w tryb LIVE.
- **Bezpieczeństwo (Control Owner)**: Wdrożono mechanizm `control_owner`, który blokuje manualne sterowanie osiami podczas playbacku EHR (`WRITE_DENIED`).

## 2. Źródło prawdy dla sygnałów
Zgodnie z zasadą nadrzędną, jedynym źródłem prawdy dla definicji sygnałów w systemie TARZAN jest plik:
**`core/tarzanZmienneSygnalowe.py`**

Wszystkie moduły (PAR, EHR, KHR, LKS) muszą używać nazw i ról zdefiniowanych w tym katalogu. `SignalBus` służy jedynie jako tablica aktualnych wartości tych sygnałów w czasie rzeczywistym.

## 3. Instrukcja testowania na MiniPC
Aby zweryfikować poprawność implementacji na realnym sprzęcie:

1.  **Wdrożenie**: Wykonaj `git pull` na MiniPC i upewnij się, że usługa `tarzan-tsp-lks-n5.service` korzysta z najnowszego kodu.
2.  **Restart**: Zrestartuj usługę: `sudo systemctl restart tarzan-tsp-lks-n5.service`.
3.  **Weryfikacja Serwera**: Sprawdź logi na MiniPC: `tail -f data/logi/tsp/tsp.log`. Powinieneś zobaczyć start serwera na porcie 7777 oraz logi z diagnostyki LKS.
4.  **Połączenie PAR**: Na stacji operatorskiej uruchom PAR i kliknij przycisk **LIVE**.
5.  **KROK ZERO**: Sprawdź w panelu logów PAR, czy pojawił się komunikat `Handshake OK` oraz czy sygnał `system_state` przyjął wartość `BOOTING` (a docelowo `READY_FOR_PAR`).
6.  **Sterowanie**: Spróbuj zmienić dowolny sygnał wyjściowy w PAR i potwierdź w logach serwera MiniPC, że zmiana została odebrana i wpisana do magistrali.

## 4. Co jeszcze nie jest pełne (Backlog)
- **Realna logika MODE**: Moduł `core/tarzanMode.py` wymaga dalszego rozszerzenia o konkretne reguły dla trybów `tMAS`, `tAA`, itp.
- **EHR Stream**: Przesyłanie dużych zestawów danych (krzywych) przez TSP wymaga optymalizacji pakietów.
- **Hardware Feedback**: Niektóre adaptery sprzętowe mogą wymagać dostrojenia do nowej architektury `SignalBus`.
- **Nextion 5/7**: Pełna integracja statusów systemowych na ekranach Nextion.

---
*Dokumentacja wygenerowana automatycznie w ramach procesu zespolenia TARZAN MAIN RUNTIME.*
