# -*- coding: utf-8 -*-
from __future__ import annotations

"""
TARZAN - Vision Tracking Setup

Osobne okno administracji rozpoznawania obrazu.
Kamera fizyczna pozostaje w osobnym Camera Setup w KHR.

To okno zapisuje parametry do data/khr/vision_settings.json:
- profile obiektu: kolor HSV + operatorowy wybór kształtu,
- filtry stabilizacji obiektu,
- biblioteki twarzy: MediaPipe / OpenCV Haar,
- opisy dla operatora.
"""

import copy
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog

from vision.tarzanVisionConfig import load_vision_settings


BG = "#101010"
PANEL = "#171717"
PANEL_2 = "#202020"
FG = "#eeeeee"
MUTED = "#9a9a9a"
LINE = "#333333"
ACCENT_OBJECT = "#d99a00"
ACCENT_HSV = "#2d7dff"
ACCENT_FACE = "#00aa88"
ACCENT_SAVE = "#aa66dd"


SHAPE_PRESETS: dict[str, dict] = {
    "ANY": {
        "label": "DOWOLNY KSZTAŁT",
        "description": "Najprostszy tryb: system śledzi obiekt po kolorze HSV i polu konturu. Dobry do szybkiego testu.",
        "shape_enabled": False,
        "shape": {"type": "ANY", "min_vertices": 0, "max_vertices": 99, "min_circularity": 0.0, "max_circularity": 1.0, "aspect_ratio_min": 0.2, "aspect_ratio_max": 5.0},
    },
    "TRIANGLE": {
        "label": "TRÓJKĄT",
        "description": "Operator wybiera trójkąt; system sam zapisuje techniczne progi konturu dla znacznika trójkątnego.",
        "shape_enabled": True,
        "shape": {"type": "TRIANGLE", "min_vertices": 3, "max_vertices": 3, "min_circularity": 0.0, "max_circularity": 0.75, "aspect_ratio_min": 0.35, "aspect_ratio_max": 2.5},
    },
    "SQUARE": {
        "label": "KWADRAT",
        "description": "System wymaga czworokąta o proporcjach zbliżonych do 1:1.",
        "shape_enabled": True,
        "shape": {"type": "SQUARE", "min_vertices": 4, "max_vertices": 4, "min_circularity": 0.45, "max_circularity": 0.95, "aspect_ratio_min": 0.75, "aspect_ratio_max": 1.35},
    },
    "RECTANGLE": {
        "label": "PROSTOKĄT",
        "description": "System wymaga czworokąta, ale dopuszcza wydłużone proporcje.",
        "shape_enabled": True,
        "shape": {"type": "RECTANGLE", "min_vertices": 4, "max_vertices": 4, "min_circularity": 0.35, "max_circularity": 0.95, "aspect_ratio_min": 0.3, "aspect_ratio_max": 4.0},
    },
    "CIRCLE": {
        "label": "KOŁO",
        "description": "System szuka obiektu o wysokiej kolistości. Dobry dla okrągłych znaczników.",
        "shape_enabled": True,
        "shape": {"type": "CIRCLE", "min_vertices": 8, "max_vertices": 99, "min_circularity": 0.72, "max_circularity": 1.0, "aspect_ratio_min": 0.75, "aspect_ratio_max": 1.35},
    },
    "STAR": {
        "label": "GWIAZDA",
        "description": "Tryb operatorowy dla znacznika-gwiazdy. Parametry techniczne są ukryte w presetu.",
        "shape_enabled": True,
        "shape": {"type": "STAR", "min_vertices": 8, "max_vertices": 16, "min_circularity": 0.2, "max_circularity": 0.75, "aspect_ratio_min": 0.6, "aspect_ratio_max": 1.7},
    },
    "TEMPLATE_IMAGE": {
        "label": "IKONA / WZORZEC",
        "description": "Docelowy tryb śledzenia wzorca z obrazka referencyjnego. Teraz zapisuje tryb do JSON do dalszego rozwoju.",
        "shape_enabled": True,
        "shape": {"type": "TEMPLATE_IMAGE", "min_vertices": 0, "max_vertices": 99, "min_circularity": 0.0, "max_circularity": 1.0, "aspect_ratio_min": 0.2, "aspect_ratio_max": 5.0},
    },
}


DEFAULT_OBJECT_PROFILE = {
    "description": "Nowy profil obiektu",
    "color_enabled": True,
    "shape_enabled": False,
    "hsv_ranges": [
        {"h_min": 0, "s_min": 90, "v_min": 70, "h_max": 10, "s_max": 255, "v_max": 255},
        {"h_min": 170, "s_min": 90, "v_min": 70, "h_max": 180, "s_max": 255, "v_max": 255},
    ],
    "min_area": 500.0,
    "max_area": 250000.0,
    "min_solidity": 0.45,
    "min_extent": 0.18,
    "morph_open_kernel": 5,
    "morph_close_kernel": 7,
    "blur_kernel": 3,
    "prefer_largest_contour": True,
    "shape": copy.deepcopy(SHAPE_PRESETS["ANY"]["shape"]),
}


