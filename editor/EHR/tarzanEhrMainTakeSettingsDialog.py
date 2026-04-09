from __future__ import annotations

from pathlib import Path
import tkinter as tk

from editor.EHR.tarzanEhrMainTakeSettings import MainTakeSettings


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

        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self, bg=self.master_window.PANEL, padx=16, pady=16)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        self._entry_row(frame, "GLOBALNY CZAS MAIN TAKE (min)", self.minutes_var)
        self._entry_row(frame, "KOLOR LINII 0", self.zero_line_color_var)
        self._scale_row(frame, "GRUBOŚĆ LINII 0", self.zero_line_width_var, 1, 3, 1)
        self._scale_row(frame, "GRUBOŚĆ LINII OSI", self.curve_line_width_var, 1, 10, 1)
        self._scale_row(frame, "GRUBOŚĆ AKTYWNEJ OSI", self.active_curve_line_width_var, 1, 12, 1)

        check_block = tk.Frame(frame, bg=self.master_window.PANEL)
        check_block.pack(fill="x", pady=(6, 10))
        self._check_row(check_block, "PRZYCIĄGANIE DO 0", self.snap_enabled_var)
        self._scale_row(check_block, "PRÓG PRZYCIĄGANIA DO 0", self.snap_threshold_var, 0.0, 30.0, 0.5)
        self._check_row(check_block, "POKAŻ PODGLĄD PROTOKOŁU", self.show_protocol_var)
        self._check_row(check_block, "POKAŻ METRYKI OSI", self.show_metrics_var)
        self._check_row(check_block, "POKAŻ NAZWY OSI", self.show_labels_var)
        self._check_row(check_block, "POKAŻ KOŁA USTAWIEŃ OSI", self.show_gears_var)
        self._check_row(check_block, "POKAŻ PASEK STATUSU", self.show_status_var)
        self._check_row(check_block, "POKAŻ SIATKĘ MINUT", self.show_grid_var)

        btns = tk.Frame(frame, bg=self.master_window.PANEL)
        btns.pack(fill="x", pady=(10, 0))
        tk.Button(btns, text="ZASTOSUJ", command=self._apply_only, bg="#0F766E", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="left")
        tk.Button(btns, text="ZAPISZ USTAWIENIA", command=self._save_all, bg="#2563EB", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="left", padx=6)
        tk.Button(btns, text="ZAMKNIJ", command=self.destroy, bg="#4B5563", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="right")

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
        )
        settings.clamp()
        return settings

    def _apply_only(self) -> None:
        self.apply_callback(self._collect())

    def _save_all(self) -> None:
        self.save_callback(self._collect())
