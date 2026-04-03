from __future__ import annotations


class TarzanEdycjaPunktow:
    NODE_RADIUS = 7
    NODE_PICK_X_TOL = 12
    NODE_PICK_Y_TOL = 12
    LINE_PICK_X_TOL = 10

    def __init__(self, time_step_ms: int = 10) -> None:
        self.time_step_ms = max(1, int(time_step_ms))

    def snap_time(self, value_ms: float) -> int:
        return int(round(float(value_ms) / self.time_step_ms) * self.time_step_ms)

    def x_to_time(self, x: float, view_start: int, view_end: int, width: int) -> int:
        width = max(1, width)
        rel = min(1.0, max(0.0, x / width))
        return self.snap_time(view_start + rel * (view_end - view_start))

    def time_to_x(self, time_ms: int, view_start: int, view_end: int, width: int) -> float:
        span = max(1, view_end - view_start)
        rel = (time_ms - view_start) / span
        return rel * width

    def value_to_y(self, value: float, height: int, pad: int = 10) -> float:
        inner = max(10, height - 2 * pad)
        rel = (1.0 - ((value + 1.0) / 2.0))
        return pad + rel * inner

    def y_to_value(self, y: float, height: int, pad: int = 10) -> float:
        inner = max(10, height - 2 * pad)
        rel = (y - pad) / inner
        value = 1.0 - 2.0 * rel
        return max(-1.0, min(1.0, value))

    def hit_test_node(self, line, x: float, y: float, view_start: int, view_end: int, width: int, height: int):
        best_index = None
        best_score = None
        for index, node in enumerate(line.nodes):
            nx = self.time_to_x(node.time_ms, view_start, view_end, width)
            ny = self.value_to_y(node.value, height)
            dx = abs(nx - x)
            dy = abs(ny - y)
            if dx <= self.NODE_PICK_X_TOL and dy <= self.NODE_PICK_Y_TOL:
                score = dx + dy
                if best_score is None or score < best_score:
                    best_score = score
                    best_index = index
        return best_index

    def hit_test_start_stop(self, line, x: float, view_start: int, view_end: int, width: int):
        start_x = self.time_to_x(line.nodes[0].time_ms, view_start, view_end, width)
        stop_x = self.time_to_x(line.nodes[-1].time_ms, view_start, view_end, width)
        if abs(x - start_x) <= self.LINE_PICK_X_TOL:
            return "start"
        if abs(x - stop_x) <= self.LINE_PICK_X_TOL:
            return "stop"
        return None
