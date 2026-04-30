from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from core.tarzanSignalBus import TarzanSignalBus, TarzanSignalState
try:
    from editor.PAR.tarzanParWidgets import COLORS, AxisCard, Led, Panel, SignalRow
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, AxisCard, Led, Panel, SignalRow

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
    "CAM_H": {"step": ["TAKE_CAM_H_STEP", "cnc_x_cam_h_ctr"], "dir": ["TAKE_CAM_H_DIR", "cnc_x_cam_h_dir"], "en": [], "left": ["cam_h_limit_left", "play_p06_cam_h_limit_left"], "right": ["cam_h_limit_right", "play_p05_cam_h_limit_right"]},
    "CAM_V": {"step": ["TAKE_CAM_V_STEP", "cnc_y_cam_v_ctr"], "dir": ["TAKE_CAM_V_DIR", "cnc_y_cam_v_dir"], "en": [], "left": ["cam_v_limit_down", "play_p08_cam_v_limit_down"], "right": ["cam_v_limit_up", "play_p07_cam_v_limit_up"]},
    "CAM_T": {"step": ["TAKE_CAM_T_STEP", "cnc_a_arm_tilt_ctr"], "dir": ["TAKE_CAM_T_DIR", "cnc_a_arm_tilt_dir"], "en": [], "left": ["cam_tilt_limit", "play_p10_cam_tilt_limit"], "right": ["cam_tilt_limit", "play_p10_cam_tilt_limit"]},
    "CAM_F": {"step": ["TAKE_CAM_F_STEP", "cnc_z_focus_ctr"], "dir": ["TAKE_CAM_F_DIR", "cnc_z_focus_dir"], "en": [], "left": [], "right": []},
    "ARM_H": {"step": ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "cnc_b_arm_h_ctr"], "dir": ["TAKE_ARM_H_DIR", "play_p38_step_dir_arm_h", "cnc_b_arm_h_dir"], "en": ["play_p50_step_en_arm_h"], "left": ["arm_h_limit_left", "play_p03_arm_h_limit_left"], "right": ["arm_h_limit_right", "play_p01_arm_h_auto_limit", "play_p02_arm_h_limit_right"]},
    "ARM_V": {"step": ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "cnc_c_arm_v_ctr"], "dir": ["TAKE_ARM_V_DIR", "play_p39_step_dir_arm_v", "cnc_c_arm_v_dir"], "en": ["play_p51_step_en_arm_v"], "left": ["arm_v_limit_down", "play_p04_arm_v_limit_up"], "right": ["arm_v_limit_up", "play_p09_arm_v_auto_limit"]},
    "DRON": {"step": ["TAKE_DRON_STEP"], "dir": ["TAKE_DRON_DIR"], "en": [], "left": [], "right": []},
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
            card = AxisCard(
                cards,
                title,
                fallback_icon,
                image_path=icon_path,
                on_step_left=lambda a=key: self._manual_axis_step(a, 0),
                on_step_right=lambda a=key: self._manual_axis_step(a, 1),
            )
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
            led = Led(row, size=28, bg=COLORS["panel"])
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
            l1 = Led(row, size=28, bg=COLORS["panel"]); l1.pack(side="left", padx=4); l1.set(self.bus.get(name))
            tk.Label(row, text="→", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 16, "bold")).pack(side="left", padx=6)
            l2 = Led(row, size=28, bg=COLORS["panel"]); l2.pack(side="left", padx=4); l2.set(not self.bus.get(name))
        return panel

    def dron(self, parent):
        panel = self.panel("dron", parent, "DRON")
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=6)

        tk.Label(row, text="ZWOLNIENIE", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

        value = self.bus.get("play_p14_drone_release") if hasattr(self, "bus") else self.state.get("play_p14_drone_release")
        led = Led(row, size=28, bg=COLORS["panel"])
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
        panel = self.panel("matrix_led", parent, "MATRIX LED 8x8 — REC")
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
            row = SignalRow(panel.body, self.clean(meta.opis if meta else name), self.bus.get(name), command=None, icon="▦", led_size=22)
            row.pack(fill="x", pady=1)
            self.rows[name] = row
        return panel

    def matrix(self, parent):
        panel = self.panel("matrix", parent, "MATRIX LED 8x8 — REC")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="x")

        def matrix_box(parent, title, pattern):
            box = tk.Frame(parent, bg="#05080a", highlightbackground="#263844", highlightthickness=1)
            box.pack(fill="x", padx=2, pady=5)
            tk.Label(
                box,
                text=title,
                bg="#05080a",
                fg=COLORS["muted"],
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).pack(fill="x", padx=8, pady=(5, 2))
            grid = tk.Frame(box, bg="#05080a")
            grid.pack(padx=8, pady=(0, 8))
            for r in range(8):
                for c in range(8):
                    on = bool(pattern(r, c))
                    color = COLORS["green"] if on else "#123018"
                    dot = tk.Canvas(grid, width=15, height=15, bg="#05080a", highlightthickness=0)
                    dot.grid(row=r, column=c, padx=1, pady=1)
                    dot.create_oval(2, 2, 13, 13, fill=color, outline="")
        matrix_box(wrap, "REC MATRIX", lambda r, c: (r in (1, 6) and 1 <= c <= 6) or (c in (1, 6) and 1 <= r <= 6))
        return panel

    def matrix_panel(self, parent):
        return self.matrix(parent)


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
            row = SignalRow(inner, self._hardware_label(name), self.bus.get(name), command=cmd, icon="▤", led_size=22)
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



    # ------------------------------------------------------------------
    # NOWE OKNA WSKAŹNIKOWE CZUJNIKÓW / URZĄDZEŃ
    # Zasada: czujniki są tylko odczytem/wskaźnikiem. Nie ustawiamy ich z UI.
    # Wyjątek: lampka pracy ramienia jest klikalnym wskaźnikiem ON/OFF.
    # ------------------------------------------------------------------
    def _big_value(self, parent, label: str, signal_name: str, suffix: str = "", decimals: int = 0):
        frame = tk.Frame(parent, bg=COLORS["panel"])
        frame.pack(fill="x", pady=6)
        tk.Label(frame, text=label.upper(), bg=COLORS["panel"], fg=COLORS["muted"],
                 font=("Segoe UI", 9, "bold"), anchor="center").pack(fill="x")
        value_label = tk.Label(frame, text=self._format_value(self.bus.get(signal_name), suffix, decimals),
                               bg=COLORS["panel"], fg=COLORS["green"],
                               font=("Consolas", 24, "bold"), anchor="center", justify="center")
        value_label.pack(fill="x")
        self.rows[signal_name] = type(
            "_BigValueProxy",
            (),
            {"set": lambda _self, v, lab=value_label, suf=suffix, dec=decimals: lab.configure(text=self._format_value(v, suf, dec))}
        )()
        return value_label

    def _format_value(self, value, suffix: str = "", decimals: int = 0):
        try:
            number = float(value or 0)
            if decimals > 0:
                text = f"{number:.{decimals}f}"
            else:
                text = str(int(round(number)))
        except Exception:
            text = str(value)
        return f"{text} {suffix}".rstrip()

    def _indicator_led_row(self, parent, label: str, signal_name: str):
        row = tk.Frame(parent, bg=COLORS["panel"])
        row.pack(fill="x", pady=5)
        tk.Label(row, text=label.upper(), bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        led = Led(row, size=28, bg=COLORS["panel"])
        led.pack(side="right", padx=6)
        led.set(self.bus.get(signal_name))
        self.rows[signal_name] = type("_LedProxy", (), {"set": lambda _self, v, l=led: l.set(v)})()
        return led

    def lamp_panel(self, parent):
        panel = self.panel("lamp", parent, "PRACA")
        canvas = tk.Canvas(panel.body, width=92, height=70, bg=COLORS["panel"], highlightthickness=0)
        canvas.pack(padx=8, pady=8)
        state = self.bus.get("par_lamp_auto_active")
        rect = canvas.create_rectangle(
            14, 10, 78, 60,
            fill=COLORS["red"] if state else "#5b6268",
            outline="#d7e0e5",
            width=3,
        )
        
        def update_lamp(v, c=canvas, r=rect):
            c.itemconfigure(r, fill=COLORS["red"] if v else "#5b6268")

        def toggle(_event=None):
            self.bus.toggle_input("par_lamp_auto_active", source="PAR_LAMP")

        canvas.bind("<Button-1>", toggle)
        panel.body.bind("<Button-1>", toggle)
        self.rows["par_lamp_auto_active"] = type("_LampProxy", (), {"set": lambda _self, v: update_lamp(v)})()
        return panel

    def mass_regulator_panel(self, parent):
        panel = self.panel("mass_regulator", parent, "REGULATOR MASY")
        self._indicator_led_row(panel.body, "REGULATOR WŁĄCZONY", "par_mass_reg_enable")
        self._indicator_led_row(panel.body, "MASA DODANA", "par_mass_reg_limit_add")
        self._indicator_led_row(panel.body, "MASA ODJĘTA", "par_mass_reg_limit_remove")
        return panel

    def shock_sensor_panel(self, parent):
        panel = self.panel("shock_sensor_panel", parent, "WSTRZĄS")
        led = Led(panel.body, size=60, bg=COLORS["panel"])
        led.pack(expand=True, pady=10)
        led.set(self.bus.get("par_shock_sensor_state"))
        self.rows["par_shock_sensor_state"] = type("_ShockProxy", (), {"set": lambda _self, v: led.set(v)})()
        return panel

    def light_bh1750_panel(self, parent):
        panel = self.panel("light_bh1750", parent, "ŚWIATŁO")
        self._big_value(panel.body, "LUMENY / LUX", "par_bh1750_lux", "lx", 0)
        return panel

    def level_xyz_panel(self, parent):
        panel = self.panel("level_xyz", parent, "POZIOM")
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="both", expand=True, padx=4, pady=6)

        for col, (axis, sig) in enumerate([("X", "par_level_x"), ("Y", "par_level_y"), ("Z", "par_level_z")]):
            box = tk.Frame(row, bg=COLORS["panel"])
            box.grid(row=0, column=col, sticky="nsew", padx=4)
            row.grid_columnconfigure(col, weight=1)

            tk.Label(box, text=axis, bg=COLORS["panel"], fg=COLORS["muted"],
                     font=("Segoe UI", 13, "bold"), anchor="center").pack(fill="x")
            value_label = tk.Label(
                box,
                text=self._format_value(self.bus.get(sig), "", 0),
                bg=COLORS["panel"],
                fg=COLORS["green"],
                font=("Consolas", 24, "bold"),
                anchor="center",
                justify="center",
            )
            value_label.pack(fill="both", expand=True)
            self.rows[sig] = type(
                "_LevelValueProxy",
                (),
                {"set": lambda _self, v, lab=value_label: lab.configure(text=self._format_value(v, "", 0))}
            )()
        return panel


    def temperature_panel(self, parent):
        panel = self.panel("temperature", parent, "TEMPERATURA")
        self._big_value(panel.body, "TEMPERATURA", "par_temperature_c", "°C", 1)
        return panel

    def laser_panel(self, parent):
        panel = self.panel("laser", parent, "LASER")
        led = Led(panel.body, size=60, bg=COLORS["panel"])
        led.pack(expand=True, pady=10)
        led.set(self.bus.get("par_laser_set"))
        self.rows["par_laser_set"] = type("_LaserProxy", (), {"set": lambda _self, v: led.set(v)})()
        return panel



    def camera(self, parent):
        panel = self.panel("camera", parent, "KAMERA — KHR / KLONOWANIE")
        vals = [("KAMERA START", 0), ("KAMERA BUSY", 1), ("KAMERA ERROR", 0), ("COPY DONE", 1), ("COPY ERROR", 0), ("KAMERA RDY", 1)]
        for name, val in vals:
            row = SignalRow(panel.body, name, val, icon=" ", led_size=22)
            row.pack(fill="x", pady=3)
        tk.Button(panel.body, text="COPY START", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self.bus.log("KHR", "COPY START")).pack(fill="x", pady=8)
        return panel

    def autostatus(self, parent):
        panel = self.panel("autostatus", parent, "AUTOSTATUS (PLAY)")
        vals = [("AUTO ACTIVE", 0), ("SNAPSHOT BUSY", 0), ("RECOVERY ACTIVE", 0), ("RECOVERY DONE", 1), ("SAFETY OK", 1), ("ERROR", 0)]
        for name, val in vals:
            row = SignalRow(panel.body, name, val, icon=" ", led_size=22)
            row.pack(fill="x", pady=3)
        return panel

    def system(self, parent):
        panel = self.panel("system", parent, "SYSTEM I STATUS")
        tk.Button(panel.body, text="SYSTEM OK", bg="#b0211a", fg="#fff", relief="flat", font=("Segoe UI", 10, "bold")).pack(fill="x", pady=5)
        for name, val in [("SYSTEM OK", 1), ("POKEYS CHARGE PUMP", 1), ("1-WIRE ACTIVE", 1)]:
            SignalRow(panel.body, name, val, icon=" ", led_size=22).pack(fill="x", pady=3)
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
            row = SignalRow(inner, label, self.bus.get(name), command=cmd, icon="", led_size=22)
            row.pack(fill="x", pady=1)
            self.rows[name] = row
        return panel


    def _manual_axis_step(self, axis: str, direction: int):
        bind = AXIS_SIGNAL_BINDINGS.get(axis, {})
        for name in bind.get("dir", []):
            if self.bus.exists(name):
                self.bus.force_signal(name, int(direction), source="PAR_AXIS_STEP")
        for name in bind.get("en", []):
            if self.bus.exists(name):
                self.bus.force_signal(name, 1, source="PAR_AXIS_STEP")
        for name in bind.get("step", []):
            if self.bus.exists(name):
                self.bus.force_signal(name, 1, source="PAR_AXIS_STEP")
                try:
                    self.app.after(70, lambda n=name: self.bus.force_signal(n, 0, source="PAR_AXIS_STEP"))
                except Exception:
                    pass


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
            card.set_end_left(self._first_value(bind.get("left", [])))
            card.set_end_right(self._first_value(bind.get("right", [])))

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
        led = Led(row, size=28, bg=COLORS["panel"])
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
        led = Led(row, size=28, bg=COLORS["panel"])
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
        panel = self.panel("ui", parent, "UI PANEL PLAY / REC")
        tk.Label(panel.body, text="PRZYCISKI FUNKCYJNE PLAY / REC", bg=COLORS["panel"], fg=COLORS["muted"],
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", pady=(0, 6))

        grid = tk.Frame(panel.body, bg=COLORS["panel"])
        grid.pack(fill="x")

        buttons = [
            ("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
            ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
            ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
            ("F4", "rec_p51_sw_f4", "rec_p52_led_f4"),
        ]

        for i, (label, sw, led_sig) in enumerate(buttons):
            cell = tk.Frame(grid, bg="#0f171d", highlightbackground="#30424f", highlightthickness=1)
            cell.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)

            btn = tk.Button(
                cell,
                text=label,
                bg="#243847",
                fg="#f2f7fb",
                activebackground="#31556e",
                activeforeground="#ffffff",
                relief="flat",
                font=("Segoe UI", 16, "bold"),
                height=2,
                command=lambda s=sw: self._set_or_toggle(s),
            )
            btn.pack(fill="x", padx=7, pady=(7, 5))

            row = tk.Frame(cell, bg="#0f171d")
            row.pack(fill="x", padx=7, pady=(0, 7))
            tk.Label(row, text="LED", bg="#0f171d", fg=COLORS["muted"],
                     font=("Segoe UI", 8, "bold")).pack(side="left")
            led = Led(row, size=28, bg="#0f171d")
            led.pack(side="right")
            try:
                led.set(self.bus.get(led_sig))
            except Exception:
                led.set(0)

        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        return panel


# =====================================================================
# TARZAN PAR — implementacja symulatorów infrastruktury elektronicznej
# Dopisane jako jawne podmiany metod klasy, żeby nie naruszać układu App.
# =====================================================================

class _ParValueProxy:
    def __init__(self, callback):
        self.callback = callback
    def set(self, value):
        try:
            self.callback(value)
        except Exception:
            pass


def _par_set_signal(self, name, value, source="PAR_SIM"):
    try:
        if not self.bus.exists(name):
            self.bus.force_signal(name, value, source=source)
            return
        meta = self.bus.get_meta(name)
        if meta and getattr(meta, "is_output", False):
            self.bus.write_output(name, value, source=source)
        else:
            self.bus.set_input(name, value, source=source)
    except Exception:
        try:
            self.bus.force_signal(name, value, source=source)
        except Exception:
            pass


def _par_sensor_slider_panel(self, parent, *, key, title, signal, unit, start, end):
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    value_label = tk.Label(wrap, text=f"{int(float(self.bus.get(signal, 0)))} {unit}", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 18, "bold"))
    value_label.pack(side="right", padx=(8, 0), fill="x", expand=True)

    scale = tk.Scale(
        wrap,
        from_=end,
        to=start,
        orient="vertical",
        length=130,
        width=18,
        bg=COLORS["panel"],
        fg=COLORS["text"],
        troughcolor=COLORS["green"],
        activebackground=COLORS["green"],
        highlightthickness=0,
        relief="flat",
        showvalue=False,
        command=lambda v: (value_label.configure(text=f"{int(float(v))} {unit}"), _par_set_signal(self, signal, float(v), "PAR_SENSOR")),
    )
    scale.set(float(self.bus.get(signal, start)))
    scale.pack(side="left", padx=(0, 8), pady=4)

    tk.Label(wrap, text="SYMULACJA\nODCZYTU", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8, "bold"), justify="left").pack(side="left", anchor="s")
    self.rows[signal] = _ParValueProxy(lambda v: (scale.set(float(v)), value_label.configure(text=f"{int(float(v))} {unit}")))
    return panel


def _par_light_bh1750_panel(self, parent):
    return _par_sensor_slider_panel(self, parent, key="light_bh1750", title="CZUJNIK ŚWIATŁA BH1750", signal="par_bh1750_lux", unit="lux", start=0, end=1000)


def _par_temperature_panel(self, parent):
    return _par_sensor_slider_panel(self, parent, key="temperature", title="CZUJNIK TEMPERATURY", signal="par_temperature_c", unit="°C", start=-20, end=80)


def _par_click_sensor_panel(self, parent, *, key, title, signal, on_text, off_text, extra=None):
    panel = self.panel(key, parent, title)
    state = {"value": 1 if self.bus.get(signal) else 0}
    led = tk.Canvas(panel.body, width=92, height=92, bg=COLORS["panel"], highlightthickness=0)
    led.pack(anchor="center", pady=(2, 5))
    label = tk.Label(panel.body, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10, "bold"))
    label.pack(fill="x")

    def draw(value=None):
        if value is not None:
            state["value"] = 1 if value else 0
        led.delete("all")
        color = COLORS["red"] if state["value"] else COLORS["green"]
        glow = "#5a1613" if state["value"] else "#134d16"
        led.create_oval(5, 5, 87, 87, fill=glow, outline="")
        led.create_oval(16, 16, 76, 76, fill=color, outline="#111", width=2)
        label.configure(text=on_text if state["value"] else off_text)

    def toggle(_event=None):
        new_value = 0 if state["value"] else 1
        _par_set_signal(self, signal, new_value, "PAR_SENSOR_CLICK")
        if extra:
            for name, val_fn in extra.items():
                _par_set_signal(self, name, val_fn(new_value), "PAR_SENSOR_CLICK")
        draw(new_value)

    led.bind("<Button-1>", toggle)
    label.bind("<Button-1>", toggle)
    draw()
    self.rows[signal] = _ParValueProxy(draw)
    return panel


def _par_shock_sensor_panel(self, parent):
    return _par_click_sensor_panel(
        self,
        parent,
        key="shock_sensor_panel",
        title="CZUJNIK WSTRZĄSOWY",
        signal="par_shock_sensor_state",
        on_text="WSTRZĄS = 1",
        off_text="SPOKÓJ = 0",
        extra={"rec_p39_shock_sensor": lambda v: v},
    )


