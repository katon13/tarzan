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


class _RowRegistry(dict):
    def __setitem__(self, key, value):
        if key in self:
            current = dict.__getitem__(self, key)
            if isinstance(current, list):
                current.append(value)
                dict.__setitem__(self, key, current)
            else:
                dict.__setitem__(self, key, [current, value])
            return
        dict.__setitem__(self, key, value)

    def set_value(self, key, value):
        current = dict.get(self, key)
        if current is None:
            return
        if isinstance(current, list):
            for proxy in list(current):
                try:
                    proxy.set(value)
                except Exception:
                    pass
            return
        try:
            current.set(value)
        except Exception:
            pass


class TarzanParPanels:
    def __init__(self, app, bus: TarzanSignalBus) -> None:
        self.app = app
        self.bus = bus
        self.rows: Dict[str, SignalRow] = _RowRegistry()
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

        def _on_mousewheel(event):
            try:
                if getattr(event, 'delta', 0):
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
                elif getattr(event, 'num', None) == 4:
                    canvas.yview_scroll(-1, 'units')
                elif getattr(event, 'num', None) == 5:
                    canvas.yview_scroll(1, 'units')
            except Exception:
                pass

        def _bind_mousewheel(_event=None):
            for widget in (canvas, inner):
                widget.bind_all('<MouseWheel>', _on_mousewheel, add='+')
                widget.bind_all('<Button-4>', _on_mousewheel, add='+')
                widget.bind_all('<Button-5>', _on_mousewheel, add='+')

        def _unbind_mousewheel(_event=None):
            for sequence in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                try:
                    canvas.unbind_all(sequence)
                except Exception:
                    pass

        canvas.bind('<Enter>', _bind_mousewheel, add='+')
        inner.bind('<Enter>', _bind_mousewheel, add='+')
        canvas.bind('<Leave>', _unbind_mousewheel, add='+')
        inner.bind('<Leave>', _unbind_mousewheel, add='+')

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
            self.rows.set_value(name, state.value)
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


_PAR_BURGUNDY = "#7a1630"



def _par_click_sensor_panel(self, parent, *, key, title, signal, on_text, off_text, extra=None, led_size=92, show_text=True):
    panel = self.panel(key, parent, title)
    state = {"value": 1 if self.bus.get(signal) else 0}
    led = tk.Canvas(panel.body, width=led_size, height=led_size, bg=COLORS["panel"], highlightthickness=0)
    led.pack(anchor="center", pady=(2, 5))
    label = None
    if show_text:
        label = tk.Label(panel.body, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10, "bold"))
        label.pack(fill="x")

    def draw(value=None):
        if value is not None:
            state["value"] = 1 if value else 0
        led.delete("all")
        color = COLORS["red"] if state["value"] else COLORS["green"]
        glow = "#5a1613" if state["value"] else "#134d16"
        outer_pad = max(4, int(led_size * 0.05))
        inner_pad = max(12, int(led_size * 0.17))
        led.create_oval(outer_pad, outer_pad, led_size - outer_pad, led_size - outer_pad, fill=glow, outline="")
        led.create_oval(inner_pad, inner_pad, led_size - inner_pad, led_size - inner_pad, fill=color, outline="#111", width=2)
        if label is not None:
            label.configure(text=on_text if state["value"] else off_text)

    def toggle(_event=None):
        new_value = 0 if state["value"] else 1
        _par_set_signal(self, signal, new_value, "PAR_SENSOR_CLICK")
        if extra:
            for name, val_fn in extra.items():
                _par_set_signal(self, name, val_fn(new_value), "PAR_SENSOR_CLICK")
        draw(new_value)

    led.bind("<Button-1>", toggle)
    if label is not None:
        label.bind("<Button-1>", toggle)
    draw()
    self.rows[signal] = _ParValueProxy(draw)
    return panel


def _par_canvas_sensor_slider_panel_final(self, parent, *, key, title, signal, unit, start, end, decimals=0):
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


def _par_light_bh1750_panel_final(self, parent):
    return _par_canvas_sensor_slider_panel_final(
        self, parent,
        key="light_bh1750",
        title="ŚWIATŁO BH1750",
        signal="par_bh1750_lux",
        unit="lx",
        start=0,
        end=120000,
        decimals=0,
    )


def _par_temperature_panel_final(self, parent):
    return _par_canvas_sensor_slider_panel_final(
        self, parent,
        key="temperature",
        title="TEMPERATURA",
        signal="par_temperature_c",
        unit="°C",
        start=-20,
        end=50,
        decimals=1,
    )


def _par_shock_sensor_panel_final(self, parent):
    return _par_click_sensor_panel(
        self,
        parent,
        key="shock_sensor_panel",
        title="SHOK",
        signal="par_shock_sensor_state",
        on_text="WSTRZĄS = 1",
        off_text="SPOKÓJ = 0",
        extra={"rec_p39_shock_sensor": lambda v: v},
        led_size=62,
        show_text=False,
    )


def _par_laser_panel_final(self, parent):
    return _par_click_sensor_panel(
        self,
        parent,
        key="laser",
        title="LASER",
        signal="par_laser_set",
        on_text="UTRACONA OŚ = 1",
        off_text="OŚ OK = 0",
        extra={
            "par_laser_error": lambda v: v,
            "par_laser_state_high": lambda v: v,
            "par_laser_state_low": lambda v: 0 if v else 1,
        },
        led_size=62,
        show_text=False,
    )


def _par_matrix_final(self, parent):
    panel = self.panel("matrix", parent, "MATRIX LED")
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


def _par_lcd_final(self, parent):
    panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602")
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


