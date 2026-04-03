from __future__ import annotations

import tkinter as tk


class TarzanPanelOsi(tk.Frame):
    def __init__(
        self,
        parent,
        axis_name: str,
        on_select,
        on_pan,
        on_smooth,
        on_reset,
        on_auto,
    ) -> None:
        super().__init__(parent, bg="#23272E", width=150)
        self.pack_propagate(False)

        self.axis_name = axis_name
        self._bg_normal = "#23272E"
        self._bg_selected = "#313844"

        self.title_var = tk.StringVar(value=axis_name)

        title = tk.Label(
            self,
            textvariable=self.title_var,
            bg=self._bg_normal,
            fg="#F3F6F8",
            font=("Segoe UI Semibold", 9),
            justify="left",
            anchor="w",
            wraplength=128,
        )
        title.pack(fill="x", padx=8, pady=(8, 6))
        self._title_label = title

        row1 = tk.Frame(self, bg=self._bg_normal)
        row1.pack(fill="x", padx=6, pady=(0, 2))
        row2 = tk.Frame(self, bg=self._bg_normal)
        row2.pack(fill="x", padx=6, pady=(0, 8))
        self._rows = (row1, row2)

        self.btn_select = self._make_btn(row1, "WYBIERZ", on_select)
        self.btn_pan = self._make_btn(row1, "PAN", on_pan)
        self.btn_smooth = self._make_btn(row2, "SMOOTH", on_smooth)
        self.btn_reset = self._make_btn(row2, "RESET", on_reset)
        self.btn_auto = self._make_btn(row2, "AUTO", on_auto)

    def _make_btn(self, parent, text: str, command):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg="#3A434E",
            fg="white",
            activebackground="#556274",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=6,
            pady=4,
            font=("Segoe UI", 8),
            cursor="hand2",
        )
        btn.pack(side="left", padx=2)
        return btn

    def set_selected(self, selected: bool) -> None:
        bg = self._bg_selected if selected else self._bg_normal
        self.configure(bg=bg)
        self._title_label.configure(bg=bg)
        for row in self._rows:
            row.configure(bg=bg)

    def set_pan_active(self, active: bool) -> None:
        self.btn_pan.configure(text="PAN ON" if active else "PAN")

    def set_axis_name(self, axis_name: str) -> None:
        self.title_var.set(axis_name)
