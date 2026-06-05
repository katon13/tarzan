from __future__ import annotations
from core.tarzanSignalBus import get_signal_bus
from core.TSP.tarzanTspClient import TarzanTspClient
from core.TSP.tarzanTspConfig import TSP_MINI_PC_HOST
from core.tarzanSnajper import create_default_tarzan_snajper, TkCanvasSnajperAdapter, TkWidgetSnajperAdapter
from core.tarzanSnajperTarget import T

import copy
import json
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any, Callable

import tkinter as tk
from tkinter import filedialog
from tkinter import font as tkfont

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except Exception as exc:  # pragma: no cover
    raise RuntimeError("TARZAN EHR wymaga Pillow. Zainstaluj: pip install pillow") from exc

from editor.EHR.tarzanEhrMainTakeSettings import DEFAULT_AXIS_COLORS, MainTakeSettings
from editor.EHR.tarzanEhrMultiAxisModel import (
    AxisCurveModel,
    DEFAULT_AXIS_DEFINITIONS,
    EhrEditorConfig,
    StepTuning,
)
from editor.EHR.tarzanTakeTxtCore import save_take_txt, load_take_txt, next_take_txt_path
from editor.KRO.tarzanKroEhrAdapter import TarzanKroEhrAdapter

try:
    from core.tarzanProfiler import profile_method
except Exception:
    def profile_method(name=None):
        def decorator(func):
            return func
        return decorator

# --- ŚCIEŻKI I ŚRODOWISKO ---

# UWAGA: tarzanEhrUi.py jest w editor/EHR, więc parents[2] to root
THIS_FILE = Path(__file__).resolve()
PROJECT_DIR = THIS_FILE.parents[2]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

DATA_DIR = PROJECT_DIR / "data"
EHR_DIR = DATA_DIR / "ehr"
TAKE_DIR = DATA_DIR / "protokoly"
TAKE_DATA_DIR = DATA_DIR / "take"
IMG_TAKE_DIR = PROJECT_DIR / "img" / "take"
FONT_DIR = PROJECT_DIR / "font"

SLOTS_JSON_PATH = EHR_DIR / "take_protocol_slots.json"
SANDBOX_ASSET_DIR = Path("/mnt/data")
SANDBOX_FONT_PATH = PROJECT_DIR / "font" / "Pattifont.ttf"

try:
    from core.tarzanAssets import take_icon as project_take_icon  # type: ignore
except Exception:
    project_take_icon = None

# --- KOLORY / STAŁE UI ---

WINDOW_BG = "#16181C"
HEADER_BG = "#0A1020"
PROTOCOL_OUTER_BG = "#1B2028"
PROTOCOL_INNER_BG = "#1B2028"
STATUS_BG = "#09101D"

TEXT = "#F3F7FB"
MUTED = "#A7B3C3"
STATUS_FG = "#D5DCE7"

BTN_GREEN = "#46815A"
BTN_GREEN_ACTIVE = "#3E744F"
SAVE_GREEN_FG = "#F4FBF5"

TITLE_HEIGHT = 58
STATUS_HEIGHT = 36
SLOT_COUNT = 10

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 520

# --- STAŁE GŁÓWNEGO UKŁADU EHR ---
# Jedno źródło szerokości lewej kolumny: B = zegar, D = podgląd/info.
LEFT_COLUMN_WIDTH = 400
CLOCK_FONT_SIZE = 80
CLOCK_FONT_CANDIDATES = (
    "DSEG7 Classic",
    "DSEG7 Classic Mini",
    "DSEG7 Modern",
    "DSEG7 Modern Mini",
    "Digital-7 Mono",
    "Digital-7",
    "Seven Segment",
    "Seven Segment Display",
    "DS-Digital",
    "LCDMono2",
    "Consolas",
)

# --- STAŁE BOCZNEGO PODGLĄDU STEP STRUMIEŃ ---
# Text nie może rozpychać lewej kolumny; szerokość trzyma LEFT_COLUMN_WIDTH.
PROTOCOL_STREAM_TEXT_HEIGHT = 42
PROTOCOL_STREAM_TEXT_WIDTH = 1
PROTOCOL_STREAM_DESC_FONT_SIZE = 5
PROTOCOL_STREAM_BITS_FONT_SIZE = 5
PROTOCOL_STREAM_FG = "#22C55E"
PROTOCOL_STREAM_DESC_FONT_CANDIDATES = (
    "Lato",
    "Lato Medium",
    "Lato Semibold",
    "Segoe UI",
    "Arial",
    "Verdana",
    "Tahoma",
    "Consolas",
)
PROTOCOL_STREAM_PRE_ROLL_ROWS = 80
PROTOCOL_STREAM_CHUNK_SIZE = 68


def _select_first_available_font(candidates: tuple[str, ...], fallback: str) -> str:
    """Zwraca pierwszy dostępny font Tkinter z listy kandydatów."""
    try:
        available = {str(name).lower(): str(name) for name in tkfont.families()}
        for candidate in candidates:
            found = available.get(candidate.lower())
            if found:
                return found
    except Exception:
        pass
    return fallback


def select_clock_font_family() -> str:
    """Wybiera font zegara w stylu seven-segment, zgodnie z PAR, z bezpiecznym fallbackiem."""
    return _select_first_available_font(CLOCK_FONT_CANDIDATES, "Consolas")


def select_protocol_desc_font_family() -> str:
    """Wybiera czytelny font opisów bocznego STEP STRUMIEŃ."""
    return _select_first_available_font(PROTOCOL_STREAM_DESC_FONT_CANDIDATES, "Segoe UI")

# --- KONFIGURACJA POZYCJI KONTROLEK OSI ---
GEAR_OFFSET_X = -15
GEAR_OFFSET_Y = -10
# Ikona wygładzania ma stać obok zębatki, a nie daleko w pasie KRO.
SMOOTH_OFFSET_X = -45
SMOOTH_OFFSET_Y = -10
CONTROL_FONT_SIZE = 14

# --- KLASY UI ---
@dataclass
class UiSettings:
    """Ustawienia layoutu TAKE zapisane wyłącznie w kodzie."""

    protocol_title_y: int = 0
    protocol_height: int = 0
    row_center_y: int = 0
    protocol_inner_pad_x: int = 0
    row_pad_x: int = 0

    icon_width: int = 0
    icon_height: int = 0

    number_x: int = 0
    number_y: int = 0
    number_font_size: int = 0
    number_digits: int = 0
    number_dx: int = 0
    number_dy: int = 0

    version_x: int = 0
    version_y: int = 0
    version_font_size: int = 0
    version_dx: int = 0
    version_dy: int = 0

    action_x: int = 0
    action_y: int = 0
    action_font_size: int = 0
    action_icon_text: str = ""

    edit_x: int = 0
    edit_y: int = 0
    edit_font_size: int = 0

    saved_x: int = 0
    saved_y: int = 0
    saved_font_size: int = 0

    load_x: int = 0
    load_y: int = 0
    load_font_size: int = 0

    save_offset_x: int = 0
    save_offset_y: int = 0
    save_width: int = 0
    save_height: int = 0
    save_font_size: int = 0

    @classmethod
    def _field_names(cls) -> set[str]:
        """Zwraca komplet pól używanych przez wersję LIGHT."""
        return set(cls.__dataclass_fields__.keys())

    @classmethod
    def code_values(cls) -> dict[str, Any]:
        """Jedyne źródło pozycji i rozmiarów ikon TAKE."""
        return {
            "protocol_title_y": 70,
            "protocol_height": 180,
            "row_center_y": 6,
            "protocol_inner_pad_x": 12,
            "row_pad_x": 0,
            "icon_width": 167,
            "icon_height": 168,
            "number_x": 62,
            "number_y": 87,
            "number_font_size": 73,
            "number_digits": 1,
            "number_dx": 7,
            "number_dy": 0,
            "version_x": 122,
            "version_y": 70,
            "version_font_size": 28,
            "version_dx": 0,
            "version_dy": 0,
            "action_x": 106,
            "action_y": 65,
            "action_font_size": 30,
            "action_icon_text": "✋️",
            "edit_x": 26,
            "edit_y": 129,
            "edit_font_size": 11,
            "saved_x": 63,
            "saved_y": 129,
            "saved_font_size": 11,
            "load_x": 112,
            "load_y": 129,
            "load_font_size": 11,
            "save_offset_x": 3,
            "save_offset_y": -35,
            "save_width": 130,
            "save_height": 28,
            "save_font_size": 16,
        }

    @classmethod
    def from_code(cls) -> "UiSettings":
        """Buduje ustawienia TAKE wyłącznie z wartości zapisanych w kodzie."""
        values = cls.code_values()
        payload: dict[str, Any] = {}
        for name in cls._field_names():
            payload[name] = values[name]
        ui = cls(**payload)
        ui.clamp()
        return ui

    def clamp(self) -> None:
        """Ogranicza wartości do bezpiecznych zakresów."""
        def ci(name: str, lo: int, hi: int) -> None:
            setattr(self, name, max(lo, min(hi, int(getattr(self, name)))))

        ci("protocol_title_y", 10, 200)
        ci("protocol_height", 160, 520)
        ci("row_center_y", -20, 360)
        ci("protocol_inner_pad_x", 0, 80)
        ci("row_pad_x", 0, 40)

        ci("icon_width", 96, 320)
        ci("icon_height", 96, 320)

        ci("number_x", 0, 300)
        ci("number_y", 0, 300)
        ci("number_font_size", 8, 180)
        ci("number_digits", 1, 6)
        ci("number_dx", -100, 100)
        ci("number_dy", -100, 100)

        ci("version_x", 0, 300)
        ci("version_y", 0, 300)
        ci("version_font_size", 8, 80)
        ci("version_dx", -100, 100)
        ci("version_dy", -100, 100)

        ci("action_x", -20, 250)
        ci("action_y", -20, 250)
        ci("action_font_size", 8, 80)
        self.action_icon_text = str(self.action_icon_text or "✋️")

        ci("edit_x", 0, 260)
        ci("edit_y", 0, 260)
        ci("edit_font_size", 6, 40)

        ci("saved_x", 0, 260)
        ci("saved_y", 0, 260)
        ci("saved_font_size", 6, 40)

        ci("load_x", 0, 260)
        ci("load_y", 0, 260)
        ci("load_font_size", 6, 40)

        ci("save_offset_x", -160, 160)
        ci("save_offset_y", -160, 160)
        ci("save_width", 40, 320)
        ci("save_height", 18, 100)
        ci("save_font_size", 8, 44)


# --- DANE SLOTÓW ---

@dataclass
class SlotRecord:
    """Rekord w JSON pamięci slotów."""
    path: Optional[str] = None