def _par_keyboard_final(self, parent):
    panel = self.panel("keyboard", parent, "KLAWIATURA")
    grid = tk.Frame(panel.body, bg=COLORS["panel"])
    grid.pack(anchor="center")
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for i, label in enumerate(keys):
        tk.Button(grid, text=label, bg="#202b33", fg=COLORS["text"], relief="flat", font=("Segoe UI", 12, "bold"), width=3, height=1, command=lambda k=label: self._log("KEYBOARD", f"KEY {k}")).grid(row=i // 3, column=i % 3, sticky="nsew", padx=3, pady=3)
    for i in range(3):
        grid.grid_columnconfigure(i, weight=1)
    return panel








def _par_lamp_panel_final(self, parent):
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



_AXIS_TIMELINE_ROWS = [
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
    ("CAM_F", "STEP", ["TAKE_CAM_F_STEP", "cnc_z_focus_ctr", "rec_p05_copy_ctr_focus", "cnc_z_cam_f_ctr", "rec_p07_copy_ctr_cam_f"], COLORS["green"]),
    ("CAM_F", "DIR",  ["TAKE_CAM_F_DIR",  "cnc_z_focus_dir", "rec_p07_copy_dir_focus", "cnc_z_cam_f_dir", "rec_p07_copy_dir_cam_f"], COLORS["blue"]),
]

_TIMELINE_DEBOUNCE_MS = 80
_TIMELINE_HISTORY_LIMIT = 600
_TIMELINE_POINTS_LIMIT = 140
_TIMELINE_H_COLOR = COLORS.get("red", "#ff2b22")
_TIMELINE_L_COLOR = COLORS.get("muted", "#a9b5bd")

_AXIS_ICON_NAMES = {
    "ARM_H": "oś pozioma ramienia",
    "ARM_V": "oś pionowa ramienia",
    "CAM_H": "oś pozioma kamery",
    "CAM_V": "oś pionowa kamery",
    "CAM_T": "oś pochyłu kamery",
    "CAM_F": "oś ostrości kamery",
}

_FOCUS_MANUAL_PATCH = {
    "CAM_F": {
        "step": ["TAKE_CAM_F_STEP", "cnc_z_focus_ctr", "rec_p05_copy_ctr_focus", "cnc_z_cam_f_ctr", "rec_p07_copy_ctr_cam_f"],
        "dir": ["TAKE_CAM_F_DIR", "cnc_z_focus_dir", "rec_p07_copy_dir_focus", "cnc_z_cam_f_dir", "rec_p07_copy_dir_cam_f"],
    }
}




def _axis_icon_path(axis_key: str):
    if not axis_icon:
        return None
    try:
        return axis_icon(_AXIS_ICON_NAMES.get(axis_key, axis_key), size=64, state="active", ext="png")
    except Exception:
        return None


def _load_timeline_icon(self, axis_key: str):
    if not hasattr(self, "_timeline_icon_cache"):
        self._timeline_icon_cache = {}
    if axis_key in self._timeline_icon_cache:
        return self._timeline_icon_cache[axis_key]
    path = _axis_icon_path(axis_key)
    photo = None
    if path:
        try:
            from pathlib import Path as _Path
            if _Path(path).exists():
                photo = tk.PhotoImage(file=str(path))
                try:
                    if photo.width() > 36:
                        factor = max(1, int(round(photo.width() / 32)))
                        photo = photo.subsample(factor, factor)
                except Exception:
                    pass
        except Exception:
            photo = None
    self._timeline_icon_cache[axis_key] = photo
    return photo


def _timeline_current_value(self, names):
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


def _schedule_timeline_redraw(self):
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
    if getattr(self, "_timeline_after_id", None):
        return

    def _do_redraw():
        self._timeline_after_id = None
        try:
            self.draw_timeline()
        except Exception:
            pass

    try:
        self._timeline_after_id = app.after(_TIMELINE_DEBOUNCE_MS, _do_redraw)
    except Exception:
        self._timeline_after_id = None
        _do_redraw()


def _par_timeline_final(self, parent):
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
    self._timeline_after_id = None
    canvas.bind("<Configure>", lambda _e: self._schedule_timeline_redraw())
    self.draw_timeline()
    return panel


def _par_draw_timeline_final(self):
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
    row_h = max(15, min(22, int((h - 28) / 12)))
    amp = max(5, min(9, row_h - 7))
    total_h = row_h * 12
    hist = getattr(self.bus, "history", [])[-_TIMELINE_HISTORY_LIMIT:]

    buckets = {tuple(names): [] for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS}
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

    for idx, (axis, kind, names, color) in enumerate(_AXIS_TIMELINE_ROWS):
        y = top + idx * row_h + row_h // 2
        if kind == "STEP":
            sep_y = max(top, y - row_h // 2)
            canvas.create_line(4, sep_y, right, sep_y, fill="#101a20")
            icon = _load_timeline_icon(self, axis)
            y_icon = y + row_h // 2
            if icon:
                canvas.create_image(icon_x, y_icon, image=icon, anchor="center")
            else:
                canvas.create_text(icon_x, y_icon, text=axis, anchor="center", fill=COLORS["muted"], font=("Segoe UI", 7, "bold"))

        cur = _timeline_current_value(self, names)
        canvas.create_text(kind_x, y, text="S" if kind == "STEP" else "D", anchor="center", fill=color, font=("Segoe UI", 7, "bold"))
        canvas.create_text(
            hl_x,
            y,
            text="H" if cur else "L",
            anchor="center",
            fill=_TIMELINE_H_COLOR if cur else _TIMELINE_L_COLOR,
            font=("Segoe UI", 7, "bold"),
        )
        canvas.create_line(left, y, right, y, fill="#22313a")

        filtered = buckets.get(tuple(names), [])[-_TIMELINE_POINTS_LIMIT:]
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
        canvas.create_text(
            left,
            h - 8,
            text="czerwona linia = chwila odczytu; H/L = aktualny stan STEP/DIR",
            anchor="w",
            fill=COLORS["muted"],
            font=("Segoe UI", 7),
        )




_base_axes = TarzanParPanels.axes
_base_on_state_change = TarzanParPanels.on_state_change


def _par_axes_final(self, parent):
    panel = _base_axes(self, parent)
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

    try:
        card = self.axis_cards.get("ARM_V")
        if not card:
            return panel
        if getattr(card, "_tarzan_mass_leds_final", False):
            return panel

        led_row = None
        try:
            led_row = card.en.master.master
        except Exception:
            pass
        if led_row is not None:
            add_led = _par_add_mass_led_box_v14(led_row, "+MASA", COLORS["green"])
            rem_led = _par_add_mass_led_box_v14(led_row, "−MASA", COLORS["blue"])

            def update_mass_leds(_v=None):
                add = bool(self.bus.get("par_mass_reg_limit_add") or self.bus.get("play_p13_mass_reg_limit_add"))
                rem = bool(self.bus.get("par_mass_reg_limit_remove") or self.bus.get("play_p23_mass_reg_limit_remove"))
                add_led.set(add)
                rem_led.set(rem)

            card._tarzan_mass_leds_final = True
            self.rows["par_mass_reg_limit_add"] = _ParValueProxy(update_mass_leds)
            self.rows["par_mass_reg_limit_remove"] = _ParValueProxy(update_mass_leds)
            self.rows["play_p13_mass_reg_limit_add"] = _ParValueProxy(update_mass_leds)
            self.rows["play_p23_mass_reg_limit_remove"] = _ParValueProxy(update_mass_leds)
            update_mass_leds()
    except Exception:
        pass
    return panel


def _par_refresh_axis_cards_final(self):
    for axis, card in self.axis_cards.items():
        bind = AXIS_SIGNAL_BINDINGS.get(axis, {})
        card.set_step(self._first_value(bind.get("step", [])))
        card.set_dir(self._first_value(bind.get("dir", [])))
        en_names = bind.get("en", [])
        card.set_en(self._first_value(en_names) if en_names else 1)
        card.set_end_left(self._first_value(bind.get("left", [])))
        card.set_end_right(self._first_value(bind.get("right", [])))

        def _mk_logger(axis_key, card_ref):
            def _logger():
                try:
                    self.bus.log("PAR_MOTOR", f"{axis_key}: DIR={1 if card_ref.dir.state else 0} STEP=01")
                except Exception:
                    pass
            return _logger
        card.on_motor_step_log = _mk_logger(axis, card)


def _par_on_state_change_final(self, name, state):
    _base_on_state_change(self, name, state)
    try:
        for _axis, _kind, names, _color in _AXIS_TIMELINE_ROWS:
            if name in names:
                self._schedule_timeline_redraw()
                break
    except Exception:
        pass


def _par_take_panel_final(self, parent):
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
        font=("Segoe UI", 11, "bold"),
    )
    self.app.take_label.pack(fill="x", pady=8)
    return panel


def _par_manual_axis_step_final(self, axis: str, direction: int):
    bind = dict(AXIS_SIGNAL_BINDINGS.get(axis, {}))
    if axis in _FOCUS_MANUAL_PATCH:
        patched = _FOCUS_MANUAL_PATCH[axis]
        bind["step"] = list(dict.fromkeys(list(patched.get("step", [])) + list(bind.get("step", []))))
        bind["dir"] = list(dict.fromkeys(list(patched.get("dir", [])) + list(bind.get("dir", []))))

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
    try:
        self.draw_timeline()
    except Exception:
        pass


def _par_level_xyz_panel_final(self, parent):
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

    def calc_z_from_xy(x, y):
        import math
        x = clamp(x)
        y = clamp(y)
        r2 = min(10000.0, x * x + y * y)
        return clamp(math.sqrt(max(0.0, 10000.0 - r2)))

    def publish_axis(axis_key: str):
        sig = {"x": "par_level_x", "y": "par_level_y", "z": "par_level_z"}.get(axis_key)
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
        set_axis(axis, state[key] + delta, publish_signal=True)

    def zero_axis(axis: str):
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

    def drag(event):
        state["x"] = clamp((event.x - 69) / 44 * 100)
        state["y"] = clamp(-(event.y - 47) / 31 * 100)
        state["z"] = calc_z_from_xy(state["x"], state["y"])
        publish_all()
        draw()

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    draw()
    self.rows["par_level_x"] = _ParValueProxy(lambda v: set_axis("X", v, publish_signal=False))
    self.rows["par_level_y"] = _ParValueProxy(lambda v: set_axis("Y", v, publish_signal=False))
    self.rows["par_level_z"] = _ParValueProxy(lambda v: set_axis("Z", v, publish_signal=False))
    return panel



# ---------------------------------------------------------------------
# Spójna logika LED wg mapy sygnałów:
# IN aktywny = klikalny w PAR; OUT = podgląd; F/RESERVED = fioletowy i zablokowany.
# ---------------------------------------------------------------------
def _par_signal_blocked(self, name: str) -> bool:
    meta = self.bus.get_meta(name)
    if not meta:
        return False
    try:
        return bool(meta.is_forbidden) or meta.typ in {"F", "RESERVED"} or meta.kierunek in {"F", "RESERVED"}
    except Exception:
        return meta.typ in {"F", "RESERVED"} or meta.kierunek in {"F", "RESERVED"}


def _par_signal_clickable_input(self, name: str) -> bool:
    meta = self.bus.get_meta(name)
    if not meta:
        return False
    return bool(getattr(meta, "is_input", False)) and not _par_signal_blocked(self, name)


def _par_signal_row(self, parent, name: str, label: str, *, icon: str = "", led_size: int = 22, source: str = "PAR"):
    blocked = _par_signal_blocked(self, name)
    command = (lambda n=name: self.bus.toggle_input(n, source=source)) if _par_signal_clickable_input(self, name) else None
    row = SignalRow(parent, label, self.bus.get(name), command=command, icon=icon, led_size=led_size, blocked=blocked)
    row.pack(fill="x", pady=1)
    self.rows[name] = row
    return row


def _par_sensors_led_logic_final(self, parent):
    panel = self.panel("sensors", parent, "CZUJNIKI / ANALOG / I2C / 1-WIRE")
    inner = self._scroll_body(panel)
    names = self._group_or_search("CZUJNIKI", ["sensor", "czujnik", "pot", "analog", "i2c", "1-wire", "wire"])
    for name in names:
        meta = self.bus.get_meta(name)
        if not meta:
            continue
        if getattr(meta, "is_analog", False) and not _par_signal_blocked(self, name):
            self._analog_row(inner, name, self.sensor_label(name))
        else:
            _par_signal_row(self, inner, name, self.sensor_label(name), icon="◈", led_size=22, source="PAR_SENSOR")
    if not names:
        tk.Label(inner, text="Brak czujników — sprawdź ładowanie pełnej mapy I/O.", bg=COLORS["panel"], fg=COLORS["red"]).pack(anchor="w")
    return panel


def _par_functions_panel_led_logic_final(self, parent):
    panel = self.panel("functions", parent, "FUNKCJE SPRZĘTOWE / REZERWY")
    inner = self._scroll_body(panel)
    names = []
    for name in self.bus.names():
        if _par_signal_blocked(self, name):
            names.append(name)
    for name in names:
        meta = self.bus.get_meta(name)
        label = f"{meta.plytka} {meta.pin or meta.kanal or '-'}  {name}" if meta else name
        _par_signal_row(self, inner, name, label, icon="🔒", led_size=22, source="PAR_BLOCKED")
    return panel




def _par_poextbus_cnc_led_logic_final(self, parent):
    panel = self.panel("poextbus_cnc", parent, "PoExtBus / CNC / PULSE ENGINE")
    inner = self._scroll_body(panel)
    names = []
    for needle in ["poextbus", "cnc_", "pulse engine", "pulse_engine"]:
        for name in self.bus.search(needle):
            if name not in names:
                names.append(name)
    for name in names:
        _par_signal_row(self, inner, name, self._hardware_label(name), icon="▤", led_size=22, source="PAR_POEXTBUS")
    return panel





# =====================================================================
# TARZAN PAR — DOMKNIĘCIE CSV NA BAZIE DZIAŁAJĄCYCH PLIKÓW
# Zakres: tylko PAR. Bez usuwania istniejących sekcji.
# =====================================================================

class _CsvProxy:
    def __init__(self, fn):
        self.fn = fn
    def set(self, value):
        try:
            self.fn(value)
        except Exception:
            pass


def _csv_led(parent, value=0, *, size=22, mode="normal", bg=None):
    bg = bg or COLORS["panel"]
    c = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
    state = {"value": 1 if value else 0}

    def draw(v=None):
        if v is not None:
            state["value"] = 1 if v else 0
        c.delete("all")
        if mode == "violet":
            outer, inner, outline = "#3d145f", COLORS.get("violet", "#9b35ff"), "#c58cff"
        elif mode == "gray":
            outer = "#283038" if state["value"] else "#20262c"
            inner = "#8b949b" if state["value"] else "#5b646b"
            outline = "#c7d0d6"
        elif mode == "neutral":
            outer = "#20262c" if not state["value"] else "#5a1613"
            inner = "#5b646b" if not state["value"] else COLORS["red"]
            outline = "#c7d0d6" if not state["value"] else "#111"
        else:
            outer = "#134d16" if state["value"] else "#5a1613"
            inner = COLORS["green"] if state["value"] else COLORS["red"]
            outline = "#111"
        c.create_oval(1, 1, size - 1, size - 1, fill=outer, outline="")
        c.create_oval(4, 4, size - 4, size - 4, fill=inner, outline=outline, width=2)
    draw()
    c.csv_set = draw
    return c




def _tarzan_bridge_csv(self, parent):
    panel = self.panel("bridge", parent, "MOSTEK PLAY ↔ REC")
    inner = self._scroll_body(panel)
    names = self.bus.by_group("MOSTEK_PLAY_REC")
    for name in names:
        label = self.bridge_label(name)
        frame = tk.Frame(inner, bg=COLORS["panel"])
        frame.pack(fill="x", pady=2)
        tk.Label(frame, text=label, bg=COLORS["panel"], fg=COLORS["text"], width=20, anchor="w", font=("Segoe UI", 9)).pack(side="left")
        led = _csv_led(frame, self.bus.get(name), mode="gray", bg=COLORS["panel"])
        led.pack(side="left", padx=4)
        tk.Label(frame, text="→", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 12, "bold")).pack(side="left", padx=4)
        self.rows[name] = _CsvProxy(lambda v, l=led: l.csv_set(v))
    return panel















