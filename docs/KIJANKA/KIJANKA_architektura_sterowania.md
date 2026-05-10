# KIJANKA_architektura_sterowania.md
# KIJANKA — architektura sterowania

## 1. Warstwa 1 — wykonawcza
Lokalne serwo każdego koła:
- pozycja
- prędkość
- hamulec
- enkoder

## 2. Warstwa 2 — kompensacja
Sterownik kompensacji:
- dane z IMU
- dane z pozycji kół
- korekcja wysokości
- limity i bezpieczeństwo

## 3. Warstwa 3 — system nadrzędny
TARZAN / EHR / TAKE:
- zapis przejazdu
- odtwarzanie
- synchronizacja z osią przejazdu
- logika sceny

## 4. Zasada
Nie mieszać:
- szybkiej automatyki lokalnej
- logiki scenicznej
- funkcji bezpieczeństwa

## 5. Wniosek
Sterowanie ma być warstwowe, bo tylko wtedy układ będzie jednocześnie:
- szybki
- czytelny
- rozwijalny
