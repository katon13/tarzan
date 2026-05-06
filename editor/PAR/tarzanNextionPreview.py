from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from editor.PAR.tarzanParWidgets import COLORS, Panel
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, Panel


class TarzanNextionPreviewPanel(tk.Frame):
    def __init__(self, parent, bridge, screen_key: str, title: str) -> None:
        super().__init__(parent, bg=COLORS["panel"])
        self.bridge = bridge
        self.screen_key = screen_key
        self.title = title
        self.state: Dict[str, Any] = {}
        self.current_page_id: Optional[str] = None

        self._intro_after_id = None
        self._intro_running = False
        self._intro_complete = False
        self._intro_index = 0

        self._photo_cache: Dict[str, tk.PhotoImage] = {}
        self._screen_photo: Optional[tk.PhotoImage] = None
        self._page1_button_box = None

        self.panel = Panel(self, title=title)
        self.panel.pack(fill="both", expand=True)

        self._load_config()
        self._build_shell()
        self.refresh()

    def _load_config(self) -> None:
        root = Path(__file__).resolve().parents[2]
        settings_path = root / "data" / "nextion" / "nextion_7_settings.json"
        try:
            import json
            self.settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            self.settings = {}

        preview = self.settings.get("preview") or {}
        self.scale = float(preview.get("scale", 0.5) or 0.5)
        self.bg_color = str(preview.get("background", "#000000"))

        self.intro_cfg = self.settings.get("intro") or {}
        self.screen_width = int(800 * self.scale)
        self.screen_height = int(480 * self.scale)

        frames_dir = self.intro_cfg.get("frames_dir", "img/nextion/intro_max/800_480")
        self.intro_dir = root / frames_dir
        self.intro_frames = list(self.intro_cfg.get("frames") or [])
        self.intro_frame_ms = int(self.intro_cfg.get("frame_time_ms", 180) or 180)
        self.tap_to_page = str(self.intro_cfg.get("tap_to_page", "page1") or "page1")
        self.level_img_path = root / "img" / "nextion" / "tarzanPoziomicaXYZ.png"

    def _build_shell(self) -> None:
        toolbar = tk.Frame(self.panel.body, bg=COLORS["panel"])
        toolbar.pack(fill="x", pady=(0, 6))

        tk.Button(toolbar, text="◀", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self._switch(-1)).pack(side="left", padx=2)
        tk.Button(toolbar, text="▶", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self._switch(1)).pack(side="left", padx=2)
        tk.Button(toolbar, text="SYNC", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self.bridge.sync(force=True)).pack(side="left", padx=4)
        tk.Button(toolbar, text="POŁĄCZ", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=self._connect).pack(side="left", padx=4)
        tk.Button(toolbar, text="ROZŁĄCZ", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=self._disconnect).pack(side="left", padx=2)

        self.page_label = tk.Label(toolbar, text="PAGE", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 10, "bold"))
        self.page_label.pack(side="right")

        self.screen_frame = tk.Frame(self.panel.body, bg="#0a0d10", highlightbackground="#4b5660", highlightthickness=2)
        self.screen_frame.pack(fill="both", expand=True)

        self.screen_canvas = tk.Canvas(
            self.screen_frame,
            width=self.screen_width,
            height=self.screen_height,
            bg=self.bg_color,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.screen_canvas.pack(expand=True, pady=10)
        self.screen_canvas.bind("<Button-1>", self._on_screen_tap)

        self.status = tk.Label(self.panel.body, text="", bg=COLORS["panel"], fg=COLORS["muted"], anchor="w", justify="left")
        self.status.pack(fill="x", pady=(6, 0))

    def _switch(self, step: int) -> None:
        if not self._is_connected():
            return
        self._cancel_intro()
        if step > 0:
            self.current_page_id = self.tap_to_page
            self._set_bridge_page(self.tap_to_page)
        else:
            self._start_intro(force=True)
        self.refresh()

    def _connect(self) -> None:
        if hasattr(self.bridge, "connect_screen"):
            self.bridge.connect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_connect_screen"):
            self.bridge.nextion_connect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_connect"):
            self.bridge.nextion_connect()
        self._start_intro(force=True)
        self.refresh()

    def _disconnect(self) -> None:
        self._cancel_intro()
        if hasattr(self.bridge, "disconnect_screen"):
            self.bridge.disconnect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_disconnect_screen"):
            self.bridge.nextion_disconnect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_disconnect_all"):
            self.bridge.nextion_disconnect_all()
        self.current_page_id = None
        self._intro_complete = False
        self._intro_index = 0
        self.refresh()

    def refresh(self) -> None:
        self.state = self.bridge.snapshot()

        connected = self._is_connected()
        device = getattr(self.bridge, "devices", {}).get(self.screen_key)
        port = getattr(device, "port", self.state.get(f"{self.screen_key}.port", ""))
        err = getattr(device, "last_error", None) or self.state.get(f"{self.screen_key}.last_error", "") or "-"
        if connected:
            err = "-"

        if not connected:
            self.current_page_id = None
            self.page_label.configure(text=f"{self.screen_key.upper()} | OFF")
            self.status.configure(text=f"PORT: {port}   COM: OFF   ERR: {err}")
            self._render_black()
            return

        bridge_page = self._bridge_page_id()

        if bridge_page == "level_xyz":
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = "level_xyz"
            self.page_label.configure(text=f"{self.screen_key.upper()} | LEVEL_XYZ")
            self.status.configure(text=f"PORT: {port}   COM: OK   ERR: -")
            self._render_level_xyz()
            return

        if bridge_page == self.tap_to_page:
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = self.tap_to_page
            self.page_label.configure(text=f"{self.screen_key.upper()} | {self.tap_to_page.upper()}")
            self.status.configure(text=f"PORT: {port}   COM: OK   ERR: -")
            self._render_page1()
            return

        if self._intro_running or (self.current_page_id == "boot" and self._intro_complete):
            self.current_page_id = "boot"
            self.page_label.configure(text=f"{self.screen_key.upper()} | BOOT")
            self.status.configure(text=f"PORT: {port}   COM: OK   ERR: -")
            self._render_intro_frame(self._intro_index)
            return

        self.current_page_id = bridge_page or "boot"
        page_name = (self.current_page_id or "boot").upper()
        self.page_label.configure(text=f"{self.screen_key.upper()} | {page_name}")
        self.status.configure(text=f"PORT: {port}   COM: OK   ERR: -")
        self._render_black()

    def _bridge_page_id(self) -> str:
        try:
            page = self.bridge.get_page(self.screen_key)
            return str(page.get("id", "") or "")
        except Exception:
            return ""

    def _set_bridge_page(self, page_id: str) -> None:
        try:
            self.bridge.set_page(self.screen_key, page_id)
        except Exception:
            pass

    def _render_black(self) -> None:
        self._page1_button_box = None
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        self._screen_photo = None

    def _render_page1(self) -> None:
        self._page1_button_box = None
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        self._screen_photo = None

        bw = int(220 * self.scale)
        bh = int(54 * self.scale)
        x1 = (self.screen_width - bw) // 2
        y1 = int(180 * self.scale)
        x2 = x1 + bw
        y2 = y1 + bh
        self._page1_button_box = (x1, y1, x2, y2)

        self.screen_canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS["button"], outline=COLORS["border"], width=2)
        self.screen_canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text="POZIOMICA", fill=COLORS["text"], font=("Segoe UI", max(10, int(12 * self.scale)), "bold"))

    def _image_for_path(self, path: Path) -> Optional[tk.PhotoImage]:
        key = str(path)
        if key in self._photo_cache:
            return self._photo_cache[key]
        if not path.exists():
            return None
        try:
            image = tk.PhotoImage(file=str(path))
            if self.scale == 0.5:
                image = image.subsample(2, 2)
            self._photo_cache[key] = image
            return image
        except Exception:
            return None

    def _image_for_frame(self, filename: str) -> Optional[tk.PhotoImage]:
        return self._image_for_path(self.intro_dir / filename)

    def _render_intro_frame(self, index: int) -> None:
        if not self.intro_frames:
            self._render_black()
            return
        idx = max(0, min(len(self.intro_frames) - 1, index))
        photo = self._image_for_frame(self.intro_frames[idx])

        self._page1_button_box = None
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        if photo is not None:
            self._screen_photo = photo
            self.screen_canvas.create_image(0, 0, image=photo, anchor="nw")
        else:
            self._screen_photo = None

    def _bus_value(self, name: str, default: int = 0) -> int:
        try:
            bus = getattr(self.bridge, "bus", None)
            if bus is not None and hasattr(bus, "get"):
                return int(float(bus.get(name, default)))
        except Exception:
            pass
        try:
            return int(float(self.state.get(name, default)))
        except Exception:
            return default

    def _render_level_xyz(self) -> None:
        self._page1_button_box = None
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)

        photo = self._image_for_path(self.level_img_path)
        self._screen_photo = photo

        img_x = int(190 * self.scale)
        img_y = int(30 * self.scale)
        if photo is not None:
            self.screen_canvas.create_image(img_x, img_y, image=photo, anchor="nw")

        cx = int(400 * self.scale)
        cy = int(240 * self.scale)

        # NAJWAŻNIEJSZE: bierz live wartości bezpośrednio z busa, nie tylko ze snapshotu
        x_raw = self._bus_value("par_level_x", 0)
        y_raw = self._bus_value("par_level_y", 0)

        x_val = max(-30, min(30, x_raw))
        y_val = max(-30, min(30, y_raw))

        px_per_point = 4.0 * self.scale
        dot_x = cx + int(round(x_val * px_per_point))
        dot_y = cy + int(round(y_val * px_per_point))

        x1 = int(265 * self.scale)
        x2 = int(535 * self.scale)
        y1 = int(105 * self.scale)
        y2 = int(375 * self.scale)

        line_color = COLORS["green"] if (x_val == 0 and y_val == 0) else COLORS["red"]

        self.screen_canvas.create_line(x1, cy, x2, cy, fill=line_color, width=1)
        self.screen_canvas.create_line(cx, y1, cx, y2, fill=line_color, width=1)
        self.screen_canvas.create_oval(dot_x - 8, dot_y - 8, dot_x + 8, dot_y + 8, fill=COLORS["red"], outline=COLORS["red"])

    def _start_intro(self, force: bool = False) -> None:
        if not self._is_connected():
            return
        if self._intro_running and not force:
            return
        self._cancel_intro()
        self._intro_running = True
        self._intro_complete = False
        self._intro_index = 0
        self.current_page_id = "boot"
        self._set_bridge_page("boot")
        self.refresh()
        self._schedule_intro_step()

    def _schedule_intro_step(self) -> None:
        def _step() -> None:
            if not self._is_connected():
                self._cancel_intro()
                return
            if self._intro_index >= len(self.intro_frames) - 1:
                self._intro_running = False
                self._intro_complete = True
                self.current_page_id = "boot"
                self.refresh()
                return
            self._intro_index += 1
            self.refresh()
            self._schedule_intro_step()

        self._intro_after_id = self.after(self.intro_frame_ms, _step)

    def _cancel_intro(self) -> None:
        self._intro_running = False
        if self._intro_after_id is not None:
            try:
                self.after_cancel(self._intro_after_id)
            except Exception:
                pass
        self._intro_after_id = None

    def _is_connected(self) -> bool:
        device = getattr(self.bridge, "devices", {}).get(self.screen_key)
        return bool(getattr(device, "connected", False))

    def _on_screen_tap(self, event=None) -> None:
        if not self._is_connected():
            return
        if self.current_page_id == "boot" and self._intro_complete:
            self.current_page_id = self.tap_to_page
            self._set_bridge_page(self.tap_to_page)
            self.refresh()
            return
        if self.current_page_id == "page1" and self._page1_button_box:
            x1, y1, x2, y2 = self._page1_button_box
            if event is not None and x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.current_page_id = "level_xyz"
                self._set_bridge_page("level_xyz")
                self.refresh()