# =====================================================================
# TARZAN PAR — KOREKTY LISTY WSZYSTKICH SYGNAŁÓW / RRP / AUTO / CNC
# =====================================================================

# Korekty map osi wg uwag operatora.
try:
    AXIS_SIGNAL_BINDINGS["ARM_V"]["left"] = ["arm_v_limit_down", "play_p12_arm_v_limit_down"]
    AXIS_SIGNAL_BINDINGS["ARM_V"]["right"] = ["arm_v_limit_up", "play_p04_arm_v_limit_up"]
    AXIS_SIGNAL_BINDINGS["CAM_T"]["left"] = ["cam_tilt_limit", "play_p10_cam_tilt_limit"]
    AXIS_SIGNAL_BINDINGS["CAM_T"]["right"] = []
    AXIS_SIGNAL_BINDINGS["ARM_H"]["right"] = ["arm_h_limit_right", "play_p01_arm_h_auto_limit", "play_p02_arm_h_limit_right"]
    AXIS_SIGNAL_BINDINGS["ARM_H"]["left"] = ["arm_h_limit_left", "play_p03_arm_h_limit_left"]
except Exception:
    pass

_MANUAL_FORCE_SIGNALS = {
    "play_p15_rrp_dir_h_res", "play_p38_step_dir_arm_h", "play_p39_step_dir_arm_v", "play_p40_step_dir_arm_tilt",
    "play_p46_step_ctr_arm_h", "play_p48_step_ctr_arm_v", "play_p49_step_ctr_arm_tilt",
    "play_p50_step_en_arm_h", "play_p51_step_en_arm_v", "play_p52_step_en_arm_tilt",
    "play_p53_rrp_en_res", "rec_p12_rec_dir_arm_h", "rec_p13_rec_dir_arm_v", "rec_p15_rec_ctr_arm_h",
    "rec_p16_rec_ctr_arm_v", "rec_p38_auto_enable", "par_lamp_auto_active", "par_mass_reg_enable",
    "par_mass_reg_limit_add", "par_mass_reg_limit_remove", "par_shock_sensor_state",
}

_LINKED_SIGNAL_GROUPS = {
    "play_p14_drone_release": ["play_p14_drone_release"],
    "play_p16_action_led": ["play_p16_action_led", "par_lamp_auto_active"],
    "par_lamp_auto_active": ["par_lamp_auto_active", "play_p16_action_led"],
    "play_p13_mass_reg_limit_add": ["play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"],
    "par_mass_reg_limit_add": ["play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"],
    "play_p23_mass_reg_limit_remove": ["play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"],
    "par_mass_reg_limit_remove": ["play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"],
    "play_p41_mass_reg_enable": ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "rec_p36_mass_reg_enable": ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "par_mass_reg_enable": ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "rec_p39_shock_sensor": ["rec_p39_shock_sensor", "par_shock_sensor_state"],
    "par_shock_sensor_state": ["rec_p39_shock_sensor", "par_shock_sensor_state"],
    "play_p37_step_disconnect_manual": ["play_p37_step_disconnect_manual"],
    "rec_p38_auto_enable": ["rec_p38_auto_enable"],
}

_SIGNAL_LABEL_OVERRIDES = {
    "play_p15_rrp_dir_h_res": "PLAY P15  play_p15_rrp_dir_h_res  REZERWA RRP DIR H",
    "play_p42_res": "PLAY P42  play_p42_res  REZERWA",
    "play_p43_res": "PLAY P43  play_p43_res  REZERWA",
    "play_p44_res": "PLAY P44  play_p44_res  REZERWA",
    "play_p53_rrp_en_res": "PLAY P53  play_p53_rrp_en_res  REZERWA RRP EN",
    "play_p55_bridge_rec_enable": "PLAY P55  play_p55_bridge_rec_enable  MOSTEK / REZERWA",
    "rec_p27_free_limit_res": "REC P27  rec_p27_free_limit_res  PIN WOLNY",
    "rec_p35_free_keyboard_old": "REC P35  rec_p35_free_keyboard_old  PIN WOLNY",
    "rec_p40_free_limit_res": "REC P40  rec_p40_free_limit_res  PIN WOLNY",
    "rec_p41_free_aux_pot": "REC P41  rec_p41_free_aux_pot  REZERWA",
    "rec_p42_free_keyboard_old": "REC P42  rec_p42_free_keyboard_old  REZERWA",
    "rec_p43_free_keyboard_old": "REC P43  rec_p43_free_keyboard_old  REZERWA",
    "rec_p44_free_keyboard_old": "REC P44  rec_p44_free_keyboard_old  REZERWA",
    "rec_p55_free_cart_spare": "REC P55  rec_p55_free_cart_spare  REZERWA / ZAPAS",
}

_VIOLET_NAME_PARTS = (
    "kb", "lcd_", "i2c_", "led_data", "led_latch", "led_clk", "poextbus", "res", "free"
)
_GRAY_NAME_PARTS = ("bridge_",)


def _final_force_or_toggle(self, name: str, *, source: str = "PAR"):
    current = 1 if self.bus.get(name) else 0
    new_value = 0 if current else 1
    meta = self.bus.get_meta(name)
    try:
        if name in _MANUAL_FORCE_SIGNALS:
            self.bus.force_signal(name, new_value, source=source)
        elif meta and getattr(meta, "is_input", False) and not getattr(meta, "is_forbidden", False):
            self.bus.toggle_input(name, source=source)
        elif meta and getattr(meta, "is_output", False):
            self.bus.force_signal(name, new_value, source=source)
        else:
            self.bus.force_signal(name, new_value, source=source)
    except Exception:
        try:
            self.bus.force_signal(name, new_value, source=source)
        except Exception:
            pass


def _final_signal_style(self, name: str):
    meta = self.bus.get_meta(name)
    lower = (name or "").lower()
    if name == "play_p15_rrp_dir_h_res":
        return "neutral"
    if any(part in lower for part in _GRAY_NAME_PARTS) or (meta and (meta.grupa or "").upper() == "MOSTEK_PLAY_REC"):
        return "gray"
    if any(part in lower for part in _VIOLET_NAME_PARTS) or (meta and (meta.is_forbidden or (meta.typ in {"F", "RESERVED"}) or (meta.kierunek in {"F", "RESERVED"}))):
        return "violet"
    return "normal"


def _final_signal_clickable(self, name: str):
    meta = self.bus.get_meta(name)
    if name in _MANUAL_FORCE_SIGNALS:
        return True
    if not meta:
        return True
    if getattr(meta, "is_forbidden", False):
        return False
    return bool(getattr(meta, "is_input", False))


def _final_signal_label(self, name: str):
    if name in _SIGNAL_LABEL_OVERRIDES:
        return _SIGNAL_LABEL_OVERRIDES[name]
    meta = self.bus.get_meta(name)
    board = meta.plytka if meta else ""
    pin = meta.pin if (meta and meta.pin is not None) else (meta.kanal if meta and meta.kanal else "-")
    opis = (meta.opis or "") if meta else ""
    if opis:
        return f"{board} {pin}  {name}  {opis}"
    return f"{board} {pin}  {name}"


