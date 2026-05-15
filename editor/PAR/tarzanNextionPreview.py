from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from editor.PAR.tarzanParWidgets import COLORS, Panel
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, Panel

try:
    # 1. Próba importu absolutnego
    from editor.TFD.tfd_state import tfd_state
    from editor.TFD.nextion_text_layout import get_layout
except (ImportError, ModuleNotFoundError):
    try:
        # 2. Próba importu bezpośredniego (jeśli editor jest w sys.path)
        from TFD.tfd_state import tfd_state
        from TFD.nextion_text_layout import get_layout
    except (ImportError, ModuleNotFoundError):
        try:
            # 3. Próba wymuszenia ścieżki
            import sys
            from pathlib import Path
            _root = Path(__file__).resolve().parents[2]
            if str(_root) not in sys.path:
                sys.path.insert(0, str(_root))
            from editor.TFD.tfd_state import tfd_state
            from editor.TFD.nextion_text_layout import get_layout
        except:
            tfd_state = None
            def get_layout(x): return []

try:
    from audio.tarzanAudioPlayer import play as play_audio
except ImportError:
    play_audio = lambda msg: None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


PAGE_TRANSITIONS: Dict[str, Dict[str, Optional[str]]] = {
    "page1": {"left": "level_xyz", "right": "take_main", "home": None},
    "level_xyz": {"left": "face_rec", "right": "rrp_main", "home": "page1"},
    "face_rec": {"left": "take_main", "right": "level_xyz", "home": "page1"},
    "rrp_main": {"left": "level_xyz", "right": "sensors_main", "home": "page1"},
    "sensors_main": {"left": "rrp_main", "right": "settings_main", "home": "page1"},
    "settings_main": {"left": "sensors_main", "right": "take_main", "home": "page1"},
    "take_main": {"left": "settings_main", "right": "level_xyz", "home": "page1"},
}

PAGE_TITLES = {
    "face_rec": "FACE",
    "rrp_main": "RRP",
    "sensors_main": "SENSORS",
    "settings_main": "SETTINGS",
    "take_main": "TAKE",
}

PAGE1_BUTTONS = [
    ("b_face", "face_rec", "Nextion_face_ico_200.png", (100, 40, 200, 200)),
    ("b_level", "level_xyz", "Nextion_level_ico_200.png", (300, 40, 200, 200)),
    ("b_rrp", "rrp_main", "Nextion_rrp_ico_200.png", (500, 40, 200, 200)),
    ("b_sensors", "sensors_main", "Nextion_sensors_ico_200.png", (100, 240, 200, 200)),
    ("b_settings", "settings_main", "Nextion_setting_ico_200.png", (300, 240, 200, 200)),
    ("b_take", "take_main", "Nextion_take_ico_200.png", (500, 240, 200, 200)),
]

