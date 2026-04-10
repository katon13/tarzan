from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    PIL_OK = True
except Exception:
    Image = ImageDraw = ImageFont = ImageTk = None
    PIL_OK = False

THIS_FILE = Path(__file__).resolve()
EDITOR_DIR = THIS_FILE.parent
PROJECT_DIR = EDITOR_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

try:
    from core.tarzanAssets import take_icon as project_take_icon
except Exception:
    project_take_icon = None

APP_TITLE = "TARZAN — TAKE PROTOCOL SANDBOX"
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
HEADER_H = 56
STATUS_H = 34
SLOT_COUNT = 10

BG = "#0A1220"
HEADER_BG = "#08111E"
TEXT = "#F0F4F8"
MUTED = "#A8B4C3"
PANEL_BG = "#101B2D"
PANEL_SECTION = "#0E1828"
PANEL_BORDER = "#24324C"
INPUT_BG = "#1B2942"
STATUS_BG = "#091220"
PROTOCOL_BG = "#122034"
PROTOCOL_BAND = "#16263B"
BUTTON_BG = "#243654"
BUTTON_BG_HOVER = "#31456B"
BUTTON_TEXT = "#F5F7FA"
SAVE_BG = "#2E8B57"
SAVE_BG_HOVER = "#3AA565"
SAVE_TEXT = "#FFFFFF"

TAKE_DIR = PROJECT_DIR / "data" / "take"
EHR_DIR = PROJECT_DIR / "data" / "ehr"
SLOTS_JSON = EHR_DIR / "take_protocol_slots.json"
UI_JSON = EHR_DIR / "take_protocol_ui_settings.json"
FONT_PATH = PROJECT_DIR / "font" / "Pattifont.ttf"


class SlotState:
    EMPTY = "empty"
    LINKED = "linked"
    ACTIVE = "active"


@dataclass
class UiSettings:
    protocol_title_font_size: int = 34
    protocol_title_y: int = 58
    protocol_row_center_y: int = 275
    row_pad_x: int = 6
    row_pad_y: int = 0
    icon_width: int = 169
    icon_height: int = 168
    slot_canvas_extra_top: int = 90
    slot_canvas_extra_bottom: int = 40
    number_x: int = 86
    number_y: int = 89
    number_font_size: int = 72
    number_digits: int = 3
    number_dx: int = 0
    number_dy: int = 0
    edit_x: int = 16
    edit_y: int = 128
    edit_font_size: int = 12
    saved_x: int = 78
    saved_y: int = 128
    saved_font_size: int = 12
    load_x: int = 132
    load_y: int = 128
    load_font_size: int = 12
    save_offset_x: int = 0
    save_offset_y: int = 18
    save_width: int = 156
    save_height: int = 34
    save_font_size: int = 16
    action_x: int = 12
    action_y: int = 6
    action_font_size: int = 18
    action_text: str = "🎬"
    save_icon_x: int = 12
    save_icon_y: int = 6
    save_icon_size: int = 64
    save_icon_text: str = "save"
    hit_expand_x: int = 8
    hit_expand_y: int = 8

    def clamp(self) -> None:
        for f in fields(self):
            if f.type == int:
                setattr(self, f.name, int(getattr(self, f.name)))
        self.protocol_title_font_size = max(18, min(64, self.protocol_title_font_size))
        self.protocol_title_y = max(10, min(180, self.protocol_title_y))
        self.protocol_row_center_y = max(120, min(700, self.protocol_row_center_y))
        self.row_pad_x = max(0, min(40, self.row_pad_x))
        self.row_pad_y = max(0, min(40, self.row_pad_y))
        self.icon_width = max(80, min(320, self.icon_width))
        self.icon_height = max(80, min(320, self.icon_height))
        self.slot_canvas_extra_top = max(20, min(200, self.slot_canvas_extra_top))
        self.slot_canvas_extra_bottom = max(10, min(140, self.slot_canvas_extra_bottom))
        self.number_font_size = max(12, min(200, self.number_font_size))
        self.number_digits = max(1, min(6, self.number_digits))
        self.edit_font_size = max(6, min(48, self.edit_font_size))
        self.saved_font_size = max(6, min(48, self.saved_font_size))
        self.load_font_size = max(6, min(48, self.load_font_size))
        self.save_width = max(60, min(300, self.save_width))
        self.save_height = max(20, min(80, self.save_height))
        self.save_font_size = max(8, min(36, self.save_font_size))
        self.action_font_size = max(8, min(64, self.action_font_size))
        self.save_icon_size = max(16, min(320, self.save_icon_size))
        self.action_text = str(self.action_text or "🎬")
        self.save_icon_text = str(self.save_icon_text or "save")

    @classmethod
    def load_or_default(cls, path: Path) -> "UiSettings":
        settings = cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for f in fields(settings):
                if f.name in raw:
                    setattr(settings, f.name, raw[f.name])
        except Exception:
            pass
        settings.clamp()
        return settings

    def save(self, path: Path) -> None:
        self.clamp()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class SlotRecord:
    path: Optional[str] = None