def _par_laser_panel(self, parent):
    return _par_click_sensor_panel(
        self,
        parent,
        key="laser",
        title="CZUJNIK LASEROWY — OŚ TARZANA",
        signal="par_laser_set",
        on_text="UTRACONA OŚ / LASER = 1",
        off_text="OŚ OK / LASER = 0",
        extra={
            "par_laser_error": lambda v: v,
            "par_laser_state_high": lambda v: v,
            "par_laser_state_low": lambda v: 0 if v else 1,
        },
    )


def _par_level_xyz_panel(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=160, height=130, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 8), pady=3)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)
    x_var = tk.StringVar(value="X 0")
    y_var = tk.StringVar(value="Y 0")
    z_var = tk.StringVar(value="Z 0")
    for var in (x_var, y_var, z_var):
        tk.Label(side, textvariable=var, bg=COLORS["panel"], fg=COLORS["green"], font=("Consolas", 13, "bold"), anchor="w").pack(fill="x")
    tk.Label(side, text="przeciągnij kulę\nZ suwakiem", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), justify="left").pack(anchor="w", pady=(4, 2))
    z_scale = tk.Scale(side, from_=100, to=-100, orient="vertical", length=82, showvalue=False, bg=COLORS["panel"], troughcolor=COLORS["green"], activebackground=COLORS["green"], highlightthickness=0, command=lambda v: set_values(z=float(v)))
    z_scale.pack(anchor="w")

    state = {
        "x": float(self.bus.get("par_level_x", 0)),
        "y": float(self.bus.get("par_level_y", 0)),
        "z": float(self.bus.get("par_level_z", 0)),
    }

    def clamp(v):
        return max(-100.0, min(100.0, float(v)))

    def draw():
        canvas.delete("all")
        w, h = 160, 130
        cx, cy = w / 2, h / 2
        canvas.create_line(10, cy, w - 10, cy, fill="#2f4350")
        canvas.create_line(cx, 10, cx, h - 10, fill="#2f4350")
        tilt_x = state["x"] / 100.0 * 32
        tilt_y = state["y"] / 100.0 * 24
        canvas.create_polygon(28 + tilt_x, 80 + tilt_y, 132 + tilt_x, 66 - tilt_y, 122 - tilt_x, 92 - tilt_y, 38 - tilt_x, 104 + tilt_y, fill="#13242a", outline=COLORS["blue"])
        bx = cx + state["x"] / 100.0 * 55
        by = cy - state["y"] / 100.0 * 45
        r = 10 + (state["z"] + 100) / 200.0 * 8
        canvas.create_oval(bx - r, by - r, bx + r, by + r, fill=COLORS["green"], outline="#dfffe2")
        canvas.create_text(8, 8, anchor="nw", text="+Y", fill=COLORS["muted"], font=("Segoe UI", 8, "bold"))
        canvas.create_text(w - 8, cy + 5, anchor="ne", text="+X", fill=COLORS["muted"], font=("Segoe UI", 8, "bold"))
        x_var.set(f"X {int(state['x']):+d}")
        y_var.set(f"Y {int(state['y']):+d}")
        z_var.set(f"Z {int(state['z']):+d}")

    def set_values(x=None, y=None, z=None, publish=True):
        if x is not None: state["x"] = clamp(x)
        if y is not None: state["y"] = clamp(y)
        if z is not None: state["z"] = clamp(z)
        if publish:
            _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
            _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
            _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")
        draw()

    def drag(event):
        x = (event.x - 80) / 55 * 100
        y = -(event.y - 65) / 45 * 100
        set_values(x=x, y=y)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    z_scale.set(state["z"])
    draw()
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: (z_scale.set(float(v)), set_values(z=v, publish=False)))
    return panel


def _par_lcd(self, parent):
    panel = self.panel("lcd", parent, "WYŚWIETLACZ LCD 1602 — EDYCJA")
    box = tk.Frame(panel.body, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
    box.pack(fill="x", pady=5)
    tk.Label(box, text="LCD 1602", bg="#07110a", fg=COLORS["muted"], font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=8, pady=(5, 0))
    line1 = tk.StringVar(value=str(self.bus.get("par_lcd_line1", "TARZAN PLAY"))[:16])
    line2 = tk.StringVar(value=str(self.bus.get("par_lcd_line2", "READY"))[:16])
    e1 = tk.Entry(box, textvariable=line1, bg="#0b1c10", fg="#38ff6a", insertbackground="#38ff6a", font=("Consolas", 14, "bold"), relief="flat", width=16)
    e2 = tk.Entry(box, textvariable=line2, bg="#0b1c10", fg="#38ff6a", insertbackground="#38ff6a", font=("Consolas", 14, "bold"), relief="flat", width=16)
    e1.pack(fill="x", padx=10, pady=(4, 2)); e2.pack(fill="x", padx=10, pady=(0, 8))
    def update():
        l1 = line1.get()[:16].ljust(16)
        l2 = line2.get()[:16].ljust(16)
        line1.set(l1); line2.set(l2)
        _par_set_signal(self, "par_lcd_line1", l1, "PAR_LCD")
        _par_set_signal(self, "par_lcd_line2", l2, "PAR_LCD")
        self.bus.log("LCD1602", f"UPDATE |{l1}| |{l2}|")
    tk.Button(panel.body, text="UPDATE LCD", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=update).pack(fill="x", pady=(2, 0))
    return panel


def _par_matrix(self, parent):
    panel = self.panel("matrix", parent, "MATRIX LED 8x8 — EDYCJA")
    grid = tk.Frame(panel.body, bg=COLORS["panel"])
    grid.pack(anchor="w", pady=4)
    cells = []
    state = [[0 for _ in range(8)] for _ in range(8)]
    def draw_cell(r, c):
        canvas = cells[r][c]
        canvas.delete("all")
        canvas.create_oval(2, 2, 15, 15, fill=COLORS["green"] if state[r][c] else "#123018", outline="")
    def toggle(r, c):
        state[r][c] = 0 if state[r][c] else 1
        draw_cell(r, c)
    for r in range(8):
        row = []
        for c in range(8):
            dot = tk.Canvas(grid, width=17, height=17, bg=COLORS["panel"], highlightthickness=0)
            dot.grid(row=r, column=c, padx=1, pady=1)
            dot.bind("<Button-1>", lambda _e, rr=r, cc=c: toggle(rr, cc))
            row.append(dot)
        cells.append(row)
    for r in range(8):
        for c in range(8):
            state[r][c] = 1 if (r in (1, 6) and 1 <= c <= 6) or (c in (1, 6) and 1 <= r <= 6) else 0
            draw_cell(r, c)
    def update():
        pattern = "/".join("".join("1" if state[r][c] else "0" for c in range(8)) for r in range(8))
        _par_set_signal(self, "par_matrix_pattern", pattern, "PAR_MATRIX")
        self.bus.log("MATRIX_LED", f"UPDATE {pattern}")
    tk.Button(panel.body, text="UPDATE MATRIX", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=update).pack(fill="x", pady=(5, 0))
    return panel


def _par_mass_regulator_panel(self, parent):
    panel = self.panel("mass_regulator", parent, "REGULATOR MASY")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"]); wrap.pack(fill="both", expand=True)
    value = tk.Label(wrap, text=f"{int(float(self.bus.get('par_mass_reg_value', 0)))} %", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 18, "bold"))
    value.pack(fill="x")
    scale = tk.Scale(wrap, from_=100, to=0, orient="vertical", length=115, showvalue=False, bg=COLORS["panel"], troughcolor=COLORS["green"], activebackground=COLORS["green"], highlightthickness=0)
    scale.pack(side="left", pady=4)
    def changed(v):
        v = float(v); value.configure(text=f"{int(v)} %")
        _par_set_signal(self, "par_mass_reg_value", v, "PAR_MASS")
        _par_set_signal(self, "par_mass_reg_enable", 1 if v else 0, "PAR_MASS")
        _par_set_signal(self, "play_p41_mass_reg_enable", 1 if v else 0, "PAR_MASS")
        _par_set_signal(self, "rec_p36_mass_reg_enable", 1 if v else 0, "PAR_MASS")
        _par_set_signal(self, "par_mass_reg_limit_add", 1 if v >= 100 else 0, "PAR_MASS")
        _par_set_signal(self, "par_mass_reg_limit_remove", 1 if v <= 0 else 0, "PAR_MASS")
    scale.configure(command=changed)
    scale.set(float(self.bus.get("par_mass_reg_value", 0)))
    tk.Label(wrap, text="symulacja pozycji\nregulatora masy", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), justify="left").pack(side="left", padx=8, anchor="s")
    self.rows["par_mass_reg_value"] = _ParValueProxy(lambda v: scale.set(float(v)))
    return panel


def _par_ui_panel(self, parent):
    panel = self.panel("ui", parent, "UI — PANEL PLAY/REC")
    tk.Label(panel.body, text="ZWYKŁE PRZYCISKI CHWILOWE", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
    grid = tk.Frame(panel.body, bg=COLORS["panel"]); grid.pack(fill="x")
    buttons = [("F1", "rec_p45_sw_f1", "rec_p46_led_f1"), ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"), ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"), ("F4", "rec_p51_sw_f4", "rec_p52_led_f4")]
    def press(sig): _par_set_signal(self, sig, 1, "PAR_UI_BUTTON")
    def release(sig): _par_set_signal(self, sig, 0, "PAR_UI_BUTTON")
    for i, (label, sw, led_sig) in enumerate(buttons):
        cell = tk.Frame(grid, bg=COLORS["panel"]); cell.grid(row=0, column=i, sticky="nsew", padx=4)
        btn = tk.Button(cell, text=label, bg=COLORS["button"], fg=COLORS["text"], activebackground="#31556e", activeforeground="#ffffff", relief="raised", font=("Segoe UI", 12, "bold"), height=2)
        btn.pack(fill="x")
        btn.bind("<ButtonPress-1>", lambda _e, s=sw: press(s))
        btn.bind("<ButtonRelease-1>", lambda _e, s=sw: release(s))
        led = Led(cell, size=24, bg=COLORS["panel"]); led.pack(pady=4)
        led.set(self.bus.get(led_sig) or self.bus.get(sw))
        self.rows[led_sig] = _ParValueProxy(lambda v, l=led: l.set(v))
        self.rows[sw] = _ParValueProxy(lambda v, l=led: l.set(v))
    for i in range(4): grid.grid_columnconfigure(i, weight=1)
    return panel


TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel
TarzanParPanels.temperature_panel = _par_temperature_panel
TarzanParPanels.shock_sensor_panel = _par_shock_sensor_panel
TarzanParPanels.laser_panel = _par_laser_panel
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel
TarzanParPanels.lcd = _par_lcd
TarzanParPanels.lcd_panel = _par_lcd
TarzanParPanels.matrix = _par_matrix
TarzanParPanels.matrix_panel = _par_matrix
TarzanParPanels.mass_regulator_panel = _par_mass_regulator_panel
TarzanParPanels.ui_panel = _par_ui_panel

# =====================================================================
# TARZAN PAR — KOREKTY 2026-04-30 WG LISTY UŻYTKOWNIKA
# Zakres: tylko PAR / symulator elektroniki. Bez EHR i Projektanta Układu.
# =====================================================================

def _par_sensor_slider_panel_v2(self, parent, *, key, title, signal, unit, start, end, decimals=0):
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    def fmt(v):
        try:
            fv = float(v)
        except Exception:
            fv = float(start)
        return f"{fv:.{decimals}f} {unit}" if decimals else f"{int(round(fv))} {unit}"

    value_label = tk.Label(
        wrap,
        text=fmt(self.bus.get(signal, start)),
        bg=COLORS["panel"],
        fg=COLORS["green"],
        font=("Segoe UI", 18, "bold"),
    )
    value_label.pack(side="right", padx=(8, 0), fill="x", expand=True)

    scale = tk.Scale(
        wrap,
        from_=end,
        to=start,
        orient="vertical",
        length=130,
        width=18,
        bg=COLORS["panel"],
        fg=COLORS["text"],
        troughcolor=COLORS["green"],
        activebackground=COLORS["green"],
        highlightthickness=0,
        relief="flat",
        showvalue=False,
        command=lambda v: (value_label.configure(text=fmt(v)), _par_set_signal(self, signal, float(v), "PAR_SENSOR")),
    )
    scale.set(float(self.bus.get(signal, start) or start))
    scale.pack(side="left", padx=(0, 8), pady=4)
    self.rows[signal] = _ParValueProxy(lambda v: (scale.set(float(v)), value_label.configure(text=fmt(v))))
    return panel


def _par_light_bh1750_panel_v2(self, parent):
    return _par_sensor_slider_panel_v2(
        self,
        parent,
        key="light_bh1750",
        title="CZUJNIK ŚWIATŁA BH1750",
        signal="par_bh1750_lux",
        unit="lx",
        start=0,
        end=1000,
        decimals=0,
    )


def _par_temperature_panel_v2(self, parent):
    return _par_sensor_slider_panel_v2(
        self,
        parent,
        key="temperature",
        title="TEMPERATURA POWIETRZA",
        signal="par_temperature_c",
        unit="°C",
        start=0,
        end=50,
        decimals=1,
    )


def _par_level_xyz_panel_v2(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=178, height=142, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 8), pady=3)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    x_var = tk.StringVar(value="X +0")
    y_var = tk.StringVar(value="Y +0")
    z_var = tk.StringVar(value="Z +0")
    for var in (x_var, y_var, z_var):
        tk.Label(side, textvariable=var, bg=COLORS["panel"], fg=COLORS["green"], font=("Consolas", 13, "bold"), anchor="w").pack(fill="x")

    tk.Label(side, text="Z", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8, "bold"), anchor="w").pack(anchor="w", pady=(4, 0))
    z_scale = tk.Scale(
        side,
        from_=100,
        to=-100,
        orient="vertical",
        length=82,
        width=16,
        showvalue=False,
        bg=COLORS["panel"],
        troughcolor=COLORS["green"],
        activebackground=COLORS["green"],
        highlightthickness=0,
        command=lambda v: set_values(z=float(v)),
    )
    z_scale.pack(anchor="w")

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 0) or 0),
    }

    def clamp(v):
        return max(-100.0, min(100.0, float(v)))

    def draw():
        canvas.delete("all")
        w, h = 178, 142
        cx, cy = w / 2, h / 2
        canvas.create_line(12, cy, w - 12, cy, fill="#2f4350")
        canvas.create_line(cx, 12, cx, h - 12, fill="#2f4350")
        canvas.create_text(w - 8, cy + 8, anchor="ne", text="+X", fill=COLORS["muted"], font=("Segoe UI", 8, "bold"))
        canvas.create_text(8, 8, anchor="nw", text="+Y", fill=COLORS["muted"], font=("Segoe UI", 8, "bold"))
        canvas.create_text(w - 8, h - 8, anchor="se", text="Z: rozmiar kuli", fill=COLORS["muted"], font=("Segoe UI", 7))

        # Płaszczyzna czujnika — odchyla się po X/Y.
        tx = state["x"] / 100.0 * 34
        ty = state["y"] / 100.0 * 25
        canvas.create_polygon(
            30 + tx, 84 + ty,
            148 + tx, 68 - ty,
            134 - tx, 98 - ty,
            44 - tx, 112 + ty,
            fill="#13242a",
            outline=COLORS["blue"],
            width=2,
        )

        bx = cx + state["x"] / 100.0 * 62
        by = cy - state["y"] / 100.0 * 50
        r = 8 + (state["z"] + 100.0) / 200.0 * 16
        shade = "#7dff85" if state["z"] >= 0 else "#24e22d"
        canvas.create_oval(bx - r, by - r, bx + r, by + r, fill=shade, outline="#dfffe2", width=2)
        canvas.create_text(bx, by, text="Z", fill="#062008", font=("Segoe UI", 8, "bold"))

        x_var.set(f"X {int(round(state['x'])):+d}")
        y_var.set(f"Y {int(round(state['y'])):+d}")
        z_var.set(f"Z {int(round(state['z'])):+d}")

    def set_values(x=None, y=None, z=None, publish=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        if publish:
            _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
            _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
            _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")
        draw()

    def drag(event):
        set_values(x=(event.x - 89) / 62 * 100, y=-(event.y - 71) / 50 * 100)

    def wheel(event):
        delta = 10 if getattr(event, "delta", 0) > 0 else -10
        z_scale.set(clamp(state["z"] + delta))

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    canvas.bind("<MouseWheel>", wheel)
    z_scale.set(state["z"])
    draw()
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: (z_scale.set(float(v)), set_values(z=v, publish=False)))
    return panel


