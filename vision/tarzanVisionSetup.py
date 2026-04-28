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
from tkinter import ttk

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

        self.content.grid_columnconfigure(0, weight=1, uniform="vision_cols")
        self.content.grid_columnconfigure(1, weight=1, uniform="vision_cols")
        self.content.grid_columnconfigure(2, weight=1, uniform="vision_cols")

        col_object = self._panel(self.content, "1  PROFIL OBIEKTU", ACCENT_OBJECT)
        col_hsv = self._panel(self.content, "2  KOLOR + KSZTAŁT + STABILNOŚĆ", ACCENT_HSV)
        col_face = self._panel(self.content, "3  TWARZ / BIBLIOTEKI + SAVE", ACCENT_FACE)
        col_object.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)
        col_hsv.grid(row=0, column=1, sticky="nsew", padx=6, pady=4)
        col_face.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=4)

        self._build_profile_panel(col_object)
        self._build_hsv_shape_panel(col_hsv)
        self._build_face_save_panel(col_face)

        footer = tk.Frame(self, bg=BG)
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(2, 8))
        tk.Label(footer, textvariable=self.status_var, bg=BG, fg="#d6d6d6", anchor="w", font=("Consolas", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(footer, text="SAVE PARAMETERS", command=self.save_to_json, bg="#16885f", fg="white", width=20).pack(side=tk.RIGHT, padx=4)
        tk.Button(footer, text="RELOAD JSON", command=self.reload_from_json, width=14).pack(side=tk.RIGHT, padx=4)
        tk.Button(footer, text="CLOSE", command=self.destroy, width=10).pack(side=tk.RIGHT, padx=4)

    def _panel(self, parent, title: str, color: str) -> tk.Frame:
        panel = tk.Frame(parent, bg=PANEL, highlightthickness=2, highlightbackground=color)
        panel.grid_columnconfigure(0, weight=1)
        tk.Label(panel, text=title, bg=PANEL, fg=FG, font=("Segoe UI", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        tk.Frame(panel, height=1, bg=LINE).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        return panel

    def _group(self, parent, row: int, title: str, help_text: str | None = None, accent: str = LINE) -> tk.Frame:
        group = tk.LabelFrame(parent, text=title, bg=PANEL, fg=FG, bd=1, relief=tk.SOLID, highlightthickness=1, highlightbackground=accent, font=("Segoe UI", 9, "bold"), labelanchor="nw")
        group.grid(row=row, column=0, sticky="ew", padx=10, pady=7)
        group.grid_columnconfigure(0, minsize=170)
        group.grid_columnconfigure(1, weight=1)
        group.grid_columnconfigure(2, minsize=82)
        group.grid_columnconfigure(3, minsize=190)
        if help_text:
            lbl = tk.Label(group, text=help_text, bg=PANEL_2, fg="#d8d8d8", justify=tk.LEFT, anchor="w", wraplength=620, font=("Segoe UI", 9))
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
            tk.Label(parent, text=text, bg=PANEL, fg="#777777", anchor="w", justify=tk.LEFT, wraplength=210, font=("Segoe UI", 8)).grid(row=row, column=3, sticky="w", padx=6, pady=3)

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
        row = self._next_row(parent)
        self._label(parent, row, label)
        scale = tk.Scale(parent, variable=var, from_=from_, to=to, resolution=resolution, orient=tk.HORIZONTAL, bg=PANEL, fg=FG, troughcolor="#333333", highlightthickness=0, showvalue=False)
        scale.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
        tk.Label(parent, textvariable=var, bg=PANEL, fg="#dcdcdc", anchor="e", width=8, font=("Consolas", 9)).grid(row=row, column=2, sticky="e", padx=4, pady=3)
        self._hint(parent, row, hint)

    def _info_box(self, parent, row: int, text_var, accent: str) -> None:
        box = tk.Label(parent, textvariable=text_var, bg=PANEL_2, fg="#f0d28a", justify=tk.LEFT, anchor="nw", wraplength=620, padx=8, pady=8, font=("Segoe UI", 9), highlightthickness=1, highlightbackground=accent)
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

        g = self._group(parent, 5, "JAK TO DZIAŁA", None, ACCENT_OBJECT)
        text = (
            "1. Kolor HSV wycina z obrazu tylko obszar celu.\n"
            "2. Kształt operatorowy ogranicza przypadkowe trafienia.\n"
            "3. Stabilizacja decyduje czy cel jest wiarygodny.\n"
            "4. KHR używa wyłącznie error_x i visible — nie steruje kamerą."
        )
        tk.Label(g, text=text, bg=PANEL, fg="#d8d8d8", justify=tk.LEFT, anchor="w", wraplength=620, font=("Segoe UI", 9)).grid(row=0, column=0, columnspan=4, sticky="ew", padx=8, pady=8)

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
        g = self._group(parent, 2, "TWARZ — WYBÓR BIBLIOTEKI", "MediaPipe jest docelową zależnością TARZANA. Haar zostaje jako tryb awaryjny/testowy.", ACCENT_FACE)
        self._combo_row(g, "Backend", self.face_backend_var, ["MEDIAPIPE", "HAAR"], "biblioteka twarzy")
        self._combo_row(g, "Target point", self.face_target_point, ["FACE_CENTER", "NOSE", "LEFT_EYE", "RIGHT_EYE"], "punkt podążania")
        self._check_row(g, "Draw debug", self.face_draw_debug, "box, środek, tekst")

        g = self._group(parent, 3, "WSPÓLNE PARAMETRY FACE", "Te ustawienia są niezależne od biblioteki i wpływają na stabilność podążania za twarzą.", ACCENT_FACE)
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

        g = self._group(parent, 4, "MEDIAPIPE", "Model 0: bliższe twarze. Model 1: dalszy dystans. Confidence to próg pewności detekcji.", ACCENT_FACE)
        self._combo_row(g, "Model selection", self.mp_model_selection, [0, 1], "0 blisko, 1 dalej")
        self._scale_row(g, "Confidence", self.mp_confidence, 0.1, 0.95, 0.01, "próg detekcji")
        self._check_row(g, "Require installed", self.mp_require_installed, "brak = błąd środowiska")

        g = self._group(parent, 5, "OPENCV HAAR", "Tryb awaryjny. Scale factor i min neighbors decydują o czułości i liczbie fałszywych detekcji.", ACCENT_FACE)
        self._entry_row(g, "Cascade", self.haar_cascade, "plik cascade")
        self._scale_row(g, "Scale factor", self.haar_scale, 1.01, 1.5, 0.01, "skala piramidy")
        self._scale_row(g, "Min neighbors", self.haar_neighbors, 1, 20, 1, "więcej = pewniej")
        self._scale_row(g, "Min size W", self.haar_min_w, 10, 400, 10, None)
        self._scale_row(g, "Min size H", self.haar_min_h, 10, 400, 10, None)
        self._scale_row(g, "Max size W", self.haar_max_w, 0, 1000, 10, "0 = brak limitu")
        self._scale_row(g, "Max size H", self.haar_max_h, 0, 1000, 10, None)
        self._check_row(g, "Equalize hist", self.haar_equalize, "lepszy kontrast")

        g = self._group(parent, 6, "ZAPIS / AKCJE", "SAVE PARAMETERS zapisuje wszystko do data/khr/vision_settings.json. Główne KHR potem tylko czyta te ustawienia.", ACCENT_SAVE)
        row = self._next_row(g)
        tk.Button(g, text="SAVE PARAMETERS TO JSON", command=self.save_to_json, bg="#16885f", fg="white", height=2).grid(row=row, column=0, columnspan=4, sticky="ew", padx=8, pady=5)
        row = self._next_row(g)
        tk.Button(g, text="RELOAD FROM JSON", command=self.reload_from_json, height=2).grid(row=row, column=0, columnspan=2, sticky="ew", padx=8, pady=5)
        tk.Button(g, text="RESET OBJECT DEFAULT", command=self.reset_active_object_default, height=2).grid(row=row, column=2, columnspan=2, sticky="ew", padx=8, pady=5)

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
            "scale_factor": float(self.haar_scale.get()),
            "min_neighbors": int(self.haar_neighbors.get()),
            "flags": 0,
            "min_size_w": int(self.haar_min_w.get()),
            "min_size_h": int(self.haar_min_h.get()),
            "max_size_w": int(self.haar_max_w.get()),
            "max_size_h": int(self.haar_max_h.get()),
            "equalize_hist": bool(self.haar_equalize.get()),
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
