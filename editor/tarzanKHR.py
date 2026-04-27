# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import math
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- KONFIGURACJA PROFILERA ---
ENABLE_EHR_PROFILER = 1
EHR_PROFILER_INTERVAL_S = 2.0
EHR_PROFILER_TOP_N = 14

if ENABLE_EHR_PROFILER:
    try:
        from core.tarzanProfiler import clear_profiler, enable_profiler, start_profiler_reporting
        enable_profiler(True)
        clear_profiler()
        start_profiler_reporting(interval_s=EHR_PROFILER_INTERVAL_S, top_n=EHR_PROFILER_TOP_N)
    except Exception:
        pass


# --- LEKKI PROFILER KHR UI ---
# Działa nawet wtedy, gdy core.tarzanProfiler nie ma dekoratora pomiarowego.
# Mierzy tylko lokalne metody KHR i wypisuje raport co EHR_PROFILER_INTERVAL_S.
_KHR_PROFILE = {}
_KHR_PROFILE_LAST_REPORT = 0.0


def _khr_profile_record(name: str, wall_s: float) -> None:
    if not ENABLE_EHR_PROFILER:
        return

    import time as _time

    item = _KHR_PROFILE.setdefault(
        name,
        {
            "calls": 0,
            "total_ms": 0.0,
            "max_ms": 0.0,
            "last_ms": 0.0,
        },
    )

    ms = wall_s * 1000.0
    item["calls"] += 1
    item["total_ms"] += ms
    item["max_ms"] = max(item["max_ms"], ms)
    item["last_ms"] = ms

    global _KHR_PROFILE_LAST_REPORT
    now = _time.time()
    if now - _KHR_PROFILE_LAST_REPORT >= EHR_PROFILER_INTERVAL_S:
        _KHR_PROFILE_LAST_REPORT = now
        _khr_profile_report()


def _khr_profile_report() -> None:
    if not _KHR_PROFILE:
        return

    rows = sorted(_KHR_PROFILE.items(), key=lambda kv: kv[1]["total_ms"], reverse=True)
    rows = rows[:EHR_PROFILER_TOP_N]

    print()
    print("=" * 118)
    print("TARZAN KHR PROFILER REPORT")
    print("-" * 118)
    print(f"{'LP':>3} | {'NAZWA':<44} | {'CALLS':>7} | {'TOTAL WALL ms':>14} | {'AVG WALL ms':>11} | {'MAX WALL ms':>11} | {'LAST WALL ms':>12}")
    print("-" * 118)

    for i, (name, item) in enumerate(rows, start=1):
        calls = item["calls"]
        total = item["total_ms"]
        avg = total / calls if calls else 0.0
        print(f"{i:>3} | {name:<44} | {calls:>7} | {total:>14.3f} | {avg:>11.3f} | {item['max_ms']:>11.3f} | {item['last_ms']:>12.3f}")

    print("=" * 118)