def _par_lcd_v2(self, parent):
    panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602 — EDYCJA")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="x")

    def lcd_box(title, sig1, sig2, default1, default2):
        box = tk.Frame(wrap, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
        box.pack(fill="x", pady=5)
        tk.Label(box, text=title, bg="#07110a", fg=COLORS["muted"], font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=8, pady=(5, 0))
        line1 = tk.StringVar(value=str(self.bus.get(sig1, default1))[:16])
        line2 = tk.StringVar(value=str(self.bus.get(sig2, default2))[:16])
        e1 = tk.Entry(box, textvariable=line1, bg="#0b1c10", fg="#38ff6a", insertbackground="#38ff6a", font=("Consolas", 14, "bold"), relief="flat", width=16)
        e2 = tk.Entry(box, textvariable=line2, bg="#0b1c10", fg="#38ff6a", insertbackground="#38ff6a", font=("Consolas", 14, "bold"), relief="flat", width=16)
        e1.pack(fill="x", padx=10, pady=(4, 2))
        e2.pack(fill="x", padx=10, pady=(0, 8))
        def update():
            l1 = line1.get()[:16].ljust(16)
            l2 = line2.get()[:16].ljust(16)
            line1.set(l1)
            line2.set(l2)
            _par_set_signal(self, sig1, l1, "PAR_LCD")
            _par_set_signal(self, sig2, l2, "PAR_LCD")
            # Kompatybilność ze starszym pojedynczym LCD.
            if title.upper().startswith("PLAY"):
                _par_set_signal(self, "par_lcd_line1", l1, "PAR_LCD")
                _par_set_signal(self, "par_lcd_line2", l2, "PAR_LCD")
            self.bus.log("LCD1602", f"{title} UPDATE |{l1}| |{l2}|")
        tk.Button(box, text=f"UPDATE {title}", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=update).pack(fill="x", padx=10, pady=(0, 8))

    lcd_box("PLAY LCD 1602", "par_lcd_play_line1", "par_lcd_play_line2", "TARZAN PLAY", "READY")
    lcd_box("REC LCD 1602", "par_lcd_rec_line1", "par_lcd_rec_line2", "TARZAN REC", "READY")
    return panel


def _par_mass_regulator_panel_v2(self, parent):
    panel = self.panel("mass_regulator", parent, "REGULATOR MASY")
    state = {"mode": "OFF"}

    def set_mode(mode):
        state["mode"] = mode
        add = 1 if mode == "ADD" else 0
        rem = 1 if mode == "REMOVE" else 0
        en = 1 if mode in {"ADD", "REMOVE"} else 0
        # Realne sygnały z mapy + wirtualne wskaźniki PAR są zespolone.
        for sig, val in [
            ("play_p41_mass_reg_enable", en),
            ("rec_p36_mass_reg_enable", en),
            ("play_p13_mass_reg_limit_add", add),
            ("play_p23_mass_reg_limit_remove", rem),
            ("par_mass_reg_enable", en),
            ("par_mass_reg_limit_add", add),
            ("par_mass_reg_limit_remove", rem),
        ]:
            _par_set_signal(self, sig, val, "PAR_MASS_3STATE")
        refresh()

    btns = tk.Frame(panel.body, bg=COLORS["panel"])
    btns.pack(fill="x", pady=(0, 8))
    for txt, mode in [("STOP", "OFF"), ("DODAJ", "ADD"), ("ODEJMIJ", "REMOVE")]:
        tk.Button(btns, text=txt, bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"), command=lambda m=mode: set_mode(m)).pack(side="left", fill="x", expand=True, padx=3)

    leds = {}
    def led_row(label, sig):
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"], anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", fill="x", expand=True)
        led = Led(row, size=24, bg=COLORS["panel"])
        led.pack(side="right")
        leds[sig] = led
        self.rows[sig] = _ParValueProxy(lambda v, l=led: l.set(v))
        led.set(self.bus.get(sig))

    led_row("PLAY EN", "play_p41_mass_reg_enable")
    led_row("REC EN", "rec_p36_mass_reg_enable")
    led_row("KRAŃCÓWKA DODANE", "play_p13_mass_reg_limit_add")
    led_row("KRAŃCÓWKA ODJĘTE", "play_p23_mass_reg_limit_remove")

    def refresh():
        for sig, led in leds.items():
            led.set(self.bus.get(sig))

    refresh()
    return panel


def _par_ui_panel_v2(self, parent):
    panel = self.panel("ui", parent, "UI — PANEL PLAY/REC")
    buttons = [
        ("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
        ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
        ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
        ("F4", "rec_p51_sw_f4", "rec_p52_led_f4"),
    ]
    for label, sw_sig, led_sig in buttons:
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=5)
        tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"], width=4, font=("Segoe UI", 15, "bold")).pack(side="left")
        btn = tk.Button(row, text="", width=7, bg=COLORS["button"], activebackground="#31556e", relief="raised")
        btn.pack(side="left", padx=16)
        btn.bind("<ButtonPress-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 1, "PAR_UI_BUTTON"))
        btn.bind("<ButtonRelease-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 0, "PAR_UI_BUTTON"))
        tk.Label(row, text="LED", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8, "bold")).pack(side="left")
        led = Led(row, size=28, bg=COLORS["panel"])
        led.pack(side="right", padx=6)
        led.set(self.bus.get(led_sig))
        self.rows[led_sig] = _ParValueProxy(lambda v, l=led: l.set(v))
    return panel

# Finalne przypięcie korekt.
TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v2
TarzanParPanels.temperature_panel = _par_temperature_panel_v2
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v2
TarzanParPanels.lcd = _par_lcd_v2
TarzanParPanels.lcd_panel = _par_lcd_v2
TarzanParPanels.mass_regulator_panel = _par_mass_regulator_panel_v2
TarzanParPanels.ui_panel = _par_ui_panel_v2

# =====================================================================
# TARZAN PAR — KOREKTY v3 wg uwag użytkownika
# Zakres: tylko PAR / panele symulatora. Bez EHR i Projektanta Układu.
# =====================================================================

def _par_light_bh1750_panel_v3(self, parent):
    # Zakres praktyczny dla BH1750: noc -> pełne słońce.
    return _par_sensor_slider_panel_v2(
        self,
        parent,
        key="light_bh1750",
        title="CZUJNIK ŚWIATŁA BH1750",
        signal="par_bh1750_lux",
        unit="lx",
        start=0,
        end=120000,
        decimals=0,
    )


def _par_temperature_panel_v3(self, parent):
    return _par_sensor_slider_panel_v2(
        self,
        parent,
        key="temperature",
        title="TEMPERATURA POWIETRZA",
        signal="par_temperature_c",
        unit="°C",
        start=0,
        end=50,
        decimals=1,
    )


def _par_matrix_v3(self, parent):
    panel = self.panel("matrix", parent, "MATRIX LED 8x8 — EDYCJA")
    holder = tk.Frame(panel.body, bg=COLORS["panel"])
    holder.pack(fill="both", expand=True)
    grid = tk.Frame(holder, bg=COLORS["panel"])
    grid.pack(anchor="center", pady=4)
    cells = []
    state = [[0 for _ in range(8)] for _ in range(8)]

    def draw_cell(r, c):
        canvas = cells[r][c]
        canvas.delete("all")
        canvas.create_oval(2, 2, 15, 15, fill=COLORS["green"] if state[r][c] else "#123018", outline="")

    def toggle(r, c):
        state[r][c] = 0 if state[r][c] else 1
        draw_cell(r, c)

    for r in range(8):
        row = []
        for c in range(8):
            dot = tk.Canvas(grid, width=17, height=17, bg=COLORS["panel"], highlightthickness=0)
            dot.grid(row=r, column=c, padx=1, pady=1)
            dot.bind("<Button-1>", lambda _e, rr=r, cc=c: toggle(rr, cc))
            row.append(dot)
        cells.append(row)

    for r in range(8):
        for c in range(8):
            state[r][c] = 1 if (r in (1, 6) and 1 <= c <= 6) or (c in (1, 6) and 1 <= r <= 6) else 0
            draw_cell(r, c)

    def update():
        pattern = "/".join("".join("1" if state[r][c] else "0" for c in range(8)) for r in range(8))
        _par_set_signal(self, "par_matrix_pattern", pattern, "PAR_MATRIX")
        self.bus.log("MATRIX_LED", f"UPDATE {pattern}")

    tk.Button(holder, text="UPDATE MATRIX", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=update).pack(fill="x", pady=(5, 0))
    return panel


def _par_lcd_v3(self, parent):
    panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602 — EDYCJA")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="x")

    def lcd_box(title, sig1, sig2, default1, default2):
        box = tk.Frame(wrap, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
        box.pack(fill="x", pady=4)
        tk.Label(box, text=title, bg="#07110a", fg=COLORS["muted"], font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=7, pady=(4, 0))
        row = tk.Frame(box, bg="#07110a")
        row.pack(fill="x", padx=7, pady=(3, 6))
        display = tk.Frame(row, bg="#07110a")
        display.pack(side="left", fill="both", expand=True)
        line1 = tk.StringVar(value=str(self.bus.get(sig1, default1))[:16])
        line2 = tk.StringVar(value=str(self.bus.get(sig2, default2))[:16])
        e1 = tk.Entry(display, textvariable=line1, bg="#0b1c10", fg="#38ff6a", insertbackground="#38ff6a", font=("Consolas", 12, "bold"), relief="flat", width=16)
        e2 = tk.Entry(display, textvariable=line2, bg="#0b1c10", fg="#38ff6a", insertbackground="#38ff6a", font=("Consolas", 12, "bold"), relief="flat", width=16)
        e1.pack(fill="x", pady=(0, 2))
        e2.pack(fill="x")

        def send():
            l1 = line1.get()[:16].ljust(16)
            l2 = line2.get()[:16].ljust(16)
            line1.set(l1)
            line2.set(l2)
            _par_set_signal(self, sig1, l1, "PAR_LCD")
            _par_set_signal(self, sig2, l2, "PAR_LCD")
            if title.upper().startswith("PLAY"):
                _par_set_signal(self, "par_lcd_line1", l1, "PAR_LCD")
                _par_set_signal(self, "par_lcd_line2", l2, "PAR_LCD")
            self.bus.log("LCD1602", f"{title} SEND |{l1}| |{l2}|")

        tk.Button(row, text="SEND", bg=COLORS["green"], fg="#061006", activebackground="#43ff4e", relief="raised", font=("Segoe UI", 8, "bold"), width=5, command=send).pack(side="right", padx=(6, 0), fill="y")

    lcd_box("PLAY LCD 1602", "par_lcd_play_line1", "par_lcd_play_line2", "TARZAN PLAY", "READY")
    lcd_box("REC LCD 1602", "par_lcd_rec_line1", "par_lcd_rec_line2", "TARZAN REC", "READY")
    return panel


def _par_level_xyz_panel_v3(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=178, height=142, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 8), pady=3)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    x_var = tk.StringVar(value="X +0")
    y_var = tk.StringVar(value="Y +0")
    z_var = tk.StringVar(value="Z +0")
    for var in (x_var, y_var, z_var):
        tk.Label(side, textvariable=var, bg=COLORS["panel"], fg=COLORS["green"], font=("Consolas", 13, "bold"), anchor="w").pack(fill="x")

    z_scale = tk.Scale(side, from_=100, to=-100, orient="vertical", length=82, width=16, showvalue=False, bg=COLORS["panel"], troughcolor=COLORS["green"], activebackground=COLORS["green"], highlightthickness=0)
    z_scale.pack(anchor="w", pady=(4, 0))

    state = {"x": float(self.bus.get("par_level_x", 0) or 0), "y": float(self.bus.get("par_level_y", 0) or 0), "z": float(self.bus.get("par_level_z", 0) or 0)}

    def clamp(v):
        return max(-100.0, min(100.0, float(v)))

    def draw():
        canvas.delete("all")
        w, h = 178, 142
        cx, cy = w / 2, h / 2
        canvas.create_line(12, cy, w - 12, cy, fill="#2f4350")
        canvas.create_line(cx, 12, cx, h - 12, fill="#2f4350")
        canvas.create_text(w - 8, cy + 8, anchor="ne", text="+X", fill=COLORS["muted"], font=("Segoe UI", 8, "bold"))
        canvas.create_text(8, 8, anchor="nw", text="+Y", fill=COLORS["muted"], font=("Segoe UI", 8, "bold"))
        tx = state["x"] / 100.0 * 34
        ty = state["y"] / 100.0 * 25
        canvas.create_polygon(30 + tx, 84 + ty, 148 + tx, 68 - ty, 134 - tx, 98 - ty, 44 - tx, 112 + ty, fill="#13242a", outline=COLORS["blue"], width=2)
        bx = cx + state["x"] / 100.0 * 62
        by = cy - state["y"] / 100.0 * 50
        r = 8 + (state["z"] + 100.0) / 200.0 * 16
        shade = "#7dff85" if state["z"] >= 0 else "#24e22d"
        canvas.create_oval(bx - r, by - r, bx + r, by + r, fill=shade, outline="#dfffe2", width=2)
        x_var.set(f"X {int(round(state['x'])):+d}")
        y_var.set(f"Y {int(round(state['y'])):+d}")
        z_var.set(f"Z {int(round(state['z'])):+d}")

    def set_values(x=None, y=None, z=None, publish=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        if publish:
            _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
            _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
            _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")
        draw()

    z_scale.configure(command=lambda v: set_values(z=float(v)))

    def drag(event):
        set_values(x=(event.x - 89) / 62 * 100, y=-(event.y - 71) / 50 * 100)

    def wheel(event):
        delta = 10 if getattr(event, "delta", 0) > 0 else -10
        new_z = clamp(state["z"] + delta)
        z_scale.set(new_z)
        set_values(z=new_z)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    canvas.bind("<MouseWheel>", wheel)
    z_scale.set(state["z"])
    draw()
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: (z_scale.set(float(v)), set_values(z=v, publish=False)))
    return panel


def _par_keyboard_v3(self, parent):
    panel = self.panel("keyboard", parent, "KLAWIATURA")
    grid = tk.Frame(panel.body, bg=COLORS["panel"])
    grid.pack(anchor="center")
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for i, label in enumerate(keys):
        tk.Button(grid, text=label, bg="#202b33", fg=COLORS["text"], relief="flat", font=("Segoe UI", 12, "bold"), width=3, height=1, command=lambda k=label: self._log("KEYBOARD", f"KEY {k}")).grid(row=i // 3, column=i % 3, sticky="nsew", padx=3, pady=3)
    for i in range(3):
        grid.grid_columnconfigure(i, weight=1)
    return panel


TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v3
TarzanParPanels.temperature_panel = _par_temperature_panel_v3
TarzanParPanels.matrix = _par_matrix_v3
TarzanParPanels.matrix_panel = _par_matrix_v3
TarzanParPanels.lcd = _par_lcd_v3
TarzanParPanels.lcd_panel = _par_lcd_v3
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v3
TarzanParPanels.keyboard = _par_keyboard_v3
TarzanParPanels.keyboard_panel = _par_keyboard_v3


# =====================================================================
# TARZAN PAR — KOREKTY v4 wg uwag użytkownika
# Zakres: tylko PAR / panele symulatora. Bez EHR i Projektanta Układu.
# =====================================================================

def _par_matrix_v4(self, parent):
    panel = self.panel("matrix", parent, "MATRIX LED 8x8 — EDYCJA")
    holder = tk.Frame(panel.body, bg=COLORS["panel"])
    holder.pack(fill="both", expand=True)
    holder.grid_rowconfigure(0, weight=1)
    holder.grid_columnconfigure(0, weight=1)

    center = tk.Frame(holder, bg=COLORS["panel"])
    center.grid(row=0, column=0, sticky="nsew")
    center.grid_rowconfigure(0, weight=1)
    center.grid_columnconfigure(0, weight=1)

    grid = tk.Frame(center, bg=COLORS["panel"])
    grid.grid(row=0, column=0, sticky="")
    cells = []
    state = [[0 for _ in range(8)] for _ in range(8)]

    def draw_cell(r, c):
        canvas = cells[r][c]
        canvas.delete("all")
        canvas.create_oval(2, 2, 12, 12, fill=COLORS["green"] if state[r][c] else "#123018", outline="")

    def toggle(r, c):
        state[r][c] = 0 if state[r][c] else 1
        draw_cell(r, c)

    for r in range(8):
        row = []
        for c in range(8):
            dot = tk.Canvas(grid, width=14, height=14, bg=COLORS["panel"], highlightthickness=0)
            dot.grid(row=r, column=c, padx=1, pady=1)
            dot.bind("<Button-1>", lambda _e, rr=r, cc=c: toggle(rr, cc))
            row.append(dot)
        cells.append(row)

    for r in range(8):
        for c in range(8):
            state[r][c] = 1 if (r in (1, 6) and 1 <= c <= 6) or (c in (1, 6) and 1 <= r <= 6) else 0
            draw_cell(r, c)

    def update():
        pattern = "/".join("".join("1" if state[r][c] else "0" for c in range(8)) for r in range(8))
        _par_set_signal(self, "par_matrix_pattern", pattern, "PAR_MATRIX")
        self.bus.log("MATRIX_LED", f"UPDATE {pattern}")

    tk.Button(holder, text="UPDATE MATRIX", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=update).grid(row=1, column=0, sticky="ew", pady=(4, 0))
    return panel


def _par_mass_regulator_panel_v4(self, parent):
    panel = self.panel("mass_regulator", parent, "REGULATOR MASY")
    state = {"mode": "OFF"}

    def set_mode(mode):
        state["mode"] = mode
        add = 1 if mode == "ADD" else 0
        rem = 1 if mode == "REMOVE" else 0
        en = 1 if mode in {"ADD", "REMOVE"} else 0

        # Realne sygnały regulatora masy z mapy + wirtualne sygnały PAR są zespolone.
        for sig, val in [
            ("play_p41_mass_reg_enable", en),
            ("rec_p36_mass_reg_enable", en),
            ("play_p13_mass_reg_limit_add", add),
            ("play_p23_mass_reg_limit_remove", rem),
            ("par_mass_reg_enable", en),
            ("par_mass_reg_limit_add", add),
            ("par_mass_reg_limit_remove", rem),
        ]:
            _par_set_signal(self, sig, val, "PAR_MASS_3STATE")
        refresh()

    btns = tk.Frame(panel.body, bg=COLORS["panel"])
    btns.pack(fill="x", pady=(0, 6))

    add_btn = tk.Button(btns, text="DODAJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 9, "bold"), command=lambda: set_mode("ADD"))
    rem_btn = tk.Button(btns, text="UJMIJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 9, "bold"), command=lambda: set_mode("REMOVE"))
    add_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))
    rem_btn.pack(side="left", fill="x", expand=True, padx=(3, 0))

    status = tk.Label(panel.body, text="STAN: SPOCZYNEK", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold"))
    status.pack(fill="x", pady=(1, 4))

    leds = {}
    def led_row(label, sig):
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"], anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", fill="x", expand=True)
        led = Led(row, size=20, bg=COLORS["panel"])
        led.pack(side="right")
        leds[sig] = led
        self.rows[sig] = _ParValueProxy(lambda v, l=led: l.set(v))
        led.set(self.bus.get(sig))

    led_row("MASA DODANA", "play_p13_mass_reg_limit_add")
    led_row("MASA UJĘTA", "play_p23_mass_reg_limit_remove")

    def refresh():
        for sig, led in leds.items():
            led.set(self.bus.get(sig))
        if state["mode"] == "ADD":
            status.configure(text="STAN: DODAJĘ MASY", fg=COLORS["green"])
        elif state["mode"] == "REMOVE":
            status.configure(text="STAN: UJMUJĘ MASY", fg=COLORS["amber"])
        else:
            status.configure(text="STAN: SPOCZYNEK", fg=COLORS["muted"])

    refresh()
    return panel


def _par_level_xyz_panel_v4(self, parent):
    # MMA7660FC to akcelerometr 3-osiowy. X/Y pokazują przechył w płaszczyźnie,
    # a Z wynika z ustawienia tej płaszczyzny względem grawitacji, więc nie ma osobnego suwaka.
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=145, height=108, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 6), pady=2)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    x_var = tk.StringVar(value="X +0")
    y_var = tk.StringVar(value="Y +0")
    z_var = tk.StringVar(value="Z +100")
    for var in (x_var, y_var, z_var):
        tk.Label(side, textvariable=var, bg=COLORS["panel"], fg=COLORS["green"], font=("Consolas", 11, "bold"), anchor="w").pack(fill="x")

    state = {"x": float(self.bus.get("par_level_x", 0) or 0), "y": float(self.bus.get("par_level_y", 0) or 0), "z": float(self.bus.get("par_level_z", 100) or 100)}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def calc_z(x, y):
        import math
        # Prosty model statyczny: całkowity wektor g ma długość 100.
        # Z maleje, gdy płaszczyzna jest mocno pochylona w X/Y.
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def draw():
        canvas.delete("all")
        w, h = 145, 108
        cx, cy = w / 2, h / 2
        x = clamp(state["x"])
        y = clamp(state["y"])
        z = clamp(state["z"])

        # Płaszczyzna i osie X/Y.
        canvas.create_line(12, cy, w - 12, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 10, cx, h - 10, fill="#31414a", width=1)
        canvas.create_polygon(26 + x * 0.12, 28 - y * 0.12, w - 26 + x * 0.12, 34 + y * 0.12, w - 30 - x * 0.12, h - 28 + y * 0.12, 30 - x * 0.12, h - 34 - y * 0.12, fill="#0d222c", outline="#386271")
        px = cx + x / 100.0 * 46
        py = cy - y / 100.0 * 34
        size = 7 + max(0, z) / 100.0 * 3
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        canvas.create_text(12, 10, text="XY", fill=COLORS["muted"], anchor="w", font=("Segoe UI", 7, "bold"))

        x_var.set(f"X {int(round(x)):+d}")
        y_var.set(f"Y {int(round(y)):+d}")
        z_var.set(f"Z {int(round(z)):+d}")

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def set_values(x=None, y=None, publish_signals=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        state["z"] = calc_z(state["x"], state["y"])
        if publish_signals:
            publish()
        draw()

    def drag(event):
        set_values(x=(event.x - 72.5) / 46 * 100, y=-(event.y - 54) / 34 * 100)

    def zero():
        set_values(x=0, y=0)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    tk.Button(side, text="ZERUJ", bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 8, "bold"), command=zero).pack(fill="x", pady=(3, 0))

    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: (state.__setitem__("z", clamp(v)), draw()))
    return panel


TarzanParPanels.matrix = _par_matrix_v4
TarzanParPanels.matrix_panel = _par_matrix_v4
TarzanParPanels.mass_regulator_panel = _par_mass_regulator_panel_v4
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v4

# =====================================================================
# TARZAN PAR — KOREKTY v5 wg uwag użytkownika
# Zakres: tylko PAR / panele symulatora. Bez EHR i Projektanta Układu.
# =====================================================================

_PAR_BURGUNDY = "#7a1630"