class VisionSetupWindow(tk.Toplevel):
    """Czytelne, osobne okno ustawień trackingu. Bez ustawień fizycznej kamery."""

    def __init__(self, parent, project_root: Path) -> None:
        super().__init__(parent)
        self.parent = parent
        self.project_root = Path(project_root)
        self.settings = load_vision_settings(self.project_root)

        self.title("TARZAN - VISION TRACKING SETUP / OBIEKT + TWARZ")
        # Pełne okno Full HD — osobne od CAMERA SETUP.
        # Tu nie ma ustawień fizycznej kamery, tylko parametry rozpoznawania.
        self.geometry("1920x1080")
        self.minsize(1600, 900)
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.configure(bg=BG)

        self._configure_styles()
        self._build_vars()
        self._build_ui()
        self._load_active_profile_to_vars()
        self._load_face_to_vars()
        self._update_shape_description()
        self._update_status("Wczytano ustawienia trackingu z vision_settings.json")

    # ------------------------------------------------------------------
    # STYLE / VARS
    # ------------------------------------------------------------------
    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TCombobox", fieldbackground="#f7f7f7", background="#e8e8e8")

    def _build_vars(self) -> None:
        tracking = self.settings.setdefault("tracking", {})
        self.profile_var = tk.StringVar(value=str(tracking.get("active_target", "RED_OBJECT")))
        self.new_profile_var = tk.StringVar(value="CUSTOM_OBJECT_01")
        self.desc_var = tk.StringVar(value="")

        self.color_enabled_var = tk.BooleanVar(value=True)
        self.shape_enabled_var = tk.BooleanVar(value=False)
        self.shape_type_var = tk.StringVar(value="ANY")
        self.shape_desc_var = tk.StringVar(value="")

        self.h1_min = tk.IntVar(value=0)
        self.h1_max = tk.IntVar(value=10)
        self.h2_min = tk.IntVar(value=170)
        self.h2_max = tk.IntVar(value=180)
        self.s_min = tk.IntVar(value=90)
        self.s_max = tk.IntVar(value=255)
        self.v_min = tk.IntVar(value=70)
        self.v_max = tk.IntVar(value=255)

        self.min_area = tk.DoubleVar(value=500.0)
        self.max_area = tk.DoubleVar(value=250000.0)
        self.min_solidity = tk.DoubleVar(value=0.45)
        self.min_extent = tk.DoubleVar(value=0.18)
        self.blur_kernel = tk.IntVar(value=3)
        self.open_kernel = tk.IntVar(value=5)
        self.close_kernel = tk.IntVar(value=7)
        self.prefer_largest = tk.BooleanVar(value=True)
        self.prefer_center = tk.BooleanVar(value=False)

        self.face_backend_var = tk.StringVar(value="MEDIAPIPE")
        self.face_processing_width = tk.IntVar(value=480)
        self.face_preview_width = tk.IntVar(value=640)
        self.face_draw_debug = tk.BooleanVar(value=True)
        self.face_min_area = tk.DoubleVar(value=1200.0)
        self.face_max_area = tk.DoubleVar(value=250000.0)
        self.face_target_point = tk.StringVar(value="FACE_CENTER")
        self.face_smoothing = tk.DoubleVar(value=0.35)
        self.face_area_smoothing = tk.DoubleVar(value=0.25)
        self.face_hyst_on = tk.IntVar(value=2)
        self.face_hyst_off = tk.IntVar(value=5)
        self.face_hold_ms = tk.IntVar(value=250)
        self.face_max_jump = tk.DoubleVar(value=260.0)

        self.mp_model_selection = tk.IntVar(value=0)
        self.mp_confidence = tk.DoubleVar(value=0.55)
        self.mp_require_installed = tk.BooleanVar(value=True)

        self.haar_cascade = tk.StringVar(value="haarcascade_frontalface_default.xml")
        self.haar_scale = tk.DoubleVar(value=1.10)
        self.haar_neighbors = tk.IntVar(value=5)
        self.haar_min_w = tk.IntVar(value=40)
        self.haar_min_h = tk.IntVar(value=40)
        self.haar_max_w = tk.IntVar(value=0)
        self.haar_max_h = tk.IntVar(value=0)
        self.haar_equalize = tk.BooleanVar(value=True)

        self.head_profile_cascade = tk.StringVar(value="haarcascade_profileface.xml")
        self.head_min_area = tk.DoubleVar(value=1400.0)
        self.head_max_area = tk.DoubleVar(value=300000.0)
        self.head_center_smoothing = tk.DoubleVar(value=0.28)
        self.head_area_smoothing = tk.DoubleVar(value=0.22)
        self.head_hold_ms = tk.IntVar(value=450)
        self.head_max_jump_px = tk.DoubleVar(value=320.0)
        self.head_front_weight = tk.DoubleVar(value=1.0)
        self.head_profile_weight = tk.DoubleVar(value=0.92)
        self.head_detect_every_n = tk.IntVar(value=2)
        self.head_profile_every_n = tk.IntVar(value=3)
        self.head_use_left_profile = tk.BooleanVar(value=True)
        self.head_use_right_profile = tk.BooleanVar(value=True)
        self.head_description_var = tk.StringVar(
            value="KameraHEAD: jeden cel GŁOWA = frontal + profil prawy + profil lewy + podtrzymanie filtra."
        )

        # GLOBAL TARGET LOCK — wspólne przyspawanie celu dla każdego pluginu.
        self.target_lock_enabled = tk.BooleanVar(value=True)
        self.target_lock_draw_overlay = tk.BooleanVar(value=True)
        self.target_lock_hold_ms = tk.IntVar(value=550)
        self.target_lock_confirm_frames = tk.IntVar(value=2)
        self.target_lock_lost_frames = tk.IntVar(value=6)
        self.target_lock_error_smoothing = tk.DoubleVar(value=0.35)
        self.target_lock_center_smoothing = tk.DoubleVar(value=0.30)
        self.target_lock_area_smoothing = tk.DoubleVar(value=0.20)
        self.target_lock_decay = tk.DoubleVar(value=0.96)
        self.target_lock_max_jump_px = tk.DoubleVar(value=300.0)
        self.target_lock_box_scale = tk.DoubleVar(value=1.35)

        self.status_var = tk.StringVar(value="")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=BG)
        header.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(8, 4))
        tk.Label(header, text="TARZAN VISION TRACKING SETUP", bg=BG, fg="#f2f2f2", font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="  obiekt / kolor / kształt + twarz + zapis JSON   |   kamera fizyczna jest w CAMERA SETUP", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10)

        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.content = tk.Frame(canvas, bg=BG)
        window_id = canvas.create_window((0, 0), window=self.content, anchor="nw")

        def _sync_scroll(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))
            try:
                canvas.itemconfig(window_id, width=canvas.winfo_width())
            except Exception:
                pass

        self.content.bind("<Configure>", _sync_scroll)
        canvas.bind("<Configure>", _sync_scroll)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Układ 1+2 | 3 | 4:
        # - kolumna 1 i 2 są logicznie zachowane, ale wizualnie ustawione jedna pod drugą,
        #   żeby pierwsza nie rozciągała całego okna w poziomie;
        # - kolumna 3 zostaje szeroka i wewnętrznie rozbita na dwie sekcje;
        # - kolumna 4 zostaje osobno po prawej jako GLOBAL TARGET LOCK.
        self.content.grid_columnconfigure(0, weight=1, uniform="vision_main")
        self.content.grid_columnconfigure(1, weight=2, uniform="vision_main")
        self.content.grid_columnconfigure(2, weight=1, uniform="vision_main")

        left_stack = tk.Frame(self.content, bg=BG)
        left_stack.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=4)
        left_stack.grid_columnconfigure(0, weight=1)

        col_profile = self._panel(left_stack, "1  OBIEKT / PROFIL", ACCENT_OBJECT)
        col_hsv = self._panel(left_stack, "2  KOLOR / KSZTAŁT / STABILNOŚĆ", ACCENT_HSV)
        col_face = self._panel(self.content, "3  TWARZ / GŁOWA / BIBLIOTEKI", ACCENT_FACE)
        col_lock = self._panel(self.content, "4  GLOBAL TARGET LOCK", ACCENT_SAVE)

        col_profile.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 4))
        col_hsv.grid(row=1, column=0, sticky="ew", padx=0, pady=(4, 0))
        col_face.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        col_lock.grid(row=0, column=2, sticky="nsew", padx=(4, 0), pady=4)

        self._build_profile_panel(col_profile)
        self._build_hsv_shape_panel(col_hsv)
        self._build_face_save_panel(col_face)
        self._build_target_lock_panel(col_lock)

        # Dolny pasek serwisowy: wszystkie akcje są pod oknami ustawień.
        # Dzięki temu prawa kolumna nie rozciąga layoutu i nic nie znika poza ekranem.
        footer = tk.Frame(self, bg=BG, highlightthickness=1, highlightbackground=LINE)
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(2, 6))
        tk.Label(footer, textvariable=self.status_var, bg=BG, fg="#d6d6d6", anchor="w", font=("Consolas", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 8))
        tk.Button(footer, text="RESET", command=self.reset_active_object_default, width=9).pack(side=tk.RIGHT, padx=2, pady=3)
        tk.Button(footer, text="IMPORT", command=self.import_target_profile, width=9).pack(side=tk.RIGHT, padx=2, pady=3)
        tk.Button(footer, text="EXPORT", command=self.export_target_profile, width=9).pack(side=tk.RIGHT, padx=2, pady=3)
        tk.Button(footer, text="RELOAD", command=self.reload_from_json, width=9).pack(side=tk.RIGHT, padx=2, pady=3)
        tk.Button(footer, text="SAVE", command=self.save_to_json, bg="#16885f", fg="white", width=9).pack(side=tk.RIGHT, padx=2, pady=3)
        tk.Button(footer, text="CLOSE", command=self.destroy, width=9).pack(side=tk.RIGHT, padx=2, pady=3)

    def _panel(self, parent, title: str, color: str) -> tk.Frame:
        panel = tk.Frame(parent, bg=PANEL, highlightthickness=2, highlightbackground=color)
        panel.grid_columnconfigure(0, weight=1)
        tk.Label(panel, text=title, bg=PANEL, fg=FG, font=("Segoe UI", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        tk.Frame(panel, height=1, bg=LINE).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        return panel

    def _group(self, parent, row: int, title: str, help_text: str | None = None, accent: str = LINE) -> tk.Frame:
        group = tk.LabelFrame(parent, text=title, bg=PANEL, fg=FG, bd=1, relief=tk.SOLID, highlightthickness=1, highlightbackground=accent, font=("Segoe UI", 9, "bold"), labelanchor="nw")
        group.grid(row=row, column=0, sticky="ew", padx=7, pady=5)

        # Kompaktowy układ pod trzy główne kolumny. Suwak jest w jednym
        # wierszu, więc całe okno mieści się bez przewijania.
        group.grid_columnconfigure(0, minsize=86)
        group.grid_columnconfigure(1, weight=1)
        group.grid_columnconfigure(2, minsize=48)
        group.grid_columnconfigure(3, minsize=80)

        if help_text:
            lbl = tk.Label(group, text=help_text, bg=PANEL_2, fg="#d8d8d8", justify=tk.LEFT, anchor="w", wraplength=320, font=("Segoe UI", 8))
            lbl.grid(row=0, column=0, columnspan=4, sticky="ew", padx=8, pady=(6, 8))
            group._next_row = 1
        else:
            group._next_row = 0
        return group

    def _next_row(self, parent) -> int:
        row = int(getattr(parent, "_next_row", 0))
        parent._next_row = row + 1
        return row

    def _label(self, parent, row: int, text: str) -> None:
        tk.Label(parent, text=text, bg=PANEL, fg="#c8c8c8", anchor="w", font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", padx=8, pady=3)

    def _hint(self, parent, row: int, text: str | None) -> None:
        if text:
            tk.Label(parent, text=text, bg=PANEL, fg="#777777", anchor="w", justify=tk.LEFT, wraplength=120, font=("Segoe UI", 8)).grid(row=row, column=3, sticky="w", padx=4, pady=3)

    def _entry_row(self, parent, label: str, var, hint: str | None = None) -> None:
        row = self._next_row(parent)
        self._label(parent, row, label)
        tk.Entry(parent, textvariable=var).grid(row=row, column=1, columnspan=2, sticky="ew", padx=4, pady=3)
        self._hint(parent, row, hint)

    def _combo_row(self, parent, label: str, var, values, hint: str | None = None, command=None) -> ttk.Combobox:
        row = self._next_row(parent)
        self._label(parent, row, label)
        box = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        box.grid(row=row, column=1, columnspan=2, sticky="ew", padx=4, pady=3)
        if command:
            box.bind("<<ComboboxSelected>>", command)
        self._hint(parent, row, hint)
        return box

    def _check_row(self, parent, text: str, var, hint: str | None = None) -> None:
        row = self._next_row(parent)
        cb = tk.Checkbutton(parent, text=text, variable=var, bg=PANEL, fg=FG, selectcolor="#333333", activebackground=PANEL, activeforeground=FG, anchor="w")
        cb.grid(row=row, column=0, columnspan=3, sticky="w", padx=6, pady=3)
        self._hint(parent, row, hint)

    def _scale_row(self, parent, label: str, var, from_, to, resolution, hint: str | None = None) -> None:
        # Jeden kompaktowy wiersz: nazwa | suwak | wartość | krótka podpowiedź.
        # Po przełożeniu kolumny 2 pod 1 mamy dość szerokości, a mniejsza
        # wysokość pozwala zmieścić ustawienia bez scrolla.
        row = self._next_row(parent)
        tk.Label(parent, text=label, bg=PANEL, fg="#c8c8c8", anchor="w", font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", padx=6, pady=2)
        scale = tk.Scale(
            parent,
            variable=var,
            from_=from_,
            to=to,
            resolution=resolution,
            orient=tk.HORIZONTAL,
            bg=PANEL,
            fg=FG,
            troughcolor="#333333",
            highlightthickness=0,
            showvalue=False,
            length=120,
            sliderlength=14,
            width=8,
            bd=0,
        )
        scale.grid(row=row, column=1, sticky="ew", padx=3, pady=1)
        tk.Label(parent, textvariable=var, bg=PANEL, fg="#dcdcdc", anchor="e", width=7, font=("Consolas", 8)).grid(row=row, column=2, sticky="e", padx=3, pady=2)
        if hint:
            tk.Label(parent, text=hint, bg=PANEL, fg="#777777", anchor="w", justify=tk.LEFT, wraplength=95, font=("Segoe UI", 7)).grid(row=row, column=3, sticky="w", padx=2, pady=2)

    def _info_box(self, parent, row: int, text_var, accent: str) -> None:
        box = tk.Label(parent, textvariable=text_var, bg=PANEL_2, fg="#f0d28a", justify=tk.LEFT, anchor="nw", wraplength=360, padx=7, pady=6, font=("Segoe UI", 8), highlightthickness=1, highlightbackground=accent)
        box.grid(row=row, column=0, sticky="ew", padx=10, pady=7)

    # ------------------------------------------------------------------
    # UI PANELS
    # ------------------------------------------------------------------
    def _build_profile_panel(self, parent) -> None:
        parent._next_panel_row = 2
        profiles = self._profile_names()

        g = self._group(parent, 2, "PROFIL ROZPOZNAWANIA", "Wybierasz konkretny cel dla TARZANA. To nie jest już 'czerwone coś', tylko zapisany profil obiektu.", ACCENT_OBJECT)
        self._combo_row(g, "Aktywny profil", self.profile_var, profiles, "profil z JSON", self._on_profile_change)
        self._entry_row(g, "Opis profilu", self.desc_var, "opis dla operatora")
        self._entry_row(g, "Nowy profil", self.new_profile_var, "nazwa do ADD/COPY")
        row = self._next_row(g)
        tk.Button(g, text="ADD / COPY PROFILE", command=self.copy_profile, width=18).grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=8)
        tk.Button(g, text="RESET ACTIVE", command=self.reset_active_object_default, width=14).grid(row=row, column=2, sticky="e", padx=4, pady=8)

        g = self._group(parent, 3, "TRYB OPERATORA", "Operator wybiera co śledzić. Parametry techniczne są zapisywane do JSON, ale nie trzeba ich zgadywać ręcznie.", ACCENT_OBJECT)
        self._check_row(g, "Kolor HSV aktywny", self.color_enabled_var, "pierwszy filtr obiektu")
        self._combo_row(g, "Kształt", self.shape_type_var, list(SHAPE_PRESETS.keys()), "wybór operatorowy", self._on_shape_change)
        self._check_row(g, "Wymagaj kształtu", self.shape_enabled_var, "OFF = tylko kolor")
        row = self._next_row(g)
        tk.Button(g, text="APPLY SHAPE PRESET", command=self.apply_shape_preset, width=22).grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=8)

        self._info_box(parent, 4, self.shape_desc_var, ACCENT_OBJECT)

    def _build_hsv_shape_panel(self, parent) -> None:
        g = self._group(parent, 2, "HSV — ZAKRES KOLORU", "Te suwaki opisują kolor celu. Dla czerwieni używane są dwa zakresy H, bo czerwony leży na początku i końcu skali Hue.", ACCENT_HSV)
        self._scale_row(g, "H1 min", self.h1_min, 0, 180, 1, "pierwszy zakres hue")
        self._scale_row(g, "H1 max", self.h1_max, 0, 180, 1, None)
        self._scale_row(g, "H2 min", self.h2_min, 0, 180, 1, "drugi zakres dla czerwieni")
        self._scale_row(g, "H2 max", self.h2_max, 0, 180, 1, None)
        self._scale_row(g, "S min", self.s_min, 0, 255, 1, "minimalne nasycenie")
        self._scale_row(g, "S max", self.s_max, 0, 255, 1, None)
        self._scale_row(g, "V min", self.v_min, 0, 255, 1, "minimalna jasność")
        self._scale_row(g, "V max", self.v_max, 0, 255, 1, None)

        g = self._group(parent, 3, "STABILNOŚĆ / FILTRY OBIEKTU", "Te wartości decydują, czy znaleziony kontur jest celem, czy przypadkowym śmieciem w obrazie.", ACCENT_HSV)
        self._scale_row(g, "Min area", self.min_area, 20, 20000, 20, "odcina małe śmieci")
        self._scale_row(g, "Max area", self.max_area, 1000, 500000, 1000, "odcina wielkie plamy")
        self._scale_row(g, "Solidity min", self.min_solidity, 0.0, 1.0, 0.01, "zwartość konturu")
        self._scale_row(g, "Extent min", self.min_extent, 0.0, 1.0, 0.01, "wypełnienie boxa")
        self._scale_row(g, "Blur kernel", self.blur_kernel, 1, 21, 2, "wygładza szum")
        self._scale_row(g, "Open kernel", self.open_kernel, 1, 21, 2, "usuwa drobiny")
        self._scale_row(g, "Close kernel", self.close_kernel, 1, 21, 2, "domyka dziury")
        self._check_row(g, "Preferuj największy kontur", self.prefer_largest, "typowo dla znacznika")
        self._check_row(g, "Preferuj obiekt bliżej środka", self.prefer_center, "do przyszłego scoringu")

    def _build_face_save_panel(self, parent) -> None:
        """Sekcja 3 ułożona w dwie wewnętrzne kolumny.

        Nie usuwamy pól. Zmieniamy tylko geometrię, żeby TRACKING SETUP
        zmieścił się w oknie: po lewej wybór i wspólne parametry, po prawej
        MediaPipe / KameraHEAD / Haar. Akcje serwisowe są na dolnym pasku.
        """
        inner = tk.Frame(parent, bg=PANEL)
        inner.grid(row=2, column=0, sticky="nsew", padx=5, pady=3)
        inner.grid_columnconfigure(0, weight=1, uniform="face_inner")
        inner.grid_columnconfigure(1, weight=1, uniform="face_inner")

        left = tk.Frame(inner, bg=PANEL)
        right = tk.Frame(inner, bg=PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        left.grid_columnconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        g = self._group(left, 0, "TWARZ — WYBÓR BIBLIOTEKI", "MediaPipe jest dokładny, Haar szybki, a HEAD_HAAR traktuje cel jako głowę: front + profil.", ACCENT_FACE)
        self._combo_row(g, "Backend", self.face_backend_var, ["MEDIAPIPE", "HAAR", "HEAD_HAAR"], "FACE=twarz, HEAD=głowa")
        self._combo_row(g, "Target point", self.face_target_point, ["FACE_CENTER", "NOSE", "LEFT_EYE", "RIGHT_EYE"], "punkt podążania")
        self._check_row(g, "Draw debug", self.face_draw_debug, "box, środek, tekst")

        g = self._group(left, 1, "WSPÓLNE PARAMETRY FACE / HEAD", "Wspólna stabilność dla twarzy i głowy. Logika zostaje bez zmian; to tylko ustawienia.", ACCENT_FACE)
        self._scale_row(g, "Processing width", self.face_processing_width, 160, 1280, 20, "mniej = szybciej")
        self._scale_row(g, "Preview width", self.face_preview_width, 160, 1280, 20, "obraz do UI")
        self._scale_row(g, "Min face area", self.face_min_area, 100, 50000, 100, "odcina małe detekcje")
        self._scale_row(g, "Max face area", self.face_max_area, 1000, 500000, 1000, "odcina duże boxy")
        self._scale_row(g, "Smoothing", self.face_smoothing, 0.0, 1.0, 0.01, "płynność środka")
        self._scale_row(g, "Area smooth", self.face_area_smoothing, 0.0, 1.0, 0.01, "płynność pola")
        self._scale_row(g, "Hysteresis ON", self.face_hyst_on, 1, 10, 1, "ile ramek do visible")
        self._scale_row(g, "Hysteresis OFF", self.face_hyst_off, 1, 20, 1, "ile ramek do lost")
        self._scale_row(g, "Hold ms", self.face_hold_ms, 0, 2000, 10, "podtrzymanie celu")
        self._scale_row(g, "Max jump px", self.face_max_jump, 20, 1000, 10, "ochrona przed skokiem")

        g = self._group(right, 0, "MEDIAPIPE", "Model 0 → bliska twarz / szybciej. Model 1 → dalsza twarz / zwykle wolniej. Fallback nie zatrzymuje kamery.", ACCENT_FACE)
        self._combo_row(g, "Model selection", self.mp_model_selection, [0, 1], "0 blisko, 1 dalej")
        self._scale_row(g, "Confidence", self.mp_confidence, 0.1, 0.95, 0.01, "próg detekcji")
        self._check_row(g, "Require installed", self.mp_require_installed, "brak = błąd środowiska")

        g = self._group(right, 1, "KameraHEAD — PROFIL GŁOWY", "Operatorowe ustawienia celu GŁOWA. Nie zmieniamy architektury: KHR dalej dostaje jeden error_x, a kamera/tracking pozostają w osobnych workerach.", ACCENT_FACE)
        row = self._next_row(g)
        tk.Label(g, textvariable=self.head_description_var, bg=PANEL_2, fg="#d8d8d8", justify=tk.LEFT, anchor="w", wraplength=460, font=("Segoe UI", 9)).grid(row=row, column=0, columnspan=4, sticky="ew", padx=8, pady=(6, 8))
        self._scale_row(g, "Head min area", self.head_min_area, 100, 60000, 100, "mała głowa / daleko")
        self._scale_row(g, "Head max area", self.head_max_area, 1000, 500000, 1000, "duża głowa / blisko")
        self._scale_row(g, "Head smoothing", self.head_center_smoothing, 0.0, 1.0, 0.01, "płynność środka")
        self._scale_row(g, "Head area smooth", self.head_area_smoothing, 0.0, 1.0, 0.01, "płynność rozmiaru")
        self._scale_row(g, "Head hold ms", self.head_hold_ms, 0, 2000, 10, "podtrzymanie przy obrocie")
        self._scale_row(g, "Head max jump", self.head_max_jump_px, 20, 1200, 10, "ochrona przed przeskokiem")
        self._scale_row(g, "Front weight", self.head_front_weight, 0.1, 2.0, 0.05, "priorytet frontu")
        self._scale_row(g, "Profile weight", self.head_profile_weight, 0.1, 2.0, 0.05, "priorytet profilu")
        self._scale_row(g, "Detect every N", self.head_detect_every_n, 1, 10, 1, "co ile klatek HEAD")
        self._scale_row(g, "Profile every N", self.head_profile_every_n, 1, 12, 1, "profil rzadziej = lżej")
        self._check_row(g, "Profil lewy aktywny", self.head_use_left_profile, "odbicie klatki")
        self._check_row(g, "Profil prawy aktywny", self.head_use_right_profile, "oryginalna klatka")
        row = self._next_row(g)
        tk.Label(g, text="Zaawansowane: pliki XML OpenCV są klasyfikatorami Haar. Zostają zapisane w JSON, ale operator normalnie stroi parametry powyżej.", bg=PANEL, fg="#aaaaaa", justify=tk.LEFT, anchor="w", wraplength=460, font=("Segoe UI", 8)).grid(row=row, column=0, columnspan=4, sticky="ew", padx=8, pady=(6, 2))
        self._entry_row(g, "Profile cascade XML", self.head_profile_cascade, "serwisowe / OpenCV")

        g = self._group(right, 2, "OPENCV HAAR", "Fallback OpenCV. Szybki i bezpieczny; utrzymuje tracking, gdy MediaPipe nie działa.", ACCENT_FACE)
        self._entry_row(g, "Cascade", self.haar_cascade, "plik cascade")
        self._scale_row(g, "Scale factor", self.haar_scale, 1.01, 1.5, 0.01, "skala piramidy")
        self._scale_row(g, "Min neighbors", self.haar_neighbors, 1, 20, 1, "więcej = pewniej")
        self._scale_row(g, "Min size W", self.haar_min_w, 10, 400, 10, None)
        self._scale_row(g, "Min size H", self.haar_min_h, 10, 400, 10, None)
        self._scale_row(g, "Max size W", self.haar_max_w, 0, 1000, 10, "0 = brak limitu")
        self._scale_row(g, "Max size H", self.haar_max_h, 0, 1000, 10, None)
        self._check_row(g, "Equalize hist", self.haar_equalize, "lepszy kontrast")

        
    def _build_target_lock_panel(self, parent) -> None:
        """Czwarta kolumna: globalne przyspawanie celu dla wszystkich pluginów.

        To jest tylko układ. Logika TargetLock, zapis JSON i parametry zostają te same.
        """
        g = self._group(
            parent,
            2,
            "GLOBAL TARGET LOCK — PRZYSPAWANIE CELU",
            "Wspólna stabilizacja dla KameraHSV / Haar / MediaPipe / HEAD. Na podglądzie: DETECT zielony, LOCK żółty, HOLD pomarańczowy przerywany.",
            ACCENT_SAVE,
        )
        self._check_row(g, "Target Lock aktywny", self.target_lock_enabled, "ON = KHR nie traci korekcji po jednej zgubionej próbce")
        self._check_row(g, "Rysuj status na podglądzie", self.target_lock_draw_overlay, "prosta ramka + tekst LOCK/HOLD")
        self._scale_row(g, "Hold target ms", self.target_lock_hold_ms, 0, 2000, 10, "czas przyspawania po zgubieniu")
        self._scale_row(g, "Lock frames", self.target_lock_confirm_frames, 1, 10, 1, "ile trafień do LOCK")
        self._scale_row(g, "Lost frames", self.target_lock_lost_frames, 1, 20, 1, "ile pustych prób do LOST")
        self._scale_row(g, "Error smoothing", self.target_lock_error_smoothing, 0.0, 1.0, 0.01, "wygładza korekcję error_x")
        self._scale_row(g, "Center smoothing", self.target_lock_center_smoothing, 0.0, 1.0, 0.01, "wygładza pozycję celu")
        self._scale_row(g, "Area smoothing", self.target_lock_area_smoothing, 0.0, 1.0, 0.01, "wygładza rozmiar ramki")
        self._scale_row(g, "Lost decay", self.target_lock_decay, 0.0, 1.0, 0.01, "powolne gaszenie error_x w HOLD")
        self._scale_row(g, "Max jump px", self.target_lock_max_jump_px, 20, 1500, 10, "ochrona przed przeskokiem na inny cel")
        self._scale_row(g, "Box scale", self.target_lock_box_scale, 0.5, 3.0, 0.05, "rozmiar ramki lock na podglądzie")


    # ------------------------------------------------------------------
    # DATA LOAD/SAVE
    # ------------------------------------------------------------------
    def _profile_names(self) -> list[str]:
        return list(self.settings.get("tracking", {}).get("target_profiles", {}).keys()) or ["RED_OBJECT"]

    def _active_profile_data(self) -> dict:
        tracking = self.settings.setdefault("tracking", {})
        profiles = tracking.setdefault("target_profiles", {})
        name = self.profile_var.get() or tracking.get("active_target", "RED_OBJECT")
        if name not in profiles:
            profiles[name] = copy.deepcopy(DEFAULT_OBJECT_PROFILE)
        return profiles[name]

    def _on_profile_change(self, _event=None) -> None:
        self._load_active_profile_to_vars()
        self._update_status(f"Wczytano profil obiektu: {self.profile_var.get()}")

    def _on_shape_change(self, _event=None) -> None:
        self._update_shape_description()

    def _update_shape_description(self) -> None:
        key = str(self.shape_type_var.get() or "ANY")
        preset = SHAPE_PRESETS.get(key, SHAPE_PRESETS["ANY"])
        self.shape_desc_var.set(f"{preset['label']} — {preset['description']}")
        self.shape_enabled_var.set(key != "ANY")

    def _load_active_profile_to_vars(self) -> None:
        tracking = self.settings.setdefault("tracking", {})
        active = str(tracking.get("active_target", self.profile_var.get() or "RED_OBJECT"))
        self.profile_var.set(active)
        profile = self._active_profile_data()
        self.desc_var.set(str(profile.get("description", "")))
        self.color_enabled_var.set(bool(profile.get("color_enabled", True)))
        self.shape_enabled_var.set(bool(profile.get("shape_enabled", False)))
        shape = profile.get("shape", {}) or {}
        self.shape_type_var.set(str(shape.get("type", "ANY")))

        ranges = profile.get("hsv_ranges", DEFAULT_OBJECT_PROFILE["hsv_ranges"])
        r1 = ranges[0] if len(ranges) > 0 else DEFAULT_OBJECT_PROFILE["hsv_ranges"][0]
        r2 = ranges[1] if len(ranges) > 1 else DEFAULT_OBJECT_PROFILE["hsv_ranges"][1]
        self.h1_min.set(int(r1.get("h_min", 0)))
        self.h1_max.set(int(r1.get("h_max", 10)))
        self.h2_min.set(int(r2.get("h_min", 170)))
        self.h2_max.set(int(r2.get("h_max", 180)))
        self.s_min.set(int(r1.get("s_min", 90)))
        self.s_max.set(int(r1.get("s_max", 255)))
        self.v_min.set(int(r1.get("v_min", 70)))
        self.v_max.set(int(r1.get("v_max", 255)))

        self.min_area.set(float(profile.get("min_area", 500.0)))
        self.max_area.set(float(profile.get("max_area", 250000.0)))
        self.min_solidity.set(float(profile.get("min_solidity", 0.45)))
        self.min_extent.set(float(profile.get("min_extent", 0.18)))
        self.blur_kernel.set(int(profile.get("blur_kernel", 3)))
        self.open_kernel.set(int(profile.get("morph_open_kernel", 5)))
        self.close_kernel.set(int(profile.get("morph_close_kernel", 7)))
        self.prefer_largest.set(bool(profile.get("prefer_largest_contour", True)))
        self.prefer_center.set(bool(profile.get("prefer_center", False)))
        self._update_shape_description()

    def _load_face_to_vars(self) -> None:
        face = self.settings.setdefault("tracking", {}).setdefault("face_tracking", {})
        common = face.setdefault("common", {})
        mp = face.setdefault("mediapipe", {})
        haar = face.setdefault("haar", {})

        self.face_backend_var.set(str(face.get("active_backend", face.get("backend", "MEDIAPIPE"))).upper())
        self.face_processing_width.set(int(common.get("processing_max_width", face.get("processing_max_width", 480))))
        self.face_preview_width.set(int(common.get("preview_max_width", face.get("max_width", 640))))
        self.face_draw_debug.set(bool(common.get("draw_debug", face.get("draw_debug", True))))
        self.face_min_area.set(float(common.get("min_face_area", face.get("min_face_area", 1200.0))))
        self.face_max_area.set(float(common.get("max_face_area", 250000.0)))
        self.face_target_point.set(str(common.get("target_point", "FACE_CENTER")))
        self.face_smoothing.set(float(common.get("center_smoothing", 0.35)))
        self.face_area_smoothing.set(float(common.get("area_smoothing", 0.25)))
        self.face_hyst_on.set(int(common.get("visible_hysteresis_on", 2)))
        self.face_hyst_off.set(int(common.get("visible_hysteresis_off", 5)))
        self.face_hold_ms.set(int(common.get("hold_last_target_ms", 250)))
        self.face_max_jump.set(float(common.get("max_jump_px", 260)))

        self.mp_model_selection.set(int(mp.get("model_selection", face.get("model_selection", 0))))
        self.mp_confidence.set(float(mp.get("min_detection_confidence", face.get("min_detection_confidence", 0.55))))
        self.mp_require_installed.set(bool(mp.get("require_installed", True)))

        self.haar_cascade.set(str(haar.get("cascade_name", "haarcascade_frontalface_default.xml")))
        self.haar_scale.set(float(haar.get("scale_factor", 1.10)))
        self.haar_neighbors.set(int(haar.get("min_neighbors", 5)))
        self.haar_min_w.set(int(haar.get("min_size_w", 40)))
        self.haar_min_h.set(int(haar.get("min_size_h", 40)))
        self.haar_max_w.set(int(haar.get("max_size_w", 0)))
        self.haar_max_h.set(int(haar.get("max_size_h", 0)))
        self.haar_equalize.set(bool(haar.get("equalize_hist", True)))
        head = face.setdefault("head", {})
        self.head_profile_cascade.set(str(head.get("profile_cascade_name", haar.get("profile_cascade_name", "haarcascade_profileface.xml"))))
        self.head_min_area.set(float(head.get("min_head_area", common.get("min_face_area", 1400.0))))
        self.head_max_area.set(float(head.get("max_head_area", common.get("max_face_area", 300000.0))))
        self.head_center_smoothing.set(float(head.get("center_smoothing", common.get("center_smoothing", 0.28))))
        self.head_area_smoothing.set(float(head.get("area_smoothing", common.get("area_smoothing", 0.22))))
        self.head_hold_ms.set(int(head.get("hold_last_head_ms", common.get("hold_last_target_ms", 450))))
        self.head_max_jump_px.set(float(head.get("max_head_jump_px", common.get("max_jump_px", 320.0))))
        self.head_front_weight.set(float(head.get("front_weight", 1.0)))
        self.head_profile_weight.set(float(head.get("profile_weight", 0.92)))
        self.head_detect_every_n.set(int(head.get("detect_every_n", 2)))
        self.head_profile_every_n.set(int(head.get("profile_every_n", 3)))
        self.head_use_left_profile.set(bool(head.get("use_left_profile", True)))
        self.head_use_right_profile.set(bool(head.get("use_right_profile", True)))

        target_lock = self.settings.setdefault("tracking", {}).setdefault("target_lock", {})
        self.target_lock_enabled.set(bool(target_lock.get("enabled", True)))
        self.target_lock_draw_overlay.set(bool(target_lock.get("draw_overlay", True)))
        self.target_lock_hold_ms.set(int(target_lock.get("hold_ms", 550)))
        self.target_lock_confirm_frames.set(int(target_lock.get("lock_confirm_frames", 2)))
        self.target_lock_lost_frames.set(int(target_lock.get("lost_confirm_frames", 6)))
        self.target_lock_error_smoothing.set(float(target_lock.get("error_smoothing", 0.35)))
        self.target_lock_center_smoothing.set(float(target_lock.get("center_smoothing", 0.30)))
        self.target_lock_area_smoothing.set(float(target_lock.get("area_smoothing", 0.20)))
        self.target_lock_decay.set(float(target_lock.get("lost_decay", 0.96)))
        self.target_lock_max_jump_px.set(float(target_lock.get("max_jump_px", 300.0)))
        self.target_lock_box_scale.set(float(target_lock.get("approximate_box_scale", 1.35)))

    def _write_vars_to_settings(self) -> None:
        tracking = self.settings.setdefault("tracking", {})
        tracking["active_target"] = str(self.profile_var.get())
        profile = self._active_profile_data()

        profile["description"] = str(self.desc_var.get())
        profile["color_enabled"] = bool(self.color_enabled_var.get())
        profile["shape_enabled"] = bool(self.shape_enabled_var.get())
        profile["hsv_ranges"] = [
            {"h_min": int(self.h1_min.get()), "s_min": int(self.s_min.get()), "v_min": int(self.v_min.get()), "h_max": int(self.h1_max.get()), "s_max": int(self.s_max.get()), "v_max": int(self.v_max.get())},
            {"h_min": int(self.h2_min.get()), "s_min": int(self.s_min.get()), "v_min": int(self.v_min.get()), "h_max": int(self.h2_max.get()), "s_max": int(self.s_max.get()), "v_max": int(self.v_max.get())},
        ]
        profile["min_area"] = float(self.min_area.get())
        profile["max_area"] = float(self.max_area.get())
        profile["min_solidity"] = float(self.min_solidity.get())
        profile["min_extent"] = float(self.min_extent.get())
        profile["blur_kernel"] = int(self.blur_kernel.get())
        profile["morph_open_kernel"] = int(self.open_kernel.get())
        profile["morph_close_kernel"] = int(self.close_kernel.get())
        profile["prefer_largest_contour"] = bool(self.prefer_largest.get())
        profile["prefer_center"] = bool(self.prefer_center.get())
        preset = SHAPE_PRESETS.get(str(self.shape_type_var.get()), SHAPE_PRESETS["ANY"])
        profile["shape"] = copy.deepcopy(preset["shape"])
        tracking.setdefault("target_profiles", {})[str(self.profile_var.get())] = profile

        face = tracking.setdefault("face_tracking", {})
        face["active_backend"] = str(self.face_backend_var.get()).upper()
        face["backend"] = str(self.face_backend_var.get()).upper()
        face["processing_max_width"] = int(self.face_processing_width.get())
        face["max_width"] = int(self.face_preview_width.get())
        face["draw_debug"] = bool(self.face_draw_debug.get())
        face["min_face_area"] = float(self.face_min_area.get())
        face["common"] = {
            "processing_max_width": int(self.face_processing_width.get()),
            "preview_max_width": int(self.face_preview_width.get()),
            "draw_debug": bool(self.face_draw_debug.get()),
            "select_largest_face": True,
            "min_face_area": float(self.face_min_area.get()),
            "max_face_area": float(self.face_max_area.get()),
            "target_point": str(self.face_target_point.get()),
            "center_smoothing": float(self.face_smoothing.get()),
            "area_smoothing": float(self.face_area_smoothing.get()),
            "visible_hysteresis_on": int(self.face_hyst_on.get()),
            "visible_hysteresis_off": int(self.face_hyst_off.get()),
            "hold_last_target_ms": int(self.face_hold_ms.get()),
            "max_jump_px": float(self.face_max_jump.get()),
        }
        face["mediapipe"] = {
            "enabled": True,
            "require_installed": bool(self.mp_require_installed.get()),
            "model_selection": int(self.mp_model_selection.get()),
            "min_detection_confidence": float(self.mp_confidence.get()),
        }
        face["model_selection"] = int(self.mp_model_selection.get())
        face["min_detection_confidence"] = float(self.mp_confidence.get())
        face["haar"] = {
            "enabled": True,
            "cascade_name": str(self.haar_cascade.get()),
            "profile_cascade_name": str(self.head_profile_cascade.get()),
            "scale_factor": float(self.haar_scale.get()),
            "min_neighbors": int(self.haar_neighbors.get()),
            "flags": 0,
            "min_size_w": int(self.haar_min_w.get()),
            "min_size_h": int(self.haar_min_h.get()),
            "max_size_w": int(self.haar_max_w.get()),
            "max_size_h": int(self.haar_max_h.get()),
            "equalize_hist": bool(self.haar_equalize.get()),
        }
        face["head"] = {
            "enabled": True,
            "backend": "HEAD_HAAR",
            "frontal_cascade_name": str(self.haar_cascade.get()),
            "profile_cascade_name": str(self.head_profile_cascade.get()),
            "min_head_area": float(self.head_min_area.get()),
            "max_head_area": float(self.head_max_area.get()),
            "center_smoothing": float(self.head_center_smoothing.get()),
            "area_smoothing": float(self.head_area_smoothing.get()),
            "hold_last_head_ms": int(self.head_hold_ms.get()),
            "max_head_jump_px": float(self.head_max_jump_px.get()),
            "front_weight": float(self.head_front_weight.get()),
            "profile_weight": float(self.head_profile_weight.get()),
            "detect_every_n": int(self.head_detect_every_n.get()),
            "profile_every_n": int(self.head_profile_every_n.get()),
            "use_left_profile": bool(self.head_use_left_profile.get()),
            "use_right_profile": bool(self.head_use_right_profile.get()),
            "description": "Głowa jako jeden cel: frontal + profil prawy + profil lewy + hold filtra.",
        }

        tracking["target_lock"] = {
            "enabled": bool(self.target_lock_enabled.get()),
            "draw_overlay": bool(self.target_lock_draw_overlay.get()),
            "hold_ms": int(self.target_lock_hold_ms.get()),
            "lock_confirm_frames": int(self.target_lock_confirm_frames.get()),
            "lost_confirm_frames": int(self.target_lock_lost_frames.get()),
            "error_smoothing": float(self.target_lock_error_smoothing.get()),
            "center_smoothing": float(self.target_lock_center_smoothing.get()),
            "area_smoothing": float(self.target_lock_area_smoothing.get()),
            "lost_decay": float(self.target_lock_decay.get()),
            "max_jump_px": float(self.target_lock_max_jump_px.get()),
            "approximate_box_scale": float(self.target_lock_box_scale.get()),
            "description": "Globalne przyspawanie celu po każdym pluginie: DETECT / LOCK / HOLD / LOST.",
        }

    def apply_shape_preset(self) -> None:
        preset = SHAPE_PRESETS.get(str(self.shape_type_var.get()), SHAPE_PRESETS["ANY"])
        self.shape_enabled_var.set(bool(preset["shape_enabled"]))
        self._update_shape_description()
        self._update_status(f"Zastosowano preset kształtu: {preset['label']}")

    def copy_profile(self) -> None:
        self._write_vars_to_settings()
        new_name = str(self.new_profile_var.get()).strip() or "CUSTOM_OBJECT_01"
        profiles = self.settings.setdefault("tracking", {}).setdefault("target_profiles", {})
        profiles[new_name] = copy.deepcopy(self._active_profile_data())
        self.settings["tracking"]["active_target"] = new_name
        self.profile_var.set(new_name)
        self._update_status(f"Dodano/skopiowano profil: {new_name}. Kliknij SAVE PARAMETERS, aby zapisać do JSON.")

    def reset_active_object_default(self) -> None:
        name = str(self.profile_var.get()) or "RED_OBJECT"
        self.settings.setdefault("tracking", {}).setdefault("target_profiles", {})[name] = copy.deepcopy(DEFAULT_OBJECT_PROFILE)
        self._load_active_profile_to_vars()
        self._update_status(f"Zresetowano profil {name} do ustawień domyślnych. Kliknij SAVE PARAMETERS, aby zapisać.")

    def reload_from_json(self) -> None:
        self.settings = load_vision_settings(self.project_root)
        self._load_active_profile_to_vars()
        self._load_face_to_vars()
        self._update_status("Przeładowano ustawienia z JSON")


    def export_target_profile(self) -> None:
        """Eksportuje aktywny profil obiektu do osobnego JSON.

        To jest funkcja serwisowa TRACKING SETUP, nie przycisk głównego KHR.
        Główne KHR zawsze ładuje active_target z vision_settings.json automatycznie.
        """
        self._write_vars_to_settings()
        name = str(self.profile_var.get() or "TARGET")
        data = {
            "type": "TARZAN_TARGET_PROFILE",
            "name": name,
            "profile": copy.deepcopy(self._active_profile_data()),
        }
        default_dir = self.project_root / "data" / "khr" / "targets"
        default_dir.mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(
            title="Eksport profilu targetu",
            initialdir=str(default_dir),
            initialfile=f"{name}.json",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Wszystkie pliki", "*.*")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._update_status(f"Wyeksportowano profil targetu: {path}")

    def import_target_profile(self) -> None:
        """Importuje profil targetu i ustawia go jako aktywny w TRACKING SETUP."""
        default_dir = self.project_root / "data" / "khr" / "targets"
        default_dir.mkdir(parents=True, exist_ok=True)
        path = filedialog.askopenfilename(
            title="Import profilu targetu",
            initialdir=str(default_dir),
            filetypes=[("JSON", "*.json"), ("Wszystkie pliki", "*.*")],
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "profile" in data:
            name = str(data.get("name") or Path(path).stem)
            profile = data.get("profile") or {}
        else:
            name = Path(path).stem
            profile = data

        if not isinstance(profile, dict):
            self._update_status("IMPORT TARGET ERROR: plik nie zawiera profilu JSON")
            return

        tracking = self.settings.setdefault("tracking", {})
        profiles = tracking.setdefault("target_profiles", {})
        profiles[name] = copy.deepcopy(profile)
        tracking["active_target"] = name
        self.profile_var.set(name)
        self._load_active_profile_to_vars()
        self._update_status(f"Zaimportowano profil targetu: {name}. Kliknij SAVE PARAMETERS, aby zapisać do vision_settings.json.")

    def save_to_json(self) -> None:
        self._write_vars_to_settings()
        path = self.project_root / "data" / "khr" / "vision_settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
        try:
            if hasattr(self.parent, "_reload_vision_settings_from_json"):
                self.parent._reload_vision_settings_from_json()
        except Exception:
            pass
        self._update_status(f"Zapisano parametry trackingu do JSON: {path}")

    def _update_status(self, text: str) -> None:
        self.status_var.set(text)