def _csv_signal_row_final(self, parent, name: str, label: str, *, mode="normal", clickable=False, source="PAR"):
    frame = tk.Frame(parent, bg=COLORS["panel"])
    frame.pack(fill="x", pady=1)
    fg = COLORS["muted"] if mode in {"violet", "gray"} else COLORS["text"]
    text_label = tk.Label(frame, text=label, bg=COLORS["panel"], fg=fg, anchor="w", font=("Segoe UI", 9), justify="left", wraplength=520)
    text_label.pack(side="left", fill="x", expand=True)
    led = _csv_led(frame, self.bus.get(name), mode=mode, bg=COLORS["panel"])
    led.pack(side="right", padx=(8, 4))
    self.rows[name] = _CsvProxy(lambda v, l=led: l.csv_set(v))

    if clickable:
        def click(_e=None, n=name):
            _final_force_or_toggle(self, n, source=source)
        for widget in (frame, text_label, led):
            widget.bind("<Button-1>", click)
    return frame


def _final_emit_pulse(self, names, *, source="PAR_PULSE", delay_ms=70):
    for name in names:
        try:
            self.bus.force_signal(name, 1, source=source)
            self.app.after(delay_ms, lambda n=name, s=source: self.bus.force_signal(n, 0, source=s))
        except Exception:
            pass


def _set_many_signals(self, names, value, *, source="PAR_LINK"):
    for name in names:
        try:
            self.bus.force_signal(name, value, source=source)
        except Exception:
            try:
                self.bus.set_input(name, value, source=source)
            except Exception:
                pass


def _pulse_many_signals(self, names, *, source="PAR_PULSE", delay_ms=70):
    unique = []
    seen = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        unique.append(name)
    if unique:
        _final_emit_pulse(self, unique, source=source, delay_ms=delay_ms)


def _final_linked_set(self, name: str, value):
    linked = _LINKED_SIGNAL_GROUPS.get(name, [name])
    for target in linked:
        proxy = self.rows.get(target)
        if proxy and target != name:
            try:
                proxy.set(value)
            except Exception:
                pass




def _tarzan_automatyka_panel_v2(self, parent):
    panel = self.panel("automatyka", parent, "AUTOMATYKA")
    box = tk.Frame(panel.body, bg=COLORS["panel"])
    box.pack(fill="both", expand=True)
    c = tk.Canvas(box, width=78, height=78, bg=COLORS["panel"], highlightthickness=0)
    c.pack(anchor="center", pady=6)
    state = {"value": 1 if self.bus.get("play_p37_step_disconnect_manual") else 0}
    def draw(v=None):
        if v is not None:
            state["value"] = 1 if v else 0
        c.delete("all")
        body = COLORS["red"] if state["value"] else "#66707a"
        glow = "#5a1613" if state["value"] else "#2c343a"
        c.create_oval(8, 8, 70, 70, fill=glow, outline="")
        c.create_polygon(39,12, 26,39, 34,39, 29,65, 53,31, 42,31, 50,12, fill=body, outline="#111", width=1)
    def toggle(_e=None):
        _final_force_or_toggle(self, "play_p37_step_disconnect_manual", source="PAR_AUTO")
    c.bind("<Button-1>", toggle)
    draw()
    self.rows["play_p37_step_disconnect_manual"] = _CsvProxy(draw)
    return panel


def _tarzan_auto_panel_v2(self, parent):
    panel = self.panel("autostatus", parent, "AUTO")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)
    led = _csv_led(wrap, self.bus.get("rec_p38_auto_enable"), mode="normal", bg=COLORS["panel"], size=62)
    led.pack(anchor="center", pady=10)
    def click(_e=None):
        _final_force_or_toggle(self, "rec_p38_auto_enable", source="PAR_AUTO_WINDOW")
    for w in (wrap, led):
        w.bind("<Button-1>", click)
    self.rows["rec_p38_auto_enable"] = _CsvProxy(lambda v: led.csv_set(v))
    return panel




def _tarzan_ui_panel_v2(self, parent):
    panel = self.panel("ui", parent, "UI PANEL PLAY / REC")
    grid = tk.Frame(panel.body, bg=COLORS["panel"])
    grid.pack(fill="x")
    self._ui_button_widgets = {}
    self._ui_led_widgets = {}
    buttons = [
        ("F1", "rec_p45_sw_f1", "rec_p46_led_f1"),
        ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
        ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"),
        ("F4", "rec_p51_sw_f4", "rec_p52_led_f4"),
    ]
    for i, (label_text, sw, led_sig) in enumerate(buttons):
        cell = tk.Frame(grid, bg="#0f171d", highlightbackground="#30424f", highlightthickness=1)
        cell.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
        led = Led(cell, size=28, bg="#0f171d")
        led.pack(pady=(7, 4))
        led.set(self.bus.get(led_sig))
        btn = tk.Button(cell, text=label_text, bg="#243847", fg="#f2f7fb", activebackground="#31556e", activeforeground="#ffffff", relief="flat", font=("Segoe UI", 16, "bold"), height=2)
        btn.pack(fill="x", padx=7, pady=(0, 3))
        underline = tk.Frame(cell, bg=COLORS["green"], height=4)
        underline.pack(fill="x", padx=7, pady=(0, 7))
        btn.bind("<ButtonPress-1>", lambda _e, s=sw: _par_set_signal(self, s, 1, "PAR_UI_BUTTON"))
        btn.bind("<ButtonRelease-1>", lambda _e, s=sw: _par_set_signal(self, s, 0, "PAR_UI_BUTTON"))
        btn.bind("<Leave>", lambda _e, s=sw: _par_set_signal(self, s, 0, "PAR_UI_BUTTON"))
        self._ui_button_widgets[sw] = btn
        self._ui_led_widgets[led_sig] = led
        self.rows[led_sig] = _ParValueProxy(lambda v, l=led: l.set(v))
        self.rows[sw] = _ParValueProxy(lambda v, b=btn: b.configure(bg=COLORS["green"] if v else "#243847", fg="#061006" if v else "#f2f7fb"))
        try:
            self.rows[sw].set(self.bus.get(sw))
        except Exception:
            pass
    for i in range(4):
        grid.grid_columnconfigure(i, weight=1)
    return panel


def _tarzan_mass_regulator_panel_v2(self, parent):
    panel = self.panel("mass_regulator", parent, "REGULATOR MASY")
    wrap = tk.Frame(panel.body, bg=COLORS["panel"])
    wrap.pack(fill="both", expand=True)

    enable_box = tk.Frame(wrap, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)
    enable_box.pack(fill="x", pady=(0, 6))
    enable_led = Led(enable_box, size=26, bg=COLORS["panel3"])
    enable_led.pack(pady=6)

    btn_row = tk.Frame(wrap, bg=COLORS["panel"])
    btn_row.pack(fill="x")
    add_btn = tk.Button(btn_row, text="DODAJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"))
    rem_btn = tk.Button(btn_row, text="UJMIJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"))
    add_btn.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=2)
    rem_btn.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=2)

    def set_mass_mode(mode: str):
        current_add = 1 if self.bus.get("par_mass_reg_limit_add") else 0
        current_rem = 1 if self.bus.get("par_mass_reg_limit_remove") else 0

        if mode == "ADD":
            new_add = 0 if current_add else 1
            new_rem = 0
        else:
            new_rem = 0 if current_rem else 1
            new_add = 0

        new_en = 1 if (new_add or new_rem) else 0

        for sig, val in [
            ("play_p13_mass_reg_limit_add", new_add),
            ("par_mass_reg_limit_add", new_add),
            ("play_p23_mass_reg_limit_remove", new_rem),
            ("par_mass_reg_limit_remove", new_rem),
            ("play_p41_mass_reg_enable", new_en),
            ("rec_p36_mass_reg_enable", new_en),
            ("par_mass_reg_enable", new_en),
        ]:
            try:
                self.bus.force_signal(sig, val, source="PAR_MASS_EXCLUSIVE")
            except Exception:
                try:
                    self.bus.set_input(sig, val, source="PAR_MASS_EXCLUSIVE")
                except Exception:
                    pass

    add_btn.configure(command=lambda: set_mass_mode("ADD"))
    rem_btn.configure(command=lambda: set_mass_mode("REMOVE"))

    def paint_enable(v=None):
        value = self.bus.get("par_mass_reg_enable") if v is None else v
        enable_box.configure(bg="#143d16" if value else COLORS["panel3"])
        enable_led.configure(bg="#143d16" if value else COLORS["panel3"])
        enable_led.set(value)

    def paint_add(v=None):
        value = self.bus.get("par_mass_reg_limit_add") if v is None else v
        add_btn.configure(bg=COLORS["green"] if value else COLORS["button"], fg="#061006" if value else COLORS["text"])

    def paint_rem(v=None):
        value = self.bus.get("par_mass_reg_limit_remove") if v is None else v
        rem_btn.configure(bg=COLORS["blue"] if value else COLORS["button"], fg="#ffffff")

    self.rows["par_mass_reg_enable"] = _ParValueProxy(paint_enable)
    self.rows["play_p41_mass_reg_enable"] = _ParValueProxy(paint_enable)
    self.rows["rec_p36_mass_reg_enable"] = _ParValueProxy(paint_enable)
    self.rows["par_mass_reg_limit_add"] = _ParValueProxy(paint_add)
    self.rows["play_p13_mass_reg_limit_add"] = _ParValueProxy(paint_add)
    self.rows["par_mass_reg_limit_remove"] = _ParValueProxy(paint_rem)
    self.rows["play_p23_mass_reg_limit_remove"] = _ParValueProxy(paint_rem)
    paint_enable(); paint_add(); paint_rem()
    return panel


