from __future__ import annotations

from bisect import bisect_left


def clamp_y(value: float, limit: float) -> float:
    limit = max(1.0, float(limit or 100.0))
    return max(-limit, min(limit, float(value)))


def sorted_points(points: list[tuple[int, float]]) -> list[tuple[int, float]]:
    return sorted((int(t), float(y)) for t, y in points)


def value_at(points: list[tuple[int, float]], time_ms: int) -> float:
    points = sorted_points(points)
    if not points:
        return 0.0

    t = int(time_ms)
    if t <= points[0][0]:
        return float(points[0][1])
    if t >= points[-1][0]:
        return float(points[-1][1])

    times = [p[0] for p in points]
    idx = bisect_left(times, t)

    t0, y0 = points[idx - 1]
    t1, y1 = points[idx]

    if t1 <= t0:
        return float(y1)

    k = (t - t0) / float(t1 - t0)
    return float(y0) + (float(y1) - float(y0)) * max(0.0, min(1.0, k))


def normalize_to_target_times(
    source_points: list[tuple[int, float]],
    target_points: list[tuple[int, float]],
) -> list[tuple[int, float]]:
    """
    Zwraca SOURCE przeliczony w czasach TARGET.

    To jest podstawa pluginów:
    TARGET ma swoją strukturę czasową,
    SOURCE tylko daje wpływ y w tych czasach.
    """
    out: list[tuple[int, float]] = []
    for t, _target_y in sorted_points(target_points):
        out.append((int(t), value_at(source_points, int(t))))
    return out


def points_to_nodes_payload(points: list[tuple[int, float]], y_limit: float) -> list[tuple[int, float]]:
    """
    Bezpieczna postać do zamiany na AxisNode po stronie adaptera EHR.
    Nie zna klasy AxisNode.
    """
    return [(int(t), clamp_y(float(y), y_limit)) for t, y in sorted_points(points)]
