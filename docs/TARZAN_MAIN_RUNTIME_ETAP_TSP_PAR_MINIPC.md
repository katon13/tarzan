# TARZAN MAIN RUNTIME — Etap Pełnego Zespolenia Wykonawczego (Etapy 0-17)

**Status:** PEŁNE ZESPOLENIE WYKONAWCZE. System przeszedł w tryb suwerennego Runtime na miniPC.
**Wersja:** 4.0 (Zespolenie Wykonawcze)
**Data:** 2026-06-05

## 1. Stan Implementacji (ZROBIONE)

### Etapy 6-7: PAR LIVE & Synchronizacja (ZROBIONE)
- **Status**: Stabilny, jedyny tor komunikacji PAR ↔ miniPC.
- **Zrealizowano**: Pełna synchronizacja dwukierunkowa bez pętli zwrotnych. Filtrowanie identycznych wartości w `SignalBus` skutecznie stabilizuje UI.

### Etap 8: PAR Administracja (ZROBIONE)
- **Status**: PAR jest suwerenną konsolą administracyjną. 
- **Zrealizowano**: Zdalne sterowanie wszystkimi modułami (Reboot, Diagnostyka, EHR/KHR Start/Stop) przez ujednolicone wywołania `TSP call_action`.

### Etap 13: Aktywacja Mięśni (ZROBIONE)
- **Status**: Tor wykonawczy odblokowany.
- **WAŻNE**: Flaga `safety_axis_unlock` została ustawiona na `True`. System generuje realne impulsy STEP/DIR na podstawie intencji w SignalBus.
- **Zrealizowano**: HardwareBridge generuje impulsy w trybie tM oraz zarządza osiami w trybie tAA.

### Etapy 14 i 15: EHR Playback & KHR Correction (ZROBIONE)
- **Status**: Wdrożone wykonanie ruchu.
- **EHR**: Pełna pętla playbacku (100Hz) na miniPC, aplikująca wiersze TAKE bezpośrednio do HardwareBridge.
- **KHR**: Mechanizm dynamicznego blendingu pozycji (offset KHR) działa w czasie rzeczywistym wewnątrz pętli wykonawczej.

### Etap 17: Sprzątanie i Optymalizacja (ZROBIONE)
- **Zrealizowano**: Usunięto martwą symulację ruchu z `tarzanTspSignals.py`.
- **Zrealizowano**: Usunięto duplikaty metod w `tarzanTspServer.py`.
- **Zrealizowano**: Oznaczono stare mostki (core/tarzanParBridge.py) jako przestarzałe.
- **Zrealizowano**: Uzupełniono katalog sygnałów o brakujące statusy diagnostyki LKS.

## 2. Architektura Toru Wykonawczego
Zasada nadrzędna:
`PAR / EHR / KHR / LKS → TSP / SignalBus → Snajper / Bridge / adaptery → hardware.`

`TarzanHardwareBridge` jest teraz aktywnym **adapterem wykonawczy** (LIVE_ADAPTER) dla SignalBus na miniPC. Każdy zapis do sygnału wyjściowego osi (np. `axis_cam_h_step`) jest natychmiast procesowany przez fizyczny silnik impulsów PoKeys.

## 3. Bezpieczeństwo i Testy
System jest w fazie pełnego działania:
1.  **Diagnostyka**: Izolowana w osobnym procesie, chroni Runtime przed błędami hardware.
2.  **Control Owner**: Twardo pilnuje priorytetów (np. blokada RRP podczas EHR Playback).
3.  **Safety**: Wyłącznik fizyczny STOP ma najwyższy priorytet sprzętowy (PoKeys).

## 4. Główne Przypomnienie
- **Źródło Prawdy**: `core/tarzanZmienneSygnalowe.py`.
- **Aktualny Stan**: `SignalBus`.
- **Protokół**: Programowanie ↔ Elektronika TYLKO przez protokół komunikacji.

---
*Dokumentacja zaktualizowana przez JUNI dla systemu TARZAN.*