def _tarzan_dron_panel_v2(self, parent):
    panel = self.panel("dron", parent, "DRON")
    row = tk.Frame(panel.body, bg=COLORS["panel"])
    row.pack(fill="x", pady=6)
    tk.Label(row, text="ZWOLNIENIE", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
    led = Led(row, size=28, bg=COLORS["panel"])
    led.pack(side="right", padx=6)
    led.set(self.bus.get("play_p14_drone_release"))
    btn = tk.Button(panel.body, text="ZWOLNIJ DRONA", bg="#7a251f", fg="#fff", relief="flat", font=("Segoe UI", 10, "bold"), command=lambda: _final_force_or_toggle(self, "play_p14_drone_release", source="PAR_DRON"))
    btn.pack(fill="x", pady=(8, 2))
    self.rows["play_p14_drone_release"] = _ParValueProxy(lambda v: led.set(v))
    return panel


def _tarzan_axes_final_v2(self, parent):
    panel = _par_axes_final(self, parent)
    try:
        card = self.axis_cards.get("CAM_T")
        if card:
            left_parent = getattr(card.end_left, 'master', None)
            right_parent = getattr(card.end_right, 'master', None)
            if left_parent and not getattr(card, '_cam_t_label_fixed', False):
                for child in left_parent.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(text="STOP")
                for child in right_parent.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(text="")
                card._cam_t_label_fixed = True
    except Exception:
        pass
    return panel


def _tarzan_refresh_axis_cards_final_v2(self):
    _par_refresh_axis_cards_final(self)
    try:
        card = self.axis_cards.get("CAM_T")
        if card:
            value = 1 if (self.bus.get("cam_tilt_limit") or self.bus.get("play_p10_cam_tilt_limit")) else 0
            card.set_end_left(value)
            card.set_end_right(0)
    except Exception:
        pass


def _tarzan_rrp_panel_v2(self, parent):
    panel = self.panel("operator", parent, "STEROWANIE OPERATORA (RRP)")
    root = tk.Frame(panel.body, bg=COLORS["panel"])
    root.pack(fill="both", expand=True)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    axis_map = {
        "ARM_H": {"step": ["play_p46_step_ctr_arm_h", "rec_p15_rec_ctr_arm_h", "cnc_b_arm_h_ctr"], "dir": ["play_p38_step_dir_arm_h", "rec_p12_rec_dir_arm_h", "cnc_b_arm_h_dir"]},
        "ARM_V": {"step": ["play_p48_step_ctr_arm_v", "rec_p16_rec_ctr_arm_v", "cnc_c_arm_v_ctr"], "dir": ["play_p39_step_dir_arm_v", "rec_p13_rec_dir_arm_v", "cnc_c_arm_v_dir"]},
        "CAM_H": {"step": ["rec_p01_copy_ctr_cam_h", "cnc_x_cam_h_ctr", "TAKE_CAM_H_STEP"], "dir": ["rec_p03_copy_dir_cam_h", "cnc_x_cam_h_dir", "TAKE_CAM_H_DIR"]},
        "CAM_V": {"step": ["rec_p02_copy_ctr_cam_v", "cnc_y_cam_v_ctr", "TAKE_CAM_V_STEP"], "dir": ["rec_p04_copy_dir_cam_v", "cnc_y_cam_v_dir", "TAKE_CAM_V_DIR"]},
        "CAM_T": {"step": ["rec_p06_copy_ctr_tilt", "cnc_a_arm_tilt_ctr", "play_p49_step_ctr_arm_tilt", "TAKE_CAM_T_STEP"], "dir": ["rec_p08_copy_dir_tilt", "cnc_a_arm_tilt_dir", "play_p40_step_dir_arm_tilt", "TAKE_CAM_T_DIR"]},
        "CAM_F": {"step": ["rec_p05_copy_ctr_focus", "cnc_z_focus_ctr", "TAKE_CAM_F_STEP"], "dir": ["rec_p07_copy_dir_focus", "cnc_z_focus_dir", "TAKE_CAM_F_DIR"]},
    }

    def axis_state(axis_key):
        current = axis_map.get(axis_key, axis_map["ARM_H"])
        dir_value = 0
        for dir_name in current["dir"]:
            try:
                if self.bus.exists(dir_name):
                    dir_value = 1 if self.bus.get(dir_name) else 0
                    break
            except Exception:
                pass
        return current, dir_value

    def knob(cell, title, signal, default_axis):
        box = tk.Frame(cell, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)
        box.pack(fill="both", expand=True, padx=4, pady=4)
        tk.Label(box, text=title, bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).pack(fill="x")

        axis_var = tk.StringVar(value=default_axis)
        tune_var = tk.DoubleVar(value=1.0)
        state = {"value": float(self.bus.get(signal) or 0), "after_id": None}

        position_frame = tk.Frame(box, bg=COLORS["panel3"])
        position_frame.pack(fill="x", padx=6, pady=(6, 2))
        position_value = tk.Label(position_frame, text="0", bg="#0f171d", fg=COLORS["green"], relief="flat", font=("Consolas", 18, "bold"), pady=4)
        position_value.pack(fill="x", pady=(2, 0))

        canvas_size = 122
        canvas = tk.Canvas(box, width=canvas_size, height=canvas_size, bg=COLORS["panel3"], highlightthickness=0)
        canvas.pack(pady=(2, 4))

        buttons_row = tk.Frame(box, bg=COLORS["panel3"])
        buttons_row.pack(fill="x", padx=6, pady=(0, 6))
        dir_btn = tk.Button(buttons_row, text="DIR", bg=COLORS["button"], fg=COLORS["text"], relief="flat", font=("Segoe UI", 9, "bold"))
        dir_btn.pack(side="left", fill="x", expand=True)

        controls = tk.Frame(box, bg=COLORS["panel3"])
        controls.pack(fill="x", padx=6, pady=(0, 4))

        axis_wrap = tk.Frame(controls, bg=COLORS["green"], highlightthickness=0)
        axis_wrap.pack(fill="x", pady=(0, 6))
        axis_menu = tk.OptionMenu(axis_wrap, axis_var, default_axis, *axis_map.keys())
        axis_menu.configure(bg=COLORS["green"], fg="#061006", activebackground="#43ff4e", activeforeground="#061006", relief="flat", highlightthickness=0, font=("Segoe UI", 10, "bold"), anchor="center")
        axis_menu["menu"].configure(bg=COLORS["green"], fg="#061006", activebackground="#43ff4e", activeforeground="#061006", font=("Segoe UI", 10, "bold"))
        axis_menu.pack(fill="x", padx=4, pady=4)

        tune_scale = tk.Scale(controls, from_=0.2, to=3.0, resolution=0.1, orient="horizontal", variable=tune_var, bg=COLORS["panel3"], troughcolor="#0f7d18", fg=COLORS["text"], highlightthickness=0, bd=0, length=170, showvalue=False)
        tune_scale.pack(fill="x")

        def paint_dir(v=None):
            _current, dir_value = axis_state(axis_var.get())
            active = dir_value if v is None else (1 if v else 0)
            dir_btn.configure(bg=COLORS["green"] if active else COLORS["button"], fg="#061006" if active else COLORS["text"])

        def draw(v=None):
            import math
            if v is not None:
                state["value"] = max(0.0, min(4095.0, float(v)))
            canvas.delete("all")
            cx = canvas_size // 2
            cy = canvas_size // 2
            r = 40
            canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=225, extent=270, style="arc", outline="#5f6b72", width=8)
            frac = state["value"] / 4095.0
            angle_deg = 225 + 270 * frac
            angle = math.radians(angle_deg)
            x = cx + math.cos(angle) * (r - 5)
            y = cy - math.sin(angle) * (r - 5)
            canvas.create_oval(cx-26, cy-26, cx+26, cy+26, fill="#101820", outline=COLORS["border"], width=2)
            canvas.create_line(cx, cy, x, y, fill=COLORS["red"], width=4, capstyle=tk.ROUND)
            canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill="#dfe6e9", outline="#111")
            position_value.configure(text=str(int(state["value"])))

        def pulse_step(delay_ms):
            current, _dir_value = axis_state(axis_var.get())
            _pulse_many_signals(self, current["step"], source="PAR_RRP_STEP", delay_ms=delay_ms)

        def stop_generator():
            after_id = state.get("after_id")
            if after_id is not None:
                try:
                    self.app.after_cancel(after_id)
                except Exception:
                    pass
                state["after_id"] = None

        def generator_tick():
            stop_generator()
            value = float(state["value"])
            if value <= 0.0:
                return
            speed_factor = max(0.2, float(tune_var.get()))
            intensity = value / 4095.0
            delay_ms = max(18, int(260 / max(0.05, intensity * speed_factor)))
            pulse_step(delay_ms)
            state["after_id"] = self.app.after(delay_ms, generator_tick)

        def restart_generator():
            stop_generator()
            if float(state["value"]) > 0.0:
                generator_tick()

        def toggle_dir():
            current, dir_value = axis_state(axis_var.get())
            new_value = 0 if dir_value else 1
            _set_many_signals(self, current["dir"], new_value, source="PAR_RRP_DIR")
            paint_dir(new_value)

        def on_axis_change(*_args):
            paint_dir()
            draw()
            restart_generator()

        def on_tune_change(*_args):
            restart_generator()

        def apply_delta(delta_steps):
            if not delta_steps:
                return
            step_size = 48
            val = max(0, min(4095, int(state["value"] + (delta_steps * step_size))))
            if val == int(state["value"]):
                return
            state["value"] = val
            self.bus.force_signal(signal, val, source="PAR_RRP_POT")
            draw()
            restart_generator()

        def on_wheel(event):
            delta_steps = 0
            if getattr(event, "delta", 0):
                delta_steps = 1 if event.delta > 0 else -1
            elif getattr(event, "num", None) == 4:
                delta_steps = 1
            elif getattr(event, "num", None) == 5:
                delta_steps = -1
            apply_delta(delta_steps)
            return "break"

        axis_var.trace_add("write", on_axis_change)
        tune_var.trace_add("write", on_tune_change)
        dir_btn.configure(command=toggle_dir)
        canvas.bind("<MouseWheel>", on_wheel)
        canvas.bind("<Button-4>", on_wheel)
        canvas.bind("<Button-5>", on_wheel)
        box.bind("<Destroy>", lambda _e: stop_generator(), add="+")
        self.rows[signal] = _CsvProxy(lambda v: (draw(v), restart_generator()))
        draw()
        paint_dir()
        restart_generator()
        return box

    left = tk.Frame(root, bg=COLORS["panel"])
    left.grid(row=0, column=0, sticky="nsew")
    right = tk.Frame(root, bg=COLORS["panel"])
    right.grid(row=0, column=1, sticky="nsew")
    knob(left, "POTENCJOMETR RRP X", "play_p45_rrp_pot_h", "ARM_H")
    knob(right, "POTENCJOMETR RRP Y", "play_p47_rrp_pot_v", "ARM_V")
    return panel