_RRP_BUTTONS = [
    ("p1_cam_v", "CAM V", 20, 20),
    ("p1_cam_t", "CAM T", 120, 20),
    ("p1_cam_f", "FOCUS", 220, 20),
    ("p1_cam_h", "CAM H", 320, 20),
    ("p1_arm_h", "ARM H", 420, 20),
    ("p1_arm_v", "ARM V", 520, 20),
    ("p2_cam_v", "CAM V", 20, 260),
    ("p2_cam_t", "CAM T", 120, 260),
    ("p2_cam_f", "FOCUS", 220, 260),
    ("p2_cam_h", "CAM H", 320, 260),
    ("p2_arm_h", "ARM H", 420, 260),
    ("p2_arm_v", "ARM V", 520, 260),
    ("home", "HOME", 700, 385),
]


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
        self._hitboxes: Dict[str, Tuple[int, int, int, int]] = {}

        self._rrp_drag_target: Optional[str] = None

        self._edit_entry: Optional[tk.Entry] = None
        self._edit_target: Optional[str] = None
        self._edit_window: Optional[int] = None

        self.panel = Panel(self, title=title)
        self.panel.pack(fill="both", expand=True)

        self._load_config()
        self._build_shell()
        self.refresh()

    def _load_config(self) -> None:
        root = Path(__file__).resolve().parents[2]
        settings_path = root / "data" / "nextion" / "nextion_7_settings.json"
        try:
            self.settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            self.settings = {}

        preview = self.settings.get("preview") or {}
        self.scale = float(preview.get("scale", 0.5) or 0.5)
        self.bg_color = str(preview.get("background", "#000000"))
        self.screen_width = int(800 * self.scale)
        self.screen_height = int(480 * self.scale)

        self.intro_cfg = self.settings.get("intro") or {}
        self.pages_order = list(self.settings.get("pages_order") or [
            "boot", "page1", "level_xyz", "face_rec", "rrp_main", "sensors_main", "settings_main", "take_main"
        ])

        frames_dir = self.intro_cfg.get("frames_dir", "img/nextion/intro_max/800_480")
        self.intro_dir = root / frames_dir
        self.intro_frames = list(self.intro_cfg.get("frames") or [])
        self.intro_frame_ms = int(self.intro_cfg.get("frame_time_ms", 180) or 180)
        self.tap_to_page = str(self.intro_cfg.get("tap_to_page", "page1") or "page1")

        self.level_img_path = root / "img" / "nextion" / "tarzanPoziomicaXYZ.png"
        self.page_icons_dir = root / "img" / "nextion" / "page"
        self.home_icon_candidates = [
            self.page_icons_dir / "Nextion_home_ico_69.png",
            self.page_icons_dir / "Nextion_home_ico_200.png",
            self.page_icons_dir / "Nextion_home.png",
            root / "img" / "nextion" / "Nextion_home.png",
        ]

    def _build_shell(self) -> None:
        toolbar = tk.Frame(self.panel.body, bg=COLORS["panel"])
        toolbar.pack(fill="x", pady=(0, 6))

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
        self.screen_canvas.bind("<B1-Motion>", self._on_screen_drag)
        self.screen_canvas.bind("<B1-Motion>", self._on_screen_drag)
        self.screen_canvas.bind("<ButtonRelease-1>", self._on_screen_release)

        self.status = tk.Label(self.panel.body, text="", bg=COLORS["panel"], fg=COLORS["muted"], anchor="w", justify="left")
        self.status.pack(fill="x", pady=(6, 0))

    def _toolbar_switch(self, step: int) -> None:
        if not self._is_connected():
            return
        self._cancel_intro()
        cur = self._bridge_page_id() or "boot"
        if cur in PAGE_TRANSITIONS:
            target = PAGE_TRANSITIONS[cur]["right" if step > 0 else "left"]
            if target:
                self._set_bridge_page(target)
        else:
            pages = self.pages_order or ["boot", "page1"]
            idx = pages.index(cur) if cur in pages else 0
            self._set_bridge_page(pages[(idx + (1 if step > 0 else -1)) % len(pages)])
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
        # Nie odświeżamy jeśli trwa edycja pola tekstowego (aby nie zniknął kursor/fokus)
        if self._edit_entry:
            return

        self.state = self.bridge.snapshot()

        connected = self._is_connected()
        device = getattr(self.bridge, "devices", {}).get(self.screen_key)
        port = getattr(device, "port", self.state.get(f"{self.screen_key}.port", ""))
        err = getattr(device, "last_error", None) or self.state.get(f"{self.screen_key}.last_error", "") or "-"
        recent_log = ""
        if hasattr(self.bridge, "get_recent_transport_log"):
            try:
                logs = self.bridge.get_recent_transport_log(self.screen_key, limit=1)
                recent_log = logs[-1] if logs else ""
            except Exception:
                recent_log = ""

        if connected:
            err = "-"

        if False and not connected:
            self.current_page_id = None
            self.page_label.configure(text=f"{self.screen_key.upper()} | OFF")
            self.status.configure(text=f"PORT: {port}   COM: OFF   ERR: {err}")
            self._render_black()
            return

        bridge_page = self._bridge_page_id()

        # Obsługa BOOT / INTRO
        if bridge_page == "boot" or not bridge_page:
            if not self._intro_complete and not self._intro_running:
                # Automatyczny start intro przy wejściu na boot
                self._start_intro()
                return

            self.current_page_id = "boot"
            self.page_label.configure(text=f"{self.screen_key.upper()} | BOOT")
            self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
            
            if self._intro_running:
                self._render_intro_frame(self._intro_index)
            elif self._intro_complete:
                self._render_page1() # Nextion zazwyczaj po boot przechodzi do page1
            else:
                self._render_intro_frame(0)
            return

        if bridge_page == "level_xyz":
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = "level_xyz"
            self.page_label.configure(text=f"{self.screen_key.upper()} | LEVEL_XYZ")
            self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
            self._render_level_xyz()
            return

        if bridge_page == "rrp_main":
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = "rrp_main"
            self.page_label.configure(text=f"{self.screen_key.upper()} | RRP_MAIN")
            self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
            self._render_rrp_main()
            return

        if bridge_page == self.tap_to_page:
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = self.tap_to_page
            self.page_label.configure(text=f"{self.screen_key.upper()} | {self.tap_to_page.upper()}")
            self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
            self._render_page1()
            return

        if bridge_page == "take_main":
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = "take_main"
            self.page_label.configure(text=f"{self.screen_key.upper()} | TAKE_MAIN")
            self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
            self._render_take_main()
            return

        if bridge_page == "settings_main":
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = "settings_main"
            self.page_label.configure(text=f"{self.screen_key.upper()} | SETTINGS_MAIN")
            self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
            self._render_settings_main()
            return

        if bridge_page in PAGE_TITLES:
            self._cancel_intro()
            self._intro_complete = False
            self.current_page_id = bridge_page
            self.page_label.configure(text=f"{self.screen_key.upper()} | {bridge_page.upper()}")
            self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
            self._render_placeholder_page(bridge_page)
            return

        self.current_page_id = bridge_page or "boot"
        self.page_label.configure(text=f"{self.screen_key.upper()} | {(self.current_page_id or 'boot').upper()}")
        self.status.configure(text=f"PORT: {port}   COM: OK   {recent_log}")
        if self.current_page_id == "boot":
            self._render_intro_frame(0)
        else:
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
        self._hitboxes = {}
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        self._screen_photo = None

    def _render_take_main(self) -> None:
        """Renderuje statyczny, tekstowy podgląd TFD (zastępuje rysowanie na podstawie take_main.txt)."""
        self._hitboxes = {}
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg="#000")
        self._screen_photo = None
        
        sc = self.scale
        packet = tfd_state.get_packet() if tfd_state else {}
        axes = packet.get("axes", {})
        sensors = packet.get("sensors", {})
        
        # --- GÓRA: TITLE i DIRECTOR ---
        t1_val = packet.get("title", "---")
        t1_display = f"TITLE: {t1_val}" if not str(t1_val).startswith("TITLE:") else t1_val
        
        self.screen_canvas.create_text(
            20 * sc, 10 * sc,
            text=t1_display.upper(),
            fill="#fff", font=("Consolas", int(32 * sc), "bold"), anchor="nw"
        )
        self._hitboxes["t1"] = (20 * sc, 10 * sc, 650 * sc, 55 * sc)
        
        t2_val = packet.get("director", "---")
        t2_display = f"DIRECTOR: {t2_val}" if not str(t2_val).startswith("DIRECTOR:") else t2_val
        self.screen_canvas.create_text(
            20 * sc, 60 * sc,
            text=t2_display,
            fill="#fff", font=("Consolas", int(24 * sc)), anchor="nw"
        )
        self._hitboxes["t2"] = (20 * sc, 60 * sc, 650 * sc, 95 * sc)
        
        # --- STATUS ---
        status = packet.get("status", "LIVE")
        st_color = COLORS["green"] if status == "LIVE" else COLORS["red"]
        self.screen_canvas.create_rectangle(
            680 * sc, 10 * sc, 790 * sc, 90 * sc,
            outline=st_color, width=int(2 * sc)
        )
        self.screen_canvas.create_text(
            735 * sc, 50 * sc,
            text=status, fill=st_color, font=("Consolas", int(24 * sc), "bold")
        )

        self.screen_canvas.create_line(10 * sc, 105 * sc, 790 * sc, 105 * sc, fill="#333")

        # --- CLAP ---
        clap_active = packet.get("clap", False)
        clap_color = COLORS["red"] if clap_active else "#500"
        self.screen_canvas.create_rectangle(
            20 * sc, 180 * sc, 120 * sc, 280 * sc,
            outline=clap_color, fill="#100", width=int(2 * sc)
        )
        self.screen_canvas.create_text(
            70 * sc, 230 * sc,
            text="CLAP", fill=clap_color, font=("Consolas", int(18 * sc), "bold")
        )
        self._hitboxes["b_clap"] = (20 * sc, 180 * sc, 120 * sc, 280 * sc)

        # --- TAKE ---
        self.screen_canvas.create_text(
            230 * sc, 190 * sc,
            text="TAKE", fill="#777", font=("Consolas", int(14 * sc))
        )
        self.screen_canvas.create_text(
            230 * sc, 240 * sc,
            text=packet.get('take', '001-01'),
            fill="#fff", font=("Consolas", int(40 * sc), "bold")
        )

        # --- OSIE ---
        def draw_ax(x, y, label, key):
            val = axes.get(key, {}).get("pos", "+00000") if isinstance(axes.get(key), dict) else "+00000"
            self.screen_canvas.create_text(
                x * sc, y * sc,
                text=label, fill="#666", font=("Consolas", int(11 * sc)), anchor="nw"
            )
            self.screen_canvas.create_text(
                (x + 65) * sc, y * sc,
                text=val, fill=COLORS["red"], font=("Consolas", int(26 * sc), "bold"), anchor="nw"
            )

        draw_ax(360, 115, "CAM H", "axis0")
        draw_ax(360, 175, "CAM V", "axis1")
        draw_ax(360, 235, "ARM H", "axis5")
        
        draw_ax(580, 115, "FOCUS", "axis3")
        draw_ax(580, 175, "CAM T", "axis2")
        draw_ax(580, 235, "ARM V", "axis4")

        self.screen_canvas.create_line(345 * sc, 110 * sc, 345 * sc, 300 * sc, fill="#222")

        # --- TIMECODE ---
        self.screen_canvas.create_text(
            20 * sc, 320 * sc,
            text="TC:", fill="#666", font=("Consolas", int(14 * sc)), anchor="nw"
        )
        self.screen_canvas.create_text(
            75 * sc, 312 * sc,
            text=packet.get('t0', packet.get('tc', '00:00:00:0000')),
            fill="#fff", font=("Consolas", int(44 * sc), "bold"), anchor="nw"
        )

        self.screen_canvas.create_line(10 * sc, 385 * sc, 790 * sc, 385 * sc, fill="#333")

        # --- SENSORY ---
        self.screen_canvas.create_text(
            20 * sc, 400 * sc,
            text=f"{sensors.get('xyz', '---')}", fill=COLORS["green"], font=("Consolas", int(16 * sc), "bold"), anchor="nw"
        )
        self.screen_canvas.create_text(
            400 * sc, 400 * sc,
            text=f"LIGHT: {sensors.get('light', '---')}", fill="#ff0", font=("Consolas", int(13 * sc)), anchor="nw"
        )
        
        s_f = ("Consolas", int(11 * sc))
        self.screen_canvas.create_text(20 * sc, 440 * sc, text=f"LIMITS: {sensors.get('limits', 'OK')}", fill="#0f0", font=s_f, anchor="nw")
        self.screen_canvas.create_text(180 * sc, 440 * sc, text=f"LASER: {sensors.get('laser', 'OFF')}", fill="#0f0", font=s_f, anchor="nw")
        self.screen_canvas.create_text(340 * sc, 440 * sc, text=f"SHOCK: {sensors.get('shock', 'OK')}", fill="#0f0", font=s_f, anchor="nw")
        self.screen_canvas.create_text(500 * sc, 440 * sc, text=f"TEMP: {sensors.get('temp', '22.00 C')}", fill="#0f0", font=s_f, anchor="nw")

        self._draw_nav_arrows(show_home=True)

    def _render_settings_main(self) -> None:
        """Renderuje stronę SETTINGS_MAIN."""
        self._hitboxes = {}
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        
        layout = get_layout("settings_main.txt")
        if not layout:
            err_msg = "BŁĄD: Brak settings_main.txt"
            if hasattr(get_layout, "__name__") and get_layout.__name__ == "get_layout":
                 err_msg += "\nBłąd parsowania lub brak pliku."
            else:
                 err_msg += "\nBłąd importu modułu layoutu."
                 
            self.screen_canvas.create_text(
                self.screen_width // 2, self.screen_height // 2,
                text=err_msg,
                fill="#f00", font=("Segoe UI", 10, "bold")
            )
            self._draw_nav_arrows(show_home=True)
            return
            
        val_map = {
            "t_title": tfd_state.title if tfd_state else "TYTUŁ",
            "t_director": tfd_state.director if tfd_state else "REŻYSER"
        }

        for comp in layout:
            name = comp["name"]
            attrs = comp["attrs"]
            try:
                x = int(attrs.get("x coordinate", 0))
                y = int(attrs.get("y coordinate", 0))
                w = int(attrs.get("Width", 10))
                h = int(attrs.get("Height", 10))
            except ValueError: continue
            
            sx, sy = int(x * self.scale), int(y * self.scale)
            sw, sh = int(w * self.scale), int(h * self.scale)
            
            if comp["type"] == "Text":
                text = val_map.get(name, attrs.get("Text", ""))
                self._hitboxes[name] = (sx, sy, sx + sw, sy + sh)
                self.screen_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, outline="#555", fill="#111")
                
                font_size = max(10, int(18 * self.scale))
                if name in ["t_title", "t_director"]:
                    font_size = max(12, int(24 * self.scale))
                
                self.screen_canvas.create_text(
                    sx + sw // 2, sy + sh // 2,
                    text=text, fill="#fff",
                    font=("Segoe UI", font_size, "bold"),
                    width=sw
                )
            elif comp["type"] == "Button":
                self._hitboxes[name] = (sx, sy, sx + sw, sy + sh)
                color = COLORS["green"] if name == "b_save_meta" else "#333"
                self.screen_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, outline="#fff", fill=color)
                label = "SAVE" if name == "b_save_meta" else name
                self.screen_canvas.create_text(sx + sw // 2, sy + sh // 2, text=label, fill="#fff", font=("Segoe UI", 9, "bold"))

        self._draw_nav_arrows(show_home=True)

    def _get_tfd_icon(self, name: str, packet: dict = None) -> Optional[tk.PhotoImage]:
        if Image is None or ImageTk is None:
            return None
            
        icon_map = {
            "p_axis0": "tfd_1.png", "p_axis1": "tfd_2.png", "p_axis2": "tfd_3.png",
            "p_axis3": "tfd_4.png", "p_axis4": "tfd_5.png", "p_axis5": "tfd_6.png",
            "p_laser": "tfd_laser.png", "p_limits": "tfd_limit.png", 
            "p_light": "tfd_litht.png", "p_shock": "tfd_shock.png",
            "p_temp": "tfd_temp.png", "p_xyz": "tfd_xyz.png",
            "p5": "clamp_acive.png" if packet and packet.get("clap") else "clamp_inacive.png"
        }
        filename = icon_map.get(name)
        if not filename: return None
        
        cache_key = f"tfd_icon_{filename}_{self.scale}"
        if cache_key in self._photo_cache:
            return self._photo_cache[cache_key]
            
        root = Path(__file__).resolve().parents[2]
        path = root / "img" / "nextion" / "page" / filename
        if path.exists():
            try:
                img = Image.open(path)
                w, h = img.size
                img = img.resize((int(w * self.scale), int(h * self.scale)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_cache[cache_key] = photo
                return photo
            except Exception:
                return None
        return None

    def _nextion_color_to_hex(self, nextion_color: str) -> str:
        try:
            val = int(nextion_color)
            r = (val >> 11) & 0x1F
            g = (val >> 5) & 0x3F
            b = val & 0x1F
            r = int(r * 255 / 31)
            g = int(g * 255 / 63)
            b = int(b * 255 / 31)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "#ffffff"

    def _render_page1(self) -> None:
        self._hitboxes = {}
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        self._screen_photo = None

        for _, target, filename, (x, y, w, h) in PAGE1_BUTTONS:
            sx, sy = int(x * self.scale), int(y * self.scale)
            sw, sh = int(w * self.scale), int(h * self.scale)
            self._hitboxes[target] = (sx, sy, sx + sw, sy + sh)
            image = self._image_for_path(self.page_icons_dir / filename)
            if image is not None:
                self.screen_canvas.create_image(sx, sy, image=image, anchor="nw")
            else:
                self.screen_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, outline=COLORS["border"], fill="#101820", width=2)
                self.screen_canvas.create_text(sx + sw // 2, sy + sh // 2, text=target.upper(), fill=COLORS["text"], font=("Segoe UI", max(9, int(12 * self.scale)), "bold"))

    def _render_placeholder_page(self, page_id: str) -> None:
        self._hitboxes = {}
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        self._screen_photo = None
        self._draw_home_only()
        title = PAGE_TITLES.get(page_id, page_id.upper())
        self.screen_canvas.create_text(
            self.screen_width // 2,
            int(230 * self.scale),
            text=title,
            fill="#ffffff",
            font=("Segoe UI", max(12, int(22 * self.scale)), "bold"),
        )

    def _draw_nav_arrows(self, show_home: bool) -> None:
        if show_home:
            home_x = int(700 * self.scale)
            home_y = int(385 * self.scale)
            home_w = int(69 * self.scale)
            home_h = int(69 * self.scale)
            home = None
            for candidate in self.home_icon_candidates:
                home = self._image_for_path(candidate)
                if home is not None:
                    break
            if home is not None:
                self.screen_canvas.create_image(home_x, home_y, image=home, anchor="nw")
            else:
                self.screen_canvas.create_rectangle(home_x, home_y, home_x + home_w, home_y + home_h, fill="#101820", outline=COLORS["border"], width=2)
                self.screen_canvas.create_text(home_x + home_w // 2, home_y + home_h // 2, text="HOME", fill=COLORS["text"], font=("Segoe UI", max(8, int(10 * self.scale)), "bold"))
            self._hitboxes["__home__"] = (home_x, home_y, home_x + home_w, home_y + home_h)

    def _draw_home_only(self) -> None:
        home_x = int(15 * self.scale)
        home_y = int(400 * self.scale)
        home_w = int(69 * self.scale)
        home_h = int(69 * self.scale)
        home = None
        for candidate in self.home_icon_candidates:
            home = self._image_for_path(candidate)
            if home is not None:
                break
        if home is not None:
            self.screen_canvas.create_image(home_x, home_y, image=home, anchor="nw")
        else:
            self.screen_canvas.create_rectangle(home_x, home_y, home_x + home_w, home_y + home_h, fill="#101820", outline=COLORS["border"], width=2)
            self.screen_canvas.create_text(home_x + home_w // 2, home_y + home_h // 2, text="HOME", fill=COLORS["text"], font=("Segoe UI", max(8, int(10 * self.scale)), "bold"))
        self._hitboxes["__home__"] = (home_x, home_y, home_x + home_w, home_y + home_h)

    def _image_for_path(self, path: Path) -> Optional[tk.PhotoImage]:
        key = str(path)
        if key in self._photo_cache:
            return self._photo_cache[key]
        if not path.exists():
            return None
        try:
            # Używamy PIL jeśli dostępne (obsługuje JPG/BMP i lepsze skalowanie)
            if Image and ImageTk:
                img = Image.open(path)
                if self.scale != 1.0:
                    w = int(img.width * self.scale)
                    h = int(img.height * self.scale)
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_cache[key] = photo
                return photo
            else:
                # Fallback do wbudowanego PhotoImage (tylko PNG/GIF)
                image = tk.PhotoImage(file=str(path))
                if self.scale != 1.0:
                    # subsample() przyjmuje tylko liczby całkowite
                    factor = int(1.0 / self.scale) if self.scale < 1.0 else 1
                    if factor > 1:
                        image = image.subsample(factor, factor)
                self._photo_cache[key] = image
                return image
        except Exception as exc:
            if hasattr(self, "bridge") and hasattr(self.bridge, "bus") and hasattr(self.bridge.bus, "log"):
                self.bridge.bus.log("PAR_ERROR", f"Błąd ładowania obrazu {path.name}: {exc}")
            return None

    def _image_for_frame(self, filename: str) -> Optional[tk.PhotoImage]:
        return self._image_for_path(self.intro_dir / filename)

    def _render_intro_frame(self, index: int) -> None:
        self._hitboxes = {}
        if not self.intro_frames:
            self._render_black()
            return
        idx = max(0, min(len(self.intro_frames) - 1, index))
        photo = self._image_for_frame(self.intro_frames[idx])
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
        self._hitboxes = {}
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)

        photo = self._image_for_path(self.level_img_path)
        self._screen_photo = photo
        img_x = int(190 * self.scale)
        img_y = int(30 * self.scale)
        if photo is not None:
            self.screen_canvas.create_image(img_x, img_y, image=photo, anchor="nw")

        self._draw_nav_arrows(show_home=True)

        cx = int(400 * self.scale)
        cy = int(240 * self.scale)
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
        dot_color = COLORS["green"] if (x_val == 0 and y_val == 0) else COLORS["red"]
        self.screen_canvas.create_line(x1, cy, x2, cy, fill=line_color, width=1)
        self.screen_canvas.create_line(cx, y1, cx, y2, fill=line_color, width=1)
        r = max(8, int(16 * self.scale))
        self.screen_canvas.create_oval(dot_x - r, dot_y - r, dot_x + r, dot_y + r, fill=dot_color, outline=dot_color)

    def _rrp_state(self) -> Dict[str, Any]:
        try:
            return self.bridge.get_rrp_state(self.screen_key)
        except Exception:
            return {
                "va_p1_axis": -1, "va_p2_axis": -1, "va_p1_dir": 0, "va_p2_dir": 0,
                "va_p1_val": 0, "va_p2_val": 0, "h_p1_sens": 50, "h_p2_sens": 50,
                "p1_axis_label": "STOP", "p2_axis_label": "STOP",
            }

    def _rrp_disabled_keys(self, state: Dict[str, Any]) -> set[str]:
        disabled: set[str] = set()
        p1_axis = int(state.get("va_p1_axis", -1))
        p2_axis = int(state.get("va_p2_axis", -1))
        axis_key_map = {
            0: "cam_v",
            1: "cam_t",
            2: "cam_f",
            3: "cam_h",
            4: "arm_h",
            5: "arm_v",
        }
        if p1_axis in axis_key_map:
            disabled.add(f"p2_{axis_key_map[p1_axis]}")
        if p2_axis in axis_key_map:
            disabled.add(f"p1_{axis_key_map[p2_axis]}")
        return disabled

    def _render_rrp_main(self) -> None:
        self._hitboxes = {}
        self.screen_canvas.delete("all")
        self.screen_canvas.configure(bg=self.bg_color)
        self._screen_photo = None

        state = self._rrp_state()

        def s(v: int) -> int:
            return int(v * self.scale)

        def draw_slider(x: int, y: int, label: str, value: int, hit_key: str) -> None:
            sx, sy = s(x), s(y)
            sw, sh = s(400), s(81)
            shown = max(0, min(100, int(value)))
            self.screen_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, fill="#1b242b", outline="#3c4b55", width=2)
            fill_w = int(round((shown / 100.0) * sw))
            self.screen_canvas.create_rectangle(sx, sy, sx + fill_w, sy + sh, fill="#3a8f2d", outline="")
            knob_x = sx + fill_w
            knob_w = s(81)
            self.screen_canvas.create_rectangle(max(sx, knob_x - knob_w // 2), sy, min(sx + sw, knob_x + knob_w // 2), sy + sh, fill="#d7dde2", outline="#202830")
            self.screen_canvas.create_text(sx + sw // 2, sy + sh // 2, text=f"{label} SENS: {shown}", fill="#ffffff", font=("Segoe UI", max(8, s(18)), "bold"))
            self._hitboxes[hit_key] = (sx, sy, sx + sw, sy + sh)

        def draw_display(x: int, y: int, value: int, label: str) -> None:
            sx, sy = s(x), s(y)
            sw, sh = s(200), s(81)
            self.screen_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, fill="#0d1014", outline="#4a545d", width=2)
            self.screen_canvas.create_text(sx + sw // 2, sy + sh // 2, text=str(int(value)), fill="#ffffff", font=("Segoe UI", max(12, s(28)), "bold"))
            self.screen_canvas.create_text(sx + sw // 2, sy + sh + s(10), text=label, fill="#5f6b72", font=("Segoe UI", max(8, s(10))))

        disabled_keys = self._rrp_disabled_keys(state)

        def draw_button(x: int, y: int, w: int, h: int, text: str, active: bool, key: str) -> None:
            sx, sy = s(x), s(y)
            sw, sh = s(w), s(h)
            disabled = key in disabled_keys
            if disabled:
                fill = "#151b20"
                fg = "#7f8b93"
                outline = "#46525b"
            else:
                fill = "#4cc63f" if active else "#27333b"
                fg = "#081108" if active else "#ffffff"
                outline = "#d0d7de"
            self.screen_canvas.create_rectangle(sx, sy, sx + sw, sy + sh, fill=fill, outline=outline, width=2)
            self.screen_canvas.create_text(sx + sw // 2, sy + sh // 2, text=text, fill=fg, font=("Segoe UI", max(8, s(12)), "bold"))
            if disabled:
                self.screen_canvas.create_line(sx + s(10), sy + s(10), sx + sw - s(10), sy + sh - s(10), fill="#b74141", width=max(2, s(2)))
            self._hitboxes[key] = (sx, sy, sx + sw, sy + sh)

        draw_slider(20, 140, "P1", int(state.get("h_p1_sens", 50)), "slider_p1")
        draw_slider(20, 380, "P2", int(state.get("h_p2_sens", 50)), "slider_p2")
        draw_display(420, 140, int(state.get("va_p1_val", 0)), "t_p1_val")
        draw_display(420, 380, int(state.get("va_p2_val", 0)), "t_p2_val")

        draw_button(680, 20, 100, 100, "DIR", bool(state.get("va_p1_dir", 0)), "p1_dir")
        draw_button(680, 260, 100, 100, "DIR", bool(state.get("va_p2_dir", 0)), "p2_dir")
        draw_button(680, 138, 100, 100, "STOP", False, "stop")

        p1_axis = int(state.get("va_p1_axis", -1))
        p2_axis = int(state.get("va_p2_axis", -1))
        active_map = {
            "p1_cam_v": p1_axis == 0,
            "p1_cam_t": p1_axis == 1,
            "p1_cam_f": p1_axis == 2,
            "p1_cam_h": p1_axis == 3,
            "p1_arm_h": p1_axis == 4,
            "p1_arm_v": p1_axis == 5,
            "p2_cam_v": p2_axis == 0,
            "p2_cam_t": p2_axis == 1,
            "p2_cam_f": p2_axis == 2,
            "p2_cam_h": p2_axis == 3,
            "p2_arm_h": p2_axis == 4,
            "p2_arm_v": p2_axis == 5,
        }

        for key, label, x, y in _RRP_BUTTONS:
            draw_button(x, y, 100, 100, label, active_map.get(key, False), key)

        self._draw_nav_arrows(show_home=True)

    def _start_intro(self, force: bool = False) -> None:
        try:
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
            # Nie wywołujemy refresh() tutaj, bo start intro jest zwykle wywoływany Z refresh()
            self._schedule_intro_step()
        except Exception as exc:
            self._intro_running = False
            if hasattr(self.bridge, "bus") and hasattr(self.bridge.bus, "log"):
                self.bridge.bus.log("PAR_ERROR", f"Błąd startu intro: {exc}")

    def _schedule_intro_step(self) -> None:
        def _step() -> None:
            try:
                if not self._intro_running:
                    return
                if not self._is_connected():
                    self._cancel_intro()
                    return
                
                if not self.intro_frames or self._intro_index >= len(self.intro_frames) - 1:
                    self._intro_running = False
                    self._intro_complete = True
                    self.current_page_id = "boot"
                    self.refresh()
                    return
                
                self._intro_index += 1
                self.refresh()
                self._schedule_intro_step()
            except Exception as exc:
                self._intro_running = False
                if hasattr(self.bridge, "bus") and hasattr(self.bridge.bus, "log"):
                    self.bridge.bus.log("PAR_ERROR", f"Błąd kroku intro: {exc}")

        self._intro_after_id = self.after(max(10, self.intro_frame_ms), _step)

    def _cancel_intro(self) -> None:
        self._intro_running = False
        if self._intro_after_id:
            try:
                self.after_cancel(self._intro_after_id)
            except Exception:
                pass
        self._intro_after_id = None

    def _is_connected(self) -> bool:
        """
        Zwraca True, aby umożliwić interakcję z podglądem w PAR 
        nawet bez fizycznego połączenia (tryb symulacji/podglądu).
        """
        return True

    def _slider_value_from_hit(self, key: str, x: int) -> int:
        box = self._hitboxes.get(key)
        if not box:
            return 0
        x1, _, x2, _ = box
        if x2 <= x1:
            return 0
        frac = (x - x1) / float(x2 - x1)
        return max(0, min(100, int(round(frac * 100))))

    def _refresh_current_page_view(self) -> None:
        current = self._bridge_page_id() or self.current_page_id or "boot"
        if current == "rrp_main":
            self.current_page_id = "rrp_main"
            self.page_label.configure(text=f"{self.screen_key.upper()} | RRP_MAIN")
            self._render_rrp_main()
            return
        self.refresh()

    def _apply_rrp_preview_slider(self, player: str, x: int) -> None:
        key = f"slider_{player}"
        value = self._slider_value_from_hit(key, x)
        try:
            self.bridge.preview_rrp_set_value(self.screen_key, player, value)
        except Exception:
            return
        # refresh() zostanie wywołany przez TarzanParApp.nextion_tick() 
        # gdy zauważy zmianę rewizji rrp w mostku.

    def _on_screen_drag(self, event) -> None:
        if not self._is_connected():
            return
        current = self._bridge_page_id() or self.current_page_id or "boot"
        if current != "rrp_main":
            return
        if self._rrp_drag_target in {"p1", "p2"}:
            self._apply_rrp_preview_slider(self._rrp_drag_target, int(event.x))

    def _on_screen_release(self, _event) -> None:
        self._rrp_drag_target = None

    def _on_screen_tap(self, event) -> None:
        if not self._is_connected():
            return

        x, y = int(event.x), int(event.y)
        current = self._bridge_page_id() or self.current_page_id or "boot"

        if current == "boot":
            if self._intro_complete:
                self._set_bridge_page("page1")
                self.refresh()
            return

        if current == "page1":
            for _, target, _, (bx, by, bw, bh) in PAGE1_BUTTONS:
                sx, sy = int(bx * self.scale), int(by * self.scale)
                sw, sh = int(bw * self.scale), int(bh * self.scale)
                if sx <= x <= sx + sw and sy <= y <= sy + sh:
                    self._set_bridge_page(target)
                    self.refresh()
                    return

        if current == "rrp_main":
            for key in [
                "p1_cam_v", "p1_cam_t", "p1_cam_f", "p1_cam_h", "p1_arm_h", "p1_arm_v",
                "p2_cam_v", "p2_cam_t", "p2_cam_f", "p2_cam_h", "p2_arm_h", "p2_arm_v",
                "p1_dir", "p2_dir", "stop", "home",
            ]:
                box = self._hitboxes.get(key)
                if box and box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                    if key in self._rrp_disabled_keys(self._rrp_state()):
                        return
                    try:
                        self.bridge.preview_rrp_tap(self.screen_key, key)
                    except Exception:
                        pass
                    # refresh() nastąpi automatycznie przez TarzanParApp
                    return

            slider_p1 = self._hitboxes.get("slider_p1")
            if slider_p1 and slider_p1[0] <= x <= slider_p1[2] and slider_p1[1] <= y <= slider_p1[3]:
                self._rrp_drag_target = "p1"
                self._apply_rrp_preview_slider("p1", x)
                return

            slider_p2 = self._hitboxes.get("slider_p2")
            if slider_p2 and slider_p2[0] <= x <= slider_p2[2] and slider_p2[1] <= y <= slider_p2[3]:
                self._rrp_drag_target = "p2"
                self._apply_rrp_preview_slider("p2", x)
                return

        if current == "take_main":
            # Obsługa przycisku b_clap
            box = self._hitboxes.get("b_clap")
            if box and box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                if tfd_state:
                    tfd_state.set_clap(1)
                    play_audio("clap")
                    # Symulujemy wysłanie do mostka jeśli mostek obsługuje przesyłanie zdarzeń do hardware
                    if hasattr(self.bridge, "devices"):
                        dev = self.bridge.devices.get(self.screen_key)
                        if dev and dev.connected:
                            dev.send_command("print \"take:clap=1\"")
                            dev.send_raw(b"\xff\xff\xff")
                self.refresh()
                return

        if current == "settings_main":
            # Obsługa wpisywania metadanych bez wyskakujących okienek
            for field in ["t_title", "t_director"]:
                box = self._hitboxes.get(field)
                if box and box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                    self._start_edit(field, box)
                    return
            
            # Obsługa b_save_meta
            box = self._hitboxes.get("b_save_meta")
            if box and box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                if tfd_state and hasattr(self.bridge, "devices"):
                    dev = self.bridge.devices.get(self.screen_key)
                    if dev and dev.connected:
                        dev.send_command(f"print \"set:title={tfd_state.title}\"")
                        dev.send_raw(b"\xff\xff\xff")
                        dev.send_command(f"print \"set:director={tfd_state.director}\"")
                        dev.send_raw(b"\xff\xff\xff")
                self.refresh()
                return

        home = self._hitboxes.get("__home__")
        if home and home[0] <= x <= home[2] and home[1] <= y <= home[3]:
            self._set_bridge_page("page1")
            self.refresh()
            return

    def _start_edit(self, field: str, box: Tuple[int, int, int, int]) -> None:
        """Rozpoczyna edycję pola tekstowego bezpośrednio na canvasie (bez popupów)."""
        self._cancel_edit()
        
        self._edit_target = field
        sx, sy, ex, ey = box
        
        val = tfd_state.title if field == "t_title" else tfd_state.director
        
        entry = tk.Entry(self.screen_canvas, bg="#111", fg="#fff", insertbackground="#fff", 
                         font=("Consolas", max(10, int(20 * self.scale)), "bold"), bd=0, highlightthickness=1, highlightbackground="#555")
        entry.insert(0, val)
        entry.select_range(0, tk.END)
        
        # Umieszczamy entry na canvasie
        self._edit_window = self.screen_canvas.create_window(sx, sy, window=entry, anchor="nw", 
                                                           width=ex-sx, height=ey-sy)
        self._edit_entry = entry
        entry.focus_set()
        
        entry.bind("<Return>", lambda e: self._finish_edit())
        entry.bind("<Escape>", lambda e: self._cancel_edit())
        # FocusOut może być zdradliwy przy przełączaniu okien, ale tu chcemy żeby zatwierdzał
        entry.bind("<FocusOut>", lambda e: self._finish_edit())

    def _finish_edit(self) -> None:
        """Kończy edycję i zapisuje wartość."""
        if not self._edit_entry or not self._edit_target:
            return
            
        new_val = self._edit_entry.get()
        if tfd_state:
            if self._edit_target == "t_title": tfd_state.update_meta(title=new_val)
            else: tfd_state.update_meta(director=new_val)
        
        self._cancel_edit()
        self.refresh()

    def _cancel_edit(self) -> None:
        """Anuluje edycję bez zapisu."""
        if self._edit_entry:
            self._edit_entry.destroy()
            self._edit_entry = None
        if hasattr(self, "_edit_window") and self._edit_window:
            self.screen_canvas.delete(self._edit_window)
            self._edit_window = None
        self._edit_target = None
