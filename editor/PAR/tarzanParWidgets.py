from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Callable, Optional

COLORS = {
    "bg": "#050708",
    "panel": "#11191f",
    "panel2": "#18232b",
    "panel3": "#0d1318",
    "border": "#2e3f4b",
    "text": "#eef4f7",
    "muted": "#a9b5bd",
    "green": "#24e22d",
    "red": "#ff2b22",
    "amber": "#f0a622",
    "blue": "#2688f0",
    "button": "#202b33",
}


def apply_dark_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TCombobox", fieldbackground="#11191f", background="#11191f", foreground=COLORS["text"])
    style.configure("Horizontal.TScale", background=COLORS["panel"])
    style.configure("Vertical.TScrollbar", background=COLORS["panel2"], troughcolor=COLORS["panel"])


class Led(tk.Canvas):
    def __init__(self, parent, size: int = 24, bg: str = COLORS["panel"], **kwargs):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.size = size
        self.state = 0
        self.draw()

    def set(self, value):
        self.state = 1 if value else 0
        self.draw()

    def draw(self):
        self.delete("all")
        color = COLORS["green"] if self.state else COLORS["red"]
        glow = "#134d16" if self.state else "#5a1613"
        self.create_oval(1, 1, self.size - 1, self.size - 1, fill=glow, outline="")
        self.create_oval(4, 4, self.size - 4, self.size - 4, fill=color, outline="#111")
        self.create_oval(7, 5, max(8, self.size // 2), max(8, self.size // 2), fill="#ffffff", outline="", stipple="gray50")


class Panel(tk.Frame):
    def __init__(self, parent, title: str, on_hide: Optional[Callable[[], None]] = None):
        super().__init__(parent, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        head = tk.Frame(self, bg=COLORS["panel2"], height=34)
        head.pack(fill="x")
        tk.Label(head, text=title, bg=COLORS["panel2"], fg=COLORS["text"],
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=12, pady=7)
        if on_hide:
            tk.Button(head, text="👁", bg="#22313a", fg=COLORS["text"], relief="flat",
                      width=3, command=on_hide).pack(side="right", padx=5, pady=4)
        self.body = tk.Frame(self, bg=COLORS["panel"])
        self.body.pack(fill="both", expand=True, padx=10, pady=8)


class SignalRow(tk.Frame):
    def __init__(self, parent, label: str, value=0, command: Optional[Callable[[], None]] = None, icon: str = "●", led_size: int = 22):
        super().__init__(parent, bg=COLORS["panel"])
        self.command = command
        if icon:
            tk.Label(self, text=icon, bg=COLORS["panel"], fg="#e9eef2", width=2,
                     font=("Segoe UI Symbol", 12)).pack(side="left")
        tk.Label(self, text=label, bg=COLORS["panel"], fg=COLORS["text"], anchor="w",
                 font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)
        self.led = Led(self, size=led_size, bg=COLORS["panel"])
        self.led.pack(side="right", padx=4)
        self.led.set(value)
        self.bind("<Button-1>", self._click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._click)

    def _click(self, _event=None):
        if self.command:
            self.command()

    def set(self, value):
        self.led.set(value)


class AxisCard(tk.Frame):
    def __init__(self, parent, title: str, icon_text: str, image_path: Optional[str] = None):
        super().__init__(parent, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)
        self._photo = None
        tk.Label(self, text=title, bg=COLORS["panel3"], fg=COLORS["text"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        if image_path and Path(image_path).exists():
            try:
                self._photo = tk.PhotoImage(file=image_path)
                tk.Label(self, image=self._photo, bg=COLORS["panel3"]).pack(anchor="w", padx=12, pady=(0, 4))
            except Exception:
                tk.Label(self, text=icon_text, bg=COLORS["panel3"], fg=COLORS["blue"], font=("Segoe UI Symbol", 34, "bold")).pack(anchor="w", padx=14)
        else:
            tk.Label(self, text=icon_text, bg=COLORS["panel3"], fg=COLORS["blue"], font=("Segoe UI Symbol", 34, "bold")).pack(anchor="w", padx=14)

        led_row = tk.Frame(self, bg=COLORS["panel3"])
        led_row.pack(fill="x", padx=8, pady=4)
        self.step = self._mini_led(led_row, "STEP", 0)
        self.dir = self._mini_led(led_row, "DIR", 0)
        self.en = self._mini_led(led_row, "EN", 1)

        flag = tk.Frame(self, bg=COLORS["panel3"])
        flag.pack(fill="x", padx=8, pady=6)
        self.flag_led = Led(flag, size=22, bg=COLORS["panel3"])
        self.flag_led.pack(side="left")
        self.flag_led.set(0)
        tk.Label(flag, text="  FLAGA (KONIEC RUCHU)", bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 10)).pack(side="left")

        tk.Label(self, text="STEROWANIE", bg=COLORS["panel3"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=8, pady=(2, 0))
        btns = tk.Frame(self, bg=COLORS["panel3"])
        btns.pack(fill="x", padx=8, pady=5)
        tk.Button(btns, text="◀ KROK", bg=COLORS["button"], fg=COLORS["text"], relief="flat").pack(side="left", padx=(0, 5))
        tk.Button(btns, text="KROK ▶", bg=COLORS["button"], fg=COLORS["text"], relief="flat").pack(side="left", padx=(0, 5))
        tk.Button(btns, text="STOP", bg="#b0211a", fg="#fff", relief="flat").pack(side="right")

        speed = tk.Frame(self, bg=COLORS["panel3"])
        speed.pack(fill="x", padx=8, pady=5)
        tk.Label(speed, text="PRĘDKOŚĆ", bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w")
        scale = tk.Scale(speed, from_=0, to=100, orient="horizontal", bg=COLORS["panel3"], troughcolor="#263741", highlightthickness=0, showvalue=False, length=150)
        scale.set(50)
        scale.pack(side="left", fill="x", expand=True)
        tk.Label(speed, text="50%", bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 11)).pack(side="right")

        self.counter_label = tk.Label(self, text="LICZNIK KROKÓW        0", bg=COLORS["panel3"], fg=COLORS["green"], font=("Segoe UI", 10, "bold"))
        self.counter_label.pack(anchor="w", padx=8, pady=(3, 10))
        self.counter = 0

    def _mini_led(self, parent, label, value):
        box = tk.Frame(parent, bg=COLORS["panel3"])
        box.pack(side="left", fill="x", expand=True)
        tk.Label(box, text=label, bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).pack()
        led = Led(box, size=26, bg=COLORS["panel3"])
        led.pack(pady=2)
        led.set(value)
        return led

    def set_step(self, value):
        if value and not self.step.state:
            self.counter += 1
            self.counter_label.configure(text=f"LICZNIK KROKÓW        {self.counter}")
        self.step.set(value)

    def set_dir(self, value):
        self.dir.set(value)

    def set_en(self, value):
        self.en.set(value)
