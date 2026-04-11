# TARZAN – Zasady commitów projektu

Dokument opisuje zasady zapisywania zmian w repozytorium projektu TARZAN.

Celem jest zachowanie czytelnej historii rozwoju systemu.

---

# 1. Jedna zmiana = jeden commit

Commit powinien opisywać jedną logiczną zmianę w projekcie.

Nie należy łączyć wielu różnych zmian w jednym commicie.

Przykład dobrego podejścia:

motion: dodanie wygładzania trajektorii  
motion: implementacja motion planner  
motion: dodanie analizatora segmentów

---

# 2. Commit musi opisywać zmianę

Nie używamy opisów typu:

update  
changes  
fix

Zamiast tego opisujemy rzeczywistą zmianę.

Przykłady:

Dodanie szkieletu motion planner  
Implementacja ograniczeń mechanicznych osi  
Aktualizacja timeline edytora choreografii  
Dodanie struktury safety manager  
Poprawka mapowania sygnałów PoKeys  
Aktualizacja dokumentacji projektu

---

# 3. Prefiks modułu

Jeżeli zmiana dotyczy konkretnego modułu systemu,
należy dodać prefiks.

Przykłady:

motion: dodanie wygładzania trajektorii  
safety: implementacja zatrzymania awaryjnego  
editor: poprawa zoomu timeline  
docs: aktualizacja mapy architektury projektu  
mechanics: dodanie kompensacji luzów

---

# 4. Tagowanie etapów projektu

Tagi Git oznaczają ważne etapy rozwoju systemu.

Przykład:

v0.1.0  – uporządkowana struktura projektu  
v0.2.0  – system mechaniki osi  
v0.3.0  – motion planner  
v0.4.0  – protokół ruchu  
v0.5.0  – edytor choreografii  
v1.0.0  – pierwszy pełny system

Tagi tworzymy tylko dla ważnych etapów projektu.

---

# 5. Cel

Historia Git powinna dokumentować rozwój systemu TARZAN
i umożliwiać łatwe odtworzenie kolejnych etapów projektu.