def _tarzan_on_state_change_v2(self, name, state):
    _par_on_state_change_final(self, name, state)
    _final_linked_set(self, name, state.value)
    try:
        if name in {"play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"}:
            for extra in ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"]:
                if extra != name and self.bus.exists(extra):
                    self.bus.force_signal(extra, state.value, source="PAR_LINK")
        elif name in {"play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"}:
            for extra in ["play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"]:
                if extra != name and self.bus.exists(extra):
                    self.bus.force_signal(extra, state.value, source="PAR_LINK")
        elif name in {"play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"}:
            for extra in ["play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"]:
                if extra != name and self.bus.exists(extra):
                    self.bus.force_signal(extra, state.value, source="PAR_LINK")
        elif name in {"par_lamp_auto_active", "play_p16_action_led"}:
            for extra in ["par_lamp_auto_active", "play_p16_action_led"]:
                if extra != name and self.bus.exists(extra):
                    self.bus.force_signal(extra, state.value, source="PAR_LINK")
        elif name in {"par_shock_sensor_state", "rec_p39_shock_sensor"}:
            for extra in ["par_shock_sensor_state", "rec_p39_shock_sensor"]:
                if extra != name and self.bus.exists(extra):
                    self.bus.force_signal(extra, state.value, source="PAR_LINK")
    except Exception:
        pass


try:
    _AXIS_TIMELINE_ROWS[:] = [
        ("ARM_H", "STEP", ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "cnc_b_arm_h_ctr"], COLORS["green"]),
        ("ARM_H", "DIR",  ["TAKE_ARM_H_DIR",  "play_p38_step_dir_arm_h", "cnc_b_arm_h_dir"], COLORS["blue"]),
        ("ARM_V", "STEP", ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "cnc_c_arm_v_ctr"], COLORS["green"]),
        ("ARM_V", "DIR",  ["TAKE_ARM_V_DIR",  "play_p39_step_dir_arm_v", "cnc_c_arm_v_dir"], COLORS["blue"]),
        ("CAM_H", "STEP", ["TAKE_CAM_H_STEP", "cnc_x_cam_h_ctr", "rec_p01_copy_ctr_cam_h"], COLORS["green"]),
        ("CAM_H", "DIR",  ["TAKE_CAM_H_DIR",  "cnc_x_cam_h_dir", "rec_p03_copy_dir_cam_h"], COLORS["blue"]),
        ("CAM_V", "STEP", ["TAKE_CAM_V_STEP", "cnc_y_cam_v_ctr", "rec_p02_copy_ctr_cam_v"], COLORS["green"]),
        ("CAM_V", "DIR",  ["TAKE_CAM_V_DIR",  "cnc_y_cam_v_dir", "rec_p04_copy_dir_cam_v"], COLORS["blue"]),
        ("CAM_T", "STEP", ["TAKE_CAM_T_STEP", "cnc_a_arm_tilt_ctr", "rec_p06_copy_ctr_tilt"], COLORS["green"]),
        ("CAM_T", "DIR",  ["TAKE_CAM_T_DIR",  "cnc_a_arm_tilt_dir", "rec_p08_copy_dir_tilt"], COLORS["blue"]),
        ("CAM_F", "STEP", ["TAKE_CAM_F_STEP", "cnc_z_focus_ctr", "rec_p05_copy_ctr_focus"], COLORS["green"]),
        ("CAM_F", "DIR",  ["TAKE_CAM_F_DIR",  "cnc_z_focus_dir", "rec_p07_copy_dir_focus"], COLORS["blue"]),
    ]
except Exception:
    pass


# =====================================================================
# w liście zgodnie z uwagami operatora. LED zawsze po lewej stronie.
# =====================================================================

_ALL_SIGNALS_FORCE_CLICK = {
    "play_p15_rrp_dir_h_res", "play_p38_step_dir_arm_h", "play_p39_step_dir_arm_v", "play_p40_step_dir_arm_tilt",
    "play_p41_mass_reg_enable", "play_p42_res", "play_p43_res", "play_p44_res",
    "play_p46_step_ctr_arm_h", "play_p48_step_ctr_arm_v", "play_p49_step_ctr_arm_tilt",
    "play_p50_step_en_arm_h", "play_p51_step_en_arm_v", "play_p52_step_en_arm_tilt", "play_p53_rrp_en_res",
    "rec_p12_rec_dir_arm_h", "rec_p13_rec_dir_arm_v", "rec_p15_rec_ctr_arm_h", "rec_p16_rec_ctr_arm_v",
    "rec_p27_free_limit_res", "rec_p35_free_keyboard_old", "rec_p36_mass_reg_enable", "rec_p38_auto_enable",
    "rec_p40_free_limit_res", "rec_p41_free_aux_pot", "rec_p42_free_keyboard_old", "rec_p43_free_keyboard_old", "rec_p44_free_keyboard_old",
    "rec_p46_led_f1", "rec_p48_led_f2", "rec_p50_led_f3", "rec_p52_led_f4",
    "rec_p53_copy_cam_v_limit_up",
}

_ALL_SIGNALS_PASSIVE = {
    "play_p17_bridge_rec_dir_x", "play_p18_bridge_rec_dir_y", "play_p19_bridge_rec_dir_z",
    "play_p20_bridge_rec_ctr_x", "play_p21_bridge_rec_ctr_y", "play_p22_bridge_rec_ctr_z",
    "rec_p17_bridge_play_dir_x", "rec_p18_bridge_play_dir_y", "rec_p19_bridge_play_dir_z",
    "rec_p20_bridge_play_ctr_x", "rec_p21_bridge_play_ctr_y", "rec_p22_bridge_play_ctr_z",
    "rec_p37_bridge_play_rec_in", "rec_p54_bridge_play_rec_out", "play_p55_bridge_rec_enable",
}


def _all_signals_style_v3(self, name: str):
    lower = (name or "").lower()
    meta = self.bus.get_meta(name)
    if name == "play_p15_rrp_dir_h_res":
        return "neutral"
    if name in _ALL_SIGNALS_PASSIVE or "bridge_" in lower:
        return "gray"
    if lower.startswith("cnc_"):
        return "gray"
    if any(k in lower for k in ("kb", "lcd_", "i2c_", "led_data", "led_latch", "led_clk", "poextbus")):
        return "violet"
    if any(k in lower for k in ("_res", "free_", "_free")):
        return "violet"
    if meta and (getattr(meta, "is_forbidden", False) or getattr(meta, "typ", "") in {"F", "RESERVED"} or getattr(meta, "kierunek", "") in {"F", "RESERVED"}):
        return "violet"
    return "normal"


def _all_signals_clickable_v3(self, name: str):
    if name in _ALL_SIGNALS_PASSIVE:
        return False
    if name in _ALL_SIGNALS_FORCE_CLICK:
        return True
    meta = self.bus.get_meta(name)
    if meta is None:
        return True
    if getattr(meta, "is_input", False):
        return True
    if getattr(meta, "is_output", False):
        return True
    return True


def _all_signals_label_v3(self, name: str):
    if name in _SIGNAL_LABEL_OVERRIDES:
        return _SIGNAL_LABEL_OVERRIDES[name]
    meta = self.bus.get_meta(name)
    board = meta.plytka if meta else ""
    pin = meta.pin if (meta and meta.pin is not None) else (meta.kanal if meta and meta.kanal else "-")
    opis = (meta.opis or "") if meta else ""
    opis = " ".join(str(opis).split())
    extra = ""
    lower = name.lower()
    if name in _ALL_SIGNALS_PASSIVE or "bridge_" in lower:
        extra = "  [MOSTEK]"
    elif any(k in lower for k in ("_res", "free_", "_free")):
        extra = "  [REZERWA]"
    elif lower.startswith("cnc_"):
        extra = "  [CNC]"
    if opis:
        return f"{board} {pin}  {name}  {opis}{extra}"
    return f"{board} {pin}  {name}{extra}"


def _all_signals_toggle_v3(self, name: str, *, source: str = "PAR_ALL"):
    current = 1 if self.bus.get(name) else 0
    new_value = 0 if current else 1
    try:
        self.bus.force_signal(name, new_value, source=source)
    except Exception:
        try:
            self.bus.set_input(name, new_value, source=source)
        except Exception:
            pass







# =====================================================================
# Zakres: tylko lista nadrzędna PAR, reszty nie ruszać.
# =====================================================================

_ALL_SIGNALS_PULSE = {
    "play_p46_step_ctr_arm_h", "play_p48_step_ctr_arm_v", "play_p49_step_ctr_arm_tilt",
    "rec_p15_rec_ctr_arm_h", "rec_p16_rec_ctr_arm_v",
    "cnc_x_cam_h_ctr", "cnc_y_cam_v_ctr", "cnc_z_focus_ctr", "cnc_a_arm_tilt_ctr",
    "cnc_b_arm_h_ctr", "cnc_c_arm_v_ctr", "cnc_d_cart_ctr",
}