@dataclass
class SlotStore:
    slots: list[SlotRecord]
    active_slot: Optional[int] = None

    @classmethod
    def load_or_default(cls, path: Path) -> "SlotStore":
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            slots_raw = raw.get("slots") or []
            slots = []
            for i in range(SLOT_COUNT):
                item = slots_raw[i] if i < len(slots_raw) else {}
                slots.append(SlotRecord(path=(item or {}).get("path")))
            active = raw.get("active_slot")
            if not isinstance(active, int):
                active = None
            return cls(slots=slots, active_slot=active)
        except Exception:
            return cls(slots=[SlotRecord() for _ in range(SLOT_COUNT)], active_slot=None)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"slots": [asdict(s) for s in self.slots], "active_slot": self.active_slot}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class SlotModel:
    index: int
    file_path: Optional[Path] = None
    state: str = SlotState.EMPTY
    take_number: str = ""
    is_saved: bool = False
    is_loaded: bool = False


def ensure_dirs() -> None:
    TAKE_DIR.mkdir(parents=True, exist_ok=True)
    EHR_DIR.mkdir(parents=True, exist_ok=True)


def safe_relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_take_number(path: Path, digits: int) -> str:
    try:
        raw = read_json(path)
        take_id = (((raw.get("metadata") or {}).get("take_id")) or "")
        match = re.search(r"(\d+)", str(take_id))
        if match:
            return match.group(1).zfill(digits)
    except Exception:
        pass
    match = re.search(r"TAKE[_\- ]?(\d+)", path.name, flags=re.IGNORECASE)
    if not match:
        match = re.search(r"(\d+)", path.name)
    if match:
        return match.group(1).zfill(digits)
    return "---".zfill(digits)


def copy_take_to_project(src: Path) -> Path:
    ensure_dirs()
    dst = TAKE_DIR / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
        return dst
    stem = src.stem
    suffix = src.suffix or ".json"
    i = 1
    while True:
        candidate = TAKE_DIR / f"{stem}_import_{i:02d}{suffix}"
        if not candidate.exists():
            shutil.copy2(src, candidate)
            return candidate
        i += 1


def try_project_take_icon(state: str, size: int) -> Optional[Path]:
    img_take_dir = PROJECT_DIR / "img" / "take"
    candidates = []
    if project_take_icon is not None:
        try:
            candidates.append(Path(project_take_icon(size=size, state=state)))
        except Exception:
            pass
    candidates.extend([
        img_take_dir / f"take_{state}_{size}.png",
        img_take_dir / f"take_{state}_320.png",
        img_take_dir / f"take_{state}_256.png",
        img_take_dir / f"take_{state}_128.png",
        img_take_dir / "take_icon_01.png",
        img_take_dir / "take_icon_02.png",
    ])
    for c in candidates:
        if c.exists():
            return c
    return None