def _par_sensor_slider_panel_v5(self, parent, *, key, title, signal, unit, start, end):
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    value_label = tk.Label(
        wrap,
        text=f"{int(float(self.bus.get(signal, start) or start))} {unit}",
        bg=COLORS["panel"],
        fg=COLORS["green"],
        font=("Segoe UI", 18, "bold"),
    )
    value_label.pack(side="right", padx=(7, 0), fill="x", expand=True)

    scale = tk.Scale(
        wrap,
        from_=end,
        to=start,
        orient="vertical",
        length=118,
        width=18,
        bg=COLORS["panel"],
        fg=COLORS["text"],
        troughcolor=_PAR_BURGUNDY,
        activebackground=_PAR_BURGUNDY,
        highlightthickness=0,
        relief="flat",
        showvalue=False,
        command=lambda v: (
            value_label.configure(text=f"{int(float(v))} {unit}"),
            _par_set_signal(self, signal, float(v), "PAR_SENSOR"),
        ),
    )
    scale.set(float(self.bus.get(signal, start) or start))
    scale.pack(side="left", padx=(0, 8), pady=3)

    self.rows[signal] = _ParValueProxy(
        lambda v: (scale.set(float(v)), value_label.configure(text=f"{int(float(v))} {unit}"))
    )
    return panel


def _par_light_bh1750_panel_v5(self, parent):
    # Zakres ustawiony pod realną symulację nocy / pomieszczenia / światła słonecznego.
    return _par_sensor_slider_panel_v5(
        self,
        parent,
        key="light_bh1750",
        title="CZUJNIK ŚWIATŁA BH1750",
        signal="par_bh1750_lux",
        unit="lux",
        start=0,
        end=120000,
    )


def _par_temperature_panel_v5(self, parent):
    # Temperatura powietrza, bez zakresów technicznych czujnika.
    return _par_sensor_slider_panel_v5(
        self,
        parent,
        key="temperature",
        title="CZUJNIK TEMPERATURY POWIETRZA",
        signal="par_temperature_c",
        unit="°C",
        start=-20,
        end=50,
    )


def _par_limits_v5(self, parent):
    panel = self.panel("limits", parent, "KRAŃCÓWKI")
    inner = self._scroll_body(panel)
    names = self._group_or_search("KRAŃCÓWKI", ["limit"])
    for name in names:
        row = tk.Frame(inner, bg=COLORS["panel"])
        row.pack(fill="x", pady=1)
        tk.Label(
            row,
            text=self.limit_label(name),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            anchor="w",
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 5))
        led = Led(row, size=18, bg=COLORS["panel"])
        led.pack(side="left", padx=(0, 4))
        led.set(self.bus.get(name))
        self.rows[name] = _ParValueProxy(lambda v, l=led: l.set(v))
        row.bind("<Button-1>", lambda _e, n=name: self.bus.toggle_input(n, source="PAR_LIMIT"))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda _e, n=name: self.bus.toggle_input(n, source="PAR_LIMIT"))
    if not names:
        tk.Label(inner, text="Brak krańcówek w mapie sygnałów.", bg=COLORS["panel"], fg=COLORS["red"]).pack(anchor="w")
    return panel


def _par_ui_panel_v5(self, parent):
    panel = self.panel("ui", parent, "PANEL PLAY/REC")
    buttons = [
        ("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
        ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
        ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
        ("F4", "rec_p51_sw_f4", "rec_p52_led_f4"),
    ]
    for label, sw_sig, led_sig in buttons:
        row = tk.Frame(panel.body, bg=COLORS["panel"])
        row.pack(fill="x", pady=3)
        tk.Label(
            row,
            text=label,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            width=3,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left", padx=(0, 4))
        btn = tk.Button(
            row,
            text="",
            width=5,
            height=1,
            bg=COLORS["button"],
            activebackground="#31556e",
            relief="raised",
        )
        btn.pack(side="left", padx=(0, 6))
        btn.bind("<ButtonPress-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 1, "PAR_UI_BUTTON"))
        btn.bind("<ButtonRelease-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 0, "PAR_UI_BUTTON"))
        led = Led(row, size=20, bg=COLORS["panel"])
        led.pack(side="left", padx=(0, 2))
        led.set(self.bus.get(led_sig))
        self.rows[led_sig] = _ParValueProxy(lambda v, l=led: l.set(v))
    return panel


def _par_level_xyz_panel_v5(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=112, height=82, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 6), pady=1)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 100) or 100),
    }
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def calc_z(x, y):
        import math
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def draw():
        canvas.delete("all")
        w, h = 112, 82
        cx, cy = w / 2, h / 2
        x = clamp(state["x"])
        y = clamp(state["y"])
        z = clamp(state["z"])

        canvas.create_line(9, cy, w - 9, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 8, cx, h - 8, fill="#31414a", width=1)
        canvas.create_polygon(
            25 + x * 0.07,
            24 - y * 0.07,
            w - 25 + x * 0.07,
            27 + y * 0.07,
            w - 28 - x * 0.07,
            h - 24 + y * 0.07,
            28 - x * 0.07,
            h - 27 - y * 0.07,
            fill="#0d222c",
            outline="#386271",
        )
        px = cx + x / 100.0 * 34
        py = cy - y / 100.0 * 25
        size = 5 + max(0, z) / 100.0 * 2
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        canvas.create_text(8, 7, text="XY", fill=COLORS["muted"], anchor="w", font=("Segoe UI", 7, "bold"))

        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_values(x=None, y=None, z=None, publish_signals=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        else:
            state["z"] = calc_z(state["x"], state["y"])
        if publish_signals:
            publish()
        draw()

    def nudge(axis, delta):
        key = axis.lower()
        if axis == "Z":
            set_values(z=state["z"] + delta)
        else:
            set_values(**{key: state[key] + delta})

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=1)
        tk.Label(
            row,
            textvariable=vars_by_axis[axis],
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Consolas", 10, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="−", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda a=axis: nudge(a, -1)).pack(side="right", padx=(1, 0))
        tk.Button(row, text="+", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda a=axis: nudge(a, 1)).pack(side="right", padx=(1, 0))

    def drag(event):
        set_values(x=(event.x - 56) / 34 * 100, y=-(event.y - 41) / 25 * 100)

    def zero():
        set_values(x=0, y=0)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    tk.Button(side, text="ZERUJ", bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 8, "bold"), command=zero).pack(fill="x", pady=(3, 0))

    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_values(z=v, publish_signals=False))
    return panel


TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v5
TarzanParPanels.temperature_panel = _par_temperature_panel_v5
TarzanParPanels.limits = _par_limits_v5
TarzanParPanels.ui_panel = _par_ui_panel_v5
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v5


# =====================================================================
# TARZAN PAR — KOREKTY v6 wg uwag użytkownika
# Zakres: tylko PAR / panele symulatora. Bez EHR i Projektanta Układu.
# =====================================================================

def _par_sensor_slider_panel_v6(self, parent, *, key, title, signal, unit, start, end):
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    def fmt(v):
        try:
            return f"{int(round(float(v)))} {unit}"
        except Exception:
            return f"{int(start)} {unit}"

    value_label = tk.Label(
        wrap,
        text=fmt(self.bus.get(signal, start)),
        bg=COLORS["panel"],
        fg=COLORS["green"],
        font=("Segoe UI", 18, "bold"),
    )
    value_label.pack(side="right", padx=(7, 0), fill="x", expand=True)

    # Tło/trough zostaje zielone; bordo służy jako kolor aktywnego uchwytu suwaka.
    scale = tk.Scale(
        wrap,
        from_=end,
        to=start,
        orient="vertical",
        length=118,
        width=18,
        bg=COLORS["panel"],
        fg=COLORS["text"],
        troughcolor=COLORS["green"],
        activebackground=_PAR_BURGUNDY,
        highlightthickness=0,
        relief="flat",
        sliderrelief="raised",
        showvalue=False,
        command=lambda v: (
            value_label.configure(text=fmt(v)),
            _par_set_signal(self, signal, float(v), "PAR_SENSOR"),
        ),
    )
    scale.set(float(self.bus.get(signal, start) or start))
    scale.pack(side="left", padx=(0, 8), pady=3)

    self.rows[signal] = _ParValueProxy(
        lambda v: (scale.set(float(v)), value_label.configure(text=fmt(v)))
    )
    return panel


def _par_light_bh1750_panel_v6(self, parent):
    return _par_sensor_slider_panel_v6(
        self,
        parent,
        key="light_bh1750",
        title="CZUJNIK ŚWIATŁA BH1750",
        signal="par_bh1750_lux",
        unit="lux",
        start=0,
        end=120000,
    )


def _par_temperature_panel_v6(self, parent):
    return _par_sensor_slider_panel_v6(
        self,
        parent,
        key="temperature",
        title="CZUJNIK TEMPERATURY POWIETRZA",
        signal="par_temperature_c",
        unit="°C",
        start=-20,
        end=50,
    )


def _par_limits_v6(self, parent):
    panel = self.panel("limits", parent, "KRAŃCÓWKI")
    body = tk.Frame(panel.body, bg=COLORS["panel"])
    body.pack(fill="both", expand=True)
    names = self._group_or_search("KRAŃCÓWKI", ["limit"])
    if not names:
        tk.Label(body, text="Brak krańcówek w mapie sygnałów.", bg=COLORS["panel"], fg=COLORS["red"]).pack(anchor="w")
        return panel

    cols = 3
    for col in range(cols):
        body.grid_columnconfigure(col, weight=1, uniform="limit_col")

    for i, name in enumerate(names):
        r = i // cols
        c = i % cols
        cell = tk.Frame(body, bg=COLORS["panel"])
        cell.grid(row=r, column=c, sticky="ew", padx=3, pady=1)
        cell.grid_columnconfigure(0, weight=1)

        label = tk.Label(
            cell,
            text=self.limit_label(name),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            anchor="w",
            font=("Segoe UI", 8),
        )
        label.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        led = Led(cell, size=17, bg=COLORS["panel"])
        led.grid(row=0, column=1, sticky="e", padx=(2, 0))
        led.set(self.bus.get(name))
        self.rows[name] = _ParValueProxy(lambda v, l=led: l.set(v))

        def click(_event=None, n=name):
            self.bus.toggle_input(n, source="PAR_LIMIT")

        cell.bind("<Button-1>", click)
        label.bind("<Button-1>", click)
        led.bind("<Button-1>", click)

    return panel


def _par_ui_panel_v6(self, parent):
    panel = self.panel("ui", parent, "PANEL PLAY/REC")
    buttons = [
        ("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
        ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
        ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
        ("F4", "rec_p51_sw_f4", "rec_p52_led_f4"),
    ]
    grid = tk.Frame(panel.body, bg=COLORS["panel"])
    grid.pack(fill="x")
    for col in range(2):
        grid.grid_columnconfigure(col, weight=1, uniform="playrec_col")

    for i, (label_text, sw_sig, led_sig) in enumerate(buttons):
        cell = tk.Frame(grid, bg=COLORS["panel"])
        cell.grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=3)
        cell.grid_columnconfigure(1, weight=1)

        tk.Label(
            cell,
            text=label_text,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            width=2,
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 3))

        btn = tk.Button(
            cell,
            text="",
            width=4,
            height=1,
            bg=COLORS["button"],
            activebackground="#31556e",
            relief="raised",
        )
        btn.grid(row=0, column=1, sticky="ew", padx=(0, 7))
        btn.bind("<ButtonPress-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 1, "PAR_UI_BUTTON"))
        btn.bind("<ButtonRelease-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 0, "PAR_UI_BUTTON"))

        led = Led(cell, size=24, bg=COLORS["panel"])
        led.grid(row=0, column=2, sticky="e", padx=(2, 0))
        led.set(self.bus.get(led_sig))
        self.rows[led_sig] = _ParValueProxy(lambda v, l=led: l.set(v))
        self.rows[sw_sig] = _ParValueProxy(lambda v, l=led, ls=led_sig: l.set(self.bus.get(ls) or v))

    return panel


def _par_level_xyz_panel_v6(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    # Płytka pomiarowa zmniejszona względem poprzedniej wersji.
    canvas = tk.Canvas(wrap, width=82, height=60, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 5), pady=1)

    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 100) or 100),
    }
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def calc_z(x, y):
        import math
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def draw():
        canvas.delete("all")
        w, h = 82, 60
        cx, cy = w / 2, h / 2
        x = clamp(state["x"])
        y = clamp(state["y"])
        z = clamp(state["z"])

        canvas.create_line(7, cy, w - 7, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 6, cx, h - 6, fill="#31414a", width=1)
        canvas.create_polygon(
            18 + x * 0.045,
            18 - y * 0.045,
            w - 18 + x * 0.045,
            20 + y * 0.045,
            w - 20 - x * 0.045,
            h - 16 + y * 0.045,
            20 - x * 0.045,
            h - 18 - y * 0.045,
            fill="#0d222c",
            outline="#386271",
        )
        px = cx + x / 100.0 * 25
        py = cy - y / 100.0 * 18
        size = 4 + max(0, z) / 100.0 * 1.5
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        canvas.create_text(6, 5, text="XY", fill=COLORS["muted"], anchor="w", font=("Segoe UI", 6, "bold"))

        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_values(x=None, y=None, z=None, publish_signals=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        else:
            state["z"] = calc_z(state["x"], state["y"])
        if publish_signals:
            publish()
        draw()

    def nudge(axis, delta):
        key = axis.lower()
        if axis == "Z":
            # Z jest wynikiem pochylenia; korekta ręczna zostaje tylko do symulacji testowej.
            set_values(z=state["z"] + delta)
        else:
            set_values(**{key: state[key] + delta})

    def zero_axis(axis):
        if axis == "X":
            set_values(x=0)
        elif axis == "Y":
            set_values(y=0)
        else:
            # Zerowanie Z w modelu akcelerometru = powrót płaszczyzny do poziomu.
            set_values(x=0, y=0)

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=0)
        tk.Label(
            row,
            textvariable=vars_by_axis[axis],
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Consolas", 9, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Przy każdej osi są trzy małe przyciski: minus, plus i zerowanie danej osi.
        tk.Button(row, text="0", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 7, "bold"), command=lambda a=axis: zero_axis(a)).pack(side="right", padx=(1, 0))
        tk.Button(row, text="+", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 7, "bold"), command=lambda a=axis: nudge(a, 1)).pack(side="right", padx=(1, 0))
        tk.Button(row, text="−", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 7, "bold"), command=lambda a=axis: nudge(a, -1)).pack(side="right", padx=(1, 0))

    def drag(event):
        set_values(x=(event.x - 41) / 25 * 100, y=-(event.y - 30) / 18 * 100)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)

    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_values(z=v, publish_signals=False))
    return panel


TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v6
TarzanParPanels.temperature_panel = _par_temperature_panel_v6
TarzanParPanels.limits = _par_limits_v6
TarzanParPanels.ui_panel = _par_ui_panel_v6
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v6

# =====================================================================
# TARZAN PAR — KOREKTY v7 wg uwag użytkownika
# Zakres: tylko PAR / panele symulatora. Bez EHR i Projektanta Układu.
# =====================================================================

def _par_sensor_canvas_slider_panel_v7(self, parent, *, key, title, signal, unit, start, end):
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    def clamp(v):
        try:
            lo, hi = sorted([float(start), float(end)])
            return max(lo, min(hi, float(v)))
        except Exception:
            return float(start)

    state = {"value": clamp(self.bus.get(signal, start) or start)}

    def fmt(v):
        try:
            return f"{int(round(float(v)))} {unit}"
        except Exception:
            return f"{int(start)} {unit}"

    value_label = tk.Label(
        wrap,
        text=fmt(state["value"]),
        bg=COLORS["panel"],
        fg=COLORS["green"],
        font=("Segoe UI", 18, "bold"),
    )
    value_label.pack(side="right", padx=(7, 0), fill="x", expand=True)

    canvas = tk.Canvas(wrap, width=34, height=124, bg=COLORS["panel"], highlightthickness=0)
    canvas.pack(side="left", padx=(0, 8), pady=2)

    def y_from_value(v):
        lo, hi = sorted([float(start), float(end)])
        span = max(1.0, hi - lo)
        return 112 - ((clamp(v) - lo) / span) * 100

    def value_from_y(y):
        lo, hi = sorted([float(start), float(end)])
        ratio = (112 - max(12, min(112, y))) / 100
        return lo + ratio * (hi - lo)

    def draw(v=None, publish=False):
        if v is not None:
            state["value"] = clamp(v)
        canvas.delete("all")
        canvas.create_rectangle(12, 10, 22, 114, fill=COLORS["green"], outline="#0a2d0c", width=1)
        y = y_from_value(state["value"])
        # Stały bordowy uchwyt, niezależny od najechania myszką.
        canvas.create_rectangle(5, y - 7, 29, y + 7, fill=_PAR_BURGUNDY, outline="#ffd5d5", width=1)
        canvas.create_line(9, y, 25, y, fill="#ffffff", width=1)
        value_label.configure(text=fmt(state["value"]))
        if publish:
            _par_set_signal(self, signal, state["value"], "PAR_SENSOR")

    def drag(event):
        draw(value_from_y(event.y), publish=True)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    draw()
    self.rows[signal] = _ParValueProxy(lambda v: draw(v, publish=False))
    return panel


def _par_light_bh1750_panel_v7(self, parent):
    return _par_sensor_canvas_slider_panel_v7(
        self, parent, key="light_bh1750", title="CZUJNIK ŚWIATŁA BH1750",
        signal="par_bh1750_lux", unit="lux", start=0, end=120000,
    )


def _par_temperature_panel_v7(self, parent):
    return _par_sensor_canvas_slider_panel_v7(
        self, parent, key="temperature", title="CZUJNIK TEMPERATURY POWIETRZA",
        signal="par_temperature_c", unit="°C", start=-20, end=50,
    )


def _par_limits_v7(self, parent):
    panel = self.panel("limits", parent, "KRAŃCÓWKI")
    body = tk.Frame(panel.body, bg=COLORS["panel"])
    body.pack(fill="both", expand=True)
    raw_names = self._group_or_search("KRAŃCÓWKI", ["limit"])
    names = []
    for name in raw_names:
        label = self.limit_label(name)
        blob = f"{name} {label}".upper()
        if "PIN WOLNY" in blob or "WOLNY" in blob or "FREE" in blob:
            continue
        names.append(name)
    if not names:
        tk.Label(body, text="Brak krańcówek w mapie sygnałów.", bg=COLORS["panel"], fg=COLORS["red"]).pack(anchor="w")
        return panel

    cols = 3
    for col in range(cols):
        body.grid_columnconfigure(col, weight=1, uniform="limit_col")

    for i, name in enumerate(names):
        r = i // cols
        c = i % cols
        cell = tk.Frame(body, bg=COLORS["panel"])
        cell.grid(row=r, column=c, sticky="ew", padx=3, pady=1)
        cell.grid_columnconfigure(1, weight=1)

        led = Led(cell, size=17, bg=COLORS["panel"])
        led.grid(row=0, column=0, sticky="w", padx=(0, 4))
        led.set(self.bus.get(name))
        self.rows[name] = _ParValueProxy(lambda v, l=led: l.set(v))

        label = tk.Label(
            cell, text=self.limit_label(name), bg=COLORS["panel"], fg=COLORS["text"],
            anchor="w", font=("Segoe UI", 8),
        )
        label.grid(row=0, column=1, sticky="ew")

        def click(_event=None, n=name):
            self.bus.toggle_input(n, source="PAR_LIMIT")
        cell.bind("<Button-1>", click)
        label.bind("<Button-1>", click)
        led.bind("<Button-1>", click)
    return panel