@dataclass
class SlotStore:
    """Model pamięci slotów (przypięte pliki, aktywny slot, aktywność osi)."""
    slots: list[SlotRecord]
    active_slot: Optional[int] = None
    axis_activity: dict[str, bool] = None

    def __post_init__(self):
        if self.axis_activity is None:
            self.axis_activity = {}

    @classmethod
    def default(cls) -> "SlotStore":
        """Tworzy pusty stan 10 slotów i domyślną aktywność osi."""
        return cls(
            slots=[SlotRecord() for _ in range(SLOT_COUNT)],
            active_slot=None,
            axis_activity={ax.axis_name: True for ax in DEFAULT_AXIS_DEFINITIONS}
        )

    @classmethod
    def load_or_default(cls, path: Path) -> "SlotStore":
        """
        Wczytuje pamięć slotów z JSON.

        Przy błędzie odczytu zwracany jest pusty stan,
        aby moduł testowy mógł dalej działać.
        """
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw_slots = raw.get("slots") or []
            slots: list[SlotRecord] = []
            for i in range(SLOT_COUNT):
                item = raw_slots[i] if i < len(raw_slots) and isinstance(raw_slots[i], dict) else {}
                slots.append(SlotRecord(path=item.get("path")))
            active_slot = raw.get("active_slot")
            if active_slot is not None:
                active_slot = int(active_slot)
                if not (0 <= active_slot < SLOT_COUNT):
                    active_slot = None
            
            # Wczytywanie aktywności osi
            axis_activity = {ax.axis_name: True for ax in DEFAULT_AXIS_DEFINITIONS}
            raw_activity = raw.get("axis_activity")
            if isinstance(raw_activity, dict):
                for name, state in raw_activity.items():
                    if name in axis_activity:
                        axis_activity[name] = bool(state)

            return cls(slots=slots, active_slot=active_slot, axis_activity=axis_activity)
        except Exception:
            return cls.default()

    def save(self, path: Path) -> None:
        """
        Zapisuje pamięć slotów do JSON.

        Ta metoda nie zapisuje danych TAKE.
        Zapisuje tylko stan przypięcia slotów oraz aktywny slot UI.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "slots": [asdict(slot) for slot in self.slots],
            "active_slot": self.active_slot,
            "axis_activity": self.axis_activity
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class SlotState:
    """
    Jawne stany slotu TAKE.

    Kontrakt stanów pozostaje zgodny z ustaleniami:
    - EMPTY
    - LINKED / LOADED
    - ACTIVE
    - SAVED jest reprezentowany jako ACTIVE + is_saved=True
    """
    EMPTY = "empty"
    LINKED = "linked"
    ACTIVE = "active"


@dataclass
class SlotVM:
    """
    Lekki model widoku pojedynczego slotu.

    To jest model stricte UI:
    - gdzie jest plik,
    - jaki numer TAKE ma być pokazany,
    - jaki jest stan widoku,
    - czy aktywny TAKE jest zapisany,
    - czy aktywny TAKE jest załadowany.
    """
    index: int
    file_path: Optional[Path] = None
    take_number: str = ""
    take_version: str = ""
    state: str = SlotState.EMPTY
    is_saved: bool = False
    is_loaded: bool = False

    def rel_path(self) -> Optional[str]:
        """
        Zwraca ścieżkę względną względem katalogu projektu.

        Dzięki temu pamięć slotów pozostaje przenaszalna w obrębie repo.
        """
        if self.file_path is None:
            return None
        try:
            return str(self.file_path.resolve().relative_to(PROJECT_DIR.resolve())).replace("\\", "/")
        except Exception:
            return str(self.file_path).replace("\\", "/")


# ======================================================================================
# HELPERY
# ======================================================================================

def ensure_dirs() -> None:
    """Zapewnia istnienie katalogów danych używanych przez moduł."""
    TAKE_DIR.mkdir(parents=True, exist_ok=True)
    EHR_DIR.mkdir(parents=True, exist_ok=True)


def take_path_from_record(path_value: Optional[str]) -> Optional[Path]:
    """
    Zamienia ścieżkę zapisaną w pamięci slotów na istniejący obiekt Path.

    Obsługuje ścieżki absolutne i względne względem repo.
    """
    if not path_value:
        return None
    p = Path(path_value)
    if p.is_absolute():
        return p if p.exists() else None
    candidate = (PROJECT_DIR / p).resolve()
    return candidate if candidate.exists() else None


def extract_number_from_take_id(take_id: str) -> Optional[str]:
    """Wyciąga numer TAKE z pola metadata.take_id."""
    match = re.search(r"(\d+)", str(take_id or ""))
    return match.group(1) if match else None


def extract_number_from_filename(path: Path) -> Optional[str]:
    """Wyciąga numer TAKE z nazwy pliku, gdy metadata nie jest dostępne."""
    match = re.search(r"TAKE[_\- ]?(\d+)", path.name, flags=re.IGNORECASE)
    if not match:
        match = re.search(r"(\d+)", path.stem)
    return match.group(1) if match else None



def extract_version_from_filename(path: Path) -> str:
    """Wyciąga wersję zapisu z nazwy pliku, np. _v02.json -> 02."""
    name = path.stem
    match = re.search(r"(?:^|[_\- ])v(\d+)(?:$|[_\- ])", name, flags=re.IGNORECASE)
    if not match:
        return ""
    return match.group(1).zfill(2)


def read_take_number(path: Path, digits: int) -> str:
    """
    Odczytuje numer TAKE wyłącznie z nazwy pliku.
    Architektura bazuje tylko na nazwach typu TAKE_001_v01.txt.
    """
    number = extract_number_from_filename(path)
    return number.zfill(digits) if number else "---"



def read_take_version(path: Path) -> str:
    """Odczytuje wersję zapisu wyłącznie z nazwy pliku TAKE."""
    return extract_version_from_filename(path)


def copy_take_into_project(src: Path) -> Path:
    """
    Nie kopiujemy i nie importujemy plików.
    Architektura opiera się wyłącznie na istniejących plikach TAKE TXT.
    """
    return src.resolve()


def _existing(paths: list[Path]) -> Optional[Path]:
    """Zwraca pierwszą istniejącą ścieżkę z listy kandydatów."""
    for path in paths:
        if path.exists():
            return path
    return None


def project_take_icon_path(state: str, size: int) -> Optional[Path]:
    """
    Szuka ikony TAKE dla danego stanu.
    Najpierw próbuje skorzystać z helpera projektu, a potem z katalogu img/take.
    """
    candidates: list[Path] = []
    
    # 1. Próba z helperem projektu dla dokładnego rozmiaru
    if project_take_icon is not None:
        try:
            p = Path(project_take_icon(size=size, state=state))
            if p.exists(): candidates.append(p)
        except Exception:
            pass

    # 2. Standardowe rozmiary w projekcie
    std_sizes = [320, 256, 128, 64]
    for s in std_sizes:
        for ext in ["png", "ico"]:
            candidates.append(IMG_TAKE_DIR / f"take_{state}_{s}.{ext}")
            # Fallback do 'closed' jeśli inny stan nie istnieje
            if state != "closed":
                candidates.append(IMG_TAKE_DIR / f"take_closed_{s}.{ext}")
        if project_take_icon is not None:
            try:
                candidates.append(Path(project_take_icon(size=s, state=state)))
            except Exception: pass

    return _existing(candidates)


def chalk_font_candidates(size: int) -> list[Any]:
    """
    Zwraca listę kandydatów na font kredowy do numeru TAKE.

    Priorytetem pozostaje font projektu z katalogu font.
    """
    fonts = []
    for path in [FONT_DIR / "Pattifont.ttf", SANDBOX_FONT_PATH]:
        if path.exists():
            try:
                fonts.append(ImageFont.truetype(str(path), size=size))
            except Exception:
                pass
    for name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]:
        try:
            fonts.append(ImageFont.truetype(name, size=size))
        except Exception:
            pass
    try:
        fonts.append(ImageFont.load_default())
    except Exception:
        pass
    return fonts


def normal_font_candidates(size: int) -> list[Any]:
    """Zwraca listę zwykłych fontów do mini etykiet UI."""
    fonts = []
    for name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Verdana.ttf"]:
        try:
            fonts.append(ImageFont.truetype(name, size=size))
        except Exception:
            pass
    try:
        fonts.append(ImageFont.load_default())
    except Exception:
        pass
    return fonts


def fit_font(text: str, max_w: int, max_h: int, preferred: int, chalk: bool) -> Any:
    """
    Dobiera możliwie największy font mieszczący się w zadanym obszarze.

    Używane przy numerze TAKE oraz małych etykietach.
    """
    font_loader = chalk_font_candidates if chalk else normal_font_candidates
    for size in range(preferred, 7, -2):
        for font in font_loader(size):
            probe = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
            draw = ImageDraw.Draw(probe)
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
            except Exception:
                continue
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if width <= max_w and height <= max_h:
                return font
    fonts = font_loader(max(8, preferred // 2))
    return fonts[0] if fonts else None


# --- RENDERER IKON ---

class IconRenderer:
    """Renderer ikon slotów TAKE z cache."""

    def __init__(self, ui: UiSettings) -> None:

        # TARZAN_SNAJPER_EHR_SECTION_INIT_CORE

        self.tarzan_snajper = create_default_tarzan_snajper()

        self.snajper_canvas_adapter = TkCanvasSnajperAdapter()

        self.snajper_tk_adapter = TkWidgetSnajperAdapter()

        self.tarzan_snajper.register_adapter("ehr_canvas", self.snajper_canvas_adapter)

        self.tarzan_snajper.register_adapter("ehr_tkinter", self.snajper_tk_adapter)
        self.ui = ui
        self.base_cache: dict[tuple[str, int, int], Image.Image | None] = {}
        self.photo_cache: dict[tuple[Any, ...], Any] = {}

    def _load_base_icon(self, state: str) -> Image.Image:
        """Ładuje bazową ikonę dla stanu i rozmiaru (PIL Image)."""
        key = (state, self.ui.icon_width, self.ui.icon_height)
        if key in self.base_cache and self.base_cache[key] is not None:
            return self.base_cache[key].copy()  # type: ignore[return-value]

        source_path = project_take_icon_path(state, max(self.ui.icon_width, self.ui.icon_height))
        if source_path and source_path.exists():
            try:
                # print(f"DEBUG: Ładowanie ikony TAKE ze ścieżki: {source_path}")
                img = Image.open(source_path).convert("RGBA").resize(
                    (self.ui.icon_width, self.ui.icon_height),
                    Image.LANCZOS,
                )
            except Exception as e:
                print(f"ERROR: Błąd ładowania ikony TAKE {source_path}: {e}")
                img = None
        else:
            if source_path:
                print(f"ERROR: Ikona TAKE nie istnieje pod ścieżką: {source_path}")
            else:
                print(f"ERROR: Nie znaleziono żadnej ikony TAKE dla stanu: {state}")
            img = None

        if img is None:
            img = Image.new("RGBA", (self.ui.icon_width, self.ui.icon_height), (20, 20, 25, 255))
            draw = ImageDraw.Draw(img)
            # Rysuj ramkę zastępczą, aby było widać że coś tam jest
            draw.rectangle((0, 0, self.ui.icon_width-1, self.ui.icon_height-1), outline=(100, 100, 120, 255), width=2)
            msg = state.upper()
            try:
                fnt = fit_font(msg, self.ui.icon_width-10, 30, 20, False)
                if fnt: draw.text((10, 10), msg, font=fnt, fill=(150, 150, 170, 255))
            except Exception: pass
            
            if state == "active":
                draw.rectangle((0, 0, self.ui.icon_width - 1, 30), fill=(212, 59, 59, 255))
            elif state == "save":
                draw.rectangle((0, 0, self.ui.icon_width - 1, 30), fill=(79, 140, 98, 255))
            draw.line(
                (20, self.ui.icon_height - 30, self.ui.icon_width - 20, self.ui.icon_height - 30),
                fill=(230, 230, 230, 255),
                width=2,
            )

        self.base_cache[key] = img
        return img.copy()

    def build_slot_photo(self, vm: SlotVM) -> Any:
        """Buduje finalną bitmapę slotu (z cache)."""
        cache_key = (
            vm.state,
            vm.take_number,
            vm.take_version,
            vm.is_saved,
            vm.is_loaded,
            self.ui.icon_width,
            self.ui.icon_height,
            self.ui.number_x,
            self.ui.number_y,
            self.ui.number_font_size,
            self.ui.number_digits,
            self.ui.number_dx,
            self.ui.number_dy,
            self.ui.edit_x,
            self.ui.edit_y,
            self.ui.edit_font_size,
            self.ui.saved_x,
            self.ui.saved_y,
            self.ui.saved_font_size,
            self.ui.load_x,
            self.ui.load_y,
            self.ui.load_font_size,
        )
        if cache_key in self.photo_cache:
            return self.photo_cache[cache_key]

        base_state = "closed" if vm.state in (SlotState.EMPTY, SlotState.LINKED) else ("save" if vm.is_saved else "active")
        img = self._load_base_icon(base_state)
        draw = ImageDraw.Draw(img)

        if vm.state != SlotState.EMPTY and vm.take_number:
            text = vm.take_number.zfill(self.ui.number_digits)
            font = fit_font(
                text=text,
                max_w=int(self.ui.icon_width * 0.72),
                max_h=int(self.ui.icon_height * 0.32),
                preferred=self.ui.number_font_size,
                chalk=True,
            )
            if font is not None:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = int(self.ui.number_x - text_width / 2 + self.ui.number_dx)
                y = int(self.ui.number_y - text_height / 2 + self.ui.number_dy)
                for dx, dy in [(0, 0), (1, 0), (0, 1)]:
                    draw.text((x + dx, y + dy), text, font=font, fill=(245, 245, 245, 255))

                if vm.take_version:
                    version_font = fit_font(
                        text=vm.take_version,
                        max_w=int(self.ui.icon_width * 0.22),
                        max_h=int(self.ui.icon_height * 0.18),
                        preferred=self.ui.version_font_size,
                        chalk=True,
                    )
                    if version_font is not None:
                        vbbox = draw.textbbox((0, 0), vm.take_version, font=version_font)
                        vx = int(self.ui.version_x + self.ui.version_dx)
                        vy = int(self.ui.version_y + self.ui.version_dy)
                        for dx, dy in [(0, 0), (1, 0), (0, 1)]:
                            draw.text((vx + dx, vy + dy), vm.take_version, font=version_font, fill=(245, 245, 245, 255))

        if vm.state == SlotState.ACTIVE:
            edit_font = fit_font("EDIT", 90, 20, self.ui.edit_font_size, chalk=False)
            saved_font = fit_font("SAVED", 90, 20, self.ui.saved_font_size, chalk=False)
            load_font = fit_font("LOAD", 90, 20, self.ui.load_font_size, chalk=False)

            if edit_font is not None:
                draw.text((self.ui.edit_x, self.ui.edit_y), "EDIT", font=edit_font, fill=(240, 240, 240, 255))
            if vm.is_saved and saved_font is not None:
                draw.text((self.ui.saved_x, self.ui.saved_y), "SAVED", font=saved_font, fill=(95, 255, 95, 255))
            if vm.is_loaded and load_font is not None:
                draw.text((self.ui.load_x, self.ui.load_y), "LOAD", font=load_font, fill=(85, 170, 255, 255))

        photo = ImageTk.PhotoImage(img)
        self.photo_cache[cache_key] = photo
        return photo

    def clear_runtime_cache(self) -> None:
        """Czyści cache renderer."""
        self.base_cache.clear()
        self.photo_cache.clear()


# --- WIDGET SLOTU ---

class SlotWidget(tk.Frame):
    """Widget pojedynczego slotu TAKE (hover, klik, ikona, SAVE)."""

    def __init__(self, master: tk.Misc, owner: "TarzanTakeProtocolLightWidget", vm: SlotVM) -> None:
        super().__init__(master, bg=owner.protocol_bg(), highlightthickness=0, bd=0)
        self.owner = owner
        self.vm = vm
        self.hovered = False

        self.slot_photo_ref = None
        self.icon_hitbox: Optional[tuple[int, int, int, int]] = None
        self.action_hitbox: Optional[tuple[int, int, int, int]] = None
        self.save_button: Optional[tk.Button] = None
        self.save_button_window: Optional[int] = None

        self.canvas = tk.Canvas(
            self,
            width=owner.ui.icon_width,
            height=owner.ui.icon_height,
            bg=owner.protocol_bg(),
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.canvas.pack()

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)

        self.redraw()

    def redraw(self) -> None:
        """Renderuje tylko ten jeden slot."""
        self.configure(bg=self.owner.protocol_bg())
        self.canvas.configure(
            bg=self.owner.protocol_bg(),
            width=self.owner.ui.icon_width,
            height=self.owner.ui.icon_height,
        )
        self.canvas.delete("all")
        self.action_hitbox = None
        self.save_button = None
        self.save_button_window = None

        top_y = 0

        self.slot_photo_ref = self.owner.renderer.build_slot_photo(self.vm)
        self.canvas.create_image(self.owner.ui.icon_width / 2, top_y + self.owner.ui.icon_height / 2, image=self.slot_photo_ref)
        self.icon_hitbox = (0, top_y, self.owner.ui.icon_width, top_y + self.owner.ui.icon_height)

        save_visible = self.vm.state == SlotState.ACTIVE and not self.vm.is_saved
        show_hand = self.hovered and self.vm.state == SlotState.LINKED and not save_visible

        if save_visible:
            self._draw_save_button(top_y)
        if show_hand:
            self._draw_action(top_y)

    def _draw_action(self, top_y: int) -> None:
        """Rysuje łapkę akcji (widoczna tylko dla LINKED na hover)."""
        x = self.owner.ui.action_x
        y = top_y + self.owner.ui.action_y
        item = self.canvas.create_text(
            x,
            y,
            text=self.owner.ui.action_icon_text,
            anchor="nw",
            fill="#F04343",
            font=("Segoe UI Emoji", self.owner.ui.action_font_size),
        )
        self.action_hitbox = self.canvas.bbox(item)

    def _draw_save_button(self, top_y: int) -> None:
        """Rysuje przycisk SAVE nad ikoną."""
        ui = self.owner.ui
        x = int((ui.icon_width - ui.save_width) / 2 + ui.save_offset_x)
        y = int(max(0, top_y - ui.save_offset_y - ui.save_height))
        # Skoryguj pozycję przycisku SAVE jeśli top_y jest ujemne
        if top_y < 0:
            y = max(0, y + top_y)

        self.save_button = tk.Button(
            self.canvas,
            text="SAVE",
            command=lambda idx=self.vm.index: self.owner.on_save_clicked(idx),
            bg=BTN_GREEN,
            fg=SAVE_GREEN_FG,
            activebackground=BTN_GREEN_ACTIVE,
            activeforeground=SAVE_GREEN_FG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=8,
            pady=0,
            font=("Segoe UI Semibold", self.owner.ui.save_font_size),
            cursor="hand2",
        )
        self.save_button_window = self.canvas.create_window(
            x,
            y,
            window=self.save_button,
            anchor="nw",
            width=ui.save_width,
            height=ui.save_height,
        )

    @staticmethod
    def _inside(x: int, y: int, rect: Optional[tuple[int, int, int, int]]) -> bool:
        """Sprawdza, czy punkt znajduje się w prostokącie hitbox."""
        if rect is None:
            return False
        left, top, right, bottom = rect
        return left <= x <= right and top <= y <= bottom

    def _on_motion(self, event: tk.Event) -> None:
        """
        Obsługuje hover lokalnie dla slotu.

        Redraw wykonywany jest tylko wtedy, gdy rzeczywiście zmienia się stan hover.
        """
        inside = self._inside(event.x, event.y, self.icon_hitbox)
        if inside != self.hovered:
            self.hovered = inside
            self.redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        """Kasuje hover lokalnie po opuszczeniu slotu."""
        if self.hovered:
            self.hovered = False
            self.redraw()

    def _on_click(self, event: tk.Event) -> None:
        """
        Rozdziela kliknięcia slotu:
        - łapka -> aktywacja,
        - ikona -> wybór / podmiana pliku,
        - ACTIVE ignoruje zwykły klik w ikonę.
        """
        if self._inside(event.x, event.y, self.action_hitbox):
            self.owner.on_action_clicked(self.vm.index)
            return

        if self.vm.state == SlotState.ACTIVE:
            return

        if self._inside(event.x, event.y, self.icon_hitbox):
            self.owner.on_slot_clicked(self.vm.index)

    def set_vm(self, vm: SlotVM) -> None:
        """
        Podmienia model widoku i lokalnie odświeża widget.

        To jest podstawowa ścieżka lokalnego refresh bez przebudowy całego rzędu.
        """
        self.vm = vm
        self.redraw()


# --- GŁÓWNY WIDGET LIGHT ---

class TarzanTakeProtocolLightWidget(tk.Frame):
    """Widget TAKE PROTOCOL do wpięcia w EHR."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        status_sink: Optional[Callable[[str], None]] = None,
        save_callback: Optional[Callable[[int, Optional[Path]], Optional[Path]]] = None,
        load_callback: Optional[Callable[[Path], None]] = None,
    ) -> None:
        """Inicjalizuje widget TAKE PROTOCOL LIGHT."""
        super().__init__(master, bg=WINDOW_BG, highlightthickness=0, bd=0)
        ensure_dirs()

        self.external_status_sink = status_sink
        self.external_save_callback = save_callback
        self.external_load_callback = load_callback
        self.external_save_callback = save_callback
        self.external_load_callback = load_callback
        self.store = SlotStore.load_or_default(SLOTS_JSON_PATH)
        self.ui = UiSettings.from_code()
        self.renderer = IconRenderer(self.ui)

        self.status_var = tk.StringVar(value="Gotowy.")
        self.slot_widgets: list[SlotWidget] = []

        self.protocol_title_id: Optional[int] = None
        self.row_window: Optional[int] = None

        self.slot_models = self._build_models()
        self._build_ui()
        self._build_slot_row()
        self._layout_protocol()

    def protocol_bg(self) -> str:
        """Zwraca kolor tła wewnętrznego pasa TAKE."""
        return PROTOCOL_INNER_BG

    def _set_status(self, text: str) -> None:
        """Ustawia komunikat statusu lokalnie i opcjonalnie emituje na zewnątrz."""
        self.status_var.set(text)
        if self.external_status_sink is not None:
            try:
                self.external_status_sink(text)
            except Exception:
                pass

    def _build_models(self) -> list[SlotVM]:
        """Buduje modele widoku slotów (EMPTY, LINKED, ACTIVE)."""
        out: list[SlotVM] = []
        for index in range(SLOT_COUNT):
            vm = SlotVM(index=index)
            record = self.store.slots[index]
            path = take_path_from_record(record.path)
            if path is not None:
                vm.file_path = path
                vm.take_number = read_take_number(path, self.ui.number_digits)
                vm.take_version = read_take_version(path)
                vm.state = SlotState.LINKED
            out.append(vm)

        if self.store.active_slot is not None and 0 <= self.store.active_slot < SLOT_COUNT:
            vm = out[self.store.active_slot]
            if vm.file_path is not None:
                vm.state = SlotState.ACTIVE
                vm.is_loaded = True

        return out

    def _build_ui(self) -> None:
        """
        Buduje zwartą wersję widgetu osadzaną bezpośrednio w EHR.

        Bez:
        - lokalnego nagłówka,
        - lokalnego status bara,
        - górnego marginesu.
        """
        self.protocol_holder = tk.Frame(self, bg=PROTOCOL_OUTER_BG, height=self.ui.protocol_height)
        self.protocol_holder.pack(fill="x", side="top")
        self.protocol_holder.pack_propagate(False)

        self.protocol_canvas = tk.Canvas(
            self.protocol_holder,
            bg=PROTOCOL_OUTER_BG,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.protocol_canvas.pack(fill="both", expand=True)
        self.protocol_canvas.bind("<Configure>", lambda _event: self._layout_protocol())

        self.protocol_title_id = None
        self.row_frame = tk.Frame(self.protocol_canvas, bg=self.protocol_bg())
        self.row_window = self.protocol_canvas.create_window(0, 0, window=self.row_frame, anchor="n")

    def _build_slot_row(self) -> None:
        """Buduje rząd 10 slotów (raz podczas inicjalizacji)."""
        for index in range(SLOT_COUNT):
            widget = SlotWidget(self.row_frame, self, self.slot_models[index])
            widget.pack(side="left", padx=self.ui.row_pad_x, pady=0)
            self.slot_widgets.append(widget)

    def _save_slots_json(self) -> None:
        """Zapisuje aktualny stan UI do pamięci JSON."""
        store = SlotStore.default()
        store.slots = []
        store.active_slot = None

        for vm in self.slot_models:
            store.slots.append(SlotRecord(path=vm.rel_path()))

        for vm in self.slot_models:
            if vm.state == SlotState.ACTIVE:
                store.active_slot = vm.index
                break

        store.save(SLOTS_JSON_PATH)

    def _refresh_slot(self, index: int) -> None:
        """Lokalnie odświeża tylko jeden slot."""
        if 0 <= index < len(self.slot_widgets):
            self.slot_widgets[index].set_vm(self.slot_models[index])

    def _refresh_slots(self, indices: list[int]) -> None:
        """Lokalnie odświeża kilka konkretnych slotów."""
        for index in indices:
            self._refresh_slot(index)

    def _layout_protocol(self) -> None:
        """Przelicza geometrię pasa TAKE."""
        width = max(900, int(self.protocol_canvas.winfo_width() or 1200))
        height = max(180, int(self.protocol_canvas.winfo_height() or self.ui.protocol_height))
        inner = self.ui.protocol_inner_pad_x

        self.protocol_canvas.delete("band_bg")
        self.protocol_canvas.create_rectangle(0, 0, width, height, fill=PROTOCOL_OUTER_BG, outline="", tags="band_bg")
        self.protocol_canvas.create_rectangle(inner, 0, width - inner, height, fill=PROTOCOL_INNER_BG, outline="", tags="band_bg")
        self.protocol_canvas.tag_lower("band_bg")

        if self.row_window is not None:
            self.protocol_canvas.coords(self.row_window, width / 2, self.ui.row_center_y)

    def on_slot_clicked(self, index: int) -> None:
        """Obsługuje klik w slot (wybór pliku)."""
        vm = self.slot_models[index]
        if vm.state == SlotState.ACTIVE:
            return

        if not TAKE_DATA_DIR.exists():
            TAKE_DATA_DIR.mkdir(parents=True, exist_ok=True)

        path = filedialog.askopenfilename(
            title="Wybierz plik TAKE",
            initialdir=str(TAKE_DATA_DIR),
            filetypes=[("TAKE TXT", "*.txt"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            dst = copy_take_into_project(Path(path))
        except Exception as exc:
            self._set_status(f"Błąd importu TAKE: {exc}")
            return

        vm.file_path = dst
        vm.take_number = read_take_number(dst, self.ui.number_digits)
        vm.take_version = read_take_version(dst)
        vm.state = SlotState.LINKED
        vm.is_saved = False
        vm.is_loaded = False

        self._save_slots_json()
        self._refresh_slot(index)
        self._set_status(f"TAKE {vm.take_number} podpięty.")

    def on_action_clicked(self, index: int) -> None:
        """Obsługuje klik w łapkę aktywacji."""
        vm = self.slot_models[index]
        if vm.state != SlotState.LINKED:
            return

        old_active = None
        for other in self.slot_models:
            if other.state == SlotState.ACTIVE:
                old_active = other.index
                other.state = SlotState.LINKED
                other.is_loaded = False
                other.is_saved = False
                break

        vm.state = SlotState.ACTIVE
        vm.is_loaded = True
        vm.is_saved = False

        self._save_slots_json()

        changed = [index]
        if old_active is not None:
            changed.append(old_active)

        if self.external_load_callback is not None and vm.file_path is not None:
            try:
                self.external_load_callback(vm.file_path)
            except Exception as exc:
                vm.state = SlotState.LINKED
                vm.is_loaded = False
                vm.is_saved = False
                self._refresh_slots(changed)
                self._set_status(f"Błąd LOAD TAKE: {exc}")
                return

        self._refresh_slots(changed)
        self._set_status(f"TAKE {vm.take_number} aktywowany. LOAD=ON.")

    def on_save_clicked(self, index: int) -> None:
        """Obsługuje SAVE aktywnego TAKE (symulacja stanu)."""
        vm = self.slot_models[index]
        if vm.state != SlotState.ACTIVE:
            return

        if self.external_save_callback is not None:
            try:
                new_path = self.external_save_callback(index, vm.file_path)
                if new_path is not None:
                    vm.file_path = Path(new_path)
                    vm.take_number = read_take_number(vm.file_path, self.ui.number_digits)
                    vm.take_version = read_take_version(vm.file_path)
            except Exception as exc:
                self._set_status(f"Błąd SAVE TAKE: {exc}")
                return

        vm.is_saved = True
        self._save_slots_json()
        self._refresh_slot(index)
        self._set_status(f"TAKE {vm.take_number} zapisany. SAVED=ON.")

    def notify_active_take_modified(self) -> None:
        """Publiczne API do powiadamiania o modyfikacji danych TAKE."""
        for index, vm in enumerate(self.slot_models):
            if vm.state == SlotState.ACTIVE:
                vm.is_saved = False
                vm.is_loaded = True
                self._refresh_slot(index)
                self._set_status(f"TAKE {vm.take_number} zmieniony. SAVE ponownie wymagany.")
                break

    def force_reload_slots_from_json(self) -> None:
        """Przeładowuje dane slotów z JSON i odświeża widok (bez pełnej przebudowy layoutu)."""
        self.store = SlotStore.load_or_default(SLOTS_JSON_PATH)
        self.slot_models = self._build_models()
        for index, widget in enumerate(self.slot_widgets):
            widget.set_vm(self.slot_models[index])
        self._set_status("Lista TAKE została odświeżona.")

    def force_reload_layout_from_code(self) -> None:
        """Przeładowuje layout z wartości zapisanych w kodzie i przebudowuje widok."""
        self.ui = UiSettings.from_code()
        self.renderer = IconRenderer(self.ui)

        for vm in self.slot_models:
            if vm.file_path is not None:
                vm.take_number = read_take_number(vm.file_path, self.ui.number_digits)
                vm.take_version = read_take_version(vm.file_path)

        self.protocol_holder.configure(height=self.ui.protocol_height)

        for widget in self.slot_widgets:
            widget.destroy()
        self.slot_widgets.clear()

        self.row_frame.destroy()
        self.row_frame = tk.Frame(self.protocol_canvas, bg=self.protocol_bg())
        self.row_window = self.protocol_canvas.create_window(0, 0, window=self.row_frame, anchor="n")
        self._build_slot_row()
        self._layout_protocol()
        self._set_status("Przeładowano layout TAKE PROTOCOL z kodu.")


# ======================================================================================
# UI TAKE PROTOCOL LIGHT — koniec sekcji widgetu osadzanego w EHR
# WAŻNE: bez standalone okna testowego i bez lokalnego main() TAKE.
# Start programu pozostaje tylko na końcu pliku: TarzanEhrMultiAxisWindow.

# ======================================================================================
# OKNO: USTAWIENIA MAIN TAKE
# ======================================================================================
# Tu zaczyna się okno głównych ustawień EHR / MAIN TAKE.
# Model ustawień pozostaje w tarzanEhrMainTakeSettings.py.

class MainTakeSettingsDialog(tk.Toplevel):
    def __init__(self, master, settings: MainTakeSettings, save_callback, apply_callback) -> None:
        super().__init__(master)
        self.master_window = master
        self.settings = settings
        self.save_callback = save_callback
        self.apply_callback = apply_callback

        self.title("Ustawienia MAIN TAKE")
        self.configure(bg=master.BG)
        self.transient(master)
        self.grab_set()
        self.geometry("760x980")
        self.minsize(680, 900)

        self.minutes_var = tk.DoubleVar(value=settings.take_duration_minutes)
        self.zero_line_color_var = tk.StringVar(value=settings.zero_line_color)
        self.zero_line_width_var = tk.IntVar(value=settings.zero_line_width)
        self.curve_line_width_var = tk.IntVar(value=settings.curve_line_width)
        self.active_curve_line_width_var = tk.IntVar(value=settings.active_curve_line_width)
        self.snap_enabled_var = tk.BooleanVar(value=settings.snap_to_zero_enabled)
        self.snap_threshold_var = tk.DoubleVar(value=settings.snap_to_zero_threshold)
        self.show_protocol_var = tk.BooleanVar(value=settings.show_protocol_preview)
        self.show_metrics_var = tk.BooleanVar(value=settings.show_axis_metrics)
        self.show_labels_var = tk.BooleanVar(value=settings.show_axis_labels)
        self.show_gears_var = tk.BooleanVar(value=settings.show_axis_gears)
        self.show_status_var = tk.BooleanVar(value=settings.show_status_bar)
        self.show_grid_var = tk.BooleanVar(value=settings.show_minute_grid)
        self.show_background_tint_var = tk.BooleanVar(value=settings.show_axis_background_tint)
        self.background_strength_var = tk.IntVar(value=settings.axis_background_strength_percent)
        self.active_axis_emphasis_var = tk.IntVar(value=getattr(settings, 'active_axis_emphasis_percent', 10))
        self.active_axis_border_width_var = tk.IntVar(value=getattr(settings, 'active_axis_border_width', 3))
        self.show_start_stop_squares_var = tk.BooleanVar(value=settings.show_start_stop_squares)
        self.show_activity_markers_var = tk.BooleanVar(value=settings.show_axis_activity_markers)
        self.smooth_strength_default_var = tk.DoubleVar(value=getattr(settings, 'smooth_strength_default', 0.35))
        self.smooth_passes_default_var = tk.IntVar(value=getattr(settings, 'smooth_passes_default', 2))
        self.show_ghost_var = tk.BooleanVar(value=getattr(settings, 'show_ghost_line', True))
        self.ghost_color_var = tk.StringVar(value=getattr(settings, 'ghost_line_color', '#EAB308'))
        self.ghost_width_var = tk.IntVar(value=getattr(settings, 'ghost_line_width', 1))
        self.ghost_dash_on_var = tk.IntVar(value=getattr(settings, 'ghost_line_dash_on', 4))
        self.ghost_dash_off_var = tk.IntVar(value=getattr(settings, 'ghost_line_dash_off', 4))
        self.ghost_assist_enabled_var = tk.BooleanVar(value=getattr(settings, 'ghost_assist_enabled', False))
        self.ghost_assist_threshold_var = tk.DoubleVar(value=getattr(settings, 'ghost_assist_threshold_y', 4.0))
        self.kro_enabled_var = tk.BooleanVar(value=getattr(settings, 'kro_enabled', True))
        self.axis_color_vars = {
            axis.axis_id: tk.StringVar(value=settings.axis_color_overrides.get(axis.axis_id, DEFAULT_AXIS_COLORS.get(axis.axis_id, axis.color)))
            for axis in DEFAULT_AXIS_DEFINITIONS
        }

        self._build_ui()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.master_window.BG)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        canvas = tk.Canvas(outer, bg=self.master_window.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        frame = tk.Frame(canvas, bg=self.master_window.PANEL, padx=16, pady=16)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        s1 = self._section_label(frame, "CZAS I LINIE GŁÓWNE")
        self._entry_row(s1, "GLOBALNY CZAS MAIN TAKE (min)", self.minutes_var, 0, 0)
        self._entry_row(s1, "KOLOR LINII 0", self.zero_line_color_var, 0, 1)
        self._entry_row(s1, "GRUBOŚĆ LINII 0", self.zero_line_width_var, 1, 0)
        self._entry_row(s1, "GRUBOŚĆ LINII OSI", self.curve_line_width_var, 1, 1)
        self._entry_row(s1, "GRUBOŚĆ AKTYWNEJ OSI", self.active_curve_line_width_var, 2, 0)

        s2 = self._section_label(frame, "PROSTOTA INTERFEJSU")
        self._check_row(s2, "PRZYCIĄGANIE DO 0", self.snap_enabled_var, 0, 0)
        self._entry_row(s2, "PRÓG PRZYCIĄGANIA DO 0", self.snap_threshold_var, 0, 1)
        self._check_row(s2, "POKAŻ PODGLĄD PROTOKOŁU", self.show_protocol_var, 1, 0)
        self._check_row(s2, "POKAŻ METRYKI OSI", self.show_metrics_var, 1, 1)
        self._check_row(s2, "POKAŻ NAZWY OSI", self.show_labels_var, 2, 0)
        self._check_row(s2, "POKAŻ KOŁA USTAWIEŃ OSI", self.show_gears_var, 2, 1)
        self._check_row(s2, "POKAŻ PASEK STATUSU", self.show_status_var, 3, 0)
        self._check_row(s2, "POKAŻ SIATKĘ MINUT", self.show_grid_var, 3, 1)

        s3 = self._section_label(frame, "PODŚWIETLANIE AKTYWNEJ OSI")
        self._check_row(s3, "POKAŻ DELIKATNE TŁO OSI W KOLORZE LINII", self.show_background_tint_var, 0, 0)
        self._entry_row(s3, "PRZEŹROCZYSTOŚĆ / SIŁA TŁA OSI (%)", self.background_strength_var, 0, 1)
        self._entry_row(s3, "DODATKOWE PODBICIE AKTYWNEJ OSI (%)", self.active_axis_emphasis_var, 1, 0)
        self._entry_row(s3, "GRUBOŚĆ LEWEGO ZNACZNIKA AKTYWNEJ OSI", self.active_axis_border_width_var, 1, 1)
        self._check_row(s3, "POKAŻ PUNKTY GRANICZNE TAKE", self.show_start_stop_squares_var, 2, 0)
        self._check_row(s3, "POKAŻ MARKERY CZASU DZIAŁANIA OSI", self.show_activity_markers_var, 2, 1)

        s4 = self._section_label(frame, "DOMYŚLNE WYGŁADZANIE")
        self._entry_row(s4, "DOMYŚLNA SIŁA WYGŁADZANIA", self.smooth_strength_default_var, 0, 0)
        self._entry_row(s4, "DOMYŚLNA ILOŚĆ PRZEJŚĆ", self.smooth_passes_default_var, 0, 1)

        s5 = self._section_label(frame, "GHOST (ZAPISANA KRZYWA)")
        self._check_row(s5, "POKAŻ GHOST", self.show_ghost_var, 0, 0)
        self._entry_row(s5, "KOLOR GHOST", self.ghost_color_var, 0, 1)
        self._entry_row(s5, "GRUBOŚĆ GHOST", self.ghost_width_var, 1, 0)
        self._entry_row(s5, "DASH ON", self.ghost_dash_on_var, 1, 1)
        self._entry_row(s5, "DASH OFF", self.ghost_dash_off_var, 2, 0)
        self._check_row(s5, "GHOST ASSIST / PRZYCIĄGANIE DO GHOST", self.ghost_assist_enabled_var, 3, 0)
        self._entry_row(s5, "PRÓG PRZYCIĄGANIA GHOST ASSIST", self.ghost_assist_threshold_var, 3, 1)

        s6 = self._section_label(frame, "KRO (KONTRAPUNKT RUCHU OSI)")
        self._check_row(s6, "WŁĄCZ SYSTEM KRO (ON/OFF)", self.kro_enabled_var, 0, 0)

        self._section_label(frame, "KOLORY POSZCZEGÓLNYCH OSI")
        color_grid = tk.Frame(frame, bg=self.master_window.PANEL)
        color_grid.pack(fill="x", pady=(0, 8))
        for row, axis in enumerate(DEFAULT_AXIS_DEFINITIONS):
            tk.Label(color_grid, text=axis.axis_name, bg=self.master_window.PANEL, fg=self.master_window.FG,
                     anchor="w", font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
            tk.Entry(color_grid, textvariable=self.axis_color_vars[axis.axis_id], bg="#39424E", fg=self.master_window.FG,
                     relief="flat", insertbackground=self.master_window.FG, width=14).grid(row=row, column=1, sticky="ew", pady=4)
            preview = tk.Canvas(color_grid, width=36, height=18, bg=self.master_window.PANEL, highlightthickness=0)
            preview.grid(row=row, column=2, padx=(8, 0), pady=4)
            self._bind_color_preview(preview, self.axis_color_vars[axis.axis_id])
        color_grid.grid_columnconfigure(1, weight=1)

        btns = tk.Frame(frame, bg=self.master_window.PANEL)
        btns.pack(fill="x", pady=(14, 0))
        tk.Button(btns, text="ZASTOSUJ", command=self._apply_only, bg="#0F766E", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="left")
        tk.Button(btns, text="ZAPISZ USTAWIENIA", command=self._save_all, bg="#2563EB", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="left", padx=6)
        tk.Button(btns, text="ZAMKNIJ", command=self.destroy, bg="#4B5563", fg="white", relief="flat", bd=0, padx=10, pady=6).pack(side="right")

    def _bind_color_preview(self, canvas: tk.Canvas, var: tk.StringVar) -> None:
        def _safe_color(value: str) -> str:
            value = (value or "").strip()
            if len(value) == 7 and value.startswith("#"):
                try:
                    int(value[1:], 16)
                    return value
                except ValueError:
                    pass
            return "#39424E"

        def draw(*_args) -> None:
            color = _safe_color(var.get())
            canvas.delete("all")
            canvas.create_rectangle(2, 2, 34, 16, fill=color, outline="#66707C")
        var.trace_add("write", draw)
        draw()

    def _section_label(self, parent, text) -> tk.Frame:
        tk.Label(parent, text=text, bg=self.master_window.PANEL, fg=self.master_window.FG,
                 anchor="w", font=("Segoe UI Semibold", 10)).pack(fill="x", pady=(8, 6))
        grid_frame = tk.Frame(parent, bg=self.master_window.PANEL)
        grid_frame.pack(fill="x")
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        return grid_frame

    def _entry_row(self, parent, label, var, row, col) -> None:
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        tk.Entry(wrap, textvariable=var, bg="#39424E", fg=self.master_window.FG, relief="flat", insertbackground=self.master_window.FG).pack(fill="x")

    def _scale_row(self, parent, label, var, from_, to, resolution, row, col) -> None:
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                 bg=self.master_window.PANEL, fg=self.master_window.FG, troughcolor="#39424E",
                 highlightthickness=0, bd=0, length=320).pack(fill="x")

    def _check_row(self, parent, label, var, row, col) -> None:
        cb = tk.Checkbutton(parent, text=label, variable=var, bg=self.master_window.PANEL, fg=self.master_window.FG,
                       activebackground=self.master_window.PANEL, activeforeground=self.master_window.FG,
                       selectcolor="#39424E", anchor="w", relief="flat")
        cb.grid(row=row, column=col, sticky="w", padx=4, pady=1)

    def _collect(self) -> MainTakeSettings:
        settings = MainTakeSettings(
            take_duration_minutes=float(self.minutes_var.get()),
            zero_line_color=self.zero_line_color_var.get().strip() or "#E03A3A",
            zero_line_width=int(self.zero_line_width_var.get()),
            curve_line_width=int(self.curve_line_width_var.get()),
            active_curve_line_width=int(self.active_curve_line_width_var.get()),
            snap_to_zero_enabled=bool(self.snap_enabled_var.get()),
            snap_to_zero_threshold=float(self.snap_threshold_var.get()),
            show_protocol_preview=bool(self.show_protocol_var.get()),
            show_axis_metrics=bool(self.show_metrics_var.get()),
            show_axis_labels=bool(self.show_labels_var.get()),
            show_axis_gears=bool(self.show_gears_var.get()),
            show_status_bar=bool(self.show_status_var.get()),
            show_minute_grid=bool(self.show_grid_var.get()),
            show_axis_background_tint=bool(self.show_background_tint_var.get()),
            axis_background_strength_percent=int(self.background_strength_var.get()),
            active_axis_emphasis_percent=int(self.active_axis_emphasis_var.get()),
            active_axis_border_width=int(self.active_axis_border_width_var.get()),
            show_start_stop_squares=bool(self.show_start_stop_squares_var.get()),
            show_axis_activity_markers=bool(self.show_activity_markers_var.get()),
            smooth_strength_default=float(self.smooth_strength_default_var.get()),
            smooth_passes_default=int(self.smooth_passes_default_var.get()),
            axis_color_overrides={axis_id: var.get().strip() or DEFAULT_AXIS_COLORS.get(axis_id, "#FFFFFF") for axis_id, var in self.axis_color_vars.items()},
            show_ghost_line=bool(self.show_ghost_var.get()),
            ghost_line_color=self.ghost_color_var.get().strip() or "#EAB308",
            ghost_line_width=int(self.ghost_width_var.get()),
            ghost_line_dash_on=int(self.ghost_dash_on_var.get()),
            ghost_line_dash_off=int(self.ghost_dash_off_var.get()),
            ghost_assist_enabled=bool(self.ghost_assist_enabled_var.get()),
            ghost_assist_threshold_y=float(self.ghost_assist_threshold_var.get()),
            kro_enabled=bool(self.kro_enabled_var.get()),
        )
        settings.clamp()
        return settings

    def _apply_only(self) -> None:
        self.apply_callback(self._collect())

    def _save_all(self) -> None:
        self.save_callback(self._collect())

# ======================================================================================
# OKNA: EHR GŁÓWNY + USTAWIENIA POJEDYNCZEJ OSI
# ======================================================================================
# Tu zaczyna się główne okno EHR oraz okno edycji pojedynczej osi.
# Modele osi i generator protokołu pozostają w tarzanEhrMultiAxisModel.py.

@dataclass
class AxisViewportRect:
    left: int
    top: int
    right: int
    bottom: int

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom


@dataclass
class GearRect:
    left: int
    top: int
    right: int
    bottom: int

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom


@dataclass
class WaveRect:
    left: int
    top: int
    right: int
    bottom: int

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom


class AxisDialogSnajperAdapter:
    """Lokalny adapter Snajpera dla okna ustawień pojedynczej osi.

    Ten adapter nie buduje nowej logiki rysowania. Tylko kieruje strzał
    Snajpera w istniejące cele AxisSettingsDialog: krzywą, STEP preview,
    metryki i status.
    """

    def __init__(self, dialog: "AxisSettingsDialog") -> None:
        self.dialog = dialog

    def update_target(self, target, value: Any) -> None:
        if target.target == "curve":
            self.dialog._draw_curve()
            self.dialog._curve_needs_redraw = False
            return

        if target.target == "step_preview":
            self.dialog._draw_step()
            self.dialog._step_needs_redraw = False
            return

        if target.target == "metrics":
            self.dialog._refresh_metrics()
            return

        if target.target == "status":
            self.dialog._set_status(str(value))
            return


class AxisSettingsDialog(tk.Toplevel):
    def __init__(self, master: "TarzanEhrMultiAxisWindow", axis_index: int) -> None:
        super().__init__(master)
        self.master_window = master
        self.axis_index = axis_index
        self.model = master.axis_models[axis_index]

        self.title(f"Ustawienia osi — {self.model.axis_def.axis_name}")
        self.minsize(1500, 920)
        try:
            self.state("zoomed")
        except tk.TclError:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.configure(bg=master.BG)
        self.resizable(True, True)

        self.display_y_scale = tk.DoubleVar(value=self.model.sandbox.display_y_scale)
        self.mouse_y_precision = tk.DoubleVar(value=1.0)
        self.top_bottom_margin = tk.IntVar(value=8)
        self.model.sandbox.mouse_y_precision = float(self.mouse_y_precision.get())
        self.model.sandbox.top_bottom_margin = int(self.top_bottom_margin.get())
        self.status_var = tk.StringVar(value="Gotowy.")
        self.metrics_var = tk.StringVar(value="")
        self.is_ghost_snapped = False
        self._ghost_samples_cache = []

        defaults = copy.deepcopy(self.model.step_tuning)
        self.step_vars = {
            "dead_zone_y": tk.DoubleVar(value=defaults.dead_zone_y),
            "input_max_y": tk.DoubleVar(value=defaults.input_max_y),
            "input_gamma": tk.DoubleVar(value=defaults.input_gamma),
            "step_rate_gain": tk.DoubleVar(value=defaults.step_rate_gain),
            "step_rate_max_percent": tk.DoubleVar(value=defaults.step_rate_max_percent),
            "preview_rate_smoothing": tk.DoubleVar(value=defaults.preview_rate_smoothing),
            # ADRR jest przechowywany technicznie jako 0.0–1.0, ale operator stroi go
            # w precyzyjnej skali 0–1000, jak dostrajanie rezonansu HARMONII RUCHU.
            "adrr_strength": tk.DoubleVar(value=self._adrr_strength_to_operator(getattr(defaults, "adrr_strength", 0.0))),
            "bucket_width_px": tk.IntVar(value=defaults.bucket_width_px),
            "off_bar_height": tk.IntVar(value=defaults.off_bar_height),
            "low_zone_gain": tk.DoubleVar(value=defaults.low_zone_gain),
            "mid_zone_gain": tk.DoubleVar(value=defaults.mid_zone_gain),
            "high_zone_gain": tk.DoubleVar(value=defaults.high_zone_gain),
            "accumulator_bias": tk.DoubleVar(value=defaults.accumulator_bias),
            "emit_threshold": tk.DoubleVar(value=defaults.emit_threshold),
            "node_hit_radius_px": tk.IntVar(value=defaults.node_hit_radius_px),
            "time_drag_threshold_samples": tk.IntVar(value=defaults.time_drag_threshold_samples),
        }

        self.selected_index: int | None = None
        self.selected_node_ref = None
        self.drag_mode: str | None = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._drag_zero_snap_locked = False
        self.drag_anchor_node_time = 0
        self.drag_anchor_node_y = 0.0
        self._drag_zero_snap_locked = False
        self._curve_needs_redraw = True
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._nodes_dirty = True
        self._curve_redraw_after_id = None
        self._step_tuning_after_id = None
        self._step_redraw_after_id = None
        self._axis_dialog_fire_seq = 0
        self._is_switching_axis = False
        self._is_live_preview = False

        self.tarzan_snajper = create_default_tarzan_snajper()
        self.axis_dialog_snajper_adapter = AxisDialogSnajperAdapter(self)
        self.tarzan_snajper.register_adapter("axis_dialog", self.axis_dialog_snajper_adapter)
        self._register_axis_dialog_snajper_targets()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self.update()
        self.tarzan_snajper.clear_scope(f"axis_dialog_{self.axis_index}")
        self._snajper_refresh_targets(curve=True, step=True, metrics=True, status="Gotowy.")

    def switch_axis(self, axis_index: int) -> None:
        """Przełącza lupę na inną oś bez ponownego otwierania okna."""
        self._is_switching_axis = True
        try:
            self.axis_index = axis_index
            self.model = self.master_window.axis_models[axis_index]
            self.title(f"Ustawienia osi — {self.model.axis_def.axis_name}")

            # Aktualizacja nagłówka i nazwy osi w UI
            if hasattr(self, "header_label"):
                self.header_label.config(text=f"TARZAN — USTAWIENIA OSI: {self.model.axis_def.axis_name.upper()}")
            if hasattr(self, "axis_name_label"):
                self.axis_name_label.config(text=self.model.axis_def.axis_name.upper())

            # Przeładuj wartości suwaków z self.model.step_tuning
            defaults = copy.deepcopy(self.model.step_tuning)
            self.step_vars["dead_zone_y"].set(defaults.dead_zone_y)
            self.step_vars["input_max_y"].set(defaults.input_max_y)
            self.step_vars["input_gamma"].set(defaults.input_gamma)
            self.step_vars["step_rate_gain"].set(defaults.step_rate_gain)
            self.step_vars["step_rate_max_percent"].set(defaults.step_rate_max_percent)
            self.step_vars["preview_rate_smoothing"].set(defaults.preview_rate_smoothing)
            self.step_vars["adrr_strength"].set(self._adrr_strength_to_operator(getattr(defaults, "adrr_strength", 0.0)))
            self.step_vars["bucket_width_px"].set(defaults.bucket_width_px)
            self.step_vars["off_bar_height"].set(defaults.off_bar_height)
            self.step_vars["low_zone_gain"].set(defaults.low_zone_gain)
            self.step_vars["mid_zone_gain"].set(defaults.mid_zone_gain)
            self.step_vars["high_zone_gain"].set(defaults.high_zone_gain)
            self.step_vars["accumulator_bias"].set(defaults.accumulator_bias)
            self.step_vars["emit_threshold"].set(defaults.emit_threshold)
            self.step_vars["node_hit_radius_px"].set(defaults.node_hit_radius_px)
            self.step_vars["time_drag_threshold_samples"].set(defaults.time_drag_threshold_samples)

            self.selected_index = None
            self.selected_node_ref = None
            self.drag_mode = None

            # Wyczyść cache lokalne metryk/step
            self._metrics_cache_key = None
            self._metrics_cache_text = ""
            self._nodes_dirty = True
            self._curve_needs_redraw = True
            self._step_needs_redraw = True

            # Odśwież przez lokalnego Snajpera
            self.tarzan_snajper.clear_scope(f"axis_dialog_{self.axis_index}")
            self._register_axis_dialog_snajper_targets()
            self._snajper_refresh_targets(curve=True, step=True, metrics=True, status=f"Przełączono na oś: {self.model.axis_def.axis_name}")
        finally:
            self._is_switching_axis = False

    def _register_axis_dialog_snajper_targets(self) -> None:
        """Rejestruje lokalne cele Snajpera dla tego konkretnego okna osi."""
        scope = f"axis_dialog_{self.axis_index}"
        self.tarzan_snajper.register_target("axis_dialog_curve", T("axis_dialog", scope, "curve", "refresh"))
        self.tarzan_snajper.register_target("axis_dialog_step_preview", T("axis_dialog", scope, "step_preview", "refresh"))
        self.tarzan_snajper.register_target("axis_dialog_metrics", T("axis_dialog", scope, "metrics", "refresh"))
        self.tarzan_snajper.register_target("axis_dialog_status", T("axis_dialog", scope, "status", "text"))

    @staticmethod
    def _adrr_operator_to_strength(value: float) -> float:
        """Mapuje operatorskie strojenie ADRR 0–1000 na techniczną siłę 0.0–1.0.

        Skala jest celowo nieliniowa: początek działa bardzo łagodnie, środek
        buduje HARMONIĘ RUCHU, a wysokie wartości wchodzą w mocne, rezonansowe
        układanie matrixa STEP.
        """
        ui_value = max(0.0, min(1000.0, float(value)))
        if ui_value <= 0.0:
            return 0.0
        return max(0.0, min(1.0, (ui_value / 1000.0) ** 1.6))

    @staticmethod
    def _adrr_strength_to_operator(strength: float) -> float:
        """Odwrotność mapowania ADRR: 0.0–1.0 -> 0–1000 dla suwaka UI."""
        normalized = max(0.0, min(1.0, float(strength)))
        if normalized <= 0.0:
            return 0.0
        return max(0.0, min(1000.0, 1000.0 * (normalized ** (1.0 / 1.6))))

    def _snajper_fire(self, logical_signal: str, value: Any | None = None) -> None:
        """Wymusza celowany strzał Snajpera w lokalny target okna osi."""
        self._axis_dialog_fire_seq += 1
        payload = self._axis_dialog_fire_seq if value is None else value
        self.tarzan_snajper.fire(logical_signal, payload)

    def _restore_selected_index_from_ref(self) -> None:
        ref = getattr(self, "selected_node_ref", None)
        if ref is None:
            return
        try:
            self.selected_index = self.model.nodes.index(ref)
        except ValueError:
            self.selected_index = None
            self.selected_node_ref = None

    def _snajper_refresh_targets(
        self,
        *,
        curve: bool = False,
        step: bool = False,
        metrics: bool = False,
        status: str | None = None,
    ) -> None:
        """Odświeża tylko wskazane cele okna pojedynczej osi."""
        if curve:
            self._snajper_fire("axis_dialog_curve")
        if step:
            self._snajper_fire("axis_dialog_step_preview")
        if metrics:
            self._snajper_fire("axis_dialog_metrics")
        if status is not None:
            self._snajper_fire("axis_dialog_status", status)

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=self.master_window.BG)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg=self.master_window.BG)
        top.pack(fill="x", pady=(0, 8))
        self.header_label = tk.Label(
            top,
            text=f"TARZAN — USTAWIENIA OSI: {self.model.axis_def.axis_name.upper()}",
            bg=self.master_window.BG,
            fg=self.master_window.FG,
            font=("Segoe UI Semibold", 16),
        )
        self.header_label.pack(side="left")

        btns = tk.Frame(top, bg=self.master_window.BG)
        btns.pack(side="right")

        self._btn(btns, "SET UP -> MAIN TAKE", self._apply_to_main_take, "#047857").pack(side="left", padx=3)
        self._btn(btns, "ZAMKNIJ", self._on_close, "#4B5563").pack(side="left", padx=3)

        body = tk.Frame(outer, bg=self.master_window.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.master_window.BG, width=210)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=self.master_window.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(left)

        self.curve_canvas = tk.Canvas(right, bg="#1B2028", width=1520, height=420, highlightthickness=0)
        self.curve_canvas.pack(fill="both", expand=True, pady=(0, 8))
        self.curve_canvas.bind("<Button-1>", self._on_curve_press)
        self.curve_canvas.bind("<B1-Motion>", self._on_curve_drag)
        self.curve_canvas.bind("<ButtonRelease-1>", self._on_curve_release)
        self.curve_canvas.bind("<Double-Button-1>", self._on_curve_double_click)
        self.curve_canvas.bind("<Button-3>", self._on_curve_right_click)

        self.step_canvas = tk.Canvas(right, bg="#1A1E24", width=1520, height=255, highlightthickness=0)
        self.step_canvas.pack(fill="both", expand=True)

        self._build_step_tuning_panel(right)

        status = tk.Label(
            outer,
            textvariable=self.status_var,
            bg=self.master_window.PANEL2,
            fg=self.master_window.FG,
            anchor="w",
            padx=10,
            pady=8,
            font=("Segoe UI", 9),
        )
        status.pack(fill="x", pady=(8, 0))

    def _build_left_panel(self, parent: tk.Misc) -> None:
        self.axis_name_label = tk.Label(parent, text=self.model.axis_def.axis_name.upper(), bg=self.master_window.BG, fg=self.master_window.FG,
                 anchor="w", font=("Segoe UI Semibold", 12))
        self.axis_name_label.pack(fill="x", pady=(0, 8))
        tk.Label(parent, textvariable=self.metrics_var, bg=self.master_window.BG, fg=self.master_window.MUTED,
                 justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x", pady=(0, 12))


    def _build_step_tuning_panel(self, parent: tk.Misc) -> None:
        panel = tk.Frame(parent, bg=self.master_window.PANEL, padx=10, pady=10)
        panel.pack(fill="x", pady=(8, 0))
        tk.Label(panel, text="STROJENIE DRUGIEGO WYKRESU / STEP PREVIEW", bg=self.master_window.PANEL,
                 fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 10)).pack(fill="x", pady=(0, 8))
        grid = tk.Frame(panel, bg=self.master_window.PANEL)
        grid.pack(fill="x")

        sliders = [
            ("dead_zone_y", "MIĘKKI START", 0.0, 30.0, 0.5),
            ("step_rate_gain", "GĘSTOŚĆ RUCHU", 0.1, 5.0, 0.05),
            ("preview_rate_smoothing", "PŁYNNOŚĆ RUCHU", 0.0, 0.95, 0.01),
            ("adrr_strength", "ADRR — HARMONIA RUCHU", 0.0, 1000.0, 1.0),
        ]
        for idx, (key, label, start, end, res) in enumerate(sliders):
            col = idx % 4
            row = idx // 4
            self._scale_row_grid(grid, row, col, label, self.step_vars[key], start, end, res, self._apply_step_tuning_live)


    def _scale_row(self, parent, label, var, from_, to, resolution, command):
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.pack(fill="x", padx=10, pady=8)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                         command=lambda _v: command(), bg=self.master_window.PANEL, fg=self.master_window.FG,
                         troughcolor="#39424E", highlightthickness=0, bd=0, length=240)
        scale.bind("<ButtonRelease-1>", lambda _: self._on_scale_release())
        scale.pack(fill="x")

    def _scale_row_grid(self, parent, row, col, label, var, from_, to, resolution, command):
        wrap = tk.Frame(parent, bg=self.master_window.PANEL)
        wrap.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(wrap, text=label, bg=self.master_window.PANEL, fg=self.master_window.FG, anchor="w",
                 font=("Segoe UI", 8, "bold")).pack(fill="x")
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                         command=lambda _v: command(), bg=self.master_window.PANEL, fg=self.master_window.FG,
                         troughcolor="#39424E", highlightthickness=0, bd=0, length=300)
        scale.bind("<ButtonRelease-1>", lambda _: self._on_scale_release())
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=10, pady=6,
                         font=("Segoe UI Semibold", 9), cursor="hand2")

    def _small_btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=8, pady=4,
                         font=("Segoe UI Semibold", 8), cursor="hand2")

    def _curve_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.curve_canvas.winfo_width() or 1200))
        h = max(220, int(self.curve_canvas.winfo_height() or 430))
        return 70, 14, w - 20, h - 20

    def _step_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.step_canvas.winfo_width() or 1200))
        h = max(120, int(self.step_canvas.winfo_height() or 260))
        return 70, 16, w - 20, h - 24

    def _time_to_x(self, t_ms: int, left: int, right: int) -> float:
        span = max(1, self.master_window.global_take_duration_ms)
        return left + (t_ms / span) * (right - left)

    def _x_to_time(self, x: float, left: int, right: int) -> int:
        rel = (x - left) / max(1.0, (right - left))
        rel = max(0.0, min(1.0, rel))
        return self.model.snap_time(rel * self.master_window.global_take_duration_ms)

    def _logical_y_to_canvas(self, y: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(self.model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(self.model.config.y_limit))
        operator_y = float(y) * (operator_range / logical_limit)
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.model.sandbox.top_bottom_margin)
        return mid - (operator_y / operator_range) * usable

    def _canvas_to_logical_y(self, py: float, top: int, bottom: int, apply_snap: bool = True) -> float:
        operator_range = max(200.0, float(self.model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(self.model.config.y_limit))
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(self.model.sandbox.top_bottom_margin)
        operator_y = ((mid - py) / max(1.0, usable)) * operator_range
        logical_y = operator_y * (logical_limit / operator_range)
        logical_y = self.model.clamp_y(logical_y)
        if apply_snap:
            return self.model.apply_zero_snap(self.master_window.main_take_settings, logical_y)
        return logical_y

    def _drag_delta_to_logical_y(self, delta_py: float, top: int, bottom: int) -> float:
        logical_limit = max(1.0, float(self.model.config.y_limit))
        usable = (bottom - top) / 2.0 - float(self.model.sandbox.top_bottom_margin)
        precision = max(0.05, float(self.model.sandbox.mouse_y_precision))
        logical_per_px = logical_limit / max(1.0, usable)
        return float(delta_py) * logical_per_px * precision

    def _read_step_tuning_from_ui(self) -> StepTuning:
        tuning = StepTuning(
            dead_zone_y=float(self.step_vars["dead_zone_y"].get()),
            input_max_y=float(self.step_vars["input_max_y"].get()),
            input_gamma=float(self.step_vars["input_gamma"].get()),
            step_rate_gain=float(self.step_vars["step_rate_gain"].get()),
            step_rate_max_percent=float(self.step_vars["step_rate_max_percent"].get()),
            preview_rate_smoothing=float(self.step_vars["preview_rate_smoothing"].get()),
            adrr_strength=self._adrr_operator_to_strength(float(self.step_vars["adrr_strength"].get())),
            bucket_width_px=int(self.step_vars["bucket_width_px"].get()),
            off_bar_height=int(self.step_vars["off_bar_height"].get()),
            low_zone_gain=float(self.step_vars["low_zone_gain"].get()),
            mid_zone_gain=float(self.step_vars["mid_zone_gain"].get()),
            high_zone_gain=float(self.step_vars["high_zone_gain"].get()),
            accumulator_bias=float(self.step_vars["accumulator_bias"].get()),
            emit_threshold=float(self.step_vars["emit_threshold"].get()),
            node_hit_radius_px=int(self.step_vars["node_hit_radius_px"].get()),
            time_drag_threshold_samples=int(self.step_vars["time_drag_threshold_samples"].get()),
        )
        tuning.clamp()
        return tuning

    def _apply_to_main_take(self) -> None:
        self.master_window.sync_axis_from_dialog(self.axis_index, status=f"Zaktualizowano MAIN TAKE z osi: {self.model.axis_def.axis_name}.")

    def _apply_visual_settings(self) -> None:
        self.model.sandbox.display_y_scale = float(self.display_y_scale.get())
        self.model.sandbox.mouse_y_precision = float(self.mouse_y_precision.get())
        self.model.sandbox.top_bottom_margin = int(self.top_bottom_margin.get())
        self._curve_needs_redraw = True
        self._refresh_curve_only("Zastosowano ustawienia wizualne (tylko krzywa).")

    def _apply_step_tuning_live(self) -> None:
        if getattr(self, "_is_switching_axis", False):
            return
        self._is_live_preview = True
        if self._step_tuning_after_id is not None:
            self.after_cancel(self._step_tuning_after_id)
        self._step_tuning_after_id = self.after(100, self._flush_step_tuning_live)

    def _on_scale_release(self) -> None:
        """Po puszczeniu suwaka liczy pełny ADRR i odświeża wynik osi."""
        self._apply_adrr_after_axis_edit(
            curve=False,
            apply_step_tuning=True,
            status="ADRR przeliczony po puszczeniu suwaka.",
        )

    def _apply_adrr_after_axis_edit(
        self,
        *,
        curve: bool = False,
        apply_step_tuning: bool = False,
        status: str | None = None,
    ) -> None:
        """Finalizuje operację operatora: pełny ADRR, markery i matrix osi.

        Live preview używa RAW STEP bez pełnego ADRR. Ta metoda jest jedyną
        ścieżką finalną po puszczeniu kropki/suwaka albo po dodaniu/usunięciu
        punktu. Najpierw liczy build_step_rows(..., fast_mode=False), aby
        last_adrr_dirt był gotowy przed rysowaniem czerwonych markerów.
        """
        self._is_live_preview = False

        if self._step_redraw_after_id is not None:
            self.after_cancel(self._step_redraw_after_id)
            self._step_redraw_after_id = None
        if self._step_tuning_after_id is not None:
            self.after_cancel(self._step_tuning_after_id)
            self._step_tuning_after_id = None

        if apply_step_tuning:
            old_dead_zone = float(self.model.step_tuning.dead_zone_y)
            tuning = self._read_step_tuning_from_ui()
            self.model.set_step_tuning(tuning)
            curve = curve or abs(float(tuning.dead_zone_y) - old_dead_zone) > 1e-9

        if self._nodes_dirty:
            self.model.sort_and_fix_nodes()
            self._nodes_dirty = False

        self.model._invalidate_cache()
        self.model.build_step_rows(
            duration_ms=self.master_window.global_take_duration_ms,
            fast_mode=False,
        )

        self._curve_needs_redraw = self._curve_needs_redraw or bool(curve)
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""

        self._snajper_refresh_targets(
            curve=bool(curve),
            step=True,
            metrics=True,
            status=status,
        )
        self.master_window._request_dialog_axis_final_preview(self.axis_index)

    def _flush_step_tuning_live(self) -> None:
        self._step_tuning_after_id = None
        old_dead_zone = float(self.model.step_tuning.dead_zone_y)
        tuning = self._read_step_tuning_from_ui()
        self.model.set_step_tuning(tuning)
        self._curve_needs_redraw = abs(float(tuning.dead_zone_y) - old_dead_zone) > 1e-9
        self._step_needs_redraw = True
        self._metrics_cache_key = None
        self._metrics_cache_text = ""
        self._nodes_dirty = True
        self._snajper_refresh_targets(
            curve=self._curve_needs_redraw,
            step=True,
            metrics=True,
            status="Zastosowano strojenie STEP.",
        )
        self.master_window._request_dialog_axis_live_preview(self.axis_index)

    def _refresh_metrics(self) -> None:
        cache_key = (
            self.master_window.global_take_duration_ms,
            self.model.release_time_ms,
            tuple((n.time_ms, round(n.y, 4)) for n in self.model.nodes),
            self.model.step_tuning.dead_zone_y,
            self.model.step_tuning.input_max_y,
            self.model.step_tuning.input_gamma,
            self.model.step_tuning.step_rate_gain,
            self.model.step_tuning.step_rate_max_percent,
            self.model.step_tuning.preview_rate_smoothing,
            getattr(self.model.step_tuning, "adrr_strength", 0.0),
        )
        if cache_key != self._metrics_cache_key:
            is_live = self._is_live_preview or (self._step_redraw_after_id is not None) or (self._step_tuning_after_id is not None)
            self._metrics_cache_text = self.model.metrics_summary(
                duration_ms=self.master_window.global_take_duration_ms,
                fast_mode=is_live,
            )
            self._metrics_cache_key = cache_key
        
        if self.metrics_var.get() != self._metrics_cache_text:
            self.metrics_var.set(self._metrics_cache_text)

    def _soft_start_segments_from_samples(self, samples: list[tuple[int, float]], dead_zone: float) -> list[tuple[float, float]]:
        """
        Wyznacza lokalne strefy MIĘKKIEGO STARTU na podstawie przebiegu krzywej.

        TARZAN nie traktuje początku i końca TAKE jak CNC. Brązowa strefa ma
        pojawiać się tylko lokalnie tam, gdzie krzywa przechodzi przez okolice
        zera, czyli w paśmie:

            -dead_zone_y <= y <= +dead_zone_y

        Nie poszerzamy tej strefy o start_settle_ms/start_ramp_ms z mechaniki,
        bo wtedy przy kilku przejściach przez zero obszary zlewają się w jeden
        długi pas od początku do końca. Mechanika ogranicza generator STEP,
        a tutaj rysujemy czytelny operatorski obraz MIĘKKIEGO STARTU.
        """
        if not samples or len(samples) < 2 or dead_zone <= 0.0:
            return []

        ordered = sorted((float(t), float(y)) for t, y in samples)
        zero_segments: list[tuple[float, float]] = []

        # Dokładnie wyznaczamy odcinki, w których krzywa jest w paśmie zera.
        # Granice są interpolowane na poziomach +dead_zone_y / -dead_zone_y,
        # a nie zaokrąglane do najbliższej próbki.
        for idx in range(1, len(ordered)):
            t0, y0 = ordered[idx - 1]
            t1, y1 = ordered[idx]
            if t1 <= t0:
                continue

            cuts = [t0, t1]
            dy = y1 - y0
            if abs(dy) > 1e-9:
                for level in (-dead_zone, dead_zone):
                    frac = (level - y0) / dy
                    if 0.0 < frac < 1.0:
                        cuts.append(t0 + frac * (t1 - t0))

            cuts = sorted(set(round(cut, 6) for cut in cuts))
            for a, b in zip(cuts, cuts[1:]):
                if b <= a:
                    continue
                mid_t = (a + b) / 2.0
                mid_frac = (mid_t - t0) / (t1 - t0)
                mid_y = y0 + dy * mid_frac
                if abs(mid_y) <= dead_zone:
                    zero_segments.append((a, b))

        # Łączymy tylko bezpośrednio sąsiadujące fragmenty tego samego przejścia.
        # Nie dokładamy tu mechanicznego czasu rampy, żeby nie tworzyć długich
        # brązowych pól między osobnymi przejściami przez zero.
        merged: list[tuple[float, float]] = []
        for a, b in zero_segments:
            if not merged:
                merged.append((a, b))
                continue
            prev_a, prev_b = merged[-1]
            if a <= prev_b + 0.001:
                merged[-1] = (prev_a, max(prev_b, b))
            else:
                merged.append((a, b))
        return merged


    def _draw_soft_start_background(
        self,
        canvas: tk.Canvas,
        left: int,
        top: int,
        right: int,
        bottom: int,
        samples: list[tuple[int, float]],
    ) -> None:
        """
        Rysuje tło stref ruchu w oknie pojedynczej osi.

        Zielony obszar = normalny ruch poza lokalną strefą MIĘKKIEGO STARTU.
        Brązowy obszar = lokalny MIĘKKI START / lokalne wygaszenie:
        każde przejście krzywej przez pas zera wyznaczony przez dead_zone_y.
        Strefa nie jest poszerzana o start_settle_ms/start_ramp_ms.
        """
        canvas.create_rectangle(left, top, right, bottom, fill=self.master_window.SAFE, outline="")

        dead_zone = max(0.0, float(self.model.step_tuning.dead_zone_y))
        min_px_width = 2.0
        for start_t, end_t in self._soft_start_segments_from_samples(samples, dead_zone):
            if end_t <= start_t:
                continue
            x_a = self._time_to_x(int(round(start_t)), left, right)
            x_b = self._time_to_x(int(round(end_t)), left, right)
            if x_b <= x_a:
                continue
            if x_b - x_a < min_px_width:
                center = (x_a + x_b) / 2.0
                x_a = max(left, center - min_px_width / 2.0)
                x_b = min(right, center + min_px_width / 2.0)
            canvas.create_rectangle(x_a, top, x_b, bottom, fill=self.master_window.WARN, outline="")

    def _draw_curve(self) -> None:
        c = self.curve_canvas
        c.delete("all")
        left, top, right, bottom = self._curve_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="")

        samples = self.model.sample_curve(1000, duration_ms=self.master_window.global_take_duration_ms)
        self._draw_soft_start_background(c, left, top, right, bottom, samples)

        for yv in [100, 50, 0, -50, -100]:
            py = self._logical_y_to_canvas(yv, top, bottom)
            width = self.master_window.main_take_settings.zero_line_width if yv == 0 else 1
            dash = None if yv == 0 else (5, 4)
            color = self.master_window.main_take_settings.zero_line_color if yv == 0 else self.master_window.WARN
            c.create_line(left, py, right, py, fill=color, width=width, dash=dash)
            c.create_text(left - 8, py, text=str(yv), fill=self.master_window.MUTED, anchor="e", font=("Consolas", 8))

        total_minutes = max(1, int(self.master_window.global_take_duration_ms // 60000))
        for minute in range(0, total_minutes + 1):
            t_ms = minute * 60000
            if t_ms > self.master_window.global_take_duration_ms:
                continue
            px = self._time_to_x(t_ms, left, right)
            c.create_line(px, top, px, bottom, fill="#43505C", dash=(2, 6))
            c.create_text(px, bottom + 10, text=f"{minute}m", fill=self.master_window.MUTED, anchor="n", font=("Consolas", 8))

        original_nodes = getattr(self.model, "original_nodes", None)
        ghost_settings = self.master_window.main_take_settings
        if getattr(ghost_settings, "show_ghost_line", True) and original_nodes and len(original_nodes) >= 2:
            # Używamy zoptymalizowanego samplowania ghostów
            ghost_samples = self.master_window._sample_original_curve(self.model)
            ghost_pts = []
            for t, y in ghost_samples:
                ghost_pts.extend([self._time_to_x(t, left, right), self._logical_y_to_canvas(y, top, bottom)])
            if len(ghost_pts) >= 4:
                c.create_line(
                    *ghost_pts,
                    fill=getattr(ghost_settings, "ghost_line_color", "#EAB308"),
                    width=int(getattr(ghost_settings, "ghost_line_width", 1)),
                    dash=(
                        int(getattr(ghost_settings, "ghost_line_dash_on", 4)),
                        int(getattr(ghost_settings, "ghost_line_dash_off", 4)),
                    ),
                    smooth=False,
                )

        pts = []
        for t, y in samples:
            pts.extend([self._time_to_x(t, left, right), self._logical_y_to_canvas(y, top, bottom)])
        if len(pts) >= 4:
            c.create_line(*pts, fill=self.master_window.CURVE, width=self.master_window.main_take_settings.curve_line_width, smooth=False)

        hit_radius = self.model.step_tuning.node_hit_radius_px
        r = max(4, min(10, hit_radius // 2))
        for i, n in enumerate(self.model.nodes):
            px = self._time_to_x(n.time_ms, left, right)
            py = self._logical_y_to_canvas(n.y, top, bottom)
            
            fill = self.master_window.NODE_SEL if i == self.selected_index else self.master_window.NODE
            
            # Podświetlenie punktu jeśli jest przyciągnięty do ghosta (Dla punktu lub PAN)
            is_snapped = False
            if self.drag_mode == "node" and i == self.selected_index:
                if getattr(self, "is_ghost_snapped", False) or getattr(self, "is_zero_snapped", False) or (getattr(self, "_drag_zero_snap_locked", False) and n.y == 0.0):
                    is_snapped = True
            elif self.drag_mode == "pan":
                if getattr(self, "is_ghost_snapped", False):
                    is_snapped = True
                
            if is_snapped:
                fill = "#22C55E" # Zielony (Emerald-500)
            
            if i == 0 or i == len(self.model.nodes) - 1:
                fill = "#D6EAF8"
            c.create_oval(px - r, py - r, px + r, py + r, fill=fill, outline="black")

        x0 = self._time_to_x(0, left, right)
        x1 = self._time_to_x(self.master_window.global_take_duration_ms, left, right)
        c.create_line(x0, top, x0, bottom, fill="#45C46B", width=3)
        c.create_line(x1, top, x1, bottom, fill="#E65D5D", width=3)

    def _draw_step(self) -> None:
        if self._nodes_dirty:
            self.model.sort_and_fix_nodes()
            self.model._invalidate_cache()
            self._nodes_dirty = False

        c = self.step_canvas
        c.delete("all")
        left, top, right, bottom = self._step_rect()
        c.create_rectangle(left, top, right, bottom, fill="#1A1E24", outline="#303A45")

        # Wymuszamy fast_mode=True podczas jakiejkolwiek interakcji live (drag punktu lub suwaka).
        is_live = self._is_live_preview or (self._step_redraw_after_id is not None) or (self._step_tuning_after_id is not None)
        rows = self.model.build_step_rows(duration_ms=self.master_window.global_take_duration_ms, fast_mode=is_live)
        if not rows:
            return
        tuning = self.model.step_tuning
        y_mid = (top + bottom) / 2.0
        c.create_line(left, y_mid, right, y_mid, fill="#55606D")
        bucket = max(1, tuning.bucket_width_px)
        px_bucket = {}
        for row in rows:
            raw_x = int(round(self._time_to_x(row["time_ms"], left, right)))
            x = ((raw_x - left) // bucket) * bucket + left
            item = px_bucket.setdefault(x, {"step": 0, "count": 0})
            item["step"] = max(item["step"], int(row["step"]))
            item["count"] = int(row["count"])
        for x in sorted(px_bucket.keys()):
            row = px_bucket[x]
            if row["step"] == 1:
                c.create_line(x, y_mid, x, top + 12, fill=self.master_window.STEP_ON, width=max(1, bucket))
            else:
                c.create_line(x, y_mid, x, y_mid + tuning.off_bar_height, fill=self.master_window.STEP_OFF, width=max(1, bucket))

        adrr_dirt = list(getattr(self.model, "last_adrr_dirt", []) or [])
        if adrr_dirt:
            marker_bucket = max(1, bucket)
            marked_x: set[int] = set()
            for dirt in adrr_dirt:
                time_ms = int(getattr(dirt, "time_ms", 0))
                raw_x = int(round(self._time_to_x(time_ms, left, right)))
                x = ((raw_x - left) // marker_bucket) * marker_bucket + left
                if x in marked_x:
                    continue
                marked_x.add(x)
                marker_top = top + 6
                marker_bottom = min(bottom, int(y_mid + tuning.off_bar_height + 4))
                c.create_line(x, marker_bottom, x, marker_top, fill="#FF3B30", width=max(2, marker_bucket), stipple="gray50")

        c.create_text(left, top - 2, text="STEP 0/1 preview", fill=self.master_window.FG, anchor="sw", font=("Segoe UI Semibold", 9))
        c.create_text(right, top - 2, text=f"rows={len(rows)}  pulses={rows[-1]['count']}", fill=self.master_window.MUTED, anchor="se", font=("Consolas", 8))

        # ADRR diagnostics must stay readable in the STEP preview area.
        # Do not build one long line: each operator value gets its own ADRR-prefixed row.
        chaos = getattr(self.model, "last_adrr_chaos", None)
        diag_lines: list[str] = []
        if adrr_dirt:
            diag_lines.append(f"ADRR dirt: {len(adrr_dirt)}")
        if chaos is not None:
            try:
                before = float(getattr(chaos, "chaos_before", 0.0))
                after = float(getattr(chaos, "chaos_after", 0.0))
                improvement = float(getattr(chaos, "improvement_percent", 0.0))
                moved = int(getattr(chaos, "moved_count", 0))
                removed = int(getattr(chaos, "removed_count", 0))
                diag_lines.extend([
                    f"ADRR chaos przed: {before:.0f}",
                    f"ADRR chaos po: {after:.0f}",
                    f"ADRR poprawa: {improvement:+.0f}%",
                    f"ADRR moved: {moved}",
                    f"ADRR removed: {removed}",
                ])
            except Exception:
                diag_lines.append("ADRR chaos: -")
        if diag_lines:
            diag_x = right - 4
            diag_y = top + 8
            line_h = 11
            for idx, line in enumerate(diag_lines[:6]):
                c.create_text(
                    diag_x,
                    diag_y + idx * line_h,
                    text=line,
                    fill=self.master_window.MUTED,
                    anchor="ne",
                    font=("Consolas", 8),
                )

    def _set_status(self, status: str | None = None) -> None:
        self.status_var.set(status if status is not None else "Sandbox osi gotowy do strojenia.")

    def _request_curve_redraw(self) -> None:
        self._curve_needs_redraw = True
        if self._curve_redraw_after_id is not None:
            return
        self._curve_redraw_after_id = self.after(16, self._flush_curve_redraw)

    def _flush_curve_redraw(self) -> None:
        self._curve_redraw_after_id = None
        if self._curve_needs_redraw:
            self._snajper_refresh_targets(curve=True)

    def _apply_drag_zero_snap(self, value: float) -> float:
        value = self.model.clamp_y(value)
        if not getattr(self.master_window.main_take_settings, "snap_to_zero_enabled", False):
            self._drag_zero_snap_locked = False
            return value
        threshold = max(0.0, float(getattr(self.master_window.main_take_settings, "snap_to_zero_threshold", 0.0)))
        enter_threshold = threshold * 0.6
        release_threshold = max(enter_threshold, threshold)
        if self._drag_zero_snap_locked:
            if abs(value) <= release_threshold:
                return 0.0
            self._drag_zero_snap_locked = False
            return value
        if abs(value) <= enter_threshold:
            self._drag_zero_snap_locked = True
            return 0.0
        return value

    def _refresh_metrics_only(self) -> None:
        self._refresh_metrics()

    def _refresh_curve_only(self, status: str | None = None) -> None:
        if self._curve_needs_redraw:
            if self._nodes_dirty:
                self.model.sort_and_fix_nodes()
                self._nodes_dirty = False
            self._snajper_refresh_targets(curve=True)
        if status is not None:
            self._snajper_refresh_targets(status=status)

    def _refresh_step_only(self, status: str | None = None) -> None:
        if self._step_needs_redraw:
            self._snajper_refresh_targets(step=True)
        if status is not None:
            self._snajper_refresh_targets(status=status)

    def _request_step_redraw(self) -> None:
        self._is_live_preview = True
        self._step_needs_redraw = True
        if self._step_redraw_after_id is not None:
            return
        self._step_redraw_after_id = self.after(100, self._flush_step_redraw)

    def _flush_step_redraw(self) -> None:
        self._step_redraw_after_id = None
        if self._step_needs_redraw:
            self._snajper_refresh_targets(step=True)

    def _hit_node(self, x: float, y: float) -> int | None:
        left, top, right, bottom = self._curve_rect()
        radius = self.model.step_tuning.node_hit_radius_px
        for i, n in enumerate(self.model.nodes):
            px = self._time_to_x(n.time_ms, left, right)
            py = self._logical_y_to_canvas(n.y, top, bottom)
            if abs(px - x) <= radius and abs(py - y) <= radius:
                return i
        return None

    def _get_ghost_y_at_time(self, t_ms: int) -> float | None:
        """
        Zwraca wartość y ghosta (original_nodes) dla czasu t_ms na podstawie cachowanych próbek.
        """
        if not hasattr(self, "_ghost_samples_cache") or not self._ghost_samples_cache:
            return None
        
        # Proste wyszukiwanie w posortowanych próbkach (linearna interpolacja lub najbliższy sąsiad)
        # Biorąc pod uwagę, że próbek jest max 450-800, prosty loop wystarczy, ale binary search lepszy.
        samples = self._ghost_samples_cache
        if t_ms <= samples[0][0]: return samples[0][1]
        if t_ms >= samples[-1][0]: return samples[-1][1]
        
        import bisect
        idx = bisect.bisect_left(samples, (t_ms, -1e9))
        if idx == 0: return samples[0][1]
        if idx >= len(samples): return samples[-1][1]
        
        t0, y0 = samples[idx-1]
        t1, y1 = samples[idx]
        if t1 == t0: return y0
        
        frac = (t_ms - t0) / (t1 - t0)
        return y0 + frac * (y1 - y0)

    def _on_curve_press(self, event) -> None:
        idx = self._hit_node(event.x, event.y)
        if idx is not None:
            self._is_live_preview = True
            self.selected_index = idx
            self.selected_node_ref = self.model.nodes[idx]
            self.drag_mode = "node"
            # Ghost assist cache
            self._ghost_samples_cache = []
            if getattr(self.master_window.main_take_settings, "ghost_assist_enabled", False):
                self._ghost_samples_cache = self.master_window._sample_original_curve(self.model)

            # Natychmiastowe przyciągnięcie punktu pod kursor (podczas drag bez snapu)
            left, top, right, bottom = self._curve_rect()
            new_t = self._x_to_time(event.x, left, right)
            new_y = self._canvas_to_logical_y(event.y, top, bottom, apply_snap=False)
            self.model.move_node(self.selected_index, new_t, new_y)
            self._restore_selected_index_from_ref()
            self.master_window._request_dialog_axis_live_preview(self.axis_index)
            
            self.drag_anchor_x = event.x
            self.drag_anchor_y = event.y
            self._request_curve_redraw()
            self._set_status(f"Wybrano punkt {idx} i przyciągnięto do kursora.")
            return
        self.selected_index = None
        self.drag_mode = "pan"
        self._is_live_preview = True
        self.drag_anchor_x = event.x
        
        # Ghost assist cache for PAN
        self._ghost_samples_cache = []
        if getattr(self.master_window.main_take_settings, "ghost_assist_enabled", False):
            self._ghost_samples_cache = self.master_window._sample_original_curve(self.model)

        self._request_curve_redraw()
        self._set_status("PAN linii.")

    def _on_curve_drag(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        if self.drag_mode == "node" and self.selected_index is not None:
            new_t = self._x_to_time(event.x, left, right)
            new_y = self._canvas_to_logical_y(event.y, top, bottom, apply_snap=False)
            
            # Ghost Assist logic
            self.is_ghost_snapped = False
            self.is_zero_snapped = False
            ms = self.master_window.main_take_settings
            if getattr(ms, "ghost_assist_enabled", False) and self._ghost_samples_cache:
                gy = self._get_ghost_y_at_time(new_t)
                if gy is not None:
                    threshold = getattr(ms, "ghost_assist_threshold_y", 4.0)
                    if abs(new_y - gy) <= threshold:
                        new_y = gy
                        self.is_ghost_snapped = True

            if not self.is_ghost_snapped:
                snapped_y = self._apply_drag_zero_snap(new_y)
                if snapped_y == 0.0 and new_y != 0.0:
                    self.is_zero_snapped = True
                new_y = snapped_y

            if self.model.move_node(self.selected_index, new_t, new_y):
                self._restore_selected_index_from_ref()
                self.model._invalidate_cache()
                self._curve_needs_redraw = True
                self._step_needs_redraw = True
                self._nodes_dirty = True
                self._request_curve_redraw()
                self._request_step_redraw()
                self.master_window._request_dialog_axis_live_preview(self.axis_index)
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(event.x, left, right)
            old_time = self._x_to_time(self.drag_anchor_x, left, right)
            delta = new_time - old_time
            
            # Ghost Assist logic for PAN (Time Snap Only)
            self.is_ghost_snapped = False
            ms = self.master_window.main_take_settings
            if getattr(ms, "ghost_assist_enabled", False) and self._ghost_samples_cache and self.model.nodes:
                threshold_y = getattr(ms, "ghost_assist_threshold_y", 4.0)
                threshold_t = 50.0 # Progiem dla PAN w czasie może być np. 50ms
                
                # Szukamy czy jakikolwiek node po przesunięciu o delta trafi w ghost
                for node in self.model.nodes:
                    planned_t = node.time_ms + delta
                    gy = self._get_ghost_y_at_time(planned_t)
                    if gy is not None:
                        # Jeśli Y jest blisko, to snapujemy w czasie do najbliższego momentu o tym samym Y na ghost?
                        # Instrukcja mówi: "skoryguj delta_t tak, żeby node.time_ms po przesunięciu równał się ghost_node.time_ms"
                        # Ale nie mamy bezpośrednio ghost_nodes, mamy samples. 
                        # Jednak original_nodes są dostępne w modelu jeśli zostały zapisane.
                        pass
                
                # Spróbujmy podejścia z original_nodes dla precyzyjnego snapu do węzłów
                if hasattr(self.model, 'original_nodes') and self.model.original_nodes:
                    best_snap_delta = None
                    for node in self.model.nodes:
                        planned_t = node.time_ms + delta
                        for g_node in self.model.original_nodes:
                            if abs(planned_t - g_node.time_ms) <= threshold_t and abs(node.y - g_node.y) <= threshold_y:
                                # Snapujemy delta_t tak, aby node trafił dokładnie w g_node.time_ms
                                best_snap_delta = g_node.time_ms - node.time_ms
                                break
                        if best_snap_delta is not None: break
                    
                    if best_snap_delta is not None:
                        delta = best_snap_delta
                        self.is_ghost_snapped = True

            self.drag_anchor_x = event.x
            if self.model.shift_all(delta):
                self.model._invalidate_cache()
                self._curve_needs_redraw = True
                self._step_needs_redraw = True
                self._nodes_dirty = True
                self._request_curve_redraw()
                self._request_step_redraw()
                self.master_window._request_dialog_axis_live_preview(self.axis_index)

    def _on_curve_release(self, _event) -> None:
        self.is_ghost_snapped = False
        self._is_live_preview = False
        
        # Anulujemy planowane odświeżenia live, aby wymusić pełny FINAL refresh
        if self._step_redraw_after_id is not None:
            self.after_cancel(self._step_redraw_after_id)
            self._step_redraw_after_id = None
        if self._step_tuning_after_id is not None:
            self.after_cancel(self._step_tuning_after_id)
            self._step_tuning_after_id = None

        if self.drag_mode == "node" and self.selected_index is not None:
            # Dopiero przy release stosujemy snap do zera
            left, top, right, bottom = self._curve_rect()
            node = self.model.nodes[self.selected_index]
            final_y = self.model.apply_zero_snap(self.master_window.main_take_settings, node.y)
            if self.model.move_node(self.selected_index, node.time_ms, final_y):
                self._restore_selected_index_from_ref()
                self.model._invalidate_cache()
                self._nodes_dirty = True

        self.drag_mode = None
        self.selected_node_ref = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._curve_needs_redraw = True
        self._apply_adrr_after_axis_edit(
            curve=True,
            apply_step_tuning=False,
            status="ADRR przeliczony po puszczeniu punktu.",
        )

    def _on_curve_double_click(self, event) -> None:
        left, top, right, bottom = self._curve_rect()
        t = self._x_to_time(event.x, left, right)
        y = self._canvas_to_logical_y(event.y, top, bottom)
        self.model.add_node(t, y)
        self._curve_needs_redraw = True
        self._nodes_dirty = True
        self._apply_adrr_after_axis_edit(
            curve=True,
            apply_step_tuning=False,
            status="ADRR przeliczony po dodaniu punktu.",
        )

    def _on_curve_right_click(self, event) -> None:
        idx = self._hit_node(event.x, event.y)
        if idx is None:
            return
        self.model.remove_node(idx)
        self.selected_index = None
        self.selected_node_ref = None
        self._curve_needs_redraw = True
        self._nodes_dirty = True
        self._apply_adrr_after_axis_edit(
            curve=True,
            apply_step_tuning=False,
            status="ADRR przeliczony po usunięciu punktu.",
        )

    def _on_close(self) -> None:
        # Zamknięcie okna pojedynczej osi nie synchronizuje MAIN TAKE.
        # Dane trafiają do głównego EHR wyłącznie przez SET UP -> MAIN TAKE.
        self.selected_node_ref = None
        self.master_window.axis_detail_dialog = None
        self.destroy()



class EhrMainSnajperAdapter:
    """Adapter Snajpera dla głównego EHR.

    Nie generuje STEP ani ADRR. Tylko kieruje strzał Snajpera w istniejące
    metody odświeżenia aktywnej osi: krzywa, metryki, STEP preview.
    """

    def __init__(self, window: "TarzanEhrMultiAxisWindow") -> None:
        self.window = window

    def update_target(self, target, value: Any) -> None:
        if str(target.target) == "page_full":
            self.window._snajper_draw_ehr_page_full()
            return
        if str(target.target) == "active_axis_changed":
            self.window._refresh_axis_context(refresh_axis_info=True, refresh_protocol=True)
            return
        if str(target.target) == "page_init":
            self.window._snajper_draw_ehr_page_init()
            return

        axis_index = self.window._axis_index_from_ehr_target(str(target.target))
        if axis_index is None:
            return

        if str(target.target).endswith("_curve"):
            self.window._snajper_draw_ehr_axis_curve(axis_index)
            return

        if str(target.target).endswith("_step_preview"):
            self.window._snajper_draw_ehr_axis_step_preview(axis_index)
            return

        if str(target.target).endswith("_metrics"):
            self.window._snajper_draw_ehr_axis_metrics(axis_index)
            return

        if str(target.target).endswith("_live_matrix"):
            self.window._snajper_draw_ehr_axis_live_matrix(axis_index)
            return

        if str(target.target).endswith("_final_matrix"):
            self.window._snajper_draw_ehr_axis_final_matrix(axis_index)
            return


class TarzanEhrMultiAxisWindow(tk.Tk):
    BG = "#1B2028"
    MAIN_CURVE_SAMPLES_IDLE = 450
    MAIN_CURVE_SAMPLES_DRAG = 120
    PANEL = "#1B2028"
    PANEL2 = "#212730"
    FG = "#F3F6F8"
    MUTED = "#AEB7C2"
    CURVE = "#D9E7F5"
    NODE = "#FFD166"
    NODE_SEL = "#FF9F1C"
    STEP_ON = "#45C46B"
    STEP_OFF = "#48525E"
    SAFE = "#1E3A2F"
    WARN = "#5A4A1B"
    DANGER = "#4A2222"

    def __init__(self) -> None:
        super().__init__()
        self.title("TARZAN — tarzanEHR")
        self.geometry("1780x1080")
        self.minsize(1500, 920)
        self.configure(bg=self.BG)
        self.clock_font_family = select_clock_font_family()
        self.protocol_desc_font_family = select_protocol_desc_font_family()

        self.config_model = EhrEditorConfig()
        self.settings_path = self._settings_path()
        self.main_take_settings = MainTakeSettings.load_or_default(self.settings_path)
        self.global_take_duration_ms = self.main_take_settings.take_duration_ms()
        self.axis_models = [AxisCurveModel(axis_def, self.config_model) for axis_def in DEFAULT_AXIS_DEFINITIONS]
        for axis in self.axis_models:
            axis.sandbox.mouse_y_precision = 1.0
            axis.sandbox.top_bottom_margin = 8
            axis.set_axis_take_duration_ms(self.global_take_duration_ms)
        self.active_axis_index = 0
        self.selected_index: int | None = None
        self.selected_node_ref = None
        self.drag_axis_index: int | None = None
        self.drag_mode: str | None = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self.drag_anchor_node_time = 0
        self.drag_anchor_node_y = 0.0
        self.axis_rects: dict[int, AxisViewportRect] = {}
        self.gear_rects: dict[int, GearRect] = {}
        self.wave_rects: dict[int, WaveRect] = {}
        self.kro_enabled_var = tk.BooleanVar(value=getattr(self.main_take_settings, 'kro_enabled', True))
        self.kro = TarzanKroEhrAdapter(self)
        self.axis_detail_dialog: AxisSettingsDialog | None = None
        self.drag_release_anchor_time = 0
        self._drag_zero_snap_locked = False
        self._drag_data_changed = False
        self.dirty_axis_indices: set[int] = set()
        self._axis_data_versions = [0 for _ in self.axis_models]
        self._axis_selection_version = 0

        self.selected_point_time_var = tk.StringVar(value="--:--")
        self.axis_info_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Gotowy.")
        self.protocol_cache_key = None
        self.protocol_cache_text = ""
        self.axis_info_cache_key = None
        self.axis_info_cache_text = ""
        self.is_ghost_snapped = False
        self._ghost_samples_cache = []
        self._main_canvas_needs_redraw = True
        self._axis_info_dirty = True
        self._protocol_dirty = True
        self._force_curve_resample_after_save = False
        self._configure_after_id = None
        self._main_canvas_redraw_after_id = None
        self.main_grid = None
        self.panel_a_top = None
        self.panel_b_clock = None
        self.take_panel = None
        self.panel_d_info = None
        self.panel_e_timeline = None
        self.panel_f_status = None
        self.take_widget = None
        self._axis_activity: dict[str, bool] = {}
        self.main_body = None
        self._axis_icons_cache: dict[tuple[str, int], ImageTk.PhotoImage] = {}
        self._axis_icon_mapping = {
            "oś pozioma ramienia": "ta_os_pozioma_ramienia_ico_320_active.png",
            "oś pozioma kamery": "ta_os_pozioma_kamery_ico_320_active.png",
            "oś pochyłu kamery": "ta_os_pochylu_kamery_ico_320_active.png",
            "oś pochyłu ramienia": "ta_os_pochylu_kamery_ico_320_active.png",
            "oś pionowa ramienia": "ta_os_pionowa_ramienia_ico_320_active.png",
            "oś pionowa kamery": "ta_os_pionowa_kamery_ico_320_active.png",
            "oś ostrości kamery": "ta_os_ostrosci_kamery_ico_320_active.png",
            "DRON": "ta_dron_ico_320_active.png"
        }

        # TARZAN EHR MAIN -> SNAJPER
        # Jeden strzał Snajpera odświeża tylko wskazaną oś głównego EHR.
        self.tarzan_snajper = create_default_tarzan_snajper()
        self.ehr_main_snajper_adapter = EhrMainSnajperAdapter(self)
        self.tarzan_snajper.register_adapter("ehr_main", self.ehr_main_snajper_adapter)
        self.tarzan_snajper.register_adapter("ehr_canvas", self.ehr_main_snajper_adapter)
        self.tarzan_snajper.register_adapter("ehr_tkinter", self.ehr_main_snajper_adapter)

        self.tarzan_snajper.register_target("ehr_init", T("ehr_main", "page", "page_init", "refresh"))
        self.tarzan_snajper.register_target("ehr_page_full", T("ehr_main", "page", "page_full", "refresh"))
        self.tarzan_snajper.register_target("ehr_active_axis_changed", T("ehr_main", "page", "active_axis_changed", "refresh"))

        self._ehr_axis_fire_seq = 0

        self._init_runtime_integration()
        self._build_ui()
        self._load_axis_activity()
        self.update_idletasks()
        self.after_idle(lambda: self._snajper_init_ehr_page(status="Gotowy."))
        self.after_idle(self._load_active_slot_on_start)

    def _init_runtime_integration(self) -> None:
        """Inicjalizacja spięcia z SignalBus i TSP (Etap 9)."""
        self.bus = get_signal_bus()
        self.tsp_client = None
        
        # Raportujemy stan początkowy do lokalnego SignalBus
        self.bus.set_input("ehr_state", "READY", source="EHR_INIT")
        
        # Jeśli jesteśmy w trybie LIVE, uruchamiamy klienta TSP
        if self.bus.mode == "LIVE":
            self._start_tsp_client()

    def _start_tsp_client(self) -> None:
        """Uruchamia klienta TSP dla raportowania stanu do miniPC."""
        try:
            self.tsp_client = TarzanTspClient(host=TSP_MINI_PC_HOST, name="tarzanEHR")
            self.tsp_client.connect()
            self.tsp_client.hello()
            self.bus.log("EHR", "TSP Client connected to miniPC.")
            self.bus.set_input("ehr_state", "CONNECTED", source="EHR_TSP")
        except Exception as e:
            self.bus.log("EHR", f"TSP Connection failed: {e}")

    def _update_runtime_state(self, state: str) -> None:
        """Aktualizuje stan EHR w systemie."""
        self.bus.set_input("ehr_state", state, source="EHR_RUNTIME")
        if self.tsp_client:
            try:
                self.tsp_client.set_signal("ehr_state", state)
            except Exception: pass

    def _load_active_slot_on_start(self) -> None:
        """
        Inicjalne ładowanie aktywnego slotu przy starcie aplikacji.
        Logika zgodna z wytycznymi: brak popupów przy braku pliku, użycie istniejącego loadera.
        """
        if not self.take_widget:
            return

        store = self.take_widget.store
        active_idx = store.active_slot

        if active_idx is None or not (0 <= active_idx < len(self.take_widget.slot_models)):
            return

        vm = self.take_widget.slot_models[active_idx]
        if vm.file_path and vm.file_path.exists():
            try:
                # Wywołujemy ten sam loader co przy ręcznym kliknięciu łapki
                self._load_take_from_path(vm.file_path)

                # Upewniamy się, że VM wie o załadowaniu (UI sync)
                vm.is_loaded = True
                vm.state = SlotState.ACTIVE
                self.take_widget._refresh_slot(active_idx)

                self._set_status(f"Auto-load: TAKE {vm.take_number} załadowany z aktywnego slotu.")
                return
            except Exception as e:
                print(f"Błąd auto-loadingu TAKE ze slotu {active_idx}: {e}")
        elif vm.file_path:
            print(f"Auto-load SKIP: Plik {vm.file_path} nie istnieje.")
        
        # Jeśli nie załadowano pliku (lub błąd), wymuś inicjalny refresh
        self._snajper_init_ehr_page(status="Gotowy.")

    def _load_axis_activity(self) -> None:
        """Wczytuje stan aktywności osi z widgetu slotów."""
        if self.take_widget and self.take_widget.store:
            self._axis_activity = copy.deepcopy(self.take_widget.store.axis_activity)

    def _save_axis_activity(self) -> None:
        """
        Zapisuje stan aktywności osi do widgetu slotów i do pliku.
        Implementacja zapewnia natychmiastowy i bezpieczny zapis sekcji axis_activity
        bez nadpisywania całego pliku zera (read-modify-write).
        """
        if self.take_widget and self.take_widget.store:
            # 1. Aktualizacja w pamięci runtime
            self.take_widget.store.axis_activity = copy.deepcopy(self._axis_activity)

            # 2. Bezpieczny zapis do pliku (natychmiastowy)
            try:
                path = SLOTS_JSON_PATH
                # Wczytujemy aktualny stan pliku, aby nie zgubić innych danych
                if path.exists():
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        data = {}
                else:
                    data = {}

                # Aktualizujemy tylko sekcję aktywności osi
                data["axis_activity"] = self._axis_activity

                # Upewniamy się, że inne klucze (slots, active_slot) istnieją,
                # jeśli plik był pusty lub uszkodzony, pobierając je z bieżącego store
                if "slots" not in data:
                    data["slots"] = [asdict(slot) for slot in self.take_widget.store.slots]
                if "active_slot" not in data:
                    data["active_slot"] = self.take_widget.store.active_slot

                # Zapisujemy z powrotem
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except Exception as e:
                print(f"Błąd natychmiastowego zapisu axis_activity: {e}")

    def _is_axis_active(self, axis_index: int) -> bool:
        """Zwraca czy dana oś jest aktywna."""
        if 0 <= axis_index < len(self.axis_models):
            name = self.axis_models[axis_index].axis_def.axis_name
            return self._axis_activity.get(name, True)
        return True

    def _toggle_axis_activity(self, axis_index: int) -> None:
        """Przełącza stan aktywności osi."""
        if 0 <= axis_index < len(self.axis_models):
            name = self.axis_models[axis_index].axis_def.axis_name
            current = self._axis_activity.get(name, True)
            self._axis_activity[name] = not current
            self._save_axis_activity()
            self._request_main_canvas_redraw(only_axis_index=axis_index)
            state_str = "AKTYWNA" if self._axis_activity[name] else "NIEAKTYWNA (blokada edycji)"
            self._set_status(f"Oś {name} jest teraz {state_str}.")

    def _settings_path(self) -> Path:
        editor_dir = Path(__file__).resolve().parent.parent
        project_dir = editor_dir.parent
        return project_dir / "data" / "ehr" / "main_take_settings.json"

    def _build_ui(self) -> None:
        """
        Buduje główne okno EHR na jednym wzorze siatki:

        | A A |  A = TOP
        | B C |  B = zegar / punkt, C = TAKE
        | D E |  D = podgląd i info, E = timeline
        | F F |  F = stopka / status

        Pozycję paneli ustawia wyłącznie _grid_main_layout().
        """
        self.main_grid = tk.Frame(self, bg=self.BG)
        self.main_grid.pack(fill="both", expand=True, padx=0, pady=0)
        self.main_grid.grid_columnconfigure(0, weight=0, minsize=LEFT_COLUMN_WIDTH)
        self.main_grid.grid_columnconfigure(1, weight=1)
        self.main_grid.grid_rowconfigure(0, weight=0)
        self.main_grid.grid_rowconfigure(1, weight=0)
        self.main_grid.grid_rowconfigure(2, weight=1)
        self.main_grid.grid_rowconfigure(3, weight=0)

        self.panel_a_top = tk.Frame(self.main_grid, bg=self.BG)
        tk.Label(self.panel_a_top, text="TARZAN — EHR", bg=self.BG, fg=self.FG, font=("Segoe UI Semibold", 16)).pack(side="left")
        tk.Button(self.panel_a_top, text="⚙", command=self._open_take_settings, bg="#39424E", fg=self.FG,
                  activebackground="#39424E", activeforeground=self.FG, relief="flat", bd=0, padx=10, pady=4,
                  font=("Segoe UI Symbol", 12), cursor="hand2").pack(side="left", padx=(8, 0))

        tk.Button(self.panel_a_top, text="CLEAR TAKE", command=self._clear_take_slots_click, bg="#DC2626", fg="white",
                  activebackground="#DC2626", activeforeground="white", relief="flat", bd=0, padx=10, pady=6,
                  font=("Segoe UI Semibold", 9), cursor="hand2").pack(side="right", padx=(0, 6))
        tk.Button(self.panel_a_top, text="SAVE TXT", command=self._save_take_txt_click, bg="#047857", fg="white",
                  activebackground="#047857", activeforeground="white", relief="flat", bd=0, padx=10, pady=6,
                  font=("Segoe UI Semibold", 9), cursor="hand2").pack(side="right", padx=(0, 6))
        tk.Button(self.panel_a_top, text="LOAD TXT", command=self._load_take_txt_click, bg="#7C3AED", fg="white",
                  activebackground="#7C3AED", activeforeground="white", relief="flat", bd=0, padx=10, pady=6,
                  font=("Segoe UI Semibold", 9), cursor="hand2").pack(side="right", padx=(0, 6))

        self.panel_b_clock = tk.Frame(self.main_grid, bg=self.BG, width=LEFT_COLUMN_WIDTH)
        self.panel_b_clock.grid_propagate(False)
        self.panel_b_clock.pack_propagate(False)

        self.take_panel = tk.Frame(self.main_grid, bg=self.BG)
        self.take_widget = TarzanTakeProtocolLightWidget(
            self.take_panel,
            status_sink=self._set_status,
            save_callback=self._save_take_slot,
            load_callback=self._load_take_from_path,
        )
        self.take_widget.pack(fill="x")

        self.panel_d_info = tk.Frame(self.main_grid, bg=self.BG, width=LEFT_COLUMN_WIDTH)
        self.panel_d_info.grid_propagate(False)
        self.panel_d_info.pack_propagate(False)
        self.left = self.panel_d_info

        self.panel_e_timeline = tk.Frame(self.main_grid, bg=self.BG)
        self.main_body = self.panel_e_timeline

        self._build_left_panel(self.panel_b_clock, self.panel_d_info)

        self.timeline_canvas = tk.Canvas(self.panel_e_timeline, bg="#1B2028", highlightthickness=0)
        self.timeline_canvas.pack(fill="both", expand=True)
        self.timeline_canvas.bind("<Configure>", self._on_canvas_configure)
        self.timeline_canvas.bind("<Button-1>", self._on_canvas_press)
        self.timeline_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.timeline_canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        self.timeline_canvas.bind("<Button-3>", self._on_canvas_right_click)

        self.status = tk.Label(self.main_grid, textvariable=self.status_var, bg=self.PANEL2, fg=self.FG, anchor="w",
                               padx=10, pady=8, font=("Segoe UI", 9))
        self.panel_f_status = self.status

        self._grid_main_layout()
        self._apply_visibility_settings()

    def _grid_main_layout(self) -> None:
        """
        Jedyny właściciel położenia głównych paneli EHR.

        | A A |
        | B C |
        | D E |
        | F F |
        """
        if self.main_grid is None:
            return

        if self.panel_a_top is not None:
            self.panel_a_top.grid(row=0, column=0, columnspan=2, sticky="ew")

        if self.panel_b_clock is not None:
            self.panel_b_clock.grid(row=1, column=0, sticky="nsew")

        if self.take_panel is not None:
            self.take_panel.grid(row=1, column=1, sticky="ew")

        if self.panel_d_info is not None:
            self.panel_d_info.grid(row=2, column=0, sticky="nsew")

        if self.panel_e_timeline is not None:
            self.panel_e_timeline.grid(row=2, column=1, sticky="nsew")

        if self.status is not None:
            if self.main_take_settings.show_status_bar:
                self.status.grid(row=3, column=0, columnspan=2, sticky="ew")
            else:
                self.status.grid_remove()

    def _build_left_panel(self, clock_parent: tk.Misc, info_parent: tk.Misc | None = None) -> None:
        if info_parent is None:
            info_parent = clock_parent
        self.active_axis_name_var = tk.StringVar(value=self._active_model().axis_def.axis_name)

        self.selected_point_time_label = tk.Label(
            clock_parent,
            textvariable=self.selected_point_time_var,
            bg=self.PANEL,
            fg="#22C55E",
            anchor="center",
            font=(self.clock_font_family, CLOCK_FONT_SIZE, "normal"),
            padx=0,
            pady=0
        )
        self.selected_point_time_label.pack(fill="both", expand=True, padx=0, pady=0)
        self.axis_info_label = tk.Label(info_parent, textvariable=self.axis_info_var, bg=self.PANEL, fg=self.MUTED,
                                        justify="left", anchor="w", font=("Consolas", 9), padx=10, pady=4)
        self.axis_info_label.pack(fill="x", pady=(0, 4))

        self.protocol_label_var = tk.StringVar(value=f"STEP MATRIX — {self._active_model().axis_def.axis_name}")
        self.protocol_label = tk.Label(info_parent, textvariable=self.protocol_label_var, bg=self.BG, fg=self.FG,
                                       anchor="w", font=("Segoe UI Semibold", 11))
        self.protocol_label.pack(fill="x", pady=(0, 2), padx=10)

        self.protocol_box = tk.Frame(info_parent, bg=self.PANEL)
        self.protocol_box.pack(fill="both", expand=True, pady=(0, 4))
        self.protocol_text = tk.Text(
            self.protocol_box,
            height=PROTOCOL_STREAM_TEXT_HEIGHT,
            width=PROTOCOL_STREAM_TEXT_WIDTH,
            bg=self.PANEL,
            fg=self.FG,
            insertbackground=self.FG,
            relief="flat",
            wrap="none",
            font=(self.protocol_desc_font_family, PROTOCOL_STREAM_DESC_FONT_SIZE),
        )
        self.protocol_text.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.protocol_text.tag_configure(
            "step_bits",
            foreground=PROTOCOL_STREAM_FG,
            font=(self.clock_font_family, PROTOCOL_STREAM_BITS_FONT_SIZE, "normal"),
        )
        self.protocol_text.configure(state="disabled")

    def _apply_visibility_settings(self) -> None:
        self.selected_point_time_label.pack_forget()
        self.axis_info_label.pack_forget()
        self.protocol_label.pack_forget()
        self.protocol_box.pack_forget()
        
        self.selected_point_time_label.pack(fill="both", expand=True, padx=0, pady=0)
        
        if self.main_take_settings.show_axis_metrics:
            self.axis_info_label.pack(fill="x", pady=(0, 12), padx=0)
        if self.main_take_settings.show_protocol_preview:
            self.protocol_label.pack(fill="x", pady=(0, 6), padx=10)
            self.protocol_box.pack(fill="both", expand=True, pady=(0, 10))
        
        self._update_selected_point_time_indicator()
        self._grid_main_layout()

    def _bump_axis_data_version(self, axis_index: int) -> None:
        self._axis_data_versions[axis_index] += 1


    def _mark_axis_metrics_dirty(self) -> None:
        self._axis_info_dirty = True

    def _mark_protocol_dirty(self) -> None:
        self._protocol_dirty = True

    def _set_active_axis(self, axis_index: int) -> bool:
        old_axis_index = self.active_axis_index
        changed = (axis_index != old_axis_index)
        self.active_axis_index = axis_index
        if changed:
            self._axis_selection_version += 1
            self._update_selected_point_time_indicator()
            self._mark_axis_metrics_dirty()
            self._mark_protocol_dirty()
            
            # Odśwież tylko starą i nową oś, aby zaktualizować podświetlenie (highlight)
            if old_axis_index is not None:
                self._request_main_canvas_redraw(only_axis_index=old_axis_index)
            self._request_main_canvas_redraw(only_axis_index=axis_index)

            # Powiadomienie Snajpera o zmianie aktywnej osi
            self._snajper_fire_ehr("ehr_active_axis_changed")

        if self.axis_detail_dialog is not None:
            try:
                if self.axis_detail_dialog.winfo_exists():
                    if self.axis_detail_dialog.axis_index != axis_index:
                        self.axis_detail_dialog.switch_axis(axis_index)
                else:
                    self.axis_detail_dialog = None
            except Exception:
                self.axis_detail_dialog = None

        return changed

    def _mark_axis_data_changed(self, axis_index: int, *, mark_protocol: bool = True, mark_axis_info: bool = True, notify_ui: bool = True, skip_kro: bool = False) -> None:
        self._bump_axis_data_version(axis_index)
        if axis_index == self.active_axis_index:
            if mark_protocol:
                self._mark_protocol_dirty()
            if mark_axis_info:
                self._mark_axis_metrics_dirty()
        
        # Kaskada KRO: jeśli ta oś jest źródłem, aktualizujemy zależne osie
        if not skip_kro:
            self.kro.on_axis_changed(axis_index)

        if notify_ui and self.take_widget is not None:
            try:
                self.take_widget.notify_active_take_modified()
            except Exception:
                pass

    def mark_axis_dirty(self, axis_index: int, status: str | None = None, redraw: bool = True) -> None:
        self.dirty_axis_indices.add(axis_index)
        self._mark_axis_data_changed(axis_index, mark_protocol=redraw, mark_axis_info=redraw, notify_ui=redraw)
        if redraw:
            self._request_main_canvas_redraw()
            self._set_status(status or f"Oś zmieniona lokalnie: {self.axis_models[axis_index].axis_def.axis_name}.")
        self._configure_after_id = None


    def sync_axis_from_dialog(self, axis_index: int, status: str | None = None) -> None:
        self.dirty_axis_indices.discard(axis_index)
        self._snajper_refresh_ehr_axis(
            axis_index,
            curve=True,
            metrics=True,
            step=True,
            status=status,
            notify_ui=True,
        )

    def _axis_index_from_ehr_target(self, target_name: str) -> int | None:
        match = re.search(r"axis_(\d+)_", str(target_name or ""))
        if not match:
            return None
        axis_index = int(match.group(1))
        if 0 <= axis_index < len(self.axis_models):
            return axis_index
        return None

    def _snajper_fire_ehr(self, logical_signal: str, policy: str = "IMMEDIATE") -> None:
        """Wymusza celowany strzał Snajpera mimo cache identycznych wartości.

        Polityka odświeżania należy do Snajpera. EHR zgłasza tylko typ
        strzału: IMMEDIATE/FINAL idą od razu, LIVE_MATRIX jest throttlowany
        centralnie w Snajperze.
        """
        self._ehr_axis_fire_seq += 1
        self.tarzan_snajper.fire_with_policy(
            logical_signal,
            self._ehr_axis_fire_seq,
            policy=policy,
            scheduler=self.after,
        )

    def _restore_selected_index_from_ref(self) -> None:
        ref = getattr(self, "selected_node_ref", None)
        if ref is None:
            return
        axis_idx = getattr(self, "drag_axis_index", None)
        if axis_idx is None:
            axis_idx = self.active_axis_index
        
        model = self.axis_models[axis_idx]
        try:
            self.selected_index = model.nodes.index(ref)
        except ValueError:
            self.selected_index = None
            self.selected_node_ref = None

    def _snajper_refresh_ehr_axis(
        self,
        axis_index: int,
        *,
        curve: bool = True,
        metrics: bool = True,
        step: bool = True,
        status: str | None = None,
        notify_ui: bool = True,
        change_active: bool = True,
        skip_kro: bool = False,
    ) -> None:
        """Centralne odświeżenie jednej osi EHR przez Snajpera.

        Zasada:
            jedna aktywna oś -> sygnał ehr_axis_N_* -> odświeżenie jej widoku.
        Snajper nie generuje STEP ani ADRR. Model osi pozostaje źródłem matrixa,
        markerów ADRR i Chaos Index.
        """
        if not (0 <= int(axis_index) < len(self.axis_models)):
            return

        axis_index = int(axis_index)
        self.dirty_axis_indices.discard(axis_index)

        if change_active:
            self._set_active_axis(axis_index)
            
        self._main_canvas_needs_redraw = False
        self._configure_after_id = None

        self._mark_axis_data_changed(
            axis_index,
            mark_protocol=step,
            mark_axis_info=metrics,
            notify_ui=notify_ui,
            skip_kro=skip_kro
        )

        if step or metrics:
            # Aktualizacja matrixa tej osi. To wywołanie pozostaje w modelu osi,
            # więc ADRR, markery i Chaos Index są liczone w dotychczasowej warstwie.
            try:
                self.axis_models[axis_index].build_step_rows(duration_ms=self.global_take_duration_ms)
            except AttributeError:
                self.axis_models[axis_index].protocol_rows(duration_ms=self.global_take_duration_ms)

        if curve:
            self._snajper_fire_ehr(f"ehr_axis_{axis_index}_curve")
        if metrics:
            self._snajper_fire_ehr(f"ehr_axis_{axis_index}_metrics")
        if step:
            self._snajper_fire_ehr(f"ehr_axis_{axis_index}_step_preview")

        if status is not None:
            self._set_status(status)

    def _snajper_draw_ehr_axis_curve(self, axis_index: int) -> None:
        self._draw_main_canvas(only_axis_index=axis_index)
        self._main_canvas_needs_redraw = False

    def _snajper_draw_ehr_axis_metrics(self, axis_index: int) -> None:
        if axis_index != self.active_axis_index:
            return
        self._refresh_axis_info(force=True)
        self._axis_info_dirty = False

    def _snajper_draw_ehr_axis_step_preview(self, axis_index: int) -> None:
        if axis_index != self.active_axis_index:
            return
        self._refresh_protocol_preview(force=True)
        self._protocol_dirty = False

    def _request_live_matrix_refresh(self, axis_index: int) -> None:
        """Zgłasza live matrix do Snajpera.

        Interwał i koaleskowanie nie są już lokalnym timerem EHR.
        Snajper trzyma politykę LIVE_MATRIX, a EHR dostarcza tylko zdarzenie.
        """
        if not (0 <= axis_index < len(self.axis_models)):
            return
        self._snajper_fire_ehr(f"ehr_axis_{axis_index}_live_matrix", policy="LIVE_MATRIX")

    @profile_method('EHR_MAIN._snajper_draw_ehr_axis_live_matrix')
    def _snajper_draw_ehr_axis_live_matrix(self, axis_index: int) -> None:
        if not (0 <= axis_index < len(self.axis_models)):
            return

        # Ustawienie osi jako aktywnej
        if axis_index != self.active_axis_index:
            self._set_active_axis(axis_index)

        # Inwalidacja cache modelu osi
        model = self.axis_models[axis_index]
        model._invalidate_cache()

        # Wyczyszczenie kluczy cache i odświeżenie UI w trybie FAST.
        # fast_mode=True = RAW STEP bez pełnego ADRR.
        self.protocol_cache_key = None
        self.axis_info_cache_key = None
        self._refresh_protocol_preview(force=True, fast_mode=True)
        self._refresh_axis_info(force=True, fast_mode=True)
        self._protocol_dirty = False
        self._axis_info_dirty = False

    @profile_method('EHR_MAIN._snajper_draw_ehr_axis_final_matrix')
    def _snajper_draw_ehr_axis_final_matrix(self, axis_index: int) -> None:
        if not (0 <= axis_index < len(self.axis_models)):
            return

        if axis_index != self.active_axis_index:
            self._set_active_axis(axis_index)

        # Finalny strzał po puszczeniu elementu: pełny ADRR już jest policzony
        # w modelu osi, a tutaj odświeżamy matrix/protocol i metryki bez fast_mode.
        self.protocol_cache_key = None
        self.axis_info_cache_key = None
        self._protocol_dirty = True
        self._axis_info_dirty = True
        self._refresh_protocol_preview(force=True, fast_mode=False)
        self._refresh_axis_info(force=True, fast_mode=False)
        self._protocol_dirty = False
        self._axis_info_dirty = False

    def _snajper_init_ehr_page(self, status: str = "Gotowy.") -> None:
        """Inicjalizacja widoku EHR przez Snajpera."""
        if status is not None:
            self._set_status(status)
        self._snajper_fire_ehr("ehr_init")

    def _snajper_refresh_ehr_page_full(self, status: str | None = None) -> None:
        """Pełne odświeżenie strony EHR przez Snajpera (Canvas, Info, Protocol)."""
        if status is not None:
            self._set_status(status)
        self._snajper_fire_ehr("ehr_page_full")

    @profile_method('EHR_MAIN._snajper_draw_ehr_page_full')
    def _snajper_draw_ehr_page_full(self) -> None:
        """Realizacja strzału Snajpera: pełne odświeżenie strony."""
        self.protocol_cache_key = None
        self.axis_info_cache_key = None
        self._main_canvas_needs_redraw = True
        self._axis_info_dirty = True
        self._protocol_dirty = True
        self._draw_main_canvas()
        self._refresh_axis_info(force=True)
        self._refresh_protocol_preview(force=True)
        self._main_canvas_needs_redraw = False
        self._axis_info_dirty = False
        self._protocol_dirty = False

    def _snajper_draw_ehr_page_init(self) -> None:
        """Realizacja strzału Snajpera: inicjalizacja strony."""
        self._snajper_draw_ehr_page_full()

    def _refresh_axis_dialog_if_needed(self, axis_index: int) -> None:
        """Odświeża otwarte okno lupy, jeśli dotyczy tej samej osi."""
        if self.axis_detail_dialog and self.axis_detail_dialog.winfo_exists() and self.axis_detail_dialog.axis_index == axis_index:
            self.axis_detail_dialog._curve_needs_redraw = True
            self.axis_detail_dialog._step_needs_redraw = True
            self.axis_detail_dialog._metrics_cache_key = None
            self.axis_detail_dialog._metrics_cache_text = ""
            self.axis_detail_dialog._nodes_dirty = True
            self.axis_detail_dialog._snajper_refresh_targets(curve=True, step=True, metrics=True)

    def _open_or_switch_axis_detail(self, axis_index: int) -> None:
        """Otwiera lub przełącza istniejące okno szczegółowe osi (Lupa)."""
        if self.axis_models[axis_index].is_release_axis:
            # Oś DRON/release nie ma okna szczegółowego
            return

        self._set_active_axis(axis_index)

        if self.axis_detail_dialog is None or not self.axis_detail_dialog.winfo_exists():
            self.axis_detail_dialog = AxisSettingsDialog(self, axis_index)

        self.axis_detail_dialog.lift()
        self.axis_detail_dialog.focus_force()

    def _request_dialog_axis_live_preview(self, axis_index: int) -> None:
        """Throttlowane odświeżenie MAIN EHR podczas ruchu operatora.

        Ten tor zostaje szybki i używa fast_mode=True, więc pokazuje RAW STEP
        bez pełnego ADRR. Pełna HARMONIA RUCHU idzie dopiero przez
        _request_dialog_axis_final_preview().
        """
        # Wykorzystujemy istniejący mechanizm live matrix
        self._request_live_matrix_refresh(axis_index)
        # Dodatkowo krzywa
        self._snajper_fire_ehr(f"ehr_axis_{axis_index}_curve")

    def _request_dialog_axis_final_preview(self, axis_index: int) -> None:
        """Finalne odświeżenie MAIN EHR po puszczeniu elementu w oknie osi.

        Tu nie używamy 100 ms live matrix. Po pełnym ADRR odświeżamy aktywną
        oś w trybie finalnym: protocol preview/matrix i metryki z fast_mode=False.
        """
        if not (0 <= axis_index < len(self.axis_models)):
            return
        if axis_index != self.active_axis_index:
            self._set_active_axis(axis_index)

        self._snajper_fire_ehr(f"ehr_axis_{axis_index}_curve", policy="FINAL")
        self._snajper_fire_ehr(f"ehr_axis_{axis_index}_final_matrix", policy="FINAL")

    def _open_take_settings(self) -> None:
        dlg = MainTakeSettingsDialog(
            self,
            copy.deepcopy(self.main_take_settings),
            save_callback=self._save_take_settings,
            apply_callback=self._apply_take_settings,
        )
        dlg.focus_force()

    def _apply_take_settings(self, settings: MainTakeSettings) -> None:
        self.main_take_settings = settings
        self.kro_enabled_var.set(getattr(settings, 'kro_enabled', True))
        new_take_ms = settings.take_duration_ms()
        self.global_take_duration_ms = new_take_ms
        for axis in self.axis_models:
            axis.set_axis_take_duration_ms(new_take_ms)
            # set_axis_take_duration_ms wywołuje sort_and_fix_nodes() wewnętrznie
        self._apply_visibility_settings()
        self.protocol_cache_key = None
        self.axis_info_cache_key = None
        self._main_canvas_needs_redraw = True
        self._mark_protocol_dirty()
        self._mark_axis_metrics_dirty()
        self._configure_after_id = None

        self._snajper_refresh_ehr_page_full(
            status="Zastosowano ustawienia MAIN TAKE.",
        )

        if self.axis_detail_dialog is not None and self.axis_detail_dialog.winfo_exists():
            self.axis_detail_dialog._curve_needs_redraw = True
            self.axis_detail_dialog._step_needs_redraw = True
            self.axis_detail_dialog._metrics_cache_key = None
            self.axis_detail_dialog._metrics_cache_text = ""
            self.axis_detail_dialog._snajper_refresh_targets(curve=True, step=True, metrics=True)

    def _save_take_settings(self, settings: MainTakeSettings) -> None:
        self._apply_take_settings(settings)
        settings.save(self.settings_path)
        self.status_var.set(f"Zapisano ustawienia MAIN TAKE: {self.settings_path}")

    def _refresh_axis_context(
        self,
        *,
        status: str | None = None,
        refresh_axis_info: bool = False,
        refresh_protocol: bool = False,
        force_axis_info: bool = False,
        force_protocol: bool = False,
        redraw_canvas: bool = True,
    ) -> None:
        if redraw_canvas:
            self._request_main_canvas_redraw()
        if refresh_axis_info and (force_axis_info or self._axis_info_dirty):
            self._refresh_axis_info(force=force_axis_info)
        if refresh_protocol and (force_protocol or self._protocol_dirty or self.protocol_cache_key is None):
            self._refresh_protocol_preview(force=force_protocol)
            self._protocol_dirty = False
        self._set_status(status)

    def _scale_row(self, parent, label, var, from_, to, resolution):
        wrap = tk.Frame(parent, bg=self.PANEL)
        wrap.pack(fill="x", padx=10, pady=6)
        tk.Label(wrap, text=label, bg=self.PANEL, fg=self.FG, anchor="w", font=("Segoe UI Semibold", 9)).pack(fill="x")
        scale = tk.Scale(wrap, variable=var, from_=from_, to=to, resolution=resolution, orient="horizontal",
                         command=lambda _v: self._request_main_canvas_redraw(), bg=self.PANEL, fg=self.FG,
                         troughcolor="#39424E", highlightthickness=0, bd=0, length=280)
        scale.pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=10, pady=6,
                         font=("Segoe UI Semibold", 9), cursor="hand2")

    def _small_btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", bd=0, padx=8, pady=4,
                         font=("Segoe UI Semibold", 8), cursor="hand2")

    def _active_model(self) -> AxisCurveModel:
        return self.axis_models[self.active_axis_index]

    def _curve_area_rect(self) -> tuple[int, int, int, int]:
        w = max(300, int(self.timeline_canvas.winfo_width() or 1200))
        h = max(300, int(self.timeline_canvas.winfo_height() or 820))
        return 290, 24, w - 28, h - 38

    def _time_to_x(self, t_ms: int, left: int, right: int) -> float:
        span = max(1, self.global_take_duration_ms)
        return left + (t_ms / span) * (right - left)

    def _x_to_time(self, x: float, left: int, right: int) -> int:
        rel = (x - left) / max(1.0, (right - left))
        rel = max(0.0, min(1.0, rel))
        step = self._active_model().sample_ms
        return int(round((rel * self.global_take_duration_ms) / step) * step)

    def _logical_y_to_canvas(self, model: AxisCurveModel, y: float, top: int, bottom: int) -> float:
        operator_range = max(200.0, float(model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(model.config.y_limit))
        operator_y = float(y) * (operator_range / logical_limit)
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(model.sandbox.top_bottom_margin)
        return mid - (operator_y / operator_range) * usable

    def _canvas_to_logical_y(self, model: AxisCurveModel, py: float, top: int, bottom: int, apply_snap: bool = True) -> float:
        operator_range = max(200.0, float(model.sandbox.display_y_scale))
        logical_limit = max(1.0, float(model.config.y_limit))
        mid = (top + bottom) / 2.0
        usable = (bottom - top) / 2.0 - float(model.sandbox.top_bottom_margin)
        operator_y = ((mid - py) / max(1.0, usable)) * operator_range
        logical_y = operator_y * (logical_limit / operator_range)
        logical_y = max(-logical_limit, min(logical_limit, logical_y))
        if apply_snap:
            return model.apply_zero_snap(self.main_take_settings, logical_y)
        # Podczas drag używamy _apply_drag_zero_snap w metodach _on_canvas_drag
        return logical_y

    def _drag_delta_to_logical_y(self, model: AxisCurveModel, delta_py: float, top: int, bottom: int) -> float:
        logical_limit = max(1.0, float(model.config.y_limit))
        usable = (bottom - top) / 2.0 - float(model.sandbox.top_bottom_margin)
        precision = max(0.05, float(model.sandbox.mouse_y_precision))
        logical_per_px = logical_limit / max(1.0, usable)
        return float(delta_py) * logical_per_px * precision

    def _axis_index_from_point(self, x: float, y: float) -> int | None:
        for axis_index, rect in self.axis_rects.items():
            if rect.contains(x, y):
                return axis_index
        return None

    def _gear_axis_from_point(self, x: float, y: float) -> int | None:
        for axis_index, rect in self.gear_rects.items():
            if rect.contains(x, y):
                return axis_index
        return None

    def _wave_axis_from_point(self, x: float, y: float) -> int | None:
        for axis_index, rect in self.wave_rects.items():
            if rect.contains(x, y):
                return axis_index
        return None

    def _smooth_axis_idx(self, axis_index: int) -> None:
        model = self.axis_models[axis_index]
        strength = float(getattr(self.main_take_settings, "smooth_strength_default", 0.35))
        passes = int(getattr(self.main_take_settings, "smooth_passes_default", 2))
        model.smooth_all(strength=strength, passes=passes)

        # Inwalidacja cache przed sygnałem Snajpera
        model._invalidate_cache()
        
        status = f"Wygładzono przebieg osi: {model.axis_def.axis_name}. siła={strength:.2f} przejścia={passes}."
        self._snajper_refresh_ehr_axis(axis_index, curve=True, metrics=True, step=True, status=status)

        self._refresh_axis_dialog_if_needed(axis_index)

    def _schedule_configure_refresh(self) -> None:
        if self._configure_after_id is not None:
            try:
                self.after_cancel(self._configure_after_id)
            except Exception:
                pass
        self._configure_after_id = self.after(40, self._flush_configure_refresh)

    def _flush_configure_refresh(self) -> None:
        self._configure_after_id = None
        self._request_main_canvas_redraw()

    def _hit_node(self, axis_index: int, x: float, y: float) -> int | None:
        if axis_index not in self.axis_rects:
            return None
        rect = self.axis_rects[axis_index]
        model = self.axis_models[axis_index]
        if model.is_release_axis:
            return None
        radius = model.step_tuning.node_hit_radius_px
        for i, n in enumerate(model.nodes):
            px = self._time_to_x(n.time_ms, rect.left, rect.right)
            py = self._logical_y_to_canvas(model, n.y, rect.top, rect.bottom)
            if abs(px - x) <= radius and abs(py - y) <= radius:
                return i
        return None

    def _hit_release(self, axis_index: int, x: float, y: float) -> bool:
        if axis_index not in self.axis_rects:
            return False
        model = self.axis_models[axis_index]
        if not model.is_release_axis or model.release_time_ms is None:
            return False
        rect = self.axis_rects[axis_index]
        px = self._time_to_x(model.release_time_ms, rect.left, rect.right)
        py = (rect.top + rect.bottom) / 2.0
        return abs(px - x) <= 14 and abs(py - y) <= 14

    def _axis_layout(self) -> list[tuple[int, AxisViewportRect]]:
        left, top, right, bottom = self._curve_area_rect()
        total_h = bottom - top
        gap = 10
        n = max(1, len(self.axis_models))
        band_h = max(72, int((total_h - gap * (n - 1)) / n))
        layout = []
        cur_top = top
        for axis_index in range(n):
            rect = AxisViewportRect(left, cur_top, right, cur_top + band_h)
            layout.append((axis_index, rect))
            cur_top += band_h + gap
        return layout

    def _hex_to_rgb(self, color: str) -> tuple[int, int, int]:
        color = (color or "#000000").strip()
        if color.startswith("#") and len(color) == 7:
            try:
                return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            except ValueError:
                return 0, 0, 0
        return 0, 0, 0

    def _blend_hex(self, base: str, overlay: str, strength_percent: int) -> str:
        strength = max(0.0, min(1.0, float(strength_percent) / 100.0))
        br, bg, bb = self._hex_to_rgb(base)
        or_, og, ob = self._hex_to_rgb(overlay)
        rr = int(round(br * (1.0 - strength) + or_ * strength))
        rg = int(round(bg * (1.0 - strength) + og * strength))
        rb = int(round(bb * (1.0 - strength) + ob * strength))
        return f"#{rr:02X}{rg:02X}{rb:02X}"


    def _sample_original_curve(self, model: AxisCurveModel) -> list[tuple[int, float]]:
        """
        Zwraca próbki ghost/original bez naruszania bieżącego stanu modelu.
        """
        original_nodes = getattr(model, "original_nodes", None)
        if not original_nodes or len(original_nodes) < 2:
            return []

        # Używamy cache'u modelu dla original_nodes, jeśli to możliwe (specyficzny klucz)
        cache_key = ("ghost", self._main_curve_sample_count(), self.global_take_duration_ms)
        if hasattr(model, "_ghost_cache") and cache_key in model._ghost_cache:
            return list(model._ghost_cache[cache_key])
        
        if not hasattr(model, "_ghost_cache"):
            model._ghost_cache = {}

        # Oszczędna symulacja stanu modelu dla potrzeb samplowania original_nodes
        real_nodes = model.nodes
        try:
            model.nodes = original_nodes
            # Sample curve wygeneruje wynik i zapisze go w swoim cache pod kluczem (steps, duration)
            # ale my chcemy mieć to oddzielnie, by nie czyścić cache głównego
            res = model.sample_curve(self._main_curve_sample_count(), duration_ms=self.global_take_duration_ms)
            model._ghost_cache[cache_key] = tuple(res)
            return res
        finally:
            model.nodes = real_nodes

    def _main_curve_sample_count(self) -> int:
        if self.drag_mode is not None and self.drag_axis_index is not None:
            return self.MAIN_CURVE_SAMPLES_DRAG
        return self.MAIN_CURVE_SAMPLES_IDLE

    def _axis_curve_color(self, model: AxisCurveModel) -> str:
        return self.main_take_settings.axis_color(model.axis_def.axis_id, model.axis_def.color)

    def _axis_panel_fill(self, axis_color: str, is_active: bool, is_axis_enabled: bool = True) -> str:
        base = "#232A33" if is_active else "#1C2128"
        if not is_axis_enabled:
            base = "#14181E" # Jeszcze ciemniejszy dla nieaktywnej osi
        
        if not self.main_take_settings.show_axis_background_tint:
            return base
        strength = self.main_take_settings.axis_background_strength_percent
        if is_active:
            strength = min(40, strength + int(getattr(self.main_take_settings, "active_axis_emphasis_percent", 10)))
        
        if not is_axis_enabled:
            strength = max(5, strength // 2) # Słabszy tint dla nieaktywnej osi

        return self._blend_hex(base, axis_color, strength)

    def _get_axis_icon(self, axis_name: str, height: int, active: bool = True) -> ImageTk.PhotoImage | None:
        cache_key = (axis_name, height, active)
        if cache_key in self._axis_icons_cache:
            return self._axis_icons_cache[cache_key]

        icon_filename = self._axis_icon_mapping.get(axis_name)
        if not icon_filename:
            return None
        
        if not active:
            icon_filename = icon_filename.replace("_active.png", "_inactive.png")

        icon_path = PROJECT_DIR / "img" / "axes" / icon_filename
        if not icon_path.exists():
            return None

        try:
            img = Image.open(icon_path)
            # Skalowanie z zachowaniem proporcji do podanej wysokości
            w, h = img.size
            if h > 0:
                new_w = int(w * (height / h))
                img = img.resize((new_w, height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self._axis_icons_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    @profile_method('EHR_MAIN._draw_main_canvas')
    def _draw_main_canvas(self, only_axis_index: int | None = None) -> None:
        if not hasattr(self, "_last_canvas_draw_key"):
            self._last_canvas_draw_key = None

        left, top, right, bottom = self._curve_area_rect()
        current_draw_key = (
            self.active_axis_index,
            self.global_take_duration_ms,
            tuple(self._axis_data_versions),
            left, top, right, bottom,
            self.drag_mode,
            self.drag_axis_index,
            self.selected_index,
            # Dodaj istotne ustawienia wizualne do klucza cache
            self.main_take_settings.show_minute_grid,
            self.main_take_settings.show_axis_labels,
            self.main_take_settings.show_axis_gears,
            self.main_take_settings.show_axis_activity_markers,
            self.kro_enabled_var.get() # Dodano KRO ON/OFF do klucza
        )

        if only_axis_index is None:
            if current_draw_key == self._last_canvas_draw_key and not self._main_canvas_needs_redraw:
                # Jeśli wymuszono resampling po SAVE, nie przerywaj rysowania mimo braku zmian w kluczu
                if not getattr(self, "_force_curve_resample_after_save", False):
                    return
            self._last_canvas_draw_key = current_draw_key

        c = self.timeline_canvas
        if only_axis_index is None:
            c.delete("all")
            self.axis_rects.clear()
            self.gear_rects.clear()
            self.wave_rects.clear()
            # left, top, right, bottom już mamy z obliczeń klucza
            c.create_rectangle(left, top, right, bottom, fill="#1B2028", outline="", tags="bg")

            total_minutes = max(1, int(self.global_take_duration_ms // 60000))
            if self.main_take_settings.show_minute_grid:
                for minute in range(0, total_minutes + 1):
                    t_ms = minute * 60000
                    if t_ms > self.global_take_duration_ms:
                        continue
                    px = self._time_to_x(t_ms, left, right)
                    c.create_line(px, top, px, bottom, fill="#36414C", dash=(2, 6), tags="grid")
        else:
            c.delete(f"axis_{only_axis_index}")
            c.delete("kro")
            total_minutes = max(1, int(self.global_take_duration_ms // 60000))

        for axis_index, rect in self._axis_layout():
            if only_axis_index is not None and axis_index != only_axis_index:
                continue

            self.axis_rects[axis_index] = rect
            model = self.axis_models[axis_index]
            is_active = axis_index == self.active_axis_index
            is_ax_enabled = self._is_axis_active(axis_index)
            axis_color = self._axis_curve_color(model)
            panel_fill = self._axis_panel_fill(axis_color, is_active, is_ax_enabled)
            
            # Tagowanie wszystkich elementów danej osi
            axis_tag = f"axis_{axis_index}"

            c.create_rectangle(rect.left, rect.top, rect.right, rect.bottom, fill=panel_fill, outline="", tags=(axis_tag, "panel"))
            if is_active:
                c.create_line(rect.left, rect.top + 2, rect.left, rect.bottom - 2, fill=axis_color, width=max(1, int(getattr(self.main_take_settings, "active_axis_border_width", 3))), tags=(axis_tag, "border"))

            mid = (rect.top + rect.bottom) / 2.0
            c.create_line(rect.left, mid, rect.right, mid,
                          fill=self.main_take_settings.zero_line_color,
                          width=self.main_take_settings.zero_line_width, tags=(axis_tag, "zero_line"))

            if not model.is_release_axis:
                if self.main_take_settings.show_axis_gears:
                    gear_x = rect.left + GEAR_OFFSET_X
                    gear_y = rect.bottom + GEAR_OFFSET_Y
                    gear = GearRect(gear_x - 13, gear_y - 8, gear_x + 13, gear_y + 8)
                    self.gear_rects[axis_index] = gear
                    c.create_text(gear_x, gear_y, text="⚙", fill="#FFFFFF",
                                  font=("Segoe UI Symbol", CONTROL_FONT_SIZE), tags=("axis_controls", "gear", f"overlay_{axis_index}", axis_tag))
                
                smooth_x = rect.left + SMOOTH_OFFSET_X
                smooth_y = rect.bottom + SMOOTH_OFFSET_Y
                wave = WaveRect(smooth_x - 13, smooth_y - 8, smooth_x + 13, smooth_y + 8)
                self.wave_rects[axis_index] = wave
                c.create_text(smooth_x, smooth_y, text="≈", fill="#FFFFFF",
                              font=("Segoe UI Semibold", CONTROL_FONT_SIZE), tags=("axis_controls", "smooth", f"overlay_{axis_index}", axis_tag))

            if self.main_take_settings.show_axis_labels:
                icon_h = int((rect.bottom - rect.top) * 0.8)
                is_ax_active = self._is_axis_active(axis_index)
                icon = self._get_axis_icon(model.axis_def.axis_name, icon_h, active=is_ax_active)
                if icon:
                    c.create_image(rect.left - 12, mid, image=icon, anchor="e", tags=(axis_tag, "icon", "activity_btn"))
                else:
                    c.create_text(rect.left - 12, mid, text=model.axis_def.axis_name, fill=self.FG, anchor="e",
                                  font=("Segoe UI", 9, "bold"), tags=(axis_tag, "label", "activity_btn"))

            # Podnieś ikony ustawień nad ikonę osi
            c.tag_raise("axis_controls")
            c.tag_raise(f"overlay_{axis_index}")

            if self.main_take_settings.show_minute_grid:
                for minute in range(0, total_minutes + 1):
                    t_ms = minute * 60000
                    if t_ms > self.global_take_duration_ms:
                        continue
                    px = self._time_to_x(t_ms, rect.left, rect.right)
                    c.create_line(px, rect.top, px, rect.bottom, fill="#303842", dash=(2, 6), tags=(axis_tag, "minute_grid"))

            if not model.is_release_axis:
                if self.main_take_settings.show_axis_activity_markers and len(model.nodes) >= 4:
                    first_edit = model.nodes[1]
                    last_edit = model.nodes[-2]
                    for node in (first_edit, last_edit):
                        mx = self._time_to_x(node.time_ms, rect.left, rect.right)
                        c.create_line(mx, rect.top + 4, mx, rect.bottom - 4, fill=axis_color, width=1, dash=(3, 5), tags=(axis_tag, "marker"))

                ghost_settings = self.main_take_settings
                if getattr(ghost_settings, "show_ghost_line", True):
                    ghost_samples = self._sample_original_curve(model)
                    ghost_pts = []
                    for t_ms, y in ghost_samples:
                        ghost_pts.extend([self._time_to_x(t_ms, rect.left, rect.right),
                                          self._logical_y_to_canvas(model, y, rect.top, rect.bottom)])
                    if len(ghost_pts) >= 4:
                        c.create_line(
                            *ghost_pts,
                            fill=getattr(ghost_settings, "ghost_line_color", "#EAB308"),
                            width=int(getattr(ghost_settings, "ghost_line_width", 1)),
                            dash=(
                                int(getattr(ghost_settings, "ghost_line_dash_on", 4)),
                                int(getattr(ghost_settings, "ghost_line_dash_off", 4)),
                            ),
                            smooth=False,
                            tags=(axis_tag, "ghost")
                        )

                samples = model.sample_curve(self._main_curve_sample_count(), duration_ms=self.global_take_duration_ms)
                pts = []
                for t_ms, y in samples:
                    pts.extend([self._time_to_x(t_ms, rect.left, rect.right),
                                self._logical_y_to_canvas(model, y, rect.top, rect.bottom)])
                if len(pts) >= 4:
                    curve_color = axis_color if is_ax_enabled else self._blend_hex(axis_color, "#000000", 60)
                    c.create_line(*pts, fill=curve_color,
                                  width=self.main_take_settings.active_curve_line_width if is_active else self.main_take_settings.curve_line_width,
                                  smooth=False, tags=(axis_tag, "curve"))

                node_r = max(4, min(9, model.step_tuning.node_hit_radius_px // 2))
                square_half = max(5, node_r)
                node_outline = "black" if is_ax_enabled else "#4B5563"
                for i, n in enumerate(model.nodes):
                    px = self._time_to_x(n.time_ms, rect.left, rect.right)
                    py = self._logical_y_to_canvas(model, n.y, rect.top, rect.bottom)
                    fill = self.NODE_SEL if (axis_index == self.drag_axis_index and i == self.selected_index) else self.NODE
                    if not is_ax_enabled:
                        fill = self._blend_hex(fill, "#000000", 50)

                    if i == 0 or i == len(model.nodes) - 1:
                        if self.main_take_settings.show_start_stop_squares:
                            c.create_rectangle(px - square_half, py - square_half, px + square_half, py + square_half, fill=self.main_take_settings.zero_line_color if is_ax_enabled else "#374151", outline=node_outline, tags=(axis_tag, "node_square"))
                        else:
                            c.create_oval(px - node_r, py - node_r, px + node_r, py + node_r, fill="#D6EAF8" if is_ax_enabled else "#4B5563", outline=node_outline, tags=(axis_tag, "node_oval"))
                    else:
                        # Podświetlenie punktu jeśli jest przyciągnięty do ghosta (Main Canvas)
                        node_fill = fill
                        is_snapped = False
                        if axis_index == self.drag_axis_index:
                            if self.drag_mode == "node" and i == self.selected_index:
                                if getattr(self, "is_ghost_snapped", False) or getattr(self, "is_zero_snapped", False) or (self._drag_zero_snap_locked and n.y == 0.0):
                                    is_snapped = True
                            elif self.drag_mode == "pan":
                                if getattr(self, "is_ghost_snapped", False):
                                    is_snapped = True
                        
                        if is_snapped:
                            node_fill = "#22C55E" # Zielony (Emerald-500)
                        
                        c.create_oval(px - node_r, py - node_r, px + node_r, py + node_r, fill=node_fill, outline=node_outline, tags=(axis_tag, "node_oval"))

            if model.is_release_axis and model.release_time_ms is not None:
                inner_top = rect.top + max(12, (rect.bottom - rect.top) // 3)
                inner_bottom = rect.bottom - max(12, (rect.bottom - rect.top) // 3)
                inner_mid = (inner_top + inner_bottom) / 2.0
                c.create_rectangle(rect.left, inner_top, rect.right, inner_bottom, fill=panel_fill, outline="", tags=(axis_tag, "release_panel"))
                c.create_line(rect.left, inner_mid, rect.right, inner_mid,
                              fill=self.main_take_settings.zero_line_color,
                              width=self.main_take_settings.zero_line_width, tags=(axis_tag, "release_zero"))
                rx = self._time_to_x(model.release_time_ms, rect.left, rect.right)
                ry = inner_mid
                r = 7
                fill = "#F59E0B" if self.drag_mode == 'release' and axis_index == self.drag_axis_index else axis_color
                if not is_ax_enabled:
                    fill = self._blend_hex(fill, "#000000", 50)
                c.create_polygon(rx, ry - r, rx + r, ry, rx, ry + r, rx - r, ry, fill=fill, outline='black' if is_ax_enabled else '#4B5563', tags=(axis_tag, "release_diamond"))
                text_color = axis_color if is_ax_enabled else self._blend_hex(axis_color, "#000000", 40)
                c.create_text(rx + 14, ry - 10, text='RELEASE', fill=text_color, anchor='w', font=('Segoe UI', 8, 'bold'), tags=(axis_tag, "release_text"))
                
                # Pionowa linia dla punktu RELEASE (jak show_axis_activity_markers)
                c.create_line(rx, rect.top + 4, rx, rect.bottom - 4, fill=axis_color, width=1, dash=(3, 5), tags=(axis_tag, "release_marker"))

        if only_axis_index is None:
            for minute in range(0, total_minutes + 1):
                t_ms = minute * 60000
                if t_ms > self.global_take_duration_ms:
                    continue
                px = self._time_to_x(t_ms, left, right)
                c.create_text(px, bottom + 8, text=f"{minute}m", fill=self.MUTED, anchor="n", font=("Consolas", 8), tags="time_label")

        if self.kro_enabled_var.get():
            self.kro.draw(c)
            c.tag_raise("kro")

    def _on_canvas_configure(self, _event=None) -> None:
        self._schedule_configure_refresh()

    @profile_method('EHR_MAIN._refresh_axis_info')
    def _get_ghost_y_at_time(self, t_ms: int) -> float | None:
        """
        Zwraca wartość y ghosta (original_nodes) dla czasu t_ms na podstawie cachowanych próbek.
        """
        if not hasattr(self, "_ghost_samples_cache") or not self._ghost_samples_cache:
            return None
        
        samples = self._ghost_samples_cache
        if t_ms <= samples[0][0]: return samples[0][1]
        if t_ms >= samples[-1][0]: return samples[-1][1]
        
        import bisect
        idx = bisect.bisect_left(samples, (t_ms, -1e9))
        if idx == 0: return samples[0][1]
        if idx >= len(samples): return samples[-1][1]
        
        t0, y0 = samples[idx-1]
        t1, y1 = samples[idx]
        if t1 == t0: return y0
        
        frac = (t_ms - t0) / (t1 - t0)
        return y0 + frac * (y1 - y0)

    def _format_take_time(self, t_ms: int | None) -> str:
        if t_ms is None:
            return "--:--"
        minutes = int(t_ms // 60000)
        seconds = int((t_ms % 60000) // 1000)
        return f"{minutes:02d}:{seconds:02d}"

    def _update_selected_point_time_indicator(self, axis_index=None, node_index=None, time_ms=None):
        if time_ms is None:
            if axis_index is None:
                axis_index = self.active_axis_index
            
            if node_index is None:
                node_index = self.selected_index
                
            model = self.axis_models[axis_index]
            
            # Obsługa DRON (release axis)
            if model.is_release_axis:
                time_ms = model.release_time_ms
            elif node_index is not None and 0 <= node_index < len(model.nodes):
                time_ms = model.nodes[node_index].time_ms
            else:
                # Spróbujmy pokazać pierwszy roboczy punkt (index 1)
                if len(model.nodes) > 1:
                    time_ms = model.nodes[1].time_ms
                else:
                    self.selected_point_time_var.set("--:--")
                    return

        self.selected_point_time_var.set(self._format_take_time(int(time_ms) if time_ms is not None else None))

    def _refresh_axis_info(self, force: bool = False, fast_mode: bool = False) -> None:
        model = self._active_model()
        self.active_axis_name_var.set(model.axis_def.axis_name)
        if not self.main_take_settings.show_axis_metrics:
            self.axis_info_var.set("")
            self._axis_info_dirty = False
            return
        cache_key = (
            self.active_axis_index,
            self._axis_selection_version,
            self._axis_data_versions[self.active_axis_index],
            self.global_take_duration_ms,
            fast_mode,
            model.step_tuning.dead_zone_y,
            model.step_tuning.input_max_y,
            model.step_tuning.input_gamma,
            model.step_tuning.step_rate_gain,
            model.step_tuning.step_rate_max_percent,
            model.step_tuning.preview_rate_smoothing,
        )
        if force or self._axis_info_dirty or cache_key != self.axis_info_cache_key:
            self.axis_info_cache_text = model.metrics_summary(duration_ms=self.global_take_duration_ms, fast_mode=fast_mode)
            self.axis_info_cache_key = cache_key
            self._axis_info_dirty = False
        
        # Unikamy zbędnego wywołania .set() jeśli tekst się nie zmienił
        if self.axis_info_var.get() != self.axis_info_cache_text:
            self.axis_info_var.set(self.axis_info_cache_text)

    @profile_method('EHR_MAIN._refresh_protocol_preview')
    def _refresh_protocol_preview(self, force: bool = False, fast_mode: bool = False) -> None:
        if not self.main_take_settings.show_protocol_preview:
            return
        model = self._active_model()
        cache_key = (
            self.active_axis_index,
            self._axis_selection_version,
            self._axis_data_versions[self.active_axis_index],
            self.global_take_duration_ms,
            fast_mode,
        )
        
        title = f"STEP MATRIX — {model.axis_def.axis_name}"
        if self.protocol_label_var.get() != title:
            self.protocol_label_var.set(title)

        if (not force) and cache_key == self.protocol_cache_key:
            return

        rows = model.protocol_rows(duration_ms=self.global_take_duration_ms, fast_mode=fast_mode)
        if not rows:
            text = "Brak danych protokołu.\n"
        else:
            first_active_idx = 0
            for idx, row in enumerate(rows):
                if int(row['step']) == 1 or str(row['event']).strip():
                    first_active_idx = idx
                    break
            pre_roll = PROTOCOL_STREAM_PRE_ROLL_ROWS
            sample_ms = max(1, int(getattr(model, "sample_ms", 10) or 10))
            # Ilość próbek podglądu wynika z czasu MAIN TAKE.
            # Przykład: 3 min = 180000 ms / 10 ms = 18000 próbek.
            main_window = max(1, int(round(self.global_take_duration_ms / sample_ms)))
            start_idx = max(0, first_active_idx - pre_roll)
            end_idx = min(len(rows), start_idx + main_window)
            window_rows = rows[start_idx:end_idx]

            bit_chunks = []
            chunk_size = PROTOCOL_STREAM_CHUNK_SIZE
            for i in range(0, len(window_rows), chunk_size):
                chunk_rows = window_rows[i:i + chunk_size]
                chunk_bits = ''.join(str(int(r['step'])) for r in chunk_rows)
                chunk_time = chunk_rows[0]['time_ms'] if chunk_rows else 0
                bit_chunks.append(f"{chunk_time:7d} ms | {chunk_bits}\n")

            text = ''.join(bit_chunks)

        self.protocol_cache_key = cache_key
        self.protocol_cache_text = text
        self.protocol_text.configure(state='normal')
        self.protocol_text.delete('1.0', 'end')
        self.protocol_text.insert('1.0', text)
        self.protocol_text.tag_remove('step_bits', '1.0', 'end')
        for match in re.finditer(r'^\s*\d+\s+ms \| ([01]+)$', text, flags=re.MULTILINE):
            self.protocol_text.tag_add(
                'step_bits',
                f"1.0+{match.start(1)}c",
                f"1.0+{match.end(1)}c",
            )
        self.protocol_text.configure(state='disabled')

    def _set_status(self, status: str | None = None) -> None:
        self.status_var.set(status if status is not None else "EHR gotowy.")

    def _request_main_canvas_redraw(self, only_axis_index: int | None = None) -> None:
        if only_axis_index is not None:
            self._draw_main_canvas(only_axis_index=only_axis_index)
            return

        self._main_canvas_needs_redraw = True
        if self._main_canvas_redraw_after_id is not None:
            return
        self._main_canvas_redraw_after_id = self.after(16, self._flush_main_canvas_redraw)

    def _flush_main_canvas_redraw(self) -> None:
        self._main_canvas_redraw_after_id = None
        if self._main_canvas_needs_redraw:
            self._draw_main_canvas()
            self._main_canvas_needs_redraw = False

    def _apply_drag_zero_snap(self, model: AxisCurveModel, value: float) -> float:
        value = model.clamp_y(value)
        if not getattr(self.main_take_settings, "snap_to_zero_enabled", False):
            self._drag_zero_snap_locked = False
            return value
        threshold = max(0.0, float(getattr(self.main_take_settings, "snap_to_zero_threshold", 0.0)))
        enter_threshold = threshold * 0.6
        release_threshold = max(enter_threshold, threshold)
        if self._drag_zero_snap_locked:
            if abs(value) <= release_threshold:
                return 0.0
            self._drag_zero_snap_locked = False
            return value
        if abs(value) <= enter_threshold:
            self._drag_zero_snap_locked = True
            return 0.0
        return value

    def _refresh_light_ui(self, status: str | None = None, refresh_axis_info: bool = False, refresh_protocol: bool = False) -> None:
        self._refresh_axis_context(
            status=status,
            refresh_axis_info=refresh_axis_info,
            refresh_protocol=refresh_protocol,
            force_axis_info=refresh_axis_info,
            force_protocol=refresh_protocol,
        )


    def _open_settings(self, axis_index: int) -> None:
        self._open_or_switch_axis_detail(axis_index)

    def _on_canvas_press(self, event) -> None:
        if self.kro_enabled_var.get():
            if self.kro.handle_press(event.x, event.y, event.x_root, event.y_root):
                self._request_main_canvas_redraw()
                return

        gear_axis = self._gear_axis_from_point(event.x, event.y)
        if gear_axis is not None:
            if not self._is_axis_active(gear_axis):
                self._set_status(f"Oś {self.axis_models[gear_axis].axis_def.axis_name} jest zablokowana.")
                return
            self._open_settings(gear_axis)
            return
        wave_axis = self._wave_axis_from_point(event.x, event.y)
        if wave_axis is not None:
            if not self._is_axis_active(wave_axis):
                self._set_status(f"Oś {self.axis_models[wave_axis].axis_def.axis_name} jest zablokowana.")
                return
            self._smooth_axis_idx(wave_axis)
            return

        # Sprawdź kliknięcie w ikonę/label aktywności (lewa strona osi)
        for ax_idx, rect in self.axis_rects.items():
            if event.x < rect.left and abs(event.y - (rect.top + rect.bottom) / 2.0) < (rect.bottom - rect.top) / 2.0:
                self._toggle_axis_activity(ax_idx)
                return

        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        
        is_active = self._is_axis_active(axis_index)
        axis_changed = self._set_active_axis(axis_index)
        self._configure_after_id = None
        if axis_changed:
            self._update_selected_point_time_indicator()
            self._refresh_axis_context(
                status=None,
                refresh_axis_info=True,
                refresh_protocol=True,
                force_axis_info=True,
                force_protocol=True,
            )
        
        if not is_active:
            self._set_status(f"Oś {self.axis_models[axis_index].axis_def.axis_name} jest zablokowana.")
            return

        model = self.axis_models[axis_index]
        if self._hit_release(axis_index, event.x, event.y):
            self.drag_axis_index = axis_index
            self.selected_index = None
            self.drag_mode = "release"
            self._update_selected_point_time_indicator(axis_index)
            self.drag_anchor_x = event.x
            self.drag_release_anchor_time = int(model.release_time_ms or 0)
            self._drag_zero_snap_locked = False
            self._drag_data_changed = False
            self._request_main_canvas_redraw()
            self._set_status(f"Wybrano RELEASE osi: {model.axis_def.axis_name}.")
            return
        node_index = self._hit_node(axis_index, event.x, event.y)
        if node_index is not None:
            self.drag_axis_index = axis_index
            self.selected_index = node_index
            self.selected_node_ref = model.nodes[node_index]
            self.drag_mode = "node"
            self._update_selected_point_time_indicator(axis_index, node_index)
            rect = self.axis_rects[axis_index]
            
            # Ghost assist cache
            self._ghost_samples_cache = []
            model._invalidate_cache()
            if getattr(self.main_take_settings, "ghost_assist_enabled", False):
                self._ghost_samples_cache = self._sample_original_curve(model)

            # Natychmiastowe przyciągnięcie punktu pod kursor (bez snapu podczas drag)
            new_t = self._x_to_time(event.x, rect.left, rect.right)
            new_y = self._canvas_to_logical_y(model, event.y, rect.top, rect.bottom, apply_snap=False)
            model.move_node(self.selected_index, new_t, new_y)
            self._restore_selected_index_from_ref()
            self._request_live_matrix_refresh(axis_index)
            
            self.drag_anchor_x = event.x
            self.drag_anchor_y = event.y
            self._drag_data_changed = True
            self._request_main_canvas_redraw()
            self._set_status(f"Wybrano punkt osi: {model.axis_def.axis_name} i przyciągnięto do kursora.")
            return
        self.drag_axis_index = axis_index
        self.selected_index = None
        self.drag_mode = "pan"
        self.drag_anchor_x = event.x
        self._drag_zero_snap_locked = False
        self._drag_data_changed = False
        
        # Ghost assist cache for PAN
        self._ghost_samples_cache = []
        model._invalidate_cache()
        if getattr(self.main_take_settings, "ghost_assist_enabled", False):
            self._ghost_samples_cache = self._sample_original_curve(model)

        self._request_main_canvas_redraw()
        self._set_status(f"PAN osi: {model.axis_def.axis_name}.")

    def _on_canvas_drag(self, event) -> None:
        if self.kro_enabled_var.get():
            if self.kro.handle_drag(event.x, event.y):
                self._request_main_canvas_redraw()
                return

        axis_index = self.drag_axis_index
        if axis_index is None or axis_index not in self.axis_rects:
            return
        model = self.axis_models[axis_index]
        rect = self.axis_rects[axis_index]

        # Wymuś unieważnienie cache po SAVE przy pierwszym ruchu
        if getattr(self, "_force_curve_resample_after_save", False):
            # 1. Unieważnij cache aktywnej osi
            model._invalidate_cache()
            # 2. Wymuś ponowne sample_curve aktywnej osi z aktualnego model.nodes
            model.sample_curve(self._main_curve_sample_count(), duration_ms=self.global_take_duration_ms)
            # 3. Zresetuj flagę
            self._force_curve_resample_after_save = False

        if self.drag_mode == "node" and self.selected_index is not None:
            new_t = self._x_to_time(event.x, rect.left, rect.right)
            new_y = self._canvas_to_logical_y(model, event.y, rect.top, rect.bottom, apply_snap=False)
            
            # Ghost Assist logic
            self.is_ghost_snapped = False
            self.is_zero_snapped = False
            ms = self.main_take_settings
            if getattr(ms, "ghost_assist_enabled", False) and self._ghost_samples_cache:
                gy = self._get_ghost_y_at_time(new_t)
                if gy is not None:
                    threshold = getattr(ms, "ghost_assist_threshold_y", 4.0)
                    if abs(new_y - gy) <= threshold:
                        new_y = gy
                        self.is_ghost_snapped = True

            if not self.is_ghost_snapped:
                snapped_y = self._apply_drag_zero_snap(model, new_y)
                if snapped_y == 0.0 and new_y != 0.0:
                    self.is_zero_snapped = True
                new_y = snapped_y

            if model.move_node(self.selected_index, new_t, new_y):
                self._restore_selected_index_from_ref()
                self._update_selected_point_time_indicator(axis_index, self.selected_index, new_t)
                # Po move_node nody mogły zmienić kolejność, ale move_node zwraca True jeśli nastąpiła zmiana.
                # sort_and_fix_nodes() w _draw_main_canvas zadba o spójność rysowania.
                model._invalidate_cache()
                # Wymuś resampling natychmiast po zmianie pozycji punktu
                model.sample_curve(self._main_curve_sample_count(), duration_ms=self.global_take_duration_ms)
                self._drag_data_changed = True
                self._request_main_canvas_redraw(only_axis_index=axis_index)
                self._request_live_matrix_refresh(axis_index)
                if self.kro_enabled_var.get():
                    self.kro.on_axis_changed(axis_index)
        elif self.drag_mode == "release":
            new_time = self._x_to_time(event.x, rect.left, rect.right)
            if model.set_release_time(new_time):
                self._update_selected_point_time_indicator(axis_index, time_ms=new_time)
                self._drag_data_changed = True
                self._request_main_canvas_redraw(only_axis_index=axis_index)
                self._request_live_matrix_refresh(axis_index)
                if self.kro_enabled_var.get():
                    self.kro.on_axis_changed(axis_index)
        elif self.drag_mode == "pan":
            new_time = self._x_to_time(event.x, rect.left, rect.right)
            old_time = self._x_to_time(self.drag_anchor_x, rect.left, rect.right)
            delta = new_time - old_time

            # Ghost Assist logic for PAN (Time Snap Only)
            self.is_ghost_snapped = False
            ms = self.main_take_settings
            if getattr(ms, "ghost_assist_enabled", False) and self._ghost_samples_cache and model.nodes:
                threshold_y = getattr(ms, "ghost_assist_threshold_y", 4.0)
                threshold_t = 50.0 # 50ms threshold
                
                if hasattr(model, 'original_nodes') and model.original_nodes:
                    best_snap_delta = None
                    for node in model.nodes:
                        planned_t = node.time_ms + delta
                        for g_node in model.original_nodes:
                            if abs(planned_t - g_node.time_ms) <= threshold_t and abs(node.y - g_node.y) <= threshold_y:
                                best_snap_delta = g_node.time_ms - node.time_ms
                                break
                        if best_snap_delta is not None: break
                    
                    if best_snap_delta is not None:
                        delta = best_snap_delta
                        self.is_ghost_snapped = True

            self.drag_anchor_x = event.x
            if model.shift_all(delta):
                model._invalidate_cache()
                self._update_selected_point_time_indicator()
                self._drag_data_changed = True
                self._request_main_canvas_redraw(only_axis_index=axis_index)
                self._request_live_matrix_refresh(axis_index)
                if self.kro_enabled_var.get():
                    self.kro.on_axis_changed(axis_index)

    def _on_canvas_release(self, _event) -> None:
        if self.kro_enabled_var.get():
            if self.kro.handle_release(_event.x, _event.y):
                self._request_main_canvas_redraw()
                return

        self.is_ghost_snapped = False
        changed_axis_index = self.drag_axis_index
        had_drag_mode = self.drag_mode is not None
        drag_data_changed = self._drag_data_changed

        if had_drag_mode and changed_axis_index is not None and self.drag_mode == "node" and self.selected_index is not None:
            model = self.axis_models[changed_axis_index]
            node = model.nodes[self.selected_index]
            # Dopiero przy release stosujemy snap do zera
            final_y = model.apply_zero_snap(self.main_take_settings, node.y)
            if model.move_node(self.selected_index, node.time_ms, final_y):
                self._restore_selected_index_from_ref()
                model._invalidate_cache()
                drag_data_changed = True

        self.drag_axis_index = None
        self.selected_index = None
        self.selected_node_ref = None
        self.drag_mode = None
        self.drag_anchor_x = 0
        self.drag_anchor_y = 0
        self._drag_zero_snap_locked = False
        self._drag_data_changed = False
        self._main_canvas_needs_redraw = True
        self._configure_after_id = None
        if had_drag_mode and changed_axis_index is not None and drag_data_changed:
            self._snajper_refresh_ehr_axis(
                changed_axis_index,
                curve=True,
                metrics=True,
                step=True,
                status="Gotowy.",
            )
            self._refresh_axis_dialog_if_needed(changed_axis_index)
            return
        if changed_axis_index is not None:
            self._main_canvas_needs_redraw = False
            self._request_main_canvas_redraw(only_axis_index=changed_axis_index)
        else:
            self._request_main_canvas_redraw()
        self._set_status("Gotowy.")

    def _on_canvas_double_click(self, event) -> None:
        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        if not self._is_axis_active(axis_index):
            self._set_status(f"Oś {self.axis_models[axis_index].axis_def.axis_name} jest zablokowana.")
            return
        if self._gear_axis_from_point(event.x, event.y) is not None or self._wave_axis_from_point(event.x, event.y) is not None:
            return
        model = self.axis_models[axis_index]
        rect = self.axis_rects[axis_index]
        self._set_active_axis(axis_index)
        t_ms = self._x_to_time(event.x, rect.left, rect.right)
        if model.is_release_axis and abs(event.y - ((rect.top + rect.bottom) / 2.0)) <= 20:
            if model.set_release_time(t_ms):
                model._invalidate_cache()
                self._snajper_refresh_ehr_axis(
                    axis_index,
                    curve=True,
                    metrics=True,
                    step=True,
                    status=f"Ustawiono RELEASE na osi: {model.axis_def.axis_name}.",
                )
            else:
                self._request_main_canvas_redraw(only_axis_index=axis_index)
                self._set_status(f"Ustawiono RELEASE na osi: {model.axis_def.axis_name}.")
            return
        y = self._canvas_to_logical_y(model, event.y, rect.top, rect.bottom)
        model.add_node(t_ms, y)
        self._update_selected_point_time_indicator(axis_index, time_ms=t_ms)
        model._invalidate_cache()
        self._snajper_refresh_ehr_axis(
            axis_index,
            curve=True,
            metrics=True,
            step=True,
            status=f"Dodano punkt na osi: {model.axis_def.axis_name}.",
        )
        self._refresh_axis_dialog_if_needed(axis_index)

    def _on_canvas_right_click(self, event) -> None:
        if self.kro_enabled_var.get():
            if self.kro.handle_right_click(event.x, event.y):
                self._request_main_canvas_redraw()
                return

        axis_index = self._axis_index_from_point(event.x, event.y)
        if axis_index is None:
            return
        if not self._is_axis_active(axis_index):
            self._set_status(f"Oś {self.axis_models[axis_index].axis_def.axis_name} jest zablokowana.")
            return
        if self._gear_axis_from_point(event.x, event.y) is not None or self._wave_axis_from_point(event.x, event.y) is not None:
            return
        node_index = self._hit_node(axis_index, event.x, event.y)
        if node_index is None:
            return
        model = self.axis_models[axis_index]
        model.remove_node(node_index)
        self.selected_index = None
        self.selected_node_ref = None
        self._update_selected_point_time_indicator()
        model._invalidate_cache()
        self._snajper_refresh_ehr_axis(
            axis_index,
            curve=True,
            metrics=True,
            step=True,
            status=f"Usunięto punkt z osi: {model.axis_def.axis_name}.",
        )
        self._refresh_axis_dialog_if_needed(axis_index)

    def _smooth_active(self) -> None:
        model = self._active_model()
        axis_index = self.active_axis_index
        strength = max(0.0, min(1.0, float(getattr(self.main_take_settings, "smooth_strength_default", 0.35))))
        passes = max(1, min(8, int(getattr(self.main_take_settings, "smooth_passes_default", 2))))
        model.smooth_all(strength=strength, passes=passes)

        # Inwalidacja cache przed sygnałem Snajpera
        model._invalidate_cache()
        self.protocol_cache_key = None
        self.axis_info_cache_key = None

        self._snajper_fire_ehr(f"ehr_axis_{axis_index}_curve", policy="FINAL")
        self._snajper_fire_ehr(f"ehr_axis_{axis_index}_final_matrix", policy="FINAL")
        self._set_status(f"Wygładzono przebieg osi: {model.axis_def.axis_name}. siła={strength:.2f} przejścia={passes}.")

        self._refresh_axis_dialog_if_needed(axis_index)



    def _take_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / "data" / "take"
    def _save_take_to_path(self, path: Path) -> Path:
        saved_path = save_take_txt(self.axis_models, self.global_take_duration_ms, path)
        # Po udanym SAVE: obecna aktywna linia zostaje skopiowana jako nowy ghost
        for axis in self.axis_models:
            axis.clone_original_state()
            # Unieważnij wszystkie cache modelu
            axis._invalidate_cache()
            # WYMUSZONY SAMPLING po SAVE, aby zsynchronizować model z widokiem
            axis.sample_curve(self._main_curve_sample_count(), duration_ms=self.global_take_duration_ms)
            if hasattr(axis, "_ghost_cache"):
                axis._ghost_cache.clear()
        
        # Wyczyść globalne cache UI
        self._ghost_samples_cache = []
        self._force_curve_resample_after_save = True
        self._main_canvas_needs_redraw = True

        self._snajper_refresh_ehr_page_full(
            status=f"Zapisano TAKE TXT: {saved_path.name}",
        )

        return saved_path

    def _load_take_from_path(self, path: Path) -> None:
        loaded_duration = load_take_txt(self.axis_models, path)
        if loaded_duration and loaded_duration != self.global_take_duration_ms:
            self.global_take_duration_ms = loaded_duration
        
        # load_take_txt() wywołuje sort_and_fix_nodes() dla wszystkich osi,
        # więc tutaj tylko czyścimy cache i markujemy UI.
        for axis in self.axis_models:
            axis.sandbox.mouse_y_precision = 1.0
            axis.sandbox.top_bottom_margin = 8
            axis._invalidate_cache()
            if hasattr(axis, "_ghost_cache"):
                axis._ghost_cache.clear()
                
        self.protocol_cache_key = None
        self.axis_info_cache_key = None
        self._main_canvas_needs_redraw = True
        self._mark_protocol_dirty()
        self._mark_axis_metrics_dirty()
        self._snajper_refresh_ehr_page_full(
            status=f"Wczytano TAKE TXT: {path.name}",
        )

    def _save_take_slot(self, slot_index: int, current_path: Path | None) -> Path:
        path = next_take_txt_path(current_path, self._take_dir(), slot_index)
        saved_path = self._save_take_to_path(path)
        self._set_status(f"Zapisano TAKE TXT: {saved_path.name}")
        return saved_path

    def _save_take_txt_click(self) -> None:
        default_path = next_take_txt_path(None, self._take_dir(), 0)
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialdir=str(self._take_dir()),
            initialfile=default_path.name,
            filetypes=[("TAKE TXT", "*.txt"), ("Text", "*.txt"), ("All files", "*.*")],
            title="Zapisz TAKE TXT",
        )
        if not path:
            return
        saved_path = self._save_take_to_path(Path(path))
        self._set_status(f"Zapisano TAKE TXT: {saved_path.name}")

    def _load_take_txt_click(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(self._take_dir()),
            filetypes=[("TAKE TXT", "*.txt"), ("Text", "*.txt"), ("All files", "*.*")],
            title="Wczytaj TAKE TXT",
        )
        if not path:
            return
        self._load_take_from_path(Path(path))

    def _clear_take_slots_click(self) -> None:
        """Handler przycisku CLEAR TAKE — czyści listę slotów w JSON."""
        try:
            SLOTS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            SLOTS_JSON_PATH.write_text("{}", encoding="utf-8")
            if self.take_widget:
                self.take_widget.force_reload_slots_from_json()
            self._set_status("Wyczyszczono listę TAKE.")
        except Exception as exc:
            print(f"ERROR: Błąd podczas czyszczenia TAKE: {exc}")



def main() -> None:
    app = TarzanEhrMultiAxisWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
