# TARZAN Motion Model

## Matematyczny model choreografii ruchu systemu TARZAN

------------------------------------------------------------------------

## 1. Wprowadzenie

System **TARZAN** steruje ruchem ramienia kamerowego poprzez generowanie
sygnałów **STEP / DIR / ENABLE** w funkcji czasu.

W przeciwieństwie do systemów CNC, które opisują ruch jako przejście
pomiędzy pozycjami, TARZAN opisuje ruch jako **ciągłą funkcję czasu**.

**Filozofia systemu:**

    czas → natężenie ruchu → gęstość impulsów → impulsy STEP → ruch mechaniczny

------------------------------------------------------------------------

# 2. Oś czasu systemu

Czas systemu jest dyskretyzowany:

$$
t_n = n \cdot \Delta t
$$

gdzie:

- $t_n$ --- n-ta próbka czasu\
- $n$ --- numer próbki\
- $\Delta t$ --- krok próbkowania

W systemie TARZAN:

$$
\Delta t = CZAS\_PROBKOWANIA\_MS = 10ms
$$

czyli:

    t = 0, 10, 20, 30, ...

------------------------------------------------------------------------

# 3. Funkcja natężenia ruchu

Ruch osi opisuje funkcja:

$$
A(t)
$$

gdzie:

- $A(t)$ --- amplituda / natężenie ruchu
- $t$ --- czas

Funkcja ta tworzona jest z punktów kontrolnych:

    (t0, A0)
    (t1, A1)
    (t2, A2)
    ...

Interpolacja spline tworzy **gładką funkcję ruchu**.

------------------------------------------------------------------------

# 4. Gęstość impulsów STEP

Natężenie ruchu przekształcane jest w gęstość impulsów:

$$
\rho(t) = k \cdot |A(t)|
$$

gdzie:

- $\rho(t)$ --- gęstość impulsów (impuls/ms)
- $k$ --- współczynnik skalowania
- $A(t)$ --- funkcja natężenia ruchu

Interpretacja:

    ρ(t) mówi ile impulsów STEP przypada na jednostkę czasu

------------------------------------------------------------------------

# 5. Liczba impulsów w segmencie

Dla segmentu ruchu obowiązuje:

$$
N = \int_{t_0}^{t_1} \rho(t)\, dt
$$

gdzie:

- $N$ --- liczba impulsów
- $t_0, t_1$ --- granice segmentu
- $\rho(t)$ --- gęstość impulsów

Interpretacja:

**liczba impulsów = pole pod krzywą**.

------------------------------------------------------------------------

# 6. Generator impulsów STEP

Generator impulsów działa jako integrator:

$$
\sum \rho(t) dt \ge 1
$$

czyli:

    gdy suma osiąga 1 → generowany jest impuls STEP

Mechanizm ten nazywany jest **akumulatorem impulsów**.

------------------------------------------------------------------------

# 7. Dyskretny protokół sterowania

Na podstawie impulsów powstaje timeline sygnałów:

    STEP
    DIR
    ENABLE

dla kolejnych chwil czasu:

    t0
    t1
    t2
    ...

stan sygnałów:

$$
STEP(t_n), DIR(t_n), ENABLE(t_n)
$$

------------------------------------------------------------------------

# 8. Matematyczny model jednej osi

$$
STEP(t_n) =
\begin{cases}
1 & \text{jeśli } \int_{t_{n-1}}^{t_n} \rho(t)\,dt \ge 1 \\
0 & \text{w przeciwnym przypadku}
\end{cases}
$$

gdzie:

- $STEP(t_n)$ --- impuls STEP
- $\rho(t)$ --- gęstość impulsów
- $t_n$ --- próbka czasu

------------------------------------------------------------------------

# 9. Model wielu osi

Jeżeli system posiada **M osi**:

$$
i = 1..M
$$

każda oś posiada własną funkcję ruchu:

$$
A_i(t)
$$

oraz gęstość impulsów:

$$
\rho_i(t) = k_i \cdot |A_i(t)|
$$

Impuls dla osi $i$:

$$
STEP_i(t_n) =
\begin{cases}
1 & \text{jeśli } \int_{t_{n-1}}^{t_n} \rho_i(t)\,dt \ge 1 \\
0 & \text{w przeciwnym przypadku}
\end{cases}
$$

Stan systemu:

$$
S(t_n) =
\begin{bmatrix}
STEP_1(t_n) \\
STEP_2(t_n) \\
\vdots \\
STEP_M(t_n)
\end{bmatrix}
$$

------------------------------------------------------------------------

# 10. Interpretacja fizyczna

Model TARZANA opisuje ruch jako:

    energia ruchu w funkcji czasu

a nie jako:

    pozycja → pozycja

Dzięki temu:

- ruch jest bardzo płynny
- łatwa synchronizacja osi
- naturalna choreografia kamerowa

------------------------------------------------------------------------

# 11. Fundamentalne równanie TARZAN

$$
STEP_i(t_n) =
\begin{cases}
1 & \text{jeśli } \int_{t_{n-1}}^{t_n} k_i |A_i(t)| dt \ge 1 \\
0 & \text{w przeciwnym przypadku}
\end{cases}
$$

gdzie:

- $A_i(t)$ --- funkcja natężenia ruchu osi\
- $k_i$ --- współczynnik przeliczenia na impulsy\
- $STEP_i(t_n)$ --- impuls sterujący silnikiem

To równanie opisuje **matematyczny fundament systemu TARZAN**.

------------------------------------------------------------------------

# 12. Diagram przepływu matematycznego systemu TARZAN

Poniższy diagram przedstawia pełny przepływ matematyczny systemu -- od
choreografii TAKE do impulsów sterujących silnikami.

```mermaid
flowchart TD

A[TAKE Choreography] --> B[A(t)\nFunction of motion intensity]
B --> C[ρ(t)\nPulse density]
C --> D[∫ ρ(t) dt\nPulse integration]
D --> E[STEP(t)\nGenerated step impulses]
E --> F[Motor driver]
F --> G[Mechanical motion of axis]
```

Interpretacja:

1. **TAKE** -- zapis choreografii ruchu kamery.
2. **A(t)** -- funkcja natężenia ruchu powstała z interpolacji punktów
   kontrolnych.
3. **ρ(t)** -- gęstość impulsów STEP wynikająca z amplitudy ruchu.
4. **∫ρ(t)dt** -- integracja gęstości impulsów w czasie.
5. **STEP(t)** -- wygenerowane impulsy sterujące.
6. **Motor driver** -- sterownik silnika.
7. **Mechanical motion** -- rzeczywisty ruch osi systemu TARZAN.

Diagram pokazuje, że TARZAN jest systemem **time‑driven motion
control**, gdzie sterowanie ruchem wynika bezpośrednio z funkcji czasu.
