from __future__ import annotations
from core.tarzanSnajper import create_default_tarzan_snajper, NextionPhysicalSnajperAdapter

import json
import time
import tkinter as tk
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tkinter import filedialog, messagebox, ttk

from core.tarzanSignalBus import get_signal_bus
try:
    from core.tarzanParBridge import TarzanParBridge
except ModuleNotFoundError:
    try:
        from editor.PAR.tarzanParBridge import TarzanParBridge
    except ModuleNotFoundError:
        from tarzanParBridge import TarzanParBridge
try:
    from editor.PAR.tarzanParPanels import TarzanParPanels
except ModuleNotFoundError:
    from tarzanParPanels import TarzanParPanels
try:
    from editor.PAR.tarzanParWidgets import COLORS, apply_dark_style
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, apply_dark_style

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
    "take": True,
    "info": True,
    "log": True,
    "limits": True,
    "sensors": True,
    "operator": True,
    "ui": True,
    "bridge": True,
    "poextbus": True,
    "functions": True,
    "timeline": True,
    "dron": True,
    "lcd": True,
    "matrix": True,
    "keyboard": True,
    "camera": True,
    "autostatus": True,
    "system": True,
    "settings": True,
    "all_signals": False,    "lamp": True,
    "mass_regulator": True,
    "shock_sensor_panel": True,
    "light_bh1750": True,
    "level_xyz": True,
    "temperature": True,
    "laser": True,
    "sok": True,
    "cnc_signals": True,
    "automatyka": True,
    "nextion_7_preview": True,

}

DEFAULT_PANEL_ZONES = {
    "axes": "top",
    "take": "right",
    "info": "right",
    "log": "right",
    "limits": "middle_top",
    "sensors": "middle_top",
    "operator": "middle_top",
    "ui": "middle_top",
    "bridge": "middle_bottom",
    "poextbus": "middle_bottom",
    "functions": "middle_bottom",
    "timeline": "bottom",
    "dron": "right",
    "lcd": "right",
    "matrix": "right",
    "keyboard": "right",
    "camera": "right",
    "autostatus": "right",
    "system": "right",
    "settings": "right",
    "all_signals": "left",    "lamp": "middle_top",
    "mass_regulator": "middle_top",
    "shock_sensor_panel": "middle_top",
    "light_bh1750": "middle_top",
    "level_xyz": "middle_top",
    "temperature": "middle_top",
    "laser": "middle_top",
    "sok": "middle_top",
    "cnc_signals": "middle_bottom",
    "automatyka": "middle_top",
    "nextion_7_preview": "right",

}

DEFAULT_PANEL_LAYOUT = {
    "axes": {"zone": "top", "order": 10, "colspan": 12, "rowspan": 2},
    "take": {"zone": "right", "order": 10, "colspan": 4, "rowspan": 1},
    "info": {"zone": "right", "order": 20, "colspan": 4, "rowspan": 1},
    "log": {"zone": "right", "order": 30, "colspan": 4, "rowspan": 2},
    "dron": {"zone": "right", "order": 40, "colspan": 4, "rowspan": 1},
    "lcd": {"zone": "right", "order": 50, "colspan": 4, "rowspan": 1},
    "matrix": {"zone": "right", "order": 60, "colspan": 4, "rowspan": 2},
    "keyboard": {"zone": "right", "order": 70, "colspan": 4, "rowspan": 2},
    "camera": {"zone": "right", "order": 80, "colspan": 4, "rowspan": 1},
    "autostatus": {"zone": "right", "order": 90, "colspan": 4, "rowspan": 1},
    "system": {"zone": "right", "order": 100, "colspan": 4, "rowspan": 1},
    "settings": {"zone": "right", "order": 110, "colspan": 4, "rowspan": 1},
    "all_signals": {"zone": "left", "order": 10, "colspan": 4, "rowspan": 3},
    "limits": {"zone": "middle_top", "order": 10, "colspan": 3, "rowspan": 2},
    "sensors": {"zone": "middle_top", "order": 20, "colspan": 3, "rowspan": 2},
    "operator": {"zone": "middle_top", "order": 30, "colspan": 3, "rowspan": 1},
    "ui": {"zone": "middle_top", "order": 40, "colspan": 3, "rowspan": 1},
    "bridge": {"zone": "middle_bottom", "order": 10, "colspan": 3, "rowspan": 1},
    "poextbus": {"zone": "middle_bottom", "order": 20, "colspan": 4, "rowspan": 1},
    "functions": {"zone": "middle_bottom", "order": 30, "colspan": 4, "rowspan": 1},
    "timeline": {"zone": "bottom", "order": 10, "colspan": 8, "rowspan": 2},    "lamp": {"zone": "middle_top", "order": 50, "colspan": 2, "rowspan": 2},
    "mass_regulator": {"zone": "middle_top", "order": 60, "colspan": 3, "rowspan": 2},
    "shock_sensor_panel": {"zone": "middle_top", "order": 70, "colspan": 2, "rowspan": 2},
    "light_bh1750": {"zone": "middle_top", "order": 80, "colspan": 2, "rowspan": 2},
    "level_xyz": {"zone": "middle_top", "order": 90, "colspan": 3, "rowspan": 2},
    "temperature": {"zone": "middle_top", "order": 100, "colspan": 2, "rowspan": 2},
    "laser": {"zone": "middle_top", "order": 110, "colspan": 2, "rowspan": 2},
    "automatyka": {"zone": "middle_top", "order": 55, "colspan": 2, "rowspan": 2},
    "sok": {"zone": "middle_top", "order": 120, "colspan": 3, "rowspan": 6},
    "cnc_signals": {"zone": "middle_bottom", "order": 5, "colspan": 4, "rowspan": 3},
    "nextion_7_preview": {"zone": "right", "order": 130, "colspan": 4, "rowspan": 4},

}


DEFAULT_GRID = {
    "top_columns": 12,
    "middle_top_columns": 12,
    "middle_bottom_columns": 12,
    "bottom_columns": 12,
    "right_columns": 4,
    "left_columns": 4,
}


DEFAULT_MASTER_GRID = {
    "columns": 24,
    "rows": 16,
}


DEFAULT_ROW_HEIGHT_PX = 80


DEFAULT_PANEL_SLOT_MIN_W = 90
DEFAULT_PANEL_SLOT_PAD = 4

DEFAULT_ZONE_LAYOUT = {
    "left": {"col": 0, "row": 0, "colspan": 5, "rowspan": 16},
    "top": {"col": 5, "row": 0, "colspan": 15, "rowspan": 3},
    "middle_top": {"col": 5, "row": 3, "colspan": 15, "rowspan": 6},
    "middle_bottom": {"col": 5, "row": 9, "colspan": 15, "rowspan": 4},
    "bottom": {"col": 5, "row": 13, "colspan": 15, "rowspan": 3},
    "right": {"col": 20, "row": 0, "colspan": 4, "rowspan": 16},
}

class TarzanParApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TARZAN PAR — Pulpit Anatomii Ruchu")
        self.geometry("1600x1000")
        self.minsize(1280, 760)
        self.configure(bg=COLORS["bg"])
        apply_dark_style(self)

        self.layout_cfg = self.load_layout()

        self.visible = dict(DEFAULT_VISIBLE)
        self.visible.update(self.layout_cfg.get("panels", {}))

        self.panel_zones = dict(DEFAULT_PANEL_ZONES)
        self.panel_zones.update(self.layout_cfg.get("panel_zones", {}))

        self.panel_layout = self._normalize_panel_layout(self.layout_cfg.get("panel_layout", {}))

        self.grid_settings = dict(DEFAULT_GRID)
        self.grid_settings.update(self.layout_cfg.get("grid", {}))

        self.master_grid = dict(DEFAULT_MASTER_GRID)
        self.master_grid.update(self.layout_cfg.get("master_grid", {}))

        self.zone_layout = {k: dict(v) for k, v in DEFAULT_ZONE_LAYOUT.items()}
        for _zone_key, _zone_cfg in self.layout_cfg.get("zone_layout", {}).items():
            if _zone_key in self.zone_layout:
                self.zone_layout[_zone_key].update(_zone_cfg)

        self.row_height_px = int(self.layout_cfg.get("row_height_px", DEFAULT_ROW_HEIGHT_PX))

        self.bus = get_signal_bus("TEST")
        self.bridge = TarzanParBridge(self.bus, after=self.after, after_cancel=self.after_cancel)
        self.tarzan_snajper = create_default_tarzan_snajper()
        self.bridge.tarzan_snajper = self.tarzan_snajper
        self.tarzan_snajper.register_adapter("physical_nextion", NextionPhysicalSnajperAdapter(self.bridge))
        
        # TARZAN_SNAJPER: Rejestracja adaptera dla Tkinter w PAR
        from core.tarzanSnajper import TkWidgetSnajperAdapter
        self.tarzan_snajper.register_adapter("par_tkinter", TkWidgetSnajperAdapter())

        # TARZAN_SNAJPER: Rejestracja adaptera dla Canvas Preview
        from core.tarzanSnajper import TkCanvasSnajperAdapter
        self.par_canvas_adapter = TkCanvasSnajperAdapter()
        self.tarzan_snajper.register_adapter("canvas_preview", self.par_canvas_adapter)

        # TARZAN_SNAJPER: fizyczny Nextion używa katalogu celów z core/tarzanSnajper.py.
        # To jest brakujące stałe połączenie BUS -> Snajper. Bez tego flush może nie mieć
        # pending commands dla TC/TAKE po bus.set_take_time(...).
        self.bus.subscribe(lambda name, state: self.tarzan_snajper.fire_from_signal(name, getattr(state, "value", state)))
        # Nie rejestrujemy ręcznych map w panelach.
        self.panels = TarzanParPanels(self, self.bus)
        self.bus.subscribe(self.panels.on_state_change)
        self.take_label = None

        self.build()
        # WYCIETE HARD CUT V3: stary model odswiezania usuniety.
        try:
            self.bridge.nextion_connect()
            self.bridge.nextion_sync(force=True)
        except Exception:
            pass
        self.after_idle(self.snajper_render_initial_structure)
        self.after(30, self.nextion_snajper_tick)
        # USUNIĘTE: PAR_APP.tick wyłączony

    def load_layout(self):
        try:
            return json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"panels": DEFAULT_VISIBLE}



    def _safe_int(self, value, default=0, minimum=0):
        try:
            return max(minimum, int(value))
        except Exception:
            return default


    def _clamp_zone_layout(self):
        if not hasattr(self, "master_grid"):
            self.master_grid = dict(DEFAULT_MASTER_GRID)
        if not hasattr(self, "zone_layout"):
            self.zone_layout = {k: dict(v) for k, v in DEFAULT_ZONE_LAYOUT.items()}

        cols = self._safe_int(self.master_grid.get("columns", 24), 24, 1)
        rows = self._safe_int(self.master_grid.get("rows", 16), 16, 1)

        for zone, default_cfg in DEFAULT_ZONE_LAYOUT.items():
            cfg = dict(default_cfg)
            cfg.update(self.zone_layout.get(zone, {}))

            col = min(cols - 1, self._safe_int(cfg.get("col", 0), 0, 0))
            row = min(rows - 1, self._safe_int(cfg.get("row", 0), 0, 0))
            colspan = max(1, min(cols - col, self._safe_int(cfg.get("colspan", 1), 1, 1)))
            rowspan = max(1, min(rows - row, self._safe_int(cfg.get("rowspan", 1), 1, 1)))

            self.zone_layout[zone] = {
                "col": col,
                "row": row,
                "colspan": colspan,
                "rowspan": rowspan,
            }

    def _clamp_panel_layout(self):
        if not hasattr(self, "panel_layout"):
            self.panel_layout = self._normalize_panel_layout({})
        if not hasattr(self, "grid_settings"):
            self.grid_settings = dict(DEFAULT_GRID)

        for key, cfg in list(self.panel_layout.items()):
            zone = cfg.get("zone", DEFAULT_PANEL_ZONES.get(key, "middle_top"))
            if zone == "hidden":
                continue
            columns = self._zone_columns(zone)
            try:
                cfg["colspan"] = max(1, min(columns, int(cfg.get("colspan", 1))))
            except Exception:
                cfg["colspan"] = min(columns, 3)
            try:
                cfg["rowspan"] = max(1, min(12, int(cfg.get("rowspan", 1))))
            except Exception:
                cfg["rowspan"] = 1
            self.panel_layout[key] = cfg


    def _apply_master_zone_grid(self):
        if not hasattr(self, "master_grid"):
            self.master_grid = dict(DEFAULT_MASTER_GRID)
        if not hasattr(self, "zone_layout"):
            self.zone_layout = {k: dict(v) for k, v in DEFAULT_ZONE_LAYOUT.items()}

        self._clamp_zone_layout()

        for child in [self.left, self.top, self.middle_top, self.middle_bottom, self.bottom, self.right]:
            child.grid_forget()

        cols = self._safe_int(self.master_grid.get("columns", 24), 24, 1)
        rows = self._safe_int(self.master_grid.get("rows", 16), 16, 1)

        for c in range(0, 64):
            self.layout_master.grid_columnconfigure(c, weight=0, uniform="", minsize=0)
        for r in range(0, 64):
            self.layout_master.grid_rowconfigure(r, weight=0, uniform="", minsize=0)

        for c in range(cols):
            self.layout_master.grid_columnconfigure(c, weight=1, uniform="par_master_col", minsize=10)
        for r in range(rows):
            self.layout_master.grid_rowconfigure(r, weight=1, uniform="par_master_row", minsize=10)

        frames = {
            "left": self.left,
            "top": self.top,
            "middle_top": self.middle_top,
            "middle_bottom": self.middle_bottom,
            "bottom": self.bottom,
            "right": self.right,
        }

        for zone, frame in frames.items():
            cfg = self.zone_layout[zone]
            frame.grid(
                row=cfg["row"],
                column=cfg["col"],
                rowspan=cfg["rowspan"],
                columnspan=cfg["colspan"],
                sticky="nsew",
                padx=4,
                pady=4,
            )

    def _normalize_panel_layout(self, raw_layout):
        layout = {}
        for key in DEFAULT_VISIBLE:
            base = dict(DEFAULT_PANEL_LAYOUT.get(key, {"zone": DEFAULT_PANEL_ZONES.get(key, "middle_top"), "order": 100, "colspan": 3, "rowspan": 1}))
            incoming = dict(raw_layout.get(key, {})) if isinstance(raw_layout, dict) else {}
            base.update(incoming)
            base["zone"] = str(base.get("zone", DEFAULT_PANEL_ZONES.get(key, "middle_top")))
            try:
                base["order"] = int(base.get("order", 100))
            except Exception:
                base["order"] = 100
            try:
                base["colspan"] = max(1, int(base.get("colspan", 3)))
            except Exception:
                base["colspan"] = 3
            try:
                base["rowspan"] = max(1, int(base.get("rowspan", 1)))
            except Exception:
                base["rowspan"] = 1
            layout[key] = base
        return layout

    def _panel_zone(self, key):
        if not hasattr(self, "panel_layout"):
            self.panel_layout = self._normalize_panel_layout({})
        return self.panel_layout.get(key, {}).get("zone", self.panel_zones.get(key, DEFAULT_PANEL_ZONES.get(key, "middle_top")))

    def _panel_order(self, key):
        if not hasattr(self, "panel_layout"):
            self.panel_layout = self._normalize_panel_layout({})
        return int(self.panel_layout.get(key, {}).get("order", 100))

    def _zone_columns(self, zone):
        if not hasattr(self, "grid_settings"):
            self.grid_settings = dict(DEFAULT_GRID)
        return max(1, int(self.grid_settings.get(f"{zone}_columns", DEFAULT_GRID.get(f"{zone}_columns", 12))))

    def _grid_pack_panel(self, zone_frame, key, builder, cursor_by_zone):
        zone = self._panel_zone(key)
        columns = self._zone_columns(zone)
        cfg = self.panel_layout.get(key, {})
        colspan = max(1, min(columns, int(cfg.get("colspan", 3))))
        rowspan = max(1, int(cfg.get("rowspan", 1)))
        row_height = max(32, int(getattr(self, "row_height_px", DEFAULT_ROW_HEIGHT_PX)))

        cursor = cursor_by_zone.setdefault(zone, {"row": 0, "col": 0, "row_height": 1})
        row = int(cursor.get("row", 0))
        col = int(cursor.get("col", 0))
        current_row_height = max(1, int(cursor.get("row_height", 1)))

        if col + colspan > columns:
            row += current_row_height
            col = 0
            current_row_height = 1

        slot = tk.Frame(zone_frame, bg=COLORS["bg"])
        slot.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, sticky="nsew", padx=4, pady=4)
        slot.grid_propagate(False)
        slot.pack_propagate(False)

        widget = builder(slot)
        try:
            widget.pack(fill="both", expand=True)
        except Exception:
            # Jeżeli panel sam się spakował lub jest już zarządzany, nie zabijaj całego pulpitu.
            pass

        for c in range(columns):
            zone_frame.grid_columnconfigure(
                c,
                weight=1,
                uniform=f"{zone}_col",
                minsize=DEFAULT_PANEL_SLOT_MIN_W,
            )

        for r in range(row, row + rowspan):
            zone_frame.grid_rowconfigure(
                r,
                weight=0,
                uniform=f"{zone}_row",
                minsize=row_height,
            )

        col += colspan
        current_row_height = max(current_row_height, rowspan)

        if col >= columns:
            row += current_row_height
            col = 0
            current_row_height = 1

        cursor_by_zone[zone] = {"row": row, "col": col, "row_height": current_row_height}

    def save_layout(self):
        if not hasattr(self, "panel_zones"):
            self.panel_zones = dict(DEFAULT_PANEL_ZONES)
        if not hasattr(self, "panel_layout"):
            self.panel_layout = self._normalize_panel_layout({})
        if not hasattr(self, "grid_settings"):
            self.grid_settings = dict(DEFAULT_GRID)
        if not hasattr(self, "master_grid"):
            self.master_grid = dict(DEFAULT_MASTER_GRID)
        if not hasattr(self, "zone_layout"):
            self.zone_layout = {k: dict(v) for k, v in DEFAULT_ZONE_LAYOUT.items()}
        if not hasattr(self, "row_height_px"):
            self.row_height_px = DEFAULT_ROW_HEIGHT_PX

        LAYOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        LAYOUT_PATH.write_text(
            json.dumps(
                {
                    "panels": self.visible,
                    "panel_zones": self.panel_zones,
                    "panel_layout": self.panel_layout,
                    "grid": self.grid_settings,
                    "master_grid": self.master_grid,
                    "zone_layout": self.zone_layout,
                    "row_height_px": self.row_height_px,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

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

        self.layout_master = tk.Frame(self.body, bg=COLORS["bg"])
        self.layout_master.pack(fill="both", expand=True)

        self.left = tk.Frame(self.layout_master, bg=COLORS["bg"])
        self.top = tk.Frame(self.layout_master, bg=COLORS["bg"])
        self.middle_top = tk.Frame(self.layout_master, bg=COLORS["bg"])
        self.middle_bottom = tk.Frame(self.layout_master, bg=COLORS["bg"])
        self.bottom = tk.Frame(self.layout_master, bg=COLORS["bg"])
        self.right = tk.Frame(self.layout_master, bg=COLORS["bg"])

        # Zgodność ze starszym kodem: center/mid wskazują na master/środek.
        self.center = self.layout_master
        self.mid = self.middle_top

        tk.Label(self.footer, text="TARZAN PAR v0.44.0 REAL MOTOR SYNC", bg="#020304", fg=COLORS["muted"]).pack(side="left", padx=12)
        tk.Label(self.footer, text="PULPIT ANATOMII RUCHU — TEST/LIVE/MIX — TAKE → SIGNALBUS", bg="#020304", fg=COLORS["muted"]).pack(side="left", expand=True)
        self.clock = tk.Label(self.footer, text="", bg="#020304", fg=COLORS["muted"])
        self.clock.pack(side="right", padx=12)

    def nav(self):
        tk.Label(self.left, text="URZĄDZENIA", bg=COLORS["panel2"], fg=COLORS["text"], anchor="w", padx=12, pady=9, font=("Segoe UI", 11, "bold")).pack(fill="x")
        items = [
            ("axes", "  🦾  Osie i Silniki"), ("limits", "  ♟  Krańcówki"), ("sensors", "  ◈  Czujniki"),
            ("lamp", "  ▣  Lampka pracy ramienia"), ("mass_regulator", "  ⚖  Regulator masy"), ("shock_sensor_panel", "  ◈  Wstrząs"),
            ("operator", "  ⌁  Sterowanie Operatora"), ("ui", "  ▣  UI (Panel)"),
            ("light_bh1750", "  ☀  BH1750"), ("level_xyz", "  ⊕  Poziom XYZ"), ("temperature", "  ℃  Temperatura"), ("laser", "  ⌁  Laser"),
            ("automatyka", "  ⚡  AUTOMATYKA"), ("sok", "  ◉  SOK"), ("cnc_signals", "  ▥  CNC"),
            ("bridge", "  ↔  Mostek PLAY ↔ REC"),
            ("dron", "  🛩  DRON"), ("lcd", "  ▤  LCD 1602"), ("matrix_led", "  ▦  Matrix LED 8x8"),
            ("keyboard", "  ⌨  Klawiatura"), ("poextbus_cnc", "  ▥  PoExtBus / CNC"), ("functions", "  🔒  Funkcje / Rezerwy"),
            ("camera", "  📷  Kamera i KHR"), ("autostatus", "  ⚙  AUTOSTATUS"), ("system", "  ⚙  System i Status"),
            ("take", "  🎬  TAKE Player"), ("info", "  ℹ  Panel informacyjny"), ("log", "  📜  Logi"), ("all_signals", "  ✣  Wszystkie Sygnały"),
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
        for parent in [self.top, self.middle_top, self.middle_bottom, self.bottom, self.right, self.left]:
            for child in parent.winfo_children():
                child.destroy()

    @profile_method("PAR_APP.refresh")

    def _ensure_any_visible_panel(self):
        try:
            return any(self.visible.get(k) and self._panel_zone(k) != "hidden" for k in self.visible)
        except Exception:
            return False

    def refresh(self):
        if not hasattr(self, "panel_zones"):
            self.panel_zones = dict(DEFAULT_PANEL_ZONES)
        if not hasattr(self, "panel_layout"):
            self.panel_layout = self._normalize_panel_layout({})
        if not hasattr(self, "grid_settings"):
            self.grid_settings = dict(DEFAULT_GRID)
        if not hasattr(self, "master_grid"):
            self.master_grid = dict(DEFAULT_MASTER_GRID)
        if not hasattr(self, "zone_layout"):
            self.zone_layout = {k: dict(v) for k, v in DEFAULT_ZONE_LAYOUT.items()}
        if not hasattr(self, "row_height_px"):
            self.row_height_px = DEFAULT_ROW_HEIGHT_PX

        self._clamp_zone_layout()
        self._clamp_panel_layout()
        if not self._ensure_any_visible_panel():
            self.visible = dict(DEFAULT_VISIBLE)
            self.panel_zones = dict(DEFAULT_PANEL_ZONES)
            self.panel_layout = self._normalize_panel_layout({})

        self._apply_master_zone_grid()
        self.clear()
        p = self.panels

        zones = {
            "top": self.top,
            "middle_top": self.middle_top,
            "middle_bottom": self.middle_bottom,
            "bottom": self.bottom,
            "right": self.right,
            "left": self.left,
        }

        for zone, frame in zones.items():
            cols = self._zone_columns(zone)

            for c in range(0, 48):
                frame.grid_columnconfigure(c, weight=0, uniform="", minsize=0)
            for r in range(0, 96):
                frame.grid_rowconfigure(r, weight=0, uniform="", minsize=0)

            for c in range(cols):
                frame.grid_columnconfigure(
                    c,
                    weight=1,
                    uniform=f"{zone}_col",
                    minsize=DEFAULT_PANEL_SLOT_MIN_W,
                )

        builders = {
            "axes": p.axes,
            "take": p.take,
            "info": p.info_panel,
            "log": p.log_panel,
            "limits": p.limits,
            "sensors": p.sensors,
            "operator": p.operator,
            "ui": p.ui,
            "bridge": p.bridge,
            "poextbus": p.poextbus,
            "poextbus_cnc": p.poextbus_cnc,
            "functions": p.functions,
            "timeline": p.timeline,
            "dron": p.dron,
            "lcd": p.lcd,
            "matrix": p.matrix,
            "matrix_led": p.matrix,
            "keyboard": p.keyboard,
            "camera": p.camera,
            "autostatus": p.autostatus,
            "system": p.system,
            "settings": p.settings,
            "all_signals": p.all_signals,
            "lamp": p.lamp_panel,
            "mass_regulator": p.mass_regulator_panel,
            "shock_sensor_panel": p.shock_sensor_panel,
            "light_bh1750": p.light_bh1750_panel,
            "level_xyz": p.level_xyz_panel,
            "temperature": p.temperature_panel,
            "laser": p.laser_panel,
            "automatyka": p.automatyka_panel,
            "sok": p.sok_panel,
            "cnc_signals": p.cnc_signals_panel,
            "nextion_7_preview": p.nextion_7_preview,
        }

        cursor_by_zone = {z: {"row": 0, "col": 0, "row_height": 1} for z in zones}

        ordered_keys = sorted(
            [k for k in self.visible if self.visible.get(k) and self._panel_zone(k) != "hidden"],
            key=lambda k: (self._panel_zone(k), self._panel_order(k), k),
        )

        for key in ordered_keys:
            builder = builders.get(key)
            if builder is None:
                continue
            zone = self._panel_zone(key)
            parent = zones.get(zone, self.middle_top)
            self._grid_pack_panel(parent, key, builder, cursor_by_zone)

        p.update_log()

    def hide_panel(self, key):
        self.visible[key] = False
        # WYCIETE HARD CUT V3: stary model odswiezania usuniety.
        self.save_layout()

    def toggle_panel(self, key):
        self.visible[key] = not self.visible.get(key, False)
        # WYCIETE HARD CUT V3: stary model odswiezania usuniety.
        self.save_layout()


    def _layout_preset_vars(self, master_cols, master_rows, zone_vars):
        master_cols.set(24)
        master_rows.set(16)
        preset = {
            "left": {"col": 0, "colspan": 5, "row": 0, "rowspan": 16},
            "top": {"col": 5, "colspan": 15, "row": 0, "rowspan": 3},
            "middle_top": {"col": 5, "colspan": 15, "row": 3, "rowspan": 6},
            "middle_bottom": {"col": 5, "colspan": 15, "row": 9, "rowspan": 4},
            "bottom": {"col": 5, "colspan": 15, "row": 13, "rowspan": 3},
            "right": {"col": 20, "colspan": 4, "row": 0, "rowspan": 16},
        }
        for zone, cfg in preset.items():
            if zone not in zone_vars:
                continue
            for key, value in cfg.items():
                zone_vars[zone][key].set(value)




    def _layout_auto_tarzan_vars(self, master_cols, master_rows, zone_vars, row_data, row_height_var=None):
        """Preset operatorski PAR: bezpieczny układ startowy dla całego pulpitu."""
        master_cols.set(24)
        master_rows.set(16)
        if row_height_var is not None:
            try:
                row_height_var.set(80)
            except Exception:
                pass

        zones = {
            "left": {"col": 0, "colspan": 4, "row": 0, "rowspan": 16},
            "top": {"col": 4, "colspan": 16, "row": 0, "rowspan": 3},
            "middle_top": {"col": 4, "colspan": 16, "row": 3, "rowspan": 5},
            "middle_bottom": {"col": 4, "colspan": 16, "row": 8, "rowspan": 5},
            "bottom": {"col": 4, "colspan": 16, "row": 13, "rowspan": 3},
            "right": {"col": 20, "colspan": 4, "row": 0, "rowspan": 16},
        }
        for zone, cfg in zones.items():
            if zone not in zone_vars:
                continue
            for key, value in cfg.items():
                zone_vars[zone][key].set(value)

        plan = {
            "axes": ("top", 10, 12, 3),
            "take": ("top", 20, 4, 2),

            "operator": ("middle_top", 10, 4, 2),
            "ui": ("middle_top", 20, 4, 2),
            "lamp": ("middle_top", 30, 2, 2),
            "mass_regulator": ("middle_top", 40, 3, 2),
            "shock_sensor_panel": ("middle_top", 50, 2, 2),
            "light_bh1750": ("middle_top", 60, 2, 2),
            "level_xyz": ("middle_top", 70, 3, 2),
            "temperature": ("middle_top", 80, 2, 2),
            "laser": ("middle_top", 90, 2, 2),
            "functions": ("middle_top", 100, 4, 2),

            "limits": ("middle_bottom", 10, 4, 3),
            "sensors": ("middle_bottom", 20, 4, 3),
            "bridge": ("middle_bottom", 30, 4, 2),
            "poextbus": ("middle_bottom", 40, 4, 2),
            "poextbus_cnc": ("middle_bottom", 50, 4, 2),

            "timeline": ("bottom", 10, 12, 3),
            "dron": ("bottom", 20, 2, 2),
            "camera": ("bottom", 30, 2, 2),

            "info": ("right", 10, 4, 2),
            "log": ("right", 20, 4, 4),
            "system": ("right", 30, 4, 2),
            "autostatus": ("right", 40, 4, 2),
            "settings": ("right", 50, 4, 2),
            "all_signals": ("right", 60, 4, 6),

            "keyboard": ("left", 10, 4, 3),
            "lcd": ("left", 20, 4, 2),
            "matrix": ("left", 30, 4, 3),
            "matrix_led": ("left", 40, 4, 3),
        }

        rev_zone = {
            "top": "GÓRA",
            "middle_top": "ŚRODEK GÓRA",
            "middle_bottom": "ŚRODEK DÓŁ",
            "bottom": "DÓŁ",
            "right": "PRAWA",
            "left": "LEWA",
            "hidden": "UKRYTY",
        }

        for data in row_data:
            key = data.get("key")
            if key in plan:
                zone, order, colspan, rowspan = plan[key]
                data["zone"].set(rev_zone[zone])
                data["colspan"].set(colspan)
                data["rowspan"].set(rowspan)
                data["visible"].set(True)
            elif key not in DEFAULT_VISIBLE:
                data["zone"].set("UKRYTY")
                data["visible"].set(False)

        order_map = {key: vals[1] for key, vals in plan.items()}
        zone_map = {key: vals[0] for key, vals in plan.items()}
        zone_order = {"top": 0, "middle_top": 1, "middle_bottom": 2, "bottom": 3, "right": 4, "left": 5, "hidden": 9}
        row_data.sort(key=lambda d: (zone_order.get(zone_map.get(d.get("key"), "hidden"), 9), order_map.get(d.get("key"), 999), d.get("key", "")))

    def panel_menu(self):
        win = tk.Toplevel(self)
        win.title("TARZAN PAR — Projektant Układu")
        win.geometry("1900x1040")
        try:
            win.state("zoomed")
        except Exception:
            pass
        win.configure(bg=COLORS["panel"])

        zone_map = {
            "GÓRA": "top",
            "ŚRODEK GÓRA": "middle_top",
            "ŚRODEK DÓŁ": "middle_bottom",
            "DÓŁ": "bottom",
            "PRAWA": "right",
            "LEWA": "left",
            "UKRYTY": "hidden",
        }
        rev_zone = {v: k for k, v in zone_map.items()}

        nice_names = {
            "axes": "Osie i silniki",
            "take": "TAKE Player",
            "info": "Panel informacyjny",
            "log": "Logi",
            "limits": "Krańcówki",
            "sensors": "Czujniki",
            "operator": "Sterowanie operatora",
            "ui": "UI PLAY / REC",
            "bridge": "Mostek PLAY ↔ REC",
            "poextbus": "PoExtBus / CNC",
            "functions": "Funkcje / Rezerwy",
            "timeline": "Timeline",
            "dron": "DRON",
            "lcd": "LCD 1602",
            "matrix": "Matrix LED 8x8",
            "keyboard": "Klawiatura",
            "camera": "Kamera / KHR",
            "autostatus": "Autostatus",
            "system": "System",
            "settings": "Ustawienia symulacji",
            "all_signals": "Wszystkie sygnały",
            "lamp": "Lampka pracy ramienia",
            "mass_regulator": "Regulator masy",
            "shock_sensor_panel": "Czujnik wstrząsowy",
            "light_bh1750": "Czujnik światła BH1750",
            "level_xyz": "Czujnik poziomu XYZ",
            "temperature": "Czujnik temperatury",
            "laser": "Czujnik laserowy",
            "automatyka": "AUTOMATYKA",
            "sok": "SOK — Sterownik Obrotowy Kurkowy",
            "cnc_signals": "Sygnały CNC",
        }

        zone_colors = {
            "left": "#31465a",
            "top": "#37592d",
            "middle_top": "#5a4a2d",
            "middle_bottom": "#5a3b2d",
            "bottom": "#2d4f5a",
            "right": "#4d355f",
            "hidden": "#333333",
        }

        header = tk.Frame(win, bg=COLORS["panel2"])
        header.pack(fill="x")
        tk.Label(
            header,
            text="TARZAN PAR — PROJEKTANT UKŁADU",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        ).pack(side="left", padx=14, pady=10)

        tk.Label(
            header,
            text="ustawienia po lewej • duży podgląd siatki po prawej • zapisz układ",
            bg=COLORS["panel2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(side="left", padx=18)

        body = tk.Frame(win, bg=COLORS["panel"])
        body.pack(fill="both", expand=True, padx=12, pady=10)

        left_col = tk.Frame(body, bg=COLORS["panel"], width=720)
        left_col.pack(side="left", fill="both", padx=(0, 10))
        left_col.pack_propagate(False)

        right_col = tk.Frame(body, bg=COLORS["panel"])
        right_col.pack(side="right", fill="both", expand=True)

        # ===== LIVE PREVIEW =====
        preview_box = tk.Frame(right_col, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        preview_box.pack(fill="both", expand=True)

        preview_header = tk.Frame(preview_box, bg=COLORS["panel2"])
        preview_header.pack(fill="x")
        tk.Label(
            preview_header,
            text="PODGLĄD CAŁEGO OKNA — mała kropka panelu = przesuń • róg = rozmiar • panel ma pierwszeństwo przed sekcją",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(side="left", padx=10, pady=7)

        status_var = tk.StringVar(value="Gotowe")
        tk.Label(
            preview_header,
            textvariable=status_var,
            bg=COLORS["panel2"],
            fg=COLORS["amber"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right", padx=10)

        canvas = tk.Canvas(preview_box, bg="#050708", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # Interaktywny podgląd stref w Projektancie:
        # kliknij i przeciągnij strefę na siatce; wartości kol/wiersz zmieniają się w formularzu.
        preview_drag = {
            "mode": "zone",          # zone / panel
            "zone": None,
            "panel": None,
            "action": None,          # move / resize_e / resize_s / resize_se
            "start_cell": None,
            "start_cfg": None,
            "hitboxes": {},
            "zone_move_handles": {},
            "panel_hitboxes": {},
            "panel_move_handles": {},
            "panel_resize_handles": {},
        }

        # ===== RIGHT EDITOR =====
        editor_box = tk.Frame(left_col, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        editor_box.pack(fill="x", pady=(0, 10))

        tk.Label(
            editor_box,
            text="1. SIATKA OKNA",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x")

        grid_body = tk.Frame(editor_box, bg=COLORS["panel"])
        grid_body.pack(fill="x", padx=10, pady=8)

        master_cols = tk.IntVar(value=int(getattr(self, "master_grid", DEFAULT_MASTER_GRID).get("columns", 24)))
        master_rows = tk.IntVar(value=int(getattr(self, "master_grid", DEFAULT_MASTER_GRID).get("rows", 16)))

        tk.Label(grid_body, text="Kolumny", bg=COLORS["panel"], fg=COLORS["text"]).grid(row=0, column=0, sticky="w")
        tk.Spinbox(grid_body, from_=8, to=48, width=6, textvariable=master_cols, bg="#101820",
                   fg=COLORS["text"], insertbackground=COLORS["text"]).grid(row=0, column=1, sticky="w", padx=8)
        tk.Label(grid_body, text="Wiersze", bg=COLORS["panel"], fg=COLORS["text"]).grid(row=1, column=0, sticky="w", pady=4)
        tk.Spinbox(grid_body, from_=6, to=32, width=6, textvariable=master_rows, bg="#101820",
                   fg=COLORS["text"], insertbackground=COLORS["text"]).grid(row=1, column=1, sticky="w", padx=8)

        row_height_var = tk.IntVar(value=int(getattr(self, "row_height_px", DEFAULT_ROW_HEIGHT_PX)))
        tk.Label(grid_body, text="Wysokość wiersza px", bg=COLORS["panel"], fg=COLORS["text"]).grid(row=2, column=0, sticky="w", pady=4)
        tk.Spinbox(grid_body, from_=40, to=180, width=6, textvariable=row_height_var, bg="#101820",
                   fg=COLORS["text"], insertbackground=COLORS["text"], command=lambda: draw_preview() if "draw_preview" in locals() else None).grid(row=2, column=1, sticky="w", padx=8)

        # Przyciski presetów ukryte na życzenie operatora.
        # Funkcje layout_preset() i auto_layout_tarzan() zostają w kodzie jako zapas,
        # ale nie są pokazywane w UI Projektanta.


        zone_box = tk.Frame(left_col, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        zone_box.pack(fill="x", pady=(0, 10))
        tk.Label(
            zone_box,
            text="2. EDYCJA STREFY",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x")

        zone_body = tk.Frame(zone_box, bg=COLORS["panel"])
        zone_body.pack(fill="x", padx=10, pady=8)

        selected_zone = tk.StringVar(value="top")
        zone_col = tk.IntVar(value=0)
        zone_row = tk.IntVar(value=0)
        zone_colspan = tk.IntVar(value=1)
        zone_rowspan = tk.IntVar(value=1)

        zone_vars = {}
        for zone, cfg in DEFAULT_ZONE_LAYOUT.items():
            current = dict(cfg)
            current.update(getattr(self, "zone_layout", {}).get(zone, {}))
            zone_vars[zone] = {
                "col": tk.IntVar(value=int(current.get("col", 0))),
                "row": tk.IntVar(value=int(current.get("row", 0))),
                "colspan": tk.IntVar(value=int(current.get("colspan", 1))),
                "rowspan": tk.IntVar(value=int(current.get("rowspan", 1))),
            }

        zone_buttons = tk.Frame(zone_body, bg=COLORS["panel"])
        zone_buttons.pack(fill="x", pady=(0, 8))

        def select_zone(zone):
            selected_zone.set(zone)
            vals = zone_vars[zone]
            zone_col.set(vals["col"].get())
            zone_row.set(vals["row"].get())
            zone_colspan.set(vals["colspan"].get())
            zone_rowspan.set(vals["rowspan"].get())
            try:
                refresh_zone_buttons()
            except Exception:
                pass
            status_var.set(f"Strefa: {rev_zone.get(zone, zone)} — możesz przeciągnąć ją na podglądzie")
            refresh_zone_buttons()
            draw_preview()

        zone_button_widgets = {}

        def refresh_zone_buttons():
            for _zone, _btn in zone_button_widgets.items():
                active = selected_zone.get() == _zone
                _btn.configure(
                    bg="#ffe08a" if active else zone_colors.get(_zone, "#202b33"),
                    fg="#111111" if active else "#ffffff",
                    relief="solid" if active else "flat",
                    bd=2 if active else 1,
                )

        for label, zone in [("LEWA", "left"), ("GÓRA", "top"), ("ŚR. GÓRA", "middle_top"), ("ŚR. DÓŁ", "middle_bottom"), ("DÓŁ", "bottom"), ("PRAWA", "right")]:
            _btn = tk.Button(
                zone_buttons,
                text=label,
                bg=zone_colors.get(zone, "#202b33"),
                fg="#ffffff",
                relief="flat",
                bd=1,
                command=lambda z=zone: select_zone(z),
            )
            _btn.pack(side="left", expand=True, fill="x", padx=2)
            zone_button_widgets[zone] = _btn

        fields = [
            ("Kol start", zone_col),
            ("Wiersz start", zone_row),
            ("Kolumn ile", zone_colspan),
            ("Wierszy ile", zone_rowspan),
        ]
        for i, (label, var) in enumerate(fields):
            tk.Label(zone_body, text=label, bg=COLORS["panel"], fg=COLORS["text"]).pack(anchor="w")
            tk.Spinbox(
                zone_body,
                from_=0 if "start" in label else 1,
                to=64,
                width=8,
                textvariable=var,
                bg="#101820",
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
            ).pack(fill="x", pady=(0, 4))

        def apply_zone_fields():
            zone = selected_zone.get()
            zone_vars[zone]["col"].set(zone_col.get())
            zone_vars[zone]["row"].set(zone_row.get())
            zone_vars[zone]["colspan"].set(zone_colspan.get())
            zone_vars[zone]["rowspan"].set(zone_rowspan.get())
            status_var.set(f"Zmieniono strefę: {rev_zone.get(zone, zone)}")
            draw_preview()

        tk.Button(zone_body, text="ZASTOSUJ STREFĘ", bg="#1f6fb7", fg="#fff", relief="flat",
                  command=apply_zone_fields).pack(fill="x", pady=(8, 0))

        panel_box = tk.Frame(left_col, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        panel_box.pack(fill="both", expand=True)

        tk.Label(
            panel_box,
            text="3. PANELE — przeciąganie kolejności + rozmiar kafla",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            panel_box,
            text="Przy każdym panelu ustawiasz strefę oraz ile kolumn i wierszy ma zajmować.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", padx=8, pady=(4, 2))

        panel_canvas = tk.Canvas(panel_box, bg=COLORS["panel"], highlightthickness=0, height=430)
        panel_scroll = tk.Scrollbar(panel_box, orient="vertical", command=panel_canvas.yview)
        panel_inner = tk.Frame(panel_canvas, bg=COLORS["panel"])
        panel_inner.bind("<Configure>", lambda e: panel_canvas.configure(scrollregion=panel_canvas.bbox("all")))
        panel_canvas.create_window((0, 0), window=panel_inner, anchor="nw")
        panel_canvas.configure(yscrollcommand=panel_scroll.set)
        panel_canvas.pack(side="left", fill="both", expand=True)
        panel_scroll.pack(side="right", fill="y")

        row_data = []
        row_widgets = []
        row_frames_by_key = {}
        drag = {"index": None}

        if not hasattr(self, "panel_layout"):
            self.panel_layout = self._normalize_panel_layout({})

        for key in sorted(DEFAULT_VISIBLE.keys(), key=lambda k: (self._panel_zone(k), self._panel_order(k), k)):
            cfg = dict(self.panel_layout.get(key, DEFAULT_PANEL_LAYOUT.get(key, {})))
            row_data.append({
                "key": key,
                "visible": tk.BooleanVar(value=self.visible.get(key, False)),
                "zone": tk.StringVar(value=rev_zone.get(cfg.get("zone", "middle_top"), "ŚRODEK GÓRA")),
                "colspan": tk.IntVar(value=int(cfg.get("colspan", 3))),
                "rowspan": tk.IntVar(value=int(cfg.get("rowspan", 1))),
            })

        def render_rows():
            for child in panel_inner.winfo_children():
                child.destroy()
            row_widgets.clear()
            row_frames_by_key.clear()

            for idx, data in enumerate(row_data):
                key = data["key"]
                selected = (
                    (preview_drag.get("mode") == "panel" and preview_drag.get("panel") == key)
                    or (preview_drag.get("mode") == "zone" and zone_map.get(data["zone"].get(), "middle_top") == preview_drag.get("zone"))
                )
                row_bg = "#2b3f4b" if selected else COLORS["panel"]
                row = tk.Frame(panel_inner, bg=row_bg)
                row.pack(fill="x", pady=1)
                row_widgets.append(row)
                row_frames_by_key[key] = row

                def _mark_panel_selected(_event=None, k=key):
                    preview_drag["mode"] = "panel"
                    preview_drag["panel"] = k
                    preview_drag["zone"] = None
                    status_var.set(f"Panel na liście: {nice_names.get(k, k)}")
                    render_rows()
                    draw_preview()
                handle = tk.Label(row, text="☰", bg=row_bg, fg=COLORS["muted"],
                                  width=2, font=("Segoe UI", 11, "bold"))
                handle.pack(side="left", padx=2)

                tk.Checkbutton(row, variable=data["visible"], bg=row_bg, fg=COLORS["text"],
                               selectcolor="#101820", activebackground=COLORS["panel"],
                               command=draw_preview).pack(side="left")

                tk.Label(row, text=nice_names.get(key, key), bg=row_bg, fg=COLORS["text"],
                         width=30, anchor="w", font=("Segoe UI", 9)).pack(side="left", padx=3)

                opt = tk.OptionMenu(row, data["zone"], *zone_map.keys(), command=lambda _=None: draw_preview())
                opt.configure(bg="#202b33", fg=COLORS["text"], relief="flat", width=14, highlightthickness=0)
                opt["menu"].configure(bg="#202b33", fg=COLORS["text"])
                opt.pack(side="left", padx=2)

                tk.Label(row, text="kol", bg=row_bg, fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left", padx=(6, 1))
                col_spin = tk.Spinbox(
                    row,
                    from_=1,
                    to=24,
                    width=4,
                    textvariable=data["colspan"],
                    bg="#101820",
                    fg=COLORS["text"],
                    insertbackground=COLORS["text"],
                    command=draw_preview,
                )
                col_spin.pack(side="left", padx=(0, 4))
                col_spin.bind("<KeyRelease>", lambda _event: draw_preview())

                tk.Label(row, text="wiersz", bg=row_bg, fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left", padx=(4, 1))
                row_spin = tk.Spinbox(
                    row,
                    from_=1,
                    to=12,
                    width=4,
                    textvariable=data["rowspan"],
                    bg="#101820",
                    fg=COLORS["text"],
                    insertbackground=COLORS["text"],
                    command=draw_preview,
                )
                row_spin.pack(side="left", padx=(0, 4))
                row_spin.bind("<KeyRelease>", lambda _event: draw_preview())

                def start_drag(event, i=idx):
                    drag["index"] = i

                def release_drag(event):
                    start = drag.get("index")
                    if start is None:
                        return
                    y = event.y_root
                    target = start
                    for j, widget in enumerate(row_widgets):
                        top = widget.winfo_rooty()
                        bottom = top + widget.winfo_height()
                        if top <= y <= bottom:
                            target = j
                            break
                    if target != start:
                        item = row_data.pop(start)
                        row_data.insert(target, item)
                        render_rows()
                        draw_preview()
                    drag["index"] = None

                # Nie bindować wszystkich dzieci wiersza.
                # OptionMenu/Spinbox/Checkbutton muszą dostać własny klik, inaczej dropdown stref nie otwiera się.
                row.bind("<Button-1>", _mark_panel_selected, add="+")
                handle.bind("<Button-1>", _mark_panel_selected, add="+")

                # Kolejność na liście zmieniamy tylko uchwytem ☰, nie całym wierszem.
                handle.bind("<ButtonPress-1>", start_drag, add="+")
                handle.bind("<ButtonRelease-1>", release_drag, add="+")

        def get_temp_layouts():
            temp_zone_layout = {}
            for zone, vars_for_zone in zone_vars.items():
                temp_zone_layout[zone] = {
                    "col": max(0, int(vars_for_zone["col"].get())),
                    "row": max(0, int(vars_for_zone["row"].get())),
                    "colspan": max(1, int(vars_for_zone["colspan"].get())),
                    "rowspan": max(1, int(vars_for_zone["rowspan"].get())),
                }
            temp_panel_layout = {}
            counters = {}
            for data in row_data:
                key = data["key"]
                zone = zone_map.get(data["zone"].get(), "middle_top")
                counters[zone] = counters.get(zone, 0) + 10
                temp_panel_layout[key] = {
                    "zone": zone,
                    "order": counters[zone],
                    "colspan": max(1, int(data["colspan"].get())),
                    "rowspan": max(1, int(data["rowspan"].get())),
                    "visible": bool(data["visible"].get()) and zone != "hidden",
                }
            return temp_zone_layout, temp_panel_layout

        def draw_preview(*_):
            # WYCIETE HARD CUT V3: stary model odswiezania usuniety.
            try:
                cols = max(1, int(master_cols.get()))
                rows = max(1, int(master_rows.get()))
            except Exception:
                cols, rows = 24, 16

            w = max(400, canvas.winfo_width())
            h = max(300, canvas.winfo_height())
            margin = 24
            cw = (w - 2 * margin) / cols
            ch = (h - 2 * margin) / rows

            temp_zone_layout, temp_panel_layout = get_temp_layouts()
            preview_drag["hitboxes"] = {}
            preview_drag["zone_move_handles"] = {}
            preview_drag["panel_hitboxes"] = {}
            preview_drag["panel_move_handles"] = {}
            preview_drag["panel_resize_handles"] = {}

            cell_zones = {}
            zone_collisions = set()

            # 1. Wypełnienie komórek strefami.
            for zone, cfg in temp_zone_layout.items():
                col = max(0, int(cfg.get("col", 0)))
                row = max(0, int(cfg.get("row", 0)))
                colspan = max(1, int(cfg.get("colspan", 1)))
                rowspan = max(1, int(cfg.get("rowspan", 1)))

                for cc in range(col, min(cols, col + colspan)):
                    for rr in range(row, min(rows, row + rowspan)):
                        cell = (cc, rr)
                        if cell in cell_zones:
                            zone_collisions.add(cell)
                            old = cell_zones[cell]
                            if isinstance(old, list):
                                old.append(zone)
                            else:
                                cell_zones[cell] = [old, zone]
                        else:
                            cell_zones[cell] = zone

            # 2. Rysuj każdą komórkę jako kolorową kratkę.
            for rr in range(rows):
                for cc in range(cols):
                    x1 = margin + cc * cw
                    y1 = margin + rr * ch
                    x2 = margin + (cc + 1) * cw
                    y2 = margin + (rr + 1) * ch
                    zone = cell_zones.get((cc, rr))
                    if (cc, rr) in zone_collisions:
                        fill = "#8b1515"
                    elif zone:
                        if isinstance(zone, list):
                            zone = zone[-1]
                        fill = zone_colors.get(zone, "#333333")
                    else:
                        fill = "#0a0f13"

                    canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#17242d")

            # 3. Zewnętrzne ramki stref + etykiety.
            for zone, cfg in temp_zone_layout.items():
                col = max(0, int(cfg.get("col", 0)))
                row = max(0, int(cfg.get("row", 0)))
                colspan = max(1, int(cfg.get("colspan", 1)))
                rowspan = max(1, int(cfg.get("rowspan", 1)))

                x1 = margin + col * cw
                y1 = margin + row * ch
                x2 = margin + min(cols, col + colspan) * cw
                y2 = margin + min(rows, row + rowspan) * ch

                preview_drag["hitboxes"][zone] = (x1, y1, x2, y2)
                selected_zone = preview_drag.get("mode") == "zone" and preview_drag.get("zone") == zone
                outline = "#ffe08a" if selected_zone else "#e7edf2"
                canvas.create_rectangle(x1, y1, x2, y2, outline=outline, width=3 if selected_zone else 2)
                # Kropka przesuwania zawsze widoczna — operator nie musi zgadywać, gdzie złapać.
                dot_r = 9
                dot_x = x1 + 14
                dot_y = y1 + 14
                preview_drag["zone_move_handles"][zone] = (dot_x-dot_r, dot_y-dot_r, dot_x+dot_r, dot_y+dot_r)
                canvas.create_oval(dot_x-dot_r, dot_y-dot_r, dot_x+dot_r, dot_y+dot_r, fill="#ffe08a", outline="#111")
                canvas.create_text(dot_x, dot_y, text="↕", fill="#111", font=("Segoe UI", 7, "bold"))

                if selected_zone:
                    handle = 9
                    canvas.create_rectangle(x2-handle, y2-handle, x2+handle, y2+handle, fill="#ffcf4d", outline="#111")
                    canvas.create_rectangle(x2-handle, (y1+y2)/2-handle, x2+handle, (y1+y2)/2+handle, fill="#ffe08a", outline="#111")
                    canvas.create_rectangle((x1+x2)/2-handle, y2-handle, (x1+x2)/2+handle, y2+handle, fill="#ffe08a", outline="#111")

                zone_label = rev_zone.get(zone, zone)
                if zone_label == "ŚRODEK GÓRA":
                    zone_label = "ŚR. GÓRA"
                elif zone_label == "ŚRODEK DÓŁ":
                    zone_label = "ŚR. DÓŁ"
                # Napis odsunięty od kropki, krótszy i z tłem, żeby się nie pokrywał.
                tx = x1 + 30
                ty = y1 + 7
                text_id = canvas.create_text(tx, ty, text=zone_label, fill="#ffffff", font=("Segoe UI", 8, "bold"), anchor="nw")
                bbox = canvas.bbox(text_id)
                if bbox:
                    canvas.create_rectangle(bbox[0]-3, bbox[1]-2, bbox[2]+3, bbox[3]+2, fill="#050708", outline="")
                    canvas.tag_raise(text_id)

            # 4. Rozłóż panele jako overlay wewnątrz stref.
            panels_by_zone = {}
            for key, cfg in temp_panel_layout.items():
                if not cfg.get("visible", False):
                    continue
                zone = cfg.get("zone", "middle_top")
                if zone == "hidden":
                    continue
                panels_by_zone.setdefault(zone, []).append((cfg.get("order", 100), key, cfg))

            panel_cells = {}
            for zone, items in panels_by_zone.items():
                if zone not in temp_zone_layout:
                    continue

                zone_cfg = temp_zone_layout[zone]
                z_col = max(0, int(zone_cfg.get("col", 0)))
                z_row = max(0, int(zone_cfg.get("row", 0)))
                z_cols = max(1, int(zone_cfg.get("colspan", 1)))
                z_rows = max(1, int(zone_cfg.get("rowspan", 1)))

                p_col = 0
                p_row = 0
                for _, key, cfg in sorted(items):
                    p_cols = max(1, min(z_cols, int(cfg.get("colspan", 1))))
                    p_rows = max(1, int(cfg.get("rowspan", 1)))

                    if p_col + p_cols > z_cols:
                        p_row += 1
                        p_col = 0

                    abs_col = z_col + p_col
                    abs_row = z_row + p_row
                    abs_cols = min(p_cols, max(1, cols - abs_col))
                    abs_rows = min(p_rows, max(1, rows - abs_row))

                    # panel overlay rectangle
                    x1 = margin + abs_col * cw + 2
                    y1 = margin + abs_row * ch + 2
                    x2 = margin + min(cols, abs_col + abs_cols) * cw - 2
                    y2 = margin + min(rows, abs_row + abs_rows) * ch - 2

                    collision = False
                    for cc in range(abs_col, min(cols, abs_col + abs_cols)):
                        for rr in range(abs_row, min(rows, abs_row + abs_rows)):
                            cell = (cc, rr)
                            if cell in panel_cells:
                                collision = True
                                panel_cells[cell] = "COLLISION"
                            else:
                                panel_cells[cell] = key

                    preview_drag["panel_hitboxes"][key] = (x1, y1, x2, y2, zone)
                    selected_panel = preview_drag.get("mode") == "panel" and preview_drag.get("panel") == key
                    overlay_fill = "#000000" if not collision else "#cc1010"
                    canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill=overlay_fill,
                        stipple="gray50",
                        outline="#ffe08a" if selected_panel else ("#ffffff" if not collision else "#ffdddd"),
                        width=3 if selected_panel else 2,
                    )
                    # Kropka przesuwania panelu.
                    dot_r = 7
                    dot_x = x1 + 10
                    dot_y = y1 + 10
                    preview_drag["panel_move_handles"][key] = (dot_x-dot_r, dot_y-dot_r, dot_x+dot_r, dot_y+dot_r)
                    canvas.create_oval(dot_x-dot_r, dot_y-dot_r, dot_x+dot_r, dot_y+dot_r, fill="#ffe08a", outline="#111")

                    if selected_panel:
                        handle = 8
                        # Jawne hitboxy resize panelu. Są większe niż wizualny kwadrat,
                        # dzięki temu klik bliżej obszaru nie przełącza na sekcję.
                        hit = 18
                        preview_drag["panel_resize_handles"][key] = {
                            "resize_se": (x2-hit, y2-hit, x2+hit, y2+hit),
                            "resize_e": (x2-hit, (y1+y2)/2-hit, x2+hit, (y1+y2)/2+hit),
                            "resize_s": ((x1+x2)/2-hit, y2-hit, (x1+x2)/2+hit, y2+hit),
                        }
                        canvas.create_rectangle(x2-handle, y2-handle, x2+handle, y2+handle, fill="#ffe08a", outline="#111")
                        canvas.create_rectangle(x2-handle, (y1+y2)/2-handle, x2+handle, (y1+y2)/2+handle, fill="#ffe08a", outline="#111")
                        canvas.create_rectangle((x1+x2)/2-handle, y2-handle, (x1+x2)/2+handle, y2+handle, fill="#ffe08a", outline="#111")

                    label = nice_names.get(key, key)
                    short_label = label if len(label) <= 18 else label[:16] + "…"
                    if (x2 - x1) > 70 and (y2 - y1) > 20:
                        text_id = canvas.create_text(
                            x1 + 20,
                            y1 + 4,
                            text=short_label,
                            fill="#ffffff",
                            font=("Segoe UI", 7, "bold"),
                            anchor="nw",
                        )
                        bbox = canvas.bbox(text_id)
                        if bbox:
                            canvas.create_rectangle(bbox[0]-2, bbox[1]-1, bbox[2]+2, bbox[3]+1, fill="#050708", outline="")
                            canvas.tag_raise(text_id)
                    elif (x2 - x1) > 45 and (y2 - y1) > 18:
                        canvas.create_text(
                            (x1 + x2) / 2,
                            (y1 + y2) / 2,
                            text=key[:3].upper(),
                            fill="#ffffff",
                            font=("Segoe UI", 7, "bold"),
                        )

                    p_col += p_cols
                    if p_col >= z_cols:
                        p_col = 0
                        p_row += p_rows

            # 5. Numery osi siatki.
            for c in range(cols + 1):
                x = margin + c * cw
                if c % 2 == 0:
                    canvas.create_text(x + 3, margin - 10, text=str(c), fill=COLORS["muted"], font=("Segoe UI", 7), anchor="w")
            for r in range(rows + 1):
                y = margin + r * ch
                if r % 2 == 0:
                    canvas.create_text(margin - 8, y, text=str(r), fill=COLORS["muted"], font=("Segoe UI", 7), anchor="e")

            zone_used = len([c for c in cell_zones])
            total = cols * rows
            zone_percent = int((zone_used / total) * 100) if total else 0
            panel_count = len([k for k, cfg in temp_panel_layout.items() if cfg.get("visible", False)])
            panel_collisions = len([v for v in panel_cells.values() if v == "COLLISION"])

            if zone_collisions or panel_collisions:
                status_var.set(f"UWAGA: kolizje stref/paneli | strefy {zone_used}/{total} ({zone_percent}%) | panele {panel_count}")
            else:
                status_var.set(f"Zajęte pola stref: {zone_used}/{total} ({zone_percent}%) | panele widoczne: {panel_count}")


        def _preview_canvas_metrics():
            try:
                cols = max(1, int(master_cols.get()))
                rows = max(1, int(master_rows.get()))
            except Exception:
                cols, rows = 24, 16
            w = max(400, canvas.winfo_width())
            h = max(300, canvas.winfo_height())
            margin = 24
            cw = (w - 2 * margin) / cols
            ch = (h - 2 * margin) / rows
            return cols, rows, margin, cw, ch

        def _inside_box(x, y, box):
            if not box:
                return False
            x1, y1, x2, y2 = box[:4]
            return x1 <= x <= x2 and y1 <= y <= y2

        def _preview_cell_from_xy(x, y):
            cols, rows, margin, cw, ch = _preview_canvas_metrics()
            col = int((x - margin) // cw)
            row = int((y - margin) // ch)
            return max(0, min(cols - 1, col)), max(0, min(rows - 1, row))

        def _preview_zone_at_xy(x, y):
            # Kropka ma pierwszeństwo.
            for zone, box in reversed(list(preview_drag.get("zone_move_handles", {}).items())):
                if _inside_box(x, y, box):
                    return zone
            for zone, box in reversed(list(preview_drag.get("hitboxes", {}).items())):
                if _inside_box(x, y, box):
                    return zone
            return None

        def _preview_panel_at_xy(x, y):
            # Panel ma pierwszeństwo przed strefą.
            # Najpierw resize-handle, potem move-handle, potem całe okno panelu.
            for key, handles in reversed(list(preview_drag.get("panel_resize_handles", {}).items())):
                for _action, box in handles.items():
                    if _inside_box(x, y, box):
                        return key
            for key, box in reversed(list(preview_drag.get("panel_move_handles", {}).items())):
                if _inside_box(x, y, box):
                    return key
            for key, box in reversed(list(preview_drag.get("panel_hitboxes", {}).items())):
                if _inside_box(x, y, box):
                    return key
            return None

        def _preview_panel_resize_action_at_xy(key, x, y):
            handles = preview_drag.get("panel_resize_handles", {}).get(key, {})
            # Róg ma pierwszeństwo przed krawędzią.
            for action in ("resize_se", "resize_e", "resize_s"):
                box = handles.get(action)
                if _inside_box(x, y, box):
                    return action
            return None

        def _preview_action_for_box(x, y, box, move_box=None):
            if move_box and _inside_box(x, y, move_box):
                return "move"
            x1, y1, x2, y2 = box[:4]
            edge = 14
            near_e = abs(x - x2) <= edge
            near_s = abs(y - y2) <= edge
            if near_e and near_s:
                return "resize_se"
            if near_e:
                return "resize_e"
            if near_s:
                return "resize_s"
            return "move"

        def _sync_selected_zone_fields(zone):
            if zone not in zone_vars:
                return
            selected_zone.set(zone)
            vals = zone_vars[zone]
            zone_col.set(vals["col"].get())
            zone_row.set(vals["row"].get())
            zone_colspan.set(vals["colspan"].get())
            zone_rowspan.set(vals["rowspan"].get())

        def _row_data_by_key(key):
            for data in row_data:
                if data.get("key") == key:
                    return data
            return None

        def _zone_by_cell(col, row, ignore_zone=None):
            found = None
            for zone, vals in zone_vars.items():
                if zone == ignore_zone:
                    continue
                zc = int(vals["col"].get())
                zr = int(vals["row"].get())
                zw = int(vals["colspan"].get())
                zh = int(vals["rowspan"].get())
                if zc <= col < zc + zw and zr <= row < zr + zh:
                    found = zone
            return found

        def _swap_zones(a, b):
            if not a or not b or a == b or a not in zone_vars or b not in zone_vars:
                return
            a_vals = {k: zone_vars[a][k].get() for k in ("col", "row", "colspan", "rowspan")}
            b_vals = {k: zone_vars[b][k].get() for k in ("col", "row", "colspan", "rowspan")}
            for k, v in b_vals.items():
                zone_vars[a][k].set(v)
            for k, v in a_vals.items():
                zone_vars[b][k].set(v)

        def on_preview_double_click(event):
            panel = _preview_panel_at_xy(event.x, event.y)
            if panel:
                preview_drag["mode"] = "panel"
                preview_drag["panel"] = panel
                preview_drag["zone"] = None
                status_var.set(f"Tryb PANEL: {nice_names.get(panel, panel)} — złap kropkę albo róg")
                render_rows()
                draw_preview()
                return "break"

            zone = _preview_zone_at_xy(event.x, event.y)
            if zone:
                preview_drag["mode"] = "zone"
                preview_drag["zone"] = zone
                preview_drag["panel"] = None
                _sync_selected_zone_fields(zone)
                status_var.set(f"Tryb STREFA: {rev_zone.get(zone, zone)} — złap kropkę albo róg")
                render_rows()
                draw_preview()
                return "break"

        def on_preview_press(event):
            preview_drag["action"] = None
            cell = _preview_cell_from_xy(event.x, event.y)

            # Panel zawsze pierwszy. To usuwa błąd: klik w kropkę panelu przełączał na sekcję.
            panel = _preview_panel_at_xy(event.x, event.y)
            if panel:
                data = _row_data_by_key(panel)
                box = preview_drag.get("panel_hitboxes", {}).get(panel)
                if not data or not box:
                    return "break"
                preview_drag["mode"] = "panel"
                preview_drag["panel"] = panel
                preview_drag["zone"] = None
                explicit_action = _preview_panel_resize_action_at_xy(panel, event.x, event.y)
                preview_drag["action"] = explicit_action or _preview_action_for_box(event.x, event.y, box, preview_drag.get("panel_move_handles", {}).get(panel))
                preview_drag["start_cell"] = cell
                preview_drag["start_cfg"] = {
                    "colspan": int(data["colspan"].get()),
                    "rowspan": int(data["rowspan"].get()),
                    "zone": zone_map.get(data["zone"].get(), "middle_top"),
                }
                status_var.set(f"Panel: {nice_names.get(panel, panel)} / {preview_drag['action']}")
                render_rows()
                draw_preview()
                return "break"

            zone = _preview_zone_at_xy(event.x, event.y)
            if zone and zone in zone_vars:
                box = preview_drag.get("hitboxes", {}).get(zone)
                preview_drag["mode"] = "zone"
                preview_drag["zone"] = zone
                preview_drag["panel"] = None
                preview_drag["action"] = _preview_action_for_box(event.x, event.y, box, preview_drag.get("zone_move_handles", {}).get(zone))
                preview_drag["start_cell"] = cell
                preview_drag["start_cfg"] = {
                    "col": int(zone_vars[zone]["col"].get()),
                    "row": int(zone_vars[zone]["row"].get()),
                    "colspan": int(zone_vars[zone]["colspan"].get()),
                    "rowspan": int(zone_vars[zone]["rowspan"].get()),
                }
                _sync_selected_zone_fields(zone)
                status_var.set(f"Strefa: {rev_zone.get(zone, zone)} / {preview_drag['action']}")
                render_rows()
                draw_preview()

        def on_preview_drag(event):
            action = preview_drag.get("action")
            start_cell = preview_drag.get("start_cell")
            start_cfg = preview_drag.get("start_cfg") or {}
            if not action or not start_cell:
                return

            cols, rows, _margin, _cw, _ch = _preview_canvas_metrics()
            current_cell = _preview_cell_from_xy(event.x, event.y)
            dx = current_cell[0] - start_cell[0]
            dy = current_cell[1] - start_cell[1]

            if preview_drag.get("mode") == "panel":
                panel = preview_drag.get("panel")
                data = _row_data_by_key(panel)
                zone = start_cfg.get("zone")
                if not data or zone not in zone_vars:
                    return
                zone_cols = max(1, int(zone_vars[zone]["colspan"].get()))
                zone_rows = max(1, int(zone_vars[zone]["rowspan"].get()))

                if action in ("resize_e", "resize_se"):
                    data["colspan"].set(max(1, min(zone_cols, int(start_cfg.get("colspan", 1)) + dx)))
                if action in ("resize_s", "resize_se"):
                    data["rowspan"].set(max(1, min(zone_rows, int(start_cfg.get("rowspan", 1)) + dy)))
                if action == "move":
                    # Panel nie ma absolutnej pozycji x/y; jest układany kolejnością w strefie.
                    # Ruch w prawo/dół = dalej, w lewo/górę = wcześniej.
                    delta = 0
                    if dx > 0:
                        delta += 1
                    elif dx < 0:
                        delta -= 1
                    if dy > 0:
                        delta += 1
                    elif dy < 0:
                        delta -= 1
                    if delta:
                        try:
                            idx = row_data.index(data)
                            new_idx = max(0, min(len(row_data) - 1, idx + delta))
                            if new_idx != idx:
                                row_data.pop(idx)
                                row_data.insert(new_idx, data)
                                preview_drag["start_cell"] = current_cell
                                render_rows()
                        except Exception:
                            pass
                draw_preview()
                return

            zone = preview_drag.get("zone")
            if not zone or zone not in zone_vars:
                return

            col = int(start_cfg.get("col", 0))
            row = int(start_cfg.get("row", 0))
            colspan = max(1, int(start_cfg.get("colspan", 1)))
            rowspan = max(1, int(start_cfg.get("rowspan", 1)))

            if action == "move":
                new_col = max(0, min(cols - colspan, col + dx))
                new_row = max(0, min(rows - rowspan, row + dy))
                zone_vars[zone]["col"].set(new_col)
                zone_vars[zone]["row"].set(new_row)
            else:
                if action in ("resize_e", "resize_se"):
                    zone_vars[zone]["colspan"].set(max(1, min(cols - col, colspan + dx)))
                if action in ("resize_s", "resize_se"):
                    zone_vars[zone]["rowspan"].set(max(1, min(rows - row, rowspan + dy)))

            _sync_selected_zone_fields(zone)
            draw_preview()

        def on_preview_release(event):
            mode = preview_drag.get("mode")
            if mode == "zone" and preview_drag.get("zone") and preview_drag.get("action") == "move":
                zone = preview_drag["zone"]
                cfg = zone_vars[zone]
                center_col = int(cfg["col"].get()) + max(0, int(cfg["colspan"].get()) // 2)
                center_row = int(cfg["row"].get()) + max(0, int(cfg["rowspan"].get()) // 2)
                target = _zone_by_cell(center_col, center_row, ignore_zone=zone)
                if target:
                    _swap_zones(zone, target)
                    _sync_selected_zone_fields(zone)
                    status_var.set(f"Podmieniono strefy: {rev_zone.get(zone, zone)} ↔ {rev_zone.get(target, target)} — kliknij ZASTOSUJ")
                else:
                    status_var.set(f"Zmieniono strefę: {rev_zone.get(zone, zone)} — kliknij ZASTOSUJ albo ZAPISZ UKŁAD")
            elif mode == "panel" and preview_drag.get("panel"):
                status_var.set(f"Zmieniono panel: {nice_names.get(preview_drag['panel'], preview_drag['panel'])} — kliknij ZASTOSUJ albo ZAPISZ UKŁAD")
            preview_drag["action"] = None
            preview_drag["start_cell"] = None
            preview_drag["start_cfg"] = None
            draw_preview()

        canvas.bind("<Double-Button-1>", on_preview_double_click)
        canvas.bind("<ButtonPress-1>", on_preview_press)
        canvas.bind("<B1-Motion>", on_preview_drag)
        canvas.bind("<ButtonRelease-1>", on_preview_release)

        def auto_layout_tarzan():
            self._layout_auto_tarzan_vars(master_cols, master_rows, zone_vars, row_data, row_height_var)
            render_rows()
            select_zone("top")
            draw_preview()
            status_var.set("Załadowano preset: UKŁAD TARZAN — kliknij ZASTOSUJ albo ZAPISZ UKŁAD")

        def layout_preset():
            master_cols.set(24)
            master_rows.set(16)
            try:
                row_height_var.set(DEFAULT_ROW_HEIGHT_PX)
            except Exception:
                pass
            preset = {
                "left": {"col": 0, "colspan": 5, "row": 0, "rowspan": 16},
                "top": {"col": 5, "colspan": 15, "row": 0, "rowspan": 3},
                "middle_top": {"col": 5, "colspan": 15, "row": 3, "rowspan": 6},
                "middle_bottom": {"col": 5, "colspan": 15, "row": 9, "rowspan": 4},
                "bottom": {"col": 5, "colspan": 15, "row": 13, "rowspan": 3},
                "right": {"col": 20, "colspan": 4, "row": 0, "rowspan": 16},
            }
            for zone, cfg in preset.items():
                for key, value in cfg.items():
                    zone_vars[zone][key].set(value)
            select_zone("top")
            draw_preview()

        def apply_from_window(save=False):
            self.master_grid = {"columns": max(1, int(master_cols.get())), "rows": max(1, int(master_rows.get()))}
            self.grid_settings = {
                "top_columns": 16,
                "middle_top_columns": 16,
                "middle_bottom_columns": 16,
                "bottom_columns": 16,
                "right_columns": 4,
                "left_columns": 4,
            }
            try:
                self.row_height_px = max(32, int(row_height_var.get()))
            except Exception:
                self.row_height_px = DEFAULT_ROW_HEIGHT_PX

            self.zone_layout = {}
            for zone, vars_for_zone in zone_vars.items():
                self.zone_layout[zone] = {
                    "col": max(0, int(vars_for_zone["col"].get())),
                    "colspan": max(1, int(vars_for_zone["colspan"].get())),
                    "row": max(0, int(vars_for_zone["row"].get())),
                    "rowspan": max(1, int(vars_for_zone["rowspan"].get())),
                }

            self.panel_layout = {}
            self.panel_zones = {}
            counters = {}
            for data in row_data:
                key = data["key"]
                zone = zone_map.get(data["zone"].get(), "middle_top")
                visible = bool(data["visible"].get()) and zone != "hidden"
                self.visible[key] = visible
                self.panel_zones[key] = zone
                counters[zone] = counters.get(zone, 0) + 10
                self.panel_layout[key] = {
                    "zone": zone,
                    "order": counters[zone],
                    "colspan": max(1, int(data["colspan"].get())),
                    "rowspan": max(1, int(data["rowspan"].get())),
                }
            try:
                detail = ", ".join([f"{k}:{v.get('zone')}/{v.get('colspan')}x{v.get('rowspan')}" for k, v in self.panel_layout.items() if k in ("axes", "limits", "sensors", "all_signals", "timeline")])
                self.bus.log("LAYOUT_APPLY_DETAIL", detail)
                self.bus.log("LAYOUT", "Zastosowano układ paneli z Projektanta")
            except Exception:
                pass
            self._clamp_zone_layout()
            self._clamp_panel_layout()
            # WYCIETE HARD CUT V3: stary model odswiezania usuniety.
            try:
                draw_preview()
            except Exception:
                pass
            if save:
                self.save_layout()

        def reset_layout():
            self.visible = dict(DEFAULT_VISIBLE)
            self.panel_zones = dict(DEFAULT_PANEL_ZONES)
            self.panel_layout = self._normalize_panel_layout({})
            self.grid_settings = dict(DEFAULT_GRID)
            self.master_grid = dict(DEFAULT_MASTER_GRID)
            self.zone_layout = {k: dict(v) for k, v in DEFAULT_ZONE_LAYOUT.items()}
            self.row_height_px = DEFAULT_ROW_HEIGHT_PX
            # WYCIETE HARD CUT V3: stary model odswiezania usuniety.
            self.save_layout()
            win.destroy()

        render_rows()
        select_zone("top")
        refresh_zone_buttons()
        win.after(200, draw_preview)
        win.after(800, draw_preview)

        buttons = tk.Frame(win, bg=COLORS["panel"])
        buttons.pack(fill="x", padx=12, pady=(0, 10))

        tk.Button(buttons, text="ZASTOSUJ", bg="#1f6fb7", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"), command=lambda: apply_from_window(False)).pack(side="left", padx=4)
        tk.Button(buttons, text="ZAPISZ UKŁAD", bg="#1d842c", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"), command=lambda: apply_from_window(True)).pack(side="left", padx=4)
        tk.Button(buttons, text="RESET UKŁADU", bg="#7a251f", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"), command=reset_layout).pack(side="right", padx=4)

    def set_mode(self, mode):
        self.bridge.set_mode(mode)
        if hasattr(self, "bus"):
            self.bus.mode = mode
            # Dodatkowo ustawiamy par_mode dla pełnej kompatybilności wstecznej TFD
            m_val = 0 if mode == "TEST" else (1 if mode == "LIVE" else 2)
            self.bus.force_signal("par_mode", m_val, source="PAR_UI")

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

    @profile_method("PAR_APP.nextion_snajper_tick")
    def nextion_snajper_tick(self):
        try:
            self.bridge.poll()
            # flush_snajper_commands jest już wywoływany wewnątrz poll(), 
            # ale zostawiamy jawne wywołanie dla pewności przy zmianach live.
            if hasattr(self.bridge, "flush_snajper_commands"):
                self.bridge.flush_snajper_commands()
        except Exception as exc:
            if hasattr(self.bus, "log"):
                self.bus.log("PAR_ERROR", f"Nextion Snajper Tick Error: {exc}")
        self.after(30, self.nextion_snajper_tick)



    def update_take_label(self):
        if not self.take_label:
            return
        take = self.bridge.take_player.take
        if not take:
            self.take_label.configure(text="TAKE: brak")
        else:
            self.take_label.configure(text=f"TAKE: {Path(take.path).name}\nrows={len(take.rows)} duration={take.duration_ms} ms\ntime={self.bus.take_time_ms} ms")


    def snajper_tick_dispatch(self) -> None:
        """
        TARZAN_SNAJPER STAGE8:
        PAR_APP.tick nie może robić odświeżania UI.
        Tick może zasilać logikę i BUS, a UI idzie przez Snajpera sekcyjnego.
        """
        panels = getattr(self, "panels", None)
        if panels is None:
            return
        section_snajper = getattr(panels, "section_snajper", None)
        if section_snajper is None and hasattr(panels, "_ensure_section_snajper"):
            panels._ensure_section_snajper()
            section_snajper = getattr(panels, "section_snajper", None)
        if section_snajper is None:
            return
        section_snajper.fire("protocol_tick", getattr(self, "_tick_counter", 0))

    def snajper_fire_layout(self, selected_cell=None, panel_status=None, zone_label=None) -> None:
        snajper = getattr(self, "tarzan_snajper", None)
        if snajper is None:
            return
        if selected_cell is not None:
            snajper.fire("layout_selected_cell", selected_cell)
        if panel_status is not None:
            snajper.fire("layout_panel_status", panel_status)
        if zone_label is not None:
            snajper.fire("layout_zone_label", zone_label)

    def snajper_render_initial_structure(self) -> None:
        """
        TARZAN_SNAJPER ETAP 1:
        Snajper nie zastępuje pierwszego renderu struktury PAR.
        Ta metoda buduje panele w środku okna jeden raz po starcie.
        Nie jest dynamicznym refresh wartości.
        """
        self.refresh()
        
        # Przekazujemy Snajpera do TFDState, aby umożliwić celowane aktualizacje z TFD
        try:
            from editor.TFD.tfd_state import tfd_state
            if tfd_state and hasattr(self, "tarzan_snajper"):
                tfd_state.set_snajper(self.tarzan_snajper)
        except Exception as e:
            print(f"SNAJPER ERROR: Could not set snajper to tfd_state: {e}")

        # Rejestracja Canvas Preview w Snajperze po pierwszym renderze
        for screen_key, widget in getattr(self.panels, "nextion_preview_widgets", {}).items():
            if hasattr(self, "par_canvas_adapter"):
                try:
                    self.par_canvas_adapter.register_canvas_panel(screen_key, widget)
                except Exception as e:
                    print(f"SNAJPER ERROR: Could not register canvas panel {screen_key}: {e}")

