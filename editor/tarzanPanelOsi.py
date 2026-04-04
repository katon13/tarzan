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
        super().__init__(parent, bg="#23272E", width=112)
        self.pack_propagate(False)

        self._bg_normal = "#23272E"
        self._bg_selected = "#313844"

        self.row1 = tk.Frame(self, bg=self._bg_normal)
        self.row1.pack(fill="x", padx=6, pady=(8, 2))
        self.row2 = tk.Frame(self, bg=self._bg_normal)
        self.row2.pack(fill="x", padx=6, pady=(0, 2))
        self.row3 = tk.Frame(self, bg=self._bg_normal)
        self.row3.pack(fill="x", padx=6, pady=(0, 8))

        self.btn_select = self._make_btn(self.row1, "✦", on_select, "WYBIERZ OŚ")
        self.btn_pan = self._make_btn(self.row1, "✋", on_pan, "PAN")

        self.btn_smooth = self._make_btn(self.row2, "〰", on_smooth, "WYGŁADŹ")
        self.btn_reset = self._make_btn(self.row2, "✕", on_reset, "RESET")
        self.btn_auto = self._make_btn(self.row2, "🚗", on_auto, "AUTO")

        self.btn_add = self._make_btn(self.row3, "⊕", on_add_node, "DODAJ WĘZEŁ")
        self.btn_remove = self._make_btn(self.row3, "⊖", on_remove_node, "USUŃ WĘZEŁ")

    def _make_btn(self, parent, text: str, command, tooltip_text: str):
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
            width=3,
            padx=0,
            pady=4,
            font=("Segoe UI Symbol", 10),
            cursor="hand2",
        )
        btn.pack(side="left", padx=2)
        return btn

    def set_selected(self, selected: bool) -> None:
        bg = self._bg_selected if selected else self._bg_normal
        self.configure(bg=bg)
        self.row1.configure(bg=bg)
        self.row2.configure(bg=bg)
        self.row3.configure(bg=bg)

    def set_pan_active(self, active: bool) -> None:
        self.btn_pan.configure(bg="#6B7D92" if active else "#3A434E")
