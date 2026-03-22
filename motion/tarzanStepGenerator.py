from __future__ import annotations

import numpy as np


class TarzanStepGenerator:
    """
    Generator timeline impulsów STEP.

    Zamienia profil gęstości impulsów w czasie
    na rzeczywiste momenty impulsów STEP.

    Wejście:
    - time_ms: próbki czasu [ms]
    - pulse_density: gęstość impulsów [impuls/ms]

    Wyjście:
    - lista czasów impulsów STEP
    """

    def __init__(self, time_ms, pulse_density) -> None:
        self.time_ms = np.array(time_ms, dtype=float)
        self.pulse_density = np.array(pulse_density, dtype=float)

    def generate_step_times(self) -> list[float]:
        pulse_times: list[float] = []
        accumulator = 0.0

        for i in range(len(self.time_ms) - 1):
            t0 = self.time_ms[i]
            t1 = self.time_ms[i + 1]
            dt = t1 - t0

            if dt <= 0:
                continue

            density = self.pulse_density[i]
            pulses_expected = density * dt
            accumulator += pulses_expected

            while accumulator >= 1.0:
                pulse_times.append(float(t0))
                accumulator -= 1.0

        return pulse_times