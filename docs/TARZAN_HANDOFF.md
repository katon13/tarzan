
# TARZAN_HANDOFF.md
## TARZAN Motion Engine – STEP Generator Concept (Stable Version)

This document captures the **working understanding of the STEP generator** that finally produced correct results in the TARZAN editor.  
It should be used as a **reference for future development** so the generator logic is not accidentally broken again.

---

# 1. Core Principle of TARZAN Motion

TARZAN does **not generate position trajectories directly**.

Instead the system works with:

curve → amplitude → pulse density → STEP pulses

The curve defines **motion intensity over time**, not position.

This is crucial.

The STEP generator converts the **shape of the curve** into **distribution of impulses over time**.

---

# 2. Global Time Base

The entire TARZAN system operates on a fixed sampling interval:

```
CZAS_PROBKOWANIA_MS = 10 ms
```

Every 10 ms the system evaluates:

- amplitude of the curve
- direction
- pulse density

This creates a **timeline matrix** of control signals.

Example timeline:

```
TIME  DIR  STEP
0     1    0
10    1    1
20    1    0
30    1    1
40    1    0
```

Important rule:

```
STEP is stored as pulse presence in a sample.
```
Not as a signal edge.

The **driver reacts to the 0→1 transition**.

---

# 3. Stepper Motor Requirement

Stepper drivers operate with:

```
STEP / DIR interface
```

Movement occurs when:

```
STEP changes from 0 → 1
```

Therefore correct pulse sequence must look like:

```
0 1 0 1 0 1
```

Never:

```
1 1 1
```

And never:

```
0 0 0 1 1
```

---

# 4. Simplest Constant Motion Example

If one axis requires:

```
9000 pulses
```

Then ideal constant motion looks like:

```
0 1 0 1 0 1 ...
```

across the TAKE duration.

The generator must **distribute pulses across time samples**.

---

# 5. Curve Driven Motion

The motion curve represents:

```
speed / motion intensity
```

Example:

```
AMP
0.0
0.2
0.4
0.7
1.0
0.7
0.4
0.2
0.0
```

The generator interprets this as:

```
higher amplitude → more pulses
lower amplitude → fewer pulses
```

Which produces variable speed.

---

# 6. Correct Generator Pipeline

The correct architecture of the generator is:

```
curve
↓
sample amplitudes
↓
density (continuous values)
↓
phase accumulator
↓
STEP pulses
```

Important rule:

The **density stage must remain continuous**.

Example density values:

```
0.05
0.12
0.30
0.80
1.20
```

These values are accumulated later to produce STEP events.

---

# 7. Phase Accumulator

The actual pulse generation happens later in the pipeline:

```
accumulator += density
ev = int(accumulator)

if ev > 0:
    accumulator -= ev
    STEP = 1
```

This mechanism guarantees:

```
Σ STEP = target_pulses
```

This part **already exists inside `_generate_rows_from_density()`**.

Therefore `_build_density_from_amplitudes()` must **NOT generate pulses directly**.

It only produces **density**.

---

# 8. Direction Handling

Direction is determined by sign of the curve.

```
AMP > 0  → DIR = 1
AMP < 0  → DIR = 0
```

If amplitude crosses zero the generator flips direction.

Example:

```
+0.4
+0.2
0
-0.1
-0.3
```

Direction change occurs when sign changes.

---

# 9. TAKE Integrity Rule

The generator must guarantee:

```
total STEP pulses = axis_take.target_pulses
```

Validation occurs using:

```
_ensure_exact_total()
```

This is critical for mechanical repeatability.

---

# 10. What Broke Previous Attempts

Several attempts broke the generator because:

1. `_build_density_from_amplitudes()` started generating **STEP pulses directly**.
2. This created **double accumulation** because `_generate_rows_from_density()` already uses an accumulator.
3. The pipeline then produced incorrect pulse counts.

Correct rule:

```
_build_density_from_amplitudes → density only
_generate_rows_from_density → pulses
```

---

# 11. Final Mental Model

The entire TARZAN motion system works like this:

```
motion curve
↓
amplitude samples
↓
pulse density
↓
phase accumulator
↓
STEP pulses
↓
stepper motor motion
```

---

# 12. Why This Model Is Good

This architecture is used in many real systems:

- CNC motion planners
- 3D printer firmware
- digital signal generators

Advantages:

• stable pulse timing  
• smooth speed transitions  
• deterministic pulse count  

---

# 13. Development Rule

Future changes must respect this rule:

```
DO NOT collapse the pipeline into a direct curve → STEP generator.
```

The density layer is essential.

---

# 14. Current Status

The generator currently:

✓ produces correct STEP pulses  
✓ maintains target pulse counts  
✓ responds to motion curve amplitude  
✓ integrates with editor protocol preview  

This version should be considered **the stable reference implementation**.

---

# End of Document
