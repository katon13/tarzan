from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any, Callable

import tkinter as tk
from tkinter import filedialog

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except Exception as exc:  # pragma: no cover
    raise RuntimeError("TarzanTakeProtocolLight.py wymaga Pillow. Zainstaluj: pip install pillow") from exc


# ======================================================================================
# ŚCIEŻKI I ŚRODOWISKO
# ======================================================================================
#
# Ten moduł jest przygotowany jako lekki widget do wpięcia w EHR.
# Źródłem ustawień layoutu pozostaje wyłącznie JSON:
#
#     data/ehr/take_protocol_ui_settings.json
#
# Wersja LIGHT:
# - NIE posiada panelu ustawień,
# - NIE posiada suwaków ani runtime strojenia UI,
# - korzysta tylko z odczytu ustawień z JSON,
# - zostawia minimalny fallback, aby testowe okno nie przestało działać,
# - zachowuje pełny kontrakt stanów TAKE,
# - nie używa _refresh_all.
#
# Warstwa:
#   UI / preview
#
# Nie ruszam:
#   - logiki TAKE,
#   - stanu plików TAKE,
#   - importu plików,
#   - symulacji SAVE,
#   - publicznych połączeń zewnętrznych.
#
# Kontrakt:
#   - 10 ikon w jednym rzędzie,
#   - dark mode,
#   - SAVE nad ikoną,
#   - łapka tylko dla LINKED,
#   - brak globalnego redraw całego modułu przy zwykłych akcjach,
#   - tylko lokalne odświeżanie slotów.
#
# Zmieniam tylko:
#   - usunięcie panelu ustawień,
#   - przebudowę do widgetu gotowego pod EHR,
#   - uproszczenie renderingu pod wersję LIGHT,
#   - pełne komentarze metod pod przyszłą integrację.
# ======================================================================================

THIS_FILE = Path(__file__).resolve()
EDITOR_DIR = THIS_FILE.parent
PROJECT_DIR = EDITOR_DIR.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

DATA_DIR = PROJECT_DIR / "data"
EHR_DIR = DATA_DIR / "ehr"
TAKE_DIR = DATA_DIR / "take"
IMG_TAKE_DIR = PROJECT_DIR / "img" / "take"
FONT_DIR = PROJECT_DIR / "font"

SLOTS_JSON_PATH = EHR_DIR / "take_protocol_slots.json"
UI_JSON_PATH = EHR_DIR / "take_protocol_ui_settings.json"

SANDBOX_ASSET_DIR = Path("/mnt/data")
SANDBOX_FONT_PATH = SANDBOX_ASSET_DIR / "Pattifont.ttf"

try:
    from core.tarzanAssets import take_icon as project_take_icon  # type: ignore
except Exception:
    project_take_icon = None


# ======================================================================================
# KOLORY / STAŁE UI
# ======================================================================================

WINDOW_BG = "#0B1220"
HEADER_BG = "#0A1020"
PROTOCOL_OUTER_BG = "#111A2A"
PROTOCOL_INNER_BG = "#152338"
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


# ======================================================================================
# USTAWIENIA UI
# ======================================================================================