def try_save_icon(size: int) -> Optional[Path]:
    candidates = [
        PROJECT_DIR / "img" / "take" / f"take_save_{size}.png",
        PROJECT_DIR / "img" / "take" / "take_save_320png.png",
        PROJECT_DIR / "img" / "take" / "take_save_320.png",
        Path("/mnt/data") / f"take_save_{size}.png",
        Path("/mnt/data") / "take_save_320png.png",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def pil_font(size: int, prefer_chalk: bool = False):
    if not PIL_OK:
        return None
    if prefer_chalk and FONT_PATH.exists():
        try:
            return ImageFont.truetype(str(FONT_PATH), size=size)
        except Exception:
            pass
    for name in ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "Verdana.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


class SlotRenderer:
    def __init__(self, ui: UiSettings):
        self.ui = ui
        self._base_cache = {}
        self._render_cache = {}
        self._save_icon_cache = {}

    def update_ui(self, ui: UiSettings) -> None:
        self.ui = ui
        self._render_cache.clear()
        self._base_cache.clear()

    def _base(self, state: str):
        key = (state, self.ui.icon_width, self.ui.icon_height)
        if key in self._base_cache:
            cached = self._base_cache[key]
            return cached.copy() if cached is not None else None
        if not PIL_OK:
            self._base_cache[key] = None
            return None
        path_state = "open" if state in (SlotState.EMPTY, SlotState.LINKED) else "active"
        path = try_project_take_icon(path_state, max(self.ui.icon_width, self.ui.icon_height))
        if path and path.exists():
            img = Image.open(path).convert("RGBA").resize((self.ui.icon_width, self.ui.icon_height), Image.LANCZOS)
        else:
            img = Image.new("RGBA", (self.ui.icon_width, self.ui.icon_height), (0, 0, 0, 255))
            d = ImageDraw.Draw(img)
            if state == SlotState.ACTIVE:
                d.rectangle((0, 0, self.ui.icon_width - 1, 28), fill=(180, 0, 0, 255))
            d.rectangle((10, self.ui.icon_height - 30, self.ui.icon_width - 10, self.ui.icon_height - 10), outline=(240, 240, 240, 255), width=2)
        self._base_cache[key] = img
        return img.copy()

    def save_icon_image(self):
        key = self.ui.save_icon_size
        if key in self._save_icon_cache:
            return self._save_icon_cache[key]
        if not PIL_OK:
            self._save_icon_cache[key] = None
            return None
        path = try_save_icon(self.ui.save_icon_size)
        if path and path.exists():
            img = Image.open(path).convert("RGBA").resize((self.ui.save_icon_size, self.ui.save_icon_size), Image.LANCZOS)
            self._save_icon_cache[key] = img
            return img
        self._save_icon_cache[key] = None
        return None

    def render(self, slot: SlotModel):
        key = (
            slot.state, slot.take_number, slot.is_saved, slot.is_loaded,
            self.ui.icon_width, self.ui.icon_height,
            self.ui.number_x, self.ui.number_y, self.ui.number_font_size, self.ui.number_digits,
            self.ui.number_dx, self.ui.number_dy,
            self.ui.edit_x, self.ui.edit_y, self.ui.edit_font_size,
            self.ui.saved_x, self.ui.saved_y, self.ui.saved_font_size,
            self.ui.load_x, self.ui.load_y, self.ui.load_font_size,
        )
        if key in self._render_cache:
            return self._render_cache[key]
        if not PIL_OK:
            self._render_cache[key] = None
            return None
        img = self._base(slot.state)
        d = ImageDraw.Draw(img)
        if slot.state != SlotState.EMPTY and slot.take_number:
            text = slot.take_number.zfill(self.ui.number_digits)
            font = pil_font(self.ui.number_font_size, prefer_chalk=True)
            if font is not None:
                bbox = d.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                x = int(self.ui.number_x - tw / 2 + self.ui.number_dx)
                y = int(self.ui.number_y - th / 2 + self.ui.number_dy)
                for ox, oy in [(0, 0), (1, 0), (0, 1)]:
                    d.text((x + ox, y + oy), text, font=font, fill=(250, 250, 250, 255))
        if slot.state == SlotState.ACTIVE:
            font_edit = pil_font(self.ui.edit_font_size, prefer_chalk=False)
            font_saved = pil_font(self.ui.saved_font_size, prefer_chalk=False)
            font_load = pil_font(self.ui.load_font_size, prefer_chalk=False)
            if font_edit is not None:
                d.text((self.ui.edit_x, self.ui.edit_y), "EDIT", font=font_edit, fill=(245, 245, 245, 255))
            if slot.is_saved and font_saved is not None:
                d.text((self.ui.saved_x, self.ui.saved_y), "SAVED", font=font_saved, fill=(120, 255, 120, 255))
            if slot.is_loaded and font_load is not None:
                d.text((self.ui.load_x, self.ui.load_y), "LOAD", font=font_load, fill=(255, 220, 120, 255))
        photo = ImageTk.PhotoImage(img)
        self._render_cache[key] = photo
        return photo


class TakeSlot(tk.Frame):
    def __init__(self, master, app: "TarzanEhrTakeSandboxWindow", model: SlotModel):
        super().__init__(master, bg=PROTOCOL_BG, highlightthickness=0, bd=0)
        self.app = app
        self.model = model
        self.hover = False
        self.photo = None
        self.action_id = None
        self.action_hit = None
        self.icon_hit = None
        self._save_icon_refs = []
        self.canvas = tk.Canvas(self, width=app.ui.icon_width,
                                height=app.ui.slot_canvas_extra_top + app.ui.icon_height + app.ui.slot_canvas_extra_bottom,
                                bg=PROTOCOL_BG, highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack()
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)
        self.save_btn = None
        self.save_btn_window = None
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        self._save_icon_refs.clear()
        self.action_hit = None
        self.icon_hit = None
        self.save_btn = None
        self.save_btn_window = None
        top = self.app.ui.slot_canvas_extra_top
        self.photo = self.app.renderer.render(self.model)
        if self.photo is not None:
            self.canvas.create_image(self.app.ui.icon_width / 2, top + self.app.ui.icon_height / 2, image=self.photo)
        else:
            self.canvas.create_rectangle(0, top, self.app.ui.icon_width, top + self.app.ui.icon_height, fill="black", outline="")
        self.icon_hit = (-self.app.ui.hit_expand_x, top - self.app.ui.hit_expand_y,
                         self.app.ui.icon_width + self.app.ui.hit_expand_x,
                         top + self.app.ui.icon_height + self.app.ui.hit_expand_y)
        if self.model.state == SlotState.ACTIVE:
            self.draw_save_button()
        if self.hover and self.model.state in (SlotState.LINKED, SlotState.ACTIVE):
            self.draw_action()

    def draw_save_button(self):
        x = int((self.app.ui.icon_width - self.app.ui.save_width) / 2 + self.app.ui.save_offset_x)
        y = int(self.app.ui.slot_canvas_extra_top - self.app.ui.save_height - self.app.ui.save_offset_y)
        if y < 0:
            y = 0
        save_icon = self.app.renderer.save_icon_image()
        if save_icon is not None and PIL_OK:
            photo = ImageTk.PhotoImage(save_icon)
            self._save_icon_refs.append(photo)
            self.canvas.create_image(self.app.ui.save_icon_x, self.app.ui.save_icon_y, image=photo, anchor="nw")
        btn = tk.Button(self.canvas, text="SAVE", command=lambda idx=self.model.index: self.app.on_save(idx),
                        bg=SAVE_BG, fg=SAVE_TEXT, activebackground=SAVE_BG_HOVER, activeforeground=SAVE_TEXT,
                        relief="flat", bd=1, highlightthickness=1, highlightbackground=PANEL_BORDER,
                        font=("Segoe UI Semibold", self.app.ui.save_font_size), cursor="hand2")
        self.save_btn = btn
        self.save_btn_window = self.canvas.create_window(x, y, width=self.app.ui.save_width,
                                                         height=self.app.ui.save_height, window=btn, anchor="nw")

    def draw_action(self):
        x = self.app.ui.action_x
        y = self.app.ui.slot_canvas_extra_top + self.app.ui.action_y
        self.action_id = self.canvas.create_text(x, y, text=self.app.ui.action_text, anchor="nw",
                                                 fill="#F34B4B", font=("Segoe UI Emoji", self.app.ui.action_font_size))
        bbox = self.canvas.bbox(self.action_id)
        if bbox:
            self.action_hit = bbox

    def contains(self, x, y, rect):
        if rect is None:
            return False
        l, t, r, b = rect
        return l <= x <= r and t <= y <= b

    def on_motion(self, event):
        new_hover = self.contains(event.x, event.y, self.icon_hit)
        if new_hover != self.hover:
            self.hover = new_hover
            self.redraw()

    def on_leave(self, _event):
        if self.hover:
            self.hover = False
            self.redraw()

    def on_click(self, event):
        if self.contains(event.x, event.y, self.action_hit):
            self.app.on_action(self.model.index)
            return
        if self.model.state == SlotState.ACTIVE:
            return
        if self.contains(event.x, event.y, self.icon_hit):
            self.app.on_slot(self.model.index)


class TarzanEhrTakeSandboxWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.ui = UiSettings.load_or_default(UI_JSON)
        self.store = SlotStore.load_or_default(SLOTS_JSON)
        self.renderer = SlotRenderer(self.ui)
        self.status_var = tk.StringVar(value="Gotowy.")
        self.vars = {}
        self.slots: list[SlotModel] = []
        self.slot_widgets: list[TakeSlot] = []
        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1100, 1900)
        self.configure(bg=BG)
        self.build_models()
        self.build_ui()
        self.fill_controls()
        self.render_slots()
        self.layout_protocol()

    def build_models(self):
        self.slots.clear()
        for i in range(SLOT_COUNT):
            rec = self.store.slots[i] if i < len(self.store.slots) else SlotRecord()
            model = SlotModel(index=i)
            if rec.path:
                p = PROJECT_DIR / rec.path if not Path(rec.path).is_absolute() else Path(rec.path)
                if p.exists():
                    model.file_path = p
                    model.take_number = extract_take_number(p, self.ui.number_digits)
                    model.state = SlotState.LINKED
            self.slots.append(model)
        if isinstance(self.store.active_slot, int) and 0 <= self.store.active_slot < SLOT_COUNT:
            active = self.slots[self.store.active_slot]
            if active.file_path is not None:
                active.state = SlotState.ACTIVE
                active.is_loaded = True

    def build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)
        header = tk.Frame(root, bg=HEADER_BG, height=HEADER_H)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text=APP_TITLE, bg=HEADER_BG, fg=TEXT, anchor="w", padx=10,
                 font=("Segoe UI Semibold", 18)).pack(fill="both", expand=True)
        main = tk.Frame(root, bg=BG)
        main.pack(fill="both", expand=True)
        self.protocol_wrap = tk.Frame(main, bg=PROTOCOL_BG)
        self.protocol_wrap.pack(fill="both", expand=True)
        self.protocol_canvas = tk.Canvas(self.protocol_wrap, bg=PROTOCOL_BG, highlightthickness=0, bd=0)
        self.protocol_canvas.pack(fill="both", expand=True)
        self.protocol_canvas.bind("<Configure>", lambda _e: self.layout_protocol())
        self.protocol_title = self.protocol_canvas.create_text(0, 0, text="TAKE PROTOCOL", fill=TEXT,
                                                               font=("Segoe UI Light", self.ui.protocol_title_font_size), anchor="n")
        self.row_frame = tk.Frame(self.protocol_canvas, bg=PROTOCOL_BG)
        self.row_win = self.protocol_canvas.create_window(0, 0, window=self.row_frame, anchor="n")
        self.controls_wrap = tk.Frame(root, bg=PANEL_BG, height=320)
        self.controls_wrap.pack(fill="x", side="bottom")
        self.controls_wrap.pack_propagate(False)
        self.build_bottom_controls(self.controls_wrap)
        status = tk.Frame(root, bg=STATUS_BG, height=STATUS_H)
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)
        tk.Label(status, textvariable=self.status_var, bg=STATUS_BG, fg=TEXT, anchor="w", padx=10,
                 font=("Segoe UI", 10)).pack(fill="both", expand=True)

    def build_bottom_controls(self, parent):
        top = tk.Frame(parent, bg=PANEL_BG)
        top.pack(fill="both", expand=True, padx=10, pady=10)
        left = tk.Frame(top, bg=PANEL_BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(top, bg=PANEL_BG)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        sec1 = tk.LabelFrame(left, text="NUMER TAKE", bg=PANEL_SECTION, fg=TEXT, bd=1, relief="solid", font=("Segoe UI Semibold", 10), labelanchor="n")
        sec1.pack(fill="x", pady=(0, 8))
        for k, a, b in [("number_x",0,250),("number_y",0,220),("number_font_size",12,160),("number_digits",1,6),("number_dx",-100,100),("number_dy",-100,100)]:
            self.slider(sec1, k, a, b)

        sec2 = tk.LabelFrame(left, text="STATUSY TABLICZKI", bg=PANEL_SECTION, fg=TEXT, bd=1, relief="solid", font=("Segoe UI Semibold", 10), labelanchor="n")
        sec2.pack(fill="x", pady=(0, 8))
        for k, a, b in [("edit_x",0,250),("edit_y",0,220),("edit_font_size",6,32),("saved_x",0,250),("saved_y",0,220),("saved_font_size",6,32),("load_x",0,250),("load_y",0,220),("load_font_size",6,32)]:
            self.slider(sec2, k, a, b)

        sec3 = tk.LabelFrame(right, text="SAVE / AKCJA", bg=PANEL_SECTION, fg=TEXT, bd=1, relief="solid", font=("Segoe UI Semibold", 10), labelanchor="n")
        sec3.pack(fill="x", pady=(0, 8))
        for k, a, b in [("save_offset_x",-150,150),("save_offset_y",-50,150),("save_width",60,260),("save_height",20,70),("save_font_size",8,28),("action_x",0,180),("action_y",0,120),("action_font_size",8,52),("save_icon_x",0,180),("save_icon_y",0,120),("save_icon_size",16,160)]:
            self.slider(sec3, k, a, b)

        sec4 = tk.LabelFrame(right, text="UKŁAD", bg=PANEL_SECTION, fg=TEXT, bd=1, relief="solid", font=("Segoe UI Semibold", 10), labelanchor="n")
        sec4.pack(fill="x", pady=(0, 8))
        for k, a, b in [("icon_width",100,260),("icon_height",100,260),("slot_canvas_extra_top",20,180),("slot_canvas_extra_bottom",10,100),("row_pad_x",0,20),("row_pad_y",0,20),("protocol_title_font_size",18,60),("protocol_title_y",20,140),("protocol_row_center_y",120,500)]:
            self.slider(sec4, k, a, b)

        actions = tk.Frame(parent, bg=PANEL_BG)
        actions.pack(fill="x", padx=10, pady=(0, 10))
        action_text_var = tk.StringVar(value=self.ui.action_text)
        self.vars["action_text"] = action_text_var
        save_icon_text_var = tk.StringVar(value=self.ui.save_icon_text)
        self.vars["save_icon_text"] = save_icon_text_var
        tk.Label(actions, text="ACTION ICON TEXT", bg=PANEL_BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left")
        e1 = tk.Entry(actions, textvariable=action_text_var, width=6, bg=INPUT_BG, fg=TEXT, insertbackground=TEXT, relief="flat")
        e1.pack(side="left", padx=(8, 18))
        e1.bind("<KeyRelease>", lambda _e: self.apply_settings())
        tk.Label(actions, text="SAVE ICON TEXT", bg=PANEL_BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left")
        e2 = tk.Entry(actions, textvariable=save_icon_text_var, width=10, bg=INPUT_BG, fg=TEXT, insertbackground=TEXT, relief="flat")
        e2.pack(side="left", padx=(8, 18))
        e2.bind("<KeyRelease>", lambda _e: self.apply_settings())
        tk.Button(actions, text="ZASTOSUJ", command=self.apply_settings, bg=BUTTON_BG, fg=BUTTON_TEXT,
                  activebackground=BUTTON_BG_HOVER, activeforeground=BUTTON_TEXT,
                  relief="flat", bd=0, padx=14, pady=8, font=("Segoe UI Semibold", 10)).pack(side="right", padx=(6, 0))
        tk.Button(actions, text="ZAPISZ JSON", command=self.save_settings, bg=BUTTON_BG, fg=BUTTON_TEXT,
                  activebackground=BUTTON_BG_HOVER, activeforeground=BUTTON_TEXT,
                  relief="flat", bd=0, padx=14, pady=8, font=("Segoe UI Semibold", 10)).pack(side="right")

    def slider(self, parent, key, start, end):
        row = tk.Frame(parent, bg=PANEL_SECTION)
        row.pack(fill="x", padx=8, pady=2)
        tk.Label(row, text=key.upper(), bg=PANEL_SECTION, fg=MUTED, width=18, anchor="w", font=("Segoe UI", 9)).pack(side="left")
        var = tk.IntVar(value=int(getattr(self.ui, key)))
        self.vars[key] = var
        scale = tk.Scale(row, variable=var, from_=start, to=end, orient="horizontal", showvalue=True,
                         resolution=1, command=lambda _v: self.apply_settings(),
                         bg=PANEL_SECTION, fg=TEXT, troughcolor=INPUT_BG, highlightthickness=0, bd=0, length=240)
        scale.pack(side="left", fill="x", expand=True)

    def fill_controls(self):
        for key, var in self.vars.items():
            try:
                var.set(getattr(self.ui, key))
            except Exception:
                pass

    def apply_settings(self):
        for key, var in self.vars.items():
            try:
                setattr(self.ui, key, var.get())
            except Exception:
                pass
        self.ui.clamp()
        self.renderer.update_ui(self.ui)
        for slot in self.slots:
            if slot.file_path:
                slot.take_number = extract_take_number(slot.file_path, self.ui.number_digits)
        self.rebuild_row()
        self.layout_protocol()
        self.status_var.set("Zastosowano ustawienia UI.")

    def save_settings(self):
        self.apply_settings()
        self.ui.save(UI_JSON)
        self.status_var.set(f"Zapisano ustawienia: {safe_relpath(UI_JSON, PROJECT_DIR)}")

    def rebuild_row(self):
        for w in self.slot_widgets:
            w.destroy()
        self.slot_widgets.clear()
        self.row_frame.destroy()
        self.row_frame = tk.Frame(self.protocol_canvas, bg=PROTOCOL_BG)
        self.row_win = self.protocol_canvas.create_window(0, 0, window=self.row_frame, anchor="n")
        self.render_slots()

    def render_slots(self):
        for i in range(SLOT_COUNT):
            slot_widget = TakeSlot(self.row_frame, self, self.slots[i])
            slot_widget.pack(side="left", padx=self.ui.row_pad_x, pady=self.ui.row_pad_y)
            self.slot_widgets.append(slot_widget)

    def layout_protocol(self):
        w = max(800, int(self.protocol_canvas.winfo_width() or 1200))
        h = max(300, int(self.protocol_canvas.winfo_height() or 500))
        self.protocol_canvas.delete("band")
        self.protocol_canvas.create_rectangle(0, 0, w, h, fill=PROTOCOL_BG, outline="", tags="band")
        self.protocol_canvas.create_rectangle(0, 0, w, h, fill=PROTOCOL_BAND, outline="", stipple="gray25", tags="band")
        self.protocol_canvas.tag_lower("band")
        self.protocol_canvas.coords(self.protocol_title, w / 2, self.ui.protocol_title_y)
        self.protocol_canvas.itemconfigure(self.protocol_title, font=("Segoe UI Light", self.ui.protocol_title_font_size))
        self.protocol_canvas.coords(self.row_win, w / 2, self.ui.protocol_row_center_y)

    def sync_store(self):
        records = []
        active = None
        for slot in self.slots:
            rel = None
            if slot.file_path:
                rel = safe_relpath(slot.file_path, PROJECT_DIR)
            records.append(SlotRecord(path=rel))
            if slot.state == SlotState.ACTIVE:
                active = slot.index
        SlotStore(slots=records, active_slot=active).save(SLOTS_JSON)

    def on_slot(self, idx: int):
        slot = self.slots[idx]
        if slot.state == SlotState.ACTIVE:
            return
        file_name = filedialog.askopenfilename(title="Wybierz TAKE", initialdir=str(TAKE_DIR), filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not file_name:
            return
        dst = copy_take_to_project(Path(file_name))
        slot.file_path = dst
        slot.take_number = extract_take_number(dst, self.ui.number_digits)
        slot.state = SlotState.LINKED
        slot.is_saved = False
        slot.is_loaded = False
        self.sync_store()
        self.slot_widgets[idx].redraw()
        self.status_var.set(f"TAKE {slot.take_number} podpięty.")

    def on_action(self, idx: int):
        slot = self.slots[idx]
        if slot.state == SlotState.EMPTY:
            return
        if slot.state == SlotState.ACTIVE:
            slot.is_loaded = True
            self.slot_widgets[idx].redraw()
            self.status_var.set(f"TAKE {slot.take_number} już aktywny.")
            return
        for i, s in enumerate(self.slots):
            if s.state == SlotState.ACTIVE:
                s.state = SlotState.LINKED
                self.slot_widgets[i].redraw()
        slot.state = SlotState.ACTIVE
        slot.is_loaded = True
        self.sync_store()
        self.slot_widgets[idx].redraw()
        self.status_var.set(f"TAKE {slot.take_number} aktywowany. LOAD.")

    def on_save(self, idx: int):
        slot = self.slots[idx]
        if slot.state != SlotState.ACTIVE:
            return
        slot.is_saved = True
        self.slot_widgets[idx].redraw()
        self.status_var.set(f"TAKE {slot.take_number} zapisany. SAVED.")

    def run(self):
        self.mainloop()


def main():
    app = TarzanEhrTakeSandboxWindow()
    app.run()


if __name__ == "__main__":
    main()
