from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Callable, Optional

COLORS = {
    "bg": "#050708",
    "panel": "#11191f",
    "panel2": "#18232b",
    "header": "#18232b",
    "panel3": "#0d1318",
    "border": "#2e3f4b",
    "text": "#eef4f7",
    "muted": "#a9b5bd",
    "green": "#24e22d",
    "red": "#ff2b22",
    "amber": "#f0a622",
    "orange": "#ff9800",
    "blue": "#2688f0",
    "violet": "#9b35ff",
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
    def __init__(self, parent, size: int = 24, bg: str = COLORS["panel"], blocked: bool = False, **kwargs):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.size = size
        self.state = 0
        self.blocked = bool(blocked)
        self.draw()

    def set_blocked(self, blocked: bool = True):
        self.blocked = bool(blocked)
        self.draw()

    def set(self, value):
        self.state = 1 if value else 0
        self.draw()

    def draw(self):
        """Zunifikowana wersja v9: LED-y bez białych rozbłysków."""
        self.delete("all")
        if self.blocked:
            color = COLORS.get("violet", "#9b35ff")
            glow = "#3d145f"
            outline = "#c58cff"
            self.create_oval(1, 1, self.size - 1, self.size - 1, fill=glow, outline="")
            self.create_oval(4, 4, self.size - 4, self.size - 4, fill=color, outline=outline, width=2)
        else:
            color = COLORS["green"] if self.state else COLORS["red"]
            glow = "#134d16" if self.state else "#5a1613"
            self.create_oval(1, 1, self.size - 1, self.size - 1, fill=glow, outline="#26333a", width=1)
            self.create_oval(4, 4, self.size - 4, self.size - 4, fill=color, outline="#111", width=1)


class RectLed(tk.Canvas):
    """Zunifikowany prostokątny wskaźnik STEP/DIR/EN (dawny _TarzanRectLed v9)."""
    def __init__(self, parent, width=42, height=18, active_color=COLORS["blue"], bg=COLORS["panel3"], **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.width = width
        self.height = height
        self.active_color = active_color
        self.state = 0
        self.draw()

    def set(self, value):
        self.state = 1 if value else 0
        self.draw()

    def draw(self):
        self.delete("all")
        if self.state:
            fill = self.active_color
            outline = "#5ebeff" if self.active_color == COLORS["blue"] else "#7dff84"
        else:
            fill = "#24313a"
            outline = "#3d5969" if self.active_color == COLORS["blue"] else "#5f6b72"
        self.create_rectangle(2, 2, self.width - 2, self.height - 2, fill=fill, outline=outline, width=2)


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
    def __init__(self, parent, label: str, value=0, command: Optional[Callable[[], None]] = None, icon: str = "●", led_size: int = 22, blocked: bool = False):
        super().__init__(parent, bg=COLORS["panel"])
        self.blocked = bool(blocked)
        self.command = None if self.blocked else command

        if icon:
            tk.Label(
                self,
                text=icon,
                bg=COLORS["panel"],
                fg="#e9eef2",
                width=2,
                font=("Segoe UI Symbol", 12),
                anchor="center",
            ).pack(side="left", padx=(0, 2))

        tk.Label(
            self,
            text=label,
            bg=COLORS["panel"],
            fg=COLORS["muted"] if self.blocked else COLORS["text"],
            anchor="w",
            font=("Segoe UI", 10),
        ).pack(side="left", fill="x", expand=True)

        self.led = Led(self, size=led_size, bg=COLORS["panel"], blocked=self.blocked)
        self.led.pack(side="right", padx=(8, 4))
        self.led.set(value)

        self.bind("<Button-1>", self._click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._click)

    def _click(self, _event=None):
        if self.command:
            self.command()

    def set(self, value):
        self.led.set(value)

    def set_blocked(self, blocked: bool = True):
        self.blocked = bool(blocked)
        self.command = None if self.blocked else self.command
        self.led.set_blocked(blocked)


class AxisCard(tk.Frame):
    def __init__(
        self,
        parent,
        title: str,
        icon_text: str,
        image_path: Optional[str] = None,
        on_step_left: Optional[Callable[[], None]] = None,
        on_step_right: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)

        self._photo = None
        self.on_step_left = on_step_left
        self.on_step_right = on_step_right
        self.counter = 0
        self.spin_phase = 0.0
        self.motor_angle = 0.0
        self._hold_after_id = None
        self._hold_direction = None
        self._motor_idle_after = None

        top = tk.Frame(self, bg=COLORS["panel3"])
        top.pack(fill="x", padx=8, pady=(6, 2))

        if image_path and Path(image_path).exists():
            try:
                self._photo = tk.PhotoImage(file=image_path)
                tk.Label(top, image=self._photo, bg=COLORS["panel3"]).pack(anchor="center")
            except Exception:
                tk.Label(top, text=icon_text, bg=COLORS["panel3"], fg=COLORS["blue"],
                         font=("Segoe UI Symbol", 30, "bold")).pack(anchor="center")
        else:
            tk.Label(top, text=icon_text, bg=COLORS["panel3"], fg=COLORS["blue"],
                     font=("Segoe UI Symbol", 30, "bold")).pack(anchor="center")

        tk.Label(self, text=title, bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 10, "bold"),
                 justify="center", wraplength=170).pack(fill="x", padx=8, pady=(0, 5))

        led_row = tk.Frame(self, bg=COLORS["panel3"])
        led_row.pack(fill="x", padx=8, pady=4)
        self.step = self._mini_led(led_row, "STEP", 0)
        self.dir = self._mini_led(led_row, "DIR", 0)
        self.en = self._mini_led(led_row, "EN", 1)

        end_row = tk.Frame(self, bg=COLORS["panel3"])
        end_row.pack(fill="x", padx=8, pady=(4, 2))
        self.end_left = self._mini_led(end_row, "STOP LEWO", 0, size=22)
        self.end_right = self._mini_led(end_row, "STOP PRAWO", 0, size=22)

        btns = tk.Frame(self, bg=COLORS["panel3"])
        btns.pack(fill="x", padx=8, pady=5)

        left_btn = tk.Button(btns, text="◀ LEWO", bg=COLORS["button"], fg=COLORS["text"], relief="flat")
        left_btn.pack(side="left", padx=(0, 5), fill="x", expand=True)

        right_btn = tk.Button(btns, text="PRAWO ▶", bg=COLORS["button"], fg=COLORS["text"], relief="flat")
        right_btn.pack(side="left", fill="x", expand=True)

        left_btn.bind("<ButtonPress-1>", lambda _e: self._start_hold(0))
        right_btn.bind("<ButtonPress-1>", lambda _e: self._start_hold(1))
        left_btn.bind("<ButtonRelease-1>", lambda _e: self._stop_hold())
        right_btn.bind("<ButtonRelease-1>", lambda _e: self._stop_hold())
        left_btn.bind("<Leave>", lambda _e: self._stop_hold())
        right_btn.bind("<Leave>", lambda _e: self._stop_hold())

        self.counter_label = tk.Label(self, text="LICZNIK KROKÓW        0", bg=COLORS["panel3"],
                                      fg=COLORS["green"], font=("Segoe UI", 10, "bold"))
        self.counter_label.pack(anchor="w", padx=8, pady=(3, 4))

        self.motor_canvas = tk.Canvas(self, width=190, height=130, bg=COLORS["panel3"], highlightthickness=0)
        self.motor_canvas.pack(fill="x", padx=8, pady=(0, 10))
        self.motor_state_label = None
        self._draw_motor(active=False)

    def _mini_led(self, parent, label, value, size: int = 26):
        """Zunifikowana wersja v11: krańcówki z etykietami obok diod."""
        box = tk.Frame(parent, bg=COLORS["panel3"])
        box.pack(side="left", fill="x", expand=True, padx=2)

        if label in {"STOP LEWO", "STOP PRAWO"}:
            row = tk.Frame(box, bg=COLORS["panel3"])
            row.pack(anchor="center", pady=2)
            led = Led(row, size=max(size, 30), bg=COLORS["panel3"])
            led.pack(side="left", padx=(0, 5))
            tk.Label(row, text=label, bg=COLORS["panel3"], fg=COLORS["text"],
                     font=("Segoe UI", 8, "bold")).pack(side="left")
            led.set(value)
            return led

        tk.Label(box, text=label, bg=COLORS["panel3"],
                 fg=COLORS["blue"] if label in {"STEP", "DIR"} else COLORS["text"],
                 font=("Segoe UI", 8, "bold")).pack()

        if label in {"STEP", "DIR", "EN"}:
            active = COLORS["blue"] if label in {"STEP", "DIR"} else COLORS["green"]
            led = RectLed(box, width=44, height=18, active_color=active, bg=COLORS["panel3"])
        else:
            led = Led(box, size=max(size, 30), bg=COLORS["panel3"])
        led.pack(pady=2)
        led.set(value)
        return led

    def _start_hold(self, direction: int):
        self._hold_direction = int(direction)
        self._do_manual_step()

    def _stop_hold(self):
        self._hold_direction = None
        if self._hold_after_id:
            try:
                self.after_cancel(self._hold_after_id)
            except Exception:
                pass
        self._hold_after_id = None
        self._schedule_motor_idle()

    def _do_manual_step(self):
        if self._hold_direction is None:
            return
        if self._hold_direction:
            if self.on_step_right: self.on_step_right()
        else:
            if self.on_step_left: self.on_step_left()
        self._hold_after_id = self.after(140, self._do_manual_step)

    def set_counter(self, value):
        self.counter = value
        self.counter_label.configure(text=f"LICZNIK KROKÓW        {self.counter}")

    def _draw_motor(self, active: bool = False):
        c = self.motor_canvas
        try:
            c.delete("all")
            w = max(int(c.winfo_width()), 190)
            h = max(int(c.winfo_height()), 130)
        except Exception:
            return

        import math
        cx, cy = w / 2, h / 2
        outer_r = min(w, h) * 0.38
        inner_r = outer_r * 0.22
        outline = COLORS["green"] if active else "#6b777e"

        c.create_oval(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r, fill="#101820", outline=outline, width=3)
        c.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, fill="#dfe6e9", outline="#111", width=2)
        angle = math.radians(self.motor_angle - 90)
        x2 = cx + math.cos(angle) * (outer_r - 8)
        y2 = cy + math.sin(angle) * (outer_r - 8)
        c.create_line(cx, cy, x2, y2, fill="#ff2b22", width=4, capstyle=tk.ROUND)
        c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#111", outline="")

    def _motor_step(self):
        """Zunifikowana wersja v7: dodano logowanie kroku silnika."""
        direction = 1 if self.dir.state else -1
        self.motor_angle = (self.motor_angle + direction * (360.0 / 200.0)) % 360
        self._draw_motor(active=True)
        if self.motor_state_label:
            self.motor_state_label.configure(
                text="SILNIK: PRAWO" if self.dir.state else "SILNIK: LEWO",
                fg=COLORS["green"],
            )
        self._schedule_motor_idle()
        
        cb = getattr(self, "on_motor_step_log", None)
        if cb:
            try:
                cb()
            except Exception:
                pass

    def _schedule_motor_idle(self):
        if self._motor_idle_after:
            try:
                self.after_cancel(self._motor_idle_after)
            except Exception:
                pass
        self._motor_idle_after = self.after(180, self._motor_idle)

    def _motor_idle(self):
        self._motor_idle_after = None
        if not self.step.state and self._hold_direction is None:
            self._draw_motor(active=False)
            if self.motor_state_label:
                self.motor_state_label.configure(text="SILNIK: STOP", fg=COLORS["muted"])

    def set_step(self, value):
        value = 1 if value else 0
        previous = 1 if self.step.state else 0
        self.step.set(value)
        if value and not previous:
            self._motor_step()
        elif not value:
            self._schedule_motor_idle()

    def set_dir(self, value):
        self.dir.set(1 if value else 0)
        if self.step.state:
            self._draw_motor(active=True)

    def set_en(self, value):
        self.en.set(1 if value else 0)

    def set_end_left(self, value):
        self.end_left.set(1 if value else 0)

    def set_end_right(self, value):
        self.end_right.set(1 if value else 0)

    def set_ready(self, value):
        """ETAP 13: Wizualizacja gotowości osi (READY)."""
        # Możemy np. zmienić kolor diody EN jeśli READY=0 (brak gotowości drivera)
        if not value:
            self.en.set(0) # Driver niegotowy
        else:
            # EN może być sterowane niezależnie, więc nie wymuszamy 1 jeśli READY=1
            pass

    def set_alarm(self, value):
        """ETAP 13: Wizualizacja alarmu osi (ALARM)."""
        color = COLORS["red"] if value else COLORS["border"]
        self.configure(highlightbackground=color, highlightthickness=2 if value else 1)

    def set_locked(self, locked: bool):
        """ETAP 13: Wizualizacja blokady bezpieczeństwa (SAFETY)."""
        if locked:
            self.configure(bg="#2a1010") # Ciemnoczerwone tło
        else:
            self.configure(bg=COLORS["panel3"])