@dataclass
class UiSettings:
    """
    Lekki adapter ustawień layoutu TAKE PROTOCOL.

    Źródłem prawdy dla layoutu pozostaje JSON w katalogu ``data/ehr``.
    Ta klasa nie jest już miejscem ręcznego strojenia UI ani rejestrem
    wartości projektowych. Jej zadaniem jest wyłącznie:

    - przyjąć komplet ustawień z JSON,
    - uzupełnić ewentualne braki minimalnym fallbackiem technicznym,
    - odfiltrować pola nieużywane przez wersję LIGHT,
    - ochronić rendering przed skrajnie błędnymi wartościami.

    Ważne:
    - pełny rejestr ustawień pozostaje w pliku JSON,
    - wersja LIGHT nie zapisuje ani nie zmienia ustawień runtime,
    - fallback jest tylko bezpiecznikiem, aby moduł nie przestał działać
      przy brakującym lub uszkodzonym JSON.
    """

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
    def _fallback_values(cls) -> dict[str, Any]:
        """
        Zwraca minimalny fallback techniczny dla aktywnych pól layoutu.

        To nie jest drugi rejestr ustawień projektu. Te wartości mają wyłącznie
        zabezpieczyć testowe uruchomienie, gdy JSON nie istnieje albo brakuje
        w nim pojedynczych pozycji. W normalnym trybie pracy źródłem prawdy
        pozostaje ``data/ehr/take_protocol_ui_settings.json``.
        """
        return {
            "protocol_title_y": 70,
            "protocol_height": 290,
            "row_center_y": 85,
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
    def load_or_default(cls, path: Path) -> "UiSettings":
        """
        Wczytuje ustawienia z JSON i mapuje je do aktywnych pól wersji LIGHT.

        Zasada pracy:
        - JSON jest głównym rejestrem ustawień,
        - bierzemy tylko pola realnie używane przez ten plik,
        - brakujące pola uzupełniamy fallbackiem technicznym,
        - pola nieużywane przez LIGHT mogą nadal istnieć w JSON, ale nie są
          mapowane do adaptera, dzięki czemu nie wpływają na działanie modułu.
        """
        raw: dict[str, Any] = {}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                raw = loaded
        except Exception:
            raw = {}

        fallback = cls._fallback_values()
        payload: dict[str, Any] = {}
        for name in cls._field_names():
            payload[name] = raw.get(name, fallback[name])

        ui = cls(**payload)
        ui.clamp()
        return ui

    def clamp(self) -> None:
        """
        Ogranicza wartości liczbowe do bezpiecznych zakresów renderingu.

        Clamp zostaje tylko jako ochrona techniczna przed błędnym JSON.
        Nie zmienia zasad działania UI i nie służy do strojenia wyglądu.
        """
        def ci(name: str, lo: int, hi: int) -> None:
            setattr(self, name, max(lo, min(hi, int(getattr(self, name)))))

        ci("protocol_title_y", 10, 200)
        ci("protocol_height", 180, 520)
        ci("row_center_y", 60, 360)
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


# ======================================================================================
# DANE SLOTÓW
# ======================================================================================

@dataclass
class SlotRecord:
    """
    Rekord przechowywany w JSON pamięci slotów.

    Pole path pozostaje lekką informacją o przypiętym pliku TAKE.
    """
    path: Optional[str] = None


@dataclass
class SlotStore:
    """
    Model pamięci slotów TAKE PROTOCOL.

    To jest wyłącznie warstwa prostego storage UI:
    - które sloty mają przypięty plik,
    - który slot jest aktywny.

    Nie jest to warstwa logiki TAKE ani modelu ruchu.
    """
    slots: list[SlotRecord]
    active_slot: Optional[int] = None

    @classmethod
    def default(cls) -> "SlotStore":
        """Tworzy pusty stan 10 slotów."""
        return cls(slots=[SlotRecord() for _ in range(SLOT_COUNT)], active_slot=None)

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
            return cls(slots=slots, active_slot=active_slot)
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
    Odczytuje numer TAKE do wyświetlenia na ikonie.

    Priorytet:
    1. metadata.take_id z pliku JSON,
    2. numer wyciągnięty z nazwy pliku.

    Gdy nic nie da się odczytać, zwracane jest '---'.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        metadata = raw.get("metadata") or {}
        take_id = metadata.get("take_id", "")
        number = extract_number_from_take_id(take_id) or extract_number_from_filename(path)
        if not number:
            return "---"
        return number.zfill(digits)
    except Exception:
        number = extract_number_from_filename(path)
        return number.zfill(digits) if number else "---"



def read_take_version(path: Path) -> str:
    """Odczytuje wersję zapisu wyłącznie z nazwy pliku TAKE."""
    return extract_version_from_filename(path)


def copy_take_into_project(src: Path) -> Path:
    """
    Importuje plik TAKE do katalogu projektu data/take.

    Zachowanie zgodne z sandboxem:
    - jeżeli plik nie istnieje -> zwykłe copy,
    - jeżeli nazwa już istnieje -> tworzymy _import_01, _import_02 itd.

    Wersja LIGHT zachowuje pełny import dokładnie jak ustalono.
    """
    ensure_dirs()
    dst = TAKE_DIR / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
        return dst

    stem = src.stem
    suffix = src.suffix or ".json"
    counter = 1
    while True:
        candidate = TAKE_DIR / f"{stem}_import_{counter:02d}{suffix}"
        if not candidate.exists():
            shutil.copy2(src, candidate)
            return candidate
        counter += 1


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
    if project_take_icon is not None:
        try:
            candidates.append(Path(project_take_icon(size=size, state=state)))
        except Exception:
            pass

    candidates.extend([
        IMG_TAKE_DIR / f"take_{state}_{size}.png",
        IMG_TAKE_DIR / f"take_{state}_320.png",
        IMG_TAKE_DIR / f"take_{state}_256.png",
        IMG_TAKE_DIR / f"take_{state}_128.png",
        IMG_TAKE_DIR / f"take_{state}_64.png",
    ])
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


# ======================================================================================
# RENDERER IKON
# ======================================================================================

class IconRenderer:
    """
    Lekki renderer ikon slotów TAKE.

    Najważniejsze założenie wersji LIGHT:
    - ikony bazowe są trzymane w cache,
    - gotowe PhotoImage są trzymane w cache pod kluczem stanu slotu,
    - unikamy niepotrzebnego odtwarzania obrazów przy każdej akcji.

    Dzięki temu zwykłe odświeżenie pojedynczego slotu nie powoduje
    pełnego redraw całego pasa TAKE.
    """

    def __init__(self, ui: UiSettings) -> None:
        self.ui = ui
        self.base_cache: dict[tuple[str, int, int], Image.Image | None] = {}
        self.photo_cache: dict[tuple[Any, ...], Any] = {}

    def _load_base_icon(self, state: str) -> Image.Image:
        """
        Ładuje bazową ikonę dla stanu i rozmiaru.

        Wynik jest trzymany w cache jako PIL Image.
        """
        key = (state, self.ui.icon_width, self.ui.icon_height)
        if key in self.base_cache and self.base_cache[key] is not None:
            return self.base_cache[key].copy()  # type: ignore[return-value]

        source_path = project_take_icon_path(state, max(self.ui.icon_width, self.ui.icon_height))
        if source_path and source_path.exists():
            img = Image.open(source_path).convert("RGBA").resize(
                (self.ui.icon_width, self.ui.icon_height),
                Image.LANCZOS,
            )
        else:
            img = Image.new("RGBA", (self.ui.icon_width, self.ui.icon_height), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)
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
        """
        Buduje finalną bitmapę pojedynczego slotu.

        Cache kluczowany jest po stanie slotu oraz parametrach tekstowych.
        To ogranicza koszty CPU przy częstych lokalnych odświeżeniach.
        """
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

        base_state = "open" if vm.state in (SlotState.EMPTY, SlotState.LINKED) else ("save" if vm.is_saved else "active")
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
        """
        Czyści cache runtime renderer.

        Przydatne wtedy, gdy integrator EHR podmieni zasoby lub ustawienia,
        a potem będzie chciał wymusić świeży render.
        """
        self.base_cache.clear()
        self.photo_cache.clear()


# ======================================================================================
# WIDGET SLOTU
# ======================================================================================

class SlotWidget(tk.Frame):
    """
    Lekki widget pojedynczego slotu TAKE.

    Widget sam dba o:
    - hover,
    - klik w ikonę,
    - klik w łapkę,
    - przycisk SAVE nad ikoną,
    - lokalny redraw tylko własnego slotu.
    """

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
            height=owner.ui.icon_height + 65,
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
        """
        Renderuje tylko ten jeden slot.

        To jest podstawowy mechanizm LIGHT:
        żadnego pełnego odświeżania całego modułu przy pojedynczej akcji.
        """
        self.configure(bg=self.owner.protocol_bg())
        self.canvas.configure(
            bg=self.owner.protocol_bg(),
            width=self.owner.ui.icon_width,
            height=self.owner.ui.icon_height + 65,
        )
        self.canvas.delete("all")
        self.action_hitbox = None
        self.save_button = None
        self.save_button_window = None

        top_y = 24

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
        """
        Rysuje łapkę akcji.

        Kontrakt:
        - widoczna tylko dla LINKED,
        - tylko na hover,
        - nie pokazuje się dla ACTIVE,
        - nie pokazuje się, gdy widoczny jest SAVE.
        """
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
        """
        Rysuje przycisk SAVE nad ikoną.

        To jest zgodne z ustalonym kontraktem UI.
        Sam zapis danych TAKE nie jest tutaj zaimplementowany.
        W tej wersji pozostaje wyłącznie symulacja stanu SAVED.
        """
        ui = self.owner.ui
        x = int((ui.icon_width - ui.save_width) / 2 + ui.save_offset_x)
        y = int(max(0, top_y - ui.save_offset_y - ui.save_height))

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


# ======================================================================================
# GŁÓWNY WIDGET LIGHT
# ======================================================================================

class TarzanTakeProtocolLightWidget(tk.Frame):
    """
    Lekki widget TAKE PROTOCOL gotowy do wpięcia w EHR.

    Najważniejsze cechy:
    - dziedziczy po tk.Frame, więc można go osadzić w istniejącym oknie EHR,
    - zachowuje kontrakt stanów TAKE,
    - nie posiada panelu runtime ustawień,
    - używa tylko lokalnych odświeżeń slotów,
    - lokalny status bar zostaje wyłącznie do testów.

    Uwaga integracyjna:
    Przy docelowym spięciu z EHR lokalny status bar powinien zostać usunięty,
    a metoda _set_status(...) powinna zostać podpięta do centralnego statusu/logera EHR.
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        status_sink: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Tworzy widget TAKE PROTOCOL LIGHT.

        Parametr status_sink:
        - opcjonalny callback pod przyszłą integrację z EHR,
        - jeżeli zostanie podany, komunikaty mogą być przekazywane na zewnątrz,
        - lokalny status bar nadal zostaje do testów.
        """
        super().__init__(master, bg=WINDOW_BG, highlightthickness=0, bd=0)
        ensure_dirs()

        self.external_status_sink = status_sink
        self.store = SlotStore.load_or_default(SLOTS_JSON_PATH)
        self.ui = UiSettings.load_or_default(UI_JSON_PATH)
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
        """
        Ustawia komunikat statusu lokalnie i opcjonalnie emituje go na zewnątrz.

        To jest jedyna metoda, przez którą ten widget ustawia status.
        Dzięki temu podczas integracji z EHR można łatwo odłączyć lokalny pasek
        i przepiąć komunikaty do globalnego loggera lub status baru EHR.
        """
        self.status_var.set(text)
        if self.external_status_sink is not None:
            try:
                self.external_status_sink(text)
            except Exception:
                pass

    def _build_models(self) -> list[SlotVM]:
        """
        Buduje modele widoku slotów na podstawie pamięci slotów.

        Zasada:
        - EMPTY jeśli brak pliku,
        - LINKED jeśli plik jest przypięty,
        - ACTIVE jeśli slot był zapisany jako aktywny.

        Wersja LIGHT nie zmienia logiki stanów.
        """
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
        Buduje stałą strukturę widgetu.

        Wersja LIGHT:
        - nie tworzy żadnych paneli ustawień,
        - nie tworzy suwaków,
        - zostawia tylko:
          * title bar,
          * pas TAKE PROTOCOL,
          * lokalny status bar.
        """
        title_bar = tk.Frame(self, bg=HEADER_BG, height=TITLE_HEIGHT)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="TARZAN — TAKE PROTOCOL LIGHT",
            bg=HEADER_BG,
            fg=TEXT,
            anchor="w",
            padx=10,
            font=("Segoe UI Semibold", 17),
        ).pack(fill="both", expand=True)

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

        self.protocol_title_id = self.protocol_canvas.create_text(
            0,
            0,
            text="TAKE PROTOCOL",
            fill=TEXT,
            anchor="n",
            font=("Segoe UI Light", 34),
        )

        self.row_frame = tk.Frame(self.protocol_canvas, bg=self.protocol_bg())
        self.row_window = self.protocol_canvas.create_window(0, 0, window=self.row_frame, anchor="n")

        status_bar = tk.Frame(self, bg=STATUS_BG, height=STATUS_HEIGHT)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg=STATUS_BG,
            fg=STATUS_FG,
            anchor="w",
            padx=10,
            font=("Segoe UI", 10),
        ).pack(fill="both", expand=True)

    def _build_slot_row(self) -> None:
        """
        Buduje rząd 10 slotów tylko raz podczas inicjalizacji.

        To jest ważna różnica względem cięższej wersji:
        nie przebudowujemy całego rzędu po zwykłych akcjach użytkownika.
        Później działamy już tylko przez _refresh_slot(...).
        """
        for index in range(SLOT_COUNT):
            widget = SlotWidget(self.row_frame, self, self.slot_models[index])
            widget.pack(side="left", padx=self.ui.row_pad_x, pady=0)
            self.slot_widgets.append(widget)

    def _save_slots_json(self) -> None:
        """
        Zapisuje aktualny stan slotów do pamięci JSON.

        Ta metoda nie dotyka danych TAKE.
        Zapisuje wyłącznie stan UI.
        """
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
        """
        Lokalnie odświeża tylko jeden slot.

        To jest główna ścieżka odświeżania w wersji LIGHT.
        """
        if 0 <= index < len(self.slot_widgets):
            self.slot_widgets[index].set_vm(self.slot_models[index])

    def _refresh_slots(self, indices: list[int]) -> None:
        """
        Lokalnie odświeża kilka konkretnych slotów.

        Używane np. przy przełączeniu aktywnego slotu.
        """
        for index in indices:
            self._refresh_slot(index)

    def _layout_protocol(self) -> None:
        """
        Przelicza geometrię statycznego pasa TAKE.

        Ten layout jest uruchamiany przy resize widgetu.
        Nie przebudowuje slotów, tylko przestawia tło i pozycje kontenerów.
        """
        width = max(900, int(self.protocol_canvas.winfo_width() or 1200))
        height = max(240, int(self.protocol_canvas.winfo_height() or self.ui.protocol_height))
        inner = self.ui.protocol_inner_pad_x

        self.protocol_canvas.delete("band_bg")
        self.protocol_canvas.create_rectangle(0, 0, width, height, fill=PROTOCOL_OUTER_BG, outline="", tags="band_bg")
        self.protocol_canvas.create_rectangle(inner, 0, width - inner, height, fill=PROTOCOL_INNER_BG, outline="", tags="band_bg")

        if self.protocol_title_id is not None:
            self.protocol_canvas.coords(self.protocol_title_id, width / 2, self.ui.protocol_title_y)
            self.protocol_canvas.itemconfigure(self.protocol_title_id, fill=TEXT, font=("Segoe UI Light", 34))

        if self.row_window is not None:
            self.protocol_canvas.coords(self.row_window, width / 2, self.ui.row_center_y)

    def on_slot_clicked(self, index: int) -> None:
        """
        Obsługuje zwykły klik w slot.

        Zasada zgodna z kontraktem:
        - EMPTY -> wybór pliku,
        - LINKED -> podmiana pliku,
        - ACTIVE -> zwykły klik ignorowany.

        Import pozostaje pełny jak w sandboxie.
        """
        vm = self.slot_models[index]
        if vm.state == SlotState.ACTIVE:
            return

        path = filedialog.askopenfilename(
            title="Wybierz plik TAKE",
            initialdir=str(TAKE_DIR),
            filetypes=[("TAKE JSON", "*.json"), ("JSON", "*.json"), ("All files", "*.*")],
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
        """
        Obsługuje klik w łapkę aktywacji.

        Logika pozostaje zamknięta:
        - tylko LINKED może przejść do ACTIVE,
        - poprzedni ACTIVE wraca do LINKED,
        - nowy ACTIVE ma LOAD=ON,
        - SAVE pojawia się tylko jeśli is_saved=False.
        """
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

        self._refresh_slots(changed)
        self._set_status(f"TAKE {vm.take_number} aktywowany. LOAD=ON.")

    def on_save_clicked(self, index: int) -> None:
        """
        Obsługuje SAVE aktywnego TAKE.

        W tej wersji LIGHT zapis pozostaje świadomie symulowany:
        - ustawiamy tylko stan SAVED w UI,
        - nie zapisujemy jeszcze realnego TAKE do pliku.

        Miejsce integracji:
        tutaj docelowo trzeba wpiąć właściwy zapis wersji TAKE w EHR.
        """
        vm = self.slot_models[index]
        if vm.state != SlotState.ACTIVE:
            return

        vm.is_saved = True
        self._refresh_slot(index)
        self._set_status(f"TAKE {vm.take_number} zapisany. SAVED=ON.")

    def notify_active_take_modified(self) -> None:
        """
        Publiczne API do spięcia z EHR.

        Gdy dane aktywnego TAKE zostaną zmienione przez edycję osi lub inne
        operacje w EHR, wywołanie tej metody ma przywrócić stan ACTIVE:
        - aktywny TAKE wraca z zielonego do czerwonego,
        - znika etykieta SAVED,
        - wraca przycisk SAVE.

        To jest kluczowy punkt połączenia zewnętrznego.
        """
        for index, vm in enumerate(self.slot_models):
            if vm.state == SlotState.ACTIVE:
                vm.is_saved = False
                vm.is_loaded = True
                self._refresh_slot(index)
                self._set_status(f"TAKE {vm.take_number} zmieniony. SAVE ponownie wymagany.")
                break

    def force_reload_layout_from_json(self) -> None:
        """
        Pomocnicze API serwisowe do ponownego wczytania layoutu z JSON.

        Nie jest używane w normalnym workflow LIGHT, ale może być przydatne
        w testach lub przy integracji, gdy EHR będzie chciał przeładować layout
        bez restartu całego okna.

        To jest jedyne miejsce, gdzie dopuszczamy przebudowę widoku,
        bo zmienia się baza geometrii widgetu.
        """
        self.ui = UiSettings.load_or_default(UI_JSON_PATH)
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
        self._set_status("Przeładowano layout TAKE PROTOCOL z JSON.")


# ======================================================================================
# TESTOWE OKNO LIGHT
# ======================================================================================

class TarzanTakeProtocolLightWindow(tk.Tk):
    """
    Małe testowe okno uruchomieniowe.

    To okno istnieje wyłącznie po to, aby można było szybko testować widget
    poza EHR. Docelowo integralną częścią systemu ma być sam widget
    TarzanTakeProtocolLightWidget osadzony w odpowiednim miejscu EHR.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("TARZAN — TAKE PROTOCOL LIGHT")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1400, 360)
        self.configure(bg=WINDOW_BG)

        self.widget = TarzanTakeProtocolLightWidget(self)
        self.widget.pack(fill="both", expand=True)

    def run(self) -> None:
        """Uruchamia pętlę testowego okna."""
        self.mainloop()


# ======================================================================================
# MAIN
# ======================================================================================

def main() -> None:
    """
    Lokalny punkt startowy do testów.

    Przy integracji do EHR należy osadzić bezpośrednio widget:
        TarzanTakeProtocolLightWidget(...)
    """
    ensure_dirs()
    app = TarzanTakeProtocolLightWindow()
    app.run()


if __name__ == "__main__":
    main()
