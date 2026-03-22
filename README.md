# TARZAN©

## Intelligent Cinematic Camera Arm System

### Z pełną kontrolą choreografi ruchu

autor: Paweł Zastrzeżyński

TARZAN jest systemem sterowania ramieniem kamerowym przeznaczonym do  
realizacji płynnych, filmowych ruchów kamery.  

System umożliwia:  

- nagrywanie ruchu wszystkich osi w czasie,  
- edycję choreografii ruchu,  
- generowanie automatycznego ruchu kamerowego,  
- synchronizację osi ramienia i kamery,  
- przygotowanie ujęć wg  zautomatyzowanych trybów operatorskich.

## Dokumentacja

- [Mapa projektu](docs/MAPA_PROJEKTU_TARZANA.md)  
- [Struktura plików](docs/STRUKTURA_PLIKOW_TARZAN.md)  
- [Mapa choreografii ruchu](docs/TARZAN_CHOREOGRAFIA_RUCHU_MAPA.md)  
- [Model matematyczny ruchu](docs/TARZAN_CHOREOGRAFIA_RUCHU_MOEDEL_MATEMATYCZNY.md)  
- [Architektura systemu](docs/TARZAN_SYSTEM_ARCHITECTURE.md)  

## Główna idea

TARZAN nie działa jak klasyczny system CNC.  
Ruch jest opisywany jako przebieg sterowania w czasie, a nie jako przejście pomiędzy pozycjami.  

## Struktura projektu

- `core/` – rdzeń systemu  
- `hardware/` – warstwa sprzętowa  
- `mechanics/` – mechanika osi  
- `motion/` – planowanie i synteza ruchu  
- `editor/` – edytor choreografii  
- `modes/` – tryby pracy  
- `safety/` – bezpieczeństwo  
- `docs/` – dokumentacja  

## Status

Projekt w trakcie rozwoju.
