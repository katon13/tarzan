from __future__ import annotations

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
        tk.Label(top, text="TAKE PREVIEW / DEBUG", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 14)).pack(side="left")

        info_wrap = tk.Frame(outer, bg=self.BG)
        info_wrap.pack(fill="x", pady=(0, 8))
        self.header_var = tk.StringVar(value="Brak danych")
        tk.Label(info_wrap, textvariable=self.header_var, bg=self.BG, fg=self.FG, anchor="w", font=("Segoe UI", 10)).pack(fill="x")

        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))

        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True, padx=(6,0))

        # Protocol on the left
        self._protocol = self._make_text_block(left, "PROTOCOL PREVIEW")

        # Segments on the right
        self._segments = self._make_text_block(right, "SEGMENTS")

    def _make_text_block(self, parent: tk.Misc, title: str) -> tk.Text:
        wrap = tk.Frame(parent, bg=self.BG)
        wrap.pack(fill="both", expand=True, pady=6)
        tk.Label(wrap, text=title, bg=self.BG, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 10)).pack(fill="x")
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

    def refresh(self, take, axis_key: str, axis_line: Any | None = None, validation_result: Any | None = None) -> None:
        self.set_axis(axis_key)
        if take is None:
            return
        if axis_key == DRONE_KEY:
            self.header_var.set("DRON / zdarzenia TAKE")
            self._write(self._segments, "DRONE EVENT\n\nBrak segmentów dla zdarzeń.")
            self._write(self._protocol, "DRONE PREVIEW\n\nZdarzenie czasowe bez sygnału STEP/DIR.")
            return

        axis_take = take.axes.get(axis_key)
        if axis_take is None:
            self.header_var.set("Brak danych osi.")
            self._write(self._segments, "Brak danych.")
            self._write(self._protocol, "Brak danych.")
            return

        self.header_var.set(
            f"{axis_take.axis_name} | full_cycle_pulses={axis_take.full_cycle_pulses} | "
            f"max_rate={axis_take.max_pulse_rate} | max_acc={axis_take.max_acceleration}"
        )
        self._write(self._segments, self._format_segments(axis_take, axis_line, validation_result))
        self._write(self._protocol, self._format_protocol(axis_take, axis_line))

    def _write(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _format_segments(self, axis_take, axis_line: Any | None, validation_result: Any | None) -> str:
        lines = [f"AXIS: {axis_take.axis_name}", ""]
        if validation_result is not None:
            lines.extend([
                f"P: {int(round(getattr(validation_result, 'pulses_total', 0)))} / {int(round(getattr(validation_result, 'pulses_limit', 0)))}",
                f"R: {int(round(getattr(validation_result, 'peak_rate', 0)))} / {int(round(getattr(validation_result, 'rate_limit', 0)))}",
                f"A: {int(round(getattr(validation_result, 'peak_acceleration', 0)))} / {int(round(getattr(validation_result, 'acceleration_limit', 0)))}",
                "",
            ])

        dynamic_rows = self._preview_segments_from_line(axis_line, validation_result)
        if dynamic_rows:
            lines.append("segment_id | start | end | dir | pulses")
            lines.extend(dynamic_rows)
            return "\n".join(lines)

        if not axis_take.segments:
            lines.append("Brak segmentów zapisanych w TAKE dla tej osi.")
        else:
            lines.append("segment_id | start | end | dir | pulses | pause | change")
            for seg in axis_take.segments:
                lines.append(
                    f"{seg.segment_id:>9} | {seg.start_time:>5} | {seg.end_time:>5} | {seg.direction:>3} | {seg.pulse_count:>6} | "
                    f"{int(bool(seg.is_pause)):>5} | {int(bool(seg.is_direction_change)):>6}"
                )
        return "\n".join(lines)

    def _preview_segments_from_line(self, axis_line: Any | None, validation_result: Any | None) -> list[str]:
        nodes = list(getattr(axis_line, "nodes", []) or [])
        if len(nodes) < 2:
            return []
        segments = []
        total_abs_area = 0.0
        spans = []
        for i in range(len(nodes) - 1):
            n0, n1 = nodes[i], nodes[i + 1]
            dt = max(0, int(getattr(n1, "time_ms", 0)) - int(getattr(n0, "time_ms", 0)))
            if dt <= 0:
                continue
            v0 = float(getattr(n0, "value", 0.0))
            v1 = float(getattr(n1, "value", 0.0))
            avg = (v0 + v1) / 2.0
            abs_area = abs(avg) * dt
            total_abs_area += abs_area
            spans.append((i, int(getattr(n0, "time_ms", 0)), int(getattr(n1, "time_ms", 0)), 0 if abs(avg) < 1e-9 else (1 if avg > 0 else -1), abs_area))

        pulses_total = float(getattr(validation_result, "pulses_total", 0.0)) if validation_result is not None else 0.0
        for i, start, end, direction, abs_area in spans:
            pulses = int(round((abs_area / total_abs_area) * pulses_total)) if total_abs_area > 0 and pulses_total > 0 else int(round(abs_area))
            if direction == 0 and pulses == 0:
                continue
            segments.append(f"SEG_{i+1:03d} | {start:>5} | {end:>5} | {direction:>3} | {pulses:>6}")
        return segments

    def _format_protocol(self, axis_take, axis_line: Any | None) -> str:
        rows = ["TIME | COUNT | STEP | DIR | ENABLE | AMP"]
        nodes = list(getattr(axis_line, "nodes", []) or [])
        if len(nodes) >= 2:
            rows.extend(self._protocol_rows_from_line(nodes))
            return "\n".join(rows)

        cps = list(getattr(getattr(axis_take, "curve", None), "control_points", []) or [])
        if cps:
            cps = sorted(cps, key=lambda p: int(getattr(p, "time", 0)))
            running = 0
            for point in cps[:128]:
                amp = float(getattr(point, "amplitude", 0.0))
                step = 1 if abs(amp) > 1e-9 else 0
                direction = 1 if amp >= 0 else -1
                running += step
                rows.append(f"{int(point.time):>4} | {running:>5} | {step:>4} | {direction:>3} | {1:>6} | {amp:>+.3f}")
        else:
            rows.append("Brak danych protokołu preview.")
        return "\n".join(rows)

    def _protocol_rows_from_line(self, nodes: list[Any]) -> list[str]:
        rows: list[str] = []
        running = 0
        for i in range(len(nodes) - 1):
            n0, n1 = nodes[i], nodes[i + 1]
            t0 = int(getattr(n0, "time_ms", 0))
            t1 = int(getattr(n1, "time_ms", 0))
            v0 = float(getattr(n0, "value", 0.0))
            v1 = float(getattr(n1, "value", 0.0))
            dt = max(10, t1 - t0)
            samples = max(1, min(32, dt // 10))
            for s in range(samples):
                rel = s / samples
                amp = v0 + (v1 - v0) * rel
                step = 1 if abs(amp) > 1e-9 else 0
                direction = 1 if amp >= 0 else -1
                if step:
                    running += 1
                time_ms = t0 + s * max(10, dt // samples)
                rows.append(f"{time_ms:>4} | {running:>5} | {step:>4} | {direction:>3} | {1:>6} | {amp:>+.3f}")
                if len(rows) >= 160:
                    rows.append("...")
                    return rows
        return rows
