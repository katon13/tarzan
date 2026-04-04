from __future__ import annotations


class TarzanEdycjaPunktow:
    NODE_PICK_X_TOL = 14
    NODE_PICK_Y_TOL = 12

    def __init__(self, step_ms: int = 10) -> None:
        self.step_ms = max(1, int(step_ms))

    def snap(self, value: float) -> int:
        return int(round(float(value) / self.step_ms) * self.step_ms)

    def x_to_time(self, x: float, start: int, end: int, width: int) -> int:
        width = max(1, width)
        rel = max(0.0, min(1.0, x / width))
        return self.snap(start + rel * (end - start))

    def time_to_x(self, t: int, start: int, end: int, width: int) -> float:
        span = max(1, end - start)
        return (t - start) / span * width

    def value_to_y(self, val: float, height: int) -> float:
        return height / 2 - val * (height / 2 - 10)

    def y_to_value(self, y: float, height: int) -> float:
        denom = max(1.0, (height / 2 - 10))
        value = (height / 2 - y) / denom
        return max(-1.0, min(1.0, value))

    def hit_node(self, line, x: float, y: float, start: int, end: int, width: int, height: int):
        best_index = None
        best_score = None
        for i, n in enumerate(line.nodes):
            nx = self.time_to_x(n.time_ms, start, end, width)
            ny = self.value_to_y(n.value, height)
            dx = abs(nx - x)
            dy = abs(ny - y)
            if dx <= self.NODE_PICK_X_TOL and dy <= self.NODE_PICK_Y_TOL:
                score = dx + dy
                if best_score is None or score < best_score:
                    best_score = score
                    best_index = i
        return best_index
