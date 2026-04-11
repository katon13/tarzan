from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class CurvePoint:
    time_ms: int
    amp: float


@dataclass(frozen=True)
class StepRow:
    sample: int
    time_ms: int
    dir: int
    step: int
    enable: int
    amp: float
    count: int


def sample_curve(points: Sequence[Tuple[int, float]], sample_ms: int = 10) -> List[float]:
    """
    Próbuje krzywą liniowo co sample_ms.
    points = [(time_ms, amp), ...]
    Zwraca listę amplitud AMP dla każdej próbki czasu.
    """
    if not points:
        return []

    pts = sorted((int(t), float(a)) for t, a in points)

    # scal duplikaty czasu
    normalized: List[Tuple[int, float]] = []
    for t, a in pts:
        if normalized and normalized[-1][0] == t:
            normalized[-1] = (t, a)
        else:
            normalized.append((t, a))

    if len(normalized) == 1:
        return [normalized[0][1], normalized[0][1]]

    start_ms = normalized[0][0]
    end_ms = normalized[-1][0]

    times = list(range(start_ms, end_ms + sample_ms, sample_ms))
    amps: List[float] = []

    seg = 0
    for t in times:
        while seg < len(normalized) - 2 and t > normalized[seg + 1][0]:
            seg += 1

        t0, a0 = normalized[seg]
        t1, a1 = normalized[seg + 1]

        if t <= t0:
            amps.append(a0)
            continue
        if t >= t1 and seg == len(normalized) - 2:
            amps.append(a1)
            continue

        if t1 == t0:
            amps.append(a1)
            continue

        ratio = (t - t0) / (t1 - t0)
        amp = a0 + ratio * (a1 - a0)
        amps.append(float(amp))

    return amps


def build_direction_samples(amps: Sequence[float]) -> List[int]:
    """
    AMP > 0 -> DIR=1
    AMP < 0 -> DIR=0
    AMP = 0 -> trzyma ostatni kierunek
    """
    out: List[int] = []
    last_dir = 1
    for amp in amps:
        if amp > 0:
            last_dir = 1
        elif amp < 0:
            last_dir = 0
        out.append(last_dir)
    return out


def generate_step_protocol_from_curve_points(
    points: Sequence[Tuple[int, float]],
    total_pulses: int,
    sample_ms: int = 10,
    enable: int = 1,
) -> List[StepRow]:
    """
    Prosty model referencyjny:
    - krzywa z punktów
    - próbkowanie co 10 ms
    - STEP jako 0/1
    - impulsy gęściej tam, gdzie |AMP| jest większe
    """
    amps = sample_curve(points, sample_ms=sample_ms)
    if not amps:
        return []

    n = len(amps)
    dir_samples = build_direction_samples(amps)

    # Sloty HIGH tylko w co drugiej próbce: 1,3,5,7...
    high_slots = list(range(1, n, 2))
    max_pulses = len(high_slots)

    if total_pulses < 0:
        total_pulses = 0
    if total_pulses > max_pulses:
        raise ValueError(
            f"Za dużo impulsów dla timeline. requested={total_pulses}, max={max_pulses}. "
            f"Przy sample_ms={sample_ms} potrzeba co najmniej {total_pulses * 2} próbek."
        )

    # Waga każdego slotu HIGH z krzywej
    weights: List[float] = []
    for hi in high_slots:
        lo = hi - 1
        w = (abs(amps[lo]) + abs(amps[hi])) * 0.5
        weights.append(w)

    total_weight = sum(weights)

    # Gdy krzywa zerowa, ale impulsów żądamy -> rozkład równy
    if total_pulses > 0 and total_weight <= 1e-12:
        weights = [1.0] * len(weights)
        total_weight = float(len(weights))

    # Rozkład total_pulses po slotach HIGH proporcjonalnie do wag
    pulse_on_high_slot: List[int] = []
    emitted = 0
    cumulative = 0.0

    if total_pulses == 0:
        pulse_on_high_slot = [0] * len(weights)
    else:
        for w in weights:
            cumulative += total_pulses * (w / total_weight)
            if cumulative >= (emitted + 1) - 1e-12 and emitted < total_pulses:
                pulse_on_high_slot.append(1)
                emitted += 1
            else:
                pulse_on_high_slot.append(0)

    pulse_map = dict(zip(high_slots, pulse_on_high_slot))

    rows: List[StepRow] = []
    count = 0
    start_time_ms = int(points[0][0])

    for i in range(n):
        step = int(pulse_map.get(i, 0))
        if step == 1:
            count += 1

        rows.append(
            StepRow(
                sample=i,
                time_ms=start_time_ms + i * sample_ms,
                dir=dir_samples[i],
                step=step,
                enable=int(enable),
                amp=float(amps[i]),
                count=count,
            )
        )

    return rows


def print_protocol(rows: Sequence[StepRow], limit: int | None = 80) -> None:
    print("COUNT | TIME | DIR | STEP | ENABLE | AMP")
    print("------------------------------------------")
    shown = rows if limit is None else rows[:limit]
    for r in shown:
        print(
            f"{r.count:5d} | "
            f"{r.time_ms:5d} | "
            f"{r.dir:3d} | "
            f"{r.step:4d} | "
            f"{r.enable:6d} | "
            f"{r.amp:+.3f}"
        )
    if limit is not None and len(rows) > limit:
        print(f"... ({len(rows) - limit} more rows)")


if __name__ == "__main__":
    # Krzywa z węzłów:
    # start wolno, środek szybciej, potem zwolnienie
    curve_points = [
        (0, 0.2),
        (500, 0.5),
        (1500, 1.5),
        (2500, 2.0),
        (3500, 0.8),
        (4500, 0.2),
    ]

    rows = generate_step_protocol_from_curve_points(
        points=curve_points,
        total_pulses=120,
        sample_ms=10,
        enable=1,
    )

    print_protocol(rows, limit=120)
    print()
    print(f"generated_pulses = {rows[-1].count}")
    print(f"rows = {len(rows)}")