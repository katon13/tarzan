from __future__ import annotations


class TarzanEdycjaPunktow:
    NODE_TOL = 10

    def __init__(self, step_ms: int = 10):
        self.step_ms = step_ms

    def snap(self, value):
        return int(round(value / self.step_ms) * self.step_ms)

    def x_to_time(self, x, start, end, width):
        rel = max(0, min(1, x / max(1, width)))
        return self.snap(start + rel * (end - start))

    def time_to_x(self, t, start, end, width):
        span = max(1, end - start)
        return (t - start) / span * width

    def value_to_y(self, val, height):
        return height / 2 - val * (height / 2 - 10)

    def y_to_value(self, y, height):
        return (height / 2 - y) / max(1, (height / 2 - 10))

    def hit_node(self, line, x, y, start, end, width, height):
        for i, n in enumerate(line.nodes):
            nx = self.time_to_x(n.time_ms, start, end, width)
            ny = self.value_to_y(n.value, height)
            if abs(nx - x) < self.NODE_TOL and abs(ny - y) < self.NODE_TOL:
                return i
        return None