_ALL_SIGNALS_LINK_V4 = {
    "play_p13_mass_reg_limit_add": ["play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"],
    "par_mass_reg_limit_add": ["play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"],
    "play_p23_mass_reg_limit_remove": ["play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"],
    "par_mass_reg_limit_remove": ["play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"],
    "play_p41_mass_reg_enable": ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "rec_p36_mass_reg_enable": ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "par_mass_reg_enable": ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "play_p16_action_led": ["play_p16_action_led", "par_lamp_auto_active"],
    "par_lamp_auto_active": ["play_p16_action_led", "par_lamp_auto_active"],
    "rec_p39_shock_sensor": ["rec_p39_shock_sensor", "par_shock_sensor_state"],
    "par_shock_sensor_state": ["rec_p39_shock_sensor", "par_shock_sensor_state"],
    "play_p14_drone_release": ["play_p14_drone_release"],
    "rec_p38_auto_enable": ["rec_p38_auto_enable"],
}


def _all_signals_set_many_v4(self, names, value, *, source='PAR_ALL_LINK'):
    for target in names:
        try:
            self.bus.force_signal(target, value, source=source)
        except Exception:
            try:
                self.bus.set_input(target, value, source=source)
            except Exception:
                pass


def _all_signals_toggle_v4(self, name: str, *, source: str = 'PAR_ALL'):
    if name in _ALL_SIGNALS_PASSIVE:
        return
    current = 1 if self.bus.get(name) else 0
    new_value = 0 if current else 1

    if name in _ALL_SIGNALS_PULSE:
        pulse_targets = [name]
        if name == 'play_p46_step_ctr_arm_h':
            pulse_targets.append('rec_p15_rec_ctr_arm_h')
        elif name == 'play_p48_step_ctr_arm_v':
            pulse_targets.append('rec_p16_rec_ctr_arm_v')
        _final_emit_pulse(self, pulse_targets, source=source, delay_ms=70)
        return

    linked = _ALL_SIGNALS_LINK_V4.get(name)
    if linked:
        _all_signals_set_many_v4(self, linked, new_value, source=source)
        return

    if name == 'rec_p53_copy_cam_v_limit_up':
        _all_signals_set_many_v4(self, ['rec_p53_copy_cam_v_limit_up', 'play_p07_cam_v_limit_up'], new_value, source=source)
        return

    try:
        self.bus.force_signal(name, new_value, source=source)
    except Exception:
        try:
            self.bus.set_input(name, new_value, source=source)
        except Exception:
            pass






# =====================================================================
# Zakres dokładnie wg uwagi operatora:
# - sama nazwa sygnału (bez opisów / płytek / pinów),
# - LED po lewej,
# - działające przełączanie po kliknięciu,
# - własny scroll + kółko myszy.
# =====================================================================

def _all_signals_scroll_body_v5(panel):
    canvas = tk.Canvas(panel.body, bg=COLORS['panel'], highlightthickness=0, bd=0)
    inner = tk.Frame(canvas, bg=COLORS['panel'])
    window_id = canvas.create_window((0, 0), window=inner, anchor='nw')

    def _on_inner_configure(_event=None):
        try:
            canvas.configure(scrollregion=canvas.bbox('all'))
        except Exception:
            pass

    def _on_canvas_configure(event):
        try:
            canvas.itemconfigure(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox('all'))
        except Exception:
            pass

    def _on_mousewheel(event):
        try:
            if getattr(event, 'delta', 0):
                delta = int(-1 * (event.delta / 120))
                if delta:
                    canvas.yview_scroll(delta, 'units')
            elif getattr(event, 'num', None) == 4:
                canvas.yview_scroll(-1, 'units')
            elif getattr(event, 'num', None) == 5:
                canvas.yview_scroll(1, 'units')
        except Exception:
            pass
        return 'break'

    def _bind_mousewheel_recursive(widget):
        try:
            widget.bind('<MouseWheel>', _on_mousewheel, add='+')
            widget.bind('<Button-4>', _on_mousewheel, add='+')
            widget.bind('<Button-5>', _on_mousewheel, add='+')
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                _bind_mousewheel_recursive(child)
        except Exception:
            pass

    inner.bind('<Configure>', lambda e: (_on_inner_configure(e), _bind_mousewheel_recursive(inner)), add='+')
    canvas.bind('<Configure>', _on_canvas_configure)
    panel.body.bind('<MouseWheel>', _on_mousewheel, add='+')
    panel.body.bind('<Button-4>', _on_mousewheel, add='+')
    panel.body.bind('<Button-5>', _on_mousewheel, add='+')
    _bind_mousewheel_recursive(canvas)
    _bind_mousewheel_recursive(inner)

    canvas.pack(fill='both', expand=True)
    return inner


def _all_signals_label_v5(self, name: str):
    return str(name)


def _all_signals_toggle_v5(self, name: str, *, source: str = 'PAR_ALL'):
    if name in _ALL_SIGNALS_PASSIVE:
        return

    current = 1 if self.bus.get(name) else 0
    new_value = 0 if current else 1

    if name in _ALL_SIGNALS_PULSE:
        pulse_targets = [name]
        if name == 'play_p46_step_ctr_arm_h':
            pulse_targets.append('rec_p15_rec_ctr_arm_h')
        elif name == 'play_p48_step_ctr_arm_v':
            pulse_targets.append('rec_p16_rec_ctr_arm_v')
        _final_emit_pulse(self, pulse_targets, source=source, delay_ms=180)
        for target in pulse_targets:
            if target in self.rows:
                try:
                    self.rows.set_value(target, 1)
                except Exception:
                    pass
        return

    linked = _ALL_SIGNALS_LINK_V4.get(name)
    if linked:
        _all_signals_set_many_v4(self, linked, new_value, source=source)
        for target in linked:
            if target in self.rows:
                try:
                    self.rows.set_value(target, new_value)
                except Exception:
                    pass
        return

    if name == 'rec_p53_copy_cam_v_limit_up':
        linked = ['rec_p53_copy_cam_v_limit_up', 'play_p07_cam_v_limit_up']
        _all_signals_set_many_v4(self, linked, new_value, source=source)
        for target in linked:
            if target in self.rows:
                try:
                    self.rows.set_value(target, new_value)
                except Exception:
                    pass
        return

    ok = False
    try:
        ok = bool(self.bus.force_signal(name, new_value, source=source))
    except Exception:
        ok = False
    if not ok:
        try:
            ok = bool(self.bus.set_input(name, new_value, source=source))
        except Exception:
            ok = False
    if not ok:
        try:
            self.bus.write_output(name, new_value, source=source)
            ok = True
        except Exception:
            ok = False

    if name in self.rows:
        try:
            self.rows.set_value(name, new_value)
        except Exception:
            pass


def _csv_signal_row_final_v5(self, parent, name: str, label: str, *, mode='normal', clickable=False, source='PAR'):
    frame = tk.Frame(parent, bg=COLORS['panel'])
    frame.pack(fill='x', pady=1)
    fg = COLORS['muted'] if mode in {'violet', 'gray'} else COLORS['text']

    led = _csv_led(frame, self.bus.get(name), mode=mode, bg=COLORS['panel'])
    led.pack(side='left', padx=(2, 8))

    text_label = tk.Label(
        frame,
        text=label,
        bg=COLORS['panel'],
        fg=fg,
        anchor='w',
        font=('Segoe UI', 9),
        justify='left',
        wraplength=0,
    )
    text_label.pack(side='left', fill='x', expand=True)
    self.rows[name] = _CsvProxy(lambda v, l=led: l.csv_set(v))

    if clickable:
        def click(_e=None, n=name):
            _all_signals_toggle_v5(self, n, source=source)
        for widget in (frame, text_label, led):
            widget.bind('<Button-1>', click)
            try:
                widget.configure(cursor='hand2')
            except Exception:
                pass
    return frame


def _tarzan_all_signals_final_v5(self, parent):
    panel = self.panel('all_signals', parent, 'WSZYSTKIE SYGNAŁY')
    inner = _all_signals_scroll_body_v5(panel)
    for name in self.bus.names():
        _csv_signal_row_final_v5(
            self,
            inner,
            name,
            _all_signals_label_v5(self, name),
            mode=_all_signals_style_v3(self, name),
            clickable=_all_signals_clickable_v3(self, name),
            source='PAR_ALL',
        )
    return panel



# =====================================================================
# TARZAN PAR — HOTFIX NA BAZIE OSTATNIEGO PLIKU UŻYTKOWNIKA
# Zakres:
# 1. CNC: tylko sama nazwa sygnału jak we Wszystkich sygnałach
# 2. Krańcówki: bez dubla MASS MAX / MASS MIN
# 3. SOK: przywrócony STEP + animacja koła
# =====================================================================

def _tarzan_cnc_signals_panel_v3(self, parent):
    panel = self.panel("cnc_signals", parent, "CNC")
    inner = self._scroll_body(panel)
    names = [n for n in self.bus.names() if n.startswith("cnc_")]
    for name in names:
        _csv_signal_row_final(self, inner, name, str(name), mode="gray", clickable=False, source="PAR_CNC")
    return panel


def _par_limits_led_logic_final_v3(self, parent):
    panel = self.panel("limits", parent, "KRAŃCÓWKI")
    body = tk.Frame(panel.body, bg=COLORS["panel"])
    body.pack(fill="both", expand=True)

    raw_names = self._group_or_search("KRAŃCÓWKI", ["limit"])
    names = []
    seen_labels = set()

    for name in raw_names:
        label = self.limit_label(name)
        blob = f"{name} {label}".upper()
        if "PIN WOLNY" in blob or "WOLNY" in blob or "FREE" in blob:
            continue
        key = label.strip().upper()
        if key in seen_labels:
            continue
        seen_labels.add(key)
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

        blocked = _par_signal_blocked(self, name)
        led = Led(cell, size=17, bg=COLORS["panel"], blocked=blocked)
        led.grid(row=0, column=0, sticky="w", padx=(0, 4))
        led.set(self.bus.get(name))
        self.rows[name] = _ParValueProxy(lambda v, l=led: l.set(v))

        label = tk.Label(
            cell,
            text=self.limit_label(name),
            bg=COLORS["panel"],
            fg=COLORS["muted"] if blocked else COLORS["text"],
            anchor="w",
            font=("Segoe UI", 8),
        )
        label.grid(row=0, column=1, sticky="ew")

        if _par_signal_clickable_input(self, name):
            def click(_event=None, n=name):
                self.bus.toggle_input(n, source="PAR_LIMIT")
            for widget in (cell, label, led):
                widget.bind("<Button-1>", click)

    return panel


