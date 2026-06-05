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
from typing import Any, Dict, Optional

from core.tarzanSignalBus import get_signal_bus
from core.TSP.tarzanTspClient import TarzanTspClient
from core.TSP.tarzanTspConfig import TSP_MINI_PC_HOST

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
from vision.tarzanCameraSession import CameraSession
from vision.tarzanCameraControls import apply_camera_settings
from vision.tarzanVisionSetup import VisionSetupWindow



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
        self.cap = None
        self.cv2 = None
        self.preview_active = False
        self.preview_photo = None
        self.last_result = CameraTrackingResult()
        self.apply_active = False
        self._apply_thread: threading.Thread | None = None
        self._apply_result: tuple[bool, str] | None = None
        self._live_apply_after_ids: dict[str, str] = {}
        self._live_apply_enabled = False

        discovery = self.settings.get("camera_discovery", {})
        camera = self.settings.get("camera_device", {})
        tracking = self.settings.get("tracking", {})
        active_target = tracking.get("active_target", "RED_OBJECT")
        active_profile = tracking.get("target_profiles", {}).get(active_target, {})

        self.title("TARZAN - CAMERA SETUP / USTAWIENIA KAMERY")
        # Pełne okno serwisowe kamery. Nie zmienia logiki kamery ani trackingu.
        # Celem jest czytelna administracja parametrów fizycznej kamery w Full HD.
        self.geometry("1920x1080")
        self.minsize(1600, 900)
        try:
            self.state("zoomed")
        except Exception:
            pass
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
        self._bind_live_camera_controls()

    def _build_ui(self) -> None:
        top = tk.Frame(self, bg="#111111")
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        tk.Label(
            top,
            text="CAMERA SETUP — KAMERA FIZYCZNA",
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

        left = tk.Frame(body, bg="#181818", width=560, highlightthickness=2, highlightbackground="#2d7dff")
        right = tk.Frame(body, bg="#181818", highlightthickness=2, highlightbackground="#444444")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="1  PARAMETRY STAŁE KAMERY", bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(fill=tk.X, padx=8, pady=6)

        self._row_combo(left, "Index", self.index_var, [0, 1, 2, 3, 4])
        self._row_combo(left, "Backend", self.backend_var, ["DSHOW", "MSMF", "ANY"], readonly=True)
        self._row_combo(left, "Width", self.width_var, [320, 640, 800, 1280, 1920])
        self._row_combo(left, "Height", self.height_var, [240, 360, 480, 720, 1080])
        self._row_combo(left, "FPS", self.fps_var, [15, 24, 25, 30, 50, 60])
        self._row_entry(left, "FOURCC", self.fourcc_var)

        tk.Label(left, text="2  UVC / OBRAZ", bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(fill=tk.X, padx=8, pady=(12, 6))
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

        # Tracking nie należy do Camera Setup.
        # To okno ustawia tylko fizyczną kamerę; tryb śledzenia wybiera główne KHR.

        buttons = tk.Frame(left, bg="#181818")
        buttons.pack(fill=tk.X, padx=8, pady=12)
        tk.Button(buttons, text="OPEN FULL", width=12, command=self.open_full).pack(side=tk.LEFT, padx=3)
        tk.Button(buttons, text="APPLY", width=10, command=self.apply_full).pack(side=tk.LEFT, padx=3)
        tk.Button(buttons, text="SAVE TO JSON", width=14, command=self.save_to_json).pack(side=tk.LEFT, padx=3)

        buttons2 = tk.Frame(left, bg="#181818")
        buttons2.pack(fill=tk.X, padx=8, pady=(0, 12))
        tk.Button(buttons2, text="SCAN", width=10, command=self.scan).pack(side=tk.LEFT, padx=3)
        tk.Button(buttons2, text="CLOSE CAMERA", width=14, command=self.close_camera).pack(side=tk.LEFT, padx=3)

        tk.Label(right, text="PODGLĄD SERWISOWY KAMERY", bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(fill=tk.X, padx=8, pady=6)
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

    def _bind_live_camera_controls(self) -> None:
        """Podłącz suwaki serwisowe do natychmiastowego cap.set(...)."""
        bindings = [
            ("brightness", self.brightness_var),
            ("contrast", self.contrast_var),
            ("saturation", self.saturation_var),
            ("gain", self.gain_var),
            ("exposure", self.exposure_var),
            ("focus", self.focus_var),
            ("white_balance", self.white_balance_var),
            ("auto_exposure", self.auto_exposure_var),
            ("auto_focus", self.auto_focus_var),
            ("white_balance_auto", self.white_balance_auto_var),
        ]
        for key, var in bindings:
            try:
                var.trace_add("write", lambda *_args, k=key: self._schedule_live_camera_apply(k))
            except Exception:
                pass
        self._live_apply_enabled = True

    def _schedule_live_camera_apply(self, key: str) -> None:
        if not self._live_apply_enabled:
            return
        old_after = self._live_apply_after_ids.pop(key, None)
        if old_after:
            try:
                self.after_cancel(old_after)
            except Exception:
                pass
        try:
            self._live_apply_after_ids[key] = self.after(120, lambda k=key: self._apply_camera_param_live(k))
        except Exception:
            pass

    def _camera_param_value(self, key: str):
        if key == "brightness":
            return float(self.brightness_var.get())
        if key == "contrast":
            return float(self.contrast_var.get())
        if key == "saturation":
            return float(self.saturation_var.get())
        if key == "gain":
            return float(self.gain_var.get())
        if key == "exposure":
            return float(self.exposure_var.get())
        if key == "focus":
            return float(self.focus_var.get())
        if key == "white_balance":
            return float(self.white_balance_var.get())
        if key == "auto_exposure":
            return bool(self.auto_exposure_var.get())
        if key == "auto_focus":
            return bool(self.auto_focus_var.get())
        if key == "white_balance_auto":
            return bool(self.white_balance_auto_var.get())
        return None

    def _apply_camera_param_live(self, key: str) -> None:
        self._live_apply_after_ids.pop(key, None)
        if self.cap is None or self.cv2 is None:
            self.status_var.set(f"LIVE {key}: kamera nie jest otwarta — OPEN FULL / PREVIEW")
            return
        try:
            if not self.cap.isOpened():
                self.status_var.set(f"LIVE {key}: kamera nie jest otwarta")
                return
        except Exception:
            pass

        cv2 = self.cv2
        prop_map = {
            "brightness": getattr(cv2, "CAP_PROP_BRIGHTNESS", None),
            "contrast": getattr(cv2, "CAP_PROP_CONTRAST", None),
            "saturation": getattr(cv2, "CAP_PROP_SATURATION", None),
            "gain": getattr(cv2, "CAP_PROP_GAIN", None),
            "exposure": getattr(cv2, "CAP_PROP_EXPOSURE", None),
            "focus": getattr(cv2, "CAP_PROP_FOCUS", None),
            "white_balance": getattr(cv2, "CAP_PROP_WB_TEMPERATURE", None),
            "auto_focus": getattr(cv2, "CAP_PROP_AUTOFOCUS", None),
            "white_balance_auto": getattr(cv2, "CAP_PROP_AUTO_WB", None),
            "auto_exposure": getattr(cv2, "CAP_PROP_AUTO_EXPOSURE", None),
        }
        prop = prop_map.get(key)
        if prop is None:
            self.status_var.set(f"LIVE {key}: parametr nieobsługiwany przez OpenCV/backend")
            return

        value = self._camera_param_value(key)
        try:
            if key == "auto_exposure":
                set_value = 0.75 if bool(value) else 0.25
            elif key in ("auto_focus", "white_balance_auto"):
                set_value = 1 if bool(value) else 0
            else:
                set_value = float(value)
            ok = self.cap.set(prop, set_value)
            self.status_var.set(f"LIVE {key} = {value} | {'OK' if ok else 'wysłano / brak potwierdzenia'}")
        except Exception as exc:
            self.status_var.set(f"LIVE {key} ERROR | {exc}")

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
        """Szybki podgląd serwisowy kamery.

        To NIE tworzy trackera, NIE robi read_camera_state i NIE robi pełnego apply UVC.
        Camera Setup na starcie ma tylko pokazać obraz z kamery.
        """
        self.close_camera()
        self.settings = self._collect_settings()
        discovery = self.settings.get("camera_discovery", {})
        index = int(discovery.get("preferred_index", 0))
        backend_name = str(discovery.get("preferred_backend", "DSHOW"))

        try:
            import cv2
        except Exception as exc:
            self.status_var.set(f"OPEN PREVIEW ERROR | Brak OpenCV: {exc}")
            return

        self.cv2 = cv2
        try:
            cv2.setLogLevel(0)
        except Exception:
            pass

        backend_value = getattr(cv2, f"CAP_{backend_name}", None)
        try:
            if backend_value is not None:
                self.cap = cv2.VideoCapture(index, backend_value)
            else:
                self.cap = cv2.VideoCapture(index)
        except Exception as exc:
            self.cap = None
            self.status_var.set(f"OPEN PREVIEW ERROR | {exc}")
            return

        if self.cap is None or not self.cap.isOpened():
            self.status_var.set(f"OPEN PREVIEW ERROR | nie można otworzyć index={index} backend={backend_name}")
            self.close_camera()
            return

        self.status_var.set(f"OPEN PREVIEW FAST | index={index} backend={backend_name} | bez trackera / bez apply")
        self.preview_active = True
        self._preview_loop()

    def apply_full(self) -> None:
        """Ręczne, świadome wysłanie ustawień do sterownika.

        APPLY może być wolny, bo wykonuje cap.set(...) na sterowniku kamery.
        Nie wolno jednak blokować Tkintera ani mieszać tego z szybkim OPEN/PREVIEW.
        Dlatego APPLY działa w osobnym workerze i na czas apply pauzuje podgląd.
        """
        if self.apply_active:
            self.status_var.set("APPLY SETTINGS | już trwa, czekam na sterownik...")
            return

        self.settings = self._collect_settings()
        camera_cfg = dict(self.settings.get("camera_device", {}))

        if self.cap is None or self.cv2 is None or not self.cap.isOpened():
            # OPEN PREVIEW jest szybki i nie robi apply. Dopiero potem worker wykona cap.set(...).
            self.open_full()

        if self.cap is None or self.cv2 is None or not self.cap.isOpened():
            self.status_var.set("APPLY ERROR | kamera nie jest otwarta")
            return

        cap = self.cap
        cv2 = self.cv2
        self.preview_active = False
        self.apply_active = True
        self._apply_result = None
        self.status_var.set("APPLY SETTINGS | wysyłam ustawienia do sterownika... UI nie jest blokowane")

        def worker() -> None:
            try:
                apply_camera_settings(cap, cv2, camera_cfg)
                self._apply_result = (True, "APPLY SETTINGS | wysłano ustawienia do sterownika")
            except Exception as exc:
                self._apply_result = (False, f"APPLY SETTINGS ERROR | {exc}")

        self._apply_thread = threading.Thread(
            target=worker,
            name="TARZAN_CAMERA_SETUP_APPLY",
            daemon=True,
        )
        self._apply_thread.start()
        self.after(50, self._poll_apply_result)

    def _poll_apply_result(self) -> None:
        if not self.apply_active:
            return

        result = self._apply_result
        if result is None:
            self.after(50, self._poll_apply_result)
            return

        ok, msg = result
        self.apply_active = False
        self._apply_result = None
        self.status_var.set(msg)

        # Po APPLY wracamy do prostego podglądu. Nie tworzymy trackera i nie czytamy stanu kamery.
        if self.cap is not None and self.cv2 is not None:
            self.preview_active = True
            self._preview_loop()

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
        if not self.preview_active or self.cap is None or self.cv2 is None:
            return

        try:
            ok, frame = self.cap.read()
            if ok and frame is not None:
                h, w = frame.shape[:2]
                frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
                self.last_result = CameraTrackingResult(
                    visible=False,
                    error_x=0.0,
                    object_x=0.0,
                    object_y=0.0,
                    frame_center_x=w / 2.0,
                    frame_width=w,
                    frame_height=h,
                    area=0.0,
                    frame_rgb=frame_rgb,
                )
            else:
                self.last_result = CameraTrackingResult()
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
            text=f"preview FAST | tracking OFF | target={self.target_profile_var.get()}",
            fill="#eeeeee",
            font=("Consolas", 12, "bold"),
        )

    def close_camera(self) -> None:
        self.preview_active = False
        for after_id in list(self._live_apply_after_ids.values()):
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._live_apply_after_ids.clear()
        if self.apply_active:
            self.status_var.set("CLOSE CAMERA | czekam krótko na zakończenie APPLY...")
            thread = self._apply_thread
            if thread is not None and thread.is_alive():
                thread.join(timeout=0.25)
            self.apply_active = False
            self._apply_result = None
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        self.cap = None
        self.cv2 = None
        self.last_result = CameraTrackingResult()

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
        self.camera_session: CameraSession | None = None
        # Główne KHR nie inicjalizuje trackera przy starcie okna.
        # Tracker należy do CameraSession i powstaje dopiero po START KHR.
        self.camera_tracker = None
        self.camera_ok = False
        self.camera_message = "Kamera nieaktywna"
        self.camera_photo = None
        self.camera_result = CameraTrackingResult()
        self.camera_preview_active = False
        self._plugin_open_guard = False

        # KHR REALTIME: kamera i UI nie mogą blokować pętli 10 ms.
        # CameraSession jest jedynym live readerem. KHR pobiera tylko latest_result/error_x.
        self._ui_loop_active = False
        self._ui_refresh_ms = 33
        self._camera_preview_refresh_ms = int(self.vision_settings.get("tracking", {}).get("preview", {}).get("ui_refresh_ms", 100))
        self.target_template_path = ""
        self.target_template_photo = None
        self.target_template_name = "brak obiektu źródłowego"
        self.camera_list: list[str] = []
        # Główne okno KHR NIE ma już pól ustawiania kamery.
        # Jedynym źródłem prawdy jest data/khr/vision_settings.json zapisany z Camera Setup.
        self.target_profile_var = tk.StringVar(value=str(tracking_cfg.get('active_target', 'RED_OBJECT')))
        initial_source = str(self.settings.get("active_source", "TEST"))
        initial_tracking_mode = str(tracking_cfg.get('tracking_mode', 'HSV_COLOR'))
        self.source_var = tk.StringVar(value=initial_source)
        self.plugin_var = tk.StringVar(value=self._plugin_label_from_source(initial_source, initial_tracking_mode))
        # Kompatybilność dla starszych odwołań: tracking_mode_var jest aliasem trybu kamery.
        self.tracking_mode_var = tk.StringVar(value=self._tracking_mode_label(initial_tracking_mode))
        # Podgląd obrazu kamery jest tylko trybem testowym/operatorowym.
        # Domyślnie OFF: moduł KHR ma działać lekko i pobierać error_x bez kosztu ImageTk/PIL.
        self.camera_image_preview_var = tk.BooleanVar(value=True)
        self.camera_config_status_var = tk.StringVar(value=self._camera_config_status_text())

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

        self._init_runtime_integration()
        self._build_ui()
        self._apply_profile_to_ui(self.profile)
        self._set_source(self.settings.get("active_source", "TEST"))
        self._draw_all()
        autostart = bool(discovery_cfg.get("autostart_camera_on_launch", False))
        if autostart and self.source_var.get() == "KAMERA":
            self.after(250, self._open_last_camera)

    def _init_runtime_integration(self) -> None:
        """Inicjalizacja spięcia z SignalBus i TSP (Etap 9)."""
        self.bus = get_signal_bus()
        self.tsp_client = None
        
        # Raportujemy stan początkowy do lokalnego SignalBus
        self.bus.set_input("khr_state", "READY", source="KHR_INIT")
        
        # Subskrypcja komend systemowych (Etap 9)
        self.bus.subscribe("cmd_khr_start", self._handle_system_cmd)
        self.bus.subscribe("cmd_khr_stop", self._handle_system_cmd)

        # Jeśli jesteśmy w trybie LIVE, uruchamiamy klienta TSP
        if self.bus.mode == "LIVE":
            self._start_tsp_client()

    def _handle_system_cmd(self, name: str, value: Any) -> None:
        """Obsługa komend przychodzących z SignalBus (np. od PAR przez TSP)."""
        if value != 1: return
        
        if name == "cmd_khr_start":
            self.bus.log("KHR", "System command: START received.")
            self._update_runtime_state("ACTIVE")
            try:
                self.start()
            except Exception as e:
                self.bus.log("KHR", f"Start failed: {e}")
                self._update_runtime_state("ERROR")
            self.bus.set_input(name, 0, source="KHR_EXEC")
        elif name == "cmd_khr_stop":
            self.bus.log("KHR", "System command: STOP received.")
            self.stop()
            self._update_runtime_state("READY")
            self.bus.set_input(name, 0, source="KHR_EXEC")

    def _handle_tsp_message(self, message: dict[str, Any]) -> None:
        """Odbiera pakiety z miniPC i aplikuje je do lokalnego SignalBus."""
        event = message.get("event")
        if event == "snajper_packet":
            values = message.get("values", {})
            self.bus.apply_snapshot(values, source="TSP_SYNC")
        elif event == "hello":
            self.bus.log("KHR", "TSP Handshake OK.")
        elif event == "error":
            self.bus.log("KHR", f"TSP Server Error: {message.get('error')}")

    def _start_tsp_client(self) -> None:
        """Uruchamia klienta TSP dla raportowania stanu do miniPC."""
        try:
            from core.TSP.tarzanTspConfig import TSP_MINI_PC_HOST
            self.tsp_client = TarzanTspClient(host=TSP_MINI_PC_HOST, name="tarzanKHR")
            self.tsp_client.on_message = self._handle_tsp_message
            self.tsp_client.connect()
            self.tsp_client.hello()
            self.tsp_client.subscribe()
            self.bus.log("KHR", "TSP Client connected to miniPC. Subscribed to signals.")
            self.bus.set_input("khr_state", "CONNECTED", source="KHR_TSP")
        except Exception as e:
            self.bus.log("KHR", f"TSP Connection failed: {e}")

    def _update_runtime_state(self, state: str) -> None:
        """Aktualizuje stan KHR w systemie."""
        self.bus.set_input("khr_state", state, source="KHR_RUNTIME")
        if self.tsp_client:
            try:
                self.tsp_client.set_signal("khr_state", state)
            except Exception: pass

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

        setup_box = tk.Frame(top, bg="#111111")
        setup_box.pack(side=tk.LEFT, padx=(18, 8))
        tk.Button(setup_box, text="CAMERA SETUP", width=14, command=self._open_camera_setup).pack(side=tk.LEFT, padx=3)
        tk.Button(setup_box, text="TRACKING SETUP", width=16, command=self._open_vision_tracking_setup).pack(side=tk.LEFT, padx=3)

        self.profile_box = ttk.Combobox(top, textvariable=self.profile_var, values=profile_names(self.settings), width=16, state="readonly")
        self.profile_box.pack(side=tk.RIGHT, padx=8)
        self.profile_box.bind("<<ComboboxSelected>>", self._on_profile_change)
        tk.Label(top, text="Profil:", bg="#111111", fg="#cccccc").pack(side=tk.RIGHT)

        self.plugin_box = ttk.Combobox(
            top,
            textvariable=self.plugin_var,
            values=self._plugin_values(),
            width=20,
            state="readonly",
        )
        self.plugin_box.pack(side=tk.RIGHT, padx=8)
        self.plugin_box.bind("<<ComboboxSelected>>", self._on_plugin_change)
        tk.Label(top, text="Plugin:", bg="#111111", fg="#cccccc").pack(side=tk.RIGHT)

        self.btn_start = tk.Button(top, text="START", width=10, command=self.start)
        self.btn_start.pack(side=tk.RIGHT, padx=4)
        self.btn_stop = tk.Button(top, text="STOP", width=10, command=self.stop)
        self.btn_stop.pack(side=tk.RIGHT, padx=4)
        self._update_run_buttons()

        body = tk.Frame(self, bg="#111111")
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.left = self._make_panel(body, "ŹRÓDŁO / WEJŚCIE")
        self.middle = self._make_panel(body, "KOREKTA - KHR")
        self.right = self._make_panel(body, "WYNIK - OŚ POZIOMA KAMERY")

        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.middle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.input_canvas = tk.Canvas(self.left, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444444")
        self.input_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))
        self._make_camera_preview_row(self.left)
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

        self._make_settings_rows(bottom)

    def _make_panel(self, parent: tk.Widget, title: str) -> tk.Frame:
        frame = tk.Frame(parent, bg="#181818", highlightthickness=1, highlightbackground="#333333")
        tk.Label(frame, text=title, bg="#181818", fg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)
        return frame

    def _update_run_buttons(self) -> None:
        """Stały, czytelny stan operatora: START zielony, STOP czerwony."""
        try:
            if self.running:
                self.btn_start.config(bg="#16885f", fg="white", activebackground="#1fab73", relief=tk.SUNKEN)
                self.btn_stop.config(bg="#8f1f1f", fg="white", activebackground="#bd2d2d", relief=tk.RAISED)
            else:
                self.btn_start.config(bg="#1f7a3a", fg="white", activebackground="#26984a", relief=tk.RAISED)
                self.btn_stop.config(bg="#b32626", fg="white", activebackground="#d43b3b", relief=tk.SUNKEN)
        except Exception:
            pass

    def _plugin_values(self) -> list[str]:
        return [
            "TEST",
            "CZUJNIK",
            "KameraHSV",
            "KameraHAAR",
            "KameraMEDIAPIPE",
            "KameraHEAD",
            "MANUAL",
        ]

    def _tracking_mode_label(self, mode: str) -> str:
        mode = (mode or "HSV_COLOR").strip().upper()
        if mode == "FACE_HAAR":
            return "TWARZ / HAAR"
        if mode == "FACE_MEDIAPIPE":
            return "TWARZ / MEDIAPIPE"
        return "KOLOR / HSV"

    def _plugin_label_from_source(self, source: str, tracking_mode: str | None = None) -> str:
        source = (source or "TEST").strip().upper()
        mode = (tracking_mode or "HSV_COLOR").strip().upper()
        if source == "KAMERA":
            if mode == "FACE_HAAR":
                return "KameraHAAR"
            if mode == "FACE_MEDIAPIPE":
                return "KameraMEDIAPIPE"
            if mode == "HEAD_HAAR":
                return "KameraHEAD"
            return "KameraHSV"
        if source == "CZUJNIK":
            return "CZUJNIK"
        if source == "MANUAL":
            return "MANUAL"
        return "TEST"

    def _plugin_source_and_tracking(self, plugin: str | None = None) -> tuple[str, str | None]:
        label = str(plugin or self.plugin_var.get() or "TEST").strip().upper()
        if label == "KAMERAHSV":
            return "KAMERA", "HSV_COLOR"
        if label == "KAMERAHAAR":
            return "KAMERA", "FACE_HAAR"
        if label == "KAMERAMEDIAPIPE":
            return "KAMERA", "FACE_MEDIAPIPE"
        if label == "KAMERAHEAD":
            return "KAMERA", "HEAD_HAAR"
        if label == "CZUJNIK":
            return "CZUJNIK", None
        if label == "MANUAL":
            return "MANUAL", None
        return "TEST", None

    def _tracking_mode_value(self) -> str:
        source, mode = self._plugin_source_and_tracking()
        if source == "KAMERA" and mode:
            return mode
        try:
            return str(self.vision_settings.get("tracking", {}).get("tracking_mode", "HSV_COLOR"))
        except Exception:
            return "HSV_COLOR"

    def _camera_plugin_label(self) -> str:
        return self._plugin_label_from_source("KAMERA", self._tracking_mode_value())

    def _make_camera_preview_row(self, parent: tk.Widget) -> None:
        row = tk.Frame(parent, bg="#181818")
        row.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(0, 8))

        tk.Button(row, text="PODGLĄD KAMERY", width=15, command=self._open_last_camera).pack(side=tk.LEFT, padx=(0, 4))
        tk.Checkbutton(
            row,
            text="PODGLĄD ON",
            variable=self.camera_image_preview_var,
            command=self._on_camera_image_preview_toggle,
            bg="#181818",
            fg="#dddddd",
            selectcolor="#222222",
            activebackground="#181818",
            activeforeground="#ffffff",
        ).pack(side=tk.LEFT, padx=4)
        tk.Label(
            row,
            textvariable=self.camera_config_status_var,
            bg="#181818",
            fg="#d6d6d6",
            font=("Consolas", 9),
            anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)


    def _on_camera_image_preview_toggle(self) -> None:
        """Przełącza tylko render obrazu w UI.

        Nie zatrzymuje kamery, nie zmienia pluginu i nie rusza pętli KHR.
        CameraSession dalej może czytać kamerę i liczyć error_x.
        """
        self.camera_photo = None
        enabled = bool(self.camera_image_preview_var.get())
        if self.camera_session is not None:
            try:
                self.camera_session.set_frame_output_enabled(enabled)
            except Exception:
                pass
        if self.source_var.get() == "KAMERA":
            self._draw_input()

    def _on_plugin_change(self, event=None) -> None:
        self._set_source_from_plugin(self.plugin_var.get())

    def _set_source_from_plugin(self, plugin: str | None) -> None:
        source, mode = self._plugin_source_and_tracking(plugin)
        self.source_var.set(source)

        if mode:
            self.tracking_mode_var.set(self._tracking_mode_label(mode))
            try:
                self.vision_settings.setdefault("tracking", {})["tracking_mode"] = mode
            except Exception:
                pass
            if self.camera_session is not None:
                try:
                    self.camera_session.set_tracking_mode(mode)
                except Exception as exc:
                    self.camera_message = f"Nie zgłoszono pluginu kamery: {exc}"

        self._set_source(source)
        if source == "KAMERA":
            self.camera_message = f"Aktywny plugin: {self._plugin_label_from_source('KAMERA', mode or self._tracking_mode_value())} | kamera z JSON"

            # W nowym modelu plugin KameraHSV/KameraHAAR/KameraMEDIAPIPE/KameraHEAD jest jednocześnie
            # źródłem KHR. Dlatego wybór pluginu kamery ma uruchomić stałą sesję kamery
            # z JSON, ale bez restartowania jej przy samej zmianie HSV/HAAR/MediaPipe.
            session_alive = self.camera_session is not None and (
                self.camera_session.is_running or self.camera_session.is_open or self.camera_session.is_opening
            )
            if not session_alive and not self._plugin_open_guard:
                self._plugin_open_guard = True
                try:
                    self._open_camera_fast()
                finally:
                    self._plugin_open_guard = False
                return

            if self.camera_session is not None and (self.camera_session.is_open or self.camera_session.is_opening):
                self._start_camera_preview()
            self._draw_input()

    def _on_tracking_mode_change(self, event=None) -> None:
        # Kompatybilność: stary handler przekierowuje na nowy model pluginu.
        mode = self._tracking_mode_value()
        self.plugin_var.set(self._plugin_label_from_source("KAMERA", mode))
        self._set_source_from_plugin(self.plugin_var.get())

    def _camera_is_configured(self) -> bool:
        last = self.vision_settings.get("last_good_camera", {})
        return bool(last.get("enabled", False))

    def _camera_config_values(self) -> tuple[int, str, int, int, int]:
        discovery = self.vision_settings.get("camera_discovery", {})
        camera = self.vision_settings.get("camera_device", {})
        return (
            int(discovery.get("preferred_index", 0)),
            str(discovery.get("preferred_backend", "DSHOW")),
            int(camera.get("frame_width", 640)),
            int(camera.get("frame_height", 360)),
            int(camera.get("fps", 15)),
        )

    def _camera_config_status_text(self) -> str:
        if not self._camera_is_configured():
            return "BRAK KONFIGURACJI KAMERY — użyj CAMERA SETUP i zapisz ustawienia"
        index, backend, width, height, fps = self._camera_config_values()
        return f"JSON OK | index={index} | backend={backend} | {width}x{height} | {fps}fps"

    def _refresh_camera_config_status(self) -> None:
        try:
            self.camera_config_status_var.set(self._camera_config_status_text())
        except Exception:
            pass

    def _open_last_camera(self) -> None:
        # NORMALNY TRYB KHR: szybkie otwarcie stałej kamery z JSON.
        # Nie wykonujemy tu pełnego APPLY parametrów UVC.
        source, _mode = self._plugin_source_and_tracking()
        if source != "KAMERA":
            saved_mode = str(self.vision_settings.get("tracking", {}).get("tracking_mode", "HSV_COLOR"))
            self.plugin_var.set(self._plugin_label_from_source("KAMERA", saved_mode))
            self.tracking_mode_var.set(self._tracking_mode_label(saved_mode))
        self._open_camera_fast()

    def _prepare_for_setup_window(self) -> None:
        """Bezpiecznie przechodzi z RUN/PREVIEW do ustawień."""
        self.running = False
        self._ui_loop_active = False
        self._update_run_buttons()
        self._close_camera()

    def _open_camera_setup(self) -> None:
        # Tryb serwisowy kamery: osobne okno tylko do fizycznej kamery.
        # Tracking / twarz / obiekt są w TRACKING SETUP.
        self._prepare_for_setup_window()
        CameraSetupWindow(self)

    def _open_vision_tracking_setup(self) -> None:
        # Administracja rozpoznawaniem: obiekt, kolor, kształt, twarz, test i zapis JSON.
        # Nie dotyka fizycznych ustawień kamery.
        self._prepare_for_setup_window()
        VisionSetupWindow(self, PROJECT_ROOT)

    def _reload_vision_settings_from_json(self) -> None:
        try:
            self.vision_settings = load_vision_settings(PROJECT_ROOT)
            self.last_good_camera = self.vision_settings.get("last_good_camera", {})
            tracking_cfg = self.vision_settings.get("tracking", {})
            active_target = str(tracking_cfg.get("active_target", "RED_OBJECT"))
            self.target_profile_var.set(active_target)
            current_mode = str(tracking_cfg.get("tracking_mode", "HSV_COLOR"))
            self.tracking_mode_var.set(self._tracking_mode_label(current_mode))
            if self.source_var.get() == "KAMERA":
                self.plugin_var.set(self._plugin_label_from_source("KAMERA", current_mode))
            self.target_template_name = active_target
            self._refresh_camera_config_status()
        except Exception as exc:
            self.camera_message = f"Nie przeładowano vision_settings.json: {exc}"

    @khr_profiled("KHR_UI._open_camera_fast")
    def _open_camera_fast(self) -> None:
        """Uruchom czystą sesję live kamery.

        Jedyny punkt startu live camera w głównym KHR.
        Nie ma tu scan, pełnego apply UVC, restartów ani cap.read().
        """
        selected_source, selected_mode = self._plugin_source_and_tracking()
        self._reload_vision_settings_from_json()
        if selected_source == "KAMERA" and selected_mode:
            self.plugin_var.set(self._plugin_label_from_source("KAMERA", selected_mode))
            self.tracking_mode_var.set(self._tracking_mode_label(selected_mode))
            try:
                self.vision_settings.setdefault("tracking", {})["tracking_mode"] = selected_mode
            except Exception:
                pass

        if not self._camera_is_configured():
            self.camera_ok = False
            self.camera_message = "Kamera nie jest skonfigurowana. Użyj CAMERA SETUP i zapisz JSON."
            self._refresh_camera_config_status()
            self.plugin_var.set(self._camera_plugin_label())
            self._set_source("KAMERA")
            self._draw_input()
            return

        mode = self._tracking_mode_value()
        if self.camera_session is None or not self.camera_session.is_running:
            self.camera_session = CameraSession(
                project_root=PROJECT_ROOT,
                profile_name=str(self.target_profile_var.get()),
                tick_profile_callback=_khr_profile_record,
                frame_output_enabled=bool(self.camera_image_preview_var.get()),
                tracking_mode=mode,
            )

        try:
            self.camera_session.set_frame_output_enabled(bool(self.camera_image_preview_var.get()))
            request_mode = getattr(self.camera_session, "request_tracking_mode", None)
            if callable(request_mode):
                request_mode(mode)
            else:
                self.camera_session.set_tracking_mode(mode)
        except Exception:
            pass

        self.camera_session.open_once()
        self.camera_message = self.camera_session.message
        self.camera_ok = self.camera_session.is_open or self.camera_session.is_opening
        self.plugin_var.set(self._camera_plugin_label())
        self._set_source("KAMERA")
        self._start_camera_preview()

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

        # Podgląd kamery NIE czyta OpenCV. Czytanie obrazu robi CameraSession.
        # Gdy checkbox PODGLĄD jest OFF, nie rysujemy canvasu co 100 ms.
        # To jest twarde odcięcie kosztu Tkinter/PIL w normalnej pracy modułu KHR.
        if self.source_var.get() == "KAMERA" and self.camera_session is not None and not self.running:
            self._sync_camera_sample_to_ui_state()
            if bool(self.camera_image_preview_var.get()):
                self._draw_input()
            self._update_status_preview_only()

        self.after(self._camera_preview_refresh_ms, self._camera_preview_loop)

    def _sync_camera_sample_to_ui_state(self) -> None:
        session = self.camera_session
        if session is None:
            self.camera_ok = False
            self.camera_message = "Kamera nieaktywna"
            self.camera_result = CameraTrackingResult()
            self.target_visible = False
            self.error_x = 0.0
            self.object_x = 0.0
            self.object_y = 0.0
            return

        result = session.latest_result
        self.camera_result = result
        self.camera_ok = session.is_open
        self.camera_message = session.message
        self.target_visible = result.visible
        self.error_x = result.error_x
        self.object_x = result.object_x - result.frame_center_x if result.visible else 0.0
        self.object_y = result.object_y - (result.frame_height / 2.0) if result.visible else 0.0

    # Live camera worker został przeniesiony do vision.tarzanCameraSession.CameraSession.
    # KHR UI nie jest właścicielem cv2.VideoCapture ani cap.read().

    def _update_status_preview_only(self) -> None:
        self.status.config(
            text=(
                f"CAMERA PREVIEW | plugin={self.plugin_var.get()} | "
                f"visible={int(self.target_visible)} | "
                f"error_x={self.error_x:+.1f} | "
                f"target={self.target_template_name}"
            )
        )

    def _scan_cameras(self) -> None:
        # Scan należy wyłącznie do Camera Setup. Główne KHR nie skanuje kamer.
        self.camera_message = "SCAN jest dostępny tylko w CAMERA SETUP"

    def _parse_camera_index(self) -> int:
        # Kompatybilność dla starych odwołań: index zawsze pochodzi z JSON.
        return int(self.vision_settings.get("camera_discovery", {}).get("preferred_index", 0))

    @khr_profiled("KHR_UI._apply_camera_controls")
    def _apply_camera_controls(self, save_as_last: bool = True, allow_fallback: bool = False) -> None:
        # Kompatybilność ze starym przyciskiem / wywołaniem.
        # Pełne APPLY nie należy już do głównego okna realtime.
        self._open_camera_setup()

    def _on_target_profile_change(self, event=None) -> None:
        # Zachowane dla kompatybilności. Tryb śledzenia wybiera główne KHR,
        # a fizyczne ustawienia kamery pozostają w Camera Setup.
        self._reload_vision_settings_from_json()

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
        # Kompatybilność dla starych odwołań: źródło fizyczne jest ukryte,
        # operator wybiera plugin w prawym górnym polu.
        self.plugin_var.set(self._plugin_label_from_source(self.source_var.get(), self._tracking_mode_value()))
        self._set_source_from_plugin(self.plugin_var.get())

    def _set_source(self, source: str) -> None:
        source = (source or "TEST").strip().upper()
        self.source_var.set(source)
        if source == "KAMERA":
            self.plugin_var.set(self._plugin_label_from_source("KAMERA", self._tracking_mode_value()))
        elif source in ("TEST", "CZUJNIK", "MANUAL"):
            self.plugin_var.set(self._plugin_label_from_source(source, self._tracking_mode_value()))

        if source in ("TEST", "KAMERA", "CZUJNIK"):
            self.khr.clear_plugins()
            self.khr.add_plugin(self.tracking)
        elif source == "MANUAL":
            self.khr.clear_plugins()
            self.khr.add_plugin(self.manual_plugin)

        if source != "KAMERA":
            self._close_camera()
        elif self.camera_session is not None and (self.camera_session.is_open or self.camera_session.is_opening):
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

        # START KHR nie otwiera ani nie restartuje kamery.
        # Kamera live jest niezależna: uruchamia ją tylko OPEN LAST / świadomy start kamery.
        self.running = True
        self._update_run_buttons()
        self.t0 = time.time()
        self.step_preview = KHRStepPreview()
        self.axis_angle = 0.0
        self.step_count = 0

        # START w trybie KAMERA uruchamia jedną sesję kamery, jeśli jeszcze jej nie ma.
        # Nie ma osobnego startu śledzenia: START/STOP steruje pracą KHR.
        if self.source_var.get() == "KAMERA":
            if self.camera_session is None or not self.camera_session.is_running:
                self._open_camera_fast()
            if self.camera_session is not None:
                try:
                    request_mode = getattr(self.camera_session, "request_tracking_mode", None)
                    if callable(request_mode):
                        request_mode(self._tracking_mode_value())
                    else:
                        self.camera_session.set_tracking_mode(self._tracking_mode_value())
                    self.camera_session.start_tracking()
                except Exception:
                    pass
        self._start_ui_loop()
        self._loop()

    def stop(self) -> None:
        self.running = False
        self._ui_loop_active = False
        self._update_run_buttons()
        if self.camera_session is not None:
            try:
                self.camera_session.stop_tracking()
            except Exception:
                pass
        if self.source_var.get() == "KAMERA" and self.camera_ok:
            self._start_camera_preview()
            self.status.config(text="STOP | kamera zostaje w podglądzie | tracking OFF")
        else:
            self.status.config(text="STOP")

    def _close_camera(self) -> None:
        self._stop_camera_preview()
        if self.camera_session is not None:
            try:
                self.camera_session.close()
            except Exception:
                pass
        self.camera_session = None
        self.camera_ok = False
        self.camera_message = "Kamera nieaktywna"
        self.camera_photo = None
        self.camera_result = CameraTrackingResult()

    @khr_profiled("KHR_UI._loop")
    def _loop(self) -> None:
        if not self.running:
            return
        self._apply_ui_settings()
        self.time_ms = int((time.time() - self.t0) * 1000)
        self._update_model()
        
        # Etap 15: Wysyłanie offsetu KHR do miniPC (TSP)
        if self.tsp_client:
            offset_signal = self._get_offset_signal_name()
            if offset_signal:
                try:
                    # Wysyłamy aktualny offset a_corr
                    self.tsp_client.set_signal(offset_signal, float(self.a_corr))
                except Exception:
                    pass

        # KHR działa co 10 ms, ale UI nie rysuje się w tej pętli.
        # Dzięki temu Canvas i obraz z kamery nie blokują korektora.
        self.after(self.sample_time_ms, self._loop)

    def _get_offset_signal_name(self) -> Optional[str]:
        """Mapuje nazwę osi na sygnał offsetu KHR (Etap 15)."""
        mapping = {
            "oś pozioma kamery": "khr_cam_h_offset",
            "oś pionowa kamery": "khr_cam_v_offset",
            "oś pochyłu kamery": "khr_arm_t_offset", # cam_t -> arm_t
            "oś pochyłu ramienia": "khr_arm_t_offset",
            "oś ostrości kamery": "khr_cam_f_offset",
            "oś pionowa ramienia": "khr_arm_v_offset",
            "oś pozioma ramienia": "khr_arm_h_offset",
            "DRON": "khr_dron_offset",
        }
        return mapping.get(self.axis_name)

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
            if self.camera_session is not None and self.camera_session.is_open and self.camera_session.tracking_enabled:
                # Realtime KHR bierze ostatni wynik z CameraSession.
                # Tu NIE wolno robić cap.read(), bo to blokuje pętlę 10 ms.
                self._sync_camera_sample_to_ui_state()
                self.tracking.set_error(self.error_x, visible=self.target_visible)
            else:
                # Kamera może być widoczna w preview, ale bez START KHR tracker jest wyłączony.
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
        tick_ms = self.camera_session.worker_tick_ms if self.camera_session is not None else 0.0
        tracking_mode = "TRACKING ON" if (self.camera_session is not None and self.camera_session.tracking_enabled) else "PREVIEW ONLY"
        plugin_text = self._tracking_mode_label(self._tracking_mode_value())
        cam_text = f"{self.camera_message} | {tracking_mode} | plugin={plugin_text} | {self._camera_config_status_text()} | tick={tick_ms:.1f}ms"
        c.create_text(60, 48, text=cam_text, fill="#aaaaaa" if self.camera_ok else "#ff5555", anchor="w", font=("Segoe UI", 10))

        image_preview_on = bool(self.camera_image_preview_var.get())

        if not image_preview_on:
            # Najlżejszy tryb pracy KHR: kamera i tracking działają, ale UI nie przepycha
            # klatek przez PIL/ImageTk. To usuwa główny koszt podglądu operatorskiego.
            self.camera_photo = None
            self.target_template_photo = None
            state = "kamera działa" if self.camera_ok else "kamera nieaktywna"
            c.create_text(
                w / 2,
                h / 2 - 20,
                text="PODGLĄD KAMERY WYŁĄCZONY",
                fill="#ffaa00",
                font=("Segoe UI", 18, "bold"),
            )
            c.create_text(
                w / 2,
                h / 2 + 18,
                text=f"{state} | KHR używa error_x bez renderowania obrazu",
                fill="#dddddd",
                font=("Segoe UI", 11),
            )
        elif self.camera_ok and self.camera_result.frame_rgb is not None:
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

        # Obiekt źródłowy / referencyjny. Miniatura jest rysowana tylko przy włączonym podglądzie.
        c.create_text(60, h - 88, text=f"target source: {self.target_template_name}", fill="#ffaa00", anchor="w", font=("Segoe UI", 10, "bold"))

        if image_preview_on and self.target_template_path:
            try:
                from PIL import Image, ImageTk
                thumb = Image.open(self.target_template_path)
                thumb.thumbnail((90, 70))
                self.target_template_photo = ImageTk.PhotoImage(thumb)
                c.create_image(95, h - 42, image=self.target_template_photo)
            except Exception:
                pass

        lock_state = getattr(self.camera_result, "lock_state", "OFF")
        lock_hold = int(getattr(self.camera_result, "lock_hold_left_ms", 0) or 0)
        lock_text = f"  lock={lock_state}" if lock_state and lock_state != "OFF" else ""
        if lock_state == "HOLD":
            lock_text += f" hold={lock_hold}ms"
        c.create_text(w/2, h-55, text=f"visible={int(self.target_visible)}  error_x={self.error_x:+.1f} px{lock_text}", fill="#eeeeee", font=("Consolas", 13, "bold"))

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
        c.create_text(60, 28, text=f"plugin: {self.plugin_var.get()}", fill="#eeeeee", anchor="w", font=("Segoe UI", 11, "bold"))
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
            text=f"RUN | plugin={self.plugin_var.get()} | source={self.source_var.get()} | t={self.time_ms} ms | profile={self.profile.name} | error_x={self.error_x:+.1f} | A_corr={self.a_corr:+.3f} | A_final={self.a_final:+.3f} | DIR={self.dir_value} STEP={self.step_value}"
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