def khr_profiled(name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not ENABLE_EHR_PROFILER:
                return func(*args, **kwargs)

            import time as _time

            t0 = _time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                _khr_profile_record(name, _time.perf_counter() - t0)

        return wrapper

    return decorator


from motion.tarzanKHR import TarzanKHR
from motion.tarzanKHRManual import KHRManual
from motion.tarzanKHRProfiles import load_khr_settings, profile_from_settings, profile_names
from vision.tarzanCameraDiscovery import scan_cameras
from vision.tarzanVisionConfig import load_vision_settings, target_profile_names
from motion.tarzanKHRStepPreview import KHRStepPreview
from motion.tarzanKHRTracking import KHRTracking
from vision.tarzanCameraTracker import CameraTrackingResult, TarzanCameraTracker



class CameraSetupWindow(tk.Toplevel):
    """
    TARZAN KHR - osobne okno serwisowe kamery.

    To okno jest miejscem na wolne operacje UVC:
    exposure / focus / white balance / brightness / scan / pełne apply.
    Główne okno KHR nie używa tych operacji w normalnym starcie realtime.
    """

    def __init__(self, parent: "TarzanKHRWindow") -> None:
        super().__init__(parent)
        self.parent = parent
        self.project_root = PROJECT_ROOT
        self.settings = load_vision_settings(PROJECT_ROOT)
        self.tracker: TarzanCameraTracker | None = None
        self.preview_active = False
        self.preview_photo = None
        self.last_result = CameraTrackingResult()

        discovery = self.settings.get("camera_discovery", {})
        camera = self.settings.get("camera_device", {})
        tracking = self.settings.get("tracking", {})
        active_target = tracking.get("active_target", "RED_OBJECT")
        active_profile = tracking.get("target_profiles", {}).get(active_target, {})

        self.title("TARZAN - USTAWIENIA KAMERY / SERWIS")
        self.geometry("1180x760")
        self.configure(bg="#111111")
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.index_var = tk.IntVar(value=int(discovery.get("preferred_index", 0)))
        self.backend_var = tk.StringVar(value=str(discovery.get("preferred_backend", "DSHOW")))
        self.width_var = tk.IntVar(value=int(camera.get("frame_width", 640)))
        self.height_var = tk.IntVar(value=int(camera.get("frame_height", 360)))
        self.fps_var = tk.IntVar(value=int(camera.get("fps", 30)))
        self.fourcc_var = tk.StringVar(value=str(camera.get("fourcc", "MJPG")))

        self.auto_exposure_var = tk.BooleanVar(value=bool(camera.get("auto_exposure", True)))
        self.exposure_var = tk.DoubleVar(value=float(camera.get("exposure", -6)))
        self.auto_focus_var = tk.BooleanVar(value=bool(camera.get("auto_focus", False)))
        self.focus_var = tk.DoubleVar(value=float(camera.get("focus", 0)))
        self.white_balance_auto_var = tk.BooleanVar(value=bool(camera.get("white_balance_auto", True)))
        self.white_balance_var = tk.DoubleVar(value=float(camera.get("white_balance", 4500)))

        self.brightness_var = tk.DoubleVar(value=float(camera.get("brightness", 0)))
        self.contrast_var = tk.DoubleVar(value=float(camera.get("contrast", 32)))
        self.saturation_var = tk.DoubleVar(value=float(camera.get("saturation", 64)))
        self.gain_var = tk.DoubleVar(value=float(camera.get("gain", 0)))

        self.target_profile_var = tk.StringVar(value=active_target)
        self.min_area_var = tk.DoubleVar(value=float(active_profile.get("min_area", 500)))

        self.status_var = tk.StringVar(value="SERWIS KAMERY | ustaw raz, zapisz do JSON, potem KHR startuje FAST")

        self._build_ui()

    def _build_ui(self) -> None:
        top = tk.Frame(self, bg="#111111")
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        tk.Label(
            top,
            text="USTAWIENIA KAMERY / SERWIS",
            bg="#111111",
            fg="#eeeeee",
            font=("Segoe UI", 16, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            top,
            text="  Pełne APPLY jest tylko tutaj. Główne KHR używa szybkiego otwarcia z JSON.",
            bg="#111111",
            fg="#aaaaaa",
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=10)

        body = tk.Frame(self, bg="#111111")
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        left = tk.Frame(body, bg="#181818", highlightthickness=1, highlightbackground="#333333")
        right = tk.Frame(body, bg="#181818", highlightthickness=1, highlightbackground="#333333")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="PARAMETRY STAŁE KAMERY", bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(fill=tk.X, padx=8, pady=6)

        self._row_combo(left, "Index", self.index_var, [0, 1, 2, 3, 4])
        self._row_combo(left, "Backend", self.backend_var, ["DSHOW", "MSMF", "ANY"], readonly=True)
        self._row_combo(left, "Width", self.width_var, [320, 640, 800, 1280, 1920])
        self._row_combo(left, "Height", self.height_var, [240, 360, 480, 720, 1080])
        self._row_combo(left, "FPS", self.fps_var, [15, 24, 25, 30, 50, 60])
        self._row_entry(left, "FOURCC", self.fourcc_var)

        tk.Label(left, text="UVC / OBRAZ", bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(fill=tk.X, padx=8, pady=(12, 6))
        self._row_check(left, "Auto exposure", self.auto_exposure_var)
        self._row_scale(left, "Exposure", self.exposure_var, -13, 0, 1)
        self._row_check(left, "Auto focus", self.auto_focus_var)
        self._row_scale(left, "Focus", self.focus_var, 0, 255, 1)
        self._row_check(left, "Auto WB", self.white_balance_auto_var)
        self._row_scale(left, "White balance", self.white_balance_var, 2500, 7500, 100)
        self._row_scale(left, "Brightness", self.brightness_var, -64, 64, 1)
        self._row_scale(left, "Contrast", self.contrast_var, 0, 128, 1)
        self._row_scale(left, "Saturation", self.saturation_var, 0, 128, 1)
        self._row_scale(left, "Gain", self.gain_var, 0, 255, 1)

        tk.Label(left, text="TRACKING", bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(fill=tk.X, padx=8, pady=(12, 6))
        self._row_combo(left, "Cel", self.target_profile_var, target_profile_names(self.settings), readonly=True)
        self._row_scale(left, "Min area", self.min_area_var, 50, 5000, 50)

        buttons = tk.Frame(left, bg="#181818")
        buttons.pack(fill=tk.X, padx=8, pady=12)
        tk.Button(buttons, text="OPEN FULL", width=12, command=self.open_full).pack(side=tk.LEFT, padx=3)
        tk.Button(buttons, text="APPLY", width=10, command=self.apply_full).pack(side=tk.LEFT, padx=3)
        tk.Button(buttons, text="SAVE TO JSON", width=14, command=self.save_to_json).pack(side=tk.LEFT, padx=3)

        buttons2 = tk.Frame(left, bg="#181818")
        buttons2.pack(fill=tk.X, padx=8, pady=(0, 12))
        tk.Button(buttons2, text="SCAN", width=10, command=self.scan).pack(side=tk.LEFT, padx=3)
        tk.Button(buttons2, text="CLOSE CAMERA", width=14, command=self.close_camera).pack(side=tk.LEFT, padx=3)

        tk.Label(right, text="PODGLĄD SERWISOWY", bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(fill=tk.X, padx=8, pady=6)
        self.preview_canvas = tk.Canvas(right, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.status = tk.Label(self, textvariable=self.status_var, bg="#111111", fg="#d6d6d6", font=("Consolas", 10), anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)

    def _row_combo(self, parent, label, variable, values, readonly: bool = False) -> None:
        row = tk.Frame(parent, bg="#181818")
        row.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(row, text=label, bg="#181818", fg="#bbbbbb", width=14, anchor="w").pack(side=tk.LEFT)
        state = "readonly" if readonly else "normal"
        ttk.Combobox(row, textvariable=variable, values=values, width=16, state=state).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _row_entry(self, parent, label, variable) -> None:
        row = tk.Frame(parent, bg="#181818")
        row.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(row, text=label, bg="#181818", fg="#bbbbbb", width=14, anchor="w").pack(side=tk.LEFT)
        tk.Entry(row, textvariable=variable, width=18).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _row_check(self, parent, label, variable) -> None:
        row = tk.Frame(parent, bg="#181818")
        row.pack(fill=tk.X, padx=8, pady=2)
        tk.Checkbutton(row, text=label, variable=variable, bg="#181818", fg="#eeeeee", selectcolor="#333333", activebackground="#181818").pack(side=tk.LEFT)

    def _row_scale(self, parent, label, variable, from_, to, resolution) -> None:
        row = tk.Frame(parent, bg="#181818")
        row.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(row, text=label, bg="#181818", fg="#bbbbbb", width=14, anchor="w").pack(side=tk.LEFT)
        tk.Scale(row, variable=variable, from_=from_, to=to, resolution=resolution, orient=tk.HORIZONTAL, bg="#181818", fg="#eeeeee", troughcolor="#333333", highlightthickness=0, length=190).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _collect_settings(self) -> dict:
        data = self.settings
        data.setdefault("camera_discovery", {})
        data.setdefault("camera_device", {})
        data.setdefault("tracking", {})
        data["camera_discovery"]["preferred_index"] = int(self.index_var.get())
        data["camera_discovery"]["preferred_backend"] = str(self.backend_var.get())
        data["camera_discovery"]["warmup_frames"] = int(data["camera_discovery"].get("warmup_frames", 0))

        cam = data["camera_device"]
        cam["frame_width"] = int(self.width_var.get())
        cam["frame_height"] = int(self.height_var.get())
        cam["fps"] = int(self.fps_var.get())
        cam["fourcc"] = str(self.fourcc_var.get()).strip() or "MJPG"
        cam["auto_exposure"] = bool(self.auto_exposure_var.get())
        cam["exposure"] = float(self.exposure_var.get())
        cam["auto_focus"] = bool(self.auto_focus_var.get())
        cam["focus"] = float(self.focus_var.get())
        cam["white_balance_auto"] = bool(self.white_balance_auto_var.get())
        cam["white_balance"] = float(self.white_balance_var.get())
        cam["brightness"] = float(self.brightness_var.get())
        cam["contrast"] = float(self.contrast_var.get())
        cam["saturation"] = float(self.saturation_var.get())
        cam["gain"] = float(self.gain_var.get())

        tracking = data["tracking"]
        target = str(self.target_profile_var.get())
        tracking["active_target"] = target
        if target in tracking.get("target_profiles", {}):
            tracking["target_profiles"][target]["min_area"] = float(self.min_area_var.get())

        data["last_good_camera"] = {
            "enabled": True,
            "index": int(self.index_var.get()),
            "backend": str(self.backend_var.get()),
            "width": int(self.width_var.get()),
            "height": int(self.height_var.get()),
            "fps": int(self.fps_var.get()),
        }
        return data

    def _make_tracker(self) -> TarzanCameraTracker:
        self.settings = self._collect_settings()
        tracker = TarzanCameraTracker(
            device_index=int(self.index_var.get()),
            frame_width=int(self.width_var.get()),
            frame_height=int(self.height_var.get()),
            min_area=float(self.min_area_var.get()),
            project_root=PROJECT_ROOT,
        )
        tracker.settings = self.settings
        tracker.set_target_profile(str(self.target_profile_var.get()))
        return tracker

    def open_full(self) -> None:
        self.close_camera()
        self.tracker = self._make_tracker()
        ok, msg = self.tracker.open(allow_fallback=False, fast_open=False, read_state=True)
        self.status_var.set(f"OPEN FULL | {msg}")
        if ok:
            self.preview_active = True
            self._preview_loop()

    def apply_full(self) -> None:
        # Pełne APPLY w trybie serwisowym: świadomie może potrwać.
        self.open_full()

    def save_to_json(self) -> None:
        self.settings = self._collect_settings()
        path = PROJECT_ROOT / "data" / "khr" / "vision_settings.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            self.status_var.set(f"SAVED TO JSON | {path}")
            self.parent._reload_vision_settings_from_json()
        except Exception as exc:
            self.status_var.set(f"BŁĄD SAVE TO JSON: {exc}")

    def scan(self) -> None:
        try:
            infos = scan_cameras(indexes=[0, 1, 2, 3, 4], backend=str(self.backend_var.get()))
            opened = [info for info in infos if info.opened]
            if opened:
                first = opened[0]
                self.index_var.set(first.index)
                self.width_var.set(first.width or int(self.width_var.get()))
                self.height_var.set(first.height or int(self.height_var.get()))
                if first.fps:
                    self.fps_var.set(int(first.fps))
                self.status_var.set(f"SCAN | znaleziono {len(opened)} | wybrano index={first.index}")
            else:
                self.status_var.set("SCAN | nie znaleziono kamery")
        except Exception as exc:
            self.status_var.set(f"SCAN ERROR: {exc}")

    def _preview_loop(self) -> None:
        if not self.preview_active or self.tracker is None:
            return

        try:
            self.last_result = self.tracker.read()
        except Exception as exc:
            self.status_var.set(f"PREVIEW ERROR: {exc}")
            self.preview_active = False
            return

        self._draw_preview()
        self.after(33, self._preview_loop)

    def _draw_preview(self) -> None:
        c = self.preview_canvas
        c.delete("all")
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 240)

        c.create_text(30, 24, text="SERWISOWY PODGLĄD KAMERY", fill="#eeeeee", anchor="w", font=("Segoe UI", 11, "bold"))

        if self.last_result.frame_rgb is not None:
            try:
                from PIL import Image, ImageTk
                img = Image.fromarray(self.last_result.frame_rgb)
                img.thumbnail((int(w - 40), int(h - 90)))
                self.preview_photo = ImageTk.PhotoImage(img)
                c.create_image(w / 2, h / 2 + 10, image=self.preview_photo)
            except Exception as exc:
                c.create_text(w / 2, h / 2, text=f"Brak PIL/ImageTk: {exc}", fill="#ff5555")
        else:
            c.create_text(w / 2, h / 2, text="Brak klatki", fill="#777777", font=("Segoe UI", 18, "bold"))

        c.create_text(
            w / 2,
            h - 28,
            text=f"visible={int(self.last_result.visible)}  error_x={self.last_result.error_x:+.1f} px  target={self.target_profile_var.get()}",
            fill="#eeeeee",
            font=("Consolas", 12, "bold"),
        )

    def close_camera(self) -> None:
        self.preview_active = False
        if self.tracker is not None:
            try:
                self.tracker.close()
            except Exception:
                pass
        self.tracker = None

    def close(self) -> None:
        self.close_camera()
        self.destroy()


class TarzanKHRWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.settings = load_khr_settings(PROJECT_ROOT)
        self.vision_settings = load_vision_settings(PROJECT_ROOT)
        self.last_good_camera = self.vision_settings.get('last_good_camera', {})
        self.axis_name = self.settings.get("axis_name", "oś pozioma kamery")
        self.sample_time_ms = int(self.settings.get("sample_time_ms", 10))
        self.profile = profile_from_settings(self.settings)

        self.title("TARZAN - KHR / Korektor Choreografii Ruchu")
        self.geometry("1700x950")
        self.configure(bg="#111111")

        self.tracking = KHRTracking()
        self.tracking.apply_profile(self.profile)
        self.manual_plugin = KHRManual()
        self.khr = TarzanKHR(plugins=[self.tracking], max_output=1.0)
        self.step_preview = KHRStepPreview()

        camera_cfg = self.vision_settings.get("camera_device", {})
        discovery_cfg = self.vision_settings.get("camera_discovery", {})
        tracking_cfg = self.vision_settings.get("tracking", {})
        self.camera_tracker = TarzanCameraTracker(
            device_index=int(discovery_cfg.get("preferred_index", 0)),
            frame_width=int(camera_cfg.get("frame_width", 640)),
            frame_height=int(camera_cfg.get("frame_height", 360)),
            min_area=float(camera_cfg.get("min_area", 500)),
            project_root=PROJECT_ROOT,
        )
        self.camera_ok = False
        self.camera_message = "Kamera nieaktywna"
        self.camera_photo = None
        self.camera_result = CameraTrackingResult()
        self.camera_preview_active = False

        # KHR REALTIME: kamera i UI nie mogą blokować pętli 10 ms.
        # Kamera pracuje jako niezależne źródło wejścia, a KHR bierze tylko ostatni znany wynik.
        self._state_lock = threading.RLock()
        self._camera_thread: threading.Thread | None = None
        self._camera_stop = threading.Event()
        self._camera_worker_active = False
        self._camera_opening = False
        self._camera_generation = 0
        self._ui_loop_active = False
        self._ui_refresh_ms = 33
        self._camera_preview_refresh_ms = 33
        self._camera_refresh_s = 1.0 / max(1, int(camera_cfg.get("fps", 30)))
        self.target_template_path = ""
        self.target_template_photo = None
        self.target_template_name = "brak obiektu źródłowego"
        self.camera_list: list[str] = []
        self.camera_index_var = tk.StringVar(value=str(self.last_good_camera.get('index', discovery_cfg.get('preferred_index', 0))))
        self.camera_backend_var = tk.StringVar(value=str(self.last_good_camera.get('backend', discovery_cfg.get('preferred_backend', 'DSHOW'))))
        self.camera_width_var = tk.IntVar(value=int(self.last_good_camera.get('width', camera_cfg.get('frame_width', 640))))
        self.camera_height_var = tk.IntVar(value=int(self.last_good_camera.get('height', camera_cfg.get('frame_height', 360))))
        self.camera_fps_var = tk.IntVar(value=int(self.last_good_camera.get('fps', camera_cfg.get('fps', 30))))
        self.camera_min_area_var = tk.DoubleVar(value=float(tracking_cfg.get('target_profiles', {}).get(tracking_cfg.get('active_target', 'RED_OBJECT'), {}).get('min_area', 500)))
        self.target_profile_var = tk.StringVar(value=str(tracking_cfg.get('active_target', 'RED_OBJECT')))

        self.running = False
        self.t0 = time.time()
        self.time_ms = 0

        self.object_x = 0.0
        self.object_y = 0.0
        self.error_x = 0.0
        self.target_visible = True

        self.a_base = 0.0
        self.a_final = 0.0
        self.a_corr = 0.0

        self.dir_value = 1
        self.step_value = 0
        self.axis_angle = 0.0
        self.step_count = 0

        self._build_ui()
        self._apply_profile_to_ui(self.profile)
        self._set_source(self.settings.get("active_source", "TEST"))
        self._draw_all()
        autostart = bool(discovery_cfg.get("autostart_camera_on_launch", False))
        if autostart and self.source_var.get() == "KAMERA":
            self.after(250, self._open_last_camera)

    def _build_ui(self) -> None:
        top = tk.Frame(self, bg="#111111")
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        tk.Label(
            top,
            text="KHR - Korektor Choreografii Ruchu",
            bg="#111111",
            fg="#eeeeee",
            font=("Segoe UI", 16, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            top,
            text=f"  /  {self.axis_name}",
            bg="#111111",
            fg="#aaaaaa",
            font=("Segoe UI", 12),
        ).pack(side=tk.LEFT)

        self.profile_var = tk.StringVar(value=self.profile.name)
        self.source_var = tk.StringVar(value=self.settings.get("active_source", "TEST"))

        self.profile_box = ttk.Combobox(top, textvariable=self.profile_var, values=profile_names(self.settings), width=16, state="readonly")
        self.profile_box.pack(side=tk.RIGHT, padx=8)
        self.profile_box.bind("<<ComboboxSelected>>", self._on_profile_change)
        tk.Label(top, text="Profil:", bg="#111111", fg="#cccccc").pack(side=tk.RIGHT)

        self.source_box = ttk.Combobox(top, textvariable=self.source_var, values=["TEST", "KAMERA", "CZUJNIK", "MANUAL"], width=16, state="readonly")
        self.source_box.pack(side=tk.RIGHT, padx=8)
        self.source_box.bind("<<ComboboxSelected>>", self._on_source_change)
        tk.Label(top, text="Źródło:", bg="#111111", fg="#cccccc").pack(side=tk.RIGHT)

        self.btn_start = tk.Button(top, text="START", width=10, command=self.start)
        self.btn_start.pack(side=tk.RIGHT, padx=4)
        self.btn_stop = tk.Button(top, text="STOP", width=10, command=self.stop)
        self.btn_stop.pack(side=tk.RIGHT, padx=4)

        body = tk.Frame(self, bg="#111111")
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.left = self._make_panel(body, "ŹRÓDŁO / WEJŚCIE")
        self.middle = self._make_panel(body, "KOREKTA - KHR")
        self.right = self._make_panel(body, "WYNIK - OŚ POZIOMA KAMERY")

        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.middle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.input_canvas = tk.Canvas(self.left, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.input_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.khr_canvas = tk.Canvas(self.middle, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.khr_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.output_canvas = tk.Canvas(self.right, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.output_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        bottom = tk.Frame(self, bg="#111111")
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)

        self.profile_desc = tk.Label(bottom, text=self.profile.description, bg="#111111", fg="#d6d6d6", font=("Segoe UI", 10), anchor="w")
        self.profile_desc.pack(fill=tk.X)

        self.status = tk.Label(bottom, text="STOP", bg="#111111", fg="#aaaaaa", font=("Consolas", 11), anchor="w")
        self.status.pack(fill=tk.X, pady=(4, 0))

        self._make_camera_control_row(bottom)
        self._make_settings_rows(bottom)

    def _make_panel(self, parent: tk.Widget, title: str) -> tk.Frame:
        frame = tk.Frame(parent, bg="#181818", highlightthickness=1, highlightbackground="#333333")
        tk.Label(frame, text=title, bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)
        return frame

    def _make_camera_control_row(self, parent: tk.Widget) -> None:
        row = tk.Frame(parent, bg="#111111")
        row.pack(fill=tk.X, pady=(8, 0))

        tk.Label(row, text="Kamera:", bg="#111111", fg="#cccccc").pack(side=tk.LEFT, padx=(0, 4))

        self.camera_box = ttk.Combobox(row, textvariable=self.camera_index_var, values=["0", "1", "2", "3", "4"], width=28)
        self.camera_box.pack(side=tk.LEFT, padx=4)

        tk.Button(row, text="OPEN LAST", width=10, command=self._open_last_camera).pack(side=tk.LEFT, padx=4)
        tk.Button(row, text="SCAN", width=8, command=self._scan_cameras).pack(side=tk.LEFT, padx=4)

        tk.Label(row, text="Backend:", bg="#111111", fg="#cccccc").pack(side=tk.LEFT, padx=(12, 4))
        self.backend_box = ttk.Combobox(row, textvariable=self.camera_backend_var, values=["DSHOW", "MSMF", "ANY"], width=8, state="readonly")
        self.backend_box.pack(side=tk.LEFT, padx=4)

        tk.Label(row, text="Rozdz:", bg="#111111", fg="#cccccc").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Combobox(row, textvariable=self.camera_width_var, values=[320, 640, 800, 1280, 1920], width=6).pack(side=tk.LEFT)
        tk.Label(row, text="x", bg="#111111", fg="#cccccc").pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=self.camera_height_var, values=[240, 360, 480, 720, 1080], width=6).pack(side=tk.LEFT)

        tk.Label(row, text="FPS:", bg="#111111", fg="#cccccc").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Combobox(row, textvariable=self.camera_fps_var, values=[15, 24, 25, 30, 50, 60], width=5).pack(side=tk.LEFT)

        tk.Label(row, text="Cel:", bg="#111111", fg="#cccccc").pack(side=tk.LEFT, padx=(12, 4))
        self.target_box = ttk.Combobox(
            row,
            textvariable=self.target_profile_var,
            values=target_profile_names(self.vision_settings),
            width=16,
            state="readonly",
        )
        self.target_box.pack(side=tk.LEFT, padx=4)
        self.target_box.bind("<<ComboboxSelected>>", self._on_target_profile_change)

        tk.Label(row, text="Min area:", bg="#111111", fg="#cccccc").pack(side=tk.LEFT, padx=(12, 4))
        tk.Entry(row, textvariable=self.camera_min_area_var, width=8).pack(side=tk.LEFT, padx=4)

        tk.Button(row, text="LOAD TARGET", width=13, command=self._load_target_template).pack(side=tk.RIGHT, padx=4)
        tk.Button(row, text="CAMERA SETUP", width=14, command=self._open_camera_setup).pack(side=tk.RIGHT, padx=4)

    def _save_last_good_camera(self) -> None:
        self.vision_settings["last_good_camera"] = {
            "enabled": True,
            "index": self._parse_camera_index(),
            "backend": self.camera_backend_var.get(),
            "width": int(self.camera_width_var.get()),
            "height": int(self.camera_height_var.get()),
            "fps": int(self.camera_fps_var.get()),
        }

        path = PROJECT_ROOT / "data" / "khr" / "vision_settings.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.vision_settings, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            self.camera_message = f"Nie zapisano last camera: {exc}"

    def _open_last_camera(self) -> None:
        # NORMALNY TRYB KHR: szybkie otwarcie stałej kamery z JSON.
        # Nie wykonujemy tu pełnego APPLY parametrów UVC.
        self._open_camera_fast()

    def _open_camera_setup(self) -> None:
        # Tryb serwisowy: osobne okno do wolnego strojenia i zapisu JSON.
        self._close_camera()
        CameraSetupWindow(self)

    def _reload_vision_settings_from_json(self) -> None:
        try:
            self.vision_settings = load_vision_settings(PROJECT_ROOT)
            self.last_good_camera = self.vision_settings.get("last_good_camera", {})
            discovery_cfg = self.vision_settings.get("camera_discovery", {})
            camera_cfg = self.vision_settings.get("camera_device", {})
            tracking_cfg = self.vision_settings.get("tracking", {})
            active_target = tracking_cfg.get("active_target", "RED_OBJECT")
            self.camera_index_var.set(str(discovery_cfg.get("preferred_index", self.last_good_camera.get("index", 0))))
            self.camera_backend_var.set(str(discovery_cfg.get("preferred_backend", self.last_good_camera.get("backend", "DSHOW"))))
            self.camera_width_var.set(int(camera_cfg.get("frame_width", self.last_good_camera.get("width", 640))))
            self.camera_height_var.set(int(camera_cfg.get("frame_height", self.last_good_camera.get("height", 360))))
            self.camera_fps_var.set(int(camera_cfg.get("fps", self.last_good_camera.get("fps", 30))))
            self.target_profile_var.set(str(active_target))
            profile_data = tracking_cfg.get("target_profiles", {}).get(active_target, {})
            self.camera_min_area_var.set(float(profile_data.get("min_area", self.camera_min_area_var.get())))
        except Exception as exc:
            self.camera_message = f"Nie przeładowano vision_settings.json: {exc}"

    @khr_profiled("KHR_UI._open_camera_fast")
    def _open_camera_fast(self) -> None:
        """Uruchom live kamerę bez blokowania UI.

        Zasada V6:
        - jeden punkt startu sesji kamery,
        - open() i read() wykonuje ten sam worker,
        - UI tylko pokazuje ostatni wynik,
        - ponowne kliknięcia nie tworzą drugiego VideoCapture ani drugiego workera.
        """
        if self._camera_opening or self._camera_worker_active:
            self.source_var.set("KAMERA")
            self._set_source("KAMERA")
            self._start_camera_preview()
            return

        self._reload_vision_settings_from_json()

        camera_cfg = self.vision_settings.get("camera_device", {})
        tracking_cfg = self.vision_settings.get("tracking", {})
        active_target = tracking_cfg.get("active_target", self.target_profile_var.get())

        self._camera_generation += 1
        generation = self._camera_generation

        tracker = TarzanCameraTracker(
            device_index=self._parse_camera_index(),
            frame_width=int(camera_cfg.get("frame_width", self.camera_width_var.get())),
            frame_height=int(camera_cfg.get("frame_height", self.camera_height_var.get())),
            min_area=float(
                tracking_cfg.get("target_profiles", {})
                .get(active_target, {})
                .get("min_area", self.camera_min_area_var.get())
            ),
            project_root=PROJECT_ROOT,
        )
        tracker.settings = self.vision_settings
        tracker.device_index = self._parse_camera_index()
        tracker.set_target_profile(str(active_target))

        self.camera_tracker = tracker
        self.camera_ok = False
        self._camera_opening = True
        self.camera_message = "Kamera: otwieranie LIVE..."
        with self._state_lock:
            self.camera_result = CameraTrackingResult()

        self.source_var.set("KAMERA")
        self._set_source("KAMERA")
        self._start_camera_preview()
        self._start_camera_worker(tracker=tracker, generation=generation)

    def _load_target_template(self) -> None:
        path = filedialog.askopenfilename(
            title="Wybierz obraz obiektu źródłowego",
            filetypes=[
                ("Obrazy", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"),
                ("Wszystkie pliki", "*.*"),
            ],
        )
        if not path:
            return
        self.target_template_path = path
        self.target_template_name = Path(path).name
        self.camera_message = f"Załadowano obiekt: {self.target_template_name}"

    def _start_camera_preview(self) -> None:
        if self.camera_preview_active:
            return
        self.camera_preview_active = True
        self._camera_preview_loop()

    def _stop_camera_preview(self) -> None:
        self.camera_preview_active = False

    @khr_profiled("KHR_UI._camera_preview_loop")
    def _camera_preview_loop(self) -> None:
        if not self.camera_preview_active:
            return

        # Podgląd kamery NIE czyta OpenCV.
        # Czytanie obrazu robi osobny worker, tu tylko odświeżamy istniejący stan UI.
        if self.source_var.get() == "KAMERA" and self.camera_ok and not self.running:
            self._sync_camera_sample_to_ui_state()
            self._draw_input()
            self._update_status_preview_only()

        self.after(self._camera_preview_refresh_ms, self._camera_preview_loop)

    def _sync_camera_sample_to_ui_state(self) -> None:
        with self._state_lock:
            result = self.camera_result

        self.target_visible = result.visible
        self.error_x = result.error_x
        self.object_x = result.object_x - result.frame_center_x if result.visible else 0.0
        self.object_y = result.object_y - (result.frame_height / 2.0) if result.visible else 0.0

    def _start_camera_worker(self, tracker: TarzanCameraTracker | None = None, generation: int | None = None) -> None:
        if self._camera_worker_active:
            return

        tracker = tracker or self.camera_tracker
        generation = self._camera_generation if generation is None else generation

        self._camera_stop.clear()
        self._camera_worker_active = True
        self._camera_thread = threading.Thread(
            target=self._camera_worker_loop,
            args=(tracker, generation),
            name="TARZAN_KHR_CAMERA_WORKER",
            daemon=True,
        )
        self._camera_thread.start()

    def _stop_camera_worker(self) -> None:
        self._camera_worker_active = False
        self._camera_stop.set()

        thread = self._camera_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.8)

        if thread is None or not thread.is_alive():
            self._camera_thread = None
            self._camera_worker_active = False

    @khr_profiled("KHR_CAMERA.worker_tick")
    def _camera_worker_tick(self, tracker: TarzanCameraTracker, generation: int) -> None:
        result = tracker.read()
        if generation != self._camera_generation:
            return
        with self._state_lock:
            self.camera_result = result

    def _camera_worker_loop(self, tracker: TarzanCameraTracker, generation: int) -> None:
        try:
            ok, msg = tracker.open(allow_fallback=False, fast_open=True, read_state=False)

            if generation != self._camera_generation:
                tracker.close()
                return

            self.camera_ok = ok
            self._camera_opening = False
            self.camera_message = msg

            if not ok:
                return

            next_t = time.perf_counter()
            while not self._camera_stop.is_set() and generation == self._camera_generation:
                try:
                    self._camera_worker_tick(tracker, generation)
                except Exception as exc:
                    if generation == self._camera_generation:
                        with self._state_lock:
                            self.camera_result = CameraTrackingResult()
                        self.camera_message = f"Błąd kamery: {exc}"
                    time.sleep(0.10)

                next_t += self._camera_refresh_s
                sleep_s = next_t - time.perf_counter()
                if sleep_s <= 0:
                    next_t = time.perf_counter()
                    sleep_s = 0.001
                self._camera_stop.wait(min(sleep_s, self._camera_refresh_s))
        finally:
            if generation == self._camera_generation:
                self._camera_worker_active = False
                self._camera_opening = False

    def _update_status_preview_only(self) -> None:
        self.status.config(
            text=(
                f"CAMERA PREVIEW | source=KAMERA | "
                f"visible={int(self.target_visible)} | "
                f"error_x={self.error_x:+.1f} | "
                f"target={self.target_template_name}"
            )
        )

    def _scan_cameras(self) -> None:
        infos = scan_cameras(indexes=[0, 1, 2], backend=self.camera_backend_var.get())
        values = []
        for info in infos:
            if info.opened:
                values.append(f"{info.index} | {info.backend} | {info.width}x{info.height} | {info.fps:.0f}fps")
        if not values:
            values = ["0", "1", "2", "3", "4"]
            self.camera_message = "Nie znaleziono kamery dla wybranego backendu"
        else:
            self.camera_message = f"Znaleziono kamer: {len(values)}"
        self.camera_box["values"] = values
        if values:
            self.camera_index_var.set(values[0])

    def _parse_camera_index(self) -> int:
        raw = str(self.camera_index_var.get()).strip()
        if "|" in raw:
            raw = raw.split("|", 1)[0].strip()
        try:
            return int(raw)
        except Exception:
            return 0

    @khr_profiled("KHR_UI._apply_camera_controls")
    def _apply_camera_controls(self, save_as_last: bool = True, allow_fallback: bool = False) -> None:
        # Kompatybilność ze starym przyciskiem / wywołaniem.
        # Pełne APPLY nie należy już do głównego okna realtime.
        self._open_camera_setup()

    def _on_target_profile_change(self, event=None) -> None:
        self.camera_tracker.set_target_profile(self.target_profile_var.get())
        try:
            profile = self.camera_tracker.profile
            self.camera_min_area_var.set(profile.min_area)
        except Exception:
            pass

    def _make_settings_rows(self, parent: tk.Widget) -> None:
        row1 = tk.Frame(parent, bg="#111111")
        row1.pack(fill=tk.X, pady=(8, 0))
        row2 = tk.Frame(parent, bg="#111111")
        row2.pack(fill=tk.X, pady=(4, 0))

        self.gain_var = tk.DoubleVar()
        self.dead_var = tk.DoubleVar()
        self.smooth_var = tk.DoubleVar()
        self.max_var = tk.DoubleVar()
        self.delta_var = tk.DoubleVar()
        self.pred_var = tk.DoubleVar()
        self.damp_var = tk.DoubleVar()
        self.speed_var = tk.DoubleVar()
        self.manual_var = tk.DoubleVar(value=0.0)

        self._slider(row1, "gain", self.gain_var, 0.0005, 0.0100, 0.0005)
        self._slider(row1, "dead zone", self.dead_var, 0, 80, 1)
        self._slider(row1, "smooth", self.smooth_var, 0.02, 0.80, 0.01)
        self._slider(row1, "max corr", self.max_var, 0.05, 1.50, 0.05)

        self._slider(row2, "max delta", self.delta_var, 0.005, 0.150, 0.005)
        self._slider(row2, "prediction", self.pred_var, 0.0, 0.40, 0.01)
        self._slider(row2, "damping", self.damp_var, 0.0, 0.35, 0.01)
        self._slider(row2, "manual", self.manual_var, -1.0, 1.0, 0.01)

    def _slider(self, parent: tk.Widget, label: str, variable: tk.DoubleVar, from_: float, to: float, resolution: float) -> None:
        box = tk.Frame(parent, bg="#111111")
        box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(box, text=label, bg="#111111", fg="#bbbbbb").pack(anchor="w")
        tk.Scale(box, variable=variable, from_=from_, to=to, resolution=resolution, orient=tk.HORIZONTAL, bg="#111111", fg="#eeeeee", troughcolor="#333333", highlightthickness=0, length=190).pack(fill=tk.X)

    def _on_profile_change(self, event=None) -> None:
        self.profile = profile_from_settings(self.settings, self.profile_var.get())
        self.tracking.apply_profile(self.profile)
        self._apply_profile_to_ui(self.profile)
        self.profile_desc.config(text=self.profile.description)

    def _on_source_change(self, event=None) -> None:
        self._set_source(self.source_var.get())

    def _set_source(self, source: str) -> None:
        self.source_var.set(source)
        if source in ("TEST", "KAMERA", "CZUJNIK"):
            self.khr.clear_plugins()
            self.khr.add_plugin(self.tracking)
        elif source == "MANUAL":
            self.khr.clear_plugins()
            self.khr.add_plugin(self.manual_plugin)

        if source != "KAMERA":
            self._close_camera()
        elif self.camera_ok or self._camera_opening:
            self._start_camera_preview()

    def _apply_profile_to_ui(self, profile) -> None:
        self.gain_var.set(profile.gain)
        self.dead_var.set(profile.dead_zone_px)
        self.smooth_var.set(profile.smooth)
        self.max_var.set(profile.max_correction)
        self.delta_var.set(profile.max_delta_per_tick)
        self.pred_var.set(profile.prediction)
        self.damp_var.set(profile.damping)

    def start(self) -> None:
        if self.running:
            return

        if self.source_var.get() == "KAMERA" and not self.camera_ok and not self._camera_opening:
            self._open_camera_fast()

        self.running = True
        self.t0 = time.time()
        self.step_preview = KHRStepPreview()
        self.axis_angle = 0.0
        self.step_count = 0

        # Kamera live ma własnego workera; START KHR nie tworzy drugiego czytnika.
        self._start_ui_loop()
        self._loop()

    def stop(self) -> None:
        self.running = False
        self._ui_loop_active = False
        if self.source_var.get() == "KAMERA" and self.camera_ok:
            self._start_camera_preview()
            self.status.config(text="STOP | kamera zostaje w podglądzie")
        else:
            self.status.config(text="STOP")

    def _close_camera(self) -> None:
        self._camera_generation += 1
        self._camera_opening = False
        self._stop_camera_preview()
        self._stop_camera_worker()
        try:
            self.camera_tracker.close()
        except Exception:
            pass
        self.camera_ok = False
        self.camera_message = "Kamera nieaktywna"
        self.camera_photo = None
        with self._state_lock:
            self.camera_result = CameraTrackingResult()

    @khr_profiled("KHR_UI._loop")
    def _loop(self) -> None:
        if not self.running:
            return
        self._apply_ui_settings()
        self.time_ms = int((time.time() - self.t0) * 1000)
        self._update_model()

        # KHR działa co 10 ms, ale UI nie rysuje się w tej pętli.
        # Dzięki temu Canvas i obraz z kamery nie blokują korektora.
        self.after(self.sample_time_ms, self._loop)

    def _start_ui_loop(self) -> None:
        if self._ui_loop_active:
            return
        self._ui_loop_active = True
        self._ui_loop()

    @khr_profiled("KHR_UI._ui_loop")
    def _ui_loop(self) -> None:
        if not self._ui_loop_active:
            return
        self._draw_all()
        self._update_status()
        self.after(self._ui_refresh_ms, self._ui_loop)

    def _apply_ui_settings(self) -> None:
        self.tracking.update_manual_settings(
            gain=float(self.gain_var.get()),
            dead_zone_px=float(self.dead_var.get()),
            smooth=float(self.smooth_var.get()),
            max_correction=float(self.max_var.get()),
            max_delta_per_tick=float(self.delta_var.get()),
            prediction=float(self.pred_var.get()),
            damping=float(self.damp_var.get()),
            return_to_zero=self.profile.return_to_zero,
            lost_target_decay=self.profile.lost_target_decay,
        )
        self.manual_plugin.set_value(float(self.manual_var.get()))

    @khr_profiled("KHR_UI._update_model")
    def _update_model(self) -> None:
        source = self.source_var.get()

        if source == "TEST":
            phase = self.time_ms * self.profile.object_speed / 1000.0
            self.object_x = math.sin(phase * 2.0 * math.pi) * 155.0
            self.object_y = math.sin(phase * 4.0 * math.pi) * 40.0
            self.target_visible = True
            self.error_x = self.object_x
            self.tracking.set_error(self.error_x, visible=True)

        elif source == "KAMERA":
            if self.camera_ok:
                # Realtime KHR bierze ostatni wynik z workera kamery.
                # Tu NIE wolno robić camera_tracker.read(), bo to blokuje pętlę 10 ms.
                self._sync_camera_sample_to_ui_state()
                self.tracking.set_error(self.error_x, visible=self.target_visible)
            else:
                self.target_visible = False
                self.error_x = 0.0
                self.tracking.set_error(0.0, visible=False)

        elif source == "CZUJNIK":
            # Placeholder: później tu będzie realny sensor.
            phase = self.time_ms * 0.012 / 1000.0
            self.error_x = math.sin(phase * 2.0 * math.pi) * 90.0
            self.target_visible = True
            self.tracking.set_error(self.error_x, visible=True)

        elif source == "MANUAL":
            self.error_x = 0.0
            self.target_visible = True

        self.a_final = self.khr.update(self.axis_name, self.time_ms, self.a_base)
        self.a_corr = self.a_final - self.a_base
        self.dir_value, self.step_value = self.step_preview.sample(self.a_final)

        if self.step_value:
            self.step_count += 1
            step_angle = self.profile.step_angle_deg
            self.axis_angle += step_angle if self.dir_value == 1 else -step_angle

    @khr_profiled("KHR_UI._draw_all")
    def _draw_all(self) -> None:
        self._draw_input()
        self._draw_khr()
        self._draw_output()

    @khr_profiled("KHR_UI._draw_input")
    def _draw_input(self) -> None:
        c = self.input_canvas
        c.delete("all")
        source = self.source_var.get()
        if source == "KAMERA":
            self._draw_camera_input()
        elif source == "MANUAL":
            self._draw_manual_input()
        elif source == "CZUJNIK":
            self._draw_sensor_input()
        else:
            self._draw_test_input()

    def _draw_test_input(self) -> None:
        c = self.input_canvas
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 320)
        cx, cy = w / 2, h / 2
        c.create_text(60, 24, text="źródło: TEST", fill="#eeeeee", anchor="w", font=("Segoe UI", 11, "bold"))
        self._draw_deadzone_scene(c, cx, cy, w, h, self.object_x, self.object_y, True)

    def _draw_sensor_input(self) -> None:
        c = self.input_canvas
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 320)
        cx, cy = w / 2, h / 2
        c.create_text(60, 24, text="źródło: CZUJNIK (symulacja)", fill="#eeeeee", anchor="w", font=("Segoe UI", 11, "bold"))
        self._draw_deadzone_scene(c, cx, cy, w, h, self.error_x, 0, True)

    def _draw_manual_input(self) -> None:
        c = self.input_canvas
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 320)
        c.create_text(w/2, 80, text="źródło: MANUAL", fill="#eeeeee", font=("Segoe UI", 16, "bold"))
        c.create_text(w/2, 140, text=f"manual correction = {self.manual_var.get():+.3f}", fill="#ffaa00", font=("Consolas", 16, "bold"))
        c.create_text(w/2, 200, text="Suwak MANUAL na dole działa bez error_x.", fill="#aaaaaa", font=("Segoe UI", 11))

    @khr_profiled("KHR_UI._draw_camera_input")
    def _draw_camera_input(self) -> None:
        c = self.input_canvas
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 320)
        c.create_text(60, 24, text="źródło: KAMERA", fill="#eeeeee", anchor="w", font=("Segoe UI", 11, "bold"))
        cam_text = f"{self.camera_message} | QUICK | index={self._parse_camera_index()} | {self.camera_width_var.get()}x{self.camera_height_var.get()} | {self.camera_fps_var.get()}fps | {self.target_profile_var.get()}"
        c.create_text(60, 48, text=cam_text, fill="#aaaaaa" if self.camera_ok else "#ff5555", anchor="w", font=("Segoe UI", 10))

        if self.camera_ok and self.camera_result.frame_rgb is not None:
            try:
                from PIL import Image, ImageTk
                img = Image.fromarray(self.camera_result.frame_rgb)
                max_w = int(w - 50)
                max_h = int(h - 140)
                img.thumbnail((max_w, max_h))
                self.camera_photo = ImageTk.PhotoImage(img)
                c.create_image(w/2, h/2, image=self.camera_photo)
            except Exception as exc:
                c.create_text(w/2, h/2, text=f"Brak PIL/ImageTk: {exc}", fill="#ff5555", font=("Segoe UI", 11))
        else:
            c.create_text(w/2, h/2, text="Brak obrazu z kamery", fill="#777777", font=("Segoe UI", 18, "bold"))

        # Obiekt źródłowy / referencyjny.
        c.create_text(60, h - 88, text=f"target source: {self.target_template_name}", fill="#ffaa00", anchor="w", font=("Segoe UI", 10, "bold"))

        if self.target_template_path:
            try:
                from PIL import Image, ImageTk
                thumb = Image.open(self.target_template_path)
                thumb.thumbnail((90, 70))
                self.target_template_photo = ImageTk.PhotoImage(thumb)
                c.create_image(95, h - 42, image=self.target_template_photo)
            except Exception:
                pass

        c.create_text(w/2, h-55, text=f"visible={int(self.target_visible)}  error_x={self.error_x:+.1f} px", fill="#eeeeee", font=("Consolas", 13, "bold"))

    def _draw_deadzone_scene(self, c, cx, cy, w, h, object_x, object_y, visible):
        c.create_line(cx, 55, cx, h - 80, fill="#666666", dash=(4, 4))
        c.create_line(20, cy, w - 20, cy, fill="#333333")
        dz = float(self.dead_var.get())
        c.create_rectangle(cx - dz, 90, cx + dz, h - 105, outline="#555555", dash=(3, 3))
        c.create_text(cx, 70, text="środek kadru / dead zone", fill="#aaaaaa", font=("Segoe UI", 10))
        ox, oy = cx + object_x, cy + object_y
        if visible:
            size = 24
            c.create_polygon([ox, oy - size, ox - size, oy + size, ox + size, oy + size], fill="#cc2222", outline="#ff7777", width=2)
            c.create_text(ox, oy + 42, text="obiekt", fill="#ff9999", font=("Segoe UI", 10))
        c.create_line(cx, cy + 80, ox, cy + 80, fill="#ffaa00", width=2)
        c.create_text(cx, h - 48, text=f"error_x = {self.error_x:+.1f} px", fill="#eeeeee", font=("Consolas", 13, "bold"))

    @khr_profiled("KHR_UI._draw_khr")
    def _draw_khr(self) -> None:
        c = self.khr_canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 320), max(c.winfo_height(), 320)
        cx = w / 2
        c.create_text(60, 28, text=f"plugin: {self.source_var.get()}", fill="#eeeeee", anchor="w", font=("Segoe UI", 11, "bold"))
        values = [("A_base", self.a_base), ("A_corr", self.a_corr), ("A_final", self.a_final)]
        y0, gap, scale = 92, 84, 180
        for i, (name, value) in enumerate(values):
            y = y0 + i * gap
            c.create_text(36, y, text=name, fill="#cccccc", anchor="w", font=("Segoe UI", 11, "bold"))
            c.create_line(115, y, w - 35, y, fill="#444444")
            c.create_line(cx, y - 25, cx, y + 25, fill="#666666", dash=(3, 3))
            x = cx + value * scale
            c.create_rectangle(cx, y - 10, x, y + 10, fill="#2d7dff", outline="")
            c.create_text(w - 42, y, text=f"{value:+.3f}", fill="#eeeeee", anchor="e", font=("Consolas", 12))

        c.create_text(cx, h - 170, text=f"DIR = {self.dir_value}     STEP = {self.step_value}", fill="#ffffff", font=("Consolas", 18, "bold"))
        density_text = "gęściej" if abs(self.a_final) > 0.30 else "rzadziej" if abs(self.a_final) > 0.05 else "stop"
        c.create_text(cx, h - 128, text=f"gęstość impulsów: {density_text}", fill="#ffaa00", font=("Segoe UI", 13, "bold"))
        c.create_text(cx, h - 88, text=f"profile={self.profile.name}  pred={self.pred_var.get():.2f}  damping={self.damp_var.get():.2f}", fill="#bbbbbb", font=("Consolas", 11))
        c.create_text(cx, h - 58, text=f"max_delta={self.delta_var.get():.3f}  visible={int(self.target_visible)}", fill="#bbbbbb", font=("Consolas", 11))

    @khr_profiled("KHR_UI._draw_output")
    def _draw_output(self) -> None:
        c = self.output_canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 320), max(c.winfo_height(), 320)
        cx, cy = w / 2, h / 2 - 10
        radius = min(w, h) * 0.25
        c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#aaaaaa", width=3)
        c.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill="#cccccc", outline="#ffffff")
        for deg in range(0, 360, 45):
            a = math.radians(deg)
            c.create_line(cx + math.cos(a)*(radius-12), cy + math.sin(a)*(radius-12), cx + math.cos(a)*radius, cy + math.sin(a)*radius, fill="#555555", width=2)
        a = math.radians(self.axis_angle)
        flag_len = radius + 42
        x_tip, y_tip = cx + math.cos(a)*flag_len, cy + math.sin(a)*flag_len
        c.create_line(cx, cy, x_tip, y_tip, fill="#ff3333", width=5)
        perp = a + math.pi / 2.0
        p1 = (x_tip, y_tip)
        p2 = (x_tip + math.cos(perp)*24, y_tip + math.sin(perp)*24)
        p3 = (x_tip + math.cos(a)*26 + math.cos(perp)*8, y_tip + math.sin(a)*26 + math.sin(perp)*8)
        c.create_polygon([p1, p2, p3], fill="#cc2222", outline="#ff8888")
        c.create_text(cx, h - 110, text=f"kąt osi = {self.axis_angle:+.1f}°", fill="#eeeeee", font=("Consolas", 14, "bold"))
        c.create_text(cx, h - 78, text=f"STEP count = {self.step_count}", fill="#cccccc", font=("Consolas", 12))
        c.create_text(cx, h - 48, text="flaga obraca się tylko przy STEP = 1", fill="#aaaaaa", font=("Segoe UI", 10))

    def _update_status(self) -> None:
        self.status.config(
            text=f"RUN | source={self.source_var.get()} | t={self.time_ms} ms | profile={self.profile.name} | error_x={self.error_x:+.1f} | A_corr={self.a_corr:+.3f} | A_final={self.a_final:+.3f} | DIR={self.dir_value} STEP={self.step_value}"
        )

    def destroy(self) -> None:
        self.running = False
        self._ui_loop_active = False
        self._close_camera()
        super().destroy()


def main() -> None:
    app = TarzanKHRWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
