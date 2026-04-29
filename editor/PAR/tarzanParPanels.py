from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from core.tarzanSignalBus import TarzanSignalBus, TarzanSignalState
from editor.PAR.tarzanParWidgets import COLORS, AxisCard, Led, Panel, SignalRow

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

try:
    from core.tarzanAssets import axis_icon
except Exception:
    axis_icon = None


LIMIT_LABELS = {
    "arm_h_auto_limit": "X HOME",
    "arm_h_limit_right": "X MAX",
    "arm_h_limit_left": "X MIN",
    "arm_v_auto_limit": "Y HOME",
    "arm_v_limit_up": "Y MAX",
    "arm_v_limit_down": "Y MIN",
    "cam_h_limit_right": "PAN MAX",
    "cam_h_limit_left": "PAN MIN",
    "cam_v_limit_up": "TILT MAX",
    "cam_v_limit_down": "TILT MIN",
    "cam_tilt_limit": "TILT HOME",
    "cart_limit_end": "CART END",
    "mass_reg_limit_add": "MASS MAX",
    "mass_reg_limit_remove": "MASS MIN",
    "copy_cam_v_limit_up": "COPY TILT MAX",
}

SENSOR_LABELS = {
    "i2c_scl": "MAGISTRALA I2C SCL",
    "i2c_sda": "MAGISTRALA I2C SDA",
    "shock_sensor": "CZUJNIK WSTRZĄSU",
    "rrp_pot_h": "POTENCJOMETR RRP X",
    "rrp_pot_v": "POTENCJOMETR RRP Y",
    "free_aux_pot": "POTENCJOMETR AUX",
    "sw_f1": "PRZYCISK F1",
    "sw_f2": "PRZYCISK F2",
    "sw_f3": "PRZYCISK F3",
    "sw_f4": "PRZYCISK F4",
}

AXIS_SIGNAL_BINDINGS = {
    "CAM_H": {"step": ["TAKE_CAM_H_STEP", "cnc_x_cam_h_ctr"], "dir": ["TAKE_CAM_H_DIR", "cnc_x_cam_h_dir"], "en": []},
    "CAM_V": {"step": ["TAKE_CAM_V_STEP", "cnc_y_cam_v_ctr"], "dir": ["TAKE_CAM_V_DIR", "cnc_y_cam_v_dir"], "en": []},
    "CAM_T": {"step": ["TAKE_CAM_T_STEP", "cnc_a_arm_tilt_ctr"], "dir": ["TAKE_CAM_T_DIR", "cnc_a_arm_tilt_dir"], "en": []},
    "CAM_F": {"step": ["TAKE_CAM_F_STEP", "cnc_z_focus_ctr"], "dir": ["TAKE_CAM_F_DIR", "cnc_z_focus_dir"], "en": []},
    "ARM_H": {"step": ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "cnc_b_arm_h_ctr"], "dir": ["TAKE_ARM_H_DIR", "play_p38_step_dir_arm_h", "cnc_b_arm_h_dir"], "en": ["play_p50_step_en_arm_h"]},
    "ARM_V": {"step": ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "cnc_c_arm_v_ctr"], "dir": ["TAKE_ARM_V_DIR", "play_p39_step_dir_arm_v", "cnc_c_arm_v_dir"], "en": ["play_p51_step_en_arm_v"]},
    "DRON": {"step": ["TAKE_DRON_STEP"], "dir": ["TAKE_DRON_DIR"], "en": []},
}


