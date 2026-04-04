from __future__ import annotations

import math
import tkinter as tk
from typing import Any


from editor.tarzanWykresOsi import DRONE_KEY


class TarzanTakePreviewWindow(tk.Toplevel):
    BG = "#16181C"
    PANEL = "#2A3038"
    FG = "#F3F6F8"
    MUTED = "#AEB7C2"

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("TARZAN — TAKE Preview")
        self.geometry("1180x860")
        self.configure(bg=self.BG)
        self.current_axis_key = ""
        self._build_ui()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(
            top,
            text="TAKE PREVIEW / DEBUG",
            bg=self.BG,
            fg=self.FG,
            font=("Segoe UI Semibold", 14),
        ).pack(side="left")

        info_wrap = tk.Frame(outer, bg=self.BG)
        info_wrap.pack(fill="x", pady=(0, 8))
        self.header_var = tk.StringVar(value="Brak danych")
        tk.Label(
            info_wrap,
            textvariable=self.header_var,
            bg=self.BG,
            fg=self.FG,
            anchor="w",
            font=("Segoe UI", 10),
        ).pack(fill="x")

        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._protocol = self._make_text_block(left, "PROTOCOL PREVIEW")
        self._segments = self._make_text_block(right, "SEGMENTS")

    def _make_text_block(self, parent: tk.Misc, title: str) -> tk.Text:
        wrap = tk.Frame(parent, bg=self.BG)
        wrap.pack(fill="both", expand=True, pady=6)
        tk.Label(
            wrap,
            text=title,
            bg=self.BG,
            fg=self.FG,
            anchor="w",
            font=("Segoe UI Semibold", 10),
        ).pack(fill="x")
        text = tk.Text(
            wrap,
            bg=self.PANEL,
            fg=self.FG,
            insertbackground=self.FG,
            relief="flat",
            height=10,
            wrap="none",
            font=("Consolas", 9),
        )
        text.pack(side="left", fill="both", expand=True, pady=(4, 0))
        sy = tk.Scrollbar(wrap, orient="vertical", command=text.yview)
        sy.pack(side="right", fill="y", pady=(4, 0))
        text.configure(yscrollcommand=sy.set)
        return text

    def set_axis(self, axis_key: str) -> None:
        self.current_axis_key = axis_key

    def refresh(
        self,
        take,
        axis_key: str,
        axis_line: Any | None = None,
        validation_result: Any | None = None,
    ) -> None:
        self.set_axis(axis_key)
        if take is None:
            return

        if axis_key == DRONE_KEY:
            self.header_var.set("DRON / zdarzenia TAKE")
            self._write(self._protocol, "COUNT | TIME | STEP | DIR | ENABLE\n\nBrak protokołu STEP/DIR dla zdarzenia DRON.")
            self._write(self._segments, "Brak segmentów dla zdarzenia DRON.")
            return

        axis_take = take.axes.get(axis_key)
        if axis_take is None:
            self.header_var.set("Brak danych osi.")
            self._write(self._protocol, "Brak danych.")
            self._write(self._segments, "Brak danych.")
            return

        sample_step = int(getattr(getattr(take, "timeline", None), "sample_step", 10) or 10)
        protocol_rows, total_generated_pulses = self._build_protocol_rows(
            axis_take=axis_take,
            axis_line=axis_line,
            validation_result=validation_result,
            sample_step=sample_step,
        )
        self.header_var.set(
            f"{axis_take.axis_name} | sample_step={sample_step} ms | "
            f"mechanical_pulses={total_generated_pulses} | full_cycle_pulses={int(getattr(axis_take, 'full_cycle_pulses', 0))} | "
            f"max_rate={int(getattr(axis_take, 'max_pulse_rate', 0))} | max_acc={int(getattr(axis_take, 'max_acceleration', 0))}"
        )
        self._write(self._protocol, self._format_protocol(protocol_rows))
        self._write(self._segments, self._format_segments(axis_take, protocol_rows, validation_result))

    def _write(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _build_protocol_rows(
        self,
        axis_take,
        axis_line: Any | None,
        validation_result: Any | None,
        sample_step: int,
    ) -> tuple[list[dict[str, float | int]], int]:
        points = self._collect_points(axis_take, axis_line)
        if len(points) < 2:
            return [], 0

        target_total_pulses = self._resolve_target_pulses(axis_take, validation_result)
        start_time = int(points[0][0])
        end_time = int(points[-1][0])

        grid_start = self._align_time_down(start_time, sample_step)
        grid_end = self._align_time_up(end_time, sample_step)
        times = list(range(grid_start, grid_end + sample_step, sample_step))
        if not times:
            return [], 0

        amps = [self._interpolate_value(points, t) for t in times]
        abs_sum = sum(abs(v) for v in amps)
        if abs_sum <= 1e-12:
            rows = []
            for t, amp in zip(times, amps):
                rows.append(
                    {
                        "count": 0,
                        "time_ms": int(t),
                        "step": 0,
                        "dir": 1,
                        "enable": 1,
                        "amp": float(amp),
                    }
                )
            return rows, 0

        # Rozkład impulsów zgodny z zasadą:
        # amplituda -> gęstość impulsów -> akumulator -> COUNT / STEP
        accumulator = 0.0
        emitted_total = 0
        last_dir = 1
        step_level = 0
        rows: list[dict[str, float | int]] = []

        for t, amp in zip(times, amps):
            density_share = abs(float(amp)) / abs_sum
            pulses_in_sample_float = density_share * target_total_pulses
            accumulator += pulses_in_sample_float
            step_count = int(math.floor(accumulator + 1e-12))
            accumulator -= step_count

            if amp > 1e-12:
                dir_value = 1
                last_dir = 1
            elif amp < -1e-12:
                dir_value = 0
                last_dir = 0
            else:
                dir_value = last_dir

            if step_count > 0:
                step_level = 0 if step_level == 1 else 1
            else:
                step_level = 0

            emitted_total += step_count
            rows.append(
                {
                    "count": int(emitted_total + step_count),
                    "time_ms": int(t),
                    "step": int(step_level),
                    "dir": int(dir_value),
                    "enable": 1,
                    "amp": float(amp),
                }
            )

        diff = int(target_total_pulses) - emitted_total
        if rows and diff != 0:
            rows[-1]["count"] = int(rows[-1]["count"]) + diff
            if int(rows[-1]["count"]) > 0:
                prev_step = int(rows[-2]["step"]) if len(rows) > 1 else 0
                rows[-1]["step"] = 0 if prev_step == 1 else 1
            emitted_total += diff

        return rows, emitted_total

    def _resolve_target_pulses(self, axis_take, validation_result: Any | None) -> int:
        # Długość osi i budżet impulsów są święte dla modelu:
        # preview pracuje na pełnej mechanicznej liczbie impulsów osi.
        full_cycle = float(getattr(axis_take, "full_cycle_pulses", 0) or 0)
        return max(0, int(round(full_cycle)))

    def _collect_points(self, axis_take, axis_line: Any | None) -> list[tuple[int, float]]:
        points: list[tuple[int, float]] = []
        if axis_line is not None and getattr(axis_line, "nodes", None):
            for node in axis_line.nodes:
                points.append((int(getattr(node, "time_ms", 0)), float(getattr(node, "value", 0.0))))
        else:
            curve = getattr(axis_take, "curve", None)
            cps = list(getattr(curve, "control_points", []) or [])
            for cp in cps:
                points.append((int(getattr(cp, "time", 0)), float(getattr(cp, "amplitude", 0.0))))

        points = sorted(points, key=lambda item: item[0])

        if not points:
            return []

        normalized: list[tuple[int, float]] = [points[0]]
        for time_ms, value in points[1:]:
            if time_ms == normalized[-1][0]:
                normalized[-1] = (time_ms, value)
            else:
                normalized.append((time_ms, value))
        return normalized

    def _align_time_down(self, value: int, step: int) -> int:
        if step <= 0:
            return int(value)
        return int(math.floor(value / step) * step)

    def _align_time_up(self, value: int, step: int) -> int:
        if step <= 0:
            return int(value)
        return int(math.ceil(value / step) * step)

    def _interpolate_value(self, points: list[tuple[int, float]], t: int) -> float:
        if not points:
            return 0.0
        if t <= points[0][0]:
            return float(points[0][1])
        if t >= points[-1][0]:
            return float(points[-1][1])

        for idx in range(len(points) - 1):
            t0, v0 = points[idx]
            t1, v1 = points[idx + 1]
            if t0 <= t <= t1:
                if t1 == t0:
                    return float(v1)
                rel = (t - t0) / float(t1 - t0)
                return float(v0 + (v1 - v0) * rel)
        return 0.0

    def _format_protocol(self, protocol_rows: list[dict[str, float | int]]) -> str:
        lines = ["COUNT | TIME | STEP | DIR | ENABLE | AMP"]
        if not protocol_rows:
            lines.append("Brak danych protokołu preview.")
            return "\n".join(lines)

        for row in protocol_rows[:320]:
            lines.append(
                f"{int(row['count']):>5} | "
                f"{int(row['time_ms']):>5} | "
                f"{int(row['step']):>4} | "
                f"{int(row['dir']):>3} | "
                f"{int(row['enable']):>6} | "
                f"{float(row['amp']):>+.3f}"
            )
        if len(protocol_rows) > 320:
            lines.append("...")
        return "\n".join(lines)

    def _format_segments(
        self,
        axis_take,
        protocol_rows: list[dict[str, float | int]],
        validation_result: Any | None,
    ) -> str:
        lines = [f"AXIS: {axis_take.axis_name}", ""]
        if validation_result is not None:
            lines.extend(
                [
                    f"P: {int(round(getattr(validation_result, 'pulses_total', 0)))} / {int(round(getattr(validation_result, 'pulses_limit', 0)))}",
                    f"R: {int(round(getattr(validation_result, 'peak_rate', 0)))} / {int(round(getattr(validation_result, 'rate_limit', 0)))}",
                    f"A: {int(round(getattr(validation_result, 'peak_acceleration', 0)))} / {int(round(getattr(validation_result, 'acceleration_limit', 0)))}",
                    "",
                ]
            )

        if not protocol_rows:
            lines.append("Brak segmentów.")
            return "\n".join(lines)

        lines.append("segment_id | start | end | dir | pulses | pause | change")
        segments = self._build_segments_from_protocol(protocol_rows)
        for seg in segments:
            lines.append(
                f"{seg['segment_id']:>9} | {seg['start_time']:>5} | {seg['end_time']:>5} | "
                f"{seg['direction']:>3} | {seg['pulse_count']:>6} | "
                f"{int(seg['is_pause']):>5} | {int(seg['is_direction_change']):>6}"
            )
        return "\n".join(lines)

    def _build_segments_from_protocol(self, protocol_rows: list[dict[str, float | int]]) -> list[dict[str, int | bool | str]]:
        segments: list[dict[str, int | bool | str]] = []
        if not protocol_rows:
            return segments

        current = None
        previous_dir = None
        seg_index = 1

        for idx, row in enumerate(protocol_rows):
            count = int(row["count"])
            time_ms = int(row["time_ms"])
            amp = float(row["amp"])
            direction = int(row["dir"]) if abs(amp) > 1e-12 or count > 0 else 0
            is_pause = direction == 0 and count == 0

            kind = ("pause", 0) if is_pause else ("move", direction)

            if current is None or current["kind"] != kind:
                if current is not None:
                    current["end_time"] = int(protocol_rows[idx - 1]["time_ms"])
                    segments.append(current)

                current = {
                    "segment_id": f"SEG_{seg_index:03d}",
                    "start_time": time_ms,
                    "end_time": time_ms,
                    "direction": direction,
                    "pulse_count": count,
                    "is_pause": is_pause,
                    "is_direction_change": False if previous_dir is None else (not is_pause and direction != previous_dir),
                    "kind": kind,
                }
                seg_index += 1
                if not is_pause:
                    previous_dir = direction
            else:
                current["pulse_count"] = int(current["pulse_count"]) + count

        if current is not None:
            current["end_time"] = int(protocol_rows[-1]["time_ms"])
            segments.append(current)

        for seg in segments:
            seg.pop("kind", None)

        return segments
