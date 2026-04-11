from __future__ import annotations

import tkinter as tk

from editor.EHR.tarzanEhrMainTakeSettings import DEFAULT_AXIS_COLORS, MainTakeSettings
from editor.EHR.tarzanEhrMultiAxisModel import DEFAULT_AXIS_DEFINITIONS


class MainTakeSettingsDialog(tk.Toplevel):
    def __init__(self, master, settings: MainTakeSettings, save_callback, apply_callback) -> None:
        super().__init__(master)
        self.master_window = master
        self.settings = settings
        self.save_callback = save_callback
        self.apply_callback = apply_callback

        self.title("Ustawienia MAIN TAKE")
        self.configure(bg=master.BG)
        self.transient(master)
        self.grab_set()
        self.geometry("760x980")
        self.minsize(680, 900)

        self.minutes_var = tk.DoubleVar(value=settings.take_duration_minutes)
        self.zero_line_color_var = tk.StringVar(value=settings.zero_line_color)
        self.zero_line_width_var = tk.IntVar(value=settings.zero_line_width)
        self.curve_line_width_var = tk.IntVar(value=settings.curve_line_width)
        self.active_curve_line_width_var = tk.IntVar(value=settings.active_curve_line_width)
        self.snap_enabled_var = tk.BooleanVar(value=settings.snap_to_zero_enabled)
        self.snap_threshold_var = tk.DoubleVar(value=settings.snap_to_zero_threshold)
        self.show_protocol_var = tk.BooleanVar(value=settings.show_protocol_preview)
        self.show_metrics_var = tk.BooleanVar(value=settings.show_axis_metrics)
        self.show_labels_var = tk.BooleanVar(value=settings.show_axis_labels)
        self.show_gears_var = tk.BooleanVar(value=settings.show_axis_gears)
        self.show_status_var = tk.BooleanVar(value=settings.show_status_bar)
        self.show_grid_var = tk.BooleanVar(value=settings.show_minute_grid)
        self.show_background_tint_var = tk.BooleanVar(value=settings.show_axis_background_tint)
        self.background_strength_var = tk.IntVar(value=settings.axis_background_strength_percent)
        self.active_axis_emphasis_var = tk.IntVar(value=getattr(settings, 'active_axis_emphasis_percent', 10))
        self.active_axis_border_width_var = tk.IntVar(value=getattr(settings, 'active_axis_border_width', 3))
        self.show_start_stop_squares_var = tk.BooleanVar(value=settings.show_start_stop_squares)
        self.show_activity_markers_var = tk.BooleanVar(value=settings.show_axis_activity_markers)
        self.smooth_strength_default_var = tk.DoubleVar(value=getattr(settings, 'smooth_strength_default', 0.35))
        self.smooth_passes_default_var = tk.IntVar(value=getattr(settings, 'smooth_passes_default', 2))
        self.axis_color_vars = {
            axis.axis_id: tk.StringVar(value=settings.axis_color_overrides.get(axis.axis_id, DEFAULT_AXIS_COLORS.get(axis.axis_id, axis.color)))
            for axis in DEFAULT_AXIS_DEFINITIONS
        }

        self._build_ui()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.master_window.BG)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        canvas = tk.Canvas(outer, bg=self.master_window.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        frame = tk.Frame(canvas, bg=self.master_window.PANEL, padx=16, pady=16)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._section_label(frame, "CZAS I LINIE GŁÓWNE")
        self._entry_row(frame, "GLOBALNY CZAS MAIN TAKE (min)", self.minutes_var)
        self._entry_row(frame, "KOLOR LINII 0", self.zero_line_color_var)
        self._entry_row(frame, "GRUBOŚĆ LINII 0", self.zero_line_width_var)
        self._entry_row(frame, "GRUBOŚĆ LINII OSI", self.curve_line_width_var)
        self._entry_row(frame, "GRUBOŚĆ AKTYWNEJ OSI", self.active_curve_line_width_var)

        self._section_label(frame, "PROSTOTA INTERFEJSU")
        self._check_row(frame, "PRZYCIĄGANIE DO 0", self.snap_enabled_var)
        self._entry_row(frame, "PRÓG PRZYCIĄGANIA DO 0", self.snap_threshold_var)
        self._check_row(frame, "POKAŻ PODGLĄD PROTOKOŁU", self.show_protocol_var)
        self._check_row(frame, "POKAŻ METRYKI OSI", self.show_metrics_var)
        self._check_row(frame, "POKAŻ NAZWY OSI", self.show_labels_var)
        self._check_row(frame, "POKAŻ KOŁA USTAWIEŃ OSI", self.show_gears_var)
        self._check_row(frame, "POKAŻ PASEK STATUSU", self.show_status_var)
        self._check_row(frame, "POKAŻ SIATKĘ MINUT", self.show_grid_var)

        self._section_label(frame, "PODŚWIETLANIE AKTYWNEJ OSI")
        self._check_row(frame, "POKAŻ DELIKATNE TŁO OSI W KOLORZE LINII", self.show_background_tint_var)
        self._entry_row(frame, "PRZEŹROCZYSTOŚĆ / SIŁA TŁA OSI (%)", self.background_strength_var)
        self._entry_row(frame, "DODATKOWE PODBICIE AKTYWNEJ OSI (%)", self.active_axis_emphasis_var)
        self._entry_row(frame, "GRUBOŚĆ LEWEGO ZNACZNIKA AKTYWNEJ OSI", self.active_axis_border_width_var)
        self._check_row(frame, "POKAŻ KWADRATY START / STOP", self.show_start_stop_squares_var)
        self._check_row(frame, "POKAŻ MARKERY CZASU DZIAŁANIA OSI", self.show_activity_markers_var)

        self._section_label(frame, "DOMYŚLNE WYGŁADZANIE")
        self._entry_row(frame, "DOMYŚLNA SIŁA WYGŁADZANIA", self.smooth_strength_default_var)
        self._entry_row(frame, "DOMYŚLNA ILOŚĆ PRZEJŚĆ", self.smooth_passes_default_var)

        self._section_label(frame, "KOLORY POSZCZEGÓLNYCH OSI")
        color_grid = tk.Frame(frame, bg=self.master_window.PANEL)
        color_grid.pack(fill="x", pady=(0, 8))
        for row, axis in enumerate(DEFAULT_AXIS_DEFINITIONS):
            tk.Label(color_grid, text=axis.axis_name, bg=self.master_window.PANEL, fg=self.master_window.FG,
                     anchor="w", font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
            tk.Entry(color_grid, textvariable=self.axis_color_vars[axis.axis_id], bg="#39424E", fg=self.master_window.FG,
                     relief="flat", insertbackground=self.master_window.FG, width=14).grid(row=row, column=1, sticky="ew", pady=4)
            preview = tk.Canvas(color_grid, width=36, height=18, bg=self.master_window.PANEL, highlightthickness=0)
            preview.grid(row=row, column=2, padx=(8, 0), pady=4)
            self._bind_color_preview(preview, self.axis_color_vars[axis.axis_id])
        color_grid.grid_columnconfigure(1, weight=1)

        btns = tk.Frame(frame, bg=self.master_window.PANEL)
        btns.pack(fill="x", pady=(14, 0))
        tk.Button(btns, text="ZASTOSUJ", command=self._apply_only, bg="#0F766E", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="left")
        tk.Button(btns, text="ZAPISZ USTAWIENIA", command=self._save_all, bg="#2563EB", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="left", padx=6)
        tk.Button(btns, text="ZAMKNIJ", command=self.destroy, bg="#4B5563", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="right")

    def _bind_color_preview(self, canvas: tk.Canvas, var: tk.StringVar) -> None:
        def _safe_color(value: str) -> str:
            value = (value or "").strip()
            if len(value) == 7 and value.startswith("#"):
                try:
                    int(value[1:], 16)
                    return value
                except ValueError:
                    pass
            return "#39424E"

        def draw(*_args) -> None:
            color = _safe_color(var.get())
            canvas.delete("all")
            canvas.create_rectangle(2, 2, 34, 16, fill=color, outline="#66707C")
        var.trace_add("write", draw)
        draw()

    def _section_label(self, parent, text) -> None:
        tk.Label(parent, text=text, bg=self.master_window.PANEL, fg=self.master_window.FG,
                 anchor="w", font=("Segoe UI Semibold", 10)).pack(fill="x", pady=(8, 6))

    def _entry_row(self, parent, label, var) -> None:
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.pack(fill="x", pady=4)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        tk.Entry(wrap, textvariable=var, bg="#39424E", fg=self.master_window.FG, relief="flat", insertbackground=self.master_window.FG).pack(fill="x")

    def _scale_row(self, parent, label, var, from_, to, resolution) -> None:
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.pack(fill="x", pady=4)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                 bg=self.master_window.PANEL, fg=self.master_window.FG, troughcolor="#39424E",
                 highlightthickness=0, bd=0, length=320).pack(fill="x")

    def _check_row(self, parent, label, var) -> None:
        tk.Checkbutton(parent, text=label, variable=var, bg=self.master_window.PANEL, fg=self.master_window.FG,
                       activebackground=self.master_window.PANEL, activeforeground=self.master_window.FG,
                       selectcolor="#39424E", anchor="w", relief="flat").pack(fill="x", pady=1)

    def _collect(self) -> MainTakeSettings:
        settings = MainTakeSettings(
            take_duration_minutes=float(self.minutes_var.get()),
            zero_line_color=self.zero_line_color_var.get().strip() or "#E03A3A",
            zero_line_width=int(self.zero_line_width_var.get()),
            curve_line_width=int(self.curve_line_width_var.get()),
            active_curve_line_width=int(self.active_curve_line_width_var.get()),
            snap_to_zero_enabled=bool(self.snap_enabled_var.get()),
            snap_to_zero_threshold=float(self.snap_threshold_var.get()),
            show_protocol_preview=bool(self.show_protocol_var.get()),
            show_axis_metrics=bool(self.show_metrics_var.get()),
            show_axis_labels=bool(self.show_labels_var.get()),
            show_axis_gears=bool(self.show_gears_var.get()),
            show_status_bar=bool(self.show_status_var.get()),
            show_minute_grid=bool(self.show_grid_var.get()),
            show_axis_background_tint=bool(self.show_background_tint_var.get()),
            axis_background_strength_percent=int(self.background_strength_var.get()),
            active_axis_emphasis_percent=int(self.active_axis_emphasis_var.get()),
            active_axis_border_width=int(self.active_axis_border_width_var.get()),
            show_start_stop_squares=bool(self.show_start_stop_squares_var.get()),
            show_axis_activity_markers=bool(self.show_activity_markers_var.get()),
            smooth_strength_default=float(self.smooth_strength_default_var.get()),
            smooth_passes_default=int(self.smooth_passes_default_var.get()),
            axis_color_overrides={axis_id: var.get().strip() or DEFAULT_AXIS_COLORS.get(axis_id, "#FFFFFF") for axis_id, var in self.axis_color_vars.items()},
        )
        settings.clamp()
        return settings

    def _apply_only(self) -> None:
        self.apply_callback(self._collect())

    def _save_all(self) -> None:
        self.save_callback(self._collect())
