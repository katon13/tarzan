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
        on_add_node,
        on_remove_node,
    ) -> None:
        super().__init__(parent, bg="#23272E", width=152)
        self.pack_propagate(False)

        self._bg_normal = "#23272E"
        self._bg_selected = "#313844"

        self.title_var = tk.StringVar(value=axis_name)

        self.title_label = tk.Label(
            self,
            textvariable=self.title_var,
            bg=self._bg_normal,
            fg="#F3F6F8",
            font=("Segoe UI Semibold", 9),
            justify="left",
            anchor="w",
            wraplength=128,
        )
        self.title_label.pack(fill="x", padx=8, pady=(8, 6))

        self.row1 = tk.Frame(self, bg=self._bg_normal)
        self.row1.pack(fill="x", padx=6, pady=(0, 2))
        self.row2 = tk.Frame(self, bg=self._bg_normal)
        self.row2.pack(fill="x", padx=6, pady=(0, 2))
        self.row3 = tk.Frame(self, bg=self._bg_normal)
        self.row3.pack(fill="x", padx=6, pady=(0, 8))

        self.btn_select = self._make_btn(self.row1, "WYBIERZ", on_select)
        self.btn_pan = self._make_btn(self.row1, "PAN", on_pan)

        self.btn_smooth = self._make_btn(self.row2, "SMOOTH", on_smooth)
        self.btn_reset = self._make_btn(self.row2, "RESET", on_reset)
        self.btn_auto = self._make_btn(self.row2, "AUTO", on_auto)

        self.btn_add = self._make_btn(self.row3, "+ WĘZEŁ", on_add_node)
        self.btn_remove = self._make_btn(self.row3, "- WĘZEŁ", on_remove_node)

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
        self.title_label.configure(bg=bg)
        self.row1.configure(bg=bg)
        self.row2.configure(bg=bg)
        self.row3.configure(bg=bg)

    def set_pan_active(self, active: bool) -> None:
        self.btn_pan.configure(text="PAN ON" if active else "PAN")

    def set_axis_name(self, axis_name: str) -> None:
        self.title_var.set(axis_name)
