from __future__ import annotations

import copy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from core.tarzanTakeVersioning import TarzanTakeVersioning
from editor.tarzanEdycjaPunktow import TarzanEdycjaPunktow
from editor.tarzanWykresOsi import AXIS_DEFINITIONS, DRONE_KEY, AxisTrack, DroneTrack, ensure_take_axes
from editor.tarzanTakePreviewWindow import TarzanTakePreviewWindow
from motion.tarzanKrzyweRuchu import TarzanKrzyweRuchu
from motion.tarzanStepGenerator import TarzanStepGenerator
from motion.tarzanTakeModel import (
    TarzanControlPoint,
    TarzanEvent,
    TarzanSourceInfo,
    TarzanTake,
    TarzanTakeMetadata,
    TarzanTimeline,
    TarzanValidation,
)


class TarzanEdytorChoreografiiRuchu(tk.Tk):
    BG = "#16181C"
    PANEL_2 = "#2A3038"
    FG = "#F3F6F8"
    BTN_PRIMARY = "#2D6CDF"
    BTN_SUCCESS = "#2E9E5B"
    BTN_WARNING = "#C78B2A"

    MODE_GENERATOR = "GENERATOR"
    MODE_EDITOR = "EDYTOR"
    MODE_PLAYER = "PLAYER"
    MODE_RECORDER = "RECORDER"
    MODE_LIVE = "LIVE"

    def __init__(self, take_path: str | Path | None = None) -> None:
        super().__init__()

        self.title("TARZAN — Edytor Choreografii Ruchu")
        self.geometry("1920x1180")
        self.minsize(1920, 1080)
        self.configure(bg=self.BG)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.default_take_path = self._find_default_take_path()
        self.take_path = Path(take_path) if take_path else None

        self.krzywe = TarzanKrzyweRuchu()
        self.versioning = TarzanTakeVersioning()
        self.edycja = TarzanEdycjaPunktow(getattr(self.krzywe, "TIME_STEP_MS", 10))
        self.step_generator = TarzanStepGenerator()

        self.editor_mode = self.MODE_GENERATOR
        self.take: TarzanTake | None = None
        self.original_take: TarzanTake | None = None
        self.axis_lines: dict[str, object] = {}
        self.axis_tracks: dict[str, object] = {}
        self.drone_track = None
        self.selected_axis_key: str | None = None
        self.status_var = tk.StringVar(value="Gotowy.")
        self.take_path_var = tk.StringVar(value=str(self.take_path) if self.take_path else "")

        self.current_xlim: tuple[int, int] | None = None
        self.preview_window: TarzanTakePreviewWindow | None = None

        self._build_ui()
        self._start_generator_mode()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.BG)
        top.pack(fill="x", pady=(0, 6))

        tk.Label(
            top,
            text="TARZAN — Edytor Choreografii Ruchu",
            bg=self.BG,
            fg=self.FG,
            font=("Segoe UI Semibold", 17),
        ).pack(side="left")

        top_right = tk.Frame(top, bg=self.BG)
        top_right.pack(side="right")
        self.open_btn = self._make_button(top_right, "Otwórz", self.open_take_dialog, self.BTN_PRIMARY)
        self.open_btn.pack(side="left", padx=2)
        self.save_btn = self._make_button(top_right, "Zapisz", self.save_take, self.BTN_SUCCESS)
        self.save_btn.pack(side="left", padx=2)
        self._make_button(top_right, "Zoom +", self.zoom_in, self.BTN_WARNING).pack(side="left", padx=2)
        self._make_button(top_right, "Zoom -", self.zoom_out, self.BTN_WARNING).pack(side="left", padx=2)
        self._make_button(top_right, "Pełny", self.zoom_reset, self.BTN_WARNING).pack(side="left", padx=2)
        self._make_button(top_right, "Preview", self.open_take_preview_window, self.BTN_PRIMARY).pack(side="left", padx=2)

        mode_row = tk.Frame(outer, bg=self.BG)
        mode_row.pack(fill="x", pady=(0, 8))
        self.mode_buttons = {}
        for mode, color in [
            (self.MODE_GENERATOR, self.BTN_SUCCESS),
            (self.MODE_EDITOR, self.BTN_PRIMARY),
            (self.MODE_PLAYER, self.BTN_WARNING),
            (self.MODE_RECORDER, self.BTN_WARNING),
            (self.MODE_LIVE, self.BTN_WARNING),
        ]:
            btn = tk.Button(
                mode_row, text=mode, command=lambda m=mode: self._switch_mode(m),
                bg=color, fg="white", activebackground=color, activeforeground="white",
                relief="flat", bd=0, padx=16, pady=10, font=("Segoe UI Semibold", 11), cursor="hand2",
            )
            btn.pack(side="left", padx=4)
            self.mode_buttons[mode] = btn

        path_row = tk.Frame(outer, bg=self.BG)
        path_row.pack(fill="x", pady=(0, 8))
        tk.Label(path_row, text="TAKE", bg=self.BG, fg=self.FG, font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(
            path_row,
            textvariable=self.take_path_var,
            bg=self.PANEL_2,
            fg=self.FG,
            insertbackground=self.FG,
            relief="flat",
            font=("Segoe UI", 10),
            bd=5,
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(body, bg=self.BG, highlightthickness=0, bd=0)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(body, orient="vertical", command=self.scroll_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        self.tracks_frame = tk.Frame(self.scroll_canvas, bg=self.BG)
        self.scroll_window = self.scroll_canvas.create_window((0, 0), window=self.tracks_frame, anchor="nw")
        self.tracks_frame.bind("<Configure>", self._on_tracks_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)

        status = tk.Label(
            outer,
            textvariable=self.status_var,
            anchor="w",
            bg=self.PANEL_2,
            fg=self.FG,
            padx=10,
            pady=8,
            font=("Segoe UI", 9),
        )
        status.pack(fill="x", pady=(8, 0))

    def _make_button(self, parent, text: str, command, color: str) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=8,
            pady=5,
            font=("Segoe UI", 9),
            cursor="hand2",
        )


    def _set_button_enabled(self, button: tk.Button, enabled: bool) -> None:
        if enabled:
            button.configure(state="normal", disabledforeground="white")
        else:
            button.configure(state="disabled", disabledforeground="#8A8F97")

    def _update_mode_ui(self) -> None:
        for mode, button in getattr(self, "mode_buttons", {}).items():
            if mode == self.editor_mode:
                button.configure(relief="sunken")
            else:
                button.configure(relief="flat")

        self._set_button_enabled(self.open_btn, self.editor_mode == self.MODE_EDITOR)

    def _on_tracks_configure(self, _event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.scroll_canvas.itemconfigure(self.scroll_window, width=event.width)

    def _find_default_take_path(self) -> Path | None:
        take_dir = self.base_dir / "data" / "take"
        if not take_dir.exists():
            return None
        candidates = sorted(take_dir.glob("TAKE_*_v*.json"))
        return candidates[0] if candidates else None

    def _load_initial_take(self) -> None:
        self._start_generator_mode()

    def _build_generator_take(self) -> TarzanTake:
        take = TarzanTake(
            metadata=TarzanTakeMetadata(
                take_id="TAKE_NEW",
                version="v01",
                title="Nowy TAKE",
                author="Jacek Joniec",
                created_at="",
                edited_at="",
                description="Generator EHR",
                notes="Start w trybie GENERATOR",
            ),
            timeline=TarzanTimeline(time_unit="ms", sample_step=int(getattr(self.krzywe, "TIME_STEP_MS", 10)), take_start=0, take_end=0, take_duration=0),
            axes={},
            events=[],
            simulation={"ghost_visible": True, "show_all_axes": True},
            source=TarzanSourceInfo(record_mode="GENERATOR", source_protocol_file="", source_notes=""),
            validation=TarzanValidation(status="generator", checked_at="", max_speed_ok=True, max_acceleration_ok=True, start_zero_ok=True, end_zero_ok=True, direction_change_ok=True, events_ok=True, messages=[]),
        )
        ensure_take_axes(take)
        sample_step = int(getattr(take.timeline, "sample_step", 10) or 10)
        max_end = sample_step
        for definition in AXIS_DEFINITIONS:
            axis = take.axes[definition.key]
            axis.curve.control_points = self._build_generator_control_points(axis, definition)
            max_end = max(max_end, int(axis.curve.control_points[-1].time))
        take.events = [TarzanEvent(event_id="EV_DRONE_001", event_type=DRONE_KEY, event_time=max(sample_step, max_end // 2), enabled=True, note="release")]
        take.timeline.take_start = 0
        take.timeline.take_end = int(max_end)
        take.timeline.take_duration = int(max_end)
        return take

    def _build_generator_control_points(self, axis_take, definition) -> list:
        cp_cls = TarzanControlPoint
        sample_step = int(getattr(self.krzywe, "TIME_STEP_MS", 10))
        duration_ms = int(round(float(getattr(definition, "min_full_cycle_time_s", 1.0)) * 1000.0))
        duration_ms = max(sample_step * 8, duration_ms)
        settle = max(sample_step, int(duration_ms * 0.08))
        ramp = max(settle + sample_step, int(duration_ms * 0.18))
        cruise_end = max(ramp + sample_step, duration_ms - settle)
        end = max(cruise_end + sample_step, duration_ms)
        return [
            cp_cls(time=0, amplitude=0.0),
            cp_cls(time=settle, amplitude=1.0),
            cp_cls(time=ramp, amplitude=1.0),
            cp_cls(time=cruise_end, amplitude=1.0),
            cp_cls(time=end, amplitude=0.0),
        ]

    def _start_generator_mode(self) -> None:
        self.editor_mode = self.MODE_GENERATOR
        self.take_path = None
        self.take_path_var.set("")
        self.take = self._build_generator_take()
        self.original_take = copy.deepcopy(self.take)
        self.axis_lines = {definition.key: self.krzywe.build_from_axis(self.take.axes[definition.key]) for definition in AXIS_DEFINITIONS}
        self.selected_axis_key = AXIS_DEFINITIONS[0].key
        self._normalize_take_timeline_from_lines()
        self.current_xlim = self._full_xlim()
        self._rebuild_tracks()
        self._regenerate_all_protocols()
        self._refresh_tracks()
        self._ensure_preview_window()
        self._refresh_preview_window()
        self._update_mode_ui()
        self.status_var.set("Tryb GENERATOR: czysty TAKE startowy bez wczytanego pliku.")

    def _switch_mode(self, mode: str) -> None:
        if mode in (self.MODE_PLAYER, self.MODE_RECORDER, self.MODE_LIVE):
            self.status_var.set(f"Tryb {mode} jeszcze nie jest aktywny w tej wersji EHR.")
            return
        if mode == self.MODE_GENERATOR:
            self._start_generator_mode()
            return
        self.editor_mode = self.MODE_EDITOR
        self._update_mode_ui()
        self.status_var.set("Tryb EDYTOR: możesz wczytać istniejący TAKE do edycji.")

    def _mechanical_axis_duration_ms(self, axis_key: str) -> int:
        if self.take is None:
            return 10
        axis_take = self.take.axes[axis_key]
        sample_step = int(getattr(self.take.timeline, "sample_step", 10) or 10)
        # Czas osi wywodzimy z mechaniki jako minimalny czas pełnego cyklu,
        # nie z full_cycle_pulses * sample_step, bo to sztucznie rozciąga TAKE.
        cycle_ms = int(round(float(getattr(axis_take, "min_full_cycle_time_s", 1.0) or 1.0) * 1000.0))
        return max(sample_step * 8, cycle_ms)

    def _stretch_line_to_mechanical_duration(self, axis_key: str, line):
        if self.take is None or line is None or not getattr(line, "nodes", None):
            return line
        target_duration = self._mechanical_axis_duration_ms(axis_key)
        start = int(line.nodes[0].time_ms)
        target_stop = start + target_duration
        current_stop = int(line.nodes[-1].time_ms)
        current_duration = max(int(getattr(self.krzywe, "TIME_STEP_MS", 10)), current_stop - start)
        scale = target_duration / float(current_duration)

        stretched = copy.deepcopy(line)
        for index, node in enumerate(stretched.nodes):
            if index == 0:
                node.time_ms = start
            elif index == len(stretched.nodes) - 1:
                node.time_ms = target_stop
            else:
                rel = int(node.time_ms) - start
                node.time_ms = self.krzywe.snap_time(start + rel * scale)
        self.krzywe.normalize_line(stretched, self.take.axes[axis_key])
        stretched.nodes[0].time_ms = start
        stretched.nodes[-1].time_ms = target_stop
        self.krzywe.normalize_line(stretched, self.take.axes[axis_key])
        return stretched

    def _conform_axis_lines_to_mechanics(self) -> None:
        if self.take is None:
            return
        for definition in AXIS_DEFINITIONS:
            axis_key = definition.key
            axis_take = self.take.axes[axis_key]
            axis_take.full_cycle_pulses = int(definition.full_cycle_pulses)
            axis_take.min_full_cycle_time_s = float(definition.min_full_cycle_time_s)
            axis_take.max_pulse_rate = int(definition.max_pulse_rate)
            axis_take.max_acceleration = int(definition.max_acceleration)
            axis_take.backlash_compensation = int(definition.backlash_compensation)
            # Nie wymuszamy tu ponownego rozciągania linii do stałej długości.
            # Długość ruchu ma wynikać z edycji krzywej i zachowania pola.


    def _axis_curve_has_nonzero_values(self, axis_take) -> bool:
        cps = list(getattr(getattr(axis_take, "curve", None), "control_points", []) or [])
        return any(abs(float(getattr(cp, "amplitude", 0.0))) > 1e-9 for cp in cps)

    def _rebuild_axis_curve_from_segments(self, axis_take) -> None:
        segments = list(getattr(axis_take, "segments", []) or [])
        if not segments:
            return
        cps = [TarzanControlPoint(time=int(segments[0].start_time), amplitude=0.0)]
        for seg in segments:
            start_t = int(seg.start_time)
            end_t = int(seg.end_time)
            if bool(getattr(seg, "is_pause", False)) or int(getattr(seg, "direction", 0)) == 0 or int(getattr(seg, "pulse_count", 0)) == 0:
                if cps[-1].time != start_t:
                    cps.append(TarzanControlPoint(time=start_t, amplitude=0.0))
                cps.append(TarzanControlPoint(time=end_t, amplitude=0.0))
                continue
            sign = 1.0 if int(seg.direction) > 0 else -1.0
            midpoint = start_t + max(self.edycja.step_ms, (end_t - start_t) // 2)
            midpoint = min(max(start_t + self.edycja.step_ms, midpoint), end_t - self.edycja.step_ms) if end_t - start_t > self.edycja.step_ms * 2 else midpoint
            if cps[-1].time != start_t:
                cps.append(TarzanControlPoint(time=start_t, amplitude=0.0))
            cps.append(TarzanControlPoint(time=midpoint, amplitude=0.45 * sign))
            cps.append(TarzanControlPoint(time=end_t, amplitude=0.0))
        dedup=[]
        for cp in cps:
            if dedup and dedup[-1].time == cp.time:
                dedup[-1] = cp
            else:
                dedup.append(cp)
        axis_take.curve.control_points = dedup

    def _load_take(self, path: str | Path) -> None:
        take_path = Path(path)
        self.editor_mode = self.MODE_EDITOR
        self.take = TarzanTake.load_json(take_path)
        ensure_take_axes(self.take)
        for definition in AXIS_DEFINITIONS:
            axis_take = self.take.axes[definition.key]
            if not self._axis_curve_has_nonzero_values(axis_take) and getattr(axis_take, "segments", None):
                self._rebuild_axis_curve_from_segments(axis_take)
        self.original_take = copy.deepcopy(self.take)
        self.take_path = take_path
        self.take_path_var.set(str(take_path))

        self.axis_lines = {definition.key: self.krzywe.build_from_axis(self.take.axes[definition.key]) for definition in AXIS_DEFINITIONS}
        self._conform_axis_lines_to_mechanics()
        self.selected_axis_key = AXIS_DEFINITIONS[0].key
        self._normalize_take_timeline_from_lines()
        self.current_xlim = self._full_xlim()

        self._rebuild_tracks()
        self._regenerate_all_protocols()
        self._refresh_tracks()
        self._update_mode_ui()
        self._ensure_preview_window()
        self._refresh_preview_window()
        self.status_var.set(f"Załadowano TAKE: {take_path.name}")

    def _rebuild_tracks(self) -> None:
        for child in self.tracks_frame.winfo_children():
            child.destroy()
        self.axis_tracks.clear()

        for definition in AXIS_DEFINITIONS:
            axis_take = self.take.axes[definition.key]
            track = AxisTrack(
                self.tracks_frame,
                axis_key=definition.key,
                axis_take=axis_take,
                line=self.axis_lines[definition.key],
                krzywe=self.krzywe,
                edycja=self.edycja,
                on_change=self._on_axis_line_change,
                on_select=self._on_select_axis,
                on_status=self._set_status,
            )
            track.pack(fill="x", pady=6)
            self.axis_tracks[definition.key] = track

        event_time = self._get_drone_time()
        self.drone_track = DroneTrack(
            self.tracks_frame,
            event_time_ms=event_time,
            on_change=self._on_drone_change,
            edycja=self.edycja,
        )
        self.drone_track.pack(fill="x", pady=6)

    def _get_drone_time(self) -> int:
        for event in getattr(self.take, "events", []):
            if getattr(event, "event_type", "") == DRONE_KEY and getattr(event, "enabled", True):
                return int(event.event_time)
        start, end = self._full_xlim()
        return int((start + end) // 2)

    def _normalize_take_timeline_from_lines(self) -> None:
        if not self.take:
            return
        starts = []
        ends = []
        sample_step = int(getattr(self.take.timeline, "sample_step", 10) or 10)
        for definition in AXIS_DEFINITIONS:
            line = self.axis_lines.get(definition.key)
            if getattr(line, "nodes", None):
                starts.append(int(line.nodes[0].time_ms))
                ends.append(int(line.nodes[-1].time_ms))
            else:
                starts.append(0)
                ends.append(sample_step)
        if not starts or not ends:
            return
        self.take.timeline.take_start = min(starts)
        self.take.timeline.take_end = max(ends)
        self.take.timeline.take_duration = max(sample_step, int(self.take.timeline.take_end) - int(self.take.timeline.take_start))

    def _regenerate_all_protocols(self) -> None:
        if not self.take:
            return
        for definition in AXIS_DEFINITIONS:
            axis_key = definition.key
            line = self.axis_lines.get(axis_key)
            axis_take = self.take.axes[axis_key]
            axis_take.generated_protocol = self.step_generator.generate_axis_protocol(
                axis_take=axis_take,
                line=line,
                timeline=self.take.timeline,
            )

    def _regenerate_axis_protocol(self, axis_key: str) -> None:
        if not self.take:
            return
        self.take.axes[axis_key] = self.krzywe.export_to_axis(self.take.axes[axis_key], self.axis_lines[axis_key])
        self.take.axes[axis_key].generated_protocol = self.step_generator.generate_axis_protocol(axis_take=self.take.axes[axis_key], line=self.axis_lines[axis_key], timeline=self.take.timeline)

    def _refresh_tracks(self) -> None:
        if not self.current_xlim:
            self.current_xlim = self._full_xlim()
        view_start, view_end = self.current_xlim
        for axis_key, track in self.axis_tracks.items():
            track.axis_take = self.take.axes[axis_key]
            track.set_line(self.axis_lines[axis_key])
            track.set_view(view_start, view_end)
            track.set_selected(axis_key == self.selected_axis_key)
        if self.drone_track is not None:
            self.drone_track.set_view(view_start, view_end)
            self.drone_track.set_selected(self.selected_axis_key == DRONE_KEY)
        self._refresh_preview_window()

    def _draw_global_timeline(self) -> None:
        c = getattr(self, "global_canvas", None)
        if c is None:
            return
        c.delete("all")
        width = max(100, int(c.winfo_width()))
        height = max(20, int(c.winfo_height()))
        c.create_line(10, height // 2, width - 10, height // 2, fill="#AEB7C2", width=2)
        if not self.current_xlim:
            return
        start, end = self.current_xlim
        step = max(100, int((end - start) / 8))
        for t in range(start, end + 1, step):
            rel = 0 if end == start else (t - start) / (end - start)
            x = 10 + rel * (width - 20)
            c.create_line(x, 4, x, height - 4, fill="#58606B", width=1)
            c.create_text(x, height - 2, anchor="n", text=str(t), fill="#F3F6F8", font=("Segoe UI", 8))

    def _full_xlim(self) -> tuple[int, int]:
        start = int(getattr(self.take.timeline, "take_start", 0))
        end = int(getattr(self.take.timeline, "take_end", 0))
        if end <= start:
            end = start + 10000
        return start, end

    def zoom_in(self) -> None:
        if not self.take:
            return
        start, end = self.current_xlim or self._full_xlim()
        center = (start + end) / 2.0
        half = max(200, int((end - start) * 0.4))
        self.current_xlim = (int(center - half), int(center + half))
        self._refresh_tracks()
        self._set_status("Powiększono timeline")

    def zoom_out(self) -> None:
        if not self.take:
            return
        full_start, full_end = self._full_xlim()
        start, end = self.current_xlim or (full_start, full_end)
        center = (start + end) / 2.0
        half = int((end - start) * 0.65)
        new_start = max(full_start, int(center - half))
        new_end = min(full_end, int(center + half))
        if new_end - new_start < 400:
            new_end = min(full_end, new_start + 400)
        self.current_xlim = (new_start, new_end)
        self._refresh_tracks()
        self._set_status("Oddalono timeline")

    def zoom_reset(self) -> None:
        if not self.take:
            return
        self.current_xlim = self._full_xlim()
        self._refresh_tracks()
        self._set_status("Pełny widok timeline")

    def _on_axis_line_change(self, axis_key: str, line) -> None:
        self.axis_lines[axis_key] = copy.deepcopy(line)
        self._normalize_take_timeline_from_lines()
        self._regenerate_axis_protocol(axis_key)
        self.current_xlim = self._full_xlim()
        if axis_key == self.selected_axis_key:
            track = self.axis_tracks.get(axis_key)
            if track is not None:
                result = track.get_validation_result()
                self._set_status(
                    f"{self.take.axes[axis_key].axis_name} | P={int(round(result.pulses_total))}/{int(round(result.pulses_limit))} | "
                    f"R={int(round(result.peak_rate))}/{int(round(result.rate_limit))} | "
                    f"A={int(round(result.peak_acceleration))}/{int(round(result.acceleration_limit))}"
                )
        self._refresh_tracks()

    def _on_select_axis(self, axis_key: str) -> None:
        self.selected_axis_key = axis_key
        self._refresh_tracks()
        self._refresh_preview_window()
        self._set_status(f"Wybrano oś: {self.take.axes[axis_key].axis_name}")

    def _on_drone_change(self, event_time_ms: int) -> None:
        self.selected_axis_key = DRONE_KEY
        updated = False
        for event in self.take.events:
            if getattr(event, "event_type", "") == DRONE_KEY:
                event.event_time = int(event_time_ms)
                updated = True
        if not updated:
            self.take.events.append(
                TarzanEvent(
                    event_id="EV_DRONE_001",
                    event_type=DRONE_KEY,
                    event_time=int(event_time_ms),
                    enabled=True,
                    note="release",
                )
            )
        self._refresh_tracks()
        self._refresh_preview_window()
        self._set_status(f"Ustawiono DRON release: {int(event_time_ms)} ms")

    def _sync_take_from_lines(self) -> None:
        for axis_key, line in self.axis_lines.items():
            self.take.axes[axis_key] = self.krzywe.export_to_axis(self.take.axes[axis_key], line)
        ensure_take_axes(self.take)
        for definition in AXIS_DEFINITIONS:
            axis_take = self.take.axes[definition.key]
            if not self._axis_curve_has_nonzero_values(axis_take) and getattr(axis_take, "segments", None):
                self._rebuild_axis_curve_from_segments(axis_take)
        self._normalize_take_timeline_from_lines()

    def _collect_validation_errors(self) -> list[str]:
        errors: list[str] = []
        for definition in AXIS_DEFINITIONS:
            track = self.axis_tracks.get(definition.key)
            if track is None:
                continue
            result = track.get_validation_result()
            if not result.is_valid:
                errors.append(
                    f"{definition.axis_name}: "
                    f"P={int(round(result.pulses_total))}/{int(round(result.pulses_limit))} | "
                    f"R={int(round(result.peak_rate))}/{int(round(result.rate_limit))} | "
                    f"A={int(round(result.peak_acceleration))}/{int(round(result.acceleration_limit))}"
                )
        return errors

    def save_take(self) -> None:
        if not self.take:
            self._set_status("Brak TAKE do zapisania.")
            return

        errors = self._collect_validation_errors()
        if errors:
            self._set_status("Zapis zablokowany: " + " || ".join(errors))
            return

        self._sync_take_from_lines()
        self._regenerate_all_protocols()
        base_path = self.take_path or self.default_take_path or (self.base_dir / "data" / "take" / "TAKE_001_v01.json")
        new_take_path = self.versioning.save_new_take(
            original_take_path=base_path,
            take_dict=self.take.to_dict(),
        )
        self.take_path = new_take_path
        self.take_path_var.set(str(new_take_path))
        self._set_status(f"Zapisano nową wersję TAKE: {new_take_path.name}")

    def open_take_dialog(self) -> None:
        if self.editor_mode != self.MODE_EDITOR:
            self._set_status("Wczytywanie pliku jest dostępne tylko w trybie EDYTOR.")
            return
        initial_dir = self.base_dir / "data" / "take"
        selected = filedialog.askopenfilename(
            title="Wybierz plik TAKE",
            initialdir=str(initial_dir),
            filetypes=[("TAKE JSON", "*.json"), ("Wszystkie pliki", "*.*")],
        )
        if selected:
            self._load_take(selected)


    def _ensure_preview_window(self) -> None:
        if self.preview_window is not None and self.preview_window.winfo_exists():
            return
        self.preview_window = TarzanTakePreviewWindow(self)
        self.preview_window.protocol("WM_DELETE_WINDOW", self._close_preview_window)

    def _close_preview_window(self) -> None:
        if self.preview_window is not None and self.preview_window.winfo_exists():
            self.preview_window.destroy()
        self.preview_window = None

    def open_take_preview_window(self) -> None:
        self._ensure_preview_window()
        if self.preview_window is not None:
            self.preview_window.deiconify()
            self.preview_window.lift()
            self._refresh_preview_window()

    def _refresh_preview_window(self) -> None:
        if self.preview_window is None or not self.preview_window.winfo_exists() or self.take is None:
            return
        axis_key = self.selected_axis_key or (AXIS_DEFINITIONS[0].key if AXIS_DEFINITIONS else DRONE_KEY)
        if axis_key in self.axis_lines:
            self._regenerate_axis_protocol(axis_key)
        track = self.axis_tracks.get(axis_key) if axis_key in self.axis_tracks else None
        line = self.axis_lines.get(axis_key)
        validation_result = track.get_validation_result() if track is not None else None
        self.preview_window.refresh(self.take, axis_key, line, validation_result)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)


def main() -> None:
    app = TarzanEdytorChoreografiiRuchu()
    app.mainloop()


if __name__ == "__main__":
    main()
