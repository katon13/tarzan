
from __future__ import annotations

import copy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.tarzanTakeVersioning import TarzanTakeVersioning
from motion.tarzanGhostMotion import TarzanGhostMotion
from motion.tarzanKrzyweRuchu import TarzanKrzyweRuchu
from motion.tarzanTakeModel import TarzanTake


class TarzanEdytorChoreografiiRuchu(tk.Tk):
    BG = "#16181C"
    PANEL = "#1F2329"
    PANEL_2 = "#2A3038"
    FG = "#F3F6F8"
    MUTED = "#AEB7C2"
    GRID = "#58606B"

    BTN_PRIMARY = "#2D6CDF"
    BTN_SUCCESS = "#2E9E5B"
    BTN_WARNING = "#C78B2A"
    BTN_DANGER = "#B74A4A"
    BTN_MODE = "#6F42C1"
    BTN_AXIS = "#3A434E"
    BTN_AXIS_ACTIVE = "#556274"

    START_COLOR = "#45C46B"
    STOP_COLOR = "#E65D5D"
    CURVE_COLOR = "#7DC4FF"
    GHOST_COLOR = "#B7C0CB"
    NODE_COLOR = "#FFD166"
    NODE_SELECTED = "#FF9F1C"

    NODE_PICK_X_TOL = 80
    NODE_PICK_Y_TOL = 0.35

    def __init__(self, take_path: str | Path | None = None) -> None:
        super().__init__()

        self.title("TARZAN — Edytor Choreografii Ruchu")
        self.geometry("1680x950")
        self.minsize(1380, 860)
        self.configure(bg=self.BG)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.default_take_path = self._find_default_take_path()
        self.take_path = Path(take_path) if take_path else self.default_take_path

        self.krzywe = TarzanKrzyweRuchu()
        self.ghost = TarzanGhostMotion()
        self.versioning = TarzanTakeVersioning()

        self.take: TarzanTake | None = None
        self.original_take: TarzanTake | None = None

        self.selected_axis_key: str | None = None
        self.axis_pan_modes: dict[str, bool] = {}
        self.axis_button_widgets: dict[str, tk.Button] = {}
        self.axis_pan_widgets: dict[str, tk.Button] = {}
        self.axis_lines: dict[str, object] = {}
        self.selected_node_index: int | None = None

        self.status_var = tk.StringVar(value="Gotowy.")
        self.take_path_var = tk.StringVar(value=str(self.take_path) if self.take_path else "")
        self.interval_start_var = tk.StringVar(value="300")
        self.interval_end_var = tk.StringVar(value="1450")
        self.smooth_strength_var = tk.StringVar(value="0.35")

        self.show_nodes_var = tk.BooleanVar(value=True)
        self.show_ghost_var = tk.BooleanVar(value=True)

        self.drag_mode: str | None = None
        self.drag_axis_key: str | None = None
        self.drag_original_line = None
        self.drag_pan_anchor_x = None
        self.preview_line = None
        self.pending_drag_event = None
        self.drag_after_id = None
        self.drag_preview_interval_ms = 50
        self.drag_value_filter = 0.16

        # Dodatkowe wygładzenie preview, żeby operator widział skutek,
        # a nie drżenie kolejnych przeliczeń.
        self.drag_preview_blend_alpha = 0.24
        self.drag_preview_neighbor_alpha = 0.12
        self.drag_preview_value_deadband = 0.01

        # Wygładzenie samego wyświetlania dla człowieka.
        # Dane mogą zmieniać się poprawnie matematycznie, ale ekran ma pokazywać
        # stabilny skutek bez drobnego "drżenia" widocznego dla oka.
        self.display_preview_blend_alpha = 0.18
        self.display_preview_sampled = None

        # Ograniczenia operatorskie podczas drag.
        # Użytkownik ma widzieć skutek zgodny z mechaniką, a nie surowe liczenie.
        self.drag_preview_max_time_step_ms = 20
        self.drag_preview_max_value_step = 0.035
        self.drag_preview_local_value_band = 0.22
        self.drag_start_node_time = None
        self.drag_start_node_value = None

        self._build_ui()
        self._connect_plot_events()
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
        self._make_small_button(top_right, "Otwórz", self.open_take_dialog, self.BTN_PRIMARY).pack(side="left", padx=2)
        self._make_small_button(top_right, "Przeładuj", self.reload_take, self.BTN_WARNING).pack(side="left", padx=2)
        self._make_small_button(top_right, "Zapisz", self.save_new_take_version, self.BTN_SUCCESS).pack(side="left", padx=2)

        path_row = tk.Frame(outer, bg=self.BG)
        path_row.pack(fill="x", pady=(0, 8))
        tk.Label(path_row, text="TAKE", bg=self.BG, fg=self.FG, font=("Segoe UI", 9)).pack(side="left")
        self.take_entry = tk.Entry(
            path_row,
            textvariable=self.take_path_var,
            bg=self.PANEL_2,
            fg=self.FG,
            insertbackground=self.FG,
            relief="flat",
            font=("Segoe UI", 10),
            bd=5,
        )
        self.take_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        content = tk.Frame(outer, bg=self.BG)
        content.pack(fill="both", expand=True)

        sidebar = tk.Frame(content, bg=self.PANEL, width=210)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        self.axis_list_frame = tk.Frame(sidebar, bg=self.PANEL)
        self.axis_list_frame.pack(fill="x", padx=6, pady=(8, 8))

        self._separator(sidebar)

        self._make_check(sidebar, "Węzły", self.show_nodes_var, self._refresh_plot).pack(fill="x", padx=8, pady=(0, 0))
        self._make_check(sidebar, "Ghost", self.show_ghost_var, self._refresh_plot).pack(fill="x", padx=8, pady=(0, 6))

        self.start_entry = self._make_entry(sidebar, self.interval_start_var)
        self._add_field(sidebar, "START", self.start_entry)

        self.end_entry = self._make_entry(sidebar, self.interval_end_var)
        self._add_field(sidebar, "STOP", self.end_entry)

        self.smooth_entry = self._make_entry(sidebar, self.smooth_strength_var)
        self._add_field(sidebar, "SMOOTH", self.smooth_entry)

        # Wymuszenie widocznych wartości już po zbudowaniu pól.
        self.after(10, lambda: self._force_entry_values(
            self.interval_start_var.get() or "300",
            self.interval_end_var.get() or "1450",
            self.smooth_strength_var.get() or "0.35",
        ))

        self._make_small_button(sidebar, "Ustaw", self.apply_start_stop_from_entries, self.BTN_WARNING).pack(fill="x", padx=8, pady=(4, 4))
        self._make_small_button(sidebar, "Wygładź", self.apply_smoothing, self.BTN_PRIMARY).pack(fill="x", padx=8, pady=(0, 4))
        self._make_small_button(sidebar, "Dodaj węzeł", self.add_node_center, self.BTN_PRIMARY).pack(fill="x", padx=8, pady=(0, 4))
        self._make_small_button(sidebar, "Usuń węzeł", self.remove_selected_node, self.BTN_DANGER).pack(fill="x", padx=8, pady=(0, 4))
        self._make_small_button(sidebar, "Reset", self.reset_current_axis, self.BTN_DANGER).pack(fill="x", padx=8, pady=(0, 8))

        self.side_info_label = tk.Label(
            sidebar,
            text="START: -\nSTOP: -\nCzas: -\nPole: -\nPAN: OFF\nWęzły: -",
            bg=self.PANEL_2,
            fg=self.FG,
            justify="left",
            anchor="nw",
            padx=10,
            pady=10,
            font=("Segoe UI", 9),
        )
        self.side_info_label.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        chart_wrap = tk.Frame(content, bg=self.BG)
        chart_wrap.pack(side="left", fill="both", expand=True)

        self.plot_title_label = tk.Label(
            chart_wrap,
            text="",
            bg=self.BG,
            fg=self.FG,
            font=("Segoe UI Semibold", 13),
            anchor="w",
            pady=2,
        )
        self.plot_title_label.pack(fill="x", pady=(0, 4))

        self.figure = Figure(figsize=(12, 7), dpi=100)
        self.figure.patch.set_facecolor(self.BG)
        self.ax_curve = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_wrap)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

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

    def _separator(self, parent) -> None:
        tk.Frame(parent, bg=self.PANEL_2, height=2).pack(fill="x", padx=8, pady=(4, 8))

    def _make_small_button(self, parent, text: str, command, color: str) -> tk.Button:
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

    def _make_axis_button(self, parent, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.BTN_AXIS,
            fg="white",
            activebackground=self.BTN_AXIS_ACTIVE,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=6,
            pady=4,
            anchor="w",
            font=("Segoe UI", 8),
            cursor="hand2",
        )

    def _make_pan_button(self, parent, command) -> tk.Button:
        return tk.Button(
            parent,
            text="PAN",
            command=command,
            bg=self.BTN_MODE,
            fg="white",
            activebackground=self.BTN_MODE,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=6,
            pady=4,
            font=("Segoe UI", 8),
            cursor="hand2",
            width=5,
        )

    def _make_check(self, parent, text: str, variable, command):
        return tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            command=command,
            bg=self.PANEL,
            fg=self.FG,
            activebackground=self.PANEL,
            activeforeground=self.FG,
            selectcolor=self.PANEL_2,
            font=("Segoe UI", 9),
            anchor="w",
            pady=2,
        )

    def _make_entry(self, parent, textvariable: tk.StringVar) -> tk.Entry:
        return tk.Entry(
            parent,
            textvariable=textvariable,
            bg=self.PANEL_2,
            fg=self.FG,
            insertbackground=self.FG,
            relief="flat",
            font=("Segoe UI", 10),
            bd=4,
            width=14,
            justify="left",
            highlightthickness=1,
            highlightbackground=self.PANEL_2,
            highlightcolor=self.BTN_PRIMARY,
            selectbackground=self.BTN_PRIMARY,
            selectforeground="white",
        )

    def _add_field(self, parent, label_text: str, entry: tk.Entry) -> None:
        wrap = tk.Frame(parent, bg=self.PANEL)
        wrap.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(wrap, text=label_text, bg=self.PANEL, fg=self.FG, font=("Segoe UI Semibold", 9)).pack(anchor="w")
        entry.pack(fill="x", pady=(3, 0), in_=wrap)

    def _rebuild_axis_buttons(self) -> None:
        for child in self.axis_list_frame.winfo_children():
            child.destroy()

        self.axis_button_widgets.clear()
        self.axis_pan_widgets.clear()

        if not self.take:
            return

        for axis_key, axis in self.take.axes.items():
            row = tk.Frame(self.axis_list_frame, bg=self.PANEL)
            row.pack(fill="x", pady=2)

            select_btn = self._make_axis_button(row, axis.axis_name, lambda k=axis_key: self.select_axis(k))
            select_btn.pack(side="left", fill="x", expand=True)

            pan_btn = self._make_pan_button(row, lambda k=axis_key: self.toggle_axis_pan(k))
            pan_btn.pack(side="left", padx=(3, 0))

            self.axis_button_widgets[axis_key] = select_btn
            self.axis_pan_widgets[axis_key] = pan_btn

        self._refresh_axis_button_states()

    def _refresh_axis_button_states(self) -> None:
        for axis_key, btn in self.axis_button_widgets.items():
            btn.configure(bg=self.BTN_AXIS_ACTIVE if axis_key == self.selected_axis_key else self.BTN_AXIS)

        for axis_key, btn in self.axis_pan_widgets.items():
            btn.configure(text="ON" if self.axis_pan_modes.get(axis_key, False) else "PAN")

    def select_axis(self, axis_key: str) -> None:
        self.selected_axis_key = axis_key
        self.selected_node_index = None
        self._sync_entries_from_line()
        self._refresh_axis_button_states()
        self._refresh_plot(status_override=f"Wybrano oś: {self.take.axes[axis_key].axis_name}")

    def toggle_axis_pan(self, axis_key: str) -> None:
        self.axis_pan_modes[axis_key] = not self.axis_pan_modes.get(axis_key, False)
        self.selected_axis_key = axis_key
        self._sync_entries_from_line()
        self._refresh_axis_button_states()
        self._refresh_plot(status_override=f"PAN {'ON' if self.axis_pan_modes[axis_key] else 'OFF'} dla osi: {self.take.axes[axis_key].axis_name}")

    def _connect_plot_events(self) -> None:
        self.canvas.mpl_connect("button_press_event", self._on_plot_press)
        self.canvas.mpl_connect("button_release_event", self._on_plot_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_plot_motion)

    def _log(self, text: str) -> None:
        print(text)
        self.status_var.set(text)

    def _find_default_take_path(self) -> Path | None:
        take_dir = self.base_dir / "data" / "take"
        if not take_dir.exists():
            return None
        candidates = sorted(take_dir.glob("TAKE_*_v*.json"))
        return candidates[0] if candidates else None

    def _load_initial_take(self) -> None:
        if not self.take_path:
            self._log("Nie znaleziono domyślnego pliku TAKE.")
            return
        self._load_take(self.take_path)

    def _load_take(self, path: str | Path) -> None:
        take_path = Path(path)
        if not take_path.exists():
            self._log(f"Nie znaleziono pliku TAKE: {take_path}")
            return

        try:
            loaded_take = TarzanTake.load_json(take_path)
        except Exception as exc:
            self._log(f"Błąd ładowania TAKE: {exc}")
            return

        self.take_path = take_path
        self.take_path_var.set(str(take_path))
        self.take = loaded_take
        self.original_take = copy.deepcopy(loaded_take)
        self.axis_lines = {}

        for axis_key, axis in self.take.axes.items():
            self.axis_pan_modes.setdefault(axis_key, False)
            try:
                self.axis_lines[axis_key] = self.krzywe.build_from_axis(axis)
            except Exception as exc:
                self._log(f"Błąd budowy linii dla osi {axis.axis_name}: {exc}")

        if not self.selected_axis_key or self.selected_axis_key not in self.take.axes:
            self.selected_axis_key = next(iter(self.take.axes.keys()), None)

        self.selected_node_index = None
        self._rebuild_axis_buttons()
        self._sync_entries_from_line()
        self._refresh_plot(status_override=f"Załadowano TAKE: {take_path.name}")

    def open_take_dialog(self) -> None:
        initial_dir = self.base_dir / "data" / "take"
        selected = filedialog.askopenfilename(
            title="Wybierz plik TAKE",
            initialdir=str(initial_dir),
            filetypes=[("TAKE JSON", "*.json"), ("Wszystkie pliki", "*.*")],
        )
        if selected:
            self._load_take(selected)

    def reload_take(self) -> None:
        if self.take_path:
            self._load_take(self.take_path)

    def save_new_take_version(self) -> None:
        if not self.take or not self.take_path:
            self._log("Brak TAKE do zapisania.")
            return

        export_take = copy.deepcopy(self.take)
        for axis_key, line in self.axis_lines.items():
            export_take.axes[axis_key] = self.krzywe.export_to_axis(export_take.axes[axis_key], line)

        try:
            new_take_path = self.versioning.save_new_take(
                original_take_path=self.take_path,
                take_dict=export_take.to_dict(),
            )
        except Exception as exc:
            self._log(f"Błąd zapisu: {exc}")
            return

        self.take = export_take
        self.original_take = copy.deepcopy(export_take)
        self.take_path = new_take_path
        self.take_path_var.set(str(new_take_path))
        self._log(f"Zapisano nową wersję TAKE: {new_take_path.name}")

    def apply_start_stop_from_entries(self) -> None:
        axis_key = self._get_current_axis_key()
        if not axis_key:
            return

        line = self.preview_line if self.preview_line is not None and self.drag_axis_key == axis_key else self.axis_lines[axis_key]

        try:
            start_ms = int(self.interval_start_var.get())
            stop_ms = int(self.interval_end_var.get())
        except ValueError:
            self._log("Start i Stop muszą być liczbami całkowitymi.")
            return

        try:
            edited = self.krzywe.set_line_start_stop(
                line=line,
                new_start_ms=start_ms,
                new_stop_ms=stop_ms,
                axis=self.take.axes[axis_key],
                preserve_distance=True,
            )
        except Exception as exc:
            self._log(f"Błąd ustawiania START/STOP: {exc}")
            return

        self.axis_lines[axis_key] = edited
        self._sync_entries_from_line()
        self._refresh_plot(status_override=f"Ustawiono START/STOP dla osi: {self.take.axes[axis_key].axis_name}")

    def apply_smoothing(self) -> None:
        axis_key = self._get_current_axis_key()
        if not axis_key:
            return

        try:
            strength = float(self.smooth_strength_var.get())
        except ValueError:
            self._log("Smooth musi być liczbą.")
            return

        strength = max(0.0, min(1.0, strength))
        axis = self.take.axes[axis_key]
        line = self.axis_lines[axis_key]

        try:
            self.axis_lines[axis_key] = self.krzywe.smooth_line(
                line=line,
                strength=strength,
                preserve_distance=True,
                axis=axis,
            )
        except Exception as exc:
            self._log(f"Błąd wygładzania: {exc}")
            return

        self._sync_entries_from_line()
        self._refresh_plot(status_override=f"Wygładzono oś: {self.take.axes[axis_key].axis_name}")

    def add_node_center(self) -> None:
        axis_key = self._get_current_axis_key()
        if not axis_key:
            return

        axis = self.take.axes[axis_key]
        line = self.axis_lines[axis_key]

        start_ms = line.nodes[0].time_ms
        stop_ms = line.nodes[-1].time_ms
        mid_time = (start_ms + stop_ms) // 2

        try:
            sampled = self.krzywe.sample_line(line)
            nearest = min(sampled, key=lambda p: abs(p[0] - mid_time))
            mid_value = nearest[1]
            self.axis_lines[axis_key] = self.krzywe.add_node(line, mid_time, mid_value, axis=axis)
        except Exception as exc:
            self._log(f"Błąd dodawania węzła: {exc}")
            return

        self._refresh_plot(status_override=f"Dodano węzeł osi: {axis.axis_name}")

    def remove_selected_node(self) -> None:
        axis_key = self._get_current_axis_key()
        if not axis_key:
            return

        if self.selected_node_index is None:
            self._log("Nie wybrano węzła do usunięcia.")
            return

        try:
            self.axis_lines[axis_key] = self.krzywe.remove_node(
                self.axis_lines[axis_key],
                self.selected_node_index,
                axis=self.take.axes[axis_key],
            )
            self.selected_node_index = None
        except Exception as exc:
            self._log(f"Błąd usuwania węzła: {exc}")
            return

        self._refresh_plot(status_override=f"Usunięto węzeł osi: {self.take.axes[axis_key].axis_name}")

    def reset_current_axis(self) -> None:
        axis_key = self._get_current_axis_key()
        if not axis_key or not self.original_take:
            return

        self.axis_lines[axis_key] = self.krzywe.build_from_axis(self.original_take.axes[axis_key])
        self.selected_node_index = None
        self._sync_entries_from_line()
        self._refresh_plot(status_override=f"Przywrócono oś: {self.take.axes[axis_key].axis_name}")

    def _on_plot_press(self, event) -> None:
        if event.inaxes != self.ax_curve or event.xdata is None:
            return

        axis_key = self._get_current_axis_key(silent=True)
        if not axis_key:
            return

        self.drag_original_line = copy.deepcopy(self.axis_lines[axis_key])
        self.preview_line = None
        self.pending_drag_event = None
        self._reset_display_preview_smoothing()
        if self.drag_after_id is not None:
            try:
                self.after_cancel(self.drag_after_id)
            except Exception:
                pass
            self.drag_after_id = None

        if self.axis_pan_modes.get(axis_key, False):
            self.drag_mode = "pan"
            self.drag_axis_key = axis_key
            self.drag_pan_anchor_x = event.xdata
            return

        self.drag_mode = self._detect_drag_mode(event.xdata, event.ydata, axis_key)
        self.drag_axis_key = axis_key

        if self.drag_mode == "node":
            self.selected_node_index = self._find_nearest_node_index(event.xdata, event.ydata, axis_key)
            if self.selected_node_index is not None:
                node = self.drag_original_line.nodes[self.selected_node_index]
                self.drag_start_node_time = node.time_ms
                self.drag_start_node_value = node.value
            self._refresh_plot(status_override=f"Wybrano węzeł osi: {self.take.axes[axis_key].axis_name}")

    def _on_plot_motion(self, event) -> None:
        if not self.drag_mode or not self.drag_axis_key:
            return
        if event.inaxes != self.ax_curve or event.xdata is None:
            return

        axis_key = self.drag_axis_key
        axis = self.take.axes[axis_key]
        original = self.drag_original_line
        if original is None:
            return

        try:
            if self.drag_mode == "pan":
                delta_ms = self.krzywe.snap_time(event.xdata - self.drag_pan_anchor_x)
                self.axis_lines[axis_key] = self.krzywe.shift_line_in_time(original, delta_ms, axis)

            elif self.drag_mode == "start":
                self.axis_lines[axis_key] = self.krzywe.set_line_start_stop(
                    original,
                    int(event.xdata),
                    original.nodes[-1].time_ms,
                    axis=axis,
                    preserve_distance=True,
                )

            elif self.drag_mode == "stop":
                self.axis_lines[axis_key] = self.krzywe.set_line_start_stop(
                    original,
                    original.nodes[0].time_ms,
                    int(event.xdata),
                    axis=axis,
                    preserve_distance=True,
                )

            elif self.drag_mode == "node":
                index = self.selected_node_index
                if index is not None:
                    self.axis_lines[axis_key] = self.krzywe.move_node(
                        original,
                        index=index,
                        new_time_ms=int(event.xdata),
                        new_value=float(event.ydata) if event.ydata is not None else None,
                        axis=axis,
                        preserve_area=True,
                    )

            self._sync_entries_from_line()
            self._refresh_plot(status_override=f"Edycja osi: {axis.axis_name}", fast=True)

        except Exception as exc:
            self._log(f"Błąd edycji wykresu: {exc}")

    def _on_plot_release(self, event) -> None:
        if not self.drag_mode or not self.drag_axis_key:
            return

        axis_name = self.take.axes[self.drag_axis_key].axis_name if self.take and self.drag_axis_key in self.take.axes else self.drag_axis_key

        self.drag_mode = None
        self.drag_axis_key = None
        self.drag_original_line = None
        self.drag_pan_anchor_x = None

        self._sync_entries_from_line()
        self._refresh_plot(status_override=f"Zakończono edycję osi: {axis_name}")

    def _detect_drag_mode(self, xdata: float, ydata: float | None, axis_key: str) -> str | None:
        line = self.axis_lines[axis_key]
        start_ms = line.nodes[0].time_ms
        stop_ms = line.nodes[-1].time_ms

        line_tol = max(30.0, stop_ms * 0.012 if stop_ms > 0 else 30.0)
        if abs(xdata - start_ms) <= line_tol:
            return "start"
        if abs(xdata - stop_ms) <= line_tol:
            return "stop"

        index = self._find_nearest_node_index(xdata, ydata, axis_key)
        if index is not None:
            return "node"

        return None

    def _find_nearest_node_index(self, xdata: float | None, ydata: float | None, axis_key: str) -> int | None:
        if xdata is None or ydata is None:
            return None

        line = self.axis_lines[axis_key]

        best_index = None
        best_score = None

        for index, node in enumerate(line.nodes):
            dx = abs(node.time_ms - xdata)
            dy = abs(node.value - ydata)
            if dx <= self.NODE_PICK_X_TOL and dy <= self.NODE_PICK_Y_TOL:
                score = dx + dy * 120.0
                if best_score is None or score < best_score:
                    best_score = score
                    best_index = index

        return best_index

    def _refresh_plot(self, status_override: str | None = None, fast: bool = False) -> None:
        if not self.take or not self.selected_axis_key or self.selected_axis_key not in self.axis_lines:
            return

        axis_key = self.selected_axis_key
        axis = self.take.axes[axis_key]
        line = self.axis_lines[axis_key]

        self.plot_title_label.config(text=axis.axis_name)
        self.ax_curve.clear()
        self.ax_curve.set_facecolor(self.BG)

        if self.preview_line is not None and self.drag_mode == "node" and self.drag_axis_key == axis_key:
            sampled = self._sample_preview_line_visual(line, sample_count=90 if fast else 180)
            sampled = self._blend_display_sampled(sampled)
        else:
            self._reset_display_preview_smoothing()
            sampled = self.krzywe.sample_line(line, sample_count=55 if fast else 800)

        xs = [x for x, _ in sampled]
        ys = [y for _, y in sampled]

        self.ax_curve.plot(
            xs,
            ys,
            linewidth=3.8,
            color=self.CURVE_COLOR,
            solid_capstyle="round",
        )

        if self.show_ghost_var.get() and self.original_take:
            try:
                comparison = self.ghost.compare_axes(
                    self.original_take.axes[axis_key],
                    self.krzywe.export_to_axis(copy.deepcopy(axis), line),
                    sample_count=180 if fast else 800,
                )
                self.ax_curve.plot(
                    comparison.original_times,
                    comparison.original_amplitudes,
                    linestyle="--",
                    linewidth=2.0,
                    color=self.GHOST_COLOR,
                    alpha=0.9,
                )
            except Exception as exc:
                self._log(f"Ghost compare warning: {exc}")

        if self.show_nodes_var.get():
            node_x = [node.time_ms for node in line.nodes]
            node_y = [node.value for node in line.nodes]

            colors = []
            for index in range(len(line.nodes)):
                colors.append(self.NODE_SELECTED if self.selected_node_index == index else self.NODE_COLOR)

            self.ax_curve.scatter(
                node_x,
                node_y,
                s=170,
                color=colors,
                edgecolors="black",
                linewidths=1.0,
                zorder=6,
            )

        area = self.krzywe.compute_area(line)

        self.side_info_label.config(
            text=(
                f"START: {line.nodes[0].time_ms} ms\n"
                f"STOP: {line.nodes[-1].time_ms} ms\n"
                f"Czas: {line.nodes[-1].time_ms - line.nodes[0].time_ms} ms\n"
                f"Pole: {area:.4f}\n"
                f"PAN: {'ON' if self.axis_pan_modes.get(axis_key, False) else 'OFF'}\n"
                f"Węzły: {len(line.nodes)}"
            )
        )

        self.ax_curve.axvline(line.nodes[0].time_ms, linewidth=3.4, color=self.START_COLOR)
        self.ax_curve.axvline(line.nodes[-1].time_ms, linewidth=3.4, color=self.STOP_COLOR)
        self.ax_curve.axhline(0.0, linewidth=1.1, color=self.MUTED, alpha=0.35)

        self.ax_curve.set_xlabel("Czas [ms]", color=self.FG, fontsize=12)
        self.ax_curve.set_ylabel("Natężenie / prędkość względna", color=self.FG, fontsize=12)

        self.ax_curve.grid(True, alpha=0.22, color=self.GRID)
        self.ax_curve.tick_params(colors=self.FG, labelsize=11)
        for spine in self.ax_curve.spines.values():
            spine.set_color(self.MUTED)

        self.figure.tight_layout()
        self.canvas.draw_idle()
        self._refresh_axis_button_states()

        if status_override:
            self.status_var.set(status_override)


    def _force_entry_values(self, start_value: str, stop_value: str, smooth_value: str | None = None) -> None:
        self.interval_start_var.set(str(start_value))
        self.interval_end_var.set(str(stop_value))
        if smooth_value is not None:
            self.smooth_strength_var.set(str(smooth_value))

        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, str(start_value))

        self.end_entry.delete(0, "end")
        self.end_entry.insert(0, str(stop_value))

        smooth_text = self.smooth_strength_var.get() if smooth_value is None else str(smooth_value)
        self.smooth_entry.delete(0, "end")
        self.smooth_entry.insert(0, smooth_text)

        self.start_entry.update_idletasks()
        self.end_entry.update_idletasks()
        self.smooth_entry.update_idletasks()

    def _sync_entries_from_line(self) -> None:
        axis_key = self._get_current_axis_key(silent=True)
        if not axis_key:
            self._force_entry_values(
                self.interval_start_var.get() or "300",
                self.interval_end_var.get() or "1450",
                self.smooth_strength_var.get() or "0.35",
            )
            return

        if axis_key in self.axis_lines and len(self.axis_lines[axis_key].nodes) >= 2:
            line = self.axis_lines[axis_key]
            start_value = str(line.nodes[0].time_ms)
            stop_value = str(line.nodes[-1].time_ms)
        else:
            axis = self.take.axes.get(axis_key) if self.take else None
            if axis and getattr(axis.curve, "control_points", None):
                start_value = str(axis.curve.control_points[0].time)
                stop_value = str(axis.curve.control_points[-1].time)
            else:
                start_value = self.interval_start_var.get() or "300"
                stop_value = self.interval_end_var.get() or "1450"

        smooth_value = self.smooth_strength_var.get() or "0.35"
        self._force_entry_values(start_value, stop_value, smooth_value)


    def _sync_entries_from_preview(self) -> None:
        axis_key = self._get_current_axis_key(silent=True)
        if not axis_key:
            return

        line = self.preview_line if self.preview_line is not None else self.axis_lines.get(axis_key)
        if line is None:
            return

        self._force_entry_values(
            str(line.nodes[0].time_ms),
            str(line.nodes[-1].time_ms),
            self.smooth_strength_var.get() or "0.35",
        )


    def _sample_preview_line_visual(self, line, sample_count: int = 140):
        """
        Operatorski preview podczas przeciągania:
        - pokazuje skutek wizualny,
        - nie pokazuje matematyki finalnego przeliczenia,
        - działa jako miękka interpolacja liniowa po aktualnych węzłach.
        Finalna matematyka domykana jest dopiero po puszczeniu myszy.
        """
        if line is None or len(line.nodes) < 2:
            return []

        xs = [node.time_ms for node in line.nodes]
        ys = [node.value for node in line.nodes]

        start_x = xs[0]
        stop_x = xs[-1]
        if stop_x <= start_x:
            return list(zip(xs, ys))

        dense_x = []
        if sample_count < 2:
            sample_count = 2

        step = max(1, int((stop_x - start_x) / (sample_count - 1)))
        current = start_x
        while current < stop_x:
            dense_x.append(current)
            current += step
        dense_x.append(stop_x)

        import numpy as _np
        dense_y = _np.interp(dense_x, xs, ys)

        sampled = [(int(x), float(y)) for x, y in zip(dense_x, dense_y)]
        if sampled:
            sampled[0] = (xs[0], 0.0)
            sampled[-1] = (xs[-1], 0.0)
        return sampled


    def _constrain_preview_node_target(self, original_line, index: int, target_time: int | None, target_value: float | None):
        """
        Ogranicza preview węzła tak, aby operator nie widział chaotycznego zachowania
        sprzecznego z mechaniką. Mysz wskazuje kierunek, ale edytor dopuszcza tylko
        ruch zgodny z lokalną logiką przebiegu.
        """
        if index is None or index < 0 or index >= len(original_line.nodes):
            return target_time, target_value

        node = original_line.nodes[index]

        # --- ograniczenie czasu ---
        if target_time is not None:
            if index == 0 or index == len(original_line.nodes) - 1:
                # START / STOP nadal mają działać, ale preview nie może szarpać.
                base_time = node.time_ms
                dt = target_time - base_time
                if dt > self.drag_preview_max_time_step_ms:
                    dt = self.drag_preview_max_time_step_ms
                elif dt < -self.drag_preview_max_time_step_ms:
                    dt = -self.drag_preview_max_time_step_ms
                target_time = base_time + dt
            else:
                left_limit = original_line.nodes[index - 1].time_ms + self.krzywe.MIN_NODE_GAP_MS
                right_limit = original_line.nodes[index + 1].time_ms - self.krzywe.MIN_NODE_GAP_MS
                base_time = node.time_ms
                dt = target_time - base_time
                if dt > self.drag_preview_max_time_step_ms:
                    dt = self.drag_preview_max_time_step_ms
                elif dt < -self.drag_preview_max_time_step_ms:
                    dt = -self.drag_preview_max_time_step_ms
                target_time = max(left_limit, min(base_time + dt, right_limit))

        # --- ograniczenie wartości ---
        if target_value is not None:
            if index == 0 or index == len(original_line.nodes) - 1:
                target_value = 0.0
            else:
                left_value = original_line.nodes[index - 1].value
                right_value = original_line.nodes[index + 1].value
                center_value = node.value

                # 1) tłumienie względem pozycji startowej
                dv = target_value - center_value
                if dv > self.drag_preview_max_value_step:
                    dv = self.drag_preview_max_value_step
                elif dv < -self.drag_preview_max_value_step:
                    dv = -self.drag_preview_max_value_step
                softened = center_value + dv

                # 2) lokalne pasmo względem sąsiadów – krzywa nie może wystrzelić nielogicznie
                local_min = min(left_value, center_value, right_value) - self.drag_preview_local_value_band
                local_max = max(left_value, center_value, right_value) + self.drag_preview_local_value_band

                # 3) pasmo względem wartości początkowej klikniętego węzła
                if self.drag_start_node_value is not None:
                    start_min = self.drag_start_node_value - 0.28
                    start_max = self.drag_start_node_value + 0.28
                    local_min = max(local_min, start_min)
                    local_max = min(local_max, start_max)

                target_value = max(local_min, min(softened, local_max))

        return target_time, target_value


    def _blend_display_sampled(self, sampled):
        """
        Wygładzenie wyłącznie warstwy wyświetlania.
        Matematyka przebiegu pozostaje ta sama, ale ekran dostaje łagodniejsze
        przejście między kolejnymi klatkami, żeby człowiek nie widział drżenia.
        """
        if not sampled:
            return sampled

        if self.display_preview_sampled is None:
            self.display_preview_sampled = list(sampled)
            return sampled

        prev = self.display_preview_sampled

        prev_dict = {int(x): float(y) for x, y in prev}
        curr_dict = {int(x): float(y) for x, y in sampled}

        common_x = sorted(set(prev_dict.keys()) & set(curr_dict.keys()))
        if len(common_x) < max(8, int(len(sampled) * 0.35)):
            self.display_preview_sampled = list(sampled)
            return sampled

        blended = []
        a = self.display_preview_blend_alpha
        for x in common_x:
            py = prev_dict[x]
            cy = curr_dict[x]
            by = py + (cy - py) * a
            blended.append((x, by))

        if blended:
            blended[0] = (sampled[0][0], sampled[0][1])
            blended[-1] = (sampled[-1][0], sampled[-1][1])

        self.display_preview_sampled = blended
        return blended

    def _reset_display_preview_smoothing(self):
        self.display_preview_sampled = None

    def _get_current_axis_key(self, silent: bool = False) -> str | None:
        if not self.take:
            if not silent:
                self._log("Brak załadowanego TAKE.")
            return None

        axis_key = self.selected_axis_key
        if not axis_key:
            if not silent:
                self._log("Nie wybrano osi.")
            return None

        if axis_key not in self.take.axes:
            if not silent:
                self._log(f"Nie znaleziono osi: {axis_key}")
            return None

        return axis_key


def main() -> None:
    app = TarzanEdytorChoreografiiRuchu()
    app.mainloop()


if __name__ == "__main__":
    main()
