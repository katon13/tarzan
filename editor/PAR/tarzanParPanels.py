from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any, Callable
import math
import time

from core.tarzanSignalBus import TarzanSignalBus, TarzanSignalState
try:
    from editor.PAR.tarzanParWidgets import COLORS, AxisCard, Led, Panel, SignalRow
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, AxisCard, Led, Panel, SignalRow

try:
    from editor.PAR.tarzanNextionPreview import TarzanNextionPreviewPanel
except ModuleNotFoundError:
    from tarzanNextionPreview import TarzanNextionPreviewPanel

try:
    from core.tarzanProfiler import profile_method, profile_block
except Exception:
    def profile_method(name=None):
        def deco(func): return func
        return deco
    class profile_block:
        def __init__(self, name): self.name = name
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

try:
    from core.tarzanAssets import axis_icon
except Exception:
    axis_icon = None

# =====================================================================
# KONFIGURACJA I MAPOWANIA (1:1 Z ORYGINAŁEM)
# =====================================================================

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
    "CAM_H": {"step": ["TAKE_CAM_H_STEP", "rec_p01_copy_ctr_cam_h", "cnc_x_cam_h_ctr"], "dir": ["TAKE_CAM_H_DIR", "rec_p03_copy_dir_cam_h", "cnc_x_cam_h_dir"], "en": [], "left": ["cam_h_limit_left", "play_p06_cam_h_limit_left"], "right": ["cam_h_limit_right", "play_p05_cam_h_limit_right"]},
    "CAM_V": {"step": ["TAKE_CAM_V_STEP", "rec_p02_copy_ctr_cam_v", "cnc_y_cam_v_ctr"], "dir": ["TAKE_CAM_V_DIR", "rec_p04_copy_dir_cam_v", "cnc_y_cam_v_dir"], "en": [], "left": ["cam_v_limit_down", "play_p08_cam_v_limit_down"], "right": ["cam_v_limit_up", "play_p07_cam_v_limit_up"]},
    "CAM_T": {"step": ["TAKE_CAM_T_STEP", "rec_p06_copy_ctr_tilt", "cnc_a_arm_tilt_ctr", "play_p49_step_ctr_arm_tilt"], "dir": ["TAKE_CAM_T_DIR", "rec_p08_copy_dir_tilt", "cnc_a_arm_tilt_dir", "play_p40_step_dir_arm_tilt"], "en": [], "left": ["cam_tilt_limit", "play_p10_cam_tilt_limit"], "right": ["cam_tilt_limit", "play_p10_cam_tilt_limit"]},
    "CAM_F": {"step": ["TAKE_CAM_F_STEP", "rec_p05_copy_ctr_focus", "cnc_z_focus_ctr"], "dir": ["TAKE_CAM_F_DIR", "rec_p07_copy_dir_focus", "cnc_z_focus_dir"], "en": [], "left": [], "right": []},
    "ARM_H": {"step": ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "rec_p15_rec_ctr_arm_h", "cnc_b_arm_h_ctr"], "dir": ["TAKE_ARM_H_DIR", "play_p38_step_dir_arm_h", "rec_p12_rec_dir_arm_h", "cnc_b_arm_h_dir"], "en": ["play_p50_step_en_arm_h"], "left": ["arm_h_limit_left", "play_p03_arm_h_limit_left"], "right": ["arm_h_limit_right", "play_p01_arm_h_auto_limit", "play_p02_arm_h_limit_right"]},
    "ARM_V": {"step": ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "rec_p16_rec_ctr_arm_v", "cnc_c_arm_v_ctr"], "dir": ["TAKE_ARM_V_DIR", "play_p39_step_dir_arm_v", "rec_p13_rec_dir_arm_v", "cnc_c_arm_v_dir"], "en": ["play_p51_step_en_arm_v"], "left": ["arm_v_limit_down", "play_p04_arm_v_limit_up"], "right": ["arm_v_limit_up", "play_p09_arm_v_auto_limit"]},
    "DRON": {"step": ["TAKE_DRON_STEP"], "dir": ["TAKE_DRON_DIR"], "en": [], "left": [], "right": []},
}