def _par_ui_panel_v7(self, parent):
    panel = self.panel("ui", parent, "PANEL PLAY/REC")
    buttons = [
        ("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
        ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
        ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
        ("F4", "rec_p51_sw_f4", "rec_p52_led_f4"),
    ]
    grid = tk.Frame(panel.body, bg=COLORS["panel"])
    grid.pack(fill="x")
    grid.grid_columnconfigure(1, weight=1)

    for i, (label_text, sw_sig, led_sig) in enumerate(buttons):
        tk.Label(
            grid, text=label_text, bg=COLORS["panel"], fg=COLORS["text"], width=2,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=i, column=0, sticky="w", padx=(0, 3), pady=2)
        btn = tk.Button(
            grid, text="", width=5, height=1, bg=COLORS["button"], activebackground="#31556e", relief="raised",
        )
        btn.grid(row=i, column=1, sticky="ew", padx=(0, 10), pady=2)
        btn.bind("<ButtonPress-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 1, "PAR_UI_BUTTON"))
        btn.bind("<ButtonRelease-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 0, "PAR_UI_BUTTON"))
        led = Led(grid, size=28, bg=COLORS["panel"])
        led.grid(row=i, column=2, sticky="e", padx=(4, 0), pady=2)
        led.set(self.bus.get(led_sig))
        self.rows[led_sig] = _ParValueProxy(lambda v, l=led: l.set(v))
        self.rows[sw_sig] = _ParValueProxy(lambda v, l=led, ls=led_sig: l.set(self.bus.get(ls) or v))
    return panel


def _par_level_xyz_panel_v7(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=104, height=76, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 6), pady=1)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    state = {"x": float(self.bus.get("par_level_x", 0) or 0), "y": float(self.bus.get("par_level_y", 0) or 0), "z": float(self.bus.get("par_level_z", 100) or 100)}
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try: return max(-100.0, min(100.0, float(v)))
        except Exception: return 0.0

    def calc_z(x, y):
        import math
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def draw():
        canvas.delete("all")
        w, h = 104, 76
        cx, cy = w / 2, h / 2
        x, y, z = clamp(state["x"]), clamp(state["y"]), clamp(state["z"])
        canvas.create_line(8, cy, w - 8, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 7, cx, h - 7, fill="#31414a", width=1)
        canvas.create_polygon(
            22 + x * 0.06, 22 - y * 0.06,
            w - 22 + x * 0.06, 24 + y * 0.06,
            w - 24 - x * 0.06, h - 20 + y * 0.06,
            24 - x * 0.06, h - 22 - y * 0.06,
            fill="#0d222c", outline="#386271",
        )
        px = cx + x / 100.0 * 34
        py = cy - y / 100.0 * 25
        size = 5 + max(0, z) / 100.0 * 2
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        canvas.create_text(7, 5, text="XY", fill=COLORS["muted"], anchor="w", font=("Segoe UI", 7, "bold"))
        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_values(x=None, y=None, z=None, publish_signals=True):
        if x is not None: state["x"] = clamp(x)
        if y is not None: state["y"] = clamp(y)
        if z is not None: state["z"] = clamp(z)
        else: state["z"] = calc_z(state["x"], state["y"])
        if publish_signals: publish()
        draw()

    def nudge(axis, delta):
        key = axis.lower()
        if axis == "Z": set_values(z=state["z"] + delta)
        else: set_values(**{key: state[key] + delta})

    def zero_axis(axis):
        if axis == "X": set_values(x=0)
        elif axis == "Y": set_values(y=0)
        else: set_values(x=0, y=0)

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=0)
        tk.Label(row, textvariable=vars_by_axis[axis], bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 18, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(row, text="0", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 7, "bold"), command=lambda a=axis: zero_axis(a)).pack(side="right", padx=(1, 0))
        tk.Button(row, text="+", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 7, "bold"), command=lambda a=axis: nudge(a, 1)).pack(side="right", padx=(1, 0))
        tk.Button(row, text="−", width=2, bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 7, "bold"), command=lambda a=axis: nudge(a, -1)).pack(side="right", padx=(1, 0))

    def drag(event):
        set_values(x=(event.x - 52) / 34 * 100, y=-(event.y - 38) / 25 * 100)
    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_values(z=v, publish_signals=False))
    return panel


def _par_lamp_panel_v7(self, parent):
    panel = self.panel("lamp", parent, "PRACA")
    canvas = tk.Canvas(panel.body, width=100, height=70, bg=COLORS["panel"], highlightthickness=0)
    canvas.pack(anchor="center", padx=6, pady=6)
    state = {"value": 1 if self.bus.get("par_lamp_auto_active") else 0}

    def draw(v=None):
        if v is not None: state["value"] = 1 if v else 0
        canvas.delete("all")
        color = COLORS["red"] if state["value"] else "#5b6268"
        glow = "#5a1613" if state["value"] else "#20282d"
        canvas.create_rectangle(5, 8, 95, 62, fill=glow, outline="")
        canvas.create_rectangle(13, 15, 87, 55, fill=color, outline="#111", width=2)
        canvas.create_rectangle(18, 19, 44, 28, fill="#ffffff", outline="", stipple="gray50")

    def toggle(_event=None):
        self.bus.toggle_input("par_lamp_auto_active", source="PAR_LAMP")
    canvas.bind("<Button-1>", toggle)
    panel.body.bind("<Button-1>", toggle)
    draw()
    self.rows["par_lamp_auto_active"] = _ParValueProxy(draw)
    return panel


# Log ruchu silników — także wtedy, gdy krok przychodzi z TAKE przez SignalBus.
_prev_refresh_axis_cards_v7 = TarzanParPanels.refresh_axis_cards

def _par_refresh_axis_cards_v7(self):
    for axis, card in self.axis_cards.items():
        if not hasattr(card, "on_motor_step_log"):
            def _mk_logger(axis_key, card_ref):
                def _logger():
                    try:
                        direction = "PRAWO" if card_ref.dir.state else "LEWO"
                        self.bus.log("PAR_MOTOR", f"{axis_key}: krok={card_ref.counter} kierunek={direction} kąt={card_ref.motor_angle:.1f}")
                    except Exception:
                        pass
                return _logger
            card.on_motor_step_log = _mk_logger(axis, card)
    _prev_refresh_axis_cards_v7(self)

TarzanParPanels.refresh_axis_cards = _par_refresh_axis_cards_v7
TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v7
TarzanParPanels.temperature_panel = _par_temperature_panel_v7
TarzanParPanels.limits = _par_limits_v7
TarzanParPanels.ui_panel = _par_ui_panel_v7
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v7
TarzanParPanels.lamp_panel = _par_lamp_panel_v7

# =====================================================================
# TARZAN PAR — KOREKTY v8 wg uwag użytkownika
# Zakres: tylko PAR / panele symulacji. Bez EHR, Projektanta Układu i generatora TAKE.
# =====================================================================

def _par_canvas_sensor_slider_panel_v8(self, parent, *, key, title, signal, unit, start, end, decimals=0):
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    def clamp(v):
        try:
            return max(float(start), min(float(end), float(v)))
        except Exception:
            return float(start)

    def fmt(v):
        fv = clamp(v)
        return f"{fv:.{decimals}f} {unit}" if decimals else f"{int(round(fv))} {unit}"

    h = 132
    w = 34
    canvas = tk.Canvas(wrap, width=w, height=h, bg=COLORS["panel"], highlightthickness=0)
    canvas.pack(side="left", padx=(0, 8), pady=3)
    value_label = tk.Label(
        wrap,
        text=fmt(self.bus.get(signal, start)),
        bg=COLORS["panel"],
        fg=COLORS["green"],
        font=("Segoe UI", 18, "bold"),
    )
    value_label.pack(side="right", padx=(8, 0), fill="x", expand=True)

    state = {"value": clamp(self.bus.get(signal, start))}

    def y_for_value(v):
        v = clamp(v)
        span = max(1.0, float(end) - float(start))
        return 10 + (float(end) - v) / span * (h - 20)

    def value_for_y(y):
        y = max(10, min(h - 10, float(y)))
        span = max(1.0, float(end) - float(start))
        return float(end) - ((y - 10) / (h - 20)) * span

    def draw():
        canvas.delete("all")
        # Zielone tło/tor suwaka zostaje, uchwyt jest stale bordowy.
        canvas.create_rectangle(13, 8, 21, h - 8, fill=COLORS["green"], outline="#0a3b10", width=1)
        y = y_for_value(state["value"])
        canvas.create_rectangle(5, y - 7, 29, y + 7, fill="#7b1730", outline="#ff9ab0", width=2)
        canvas.create_rectangle(9, y - 4, 25, y - 1, fill="#c04a62", outline="")
        value_label.configure(text=fmt(state["value"]))

    def set_value(v, publish=True):
        state["value"] = clamp(v)
        if publish:
            _par_set_signal(self, signal, state["value"], "PAR_SENSOR")
        draw()

    def drag(event):
        set_value(value_for_y(event.y), publish=True)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    draw()
    self.rows[signal] = _ParValueProxy(lambda v: set_value(v, publish=False))
    return panel


def _par_light_bh1750_panel_v8(self, parent):
    return _par_canvas_sensor_slider_panel_v8(
        self, parent,
        key="light_bh1750",
        title="CZUJNIK ŚWIATŁA BH1750",
        signal="par_bh1750_lux",
        unit="lx",
        start=0,
        end=120000,
        decimals=0,
    )


def _par_temperature_panel_v8(self, parent):
    return _par_canvas_sensor_slider_panel_v8(
        self, parent,
        key="temperature",
        title="CZUJNIK TEMPERATURY POWIETRZA",
        signal="par_temperature_c",
        unit="°C",
        start=-20,
        end=50,
        decimals=1,
    )


def _par_level_xyz_panel_v8(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=140, height=96, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 7), pady=1)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 100) or 100),
    }
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def calc_z(x, y):
        import math
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def draw():
        canvas.delete("all")
        w, h = 140, 96
        cx, cy = w / 2, h / 2
        x, y, z = clamp(state["x"]), clamp(state["y"]), clamp(state["z"])
        canvas.create_line(9, cy, w - 9, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 8, cx, h - 8, fill="#31414a", width=1)
        canvas.create_polygon(
            28 + x * 0.08, 28 - y * 0.08,
            w - 28 + x * 0.08, 30 + y * 0.08,
            w - 30 - x * 0.08, h - 24 + y * 0.08,
            30 - x * 0.08, h - 26 - y * 0.08,
            fill="#0d222c", outline="#386271", width=2,
        )
        px = cx + x / 100.0 * 45
        py = cy - y / 100.0 * 32
        size = 7 + max(0, z) / 100.0 * 3
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        canvas.create_text(8, 6, text="XY", fill=COLORS["muted"], anchor="w", font=("Segoe UI", 7, "bold"))
        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_values(x=None, y=None, z=None, publish_signals=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        else:
            state["z"] = calc_z(state["x"], state["y"])
        if publish_signals:
            publish()
        draw()

    def nudge(axis, delta):
        key = axis.lower()
        if axis == "Z":
            set_values(z=state["z"] + delta)
        else:
            set_values(**{key: state[key] + delta})

    def zero_axis(axis):
        if axis == "X":
            set_values(x=0)
        elif axis == "Y":
            set_values(y=0)
        else:
            set_values(x=0, y=0)

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=0)
        tk.Label(
            row,
            textvariable=vars_by_axis[axis],
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 15, "bold"),
            anchor="w",
            width=5,
        ).pack(side="left")
        for text, cmd in [
            ("−", lambda a=axis: nudge(a, -1)),
            ("+", lambda a=axis: nudge(a, 1)),
            ("0", lambda a=axis: zero_axis(a)),
        ]:
            tk.Button(
                row,
                text=text,
                width=2,
                bg=COLORS["button"],
                fg=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 7, "bold"),
                command=cmd,
            ).pack(side="right", padx=(1, 0))

    def drag(event):
        set_values(x=(event.x - 70) / 45 * 100, y=-(event.y - 48) / 32 * 100)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_values(z=v, publish_signals=False))
    return panel


def _par_ui_panel_v8(self, parent):
    panel = self.panel("ui", parent, "PANEL PLAY/REC")
    buttons = [
        ("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
        ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
        ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
        ("F4", "rec_p51_sw_f4", "rec_p52_led_f4"),
    ]
    grid = tk.Frame(panel.body, bg=COLORS["panel"])
    grid.pack(fill="x")
    grid.grid_columnconfigure(1, weight=0)
    grid.grid_columnconfigure(3, weight=1)

    for i, (label_text, sw_sig, led_sig) in enumerate(buttons):
        tk.Label(
            grid,
            text=label_text,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            width=3,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=i, column=0, sticky="w", padx=(0, 3), pady=3)
        btn = tk.Button(
            grid,
            text="",
            width=4,
            height=1,
            bg=COLORS["button"],
            activebackground="#31556e",
            relief="raised",
        )
        btn.grid(row=i, column=1, sticky="w", padx=(0, 8), pady=3)
        btn.bind("<ButtonPress-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 1, "PAR_UI_BUTTON"))
        btn.bind("<ButtonRelease-1>", lambda _e, s=sw_sig: _par_set_signal(self, s, 0, "PAR_UI_BUTTON"))

        # LED jest osobnym sygnałem z mapy i nie jest zespolony z przyciskiem.
        tk.Label(grid, text="LED", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 7, "bold")).grid(row=i, column=2, sticky="e", padx=(4, 3))
        led = Led(grid, size=30, bg=COLORS["panel"])
        led.grid(row=i, column=3, sticky="w", padx=(0, 0), pady=3)
        led.set(self.bus.get(led_sig))
        self.rows[led_sig] = _ParValueProxy(lambda v, l=led: l.set(v))
    return panel


def _par_mass_regulator_panel_v8(self, parent):
    panel = self.panel("mass_regulator", parent, "REGULATOR MASY")
    state = {"mode": "OFF"}
    buttons = {}

    def paint_buttons():
        for mode, btn in buttons.items():
            active = state["mode"] == mode
            if mode == "ADD":
                btn.configure(bg=COLORS["green"] if active else COLORS["button"], fg="#061006" if active else COLORS["text"])
            elif mode == "REMOVE":
                btn.configure(bg=COLORS["blue"] if active else COLORS["button"], fg="#ffffff")

    def set_mode(mode):
        # Dwa przyciski dają trzy stany: OFF / DODAJ / UJMIJ. Ponowne kliknięcie aktywnego wyłącza.
        state["mode"] = "OFF" if state["mode"] == mode else mode
        add = 1 if state["mode"] == "ADD" else 0
        rem = 1 if state["mode"] == "REMOVE" else 0
        en = 1 if state["mode"] in {"ADD", "REMOVE"} else 0
        for sig, val in [
            ("play_p41_mass_reg_enable", en),
            ("rec_p36_mass_reg_enable", en),
            ("play_p13_mass_reg_limit_add", add),
            ("play_p23_mass_reg_limit_remove", rem),
            ("par_mass_reg_enable", en),
            ("par_mass_reg_limit_add", add),
            ("par_mass_reg_limit_remove", rem),
        ]:
            _par_set_signal(self, sig, val, "PAR_MASS_3STATE")
        paint_buttons()

    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)
    btn_add = tk.Button(wrap, text="DODAJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"), command=lambda: set_mode("ADD"))
    btn_rem = tk.Button(wrap, text="UJMIJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"), command=lambda: set_mode("REMOVE"))
    btn_add.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=2)
    btn_rem.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=2)
    buttons["ADD"] = btn_add
    buttons["REMOVE"] = btn_rem
    paint_buttons()
    return panel


# Log silników bez kąta: tylko logika TARZANA DIR/CTR/STEP.
_prev_refresh_axis_cards_v8 = TarzanParPanels.refresh_axis_cards

def _par_refresh_axis_cards_v8(self):
    _prev_refresh_axis_cards_v8(self)
    for axis, card in self.axis_cards.items():
        def _mk_logger(axis_key, card_ref):
            def _logger():
                try:
                    self.bus.log("PAR_MOTOR", f"{axis_key}: CTR/STEP=1 DIR={1 if card_ref.dir.state else 0} LICZNIK={card_ref.counter}")
                except Exception:
                    pass
            return _logger
        card.on_motor_step_log = _mk_logger(axis, card)

TarzanParPanels.refresh_axis_cards = _par_refresh_axis_cards_v8
TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v8
TarzanParPanels.temperature_panel = _par_temperature_panel_v8
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v8
TarzanParPanels.ui_panel = _par_ui_panel_v8
TarzanParPanels.mass_regulator_panel = _par_mass_regulator_panel_v8

# =====================================================================
# TARZAN PAR — KOREKTY v9 wg uwag użytkownika
# Zakres: tylko PAR / panele symulacji. Bez EHR, Projektanta Układu i generatora TAKE.
# =====================================================================

# Opis osi poziomej kamery bez dopisku PAN, żeby nie rozbijał układu kart osi.
_prev_axes_v9 = TarzanParPanels.axes

def _par_axes_v9(self, parent):
    panel = _prev_axes_v9(self, parent)
    try:
        card = self.axis_cards.get("CAM_H")
        if card:
            for child in card.winfo_children():
                try:
                    if isinstance(child, tk.Label) and "OŚ POZIOMA KAMERY" in str(child.cget("text")):
                        child.configure(text="3. OŚ POZIOMA KAMERY")
                except Exception:
                    pass
    except Exception:
        pass
    return panel


def _par_canvas_sensor_slider_panel_v9(self, parent, *, key, title, signal, unit, start, end, decimals=0):
    """Prosty pionowy suwak: zielony tor + stały bordowy uchwyt, bez ukrywania po kliknięciu."""
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    def clamp(v):
        try:
            return max(float(start), min(float(end), float(v)))
        except Exception:
            return float(start)

    def fmt(v):
        fv = clamp(v)
        return f"{fv:.{decimals}f} {unit}" if decimals else f"{int(round(fv))} {unit}"

    h = 126
    w = 38
    canvas = tk.Canvas(wrap, width=w, height=h, bg=COLORS["panel"], highlightthickness=0, bd=0)
    canvas.pack(side="left", padx=(0, 8), pady=2)
    value_label = tk.Label(
        wrap,
        text=fmt(self.bus.get(signal, start)),
        bg=COLORS["panel"],
        fg=COLORS["green"],
        font=("Segoe UI", 17, "bold"),
        anchor="center",
    )
    value_label.pack(side="left", fill="both", expand=True)

    state = {"value": clamp(self.bus.get(signal, start))}

    def y_for_value(v):
        span = max(1.0, float(end) - float(start))
        return 9 + (float(end) - clamp(v)) / span * (h - 18)

    def value_for_y(y):
        y = max(9, min(h - 9, float(y)))
        span = max(1.0, float(end) - float(start))
        return float(end) - ((y - 9) / (h - 18)) * span

    def draw():
        canvas.delete("all")
        # Stały, prosty tor — zielony jak było.
        canvas.create_rectangle(14, 7, 24, h - 7, fill=COLORS["green"], outline="#063c0a", width=1)
        canvas.create_rectangle(17, 11, 21, h - 11, fill="#0f7d18", outline="")
        # Stały uchwyt — bordo, niezależny od hovera/myszy.
        y = y_for_value(state["value"])
        canvas.create_rectangle(5, y - 8, 33, y + 8, fill="#7b1730", outline="#d65c78", width=2)
        canvas.create_rectangle(9, y - 4, 29, y + 4, fill="#9e2943", outline="")
        value_label.configure(text=fmt(state["value"]))

    def set_value(v, publish=True):
        state["value"] = clamp(v)
        if publish:
            _par_set_signal(self, signal, state["value"], "PAR_SENSOR")
        draw()

    def drag(event):
        set_value(value_for_y(event.y), publish=True)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    draw()
    self.rows[signal] = _ParValueProxy(lambda v: set_value(v, publish=False))
    return panel


def _par_light_bh1750_panel_v9(self, parent):
    return _par_canvas_sensor_slider_panel_v9(
        self, parent,
        key="light_bh1750",
        title="CZUJNIK ŚWIATŁA BH1750",
        signal="par_bh1750_lux",
        unit="lx",
        start=0,
        end=120000,
        decimals=0,
    )


def _par_temperature_panel_v9(self, parent):
    return _par_canvas_sensor_slider_panel_v9(
        self, parent,
        key="temperature",
        title="CZUJNIK TEMPERATURY POWIETRZA",
        signal="par_temperature_c",
        unit="°C",
        start=-20,
        end=50,
        decimals=1,
    )


