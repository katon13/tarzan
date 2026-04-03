
# TARZAN – HANDOFF DOCUMENT
## Status projektu na moment przekazania (handoff)

Ten dokument służy do wznowienia pracy nad projektem **TARZAN – Inteligentne Ramię Kamerowe** w nowym wątku rozmowy lub przez inną sesję.

Celem jest szybkie odtworzenie kontekstu bez konieczności przeglądania całej historii rozmowy.

---

# 1. Projekt

**Nazwa:** TARZAN – Inteligentne Ramię Kamerowe  
**Repozytorium:** https://github.com/katon13/tarzan  

Projekt buduje system sterowania ramieniem kamerowym oparty o:

- zapis ruchu w funkcji **czasu**
- protokół sygnałów sterujących
- edytor choreografii ruchu

System nie działa jak CNC (pozycja → ruch).  
Zamiast tego zapisuje **stan sygnałów w czasie**.

Czyli:

czas → stan sygnałów STEP / DIR / ENABLE / itd.

To jest kluczowa zasada architektury TARZAN.

---

# 2. Architektura projektu

Główna struktura repozytorium:

```
/tarzan
│
├── main.py
├── TarzanRejestr.json
│
├── core/
│
├── hardware/
│
├── mechanics/
│   └── tarzanMechanikaOsi.py
│
├── motion/
│   └── tarzanKrzyweRuchu.py
│
├── editor/
│   └── tarzanEdytorChoreografiiRuchu.py
│
└── data/
    └── take/
```

Najważniejsze moduły:

### mechanics
Opis mechaniki osi:

- limity ruchu
- profile startu
- rampy

Plik:
```
mechanics/tarzanMechanikaOsi.py
```

---

### motion

Logika matematyczna krzywych ruchu.

Plik:
```
motion/tarzanKrzyweRuchu.py
```

Odpowiada za:

- węzły ruchu
- normalizację linii
- ograniczenia mechaniczne
- interpolację

---

### editor

GUI do projektowania ruchu.

Plik:
```
editor/tarzanEdytorChoreografiiRuchu.py
```

Funkcje:

- edycja węzłów
- wizualizacja krzywej
- preview ruchu
- wygładzanie
- START / STOP
- tryb PAN

---

# 3. Aktualny stan edytora choreografii

Edytor jest **działającym prototypem**, ale **wymaga dalszych prac**.

### Co działa

- wybór osi
- edycja węzłów
- przeciąganie punktów
- podgląd krzywej
- tryb PAN
- funkcja wygładzania
- preview ruchu

### Co wymaga dalszej pracy

1️⃣ stabilizacja UI  

2️⃣ pola:
```
START
STOP
SMOOTH
```

3️⃣ synchronizacja z linią ruchu

4️⃣ uporządkowanie logiki:

```
editor/
motion/
mechanics/
```

5️⃣ optymalizacja kodu

6️⃣ dalsze testy matematyki ruchu

---

# 4. Zasady projektu (ważne)

Podczas dalszej pracy należy przestrzegać kilku zasad:

### 1️⃣ Nie zmieniać architektury bez potrzeby

Projekt jest podzielony na:

```
mechanics
motion
editor
```

Nie należy mieszać tych warstw.

---

### 2️⃣ Nie przenosić wszystkiego do jednego pliku

Każdy moduł ma swoją odpowiedzialność.

---

### 3️⃣ Zawsze bazować na dokumentacji mechaniki

Plik:

```
mechanics/tarzanMechanikaOsi.py
```

definiuje fizykę systemu.

---

### 4️⃣ Oś czasu

System działa na:

```
CZAS_PROBKOWANIA_MS = 10
```

Nie należy zmieniać tego bez powodu.

---

# 5. Edytor – założenia projektowe

Edytor operuje na:

```
jednej ciągłej linii ruchu
z wieloma węzłami
```

Metoda:

```
Wygładź
```

powinna:

- wygładzać przebieg
- **nie dodawać nowych węzłów**
- **nie usuwać węzłów**

---

# 6. Kolejne kroki rozwoju

W nowym wątku pracy należy:

### krok 1

ustabilizować edytor

### krok 2

naprawić pola:

```
START
STOP
SMOOTH
```

### krok 3

rozbudować mechanikę ograniczeń

### krok 4

przygotować zapis choreografii

### krok 5

integracja z protokołem ruchu

---

# 7. Status commit

Projekt można teraz wysłać do repozytorium z komentarzem:

```
Editor prototype – requires further work
```
lub

```
Initial choreography editor prototype
```

---

# 8. Jak rozpocząć nowy wątek

W nowej rozmowie należy napisać:

```
Kontynuujemy projekt TARZAN.
Poniżej aktualny handoff projektu.
```
i wkleić zawartość tego pliku.

---

# Koniec dokumentu