_AXIS_TIMELINE_ROWS = [
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

_LINKED_SIGNAL_GROUPS = {
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
    "rec_p53_copy_cam_v_limit_up": ["rec_p53_copy_cam_v_limit_up", "play_p07_cam_v_limit_up"],
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

_VIOLET_NAME_PARTS = ("kb", "lcd_", "i2c_", "led_data", "led_latch", "led_clk", "poextbus", "res", "free")
_GRAY_NAME_PARTS = ("bridge_",)

_AXIS_ICON_DESCRIPTIONS = {
    "ARM_H": "oś pozioma ramienia",
    "ARM_V": "oś pionowa ramienia",
    "CAM_H": "oś pozioma kamery",
    "CAM_V": "oś pionowa kamery",
    "CAM_T": "oś pochyłu kamery",
    "CAM_F": "oś ostrości kamery",
}

_AXIS_ICON_NAMES = {
    "ARM_H": "oś pozioma ramienia",
    "ARM_V": "oś pionowa ramienia",
    "CAM_H": "oś pozioma kamery",
    "CAM_V": "oś pionowa kamery",
    "CAM_T": "oś pochyłu kamery",
    "CAM_F": "oś ostrości kamery",
}

_TIMELINE_HISTORY_LIMIT = 600
_TIMELINE_POINTS_LIMIT = 140
_TIMELINE_H_COLOR = COLORS.get("red", "#ff2b22")
_TIMELINE_L_COLOR = COLORS.get("muted", "#a9b5bd")
_TIMELINE_DEBOUNCE_MS = 80

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

class _ParMassLedV14(tk.Canvas):
    def __init__(self, parent, color_on: str, size: int = 24):
        super().__init__(parent, width=size, height=size, bg=COLORS.get("panel3", "#0c1217"), highlightthickness=0, bd=0)
        self.size = size
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
        self.create_rectangle(2, 2, self.size-2, self.size-2, fill=fill, outline=border, width=2)

_ALL_SIGNALS_PASSIVE = {
    "play_p17_bridge_rec_dir_x", "play_p18_bridge_rec_dir_y", "play_p19_bridge_rec_dir_z",
    "play_p20_bridge_rec_ctr_x", "play_p21_bridge_rec_ctr_y", "play_p22_bridge_rec_ctr_z",
    "rec_p17_bridge_play_dir_x", "rec_p18_bridge_play_dir_y", "rec_p19_bridge_play_dir_z",
    "rec_p20_bridge_play_ctr_x", "rec_p21_bridge_play_ctr_y", "rec_p22_bridge_play_ctr_z",
    "rec_p37_bridge_play_rec_in", "rec_p54_bridge_play_rec_out", "play_p55_bridge_rec_enable",
}

# =====================================================================
# POMOCNICZE KLASY I PROXY
# =====================================================================

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
        if current is None: return
        if isinstance(current, list):
            for proxy in list(current):
                try: proxy.set(value)
                except Exception: pass
            return
        try: current.set(value)
        except Exception: pass

class _ParValueProxy:
    def __init__(self, callback): self.callback = callback
    def set(self, value):
        try: self.callback(value)
        except Exception: pass

class _CsvProxy:
    def __init__(self, fn): self.fn = fn
    def set(self, value):
        try: self.fn(value)
        except Exception: pass

# =====================================================================
# GŁÓWNA KLASA PANELI PAR
# =====================================================================

class TarzanParPanels:
    def __init__(self, app, bus: TarzanSignalBus) -> None:
        self.app = app
        self.bus = bus
        self.rows: Dict[str, Any] = _RowRegistry()
        self.axis_cards: Dict[str, AxisCard] = {}
        self.log_text: Optional[tk.Text] = None
        self.timeline_canvas: Optional[tk.Canvas] = None
        self._timeline_icon_cache = {}
        self._timeline_after_id = None
        self.nextion_preview_widgets = {}
        self._last_log_snapshot = ()
        self._rrp_operator_updaters = []
        self._last_rrp_refresh_rev = None
        self._last_preview_state = {}
        
        # Centralny system RRP
        self._rrp_start_ts = time.time()

    def panel(self, key: str, parent, title: str) -> Panel:
        return Panel(parent, title=title, on_hide=lambda: self.app.hide_panel(key))

    def _register_signal_proxy(self, name: str, callback: Callable[[Any], None]):
        self.rows[name] = _ParValueProxy(callback)

    def _scroll_body(self, panel: Panel):
        """Nowoczesny przewijalny korpus panelu z obsługą kółka myszy (v5)."""
        canvas = tk.Canvas(panel.body, bg=COLORS['panel'], highlightthickness=0, bd=0)
        inner = tk.Frame(canvas, bg=COLORS['panel'])
        window_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        def _on_inner_configure(_e=None):
            try: canvas.configure(scrollregion=canvas.bbox('all'))
            except Exception: pass

        def _on_canvas_configure(e):
            try:
                canvas.itemconfigure(window_id, width=e.width)
                canvas.configure(scrollregion=canvas.bbox('all'))
            except Exception: pass

        def _on_mousewheel(event):
            try:
                if getattr(event, 'delta', 0):
                    delta = int(-1 * (event.delta / 120))
                    if delta: canvas.yview_scroll(delta, 'units')
                elif getattr(event, 'num', None) == 4: canvas.yview_scroll(-1, 'units')
                elif getattr(event, 'num', None) == 5: canvas.yview_scroll(1, 'units')
            except Exception: pass
            return 'break'

        def _bind_mousewheel_recursive(widget):
            try:
                widget.bind('<MouseWheel>', _on_mousewheel, add='+')
                widget.bind('<Button-4>', _on_mousewheel, add='+')
                widget.bind('<Button-5>', _on_mousewheel, add='+')
                for child in widget.winfo_children(): _bind_mousewheel_recursive(child)
            except Exception: pass

        inner.bind('<Configure>', lambda e: (_on_inner_configure(e), _bind_mousewheel_recursive(inner)), add='+')
        canvas.bind('<Configure>', _on_canvas_configure)
        panel.body.bind('<MouseWheel>', _on_mousewheel, add='+')
        _bind_mousewheel_recursive(canvas)
        
        canvas.pack(fill='both', expand=True)
        return inner

    # --- SEKCA: OSIE I SILNIKI ---

    def axes(self, parent):
        panel = self.panel("axes", parent, "OSIE — KARTY SILNIKÓW")
        cards_frame = tk.Frame(panel.body, bg=COLORS["panel"])
        cards_frame.pack(fill="both", expand=True)
        
        axes_list = [
            ("ARM_H", "1. OŚ POZIOMA RAMIENIA", "↔"),
            ("ARM_V", "2. OŚ PIONOWA RAMIENIA", "↕"),
            ("CAM_H", "3. OŚ POZIOMA KAMERY", "⟳"),
            ("CAM_V", "4. OŚ PIONOWA KAMERY", "↕"),
            ("CAM_T", "5. OŚ POCHYŁU KAMERY", "↧"),
            ("CAM_F", "6. OŚ OSTROŚCI KAMERY", "◎"),
        ]

        for col, (key, title, fallback) in enumerate(axes_list):
            icon_path = None
            if axis_icon:
                try:
                    desc = _AXIS_ICON_DESCRIPTIONS.get(key, "")
                    icon_path = axis_icon(desc, size=64, state="active", ext="png")
                except Exception: pass

            card = AxisCard(
                cards_frame,
                title,
                fallback,
                image_path=icon_path,
                on_step_left=lambda a=key: self._manual_axis_step(a, 0),
                on_step_right=lambda a=key: self._manual_axis_step(a, 1),
            )
            card.grid(row=0, column=col, sticky="nsew", padx=5, pady=4)
            cards_frame.grid_columnconfigure(col, weight=1)
            self.axis_cards[key] = card

        # FIX: Tytuł CAM_H
        card_h = self.axis_cards.get("CAM_H")
        if card_h:
            for child in card_h.winfo_children():
                if isinstance(child, tk.Label) and "OŚ POZIOMA KAMERY" in str(child.cget("text")):
                    child.configure(text="3. OŚ POZIOMA KAMERY")

        # FIX: CAM_T STOP label
        card_t = self.axis_cards.get("CAM_T")
        if card_t:
            try:
                left_p = getattr(card_t.end_left, 'master', None)
                if left_p:
                    for c in left_p.winfo_children():
                        if isinstance(c, tk.Label): c.configure(text="STOP")
                right_p = getattr(card_t.end_right, 'master', None)
                if right_p:
                    for c in right_p.winfo_children():
                        if isinstance(c, tk.Label): c.configure(text="")
            except Exception: pass

        # Integracja Mass Regulatora na ARM_V
        card_v = self.axis_cards.get("ARM_V")
        if card_v:
            try:
                led_row = card_v.en.master.master
                add_led = self._add_mass_led_box(led_row, "+MASA", COLORS["amber"])
                rem_led = self._add_mass_led_box(led_row, "−MASA", COLORS["blue"])
                def update_mass_leds(_v=None):
                    add = bool(self.bus.get("par_mass_reg_limit_add") or self.bus.get("play_p13_mass_reg_limit_add"))
                    rem = bool(self.bus.get("par_mass_reg_limit_remove") or self.bus.get("play_p23_mass_reg_limit_remove"))
                    add_led.set(add)
                    rem_led.set(rem)
                for s in ["par_mass_reg_limit_add", "play_p13_mass_reg_limit_add", "par_mass_reg_limit_remove", "play_p23_mass_reg_limit_remove"]:
                    self.rows[s] = _ParValueProxy(update_mass_leds)
                update_mass_leds()
            except Exception: pass

        self.refresh_axis_cards()
        return panel

    def refresh_axis_cards(self):
        for axis, card in self.axis_cards.items():
            bind = AXIS_SIGNAL_BINDINGS.get(axis, {})
            card.set_step(self._first_value(bind.get("step", [])))
            card.set_dir(self._first_value(bind.get("dir", [])))
            en_names = bind.get("en", [])
            card.set_en(self._first_value(en_names) if en_names else 1)
            card.set_end_left(self._first_value(bind.get("left", [])))
            card.set_end_right(self._first_value(bind.get("right", [])))

            # Logger silnika (v2/final)
            def _mk_logger(ax_key, c_ref):
                def _logger():
                    try: self.bus.log("PAR_MOTOR", f"{ax_key}: DIR={1 if c_ref.dir.state else 0} STEP=01")
                    except Exception: pass
                return _logger
            card.on_motor_step_log = _mk_logger(axis, card)

            # Specjalna obsługa CAM_T Home Limit
            if axis == "CAM_T":
                try:
                    left_p = getattr(card.end_left, "master", None)
                    right_p = getattr(card.end_right, "master", None)
                    if left_p:
                        for ch in left_p.winfo_children():
                            if isinstance(ch, tk.Label): ch.configure(text="STOP")
                    if right_p:
                        for ch in right_p.winfo_children():
                            if isinstance(ch, tk.Label): ch.configure(text="")
                except Exception: pass
                val = 1 if (self.bus.get("cam_tilt_limit") or self.bus.get("play_p10_cam_tilt_limit")) else 0
                card.set_end_left(val)
                card.set_end_right(0)

    # --- SEKCA: OPERATOR (RRP) ---

    def operator(self, parent):
        panel = self.panel("operator", parent, "STEROWANIE OPERATORA (RRP)")
        root = tk.Frame(panel.body, bg=COLORS["panel"])
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        self._rrp_operator_updaters = []

        axis_map = {
            "CAM_V": {"step": ["TAKE_CAM_V_STEP", "rec_p02_copy_ctr_cam_v", "cnc_y_cam_v_ctr"], "dir": ["TAKE_CAM_V_DIR", "rec_p04_copy_dir_cam_v", "cnc_y_cam_v_dir"]},
            "CAM_T": {"step": ["TAKE_CAM_T_STEP", "rec_p06_copy_ctr_tilt", "cnc_a_arm_tilt_ctr", "play_p49_step_ctr_arm_tilt"], "dir": ["TAKE_CAM_T_DIR", "rec_p08_copy_dir_tilt", "cnc_a_arm_tilt_dir", "play_p40_step_dir_arm_tilt"]},
            "CAM_F": {"step": ["TAKE_CAM_F_STEP", "rec_p05_copy_ctr_focus", "cnc_z_focus_ctr"], "dir": ["TAKE_CAM_F_DIR", "rec_p07_copy_dir_focus", "cnc_z_focus_dir"]},
            "CAM_H": {"step": ["TAKE_CAM_H_STEP", "rec_p01_copy_ctr_cam_h", "cnc_x_cam_h_ctr"], "dir": ["TAKE_CAM_H_DIR", "rec_p03_copy_dir_cam_h", "cnc_x_cam_h_dir"]},
            "ARM_H": {"step": ["TAKE_ARM_H_STEP", "play_p46_step_ctr_arm_h", "rec_p15_rec_ctr_arm_h", "cnc_b_arm_h_ctr"], "dir": ["TAKE_ARM_H_DIR", "play_p38_step_dir_arm_h", "rec_p12_rec_dir_arm_h", "cnc_b_arm_h_dir"]},
            "ARM_V": {"step": ["TAKE_ARM_V_STEP", "play_p48_step_ctr_arm_v", "rec_p16_rec_ctr_arm_v", "cnc_c_arm_v_ctr"], "dir": ["TAKE_ARM_V_DIR", "play_p39_step_dir_arm_v", "rec_p13_rec_dir_arm_v", "cnc_c_arm_v_dir"]},
        }
        axis_idx_to_name = {0: "CAM_V", 1: "CAM_T", 2: "CAM_F", 3: "CAM_H", 4: "ARM_H", 5: "ARM_V"}

        def knob(cell, title, signal, player):
            box = tk.Frame(cell, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)
            box.pack(fill="both", expand=True, padx=4, pady=4)
            tk.Label(box, text=title, bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).pack(fill="x")

            # Potencjometr RRP startuje od 0 (zgodnie z oryginałem)
            state = {"value": float(self.bus.get(signal, 0)), "after_id": None, "last_step_val": -1}

            val_lbl = tk.Label(box, text="0", bg="#0f171d", fg=COLORS["green"], font=("Consolas", 18, "bold"), pady=4)
            val_lbl.pack(fill="x", padx=6)

            axis_frame = tk.Frame(box, bg=COLORS["panel3"])
            axis_frame.pack(pady=2)
            
            axis_icon_lbl = tk.Label(axis_frame, bg=COLORS["panel3"])
            axis_icon_lbl.pack(side="left", padx=2)
            
            axis_lbl = tk.Label(axis_frame, text="STOP", bg=COLORS["panel3"], fg="#5f6b72", font=("Segoe UI", 10, "bold"))
            axis_lbl.pack(side="left", padx=2)

            can = tk.Canvas(box, width=122, height=122, bg=COLORS["panel3"], highlightthickness=0, takefocus=True)
            can.pack(pady=10)

            def drw(v=None):
                if v is not None:
                    state["value"] = max(0.0, min(4095.0, float(v)))
                can.delete("all")
                cx, cy, r = 61, 61, 40
                can.create_arc(cx-r, cy-r, cx+r, cy+r, start=225, extent=270, style="arc", outline="#5f6b72", width=8)
                frac = state["value"] / 4095.0
                angle_deg = 225 + 270 * frac
                angle = math.radians(angle_deg)
                x = cx + math.cos(angle) * (r - 5)
                y = cy - math.sin(angle) * (r - 5)
                
                bridge_axis = int(self.bus.get(f"par_rrp_{player}_axis", -1))
                is_active = (bridge_axis != -1)
                
                knob_color = COLORS["red"] if is_active else "#5f6b72"
                can.create_oval(cx-26, cy-26, cx+26, cy+26, fill="#101820", outline=COLORS["border"], width=2)
                can.create_line(cx, cy, x, y, fill=knob_color, width=4, capstyle=tk.ROUND)
                can.create_oval(cx-5, cy-5, cx+5, cy+5, fill="#dfe6e9", outline="#111")
                
                axis_name = axis_idx_to_name.get(bridge_axis, "STOP")
                axis_lbl.configure(text=axis_name, fg=COLORS["red"] if is_active else "#5f6b72")
                val_lbl.configure(text=str(int(state["value"])))
                
                # Zespolenie ikon osi
                if is_active and axis_icon:
                    try:
                        desc = _AXIS_ICON_DESCRIPTIONS.get(axis_name, "")
                        path = axis_icon(desc, size=32, state="active")
                        img = self._load_timeline_icon(axis_name) # używamy cache z timeline lub ładujemy małą
                        axis_icon_lbl.configure(image=img)
                        axis_icon_lbl.image = img
                    except Exception: 
                        axis_icon_lbl.configure(image="")
                else:
                    axis_icon_lbl.configure(image="")

            def gen_tick():
                try:
                    pot_val = float(self.bus.get(signal, 0))
                    sens = float(self.bus.get(f"par_rrp_{player}_sens", 50))
                    intensity = (pot_val / 4095.0) * (sens / 100.0)
                    
                    if intensity > 0.01:
                        delay = max(20, int(40 / intensity)) # Skalowanie dla większej płynności (20-400ms)
                        bridge_axis = int(self.bus.get(f"par_rrp_{player}_axis", -1))
                        axis_name = axis_idx_to_name.get(bridge_axis)
                        
                        if axis_name in axis_map:
                            cfg = axis_map[axis_name]
                            direction = int(self.bus.get(f"par_rrp_{player}_dir", 0))
                            
                            for d_sig in cfg["dir"]:
                                self.bus.force_signal(d_sig, direction, source="PAR_GEN")
                            
                            self._pulse_many_signals(cfg["step"], delay_ms=int(delay * 0.4), src="PAR_GEN")
                            
                            step_val = int(intensity * 100)
                            if abs(step_val - state["last_step_val"]) >= 2: # Debouncing aktualizacji Nextiona
                                state["last_step_val"] = step_val
                                self.bus.set_input(f"par_rrp_{player}_val", step_val, source="PAR_GEN")
                            
                            state["after_id"] = self.app.after(delay, gen_tick)
                            return
                            
                    state["after_id"] = self.app.after(50, gen_tick)
                except Exception:
                    state["after_id"] = self.app.after(200, gen_tick)

            def on_wheel(event):
                delta = 0
                if getattr(event, "delta", 0):
                    delta = 1 if event.delta > 0 else -1
                elif getattr(event, "num", None) == 4:
                    delta = 1
                elif getattr(event, "num", None) == 5:
                    delta = -1
                if delta:
                    nv = max(0, min(4095, int(state["value"] + delta * 128)))
                    state["value"] = nv
                    self.bus.force_signal(signal, nv, source="PAR_RRP_POT")
                    drw()
                return "break"

            for w in (can, box, val_lbl, axis_lbl, axis_icon_lbl):
                w.bind("<MouseWheel>", on_wheel)
                w.bind("<Button-4>", on_wheel)
                w.bind("<Button-5>", on_wheel)
                w.bind("<Enter>", lambda e, target=can: target.focus_set())
            
            box.bind("<Destroy>", lambda e: self.app.after_cancel(state["after_id"]) if state.get("after_id") else None)

            self._register_signal_proxy(f"par_rrp_{player}_axis", lambda v: drw())
            self._register_signal_proxy(signal, lambda v: drw(v))
            self._rrp_operator_updaters.append(drw)
            
            drw()
            gen_tick()

        l_f = tk.Frame(root, bg=COLORS["panel"]); l_f.grid(row=0, column=0, sticky="nsew")
        r_f = tk.Frame(root, bg=COLORS["panel"]); r_f.grid(row=0, column=1, sticky="nsew")
        knob(l_f, "POTENCJOMETR RRP X (P1)", "play_p45_rrp_pot_h", "p1")
        knob(r_f, "POTENCJOMETR RRP Y (P2)", "play_p47_rrp_pot_v", "p2")
        return panel

    # --- SEKCA: SOK (STEROWNIK OBROTOWY) ---

    def sok_panel(self, parent):
        panel = self.panel('sok', parent, 'SOK — STEROWNIK OBROTOWY KURKOWY')
        grid = tk.Frame(panel.body, bg=COLORS['panel'])
        grid.pack(fill='both', expand=True)
        for i in range(2):
            grid.grid_rowconfigure(i, weight=1)
            grid.grid_columnconfigure(i, weight=1)

        sections = [
            ('SOKPan', 'rec_p17_bridge_play_dir_x', 'rec_p20_bridge_play_ctr_x', (), ()),
            ('SOKTilt', 'rec_p18_bridge_play_dir_y', 'rec_p21_bridge_play_ctr_y', (), ()),
            ('SOKFokus', 'rec_p07_copy_dir_focus', 'rec_p05_copy_ctr_focus', (), ('FOKUS', 'POCHYŁ')),
            ('SOKCam', 'rec_p04_copy_dir_cam_v', 'rec_p02_copy_ctr_cam_v', (), ('POZIOM', 'PION')),
        ]

        def draw_section(p_grid, title, ds, cs, extras, opts):
            box = tk.Frame(p_grid, bg=COLORS['panel3'], highlightthickness=1, highlightbackground="#333")
            tk.Label(box, text=title, bg=COLORS['panel3'], fg="white", font=("Segoe UI", 9, "bold")).pack(pady=2)
            
            mode_var = tk.StringVar(value=opts[0] if opts else '')
            if opts:
                mode_buttons = []
                r = tk.Frame(box, bg=COLORS['panel3']);
                r.pack(fill='x', padx=4)

                def paint_mode_buttons():
                    for opt, btn in mode_buttons:
                        active = mode_var.get() == opt
                        btn.configure(
                            bg=COLORS["green"] if active else COLORS["button"],
                            fg="#061006" if active else COLORS["text"],
                        )

                for o in opts:
                    btn = tk.Button(
                        r,
                        text=o,
                        bg=COLORS['button'],
                        fg=COLORS['text'],
                        activebackground=COLORS['button'],
                        activeforeground=COLORS['text'],
                        font=('Segoe UI', 7, 'bold'),
                        command=lambda v=o: (mode_var.set(v), paint_mode_buttons()),
                    )
                    btn.pack(side='left', expand=1, fill='x', padx=1)
                    mode_buttons.append((o, btn))

                paint_mode_buttons()

            can = tk.Canvas(box, width=80, height=80, bg=COLORS['panel3'], highlightthickness=0); can.pack()
            st = {"a": 0}
            
            def dr(ang=0):
                can.delete("all"); cx, cy, r = 40, 40, 30
                can.create_oval(cx-r, cy-r, cx+r, cy+r, fill='#101820', outline='#8d99a3', width=2)
                rd = math.radians(ang)
                for j in range(24):
                    a = math.radians(j * 15 + ang)
                    x1 = cx + math.cos(a) * (r - 2)
                    y1 = cy + math.sin(a) * (r - 2)
                    x2 = cx + math.cos(a) * (r - 10)
                    y2 = cy + math.sin(a) * (r - 10)
                    can.create_line(x1, y1, x2, y2, fill='#dfe6e9', width=2)
                can.create_line(cx, 8, cx, 18, fill=COLORS['red'], width=4, capstyle=tk.ROUND)
            
            def step(d):
                st["a"] = (st["a"] + (30 if d else -30)) % 360; dr(st["a"])
                m = mode_var.get()
                sig_map = {
                    'PAN':   (['rec_p03_copy_dir_cam_h', 'cnc_x_cam_h_dir'], ['rec_p01_copy_ctr_cam_h', 'cnc_x_cam_h_ctr']),
                    'TILT':  (['rec_p04_copy_dir_cam_v', 'cnc_y_cam_v_dir'], ['rec_p02_copy_ctr_cam_v', 'cnc_y_cam_v_ctr']),
                    'FOKUS': (['rec_p07_copy_dir_focus', 'cnc_z_focus_dir'], ['rec_p05_copy_ctr_focus', 'cnc_z_focus_ctr']),
                    'POCHYŁ':(['rec_p08_copy_dir_tilt', 'cnc_a_arm_tilt_dir'], ['rec_p06_copy_ctr_tilt', 'cnc_a_arm_tilt_ctr']),
                    'POZIOM':(['rec_p03_copy_dir_cam_h'], ['rec_p01_copy_ctr_cam_h']),
                    'PION':  (['rec_p04_copy_dir_cam_v'], ['rec_p02_copy_ctr_cam_v']),
                }
                dirs, ctrs = sig_map.get(m, ([ds], [cs]))
                for n in dirs: self.bus.force_signal(n, d, source="PAR_SOK")
                self._pulse_many_signals(ctrs, delay_ms=70, src="PAR_SOK")

            btns = tk.Frame(box, bg=COLORS['panel3']); btns.pack(fill='x', padx=4, pady=4)
            tk.Button(
                btns,
                text="L",
                bg=COLORS["button"],
                fg=COLORS["text"],
                activebackground=COLORS["green"],
                activeforeground="#061006",
                command=lambda: step(0),
            ).pack(side="left", expand=1, fill="x")

            tk.Button(
                btns,
                text="R",
                bg=COLORS["button"],
                fg=COLORS["text"],
                activebackground=COLORS["green"],
                activeforeground="#061006",
                command=lambda: step(1),
            ).pack(side="left", expand=1, fill="x")
            dr(); return box

        for idx, (t, ds, cs, ex, op) in enumerate(sections):
            b = draw_section(grid, t, ds, cs, ex, op)
            b.grid(row=idx//2, column=idx%2, sticky="nsew", padx=4, pady=4)
        return panel

    # --- SEKCA: INFO I LOGI ---

    def info_panel(self, parent):
        panel = self.panel("info", parent, "PANEL INFORMACYJNY")
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

    # --- SEKCA: SYGNAŁY ---

    def all_signals(self, parent):
        panel = self.panel('all_signals', parent, 'WSZYSTKIE SYGNAŁY')
        inner = self._scroll_body(panel)
        for name in self.bus.names():
            self._csv_signal_row(inner, name, self._all_signals_label(name), mode="auto")
        return panel

    def limits(self, parent):
        panel = self.panel("limits", parent, "KRAŃCÓWKI")
        body = tk.Frame(panel.body, bg=COLORS["panel"])
        body.pack(fill="both", expand=True)
        raw = self._group_or_search("KRAŃCÓWKI", ["limit"])
        names, seen = [], set()
        for n in raw:
            lbl = self.limit_label(n)
            if any(k in f"{n} {lbl}".upper() for k in ("WOLNY", "FREE")): continue
            if lbl.upper() in seen: continue
            seen.add(lbl.upper()); names.append(n)
        
        cols = 3
        for i, n in enumerate(names):
            cell = tk.Frame(body, bg=COLORS["panel"])
            cell.grid(row=i//cols, column=i%cols, sticky="ew", padx=3, pady=1)
            cell.grid_columnconfigure(1, weight=1)
            
            bl = self._signal_blocked(n)
            led = Led(cell, size=17, bg=COLORS["panel"], blocked=bl)
            led.grid(row=0, column=0, sticky="w", padx=(0, 4))
            led.set(self.bus.get(n))
            
            l = tk.Label(cell, text=self.limit_label(n), bg=COLORS["panel"], fg=COLORS["muted"] if bl else COLORS["text"], font=("Segoe UI", 8), anchor="w")
            l.grid(row=0, column=1, sticky="ew")
            
            self.rows[n] = _ParValueProxy(led.set)
            if self._signal_clickable_input(n):
                def clk(_e, name=n): self.bus.toggle_input(name, source="PAR_LIMIT")
                for w in (cell, led, l): w.bind("<Button-1>", clk)
        for i in range(cols): body.grid_columnconfigure(i, weight=1, uniform="limit_col")
        return panel

    def sensors(self, parent):
        panel = self.panel("sensors", parent, "CZUJNIKI / ANALOG / I2C")
        body = self._scroll_body(panel)
        for n in self._group_or_search("CZUJNIKI", ["sw_", "sensor", "i2c_", "pot_", "analog"]):
            meta = self.bus.get_meta(n)
            if meta and getattr(meta, "is_input", False) and ("pot_" in n or "analog" in n):
                self._analog_row(body, n, self.sensor_label(n))
            else:
                self._csv_signal_row(body, n, self.sensor_label(n))
        return panel

    # --- SEKCA: CZUJNIKI SPECJALNE ---

    def level_xyz_panel(self, parent):
        panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ (MMA7660)")
        body = tk.Frame(panel.body, bg=COLORS["panel"])
        body.pack(fill="both", expand=True)
        w, h = 138, 94
        canvas = tk.Canvas(body, width=w, height=h, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
        canvas.pack(side="left", padx=(0, 9), pady=1)
        v_f = tk.Frame(body, bg=COLORS["panel"]); v_f.pack(side="left", fill="both", expand=True)
        st = {"x": float(self.bus.get("par_level_x") or 0), "y": float(self.bus.get("par_level_y") or 0), "z": float(self.bus.get("par_level_z") or 100)}
        vrs = {a: tk.StringVar(value=f"{a} +0") for a in ("X", "Y", "Z")}

        def clamp(v): return max(-100.0, min(100.0, float(v)))
        def calc_z(x, y): return math.sqrt(max(0, 10000 - (x*x + y*y)))

        def draw():
            canvas.delete("all"); cx, cy = w//2, h//2
            x, y, z = clamp(st["x"]), clamp(st["y"]), clamp(st["z"])
            canvas.create_line(9, cy, w-9, cy, fill="#31414a")
            canvas.create_line(cx, 8, cx, h-8, fill="#31414a")
            ox, oy = x*0.08, y*0.08
            canvas.create_polygon(28+ox, 28-oy, 110+ox, 30+oy, 108-ox, 70+oy, 30-ox, 68-oy, fill="#0d222c", outline="#386271", width=2)
            px, py, sz = cx+(x/100)*44, cy-(y/100)*31, 7+(max(0,z)/100)*3
            canvas.create_oval(px-sz, py-sz, px+sz, py+sz, fill=COLORS["green"], outline="#061006")
            for a in "XYZ": vrs[a].set(f"{a} {int(round(st[a.lower()])):+d}")

        def set_a(a, v):
            st[a] = clamp(v)
            if a in ("x", "y"): st["z"] = calc_z(st["x"], st["y"]); self.bus.set_input("par_level_z", st["z"])
            self.bus.set_input(f"par_level_{a}", st[a], source="PAR_XYZ"); draw()

        cx, cy = w//2, h//2
        for a in ("X", "Y", "Z"):
            r = tk.Frame(v_f, bg=COLORS["panel"]); r.pack(fill="x")
            tk.Label(r, textvariable=vrs[a], bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 13, "bold"), anchor="w", width=6).pack(side="left")
            for t, d in [("X", None), ("+", 1), ("-", -1)]:
                tk.Button(
                    r,
                    text=t,
                    width=2,
                    bg=COLORS["button"],
                    fg=COLORS["green"],
                    activebackground=COLORS["button"],
                    activeforeground=COLORS["green"],
                    command=lambda aa=a.lower(), dd=d: set_a(aa, 0 if dd is None else st[aa] + dd),
                ).pack(side="right", padx=1)

        def drag(e): set_a("x", (e.x-cx)/44*100); set_a("y", -(e.y-cy)/31*100)
        canvas.bind("<B1-Motion>", drag); draw(); return panel

    def _par_click_sensor_panel(self, parent, *, key, title, signal, on_text, off_text, led_size=72):
        panel = self.panel(key, parent, title)
        led = Led(panel.body, size=led_size, bg=COLORS["panel"])
        led.pack(pady=10)
        lbl = tk.Label(panel.body, text=off_text, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10, "bold"))
        lbl.pack(pady=5)
        def dr(v=None):
            val = self.bus.get(signal) if v is None else v
            led.set(val); lbl.configure(text=on_text if val else off_text, fg=COLORS["green"] if val else COLORS["text"])
        def tg(_e=None): v=1-(1 if self.bus.get(signal) else 0); self.bus.set_input(signal, v); dr(v)
        for w in (led, lbl, panel.body): w.bind("<Button-1>", tg)
        self.rows[signal] = _ParValueProxy(dr); dr(); return panel

    def _par_canvas_sensor_slider_panel(self, parent, *, key, title, signal, unit, start, end, decimals=0):
        panel = self.panel(key, parent, title)
        w = tk.Frame(panel.body, bg=COLORS["panel"]); w.pack(fill="both", expand=True)
        h, cw = 88, 38
        can = tk.Canvas(w, width=cw, height=h, bg=COLORS["panel"], highlightthickness=0)
        can.pack(side="left", padx=(0, 7))
        v_l = tk.Label(w, text="", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 15, "bold"))
        v_l.pack(side="left", fill="both", expand=True)
        def clamp(v): return max(float(start), min(float(end), float(v)))
        def fmt(v): fv = clamp(v); return f"{fv:.{decimals}f} {unit}" if decimals else f"{int(round(fv))} {unit}"
        def dr(v=None):
            curr = clamp(v if v is not None else self.bus.get(signal, start))
            can.delete("all"); can.create_rectangle(14, 5, 24, h-5, fill=COLORS["green"], outline="#063c0a")
            y = 7 + (float(end)-curr)/(max(1.0, float(end)-float(start)))*(h-14)
            can.create_rectangle(5, y-7, 33, y+7, fill="#7b1730", outline="#d65c78", width=2)
            v_l.configure(text=fmt(curr))
        def dg(e): nv = float(end) - ((max(7, min(h-7, e.y))-7)/(h-14))*(max(1.0, float(end)-float(start))); self.bus.set_input(signal, nv); dr(nv)
        can.bind("<B1-Motion>", dg); self.rows[signal] = _ParValueProxy(dr); dr(); return panel

    def temperature_panel(self, p): return self._par_canvas_sensor_slider_panel(p, key="temp", title="TEMPERATURA (\u00b0C)", signal="par_temperature_c", unit="\u00b0C", start=-20, end=50, decimals=1)
    def light_bh1750_panel(self, p): return self._par_canvas_sensor_slider_panel(p, key="light", title="ŚWIATŁO (BH1750)", signal="par_bh1750_lux", unit="lx", start=0, end=120000)
    def shock_sensor_panel(self, p): return self._par_click_sensor_panel(p, key="shock", title="SHOK", signal="par_shock_sensor_state", on_text="WSTRZĄS WYKRYTY", off_text="BRAK WSTRZĄSÓW")
    def laser_panel(self, p): return self._par_click_sensor_panel(p, key="laser", title="LASER", signal="par_laser_set", on_text="LASER ON", off_text="LASER OFF")

    def automatyka_panel(self, parent):
        panel = self.panel("automatyka", parent, "AUTOMATYKA")
        can = tk.Canvas(panel.body, width=80, height=80, bg=COLORS["panel"], highlightthickness=0)
        can.pack(pady=5)

        def draw_bolt(v):
            can.delete("all")
            glow = "#5a1613" if v else "#2c343a"
            body = COLORS["red"] if v else "#66707a"
            can.create_oval(8, 8, 70, 70, fill=glow, outline="")
            can.create_polygon([39, 12, 26, 39, 34, 39, 29, 65, 53, 31, 42, 31, 50, 12], fill=body, outline="#111",
                               width=1)

        sig = "par_manual_disconnect"
        draw_bolt(self.bus.get(sig, 0))

        def tg(_e):
            nv = 0 if self.bus.get(sig, 0) else 1
            self._set_signal(sig, nv)
            draw_bolt(nv)

        can.bind("<Button-1>", tg)
        self._register_signal_proxy(sig, draw_bolt)
        return panel

    def _analog_row(self, parent, name, label):
        frame = tk.Frame(parent, bg=COLORS["panel"])
        frame.pack(fill="x", pady=3)
        tk.Label(frame, text="▰", bg=COLORS["panel"], fg=COLORS["amber"], width=2).pack(side="left")
        tk.Label(frame, text=label, bg=COLORS["panel"], fg=COLORS["text"], width=22, anchor="w").pack(side="left")
        val_lbl = tk.Label(frame, text=str(self.bus.get(name, 0)), bg=COLORS["panel"], fg=COLORS["green"], width=7)
        val_lbl.pack(side="right")
        
        def on_scale(v):
            v_int = int(float(v))
            self._set_signal(name, v_int)
            val_lbl.config(text=str(v_int))
            
        scale = tk.Scale(frame, from_=0, to=4095, orient="horizontal", bg=COLORS["panel"], troughcolor="#263741",
                         fg=COLORS["text"], highlightthickness=0, showvalue=False,
                         command=on_scale)
        scale.set(self.bus.get(name, 0))
        scale.pack(side="right", fill="x", expand=True, padx=5)
        self._register_signal_proxy(name, lambda v: [scale.set(v), val_lbl.config(text=str(v))])
        return frame

    def _set_signal(self, name, value, source="PAR_SIM"):
        try:
            m = self.bus.get_meta(name)
            if not m:
                self.bus.force_signal(name, value, source=source)
                return
            if getattr(m, "is_input", False) or name.startswith("par_"):
                self.bus.set_input(name, value, source=source)
            else:
                self.bus.write_output(name, value, source=source)
        except Exception: pass

    def _final_force_or_toggle(self, name: str):
        try:
            curr = self.bus.get(name, 0)
            nv = 1 if curr == 0 else 0
            self._set_signal(name, nv)
        except Exception: pass

    def _final_signal_style(self, name: str):
        lower = (name or "").lower()
        meta = self.bus.get_meta(name)
        if name == "play_p15_rrp_dir_h_res": return "neutral"
        if name in _ALL_SIGNALS_PASSIVE or "bridge_" in lower: return "gray"
        if lower.startswith("cnc_"): return "gray"
        if any(k in lower for k in ("kb", "lcd_", "i2c_", "led_data", "led_latch", "led_clk", "poextbus")): return "violet"
        if any(k in lower for k in ("_res", "free_", "_free")): return "violet"
        if meta and (getattr(meta, "is_forbidden", False) or getattr(meta, "typ", "") in {"F", "RESERVED"} or getattr(meta, "kierunek", "") in {"F", "RESERVED"}):
            return "violet"
        return "normal"

    def _all_signals_clickable(self, name: str):
        if name in _ALL_SIGNALS_PASSIVE: return False
        if name in _ALL_SIGNALS_FORCE_CLICK: return True
        meta = self.bus.get_meta(name)
        if meta is None: return True
        if getattr(meta, "is_input", False): return True
        return False

    def _all_signals_label(self, name: str):
        if name in _SIGNAL_LABEL_OVERRIDES: return _SIGNAL_LABEL_OVERRIDES[name]
        meta = self.bus.get_meta(name)
        board = str(meta.plytka).upper() if (meta and meta.plytka) else ""
        pin = str(meta.pin if (meta and meta.pin is not None) else (meta.kanal if meta and meta.kanal else "-")).upper()
        opis = " ".join(str(meta.opis or "").split()) if meta else ""
        extra = ""
        lower = name.lower()
        if name in _ALL_SIGNALS_PASSIVE or "bridge_" in lower: extra = "  [MOSTEK]"
        elif any(k in lower for k in ("_res", "free_", "_free")): extra = "  [REZERWA]"
        elif lower.startswith("cnc_"): extra = "  [CNC]"

        # zmiana wyswielania nazwy
        #if opis: return f"{board} {pin}  {name}  {opis}{extra}"
        #return f"{board} {pin}  {name}{extra}"

        if opis: return f"{board} {pin}  {name}"
        return f"{board} {pin}  {name}"

    def _csv_signal_row(self, parent, name, label, mode="normal", clickable=None):
        f = tk.Frame(parent, bg=COLORS["panel"])
        f.pack(fill="x", pady=1)

        style = mode if mode != "auto" else self._final_signal_style(name)
        is_clickable = clickable if clickable is not None else self._all_signals_clickable(name)
        meta = self.bus.get_meta(name)

        # Diody po lewej ( side="left" ) 1:1 z oryginałem
        led = Led(f, size=22, bg=COLORS["panel"], blocked=(style=="violet"))
        led.pack(side="left", padx=(5, 10))
        led.set(self.bus.get(name, 0))
        self.rows[name] = _ParValueProxy(led.set)

        fg = COLORS.get(style, COLORS["text"]) if style in {"violet", "gray"} else COLORS["text"]
        lbl = tk.Label(f, text=label, bg=COLORS["panel"], fg=fg, anchor="w", font=("Segoe UI", 10))
        lbl.pack(side="left", fill="x", expand=True)

        if meta and meta.typ == "ANALOG":
            # Suwak dla sygnałów analogowych
            sc = tk.Scale(f, from_=0, to=255, orient="horizontal", showvalue=0, width=8,
                        bg=COLORS["panel"], highlightthickness=0, command=lambda v: self._set_signal(name, int(v)))
            sc.set(self.bus.get(name, 0))
            sc.pack(side="right", padx=5)
            sc.configure(length=60)
            self.rows[name] = _ParValueProxy(lambda v, s=sc, l=led: (s.set(v), l.set(v)))

        if is_clickable:
            def clk(e): self._final_force_or_toggle(name)
            for w in (f, lbl, led): 
                w.bind("<Button-1>", clk)
                w.configure(cursor="hand2")
        return f

    def _add_mass_led_box(self, parent, label, col):
        f = tk.Frame(parent, bg=COLORS["panel3"], padx=4)
        f.pack(side="left", padx=2, fill="x", expand=True)
        tk.Label(f, text=label, fg=col, bg=COLORS["panel3"], font=("Segoe UI", 8, "bold")).pack()
        led = _ParMassLedV14(f, color_on=col, size=24)
        led.pack(pady=2)
        return led

    def _manual_axis_step(self, ax, dir):
        b = AXIS_SIGNAL_BINDINGS.get(ax, {})
        for n in b.get("dir", []): self.bus.force_signal(n, dir, source="PAR_STEP")
        self._pulse_many_signals(b.get("step", []), src="PAR_STEP")

    def _pulse_many_signals(self, names, delay_ms=10, src="PAR_PULSE"):
        for n in names:
            self.bus.force_signal(n, 1, source=src)
            self.app.after(delay_ms, lambda name=n: self.bus.force_signal(name, 0, source=src))

    def _first_value(self, names: List[str]):
        for n in names:
            if self.bus.exists(n): return 1 if self.bus.get(n) else 0
        return 0

    def _group_or_search(self, group: str, needles: List[str]):
        res = []
        for name in self.bus.names():
            m = self.bus.get_meta(name)
            if (m and m.grupa == group) or any(k in name.lower() for k in needles): res.append(name)
        return sorted(list(set(res)))

    def limit_label(self, name: str): return LIMIT_LABELS.get(name, name.upper().replace("_", " "))
    def sensor_label(self, name: str): return SENSOR_LABELS.get(name, name.upper().replace("_", " "))

    def _signal_blocked(self, n): m = self.bus.get_meta(n); return bool(m and getattr(m, "is_forbidden", False))
    def _signal_clickable_input(self, n): m = self.bus.get_meta(n); return bool(m and m.is_input)

    # --- SYNCHRONIZACJA I TIMELINE ---

    def on_state_change(self, name, state):
        val = state.value
        self.rows.set_value(name, val)
        
        # Linki sygnałów
        if name in _LINKED_SIGNAL_GROUPS:
            for extra in _LINKED_SIGNAL_GROUPS[name]:
                if extra != name and self.bus.exists(extra):
                    if self.bus.get(extra) != val:
                        self.bus.force_signal(extra, val, source="PAR_LINK_SYNC")

        # Specyficzne linki dla osi i innych grup (1:1 z oryginałem)
        try:
            if name in {"play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"}:
                for extra in ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"]:
                    if extra != name and self.bus.exists(extra):
                        self.bus.force_signal(extra, val, source="PAR_LINK")
            elif name in {"play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"}:
                for extra in ["play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"]:
                    if extra != name and self.bus.exists(extra):
                        self.bus.force_signal(extra, val, source="PAR_LINK")
            elif name in {"play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"}:
                for extra in ["play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"]:
                    if extra != name and self.bus.exists(extra):
                        self.bus.force_signal(extra, val, source="PAR_LINK")
            elif name in {"par_lamp_auto_active", "play_p16_action_led"}:
                for extra in ["par_lamp_auto_active", "play_p16_action_led"]:
                    if extra != name and self.bus.exists(extra):
                        self.bus.force_signal(extra, val, source="PAR_LINK")
            elif name in {"par_shock_sensor_state", "rec_p39_shock_sensor"}:
                for extra in ["par_shock_sensor_state", "rec_p39_shock_sensor"]:
                    if extra != name and self.bus.exists(extra):
                        self.bus.force_signal(extra, val, source="PAR_LINK")
        except Exception: pass

        # Odświeżanie kart osi (wizualizacja Step/Dir) - DEBOUNCED
        for b in AXIS_SIGNAL_BINDINGS.values():
            if any(name in group for group in b.values()):
                now = time.time()
                if now - getattr(self, "_last_axis_card_refresh", 0) > 0.1: # max 10 FPS dla kart osi (oszczędność CPU)
                    self._last_axis_card_refresh = now
                    self.refresh_axis_cards()
                break

        # Timeline
        for i, (ax, mode, signals, color) in enumerate(_AXIS_TIMELINE_ROWS):
            if name in signals:
                if val != state.previous_value:
                    self._schedule_timeline_redraw()
                break

    def timeline(self, parent):
        p = self.panel("timeline", parent, "PODGLĄD SYGNAŁÓW — STEP / DIR")
        self.timeline_canvas = tk.Canvas(p.body, bg="#070b0e", height=210, highlightthickness=0)
        self.timeline_canvas.pack(fill="both", expand=True, pady=4)
        self.timeline_canvas.bind("<Configure>", lambda e: self.draw_timeline())
        self.draw_timeline()
        return p

    def _schedule_timeline_redraw(self):
        if not self._timeline_after_id:
            self._timeline_after_id = self.app.after(_TIMELINE_DEBOUNCE_MS, self._do_draw_timeline)

    def _do_draw_timeline(self):
        self._timeline_after_id = None
        self.draw_timeline()

    def _axis_icon_path(self, axis_key: str):
        if not axis_icon: return None
        try: return axis_icon(_AXIS_ICON_NAMES.get(axis_key, axis_key), size=64, state="active", ext="png")
        except Exception: return None

    def _load_timeline_icon(self, axis_key: str):
        if not hasattr(self, "_timeline_icon_cache"): self._timeline_icon_cache = {}
        if axis_key in self._timeline_icon_cache: return self._timeline_icon_cache[axis_key]
        path = self._axis_icon_path(axis_key)
        photo = None
        if path:
            try:
                from pathlib import Path as _Path
                if _Path(path).exists():
                    photo = tk.PhotoImage(file=str(path))
                    if photo.width() > 36:
                        factor = max(1, int(round(photo.width() / 32)))
                        photo = photo.subsample(factor, factor)
            except Exception: photo = None
        self._timeline_icon_cache[axis_key] = photo
        return photo

    def draw_timeline(self):
        can = self.timeline_canvas
        if not can: return
        can.delete("all")
        w, h = max(can.winfo_width(), 760), max(can.winfo_height(), 210)
        left, right = 100, w - 14
        top, row_h = 12, max(15, min(22, int((h - 28) / 12)))
        amp, total_h = max(5, min(9, row_h - 7)), row_h * 12
        hist = list(self.bus.history)[-_TIMELINE_HISTORY_LIMIT:]
        buckets = {tuple(names): [] for _ax, _ki, names, _col in _AXIS_TIMELINE_ROWS}
        name_to_bucket = {}
        for key in buckets:
            for n in key: name_to_bucket[n] = key
        for item in hist:
            k = name_to_bucket.get(item.get("name"))
            if k: buckets[k].append(item)

        mid_x = left + (right - left) / 2
        for t in range(6):
            x = left + t * ((right - left) / 5)
            can.create_line(x, top - 3, x, top + total_h + 2, fill="#162129")
        can.create_line(mid_x, top - 5, mid_x, top + total_h + 4, fill="#ff2b22", width=1)
        for idx, (axis, kind, names, color) in enumerate(_AXIS_TIMELINE_ROWS):
            y = top + idx * row_h + row_h // 2
            if kind == "STEP":
                sep_y = max(top, y - row_h // 2)
                can.create_line(4, sep_y, right, sep_y, fill="#101a20")
                icon = self._load_timeline_icon(axis)
                if icon: can.create_image(35, y + row_h // 2, image=icon, anchor="center")
                else: can.create_text(35, y + row_h // 2, text=axis, anchor="center", fill=COLORS["muted"], font=("Segoe UI", 7, "bold"))
            cur = 1 if any(self.bus.get(n) for n in names) else 0
            can.create_text(58, y, text="S" if kind == "STEP" else "D", anchor="center", fill=color, font=("Segoe UI", 7, "bold"))
            can.create_text(75, y, text="H" if cur else "L", anchor="center", fill=_TIMELINE_H_COLOR if cur else _TIMELINE_L_COLOR, font=("Segoe UI", 7, "bold"))
            can.create_line(left, y, right, y, fill="#22313a")
            
            filtered = buckets.get(tuple(names), [])[-_TIMELINE_POINTS_LIMIT:]
            points = []
            if filtered:
                step_x = max(1, (right - left) / max(1, len(filtered) - 1))
                for j, item in enumerate(filtered):
                    val = 1 if item.get("value") else 0
                    vx = left + j * step_x
                    points.append((vx, y - amp if val else y))
            else:
                points = [(left, y - amp if cur else y), (right, y - amp if cur else y)]

            if len(points) >= 2:
                for a, b in zip(points, points[1:]):
                    can.create_line(a[0], a[1], b[0], a[1], fill=color, width=2)
                    can.create_line(b[0], a[1], b[0], b[1], fill=color, width=2)
        if (top + total_h + 8) < h:
            can.create_text(left, h - 8, text="czerwona linia = chwila odczytu; H/L = aktualny stan STEP/DIR", anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7))
        if (top + total_h + 8) < h:
            can.create_text(left, h - 8, text="czerwona linia = chwila odczytu; H/L = aktualny stan STEP/DIR", anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7))

    # --- POZOSTAŁE PANELE ---

    def ui_panel(self, p): return self.ui(p)
    def ui(self, parent):
        p = self.panel("ui", parent, "UI PANEL PLAY / REC")
        g = tk.Frame(p.body, bg=COLORS["panel"])
        g.pack(fill="x")
        btns = [("F1", "rec_p45_sw_f1", "rec_p46_led_f1"), ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
                ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"), ("F4", "rec_p51_sw_f4", "rec_p52_led_f4")]
        for i, (l, sw, ls) in enumerate(btns):
            c = tk.Frame(g, bg="#0f171d", highlightbackground="#30424f", highlightthickness=1)
            c.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            led = Led(c, size=28, bg="#0f171d")
            led.pack(pady=(7, 4))
            led.set(self.bus.get(ls))

            b = tk.Button(
                c,
                text=l,
                bg="#1a242d",
                fg="#f2f7fb",
                activebackground=COLORS["green"],
                activeforeground="#061006",
                relief="flat",
                font=("Segoe UI", 16, "bold"),
                height=2,
            )

            b.pack(fill="x", padx=7, pady=(0, 3))
            
            # Podkreślenie aktywnego klawisza
            f_led = tk.Frame(c, bg="#30424f", height=4)
            f_led.pack(fill="x", padx=7, pady=(0, 7))

            b.bind("<ButtonPress-1>", lambda e, s=sw: self._set_signal(s, 1, "PAR_UI"))
            b.bind("<ButtonRelease-1>", lambda e, s=sw: self._set_signal(s, 0, "PAR_UI"))
            b.bind("<Leave>", lambda e, s=sw: self._set_signal(s, 0, "PAR_UI"))
            
            self.rows[ls] = _ParValueProxy(lambda v, ld=led: ld.set(v))
            self.rows[sw] = _ParValueProxy(lambda v, bt=b, fl=f_led: (
                bt.configure(bg=COLORS["green"] if v else "#1a242d", fg="#061006" if v else "#f2f7fb"),
                fl.configure(bg=COLORS["green"] if v else "#30424f")
            ))
        for i in range(4): g.grid_columnconfigure(i, weight=1)
        return p

    def mass_regulator_panel(self, parent):
        p = self.panel("mass_regulator", parent, "REGULATOR MASY")
        eb = tk.Frame(p.body, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)
        eb.pack(fill="x", pady=(0, 6))
        el = Led(eb, size=26, bg=COLORS["panel3"])
        el.pack(pady=6)
        bs = tk.Frame(p.body, bg=COLORS["panel"])
        bs.pack(fill="x")
        ba = tk.Button(bs, text="DODAJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"))
        ba.pack(side="left", expand=1, fill="both", padx=(0, 4), pady=2)
        br = tk.Button(bs, text="UJMIJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"))
        br.pack(side="left", expand=1, fill="both", padx=(4, 0), pady=2)
        
        def sm(m):
            va = 1 if (m=="A" and not self.bus.get("par_mass_reg_limit_add")) else 0
            vr = 1 if (m=="R" and not self.bus.get("par_mass_reg_limit_remove")) else 0
            ve = 1 if (va or vr) else 0
            for s, v in [("par_mass_reg_limit_add", va), ("play_p13_mass_reg_limit_add", va),
                         ("par_mass_reg_limit_remove", vr), ("play_p23_mass_reg_limit_remove", vr),
                         ("par_mass_reg_enable", ve), ("play_p41_mass_reg_enable", ve), ("rec_p36_mass_reg_enable", ve)]:
                self.bus.force_signal(s, v, source="PAR_MASS_EXCLUSIVE")
        
        ba.configure(command=lambda: sm("A"))
        br.configure(command=lambda: sm("R"))
        
        def pt(_v=None):
            en = self.bus.get("par_mass_reg_enable")
            eb.configure(bg="#143d16" if en else COLORS["panel3"])
            el.set(en)
            ba.configure(bg=COLORS["green"] if self.bus.get("par_mass_reg_limit_add") else COLORS["button"], fg="#061006" if self.bus.get("par_mass_reg_limit_add") else COLORS["text"])
            br.configure(bg=COLORS["blue"] if self.bus.get("par_mass_reg_limit_remove") else COLORS["button"], fg="#061006" if self.bus.get("par_mass_reg_limit_remove") else COLORS["text"])
            
        for s in ["par_mass_reg_enable", "play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_limit_add", "play_p13_mass_reg_limit_add", "par_mass_reg_limit_remove", "play_p23_mass_reg_limit_remove"]:
            self.rows[s] = _ParValueProxy(pt)
        pt(); return p

    def dron(self, p):
        pan = self.panel("dron", p, "DRON")
        r = tk.Frame(pan.body, bg=COLORS["panel"]); r.pack(fill="x", padx=6, pady=4)
        tk.Label(r, text="ZWOLNIENIE", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 13, "bold")).pack(side="left")
        led = Led(r, size=28, bg=COLORS["panel"]); led.pack(side="right"); led.set(self.bus.get("play_p14_drone_release"))
        tk.Button(
            pan.body,
            text="ZWOLNIJ DRONA",
            bg="#7a251f",
            fg="white",
            font=("Segoe UI", 14, "bold"),
            height=2,
            command=lambda: self.bus.toggle_input("play_p14_drone_release"),
        ).pack(fill="x", pady=5)
        self.rows["play_p14_drone_release"] = _ParValueProxy(led.set); return pan

    def bridge(self, p):
        pan = self.panel("bridge", p, "MOSTEK (BRIDGE)")
        b = self._scroll_body(pan)
        for n in [n for n in self.bus.names() if "bridge_" in n.lower()]: self._csv_signal_row(b, n, n.upper(), mode="gray")
        return pan

    def lamp_panel(self, p):
        pan = self.panel("lamp", p, "PRACA")
        canvas = tk.Canvas(pan.body, width=100, height=70, bg=COLORS["panel"], highlightthickness=0)
        canvas.pack(anchor="center", padx=6, pady=6)
        state = {"value": 1 if self.bus.get("par_lamp_auto_active") else 0}

        def draw(v=None):
            if v is not None:
                state["value"] = 1 if v else 0
            canvas.delete("all")
            color = COLORS["red"] if state["value"] else "#5b6268"
            glow = "#5a1613" if state["value"] else "#20282d"
            canvas.create_rectangle(5, 8, 95, 62, fill=glow, outline="")
            canvas.create_rectangle(13, 15, 87, 55, fill=color, outline="#111", width=2)
            canvas.create_rectangle(18, 19, 44, 28, fill="#ffffff", outline="", stipple="gray50")

        def toggle(_event=None):
            self.bus.toggle_input("par_lamp_auto_active", source="PAR_LAMP")

        canvas.bind("<Button-1>", toggle)
        pan.body.bind("<Button-1>", toggle)
        draw()
        self.rows["par_lamp_auto_active"] = _ParValueProxy(draw)
        return pan

    def poextbus_cnc(self, p):
        pan = self.panel("poextbus_cnc", p, "POEXTBUS CNC")
        b = self._scroll_body(pan)
        for n in [n for n in self.bus.names() if "poextbus" in n.lower()]: self._csv_signal_row(b, n, n.upper(), mode="violet")
        return pan
    def poextbus(self, p): return self.poextbus_cnc(p)
    def functions(self, p):
        pan = self.panel("functions", p, "FUNKCJE / REZERWY")
        b = self._scroll_body(pan)
        for n in [n for n in self.bus.names() if any(k in n.lower() for k in ("res", "free", "spare"))]:
            self._csv_signal_row(b, n, self._all_signals_label(n), mode="violet")
        return pan

    def lcd(self, parent):
        panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="x")

        def lcd_box(title, sig1, sig2, default1, default2):
            box = tk.Frame(wrap, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
            box.pack(fill="x", pady=4)
            tk.Label(
                box,
                text=title,
                bg="#07110a",
                fg=COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
                anchor="w",
            ).pack(fill="x", padx=7, pady=(4, 0))

            row = tk.Frame(box, bg="#07110a")
            row.pack(fill="x", padx=7, pady=(3, 6))

            display = tk.Frame(row, bg="#07110a")
            display.pack(side="left", fill="both", expand=True)

            line1 = tk.StringVar(value=str(self.bus.get(sig1, default1))[:16])
            line2 = tk.StringVar(value=str(self.bus.get(sig2, default2))[:16])

            e1 = tk.Entry(
                display,
                textvariable=line1,
                bg="#0b1c10",
                fg="#38ff6a",
                insertbackground="#38ff6a",
                font=("Consolas", 12, "bold"),
                relief="flat",
                width=16,
            )
            e2 = tk.Entry(
                display,
                textvariable=line2,
                bg="#0b1c10",
                fg="#38ff6a",
                insertbackground="#38ff6a",
                font=("Consolas", 12, "bold"),
                relief="flat",
                width=16,
            )
            e1.pack(fill="x", pady=(0, 2))
            e2.pack(fill="x")

            def send():
                l1 = line1.get()[:16].ljust(16)
                l2 = line2.get()[:16].ljust(16)
                line1.set(l1)
                line2.set(l2)

                self._set_signal(sig1, l1, "PAR_LCD")
                self._set_signal(sig2, l2, "PAR_LCD")

                if title.upper().startswith("PLAY"):
                    self._set_signal("par_lcd_line1", l1, "PAR_LCD")
                    self._set_signal("par_lcd_line2", l2, "PAR_LCD")

                self.bus.log("LCD1602", f"{title} SEND |{l1}| |{l2}|")

            tk.Button(
                row,
                text="SEND",
                bg=COLORS["green"],
                fg="#061006",
                activebackground="#43ff4e",
                relief="raised",
                font=("Segoe UI", 8, "bold"),
                width=5,
                command=send,
            ).pack(side="right", padx=(6, 0), fill="y")

        lcd_box("PLAY LCD 1602", "par_lcd_play_line1", "par_lcd_play_line2", "TARZAN PLAY", "READY")
        lcd_box("REC LCD 1602", "par_lcd_rec_line1", "par_lcd_rec_line2", "TARZAN REC", "READY")
        return panel

    def matrix(self, parent):
        panel = self.panel("matrix", parent, "MATRIX LED 8x8")
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
            self._set_signal("par_matrix_pattern", pattern, "PAR_MATRIX")
            self.bus.log("MATRIX_LED", f"UPDATE {pattern}")

        tk.Button(holder, text="UPDATE MATRIX", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=update).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return panel

    def keyboard(self, parent):
        pan = self.panel("keyboard", parent, "KLAWIATURA")
        g = tk.Frame(pan.body, bg=COLORS["panel"])
        g.pack(anchor="center")
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for i, k in enumerate(keys):
            tk.Button(
                g,
                text=k,
                bg="#202b33",
                fg=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 12, "bold"),
                width=3,
                height=1,
                command=lambda val=k: self.bus.log("KEYBOARD", f"KEY {val}")
            ).grid(row=i // 3, column=i % 3, sticky="nsew", padx=3, pady=3)
        for i in range(3):
            g.grid_columnconfigure(i, weight=1)
        return pan

    def settings(self, p):
        pan = self.panel("settings", p, "USTAWIENIA PULPITU")
        b = tk.Frame(pan.body, bg=COLORS["panel"], padx=10, pady=10); b.pack(fill="x")
        
        # Statystyki sesji
        uptime = int(time.time() - getattr(self.app, 'start_time', time.time()))
        tk.Label(b, text=f"UPTIME: {uptime}s", bg=COLORS["panel"], fg=COLORS["green"]).pack(anchor="w")
        
        debug_var = tk.BooleanVar(value=getattr(self.bus, 'debug_override_outputs', False))
        def tg_db(): self.bus.debug_override_outputs = bool(debug_var.get()); self.bus.log("PAR", f"DEBUG override OUT = {self.bus.debug_override_outputs}")
        tk.Checkbutton(b, text="DEBUG override OUT", variable=debug_var, command=tg_db, bg=COLORS["panel"], fg=COLORS["text"], selectcolor="#101820").pack(anchor="w", pady=3)
        tk.Button(b, text="RESET SYGNAŁÓW", bg="#7a251f", fg="white", command=self.bus.reset_to_defaults).pack(fill="x", pady=5)
        tk.Button(b, text="SAVE LAYOUT", bg=COLORS["button"], fg="white", command=self.app.save_layout).pack(fill="x", pady=5)
        return pan

    def take(self, p):
        pan = self.panel("take", p, "TAKE — ODTWARZACZ PROTOKOŁU")

        top = tk.Frame(pan.body, bg=COLORS["panel"])
        top.pack(fill="x")

        center = tk.Frame(top, bg=COLORS["panel"])
        center.pack(anchor="center", pady=2)

        tk.Button(center, text="LOAD", bg="#d7dde2", fg="#101820", font=("Segoe UI", 11, "bold"), width=8,
                  height=1, command=self.app.load_take_dialog).pack(side="left", padx=5, pady=3)
        for txt, cmd, bg, fg in [
            ("PLAY", self.app.play_take, COLORS["green"], "#061006"),
            ("PAUSE", self.app.pause_take, "#bf8b18", "#ffffff"),
            ("STOP", self.app.stop_take, "#ae241d", "#ffffff"),
        ]:
            tk.Button(center, text=txt, bg=bg, fg=fg, font=("Segoe UI", 12, "bold"), width=8, height=1,
                      command=cmd).pack(side="left", padx=5, pady=3)

        self.app.take_label = tk.Label(
            pan.body,
            text="TAKE: brak",
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 14),
        )
        self.app.take_label.pack(fill="x", pady=8)

        return pan

    def camera(self, p):
        panel = self.panel("camera", p, "KAMERA I KHR")
        b = tk.Frame(panel.body, bg=COLORS["panel"], padx=8, pady=8); b.pack(fill="x")
        tk.Button(b, text="OPEN KHR", bg=COLORS["button"], command=lambda: self.bus.toggle_input("par_khr_open")).pack(fill="x", pady=2)
        tk.Button(b, text="REC START/STOP", bg="#7a251f", fg="white", command=lambda: self.bus.toggle_input("par_camera_rec")).pack(fill="x", pady=2)
        return panel

    def autostatus(self, parent):
        panel = self.panel("autostatus", parent, "AUTO STATUS")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="both", expand=True)

        sig = "par_auto_mode"

        led = Led(wrap, size=62, bg=COLORS["panel"])
        led.pack(anchor="center", pady=10)
        led.set(self.bus.get(sig, 0))

        def click(_e=None):
            nv = 0 if self.bus.get(sig, 0) else 1
            self.bus.force_signal(sig, nv, source="PAR_AUTO_WINDOW")
            led.set(nv)

        led.bind("<Button-1>", click)
        wrap.bind("<Button-1>", click)

        self.rows[sig] = _ParValueProxy(led.set)
        return panel

    def system(self, p):
        panel = self.panel("system", p, "SYSTEM")
        b = tk.Frame(panel.body, bg=COLORS["panel"], padx=10, pady=10); b.pack(fill="x")
        tk.Label(b, text="TARZAN OS v2.4", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(b, text="CPU: 12%", bg=COLORS["panel"], fg=COLORS["green"]).pack(anchor="w")
        tk.Label(b, text="IP: 192.168.1.10", bg=COLORS["panel"], fg=COLORS["muted"]).pack(anchor="w")
        return panel

    def update_log(self):
        if not self.log_text: return
        self.log_text.delete("1.0", tk.END)
        for line in self.bus.log_lines[-50:]:
            self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)

    def log_panel(self, p):
        panel = self.panel("log", p, "LOGI")
        self.log_text = tk.Text(panel.body, height=8, bg="#070b0e", fg=COLORS["green"], font=("Consolas", 8)); self.log_text.pack(fill="both", expand=True)
        return panel

    def cnc_signals_panel(self, p):
        panel = self.panel("cnc", p, "CNC")
        b = self._scroll_body(panel)
        for n in [n for n in self.bus.names() if n.startswith("cnc_")]:
            self._csv_signal_row(b, n, str(n).upper(), mode="gray", clickable=False)
        return panel

    def functions_panel(self, p): return self.functions(p)
    def take_control(self, p): return self.take(p)
    def dron_panel(self, p): return self.dron(p)

    def nextion_5_preview(self, parent):
        panel = self.panel("nextion_5_preview", parent, "NEXTION 5")
        bridge = self.app.bridge.nextion if hasattr(self.app.bridge, "nextion") and self.app.bridge.nextion is not None else self.app.bridge
        widget = TarzanNextionPreviewPanel(panel.body, bridge, "nextion_5", "NEXTION 5 — PODGLĄD")
        widget.pack(fill="both", expand=True)
        self.nextion_preview_widgets["nextion_5"] = widget
        return panel

    def nextion_7_preview(self, parent):
        panel = self.panel("nextion_7_preview", parent, "NEXTION 7")
        bridge = self.app.bridge.nextion if hasattr(self.app.bridge, "nextion") and self.app.bridge.nextion is not None else self.app.bridge
        widget = TarzanNextionPreviewPanel(panel.body, bridge, "nextion_7", "NEXTION 7 — PODGLĄD")
        widget.pack(fill="both", expand=True)
        self.nextion_preview_widgets["nextion_7"] = widget
        return panel

    def nextion_refresh_previews(self):
        bridge = self.app.bridge.nextion if hasattr(self.app.bridge, "nextion") and self.app.bridge.nextion is not None else self.app.bridge
        snapshot = bridge.snapshot() if hasattr(bridge, "snapshot") else {}

        rrp_rev = snapshot.get("nextion_7.rrp_rev")
        if rrp_rev != self._last_rrp_refresh_rev:
            self._last_rrp_refresh_rev = rrp_rev
            for updater in list(getattr(self, "_rrp_operator_updaters", [])):
                try:
                    updater()
                except Exception:
                    pass

        for screen_key, widget in list(self.nextion_preview_widgets.items()):
            state_key = (
                snapshot.get(f"{screen_key}.connected"),
                snapshot.get(f"{screen_key}.page"),
                snapshot.get(f"{screen_key}.rrp_rev"),
                snapshot.get(f"{screen_key}.log_last"),
                snapshot.get("par_level_x"),
                snapshot.get("par_level_y"),
            )
            if self._last_preview_state.get(screen_key) == state_key:
                continue
            self._last_preview_state[screen_key] = state_key
            try:
                widget.refresh()
            except Exception:
                pass