def _par_level_xyz_panel_v9(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=138, height=94, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 7), pady=1)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 100) or 100),
    }
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def calc_z(x, y):
        import math
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def draw():
        canvas.delete("all")
        w, h = 138, 94
        cx, cy = w / 2, h / 2
        x, y, z = clamp(state["x"]), clamp(state["y"]), clamp(state["z"])
        canvas.create_line(9, cy, w - 9, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 8, cx, h - 8, fill="#31414a", width=1)
        canvas.create_polygon(
            28 + x * 0.08, 28 - y * 0.08,
            w - 28 + x * 0.08, 30 + y * 0.08,
            w - 30 - x * 0.08, h - 24 + y * 0.08,
            30 - x * 0.08, h - 26 - y * 0.08,
            fill="#0d222c", outline="#386271", width=2,
        )
        px = cx + x / 100.0 * 44
        py = cy - y / 100.0 * 31
        size = 7 + max(0, z) / 100.0 * 3
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_values(x=None, y=None, z=None, publish_signals=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        else:
            state["z"] = calc_z(state["x"], state["y"])
        if publish_signals:
            publish()
        draw()

    def nudge(axis, delta):
        key = axis.lower()
        if axis == "Z":
            set_values(z=state["z"] + delta)
        else:
            set_values(**{key: state[key] + delta})

    def zero_axis(axis):
        if axis == "X":
            set_values(x=0)
        elif axis == "Y":
            set_values(y=0)
        else:
            set_values(x=0, y=0)

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=0)
        tk.Label(
            row,
            textvariable=vars_by_axis[axis],
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 14, "bold"),
            anchor="w",
            width=5,
        ).pack(side="left")
        for text, cmd in [
            ("−", lambda a=axis: nudge(a, -1)),
            ("+", lambda a=axis: nudge(a, 1)),
            ("0", lambda a=axis: zero_axis(a)),
        ]:
            tk.Button(
                row,
                text=text,
                width=2,
                bg=COLORS["button"],
                fg=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 7, "bold"),
                command=cmd,
            ).pack(side="right", padx=(1, 0))

    def drag(event):
        set_values(x=(event.x - 69) / 44 * 100, y=-(event.y - 47) / 31 * 100)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_values(z=v, publish_signals=False))
    return panel


# Log silnika: tylko logika TARZANA: DIR + STEP zapisany jako 01. Bez licznika i bez kąta.
def _par_refresh_axis_cards_v9(self):
    try:
        _prev_refresh_axis_cards_v8(self)
    except Exception:
        try:
            _prev_refresh_axis_cards_v8(self)
        except Exception:
            pass
    for axis, card in self.axis_cards.items():
        def _mk_logger(axis_key, card_ref):
            def _logger():
                try:
                    self.bus.log("PAR_MOTOR", f"{axis_key}: DIR={1 if card_ref.dir.state else 0} STEP=01")
                except Exception:
                    pass
            return _logger
        card.on_motor_step_log = _mk_logger(axis, card)

TarzanParPanels.axes = _par_axes_v9
TarzanParPanels.refresh_axis_cards = _par_refresh_axis_cards_v9
TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v9
TarzanParPanels.temperature_panel = _par_temperature_panel_v9
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v9

# =====================================================================
# TARZAN PAR — KOREKTY v10 wg uwag użytkownika
# Zakres: tylko PAR / panele symulacji. Bez EHR, Projektanta Układu i generatora TAKE.
# =====================================================================

# 1) Suwaki światła/temperatury: proste pionowe, mieszczące się w panelu 2 wierszy.
def _par_canvas_sensor_slider_panel_v10(self, parent, *, key, title, signal, unit, start, end, decimals=0):
    panel = self.panel(key, parent, title)
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    def clamp(v):
        try:
            return max(float(start), min(float(end), float(v)))
        except Exception:
            return float(start)

    def fmt(v):
        fv = clamp(v)
        return f"{fv:.{decimals}f} {unit}" if decimals else f"{int(round(fv))} {unit}"

    h = 88
    w = 38
    canvas = tk.Canvas(wrap, width=w, height=h, bg=COLORS["panel"], highlightthickness=0, bd=0)
    canvas.pack(side="left", padx=(0, 7), pady=0)
    value_label = tk.Label(
        wrap,
        text=fmt(self.bus.get(signal, start)),
        bg=COLORS["panel"],
        fg=COLORS["green"],
        font=("Segoe UI", 15, "bold"),
        anchor="center",
    )
    value_label.pack(side="left", fill="both", expand=True)

    state = {"value": clamp(self.bus.get(signal, start))}

    def y_for_value(v):
        span = max(1.0, float(end) - float(start))
        return 7 + (float(end) - clamp(v)) / span * (h - 14)

    def value_for_y(y):
        y = max(7, min(h - 7, float(y)))
        span = max(1.0, float(end) - float(start))
        return float(end) - ((y - 7) / (h - 14)) * span

    def draw():
        canvas.delete("all")
        # Prosty zielony pionowy tor + stały bordowy uchwyt.
        canvas.create_rectangle(14, 5, 24, h - 5, fill=COLORS["green"], outline="#063c0a", width=1)
        canvas.create_rectangle(17, 9, 21, h - 9, fill="#0f7d18", outline="")
        y = y_for_value(state["value"])
        canvas.create_rectangle(5, y - 7, 33, y + 7, fill="#7b1730", outline="#d65c78", width=2)
        canvas.create_rectangle(9, y - 3, 29, y + 3, fill="#9e2943", outline="")
        value_label.configure(text=fmt(state["value"]))

    def set_value(v, publish=True):
        state["value"] = clamp(v)
        if publish:
            _par_set_signal(self, signal, state["value"], "PAR_SENSOR")
        draw()

    def drag(event):
        set_value(value_for_y(event.y), publish=True)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    draw()
    self.rows[signal] = _ParValueProxy(lambda v: set_value(v, publish=False))
    return panel


def _par_light_bh1750_panel_v10(self, parent):
    return _par_canvas_sensor_slider_panel_v10(
        self, parent,
        key="light_bh1750",
        title="ŚWIATŁO BH1750",
        signal="par_bh1750_lux",
        unit="lx",
        start=0,
        end=120000,
        decimals=0,
    )


def _par_temperature_panel_v10(self, parent):
    return _par_canvas_sensor_slider_panel_v10(
        self, parent,
        key="temperature",
        title="TEMPERATURA POWIETRZA",
        signal="par_temperature_c",
        unit="°C",
        start=-20,
        end=50,
        decimals=1,
    )


# 2) Krótkie nazwy paneli: WSTRZĄS / OŚ LASER.
def _par_shock_sensor_panel_v10(self, parent):
    return _par_click_sensor_panel(
        self,
        parent,
        key="shock_sensor_panel",
        title="WSTRZĄS",
        signal="par_shock_sensor_state",
        on_text="WSTRZĄS = 1",
        off_text="SPOKÓJ = 0",
        extra={"rec_p39_shock_sensor": lambda v: v},
    )


def _par_laser_panel_v10(self, parent):
    return _par_click_sensor_panel(
        self,
        parent,
        key="laser",
        title="OŚ LASER",
        signal="par_laser_set",
        on_text="UTRACONA OŚ = 1",
        off_text="OŚ OK = 0",
        extra={
            "par_laser_error": lambda v: v,
            "par_laser_state_high": lambda v: v,
            "par_laser_state_low": lambda v: 0 if v else 1,
        },
    )


# 3) Duży + / - przy osi pionowej ramienia, sprzężony z regulatorem masy.
_prev_axes_v10 = TarzanParPanels.axes

def _par_axes_v10(self, parent):
    panel = _prev_axes_v10(self, parent)
    try:
        card = self.axis_cards.get("ARM_V")
        if card and not getattr(card, "_mass_compensation_marks_v10", False):
            mark_frame = tk.Frame(card, bg=COLORS["panel3"])
            mark_frame.pack(fill="x", padx=8, pady=(4, 8))
            minus = tk.Label(
                mark_frame,
                text="−",
                bg=COLORS["panel3"],
                fg="#6c747a",
                font=("Segoe UI", 34, "bold"),
                width=2,
                anchor="center",
            )
            minus.pack(side="left", padx=(8, 2))
            tk.Label(
                mark_frame,
                text="REGULATOR\nMASY",
                bg=COLORS["panel3"],
                fg=COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
                justify="center",
            ).pack(side="left", fill="x", expand=True)
            plus = tk.Label(
                mark_frame,
                text="+",
                bg=COLORS["panel3"],
                fg="#6c747a",
                font=("Segoe UI", 34, "bold"),
                width=2,
                anchor="center",
            )
            plus.pack(side="right", padx=(2, 8))

            def update_marks(_v=None):
                add = bool(self.bus.get("par_mass_reg_limit_add") or self.bus.get("play_p13_mass_reg_limit_add"))
                rem = bool(self.bus.get("par_mass_reg_limit_remove") or self.bus.get("play_p23_mass_reg_limit_remove"))
                plus.configure(fg=COLORS["green"] if add else "#6c747a")
                minus.configure(fg=COLORS["blue"] if rem else "#6c747a")

            card._mass_compensation_marks_v10 = True
            card._mass_compensation_update_v10 = update_marks
            self.rows["par_mass_reg_limit_add"] = _ParValueProxy(update_marks)
            self.rows["par_mass_reg_limit_remove"] = _ParValueProxy(update_marks)
            self.rows["play_p13_mass_reg_limit_add"] = _ParValueProxy(update_marks)
            self.rows["play_p23_mass_reg_limit_remove"] = _ParValueProxy(update_marks)
            update_marks()
    except Exception:
        pass
    return panel


TarzanParPanels.axes = _par_axes_v10
TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_v10
TarzanParPanels.temperature_panel = _par_temperature_panel_v10
TarzanParPanels.shock_sensor_panel = _par_shock_sensor_panel_v10
TarzanParPanels.laser_panel = _par_laser_panel_v10

# =====================================================================
# TARZAN PAR — KOREKTY v11: regulator masy pod osią pionową ramienia
# Zostaje pod silnikiem, z wyróżniającym tłem i większymi znakami +/-.
# =====================================================================
_prev_axes_v11 = TarzanParPanels.axes

def _par_axes_v11(self, parent):
    panel = _prev_axes_v11(self, parent)
    try:
        card = self.axis_cards.get("ARM_V")
        if not card:
            return panel

        # Ukryj stary pasek v10, jeśli został już dodany, i dodaj czytelniejszą wersję v11.
        for child in list(card.winfo_children()):
            if getattr(child, "_tarzan_mass_bar_v11", False):
                child.destroy()
                continue
            try:
                for grand in child.winfo_children():
                    if isinstance(grand, tk.Label) and "REGULATOR" in str(grand.cget("text")) and "MASY" in str(grand.cget("text")):
                        child.destroy()
                        break
            except Exception:
                pass
        for child in list(card.winfo_children()):
            if getattr(child, "_tarzan_mass_bar_v11", False):
                child.destroy()

        bar = tk.Frame(
            card,
            bg="#17242c",
            highlightbackground="#39505d",
            highlightcolor="#39505d",
            highlightthickness=1,
        )
        bar._tarzan_mass_bar_v11 = True
        bar.pack(fill="x", padx=8, pady=(4, 9))

        def make_mark(parent_frame, text, inactive, active):
            lbl = tk.Label(
                parent_frame,
                text=text,
                bg="#101820",
                fg=inactive,
                font=("Segoe UI", 46, "bold"),
                width=2,
                anchor="center",
                relief="flat",
                highlightbackground="#435762",
                highlightcolor="#435762",
                highlightthickness=2,
            )
            lbl._inactive_color = inactive
            lbl._active_color = active
            return lbl

        minus = make_mark(bar, "−", "#6c747a", COLORS["blue"])
        minus.pack(side="left", padx=(8, 8), pady=6)

        tk.Label(
            bar,
            text="REGULATOR\nMASY",
            bg="#17242c",
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
            justify="center",
        ).pack(side="left", fill="x", expand=True, pady=6)

        plus = make_mark(bar, "+", "#6c747a", COLORS["green"])
        plus.pack(side="right", padx=(8, 8), pady=6)

        def update_marks(_v=None):
            add = bool(self.bus.get("par_mass_reg_limit_add") or self.bus.get("play_p13_mass_reg_limit_add"))
            rem = bool(self.bus.get("par_mass_reg_limit_remove") or self.bus.get("play_p23_mass_reg_limit_remove"))
            plus.configure(
                fg=COLORS["green"] if add else "#6c747a",
                highlightbackground="#6dff72" if add else "#435762",
                bg="#12251b" if add else "#101820",
            )
            minus.configure(
                fg=COLORS["blue"] if rem else "#6c747a",
                highlightbackground="#5ebeff" if rem else "#435762",
                bg="#102032" if rem else "#101820",
            )

        card._mass_compensation_update_v11 = update_marks
        self.rows["par_mass_reg_limit_add"] = _ParValueProxy(update_marks)
        self.rows["par_mass_reg_limit_remove"] = _ParValueProxy(update_marks)
        self.rows["play_p13_mass_reg_limit_add"] = _ParValueProxy(update_marks)
        self.rows["play_p23_mass_reg_limit_remove"] = _ParValueProxy(update_marks)
        update_marks()
    except Exception:
        pass
    return panel

TarzanParPanels.axes = _par_axes_v11

# =====================================================================
# TARZAN PAR — KOREKTY v12 wg uwag użytkownika
# Zakres: tylko PAR / okna osi / timeline / XYZ. Bez EHR, Projektanta i generatora TAKE.
# 1) Pasek regulatora masy pod osią pionową ramienia: wysokość ok. 20 px.
# 2) Timeline: 12 kompaktowych linii — STEP i DIR dla wszystkich osi silników, bez ENABLE/FLAGA.
# 3) XYZ: większy prawy margines, żeby wartości +100 nie były przycinane.
# =====================================================================

# --- 1. Oś pionowa ramienia: węższy pasek regulatora masy ---
_prev_axes_v12 = TarzanParPanels.axes

def _par_axes_v12(self, parent):
    panel = _prev_axes_v12(self, parent)
    try:
        card = self.axis_cards.get("ARM_V")
        if not card:
            return panel

        # Usuń starsze paski regulatora masy, aby nie dublować elementów.
        for child in list(card.winfo_children()):
            if getattr(child, "_tarzan_mass_bar_v11", False) or getattr(child, "_tarzan_mass_bar_v12", False):
                child.destroy()
                continue
            try:
                for grand in child.winfo_children():
                    if isinstance(grand, tk.Label) and "REGULATOR" in str(grand.cget("text")) and "MASY" in str(grand.cget("text")):
                        child.destroy()
                        break
            except Exception:
                pass

        bar = tk.Frame(
            card,
            bg="#16242c",
            height=24,
            highlightbackground="#39505d",
            highlightcolor="#39505d",
            highlightthickness=1,
        )
        bar._tarzan_mass_bar_v12 = True
        bar.pack(fill="x", padx=8, pady=(2, 5))
        bar.pack_propagate(False)

        def make_mark(parent_frame, text, inactive, active):
            lbl = tk.Label(
                parent_frame,
                text=text,
                bg="#101820",
                fg=inactive,
                font=("Segoe UI", 18, "bold"),
                width=3,
                anchor="center",
                relief="flat",
                highlightbackground="#435762",
                highlightcolor="#435762",
                highlightthickness=2,
            )
            lbl._inactive_color = inactive
            lbl._active_color = active
            return lbl

        minus = make_mark(bar, "−", "#6c747a", COLORS["blue"])
        minus.pack(side="left", padx=(5, 4), pady=2, fill="y")

        tk.Label(
            bar,
            text="REGULATOR MASY",
            bg="#16242c",
            fg=COLORS["muted"],
            font=("Segoe UI", 7, "bold"),
            anchor="center",
        ).pack(side="left", fill="both", expand=True, pady=1)

        plus = make_mark(bar, "+", "#6c747a", COLORS["green"])
        plus.pack(side="right", padx=(4, 5), pady=2, fill="y")

        def update_marks(_v=None):
            add = bool(self.bus.get("par_mass_reg_limit_add") or self.bus.get("play_p13_mass_reg_limit_add"))
            rem = bool(self.bus.get("par_mass_reg_limit_remove") or self.bus.get("play_p23_mass_reg_limit_remove"))
            plus.configure(
                fg=COLORS["green"] if add else "#6c747a",
                highlightbackground="#6dff72" if add else "#435762",
                bg="#12251b" if add else "#101820",
            )
            minus.configure(
                fg=COLORS["blue"] if rem else "#6c747a",
                highlightbackground="#5ebeff" if rem else "#435762",
                bg="#102032" if rem else "#101820",
            )

        card._mass_compensation_update_v12 = update_marks
        self.rows["par_mass_reg_limit_add"] = _ParValueProxy(update_marks)
        self.rows["par_mass_reg_limit_remove"] = _ParValueProxy(update_marks)
        self.rows["play_p13_mass_reg_limit_add"] = _ParValueProxy(update_marks)
        self.rows["play_p23_mass_reg_limit_remove"] = _ParValueProxy(update_marks)
        update_marks()
    except Exception:
        pass
    return panel

TarzanParPanels.axes = _par_axes_v12


# --- 2. Timeline: wszystkie osie, tylko STEP/DIR, 12 linii ---
_AXIS_TIMELINE_ROWS_V12 = [
    ("ARM_H", "STEP", ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "cnc_b_arm_h_ctr"], COLORS["green"]),
    ("ARM_H", "DIR",  ["TAKE_ARM_H_DIR",  "play_p38_step_dir_arm_h", "cnc_b_arm_h_dir"], COLORS["blue"]),
    ("ARM_V", "STEP", ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "cnc_c_arm_v_ctr"], COLORS["green"]),
    ("ARM_V", "DIR",  ["TAKE_ARM_V_DIR",  "play_p39_step_dir_arm_v", "cnc_c_arm_v_dir"], COLORS["blue"]),
    ("CAM_H", "STEP", ["TAKE_CAM_H_STEP", "cnc_x_cam_h_ctr", "rec_p01_copy_ctr_cam_h"], COLORS["green"]),
    ("CAM_H", "DIR",  ["TAKE_CAM_H_DIR",  "cnc_x_cam_h_dir", "rec_p03_copy_dir_cam_h"], COLORS["blue"]),
    ("CAM_V", "STEP", ["TAKE_CAM_V_STEP", "cnc_y_cam_v_ctr", "rec_p02_copy_ctr_cam_v"], COLORS["green"]),
    ("CAM_V", "DIR",  ["TAKE_CAM_V_DIR",  "cnc_y_cam_v_dir", "rec_p04_copy_dir_cam_v"], COLORS["blue"]),
    ("CAM_T", "STEP", ["TAKE_CAM_T_STEP", "cnc_a_arm_tilt_ctr", "rec_p08_copy_ctr_cam_tilt"], COLORS["green"]),
    ("CAM_T", "DIR",  ["TAKE_CAM_T_DIR",  "cnc_a_arm_tilt_dir", "rec_p08_copy_dir_cam_tilt"], COLORS["blue"]),
    ("CAM_F", "STEP", ["TAKE_CAM_F_STEP", "cnc_z_cam_f_ctr", "rec_p07_copy_ctr_cam_f"], COLORS["green"]),
    ("CAM_F", "DIR",  ["TAKE_CAM_F_DIR",  "cnc_z_cam_f_dir", "rec_p07_copy_dir_cam_f"], COLORS["blue"]),
]


def _par_timeline_v12(self, parent):
    panel = self.panel("timeline", parent, "PODGLĄD SYGNAŁÓW SILNIKÓW — STEP / DIR")
    top = tk.Frame(panel.body, bg=COLORS["panel"])
    top.pack(fill="x")
    tk.Label(
        top,
        text="Wszystkie osie: 12 przebiegów STEP/DIR",
        bg=COLORS["panel"],
        fg=COLORS["muted"],
        font=("Segoe UI", 8, "bold"),
    ).pack(side="left")
    tk.Button(
        top,
        text="CLEAR",
        bg=COLORS["button"],
        fg=COLORS["text"],
        relief="flat",
        command=lambda: (self.bus.history.clear(), self.draw_timeline()),
    ).pack(side="right", padx=4)

    canvas = tk.Canvas(panel.body, bg="#070b0e", height=210, highlightthickness=0)
    canvas.pack(fill="both", expand=True, pady=(4, 2))
    self.timeline_canvas = canvas
    canvas.bind("<Configure>", lambda _e: self.draw_timeline())
    self.draw_timeline()
    return panel


