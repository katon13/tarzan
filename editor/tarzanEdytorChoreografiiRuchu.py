from __future__ import annotations

import copy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from core.tarzanTakeVersioning import TarzanTakeVersioning
from editor.tarzanEdycjaPunktow import TarzanEdycjaPunktow
from editor.tarzanWykresOsi import AXIS_DEFINITIONS, DRONE_KEY, AxisTrack, DroneTrack, ensure_take_axes
from motion.tarzanKrzyweRuchu import TarzanKrzyweRuchu
from motion.tarzanTakeModel import TarzanEvent, TarzanTake


class TarzanEdytorChoreografiiRuchu(tk.Tk):
    BG = "#16181C"
    PANEL_2 = "#2A3038"
    FG = "#F3F6F8"
    BTN_PRIMARY = "#2D6CDF"
    BTN_SUCCESS = "#2E9E5B"
    BTN_WARNING = "#C78B2A"

    def __init__(self, take_path: str | Path | None = None) -> None:
        super().__init__()

        self.title("TARZAN — Edytor Choreografii Ruchu")
        self.geometry("1920x1180")
        self.minsize(1920, 1080)
        self.configure(bg=self.BG)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.take_path = Path(take_path) if take_path else self._find_default_take_path()

        self.krzywe = TarzanKrzyweRuchu()
        self.versioning = TarzanTakeVersioning()
        self.edycja = TarzanEdycjaPunktow(getattr(self.krzywe, "TIME_STEP_MS", 10))

        self.take: TarzanTake | None = None
        self.original_take: TarzanTake | None = None
        self.axis_lines: dict[str, object] = {}
        self.axis_tracks: dict[str, object] = {}
        self.drone_track = None
        self.selected_axis_key: str | None = None
        self.status_var = tk.StringVar(value="Gotowy.")
        self.take_path_var = tk.StringVar(value=str(self.take_path) if self.take_path else "")

        self.current_xlim: tuple[int, int] | None = None

        self._build_ui()
        self._load_initial_take()

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
        self._make_button(top_right, "Otwórz", self.open_take_dialog, self.BTN_PRIMARY).pack(side="left", padx=2)
        self._make_button(top_right, "Zapisz", self.save_take, self.BTN_SUCCESS).pack(side="left", padx=2)
        self._make_button(top_right, "Zoom +", self.zoom_in, self.BTN_WARNING).pack(side="left", padx=2)
        self._make_button(top_right, "Zoom -", self.zoom_out, self.BTN_WARNING).pack(side="left", padx=2)
        self._make_button(top_right, "Pełny", self.zoom_reset, self.BTN_WARNING).pack(side="left", padx=2)

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

        global_bar_wrap = tk.Frame(outer, bg=self.BG)
        global_bar_wrap.pack(fill="x", pady=(0, 8))
        tk.Label(global_bar_wrap, text="GLOBAL TIMELINE", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=6)
        self.global_canvas = tk.Canvas(global_bar_wrap, height=24, bg=self.PANEL_2, highlightthickness=0, bd=0)
        self.global_canvas.pack(fill="x", padx=6, pady=(2, 0))
        self.global_canvas.bind("<Configure>", lambda _e: self._draw_global_timeline())

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
        if not self.take_path:
            self.status_var.set("Nie znaleziono domyślnego TAKE.")
            return
        self._load_take(self.take_path)

    def _load_take(self, path: str | Path) -> None:
        take_path = Path(path)
        self.take = TarzanTake.load_json(take_path)
        ensure_take_axes(self.take)
        self.original_take = copy.deepcopy(self.take)
        self.take_path = take_path
        self.take_path_var.set(str(take_path))

        self.axis_lines = {definition.key: self.krzywe.build_from_axis(self.take.axes[definition.key]) for definition in AXIS_DEFINITIONS}
        self.selected_axis_key = AXIS_DEFINITIONS[0].key
        self._normalize_take_timeline_from_lines()
        self.current_xlim = self._full_xlim()

        self._rebuild_tracks()
        self._refresh_tracks()
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
        for line in self.axis_lines.values():
            if getattr(line, "nodes", None):
                starts.append(int(line.nodes[0].time_ms))
                ends.append(int(line.nodes[-1].time_ms))
        if not starts or not ends:
            return
        self.take.timeline.take_start = min(starts)
        self.take.timeline.take_end = max(ends)
        self.take.timeline.take_duration = int(self.take.timeline.take_end) - int(self.take.timeline.take_start)

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
        self._draw_global_timeline()

    def _draw_global_timeline(self) -> None:
        c = self.global_canvas
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
        self.axis_lines[axis_key] = line
        self._normalize_take_timeline_from_lines()
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
        self._set_status(f"Ustawiono DRON release: {int(event_time_ms)} ms")

    def _sync_take_from_lines(self) -> None:
        for axis_key, line in self.axis_lines.items():
            self.take.axes[axis_key] = self.krzywe.export_to_axis(self.take.axes[axis_key], line)
        ensure_take_axes(self.take)
        self._normalize_take_timeline_from_lines()

    def _collect_validation_errors(self) -> list[str]:
        errors: list[str] = []
        for definition in AXIS_DEFINITIONS:
            track = self.axis_tracks.get(definition.key)
            if track is None:
                continue
            result = track.get_validation_result()
            if not result.is_valid:
                errors.append(f"{definition.axis_name}: {' | '.join(result.violations)}")
        return errors

    def save_take(self) -> None:
        if not self.take or not self.take_path:
            self._set_status("Brak TAKE do zapisania.")
            return

        errors = self._collect_validation_errors()
        if errors:
            self._set_status("Zapis zablokowany: " + " || ".join(errors))
            return

        self._sync_take_from_lines()
        new_take_path = self.versioning.save_new_take(
            original_take_path=self.take_path,
            take_dict=self.take.to_dict(),
        )
        self.take_path = new_take_path
        self.take_path_var.set(str(new_take_path))
        self._set_status(f"Zapisano nową wersję TAKE: {new_take_path.name}")

    def open_take_dialog(self) -> None:
        initial_dir = self.base_dir / "data" / "take"
        selected = filedialog.askopenfilename(
            title="Wybierz plik TAKE",
            initialdir=str(initial_dir),
            filetypes=[("TAKE JSON", "*.json"), ("Wszystkie pliki", "*.*")],
        )
        if selected:
            self._load_take(selected)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)


def main() -> None:
    app = TarzanEdytorChoreografiiRuchu()
    app.mainloop()


if __name__ == "__main__":
    main()
