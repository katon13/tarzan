
# TARZAN_HANDOFF.md
Stan projektu i punkt kontynuacji pracy

Projekt: TARZAN – Intelligent Camera Arm System

Ten dokument pozwala rozpocząć pracę nad projektem w nowym wątku bez utraty kontekstu architektury, mechaniki i zasad systemu.

---

# 1. CEL SYSTEMU TARZAN

TARZAN jest systemem sterowania ramieniem kamery umożliwiającym:

• nagrywanie ruchu kamery  
• odtwarzanie ruchu kamery  
• tworzenie choreografii ruchu  
• synchronizację ruchu z ujęciem filmowym (TAKE)

System działa **nie jak CNC**.

System działa jako **rejestrator i odtwarzacz sygnałów ruchu w czasie**.

Podstawą systemu jest protokół sygnałów STEP/DIR zapisany w czasie.

---

# 2. ZASADA PROTOKOŁU RUCHU

System nie zapisuje pozycji osi.

System zapisuje **stan sygnałów sterujących w czasie**.

Każda próbka zawiera:

czas  
STEP  
DIR  
ENABLE  
stan czujników  

Częstotliwość próbkowania:

CZAS_PROBKOWANIA_MS = 10

czyli:

100 próbek na sekundę

---

# 3. OSIE SYSTEMU

Nazwy osi muszą być zgodne z mapą projektu.

## Osie kamery

oś pozioma kamery  
oś pionowa kamery  
oś pochyłu kamery  
oś ostrości kamery  

## Osie ramienia

oś pionowa ramienia  
oś pozioma ramienia  

Nie wolno używać nazw zastępczych.

---

# 4. MECHANIKA OSI

Każda oś posiada:

• maksymalną liczbę impulsów ruchu  
• maksymalną prędkość  
• maksymalne przyspieszenie  
• ograniczenia zakresu ruchu

Mechanika nie blokuje edycji.

Mechanika **ogranicza możliwy wynik ruchu**.

---

# 5. ZASADA TAKE

TAKE to pojedyncze ujęcie filmowe.

TAKE zawiera:

• czas całkowity
• przebiegi osi
• sygnały sterujące

Ten sam TAKE może być odtworzony w różnych prędkościach poprzez zmianę czasu.

---

# 6. EDYTOR CHOREOGRAFII RUCHU

Edytor pozwala projektować ruch osi jako krzywe.

Najważniejsze zasady:

• krzywa określa intensywność ruchu
• amplituda krzywej określa prędkość
• znak krzywej określa kierunek

---

# 7. ZASADA MECHANIKI W EDYTORZE

Mechanika powinna wynikać z geometrii krzywej.

Operator powinien odczuwać ograniczenia poprzez:

• maksymalną długość linii
• maksymalną amplitudę
• brak możliwości dalszego przeciągania punktów

Nie przez komunikaty tekstowe.

---

# 8. PAN

PAN przesuwa całą oś w czasie.

PAN działa:

• po kliknięciu w obszar aktywnej osi
• nie tylko po kliknięciu START/STOP

---

# 9. SMOOTH

Funkcja wygładzania:

• wygładza cały przebieg
• nie dodaje nowych węzłów

---

# 10. WSKAŹNIKI P / R / A

P – impuls  
R – prędkość  
A – przyspieszenie  

Są informacyjne i nie blokują edycji.

---

# 11. AKTUALNY STAN EDYTORA

Aktualna wersja zawiera:

• PAN po obszarze osi
• możliwość edycji punktów
• integrację z mechaniką osi
• wskaźniki parametrów ruchu

---

# 12. REPOZYTORIUM

https://github.com/katon13/tarzan

---

# 13. PUNKT STARTOWY DALSZEJ PRACY

Aktualny etap:

Integracja **mechaniki osi z edytorem choreografii ruchu**.