def _first_existing_or_first_v12(self, names):
    for name in names:
        try:
            if self.bus.exists(name):
                return name
        except Exception:
            pass
    return names[0] if names else ""


def _history_points_for_signal_v12(hist, names, max_points=180):
    name_set = set(names)
    filtered = [h for h in hist if h.get("name") in name_set]
    if len(filtered) > max_points:
        filtered = filtered[-max_points:]
    return filtered


def _par_draw_timeline_v12(self):
    canvas = getattr(self, "timeline_canvas", None)
    if not canvas:
        return
    canvas.delete("all")
    w = max(canvas.winfo_width(), 760)
    h = max(canvas.winfo_height(), 190)
    left, right = 86, w - 14
    top = 11
    row_h = max(13, min(17, int((h - 22) / 12)))
    amp = max(5, min(8, row_h - 6))
    hist = getattr(self.bus, "history", [])[-2500:]

    # Tło i pionowe kreski czasu.
    for t in range(6):
        x = left + t * ((right - left) / 5)
        canvas.create_line(x, top - 3, x, top + row_h * 12 + 2, fill="#162129")

    for idx, (axis, kind, names, color) in enumerate(_AXIS_TIMELINE_ROWS_V12):
        y = top + idx * row_h + row_h // 2
        label = f"{axis} {kind}"
        canvas.create_text(7, y, text=label, anchor="w", fill=COLORS["text"], font=("Segoe UI", 7, "bold"))
        canvas.create_line(left, y, right, y, fill="#22313a")

        filtered = _history_points_for_signal_v12(hist, names, max_points=190)
        points = []
        if filtered:
            step_x = max(1, (right - left) / max(1, len(filtered) - 1))
            for i, item in enumerate(filtered):
                val = 1 if item.get("value") else 0
                x = left + i * step_x
                points.append((x, y - amp if val else y))
        else:
            # Brak historii: pokaż aktualny stan jako płaską linię, bez sztucznego przebiegu.
            sig = _first_existing_or_first_v12(self, names)
            try:
                val = 1 if self.bus.get(sig) else 0
            except Exception:
                val = 0
            points = [(left, y - amp if val else y), (right, y - amp if val else y)]

        if len(points) == 1:
            points.append((right, points[0][1]))

        for a, b in zip(points, points[1:]):
            canvas.create_line(a[0], a[1], b[0], a[1], fill=color, width=2)
            canvas.create_line(b[0], a[1], b[0], b[1], fill=color, width=2)

    canvas.create_text(left, h - 8, text="historia sygnałów z SignalBus / TAKE", anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7))


_prev_on_state_change_v12 = TarzanParPanels.on_state_change

def _par_on_state_change_v12(self, name, state):
    _prev_on_state_change_v12(self, name, state)
    try:
        # Odświeżaj podgląd tylko dla sygnałów osi, aby timeline żył podczas PLAY, bez przebudowy całego UI.
        for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS_V12:
            if name in names:
                self.draw_timeline()
                break
    except Exception:
        pass

TarzanParPanels.timeline = _par_timeline_v12
TarzanParPanels.draw_timeline = _par_draw_timeline_v12
TarzanParPanels.on_state_change = _par_on_state_change_v12


# --- 3. XYZ: większy prawy margines i ciut bezpieczniejsze rozmieszczenie wartości ---
def _par_level_xyz_panel_v12(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas_w, canvas_h = 120, 82
    canvas = tk.Canvas(wrap, width=canvas_w, height=canvas_h, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 8), pady=1)

    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True, padx=(0, 7))

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 100) or 100),
    }
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def calc_z(x, y):
        import math
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def draw():
        canvas.delete("all")
        w, h = canvas_w, canvas_h
        cx, cy = w / 2, h / 2
        x, y, z = clamp(state["x"]), clamp(state["y"]), clamp(state["z"])
        canvas.create_line(8, cy, w - 8, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 7, cx, h - 7, fill="#31414a", width=1)
        canvas.create_polygon(
            24 + x * 0.07, 24 - y * 0.07,
            w - 24 + x * 0.07, 25 + y * 0.07,
            w - 25 - x * 0.07, h - 21 + y * 0.07,
            25 - x * 0.07, h - 22 - y * 0.07,
            fill="#0d222c", outline="#386271", width=2,
        )
        px = cx + x / 100.0 * 38
        py = cy - y / 100.0 * 27
        size = 6 + max(0, z) / 100.0 * 3
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        canvas.create_text(7, 5, text="XY", fill=COLORS["muted"], anchor="w", font=("Segoe UI", 7, "bold"))
        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_values(x=None, y=None, z=None, publish_signals=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        else:
            state["z"] = calc_z(state["x"], state["y"])
        if publish_signals:
            publish()
        draw()

    def nudge(axis, delta):
        key = axis.lower()
        if axis == "Z":
            set_values(z=state["z"] + delta)
        else:
            set_values(**{key: state[key] + delta})

    def zero_axis(axis):
        if axis == "X":
            set_values(x=0)
        elif axis == "Y":
            set_values(y=0)
        else:
            set_values(x=0, y=0)

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=0)
        tk.Label(
            row,
            textvariable=vars_by_axis[axis],
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            width=7,
        ).pack(side="left", padx=(0, 4))
        for text, cmd in [
            ("−", lambda a=axis: nudge(a, -1)),
            ("+", lambda a=axis: nudge(a, 1)),
            ("0", lambda a=axis: zero_axis(a)),
        ]:
            tk.Button(
                row,
                text=text,
                width=2,
                bg=COLORS["button"],
                fg=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 7, "bold"),
                command=cmd,
            ).pack(side="right", padx=(1, 0))

    def drag(event):
        set_values(x=(event.x - canvas_w / 2) / 38 * 100, y=-(event.y - canvas_h / 2) / 27 * 100)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_values(z=v, publish_signals=False))
    return panel

TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v12

# =====================================================================
# KOREKTA PAR v13 — TIMELINE BEZ ZAPYCHANIA TKINTERA
# =====================================================================
# Zakres: tylko PAR / podgląd timeline. Bez EHR, Projektanta i generatora TAKE.
# Timeline v12 rysował canvas natychmiast po każdej zmianie STEP/DIR.
# Przy PLAY z wielu osi robiło to lawinę canvas.delete/create. v13 zbiera zmiany
# i rysuje maksymalnie raz na okno czasowe.

_TIMELINE_DEBOUNCE_MS_V13 = 80
_TIMELINE_HISTORY_LIMIT_V13 = 600
_TIMELINE_POINTS_LIMIT_V13 = 140


def _par_schedule_timeline_redraw_v13(self):
    canvas = getattr(self, "timeline_canvas", None)
    if not canvas:
        return
    app = getattr(self, "app", None)
    if app is None:
        try:
            self.draw_timeline()
        except Exception:
            pass
        return
    if getattr(self, "_timeline_after_id_v13", None):
        return

    def _do_redraw():
        self._timeline_after_id_v13 = None
        try:
            self.draw_timeline()
        except Exception:
            pass

    try:
        self._timeline_after_id_v13 = app.after(_TIMELINE_DEBOUNCE_MS_V13, _do_redraw)
    except Exception:
        self._timeline_after_id_v13 = None


def _par_draw_timeline_v13(self):
    canvas = getattr(self, "timeline_canvas", None)
    if not canvas:
        return
    canvas.delete("all")
    w = max(canvas.winfo_width(), 760)
    h = max(canvas.winfo_height(), 190)
    left, right = 86, w - 14
    top = 11
    row_h = max(13, min(17, int((h - 22) / 12)))
    amp = max(5, min(8, row_h - 6))
    hist = getattr(self.bus, "history", [])[-_TIMELINE_HISTORY_LIMIT_V13:]

    buckets = {tuple(names): [] for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS_V12}
    name_to_bucket = {}
    for key in buckets:
        for n in key:
            name_to_bucket[n] = key
    for item in hist:
        key = name_to_bucket.get(item.get("name"))
        if key is not None:
            buckets[key].append(item)

    for t in range(6):
        x = left + t * ((right - left) / 5)
        canvas.create_line(x, top - 3, x, top + row_h * 12 + 2, fill="#162129")

    for idx, (axis, kind, names, color) in enumerate(_AXIS_TIMELINE_ROWS_V12):
        y = top + idx * row_h + row_h // 2
        canvas.create_text(7, y, text=f"{axis} {kind}", anchor="w", fill=COLORS["text"], font=("Segoe UI", 7, "bold"))
        canvas.create_line(left, y, right, y, fill="#22313a")

        filtered = buckets.get(tuple(names), [])[-_TIMELINE_POINTS_LIMIT_V13:]
        points = []
        if filtered:
            step_x = max(1, (right - left) / max(1, len(filtered) - 1))
            for i, item in enumerate(filtered):
                val = 1 if item.get("value") else 0
                x = left + i * step_x
                points.append((x, y - amp if val else y))
        else:
            sig = _first_existing_or_first_v12(self, names)
            try:
                val = 1 if self.bus.get(sig) else 0
            except Exception:
                val = 0
            points = [(left, y - amp if val else y), (right, y - amp if val else y)]

        if len(points) == 1:
            points.append((right, points[0][1]))

        for a, b in zip(points, points[1:]):
            canvas.create_line(a[0], a[1], b[0], a[1], fill=color, width=2)
            canvas.create_line(b[0], a[1], b[0], b[1], fill=color, width=2)

    canvas.create_text(left, h - 8, text="historia SignalBus / TAKE — redraw zbiorczy", anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7))


def _par_timeline_v13(self, parent):
    panel = self.panel("timeline", parent, "PODGLĄD SYGNAŁÓW SILNIKÓW — STEP / DIR")
    top = tk.Frame(panel.body, bg=COLORS["panel"])
    top.pack(fill="x")
    tk.Label(top, text="Wszystkie osie: 12 przebiegów STEP/DIR", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8, "bold")).pack(side="left")
    tk.Button(top, text="CLEAR", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: (self.bus.history.clear(), self.draw_timeline())).pack(side="right", padx=4)
    canvas = tk.Canvas(panel.body, bg="#070b0e", height=210, highlightthickness=0)
    canvas.pack(fill="both", expand=True, pady=(4, 2))
    self.timeline_canvas = canvas
    self._timeline_after_id_v13 = None
    canvas.bind("<Configure>", lambda _e: self._schedule_timeline_redraw())
    self.draw_timeline()
    return panel


def _par_on_state_change_v13(self, name, state):
    # Kopia logiki v12 bez natychmiastowego self.draw_timeline().
    try:
        _prev_on_state_change_v12(self, name, state)
    except Exception:
        pass
    try:
        for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS_V12:
            if name in names:
                self._schedule_timeline_redraw()
                break
    except Exception:
        pass


TarzanParPanels._schedule_timeline_redraw = _par_schedule_timeline_redraw_v13
TarzanParPanels.timeline = _par_timeline_v13
TarzanParPanels.draw_timeline = _par_draw_timeline_v13
TarzanParPanels.on_state_change = _par_on_state_change_v13

# =====================================================================
# TARZAN PAR — KOREKTY v14 wg uwag użytkownika
# Zakres: tylko PAR / okna osi / timeline.
# 1) Oś pionowa ramienia: regulator masy jako dwie diody przy STEP/DIR/EN.
#    Usunięty panel/pasek regulatora masy pod silnikiem.
# 2) Timeline: etykiety osi zastąpione ikonami 64 px z img/axes, przebiegi STEP/DIR zostają kwadratowe.
# =====================================================================

_AXIS_ICON_NAMES_V14 = {
    "ARM_H": "oś pozioma ramienia",
    "ARM_V": "oś pionowa ramienia",
    "CAM_H": "oś pozioma kamery",
    "CAM_V": "oś pionowa kamery",
    "CAM_T": "oś pochyłu kamery",
    "CAM_F": "oś ostrości kamery",
}

_prev_axes_v14 = TarzanParPanels.axes

class _ParMassLedV14(tk.Canvas):
    def __init__(self, parent, label: str, color_on: str, size: int = 24):
        super().__init__(parent, width=size, height=size, bg=COLORS["panel3"], highlightthickness=0, bd=0)
        self.size = size
        self.label = label
        self.color_on = color_on
        self.color_off = "#2a3238"
        self.border_off = "#52636d"
        self.border_on = color_on
        self.value = 0
        self.draw()

    def set(self, value):
        self.value = 1 if value else 0
        self.draw()

    def draw(self):
        self.delete("all")
        fill = self.color_on if self.value else self.color_off
        border = self.border_on if self.value else self.border_off
        self.create_rectangle(2, 2, self.size - 2, self.size - 2, fill="#0c1217", outline=border, width=2)
        self.create_rectangle(6, 6, self.size - 6, self.size - 6, fill=fill, outline="")


def _par_add_mass_led_box_v14(parent, label: str, color: str):
    box = tk.Frame(parent, bg=COLORS["panel3"])
    box.pack(side="left", fill="x", expand=True)
    tk.Label(
        box,
        text=label,
        bg=COLORS["panel3"],
        fg=color,
        font=("Segoe UI", 8, "bold"),
    ).pack()
    led = _ParMassLedV14(box, label=label, color_on=color, size=26)
    led.pack(pady=2)
    return led


def _par_axes_v14(self, parent):
    panel = _prev_axes_v14(self, parent)
    try:
        card = self.axis_cards.get("ARM_V")
        if not card:
            return panel

        # Usuń wszystkie stare panele/paski regulatora masy spod silnika.
        for child in list(card.winfo_children()):
            if (
                getattr(child, "_tarzan_mass_bar_v11", False)
                or getattr(child, "_tarzan_mass_bar_v12", False)
                or getattr(child, "_mass_compensation_marks_v10", False)
            ):
                child.destroy()
                continue
            try:
                texts = []
                for grand in child.winfo_children():
                    if isinstance(grand, tk.Label):
                        texts.append(str(grand.cget("text")))
                joined = " ".join(texts).upper()
                if "REGULATOR" in joined and "MAS" in joined:
                    child.destroy()
            except Exception:
                pass

        # Dodaj diody regulatora masy obok istniejących STEP/DIR/EN.
        if not getattr(card, "_tarzan_mass_leds_v14", False):
            try:
                led_row = card.en.master.master
            except Exception:
                led_row = None
            if led_row is not None:
                add_led = _par_add_mass_led_box_v14(led_row, "+MASA", COLORS["green"])
                rem_led = _par_add_mass_led_box_v14(led_row, "−MASA", COLORS["blue"])

                def update_mass_leds(_v=None):
                    add = bool(self.bus.get("par_mass_reg_limit_add") or self.bus.get("play_p13_mass_reg_limit_add"))
                    rem = bool(self.bus.get("par_mass_reg_limit_remove") or self.bus.get("play_p23_mass_reg_limit_remove"))
                    add_led.set(add)
                    rem_led.set(rem)

                card._mass_compensation_update_v14 = update_mass_leds
                card._tarzan_mass_leds_v14 = True
                self.rows["par_mass_reg_limit_add"] = _ParValueProxy(update_mass_leds)
                self.rows["par_mass_reg_limit_remove"] = _ParValueProxy(update_mass_leds)
                self.rows["play_p13_mass_reg_limit_add"] = _ParValueProxy(update_mass_leds)
                self.rows["play_p23_mass_reg_limit_remove"] = _ParValueProxy(update_mass_leds)
                update_mass_leds()
    except Exception:
        pass
    return panel


def _axis_icon_path_v14(axis_key: str):
    if not axis_icon:
        return None
    try:
        return axis_icon(_AXIS_ICON_NAMES_V14.get(axis_key, axis_key), size=64, state="active", ext="png")
    except Exception:
        return None


def _load_timeline_icon_v14(self, axis_key: str):
    if not hasattr(self, "_timeline_icon_cache_v14"):
        self._timeline_icon_cache_v14 = {}
    if axis_key in self._timeline_icon_cache_v14:
        return self._timeline_icon_cache_v14[axis_key]
    path = _axis_icon_path_v14(axis_key)
    photo = None
    if path:
        try:
            from pathlib import Path as _Path
            if _Path(path).exists():
                photo = tk.PhotoImage(file=str(path))
                # Jeśli asset nie jest dokładnie 64 px, zmniejsz bezpiecznie do ok. 32 px dla timeline.
                try:
                    if photo.width() > 36:
                        factor = max(1, int(round(photo.width() / 32)))
                        photo = photo.subsample(factor, factor)
                except Exception:
                    pass
        except Exception:
            photo = None
    self._timeline_icon_cache_v14[axis_key] = photo
    return photo


def _par_draw_timeline_v14(self):
    canvas = getattr(self, "timeline_canvas", None)
    if not canvas:
        return
    canvas.delete("all")
    w = max(canvas.winfo_width(), 760)
    h = max(canvas.winfo_height(), 190)
    # Większy lewy margines na ikonę osi; tekst osi usunięty.
    icon_x = 30
    kind_x = 60
    left, right = 88, w - 14
    top = 11
    row_h = max(13, min(17, int((h - 22) / 12)))
    amp = max(5, min(8, row_h - 6))
    hist = getattr(self.bus, "history", [])[-_TIMELINE_HISTORY_LIMIT_V13:]

    buckets = {tuple(names): [] for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS_V12}
    name_to_bucket = {}
    for key in buckets:
        for n in key:
            name_to_bucket[n] = key
    for item in hist:
        key = name_to_bucket.get(item.get("name"))
        if key is not None:
            buckets[key].append(item)

    for t in range(6):
        x = left + t * ((right - left) / 5)
        canvas.create_line(x, top - 3, x, top + row_h * 12 + 2, fill="#162129")

    for idx, (axis, kind, names, color) in enumerate(_AXIS_TIMELINE_ROWS_V12):
        y = top + idx * row_h + row_h // 2

        # Ikona osi na wspólnej etykiecie: pierwsza linia STEP dla osi dostaje ikonę na środku pary STEP/DIR.
        if kind == "STEP":
            icon = _load_timeline_icon_v14(self, axis)
            y_icon = y + row_h // 2
            if icon:
                canvas.create_image(icon_x, y_icon, image=icon, anchor="center")
            else:
                canvas.create_text(icon_x, y_icon, text=axis, anchor="center", fill=COLORS["muted"], font=("Segoe UI", 7, "bold"))

        # Zostaje tylko mały znacznik rodzaju przebiegu, bez długiego tekstu osi.
        canvas.create_text(kind_x, y, text="S" if kind == "STEP" else "D", anchor="center", fill=color, font=("Segoe UI", 7, "bold"))
        canvas.create_line(left, y, right, y, fill="#22313a")

        filtered = buckets.get(tuple(names), [])[-_TIMELINE_POINTS_LIMIT_V13:]
        points = []
        if filtered:
            step_x = max(1, (right - left) / max(1, len(filtered) - 1))
            for i, item in enumerate(filtered):
                val = 1 if item.get("value") else 0
                x = left + i * step_x
                points.append((x, y - amp if val else y))
        else:
            sig = _first_existing_or_first_v12(self, names)
            try:
                val = 1 if self.bus.get(sig) else 0
            except Exception:
                val = 0
            points = [(left, y - amp if val else y), (right, y - amp if val else y)]

        if len(points) == 1:
            points.append((right, points[0][1]))

        for a, b in zip(points, points[1:]):
            canvas.create_line(a[0], a[1], b[0], a[1], fill=color, width=2)
            canvas.create_line(b[0], a[1], b[0], b[1], fill=color, width=2)

    canvas.create_text(left, h - 8, text="historia SignalBus / TAKE — STEP i DIR wszystkich osi", anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7))


