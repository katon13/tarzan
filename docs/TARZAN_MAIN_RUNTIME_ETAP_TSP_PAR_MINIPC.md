# TARZAN MAIN RUNTIME — Etap Uruchomieniowy Fundamentu (Etapy 0-13)

**Status:** Fundament ZESPOLONY. Etapy 6-13 (Logiczne) domknięte. Etapy 14-15 (Wykonawcze) w trakcie (SZKIELET).
**Wersja:** 3.1 (Korekta merytoryczna)
**Data:** 2026-06-05

## 1. Stan Implementacji (ZROBIONE / CZĘŚCIOWE / NIEGOTOWE)

### Etap 6: PAR LIVE przez TarzanParBridge (ZROBIONE)
- **Status**: Stabilny, jedyny tor komunikacji PAR ↔ miniPC.
- **Zrealizowano**: Bridge zarządza cyklem życia `TarzanTspClient`. Handshake (HELLO, PING, GET_STATE, SUBSCRIBE) jest kompletny.
- **Weryfikacja**: Wymaga potwierdzenia z realnym serwerem na miniPC.

### Etap 7: Dwukierunkowa Synchronizacja (CZĘŚCIOWE)
- **Status**: Mechanizm wdrożony, oczekuje na weryfikację z realnym hardware i wejściami.
- **Zrealizowano**: Filtrowanie identycznych wartości w `SignalBus.apply_snapshot` i `force_signal` (ochrona przed pętlą).
- **Zrealizowano**: TSP Server zwraca czytelne statusy zapisu (`OK`, `WRITE_DENIED`).

### Etap 8: PAR Administracja Fundament (CZĘŚCIOWE)
- **Status**: Fundament administracji wdrożony. Pozwala na zdalne akcje (Diagnostyka, Reboot, Take Control).
- **Uwaga**: Nie jest to jeszcze "pełna administracja" wszystkich modułów. Wsparcie dla pełnego panelu operatorskiego RRP/SOK/osi/Nextion7 jest w fazie integracji logicznej.
- **Zrealizowano**: Ujednolicone wywołania przez `bridge.call_action(...)`.

### Etap 13: RRP / SOK / Osie Logiczne (CZĘŚCIOWE)
- **Status**: Spięcie logiczne modułów manualnych i automatycznych przez tor SignalBus.
- **WAŻNE**: Fizyczna generacja impulsów STEP/DIR jest JAWNIE ZABLOKOWANA (`safety_axis_unlock=False`).
- **Wymagane**: Osobny test bezpieczeństwa operatora przed aktywacją ruchu fizycznego.
- **Zrealizowano**: Dopisanie pełnej mapy statusów osi do katalogu centralnego. Logika `tarzanMode.py` (tM) mapuje rRP/SOK na sygnały w SignalBus.

### Etap 14 i 15: EHR Playback & KHR Correction (NIEGOTOWE / SZKIELET)
- **Status**: SZKIELET / POC.
- **Zrealizowano**: `TarzanHardwareBridge` jako fundament toru wykonawczego.
- **EHR**: Początki toru playbacku (100Hz), ale nie jest to jeszcze pełne odtwarzanie TAKE z krzywymi.
- **KHR**: Prosty mechanizm blendingu pozycji (offset KHR), wymagający rozbudowy do pełnej korekty dynamicznej.

## 2. Architektura Toru Wykonawczego
Nadal obowiązuje zasada:
`PAR / EHR / KHR / LKS → TSP / SignalBus → Snajper / Bridge / adaptery → hardware.`

`TarzanHardwareBridge` został zaimplementowany jako **adapter wykonawczy** dla SignalBus. Nie jest on "prywatnym skrótem", lecz częścią toru Snajpera na miniPC, reagującą na sygnały systemowe.

## 3. Bezpieczeństwo i Testy (SAFETY CHECKLIST)
Przed przejściem do testów fizycznych (Aktywacja Mięśni):
1.  **Test Logiczny**: Potwierdzenie `Handshake OK` i stabilności synchronizacji sygnałów systemowych.
2.  **Test Odporności**: Weryfikacja, czy błędy libusb/PoKeys nie zabijają serwera TSP.
3.  **Audit Bezpieczeństwa**: Sprawdzenie, czy `control_owner` poprawnie blokuje nieautoryzowany dostęp do osi (np. blokada RRP podczas EHR Playback).
4.  **Weryfikacja Mechaniczna**: Sprawdzenie krańcówek i fizycznego wyłącznika STOP.
5.  **Jawne Odblokowanie**: Zmiana `safety_axis_unlock = True` w `core/tarzanHardwareBridge.py` TYLKO po spełnieniu powyższych punktów przez uprawnionego operatora.

UWAGA: Kod w obecnej wersji (v3.1) ma JAWNIE ZABLOKOWANĄ generację impulsów fizycznych.

## 4. Główne Przypomnienie
- **Źródło Prawdy**: `core/tarzanZmienneSygnalowe.py`.
- **Aktualny Stan**: `SignalBus`.
- **Protokół**: Programowanie ↔ Elektronika TYLKO przez protokół komunikacji.

---
*Dokumentacja zaktualizowana przez JUNI dla systemu TARZAN.*