class TarzanParPanels:
    def __init__(self, app, bus: TarzanSignalBus) -> None:
        self.app = app
        self.bus = bus
        self.rows: Dict[str, SignalRow] = {}
        self.axis_cards: Dict[str, AxisCard] = {}
        self.log_text: Optional[tk.Text] = None
        self.timeline_canvas: Optional[tk.Canvas] = None
        self.matrix_cells: List[tk.Canvas] = []

    def panel(self, key: str, parent, title: str) -> Panel:
        return Panel(parent, title, on_hide=lambda: self.app.hide_panel(key))

    def _scroll_body(self, panel: Panel):
        canvas = tk.Canvas(panel.body, bg=COLORS["panel"], highlightthickness=0)
        scroll = ttk.Scrollbar(panel.body, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLORS["panel"])
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return inner

    @profile_method("PAR_PANEL.axes")
    def axes(self, parent):
        panel = self.panel("axes", parent, "OSIE I SILNIKI (STEP/DIR/ENABLE)")
        cards = tk.Frame(panel.body, bg=COLORS["panel"])
        cards.pack(fill="both", expand=True)
        axes = [
            ("ARM_H", "1. OŚ POZIOMA RAMIENIA", "oś pozioma ramienia", "↔"),
            ("ARM_V", "2. OŚ PIONOWA RAMIENIA", "oś pionowa ramienia", "↕"),
            ("CAM_H", "3. OŚ POZIOMA KAMERY (PAN)", "oś pozioma kamery", "⟳"),
            ("CAM_V", "4. OŚ PIONOWA KAMERY", "oś pionowa kamery", "↕"),
            ("CAM_T", "5. OŚ POCHYŁU KAMERY", "oś pochyłu kamery", "↧"),
            ("CAM_F", "6. OŚ OSTROŚCI KAMERY", "oś ostrości kamery", "◎"),
        ]
        for col, (key, title, axis_name, fallback_icon) in enumerate(axes):
            icon_path = None
            if axis_icon:
                try:
                    icon_path = axis_icon(axis_name, size=64, state="active", ext="png")
                except Exception:
                    icon_path = None
            card = AxisCard(cards, title, fallback_icon, image_path=icon_path)
            card.grid(row=0, column=col, sticky="nsew", padx=5, pady=4)
            cards.grid_columnconfigure(col, weight=1)
            self.axis_cards[key] = card
        self.refresh_axis_cards()
        return panel

    @profile_method("PAR_PANEL.limits")
    def limits(self, parent):
        panel = self.panel("limits", parent, "KRAŃCÓWKI")
        inner = self._scroll_body(panel)
        names = self._group_or_search("KRAŃCÓWKI", ["limit"])
        for name in names:
            row = SignalRow(inner, self.limit_label(name), self.bus.get(name),
                            command=lambda n=name: self.bus.toggle_input(n, source="PAR_LIMIT"),
                            icon="♟", led_size=22)
            row.pack(fill="x", pady=2)
            self.rows[name] = row
        return panel

    @profile_method("PAR_PANEL.sensors")
    def sensors(self, parent):
        panel = self.panel("sensors", parent, "CZUJNIKI / ANALOG / I2C / 1-WIRE")
        inner = self._scroll_body(panel)
        names = self._group_or_search("CZUJNIKI", ["sensor", "czujnik", "pot", "analog", "i2c", "1-wire", "wire"])
        for name in names:
            meta = self.bus.get_meta(name)
            if not meta:
                continue
            if meta.is_analog:
                self._analog_row(inner, name, self.sensor_label(name))
            else:
                cmd = (lambda n=name: self.bus.toggle_input(n, source="PAR_SENSOR")) if meta.is_input else None
                row = SignalRow(inner, self.sensor_label(name), self.bus.get(name), command=cmd, icon="◈", led_size=22)
                row.pack(fill="x", pady=2)
                self.rows[name] = row
        if not names:
            tk.Label(inner, text="Brak czujników — sprawdź ładowanie pełnej mapy I/O.", bg=COLORS["panel"], fg=COLORS["red"]).pack(anchor="w")
        return panel

    def _analog_row(self, parent, name: str, label: str):
        frame = tk.Frame(parent, bg=COLORS["panel"])
        frame.pack(fill="x", pady=3)
        tk.Label(frame, text="▰", bg=COLORS["panel"], fg=COLORS["amber"], width=2).pack(side="left")
        tk.Label(frame, text=label, bg=COLORS["panel"], fg=COLORS["text"], width=24, anchor="w").pack(side="left")
        value_label = tk.Label(frame, text=str(self.bus.get(name)), bg=COLORS["panel"], fg=COLORS["green"], width=7)
        value_label.pack(side="right")
        scale = tk.Scale(frame, from_=0, to=4095, orient="horizontal", bg=COLORS["panel"], troughcolor="#263741",
                         fg=COLORS["text"], highlightthickness=0, showvalue=False,
                         command=lambda v, n=name, lab=value_label: self._set_analog(n, v, lab))
        try:
            scale.set(float(self.bus.get(name) or 0))
        except Exception:
            pass
        scale.pack(side="left", fill="x", expand=True, padx=5)

    def _set_analog(self, name, value, label):
        try:
            v = float(value)
        except Exception:
            v = 0.0
        label.configure(text=str(int(v)))
        self.bus.set_input(name, v, source="PAR_ANALOG")

    @profile_method("PAR_PANEL.operator")
    def operator(self, parent):
        panel = self.panel("operator", parent, "STEROWANIE OPERATORA (RRP)")
        grid = tk.Frame(panel.body, bg=COLORS["panel"])
        grid.pack(fill="both", expand=True)
        buttons = [
            ("HOME ALL", "#25303a"), ("START", "#1d842c"), ("STOP", "#ae241d"), ("PAUZA", "#bf8b18"),
            ("ZASOBNIK W GÓRĘ", "#25303a"), ("ZASOBNIK W DÓŁ", "#25303a"), ("RESET", "#18528c"), ("RECOVER", "#4f2c82"),
            ("RĘKA W GÓRĘ", "#25303a"), ("RĘKA W DÓŁ", "#25303a"), ("OŚ Z WYSUNIĘTA", "#25303a"), ("OŚ Z WSUNIĘTA", "#25303a"),
        ]
        for i, (txt, bg) in enumerate(buttons):
            tk.Button(grid, text=txt, bg=bg, fg="#fff", relief="flat", font=("Segoe UI", 9, "bold"), height=2,
                      command=lambda t=txt: self.bus.log("UI", t)).grid(row=i // 4, column=i % 4, sticky="nsew", padx=5, pady=5)
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)
        return panel

    @profile_method("PAR_PANEL.ui_panel")
    def ui_panel(self, parent):
        panel = self.panel("ui", parent, "UI — PANEL (PLAY/REC)")
        candidates = [("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
                      ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
                      ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
                      ("F4", "rec_p51_sw_f4", "rec_p52_led_f4")]
        for label, sw_name, led_name in candidates:
            row = tk.Frame(panel.body, bg=COLORS["panel"])
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 16)).pack(side="left")
            tk.Button(row, text="", width=5, bg="#e8e8e8", relief="sunken",
                      command=lambda n=sw_name: self.bus.toggle_input(n, source="PAR_UI")).pack(side="left", padx=20)
            led = Led(row, size=26, bg=COLORS["panel"])
            led.pack(side="right")
            led.set(self.bus.get(led_name) or self.bus.get(sw_name))
        tk.Label(panel.body, text="ENCODER A     1234\nENCODER B     5678", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=10)
        return panel

    @profile_method("PAR_PANEL.bridge")
    def bridge(self, parent):
        panel = self.panel("bridge", parent, "MOSTEK PLAY ↔ REC")
        inner = self._scroll_body(panel)
        names = self.bus.by_group("MOSTEK_PLAY_REC")
        for name in names:
            row = tk.Frame(inner, bg=COLORS["panel"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=self.bridge_label(name), bg=COLORS["panel"], fg=COLORS["text"], width=22, anchor="w", font=("Segoe UI", 10)).pack(side="left")
            l1 = Led(row, size=22, bg=COLORS["panel"]); l1.pack(side="left", padx=4); l1.set(self.bus.get(name))
            tk.Label(row, text="→", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 16, "bold")).pack(side="left", padx=6)
            l2 = Led(row, size=22, bg=COLORS["panel"]); l2.pack(side="left", padx=4); l2.set(not self.bus.get(name))
        return panel

    def dron(self, parent):
        panel = self.panel("dron", parent, "DRON")
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=6)

        tk.Label(row, text="ZWOLNIENIE", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

        value = self.bus.get("play_p14_drone_release") if hasattr(self, "bus") else self.state.get("play_p14_drone_release")
        led = Led(row, size=30, bg=COLORS["panel"])
        led.pack(side="right", padx=6)
        led.set(value)

        tk.Button(panel.body, text="ZWOLNIJ DRONA", bg="#7a251f", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  command=lambda: self._set_or_toggle("play_p14_drone_release", 1)).pack(fill="x", pady=(8, 2))

        return panel

    def lcd_panel(self, parent):
        panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="x")

        def lcd_box(parent, title, lines):
            box = tk.Frame(parent, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
            box.pack(fill="x", pady=5)
            tk.Label(box, text=title, bg="#07110a", fg=COLORS["muted"],
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=8, pady=(5, 0))
            for line in lines:
                tk.Label(box, text=line[:16].ljust(16), bg="#07110a", fg="#38ff6a",
                         font=("Consolas", 14, "bold"), anchor="w").pack(fill="x", padx=10)

        lcd_box(wrap, "PLAY LCD", ["TARZAN PLAY", f"MODE {self.bus.mode if hasattr(self, 'bus') else 'TEST'}"])
        lcd_box(wrap, "REC LCD", ["TARZAN REC", "READY"])
        return panel

    def matrix_led_panel(self, parent):
        panel = self.panel("matrix_led", parent, "MATRIX LED 8x8 — PLAY / REC")
        grid = tk.Frame(panel.body, bg=COLORS["panel"])
        grid.pack(anchor="w", pady=4)
        self.matrix_cells = []
        for y in range(8):
            for x in range(8):
                c = tk.Canvas(grid, width=16, height=16, bg=COLORS["panel"], highlightthickness=0)
                c.grid(row=y, column=x, padx=1, pady=1)
                on = (x == y) or (x + y == 7)
                c.create_oval(2, 2, 14, 14, fill=COLORS["green"] if on else "#16301a", outline="")
                self.matrix_cells.append(c)
        names = [n for n in self.bus.names() if "matrix" in n.lower() or "led_data" in n.lower() or "led_latch" in n.lower() or "led_clk" in n.lower()]
        for name in names:
            meta = self.bus.get_meta(name)
            row = SignalRow(panel.body, self.clean(meta.opis if meta else name), self.bus.get(name), command=None, icon="▦", led_size=18)
            row.pack(fill="x", pady=1)
            self.rows[name] = row
        return panel

    def keyboard_panel(self, parent):
        panel = self.panel("keyboard", parent, "KLAWIATURA")
        grid = tk.Frame(panel.body, bg=COLORS["panel"])
        grid.pack(fill="x")

        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for i, label in enumerate(keys):
            tk.Button(grid, text=label, bg="#202b33", fg=COLORS["text"], relief="flat",
                      font=("Segoe UI", 15, "bold"), width=4, height=2,
                      command=lambda k=label: self._log("KEYBOARD", f"KEY {k}")).grid(
                          row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4
                      )

        for i in range(3):
            grid.grid_columnconfigure(i, weight=1)
        return panel

    def poextbus_cnc(self, parent):
        panel = self.panel("poextbus_cnc", parent, "PoExtBus / CNC / PULSE ENGINE")
        inner = self._scroll_body(panel)
        names = []
        for needle in ["poextbus", "cnc_", "pulse engine", "pulse_engine"]:
            for name in self.bus.search(needle):
                if name not in names:
                    names.append(name)
        for name in names:
            meta = self.bus.get_meta(name)
            cmd = None
            if meta and meta.is_input:
                cmd = lambda n=name: self.bus.toggle_input(n, source="PAR_POEXTBUS")
            row = SignalRow(inner, self._hardware_label(name), self.bus.get(name), command=cmd, icon="▤", led_size=18)
            row.pack(fill="x", pady=1)
            self.rows[name] = row
        return panel

    def functions_panel(self, parent):
        panel = self.panel("functions", parent, "FUNKCJE SPRZĘTOWE / REZERWY")
        inner = self._scroll_body(panel)
        names = []
        for name in self.bus.names():
            meta = self.bus.get_meta(name)
            if meta and (meta.is_forbidden or meta.typ in {"F", "RESERVED"} or meta.kierunek in {"F", "RESERVED"}):
                names.append(name)
        for name in names:
            meta = self.bus.get_meta(name)
            frame = tk.Frame(inner, bg=COLORS["panel"])
            frame.pack(fill="x", pady=1)
            tk.Label(frame, text="🔒", bg=COLORS["panel"], fg=COLORS["muted"], width=3).pack(side="left")
            tk.Label(frame, text=f"{meta.plytka} {meta.pin or meta.kanal or '-'}  {name}", bg=COLORS["panel"], fg=COLORS["muted"], anchor="w", font=("Segoe UI", 9)).pack(fill="x", expand=True, side="left")
        return panel


    def log_panel(self, parent):
        panel = self.panel("log", parent, "LOGI")
        top = tk.Frame(panel.body, bg=COLORS["panel"])
        top.pack(fill="x")
        tk.Button(top, text="CLEAR", bg="#202b33", fg=COLORS["text"], relief="flat",
                  command=self._clear_logs).pack(side="right", padx=2)
        tk.Label(top, text="SignalBus / PAR / TAKE", bg=COLORS["panel"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(side="left")

        self.log_text = tk.Text(panel.body, bg="#070b0e", fg=COLORS["text"], relief="flat",
                                height=12, font=("Consolas", 9), wrap="none")
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))
        self.update_log()
        return panel


    def info_panel(self, parent):
        panel = self.panel("info", parent, "PANEL INFORMACYJNY")
        snapshot = self.bus.snapshot()
        names = self.bus.names()
        in_count = out_count = f_count = reserved_count = active_count = 0
        boards = {"PLAY": 0, "REC": 0, "CNC": 0, "VIRTUAL": 0, "SYSTEM": 0}

        for name in names:
            meta = self.bus.get_meta(name)
            value = self.bus.get(name)
            if value not in (0, None, "", False):
                active_count += 1
            if not meta:
                boards["VIRTUAL"] = boards.get("VIRTUAL", 0) + 1
                continue
            boards[meta.plytka] = boards.get(meta.plytka, 0) + 1
            if meta.is_input:
                in_count += 1
            elif meta.is_output:
                out_count += 1
            elif meta.typ == "F" or meta.kierunek == "F":
                f_count += 1
            elif meta.typ == "RESERVED" or meta.kierunek == "RESERVED":
                reserved_count += 1

        def line(label, value, color=None):
            row = tk.Frame(panel.body, bg=COLORS["panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["muted"], anchor="w",
                     font=("Segoe UI", 9)).pack(side="left")
            tk.Label(row, text=str(value), bg=COLORS["panel"], fg=color or COLORS["text"], anchor="e",
                     font=("Segoe UI", 9, "bold")).pack(side="right")

        line("Tryb magistrali", self.bus.mode, COLORS["amber"] if self.bus.mode == "TEST" else COLORS["green"])
        line("Sygnały razem", len(names))
        line("Aktywne teraz", active_count, COLORS["green"])
        line("IN / OUT", f"{in_count} / {out_count}")
        line("F / RESERVED", f"{f_count} / {reserved_count}")
        line("PLAY / REC / CNC", f"{boards.get('PLAY',0)} / {boards.get('REC',0)} / {boards.get('CNC',0)}")
        line("Virtual/System", f"{boards.get('VIRTUAL',0)} / {boards.get('SYSTEM',0)}")
        line("TAKE czas", f"{self.bus.take_time_ms} ms")
        line("Historia zmian", len(self.bus.history))
        line("Log", len(self.bus.log_lines))

        tk.Label(panel.body, text="TEST: PAR podaje wejścia. OUT: pokazuje logika/TAKE.\nF i RESERVED: widoczne, ale zablokowane.",
                 bg=COLORS["panel"], fg=COLORS["text"], justify="left", anchor="w",
                 font=("Segoe UI", 8)).pack(fill="x", pady=(8, 2))

        return panel


    def camera(self, parent):
        panel = self.panel("camera", parent, "KAMERA — KHR / KLONOWANIE")
        vals = [("KAMERA START", 0), ("KAMERA BUSY", 1), ("KAMERA ERROR", 0), ("COPY DONE", 1), ("COPY ERROR", 0), ("KAMERA RDY", 1)]
        for name, val in vals:
            row = SignalRow(panel.body, name, val, icon=" ", led_size=24)
            row.pack(fill="x", pady=3)
        tk.Button(panel.body, text="COPY START", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self.bus.log("KHR", "COPY START")).pack(fill="x", pady=8)
        return panel

    def autostatus(self, parent):
        panel = self.panel("autostatus", parent, "AUTOSTATUS (PLAY)")
        vals = [("AUTO ACTIVE", 0), ("SNAPSHOT BUSY", 0), ("RECOVERY ACTIVE", 0), ("RECOVERY DONE", 1), ("SAFETY OK", 1), ("ERROR", 0)]
        for name, val in vals:
            row = SignalRow(panel.body, name, val, icon=" ", led_size=24)
            row.pack(fill="x", pady=3)
        return panel

    def system(self, parent):
        panel = self.panel("system", parent, "SYSTEM I STATUS")
        tk.Button(panel.body, text="SYSTEM OK", bg="#b0211a", fg="#fff", relief="flat", font=("Segoe UI", 10, "bold")).pack(fill="x", pady=5)
        for name, val in [("SYSTEM OK", 1), ("POKEYS CHARGE PUMP", 1), ("1-WIRE ACTIVE", 1)]:
            SignalRow(panel.body, name, val, icon=" ", led_size=24).pack(fill="x", pady=3)
        tk.Label(panel.body, text="VDD AKTUALNE        24.1 V\nTEMPERATURA         42.3 °C", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=14)
        return panel

    def take_control(self, parent):
        panel = self.panel("take", parent, "TAKE — ODTWARZACZ PROTOKOŁU")
        top = tk.Frame(panel.body, bg=COLORS["panel"]); top.pack(fill="x")
        tk.Button(top, text="LOAD TAKE", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=self.app.load_take_dialog).pack(side="left", padx=3)
        tk.Button(top, text="PLAY", bg="#1d842c", fg="#fff", relief="flat", command=self.app.play_take).pack(side="left", padx=3)
        tk.Button(top, text="PAUSE", bg="#bf8b18", fg="#fff", relief="flat", command=self.app.pause_take).pack(side="left", padx=3)
        tk.Button(top, text="STOP", bg="#ae241d", fg="#fff", relief="flat", command=self.app.stop_take).pack(side="left", padx=3)
        self.app.take_label = tk.Label(panel.body, text="TAKE: brak", bg=COLORS["panel"], fg=COLORS["text"], anchor="w")
        self.app.take_label.pack(fill="x", pady=8)
        return panel

    def timeline(self, parent):
        panel = self.panel("timeline", parent, "PODGLĄD SYGNAŁÓW (TIMELINE — STEP/DIR/ENABLE)")
        top = tk.Frame(panel.body, bg=COLORS["panel"])
        top.pack(fill="x")
        tk.Label(top, text="Skala czasu:", bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left")
        ttk.Combobox(top, values=["10 ms", "20 ms"], width=8).pack(side="left", padx=8)
        tk.Button(top, text="CLEAR", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self.bus.history.clear()).pack(side="right", padx=4)
        canvas = tk.Canvas(panel.body, bg="#070b0e", height=160, highlightthickness=0)
        canvas.pack(fill="both", expand=True, pady=8)
        self.timeline_canvas = canvas
        canvas.bind("<Configure>", lambda e: self.draw_timeline())
        self.draw_timeline()
        return panel

    def log(self, parent):
        panel = self.panel("log", parent, "LOG ZDARZEŃ")
        self.log_text = tk.Text(panel.body, bg="#070b0e", fg=COLORS["text"], relief="flat", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)
        return panel

    def settings(self, parent):
        panel = self.panel("settings", parent, "USTAWIENIA SYMULACJI")
        debug_var = tk.BooleanVar(value=self.bus.debug_override_outputs)
        def toggle_debug():
            self.bus.debug_override_outputs = bool(debug_var.get())
            self.bus.log("PAR", f"DEBUG override OUT = {self.bus.debug_override_outputs}")
        tk.Checkbutton(panel.body, text="DEBUG override OUT", variable=debug_var, command=toggle_debug, bg=COLORS["panel"], fg=COLORS["text"], selectcolor="#101820").pack(anchor="w", pady=3)
        tk.Checkbutton(panel.body, text="Loguj zdarzenia", bg=COLORS["panel"], fg=COLORS["text"], selectcolor="#101820").pack(anchor="w", pady=3)
        tk.Checkbutton(panel.body, text="Pokaż timeline", bg=COLORS["panel"], fg=COLORS["text"], selectcolor="#101820").pack(anchor="w", pady=3)
        tk.Button(panel.body, text="RESET WSZYSTKICH SYGNAŁÓW", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=self.bus.reset_to_defaults).pack(fill="x", pady=12)
        return panel

    def all_signals(self, parent):
        panel = self.panel("all_signals", parent, "WSZYSTKIE SYGNAŁY")
        inner = self._scroll_body(panel)
        for name in self.bus.names():
            meta = self.bus.get_meta(name)
            label = f"{meta.plytka if meta else ''} {meta.pin if meta else '-'}  {name}"
            cmd = (lambda n=name: self.bus.toggle_input(n, source="PAR")) if (meta and meta.is_input) else None
            row = SignalRow(inner, label, self.bus.get(name), command=cmd, icon="", led_size=18)
            row.pack(fill="x", pady=1)
            self.rows[name] = row
        return panel

    def on_state_change(self, name: str, state: TarzanSignalState):
        if name in self.rows:
            self.rows[name].set(state.value)
        self.refresh_axis_cards()
        self.update_log()

    def refresh_axis_cards(self):
        for axis, card in self.axis_cards.items():
            bind = AXIS_SIGNAL_BINDINGS.get(axis, {})
            card.set_step(self._first_value(bind.get("step", [])))
            card.set_dir(self._first_value(bind.get("dir", [])))
            en_names = bind.get("en", [])
            card.set_en(self._first_value(en_names) if en_names else 1)

    def _first_value(self, names: List[str]):
        for name in names:
            if self.bus.exists(name):
                return self.bus.get(name)
        return 0

    def update_log(self):
        if not self.log_text:
            return
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.bus.log_lines[-80:]))
        self.log_text.see("end")

    def draw_timeline(self):
        canvas = self.timeline_canvas
        if not canvas:
            return
        canvas.delete("all")
        w = max(canvas.winfo_width(), 800)
        left, right = 70, w - 15
        rows = [("STEP", COLORS["green"], "TAKE_ARM_H_STEP"), ("DIR", COLORS["blue"], "TAKE_ARM_H_DIR"), ("ENABLE", "#d4aa20", "play_p50_step_en_arm_h"), ("FLAGA", COLORS["red"], "TAKE_DRON_EVENT")]
        hist = self.bus.history[-200:]
        for idx, (label, color, sig) in enumerate(rows):
            y = 28 + idx * 31
            canvas.create_text(12, y, text=label, anchor="w", fill=COLORS["text"], font=("Segoe UI", 10, "bold"))
            canvas.create_line(left, y, right, y, fill="#22313a")
            points = []
            filtered = [h for h in hist if h.get("name") == sig]
            if not filtered:
                for x in range(left, int(right), 20):
                    val = (x // 20) % 2 if label == "STEP" else 0
                    points.append((x, y - 18 if val else y))
            else:
                step = max(1, int((right - left) / max(1, len(filtered))))
                for i, h in enumerate(filtered):
                    x = left + i * step
                    points.append((x, y - 18 if h.get("value") else y))
            for a, b in zip(points, points[1:]):
                canvas.create_line(a[0], a[1], b[0], a[1], fill=color, width=2)
                canvas.create_line(b[0], a[1], b[0], b[1], fill=color, width=2)
        for t in range(6):
            x = left + t * ((right-left)/5)
            canvas.create_line(x, 12, x, 145, fill="#162129")
            canvas.create_text(x, 10, text=f"{t}s", fill=COLORS["muted"], font=("Segoe UI", 8))

    def _group_or_search(self, group: str, needles: List[str]) -> List[str]:
        names = self.bus.by_group(group)
        seen = set(names)
        for needle in needles:
            for name in self.bus.search(needle):
                if name not in seen:
                    names.append(name); seen.add(name)
        return names

    def limit_label(self, name: str) -> str:
        for key, label in LIMIT_LABELS.items():
            if key in name:
                return label
        meta = self.bus.get_meta(name)
        return self.clean(meta.opis if meta else name)

    def sensor_label(self, name: str) -> str:
        for key, label in SENSOR_LABELS.items():
            if key in name:
                return label
        meta = self.bus.get_meta(name)
        return self.clean(meta.opis if meta else name)

    def bridge_label(self, name: str) -> str:
        for key, label in [("dir_x", "DIR X"), ("dir_y", "DIR Y"), ("dir_z", "DIR Z"), ("ctr_x", "CTR X"), ("ctr_y", "CTR Y"), ("ctr_z", "CTR Z"), ("enable", "ENABLE")]:
            if key in name:
                return label
        return "MOSTEK"

    def _hardware_label(self, name: str) -> str:
        meta = self.bus.get_meta(name)
        if not meta:
            return name
        pin = meta.pin if meta.pin is not None else (meta.kanal or "-")
        return f"{meta.plytka} {pin}  {self.clean(meta.opis or name)}"

    def clean(self, text: str) -> str:
        text = (text or "").replace("Krańcówka ", "").replace("Sygnał ", "").replace("Wejście ", "")
        return text[:42] + ("…" if len(text) > 42 else "")


    def dron_panel(self, parent):
        panel = self.panel("dron", parent, "DRON")
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=6)

        tk.Label(row, text="ZWOLNIENIE", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

        value = self.bus.get("play_p14_drone_release") if hasattr(self, "bus") else self.state.get("play_p14_drone_release")
        led = Led(row, size=30, bg=COLORS["panel"])
        led.pack(side="right", padx=6)
        led.set(value)

        tk.Button(panel.body, text="ZWOLNIJ DRONA", bg="#7a251f", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  command=lambda: self._set_or_toggle("play_p14_drone_release", 1)).pack(fill="x", pady=(8, 2))

        return panel



    def build_dron_panel(self, parent):
        panel = self.panel("dron", parent, "DRON")
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=6)

        tk.Label(row, text="ZWOLNIENIE", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

        value = self.bus.get("play_p14_drone_release") if hasattr(self, "bus") else self.state.get("play_p14_drone_release")
        led = Led(row, size=30, bg=COLORS["panel"])
        led.pack(side="right", padx=6)
        led.set(value)

        tk.Button(panel.body, text="ZWOLNIJ DRONA", bg="#7a251f", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  command=lambda: self._set_or_toggle("play_p14_drone_release", 1)).pack(fill="x", pady=(8, 2))

        return panel



    def lcd(self, parent):
        panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="x")

        def lcd_box(parent, title, lines):
            box = tk.Frame(parent, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
            box.pack(fill="x", pady=5)
            tk.Label(box, text=title, bg="#07110a", fg=COLORS["muted"],
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=8, pady=(5, 0))
            for line in lines:
                tk.Label(box, text=line[:16].ljust(16), bg="#07110a", fg="#38ff6a",
                         font=("Consolas", 14, "bold"), anchor="w").pack(fill="x", padx=10)

        lcd_box(wrap, "PLAY LCD", ["TARZAN PLAY", f"MODE {self.bus.mode if hasattr(self, 'bus') else 'TEST'}"])
        lcd_box(wrap, "REC LCD", ["TARZAN REC", "READY"])
        return panel



    def build_lcd_panel(self, parent):
        panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="x")

        def lcd_box(parent, title, lines):
            box = tk.Frame(parent, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
            box.pack(fill="x", pady=5)
            tk.Label(box, text=title, bg="#07110a", fg=COLORS["muted"],
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=8, pady=(5, 0))
            for line in lines:
                tk.Label(box, text=line[:16].ljust(16), bg="#07110a", fg="#38ff6a",
                         font=("Consolas", 14, "bold"), anchor="w").pack(fill="x", padx=10)

        lcd_box(wrap, "PLAY LCD", ["TARZAN PLAY", f"MODE {self.bus.mode if hasattr(self, 'bus') else 'TEST'}"])
        lcd_box(wrap, "REC LCD", ["TARZAN REC", "READY"])
        return panel



    def keyboard(self, parent):
        panel = self.panel("keyboard", parent, "KLAWIATURA")
        grid = tk.Frame(panel.body, bg=COLORS["panel"])
        grid.pack(fill="x")

        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for i, label in enumerate(keys):
            tk.Button(grid, text=label, bg="#202b33", fg=COLORS["text"], relief="flat",
                      font=("Segoe UI", 15, "bold"), width=4, height=2,
                      command=lambda k=label: self._log("KEYBOARD", f"KEY {k}")).grid(
                          row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4
                      )

        for i in range(3):
            grid.grid_columnconfigure(i, weight=1)
        return panel

    def build_keyboard_panel(self, parent):
        panel = self.panel("keyboard", parent, "KLAWIATURA")
        grid = tk.Frame(panel.body, bg=COLORS["panel"])
        grid.pack(fill="x")

        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for i, label in enumerate(keys):
            tk.Button(grid, text=label, bg="#202b33", fg=COLORS["text"], relief="flat",
                      font=("Segoe UI", 15, "bold"), width=4, height=2,
                      command=lambda k=label: self._log("KEYBOARD", f"KEY {k}")).grid(
                          row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4
                      )

        for i in range(3):
            grid.grid_columnconfigure(i, weight=1)
        return panel

    def klawiatura(self, parent):
        panel = self.panel("keyboard", parent, "KLAWIATURA")
        grid = tk.Frame(panel.body, bg=COLORS["panel"])
        grid.pack(fill="x")

        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for i, label in enumerate(keys):
            tk.Button(grid, text=label, bg="#202b33", fg=COLORS["text"], relief="flat",
                      font=("Segoe UI", 15, "bold"), width=4, height=2,
                      command=lambda k=label: self._log("KEYBOARD", f"KEY {k}")).grid(
                          row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4
                      )

        for i in range(3):
            grid.grid_columnconfigure(i, weight=1)
        return panel

    def _set_or_toggle(self, name, value=None):
        try:
            current = self.bus.get(name)
            new_value = (0 if current else 1) if value is None else value
            if hasattr(self.bus, "set_input"):
                self.bus.set_input(name, new_value, origin="PAR_UI")
            elif hasattr(self.bus, "write"):
                self.bus.write(name, new_value, origin="PAR_UI")
            else:
                self.bus.set(name, new_value)
            self._log("PAR_UI", f"{name} = {new_value}")
        except Exception as exc:
            self._log("PAR_UI_ERR", f"{name}: {exc}")

    def _log(self, source, message):
        try:
            if hasattr(self.bus, "log"):
                self.bus.log(source, message)
            elif hasattr(self, "state"):
                self.state.log(source, message)
        except Exception:
            pass
        self.update_log()

    def _clear_logs(self):
        try:
            if hasattr(self.bus, "log_lines"):
                self.bus.log_lines.clear()
            if hasattr(self.bus, "history"):
                self.bus.history.clear()
        except Exception:
            pass
        self.update_log()

    def update_log(self):
        if not hasattr(self, "log_text") or self.log_text is None:
            return
        try:
            lines = []
            if hasattr(self.bus, "log_lines"):
                lines.extend(self.bus.log_lines[-80:])
            if not lines and hasattr(self.bus, "history"):
                lines.extend([str(x) for x in self.bus.history[-80:]])
            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", "\n".join(lines))
            self.log_text.see("end")
        except Exception as exc:
            try:
                self.log_text.delete("1.0", "end")
                self.log_text.insert("end", f"LOG ERROR: {exc}")
            except Exception:
                pass


    def ui(self, parent):
        return self.ui_panel(parent)