TarzanParPanels.axes = _par_axes_v14
TarzanParPanels.draw_timeline = _par_draw_timeline_v14

# =====================================================================
# TARZAN PAR — KOREKTY v15 wg uwag użytkownika
# Zakres: tylko PAR / TAKE panel / XYZ / ręczne STEP / timeline.
# 1) Oś ostrości: ręczne kroki lewo/prawo dopisują też właściwe sygnały focus i wirtualne TAKE_CAM_F.
# 2) XYZ: przycisk 0 zeruje wyłącznie swoją oś.
# 3) LOAD TAKE: jasny przycisk, opis TAKE wycentrowany i większy.
# 4) Timeline: czerwona linia środka oraz H/L dla STEP i DIR przy każdej linii.
# =====================================================================

_prev_manual_axis_step_v15 = TarzanParPanels._manual_axis_step
_prev_level_xyz_panel_v15 = TarzanParPanels.level_xyz_panel


def _par_take_panel_v15(self, parent):
    panel = self.panel("take", parent, "TAKE — ODTWARZACZ PROTOKOŁU")
    top = tk.Frame(panel.body, bg=COLORS["panel"])
    top.pack(fill="x")
    tk.Button(
        top,
        text="LOAD TAKE",
        bg="#d7dde2",
        fg="#101820",
        activebackground="#eef2f5",
        activeforeground="#101820",
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        command=self.app.load_take_dialog,
    ).pack(side="left", padx=3, pady=2)
    for txt, cmd in [
        ("PLAY", self.app.play_take),
        ("PAUSE", self.app.pause_take),
        ("STOP", self.app.stop_take),
    ]:
        tk.Button(top, text=txt, bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=cmd).pack(side="left", padx=3, pady=2)
    self.app.take_label = tk.Label(
        panel.body,
        text="TAKE: brak",
        bg=COLORS["panel"],
        fg=COLORS["text"],
        anchor="center",
        justify="center",
        font=("Segoe UI", 12, "bold"),
    )
    self.app.take_label.pack(fill="x", pady=8)
    return panel


# Właściwe sygnały focus z mapy sprzętowej. Starsze wpisy cnc_z_cam_f_* zostają obsłużone,
# ale manualny krok musi na pewno trafiać w cnc_z_focus_* i rec_*_focus.
_FOCUS_MANUAL_PATCH_V15 = {
    "CAM_F": {
        "step": ["TAKE_CAM_F_STEP", "cnc_z_focus_ctr", "rec_p05_copy_ctr_focus", "cnc_z_cam_f_ctr", "rec_p07_copy_ctr_cam_f"],
        "dir": ["TAKE_CAM_F_DIR", "cnc_z_focus_dir", "rec_p07_copy_dir_focus", "cnc_z_cam_f_dir", "rec_p07_copy_dir_cam_f"],
    }
}


def _par_manual_axis_step_v15(self, axis: str, direction: int):
    bind = dict(AXIS_SIGNAL_BINDINGS.get(axis, {}))
    if axis in _FOCUS_MANUAL_PATCH_V15:
        patched = _FOCUS_MANUAL_PATCH_V15[axis]
        bind["step"] = list(dict.fromkeys(list(patched.get("step", [])) + list(bind.get("step", []))))
        bind["dir"] = list(dict.fromkeys(list(patched.get("dir", [])) + list(bind.get("dir", []))))

    # DIR: sygnały wirtualne TAKE_* tworzymy nawet jeśli jeszcze nie istniały,
    # realne sygnały piszemy tylko jeśli są w mapie albo są TAKE_*.
    for name in bind.get("dir", []):
        if name.startswith("TAKE_") or self.bus.exists(name):
            self.bus.force_signal(name, int(direction), source="PAR_AXIS_STEP")
    for name in bind.get("en", []):
        if name.startswith("TAKE_") or self.bus.exists(name):
            self.bus.force_signal(name, 1, source="PAR_AXIS_STEP")
    for name in bind.get("step", []):
        if name.startswith("TAKE_") or self.bus.exists(name):
            self.bus.force_signal(name, 1, source="PAR_AXIS_STEP")
            try:
                self.app.after(70, lambda n=name: self.bus.force_signal(n, 0, source="PAR_AXIS_STEP"))
            except Exception:
                pass


def _par_level_xyz_panel_v15(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=138, height=94, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 9), pady=1)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 100) or 100),
    }
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def calc_z(x, y):
        import math
        r2 = min(10000.0, float(x) * float(x) + float(y) * float(y))
        return math.sqrt(max(0.0, 10000.0 - r2))

    def publish():
        _par_set_signal(self, "par_level_x", state["x"], "PAR_XYZ")
        _par_set_signal(self, "par_level_y", state["y"], "PAR_XYZ")
        _par_set_signal(self, "par_level_z", state["z"], "PAR_XYZ")

    def draw():
        canvas.delete("all")
        w, h = 138, 94
        cx, cy = w / 2, h / 2
        x, y, z = clamp(state["x"]), clamp(state["y"]), clamp(state["z"])
        canvas.create_line(9, cy, w - 9, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 8, cx, h - 8, fill="#31414a", width=1)
        canvas.create_polygon(
            28 + x * 0.08, 28 - y * 0.08,
            w - 28 + x * 0.08, 30 + y * 0.08,
            w - 30 - x * 0.08, h - 24 + y * 0.08,
            30 - x * 0.08, h - 26 - y * 0.08,
            fill="#0d222c", outline="#386271", width=2,
        )
        px = cx + x / 100.0 * 44
        py = cy - y / 100.0 * 31
        size = 7 + max(0, z) / 100.0 * 3
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_values(x=None, y=None, z=None, publish_signals=True, recalc_z=True):
        if x is not None:
            state["x"] = clamp(x)
        if y is not None:
            state["y"] = clamp(y)
        if z is not None:
            state["z"] = clamp(z)
        elif recalc_z:
            state["z"] = calc_z(state["x"], state["y"])
        if publish_signals:
            publish()
        draw()

    def nudge(axis, delta):
        key = axis.lower()
        if axis == "Z":
            set_values(z=state["z"] + delta, recalc_z=False)
        else:
            set_values(**{key: state[key] + delta})

    def zero_axis(axis):
        # Każde 0 zeruje tylko własną wartość, bez zerowania pozostałych osi.
        if axis == "X":
            set_values(x=0)
        elif axis == "Y":
            set_values(y=0)
        else:
            set_values(z=0, recalc_z=False)

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=0)
        tk.Label(
            row,
            textvariable=vars_by_axis[axis],
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            width=6,
        ).pack(side="left")
        for text, cmd in [
            ("−", lambda a=axis: nudge(a, -1)),
            ("+", lambda a=axis: nudge(a, 1)),
            ("0", lambda a=axis: zero_axis(a)),
        ]:
            tk.Button(
                row,
                text=text,
                width=2,
                bg=COLORS["button"],
                fg=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 7, "bold"),
                command=cmd,
            ).pack(side="right", padx=(1, 0))

    def drag(event):
        set_values(x=(event.x - 69) / 44 * 100, y=-(event.y - 47) / 31 * 100)

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    set_values(state["x"], state["y"], publish_signals=False)
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_values(x=v, publish_signals=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_values(y=v, publish_signals=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_values(z=v, publish_signals=False, recalc_z=False))
    return panel


# CAM_F w timeline też musi widzieć realne sygnały focus używane przy ręcznym kroku.
_AXIS_TIMELINE_ROWS_V15 = []
for axis, kind, names, color in _AXIS_TIMELINE_ROWS_V12:
    names = list(names)
    if axis == "CAM_F" and kind == "STEP":
        names = list(dict.fromkeys(names + ["cnc_z_focus_ctr", "rec_p05_copy_ctr_focus"]))
    if axis == "CAM_F" and kind == "DIR":
        names = list(dict.fromkeys(names + ["cnc_z_focus_dir", "rec_p07_copy_dir_focus"]))
    _AXIS_TIMELINE_ROWS_V15.append((axis, kind, names, color))


def _timeline_current_value_v15(self, names):
    for sig in names:
        try:
            if self.bus.exists(sig):
                return 1 if self.bus.get(sig) else 0
        except Exception:
            pass
    try:
        return 1 if self.bus.get(names[0]) else 0
    except Exception:
        return 0


def _par_draw_timeline_v15(self):
    canvas = getattr(self, "timeline_canvas", None)
    if not canvas:
        return
    canvas.delete("all")
    w = max(canvas.winfo_width(), 760)
    h = max(canvas.winfo_height(), 190)
    icon_x = 30
    kind_x = 58
    hl_x = 73
    left, right = 96, w - 14
    top = 11
    row_h = max(13, min(17, int((h - 22) / 12)))
    amp = max(5, min(8, row_h - 6))
    hist = getattr(self.bus, "history", [])[-_TIMELINE_HISTORY_LIMIT_V13:]

    buckets = {tuple(names): [] for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS_V15}
    name_to_bucket = {}
    for key in buckets:
        for n in key:
            name_to_bucket[n] = key
    for item in hist:
        key = name_to_bucket.get(item.get("name"))
        if key is not None:
            buckets[key].append(item)

    mid_x = left + (right - left) / 2
    for t in range(6):
        x = left + t * ((right - left) / 5)
        canvas.create_line(x, top - 3, x, top + row_h * 12 + 2, fill="#162129")
    canvas.create_line(mid_x, top - 5, mid_x, top + row_h * 12 + 4, fill="#ff2b22", width=1)

    for idx, (axis, kind, names, color) in enumerate(_AXIS_TIMELINE_ROWS_V15):
        y = top + idx * row_h + row_h // 2

        if kind == "STEP":
            icon = _load_timeline_icon_v14(self, axis)
            y_icon = y + row_h // 2
            if icon:
                canvas.create_image(icon_x, y_icon, image=icon, anchor="center")
            else:
                canvas.create_text(icon_x, y_icon, text=axis, anchor="center", fill=COLORS["muted"], font=("Segoe UI", 7, "bold"))

        cur = _timeline_current_value_v15(self, names)
        canvas.create_text(kind_x, y, text="S" if kind == "STEP" else "D", anchor="center", fill=color, font=("Segoe UI", 7, "bold"))
        canvas.create_text(hl_x, y, text="H" if cur else "L", anchor="center", fill=color if cur else COLORS["muted"], font=("Segoe UI", 7, "bold"))
        canvas.create_line(left, y, right, y, fill="#22313a")

        filtered = buckets.get(tuple(names), [])[-_TIMELINE_POINTS_LIMIT_V13:]
        points = []
        if filtered:
            step_x = max(1, (right - left) / max(1, len(filtered) - 1))
            for i, item in enumerate(filtered):
                val = 1 if item.get("value") else 0
                x = left + i * step_x
                points.append((x, y - amp if val else y))
        else:
            val = cur
            points = [(left, y - amp if val else y), (right, y - amp if val else y)]

        if len(points) == 1:
            points.append((right, points[0][1]))

        for a, b in zip(points, points[1:]):
            canvas.create_line(a[0], a[1], b[0], a[1], fill=color, width=2)
            canvas.create_line(b[0], a[1], b[0], b[1], fill=color, width=2)

    canvas.create_text(left, h - 8, text="czerwona linia = chwila odczytu; H/L = aktualny stan STEP/DIR", anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7))


TarzanParPanels.take = _par_take_panel_v15
TarzanParPanels._manual_axis_step = _par_manual_axis_step_v15
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v15
TarzanParPanels.draw_timeline = _par_draw_timeline_v15

# =====================================================================
# TARZAN PAR — KOREKTY v16 wg uwag użytkownika
# Zakres: tylko PAR / podgląd sygnałów silników / CZUJNIK POZIOMU XYZ.
# 1) H/L w timeline: L szary, H czerwony.
# 2) Timeline: luźniejszy pion, delikatna linia rozdzielająca każdą oś.
# 3) XYZ: przyciski + / - / 0 każdej osi zmieniają tylko własną wartość.
# =====================================================================

_TIMELINE_H_COLOR_V16 = COLORS.get("red", "#ff2b22")
_TIMELINE_L_COLOR_V16 = COLORS.get("muted", "#a9b5bd")


def _par_draw_timeline_v16(self):
    canvas = getattr(self, "timeline_canvas", None)
    if not canvas:
        return
    canvas.delete("all")
    w = max(canvas.winfo_width(), 760)
    h = max(canvas.winfo_height(), 210)
    icon_x = 30
    kind_x = 58
    hl_x = 75
    left, right = 100, w - 14
    top = 12
    # v16: skoro w layout dodany jest wiersz, nie ściskamy przebiegów do 17 px.
    row_h = max(15, min(22, int((h - 28) / 12)))
    amp = max(5, min(9, row_h - 7))
    total_h = row_h * 12
    hist = getattr(self.bus, "history", [])[-_TIMELINE_HISTORY_LIMIT_V13:]

    buckets = {tuple(names): [] for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS_V15}
    name_to_bucket = {}
    for key in buckets:
        for n in key:
            name_to_bucket[n] = key
    for item in hist:
        key = name_to_bucket.get(item.get("name"))
        if key is not None:
            buckets[key].append(item)

    mid_x = left + (right - left) / 2
    for t in range(6):
        x = left + t * ((right - left) / 5)
        canvas.create_line(x, top - 3, x, top + total_h + 2, fill="#162129")
    canvas.create_line(mid_x, top - 5, mid_x, top + total_h + 4, fill="#ff2b22", width=1)

    for idx, (axis, kind, names, color) in enumerate(_AXIS_TIMELINE_ROWS_V15):
        y = top + idx * row_h + row_h // 2

        # Delikatny separator po każdej osi, czyli po parze STEP/DIR.
        if idx % 2 == 0:
            sep_y = top + idx * row_h - 2
            canvas.create_line(8, sep_y, right, sep_y, fill="#111b22")

        if kind == "STEP":
            icon = _load_timeline_icon_v14(self, axis)
            y_icon = y + row_h // 2
            if icon:
                canvas.create_image(icon_x, y_icon, image=icon, anchor="center")
            else:
                canvas.create_text(icon_x, y_icon, text=axis, anchor="center", fill=COLORS["muted"], font=("Segoe UI", 7, "bold"))

        cur = _timeline_current_value_v15(self, names)
        canvas.create_text(kind_x, y, text="S" if kind == "STEP" else "D", anchor="center", fill=color, font=("Segoe UI", 8, "bold"))
        canvas.create_text(
            hl_x,
            y,
            text="H" if cur else "L",
            anchor="center",
            fill=_TIMELINE_H_COLOR_V16 if cur else _TIMELINE_L_COLOR_V16,
            font=("Segoe UI", 8, "bold"),
        )
        canvas.create_line(left, y, right, y, fill="#22313a")

        filtered = buckets.get(tuple(names), [])[-_TIMELINE_POINTS_LIMIT_V13:]
        points = []
        if filtered:
            step_x = max(1, (right - left) / max(1, len(filtered) - 1))
            for i, item in enumerate(filtered):
                val = 1 if item.get("value") else 0
                x = left + i * step_x
                points.append((x, y - amp if val else y))
        else:
            val = cur
            points = [(left, y - amp if val else y), (right, y - amp if val else y)]

        if len(points) == 1:
            points.append((right, points[0][1]))

        for a, b in zip(points, points[1:]):
            canvas.create_line(a[0], a[1], b[0], a[1], fill=color, width=2)
            canvas.create_line(b[0], a[1], b[0], b[1], fill=color, width=2)

    bottom_y = top + total_h + 8
    if bottom_y < h:
        canvas.create_text(left, h - 8, text="czerwona linia = chwila odczytu; H/L = aktualny stan STEP/DIR", anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7))


def _par_level_xyz_panel_v16(self, parent):
    panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ — MMA7660")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrap, width=138, height=94, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
    canvas.pack(side="left", padx=(0, 9), pady=1)
    side = tk.Frame(wrap, bg=COLORS["panel"])
    side.pack(side="left", fill="both", expand=True)

    state = {
        "x": float(self.bus.get("par_level_x", 0) or 0),
        "y": float(self.bus.get("par_level_y", 0) or 0),
        "z": float(self.bus.get("par_level_z", 100) or 100),
    }
    vars_by_axis = {axis: tk.StringVar(value=f"{axis} +0") for axis in ("X", "Y", "Z")}

    def clamp(v):
        try:
            return max(-100.0, min(100.0, float(v)))
        except Exception:
            return 0.0

    def publish_axis(axis_key: str):
        sig = {
            "x": "par_level_x",
            "y": "par_level_y",
            "z": "par_level_z",
        }.get(axis_key)
        if sig:
            _par_set_signal(self, sig, state[axis_key], "PAR_XYZ")

    def publish_all():
        publish_axis("x")
        publish_axis("y")
        publish_axis("z")

    def draw():
        canvas.delete("all")
        w0, h0 = 138, 94
        cx, cy = w0 / 2, h0 / 2
        x, y, z = clamp(state["x"]), clamp(state["y"]), clamp(state["z"])
        canvas.create_line(9, cy, w0 - 9, cy, fill="#31414a", width=1)
        canvas.create_line(cx, 8, cx, h0 - 8, fill="#31414a", width=1)
        canvas.create_polygon(
            28 + x * 0.08, 28 - y * 0.08,
            w0 - 28 + x * 0.08, 30 + y * 0.08,
            w0 - 30 - x * 0.08, h0 - 24 + y * 0.08,
            30 - x * 0.08, h0 - 26 - y * 0.08,
            fill="#0d222c", outline="#386271", width=2,
        )
        px = cx + x / 100.0 * 44
        py = cy - y / 100.0 * 31
        size = 7 + max(0, z) / 100.0 * 3
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=COLORS["green"], outline="#061006")
        vars_by_axis["X"].set(f"X {int(round(x)):+d}")
        vars_by_axis["Y"].set(f"Y {int(round(y)):+d}")
        vars_by_axis["Z"].set(f"Z {int(round(z)):+d}")

    def set_axis(axis: str, value, publish_signal=True):
        key = axis.lower()
        if key not in state:
            return
        state[key] = clamp(value)
        if publish_signal:
            publish_axis(key)
        draw()

    def nudge(axis: str, delta: int):
        key = axis.lower()
        # v16: przycisk przy X zmienia tylko X; przy Y tylko Y; przy Z tylko Z.
        set_axis(axis, state[key] + delta, publish_signal=True)

    def zero_axis(axis: str):
        # v16: zero przy osi zeruje tylko własną linię/wartość.
        set_axis(axis, 0, publish_signal=True)

    for axis in ("X", "Y", "Z"):
        row = tk.Frame(side, bg=COLORS["panel"])
        row.pack(fill="x", pady=0)
        tk.Label(
            row,
            textvariable=vars_by_axis[axis],
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            width=6,
        ).pack(side="left")
        for text, cmd in [
            ("−", lambda a=axis: nudge(a, -1)),
            ("+", lambda a=axis: nudge(a, 1)),
            ("0", lambda a=axis: zero_axis(a)),
        ]:
            tk.Button(
                row,
                text=text,
                width=2,
                bg=COLORS["button"],
                fg=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 7, "bold"),
                command=cmd,
            ).pack(side="right", padx=(1, 0))

    def calc_z_from_xy(x, y):
        import math
        x = clamp(x)
        y = clamp(y)
        r2 = min(10000.0, x * x + y * y)
        return clamp(math.sqrt(max(0.0, 10000.0 - r2)))

    def drag(event):
        state["x"] = clamp((event.x - 69) / 44 * 100)
        state["y"] = clamp(-(event.y - 47) / 31 * 100)
        state["z"] = calc_z_from_xy(state["x"], state["y"])
        publish_all()
        draw()

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    draw()
    # v16: zewnętrzna aktualizacja pojedynczego sygnału też nie przelicza ani nie publikuje innych osi.
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_axis("X", v, publish_signal=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_axis("Y", v, publish_signal=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_axis("Z", v, publish_signal=False))
    return panel


TarzanParPanels.draw_timeline = _par_draw_timeline_v16
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_v16
