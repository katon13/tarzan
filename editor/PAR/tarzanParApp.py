from __future__ import annotations

import json
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.tarzanSignalBus import get_signal_bus
from editor.PAR.tarzanParBridge import TarzanParBridge
from editor.PAR.tarzanParPanels import TarzanParPanels
from editor.PAR.tarzanParWidgets import COLORS, apply_dark_style

try:
    from core.tarzanProfiler import profile_method, profile_block
except Exception:
    def profile_method(name=None):
        def deco(func):
            return func
        return deco
    class profile_block:
        def __init__(self, name): self.name = name
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

ROOT_DIR = Path(__file__).resolve().parents[2]
LAYOUT_PATH = ROOT_DIR / "data" / "par" / "tarzan_par_layout.json"
DEFAULT_TAKE_PATH = ROOT_DIR / "data" / "take" / "TAKE_001_protocol_v01.txt"

DEFAULT_VISIBLE = {
    "axes": True,
    "limits": True,
    "sensors": True,
    "operator": True,
    "ui": True,
    "bridge": True,
    "dron": True,
    "lcd": True,
    "matrix_led": True,
    "keyboard": True,
    "poextbus_cnc": True,
    "functions": False,
    "camera": True,
    "autostatus": True,
    "system": True,
    "take": True,
    "timeline": True,
    "log": True,
    "settings": True,
    "all_signals": False,
}


class TarzanParApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TARZAN PAR — Pulpit Anatomii Ruchu")
        self.geometry("1600x1000")
        self.minsize(1280, 760)
        self.configure(bg=COLORS["bg"])
        apply_dark_style(self)

        self.visible = dict(DEFAULT_VISIBLE)
        self.visible.update(self.load_layout().get("panels", {}))

        self.bus = get_signal_bus("TEST")
        self.bridge = TarzanParBridge(self.bus)
        self.panels = TarzanParPanels(self, self.bus)
        self.bus.subscribe(self.panels.on_state_change)
        self.take_label = None

        self.build()
        self.refresh()
        self.after(500, self.tick)

    def load_layout(self):
        try:
            return json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"panels": DEFAULT_VISIBLE}

    def save_layout(self):
        LAYOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        LAYOUT_PATH.write_text(json.dumps({"panels": self.visible}, ensure_ascii=False, indent=2), encoding="utf-8")

    def build(self):
        self.header = tk.Frame(self, bg="#020304", height=52)
        self.header.pack(fill="x")
        self.body = tk.Frame(self, bg=COLORS["bg"])
        self.body.pack(fill="both", expand=True, padx=8, pady=7)
        self.footer = tk.Frame(self, bg="#020304", height=28)
        self.footer.pack(fill="x")

        tk.Label(self.header, text="🦍  TARZAN PAR", bg="#020304", fg="#f6f8fa", font=("Segoe UI", 22, "bold")).pack(side="left", padx=14)
        self.mode_label = tk.Label(self.header, text="SYSTEM OK", bg="#08620e", fg="#fff", font=("Segoe UI", 11, "bold"), padx=18, pady=9)
        self.mode_label.pack(side="left", padx=8)
        tk.Button(self.header, text="TEST", bg="#b38316", fg="#fff", relief="flat", font=("Segoe UI", 10, "bold"), command=lambda: self.set_mode("TEST")).pack(side="left", padx=3)
        tk.Button(self.header, text="LIVE", bg="#1f2b34", fg="#fff", relief="flat", font=("Segoe UI", 10, "bold"), command=lambda: self.set_mode("LIVE")).pack(side="left", padx=3)
        tk.Button(self.header, text="MIX", bg="#1f2b34", fg="#fff", relief="flat", font=("Segoe UI", 10, "bold"), command=lambda: self.set_mode("MIX")).pack(side="left", padx=3)

        for text in ["PLAY (PoKeys57U) SN: 34238", "REC (PoKeys57U) SN: 33410", "CNC (PoKeys57U)"]:
            box = tk.Frame(self.header, bg="#070b0e", highlightbackground="#1c2a32", highlightthickness=1)
            box.pack(side="left", padx=6, pady=7)
            led = tk.Canvas(box, width=18, height=18, bg="#070b0e", highlightthickness=0)
            led.pack(side="left", padx=(8, 2))
            led.create_oval(4, 4, 14, 14, fill=COLORS["green"], outline="")
            tk.Label(box, text=text, bg="#070b0e", fg=COLORS["text"], font=("Segoe UI", 10)).pack(side="left", padx=8)

        tk.Button(self.header, text="⚙", bg="#11191f", fg="#fff", relief="flat", font=("Segoe UI", 16), command=self.panel_menu).pack(side="right", padx=7)

        self.left = tk.Frame(self.body, bg=COLORS["bg"], width=210)
        self.left.pack(side="left", fill="y", padx=(0, 8))
        self.center = tk.Frame(self.body, bg=COLORS["bg"])
        self.center.pack(side="left", fill="both", expand=True)
        self.right = tk.Frame(self.body, bg=COLORS["bg"], width=300)
        self.right.pack(side="right", fill="y", padx=(8, 0))

        self.nav()
        self.top = tk.Frame(self.center, bg=COLORS["bg"]); self.top.pack(fill="x")
        self.mid = tk.Frame(self.center, bg=COLORS["bg"]); self.mid.pack(fill="both", expand=True)
        self.bottom = tk.Frame(self.center, bg=COLORS["bg"], height=220); self.bottom.pack(fill="x")

        tk.Label(self.footer, text="TARZAN PAR v0.5.0 SignalBus/PAR IO", bg="#020304", fg=COLORS["muted"]).pack(side="left", padx=12)
        tk.Label(self.footer, text="PULPIT ANATOMII RUCHU — TEST/LIVE/MIX — TAKE → SIGNALBUS", bg="#020304", fg=COLORS["muted"]).pack(side="left", expand=True)
        self.clock = tk.Label(self.footer, text="", bg="#020304", fg=COLORS["muted"])
        self.clock.pack(side="right", padx=12)

    def nav(self):
        tk.Label(self.left, text="URZĄDZENIA", bg=COLORS["panel2"], fg=COLORS["text"], anchor="w", padx=12, pady=9, font=("Segoe UI", 11, "bold")).pack(fill="x")
        items = [
            ("axes", "  🦾  Osie i Silniki"), ("limits", "  ♟  Krańcówki"), ("sensors", "  ◈  Czujniki"),
            ("operator", "  ⌁  Sterowanie Operatora"), ("ui", "  ▣  UI (Panel)"), ("bridge", "  ↔  Mostek PLAY ↔ REC"),
            ("dron", "  🛩  DRON"), ("lcd", "  ▤  LCD 1602"), ("matrix_led", "  ▦  Matrix LED 8x8"),
            ("keyboard", "  ⌨  Klawiatura"), ("poextbus_cnc", "  ▥  PoExtBus / CNC"), ("functions", "  🔒  Funkcje / Rezerwy"),
            ("camera", "  📷  Kamera i KHR"), ("autostatus", "  ⚙  AUTOSTATUS"), ("system", "  ⚙  System i Status"),
            ("take", "  🎬  TAKE Player"), ("all_signals", "  ✣  Wszystkie Sygnały"),
        ]
        for key, label in items:
            tk.Button(self.left, text=label, anchor="w", bg="#101820", fg=COLORS["text"], relief="flat", font=("Segoe UI", 10), command=lambda k=key: self.toggle_panel(k)).pack(fill="x", ipady=8, pady=1)

        filt = tk.Frame(self.left, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        filt.pack(side="bottom", fill="x", pady=8)
        tk.Label(filt, text="FILTRY", bg=COLORS["panel2"], fg=COLORS["text"], anchor="w", padx=12, pady=7, font=("Segoe UI", 10, "bold")).pack(fill="x")
        for name in ["Płytka", "Kierunek", "Typ", "Grupa"]:
            row = tk.Frame(filt, bg=COLORS["panel"]); row.pack(fill="x", padx=10, pady=5)
            tk.Label(row, text=name, bg=COLORS["panel"], fg=COLORS["text"], width=8, anchor="w").pack(side="left")
            ttk.Combobox(row, values=["Wszystkie"], width=13).pack(side="right")
        tk.Entry(filt, bg="#070b0e", fg=COLORS["text"], insertbackground=COLORS["text"]).pack(fill="x", padx=10, pady=10)

    @profile_method("PAR_APP.clear")
    def clear(self):
        for parent in [self.top, self.mid, self.bottom, self.right]:
            for child in parent.winfo_children():
                child.destroy()

    @profile_method("PAR_APP.refresh")
    def refresh(self):
        with profile_block("PAR_APP.refresh.clear"):
            self.clear()
        p = self.panels
        with profile_block("PAR_APP.refresh.build_axes"):
            if self.visible.get("axes"):
                p.axes(self.top).pack(fill="x", pady=(0, 6))

        row1 = tk.Frame(self.mid, bg=COLORS["bg"])
        row1.pack(fill="both", expand=True)
        row2 = tk.Frame(self.mid, bg=COLORS["bg"])
        row2.pack(fill="both", expand=True, pady=(6, 0))

        with profile_block("PAR_APP.refresh.row1"):
            if self.visible.get("limits"): p.limits(row1).pack(side="left", fill="both", expand=True, padx=(0, 4))
            if self.visible.get("sensors"): p.sensors(row1).pack(side="left", fill="both", expand=True, padx=4)
            if self.visible.get("operator"): p.operator(row1).pack(side="left", fill="both", expand=True, padx=4)
            if self.visible.get("ui"): p.ui_panel(row1).pack(side="left", fill="both", padx=4)
            if self.visible.get("bridge"): p.bridge(row1).pack(side="left", fill="both", padx=(4, 0))

        with profile_block("PAR_APP.refresh.row2"):
            if self.visible.get("dron"): p.dron(row2).pack(side="left", fill="both", expand=True, padx=(0, 4))
            if self.visible.get("lcd"): p.lcd_panel(row2).pack(side="left", fill="both", expand=True, padx=4)
            if self.visible.get("matrix_led"): p.matrix_led_panel(row2).pack(side="left", fill="both", expand=True, padx=4)
            if self.visible.get("keyboard"): p.keyboard_panel(row2).pack(side="left", fill="both", expand=True, padx=4)
            if self.visible.get("poextbus_cnc"): p.poextbus_cnc(row2).pack(side="left", fill="both", expand=True, padx=4)
            if self.visible.get("functions"): p.functions_panel(row2).pack(side="left", fill="both", expand=True, padx=(4, 0))

        with profile_block("PAR_APP.refresh.bottom"):
            if self.visible.get("timeline"): p.timeline(self.bottom).pack(side="left", fill="both", expand=True, padx=(0, 4))
            if self.visible.get("log"): p.log(self.bottom).pack(side="left", fill="both", expand=True, padx=4)

        with profile_block("PAR_APP.refresh.right"):
            if self.visible.get("take"): p.take_control(self.right).pack(fill="x", pady=(0, 6))
            if self.visible.get("camera"): p.camera(self.right).pack(fill="x", pady=6)
            if self.visible.get("autostatus"): p.autostatus(self.right).pack(fill="x", pady=6)
            if self.visible.get("system"): p.system(self.right).pack(fill="x", pady=6)
            if self.visible.get("settings"): p.settings(self.right).pack(fill="x", pady=6)
            if self.visible.get("all_signals"): p.all_signals(self.right).pack(fill="both", expand=True, pady=6)

        p.update_log()
        self.update_take_label()
        self.save_layout()

    def hide_panel(self, key):
        self.visible[key] = False
        self.refresh()

    def toggle_panel(self, key):
        self.visible[key] = not self.visible.get(key, False)
        self.refresh()

    def panel_menu(self):
        win = tk.Toplevel(self)
        win.title("PAR — panele")
        win.geometry("340x650")
        win.configure(bg=COLORS["panel"])
        for key in DEFAULT_VISIBLE:
            var = tk.BooleanVar(value=self.visible.get(key, False))
            def cmd(k=key, v=var):
                self.visible[k] = bool(v.get())
                self.refresh()
            tk.Checkbutton(win, text=key, variable=var, command=cmd, bg=COLORS["panel"], fg=COLORS["text"], selectcolor="#101820").pack(anchor="w", padx=14, pady=5)

    def set_mode(self, mode):
        self.bridge.set_mode(mode)
        color = "#b38316" if mode == "TEST" else ("#08620e" if mode == "LIVE" else "#18528c")
        self.mode_label.configure(text=f"TRYB: {mode}", bg=color)

    def load_take_dialog(self):
        initial = str(DEFAULT_TAKE_PATH.parent if DEFAULT_TAKE_PATH.parent.exists() else ROOT_DIR)
        path = filedialog.askopenfilename(title="Wybierz TAKE TXT", initialdir=initial, filetypes=[("TARZAN TAKE TXT", "*.txt"), ("Wszystkie", "*.*")])
        if path:
            self.load_take(path)

    def load_take(self, path):
        try:
            take = self.bridge.load_take(path)
            self.bridge.step_take_index(0)
            self.update_take_label()
            self.bus.log("PAR", f"TAKE gotowy: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("PAR TAKE", str(exc))

    def play_take(self):
        self.bridge.play_take()

    def pause_take(self):
        self.bridge.pause_take()

    def stop_take(self):
        self.bridge.stop_take()

    def update_take_label(self):
        if not self.take_label:
            return
        take = self.bridge.take_player.take
        if not take:
            self.take_label.configure(text="TAKE: brak")
        else:
            self.take_label.configure(text=f"TAKE: {Path(take.path).name}\nrows={len(take.rows)} duration={take.duration_ms} ms\ntime={self.bus.take_time_ms} ms")

    @profile_method("PAR_APP.tick")
    def tick(self):
        self.clock.configure(text=f"CZAS SYSTEMU: {time.strftime('%H:%M:%S')}    TAKE: {self.bus.take_time_ms} ms    FPS: 60")
        self.panels.update_log()
        self.panels.refresh_axis_cards()
        self.panels.draw_timeline()
        self.update_take_label()
        self.after(500, self.tick)