def _tarzan_sok_section_v3(self, parent, title, dir_sig, ctr_sig, extra_buttons=(), mode_options=()):
    box = tk.Frame(parent, bg=COLORS['panel3'], highlightbackground=COLORS['border'], highlightthickness=1)
    tk.Label(box, text=title, bg=COLORS['panel3'], fg=COLORS['text'], font=('Segoe UI', 9, 'bold')).pack(fill='x', pady=(2, 0))

    state = {'angle': 0}
    mode_var = tk.StringVar(value=mode_options[0] if mode_options else '')
    mode_buttons = []

    signal_map = {
        'FOKUS': {'dir': ['rec_p07_copy_dir_focus', 'cnc_z_focus_dir', 'TAKE_CAM_F_DIR'], 'step': ['rec_p05_copy_ctr_focus', 'cnc_z_focus_ctr', 'TAKE_CAM_F_STEP']},
        'POCHYŁ': {'dir': ['rec_p08_copy_dir_tilt', 'cnc_a_arm_tilt_dir', 'play_p40_step_dir_arm_tilt', 'TAKE_CAM_T_DIR'], 'step': ['rec_p06_copy_ctr_tilt', 'cnc_a_arm_tilt_ctr', 'play_p49_step_ctr_arm_tilt', 'TAKE_CAM_T_STEP']},
        'POZIOM': {'dir': ['rec_p03_copy_dir_cam_h', 'cnc_x_cam_h_dir', 'TAKE_CAM_H_DIR'], 'step': ['rec_p01_copy_ctr_cam_h', 'cnc_x_cam_h_ctr', 'TAKE_CAM_H_STEP']},
        'PION': {'dir': ['rec_p04_copy_dir_cam_v', 'cnc_y_cam_v_dir', 'TAKE_CAM_V_DIR'], 'step': ['rec_p02_copy_ctr_cam_v', 'cnc_y_cam_v_ctr', 'TAKE_CAM_V_STEP']},
    }

    def selected_signals():
        if mode_options:
            selected = mode_var.get()
            if selected in signal_map:
                return signal_map[selected]['dir'], signal_map[selected]['step']
        return [dir_sig], [ctr_sig]

    def paint_mode_buttons():
        for opt, btn in mode_buttons:
            active = mode_var.get() == opt
            btn.configure(bg=COLORS['green'] if active else COLORS['button'], fg='#061006' if active else COLORS['text'])

    if mode_options:
        mode_row = tk.Frame(box, bg=COLORS['panel3'])
        mode_row.pack(fill='x', padx=4, pady=(2, 0))
        for opt in mode_options:
            btn = tk.Button(
                mode_row,
                text=opt,
                bg=COLORS['button'],
                fg=COLORS['text'],
                activebackground=COLORS['green'],
                activeforeground='#061006',
                relief='flat',
                font=('Segoe UI', 8, 'bold'),
                command=lambda o=opt: (mode_var.set(o), paint_mode_buttons()),
            )
            btn.pack(side='left', fill='x', expand=True, padx=2)
            mode_buttons.append((opt, btn))

    mid = tk.Frame(box, bg=COLORS['panel3'])
    mid.pack(fill='both', expand=True)
    c = tk.Canvas(mid, width=120, height=120, bg=COLORS['panel3'], highlightthickness=0)
    c.pack(pady=(4, 2))

    def draw():
        import math
        c.delete('all')
        cx = 60
        cy = 60
        r = 40
        c.create_oval(cx-r, cy-r, cx+r, cy+r, fill='#101820', outline='#8d99a3', width=2)
        for i in range(24):
            a = math.radians(i * 15 + state['angle'])
            x1 = cx + math.cos(a) * (r - 2)
            y1 = cy + math.sin(a) * (r - 2)
            x2 = cx + math.cos(a) * (r - 10)
            y2 = cy + math.sin(a) * (r - 10)
            c.create_line(x1, y1, x2, y2, fill='#dfe6e9', width=2)
        c.create_line(cx, 12, cx, 24, fill=COLORS['red'], width=4, capstyle=tk.ROUND)

    def pulse_step(direction):
        active_dir_sigs, active_ctr_sigs = selected_signals()
        state['angle'] = (state['angle'] + (15 if direction else -15)) % 360
        draw()
        _set_many_signals(self, active_dir_sigs, 1 if direction else 0, source='PAR_SOK_DIR')
        _pulse_many_signals(self, active_ctr_sigs, source='PAR_SOK_STEP', delay_ms=70)

    btn_row = tk.Frame(box, bg=COLORS['panel3'])
    btn_row.pack(fill='x', padx=6, pady=(0, 6))
    left_btn = tk.Button(
        btn_row,
        text='LEWO',
        bg=COLORS['button'],
        fg=COLORS['text'],
        activebackground=COLORS['green'],
        activeforeground='#061006',
        relief='flat',
        font=('Segoe UI', 9, 'bold'),
        command=lambda: pulse_step(0),
    )
    left_btn.pack(side='left', fill='x', expand=True, padx=(0, 3))
    right_btn = tk.Button(
        btn_row,
        text='PRAWO',
        bg=COLORS['button'],
        fg=COLORS['text'],
        activebackground=COLORS['green'],
        activeforeground='#061006',
        relief='flat',
        font=('Segoe UI', 9, 'bold'),
        command=lambda: pulse_step(1),
    )
    right_btn.pack(side='left', fill='x', expand=True, padx=(3, 0))

    paint_mode_buttons()
    draw()
    return box


def _tarzan_sok_panel_v3(self, parent):
    panel = self.panel('sok', parent, 'SOK — STEROWNIK OBROTOWY KURKOWY')
    grid = tk.Frame(panel.body, bg=COLORS['panel'])
    grid.pack(fill='both', expand=True)
    for r in range(2):
        grid.grid_rowconfigure(r, weight=1)
    for c in range(2):
        grid.grid_columnconfigure(c, weight=1)

    sections = [
        ('SOKPan', 'rec_p17_bridge_play_dir_x', 'rec_p20_bridge_play_ctr_x', (), ()),
        ('SOKTilt', 'rec_p18_bridge_play_dir_y', 'rec_p21_bridge_play_ctr_y', (), ()),
        ('SOKFokus', 'rec_p07_copy_dir_focus', 'rec_p05_copy_ctr_focus', (), ('FOKUS', 'POCHYŁ')),
        ('SOKCam', 'rec_p04_copy_dir_cam_v', 'rec_p02_copy_ctr_cam_v', (), ('POZIOM', 'PION')),
    ]
    for idx, (title, dir_sig, ctr_sig, extras, mode_options) in enumerate(sections):
        box = _tarzan_sok_section_v3(self, grid, title, dir_sig, ctr_sig, extras, mode_options)
        box.grid(row=idx // 2, column=idx % 2, sticky='nsew', padx=4, pady=4)
    return panel

# =====================================================================
# TARZAN PAR — finalne przypięcie aktywnych wersji
# =====================================================================
TarzanParPanels.axes = _tarzan_axes_final_v2
TarzanParPanels.refresh_axis_cards = _tarzan_refresh_axis_cards_final_v2
TarzanParPanels.on_state_change = _tarzan_on_state_change_v2
TarzanParPanels._schedule_timeline_redraw = _schedule_timeline_redraw
TarzanParPanels.timeline = _par_timeline_final
TarzanParPanels.draw_timeline = _par_draw_timeline_final
TarzanParPanels.take = _par_take_panel_final
TarzanParPanels._manual_axis_step = _par_manual_axis_step_final

TarzanParPanels.light_bh1750_panel = _par_light_bh1750_panel_final
TarzanParPanels.temperature_panel = _par_temperature_panel_final
TarzanParPanels.shock_sensor_panel = _par_shock_sensor_panel_final
TarzanParPanels.laser_panel = _par_laser_panel_final
TarzanParPanels.matrix = _par_matrix_final
TarzanParPanels.matrix_panel = _par_matrix_final
TarzanParPanels.lcd = _par_lcd_final
TarzanParPanels.lcd_panel = _par_lcd_final
TarzanParPanels.keyboard = _par_keyboard_final
TarzanParPanels.keyboard_panel = _par_keyboard_final
TarzanParPanels.limits = _par_limits_led_logic_final_v3
TarzanParPanels.sensors = _par_sensors_led_logic_final
TarzanParPanels.functions_panel = _par_functions_panel_led_logic_final
TarzanParPanels.functions = _par_functions_panel_led_logic_final
TarzanParPanels.all_signals = _tarzan_all_signals_final_v5
TarzanParPanels.poextbus_cnc = _par_poextbus_cnc_led_logic_final
TarzanParPanels.ui = _tarzan_ui_panel_v2
TarzanParPanels.ui_panel = _tarzan_ui_panel_v2
TarzanParPanels.mass_regulator_panel = _tarzan_mass_regulator_panel_v2
TarzanParPanels.lamp_panel = _par_lamp_panel_final
TarzanParPanels.level_xyz_panel = _par_level_xyz_panel_final
TarzanParPanels.bridge = _tarzan_bridge_csv
TarzanParPanels.automatyka_panel = _tarzan_automatyka_panel_v2
TarzanParPanels.cnc_signals_panel = _tarzan_cnc_signals_panel_v3
TarzanParPanels.operator = _tarzan_rrp_panel_v2
TarzanParPanels.sok_panel = _tarzan_sok_panel_v3
TarzanParPanels.autostatus = _tarzan_auto_panel_v2
TarzanParPanels.dron = _tarzan_dron_panel_v2
TarzanParPanels.dron_panel = _tarzan_dron_panel_v2
