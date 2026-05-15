
from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any

import tkinter as tk
from tkinter import filedialog

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except Exception as exc:  # pragma: no cover
    raise RuntimeError("TarzanEhrTakeSandbox.py wymaga Pillow. Zainstaluj: pip install pillow") from exc


# ======================================================================================
# ŚCIEŻKI I ŚRODOWISKO
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
CONTROLS_BG = "#0E1727"
SECTION_BG = "#0B1424"
SECTION_BORDER = "#24324A"
INPUT_BG = "#1A2941"
STATUS_BG = "#09101D"

TEXT = "#F3F7FB"
MUTED = "#A7B3C3"
STATUS_FG = "#D5DCE7"

BTN_GREEN = "#46815A"
BTN_GREEN_ACTIVE = "#3E744F"
SAVE_GREEN_FG = "#F4FBF5"

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1280
TITLE_HEIGHT = 58
STATUS_HEIGHT = 36
SLOT_COUNT = 10


# ======================================================================================
# USTAWIENIA UI
# ======================================================================================

@dataclass
class UiSettings:
    # Wczytane z aktualnego JSON użytkownika
    protocol_title_y: int = 70
    protocol_height: int = 290
    row_center_y: int = 85
    protocol_inner_pad_x: int = 12
    row_pad_x: int = 0

    icon_width: int = 167
    icon_height: int = 168

    number_x: int = 62
    number_y: int = 87
    number_font_size: int = 73
    number_digits: int = 1
    number_dx: int = 7
    number_dy: int = 0

    action_x: int = 106
    action_y: int = 65
    action_font_size: int = 30
    action_icon_text: str = "✋️"

    edit_x: int = 26
    edit_y: int = 129
    edit_font_size: int = 11

    saved_x: int = 63
    saved_y: int = 129
    saved_font_size: int = 11

    load_x: int = 112
    load_y: int = 129
    load_font_size: int = 11

    save_offset_x: int = 3
    save_offset_y: int = -35
    save_width: int = 130
    save_height: int = 28
    save_font_size: int = 16

    save_icon_x: int = -6
    save_icon_y: int = -13
    save_icon_scale: int = 142
    save_text_on_icon_x: int = 66
    save_text_on_icon_y: int = 37

    controls_height: int = 453
    controls_columns: int = 4
    slider_length: int = 149

    @classmethod
    def load_or_default(cls, path: Path) -> "UiSettings":
        ui = cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for key, value in raw.items():
                if hasattr(ui, key):
                    setattr(ui, key, value)
        except Exception:
            pass
        ui.controls_columns = 4
        ui.clamp()
        return ui

    def clamp(self) -> None:
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

        ci("save_icon_x", -120, 120)
        ci("save_icon_y", -120, 120)
        ci("save_icon_scale", 32, 400)
        ci("save_text_on_icon_x", 0, 260)
        ci("save_text_on_icon_y", 0, 200)

        ci("controls_height", 220, 820)
        self.controls_columns = 4
        ci("slider_length", 110, 260)

    def save(self, path: Path) -> None:
        self.clamp()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ======================================================================================
# DANE SLOTÓW
# ======================================================================================

@dataclass
class SlotRecord:
    path: Optional[str] = None


@dataclass
class SlotStore:
    slots: list[SlotRecord]
    active_slot: Optional[int] = None

    @classmethod
    def default(cls) -> "SlotStore":
        return cls(slots=[SlotRecord() for _ in range(SLOT_COUNT)], active_slot=None)

    @classmethod
    def load_or_default(cls, path: Path) -> "SlotStore":
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
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "slots": [asdict(slot) for slot in self.slots],
            "active_slot": self.active_slot,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class SlotState:
    EMPTY = "empty"
    LINKED = "linked"
    ACTIVE = "active"


@dataclass
class SlotVM:
    index: int
    file_path: Optional[Path] = None
    take_number: str = ""
    state: str = SlotState.EMPTY
    is_saved: bool = False
    is_loaded: bool = False

    def rel_path(self) -> Optional[str]:
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
    TAKE_DIR.mkdir(parents=True, exist_ok=True)
    EHR_DIR.mkdir(parents=True, exist_ok=True)


def take_path_from_record(path_value: Optional[str]) -> Optional[Path]:
    if not path_value:
        return None
    p = Path(path_value)
    if p.is_absolute():
        return p if p.exists() else None
    candidate = (PROJECT_DIR / p).resolve()
    return candidate if candidate.exists() else None


def extract_number_from_take_id(take_id: str) -> Optional[str]:
    m = re.search(r"(\d+)", str(take_id or ""))
    return m.group(1) if m else None


def extract_number_from_filename(path: Path) -> Optional[str]:
    m = re.search(r"TAKE[_\- ]?(\d+)", path.name, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"(\d+)", path.stem)
    return m.group(1) if m else None


def read_take_number(path: Path, digits: int) -> str:
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


def copy_take_into_project(src: Path) -> Path:
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
    for p in paths:
        if p.exists():
            return p
    return None


def project_take_icon_path(state: str, size: int) -> Optional[Path]:
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
    font_loader = chalk_font_candidates if chalk else normal_font_candidates
    for size in range(preferred, 7, -2):
        for font in font_loader(size):
            probe = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
            draw = ImageDraw.Draw(probe)
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
            except Exception:
                continue
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w <= max_w and h <= max_h:
                return font
    fonts = font_loader(max(8, preferred // 2))
    return fonts[0] if fonts else None


# ======================================================================================
# RENDERER IKON
# ======================================================================================

class IconRenderer:
    def __init__(self, ui: UiSettings) -> None:
        self.ui = ui
        self.base_cache: dict[tuple[str, int, int], Image.Image | None] = {}
        self.photo_cache: dict[tuple[Any, ...], Any] = {}

    def set_ui(self, ui: UiSettings) -> None:
        self.ui = ui
        self.photo_cache.clear()

    def _load_base_icon(self, state: str) -> Image.Image:
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
            draw.line((20, self.ui.icon_height - 30, self.ui.icon_width - 20, self.ui.icon_height - 30), fill=(230, 230, 230, 255), width=2)

        self.base_cache[key] = img
        return img.copy()

    def build_slot_photo(self, vm: SlotVM) -> Any:
        cache_key = (
            vm.state, vm.take_number, vm.is_saved, vm.is_loaded,
            self.ui.icon_width, self.ui.icon_height,
            self.ui.number_x, self.ui.number_y, self.ui.number_font_size, self.ui.number_digits,
            self.ui.number_dx, self.ui.number_dy,
            self.ui.edit_x, self.ui.edit_y, self.ui.edit_font_size,
            self.ui.saved_x, self.ui.saved_y, self.ui.saved_font_size,
            self.ui.load_x, self.ui.load_y, self.ui.load_font_size,
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
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                x = int(self.ui.number_x - tw / 2 + self.ui.number_dx)
                y = int(self.ui.number_y - th / 2 + self.ui.number_dy)
                for dx, dy in [(0, 0), (1, 0), (0, 1)]:
                    draw.text((x + dx, y + dy), text, font=font, fill=(245, 245, 245, 255))

        if vm.state == SlotState.ACTIVE:
            ef = fit_font("EDIT", 90, 20, self.ui.edit_font_size, chalk=False)
            sf = fit_font("SAVED", 90, 20, self.ui.saved_font_size, chalk=False)
            lf = fit_font("LOAD", 90, 20, self.ui.load_font_size, chalk=False)

            if ef is not None:
                draw.text((self.ui.edit_x, self.ui.edit_y), "EDIT", font=ef, fill=(240, 240, 240, 255))
            if vm.is_saved and sf is not None:
                draw.text((self.ui.saved_x, self.ui.saved_y), "SAVED", font=sf, fill=(95, 255, 95, 255))
            if vm.is_loaded and lf is not None:
                draw.text((self.ui.load_x, self.ui.load_y), "LOAD", font=lf, fill=(85, 170, 255, 255))

        photo = ImageTk.PhotoImage(img)
        self.photo_cache[cache_key] = photo
        return photo


# ======================================================================================
# WIDGET SLOTU
# ======================================================================================

class SlotWidget(tk.Frame):
    def __init__(self, master: tk.Misc, app: "TarzanEhrTakeSandboxWindow", vm: SlotVM) -> None:
        super().__init__(master, bg=app.protocol_bg(), highlightthickness=0, bd=0)
        self.app = app
        self.vm = vm
        self.hovered = False
        self.slot_photo_ref = None
        self.icon_hitbox: Optional[tuple[int, int, int, int]] = None
        self.action_hitbox: Optional[tuple[int, int, int, int]] = None
        self.save_button: Optional[tk.Button] = None
        self.save_button_window: Optional[int] = None

        self.canvas = tk.Canvas(
            self,
            width=app.ui.icon_width,
            height=app.ui.icon_height + 65,
            bg=app.protocol_bg(),
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
        self.configure(bg=self.app.protocol_bg())
        self.canvas.configure(
            bg=self.app.protocol_bg(),
            width=self.app.ui.icon_width,
            height=self.app.ui.icon_height + 65,
        )
        self.canvas.delete("all")
        self.action_hitbox = None
        self.save_button = None
        self.save_button_window = None

        top_y = 24

        self.slot_photo_ref = self.app.renderer.build_slot_photo(self.vm)
        self.canvas.create_image(self.app.ui.icon_width / 2, top_y + self.app.ui.icon_height / 2, image=self.slot_photo_ref)
        self.icon_hitbox = (0, top_y, self.app.ui.icon_width, top_y + self.app.ui.icon_height)

        save_visible = self.vm.state == SlotState.ACTIVE and not self.vm.is_saved
        show_hand = self.hovered and self.vm.state == SlotState.LINKED and not save_visible

        if save_visible:
            self._draw_save_button(top_y)

        if show_hand:
            self._draw_action(top_y)

    def _draw_action(self, top_y: int) -> None:
        x = self.app.ui.action_x
        y = top_y + self.app.ui.action_y
        item = self.canvas.create_text(
            x,
            y,
            text=self.app.ui.action_icon_text,
            anchor="nw",
            fill="#F04343",
            font=("Segoe UI Emoji", self.app.ui.action_font_size),
        )
        self.action_hitbox = self.canvas.bbox(item)

    def _draw_save_button(self, top_y: int) -> None:
        ui = self.app.ui
        x = int((ui.icon_width - ui.save_width) / 2 + ui.save_offset_x)
        y = int(max(0, top_y - ui.save_offset_y - ui.save_height))

        self.save_button = tk.Button(
            self.canvas,
            text="SAVE",
            command=lambda idx=self.vm.index: self.app.on_save_clicked(idx),
            bg=BTN_GREEN,
            fg=SAVE_GREEN_FG,
            activebackground=BTN_GREEN_ACTIVE,
            activeforeground=SAVE_GREEN_FG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=8,
            pady=0,
            font=("Segoe UI Semibold", self.app.ui.save_font_size),
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
        if rect is None:
            return False
        l, t, r, b = rect
        return l <= x <= r and t <= y <= b

    def _on_motion(self, event: tk.Event) -> None:
        inside = self._inside(event.x, event.y, self.icon_hitbox)
        if inside != self.hovered:
            self.hovered = inside
            self.redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        if self.hovered:
            self.hovered = False
            self.redraw()

    def _on_click(self, event: tk.Event) -> None:
        if self._inside(event.x, event.y, self.action_hitbox):
            self.app.on_action_clicked(self.vm.index)
            return
        if self.vm.state == SlotState.ACTIVE:
            return
        if self._inside(event.x, event.y, self.icon_hitbox):
            self.app.on_slot_clicked(self.vm.index)

    def set_vm(self, vm: SlotVM) -> None:
        self.vm = vm
        self.redraw()


# ======================================================================================
# GŁÓWNE OKNO
# ======================================================================================

class TarzanEhrTakeSandboxWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        ensure_dirs()

        self.store = SlotStore.load_or_default(SLOTS_JSON_PATH)
        self.ui = UiSettings.load_or_default(UI_JSON_PATH)
        self.ui.controls_columns = 4
        self.ui.clamp()
        self.renderer = IconRenderer(self.ui)

        self.title("TARZAN — TAKE PROTOCOL SANDBOX")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1700, 940)
        self.configure(bg=WINDOW_BG)

        self.status_var = tk.StringVar(value="Gotowy.")
        self.setting_vars: dict[str, tk.Variable] = {}
        self.slot_widgets: list[SlotWidget] = []

        self.slot_models = self._build_models()
        self._build_ui()
        self._populate_controls()
        self._render_all()

    def protocol_bg(self) -> str:
        return PROTOCOL_INNER_BG

    def _build_models(self) -> list[SlotVM]:
        out: list[SlotVM] = []
        for i in range(SLOT_COUNT):
            vm = SlotVM(index=i)
            record = self.store.slots[i]
            p = take_path_from_record(record.path)
            if p is not None:
                vm.file_path = p
                vm.take_number = read_take_number(p, self.ui.number_digits)
                vm.state = SlotState.LINKED
            out.append(vm)

        if self.store.active_slot is not None and 0 <= self.store.active_slot < SLOT_COUNT:
            vm = out[self.store.active_slot]
            if vm.file_path is not None:
                vm.state = SlotState.ACTIVE
                vm.is_loaded = True
        return out

    def _build_ui(self) -> None:
        root = tk.Frame(self, bg=WINDOW_BG)
        root.pack(fill="both", expand=True)

        title_bar = tk.Frame(root, bg=HEADER_BG, height=TITLE_HEIGHT)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)
        tk.Label(
            title_bar,
            text="TARZAN — TAKE PROTOCOL SANDBOX",
            bg=HEADER_BG,
            fg=TEXT,
            anchor="w",
            padx=10,
            font=("Segoe UI Semibold", 17),
        ).pack(fill="both", expand=True)

        self.protocol_holder = tk.Frame(root, bg=PROTOCOL_OUTER_BG, height=self.ui.protocol_height)
        self.protocol_holder.pack(fill="x", side="top")
        self.protocol_holder.pack_propagate(False)

        self.protocol_canvas = tk.Canvas(self.protocol_holder, bg=PROTOCOL_OUTER_BG, highlightthickness=0, bd=0, relief="flat")
        self.protocol_canvas.pack(fill="both", expand=True)
        self.protocol_canvas.bind("<Configure>", lambda _e: self._layout_protocol())

        self.protocol_title_id = self.protocol_canvas.create_text(
            0, 0,
            text="TAKE PROTOCOL",
            fill=TEXT,
            anchor="n",
            font=("Segoe UI Light", 34),
        )

        self.row_frame = tk.Frame(self.protocol_canvas, bg=self.protocol_bg())
        self.row_window = self.protocol_canvas.create_window(0, 0, window=self.row_frame, anchor="n")

        self.controls_wrap = tk.Frame(root, bg=CONTROLS_BG, height=self.ui.controls_height)
        self.controls_wrap.pack(fill="both", expand=True, side="top")
        self.controls_wrap.pack_propagate(False)
        self._build_controls(self.controls_wrap)

        status_bar = tk.Frame(root, bg=STATUS_BG, height=STATUS_HEIGHT)
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

    def _build_controls(self, parent: tk.Misc) -> None:
        outer = tk.Frame(parent, bg=CONTROLS_BG)
        outer.pack(fill="both", expand=True, padx=10, pady=8)

        columns: list[tk.Frame] = []
        for _ in range(4):
            col = tk.Frame(outer, bg=CONTROLS_BG)
            col.pack(side="left", fill="both", expand=True, padx=5)
            columns.append(col)

        sections = [
            ("NUMER TAKE", [
                ("number_x", 0, 220),
                ("number_y", 0, 220),
                ("number_font_size", 8, 140),
                ("number_digits", 1, 6),
                ("number_dx", -80, 80),
                ("number_dy", -80, 80),
            ]),
            ("EDIT / SAVED / LOAD", [
                ("edit_x", 0, 220),
                ("edit_y", 0, 220),
                ("edit_font_size", 6, 32),
                ("saved_x", 0, 220),
                ("saved_y", 0, 220),
                ("saved_font_size", 6, 32),
                ("load_x", 0, 220),
                ("load_y", 0, 220),
                ("load_font_size", 6, 32),
            ]),
            ("SAVE / BUTTON", [
                ("save_offset_x", -120, 120),
                ("save_offset_y", -120, 120),
                ("save_width", 40, 260),
                ("save_height", 18, 80),
                ("save_font_size", 8, 36),
            ]),
            ("AKCJA / PANEL", [
                ("icon_width", 96, 280),
                ("icon_height", 96, 280),
                ("row_pad_x", 0, 30),
                ("action_x", -20, 120),
                ("action_y", -20, 120),
                ("action_font_size", 8, 48),
                ("protocol_title_y", 10, 180),
                ("protocol_height", 180, 520),
                ("row_center_y", 80, 360),
                ("protocol_inner_pad_x", 0, 80),
                ("controls_height", 220, 760),
                ("slider_length", 110, 260),
            ]),
        ]

        for index, (title, items) in enumerate(sections):
            box = tk.Frame(columns[index], bg=SECTION_BG, highlightthickness=1, highlightbackground=SECTION_BORDER)
            box.pack(fill="x", pady=6)
            tk.Label(
                box,
                text=title,
                bg=SECTION_BG,
                fg=TEXT,
                anchor="w",
                padx=10,
                pady=8,
                font=("Segoe UI Semibold", 10),
            ).pack(fill="x")
            inner = tk.Frame(box, bg=SECTION_BG)
            inner.pack(fill="x", padx=8, pady=(0, 8))
            for key, lo, hi in items:
                self._make_slider(inner, key, lo, hi)

        action_box = tk.Frame(columns[3], bg=SECTION_BG, highlightthickness=1, highlightbackground=SECTION_BORDER)
        action_box.pack(fill="x", pady=6)
        tk.Label(
            action_box,
            text="IKONA AKCJI",
            bg=SECTION_BG,
            fg=TEXT,
            anchor="w",
            padx=10,
            pady=8,
            font=("Segoe UI Semibold", 10),
        ).pack(fill="x")

        action_inner = tk.Frame(action_box, bg=SECTION_BG)
        action_inner.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(action_inner, text="ACTION ICON TEXT", bg=SECTION_BG, fg=MUTED, anchor="w", font=("Segoe UI", 9)).pack(fill="x")
        self.setting_vars["action_icon_text"] = tk.StringVar(value=self.ui.action_icon_text)
        entry = tk.Entry(
            action_inner,
            textvariable=self.setting_vars["action_icon_text"],
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10),
        )
        entry.pack(fill="x", pady=(4, 8))
        entry.bind("<KeyRelease>", lambda _e: self.apply_settings())

        btn_row = tk.Frame(columns[3], bg=CONTROLS_BG)
        btn_row.pack(fill="x", pady=6)
        tk.Button(
            btn_row,
            text="ZASTOSUJ",
            command=self.apply_settings,
            bg=INPUT_BG,
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(
            btn_row,
            text="ZAPISZ JSON",
            command=self.save_ui_json,
            bg=INPUT_BG,
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _make_slider(self, parent: tk.Misc, key: str, lo: int, hi: int) -> None:
        row = tk.Frame(parent, bg=SECTION_BG)
        row.pack(fill="x", pady=2)

        tk.Label(
            row,
            text=key.replace("_", " ").upper(),
            bg=SECTION_BG,
            fg=MUTED,
            anchor="w",
            width=16,
            font=("Segoe UI", 8),
        ).pack(side="left")

        var = tk.IntVar(value=int(getattr(self.ui, key)))
        self.setting_vars[key] = var

        scale = tk.Scale(
            row,
            variable=var,
            from_=lo,
            to=hi,
            orient="horizontal",
            showvalue=True,
            resolution=1,
            length=self.ui.slider_length,
            bg=SECTION_BG,
            fg=TEXT,
            troughcolor=INPUT_BG,
            highlightthickness=0,
            bd=0,
            command=lambda _v: self.apply_settings(),
        )
        scale.pack(side="left", fill="x", expand=True)

    def _populate_controls(self) -> None:
        for key, var in self.setting_vars.items():
            try:
                var.set(getattr(self.ui, key))
            except Exception:
                pass

    def apply_settings(self) -> None:
        for key, var in self.setting_vars.items():
            try:
                setattr(self.ui, key, var.get())
            except Exception:
                pass
        self.ui.controls_columns = 4
        self.ui.clamp()
        self.renderer.set_ui(self.ui)

        for vm in self.slot_models:
            if vm.file_path is not None:
                vm.take_number = read_take_number(vm.file_path, self.ui.number_digits)

        self.controls_wrap.configure(height=self.ui.controls_height)
        self.protocol_holder.configure(height=self.ui.protocol_height)
        self._rebuild_slot_row()
        self._layout_protocol()
        self.status_var.set("Zastosowano ustawienia UI sandboxa.")

    def save_ui_json(self) -> None:
        self.apply_settings()
        self.ui.save(UI_JSON_PATH)
        self.status_var.set("Zapisano ustawienia UI do JSON.")

    def _save_slots_json(self) -> None:
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

    def on_slot_clicked(self, idx: int) -> None:
        vm = self.slot_models[idx]
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
            self.status_var.set(f"Błąd importu TAKE: {exc}")
            return

        vm.file_path = dst
        vm.take_number = read_take_number(dst, self.ui.number_digits)
        vm.state = SlotState.LINKED
        vm.is_saved = False
        vm.is_loaded = False

        self._save_slots_json()
        self._refresh_slot(idx)
        self.status_var.set(f"TAKE {vm.take_number} podpięty.")

    def on_action_clicked(self, idx: int) -> None:
        vm = self.slot_models[idx]
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
        if old_active is not None:
            self._refresh_slot(old_active)
        self._refresh_slot(idx)
        self.status_var.set(f"TAKE {vm.take_number} aktywowany. LOAD=ON.")

    def on_save_clicked(self, idx: int) -> None:
        vm = self.slot_models[idx]
        if vm.state != SlotState.ACTIVE:
            return
        vm.is_saved = True
        self._refresh_slot(idx)
        self.status_var.set(f"TAKE {vm.take_number} zapisany. SAVED=ON.")

    def notify_active_take_modified(self) -> None:
        """
        Metoda do późniejszego spięcia z EHR.
        Gdy oś zostanie ruszona / TAKE się zmieni:
        - aktywny TAKE wraca z zielonego do czerwonego
        - znika SAVED
        - wraca przycisk SAVE
        """
        for idx, vm in enumerate(self.slot_models):
            if vm.state == SlotState.ACTIVE:
                vm.is_saved = False
                vm.is_loaded = True
                self._refresh_slot(idx)
                self.status_var.set(f"TAKE {vm.take_number} zmieniony. SAVE ponownie wymagany.")
                break

    def _rebuild_slot_row(self) -> None:
        for widget in self.slot_widgets:
            widget.destroy()
        self.slot_widgets.clear()

        self.row_frame.destroy()
        self.row_frame = tk.Frame(self.protocol_canvas, bg=self.protocol_bg())
        self.row_window = self.protocol_canvas.create_window(0, 0, window=self.row_frame, anchor="n")

        for idx in range(SLOT_COUNT):
            widget = SlotWidget(self.row_frame, self, self.slot_models[idx])
            widget.pack(side="left", padx=self.ui.row_pad_x, pady=0)
            self.slot_widgets.append(widget)

    def _render_all(self) -> None:
        self._rebuild_slot_row()
        self._layout_protocol()

    def _refresh_slot(self, idx: int) -> None:
        if 0 <= idx < len(self.slot_widgets):
            self.slot_widgets[idx].set_vm(self.slot_models[idx])

    def _layout_protocol(self) -> None:
        w = max(900, int(self.protocol_canvas.winfo_width() or 1200))
        h = max(240, int(self.protocol_canvas.winfo_height() or self.ui.protocol_height))

        self.protocol_canvas.delete("band_bg")
        inner = self.ui.protocol_inner_pad_x

        self.protocol_canvas.create_rectangle(0, 0, w, h, fill=PROTOCOL_OUTER_BG, outline="", tags="band_bg")
        self.protocol_canvas.create_rectangle(inner, 0, w - inner, h, fill=PROTOCOL_INNER_BG, outline="", tags="band_bg")

        self.protocol_canvas.coords(self.protocol_title_id, w / 2, self.ui.protocol_title_y)
        self.protocol_canvas.itemconfigure(self.protocol_title_id, fill=TEXT, font=("Segoe UI Light", 34))
        self.protocol_canvas.coords(self.row_window, w / 2, self.ui.row_center_y)

    def run(self) -> None:
        self.mainloop()


# ======================================================================================
# MAIN
# ======================================================================================

def main() -> None:
    ensure_dirs()
    app = TarzanEhrTakeSandboxWindow()
    app.run()


if __name__ == "__main__":
    main()
